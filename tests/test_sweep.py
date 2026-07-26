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

_VOICES = ["gen.drone.wavetable_resonator", "gen.object.modal_bell"]


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
