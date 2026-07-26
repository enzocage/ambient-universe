"""Blueprint-Generator: DNA -> Rollen-Slots (plan.md Phase 5).

Top-Down-Ableitung: die DNA-Charakterachsen bestimmen deterministisch, welche
Rollen besetzt werden, mit welchen Budgets und welcher Periode. Zwei gleiche
DNAs erzeugen denselben Blueprint; zwei deutlich verschiedene DNAs einen
messbar verschiedenen (getestet ueber die Slot-Menge).
"""

from __future__ import annotations

from au.dsl.blueprint import (
    _PRIME_PERIODS_S,
    ROLE_PROFILES,
    Blueprint,
    RelationHint,
    RoleSlot,
)
from au.dsl.dna import AlbumDNA
from au.dsl.field import MODES, HarmonicField

#: Rollen, die praktisch jedes Ambient-Element traegt, unabhaengig vom Charakter.
_ALWAYS_PRESENT: tuple[str, ...] = ("foundation", "harmonic_drone", "atmospheric_noise")


def _select_field(dna: AlbumDNA) -> HarmonicField:
    """Modus aus Spannung/Ambiguitaet: mehr Spannung -> reibungsvollere Modi."""
    tension = dna.character.harmonic_tension_mean
    ambiguity = dna.character.tonal_ambiguity
    if ambiguity > 0.6:
        mode = "locrian" if tension > 0.6 else "phrygian"
    elif tension > 0.5:
        mode = "aeolian" if tension < 0.75 else "phrygian"
    elif dna.character.event_density_mean < 0.1:
        mode = "minor_pentatonic"
    else:
        mode = "dorian"
    assert mode in MODES
    # Grundton aus dem Seed, aber innerhalb eines musikalisch sinnvollen Registers.
    root = 45.0 + (dna.seed_root % 12)
    return HarmonicField(root_midi=root, mode=mode)


def _wanted_roles(dna: AlbumDNA) -> list[str]:
    c = dna.character
    roles = list(_ALWAYS_PRESENT)

    if c.event_density_mean >= 0.08:
        roles.append("granular_texture")
    if c.spatial_width >= 0.5:
        roles.append("moving_pad")
    if c.spectral_brightness[1] >= 0.55:
        roles.append("spectral_shimmer")
    roles.append("resonant_object")
    if c.surprise_budget >= 0.25:
        roles.append("signal_motif")
    if c.emotional_temperature[0] < 0.35 and c.spatial_depth >= 0.5:
        roles.append("subharmonic_pulse")
    if dna.innovation_vector.formal >= 0.6:
        roles.append("contrast_layer")
    if c.silence_probability >= 0.3:
        roles.append("negative_layer")

    # Deduplizieren, Reihenfolge stabil halten (Determinismus).
    seen: set[str] = set()
    ordered = []
    for r in roles:
        if r not in seen:
            seen.add(r)
            ordered.append(r)
    return ordered


def _rationale(role: str, dna: AlbumDNA) -> str:
    c = dna.character
    reasons = {
        "foundation": "Jeder Track braucht einen Traeger unter dem Hoerfokus.",
        "harmonic_drone": "Macht das harmonische Feld ueberhaupt hoerbar.",
        "atmospheric_noise": "Kittet die Schichten zu einem Raum zusammen.",
        "granular_texture": f"event_density_mean={c.event_density_mean:.2f} verlangt Koernung.",
        "moving_pad": f"spatial_width={c.spatial_width:.2f} verlangt raeumliche Bewegung.",
        "spectral_shimmer": f"spectral_brightness Ziel {c.spectral_brightness[1]:.2f} braucht oberen Glanz.",
        "resonant_object": "Ein Ambient-Track ohne koerperhaftes Einzelereignis wirkt flaechig ohne Textur.",
        "signal_motif": f"surprise_budget={c.surprise_budget:.2f} erlaubt ein wiedererkennbares Motiv.",
        "subharmonic_pulse": "Kalt und tief zugleich verlangt Koerperlichkeit im Fundament.",
        "contrast_layer": f"innovation.formal={dna.innovation_vector.formal:.2f} erlaubt bewusste Erwartungsbrueche.",
        "negative_layer": f"silence_probability={c.silence_probability:.2f} macht Stille zum geplanten Ereignis.",
    }
    return reasons.get(role, "")


def _assign_periods(roles: list[str]) -> dict[str, float]:
    """Koprime Perioden je Rolle (plan.md 4.4: kgV soll die Trackdauer uebersteigen)."""
    return {role: _PRIME_PERIODS_S[i % len(_PRIME_PERIODS_S)] for i, role in enumerate(roles)}


_RELATION_RULES: tuple[tuple[str, str, str], ...] = (
    ("supports", "foundation", "harmonic_drone"),
    ("supports", "harmonic_drone", "moving_pad"),
    ("answers", "resonant_object", "signal_motif"),
    ("avoids", "granular_texture", "spectral_shimmer"),
    ("shadows", "signal_motif", "spectral_shimmer"),
    ("avoids", "moving_pad", "granular_texture"),
    ("contrasts", "contrast_layer", "harmonic_drone"),
)


def _relation_hints(roles: list[str]) -> tuple[RelationHint, ...]:
    present = set(roles)
    hints = [
        RelationHint(kind=kind, from_role=a, to_role=b)
        for kind, a, b in _RELATION_RULES
        if a in present and b in present
    ]
    # resonates_in: alle Rollen teilen sich mindestens einen Raum.
    for role in roles:
        hints.append(RelationHint(kind="resonates_in", from_role=role, to_role="main_space"))
    return tuple(hints)


def derive_blueprint(dna: AlbumDNA) -> Blueprint:
    """Leitet aus einer Album-DNA die L4-Rollen-Slots ab."""
    field = _select_field(dna)
    roles = _wanted_roles(dna)
    periods = _assign_periods(roles)

    slots = tuple(
        RoleSlot(
            slot_id=f"{role}#0",
            role=role,
            band_hz=ROLE_PROFILES[role].band_hz,
            density=ROLE_PROFILES[role].density,
            lufs=ROLE_PROFILES[role].lufs,
            phase_period_s=periods[role],
            rationale=_rationale(role, dna),
        )
        for role in roles
    )

    return Blueprint(
        dna_title=dna.title,
        field=field,
        role_slots=slots,
        relation_hints=_relation_hints(roles),
    )
