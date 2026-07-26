"""Rhythmus-/Tempo-Controller: eine geteilte Zeitraster fuer alle Elemente.

Ohne diese Datei laeuft jedes Element auf seiner eigenen, unabhaengigen
Zeitachse (Poisson-Ziehungen, euklidische Schritte mit eigener Schrittlaenge)
-- zwei Elemente koennen dieselbe Musik tragen und trotzdem "nicht
zusammenspielen", weil ihre Ereignisse nie auf einen gemeinsamen Puls fallen.
``Clock`` gibt allen Mustergeneratoren optional dasselbe Raster vor.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Clock(BaseModel):
    """Ein gemeinsames Zeitraster (Tempo + Taktart)."""

    model_config = {"frozen": True}

    bpm: float = Field(default=52.0, gt=0.0)
    """Bewusst niedrig-defaultet: Ambient braucht keinen tanzbaren Puls, nur
    ein gemeinsames Zeitmass, an dem sich Ereignisse orientieren koennen."""
    beats_per_bar: int = Field(default=4, ge=1)
    subdivision: int = Field(default=4, ge=1)
    """Unterteilungen je Schlag, an die quantisiert wird (4 = Sechzehntel bei
    4/4). Ambient-Quantisierung ist grosszuegig -- kein enges Timing-Raster."""

    @property
    def seconds_per_beat(self) -> float:
        return 60.0 / self.bpm

    @property
    def grid_step_s(self) -> float:
        return self.seconds_per_beat / self.subdivision

    @property
    def bar_length_s(self) -> float:
        return self.seconds_per_beat * self.beats_per_bar

    def quantize(self, time_s: float, *, strength: float = 1.0) -> float:
        """Zieht ``time_s`` auf das naechste Rasterelement.

        ``strength`` in [0, 1] blendet zwischen Original (0) und vollem
        Snap (1) -- Ambient-Ereignisse sollen sich am Puls orientieren,
        nicht mechanisch einrasten.
        """
        step = self.grid_step_s
        if step <= 0:
            return time_s
        nearest = round(time_s / step) * step
        strength = max(0.0, min(1.0, strength))
        return time_s + (nearest - time_s) * strength

    def grid_times(self, duration_s: float) -> list[float]:
        """Alle Rasterpunkte innerhalb der Dauer."""
        step = self.grid_step_s
        if step <= 0:
            return [0.0]
        count = int(duration_s / step) + 1
        return [i * step for i in range(count)]

    def bar_times(self, duration_s: float) -> list[float]:
        """Alle Taktanfaenge innerhalb der Dauer -- Ankerpunkte fuer
        Akkordwechsel und Dramaturgie-Breakpoints, damit auch die
        harmonische und dramaturgische Ebene am selben Puls haengen."""
        bar = self.bar_length_s
        if bar <= 0:
            return [0.0]
        count = int(duration_s / bar) + 1
        return [i * bar for i in range(count)]


def tempo_from_character(event_density_mean: float, emotional_temperature: float) -> float:
    """Leitet ein plausibles Ambient-Tempo aus der Album-DNA ab.

    Reiner Vorschlag, kein hartes Gesetz: dichtere, waermere Charaktere
    bekommen ein etwas hoeheres Grundtempo (mehr gefuehlte Bewegung), kalte,
    karge Charaktere ein sehr niedriges (fast statisches) Tempo.
    """
    base = 36.0 + 40.0 * max(0.0, min(1.0, event_density_mean)) * 2.0
    warmth_bias = 8.0 * max(0.0, min(1.0, emotional_temperature))
    return max(30.0, min(96.0, base + warmth_bias))
