"""Kuratierte Klanggesten aus den 50 Referenzbeschreibungen.

Die Eintraege sind Kompositionswissen: Eine Geste beschreibt Quelle, Bewegung,
Rolle und Einsatz. Sie ist noch kein fertiges SynthDef und darf daher nur ueber
validierte Implementierungen in Audio uebersetzt werden.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PatternFamily(StrEnum):
    OSCILLATOR = "oscillator_modulation"
    FILTER = "filter_resonance"
    SPACE = "space_delay_reverb"
    DYNAMICS = "dynamics_distortion"
    COMPLEX = "complex_modulation"


@dataclass(frozen=True, slots=True)
class SonicPattern:
    pattern_id: str
    name: str
    family: PatternFamily
    roles: tuple[str, ...]
    function: str
    section_fit: tuple[str, ...]
    risk: float
    requires: tuple[str, ...]


SONIC_PATTERNS: tuple[SonicPattern, ...] = (
    SonicPattern("hard_sync_sweep", "Zerrissenes Schimmern", PatternFamily.OSCILLATOR, ("signal_motif", "contrast_layer"), "aggressive spectral rise", ("build", "peak"), .75, ("sync", "pitch_envelope")),
    SonicPattern("supersaw_drift", "Atmende Detune-Schwebung", PatternFamily.OSCILLATOR, ("moving_pad", "harmonic_drone"), "organic width", ("intro", "build", "outro"), .2, ("detune", "slow_lfo")),
    SonicPattern("fm_fast_pluck", "Metallisches Zirpen", PatternFamily.OSCILLATOR, ("arpeggiator", "resonant_object"), "bright transient into warmth", ("build", "peak"), .35, ("fm", "fast_envelope")),
    SonicPattern("sub_phase_growl", "Subterrestrisches Grollen", PatternFamily.OSCILLATOR, ("foundation", "bass_sequence"), "physical low body", ("intro", "build"), .4, ("sub", "phase_shift")),
    SonicPattern("ringmod_ice_arp", "Gläserne Glocken-Arpeggios", PatternFamily.OSCILLATOR, ("arpeggiator", "signal_motif"), "inharmonic crystalline motion", ("peak",), .55, ("ring_mod", "inharmonic_ratio")),
    SonicPattern("pwm_rubber_bass", "Gummi-Bass", PatternFamily.OSCILLATOR, ("bass_sequence",), "elastic syncopated bass", ("build", "peak"), .3, ("pwm", "clocked_lfo")),
    SonicPattern("velocity_wavefold_wah", "Flüssiger Wah-Morph", PatternFamily.OSCILLATOR, ("bass_sequence", "signal_motif"), "velocity-driven timbre", ("build", "peak"), .5, ("wavefold", "velocity")),
    SonicPattern("sample_rate_glitch", "Körniges Pfeifen", PatternFamily.OSCILLATOR, ("texture", "contrast_layer"), "lo-fi digital dust", ("peak",), .65, ("sample_rate_reduction",)),
    SonicPattern("legato_glide", "Unendliches Gleiten", PatternFamily.OSCILLATOR, ("bass_sequence", "signal_motif"), "continuous phrase connection", ("build", "outro"), .4, ("portamento", "legato")),
    SonicPattern("audio_rate_pitch_spark", "Metallischer Funkenregen", PatternFamily.OSCILLATOR, ("texture", "resonant_object"), "rough tonal grain", ("peak",), .7, ("audio_rate_lfo",)),
    SonicPattern("filter_ping", "Zwitscherndes Selbstoszillieren", PatternFamily.FILTER, ("resonant_object", "subtle_percussive_background"), "pitched response", ("build", "peak"), .8, ("resonance", "click_exciter")),
    SonicPattern("dual_formant_sweep", "Hohler Roboter-Gesang", PatternFamily.FILTER, ("harmonic_drone", "contrast_layer"), "vocal spectral movement", ("peak",), .5, ("dual_bpf",)),
    SonicPattern("noise_wind_sweep", "Raschelnder Herbstdunst", PatternFamily.FILTER, ("atmospheric_noise", "texture"), "wind-like transition", ("intro", "build"), .25, ("noise", "lp_sweep")),
    SonicPattern("snappy_filter_pop", "Flüssiger Klick", PatternFamily.FILTER, ("subtle_percussive_background", "resonant_object"), "short wooden transient", ("build", "peak"), .35, ("zero_attack", "filter_env")),
    SonicPattern("acid_accent", "Brodelndes Säure-Quietschen", PatternFamily.FILTER, ("bass_sequence", "signal_motif"), "accented bass articulation", ("peak",), .55, ("resonant_ladder", "accent")),
    SonicPattern("tracking_notch_glass", "Gläserner Akkord", PatternFamily.FILTER, ("harmonic_drone", "moving_pad"), "transparent harmonic body", ("intro", "outro"), .45, ("key_tracking", "notch")),
    SonicPattern("underwater_lowpass", "Düsterer Unterwasser-Bass", PatternFamily.FILTER, ("foundation", "bass_sequence"), "dark pressure", ("intro", "build"), .3, ("lowpass", "near_resonance")),
    SonicPattern("highpass_tube_edge", "Metallisches Zischen", PatternFamily.FILTER, ("contrast_layer", "texture"), "present top edge", ("peak",), .6, ("highpass", "saturation")),
    SonicPattern("comb_string_pluck", "Kammfilter-Gitarren-Pluck", PatternFamily.FILTER, ("arpeggiator", "signal_motif"), "physical plucked illusion", ("build", "peak"), .45, ("comb", "short_delay")),
    SonicPattern("tracking_phaser", "Heulende Phasen-Verschiebung", PatternFamily.FILTER, ("moving_pad", "harmonic_drone"), "register-dependent motion", ("build", "outro"), .4, ("phaser", "key_tracking")),
    SonicPattern("shimmer_reverb", "Endloses Wolken-Verblassen", PatternFamily.SPACE, ("harmonic_drone", "moving_pad"), "ascending halo", ("peak", "outro"), .55, ("reverb", "pitch_shift")),
    SonicPattern("odd_ping_pong", "Stolperndes Echo", PatternFamily.SPACE, ("subtle_percussive_background", "arpeggiator"), "polyrhythmic propulsion", ("build", "peak"), .4, ("ping_pong", "odd_times")),
    SonicPattern("freeze_reverb", "Gefrorener Augenblick", PatternFamily.SPACE, ("harmonic_drone", "texture"), "held evolving space", ("intro", "outro"), .35, ("freeze", "pitch_lfo")),
    SonicPattern("gated_cathedral", "Atemberaubender Raum-Kollaps", PatternFamily.SPACE, ("transition", "resonant_object"), "impact then vacuum", ("build", "peak"), .65, ("reverb", "gate")),
    SonicPattern("tape_pitch_drift", "Flüssiges Tape-Echo", PatternFamily.SPACE, ("signal_motif", "texture"), "unstable memory", ("outro", "peak"), .3, ("delay", "time_mod")),
    SonicPattern("feedback_dub_bloom", "Schwebende Dub-Explosion", PatternFamily.SPACE, ("subtle_percussive_background", "transition"), "self-heating echo", ("peak",), .75, ("feedback", "saturation")),
    SonicPattern("reverse_delay_bloom", "Rückwärts rollender Schleier", PatternFamily.SPACE, ("moving_pad", "transition"), "arrival into downbeat", ("build",), .45, ("reverse", "delay")),
    SonicPattern("bbd_dark_echo", "Schmutziges Lo-Fi-Echo", PatternFamily.SPACE, ("texture", "signal_motif"), "darkening memory", ("outro",), .25, ("bbd", "noise")),
    SonicPattern("haas_micro_delay", "Plastischer 3D-Klick", PatternFamily.SPACE, ("subtle_percussive_background", "resonant_object"), "near-to-wide transient", ("peak",), .2, ("micro_delay",)),
    SonicPattern("multitap_diffusion", "Chaotisches Echo-Gewebe", PatternFamily.SPACE, ("arpeggiator", "texture"), "rhythmic cave reflections", ("build", "peak"), .4, ("multitap", "diffusion")),
    SonicPattern("sidechain_pump", "Pumpender Wandschlag", PatternFamily.DYNAMICS, ("moving_pad", "harmonic_drone"), "breathing around bass", ("build", "peak"), .35, ("sidechain", "bass_trigger")),
    SonicPattern("tape_wave_crush", "Hölzernes Aufbrechen", PatternFamily.DYNAMICS, ("bass_sequence", "foundation"), "small-speaker bass bite", ("build",), .35, ("tape", "wave_crush")),
    SonicPattern("vinyl_flutter", "Grammophon-Knistern", PatternFamily.DYNAMICS, ("texture", "harmonic_drone"), "aged instability", ("intro", "outro"), .25, ("vinyl_noise", "wow_flutter")),
    SonicPattern("bitcrushed_wurli", "Staubiger Wurlitzer-Biss", PatternFamily.DYNAMICS, ("harmonic_drone", "signal_motif"), "grainy mid texture", ("build", "peak"), .3, ("bitcrush", "lowpass")),
    SonicPattern("overdriven_unison", "Brüllendes Röhren-Unisono", PatternFamily.DYNAMICS, ("foundation", "moving_pad"), "choral wall", ("peak",), .7, ("unison", "tube")),
    SonicPattern("transient_shaper_bass", "Perkussiver Snag", PatternFamily.DYNAMICS, ("bass_sequence",), "hard attack into clean sub", ("build", "peak"), .45, ("transient_shaper",)),
    SonicPattern("rhythmic_gate", "Zerfetztes Gate", PatternFamily.DYNAMICS, ("moving_pad", "harmonic_drone"), "pad becomes pulse", ("build", "peak"), .4, ("clocked_gate",)),
    SonicPattern("fm_downsample_paper", "Raschelnder Papiereffekt", PatternFamily.DYNAMICS, ("texture", "moving_pad"), "mathematical background grain", ("peak",), .65, ("fm", "downsample")),
    SonicPattern("envelope_drive", "Flüssiger Wah-Drive", PatternFamily.DYNAMICS, ("bass_sequence", "signal_motif"), "velocity-linked dirt", ("peak",), .5, ("envelope_follower", "drive")),
    SonicPattern("multiband_foundation", "Schwankendes Fundament", PatternFamily.DYNAMICS, ("foundation", "bass_sequence"), "bass makes room above", ("build", "peak"), .35, ("multiband", "ducking")),
    SonicPattern("sh_filter_random", "Lebendiges Unikat", PatternFamily.COMPLEX, ("signal_motif", "texture"), "per-note unpredictability", ("peak",), .7, ("sample_hold", "filter")),
    SonicPattern("shepherd_filter", "Shepherd-Rieseln", PatternFamily.COMPLEX, ("moving_pad", "texture"), "endless ascent illusion", ("build", "outro"), .65, ("layered_filters",)),
    SonicPattern("amplifier_breath", "Atmen des Verstärkers", PatternFamily.COMPLEX, ("moving_pad", "harmonic_drone"), "amplitude and tone breath", ("intro", "outro"), .2, ("dual_lfo",)),
    SonicPattern("legato_reset_glitch", "Rostiger Roboter-Galopp", PatternFamily.COMPLEX, ("arpeggiator",), "mixed legato and staccato", ("peak",), .55, ("arp", "selective_trigger")),
    SonicPattern("sh_pitch_pluck", "Sprechendes Kichern", PatternFamily.COMPLEX, ("arpeggiator", "resonant_object"), "digital creature articulation", ("peak",), .75, ("sample_hold", "short_pluck")),
    SonicPattern("inverted_pitch_filter", "Spiegelnder Kristall", PatternFamily.COMPLEX, ("resonant_object", "signal_motif"), "falling drop gesture", ("build", "peak"), .5, ("inverse_env",)),
    SonicPattern("slow_feedback_chorus", "Brodelndes Ölbad", PatternFamily.COMPLEX, ("moving_pad", "harmonic_drone"), "thick warm drift", ("intro", "outro"), .3, ("chorus", "slow_lfo")),
    SonicPattern("velocity_micro_delay", "Perkussives Glitching", PatternFamily.COMPLEX, ("subtle_percussive_background", "resonant_object"), "velocity-dependent mechanical click", ("peak",), .55, ("micro_delay", "velocity")),
    SonicPattern("fm_noise_stardust", "Sternenstaub-Zischen", PatternFamily.COMPLEX, ("texture", "space_noise_elements"), "tonal noise particles", ("intro", "peak"), .6, ("noise_fm",)),
    SonicPattern("wavetable_worldfire", "Epischer Weltenbrand", PatternFamily.COMPLEX, ("contrast_layer", "moving_pad"), "eight-bar cinematic rise", ("build", "peak"), .65, ("wavetable", "sub_surge")),
)


def patterns_for_role(role: str) -> tuple[SonicPattern, ...]:
    return tuple(pattern for pattern in SONIC_PATTERNS if role in pattern.roles)
