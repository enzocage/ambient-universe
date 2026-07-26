"""Hierarchisches Score-Modell fuer Plan 5.

Die Modelle geben jedem Ereignis eine musikalische Herkunft. Dadurch kann der
Composer nicht mehr nur eine flache Layerliste rendern, sondern Form, Phrase,
Motiv und Klanggeste als zusammenhaengende Struktur pruefen.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

HierarchyLevel = Literal["gesture", "event", "motif", "phrase", "section", "form"]


class HierarchyRef(BaseModel):
    model_config = {"frozen": True}

    form_id: str
    section_id: str
    phrase_id: str
    motif_id: str
    gesture_id: str


class PhrasePlan(BaseModel):
    model_config = {"frozen": True}

    phrase_id: str
    motif_ids: tuple[str, ...]
    start_s: float = Field(ge=0.0)
    duration_s: float = Field(gt=0.0)
    function: Literal["statement", "answer", "transition", "release"]
    variation_index: int = Field(ge=0)


class SectionPlan(BaseModel):
    model_config = {"frozen": True}

    section_id: str
    name: str
    start_s: float = Field(ge=0.0)
    end_s: float
    phrase_ids: tuple[str, ...]
    active_roles: tuple[str, ...]
    energy: float = Field(ge=0.0, le=1.0)
    density: float = Field(ge=0.0, le=1.0)
    spectral_brightness: float = Field(ge=0.0, le=1.0)
    spatial_width: float = Field(ge=0.0, le=1.0)


class FormPlan(BaseModel):
    model_config = {"frozen": True}

    form_id: str
    duration_s: float = Field(gt=0.0)
    sections: tuple[SectionPlan, ...]
    return_motif_id: str
    peak_section_id: str

    @property
    def energy_curve(self) -> tuple[float, ...]:
        return tuple(section.energy for section in self.sections)


class HierarchicalScore(BaseModel):
    """Unveraenderliche Gesamtstruktur vor dem Audio-Render."""

    model_config = {"frozen": True}

    form: FormPlan
    phrases: tuple[PhrasePlan, ...]
    refs: tuple[HierarchyRef, ...] = ()

    def section_for(self, time_s: float) -> SectionPlan:
        for section in self.form.sections:
            if section.start_s <= time_s < section.end_s:
                return section
        return self.form.sections[-1]

    def validate_lineage(self) -> tuple[str, ...]:
        """Liefert strukturelle Fehler statt stiller Metadatenbehauptungen."""
        errors: list[str] = []
        section_ids = {section.section_id for section in self.form.sections}
        phrase_ids = {phrase.phrase_id for phrase in self.phrases}
        for section in self.form.sections:
            missing = set(section.phrase_ids) - phrase_ids
            if missing:
                errors.append(f"{section.section_id}: fehlende Phrasen {sorted(missing)}")
        if self.form.peak_section_id not in section_ids:
            errors.append("peak_section_id verweist auf keinen Abschnitt")
        return tuple(errors)


def build_default_hierarchical_score(
    *,
    duration_s: float,
    motif_id: str,
    active_roles: tuple[str, ...],
) -> HierarchicalScore:
    """Erzeugt einen musikalisch lesbaren Startbogen fuer den Composer."""
    points = (0.0, 0.18, 0.42, 0.80, 1.0)
    names = ("intro", "build", "peak", "release")
    energies = (0.18, 0.48, 0.92, 0.24)
    sections: list[SectionPlan] = []
    phrases: list[PhrasePlan] = []
    for index, name in enumerate(names):
        start = duration_s * points[index]
        end = duration_s * points[index + 1]
        phrase_id = f"phrase_{name}"
        function = "statement" if index == 0 else "answer" if index == 1 else "transition" if index == 2 else "release"
        phrases.append(
            PhrasePlan(
                phrase_id=phrase_id,
                motif_ids=(motif_id,),
                start_s=start,
                duration_s=max(0.1, end - start),
                function=function,
                variation_index=index,
            )
        )
        section_roles = active_roles if index in (1, 2) else tuple(
            role for role in active_roles if role not in {"arpeggiator", "subtle_percussive_background"}
        )
        sections.append(
            SectionPlan(
                section_id=f"section_{name}",
                name=name,
                start_s=start,
                end_s=end,
                phrase_ids=(phrase_id,),
                active_roles=section_roles,
                energy=energies[index],
                density=min(1.0, energies[index] + 0.12),
                spectral_brightness=min(1.0, 0.25 + energies[index] * 0.7),
                spatial_width=min(1.0, 0.35 + energies[index] * 0.55),
            )
        )
    form = FormPlan(
        form_id="form_main",
        duration_s=duration_s,
        sections=tuple(sections),
        return_motif_id=motif_id,
        peak_section_id="section_peak",
    )
    score = HierarchicalScore(form=form, phrases=tuple(phrases))
    errors = score.validate_lineage()
    if errors:
        raise ValueError("Ungueltige Hierarchie: " + "; ".join(errors))
    return score
