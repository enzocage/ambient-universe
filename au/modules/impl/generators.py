"""Implementierungen der Klangquellen (L1).

Alle Quellen liefern ein Signal mit einer Spitze deutlich unter 0 dBFS. Die
endgueltige Begrenzung und die DC-Sperre setzt der Compiler; hier geht es nur
um sauberen, bandbegrenzten Klang.
"""

from __future__ import annotations

from typing import Any

from au.modules.base import BuildContext, Signals, implements

# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------


def _cents_to_ratio(cents: Any) -> Any:
    """Cent-Verstimmung als Frequenzverhaeltnis. Arbeitet auf Zahl und Signal."""
    if isinstance(cents, int | float):
        return 2.0 ** (float(cents) / 1200.0)
    return (cents * 0.01).semitones_to_ratio()


# ---------------------------------------------------------------------------
# gen.osc.bandlimited
# ---------------------------------------------------------------------------


@implements("gen.osc.bandlimited")
def build_bandlimited_oscillator(ctx: BuildContext) -> Signals:
    """Bandbegrenzte Grundwellenformen.

    SuperColliders ``Saw`` und ``Pulse`` sind bereits bandbegrenzt; Sinus und
    Dreieck sind es von Natur aus. Die Wellenformwahl ist ein Aufbauparameter
    und wird zur Uebersetzungszeit aufgeloest — ein zur Laufzeit umschaltbarer
    Wellenformwaehler waere ein Klick pro Umschaltung.
    """
    from supriya.ugens import LFTri, Pulse, Saw, SinOsc

    frequency = ctx.input("frequency", ctx.param("frequency", 110.0))
    frequency = frequency * _cents_to_ratio(ctx.param("detune_cents", 0.0))
    waveform = ctx.enum_value("waveform")

    if waveform == "sine":
        source = SinOsc.ar(frequency=frequency)  # type: ignore[attr-defined]
    elif waveform == "triangle":
        source = LFTri.ar(frequency=frequency)  # type: ignore[attr-defined]
    elif waveform == "saw":
        source = Saw.ar(frequency=frequency)  # type: ignore[attr-defined]
    else:  # square und pulse teilen sich den Generator
        width = 0.5 if waveform == "square" else ctx.param("pulse_width", 0.5)
        source = Pulse.ar(frequency=frequency, width=width)  # type: ignore[attr-defined]

    if ctx.has_input("phase_mod"):
        # Phasenmodulation ueber einen zusaetzlichen Sinus im Ringverbund:
        # klanglich ergiebiger als reine Addition und bleibt bandbegrenzt.
        source = (
            source
            + SinOsc.ar(  # type: ignore[attr-defined]
                frequency=frequency, phase=ctx.input("phase_mod") * 2.0
            )
            * 0.5
        )

    return {"out": source * 0.4}


# ---------------------------------------------------------------------------
# gen.noise.colored
# ---------------------------------------------------------------------------


@implements("gen.noise.colored")
def build_colored_noise(ctx: BuildContext) -> Signals:
    """Rauschen, dessen spektrale Neigung stufenlos einstellbar ist.

    ``tilt`` blendet zwischen braunem, weissem und blauem Rauschen. ``density``
    unter 1 duennt den Strom zu einzelnen Impulsen aus (Dust) — der Uebergang
    von Flaeche zu Ereignis ohne Modulwechsel.
    """
    from supriya.ugens import HPF, LPF, BrownNoise, Dust, WhiteNoise

    tilt = ctx.param("tilt", -0.5)
    density = ctx.param("density", 1.0)
    seed = ctx.rng_seed

    brown = BrownNoise.ar()  # type: ignore[attr-defined]
    white = WhiteNoise.ar()  # type: ignore[attr-defined]
    # "Blau": weisses Rauschen mit angehobenen Hoehen.
    blue = HPF.ar(source=WhiteNoise.ar(), frequency=2000.0)  # type: ignore[attr-defined]

    # tilt in [-1, 0] blendet braun->weiss, in [0, 1] weiss->blau.
    if isinstance(tilt, int | float):
        t = float(tilt)
        if t <= 0:
            mixed = brown * (-t) + white * (1.0 + t)
        else:
            mixed = white * (1.0 - t) + blue * t
    else:
        low = tilt.clip(-1.0, 0.0)
        high = tilt.clip(0.0, 1.0)
        mixed = brown * (-low) + white * (1.0 + low - high) + blue * high

    if isinstance(density, int | float) and float(density) >= 0.999:
        source = mixed
    else:
        # Impulsdichte skaliert bis 2000/s; darueber ist es akustisch Rauschen.
        gate = Dust.ar(density=density * 2000.0)  # type: ignore[attr-defined]
        source = mixed * (abs(gate) * 4.0).clip(0.0, 1.0) + mixed * density

    # Unhoerbares Tiefstes weg — es kostet nur Headroom.
    source = HPF.ar(source=source, frequency=18.0)  # type: ignore[attr-defined]
    source = LPF.ar(source=source, frequency=18000.0)  # type: ignore[attr-defined]
    _ = seed  # Rauschquellen folgen dem globalen NRT-Seed des Scores
    return {"out": source * 0.25}
