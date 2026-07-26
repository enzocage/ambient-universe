"""Ereignisgeneratoren (plan.md sym.pat.*, Paragraph 6.5).

Poisson-Dichte fuer Ereigniszeitpunkte, feldrelative Stufenwahl fuer
Tonhoehen. Stille ist hier keine Abwesenheit von Code, sondern das, was
zwischen den gezogenen Ereignissen ohnehin entsteht (plan.md: "Stille als
musikalisches Ereignis, gleichwertig zum Ton").
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

from au.core.seeds import SeedPath
from au.dsl.field import HarmonicField

if TYPE_CHECKING:
    from au.dsl.harmony import ChordTimeline
    from au.dsl.rhythm import Clock


def _degrees_for(field: HarmonicField, chords: ChordTimeline | None, t: float) -> tuple[int, ...]:
    """Stufenauswahl an Zeitpunkt ``t``: aus der Akkordfolge, wenn vorhanden,
    sonst aus dem vollen Feld (Rueckwaertskompatibilitaet ohne Harmonik-Engine)."""
    if chords is not None:
        return chords.degrees_at(t)
    return field.degrees()


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """Ein einzelnes, feldrelatives Ereignis."""

    time_s: float
    degree: int
    duration_s: float
    velocity: float = 0.8

    def pitch_midi(self, field: HarmonicField) -> float:
        return field.degree_to_midi(self.degree)


def poisson_density_events(
    duration_s: float,
    *,
    lambda_per_min: float,
    field: HarmonicField,
    seed: SeedPath,
    min_gap_s: float = 4.0,
    event_duration_range_s: tuple[float, float] = (2.0, 6.0),
    chords: ChordTimeline | None = None,
    clock: Clock | None = None,
    quantize_strength: float = 0.6,
) -> list[NoteEvent]:
    """Zieht Ereigniszeitpunkte aus einem Poisson-Prozess.

    ``min_gap_s`` verhindert Ueberlappungen, die bei sehr sparsamer Dichte
    ohnehin selten vorkommen, aber ohne Mindestabstand gelegentlich zwei
    Ereignisse fast gleichzeitig ausloesen wuerden — musikalisch ein Klumpen,
    kein Ereignis.

    ``chords``: wenn gesetzt, wird die Stufe aus dem zum Ereigniszeitpunkt
    aktiven Akkord gezogen statt aus dem vollen Feld -- das ist die
    harmonische Koordination zwischen gleichzeitig laufenden Elementen.

    ``clock``: wenn gesetzt, wird der gezogene Zeitpunkt sanft (``quantize_strength``)
    auf das gemeinsame Zeitraster gezogen -- Ereignisse verschiedener Elemente
    faellen dadurch eher zusammen oder in erkennbarem Abstand, statt komplett
    unabhaengig zu streuen.
    """
    rng = np.random.default_rng(seed.child("pattern", "poisson").value & 0xFFFF_FFFF)
    rate_per_s = lambda_per_min / 60.0
    if rate_per_s <= 0:
        return []

    events: list[NoteEvent] = []
    t = 0.0
    last_end = -min_gap_s
    while t < duration_s:
        gap = rng.exponential(1.0 / rate_per_s)
        t += gap
        if t >= duration_s or t < last_end + min_gap_s:
            continue
        event_time = clock.quantize(t, strength=quantize_strength) if clock else t
        event_time = max(0.0, min(duration_s - 0.01, event_time))
        dur = float(rng.uniform(*event_duration_range_s))
        dur = min(dur, duration_s - event_time)
        degrees = _degrees_for(field, chords, event_time)
        degree = int(rng.choice(degrees))
        velocity = float(rng.uniform(0.55, 0.95))
        events.append(
            NoteEvent(time_s=event_time, degree=degree, duration_s=dur, velocity=velocity)
        )
        last_end = t + dur
    return events


def sustained_events(
    duration_s: float,
    *,
    field: HarmonicField,
    seed: SeedPath,
    change_every_s: tuple[float, float] = (18.0, 40.0),
    overlap_s: float = 6.0,
    chords: ChordTimeline | None = None,
) -> list[NoteEvent]:
    """Eine durchgehende Flaeche statt diskreter Ereignisse.

    Fuer Rollen, die den Track tragen sollen (Fundament, Drone, Atmo, Pad):
    ohne diese Funktion wuerden auch sie ueber ``poisson_density_events`` mit
    wenigen Ereignissen pro Minute angesteuert und der Track bestuende
    ueberwiegend aus Stille. Stattdessen wird die Dauer in wenige lange,
    sich leicht ueberlappende Abschnitte geteilt, deren Stufe jeweils wechselt
    (harmonische Bewegung), waehrend die Flaeche selbst nie abreisst.

    ``overlap_s`` sorgt dafuer, dass ein Abschnitt zu klingen beginnt, bevor
    der vorherige endet -- ein echter Schnitt waere in einer Ambient-Flaeche
    hoerbar, eine Ueberlappung nicht.
    """
    rng = np.random.default_rng(seed.child("pattern", "sustained").value & 0xFFFF_FFFF)

    events: list[NoteEvent] = []
    t = 0.0
    previous_degree: int | None = None
    while t < duration_s:
        span = float(rng.uniform(*change_every_s))
        dur = min(span + overlap_s, duration_s - t + overlap_s)
        degrees = _degrees_for(field, chords, t)
        choices = [d for d in degrees if d != previous_degree] or list(degrees)
        degree = int(rng.choice(choices))
        velocity = float(rng.uniform(0.5, 0.75))  # traegt, draengt sich nicht auf
        events.append(NoteEvent(time_s=t, degree=degree, duration_s=dur, velocity=velocity))
        previous_degree = degree
        t += span
    return events


def euclid_sparse_events(
    duration_s: float,
    *,
    pulses: int,
    steps: int,
    step_duration_s: float,
    field: HarmonicField,
    seed: SeedPath,
    event_duration_s: float = 3.0,
    chords: ChordTimeline | None = None,
    clock: Clock | None = None,
) -> list[NoteEvent]:
    """Euklidische Verteilung seltener Ereignisse (plan.md sym.pat.euclid_sparse).

    Kumulative Methode (Positionen bei ``floor(i * steps / pulses)``): verteilt
    ``pulses`` Ereignisse so gleichmaessig wie moeglich ueber ``steps``
    Schritte. Liefert fuer kleine ``pulses/steps``-Verhaeltnisse dieselben
    Muster wie der Bjorklund-Algorithmus, ist aber ohne Sonderfaelle korrekt.

    ``step_duration_s`` wird durch ``clock.grid_step_s`` ersetzt, wenn eine
    Uhr uebergeben wird -- ein euklidischer Rhythmus ohne gemeinsamen Puls
    waere pro Element ein eigenes, unabhaengiges Metrum.
    """
    if pulses <= 0 or steps <= 0:
        return []
    pulses = min(pulses, steps)
    hit_steps = {(i * steps) // pulses for i in range(pulses)}
    effective_step_s = (
        clock.grid_step_s * max(1, round(step_duration_s / clock.grid_step_s))
        if clock
        else step_duration_s
    )

    rng = np.random.default_rng(seed.child("pattern", "euclid").value & 0xFFFF_FFFF)

    events: list[NoteEvent] = []
    for step in sorted(hit_steps):
        t = step * effective_step_s
        if t >= duration_s:
            break
        degrees = _degrees_for(field, chords, t)
        degree = int(rng.choice(degrees))
        dur = min(event_duration_s, duration_s - t)
        events.append(NoteEvent(time_s=t, degree=degree, duration_s=dur))
    return events
