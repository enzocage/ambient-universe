"""Vorhoer-Renderer fuer Klangelemente (plan.md Paragraph 9, Etappe 3).

Diese Phase deckt den Solo-Modus ab (Element allein, lautheitsnormalisiert).
"Im Feld" und "mit Nachbarn" brauchen den Blueprint bzw. bereits eingefrorene
Nachbarelemente und folgen mit Phase 6/8.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

from au.core.config import Config, get_config
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.pattern import NoteEvent
from au.render.element import render_element

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry


@dataclass(frozen=True, slots=True)
class AuditionResult:
    path: Path
    events: list[NoteEvent]
    peak: float
    rms: float
    gain_applied_db: float


def _rms_normalize(
    path: Path, target_rms_dbfs: float = -23.0, *, min_rms: float = 1e-6
) -> tuple[float, float, float]:
    """Normiert eine Datei an Ort und Stelle auf einen RMS-Zielpegel.

    Eine echte R128-Normalisierung (plan.md) braucht ein integriertes
    Lautheitsmodell; als Vorstufe genuegt RMS fuer den fairen A/B-Vergleich
    mehrerer Kandidaten in Etappe 3 — beide werden auf denselben Massstab
    gebracht, auch wenn er (noch) nicht ITU-BS.1770-konform ist.
    """
    import soundfile as sf

    data, sr = sf.read(str(path), dtype="float64", always_2d=True)
    rms = float(np.sqrt(np.mean(np.square(data))))
    if rms < min_rms:
        return 0.0, float(np.max(np.abs(data))), rms
    target_linear = 10.0 ** (target_rms_dbfs / 20.0)
    gain = target_linear / rms
    # Peak-Sicherung: Normalisierung darf nicht ins Clipping fuehren.
    peak = float(np.max(np.abs(data)))
    if peak * gain > 0.98:
        gain = 0.98 / peak
    normalized = data * gain
    sf.write(str(path), normalized, sr, subtype="FLOAT")
    gain_db = 20.0 * np.log10(gain) if gain > 0 else 0.0
    return (
        float(gain_db),
        float(np.max(np.abs(normalized))),
        float(np.sqrt(np.mean(np.square(normalized)))),
    )


def render_audition_solo(
    recipe: ElementRecipe,
    registry: Registry,
    output_path: Path,
    *,
    seed: SeedPath,
    target_rms_dbfs: float = -23.0,
    cfg: Config | None = None,
) -> AuditionResult:
    """Rendert ein Element solo und normalisiert es fuer den fairen Vergleich."""
    c = cfg or get_config()
    result, events = render_element(recipe, registry, output_path, seed=seed, cfg=c)
    gain_db, peak, rms = _rms_normalize(result.path, target_rms_dbfs)
    return AuditionResult(
        path=result.path, events=events, peak=peak, rms=rms, gain_applied_db=gain_db
    )
