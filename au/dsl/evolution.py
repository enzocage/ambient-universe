"""EvolutionPlan — Mehrdimensionale Bewegung und Anti-Monotonie-Engine (Plan 3, Paragraph 4.1).

Stellt sicher, dass keine Stimme statisch bleibt, sondern sich über 6 unabhängige
Dimensionen (Timbre, Harmonie, Zeit, Artikulation, Raum, Energie) dynamisch verändert.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math
import random

from au.core.seeds import SeedPath


@dataclass(frozen=True, slots=True)
class DimensionCurve:
    """Eine kontinuierliche Zeit-Kurve für eine einzelne Kontrolldimension."""

    dimension_name: str
    points: tuple[tuple[float, float], ...]  # List of (time_s, normalized_value 0..1)

    def sample(self, time_s: float) -> float:
        """Interpoliert den Kurvenwert zur Zeit time_s."""
        if not self.points:
            return 0.5
        if time_s <= self.points[0][0]:
            return self.points[0][1]
        if time_s >= self.points[-1][0]:
            return self.points[-1][1]

        # Lineare Interpolation zwischen Nachbarpunkten
        for i in range(len(self.points) - 1):
            t0, v0 = self.points[i]
            t1, v1 = self.points[i + 1]
            if t0 <= time_s <= t1:
                ratio = (time_s - t0) / max(1e-6, t1 - t0)
                return v0 + (v1 - v0) * ratio

        return self.points[-1][1]

    def has_movement_within_window(self, start_s: float, window_s: float = 10.0, threshold: float = 0.08) -> bool:
        """Prüft, ob sich die Kurve innerhalb eines Zeitfensters merklich entwickelt."""
        end_s = start_s + window_s
        val_start = self.sample(start_s)
        val_end = self.sample(end_s)
        val_mid = self.sample(start_s + window_s * 0.5)
        max_diff = max(abs(val_end - val_start), abs(val_mid - val_start), abs(val_end - val_mid))
        return max_diff >= threshold


@dataclass(frozen=True, slots=True)
class EvolutionPlan:
    """Mehrdimensionaler Entwicklungsplan für eine Layer-Instanz."""

    layer_id: str
    duration_s: float
    timbre: DimensionCurve
    harmony: DimensionCurve
    time_density: DimensionCurve
    articulation: DimensionCurve
    space: DimensionCurve
    energy: DimensionCurve

    def validate_anti_monotony(self, window_s: float = 10.0) -> list[str]:
        """Prüft Plan 3 Anti-Monotonie-Gate: Mindestens 2 Dimensionen müssen sich alle 8-12s bewegen."""
        issues: list[str] = []
        t = 0.0
        while t + window_s <= self.duration_s:
            active_dims = 0
            for curve in (self.timbre, self.harmony, self.time_density, self.articulation, self.space, self.energy):
                if curve.has_movement_within_window(t, window_s):
                    active_dims += 1

            if active_dims < 2:
                issues.append(f"Layer {self.layer_id}: Stagnation im Zeitfenster {t:.1f}s–{t+window_s:.1f}s (nur {active_dims} aktive Dimensionen)")

            t += window_s * 0.5  # Überlappende Fensterprüfung

        return issues


def generate_evolution_plan(
    layer_id: str,
    duration_s: float,
    seed: SeedPath,
    *,
    is_continuous: bool = True,
) -> EvolutionPlan:
    """Generiert einen mehrdimensionalen Entwicklungsplan mit garantierten Wellenbewegungen."""
    rng = random.Random(int(seed.value & 0xFFFF_FFFF))

    def make_curve(name: str, num_nodes: int = 6, phase_offset: float = 0.0) -> DimensionCurve:
        pts: list[tuple[float, float]] = []
        step = duration_s / max(1, num_nodes - 1)
        for i in range(num_nodes):
            t = i * step
            # Kombination aus niederfrequenter Sine-Welle + Jitter
            sine_val = 0.5 + 0.35 * math.sin((t / duration_s) * math.pi * 2.0 + phase_offset)
            jitter = rng.uniform(-0.15, 0.15)
            val = max(0.05, min(0.95, sine_val + jitter))
            pts.append((round(t, 2), round(val, 3)))
        return DimensionCurve(dimension_name=name, points=tuple(pts))

    # Versetzte Phasen für unterschiedliche Dimensionen garantieren kontinuierliche Dynamik
    timbre_curve = make_curve("timbre", num_nodes=7, phase_offset=0.0)
    harmony_curve = make_curve("harmony", num_nodes=5, phase_offset=math.pi * 0.5)
    time_curve = make_curve("time_density", num_nodes=6, phase_offset=math.pi * 1.0)
    articulation_curve = make_curve("articulation", num_nodes=6, phase_offset=math.pi * 1.5)
    space_curve = make_curve("space", num_nodes=5, phase_offset=math.pi * 0.25)
    energy_curve = make_curve("energy", num_nodes=7, phase_offset=math.pi * 0.75)

    return EvolutionPlan(
        layer_id=layer_id,
        duration_s=duration_s,
        timbre=timbre_curve,
        harmony=harmony_curve,
        time_density=time_curve,
        articulation=articulation_curve,
        space=space_curve,
        energy=energy_curve,
    )
