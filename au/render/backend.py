"""Non-Realtime-Renderbackend (SuperCollider via Supriya).

SuperCollider steht unter GPL-3.0 und laeuft deshalb bewusst als **eigener
Prozess**: Supriya schreibt eine NRT-Score-Datei und ruft ``scsynth -N`` auf.
Der Python-Kern beruehrt keinen SC-Code.

Reproduzierbarkeit (plan.md Paragraph 13.2): Bei identischer Backend-Version,
identischer Blockgroesse und identischem Seed ist das Ergebnis bit-genau
wiederholbar. Aendert sich die Backend-Version, greift die Metrik-Toleranz
statt Hash-Gleichheit — das haelt ``manifest.json`` ausdruecklich fest.

**Warum der Exit-Code nicht das Erfolgskriterium ist**

SuperCollider 3.14.1 unter Windows segfaultet beim Beenden, sobald der Graph
eine Delay-Leitung enthaelt (``DelayN/C/L``, ``Allpass*``, alles mit
RT-Pufferfreigabe). Das Audio wird dabei **vollstaendig und korrekt**
geschrieben; der Absturz passiert erst im Aufraeumen, nach dem letzten Block.
Nachgewiesen: 48064 von 48064 erwarteten Frames, Signal bis zum letzten
Sample, danach Exit 0xC0000005.

Deshalb prueft dieses Modul das **Artefakt**, nicht den Rueckgabewert: Existenz,
Abtastrate, Kanalzahl und Laenge. Ein Absturz mit vollstaendiger Datei wird als
Warnung mitgefuehrt, ein Absturz ohne Datei bleibt ein harter Fehler. Ohne
diese Unterscheidung waere die Haelfte des Modulkatalogs auf dieser Plattform
unbenutzbar — und mit blindem Ignorieren des Exit-Codes wuerden echte
Fehlschlaege durchrutschen.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING, cast

from au.core.config import Config, get_config
from au.core.hashing import sha256_audio, sha256_file

if TYPE_CHECKING:  # pragma: no cover
    import supriya


class BackendError(RuntimeError):
    """Das Audio-Backend fehlt, ist unbrauchbar oder das Rendering scheiterte."""


@dataclass(frozen=True, slots=True)
class RenderResult:
    """Ergebnis eines NRT-Renderlaufs.

    Attributes:
        audio_sha256: Der massgebliche Reproduzierbarkeits-Fingerabdruck ueber
            den dekodierten Audioinhalt. ``manifest.json`` speichert diesen.
        file_sha256: Hash der Containerdatei. **Nicht stabil** — libsndfile
            legt bei Float-WAVs einen ``PEAK``-Chunk mit Zeitstempel an. Nur
            zur Diagnose, nie als Vergleichsgrundlage.
    """

    path: Path
    duration_s: float
    wallclock_s: float
    sample_rate: int
    exit_code: int
    audio_sha256: str
    file_sha256: str
    frames: int = 0
    warnings: tuple[str, ...] = ()
    """Auffaelligkeiten, die das Ergebnis nicht ungueltig machen — etwa der
    bekannte Absturz beim Beenden nach vollstaendigem Rendering."""

    @property
    def realtime_factor(self) -> float:
        """Wie viel schneller als Echtzeit gerendert wurde (groesser ist besser)."""
        if self.wallclock_s <= 0:
            return float("inf")
        return self.duration_s / self.wallclock_s

    def summary(self) -> str:
        note = f"  [{len(self.warnings)} Hinweis]" if self.warnings else ""
        return (
            f"{self.path.name}  {self.duration_s:.1f}s Audio in "
            f"{self.wallclock_s:.2f}s  ({self.realtime_factor:.1f}x Echtzeit)  "
            f"audio={self.audio_sha256[:12]}{note}"
        )


def _import_supriya() -> ModuleType:
    """Laedt supriya spaet, damit `au doctor` auch ohne Backend laeuft."""
    try:
        import supriya
    except ImportError as exc:  # pragma: no cover
        raise BackendError(
            'supriya ist nicht installiert. Abhilfe: uv pip install -e ".[audio]"'
        ) from exc
    return supriya


def scsynth_options(cfg: Config | None = None, **overrides: object) -> supriya.Options:
    """Baut die scsynth-Optionen aus der Projektkonfiguration.

    ``executable`` wird explizit gesetzt, damit nicht versehentlich eine
    andere SuperCollider-Installation auf dem PATH verwendet wird — das waere
    ein stiller Determinismusbruch.
    """
    module = _import_supriya()
    c = cfg or get_config()
    exe = c.scsynth_path()
    if exe is None:
        raise BackendError(
            "scsynth wurde nicht gefunden. Abhilfe: "
            "winget install --id SuperCollider.SuperCollider "
            "oder [backend].scsynth in au.toml setzen."
        )
    params: dict[str, object] = {
        "executable": str(exe),
        "block_size": c.audio.block_size,
        "sample_rate": c.audio.sample_rate,
        "output_bus_channel_count": c.audio.channels,
        "input_bus_channel_count": 0,
        "realtime": False,
    }
    params.update(overrides)
    return cast("supriya.Options", module.Options(**params))


#: Anteil der erwarteten Frames, der vorhanden sein muss, damit ein Rendering
#: trotz Absturzcode als vollstaendig gilt. scsynth schreibt blockweise; ein
#: Ausfall mitten im Lauf faellt damit sicher auf.
_COMPLETENESS_THRESHOLD = 0.999


def _verify_artifact(
    path: Path,
    *,
    expected_frames: int,
    expected_rate: int,
    expected_channels: int,
    exit_code: int,
    render_dir: Path,
) -> tuple[int, tuple[str, ...]]:
    """Prueft die gerenderte Datei. Gibt Framezahl und Warnungen zurueck.

    Raises:
        BackendError: Wenn die Datei unlesbar, zu kurz oder im falschen Format
            ist. Ein Absturzcode allein genuegt dafuer nicht — entscheidend ist,
            ob das Audio vollstaendig da ist.
    """
    import soundfile as sf

    try:
        info = sf.info(str(path))
    except Exception as exc:
        raise BackendError(
            f"Die gerenderte Datei {path.name} ist nicht lesbar ({exc}). "
            f"scsynth-Code {exit_code}. Score-Verzeichnis: {render_dir}"
        ) from exc

    warnings: list[str] = []

    if info.samplerate != expected_rate:
        raise BackendError(f"{path.name}: Abtastrate {info.samplerate} statt {expected_rate}.")
    if info.channels != expected_channels:
        raise BackendError(f"{path.name}: {info.channels} Kanaele statt {expected_channels}.")
    if info.frames < expected_frames * _COMPLETENESS_THRESHOLD:
        raise BackendError(
            f"{path.name}: nur {info.frames} von {expected_frames} Frames "
            f"({info.frames / max(1, expected_frames):.1%}). scsynth-Code {exit_code}. "
            f"Das Rendering wurde abgebrochen. Score-Verzeichnis: {render_dir}"
        )

    if exit_code != 0:
        warnings.append(
            f"scsynth endete mit Code {exit_code}, lieferte aber alle "
            f"{info.frames} Frames. Bekannt fuer SC 3.14.1 unter Windows bei "
            f"Delay-UGens: der Absturz passiert beim Aufraeumen nach dem "
            f"letzten Block. Das Audio ist unversehrt."
        )

    return int(info.frames), tuple(warnings)


async def render_score_async(
    score: supriya.Score,
    output_path: Path,
    *,
    duration: float,
    cfg: Config | None = None,
    header_format: str = "WAV",
    sample_format: str = "FLOAT",
    options: supriya.Options | None = None,
) -> RenderResult:
    """Rendert einen Supriya-Score offline in eine Audiodatei.

    Args:
        score: Der vorbereitete NRT-Score.
        output_path: Zieldatei. Elternverzeichnisse werden angelegt.
        duration: Renderdauer in Sekunden.
        header_format: Containerformat, Vorgabe WAV.
        sample_format: Vorgabe FLOAT (32-bit) — voller Headroom im
            Produktionspfad; die 24-bit-Reduktion passiert erst beim Export.

    Raises:
        BackendError: Wenn scsynth fehlt, mit Fehlercode endet oder keine
            Datei erzeugt.
    """
    c = cfg or get_config()
    opts = options or scsynth_options(c)
    output_path = output_path.expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    render_dir = c.cache_dir / "nrt"
    render_dir.mkdir(parents=True, exist_ok=True)

    started = time.perf_counter()
    try:
        produced, exit_code = await score.render(
            output_path,
            duration=duration,
            header_format=header_format,
            sample_format=sample_format,
            sample_rate=c.audio.sample_rate,
            options=opts,
            render_directory_path=render_dir,
            # suppress_output=True bedeutet in Supriya NICHT "Konsole ruhig
            # stellen", sondern "Audio nach NUL bzw. /dev/null schreiben" —
            # das Rendering wird also verworfen. Unter Windows endet scsynth
            # dabei zusaetzlich mit Code 1. Immer False lassen.
            suppress_output=False,
        )
    except Exception as exc:  # supriya wirft je nach Fehlerart unterschiedlich
        raise BackendError(f"NRT-Rendering fehlgeschlagen: {exc}") from exc
    wallclock = time.perf_counter() - started

    candidate = Path(produced) if produced is not None else output_path
    if not candidate.is_file():
        raise BackendError(
            f"scsynth endete mit Code {exit_code} und erzeugte keine Datei unter "
            f"{output_path}. Score-Verzeichnis zur Diagnose: {render_dir}"
        )

    frames, warnings = _verify_artifact(
        candidate,
        expected_frames=round(duration * c.audio.sample_rate),
        expected_rate=c.audio.sample_rate,
        expected_channels=c.audio.channels,
        exit_code=exit_code,
        render_dir=render_dir,
    )

    return RenderResult(
        path=candidate,
        duration_s=duration,
        wallclock_s=wallclock,
        sample_rate=c.audio.sample_rate,
        exit_code=exit_code,
        audio_sha256=sha256_audio(candidate),
        file_sha256=sha256_file(candidate),
        frames=frames,
        warnings=warnings,
    )


def render_score(
    score: supriya.Score,
    output_path: Path,
    *,
    duration: float,
    cfg: Config | None = None,
    header_format: str = "WAV",
    sample_format: str = "FLOAT",
    options: supriya.Options | None = None,
) -> RenderResult:
    """Synchrone Huelle um :func:`render_score_async`.

    Der gesamte Produktionspfad (CLI, Solver, Batch-Rendering) ist synchron;
    nur Supriyas Score-Rendering ist eine Koroutine. Wer bereits in einer
    Event-Loop laeuft — etwa im Studio-Backend (Phase 6) — ruft direkt die
    async-Variante auf.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        pass  # kein Loop aktiv: der Normalfall
    else:
        raise BackendError(
            "render_score() wurde aus einer laufenden Event-Loop aufgerufen. "
            "In async-Kontexten stattdessen render_score_async() verwenden."
        )
    return asyncio.run(
        render_score_async(
            score,
            output_path,
            duration=duration,
            cfg=cfg,
            header_format=header_format,
            sample_format=sample_format,
            options=options,
        )
    )
