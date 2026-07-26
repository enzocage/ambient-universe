"""Vorschlags-Engine: Rollen-Slot -> mehrere Elementkandidaten (plan.md Phase 6).

Jeder Kandidat verfolgt eine andere These (plan.md 4.4-MI-Direktive: "fuenf
Kandidaten, die sich in ihrer Grundidee unterscheiden, nicht im Filter-
Cutoff"). Diese Phase variiert dafuer die Stimme selbst und die Grundzuege
der Ansteuerung (Dichte, Makrostellung), nicht nur einen Parameter.
"""

from __future__ import annotations

from dataclasses import dataclass

from au.core.manifest import Category
from au.core.registry import Registry
from au.core.seeds import SeedPath
from au.dsl.blueprint import RoleSlot
from au.dsl.dna import AlbumDNA
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField
from au.selection.sound_priority import prioritize_voice_modules

#: Grobe Thesen, mit denen ein Kandidat sich von den anderen unterscheidet.
_THESES: tuple[tuple[str, float, float], ...] = (
    ("Warmer, koerperhafter Grundklang", 0.35, 0.15),
    ("Helle, glasige Erscheinung", 0.75, 0.05),
    ("Sparsames, seltenes Ereignis", 0.5, -0.6),
    ("Dichte, atmende Flaeche", 0.55, 0.6),
    ("Kuehler, distanzierter Klang", 0.25, -0.1),
)

#: Rollen, die den Track TRAGEN muessen -- durchgehende Flaeche statt
#: diskreter Ereignisse. Ohne diese Unterscheidung liefen auch Fundament und
#: Drone ueber Poisson-Dichte und der Track bestand ueberwiegend aus Stille
#: (realer Befund: ein 60s-Test hatte teils < 1 Ereignis insgesamt).
_CONTINUOUS_ROLES: frozenset[str] = frozenset(
    {
        "foundation",
        "harmonic_drone",
        "moving_pad",
        "atmospheric_noise",
        "space_noise_elements",
        "harmonic_sphere",
        "subharmonic_pulse",
    }
)

#: Rollen mit regelmaessig getakteter, wiederkehrender Ansteuerung.
_RHYTHMIC_ROLES: dict[str, tuple[int, int, float]] = {
    # role -> (pulses, steps, step_duration_s)
    "arpeggiator": (11, 16, 0.9),
    "bass_sequence": (6, 16, 1.2),
    "subtle_percussive_background": (5, 16, 1.5),
}

#: Nur diese Rollen duerfen mit einem rohen L1-Rauschgenerator (statt einer
#: vollen L2-Stimme mit Huellkurve/Resonanz) angesteuert werden -- ein
#: rohes Rauschen OHNE Formung ist fuer diese Rollen der richtige Klang,
#: fuer alles Tonale waere es nur ein unbehandeltes Zischen.
_NOISE_ALLOWED_ROLES: frozenset[str] = frozenset(
    {"atmospheric_noise", "space_noise_elements", "granular_texture"}
)
_WHITELISTED_L1_VOICES: frozenset[str] = frozenset({"gen.noise.colored"})


@dataclass(frozen=True, slots=True)
class Candidate:
    recipe: ElementRecipe
    thesis: str


