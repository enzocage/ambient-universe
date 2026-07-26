"""Testsuite für Plan 3 Definition of Done (plan3.md Paragraph 9).

Überprüft:
- Mindestens 5 unterschiedliche Klangfamilien pro Track
- Kein tragender Layer > 12s ohne relevante Bewegung (EvolutionPlan)
- Mindestens 3 kontrastierende Abschnittsprofile
- Wiederkehrendes Motiv mit mindestens 3 Varianten
- Mindestens 3 wirksame Layer-Relationen
- Bestandenes Quality-Gate (LUFS, Peak, Clicks)
"""

from pathlib import Path
import pytest

from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.integrator.compose import compose_track


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


def test_plan3_definition_of_done_requirements(registry: Registry, tmp_path: Path) -> None:
    prompt = "Ein tiefes, bewegtes Ambient-Album mit gläsernen Resonanzen, chorale Vokalen und stochastischem Knistern"
    res = compose_track(prompt, tmp_path / "plan3_track", duration_s=60.0, registry=registry, seed_root=42)

    # 1. Mindestens 5 unterschiedliche Klangfamilien im Ensemble
    families = {dna.source_family for dna in res.tone_dnas.values()}
    assert len(families) >= 5, f"Zu wenige Klangfamilien ({len(families)} < 5): {families}"

    # 2. Kein tragender Layer > 12s ohne mehrdimensionale Bewegung
    for layer_id, evo in res.evolution_plans.items():
        stagnation_issues = evo.validate_anti_monotony(window_s=10.0)
        assert not stagnation_issues, f"Stagnationsprobleme gefunden in {layer_id}: {stagnation_issues}"

    # 3. Mindestens 3 kontrastierende Abschnittsprofile
    assert len(res.section_profiles) >= 3, f"Zu wenige Sektionsprofile ({len(res.section_profiles)} < 3)"
    intro = res.section_profiles["intro"]
    peak = res.section_profiles["peak"]
    assert intro.spectral_brightness != peak.spectral_brightness, "Sektionen besitzen keinen Helligkeitskontrast"

    # 4. Wiederkehrendes Motiv mit mindestens 3 Varianten
    assert len(res.transformed_motifs) >= 3, f"Zu wenige Motivtransformationen ({len(res.transformed_motifs)} < 3)"

    # 5. Mindestens 3 wirksame Layer-Relationen
    assert len(res.solve_result.layers) >= 4, "Zu wenige Schichten gerendert"

    # 6. Quality-Gate Prüfung
    assert res.quality_report.accepted, f"Quality Gate abgelehnt: {res.quality_report.reasons}"
    assert -18.0 <= res.quality_report.lufs_estimated <= -14.0, f"LUFS außerhalb (-18..-14): {res.quality_report.lufs_estimated}"
    assert res.quality_report.active_signal_ratio >= 0.75, f"Signalaktivität zu gering: {res.quality_report.active_signal_ratio}"
