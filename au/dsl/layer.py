"""L5 — Schicht/Rolle: ein Bibliothekselement im Trackkontext (plan.md 4.5)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LayerInstance(BaseModel):
    """Ein Element, platziert in Zeit, Transposition und Zeitskala."""

    model_config = {"frozen": True}

    layer_id: str
    element_id: str
    role: str
    band_hz: tuple[float, float]
    entry_time_s: float = Field(ge=0.0)
    exit_time_s: float
    transposition: float = 0.0
    phase_offset_s: float = 0.0
    time_scale: float = Field(default=1.0, gt=0.0)
    tail_overhang_s: float = 4.0
    """Wie lange nach ``exit_time_s`` noch Nachhall/Ausklang belegt (plan.md
    4.5-MI-Direktive: "plane mit dem Nachhall, nicht mit der Note")."""
    lufs_target: float = -24.0

    @property
    def duration_s(self) -> float:
        return self.exit_time_s - self.entry_time_s

    @property
    def occupied_until_s(self) -> float:
        """Ende der tatsaechlichen Raumbelegung inklusive Nachhall."""
        return self.exit_time_s + self.tail_overhang_s

    def overlaps_time(self, other: LayerInstance) -> bool:
        return (
            self.entry_time_s < other.occupied_until_s
            and other.entry_time_s < self.occupied_until_s
        )

    def overlaps_band(self, other: LayerInstance) -> bool:
        low = max(self.band_hz[0], other.band_hz[0])
        high = min(self.band_hz[1], other.band_hz[1])
        return high > low

    def band_overlap_fraction(self, other: LayerInstance) -> float:
        """Anteil des schmaleren Bands, der sich mit dem anderen deckt."""
        low = max(self.band_hz[0], other.band_hz[0])
        high = min(self.band_hz[1], other.band_hz[1])
        if high <= low:
            return 0.0
        overlap = high - low
        narrower = min(self.band_hz[1] - self.band_hz[0], other.band_hz[1] - other.band_hz[0])
        return overlap / narrower if narrower > 0 else 0.0
