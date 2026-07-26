"""Bogenform-Messung (plan.md sym.form.arc, Paragraph 4.8).

Prueft, ob ein gerendertes Signal die beabsichtigte Formkurve tatsaechlich
zeigt — die Einloesung von "arc_fit >= 0.7" als Zahl, nicht als Behauptung.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

_TARGET_SHAPES: dict[str, str] = {
    "emergence": "rising",
    "arch": "arch",
    "descent": "falling",
    "plateau_with_event": "plateau",
}


def _windowed_rms(
    signal: NDArray[np.float64], sample_rate: int, window_s: float = 5.0
) -> NDArray[np.float64]:
    mono = signal if signal.ndim == 1 else np.mean(signal, axis=1)
    window = max(1, int(window_s * sample_rate))
    n = max(1, mono.size // window)
    out = np.zeros(n)
    for i in range(n):
        chunk = mono[i * window : (i + 1) * window]
        out[i] = np.sqrt(np.mean(chunk**2)) if chunk.size else 0.0
    return out


def _target_curve(shape: str, n: int) -> NDArray[np.float64]:
    x = np.linspace(0.0, 1.0, n)
    kind = _TARGET_SHAPES.get(shape, "rising")
    if kind == "rising":
        return x
    if kind == "falling":
        return 1.0 - x
    if kind == "arch":
        return 1.0 - np.abs(2.0 * x - 1.0)
    # plateau: schneller Anstieg, dann konstant
    return np.minimum(1.0, x * 4.0)


def arc_fit(
    signal: NDArray[np.float64], sample_rate: int, arc_shape: str, window_s: float = 5.0
) -> float:
    """Korrelation zwischen der gemessenen RMS-Huellkurve und der Zielkurve.

    Werte nahe 1.0 bedeuten: das Signal entwickelt sich tatsaechlich in der
    beabsichtigten Richtung. Ein flaches oder gegenlaeufiges Signal faellt
    hier durch, unabhaengig davon, was der Trackplan behauptet.
    """
    rms_curve = _windowed_rms(signal, sample_rate, window_s)
    if rms_curve.size < 3 or np.std(rms_curve) < 1e-9:
        return 0.0
    target = _target_curve(arc_shape, rms_curve.size)
    if np.std(target) < 1e-9:
        return 0.0
    return float(np.corrcoef(rms_curve, target)[0, 1])
