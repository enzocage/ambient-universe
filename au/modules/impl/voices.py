"""Implementierungen der L2-Stimmen.

Eine Stimme ist ein vollstaendiger, spielbarer Klangkoerper. Ihr Versprechen
an alle hoeheren Ebenen sind die fuenf Makros: ``brightness``, ``body``,
``noise_ratio``, ``motion``, ``material``. Jedes muss ueber seinen *gesamten*
Weg von 0 nach 1 monoton wirken und artefaktfrei bleiben — geprueft wird das
vom Makro-Sweep-Test, nicht behauptet.
"""

from __future__ import annotations

from typing import Any

from au.modules.base import BuildContext, Signals, implements
from au.modules.impl.processors import MATERIAL_RATIOS, resonator_bank


def _material_ratios(ctx: BuildContext, param_name: str) -> tuple[float, ...]:
    """Materialreihe. Ist der Parameter makrogesteuert, waehlt der Index.

    Der Materialwechsel ist bewusst ein Aufbauparameter: zwischen Glas und
    Holz laesst sich nicht ueberblenden, ohne dass es wie ein Schnitt klingt.
    Das Makro ``material`` waehlt also die Reihe zur Uebersetzungszeit.
    """
    spec = ctx.manifest.params.get(param_name)
    choices = list(spec.enum or []) if spec else []
    if not choices:
        return MATERIAL_RATIOS["harmonic"]
    value = ctx.params.get(param_name, spec.default if spec else None)
    if isinstance(value, str):
        return MATERIAL_RATIOS.get(value, MATERIAL_RATIOS["harmonic"])
    if isinstance(value, int | float):
        index = max(0, min(len(choices) - 1, round(value)))
    else:
        index = 0
    return MATERIAL_RATIOS.get(choices[index], MATERIAL_RATIOS["harmonic"])


def _midi_to_hz(pitch: Any) -> Any:
    if isinstance(pitch, int | float):
        return 440.0 * 2.0 ** ((float(pitch) - 69.0) / 12.0)
    return pitch.midi_to_hz()


# ---------------------------------------------------------------------------
# gen.drone.wavetable_resonator
# ---------------------------------------------------------------------------


@implements("gen.drone.wavetable_resonator")
def build_wavetable_resonator(ctx: BuildContext) -> Signals:
    """Morphende Wellenformquelle durch eine Resonatorbank.

    Statt echter Wavetable-Puffer wird die Wellenform aus einer bandbegrenzten
    Impulsreihe (``Blip``) mit stufenlos veraenderlicher Teiltonzahl gebildet
    und gegen Sinus und Saegezahn ueberblendet. Das ergibt denselben
    kontinuierlichen Timbre-Weg wie eine Wavetable, ohne Pufferverwaltung im
    Non-Realtime-Rendering — ein bewusster Handel zugunsten der
    Reproduzierbarkeit.
    """
    from supriya.ugens import Blip, DelayN, LFNoise2, SinOsc

    pitch = ctx.input("pitch", 45.0)
    frequency = _midi_to_hz(pitch)

    wt_pos = ctx.param("wt_pos", 0.3)
    wt_rate = ctx.param("wt_rate", 0.02)
    res_damp = ctx.param("res_damp", 0.7)
    res_gain = ctx.param("res_gain", 0.6)
    sub_mix = ctx.param("sub_mix", 0.25)
    noise_mix = ctx.param("noise_mix", 0.1)
    drift_amt = ctx.param("drift_amt", 0.004)
    unison = int(ctx.param("unison", 3.0))

    # Analoge Instabilitaet: jede Unison-Stimme wandert eigenstaendig.
    voices = []
    for i in range(max(1, min(8, unison))):
        drift = LFNoise2.kr(frequency=0.03 + 0.017 * i) * drift_amt  # type: ignore[attr-defined]
        detuned = frequency * (1.0 + drift + (i - unison / 2.0) * 0.0009)
        # Die Teiltonzahl wandert mit wt_pos und mit der Zeit.
        travel = SinOsc.kr(frequency=wt_rate, phase=i * 1.7) * 0.5 + 0.5  # type: ignore[attr-defined]
        harmonics = 2.0 + (wt_pos * 0.7 + travel * 0.3) * 46.0
        rich = Blip.ar(frequency=detuned, harmonic_count=harmonics)  # type: ignore[attr-defined]
        pure = SinOsc.ar(frequency=detuned)  # type: ignore[attr-defined]
        voices.append(rich * wt_pos + pure * (1.0 - wt_pos))

    stacked = sum(voices) * (0.5 / max(1, len(voices)) ** 0.5)

    if ctx.has_input("excitation"):
        stacked = stacked + ctx.input("excitation") * noise_mix * 2.0

    sub = SinOsc.ar(frequency=frequency * 0.5) * sub_mix * 0.5  # type: ignore[attr-defined]

    ratios = _material_ratios(ctx, "res_ratios_set")[:6]
    resonated = (
        resonator_bank(
            stacked * 0.35,
            frequency,
            ratios,
            decay_base=0.08 + 9.0 * res_damp**3,
        )
        * 0.5
    )

    core = stacked * (1.0 - res_gain * 0.6) + resonated * res_gain + sub

    # Stereobreite aus Laufzeit statt aus Pegel: bleibt monokompatibel.
    delayed = DelayN.ar(source=core, maximum_delay_time=0.03, delay_time=0.011)  # type: ignore[attr-defined]
    left = core * 0.8 + delayed * 0.2
    right = core * 0.8 - delayed * 0.2

    envelope = abs(core).lagged(0.05)
    return {"out": [left * 0.5, right * 0.5], "env_follow": envelope}


