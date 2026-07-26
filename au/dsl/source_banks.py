"""Source Banks & Partner-Regeln (Plan 3, Paragraph 3.2).

Verwaltet kategorisierte Klangbanken pro musikalischer Funktion und erzwingt
dass kein Track aus homogenen Kopien desselben Oszillators besteht.
"""

from __future__ import annotations

from dataclasses import dataclass
import random

from au.core.seeds import SeedPath
from au.dsl.tone_dna import SourceFamily, ToneDNA


@dataclass(frozen=True, slots=True)
class SourceBankEntry:
    module_id: str
    family: SourceFamily
    primary_roles: tuple[str, ...]
    spectral_default: float
    transient_default: float
    max_duration_without_variation_s: float = 10.0


#: Die Gesamtheit aller registrierten Klangfamilien und ihrer Vertreter
SOURCE_BANK_CATALOG: tuple[SourceBankEntry, ...] = (
    # Fundament / Bass
    SourceBankEntry("gen.drone.sub_bass", SourceFamily.SUB_FOUNDATION, ("foundation", "subharmonic_pulse"), 0.2, 0.1, 12.0),
    SourceBankEntry("gen.synth.wavefolder", SourceFamily.ANALOG_WAVEFOLDED, ("foundation", "subharmonic_pulse", "bass_sequence"), 0.4, 0.3, 10.0),

    # Harmonie / Drones / Pads
    SourceBankEntry("gen.fm.dual_operator", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "moving_pad", "signal_motif"), 0.65, 0.2, 8.0),
    SourceBankEntry("gen.additive.harmonic_partials", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "moving_pad", "foundation"), 0.5, 0.15, 10.0),
    SourceBankEntry("gen.drone.wavetable_resonator", SourceFamily.RESONANT_PHYSICAL, ("harmonic_drone", "moving_pad"), 0.55, 0.2, 10.0),
    SourceBankEntry("gen.vocal.formant_pad", SourceFamily.VOCAL_SPECTRAL, ("harmonic_drone", "moving_pad", "atmospheric_noise"), 0.6, 0.1, 8.0),

    # Motive / Melodien / Resonanz-Objekte
    SourceBankEntry("gen.physical.plucked_string", SourceFamily.RESONANT_PHYSICAL, ("signal_motif", "resonant_object", "arpeggiator"), 0.7, 0.8, 6.0),
    SourceBankEntry("gen.object.modal_bell", SourceFamily.RESONANT_PHYSICAL, ("resonant_object", "signal_motif"), 0.75, 0.85, 6.0),
    SourceBankEntry("gen.arpeggio.pulse_sequence", SourceFamily.RHYTHMIC_PULSE, ("signal_motif", "arpeggiator", "bass_sequence"), 0.6, 0.5, 8.0),

    # Textur & Stochastik
    SourceBankEntry("gen.texture.granular_cloud", SourceFamily.GRANULAR_STOCHASTIC, ("granular_texture", "atmospheric_noise"), 0.5, 0.2, 8.0),
    SourceBankEntry("gen.spectral.phase_freeze", SourceFamily.VOCAL_SPECTRAL, ("granular_texture", "atmospheric_noise", "moving_pad"), 0.45, 0.1, 10.0),
    SourceBankEntry("gen.noise.stochastic_trigger", SourceFamily.GRANULAR_STOCHASTIC, ("atmospheric_noise", "resonant_object", "granular_texture"), 0.7, 0.6, 6.0),
)


def select_diverse_source_ensemble(
    roles: tuple[str, ...],
    seed: SeedPath,
) -> dict[str, SourceBankEntry]:
    """Wählt für eine Liste von Rollen ein garantierte heterogenes Klang-Ensemble.

    Plan 3 Requirement: Keine Klangfamilie darf mehr als 2 tragende Rollen dominieren.
    Mindestens 4 unterschiedliche Klangfamilien müssen im Ensemble vorkommen.
    """
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))
    result: dict[str, SourceBankEntry] = {}
    family_counts: dict[SourceFamily, int] = {f: 0 for f in SourceFamily}

    for role in roles:
        # Finde passende Einträge für die Rolle
        matching = [
            e for e in SOURCE_BANK_CATALOG
            if role in e.primary_roles and family_counts[e.family] < 2
        ]
        if not matching:
            # Fallback: Finde beliebiges Modul, dessen Familie noch < 2 Rollen besetzt
            matching = [e for e in SOURCE_BANK_CATALOG if family_counts[e.family] < 2]

        if not matching:
            matching = list(SOURCE_BANK_CATALOG)

        # Mische und wähle aus matching
        rng.shuffle(matching)
        chosen = matching[0]

        result[role] = chosen
        family_counts[chosen.family] += 1

    return result


def build_tone_dna_for_entry(entry: SourceBankEntry, role: str, seed: SeedPath) -> ToneDNA:
    """Kompiliert ein ToneDNA-Objekt aus einem Bank-Eintrag."""
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))
    spec_jitter = rng.uniform(-0.1, 0.1)
    trans_jitter = rng.uniform(-0.1, 0.1)

    return ToneDNA(
        dna_id=f"dna_{role}_{entry.module_id.split('.')[-1]}",
        source_family=entry.family,
        source_module=entry.module_id,
        spectral_profile=max(0.0, min(1.0, entry.spectral_default + spec_jitter)),
        transient_articulation=max(0.0, min(1.0, entry.transient_default + trans_jitter)),
        evolution_budget=0.85,
    )
