"""Implementierungen der Steuerquellen (L1).

Modulatoren liefern Steuersignale (k-rate). Die Glaettung ihrer Ziele setzt
der Compiler; hier geht es um die Bewegungsform selbst.
"""

from __future__ import annotations

from au.modules.base import BuildContext, Signals, implements


@implements("mod.lfo.slow_sine")
def build_slow_lfo(ctx: BuildContext) -> Signals:
    """Sehr langsamer LFO.

    Die untere Grenze von 0.0001 Hz entspricht einer Periode von knapp drei
    Stunden — laenger als jedes Album. Genau darum geht es: Bewegung, die
    innerhalb eines Tracks nie zum Ausgangspunkt zurueckkehrt.
    """
    from supriya.ugens import LFNoise2, LFSaw, LFTri, SinOsc

    rate = ctx.input("rate", ctx.param("rate_hz", 0.02))
    depth = ctx.param("depth", 0.5)
    phase = ctx.param("phase", 0.0)
    bipolar = ctx.param("bipolar", 1.0)
    waveform = ctx.enum_value("waveform")

    if waveform == "sine":
        shape = SinOsc.kr(frequency=rate, phase=phase * 6.2832)  # type: ignore[attr-defined]
    elif waveform == "triangle":
        shape = LFTri.kr(frequency=rate, initial_phase=phase * 4.0)  # type: ignore[attr-defined]
    elif waveform == "ramp_up":
        shape = LFSaw.kr(frequency=rate, initial_phase=phase * 2.0)  # type: ignore[attr-defined]
    elif waveform == "ramp_down":
        shape = LFSaw.kr(frequency=rate, initial_phase=phase * 2.0) * -1.0  # type: ignore[attr-defined]
    else:
        # Quadratisch interpoliertes Rauschen: bewegt, aber nie sprunghaft.
        shape = LFNoise2.kr(frequency=rate)  # type: ignore[attr-defined]

    scaled = shape * depth
    # Unipolar heisst hier [0, depth], nicht [-depth, depth].
    if isinstance(bipolar, int | float):
        return {"out": scaled if float(bipolar) >= 0.5 else (scaled + depth) * 0.5}
    return {"out": scaled * bipolar + (scaled + depth) * 0.5 * (1.0 - bipolar)}


@implements("mod.rand.brownian_smooth")
def build_brownian_smooth(ctx: BuildContext) -> Signals:
    """Geglaetteter Random Walk mit Rueckstellkraft.

    Reine brownsche Bewegung driftet mit der Zeit beliebig weit weg — nach
    zwanzig Minuten steht ein Parameter am Anschlag. Die Rueckstellkraft
    (``centering``) haelt den Wanderer in der Naehe der Mitte, ohne ihn
    festzunageln. Das ist der Unterschied zwischen organisch und kaputt.
    """
    from supriya.ugens import Lag, LFNoise2

    rate = ctx.input("rate", ctx.param("rate_hz", 0.05))
    step = ctx.param("step", 0.05)
    centering = ctx.param("centering", 0.15)
    smooth_ms = ctx.param("smooth_ms", 2000.0)

    # Zwei ungleich schnelle Rauschquellen: die langsame traegt die Wanderung,
    # die schnelle gibt ihr Textur. Ein einzelner Generator klingt mechanisch.
    slow = LFNoise2.kr(frequency=rate)  # type: ignore[attr-defined]
    fast = LFNoise2.kr(frequency=rate * 4.0)  # type: ignore[attr-defined]
    walk = slow + fast * 0.25

    # Die Rueckstellkraft wirkt als Daempfung der Auslenkung.
    pull = 1.0 - centering if isinstance(centering, int | float) else (1.0 - centering)
    excursion = walk * step * 6.0 * pull

    seconds = smooth_ms / 1000.0 if isinstance(smooth_ms, int | float) else smooth_ms * 0.001
    return {"out": Lag.kr(source=excursion, lag_time=seconds)}  # type: ignore[attr-defined]


@implements("mod.ctrl.constant")
def build_ctrl_constant(ctx: BuildContext) -> Signals:
    """Ein fester Steuerwert als k-rate-Signal.

    Der Umweg ueber ``DC.kr`` (statt den Python-Float direkt durchzureichen)
    stellt sicher, dass das Ergebnis ein echtes UGen-Signal ist, das sich mit
    anderen Signalen desselben Graphen mischen laesst.
    """
    from supriya.ugens import DC

    return {"out": DC.kr(source=ctx.param("value", 60.0))}  # type: ignore[attr-defined]


@implements("mod.map.linear")
def build_linear_mapper(ctx: BuildContext) -> Signals:
    """Das einzige Tor von der Analyse auf einen Parameter.

    Begrenzung und Glaettung sind hier nicht optional: ohne sie schwingt jede
    analysegesteuerte Rueckkopplung binnen Sekunden auf. Deshalb erzwingt das
    Manifest eine Mindestglaettung, und ``clamp`` steht auf 1.
    """
    from supriya.ugens import Lag

    source = ctx.input("in")
    in_low = ctx.param("in_low", 0.0)
    in_high = ctx.param("in_high", 1.0)
    out_low = ctx.param("out_low", 0.0)
    out_high = ctx.param("out_high", 1.0)
    smooth_ms = ctx.param("smooth_ms", 500.0)
    clamp = ctx.param("clamp", 1.0)

    span = in_high - in_low
    if isinstance(span, int | float) and abs(float(span)) < 1e-9:
        normalized = source * 0.0
    else:
        normalized = (source - in_low) / span

    if isinstance(clamp, int | float) and float(clamp) >= 0.5:
        normalized = normalized.clip(0.0, 1.0)

    mapped = normalized * (out_high - out_low) + out_low
    seconds = smooth_ms / 1000.0 if isinstance(smooth_ms, int | float) else smooth_ms * 0.001
    return {"out": Lag.kr(source=mapped, lag_time=seconds)}  # type: ignore[attr-defined]
