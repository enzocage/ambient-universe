from __future__ import annotations

from au.core.manifest import Guarantees, MacroSpec, MacroTarget, ModuleManifest, ParamSpec
from au.core.ports import Port, PortSet, PortType
from au.selection.sound_priority import PriorityTier, prioritize_voice_modules


def _module(module_id: str, *, roles: list[str], band: tuple[float, float]) -> ModuleManifest:
    full_id = f"gen.test.{module_id}"
    return ModuleManifest(
        id=full_id,
        version="1.0.0",
        level=2,
        category="generator",
        family="test",
        display_name=full_id,
        suggested_roles=roles,
        guarantees=Guarantees(band_hz=band),
        ports=PortSet(outputs=[Port(name="out", type=PortType.AUDIO, channels=2)]),
        params={"param_main": ParamSpec(min=0.0, max=10.0, default=1.0)},
        macros={
            m: MacroSpec(maps={"param_main": MacroTarget(start=0.0, end=1.0)})
            for m in ["body", "brightness", "material", "motion", "noise_ratio"]
        },
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
    assert len(scores) == 2
    assert scores[0].module_id == "gen.test.bass_voice"
    assert scores[0].tier in (PriorityTier.S, PriorityTier.A)


def test_selection_is_deterministic_and_rejects_unrenderable_modules() -> None:
    module = _module("stable", roles=["arpeggiator"], band=(300.0, 3500.0))
    first = prioritize_voice_modules([module], role="arpeggiator", band_hz=(200.0, 2000.0))
    second = prioritize_voice_modules([module], role="arpeggiator", band_hz=(200.0, 2000.0))
    assert [s.module_id for s in first] == [s.module_id for s in second]
    assert first[0].score > 0.5

