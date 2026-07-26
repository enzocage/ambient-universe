"""Persistente, unveraenderliche Nutzerbewertungen fuer Klangbeispiele."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class RatingEvent:
    rating_id: str
    presentation_id: str
    candidate_id: str
    audio_fingerprint: str
    role: str
    context: str
    rating: int
    labels: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 10:
            raise ValueError("rating muss zwischen 1 und 10 liegen")


class RatingStore:
    """Append-only Store; bestehende Ratings werden nie ueberschrieben."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.events: list[RatingEvent] = []
        if path and path.is_file():
            self.events = [RatingEvent(**item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def add(
        self,
        *,
        presentation_id: str,
        candidate_id: str,
        audio_fingerprint: str,
        role: str,
        context: str,
        rating: int,
        labels: tuple[str, ...] = (),
    ) -> RatingEvent:
        event = RatingEvent(
            rating_id=str(uuid4()),
            presentation_id=presentation_id,
            candidate_id=candidate_id,
            audio_fingerprint=audio_fingerprint,
            role=role,
            context=context,
            rating=rating,
            labels=labels,
        )
        self.events.append(event)
        self._save()
        return event

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(event) for event in self.events], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def mean_for(self, candidate_id: str, *, role: str | None = None) -> float | None:
        values = [
            event.rating
            for event in self.events
            if event.candidate_id == candidate_id and (role is None or event.role == role)
        ]
        return sum(values) / len(values) if values else None
