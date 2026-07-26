"""Szenen-, Rack-, Automation- und Resampling-Workflow nach Plan 6.

Die Modelle sind bewusst backend-neutral: Sie beschreiben Produktionsentscheidungen,
bevor der Renderer daraus Audio erzeugt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field


class AutomationLane(BaseModel):
    model_config = {"frozen": True}

    parameter: str
    points: tuple[tuple[float, float], ...]
    source: Literal["form", "groove", "relation", "performance"]


class ProductionRack(BaseModel):
    model_config = {"frozen": True}

    rack_id: str
    role: str
    voice_module_id: str
    articulation: str
    processors: tuple[str, ...] = ()
    macros: dict[str, float] = Field(default_factory=dict)
    compatible_roles: tuple[str, ...] = ()
    objective_score: float = Field(ge=0.0, le=1.0)
    personal_score: float = Field(ge=0.0, le=1.0)


class ResamplePass(BaseModel):
    model_config = {"frozen": True}

    source_scene_id: str
    operation: Literal["freeze", "reverse", "granular", "pitch_shift", "filter", "time_stretch"]
    amount: float = Field(ge=0.0, le=1.0)
    target_role: str
    entry_s: float = Field(ge=0.0)


class ProductionScene(BaseModel):
    model_config = {"frozen": True}

    scene_id: str
    name: str
    start_s: float = Field(ge=0.0)
    end_s: float
    active_roles: tuple[str, ...]
    rack_ids: tuple[str, ...]
    energy: float = Field(ge=0.0, le=1.0)
    density: float = Field(ge=0.0, le=1.0)
    automation: tuple[AutomationLane, ...] = ()
    transition: str = "crossfade"


class ProductionWorkflow(BaseModel):
    model_config = {"frozen": True}

    scenes: tuple[ProductionScene, ...]
    racks: tuple[ProductionRack, ...]
    resamples: tuple[ResamplePass, ...]
    render_budget_name: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        rack_ids = {rack.rack_id for rack in self.racks}
        for scene in self.scenes:
            missing = set(scene.rack_ids) - rack_ids
            if missing:
                errors.append(f"{scene.scene_id}: fehlende Racks {sorted(missing)}")
            if scene.end_s <= scene.start_s:
                errors.append(f"{scene.scene_id}: ungueltige Dauer")
        for before, after in zip(self.scenes, self.scenes[1:], strict=False):
            if before.end_s > after.start_s + 1e-6:
                errors.append(f"Szenen ueberlappen: {before.scene_id}/{after.scene_id}")
        if len(self.scenes) >= 2:
            contrasts = [
                before.active_roles != after.active_roles,
                before.energy != after.energy,
                before.density != after.density,
            ]
            if not any(contrasts):
                errors.append("Keine hoerbare Szenenkontrastdimension")
        return tuple(errors)

    def validate_budget(self, *, expected_scenes: int, expected_roles: int) -> tuple[str, ...]:
        errors = list(self.validate())
        if len(self.scenes) != expected_scenes:
            errors.append(f"Budget verlangt {expected_scenes} Szenen, erzeugt wurden {len(self.scenes)}")
        if len(self.racks) != expected_roles:
            errors.append(f"Budget verlangt {expected_roles} Racks, erzeugt wurden {len(self.racks)}")
        return tuple(errors)


def build_production_workflow(
    *, duration_s: float, budget_name: str, section_count: int = 7,
    roles: tuple[str, ...], rack_modules: dict[str, str]
) -> ProductionWorkflow:
    """Erzeugt eine kontrastierende Szenenfolge statt einer linearen Dauersumme."""
    profiles = {
        2: (("intro", "peak"), (0.2, 0.9), (0.15, 0.82)),
        4: (("intro", "build", "peak", "outro"), (0.18, 0.5, 0.92, 0.22), (0.14, 0.48, 0.9, 0.18)),
        6: (("intro", "groove", "build", "vacuum", "peak", "outro"), (0.18, 0.36, 0.58, 0.12, 0.95, 0.22), (0.16, 0.35, 0.58, 0.08, 0.9, 0.18)),
        8: (("intro", "groove", "build", "lift", "vacuum", "peak", "transform", "outro"), (0.16, 0.3, 0.46, 0.68, 0.1, 0.95, 0.65, 0.2), (0.12, 0.28, 0.46, 0.7, 0.06, 0.92, 0.52, 0.16)),
    }
    names, energies, densities = profiles.get(section_count, profiles[7] if 7 in profiles else profiles[8])
    if section_count == 7:
        names = ("intro", "groove", "build", "vacuum", "peak", "transform", "outro")
        energies = (0.18, 0.36, 0.58, 0.12, 0.95, 0.68, 0.22)
        densities = (0.16, 0.35, 0.58, 0.08, 0.9, 0.52, 0.18)
    fractions = tuple(index / len(names) for index in range(len(names) + 1))
    racks = tuple(
        ProductionRack(
            rack_id=f"rack_{role}",
            role=role,
            voice_module_id=rack_modules.get(role, "unknown"),
            articulation="pluck" if role in {"arpeggiator", "bass_sequence"} else "evolving",
            processors=("filter_motion", "room_send"),
            compatible_roles=tuple(r for r in roles if r != role),
            objective_score=0.7,
            personal_score=0.5,
        )
        for role in roles
    )
    scenes: list[ProductionScene] = []
    for index, name in enumerate(names):
        start = duration_s * fractions[index]
        end = duration_s * fractions[index + 1]
        active = roles if name in {"groove", "build", "peak", "transform"} else tuple(
            role for role in roles if role not in {"arpeggiator", "subtle_percussive_background"}
        )
        automation = (
            AutomationLane(
                parameter="brightness",
                points=((0.0, max(0.0, energies[index] - 0.12)), (max(0.01, end - start), min(1.0, energies[index] + 0.16))),
                source="form",
            ),
        )
        scenes.append(
            ProductionScene(
                scene_id=f"scene_{name}",
                name=name,
                start_s=start,
                end_s=end,
                active_roles=active,
                rack_ids=tuple(f"rack_{role}" for role in active),
                energy=energies[index],
                density=densities[index],
                automation=automation,
                transition="vacuum" if name == "vacuum" else "crossfade",
            )
        )
    workflow = ProductionWorkflow(
        scenes=tuple(scenes),
        racks=racks,
        resamples=(
            ResamplePass(
                source_scene_id="scene_peak",
                operation="freeze",
                amount=0.55,
                target_role="granular_texture",
                entry_s=duration_s * 0.74,
            ),
            ResamplePass(
                source_scene_id="scene_build",
                operation="reverse",
                amount=0.35,
                target_role="transition",
                entry_s=duration_s * 0.48,
            ),
        ),
        render_budget_name=budget_name,
    )
    errors = workflow.validate()
    if errors:
        raise ValueError("Ungueltiger Produktionsworkflow: " + "; ".join(errors))
    return workflow
