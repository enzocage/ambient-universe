"""Hintergrund-Jobverwaltung fuer die Web-Oberflaeche.

``compose_track`` ist blockierend (mehrere Sekunden Rendering); die
Oberflaeche muss trotzdem reagieren. Jeder Auftrag laeuft in einem eigenen
Thread, sein Fortschritt landet in einem Log, das der Browser per Polling
abfragt — kein WebSocket noetig fuer diesen Umfang.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from au.core.config import Config, get_config
from au.integrator.compose import ComposeResult, compose_track

JobStatus = Literal["pending", "running", "done", "error"]


@dataclass
class Job:
    job_id: str
    prompt: str
    duration_s: float
    status: JobStatus = "pending"
    log: list[str] = field(default_factory=list)
    result: ComposeResult | None = None
    error: str | None = None
    output_dir: Path | None = None

    def append(self, message: str) -> None:
        self.log.append(message)


_JOBS: dict[str, Job] = {}
_LOCK = threading.Lock()


def _run(job: Job, cfg: Config) -> None:
    job.status = "running"
    try:
        output_dir = cfg.projects_dir / "studio" / job.job_id
        job.output_dir = output_dir
        result = compose_track(
            job.prompt,
            output_dir,
            duration_s=job.duration_s,
            cfg=cfg,
            on_progress=job.append,
        )
        job.result = result
        job.status = "done"
    except Exception as exc:  # noqa: BLE001 -- dem Nutzer im Browser anzeigen, nicht verschlucken
        job.status = "error"
        job.error = str(exc)
        job.append(f"Fehler: {exc}")


def start_job(prompt: str, duration_s: float, cfg: Config | None = None) -> Job:
    c = cfg or get_config()
    job = Job(job_id=uuid.uuid4().hex[:12], prompt=prompt, duration_s=duration_s)
    with _LOCK:
        _JOBS[job.job_id] = job
    thread = threading.Thread(target=_run, args=(job, c), daemon=True)
    thread.start()
    return job


def get_job(job_id: str) -> Job | None:
    with _LOCK:
        return _JOBS.get(job_id)


def list_jobs() -> list[Job]:
    with _LOCK:
        return sorted(_JOBS.values(), key=lambda j: j.job_id, reverse=True)