def _voices_for_slot(slot: RoleSlot, registry: Registry, seed: SeedPath | None = None) -> list[str]:
    """Stimmen, deren Band den Slot ueberlappt.

    Nur vollstaendige L2-Stimmen (mit Huellkurve, Resonanz, Makros) zaehlen
    als "Stimme" -- ein roher L1-Oszillator allein ist ein Testton, kein
    Klangkoerper. Die einzige Ausnahme ist farbiges Rauschen fuer explizit
    rauschbasierte Rollen (plan.md: Rauschen ist dort der richtige Klang).
    """
    allow_noise = slot.role in _NOISE_ALLOWED_ROLES
    candidates = [
        m
        for m in registry.query(category=Category.GENERATOR)
        if m.level == 2 or (allow_noise and m.id in _WHITELISTED_L1_VOICES)
    ]
    modules = []
    for m in candidates:
        low, high = m.guarantees.band_hz
        slot_low, slot_high = slot.band_hz
        overlap = min(high, slot_high) - max(low, slot_low)
        if overlap > 0:
            modules.append(m)

    prioritized = prioritize_voice_modules(modules, role=slot.role, band_hz=slot.band_hz)
    # Nur gueltige Kandidaten werden weitergereicht. Zufall wird spaeter in
    # compose_track innerhalb der stabilen Kandidatenreihenfolge genutzt.
    ordered = [item.module_id for item in prioritized if item.tier.value != "rejected"]

    if seed and len(ordered) > 1:
        import random

        rng = random.Random(int(seed.value & 0xFFFF_FFFF))
        # Nur lokale Permutation gleichwertiger Nachbarn: S/A-Kandidaten
        # bleiben vor C-Kandidaten und der Score bleibt die Hauptentscheidung.
        for start in range(0, len(ordered), 3):
            block = ordered[start : start + 3]
            rng.shuffle(block)
            ordered[start : start + 3] = block
    return ordered or [m.id for m in candidates]


def propose_candidates(
    slot: RoleSlot,
    dna: AlbumDNA,
    field: HarmonicField,
    registry: Registry,
    *,
    seed: SeedPath,
    n: int = 5,
) -> list[Candidate]:
    """Erzeugt ``n`` Kandidaten mit unterschiedlicher These fuer einen Slot."""
    voices = _voices_for_slot(slot, registry, seed=seed)
    if not voices:
        raise ValueError(f"Kein Modul im Katalog deckt das Band von {slot.role} ab.")


    out: list[Candidate] = []
    for i in range(n):
        thesis, brightness, density_shift = _THESES[i % len(_THESES)]
        voice = voices[i % len(voices)]
        candidate_seed = seed.element_candidate(slot.slot_id, i)
        duration_s = max(20.0, min(180.0, slot.phase_period_s * 1.5))

        overrides: dict[str, object] = {}
        if slot.role in _CONTINUOUS_ROLES:
            # Durchgehende Flaeche: keine Luecken, lange Ein-/Ausblendzeiten,
            # damit Uebergaenge zwischen den Abschnitten nicht als Schnitt wirken.
            overrides = {"pattern_kind": "sustained", "attack_s": 5.0, "release_s": 9.0}
        elif slot.role in _RHYTHMIC_ROLES:
            pulses, steps, step_s = _RHYTHMIC_ROLES[slot.role]
            overrides = {
                "pattern_kind": "euclid",
                "euclid_pulses": pulses,
                "euclid_steps": steps,
                "euclid_step_s": step_s,
                "attack_s": 0.05,
                "release_s": min(step_s * 0.9, 1.2),
            }
        else:
            # Sparsame, aber HOERBARE Ereignisrollen: die alte Formel konnte bei
            # langer Slot-Periode auf < 1 Ereignis pro Track fallen (realer
            # Befund: praktisch Stille). Untergrenze sichert Praesenz, ohne die
            # Rolle in eine Flaeche zu verwandeln.
            lambda_per_min = max(
                4.0, 60.0 / max(4.0, slot.phase_period_s) * (1.0 + density_shift) * 8.0
            )
            overrides = {"pattern_kind": "poisson", "lambda_per_min": lambda_per_min}

        recipe = ElementRecipe(
            id=f"cand_{slot.slot_id}_{i}",
            name=f"{slot.role} — {thesis}",
            voice_module_id=voice,
            voice_macros={"brightness": brightness},
            field=field,
            duration_s=duration_s,
            seed_root=int(candidate_seed.value & 0xFFFF_FFFF),
            tags=(slot.role,),
            thesis=thesis,
            **overrides,
        )
        out.append(Candidate(recipe=recipe, thesis=thesis))
    return out
