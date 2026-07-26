"""Dramaturgie-Organizer: der Gesamtbogen eines Tracks (plan.md Paragraph 4.8).

Erzeugt eine Intensitaetskurve ueber die volle Trackdauer: startet bei Null,
schwingt ueber ein bis zwei Hoehepunkte (mit leichter Permutation zwischen
den Durchlaeufen, nicht symmetrisch-mechanisch), und kehrt am Ende wieder auf
Null zurueck. Diese Kurve treibt reale Klangparameter (Makro-Grundstellung
kontinuierlicher Schichten) statt nur dekorativ im Trackplan zu stehen.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from au.core.seeds import SeedPath


@dataclass(frozen=True, slots=True)
class DramaturgyArc:
    """Eine stueckweise lineare Intensitaetskurve auf [0, 1]."""

    times_s: tuple[float, ...]
    """Aufsteigend, beginnt bei 0.0 und endet bei der Trackdauer."""
    intensities: tuple[float, ...]
    """Gleich lang wie ``times_s``; erster und letzter Wert sind 0.0."""

    def intensity_at(self, t: float) -> float:
        if t <= self.times_s[0]:
            return self.intensities[0]
        if t >= self.times_s[-1]:
            return self.intensities[-1]
        for i in range(len(self.times_s) - 1):
            a_t, b_t = self.times_s[i], self.times_s[i + 1]
            if a_t <= t <= b_t:
                span = b_t - a_t
                frac = (t - a_t) / span if span > 0 else 0.0
                return self.intensities[i] + (self.intensities[i + 1] - self.intensities[i]) * frac
        return self.intensities[-1]

    def sample(self, n: int) -> list[tuple[float, float]]:
        """``n`` gleichmaessig verteilte (Zeit, Intensitaet)-Punkte -- die
        Aufloesung, mit der die Kurve in echte Automation umgesetzt wird."""
        duration = self.times_s[-1]
        return [(t, self.intensity_at(t)) for t in np.linspace(0.0, duration, n)]


def generate_arc(
    duration_s: float,
    *,
    seed: SeedPath,
    peaks: int = 2,
    peak_intensity_range: tuple[float, float] = (0.65, 1.0),
) -> DramaturgyArc:
    """Erzeugt einen Bogen: 0 -> Anstieg -> (ein bis zwei Hoehepunkte,
    dazwischen Ruecknahme, nie exakt symmetrisch) -> 0.

    ``peaks`` ist eine Obergrenze, kein Garant -- bei sehr kurzer Dauer wird
    automatisch reduziert, damit die Stufen nicht enger als noetig gedraengt
    werden (kurze Ambient-Ausschnitte brauchen keine zwei volle Zyklen).
    """
    rng = np.random.default_rng(seed.child("dramaturgy", "arc").value & 0xFFFF_FFFF)
    effective_peaks = max(1, min(peaks, max(1, int(duration_s // 25))))

    # Stufen: 0 -> Anstieg -> Peak -> Ruecknahme -> [Anstieg -> Peak -> Ruecknahme] -> 0
    fractions = [0.0]
    for i in range(effective_peaks):
        segment_start = i / effective_peaks
        segment_end = (i + 1) / effective_peaks
        rise = segment_start + (segment_end - segment_start) * rng.uniform(0.35, 0.55)
        fall = segment_start + (segment_end - segment_start) * rng.uniform(0.75, 0.92)
        fractions.extend([rise, fall])
    fractions.append(1.0)
    fractions = sorted(set(round(f, 6) for f in fractions))

    intensities = [0.0]
    for i in range(1, len(fractions) - 1):
        # Peaks (ungerade Indizes in unserer Konstruktion) hoch, Taeler tiefer,
        # aber nie ganz auf Null zurueck -- ausser am eigentlichen Ende.
        is_peak = i % 2 == 1
        if is_peak:
            intensities.append(float(rng.uniform(*peak_intensity_range)))
        else:
            intensities.append(float(rng.uniform(0.15, 0.4)))
    intensities.append(0.0)

    times = tuple(f * duration_s for f in fractions)
    return DramaturgyArc(times_s=times, intensities=tuple(intensities))
