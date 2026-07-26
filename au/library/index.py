"""Durchsuchbarer Index der Elementbibliothek (plan.md Paragraph 10.1, Phase 7)."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path

from au.core.config import Config, get_config

_SCHEMA = """
CREATE TABLE IF NOT EXISTS elements (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    voice_module_id TEXT NOT NULL,
    thesis TEXT,
    tags TEXT NOT NULL,
    peak REAL,
    rms REAL,
    centroid_hz REAL,
    loop_visible_s REAL,
    path TEXT NOT NULL
);
"""


@dataclass(frozen=True, slots=True)
class ElementRow:
    id: str
    name: str
    voice_module_id: str
    thesis: str
    tags: tuple[str, ...]
    peak: float
    rms: float
    centroid_hz: float
    loop_visible_s: float
    path: str


def _connect(cfg: Config) -> sqlite3.Connection:
    cfg.elements_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(cfg.elements_dir / "index.sqlite"))
    conn.execute(_SCHEMA)
    return conn


def register_element(element_dir: Path, cfg: Config | None = None) -> None:
    """Traegt ein bereits eingefrorenes Element in den Index ein."""
    c = cfg or get_config()
    recipe = json.loads((element_dir / "recipe.json").read_text(encoding="utf-8"))
    analysis = json.loads((element_dir / "analysis.json").read_text(encoding="utf-8"))

    with _connect(c) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO elements "
            "(id, name, voice_module_id, thesis, tags, peak, rms, centroid_hz, "
            "loop_visible_s, path) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                recipe["id"],
                recipe.get("name", ""),
                recipe["voice_module_id"],
                recipe.get("thesis", ""),
                json.dumps(recipe.get("tags", [])),
                analysis.get("peak", 0.0),
                analysis.get("rms", 0.0),
                analysis.get("centroid_hz", 0.0),
                analysis.get("loop_visible_s", -1.0),
                str(element_dir),
            ),
        )


def _row_to_element(row: tuple[object, ...]) -> ElementRow:
    return ElementRow(
        id=str(row[0]),
        name=str(row[1]),
        voice_module_id=str(row[2]),
        thesis=str(row[3] or ""),
        tags=tuple(json.loads(str(row[4]))),
        peak=float(row[5]),  # type: ignore[arg-type]
        rms=float(row[6]),  # type: ignore[arg-type]
        centroid_hz=float(row[7]),  # type: ignore[arg-type]
        loop_visible_s=float(row[8]),  # type: ignore[arg-type]
        path=str(row[9]),
    )


def search(query: str, cfg: Config | None = None, limit: int = 25) -> list[ElementRow]:
    """Einfache Stichwortsuche ueber Name, These und Tags.

    Kein semantisches Embedding (plan.md sieht das fuer den vollen Ausbau
    vor) — eine SQL-LIKE-Suche ueber die textuellen Felder deckt den
    Hauptfall (Browsen, Wiederfinden) bereits ab.
    """
    c = cfg or get_config()
    pattern = f"%{query.lower()}%"
    with _connect(c) as conn:
        rows = conn.execute(
            "SELECT id, name, voice_module_id, thesis, tags, peak, rms, centroid_hz, "
            "loop_visible_s, path FROM elements "
            "WHERE lower(name) LIKE ? OR lower(thesis) LIKE ? OR lower(tags) LIKE ? "
            "LIMIT ?",
            (pattern, pattern, pattern, limit),
        ).fetchall()
    return [_row_to_element(r) for r in rows]


def list_all(cfg: Config | None = None) -> list[ElementRow]:
    c = cfg or get_config()
    with _connect(c) as conn:
        rows = conn.execute(
            "SELECT id, name, voice_module_id, thesis, tags, peak, rms, centroid_hz, "
            "loop_visible_s, path FROM elements ORDER BY id"
        ).fetchall()
    return [_row_to_element(r) for r in rows]


def find_similar_by_voice(voice_module_id: str, cfg: Config | None = None) -> list[ElementRow]:
    """Elemente, die dieselbe Stimme verwenden — der einfachste Aehnlichkeitsproxy
    vor dem vollen Einbettungsvergleich aus plan.md."""
    c = cfg or get_config()
    with _connect(c) as conn:
        rows = conn.execute(
            "SELECT id, name, voice_module_id, thesis, tags, peak, rms, centroid_hz, "
            "loop_visible_s, path FROM elements WHERE voice_module_id = ?",
            (voice_module_id,),
        ).fetchall()
    return [_row_to_element(r) for r in rows]
