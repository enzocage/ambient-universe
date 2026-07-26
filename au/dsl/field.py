"""Harmonisches Feld — feldrelative Tonhoehe (plan.md sym.field.*, Paragraph 6.5).

Ereignisse werden nie als absolute Frequenz gespeichert, sondern als Stufe in
einem Feld. Das ist die Voraussetzung fuer spaetere Transposition und
Umharmonisierung (plan.md Paragraph 4.4, L4-Invariante "feldrelativ").
"""

from __future__ import annotations

from pydantic import BaseModel, Field

#: Intervallmuster gaengiger Modi, in Halbtoenen ab dem Grundton.
MODES: dict[str, tuple[int, ...]] = {
    "ionian": (0, 2, 4, 5, 7, 9, 11),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "lydian": (0, 2, 4, 6, 7, 9, 11),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),
    "locrian": (0, 1, 3, 5, 6, 8, 10),
    # Pentatonik: fuer sparse Ambient-Motive, weniger Reibungsflaechen.
    "major_pentatonic": (0, 2, 4, 7, 9),
    "minor_pentatonic": (0, 3, 5, 7, 10),
}


class HarmonicField(BaseModel):
    """Grundton, Modus und erlaubte Stufen fuer ein Element oder einen Verband."""

    model_config = {"frozen": True}

    root_midi: float = Field(default=57.0, ge=0.0, le=127.0)
    """Grundton in MIDI-Notennummern (57 = A3)."""
    mode: str = "dorian"
    allowed_degrees: tuple[int, ...] | None = None
    """Nur diese Stufenindizes (0-basiert in der Modusreihe) sind erlaubt.
    ``None`` bedeutet: alle Stufen des Modus."""

    def degrees(self) -> tuple[int, ...]:
        return (
            self.allowed_degrees
            if self.allowed_degrees is not None
            else tuple(range(len(MODES[self.mode])))
        )

    def degree_to_midi(self, degree: int, octave_offset: int = 0) -> float:
        """Wandelt eine Stufe (kann ausserhalb 0..len liegen) in eine MIDI-Note."""
        intervals = MODES[self.mode]
        span = len(intervals)
        octave, index = divmod(degree, span)
        return self.root_midi + intervals[index] + 12 * (octave + octave_offset)

    def transposed(self, semitones: float) -> HarmonicField:
        return HarmonicField(
            root_midi=self.root_midi + semitones,
            mode=self.mode,
            allowed_degrees=self.allowed_degrees,
        )
