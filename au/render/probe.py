"""Referenzscores fuer Rauchtest, Determinismus- und Leistungsmessung.

Diese Scores sind bewusst minimal und stabil: sie dienen als Messlatte fuer
das Backend, nicht als Musik. Sie duerfen sich nie aendern, ohne dass die
gespeicherten Referenzhashes bewusst neu gesetzt werden.
"""

from __future__ import annotations

from pathlib import Path

from au.core.config import Config, get_config
from au.core.seeds import SeedPath
from au.render.backend import RenderResult, render_score


def _build_sine_synthdef(name: str = "au_probe_sine"):  # type: ignore[no-untyped-def]
    """Ein gefensterter Sinus mit weichen Flanken — klickfrei per Konstruktion."""
    import supriya
    from supriya.ugens import EnvGen, Out, SinOsc

    # Der Name gehoert an build(), nicht an den Konstruktor — dort waere jedes
    # Schluesselwort ein SynthDef-Parameter.
    with supriya.SynthDefBuilder(
        frequency=220.0,
        amplitude=0.2,
        gate_duration=1.0,
        pan=0.0,
    ) as builder:
        # Perkussionsfreie Huellkurve: 0.5 s Anstieg, Halten, 0.5 s Abfall.
        env = supriya.Envelope(
            amplitudes=[0.0, 1.0, 1.0, 0.0],
            durations=[0.5, builder["gate_duration"] - 1.0, 0.5],
            curves=[2.0, 0.0, -2.0],
        )
        # Supriya erzeugt die Ratenkonstruktoren (.ar/.kr/.ir) zur Laufzeit per
        # Dekorator; mypy sieht sie an der Klasse nicht.
        envelope = EnvGen.ar(envelope=env, done_action=2)  # type: ignore[attr-defined]
        source = (
            SinOsc.ar(frequency=builder["frequency"])  # type: ignore[attr-defined]
            * envelope
            * builder["amplitude"]
        )
        Out.ar(bus=0, source=[source, source])  # type: ignore[attr-defined]
    return builder.build(name=name)


def build_sine_score(duration: float = 10.0, frequency: float = 220.0):  # type: ignore[no-untyped-def]
    """Score mit einem einzelnen gehaltenen Sinuston."""
    import supriya

    score = supriya.Score()
    synthdef = _build_sine_synthdef()
    with score.at(0.0):
        score.add_synthdefs(synthdef)
        score.add_synth(synthdef, frequency=frequency, gate_duration=duration)
    with score.at(duration):
        score.do_nothing()
    return score


def build_stack_score(duration: float = 10.0, voices: int = 12, seed: int = 481_723):  # type: ignore[no-untyped-def]
    """Leistungsreferenz: mehrere leicht verstimmte Stimmen, seed-gesteuert.

    Der Seed steuert die Verstimmung, damit der Score deterministisch ist,
    aber nicht trivial (identische Stimmen wuerden vom Compiler wegoptimiert).
    """
    import random

    import supriya

    rng = random.Random(SeedPath.root(seed).child("probe", "stack").value)
    score = supriya.Score()
    synthdef = _build_sine_synthdef()
    with score.at(0.0):
        score.add_synthdefs(synthdef)
        for i in range(voices):
            cents = rng.uniform(-9.0, 9.0)
            freq = 110.0 * (2 ** (i / 12.0)) * (2 ** (cents / 1200.0))
            score.add_synth(
                synthdef,
                frequency=freq,
                amplitude=0.6 / voices,
                gate_duration=duration,
            )
    with score.at(duration):
        score.do_nothing()
    return score


def render_probe(
    output_path: Path,
    *,
    duration: float = 10.0,
    kind: str = "sine",
    cfg: Config | None = None,
) -> RenderResult:
    """Rendert einen Referenzscore. ``kind`` ist ``sine`` oder ``stack``."""
    c = cfg or get_config()
    if kind == "sine":
        score = build_sine_score(duration=duration)
    elif kind == "stack":
        score = build_stack_score(duration=duration)
    else:
        raise ValueError(f"Unbekannter Referenzscore: {kind!r} (erwartet: sine, stack)")
    return render_score(score, output_path, duration=duration, cfg=c)
