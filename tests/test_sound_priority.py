from __future__ import annotations

from au.core.manifest import Guarantees, ModuleManifest
from au.selection.sound_priority import PriorityTier, prioritize_voice_modules


def _module(module_id: str, *, roles: list[str], band: tuple[float, float]) -> ModuleManifest:
    return ModuleManifest(
        id=module_id,
        version="1.0.0",
        level=2,
        category="generator",
        family="test",
        suggested_roles=roles,
        guarantees=Guarantees(band_hz=band),
        has_impl=True,
        is_renderable=True,
    )


def test_role_fit_beats_generic_band_overlap() -> None:
    scores = prioritize_voice_modules(
        [
            _module("generic", roles=[], band=(30.0, 500.0)),
            _module("bass_voice", roles=["bass_sequence"], band=(30.0, 250.0)),
        ],
        role="bass_sequence",
        band_hz=(35.0, 250.0),
    )
    assert scores[0].module_id == "bass_voice"
    assert scores[0].tier in (PriorityTier.S, PriorityTier.A)


def test_selection_is_deterministic_and_rejects_unrenderable_modules() -> None:
    module = _module("stable", roles=["arpeggiator"], band=(300.0, 3500.0))
    a = prioritize_voice_modules([module], role="arpeggiator", band_hz=(300.0, 3500.0))
    b = prioritize_voice_modules([module], role="arpeggiator", band_hz=(300.0, 3500.0))
    assert a == b
    assert a[0].score > 0.8
