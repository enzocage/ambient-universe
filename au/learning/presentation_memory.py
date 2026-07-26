"""Gedaechtnis fuer bereits gezeigte Klangbeispiele und neue Katalogoptionen."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Presentation:
    presentation_id: str
    candidate_id: str
    audio_fingerprint: str
    module_id: str
    preset_fingerprint: str
    context: str
    is_new_option: bool = False


class PresentationMemory:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self.items: list[Presentation] = []
        if path and path.is_file():
            self.items = [Presentation(**item) for item in json.loads(path.read_text(encoding="utf-8"))]

    def remember(self, item: Presentation) -> None:
        if not any(existing.presentation_id == item.presentation_id for existing in self.items):
            self.items.append(item)
            self._save()

    def has_audio(self, fingerprint: str) -> bool:
        return any(item.audio_fingerprint == fingerprint for item in self.items)

    def has_candidate(self, candidate_id: str) -> bool:
        return any(item.candidate_id == candidate_id for item in self.items)

    def new_options(self) -> tuple[Presentation, ...]:
        return tuple(item for item in self.items if item.is_new_option)

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([asdict(item) for item in self.items], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
