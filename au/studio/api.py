"""FastAPI-Backend des Web-Studios.

Startbar per ``au serve`` oder ``uvicorn au.studio.api:app``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

from au.core.config import get_config
from au.core.registry import load_registry
from au.studio.jobs import Job, get_job, list_jobs, start_job

app = FastAPI(title="Ambient Universe Studio")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_STATIC_DIR = Path(__file__).parent / "static"


class ComposeRequest(BaseModel):
    prompt: str
    duration_s: float = 90.0


class LayerPreviewRequest(BaseModel):
    macro_overrides: dict[str, float] = {}
    duration_s: float = 12.0


def _job_summary(job: Job) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "job_id": job.job_id,
        "prompt": job.prompt,
        "duration_s": job.duration_s,
        "status": job.status,
        "log": job.log,
        "error": job.error,
    }
    if job.result is not None:
        r = job.result
        # Nur die tatsaechlich befuellten Slots anzeigen -- au compose besetzt
        # aus Geschwindigkeitsgruenden hoechstens max_slots der vom Blueprint
        # vorgeschlagenen Rollen, der Rest bliebe sonst irrefuehrend gelistet.
        used_roles = {layer.role for layer in r.solve_result.layers}
        summary["result"] = {
            "title": r.dna.title,
            "descriptors": list(r.dna.character.descriptors),
            "innovation_vector": r.dna.innovation_vector.model_dump(),
            "open_questions": r.open_questions,
            "blueprint": {
                "mode": r.blueprint.field.mode,
                "root_midi": r.blueprint.field.root_midi,
                "slots": [
                    {
                        "slot_id": s.slot_id,
                        "role": s.role,
                        "band_hz": list(s.band_hz),
                        "rationale": s.rationale,
                    }
                    for s in r.blueprint.role_slots
                    if s.role in used_roles
                ],
            },
            "solver": {
                "score": r.solve_result.score,
                "feasible": r.solve_result.feasible,
                "conflicts": len(r.solve_result.conflicts),
                "log": list(r.solve_result.log),
            },
            "mix_url": f"/api/jobs/{job.job_id}/audio/mix",
            "stems": [
                {"name": name, "url": f"/api/jobs/{job.job_id}/audio/stem/{name}"}
                for name in r.track.stem_paths
            ],
            "graph_url": f"/api/jobs/{job.job_id}/graph",
            "quality_report": {
                "peak_dbfs": r.quality_report.peak_dbfs,
                "lufs_estimated": r.quality_report.lufs_estimated,
                "active_signal_ratio": r.quality_report.active_signal_ratio,
                "harmonic_energy_ratio": r.quality_report.harmonic_energy_ratio,
                "accepted": r.quality_report.accepted,
                "summary": r.quality_report.summary(),
                "reasons": list(r.quality_report.reasons),
            },
            "harmony": {
                "mode": r.blueprint.field.mode,
                "chords": [
                    {
                        "time_s": round(c.time_s, 1),
                        "duration_s": round(c.duration_s, 1),
                        "degrees": list(c.degrees),
                    }
                    for c in r.chords.chords[:8]
                ],
            },
            "motifs": [
                {"id": m.id, "name": m.name, "length": len(m.notes)}
                for m in r.motifs
            ],
            "sections": {
                "intro": [round(x, 1) for x in r.section_arrangement.intro],
                "build": [round(x, 1) for x in r.section_arrangement.build],
                "peak": [round(x, 1) for x in r.section_arrangement.peak],
                "outro": [round(x, 1) for x in r.section_arrangement.outro],
            },
        }
    return summary



@app.get("/", response_class=HTMLResponse)
def index() -> str:
    index_path = _STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")


@app.post("/api/compose")
def compose(req: ComposeRequest) -> dict[str, str]:
    if not req.prompt.strip():
        raise HTTPException(400, "Prompt darf nicht leer sein.")
    duration = max(20.0, min(300.0, req.duration_s))
    job = start_job(req.prompt.strip(), duration)
    return {"job_id": job.job_id}


@app.get("/api/jobs")
def jobs() -> list[dict[str, Any]]:
    return [_job_summary(j) for j in list_jobs()]


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(404, "Unbekannter Auftrag.")
    return _job_summary(job)


@app.get("/api/jobs/{job_id}/graph")
def job_graph(job_id: str) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None or job.result is None:
        raise HTTPException(404, "Kein fertiges Ergebnis fuer diesen Auftrag.")

    r = job.result
    nodes: list[dict[str, Any]] = [
        {
            "id": "pitch_root",
            "type": "root",
            "label": f"Root MIDI {r.blueprint.field.root_midi} ({r.blueprint.field.mode})",
        }
    ]
    edges: list[dict[str, Any]] = []

    for layer in r.solve_result.layers:
        recipe = r.recipes.get(layer.element_id)
        voice_module = recipe.voice_module_id if recipe else "unknown"
        macros = dict(recipe.voice_macros) if recipe else {}
        node_id = f"layer_{layer.layer_id}"
        nodes.append(
            {
                "id": node_id,
                "type": "layer",
                "layer_id": layer.layer_id,
                "role": layer.role,
                "voice_module_id": voice_module,
                "band_hz": list(layer.band_hz),
                "entry_time_s": layer.entry_time_s,
                "exit_time_s": layer.exit_time_s,
                "transposition": layer.transposition,
                "macros": macros,
            }
        )
        edges.append(
            {
                "src": "pitch_root",
                "dst": node_id,
                "label": f"st: {layer.transposition:+.1f}",
            }
        )

    for conflict in r.solve_result.conflicts:
        edges.append(
            {
                "src": f"layer_{conflict.layer_a}",
                "dst": f"layer_{conflict.layer_b}",
                "label": f"Conflict ({conflict.band_overlap:.0%})",
                "kind": "conflict",
            }
        )

    return {"nodes": nodes, "edges": edges}


@app.post("/api/jobs/{job_id}/layers/{layer_id}/preview")
def preview_layer(job_id: str, layer_id: str, req: LayerPreviewRequest) -> dict[str, Any]:
    from au.core.seeds import SeedPath
    from au.render.element import render_element

    job = get_job(job_id)
    if job is None or job.result is None or job.output_dir is None:
        raise HTTPException(404, "Kein fertiges Ergebnis fuer diesen Auftrag.")

    r = job.result
    target_layer = next((layer for layer in r.solve_result.layers if layer.layer_id == layer_id), None)
    if target_layer is None:
        raise HTTPException(404, f"Layer {layer_id!r} nicht gefunden.")

    base_recipe = r.recipes.get(target_layer.element_id)
    if base_recipe is None:
        raise HTTPException(404, f"Rezept fuer Layer {layer_id!r} nicht gefunden.")

    merged_macros = dict(base_recipe.voice_macros)
    merged_macros.update(req.macro_overrides)

    dur = max(3.0, min(30.0, req.duration_s))
    preview_recipe = base_recipe.transposed(target_layer.transposition).model_copy(
        update={
            "voice_macros": merged_macros,
            "duration_s": dur,
        }
    )

    cfg = get_config()
    registry = load_registry(cfg)
    seed_val = abs(hash(target_layer.layer_id)) % 1000000
    seed = SeedPath.root(seed_val).child("preview")
    preview_dir = job.output_dir / "previews"
    preview_dir.mkdir(parents=True, exist_ok=True)
    out_path = preview_dir / f"{layer_id}_preview.wav"

    try:
        render_res, _ = render_element(preview_recipe, registry, seed=seed, output_path=out_path, cfg=cfg)
        url = f"/api/jobs/{job_id}/layers/{layer_id}/preview.wav"
        return {
            "job_id": job_id,
            "layer_id": layer_id,
            "preview_url": url,
            "duration_s": render_res.duration_s,
            "macros": merged_macros,
        }
    except Exception as exc:
        raise HTTPException(500, f"Fehler beim Rendern der Vorschau: {exc}") from exc



@app.get("/api/jobs/{job_id}/layers/{layer_id}/preview.wav")
def get_layer_preview_wav(job_id: str, layer_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None or job.output_dir is None:
        raise HTTPException(404, "Auftrag nicht gefunden.")
    preview_path = job.output_dir / "previews" / f"{layer_id}_preview.wav"
    if not preview_path.exists():
        raise HTTPException(404, "Keine Vorschau-Datei vorhanden.")
    return FileResponse(preview_path, media_type="audio/wav")


@app.get("/api/jobs/{job_id}/audio/mix")
def job_mix(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None or job.result is None:
        raise HTTPException(404, "Kein fertiges Ergebnis fuer diesen Auftrag.")
    return FileResponse(job.result.track.mix_path, media_type="audio/wav")


@app.get("/api/jobs/{job_id}/audio/stem/{name}")
def job_stem(job_id: str, name: str) -> FileResponse:
    job = get_job(job_id)
    if job is None or job.result is None:
        raise HTTPException(404, "Kein fertiges Ergebnis fuer diesen Auftrag.")
    path = job.result.track.stem_paths.get(name)
    if path is None:
        raise HTTPException(404, f"Kein Stem namens {name!r}.")
    return FileResponse(path, media_type="audio/wav")


@app.get("/api/modules")
def modules() -> list[dict[str, Any]]:
    cfg = get_config()
    registry = load_registry(cfg)
    return [
        {
            "id": m.id,
            "level": m.level,
            "category": m.category,
            "display_name": m.display_name,
            "tags": list(m.tags),
            "cpu_units": m.cost.cpu_units,
        }
        for m in registry
    ]

