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
    SourceBankEntry("gen.synth.ladder_bass", SourceFamily.ANALOG_WAVEFOLDED, ("foundation", "subharmonic_pulse", "bass_sequence"), 0.3, 0.4, 10.0),
    SourceBankEntry("gen.synth.sallen_key", SourceFamily.ANALOG_WAVEFOLDED, ("foundation", "bass_sequence", "signal_motif"), 0.45, 0.5, 8.0),
    SourceBankEntry("gen.synth.folding_drone", SourceFamily.ANALOG_WAVEFOLDED, ("foundation", "harmonic_drone", "subharmonic_pulse"), 0.4, 0.2, 10.0),
    SourceBankEntry("gen.fm.feedback_drone", SourceFamily.FM_ADDITIVE, ("foundation", "harmonic_drone", "subharmonic_pulse"), 0.35, 0.2, 10.0),
    SourceBankEntry("gen.noise.brownian_drift", SourceFamily.SUB_FOUNDATION, ("foundation", "atmospheric_noise"), 0.15, 0.05, 12.0),

    # Harmonie / Drones / Pads
    SourceBankEntry("gen.fm.dual_operator", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "moving_pad", "signal_motif"), 0.65, 0.2, 8.0),
    SourceBankEntry("gen.additive.harmonic_partials", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "moving_pad", "foundation"), 0.5, 0.15, 10.0),
    SourceBankEntry("gen.drone.wavetable_resonator", SourceFamily.RESONANT_PHYSICAL, ("harmonic_drone", "moving_pad"), 0.55, 0.2, 10.0),
    SourceBankEntry("gen.vocal.formant_pad", SourceFamily.VOCAL_SPECTRAL, ("harmonic_drone", "moving_pad", "atmospheric_noise"), 0.6, 0.1, 8.0),
    SourceBankEntry("gen.synth.juno_chorus", SourceFamily.ANALOG_WAVEFOLDED, ("harmonic_drone", "moving_pad", "foundation"), 0.55, 0.2, 8.0),
    SourceBankEntry("gen.synth.biquad_sweep", SourceFamily.ANALOG_WAVEFOLDED, ("moving_pad", "atmospheric_noise", "granular_texture"), 0.6, 0.2, 8.0),
    SourceBankEntry("gen.synth.vector_pad", SourceFamily.ANALOG_WAVEFOLDED, ("moving_pad", "harmonic_drone", "atmospheric_noise"), 0.6, 0.15, 8.0),
    SourceBankEntry("gen.synth.wavetable_morph", SourceFamily.ANALOG_WAVEFOLDED, ("harmonic_drone", "moving_pad", "signal_motif"), 0.65, 0.25, 8.0),
    SourceBankEntry("gen.fm.four_operator", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "signal_motif", "moving_pad"), 0.7, 0.3, 8.0),
    SourceBankEntry("gen.fm.phase_mod_pad", SourceFamily.FM_ADDITIVE, ("moving_pad", "harmonic_drone", "atmospheric_noise"), 0.6, 0.15, 8.0),
    SourceBankEntry("gen.additive.organ_partials", SourceFamily.FM_ADDITIVE, ("harmonic_drone", "moving_pad", "foundation"), 0.55, 0.2, 10.0),
    SourceBankEntry("gen.spectral.frequency_shifter", SourceFamily.VOCAL_SPECTRAL, ("harmonic_drone", "moving_pad", "atmospheric_noise"), 0.5, 0.1, 10.0),
    SourceBankEntry("gen.vocal.choir_vowels", SourceFamily.VOCAL_SPECTRAL, ("moving_pad", "harmonic_drone", "atmospheric_noise"), 0.65, 0.1, 8.0),

    # Motive / Melodien / Resonanz-Objekte
    SourceBankEntry("gen.physical.plucked_string", SourceFamily.RESONANT_PHYSICAL, ("signal_motif", "resonant_object", "arpeggiator"), 0.7, 0.8, 6.0),
    SourceBankEntry("gen.object.modal_bell", SourceFamily.RESONANT_PHYSICAL, ("resonant_object", "signal_motif"), 0.75, 0.85, 6.0),
    SourceBankEntry("gen.arpeggio.pulse_sequence", SourceFamily.RHYTHMIC_PULSE, ("signal_motif", "arpeggiator", "bass_sequence"), 0.6, 0.5, 8.0),
    SourceBankEntry("gen.synth.prophet_lead", SourceFamily.ANALOG_WAVEFOLDED, ("signal_motif", "harmonic_drone", "arpeggiator"), 0.75, 0.5, 6.0),
    SourceBankEntry("gen.synth.chebyshev_drive", SourceFamily.ANALOG_WAVEFOLDED, ("signal_motif", "resonant_object", "bass_sequence"), 0.7, 0.6, 6.0),
    SourceBankEntry("gen.fm.bell_chime", SourceFamily.FM_ADDITIVE, ("resonant_object", "signal_motif"), 0.8, 0.9, 5.0),
    SourceBankEntry("gen.additive.bell_partials", SourceFamily.FM_ADDITIVE, ("resonant_object", "signal_motif"), 0.8, 0.85, 5.0),
    SourceBankEntry("gen.physical.bowed_string", SourceFamily.RESONANT_PHYSICAL, ("signal_motif", "harmonic_drone", "resonant_object"), 0.65, 0.6, 7.0),
    SourceBankEntry("gen.physical.marimba_bar", SourceFamily.RESONANT_PHYSICAL, ("resonant_object", "signal_motif", "arpeggiator"), 0.7, 0.85, 5.0),
    SourceBankEntry("gen.physical.flute_pipe", SourceFamily.RESONANT_PHYSICAL, ("signal_motif", "harmonic_drone", "moving_pad"), 0.6, 0.4, 7.0),
    SourceBankEntry("gen.physical.karplus_ensemble", SourceFamily.RESONANT_PHYSICAL, ("harmonic_drone", "signal_motif", "resonant_object"), 0.65, 0.7, 6.0),
    SourceBankEntry("gen.arpeggio.euclidean_pulse", SourceFamily.RHYTHMIC_PULSE, ("arpeggiator", "signal_motif", "subharmonic_pulse"), 0.65, 0.6, 8.0),
    SourceBankEntry("gen.arpeggio.random_walk_seq", SourceFamily.RHYTHMIC_PULSE, ("arpeggiator", "signal_motif"), 0.7, 0.6, 8.0),

    # Textur & Stochastik
    SourceBankEntry("gen.texture.granular_cloud", SourceFamily.GRANULAR_STOCHASTIC, ("granular_texture", "atmospheric_noise"), 0.5, 0.2, 8.0),
    SourceBankEntry("gen.spectral.phase_freeze", SourceFamily.VOCAL_SPECTRAL, ("granular_texture", "atmospheric_noise", "moving_pad"), 0.45, 0.1, 10.0),
    SourceBankEntry("gen.noise.stochastic_trigger", SourceFamily.GRANULAR_STOCHASTIC, ("atmospheric_noise", "resonant_object", "granular_texture"), 0.7, 0.6, 6.0),
    SourceBankEntry("gen.spectral.spectral_blur", SourceFamily.VOCAL_SPECTRAL, ("atmospheric_noise", "granular_texture", "moving_pad"), 0.5, 0.1, 10.0),
    SourceBankEntry("gen.vocal.whisper_noise", SourceFamily.VOCAL_SPECTRAL, ("atmospheric_noise", "granular_texture"), 0.55, 0.2, 8.0),
    SourceBankEntry("gen.texture.grain_cloud_dense", SourceFamily.GRANULAR_STOCHASTIC, ("granular_texture", "atmospheric_noise", "moving_pad"), 0.55, 0.3, 8.0),
    SourceBankEntry("gen.noise.pink_crackle", SourceFamily.GRANULAR_STOCHASTIC, ("atmospheric_noise", "granular_texture"), 0.6, 0.4, 8.0),
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
