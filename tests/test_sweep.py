"""Phase-2-Akzeptanz: Makro-Sweep-Test.

Aus plan.md Phase 2: "Makro-Sweep (0->1 in 30s) fuer alle 6 Stimmen: 0 Klicks,
0 Clips, kein DC". Der Katalog hat aktuell zwei vollstaendige L2-Stimmen;
dieser Test deckt beide mit allen ihren Makros ab.
"""

from __future__ import annotations

import pytest

from au.core.registry import Registry, load_registry
from au.render.sweep import sweep_macro

pytestmark = [pytest.mark.audio, pytest.mark.slow]

_VOICES: list[str] = [
    "gen.drone.wavetable_resonator",
    "gen.object.modal_bell",
    "gen.drone.sub_bass",
    "gen.texture.granular_cloud",
    "gen.arpeggio.pulse_sequence",
    "gen.fm.dual_operator",
    "gen.additive.harmonic_partials",
    "gen.physical.plucked_string",
    "gen.vocal.formant_pad",
    "gen.spectral.phase_freeze",
    "gen.synth.wavefolder",
    "gen.noise.stochastic_trigger",
    "gen.synth.juno_chorus",
    "gen.synth.prophet_lead",
    "gen.synth.ladder_bass",
    "gen.synth.biquad_sweep",
    "gen.synth.sallen_key",
    "gen.synth.vector_pad",
    "gen.synth.wavetable_morph",
    "gen.synth.folding_drone",
    "gen.synth.chebyshev_drive",
    "gen.fm.four_operator",
    "gen.fm.feedback_drone",
    "gen.fm.bell_chime",
    "gen.fm.phase_mod_pad",
    "gen.additive.organ_partials",
    "gen.additive.bell_partials",
    "gen.spectral.spectral_blur",
    "gen.spectral.frequency_shifter",
    "gen.physical.bowed_string",
    "gen.physical.marimba_bar",
    "gen.physical.flute_pipe",
    "gen.physical.karplus_ensemble",
    "gen.vocal.choir_vowels",
    "gen.vocal.whisper_noise",
    "gen.texture.grain_cloud_dense",
    "gen.noise.pink_crackle",
    "gen.noise.brownian_drift",
    "gen.arpeggio.euclidean_pulse",
    "gen.arpeggio.random_walk_seq",
]




@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


@pytest.mark.parametrize("module_id", _VOICES)
@pytest.mark.parametrize("macro", ["brightness", "body", "noise_ratio", "motion", "material"])
def test_macro_sweep_is_artifact_free(module_id: str, macro: str, registry: Registry) -> None:
    result = sweep_macro(module_id, macro, registry, duration=30.0)
    assert result.ok, "\n".join(result.problems())


@pytest.mark.parametrize("module_id", _VOICES)
def test_voice_is_audible_at_default_settings(module_id: str, registry: Registry) -> None:
    """Ein bestandener Sweep bei Stille waere ein falsches Gruen."""
    result = sweep_macro(module_id, "brightness", registry, duration=5.0)
    assert result.peak_level > 0.01, f"{module_id} ist praktisch stumm ({result.peak_level})"
    assert result.peak_level < 0.9, f"{module_id} ist zu laut ({result.peak_level})"


@pytest.mark.parametrize("module_id", [*_VOICES, "gen.noise.colored"])
def test_noise_driven_voices_are_deterministic_across_separate_renders(
    module_id: str, registry: Registry, tmp_path
) -> None:
    """Regressionstest fuer einen echten Fund: BrownNoise/PinkNoise/WhiteNoise
    ziehen ohne explizites RandSeed.ir() aus scsynths eigenem, node-ID-
    abhaengigen RNG-Strom statt aus unserer Seed-Hierarchie. Zwei getrennte
    NRT-Renderlaeufe mit identischem Rezept erzeugten dadurch nachweislich
    verschiedenes Audio (gefunden ueber den Determinismustest von
    au.integrator.compose) -- der Compiler setzt seither RandSeed.ir() beim
    Aufbau jeder SynthDef (au/render/compiler.py)."""
    from au.core.seeds import SeedPath
    from au.render.voice import render_graph, single_voice_graph

    seed = SeedPath.root(99).child("noise_determinism_test")
    hashes = set()
    for i in range(3):
        r, _ = render_graph(
            single_voice_graph(module_id),
            registry,
            tmp_path / f"n_{i}.wav",
            duration=6.0,
            seed=seed,
            name=f"det_{module_id}_{i}",
        )
        hashes.add(r.audio_sha256)
    assert len(hashes) == 1, (
        f"{module_id}: {len(hashes)} verschiedene Fingerabdruecke bei gleichem Seed"
    )
