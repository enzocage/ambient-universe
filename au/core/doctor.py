"""``au doctor`` — prueft die Toolchain (plan.md Phase 0).

Liefert eine Liste von Pruefungen mit Status, gemessenem Wert und, im Fehlerfall,
einer konkreten Handlungsanweisung. Der Befehl darf nie eine Ausnahme werfen —
eine fehlende Abhaengigkeit ist ein Befund, kein Absturz.
"""

from __future__ import annotations

import importlib
import importlib.metadata as md
import platform
import subprocess
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from au.core.config import Config, get_config


class Status(StrEnum):
    OK = "ok"
    WARN = "warn"
    FAIL = "fail"


@dataclass(frozen=True, slots=True)
class Check:
    name: str
    status: Status
    detail: str
    remedy: str = ""

    @property
    def blocking(self) -> bool:
        return self.status is Status.FAIL


# ---------------------------------------------------------------------------
# Einzelpruefungen
# ---------------------------------------------------------------------------


def check_python() -> Check:
    v = sys.version_info
    detail = f"{v.major}.{v.minor}.{v.micro} ({platform.machine()})"
    if (v.major, v.minor) < (3, 12):
        return Check(
            "Python",
            Status.FAIL,
            detail,
            "Python 3.12 oder neuer wird benoetigt (pyproject: requires-python).",
        )
    return Check("Python", Status.OK, detail)


def _check_package(dist: str, module: str, *, required: bool) -> Check:
    try:
        importlib.import_module(module)
    except ImportError:
        status = Status.FAIL if required else Status.WARN
        extra = {
            "supriya": "audio",
            "librosa": "analysis",
            "pyloudnorm": "analysis",
            "isobar": "symbolic",
        }.get(dist)
        hint = f'uv pip install -e ".[{extra}]"' if extra else f"uv pip install {dist}"
        return Check(dist, status, "nicht installiert", hint)
    try:
        version = md.version(dist)
    except md.PackageNotFoundError:
        version = "unbekannt"
    return Check(dist, Status.OK, version)


def check_core_packages() -> list[Check]:
    return [
        _check_package("pydantic", "pydantic", required=True),
        _check_package("numpy", "numpy", required=True),
        _check_package("soundfile", "soundfile", required=True),
        _check_package("PyYAML", "yaml", required=True),
        _check_package("typer", "typer", required=True),
        _check_package("rich", "rich", required=True),
    ]


def check_optional_packages() -> list[Check]:
    return [
        _check_package("supriya", "supriya", required=False),
        _check_package("librosa", "librosa", required=False),
        _check_package("pyloudnorm", "pyloudnorm", required=False),
        _check_package("isobar", "isobar", required=False),
    ]


def _binary_version(path: Path, args: list[str], timeout: float = 15.0) -> str:
    try:
        proc = subprocess.run(
            [str(path), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"nicht abfragbar ({type(exc).__name__})"
    out = (proc.stdout or proc.stderr or "").strip().splitlines()
    return out[0][:80] if out else "vorhanden"


def check_scsynth(cfg: Config) -> Check:
    path = cfg.scsynth_path()
    if path is None:
        return Check(
            "scsynth",
            Status.FAIL,
            "nicht gefunden",
            "winget install --id SuperCollider.SuperCollider  "
            "(oder [backend].scsynth in au.toml setzen)",
        )
    # scsynth -v gibt die Version aus und beendet sich.
    return Check("scsynth", Status.OK, f"{path}  |  {_binary_version(path, ['-v'])}")


def check_ffmpeg(cfg: Config) -> Check:
    path = cfg.ffmpeg_path()
    if path is None:
        return Check(
            "ffmpeg",
            Status.WARN,
            "nicht gefunden",
            "winget install --id Gyan.FFmpeg  (erst ab Phase 10 fuer den Export noetig)",
        )
    return Check("ffmpeg", Status.OK, _binary_version(path, ["-version"]))


def check_paths(cfg: Config) -> list[Check]:
    checks: list[Check] = []
    for label, d in (
        ("elements/", cfg.elements_dir),
        ("projects/", cfg.projects_dir),
        ("synthdefs/", cfg.synthdefs_dir),
        (".au_cache/", cfg.cache_dir),
    ):
        try:
            d.mkdir(parents=True, exist_ok=True)
            probe = d / ".au_write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink()
            checks.append(Check(label, Status.OK, str(d)))
        except OSError as exc:
            checks.append(
                Check(label, Status.FAIL, f"nicht beschreibbar: {exc}", f"Rechte auf {d} pruefen.")
            )
    return checks


def check_audio_config(cfg: Config) -> Check:
    a = cfg.audio
    detail = (
        f"{a.sample_rate} Hz / Block {a.block_size} / "
        f"intern {a.internal_bit_depth}-bit float / Export {a.export_bit_depth}-bit"
    )
    return Check("Audioformat", Status.OK, detail)


# ---------------------------------------------------------------------------
# Gesamtlauf
# ---------------------------------------------------------------------------


def run_all(cfg: Config | None = None) -> list[Check]:
    c = cfg or get_config()
    checks: list[Check] = [check_python()]
    checks += check_core_packages()
    checks += check_optional_packages()
    checks.append(check_scsynth(c))
    checks.append(check_ffmpeg(c))
    checks.append(check_audio_config(c))
    checks += check_paths(c)
    return checks
