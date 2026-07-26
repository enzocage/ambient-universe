"""Rhythm Intent Analysis Engine (Plan 4 Phase A).

Analysiert Prompt und AlbumDNA auf rhythmische Intention, Puls-Klarheit,
Bass-Bewegung, Arpeggio-Aktivität und Percussion-Anforderungen.
"""

from __future__ import annotations

from dataclasses import dataclass
import re

from au.core.seeds import SeedPath
from au.dsl.dna import AlbumDNA



@dataclass(frozen=True, slots=True)
class RhythmIntent:
    presence: float = 0.0
    pulse_clarity: float = 0.0
    syncopation: float = 0.0
    density: float = 0.0
    groove_stability: float = 0.8
    bass_motion: float = 0.0
    arpeggio_activity: float = 0.0
    percussion_activity: float = 0.0
    ambient_softness: float = 0.7
    tempo_range_bpm: tuple[float, float] = (60.0, 95.0)

    @property
    def requires_bass(self) -> bool:
        return self.presence >= 0.45 or self.bass_motion >= 0.4

    @property
    def requires_arpeggio(self) -> bool:
        return self.arpeggio_activity >= 0.35

    @property
    def requires_percussion(self) -> bool:
        return self.percussion_activity >= 0.25


def parse_rhythm_intent(prompt: str, dna: AlbumDNA | None = None) -> RhythmIntent:
    """Extrahiert die rhythmische Intention aus Text-Prompt und AlbumDNA."""
    p_lower = prompt.lower()

    # Keyword Matching
    rhythm_keywords = ["rhythmisch", "rhythmus", "puls", "groove", "takt", "beat", "sequenziert", "sequence"]
    bass_keywords = ["bass", "subbass", "tiefer bass", "basslinie", "basslauf", "bass-sequence"]
    arp_keywords = ["arpeggio", "arpeggiator", "sequenzer", "akkordlauf", "tonfolge", "glaskristall"]
    perc_keywords = ["perkussiv", "impuls", "klick", "percussion", "rhythmusgruppe", "tick", "rim"]

    presence = 0.8 if any(k in p_lower for k in rhythm_keywords) else 0.2
    bass_motion = 0.85 if any(k in p_lower for k in bass_keywords) else (0.5 if presence > 0.5 else 0.1)
    arp_activity = 0.85 if any(k in p_lower for k in arp_keywords) else (0.5 if presence > 0.5 else 0.1)
    perc_activity = 0.8 if any(k in p_lower for k in perc_keywords) else (0.4 if presence > 0.5 else 0.1)

    if dna is not None:
        if dna.character.event_density_mean > 0.6:
            presence = max(presence, 0.6)
            arp_activity = max(arp_activity, 0.5)

    return RhythmIntent(
        presence=presence,
        pulse_clarity=0.8 if presence > 0.4 else 0.3,
        syncopation=0.4,
        density=presence * 0.7 + 0.2,
        groove_stability=0.85,
        bass_motion=bass_motion,
        arpeggio_activity=arp_activity,
        percussion_activity=perc_activity,
        ambient_softness=0.6,
        tempo_range_bpm=(65.0, 92.0),
    )
