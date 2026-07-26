"""Harmonik-/Melodie-Engine: eine geteilte Akkordfolge fuer alle Elemente.

Ohne diese Datei waehlt jedes Element seine Tonhoehen unabhaengig aus dem
vollen Feld (plan.md HarmonicField.degrees()) — zwei gleichzeitige Elemente
teilen sich zwar Grundton und Modus, koennen aber auf verschiedenen
Akkordtoenen landen und reiben. Diese Engine erzeugt eine durchgehende,
ueberlappungsfreie Akkordfolge (eine "Zeitleiste"), aus der alle Muster-
generatoren (au.dsl.pattern) ihre Stufen ziehen, wenn eine Zeitleiste
uebergeben wird -- das ist die album-/trackweite harmonische Konsistenz.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from pydantic import BaseModel, Field

from au.core.seeds import SeedPath
from au.dsl.field import MODES, HarmonicField


class ChordEvent(BaseModel):
    """Ein Akkord, gueltig fuer ein Zeitfenster."""

    model_config = {"frozen": True}

    time_s: float = Field(ge=0.0)
    duration_s: float = Field(gt=0.0)
    degrees: tuple[int, ...]
    """Stufenindizes (im Sinne von HarmonicField.degree_to_midi), die diesen
    Akkord bilden -- typischerweise Terzstapel (Grundton, Terz, Quinte)."""

    @property
    def root_degree(self) -> int:
        return self.degrees[0]


@dataclass(frozen=True, slots=True)
class ChordTimeline:
    """Eine luecken- und ueberlappungsfreie Folge von Akkorden."""

    chords: tuple[ChordEvent, ...]

    def degrees_at(self, t: float) -> tuple[int, ...]:
        """Die Akkordtoene, die zum Zeitpunkt ``t`` aktiv sind.

        Faellt ausserhalb der Zeitleiste auf den ersten/letzten Akkord zurueck
        -- ein Element, dessen Dauer die Zeitleiste geringfuegig ueberschreitet
        (Nachhall, Rundungsfehler), soll nicht auf ein leeres Ergebnis treffen.
        """
        if not self.chords:
            return (0,)
        if t <= self.chords[0].time_s:
            return self.chords[0].degrees
        for chord in self.chords:
            if chord.time_s <= t < chord.time_s + chord.duration_s:
                return chord.degrees
        return self.chords[-1].degrees


def _stack_thirds(root: int, span: int, count: int = 3) -> tuple[int, ...]:
    """Stufen im Terzabstand innerhalb der Modusreihe (Grundton, Terz, Quinte, ...).

    ``span`` ist die Zahl der Stufen des Modus (z.B. 7 fuer die Kirchentonarten,
    5 fuer Pentatonik) -- Terzstapel bedeutet hier "jede zweite Stufe", nicht
    zwingend eine tonale grosse/kleine Terz, da wir in Stufen, nicht in
    Halbtoenen rechnen. Das ist musikalisch korrekt fuer modale Harmonik.
    """
    step = 2 if span > 4 else 1  # Pentatonik: jede Stufe traegt schon genug Abstand
    return tuple(root + step * i for i in range(count))


@dataclass(frozen=True, slots=True)
class ChordProgression:
    """Eine zusammenhaengende, abschnittsbasierte Akkordfolge."""

    timeline: ChordTimeline
    progression_type: str
    section_roots: tuple[int, ...]


def generate_structured_chord_timeline(
    duration_s: float,
    field: HarmonicField,
    *,
    seed: SeedPath,
    tones_per_chord: int = 3,
) -> ChordProgression:
    """Erzeugt eine musikalisch gerichtete Akkordfolge mit Sektionsdramaturgie.
    
    Intro (Tonic) -> Build (Subdominant/Mediant) -> Peak (Spannungsakkord) -> Outro (Resolution).
    """
    rng = np.random.default_rng(seed.child("harmony", "structured").value & 0xFFFF_FFFF)
    span = len(MODES.get(field.mode, MODES["ionian"]))

    # Sektions-Grundstufen (Modaler Bogen)
    patterns = [
        (0, 2, 4, 0),    # I - III - V - I
        (0, 3, 5, 0),    # I - IV - VI - I
        (0, -2, 2, 0),   # I - VII - III - I
        (0, 4, 2, -1),   # I - V - III - VII
    ]
    chosen_roots = patterns[int(rng.integers(0, len(patterns)))]

    num_chords = max(4, int(duration_s / 16.0))
    chord_dur = duration_s / num_chords

    chords: list[ChordEvent] = []
    section_roots: list[int] = []

    for i in range(num_chords):
        t = i * chord_dur
        section_idx = min(len(chosen_roots) - 1, int((i / num_chords) * len(chosen_roots)))
        base_root = chosen_roots[section_idx]
        
        # Leichte Variation innerhalb der Sektion
        step = int(rng.choice([0, 1, -1], p=[0.7, 0.15, 0.15]))
        root = base_root + step
        section_roots.append(root)

        degrees = _stack_thirds(root, span, tones_per_chord)
        chords.append(ChordEvent(time_s=t, duration_s=chord_dur, degrees=degrees))

    timeline = ChordTimeline(chords=tuple(chords))
    return ChordProgression(
        timeline=timeline,
        progression_type=f"Modal_{field.mode}",
        section_roots=tuple(section_roots),
    )


def generate_chord_timeline(
    duration_s: float,
    field: HarmonicField,
    *,
    seed: SeedPath,
    chord_change_s: tuple[float, float] = (12.0, 28.0),
    tones_per_chord: int = 3,
) -> ChordTimeline:
    """Erzeugt eine durchgehende Akkordfolge ueber die volle Trackdauer."""
    prog = generate_structured_chord_timeline(duration_s, field, seed=seed, tones_per_chord=tones_per_chord)
    return prog.timeline

