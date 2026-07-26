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
