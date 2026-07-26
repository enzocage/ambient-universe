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


def stereo_correlation(signal: NDArray[np.float64]) -> float:
    """Pearson-Korrelation zwischen den Kanaelen. 1.0 = mono, 0.0 = unkorreliert."""
    if signal.ndim != 2 or signal.shape[1] < 2:
        return 1.0
    left, right = signal[:, 0], signal[:, 1]
    if np.std(left) < 1e-12 or np.std(right) < 1e-12:
        return 1.0
    return float(np.corrcoef(left, right)[0, 1])
