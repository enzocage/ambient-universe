"""Relations-Algebra (plan.md Paragraph 7.3) — verkuerzte Fassung.

Jede Relation ist ein typisiertes, gerichtetes Verhaeltnis zwischen zwei
Layern mit einer harten, strukturell pruefbaren Bedingung. Diese Phase deckt
die zeit- und bandbasierten Constraints ab — spektrale Feinpruefung (echte
Maskierungskarte, Rauheitsindex) folgt mit dem vollen Ausbau von L6, wenn
Mehrspur-Rendering und -Analyse zur Verfuegung stehen.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from au.dsl.layer import LayerInstance

RelationKind = Literal[
    "supports",
    "answers",
    "avoids",
    "shares_motif",
    "inherits_field",
    "contrasts",
    "resonates_in",
    "doubles",
    "shadows",
]


class Relation(BaseModel):
    """Eine Relation zwischen zwei Layern (oder einem Layer und dem Raum)."""

    model_config = {"frozen": True}

    kind: RelationKind
    from_layer: str
    to_layer: str
    params: dict[str, float] = Field(default_factory=dict)

    def check(self, a: LayerInstance, b: LayerInstance) -> tuple[bool, str]:
        """Prueft die harte Bedingung dieser Relation. Gibt (erfuellt, Begruendung)."""
        if self.kind == "supports":
            # A traegt B: A liegt tiefer im Band und ist leiser (weniger Aufmerksamkeit).
            ok = a.band_hz[1] <= b.band_hz[1] and a.lufs_target <= b.lufs_target + 6.0
            return ok, "supports: A muss tiefer/leiser liegen als B"
        if self.kind == "answers":
            # B antwortet nur in den Luecken von A: keine Zeitueberlappung.
            gap = self.params.get("gap_threshold_s", 2.0)
            ok = not a.overlaps_time(b) or (
                b.entry_time_s >= a.occupied_until_s - gap
                or a.entry_time_s >= b.occupied_until_s - gap
            )
            return ok, "answers: B darf A's Aktivfenster nicht ueberlagern"
        if self.kind == "avoids":
            # B weicht A aus: keine Bandueberlappung waehrend gemeinsamer Zeit,
            # oder B ist deutlich leiser in der Ueberlappung.
            if not a.overlaps_time(b):
                return True, "avoids: keine gemeinsame Zeit, Bedingung entfaellt"
            ok = a.band_overlap_fraction(b) < 0.3 or b.lufs_target <= a.lufs_target - 6.0
            return ok, "avoids: Bandueberlappung < 0.3 oder B deutlich leiser"
        if self.kind == "contrasts":
            # Maximaler Abstand in mindestens einer Dimension: hier Band.
            ok = a.band_overlap_fraction(b) < 0.15
            return ok, "contrasts: Baender duerfen sich kaum ueberschneiden"
        if self.kind in ("resonates_in", "shares_motif", "inherits_field", "doubles", "shadows"):
            # Diese Relationen sind weiche Ziele auf L6 (Raum, Motiv, Feld) und
            # tragen keine strukturelle Zeit-/Bandbedingung auf L5 — sie werden
            # als erfuellt gefuehrt, bis L6 (voller Ausbau) sie auswertet.
            return True, f"{self.kind}: weiches Ziel, keine L5-Hartbedingung"
        return True, "unbekannte Relation als erfuellt behandelt"


class RelationSet(BaseModel):
    model_config = {"frozen": True}

    relations: tuple[Relation, ...] = ()

    @model_validator(mode="after")
    def _no_self_relations(self) -> RelationSet:
        for r in self.relations:
            if r.from_layer == r.to_layer:
                raise ValueError(f"Relation {r.kind} kann sich nicht auf denselben Layer beziehen")
        return self

    def between(self, a: str, b: str) -> list[Relation]:
        return [
            r
            for r in self.relations
            if (r.from_layer == a and r.to_layer == b) or (r.from_layer == b and r.to_layer == a)
        ]
