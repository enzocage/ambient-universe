"""Large deterministic preset bank built from original parameter data.

The bank deliberately stores *parameters*, not copied vendor sound files.  This
keeps redistribution safe while still giving the composer a VSTi-like browser.
Each profile names the renderable backend it uses and can later be replaced by
an external VST adapter without changing compositions.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256

from pydantic import BaseModel, ConfigDict, Field


@dataclass(frozen=True, slots=True)
class SynthProfile:
    id: str
    name: str
    backend_module_id: str
    family: str
    source: str = "internal-original"
    license: str = "original-parameter-data"


class ParameterPreset(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    id: str
    name: str
    synth_id: str
    backend_module_id: str
    family: str
    roles: tuple[str, ...]
    tags: tuple[str, ...]
    parameters: dict[str, float | str] = Field(default_factory=dict)
    macros: dict[str, float]
    source: str = "internal-original"
    license: str = "original-parameter-data"
    source_url: str | None = None


_BACKENDS = (
    ("aurora", "Aurora Wavetable", "gen.synth.wavetable_morph", "wavetable"),
    ("ember", "Ember Ladder", "gen.synth.ladder_bass", "analog"),
    ("frost", "Frost FM", "gen.fm.six_operator_pad", "fm"),
    ("glass", "Glass Partials", "gen.additive.bell_partials", "additive"),
    ("tide", "Tidal Resonator", "gen.drone.wavetable_resonator", "resonator"),
    ("moss", "Moss Granular", "gen.texture.grain_cloud_dense", "granular"),
    ("cinder", "Cinder Fold", "gen.synth.wavefolder", "waveshaping"),
    ("halo", "Halo Choir", "gen.vocal.choir_vowels", "vocal"),
    ("orbit", "Orbit Vector", "gen.synth.vector_pad", "vector"),
    ("quartz", "Quartz Bell", "gen.fm.bell_chime", "fm"),
    ("reed", "Reed Pipe", "gen.physical.flute_pipe", "physical"),
    ("plume", "Plume Bow", "gen.physical.bowed_string", "physical"),
    ("iron", "Iron Pan", "gen.physical.steel_pan", "physical"),
    ("rain", "Rain Whisper", "gen.vocal.whisper_noise", "vocal"),
    ("lowtide", "Low Tide Sub", "gen.synth.minimoog_sub", "subtractive"),
    ("acid", "Acid Ember", "gen.synth.tb303_acid_bass", "acid"),
    ("opal", "Opal PD", "gen.synth.casio_cz_pd", "phase-distortion"),
    ("vector3", "Vector 3D", "gen.synth.vector_3d_pad", "vector"),
    ("organ", "Organ Air", "gen.additive.organ_partials", "additive"),
    ("drawbar", "Drawbar Cloud", "gen.additive.drawbar_bank", "additive"),
    ("lorenz", "Lorenz Bloom", "gen.chaos.lorenz_attractor", "chaos"),
    ("rossler", "Rossler Drift", "gen.chaos.rossler_chaos", "chaos"),
    ("logistic", "Logistic Pulse", "gen.chaos.logistic_map", "chaos"),
    ("chua", "Chua Voltage", "gen.chaos.chua_circuit", "chaos"),
    ("reverse", "Reverse Tape", "gen.texture.reverse_grain", "tape"),
    ("pitchgrain", "Pitch Grain", "gen.texture.pitch_shift_grain", "granular"),
    ("softcut", "Softcut Memory", "gen.texture.softcut_tape", "tape"),
    ("soprano", "Soprano Formant", "gen.vocal.soprano_formant", "formant"),
    ("tenor", "Tenor Formant", "gen.vocal.tenor_formant", "formant"),
    ("cheby", "Chebyshev Bank", "gen.synth.chebyshev_bank", "waveshaping"),
)

_ARCHETYPES = (
    "dawn", "pulse", "veil", "orbit", "anchor", "bloom", "fracture", "drift", "choir", "spark", "horizon", "tension",
    "mist", "glow", "shimmer", "weight", "memory", "current", "shadow", "prism", "flare", "grain", "lift", "undertow",
    "monolith", "ripple", "glass", "ember", "sleep", "signal", "cavern", "silver", "dust", "field", "afterimage", "threshold",
)
_ROLES = ("foundation", "moving_pad", "arpeggiator", "bass_sequence", "harmonic_drone", "atmospheric_noise")


class PresetCatalog:
    def __init__(self, presets: tuple[ParameterPreset, ...], profiles: tuple[SynthProfile, ...]):
        self.presets, self.profiles = presets, profiles

    def __len__(self) -> int:
        return len(self.presets)

    def for_synth(self, synth_id: str) -> tuple[ParameterPreset, ...]:
        return tuple(p for p in self.presets if p.synth_id == synth_id)

    def for_role(self, role: str, limit: int | None = None) -> tuple[ParameterPreset, ...]:
        found = tuple(p for p in self.presets if role in p.roles)
        return found if limit is None else found[:limit]

    def select(self, seed: int, role: str, ratings: dict[str, float] | None = None) -> ParameterPreset:
        options = self.for_role(role) or self.presets
        if ratings:
            # Persönlicher Geschmack wirkt als weiches Signal: nur bereits
            # bewertete Presets werden vorgezogen, gleich gute bleiben seed-
            # stabil divers, damit der Komponist nicht in einem Klang festhängt.
            options = tuple(sorted(options, key=lambda p: (-ratings.get(p.id, 0.0), p.id)))
        return options[seed % len(options)]


@lru_cache(maxsize=1)
def get_preset_catalog() -> PresetCatalog:
    profiles = tuple(SynthProfile(f"synth.{key}", name, backend, family) for key, name, backend, family in _BACKENDS)
    presets: list[ParameterPreset] = []
    for si, profile in enumerate(profiles):
        for ai, archetype in enumerate(_ARCHETYPES):
            digest = sha256(f"{profile.id}:{archetype}".encode()).digest()
            values = [round(b / 255, 4) for b in digest[:5]]
            role = _ROLES[(si + ai) % len(_ROLES)]
            presets.append(ParameterPreset(
                id=f"preset.{profile.id}.{archetype}", name=f"{profile.name} — {archetype.title()}",
                synth_id=profile.id, backend_module_id=profile.backend_module_id, family=profile.family,
                roles=(role, _ROLES[(si + ai + 2) % len(_ROLES)]),
                tags=(profile.family, archetype, "original", "vsti-style"),
                parameters={"character": values[0], "cutoff": values[1], "resonance": values[2], "motion": values[3]},
                macros={"brightness": values[0], "body": values[1], "noise_ratio": values[2], "motion": values[3], "material": values[4]},
            ))
    return PresetCatalog(tuple(presets), profiles)
