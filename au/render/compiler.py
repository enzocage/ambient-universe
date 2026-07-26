"""SynthDef-Compiler: PatchGraph -> Supriya SynthDef (plan.md Phase 2).

Der Compiler ist die Stelle, an der die L1-Invarianten *erzwungen* werden,
statt auf die Disziplin der Modulautoren zu vertrauen:

* **Glaettung** — jeder bewegte Parameter bekommt automatisch ein ``Lag``,
  dessen Zeitkonstante aus dem Manifest oder der Wissensbasis stammt. Eine
  Implementierung kann sie nicht vergessen, weil sie sie nie selbst setzt.
* **DC-Sperre und weiche Begrenzung** — vor jedem Export, immer.
* **Rueckkopplung** — nur ueber ausdrueckliche ``feedback``-Kanten, die als
  ``LocalIn``/``LocalOut`` mit deklarierter Daempfung umgesetzt werden.
* **Makros** — werden als SynthDef-Steuerungen herausgefuehrt und im Graphen
  auf ihre Zielparameter abgebildet, monoton und im sicheren Bereich.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from au.core.config import Config, get_config
from au.core.graph import PatchGraph
from au.core.knowledge import DspRules, dsp_rules
from au.core.manifest import ModuleManifest
from au.core.seeds import SeedPath
from au.modules.base import BuildContext, get_implementation, has_implementation

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry


class CompileError(RuntimeError):
    """Ein validierter Graph liess sich dennoch nicht uebersetzen."""


#: Zuordnung Parametername -> Glaettungsklasse der Wissensbasis.
#: Greift nur, wenn das Manifest keine eigene Zeitkonstante nennt.
_PARAM_CLASS_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("freq", "cutoff", "pitch", "fundamental", "detune"), "frequency"),
    (("amp", "gain", "level", "mix", "trim"), "amplitude"),
    (("res", "resonance", "damp", "feedback"), "resonance"),
    (("material", "ratios", "waveform", "partials"), "material"),
    (("width", "spread", "pan", "size", "predelay"), "spatial"),
    (("rate", "time", "decay", "drift"), "structural"),
)


def _param_class(name: str) -> str:
    lowered = name.lower()
    for needles, klass in _PARAM_CLASS_HINTS:
        if any(n in lowered for n in needles):
            return klass
    return "timbre"


@dataclass(slots=True)
class CompiledSynthDef:
    """Das Ergebnis einer Uebersetzung."""

    synthdef: Any
    name: str
    controls: dict[str, float]
    """Steuerungen des SynthDefs mit ihren Vorgabewerten (Makros und Pegel)."""
    node_order: list[str]
    feedback_channels: int
    cpu_units: float

    def control_names(self) -> list[str]:
        return sorted(self.controls)


@dataclass(slots=True)
class _Wiring:
    """Zwischenzustand waehrend der Uebersetzung."""

    outputs: dict[tuple[str, str], Any] = field(default_factory=dict)
    controls: dict[str, float] = field(default_factory=dict)
    feedback_slots: dict[tuple[str, str], int] = field(default_factory=dict)
    local_in: Any = None


# ---------------------------------------------------------------------------
# Reihenfolge
# ---------------------------------------------------------------------------


def topological_order(graph: PatchGraph) -> list[str]:
    """Sortiert die Knoten; Rueckkopplungskanten zaehlen dabei nicht mit.

    Raises:
        CompileError: Wenn nach Entfernen der Rueckkopplungskanten noch ein
            Zyklus bleibt. Der Validator sollte das vorher abgefangen haben.
    """
    indegree = {n.node_id: 0 for n in graph.nodes}
    successors: dict[str, list[str]] = {n.node_id: [] for n in graph.nodes}
    for e in graph.edges:
        if e.is_feedback:
            continue
        if e.src[0] in successors and e.dst[0] in indegree:
            successors[e.src[0]].append(e.dst[0])
            indegree[e.dst[0]] += 1

    # Stabil: bei gleicher Bereitschaft entscheidet die Knotenreihenfolge des
    # Graphen. Ohne diese Festlegung waere die erzeugte SynthDef nicht
    # reproduzierbar.
    declared = [n.node_id for n in graph.nodes]
    ready = [nid for nid in declared if indegree[nid] == 0]
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for nxt in successors[current]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                ready.append(nxt)
        ready.sort(key=declared.index)

    if len(order) != len(declared):
        stuck = sorted(set(declared) - set(order))
        raise CompileError(
            f"Zyklus ohne Rueckkopplungskante zwischen {stuck}. "
            f"Der Graph haette die Validierung nicht bestehen duerfen."
        )
    return order


# ---------------------------------------------------------------------------
# Parameteraufloesung
# ---------------------------------------------------------------------------


def _smoothing_ms(manifest: ModuleManifest, param_name: str, rules: DspRules) -> float:
    spec = manifest.params.get(param_name)
    if spec is not None and spec.smooth_ms > 0:
        return spec.smooth_ms
    return rules.smoothing.for_class(_param_class(param_name))


def _lag(signal: Any, milliseconds: float, rules: DspRules) -> Any:
    """Legt eine Glaettung auf ein Steuersignal."""
    from supriya.ugens import Lag

    seconds = max(milliseconds, rules.smoothing.minimum_ms) / 1000.0
    return Lag.kr(source=signal, lag_time=seconds)  # type: ignore[attr-defined]


def _macro_expression(
    manifest: ModuleManifest,
    macro_name: str,
    macro_signal: Any,
    param_name: str,
) -> Any:
    """Bildet ein Makrosignal aus [0, 1] auf den Zielbereich eines Parameters ab."""
    from au.core.manifest import Curve

    macro = manifest.macros[macro_name]
    target = manifest.resolved_macro(macro_name)[param_name]

    shaped = macro_signal
    if macro.curve is Curve.EXP:
        shaped = macro_signal * macro_signal
    elif macro.curve is Curve.LOG:
        shaped = macro_signal.sqrt()

    return shaped * (target.end - target.start) + target.start


def _resolve_params(
    node_id: str,
    manifest: ModuleManifest,
    node_params: dict[str, float | str],
    node_macros: dict[str, float],
    incoming: dict[str, Any],
    wiring: _Wiring,
    rules: DspRules,
    *,
    expose_macros: bool,
    builder: Any,
) -> dict[str, Any]:
    """Bestimmt fuer jeden Parameter seinen Wert oder sein Signal.

    Rangfolge:
      1. eine eingehende Steuerkante auf diesen Parameternamen
      2. eine Makroabbildung dieses Knotens
      3. ein ausdruecklich gesetzter Wert am Knoten
      4. der Manifest-Default
    """
    resolved: dict[str, Any] = {}

    # Makros als SynthDef-Steuerungen herausfuehren, damit sie zur Laufzeit
    # (und im Sweep-Test) bewegt werden koennen.
    macro_signals: dict[str, Any] = {}
    for macro_name, macro_spec in manifest.macros.items():
        default = node_macros.get(macro_name, macro_spec.default)
        if expose_macros:
            control_name = f"{node_id}_{macro_name}" if len(manifest.macros) else macro_name
            control_name = control_name.replace(".", "_")
            wiring.controls[control_name] = float(default)
            macro_signals[macro_name] = builder[control_name]
        else:
            macro_signals[macro_name] = float(default)

    macro_by_param: dict[str, str] = {}
    for name in manifest.macros:
        for param_name in manifest.resolved_macro(name):
            macro_by_param.setdefault(param_name, name)

    for param_name, spec in manifest.params.items():
        if param_name in incoming:
            signal = incoming[param_name]
            resolved[param_name] = _lag(signal, _smoothing_ms(manifest, param_name, rules), rules)
            continue

        owning_macro = macro_by_param.get(param_name)
        if owning_macro is not None and param_name not in node_params:
            macro_name = owning_macro
            if spec.is_structural:
                # Strukturelle Parameter bestimmen die Graphform. Sie werden
                # aus der Makrostellung *als Zahl* aufgeloest, nicht als
                # Signal — ein Umbau zur Laufzeit waere ein Schnitt, kein Morph.
                position = node_macros.get(macro_name, manifest.macros[macro_name].default)
                resolved[param_name] = manifest.macro_value(macro_name, float(position), param_name)
                continue
            expression = _macro_expression(
                manifest, macro_name, macro_signals[macro_name], param_name
            )
            if isinstance(expression, int | float):
                resolved[param_name] = expression
            else:
                resolved[param_name] = _lag(
                    expression, _smoothing_ms(manifest, param_name, rules), rules
                )
            continue

        if param_name in node_params:
            resolved[param_name] = node_params[param_name]
        elif spec.default is not None:
            resolved[param_name] = spec.default

    return resolved


# ---------------------------------------------------------------------------
# Sicherheitsstufe
# ---------------------------------------------------------------------------


def apply_safety_stage(signal: Any, rules: DspRules) -> Any:
    """DC-Sperre und weiche Begrenzung — vor jedem Export, ausnahmslos.

    Das ist die Einloesung der L1-Invarianten. Keine Implementierung darf sich
    darauf verlassen, dass eine andere Stelle das uebernimmt; deshalb steht es
    hier und nirgends sonst.
    """
    from supriya.ugens import LeakDC

    ceiling = rules.safety.softclip_ceiling
    leaked = LeakDC.ar(source=signal, coefficient=0.995)  # type: ignore[attr-defined]
    # tanh-artige Kennlinie: weich, monoton, ohne harte Kante.
    return (leaked / ceiling).tanh() * ceiling


# ---------------------------------------------------------------------------
# Uebersetzung
# ---------------------------------------------------------------------------


def compile_graph(
    graph: PatchGraph,
    registry: Registry,
    *,
    name: str,
    seed: SeedPath,
    cfg: Config | None = None,
    expose_macros: bool = True,
    out_bus: int = 0,
    safety_stage: bool = True,
) -> CompiledSynthDef:
    """Uebersetzt einen validierten Patch-Graphen in eine Supriya-SynthDef.

    Args:
        expose_macros: Wenn wahr, werden alle Makros als SynthDef-Steuerungen
            herausgefuehrt (Voraussetzung fuer den Makro-Sweep-Test).
        out_bus: Ausgabebus fuer den Export ``out``.
        safety_stage: Nur fuer Messzwecke abschaltbar. Die L1-Zusage lautet,
            dass ein Modul *von sich aus* ausgesteuert ist — ob das stimmt,
            laesst sich nur ohne die Begrenzung messen. Im Produktionspfad
            bleibt die Stufe immer an.

    Raises:
        CompileError: Bei Zyklen, fehlenden Manifesten oder fehlenden
            Implementierungen.
    """
    import supriya
    from supriya.ugens import LocalIn, LocalOut, Out

    c = cfg or get_config()
    rules = dsp_rules(c)
    order = topological_order(graph)

    feedback_edges = [e for e in graph.edges if e.is_feedback]
    wiring = _Wiring()
    for index, e in enumerate(feedback_edges):
        wiring.feedback_slots[e.dst] = index

    missing = [
        n.module_id
        for n in graph.nodes
        if registry.try_get(n.module_id, n.version) is not None
        and not has_implementation(n.module_id)
    ]
    if missing:
        raise CompileError(
            "Ohne Implementierung nicht uebersetzbar: "
            + ", ".join(sorted(set(missing)))
            + ". Diese Manifeste sind planbar, aber noch nicht klangfaehig."
        )

    # Steuerungen vorab sammeln, damit der Builder sie kennt.
    prospective: dict[str, float] = {"amplitude": 1.0}
    if expose_macros:
        for n in graph.nodes:
            manifest = registry.try_get(n.module_id, n.version)
            if manifest is None:
                continue
            for macro_name, macro_spec in manifest.macros.items():
                control = f"{n.node_id}_{macro_name}".replace(".", "_")
                prospective[control] = float(n.macros.get(macro_name, macro_spec.default))

    with supriya.SynthDefBuilder(**prospective) as builder:
        if feedback_edges:
            wiring.local_in = LocalIn.ar(channel_count=len(feedback_edges))  # type: ignore[attr-defined]

        cpu_units = 0.0
        for node_id in order:
            node = graph.node(node_id)
            assert node is not None
            manifest = registry.try_get(node.module_id, node.version)
            if manifest is None:
                raise CompileError(f"Modul {node.module_id!r} fehlt in der Registry")
            cpu_units += manifest.cost.cpu_units

            incoming: dict[str, Any] = {}
            for e in graph.incoming(node_id):
                if e.is_feedback:
                    slot = wiring.feedback_slots[e.dst]
                    tapped = wiring.local_in[slot] if len(feedback_edges) > 1 else wiring.local_in
                    incoming[e.dst[1]] = tapped * (e.damping or 0.0)
                    continue
                source = wiring.outputs.get(e.src)
                if source is None:
                    raise CompileError(
                        f"Kante {e.label}: die Quelle wurde noch nicht uebersetzt. "
                        f"Die topologische Sortierung ist fehlerhaft."
                    )
                incoming[e.dst[1]] = source * e.gain if e.gain != 1.0 else source

            port_inputs = {
                port.name: incoming[port.name]
                for port in manifest.ports.inputs
                if port.name in incoming
            }
            param_inputs = {k: v for k, v in incoming.items() if k in manifest.params}

            params = _resolve_params(
                node_id,
                manifest,
                dict(node.params),
                dict(node.macros),
                param_inputs,
                wiring,
                rules,
                expose_macros=expose_macros,
                builder=builder,
            )

            ctx = BuildContext(
                manifest=manifest,
                node_id=node_id,
                params=params,
                inputs=port_inputs,
                seed=seed,
                sample_rate=c.audio.sample_rate,
                channels=c.audio.channels,
            )
            produced = get_implementation(node.module_id)(ctx)

            for port in manifest.ports.outputs:
                if port.name not in produced:
                    raise CompileError(
                        f"{manifest.id} deklariert den Ausgang {port.name!r}, "
                        f"liefert ihn aber nicht."
                    )
                wiring.outputs[(node_id, port.name)] = produced[port.name]

        if feedback_edges:
            taps = [wiring.outputs[e.src] for e in feedback_edges]
            LocalOut.ar(source=taps)  # type: ignore[attr-defined]

        export_key = graph.exports.get("out") or next(iter(graph.exports.values()))
        signal = wiring.outputs[export_key]
        if safety_stage:
            signal = apply_safety_stage(signal, rules)
        signal = signal * builder["amplitude"]

        channels = c.audio.channels
        if not isinstance(signal, list | tuple):
            try:
                width = len(signal)
            except TypeError:
                width = 1
        else:
            width = len(signal)
        if width < channels:
            signal = [signal] * channels
        Out.ar(bus=out_bus, source=signal)  # type: ignore[attr-defined]

    synthdef = builder.build(name=name)
    controls = dict(prospective)
    controls.update(wiring.controls)
    return CompiledSynthDef(
        synthdef=synthdef,
        name=name,
        controls=controls,
        node_order=order,
        feedback_channels=len(feedback_edges),
        cpu_units=cpu_units,
    )
