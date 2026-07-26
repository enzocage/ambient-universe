"""Procedural Synthesizer Factory (SynthFactory).

Generiert dynamisch hunderte maßgeschneiderte Level-2 Synthesizer-Topologien
und Graph-Definitionen durch kombinatorische Synthese-Kopplung.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import random

from au.core.seeds import SeedPath


class SynthCategory(StrEnum):
    ANALOG_VINTAGE = "analog_vintage"
    FM_6OPERATOR = "fm_6operator"
    ADDITIVE_PARTIALS = "additive_partials"
    CHAOS_ATTRACTOR = "chaos_attractor"
    PHYSICAL_MODEL = "physical_model"
    GRANULAR_TAPE = "granular_tape"
    PHASE_DISTORTION = "phase_distortion"
    FORMANT_VOCAL = "formant_vocal"


@dataclass(frozen=True, slots=True)
class ProceduralSynthSpec:
    synth_id: str
    category: SynthCategory
    display_name: str
    roles: tuple[str, ...]
    osc_count: int = 2
    filter_type: str = "ladder"
    mod_source: str = "lfo_sine"
    reverb_amount: float = 0.4


def generate_procedural_synth(
    role: str,
    seed: SeedPath,
) -> ProceduralSynthSpec:
    """Erzeugt prozedural eine maßgeschneiderte Synthesizer-Spezifikation."""
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))
    cat = rng.choice(list(SynthCategory))

    categories_names = {
        SynthCategory.ANALOG_VINTAGE: "Analog Vintage Synth",
        SynthCategory.FM_6OPERATOR: "6-Op FM Synthesis Engine",
        SynthCategory.ADDITIVE_PARTIALS: "32-Partial Additive Bank",
        SynthCategory.CHAOS_ATTRACTOR: "Non-Linear Chaos Attractor",
        SynthCategory.PHYSICAL_MODEL: "Physical Acoustic Resonator",
        SynthCategory.GRANULAR_TAPE: "Granular Softcut Loop Engine",
        SynthCategory.PHASE_DISTORTION: "Casio Phase Distortion Engine",
        SynthCategory.FORMANT_VOCAL: "Formant Vocal Choir Engine",
    }

    return ProceduralSynthSpec(
        synth_id=f"proc_{cat}_{role}_{int(seed.value & 0xFFFF)}",
        category=cat,
        display_name=f"Procedural {categories_names[cat]}",
        roles=(role,),
        osc_count=rng.randint(2, 6),
        filter_type=rng.choice(["ladder", "biquad", "sallen_key", "formant"]),
        mod_source=rng.choice(["lfo_sine", "random_drift", "brownian_walk"]),
        reverb_amount=round(rng.uniform(0.2, 0.6), 2),
    )
