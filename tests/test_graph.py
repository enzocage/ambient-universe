"""Phase-1-Akzeptanz: Patch-Graph, Typsystem und Ebenengrammatik."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from au.core.grammar import validate, validate_level
from au.core.graph import Edge, Node, PatchGraph, to_graphviz, validate_graph
from au.core.ports import ConnectionRule, PortType, connection_rule
from au.core.registry import Registry, load_registry

pytestmark = pytest.mark.smoke


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=False)


def _rules(report) -> set[str]:  # type: ignore[no-untyped-def]
    return {v.rule for v in report.violations}


# ---------------------------------------------------------------------------
# Typsystem
# ---------------------------------------------------------------------------


def test_audio_to_audio_is_allowed() -> None:
    assert connection_rule(PortType.AUDIO, PortType.AUDIO) is ConnectionRule.OK


def test_analysis_to_ctrl_needs_a_mapper() -> None:
    assert connection_rule(PortType.ANALYSIS, PortType.CTRL) is ConnectionRule.NEEDS_MAPPER


def test_audio_to_event_is_forbidden() -> None:
    assert connection_rule(PortType.AUDIO, PortType.EVENT) is ConnectionRule.FORBIDDEN


def test_spectral_cannot_leave_the_fft_chain() -> None:
    assert connection_rule(PortType.SPECTRAL, PortType.AUDIO) is ConnectionRule.FORBIDDEN


# ---------------------------------------------------------------------------
# Graphstruktur
# ---------------------------------------------------------------------------


def _chain() -> PatchGraph:
    """Gueltige L1-Kette: Oszillator -> Filter -> Begrenzung."""
    return PatchGraph(
        level=1,
        nodes=[
            Node(node_id="osc", module_id="gen.osc.bandlimited"),
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
            Node(node_id="clip", module_id="prc.util.softclip"),
        ],
        edges=[
            Edge(src=("osc", "out"), dst=("flt", "in"), kind=PortType.AUDIO),
            Edge(src=("flt", "out"), dst=("clip", "in"), kind=PortType.AUDIO),
        ],
        exports={"out": ("clip", "out")},
    )


def test_valid_chain_passes(registry: Registry) -> None:
    report = validate(_chain(), registry)
    assert report.ok, report.render()


def test_unknown_module_is_rejected_with_a_suggestion(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[Node(node_id="osc", module_id="gen.osc.bandlimitd")],
        exports={"out": ("osc", "out")},
    )
    report = validate_graph(graph, registry)
    assert "GRAPH-UNKNOWN-MODULE" in _rules(report)
    text = report.render()
    assert "gen.osc.bandlimited" in text, "Die Meldung muss eine Korrektur vorschlagen"


def test_missing_port_names_the_available_ones(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="osc", module_id="gen.osc.bandlimited"),
            Node(node_id="clip", module_id="prc.util.softclip"),
        ],
        edges=[Edge(src=("osc", "gibtsnicht"), dst=("clip", "in"), kind=PortType.AUDIO)],
        exports={"out": ("clip", "out")},
    )
    report = validate_graph(graph, registry)
    assert "GRAPH-NO-SUCH-PORT" in _rules(report)
    assert "'out'" in report.render()


def test_parameter_outside_safe_range_is_rejected(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[Node(node_id="flt", module_id="prc.filter.svf_morph", params={"resonance": 5.0})],
        exports={"out": ("flt", "out")},
    )
    report = validate_graph(graph, registry, check_required_inputs=False)
    assert "GRAPH-PARAM-RANGE" in _rules(report)
    assert "0.98" in report.render(), "Die Meldung muss den sicheren Bereich nennen"


def test_required_input_must_be_connected(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[Node(node_id="flt", module_id="prc.filter.svf_morph")],
        exports={"out": ("flt", "out")},
    )
    assert "GRAPH-MISSING-INPUT" in _rules(validate_graph(graph, registry))


def test_graph_without_export_is_rejected(registry: Registry) -> None:
    graph = PatchGraph(level=1, nodes=[Node(node_id="osc", module_id="gen.osc.bandlimited")])
    assert "GRAPH-NO-EXPORT" in _rules(validate_graph(graph, registry))


def test_ambiguous_fan_in_on_control_port(registry: Registry) -> None:
    """Zwei Steuerquellen an einem Eingang sind nicht eindeutig; Audio schon."""
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="lfo1", module_id="mod.lfo.slow_sine"),
            Node(node_id="lfo2", module_id="mod.lfo.slow_sine"),
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
            Node(node_id="osc", module_id="gen.osc.bandlimited"),
        ],
        edges=[
            Edge(src=("osc", "out"), dst=("flt", "in"), kind=PortType.AUDIO),
            Edge(src=("lfo1", "out"), dst=("flt", "cutoff"), kind=PortType.CTRL),
            Edge(src=("lfo2", "out"), dst=("flt", "cutoff"), kind=PortType.CTRL),
        ],
        exports={"out": ("flt", "out")},
    )
    assert "GRAPH-AMBIGUOUS-FAN-IN" in _rules(validate_graph(graph, registry))


# ---------------------------------------------------------------------------
# Rueckkopplung
# ---------------------------------------------------------------------------


def test_feedback_edge_without_damping_is_rejected_at_construction() -> None:
    """Akzeptanzkriterium: Feedback ohne damping wird abgelehnt."""
    with pytest.raises(ValidationError, match="ohne Daempfung"):
        Edge(src=("a", "out"), dst=("b", "in"), kind=PortType.AUDIO, is_feedback=True)


def test_damping_without_feedback_flag_is_rejected() -> None:
    with pytest.raises(ValidationError, match="nicht als"):
        Edge(src=("a", "out"), dst=("b", "in"), kind=PortType.AUDIO, damping=0.5)


def test_damping_at_or_above_limit_is_rejected(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
            Node(node_id="dc", module_id="prc.util.dcblock"),
            Node(node_id="clip", module_id="prc.util.softclip"),
        ],
        edges=[
            Edge(src=("flt", "out"), dst=("dc", "in"), kind=PortType.AUDIO),
            Edge(src=("dc", "out"), dst=("clip", "in"), kind=PortType.AUDIO),
            Edge(
                src=("clip", "out"),
                dst=("flt", "in"),
                kind=PortType.AUDIO,
                is_feedback=True,
                damping=0.99,
            ),
        ],
        exports={"out": ("clip", "out")},
    )
    assert "GRAPH-FEEDBACK-DAMPING" in _rules(validate_graph(graph, registry))


def test_implicit_cycle_is_rejected(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="a", module_id="prc.util.dcblock"),
            Node(node_id="b", module_id="prc.util.softclip"),
        ],
        edges=[
            Edge(src=("a", "out"), dst=("b", "in"), kind=PortType.AUDIO),
            Edge(src=("b", "out"), dst=("a", "in"), kind=PortType.AUDIO),
        ],
        exports={"out": ("b", "out")},
    )
    report = validate_graph(graph, registry)
    assert "GRAPH-CYCLE" in _rules(report)
    assert "is_feedback" in report.render(), "Die Meldung muss den Ausweg nennen"


def test_feedback_loop_needs_dcblock_and_softclip(registry: Registry) -> None:
    """L1-T2: eine Schleife ohne Schutzmodule ist nicht zulaessig."""
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
            Node(node_id="sat", module_id="prc.saturation.tape"),
        ],
        edges=[
            Edge(src=("flt", "out"), dst=("sat", "in"), kind=PortType.AUDIO),
            Edge(
                src=("sat", "out"),
                dst=("flt", "in"),
                kind=PortType.AUDIO,
                is_feedback=True,
                damping=0.6,
            ),
        ],
        exports={"out": ("sat", "out")},
    )
    report = validate_level(graph, registry)
    assert "L1-T2" in _rules(report)
    assert "dcblock" in report.render()


# ---------------------------------------------------------------------------
# Die Analyse-Sperre
# ---------------------------------------------------------------------------


def test_analysis_may_not_drive_a_parameter_directly(registry: Registry) -> None:
    """Akzeptanzkriterium: analysis -> param direkt wird erklaerend abgelehnt."""
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="osc", module_id="gen.osc.bandlimited"),
            Node(node_id="ana", module_id="ana.spec.centroid_flux"),
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
        ],
        edges=[
            Edge(src=("osc", "out"), dst=("ana", "in"), kind=PortType.AUDIO),
            Edge(src=("osc", "out"), dst=("flt", "in"), kind=PortType.AUDIO),
            Edge(src=("ana", "centroid"), dst=("flt", "cutoff"), kind=PortType.ANALYSIS),
        ],
        exports={"out": ("flt", "out")},
    )
    report = validate_graph(graph, registry)
    assert "PORT-ANALYSIS-DIRECT" in _rules(report)
    text = report.render()
    assert "mod.map." in text, "Die Meldung muss den vorgeschriebenen Umweg nennen"


def test_analysis_through_a_mapper_is_allowed(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[
            Node(node_id="osc", module_id="gen.osc.bandlimited"),
            Node(node_id="ana", module_id="ana.spec.centroid_flux"),
            Node(node_id="map", module_id="mod.map.linear"),
            Node(node_id="flt", module_id="prc.filter.svf_morph"),
        ],
        edges=[
            Edge(src=("osc", "out"), dst=("ana", "in"), kind=PortType.AUDIO),
            Edge(src=("osc", "out"), dst=("flt", "in"), kind=PortType.AUDIO),
            Edge(src=("ana", "centroid"), dst=("map", "in"), kind=PortType.ANALYSIS),
            Edge(src=("map", "out"), dst=("flt", "cutoff"), kind=PortType.CTRL),
        ],
        exports={"out": ("flt", "out")},
    )
    report = validate(graph, registry)
    assert report.ok, report.render()


# ---------------------------------------------------------------------------
# Ebenengrammatik
# ---------------------------------------------------------------------------


def test_l1_rejects_a_level2_module(registry: Registry) -> None:
    graph = PatchGraph(
        level=1,
        nodes=[Node(node_id="drone", module_id="gen.drone.wavetable_resonator")],
        exports={"out": ("drone", "out")},
    )
    report = validate_level(graph, registry)
    assert "L1-M1" in _rules(report)


def test_l2_rejects_space_modules(registry: Registry) -> None:
    """Raum gehoert nach L5/L6 — auf L2 ist er eine Ebenengrenzverletzung."""
    graph = PatchGraph(
        level=2,
        nodes=[
            Node(node_id="drone", module_id="gen.drone.wavetable_resonator"),
            Node(node_id="verb", module_id="spc.reverb.fdn32"),
        ],
        edges=[Edge(src=("drone", "out"), dst=("verb", "in"), kind=PortType.AUDIO)],
        exports={"out": ("verb", "out")},
    )
    report = validate_level(graph, registry)
    assert "L2-M2" in _rules(report)


def test_l2_requires_a_voice_with_macros(registry: Registry) -> None:
    graph = PatchGraph(
        level=2,
        nodes=[Node(node_id="osc", module_id="gen.osc.bandlimited")],
        exports={"out": ("osc", "out")},
    )
    report = validate_level(graph, registry)
    assert "L2-T2" in _rules(report)


def test_l2_allows_exactly_one_output(registry: Registry) -> None:
    graph = PatchGraph(
        level=2,
        nodes=[Node(node_id="drone", module_id="gen.drone.wavetable_resonator")],
        exports={"out": ("drone", "out"), "zweite": ("drone", "env_follow")},
    )
    report = validate_level(graph, registry)
    assert "L2-T1" in _rules(report)


def test_unimplemented_level_warns_instead_of_passing_silently(registry: Registry) -> None:
    graph = PatchGraph(
        level=7,
        nodes=[Node(node_id="osc", module_id="gen.osc.bandlimited")],
        exports={"out": ("osc", "out")},
    )
    report = validate_level(graph, registry)
    assert "GRAMMAR-NOT-IMPLEMENTED" in _rules(report)
    assert report.ok, "Eine fehlende Grammatik ist eine Warnung, kein Fehler"


# ---------------------------------------------------------------------------
# Nebensachen
# ---------------------------------------------------------------------------


def test_graphviz_export_mentions_every_node(registry: Registry) -> None:
    dot = to_graphviz(_chain(), registry)
    assert dot.startswith("digraph")
    for node_id in ("osc", "flt", "clip"):
        assert f'"{node_id}"' in dot


def test_cpu_budget_is_enforced(registry: Registry) -> None:
    report = validate_graph(_chain(), registry, cpu_budget=0.5)
    assert "GRAPH-CPU-BUDGET" in _rules(report)
    assert "Eskalation" in report.render(), "Die Meldung muss den Ausweg nach oben nennen"
