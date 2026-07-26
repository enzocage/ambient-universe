"""ToneDNA — Klang-Identitäts- und Rekombinationsmodell (Plan 3, Paragraph 3.1).

Modelliert die klangliche DNA einer Stimme unabhängig von bloßen Parameter-Presets.
Ermöglicht kontrollierte Mutationen, Rekombinationen und Vergleiche.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from au.core.seeds import SeedPath


class SourceFamily(StrEnum):
    ANALOG_WAVEFOLDED = "analog_wavefolded"
    FM_ADDITIVE = "fm_additive"
    RESONANT_PHYSICAL = "resonant_physical"
    VOCAL_SPECTRAL = "vocal_spectral"
    GRANULAR_STOCHASTIC = "granular_stochastic"
    RHYTHMIC_PULSE = "rhythmic_pulse"
    SUB_FOUNDATION = "sub_foundation"


@dataclass(frozen=True, slots=True)
class EnvelopeProfile:
    attack_s: float = 2.0
    decay_s: float = 3.0
    sustain_level: float = 0.7
    release_s: float = 4.0


@dataclass(frozen=True, slots=True)
class SpatialIdentity:
    stereo_width: float = 0.5
    distance: float = 0.3
    reverb_send: float = 0.3
    delay_send: float = 0.2


@dataclass(frozen=True, slots=True)
class ToneDNA:
    """Die klangliche DNA einer einzelnen Stimme."""

    dna_id: str
    source_family: SourceFamily
    source_module: str
    spectral_profile: float = 0.5  # 0.0 = dunkel/tief, 1.0 = hell/obertonreich
    transient_articulation: float = 0.2  # 0.0 = weich/geglättet, 1.0 = perkussiv/zackig
    envelope: EnvelopeProfile = field(default_factory=EnvelopeProfile)
    modulation_character: float = 0.3  # 0.0 = statisch, 1.0 = stochastisch/lebhaft
    harmonicity_noisiness: float = 0.1  # 0.0 = purer Ton, 1.0 = Rauschen/Grit
    register_density: float = 0.5  # 0.0 = ausgedünnt/tief, 1.0 = dicht/hoch
    spatial: SpatialIdentity = field(default_factory=SpatialIdentity)
    evolution_budget: float = 0.8  # Budget für zeitliche Parameterbewegungen

    def mutate(self, seed: SeedPath, mutation_rate: float = 0.2) -> ToneDNA:
        """Erzeugt eine kontrollierte Mutation der Klang-DNA unter Wahrung des SeedPaths."""
        val = int(seed.value & 0xFFFF_FFFF)
        shift_a = ((val % 100) / 100.0 - 0.5) * mutation_rate
        shift_b = (((val // 100) % 100) / 100.0 - 0.5) * mutation_rate

        return ToneDNA(
            dna_id=f"{self.dna_id}_mut",
            source_family=self.source_family,
            source_module=self.source_module,
            spectral_profile=max(0.0, min(1.0, self.spectral_profile + shift_a)),
            transient_articulation=max(0.0, min(1.0, self.transient_articulation + shift_b)),
            envelope=EnvelopeProfile(
                attack_s=max(0.05, self.envelope.attack_s * (1.0 + shift_a)),
                decay_s=max(0.1, self.envelope.decay_s * (1.0 + shift_b)),
                sustain_level=max(0.1, min(1.0, self.envelope.sustain_level + shift_a * 0.5)),
                release_s=max(0.2, self.envelope.release_s * (1.0 + shift_b)),
            ),
            modulation_character=max(0.0, min(1.0, self.modulation_character + shift_b)),
            harmonicity_noisiness=max(0.0, min(1.0, self.harmonicity_noisiness + shift_a * 0.5)),
            register_density=max(0.0, min(1.0, self.register_density + shift_a)),
            spatial=SpatialIdentity(
                stereo_width=max(0.1, min(1.0, self.spatial.stereo_width + shift_b * 0.5)),
                distance=max(0.0, min(1.0, self.spatial.distance + shift_a * 0.5)),
                reverb_send=max(0.05, min(0.9, self.spatial.reverb_send + shift_b * 0.5)),
                delay_send=max(0.0, min(0.8, self.spatial.delay_send + shift_a * 0.5)),
            ),
            evolution_budget=self.evolution_budget,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "dna_id": self.dna_id,
            "source_family": str(self.source_family),
            "source_module": self.source_module,
            "spectral_profile": round(self.spectral_profile, 3),
            "transient_articulation": round(self.transient_articulation, 3),
            "modulation_character": round(self.modulation_character, 3),
            "harmonicity_noisiness": round(self.harmonicity_noisiness, 3),
            "register_density": round(self.register_density, 3),
            "evolution_budget": round(self.evolution_budget, 3),
        }
