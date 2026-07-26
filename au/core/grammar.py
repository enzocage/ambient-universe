"""Topologie-Grammatik der Organisationsebenen (plan.md Paragraph 4).

Jede Ebene des Master-Integrators hat eine eigene Verfassung: welche Module
sie instanziieren darf, welche Verschaltungsmuster erlaubt sind und welche
Invarianten nie brechen duerfen. Diese Datei macht daraus ausfuehrbare Regeln.

Phase 1 deckt L1 und L2 ab. L3 bis L10 folgen in ihren jeweiligen Phasen;
:func:`validate_level` meldet fuer noch nicht abgedeckte Ebenen ausdruecklich,
dass keine Grammatik geprueft wurde, statt stillschweigend zu bestehen.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from au.core.graph import PatchGraph
from au.core.manifest import REQUIRED_VOICE_MACROS, Category
from au.core.ports import PortType
from au.core.violations import Severity, ValidationReport, Violation

if TYPE_CHECKING:
    from au.core.registry import Registry

#: Module, die eine Rueckkopplungsschleife absichern muessen (plan.md 4.1).
_LOOP_GUARDS: tuple[str, ...] = ("prc.util.dcblock", "prc.util.softclip")

#: Hoechstzahl kaskadierter selbstresonanter Filter in einer Stimme (plan.md 4.2).
_MAX_RESONANT_CASCADE = 3

#: Makros, die in Ambient nicht schnell moduliert werden duerfen (plan.md 4.2).
_SLOW_ONLY_MACROS: frozenset[str] = frozenset({"body", "material"})
_SLOW_MACRO_MAX_HZ = 8.0


# ---------------------------------------------------------------------------
# Gemeinsame Bausteine
# ---------------------------------------------------------------------------


def _check_max_module_level(
    graph: PatchGraph, registry: Registry, ceiling: int, rule: str, report: ValidationReport
) -> None:
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version)
        if manifest is None:
            continue
        if manifest.level > ceiling:
            report.add(
                Violation(
                    rule=rule,
                    message=(
                        f"{manifest.id} ist ein Modul der Ebene L{manifest.level} und "
                        f"gehoert nicht in einen L{graph.level}-Graphen."
                    ),
                    where=n.node_id,
                    options=(
                        f"Ein Modul mit level <= {ceiling} waehlen.",
                        f"Den Graphen auf Ebene L{manifest.level} anlegen.",
                    ),
                )
            )


def _forbid_categories(
    graph: PatchGraph,
    registry: Registry,
    forbidden: set[Category],
    rule: str,
    reason: str,
    report: ValidationReport,
) -> None:
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version)
        if manifest is None or manifest.category not in forbidden:
            continue
        report.add(
            Violation(
                rule=rule,
                message=f"{manifest.id} ({manifest.category}) ist hier nicht zulaessig. {reason}",
                where=n.node_id,
                options=("Das Modul auf der zustaendigen Ebene einsetzen.",),
            )
        )


def _check_smoothing_on_modulated_params(
    graph: PatchGraph, registry: Registry, report: ValidationReport
) -> None:
    """Jeder von aussen bewegte Parameter braucht eine Glaettung (plan.md 4.1)."""
    for e in graph.edges:
        if e.kind is not PortType.CTRL:
            continue
        dst = graph.node(e.dst[0])
        manifest = registry.try_get(dst.module_id, dst.version) if dst else None
        if manifest is None:
            continue
        spec = manifest.params.get(e.dst[1])
        if spec is None:
            continue  # Portname, kein Parametername — anderweitig geprueft
        if spec.smooth_ms <= 0.0:
            report.add(
                Violation(
                    rule="L1-T3",
                    message=(
                        f"Parameter {e.dst[1]!r} von {manifest.id} wird moduliert, "
                        f"traegt aber keine Glaettungszeit. Ein Sprung auf diesem "
                        f"Parameter erzeugt hoerbare Artefakte."
                    ),
                    where=e.label,
                    options=(
                        "Im Manifest smooth_ms setzen.",
                        "Ein prc.util.smooth zwischenschalten.",
                    ),
                )
            )


def _check_audio_rate_targets(
    graph: PatchGraph, registry: Registry, report: ValidationReport
) -> None:
    """Audiorate darf nur auf ausdruecklich freigegebene Parameter."""
    for e in graph.edges:
        if e.kind is not PortType.AUDIO:
            continue
        dst = graph.node(e.dst[0])
        manifest = registry.try_get(dst.module_id, dst.version) if dst else None
        if manifest is None:
            continue
        spec = manifest.params.get(e.dst[1])
        if spec is not None and not spec.audio_rate_safe:
            report.add(
                Violation(
                    rule="L1-T4",
                    message=(
                        f"{manifest.id}.{e.dst[1]} ist nicht fuer Audiorate-Modulation "
                        f"freigegeben (audio_rate_safe: false)."
                    ),
                    where=e.label,
                    options=(
                        "Das Signal ueber einen k-rate-Pfad fuehren.",
                        "Einen audio_rate_safe-Parameter als Ziel waehlen.",
                    ),
                )
            )


def _check_feedback_guards(graph: PatchGraph, registry: Registry, report: ValidationReport) -> None:
    """Jede Rueckkopplungsschleife braucht DC-Sperre und weiche Begrenzung."""
    feedback_edges = [e for e in graph.edges if e.is_feedback]
    if not feedback_edges:
        return
    resolved = (registry.try_get(n.module_id, n.version) for n in graph.nodes)
    present = {m.id for m in resolved if m is not None}
    missing = [guard for guard in _LOOP_GUARDS if guard not in present]
    if missing:
        report.add(
            Violation(
                rule="L1-T2",
                message=(
                    f"Der Graph enthaelt {len(feedback_edges)} Rueckkopplungskante(n), "
                    f"aber keine {', '.join(missing)}. Ohne DC-Sperre laeuft die "
                    f"Schleife weg, ohne weiche Begrenzung klirrt sie."
                ),
                where=feedback_edges[0].label,
                options=tuple(f"{guard} in die Schleife einfuegen." for guard in missing),
            )
        )


# ---------------------------------------------------------------------------
# L1 — Signal / Klangatom
# ---------------------------------------------------------------------------


def _validate_l1(graph: PatchGraph, registry: Registry) -> ValidationReport:
    report = ValidationReport()
    _check_max_module_level(graph, registry, 1, "L1-M1", report)
    _forbid_categories(
        graph,
        registry,
        {Category.SYMBOLIC, Category.SPACE, Category.TRANSITION, Category.CRITIC},
        "L1-M2",
        "L1 kennt keine Musik, nur Signale.",
        report,
    )
    _check_smoothing_on_modulated_params(graph, registry, report)
    _check_audio_rate_targets(graph, registry, report)
    _check_feedback_guards(graph, registry, report)
    return report


# ---------------------------------------------------------------------------
# L2 — Stimme / Klangkoerper
# ---------------------------------------------------------------------------


def _voice_generators(graph: PatchGraph, registry: Registry) -> list[str]:
    """Knoten-IDs der Generatoren, die als vollstaendige Stimme taugen."""
    out: list[str] = []
    for n in graph.nodes:
        manifest = registry.try_get(n.module_id, n.version)
        if manifest is None or manifest.category is not Category.GENERATOR:
            continue
        if REQUIRED_VOICE_MACROS.issubset(manifest.macros):
            out.append(n.node_id)
    return out


def _longest_resonant_cascade(graph: PatchGraph, registry: Registry) -> int:
    """Laengste Kette hintereinandergeschalteter selbstresonanter Filter."""

    def is_resonant(node_id: str) -> bool:
        node = graph.node(node_id)
        manifest = registry.try_get(node.module_id, node.version) if node else None
        return manifest is not None and "resonant" in manifest.tags

    successors: dict[str, list[str]] = {n.node_id: [] for n in graph.nodes}
    for e in graph.edges:
        if e.kind is PortType.AUDIO and not e.is_feedback and e.src[0] in successors:
            successors[e.src[0]].append(e.dst[0])

    memo: dict[str, int] = {}

    def depth(node_id: str, seen: frozenset[str]) -> int:
        if node_id in seen:
            return 0
        if node_id in memo:
            return memo[node_id]
        own = 1 if is_resonant(node_id) else 0
        best = 0
        for nxt in successors.get(node_id, ()):
            best = max(best, depth(nxt, seen | {node_id}))
        value = own + best if own else max(best, 0)
        memo[node_id] = value
        return value

    return max((depth(n.node_id, frozenset()) for n in graph.nodes), default=0)


def _check_slow_macro_modulation(
    graph: PatchGraph, registry: Registry, report: ValidationReport
) -> None:
    """`body` und `material` duerfen nicht schnell bewegt werden (Ambient-Regel)."""
    for e in graph.edges:
        if e.kind is not PortType.CTRL:
            continue
        if e.dst[1] not in _SLOW_ONLY_MACROS:
            continue
        src = graph.node(e.src[0])
        manifest = registry.try_get(src.module_id, src.version) if src else None
        if manifest is None or src is None:
            continue
        rate = src.params.get("rate_hz") or src.params.get("frequency")
        if isinstance(rate, int | float) and rate > _SLOW_MACRO_MAX_HZ:
            report.add(
                Violation(
                    rule="L2-T6",
                    message=(
                        f"{e.dst[1]!r} wird mit {rate} Hz moduliert. In Ambient wird "
                        f"jede Bewegung ueber {_SLOW_MACRO_MAX_HZ} Hz auf Koerper und "
                        f"Material als Effekt hoerbar statt als Atmung."
                    ),
                    where=e.label,
                    options=(f"Modulationsrate unter {_SLOW_MACRO_MAX_HZ} Hz waehlen.",),
                )
            )


def _validate_l2(graph: PatchGraph, registry: Registry) -> ValidationReport:
    report = ValidationReport()
    _check_max_module_level(graph, registry, 2, "L2-M1", report)
    _forbid_categories(
        graph,
        registry,
        {Category.SPACE, Category.SYMBOLIC, Category.TRANSITION, Category.CRITIC},
        "L2-M2",
        "Raum gehoert nach L5/L6, Symbolik nach L4.",
        report,
    )

    voices = _voice_generators(graph, registry)
    if not voices:
        report.add(
            Violation(
                rule="L2-T2",
                message=(
                    "Kein Generator im Graphen fuehrt den vollstaendigen Makrosatz "
                    f"{sorted(REQUIRED_VOICE_MACROS)}. Eine Stimme ohne Makros ist "
                    "fuer hoehere Ebenen nicht ansteuerbar."
                ),
                options=(
                    "Einen Generator der Ebene L2 einsetzen.",
                    "Die fehlenden Makros im Manifest ergaenzen.",
                ),
            )
        )

    if len(graph.exports) > 1:
        report.add(
            Violation(
                rule="L2-T1",
                message=(
                    f"Eine Stimme hat genau einen Ausgang, dieser Graph benennt "
                    f"{len(graph.exports)}: {sorted(graph.exports)}."
                ),
                options=(
                    "Die Ausgaenge zusammenfassen.",
                    "Den Graphen als Verband (L6) anlegen.",
                ),
            )
        )

    cascade = _longest_resonant_cascade(graph, registry)
    if cascade > _MAX_RESONANT_CASCADE:
        report.add(
            Violation(
                rule="L2-T3",
                message=(
                    f"{cascade} selbstresonante Filter in Reihe (erlaubt sind "
                    f"{_MAX_RESONANT_CASCADE}). Kaskadierte Resonanzen sind ueber "
                    f"den Parameterraum nicht mehr sicher beherrschbar."
                ),
                options=(
                    "Filter parallel statt seriell schalten.",
                    "Resonanz einer Stufe zuruecknehmen.",
                ),
            )
        )

    _check_smoothing_on_modulated_params(graph, registry, report)
    _check_audio_rate_targets(graph, registry, report)
    _check_feedback_guards(graph, registry, report)
    _check_slow_macro_modulation(graph, registry, report)
    return report


# ---------------------------------------------------------------------------
# Verteiler
# ---------------------------------------------------------------------------

_VALIDATORS = {
    1: _validate_l1,
    2: _validate_l2,
}

#: Phase, in der die Grammatik der jeweiligen Ebene entsteht (plan.md 15).
_PLANNED_IN_PHASE = {
    3: "Phase 2",
    4: "Phase 3",
    5: "Phase 8",
    6: "Phase 8",
    7: "Phase 9",
    8: "Phase 9",
    9: "Phase 10",
    10: "Phase 10",
}


def validate_level(graph: PatchGraph, registry: Registry) -> ValidationReport:
    """Prueft einen Graphen gegen die Grammatik seiner Organisationsebene."""
    validator = _VALIDATORS.get(graph.level)
    if validator is None:
        report = ValidationReport()
        phase = _PLANNED_IN_PHASE.get(graph.level, "spaeter")
        report.add(
            Violation(
                rule="GRAMMAR-NOT-IMPLEMENTED",
                message=(
                    f"Fuer Ebene L{graph.level} ist noch keine Grammatik hinterlegt "
                    f"(geplant in {phase}). Der Graph wurde nur typgeprueft."
                ),
                severity=Severity.WARNING,
            )
        )
        return report
    return validator(graph, registry)


def validate(
    graph: PatchGraph, registry: Registry, *, cpu_budget: float | None = None
) -> ValidationReport:
    """Vollpruefung: Typsystem und Struktur, dann Ebenengrammatik."""
    from au.core.graph import validate_graph

    report = validate_graph(graph, registry, cpu_budget=cpu_budget)
    report.extend(validate_level(graph, registry).violations)
    return report
