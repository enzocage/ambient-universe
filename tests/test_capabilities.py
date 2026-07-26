"""Tests fuer die Capability-Matrix aller Module (plan2.md Stufe 1)."""

from __future__ import annotations

from au.analysis.capabilities import audit_capability_matrix


def test_capability_matrix_audit() -> None:
    matrix = audit_capability_matrix()
    assert matrix.total_count > 0
    assert matrix.renderable_count > 0
    assert "Modulkatalog:" in matrix.summary()

    # Mindestens 5 Module müssen vollkommen renderbar sein
    renderables = [m for m in matrix.modules if m.is_renderable]
    assert len(renderables) >= 5

    # Sub-Bass Modul prüfen
    sub_bass = next((m for m in matrix.modules if m.module_id == "gen.drone.sub_bass"), None)
    if sub_bass:
        assert sub_bass.has_impl is True
        assert sub_bass.is_renderable is True
        assert "foundation" in sub_bass.suggested_roles
