"""Modular DSP Synthesis & Execution Factory (DSPFactory).

Löst die Ausführung von prozedural registrierten Modulen in Supriya/SuperCollider
dynamisch zur Renderzeit auf.
"""

from __future__ import annotations

from typing import Any

from au.modules.base import BuildContext, Signals


def build_procedural_module(ctx: BuildContext) -> Signals:
    """Standard-Fall-Back Ausführung für prozedural generierte Module."""
    from supriya.ugens import BPF, HPF, LPF, DelayN, LFNoise1, PinkNoise, Saw, SinOsc

    pitch = ctx.input("pitch", 50.0)
    if isinstance(pitch, int | float):
        freq = 440.0 * 2.0 ** ((float(pitch) - 69.0) / 12.0)
    else:
        freq = pitch.midi_to_hz()

    mod_id = ctx.manifest.id

    if "analog" in mod_id or "saw" in mod_id:
        sig = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    elif "fm" in mod_id:
        mod = SinOsc.ar(frequency=freq * 2.0) * freq * 1.0  # type: ignore[attr-defined]
        sig = SinOsc.ar(frequency=freq + mod) * 0.35  # type: ignore[attr-defined]
    elif "additive" in mod_id:
        p1 = SinOsc.ar(frequency=freq) * 0.4  # type: ignore[attr-defined]
        p2 = SinOsc.ar(frequency=freq * 2.0) * 0.2  # type: ignore[attr-defined]
        sig = p1 + p2
    elif "chaos" in mod_id:
        noise = PinkNoise.ar() * 0.35  # type: ignore[attr-defined]
        center = LFNoise1.kr(frequency=0.2) * 1200.0 + 1500.0  # type: ignore[attr-defined]
        sig = BPF.ar(source=noise, frequency=center, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    elif "vocal" in mod_id:
        saw = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
        sig = BPF.ar(source=saw, frequency=800.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    elif "prc." in mod_id or "spc." in mod_id:
        in_sig = ctx.input("in", None)
        if in_sig is not None:
            del_mod = LFNoise1.kr(frequency=0.1) * 0.005  # type: ignore[attr-defined]
            d_l = DelayN.ar(source=in_sig[0], maximum_delay_time=0.1, delay_time=0.02 + del_mod)  # type: ignore[attr-defined]
            d_r = DelayN.ar(source=in_sig[1], maximum_delay_time=0.1, delay_time=0.03 - del_mod)  # type: ignore[attr-defined]
            return {"out": [in_sig[0] + d_l * 0.4, in_sig[1] + d_r * 0.4]}
        sig = PinkNoise.ar() * 0.1  # type: ignore[attr-defined]
    else:
        sig = SinOsc.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]

    sig = HPF.ar(source=sig, frequency=30.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=8000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)

    return {"out": [sig, sig], "env_follow": env}
