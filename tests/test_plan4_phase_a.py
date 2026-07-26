"""Plan 4 Phase A Quality Gate Test Suite.

Verifiziert:
1. RhythmIntent Parser erkennt rhythmische Prompts zuverlässig.
2. Blueprint reserviert zwingend bass_sequence, arpeggiator und subtle_percussive_background.
3. Rhythmische Pattern (euclid) werden nicht zu poisson überschrieben.
4. Rhythmusstems (bass, arpeggio_motif, percussion) werden sauber getrennt gerendert.
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf

from au.agents.dna_agent import generate_dna
from au.core.registry import Registry, load_registry
from au.dsl.rhythm_intent import parse_rhythm_intent
from au.integrator.blueprint import derive_blueprint
from au.integrator.compose import compose_track


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


def test_rhythm_intent_parser() -> None:
    prompt = "Rhythmisch und sequenziert, tiefer bewegter Bass, warmes polymetrisches Arpeggio, subtile perkussive Impulse"
    intent = parse_rhythm_intent(prompt)
    assert intent.requires_bass
    assert intent.requires_arpeggio
    assert intent.requires_percussion


def test_blueprint_rhythm_roles_guaranteed() -> None:
    prompt = "Rhythmisch und sequenziert, tiefer bewegter Bass, warmes polymetrisches Arpeggio, subtile perkussive Impulse"
    dna = generate_dna(prompt, seed_root=42).dna
    blueprint = derive_blueprint(dna)
    roles = [slot.role for slot in blueprint.role_slots]
    assert "bass_sequence" in roles
    assert "arpeggiator" in roles
    assert "subtle_percussive_background" in roles


def test_compose_track_rhythm_patterns_and_stems(registry: Registry, tmp_path: Path) -> None:
    prompt = "Rhythmisch und sequenziert, tiefer bewegter Bass, warmes polymetrisches Arpeggio, subtile perkussive Impulse"
    res = compose_track(prompt, tmp_path / "plan4_track", duration_s=15.0, registry=registry, seed_root=123)

    # Verifiziere Pattern-Arten in den Rezepten
    rhythmic_patterns = {r.pattern_kind for r in res.recipes.values()}
    assert "euclid" in rhythmic_patterns, f"Fehlendes euklidisches Pattern in Rezepten: {rhythmic_patterns}"

    # Verifiziere Stems
    stem_files = list((tmp_path / "plan4_track").glob("stem_*.wav"))
    stem_names = [f.name for f in stem_files]
    assert any("bass" in name for name in stem_names), f"Fehlendes Bass-Stem: {stem_names}"
    assert any("arpeggio" in name for name in stem_names), f"Fehlendes Arpeggio-Stem: {stem_names}"
    assert any("percussion" in name for name in stem_names), f"Fehlendes Percussion-Stem: {stem_names}"

    # Verifiziere Signalenergie in Bass- und Arpeggio-Stems
    for f in stem_files:
        if "bass" in f.name or "arpeggio" in f.name:
            data, sr = sf.read(str(f), dtype="float64")
            rms = float(np.sqrt(np.mean(data**2)))
            assert rms > 0.0001, f"Stem {f.name} ist stumm (RMS={rms})"
