"""Dynamic Hybrid Synthesizer Recombination Engine.

Ermöglicht die freie Rekombination von Oszillatorkernen, Filtertopologien,
Shapern, Hüllkurven und Raummodulatoren zur dynamischen Erzeugung von
tausenden hybriden Synthesizer-Varianten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import random

from au.core.seeds import SeedPath


class OscCore(StrEnum):
    SAW_ANALOG = "saw_analog"
    PULSE_WIDTH = "pulse_width"
    DUAL_FM = "dual_fm"
    FOUR_FM = "four_fm"
    ADDITIVE_BANKS = "additive_banks"
    WAVETABLE = "wavetable"
    KARPLUS_STRONG = "karplus_strong"
    MODAL_RESONATOR = "modal_resonator"
    FORMANT_VOWEL = "formant_vowel"
    GRANULAR_CLOUD = "granular_cloud"
    STOCHASTIC_DUST = "stochastic_dust"


class FilterTopology(StrEnum):
    MOOG_LADDER = "moog_ladder"
    JUNO_BIQUAD = "juno_biquad"
    SALLEN_KEY = "sallen_key"
    STATE_VARIABLE = "state_variable"
    FORMANT_BANK = "formant_bank"
    NONE = "none"


class ShaperType(StrEnum):
    NONE = "none"
    WESTCOAST_FOLD = "westcoast_fold"
    TANH_SATURATION = "tanh_saturation"
    CHEBYSHEV_DRIVE = "chebyshev_drive"


@dataclass(frozen=True, slots=True)
class HybridSynthTopology:
    topology_id: str
    osc_core: OscCore
    filter_top: FilterTopology
    shaper: ShaperType
    detune_cents: float = 12.0
    sub_osc_gain: float = 0.3
    chorus_depth: float = 0.4
    reverb_mix: float = 0.35


def generate_hybrid_recombination(
    role: str,
    seed: SeedPath,
) -> HybridSynthTopology:
    """Rekombiniert zufallsbasiert (aber deterministisch durch den SeedPath) einen hybriden Synthesizer."""
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))

    osc = rng.choice(list(OscCore))
    filt = rng.choice(list(FilterTopology))
    shaper = rng.choice(list(ShaperType))

    detune = round(rng.uniform(2.0, 25.0), 1)
    sub_gain = round(rng.uniform(0.0, 0.6), 2)
    chorus = round(rng.uniform(0.1, 0.8), 2)
    reverb = round(rng.uniform(0.1, 0.6), 2)

    return HybridSynthTopology(
        topology_id=f"hybrid_{role}_{int(seed.value & 0xFFFF)}",
        osc_core=osc,
        filter_top=filt,
        shaper=shaper,
        detune_cents=detune,
        sub_osc_gain=sub_gain,
        chorus_depth=chorus,
        reverb_mix=reverb,
    )
