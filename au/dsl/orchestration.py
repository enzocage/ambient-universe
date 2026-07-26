"""L7/L8 — Orchestrierung und Relationen (plan2.md Stufe 3 & 7)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegisterAllocation(BaseModel):
    """Frequenz- und Registerzuteilung fuer eine musikalische Rolle."""

    model_config = {"frozen": True}

    role: str
    freq_min_hz: float = Field(ge=20.0)
    freq_max_hz: float = Field(le=22000.0)
    center_midi: float = Field(default=60.0)


class OrchestrationPlan(BaseModel):
    """Orchestrierungsplan: Zuteilung von Registern und Aufmerksamkeits-Budgets."""

    model_config = {"frozen": True}

    registers: tuple[RegisterAllocation, ...]
    max_active_layers: int = Field(default=6, ge=1, le=12)

    def register_for(self, role: str) -> RegisterAllocation:
        for r in self.registers:
            if r.role == role:
                return r
        return RegisterAllocation(role=role, freq_min_hz=100.0, freq_max_hz=5000.0, center_midi=60.0)