# ---------------------------------------------------------------------------
# gen.object.modal_bell
# ---------------------------------------------------------------------------


@implements("gen.object.modal_bell")
def build_modal_bell(ctx: BuildContext) -> Signals:
    """Modaler Koerper, der angeregt statt angeschlagen wird.

    Der Reiz dieses Moduls liegt am ``excitation``-Eingang: speist man ein
    sehr leises, atmendes Rauschfeld ein, klingt der Koerper dauerhaft, aber
    nie gleich — ein Glockenton, der nicht verklingt und trotzdem lebt.
    Ohne Anregung erzeugt das Modul sein eigenes, sehr leises Grundrauschen,
    damit es nie stumm bleibt.
    """
    from supriya.ugens import DelayN, LFNoise2, PinkNoise

    pitch = ctx.input("pitch", 60.0)
    frequency = _midi_to_hz(pitch)

    partials = int(ctx.param("partials", 12.0))
    partial_tilt = ctx.param("partial_tilt", -0.3)
    damp = ctx.param("damp", 0.9)
    body_gain = ctx.param("body_gain", 0.5)
    strike_noise = ctx.param("strike_noise", 0.08)
    damp_drift = ctx.param("damp_drift", 0.008)
    detune_drift = ctx.param("detune_drift", 3.0)

    excitation = ctx.input("excitation")
    if excitation is None:
        # Ohne angeschlossene Anregung bleibt der Koerper nicht stumm — ein
        # Grundrauschen haelt ihn "lebendig" (plan.md: Koerper, der atmet).
        excitation = PinkNoise.ar() * 0.08  # type: ignore[attr-defined]
    excitation = excitation + PinkNoise.ar() * strike_noise * 0.3  # type: ignore[attr-defined]

    ratios = _material_ratios(ctx, "ratios_set")
    count = max(4, min(len(ratios), int(partials)))
    ratios = ratios[:count]

    # Sehr langsame Verstimmung: der Koerper "atmet", ohne dass man es als
    # Modulation erkennt.
    wobble = LFNoise2.kr(frequency=0.021) * detune_drift * (1.0 / 1200.0)  # type: ignore[attr-defined]
    damp_wobble = LFNoise2.kr(frequency=0.013) * damp_drift  # type: ignore[attr-defined]

    # partial_tilt steuert das Amplitudengefaelle: negativ = obere Teiltoene
    # leiser, der Koerper wird hohler und dunkler, ohne dass ein Filter greift.
    bank = resonator_bank(
        excitation,
        frequency * (1.0 + damp_wobble),
        ratios,
        decay_base=0.15 + 26.0 * damp**3,
        amplitude_tilt=partial_tilt,
        detune=wobble,
    )
    normalized = bank * 0.7 * (0.4 + body_gain)

    delayed = DelayN.ar(source=normalized, maximum_delay_time=0.03, delay_time=0.013)  # type: ignore[attr-defined]
    left = normalized * 0.75 + delayed * 0.25
    right = normalized * 0.75 - delayed * 0.25

    envelope = abs(normalized).lagged(0.08)
    return {"out": [left * 0.6, right * 0.6], "env_follow": envelope}
