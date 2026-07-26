"""Abschnittsprofile und Rollenübergabe (Plan 3, Paragraph 5.1 & 5.2).

Stellt sicher, dass benachbarte Abschnitte kontrastierende Profile aufweisen
und Rollen gezielt zwischen verschiedenen Klangfamilien übergeben werden.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from au.core.seeds import SeedPath
from au.dsl.section import SectionArrangement
from au.dsl.tone_dna import SourceFamily


@dataclass(frozen=True, slots=True)
class SectionProfile:
    section_name: str
    start_s: float
    end_s: float
    active_roles: tuple[str, ...]
    preferred_families: tuple[SourceFamily, ...]
    spectral_brightness: float  # 0.0 .. 1.0
    spatial_width: float  # 0.0 .. 1.0
    tension_target: float  # 0.0 .. 1.0
    role_handover_map: dict[str, SourceFamily] = field(default_factory=dict)


def generate_section_profiles(
    arrangement: SectionArrangement,
    seed: SeedPath,
) -> dict[str, SectionProfile]:
    """Generiert 4 kontrastierende Abschnittsprofile mit expliziten Rollenübergaben."""
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))

    # Intro (Entstehung)
    intro_prof = SectionProfile(
        section_name="intro",
        start_s=arrangement.intro[0],
        end_s=arrangement.intro[1],
        active_roles=("foundation", "harmonic_drone", "atmospheric_noise"),
        preferred_families=(SourceFamily.SUB_FOUNDATION, SourceFamily.FM_ADDITIVE, SourceFamily.VOCAL_SPECTRAL),
        spectral_brightness=0.35,
        spatial_width=0.4,
        tension_target=0.2,
        role_handover_map={
            "foundation": SourceFamily.SUB_FOUNDATION,
            "harmonic_drone": SourceFamily.FM_ADDITIVE,
        },
    )

    # Build (Entwicklung)
    build_prof = SectionProfile(
        section_name="build",
        start_s=arrangement.build[0],
        end_s=arrangement.build[1],
        active_roles=("foundation", "harmonic_drone", "moving_pad", "subharmonic_pulse", "atmospheric_noise"),
        preferred_families=(SourceFamily.ANALOG_WAVEFOLDED, SourceFamily.VOCAL_SPECTRAL, SourceFamily.RHYTHMIC_PULSE),
        spectral_brightness=0.55,
        spatial_width=0.6,
        tension_target=0.5,
        role_handover_map={
            "foundation": SourceFamily.ANALOG_WAVEFOLDED,  # Handover: Sub-Bass -> Wavefolder
            "harmonic_drone": SourceFamily.VOCAL_SPECTRAL,  # Handover: FM -> Formant Pad
        },
    )

    # Peak (Höhepunkt & Transformation)
    peak_prof = SectionProfile(
        section_name="peak",
        start_s=arrangement.peak[0],
        end_s=arrangement.peak[1],
        active_roles=("foundation", "harmonic_drone", "moving_pad", "signal_motif", "resonant_object", "granular_texture"),
        preferred_families=(SourceFamily.RESONANT_PHYSICAL, SourceFamily.GRANULAR_STOCHASTIC, SourceFamily.FM_ADDITIVE),
        spectral_brightness=0.8,
        spatial_width=0.85,
        tension_target=0.9,
        role_handover_map={
            "harmonic_drone": SourceFamily.RESONANT_PHYSICAL,  # Handover -> Wavetable Resonator
            "granular_texture": SourceFamily.GRANULAR_STOCHASTIC,
            "signal_motif": SourceFamily.RESONANT_PHYSICAL,  # Plucked String / Modal Bell
        },
    )

    # Outro (Rücknahme & Abklingen)
    outro_prof = SectionProfile(
        section_name="outro",
        start_s=arrangement.outro[0],
        end_s=arrangement.outro[1],
        active_roles=("foundation", "harmonic_drone", "atmospheric_noise"),
        preferred_families=(SourceFamily.SUB_FOUNDATION, SourceFamily.VOCAL_SPECTRAL),
        spectral_brightness=0.3,
        spatial_width=0.5,
        tension_target=0.1,
        role_handover_map={
            "foundation": SourceFamily.SUB_FOUNDATION,
            "harmonic_drone": SourceFamily.VOCAL_SPECTRAL,  # Phase Freeze / Formant Pad
        },
    )

    return {
        "intro": intro_prof,
        "build": build_prof,
        "peak": peak_prof,
        "outro": outro_prof,
    }
