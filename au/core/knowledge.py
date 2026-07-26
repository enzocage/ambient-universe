"""Zugriff auf die ausfuehrbare Ambient-Wissensbasis.

Die Regeln in ``knowledge/*.yaml`` sind keine Dokumentation, sondern werden
vom SynthDef-Compiler und vom Grammatikpruefer unmittelbar angewendet.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from au.core.config import Config, get_config


class SmoothingRules(BaseModel):
    model_config = {"frozen": True}

    default_ms: float = 200.0
    minimum_ms: float = 5.0
    profiles: dict[str, dict[str, float]] = Field(default_factory=dict)

    def for_class(self, param_class: str, profile: str = "ambient_slow") -> float:
        table = self.profiles.get(profile, {})
        return table.get(param_class, self.default_ms)


class SafetyRules(BaseModel):
    model_config = {"frozen": True}

    peak_ceiling_dbfs: float = -6.0
    dc_cutoff_hz: float = 10.0
    softclip_ceiling: float = 0.5
    softclip_hardness: float = 0.3
    max_feedback_damping: float = 0.98
    nyquist_guard: float = 0.45
    aliasing_floor_db: float = -60.0


class ModulationRules(BaseModel):
    model_config = {"frozen": True}

    max_rate_hz: dict[str, float] = Field(default_factory=dict)
    slow_lfo_hz: tuple[float, float] = (0.001, 0.2)
    drift_hz: tuple[float, float] = (0.0005, 0.05)
    analog_drift_cents: tuple[float, float] = (2.0, 12.0)


class EnvelopeRules(BaseModel):
    model_config = {"frozen": True}

    min_attack_ms: float = 80.0
    impulsive_min_attack_ms: float = 3.0
    max_stage_s: float = 600.0
    min_spectral_travel: float = 0.18
    min_event_variance: float = 0.15


class Antipattern(BaseModel):
    model_config = {"frozen": True}

    id: str
    rule: str
    why: str


class DspRules(BaseModel):
    """Der ausfuehrbare Teil des Klangdesignwissens."""

    model_config = {"frozen": True}

    schema_version: str = "1.0"
    smoothing: SmoothingRules = Field(default_factory=SmoothingRules)
    safety: SafetyRules = Field(default_factory=SafetyRules)
    modulation: ModulationRules = Field(default_factory=ModulationRules)
    envelopes: EnvelopeRules = Field(default_factory=EnvelopeRules)
    antipatterns: list[Antipattern] = Field(default_factory=list)

    @classmethod
    def load(cls, path: Path) -> DspRules:
        raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls.model_validate(raw or {})


@lru_cache(maxsize=4)
def _load_cached(path: Path) -> DspRules:
    """Zwischenspeicher nach Pfad — Config selbst ist nicht hashbar."""
    if not path.is_file():
        return DspRules()
    return DspRules.load(path)


def dsp_rules(cfg: Config | None = None) -> DspRules:
    """Laedt ``knowledge/dsp_rules.yaml``; fehlende Datei nutzt die Vorgaben."""
    c = cfg or get_config()
    return _load_cached(c.knowledge_dir / "dsp_rules.yaml")
