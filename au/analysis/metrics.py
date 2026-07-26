"""Signalmetriken fuer den Makro-Sweep-Test und spaetere Kritiker (Phase 2+).

Diese Funktionen arbeiten auf dekodiertem Audio (numpy), nicht auf dem
Signalgraphen — sie messen, was tatsaechlich aus dem Renderer kam, nicht was
er beabsichtigt hat. Das ist der Punkt: Manifeste *behaupten* Garantien,
diese Datei *prueft* sie.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True, slots=True)
class ClickReport:
    count: int
    positions_s: tuple[float, ...]
    """Zeitpunkte der ersten paar Vorkommen, zur Diagnose."""


def detect_clicks(
    signal: NDArray[np.float64],
    sample_rate: int,
    *,
    jump_threshold: float = 0.25,
    min_gap_s: float = 0.02,
    max_reported: int = 10,
) -> ClickReport:
    """Zaehlt abrupte Sample-zu-Sample-Spruenge.

    Ambient-Signale sind durchgehend geglaettet; ein Sprung ueber
    ``jump_threshold`` innerhalb eines Samples ist in einem sauberen Rendering
    nicht durch Modulation erklaerbar, sondern ein Artefakt. ``min_gap_s``
    verhindert, dass ein einzelnes physisches Klickereignis (das ueber
    mehrere Samples nachschwingt) mehrfach gezaehlt wird.
    """
    mono = signal if signal.ndim == 1 else np.max(np.abs(signal), axis=1)
    diffs = np.abs(np.diff(mono))
    hits = np.flatnonzero(diffs > jump_threshold)

    min_gap_samples = int(min_gap_s * sample_rate)
    kept: list[int] = []
    last: int = -min_gap_samples - 1
    for raw_idx in hits:
        idx = int(raw_idx)
        if idx - last >= min_gap_samples:
            kept.append(idx)
            last = idx

    positions = tuple(round(i / sample_rate, 4) for i in kept[:max_reported])
    return ClickReport(count=len(kept), positions_s=positions)


def clip_ratio(signal: NDArray[np.float64], ceiling: float = 0.999) -> float:
    """Anteil der Samples auf oder ueber der Vollaussteuerung."""
    return float(np.mean(np.abs(signal) >= ceiling))


def peak(signal: NDArray[np.float64]) -> float:
    return float(np.max(np.abs(signal))) if signal.size else 0.0


def rms(signal: NDArray[np.float64]) -> float:
    return float(np.sqrt(np.mean(np.square(signal)))) if signal.size else 0.0


def dc_offset(signal: NDArray[np.float64]) -> float:
    """Mittelwert je Kanal, dann das betragsgroesste — ein Kanal reicht zum
    Scheitern, auch wenn der andere sauber ist."""
    if signal.ndim == 1:
        return float(np.mean(signal))
    means = np.mean(signal, axis=0)
    return float(means[np.argmax(np.abs(means))])


def high_frequency_energy_ratio(
    signal: NDArray[np.float64], sample_rate: int, *, cutoff_ratio: float = 0.45
) -> float:
    """Anteil der Signalenergie oberhalb ``cutoff_ratio * sample_rate``.

    Ein Aliasing-Test im strengen Sinn braucht ein Referenzsignal ohne
    Nyquist-Verletzung; ohne das dient dieser Wert als Naeherung: bandbegrenzte
    Ambient-Quellen sollten praktisch keine Energie nahe der Nyquist-Grenze
    tragen. Ein Ausreisser hier ist ein Hinweis, kein Beweis.
    """
    mono = signal if signal.ndim == 1 else np.mean(signal, axis=1)
    if mono.size < 4:
        return 0.0
    spectrum = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)
    total = float(np.sum(spectrum**2))
    if total <= 0.0:
        return 0.0
    cutoff_hz = cutoff_ratio * sample_rate
    high = float(np.sum(spectrum[freqs >= cutoff_hz] ** 2))
    return high / total


def spectral_centroid(signal: NDArray[np.float64], sample_rate: int) -> float:
    """Energiegewichteter Frequenzschwerpunkt — Mass fuer Helligkeit."""
    mono = signal if signal.ndim == 1 else np.mean(signal, axis=1)
    if mono.size < 4:
        return 0.0
    spectrum = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(mono.size, d=1.0 / sample_rate)
    total = float(np.sum(spectrum))
    if total <= 0.0:
        return 0.0
    return float(np.sum(freqs * spectrum) / total)


def windowed_centroids(
    signal: NDArray[np.float64], sample_rate: int, *, window_s: float = 1.0
) -> NDArray[np.float64]:
    """Spektralschwerpunkt je Zeitfenster — die Grundlage fuer Monotonie- und
    ``spectral_travel``-Pruefungen (L3, plan.md 4.3)."""
    mono = signal if signal.ndim == 1 else np.mean(signal, axis=1)
    window = max(1, int(window_s * sample_rate))
    n_windows = max(1, mono.size // window)
    values = np.zeros(n_windows, dtype=np.float64)
    for i in range(n_windows):
        chunk = mono[i * window : (i + 1) * window]
        values[i] = spectral_centroid(chunk, sample_rate)
    return values


def spectral_travel(centroids: NDArray[np.float64]) -> float:
    """Wie weit der Spektralschwerpunkt ueber die Geste gewandert ist, in Oktaven.

    Frequenzwahrnehmung ist logarithmisch: eine Wanderung von 200 auf 400 Hz
    ist perzeptiv dieselbe Bewegung wie 2000 auf 4000 Hz. Ein linearer
    Hertz-Abstand wuerde tiefe Klaenge systematisch als "bewegungslos"
    einstufen. Gemessen wird die Spannweite (max-min in Oktaven) ueber alle
    Zeitfenster, nicht nur Anfang gegen Ende — eine Geste, die hoch und wieder
    zurueckkehrt, hat sich trotzdem entwickelt.
    """
    positive = centroids[centroids > 1.0]
    if positive.size < 2:
        return 0.0
    log2 = np.log2(positive)
    return float(np.max(log2) - np.min(log2))


def first_visible_loop_s(
    signal: NDArray[np.float64], sample_rate: int, *, max_lag_s: float = 60.0
) -> float | None:
    """Schaetzt, ab wann eine Wiederholung im Signal hoerbar wuerde.

    Berechnet die normierte Autokorrelation der Huellkurve (nicht des
    Rohsignals — Feinstruktur wie Rauschen korreliert nie, die Grobform einer
    Wiederholung schon) und meldet die kleinste Verzoegerung mit auffaellig
    hoher Korrelation. ``None`` heisst: keine Wiederholung im geprueften
    Fenster gefunden — fuer Ambient der wuenschenswerte Fall.
    """
    mono = signal if signal.ndim == 1 else np.mean(signal, axis=1)
    # Envelope durch Downsampling auf ~50 Hz Aufloesung: schnell genug fuer
    # lange Signale, grob genug, um Formwiederholung statt Feinstruktur zu sehen.
    hop = max(1, sample_rate // 50)
    envelope = np.abs(mono[:: max(1, hop)])
    if envelope.size < 20:
        return None
    envelope = envelope - envelope.mean()
    norm = np.sum(envelope**2)
    if norm <= 1e-12:
        return None

    max_lag = int(max_lag_s * sample_rate / hop)
    max_lag = min(max_lag, envelope.size - 10)
    if max_lag <= 1:
        return None

    for lag in range(5, max_lag):
        corr = np.sum(envelope[:-lag] * envelope[lag:]) / norm
        if corr > 0.85:
            return float(lag * hop / sample_rate)
    return None


def stereo_correlation(signal: NDArray[np.float64]) -> float:
    """Pearson-Korrelation zwischen den Kanaelen. 1.0 = mono, 0.0 = unkorreliert."""
    if signal.ndim != 2 or signal.shape[1] < 2:
        return 1.0
    left, right = signal[:, 0], signal[:, 1]
    if np.std(left) < 1e-12 or np.std(right) < 1e-12:
        return 1.0
    return float(np.corrcoef(left, right)[0, 1])


@dataclass(frozen=True, slots=True)
class MusicalQualityReport:
    """Objektiver Bericht ueber die musikalischen & technischen Eigenschaften eines Tracks."""

    peak_dbfs: float
    rms_dbfs: float
    lufs_estimated: float
    active_signal_ratio: float
    harmonic_energy_ratio: float
    dc_offset: float
    clip_ratio: float
    click_count: int
    accepted: bool
    reasons: tuple[str, ...]

    def summary(self) -> str:
        status = "AKZEPTIERT" if self.accepted else "ABGELEHNT"
        return (
            f"[{status}] LUFS: {self.lufs_estimated:.1f} dB · Peak: {self.peak_dbfs:.1f} dBFS · "
            f"Aktiv: {self.active_signal_ratio:.0%} · Harmonie: {self.harmonic_energy_ratio:.0%} · "
            f"Begruendung: {', '.join(self.reasons) if self.reasons else 'Optimal'}"
        )


def analyze_musical_quality(
    signal: NDArray[np.float64],
    sample_rate: int,
    *,
    min_active_ratio: float = 0.75,
    min_lufs: float = -28.0,
    max_lufs: float = -10.0,
    target_lufs_range: tuple[float, float] = (-18.0, -14.0),
) -> MusicalQualityReport:
    """Analysiert das Audiosignal objektiv auf Musikalitaet, Pegel, Stille und Artefakte."""
    if signal.size == 0:
        return MusicalQualityReport(
            peak_dbfs=-100.0,
            rms_dbfs=-100.0,
            lufs_estimated=-100.0,
            active_signal_ratio=0.0,
            harmonic_energy_ratio=0.0,
            dc_offset=0.0,
            clip_ratio=0.0,
            click_count=0,
            accepted=False,
            reasons=("Audiosignal ist leer",),
        )

    peak_val = peak(signal)
    rms_val = rms(signal)
    peak_dbfs = 20.0 * np.log10(max(1e-6, peak_val))
    rms_dbfs = 20.0 * np.log10(max(1e-6, rms_val))

    lufs_est = rms_dbfs + 3.0

    frame_size = max(1, sample_rate // 10)
    mono = signal if signal.ndim == 1 else np.mean(np.abs(signal), axis=1)
    num_frames = mono.size // frame_size
    if num_frames > 0:
        reshaped = mono[: num_frames * frame_size].reshape(num_frames, frame_size)
        frame_rms = np.sqrt(np.mean(np.square(reshaped), axis=1))
        active_frames = np.sum(frame_rms > 0.003)
        active_ratio = float(active_frames / num_frames)
    else:
        active_ratio = 1.0

    start_idx = int(mono.size * 0.15)
    end_idx = min(mono.size, start_idx + sample_rate * 10)
    sample_segment = mono[start_idx:end_idx] if end_idx > start_idx else mono
    fft_vals = np.abs(np.fft.rfft(sample_segment))
    if fft_vals.size > 0:
        fft_peaks = np.sort(fft_vals)[::-1]
        tonal_energy = float(np.sum(fft_peaks[: min(30, fft_peaks.size)]))
        total_energy = float(np.sum(fft_vals)) + 1e-9
        harmonic_ratio = float(min(1.0, (tonal_energy / total_energy) * 5.0))
    else:
        harmonic_ratio = 0.5

    dc_val = dc_offset(signal)
    clip_val = clip_ratio(signal)

    clicks = detect_clicks(signal, sample_rate)

    reasons: list[str] = []
    accepted = True

    if active_ratio < min_active_ratio:
        accepted = False
        reasons.append(f"Zu viel Stille (Aktiver Anteil {active_ratio:.0%} < {min_active_ratio:.0%})")

    if lufs_est < min_lufs:
        accepted = False
        reasons.append(f"Signal zu leise ({lufs_est:.1f} LUFS < {min_lufs:.1f} LUFS)")

    if clip_val > 0.001:
        accepted = False
        reasons.append(f"Clipping festgestellt ({clip_val:.2%} Samples)")

    if clicks.count > 0:
        accepted = False
        reasons.append(f"{clicks.count} Klick-Artefakt(e) erkannt")

    if harmonic_ratio < 0.10:
        accepted = False
        reasons.append("Track besteht ueberwiegend aus unbestimmtem Rauschen ohne Tonalitaet")

    return MusicalQualityReport(
        peak_dbfs=float(peak_dbfs),
        rms_dbfs=float(rms_dbfs),
        lufs_estimated=float(lufs_est),
        active_signal_ratio=float(active_ratio),
        harmonic_energy_ratio=float(harmonic_ratio),
        dc_offset=float(dc_val),
        clip_ratio=float(clip_val),
        click_count=clicks.count,
        accepted=accepted,
        reasons=tuple(reasons),
    )

