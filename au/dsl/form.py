"""L5/L6 — Form- und Zeitplanung (plan2.md Stufe 3 & 5)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

FormArchetype = Literal["arch", "emergence", "wave", "accumulation", "episodic", "contrast"]


class SectionPlan(BaseModel):
    """Plan eines Formabschnitts mit expliziter Rollen- & Motivzuordnung."""

    model_config = {"frozen": True}

    section_id: str
    name: str
    start_s: float = Field(ge=0.0)
    end_s: float
    target_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    active_roles: tuple[str, ...]
    allow_motifs: bool = True

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s


class FormPlan(BaseModel):
    """Gesamter musikalischer Formplan eines Tracks."""

    model_config = {"frozen": True}

    archetype: FormArchetype = "emergence"
    total_duration_s: float = Field(gt=0.0)
    sections: tuple[SectionPlan, ...]

    def section_at(self, t: float) -> SectionPlan:
        for sec in self.sections:
            if sec.start_s <= t < sec.end_s:
                return sec
        return self.sections[-1]
