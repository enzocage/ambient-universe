"""Der Patch-Graph und seine Validierung (plan.md Paragraph 7.1).

Ein Graph ist gueltig, wenn er
  (a) typkorrekt ist,
  (b) die Grammatik seiner Ebene erfuellt (siehe :mod:`au.core.grammar`),
  (c) azyklisch ist ausser ueber ``feedback``-Kanten mit deklarierter Daempfung,
  (d) alle Kostenbudgets einhaelt.

Diese Datei deckt (a), (c) und (d) ab; (b) liegt bewusst daneben, weil die
Grammatik je nach Organisationsebene voellig andere Fragen stellt.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from pydantic import BaseModel, Field, model_validator

from au.core.ports import (
    MAPPER_PREFIX,
    ConnectionRule,
    PortType,
    connection_rule,
    explain_forbidden,
)
from au.core.violations import Severity, ValidationReport, Violation

if TYPE_CHECKING:
    from au.core.registry import Registry

#: Obergrenze fuer die Daempfung einer Rueckkopplungsschleife (plan.md 4.1).
MAX_FEEDBACK_DAMPING = 0.98

#: Porttypen, bei denen mehrere Quellen an einem Eingang sinnvoll summieren.
_SUMMABLE: frozenset[PortType] = frozenset({PortType.AUDIO})


class Node(BaseModel):
    """Eine Modulinstanz im Graphen."""

    model_config = {"frozen": True, "extra": "forbid"}

    node_id: str
    module_id: str
    version: str | None = None
    params: dict[str, float | str] = Field(default_factory=dict)
    macros: dict[str, float] = Field(default_factory=dict)


class Edge(BaseModel):
    """Eine gerichtete Verbindung zwischen zwei Ports."""

    model_config = {"frozen": True, "extra": "forbid"}

    src: tuple[str, str]
    """(node_id, port_name) der Quelle."""
    dst: tuple[str, str]
    """(node_id, port_name) des Ziels."""
    kind: PortType
    gain: float = 1.0
    is_feedback: bool = False
    damping: float | None = None
    """Pflicht bei ``is_feedback``. Beweist, dass die Schleife abklingt."""

    @model_validator(mode="after")
    def _feedback_needs_damping(self) -> Self:
        if self.is_feedback and self.damping is None:
            raise ValueError(
                f"Rueckkopplungskante {self.label} ohne Daempfung. "
                f"Eine ungedaempfte Schleife ist nicht beweisbar stabil."
            )
        if not self.is_feedback and self.damping is not None:
            raise ValueError(
                f"Kante {self.label} traegt eine Daempfung, ist aber nicht als "
                f"Rueckkopplung markiert."
            )
        return self

    @property
    def label(self) -> str:
        return f"{self.src[0]}.{self.src[1]} -> {self.dst[0]}.{self.dst[1]}"


class PatchGraph(BaseModel):
    """Ein typisierter Modulgraph auf einer bestimmten Organisationsebene."""

    model_config = {"frozen": True, "extra": "forbid"}

    level: int = Field(ge=1, le=10)
    nodes: list[Node] = Field(default_factory=list)
    edges: list[Edge] = Field(default_factory=list)
    exports: dict[str, tuple[str, str]] = Field(default_factory=dict)
    """Benannte Ausgaenge des Graphen, etwa ``{"out": ("verb", "out")}``."""

    # -- Zugriff -------------------------------------------------------------

    def node(self, node_id: str) -> Node | None:
        return next((n for n in self.nodes if n.node_id == node_id), None)

    def incoming(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.dst[0] == node_id]

    def outgoing(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.src[0] == node_id]

    def nodes_matching(self, pattern: str) -> list[Node]:
        """Knoten, deren Modul-ID auf ein Muster wie ``gen.*`` passt."""
        if pattern.endswith("*"):
            head = pattern[:-1]
            return [n for n in self.nodes if n.module_id.startswith(head)]
        return [n for n in self.nodes if n.module_id == pattern]

    @property
    def total_cpu_units(self) -> float:
        """Nur mit Registry berechenbar; siehe :meth:`cpu_units`."""
        raise NotImplementedError("cpu_units(registry) verwenden")

    def cpu_units(self, registry: Registry) -> float:
        total = 0.0
        for n in self.nodes:
            manifest = registry.try_get(n.module_id, n.version)
            if manifest is not None:
                total += manifest.cost.cpu_units
        return total


# ---------------------------------------------------------------------------
# Validierung
# ---------------------------------------------------------------------------


def _check_node_ids(graph: PatchGraph, report: ValidationReport) -> None:
    seen: set[str] = set()
    for n in graph.nodes:
        if n.node_id in seen:
            report.add(
                Violation(
                    rule="GRAPH-DUP-NODE",
                    message=f"Knoten-ID {n.node_id!r} kommt mehrfach vor.",
                    where=n.node_id,
                    options=("Eine der Instanzen umbenennen.",),
                )
            )
        seen.add(n.node_id)


def _check_modules_resolve(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    for n in graph.nodes:
        if registry.try_get(n.module_id, n.version) is None:
            similar = registry.suggest(n.module_id, limit=3)
            options = (
                (f"Meintest du: {', '.join(similar)}?",)
                if similar
                else ("Modul im Katalog anlegen oder ID korrigieren.",)
            )
            report.add(
                Violation(
                    rule="GRAPH-UNKNOWN-MODULE",
                    message=f"Modul {n.module_id!r} ist nicht in der Registry.",
                    where=n.node_id,
                    options=options,
                )
            )


def _check_params_and_macros(
    graph: PatchGraph, registry: Registry, report: ValidationReport
) -> None:
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version)
        if manifest is None:
            continue
        for name, value in n.params.items():
            spec = manifest.params.get(name)
            if spec is None:
                report.add(
                    Violation(
                        rule="GRAPH-UNKNOWN-PARAM",
                        message=f"{n.module_id} kennt keinen Parameter {name!r}.",
                        where=n.node_id,
                        options=(f"Bekannt sind: {sorted(manifest.params)}",),
                    )
                )
                continue
            if spec.is_enum:
                if value not in (spec.enum or []):
                    report.add(
                        Violation(
                            rule="GRAPH-PARAM-ENUM",
                            message=f"{name}={value!r} ist keine gueltige Auswahl.",
                            where=n.node_id,
                            options=(f"Erlaubt: {spec.enum}",),
                        )
                    )
            elif isinstance(value, str):
                report.add(
                    Violation(
                        rule="GRAPH-PARAM-TYPE",
                        message=f"{name} erwartet eine Zahl, bekam {value!r}.",
                        where=n.node_id,
                    )
                )
            elif (
                spec.min is not None
                and spec.max is not None
                and not (spec.min <= value <= spec.max)
            ):
                report.add(
                    Violation(
                        rule="GRAPH-PARAM-RANGE",
                        message=(
                            f"{name}={value} liegt ausserhalb des sicheren Bereichs "
                            f"[{spec.min}, {spec.max}]."
                        ),
                        where=n.node_id,
                        options=(f"Auf {spec.clamp(value)} begrenzen.",),
                    )
                )
        for name in n.macros:
            if name not in manifest.macros:
                report.add(
                    Violation(
                        rule="GRAPH-UNKNOWN-MACRO",
                        message=f"{n.module_id} kennt kein Makro {name!r}.",
                        where=n.node_id,
                        options=(f"Bekannt sind: {sorted(manifest.macros)}",),
                    )
                )


def _check_edges(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    for e in graph.edges:
        src_node, dst_node = graph.node(e.src[0]), graph.node(e.dst[0])
        if src_node is None or dst_node is None:
            missing = e.src[0] if src_node is None else e.dst[0]
            report.add(
                Violation(
                    rule="GRAPH-DANGLING-EDGE",
                    message=f"Kante verweist auf unbekannten Knoten {missing!r}.",
                    where=e.label,
                )
            )
            continue

        src_mf = registry.try_get(src_node.module_id, src_node.version)
        dst_mf = registry.try_get(dst_node.module_id, dst_node.version)
        if src_mf is None or dst_mf is None:
            continue  # bereits als GRAPH-UNKNOWN-MODULE gemeldet

        src_port = src_mf.ports.output(e.src[1])
        dst_port = dst_mf.ports.input(e.dst[1])
        if src_port is None:
            report.add(
                Violation(
                    rule="GRAPH-NO-SUCH-PORT",
                    message=f"{src_mf.id} hat keinen Ausgang {e.src[1]!r}.",
                    where=e.label,
                    options=(f"Vorhanden: {[p.name for p in src_mf.ports.outputs]}",),
                )
            )
            continue
        if dst_port is None:
            report.add(
                Violation(
                    rule="GRAPH-NO-SUCH-PORT",
                    message=f"{dst_mf.id} hat keinen Eingang {e.dst[1]!r}.",
                    where=e.label,
                    options=(f"Vorhanden: {[p.name for p in dst_mf.ports.inputs]}",),
                )
            )
            continue

        if e.kind != src_port.type:
            report.add(
                Violation(
                    rule="GRAPH-EDGE-KIND",
                    message=(
                        f"Kante ist als {e.kind} deklariert, der Quellport fuehrt "
                        f"aber {src_port.type}."
                    ),
                    where=e.label,
                    options=(f"kind auf {src_port.type} setzen.",),
                )
            )

        rule = connection_rule(src_port.type, dst_port.type)
        if rule is ConnectionRule.FORBIDDEN:
            report.add(
                Violation(
                    rule="PORT-TYPE",
                    message=explain_forbidden(src_port.type, dst_port.type),
                    where=e.label,
                    options=(
                        "Ein passendes Wandlermodul zwischenschalten.",
                        "Die Verbindung streichen.",
                    ),
                )
            )
        elif rule is ConnectionRule.NEEDS_MAPPER and not dst_mf.id.startswith(MAPPER_PREFIX):
            report.add(
                Violation(
                    rule="PORT-ANALYSIS-DIRECT",
                    message=(
                        f"Ein Merkmalsstrom darf keinen Parameter unmittelbar steuern. "
                        f"{dst_mf.id} ist kein {MAPPER_PREFIX}*-Modul."
                    ),
                    where=e.label,
                    options=(
                        f"Ein {MAPPER_PREFIX}linear oder {MAPPER_PREFIX}compressed "
                        f"dazwischensetzen (deklarierte, begrenzte, geglaettete Abbildung).",
                    ),
                )
            )

        if e.is_feedback and e.damping is not None and e.damping >= MAX_FEEDBACK_DAMPING:
            report.add(
                Violation(
                    rule="GRAPH-FEEDBACK-DAMPING",
                    message=(
                        f"Daempfung {e.damping} erreicht oder ueberschreitet die "
                        f"Stabilitaetsgrenze {MAX_FEEDBACK_DAMPING}."
                    ),
                    where=e.label,
                    options=(f"Daempfung unter {MAX_FEEDBACK_DAMPING} waehlen.",),
                )
            )


def _check_fan_in(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    """Mehrfachbelegung eines Eingangs ist nur bei summierbaren Typen sinnvoll."""
    counts: dict[tuple[str, str], list[Edge]] = {}
    for e in graph.edges:
        counts.setdefault(e.dst, []).append(e)
    for (node_id, port_name), edges in counts.items():
        if len(edges) < 2:
            continue
        node = graph.node(node_id)
        manifest = registry.try_get(node.module_id, node.version) if node else None
        port = manifest.ports.input(port_name) if manifest else None
        if port is None or port.type in _SUMMABLE:
            continue
        report.add(
            Violation(
                rule="GRAPH-AMBIGUOUS-FAN-IN",
                message=(
                    f"{len(edges)} Quellen an {node_id}.{port_name} ({port.type}). "
                    f"Nur Audiosignale summieren sich eindeutig."
                ),
                where=f"{node_id}.{port_name}",
                options=(
                    "Auf eine Quelle reduzieren.",
                    "Die Quellen ueber ein Mischmodul zusammenfuehren.",
                ),
            )
        )


def _check_required_inputs(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    connected = {e.dst for e in graph.edges}
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version)
        if manifest is None:
            continue
        for port in manifest.ports.required_inputs:
            if (n.node_id, port.name) not in connected:
                report.add(
                    Violation(
                        rule="GRAPH-MISSING-INPUT",
                        message=(
                            f"Pflichteingang {port.name!r} ({port.type}) von "
                            f"{manifest.id} ist unverbunden."
                        ),
                        where=n.node_id,
                        options=(f"Eine {port.type}-Quelle anschliessen.",),
                    )
                )


def _check_acyclic(graph: PatchGraph, report: ValidationReport) -> None:
    """Zyklen sind nur ueber ausdrueckliche Rueckkopplungskanten erlaubt."""
    adjacency: dict[str, list[tuple[str, Edge]]] = {n.node_id: [] for n in graph.nodes}
    for e in graph.edges:
        if e.is_feedback:
            continue  # bewusste Schleife, separat auf Daempfung geprueft
        if e.src[0] in adjacency:
            adjacency[e.src[0]].append((e.dst[0], e))

    WHITE, GREY, BLACK = 0, 1, 2
    colour = dict.fromkeys(adjacency, WHITE)
    stack: list[str] = []

    def visit(node_id: str) -> list[str] | None:
        colour[node_id] = GREY
        stack.append(node_id)
        for nxt, _edge in adjacency.get(node_id, ()):
            if colour.get(nxt, BLACK) == GREY:
                return [*stack[stack.index(nxt) :], nxt]
            if colour.get(nxt, BLACK) == WHITE:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        colour[node_id] = BLACK
        return None

    for node_id in adjacency:
        if colour[node_id] == WHITE:
            cycle = visit(node_id)
            if cycle:
                report.add(
                    Violation(
                        rule="GRAPH-CYCLE",
                        message=(
                            "Zyklus ohne Rueckkopplungskante: " + " -> ".join(cycle) + ". "
                            "Eine implizite Schleife ist nicht auf Stabilitaet pruefbar."
                        ),
                        where=cycle[0],
                        options=(
                            "Eine Kante des Zyklus als is_feedback mit damping markieren.",
                            "Den Zyklus aufloesen.",
                        ),
                    )
                )
                return


def _check_exports(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    if not graph.exports:
        report.add(
            Violation(
                rule="GRAPH-NO-EXPORT",
                message="Der Graph benennt keinen Ausgang.",
                options=('exports setzen, etwa {"out": ("<knoten>", "out")}.',),
            )
        )
    for name, (node_id, port_name) in graph.exports.items():
        node = graph.node(node_id)
        if node is None:
            report.add(
                Violation(
                    rule="GRAPH-BAD-EXPORT",
                    message=f"Export {name!r} verweist auf unbekannten Knoten {node_id!r}.",
                    where=name,
                )
            )
            continue
        manifest = registry.try_get(node.module_id, node.version)
        if manifest is not None and manifest.ports.output(port_name) is None:
            report.add(
                Violation(
                    rule="GRAPH-BAD-EXPORT",
                    message=f"Export {name!r}: {manifest.id} hat keinen Ausgang {port_name!r}.",
                    where=name,
                    options=(f"Vorhanden: {[p.name for p in manifest.ports.outputs]}",),
                )
            )


def _check_cpu_budget(
    graph: PatchGraph, registry: Registry, budget: float | None, report: ValidationReport
) -> None:
    if budget is None:
        return
    used = graph.cpu_units(registry)
    if used > budget:
        report.add(
            Violation(
                rule="GRAPH-CPU-BUDGET",
                message=f"Rechenlast {used:.1f} ueberschreitet das Budget {budget:.1f}.",
                options=(
                    "Ein teures Modul durch ein schlankeres ersetzen.",
                    "Stimmenzahl oder Partialtonzahl senken.",
                    "Mehr Budget von der Ebene darueber anfordern (Eskalation).",
                ),
            )
        )


def validate_graph(
    graph: PatchGraph,
    registry: Registry,
    *,
    cpu_budget: float | None = None,
    check_required_inputs: bool = True,
) -> ValidationReport:
    """Prueft einen Graphen gegen Typsystem, Struktur und Kosten.

    Die Grammatik der Organisationsebene wird hier bewusst **nicht** geprueft —
    dafuer ist :func:`au.core.grammar.validate_level` zustaendig.

    Args:
        cpu_budget: Wenn gesetzt, wird die Summe der Modulkosten geprueft.
        check_required_inputs: Bei Teilgraphen (etwa waehrend der Bearbeitung
            im Studio) abschaltbar.
    """
    report = ValidationReport()
    _check_node_ids(graph, report)
    _check_modules_resolve(graph, registry, report)
    _check_params_and_macros(graph, registry, report)
    _check_edges(graph, registry, report)
    _check_fan_in(graph, registry, report)
    if check_required_inputs:
        _check_required_inputs(graph, registry, report)
    _check_acyclic(graph, report)
    _check_exports(graph, registry, report)
    _check_cpu_budget(graph, registry, cpu_budget, report)
    return report


def to_graphviz(graph: PatchGraph, registry: Registry | None = None) -> str:
    """Erzeugt eine DOT-Darstellung fuer die Diagnose."""
    palette = {
        PortType.AUDIO: "#2b6cb0",
        PortType.CTRL: "#2f855a",
        PortType.EVENT: "#b7791f",
        PortType.FIELD: "#6b46c1",
        PortType.SPECTRAL: "#c05621",
        PortType.ANALYSIS: "#718096",
        PortType.TIME: "#97266d",
        PortType.BUS: "#285e61",
    }
    lines = [
        f"digraph patch_L{graph.level} {{",
        '  rankdir=LR; node [shape=box, style=rounded, fontname="Segoe UI"];',
        f'  label="Patch, Ebene L{graph.level}"; labelloc=t;',
    ]
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version) if registry else None
        title = manifest.display_name if manifest else n.module_id
        lines.append(f'  "{n.node_id}" [label="{n.node_id}\\n{title}"];')
    for e in graph.edges:
        colour = palette.get(e.kind, "#000000")
        style = "dashed" if e.is_feedback else "solid"
        label = f"{e.kind}" + (f" fb {e.damping}" if e.is_feedback else "")
        lines.append(
            f'  "{e.src[0]}" -> "{e.dst[0]}" '
            f'[color="{colour}", style={style}, label="{label}", fontsize=9];'
        )
    for name, (node_id, _port) in graph.exports.items():
        lines.append(f'  "{name}" [shape=doublecircle, style=filled, fillcolor="#e2e8f0"];')
        lines.append(f'  "{node_id}" -> "{name}" [style=bold];')
    lines.append("}")
    return "\n".join(lines)


__all__ = [
    "MAX_FEEDBACK_DAMPING",
    "Edge",
    "Node",
    "PatchGraph",
    "Severity",
    "to_graphviz",
    "validate_graph",
]
