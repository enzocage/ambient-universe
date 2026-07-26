"""Freeze-Pipeline: Element -> unveraenderliche Ablage (plan.md Paragraph 10.1).

Ein eingefrorenes Element ist ein Ordner mit Rezept, Steckbrief, Analyse und
Vorhoer-Audio. Das Rezept ist die Quelle der Wahrheit (plan.md 10.3: Rezept
statt Audio) — die Audiodatei dient nur dem schnellen Browsen.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import soundfile as sf

from au.analysis.metrics import (
    dc_offset,
    first_visible_loop_s,
    peak,
    rms,
    spectral_centroid,
    stereo_correlation,
)
from au.core.config import Config, get_config
from au.core.hashing import sha256_audio, sha256_json
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.render.audition import render_audition_solo

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry


def _write_card(recipe: ElementRecipe, analysis: dict[str, float]) -> str:
    lines = [
        f"# {recipe.name or recipe.id}",
        "",
        f"**These:** {recipe.thesis or '(keine angegeben)'}",
        "",
        f"- Stimme: `{recipe.voice_module_id}`",
        f"- Feld: {recipe.field.mode} ab MIDI {recipe.field.root_midi:.1f}",
        f"- Dauer: {recipe.duration_s:.0f}s, Ereignisdichte: {recipe.lambda_per_min:.1f}/min",
        f"- Tags: {', '.join(recipe.tags) or '(keine)'}",
        "",
        "## Analyse",
        f"- Spitze: {analysis['peak']:.3f}",
        f"- RMS: {analysis['rms']:.4f}",
        f"- Spektralschwerpunkt: {analysis['centroid_hz']:.0f} Hz",
        f"- Stereo-Korrelation: {analysis['stereo_correlation']:+.2f}",
        f"- Erste sichtbare Wiederholung: "
        + (
            f"{analysis['loop_visible_s']:.0f}s"
            if analysis["loop_visible_s"] >= 0
            else "keine gefunden"
        ),
    ]
    return "\n".join(lines) + "\n"


def freeze_element(
    recipe: ElementRecipe,
    registry: Registry,
    *,
    seed: SeedPath,
    cfg: Config | None = None,
) -> Path:
    """Rendert, analysiert und legt ein Element unveraenderlich ab.

    Raises:
        FileExistsError: Wenn unter der ID bereits ein Element abgelegt ist —
            Einfrieren ist eine einmalige Operation (plan.md 4.4: "ein
            eingefrorenes Element ist unveraenderlich").
    """
    c = cfg or get_config()
    element_dir = c.elements_dir / recipe.id
    if element_dir.exists():
        raise FileExistsError(
            f"Element {recipe.id!r} ist bereits eingefroren. "
            f"Aenderungen erzeugen ein neues Element, kein Ueberschreiben."
        )
    element_dir.mkdir(parents=True)

    preview_path = element_dir / "preview_solo.wav"
    result = render_audition_solo(recipe, registry, preview_path, seed=seed)

    data, sr = sf.read(str(preview_path), dtype="float64", always_2d=True)
    loop_s = first_visible_loop_s(data, sr)
    analysis = {
        "peak": peak(data),
        "rms": rms(data),
        "dc_offset": dc_offset(data),
        "centroid_hz": spectral_centroid(data if data.ndim == 1 else np.mean(data, axis=1), sr),
        "stereo_correlation": stereo_correlation(data),
        "loop_visible_s": loop_s if loop_s is not None else -1.0,
        "event_count": float(len(result.events)),
    }

    recipe_path = element_dir / "recipe.json"
    recipe_path.write_text(recipe.model_dump_json(indent=2), encoding="utf-8")

    import json

    (element_dir / "analysis.json").write_text(json.dumps(analysis, indent=2), encoding="utf-8")
    (element_dir / "card.md").write_text(_write_card(recipe, analysis), encoding="utf-8")

    provenance = {
        "recipe_hash": sha256_json(recipe.model_dump(mode="json")),
        "audio_hash": sha256_audio(preview_path),
        "seed": int(seed.value),
    }
    (element_dir / "provenance.json").write_text(json.dumps(provenance, indent=2), encoding="utf-8")

    return element_dir
