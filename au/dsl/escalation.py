"""Mehrdimensionale, musikalisch begruendete Aufschaukelung (Plan 5)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

EscalationDimension = Literal[
    "density", "harmony", "register", "brightness", "loudness", "transient", "space", "roles"
]


class EscalationStep(BaseModel):
    model_config = {"frozen": True}

    step_id: str
    phrase_index: int = Field(ge=0)
    label: Literal["statement", "variation", "counterline", "transformation", "vacuum", "peak", "release"]
    active_roles: tuple[str, ...]
    dimensions: tuple[EscalationDimension, ...]
    dimension_targets: dict[EscalationDimension, float]
    motif_transform: str
    relation_triggers: tuple[str, ...] = ()


class EscalationGraph(BaseModel):
    model_config = {"frozen": True}

    steps: tuple[EscalationStep, ...]
    peak_step_id: str

    def step_for_phrase(self, phrase_index: int) -> EscalationStep:
        if not self.steps:
            raise ValueError("EscalationGraph braucht mindestens einen Schritt")
        return self.steps[min(max(phrase_index, 0), len(self.steps) - 1)]

    def validate_progression(self) -> tuple[str, ...]:
        errors: list[str] = []
        if self.peak_step_id not in {step.step_id for step in self.steps}:
            errors.append("Peak-Schritt fehlt")
        for before, after in zip(self.steps, self.steps[1:], strict=False):
            changed = set(after.dimensions) - set(before.dimensions)
            if len(changed) > 2:
                errors.append(f"{after.step_id}: mehr als zwei neue Eskalationsdimensionen")
        return tuple(errors)


def build_escalation_graph(active_roles: tuple[str, ...]) -> EscalationGraph:
    """Baut eine konservative Folge von Identitaet zu Peak und Release."""
    rhythm_roles = tuple(
        role for role in active_roles
        if role in {"bass_sequence", "arpeggiator", "subtle_percussive_background"}
    )
    base_roles = tuple(role for role in active_roles if role not in set(rhythm_roles))
    steps = (
        EscalationStep(
            step_id="statement", phrase_index=0, label="statement", active_roles=base_roles,
            dimensions=("roles",), dimension_targets={"roles": 0.25}, motif_transform="exact",
        ),
        EscalationStep(
            step_id="variation", phrase_index=1, label="variation", active_roles=active_roles,
            dimensions=("density", "brightness"), dimension_targets={"density": 0.42, "brightness": 0.45},
            motif_transform="rhythmic_variation", relation_triggers=("bass_to_harmony",),
        ),
        EscalationStep(
            step_id="counterline", phrase_index=2, label="counterline", active_roles=active_roles,
            dimensions=("register", "transient"), dimension_targets={"register": 0.55, "transient": 0.48},
            motif_transform="answer_phrase", relation_triggers=("motif_to_response", "arp_to_resonator"),
        ),
        EscalationStep(
            step_id="transformation", phrase_index=3, label="transformation", active_roles=active_roles,
            dimensions=("harmony", "space"), dimension_targets={"harmony": 0.66, "space": 0.68},
            motif_transform="timbre_register_transform", relation_triggers=("chord_to_pattern",),
        ),
        EscalationStep(
            step_id="vacuum", phrase_index=4, label="vacuum", active_roles=base_roles,
            dimensions=("density", "loudness"), dimension_targets={"density": 0.16, "loudness": 0.25},
            motif_transform="fragment_before_peak", relation_triggers=("transition_gap",),
        ),
        EscalationStep(
            step_id="peak", phrase_index=5, label="peak", active_roles=active_roles,
            dimensions=("density", "brightness"), dimension_targets={"density": 0.9, "brightness": 0.82},
            motif_transform="known_core_new_environment", relation_triggers=("bass_ducking", "fill_to_space"),
        ),
        EscalationStep(
            step_id="release", phrase_index=6, label="release", active_roles=base_roles,
            dimensions=("space", "loudness"), dimension_targets={"space": 0.52, "loudness": 0.28},
            motif_transform="return_and_dissolve", relation_triggers=("remove_high_motion",),
        ),
    )
    graph = EscalationGraph(steps=steps, peak_step_id="peak")
    errors = graph.validate_progression()
    if errors:
        raise ValueError("Ungueltige Eskalation: " + "; ".join(errors))
    return graph
