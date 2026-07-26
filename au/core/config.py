"""Konfiguration und Pfadaufloesung.

Die Konfiguration wird aus ``au.toml`` im Projektwurzelverzeichnis gelesen.
Alle Felder haben Vorgaben, sodass das System auch ohne ``au.toml`` startet.

Entscheidung E7 aus plan.md: 48 kHz, intern 32-bit float, Export 24-bit.
"""

from __future__ import annotations

import os
import shutil
import tomllib
from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Bekannte Installationsorte des Audio-Backends (Windows / Linux / macOS)
# ---------------------------------------------------------------------------

_SCSYNTH_CANDIDATES: tuple[str, ...] = (
    r"C:\Program Files\SuperCollider-3.14.1\scsynth.exe",
    r"C:\Program Files\SuperCollider-3.13.0\scsynth.exe",
    r"C:\Program Files\SuperCollider\scsynth.exe",
    "/usr/bin/scsynth",
    "/usr/local/bin/scsynth",
    "/Applications/SuperCollider.app/Contents/Resources/scsynth",
)


def _find_binary(name: str, candidates: tuple[str, ...] = ()) -> Path | None:
    """Sucht eine ausfuehrbare Datei auf dem PATH und danach in bekannten Orten.

    Die Suche jenseits des PATH ist unter Windows noetig: frisch per winget
    installierte Werkzeuge erscheinen erst in einer neuen Shell auf dem PATH.
    """
    on_path = shutil.which(name)
    if on_path:
        return Path(on_path)
    for candidate in candidates:
        p = Path(candidate)
        if p.is_file():
            return p
    # Windows: winget legt Verknuepfungen und Paketverzeichnisse unter LOCALAPPDATA ab.
    if os.name == "nt":
        local = Path(os.environ.get("LOCALAPPDATA", ""))
        link = local / "Microsoft" / "WinGet" / "Links" / f"{name}.exe"
        if link.is_file():
            return link
        pkgs = local / "Microsoft" / "WinGet" / "Packages"
        if pkgs.is_dir():
            found = next(iter(sorted(pkgs.glob(f"*/**/bin/{name}.exe"), reverse=True)), None)
            if found is not None:
                return found
    # Windows: SuperCollider-Verzeichnisse mit Versionssuffix aufspueren
    if os.name == "nt" and name == "scsynth":
        for root in (Path(r"C:\Program Files"), Path(r"C:\Program Files (x86)")):
            if not root.is_dir():
                continue
            for sub in sorted(root.glob("SuperCollider*"), reverse=True):
                exe = sub / "scsynth.exe"
                if exe.is_file():
                    return exe
    return None


# ---------------------------------------------------------------------------
# Modelle
# ---------------------------------------------------------------------------


class AudioConfig(BaseModel):
    """Audioformat des Produktionspfads."""

    sample_rate: int = 48_000
    block_size: int = 64
    internal_bit_depth: int = 32  # float
    export_bit_depth: int = 24
    channels: int = 2

    @field_validator("block_size")
    @classmethod
    def _block_is_power_of_two(cls, v: int) -> int:
        if v <= 0 or (v & (v - 1)) != 0:
            raise ValueError(f"block_size muss eine Zweierpotenz sein, war {v}")
        return v


class RenderConfig(BaseModel):
    """Grenzen fuer Renderjobs (Phase 13 setzt diese hart durch)."""

    nrt_timeout_s: int = 600
    max_parallel_jobs: int = 4
    audition_seconds: float = 45.0
    audition_sample_rate: int = 48_000
    audition_lufs_target: float = -23.0


class PathsConfig(BaseModel):
    """Projektpfade. Alle relativ zur Projektwurzel, falls nicht absolut."""

    elements: Path = Path("elements")
    projects: Path = Path("projects")
    synthdefs: Path = Path("synthdefs")
    knowledge: Path = Path("knowledge")
    modules: Path = Path("au/modules")
    cache: Path = Path(".au_cache")


class BackendConfig(BaseModel):
    """Externe Werkzeuge. ``None`` bedeutet: automatisch suchen."""

    scsynth: Path | None = None
    ffmpeg: Path | None = None


class Config(BaseModel):
    """Wurzelkonfiguration."""

    root: Path = Field(default_factory=Path.cwd)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    render: RenderConfig = Field(default_factory=RenderConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    backend: BackendConfig = Field(default_factory=BackendConfig)

    # -- abgeleitete Pfade ---------------------------------------------------

    def resolve(self, p: Path) -> Path:
        return p if p.is_absolute() else (self.root / p)

    @property
    def elements_dir(self) -> Path:
        return self.resolve(self.paths.elements)

    @property
    def projects_dir(self) -> Path:
        return self.resolve(self.paths.projects)

    @property
    def synthdefs_dir(self) -> Path:
        return self.resolve(self.paths.synthdefs)

    @property
    def knowledge_dir(self) -> Path:
        return self.resolve(self.paths.knowledge)

    @property
    def modules_dir(self) -> Path:
        return self.resolve(self.paths.modules)

    @property
    def cache_dir(self) -> Path:
        return self.resolve(self.paths.cache)

    # -- Backends ------------------------------------------------------------

    def scsynth_path(self) -> Path | None:
        if self.backend.scsynth is not None:
            return self.backend.scsynth if self.backend.scsynth.is_file() else None
        return _find_binary("scsynth", _SCSYNTH_CANDIDATES)

    def ffmpeg_path(self) -> Path | None:
        if self.backend.ffmpeg is not None:
            return self.backend.ffmpeg if self.backend.ffmpeg.is_file() else None
        return _find_binary("ffmpeg")

    def ensure_dirs(self) -> None:
        """Legt alle Arbeitsverzeichnisse an (idempotent)."""
        for d in (
            self.elements_dir,
            self.projects_dir,
            self.synthdefs_dir,
            self.cache_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Laden
# ---------------------------------------------------------------------------


def find_project_root(start: Path | None = None) -> Path:
    """Sucht aufwaerts nach ``au.toml`` oder ``pyproject.toml``."""
    cur = (start or Path.cwd()).resolve()
    for candidate in (cur, *cur.parents):
        if (candidate / "au.toml").is_file() or (candidate / "pyproject.toml").is_file():
            return candidate
    return cur


def load_config(root: Path | None = None) -> Config:
    """Laedt die Konfiguration; fehlende Datei ist kein Fehler."""
    project_root = find_project_root(root)
    cfg_file = project_root / "au.toml"
    data: dict[str, object] = {}
    if cfg_file.is_file():
        with cfg_file.open("rb") as fh:
            data = tomllib.load(fh)
    data["root"] = project_root
    return Config.model_validate(data)


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Prozessweit zwischengespeicherte Konfiguration."""
    return load_config()
