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


def generate_chord_timeline(
    duration_s: float,
    field: HarmonicField,
    *,
    seed: SeedPath,
    chord_change_s: tuple[float, float] = (12.0, 28.0),
    tones_per_chord: int = 3,
) -> ChordTimeline:
    """Erzeugt eine durchgehende Akkordfolge ueber die volle Trackdauer.

    Der naechste Akkord wird per Random Walk auf den Modusstufen gewaehlt
    (kleine Schritte bevorzugt) statt komplett zufaellig -- das vermeidet
    weite Spruenge, die in Ambient-Harmonik selten sind (plan.md:
    "sehr langsames Voice Leading").
    """
    rng = np.random.default_rng(seed.child("harmony", "chords").value & 0xFFFF_FFFF)
    span = len(MODES[field.mode])
    degree_pool = field.degrees()
    if not degree_pool:
        degree_pool = tuple(range(span))

    chords: list[ChordEvent] = []
    t = 0.0
    current_root = int(rng.choice(degree_pool))
    while t < duration_s:
        dur = float(rng.uniform(*chord_change_s))
        dur = min(dur, duration_s - t)
        degrees = _stack_thirds(current_root, span, tones_per_chord)
        chords.append(ChordEvent(time_s=t, duration_s=dur, degrees=degrees))
        t += dur
        # Kleiner Schritt auf der Stufenreihe (+-1 bevorzugt, +-2 selten) statt
        # eines beliebigen Sprungs -- "sehr langsames Voice Leading" (plan.md).
        step = int(rng.choice([-2, -1, 1, 2], p=[0.15, 0.35, 0.35, 0.15]))
        # Gelegentlich (15%) ein bewusster groesserer Sprung auf eine neue
        # zufaellige Stufe -- verhindert, dass die Folge stur monoton driftet.
        current_root = int(rng.choice(degree_pool)) if rng.random() < 0.15 else current_root + step
    return ChordTimeline(chords=tuple(chords))
