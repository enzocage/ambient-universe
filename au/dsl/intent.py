"""L0/L1 — Musikalische Intention und Klangidentitaet (plan2.md Stufe 3)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SonicIdentity(BaseModel):
    """Klangidentitaet eines Werks: Waerme, Helligkeit, Dichte, Raumtiefe."""

    model_config = {"frozen": True}

    warmth: float = Field(default=0.5, ge=0.0, le=1.0)
    brightness: float = Field(default=0.5, ge=0.0, le=1.0)
    hardness: float = Field(default=0.3, ge=0.0, le=1.0)
    body: float = Field(default=0.7, ge=0.0, le=1.0)
    density: float = Field(default=0.4, ge=0.0, le=1.0)
    spatial_depth: float = Field(default=0.6, ge=0.0, le=1.0)


class ComplexityProfile(BaseModel):
    """Komplexitaetsprofil ueber Form, Harmonie und Textur."""

    model_config = {"frozen": True}

    harmonic_complexity: float = Field(default=0.5, ge=0.0, le=1.0)
    rhythmic_complexity: float = Field(default=0.3, ge=0.0, le=1.0)
    timbral_complexity: float = Field(default=0.6, ge=0.0, le=1.0)


class MusicalIntent(BaseModel):
    """Das zusammenhaengende Absichtsmodell eines Kompositionsauftrags."""

    model_config = {"frozen": True}

    prompt: str
    identity: SonicIdentity
    complexity: ComplexityProfile
    target_lufs: float = Field(default=-16.0, ge=-30.0, le=-6.0)
    target_duration_s: float = Field(default=60.0, gt=0.0)
