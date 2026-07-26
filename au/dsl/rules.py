"""Auswertung von Negativregeln gegen gemessene Metriken (plan.md 8.1, 12.1).

Jede Negativregel ist ein :class:`au.dsl.dna.NegativeRule` mit einem
strukturierten Praedikat. Diese Datei bildet Metriknamen auf tatsaechliche
Messfunktionen ab, damit eine Regel wie "keine Stimme" pruefbar wird, ohne
dass eine hoehere Ebene wissen muss, *wie* das gemessen wird.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from au.analysis.metrics import (
    dc_offset,
    first_visible_loop_s,
    high_frequency_energy_ratio,
    peak,
    spectral_centroid,
    stereo_correlation,
)
from au.dsl.dna import NegativeRule

#: Bekannte Metriknamen, die eine Negativregel referenzieren darf.
KNOWN_METRICS = frozenset(
    {
        "peak",
        "dc_offset_abs",
        "spectral_centroid_hz",
        "high_freq_energy_ratio",
        "stereo_correlation",
        "loop_visible_s",
    }
)


def _measure(name: str, signal: NDArray[np.float64], sample_rate: int) -> float:
    if name == "peak":
        return peak(signal)
    if name == "dc_offset_abs":
        return abs(dc_offset(signal))
    if name == "spectral_centroid_hz":
        return spectral_centroid(
            signal if signal.ndim == 1 else np.mean(signal, axis=1), sample_rate
        )
    if name == "high_freq_energy_ratio":
        return high_frequency_energy_ratio(signal, sample_rate)
    if name == "stereo_correlation":
        return stereo_correlation(signal)
    if name == "loop_visible_s":
        found = first_visible_loop_s(signal, sample_rate)
        return found if found is not None else float("inf")
    raise ValueError(f"Unbekannte Metrik {name!r}. Bekannt: {sorted(KNOWN_METRICS)}")


@dataclass(frozen=True, slots=True)
class RuleVerdict:
    rule_id: str
    summary: str
    passed: bool
    measured: float
    predicate: str


def evaluate_negative_rule(
    rule: NegativeRule, signal: NDArray[np.float64], sample_rate: int
) -> RuleVerdict:
    """Prueft eine einzelne Negativregel gegen ein gerendertes Signal."""
    value = _measure(rule.predicate.metric, signal, sample_rate)
    passed = rule.predicate.check(value)
    predicate_str = f"{rule.predicate.metric} {rule.predicate.operator} {rule.predicate.threshold}"
    return RuleVerdict(
        rule_id=rule.id,
        summary=rule.summary,
        passed=passed,
        measured=value,
        predicate=predicate_str,
    )


def evaluate_all(
    rules: tuple[NegativeRule, ...], signal: NDArray[np.float64], sample_rate: int
) -> list[RuleVerdict]:
    return [evaluate_negative_rule(r, signal, sample_rate) for r in rules]
