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


# ---------------------------------------------------------------------------
# gen.drone.sub_bass
# ---------------------------------------------------------------------------


@implements("gen.drone.sub_bass")
def build_sub_bass(ctx: BuildContext) -> Signals:
    """Tiefes Sub-Bass-Fundament mit modulierbarer Saettigung."""
    from supriya.ugens import DelayN, HPF, LFNoise2, LPF, SinOsc

    pitch = ctx.input("pitch", 36.0)
    frequency = _midi_to_hz(pitch)

    sub_gain = ctx.param("sub_gain", 0.7)
    sub_cutoff = ctx.param("sub_cutoff", 400.0)
    drive = ctx.param("drive", 0.2)
    rumble_mix = ctx.param("rumble_mix", 0.05)
    lfo_rate = ctx.param("lfo_rate", 0.1)
    wobble_depth = ctx.param("wobble_depth", 0.1)
    bass_boost = ctx.param("bass_boost", 0.5)

    lfo = LFNoise2.kr(frequency=lfo_rate) * wobble_depth  # type: ignore[attr-defined]
    detuned_freq = frequency * (1.0 + lfo)

    sub_osc = SinOsc.ar(frequency=detuned_freq) * sub_gain * 0.5  # type: ignore[attr-defined]
    oct_sub = SinOsc.ar(frequency=detuned_freq * 0.5) * sub_gain * bass_boost * 0.3  # type: ignore[attr-defined]

    raw = sub_osc + oct_sub
    if ctx.has_input("excitation"):
        raw = raw + ctx.input("excitation") * rumble_mix * 0.2

    saturated = (raw * (1.0 + drive * 2.0)).tanh()
    filtered = LPF.ar(source=saturated, frequency=sub_cutoff)  # type: ignore[attr-defined]
    filtered = HPF.ar(source=filtered, frequency=20.0)  # type: ignore[attr-defined]

    delayed = DelayN.ar(source=filtered, maximum_delay_time=0.02, delay_time=0.008)  # type: ignore[attr-defined]
    left = filtered * 0.8 + delayed * 0.2
    right = filtered * 0.8 - delayed * 0.2

    envelope = abs(filtered).lagged(0.08)
    return {"out": [left * 0.4, right * 0.4], "env_follow": envelope}


# ---------------------------------------------------------------------------
# gen.texture.granular_cloud
# ---------------------------------------------------------------------------


@implements("gen.texture.granular_cloud")
def build_granular_cloud(ctx: BuildContext) -> Signals:
    """Atmosphaerische Rausch- und Texturwolke."""
    from supriya.ugens import BPF, HPF, LFNoise2, PinkNoise, WhiteNoise

    pitch = ctx.input("pitch", 60.0)
    frequency = _midi_to_hz(pitch)

    filter_cutoff = ctx.param("filter_cutoff", 2500.0)
    high_pass = ctx.param("high_pass", 150.0)
    cloud_density = ctx.param("cloud_density", 0.5)
    resonance = ctx.param("resonance", 0.3)
    noise_blend = ctx.param("noise_blend", 0.4)
    grain_rate = ctx.param("grain_rate", 0.2)

    excitation = ctx.input("excitation")
    if excitation is None:
        excitation = PinkNoise.ar() * noise_blend  # type: ignore[attr-defined]
    else:
        excitation = excitation + WhiteNoise.ar() * noise_blend * 0.3  # type: ignore[attr-defined]

    wobble = LFNoise2.kr(frequency=grain_rate) * 200.0  # type: ignore[attr-defined]
    center_freq = (frequency + filter_cutoff + wobble).clip(100.0, 14000.0)

    rq = (1.0 - resonance * 0.85).clip(0.05, 1.0)
    band_filtered = BPF.ar(source=excitation * cloud_density, frequency=center_freq, reciprocal_of_q=rq)  # type: ignore[attr-defined]
    hp_filtered = HPF.ar(source=band_filtered, frequency=high_pass)  # type: ignore[attr-defined]

    pan_wobble = LFNoise2.kr(frequency=grain_rate * 0.7) * 0.4  # type: ignore[attr-defined]
    left = hp_filtered * (0.5 + pan_wobble)
    right = hp_filtered * (0.5 - pan_wobble)

    envelope = abs(hp_filtered).lagged(0.1)
    return {"out": [left * 2.0, right * 2.0], "env_follow": envelope}




# ---------------------------------------------------------------------------
# gen.arpeggio.pulse_sequence
# ---------------------------------------------------------------------------


@implements("gen.arpeggio.pulse_sequence")
def build_pulse_sequence(ctx: BuildContext) -> Signals:
    """Rhythmischer Pulsator mit dynamischer Filterung."""
    from supriya.ugens import HPF, LPF, SinOsc, VarSaw

    pitch = ctx.input("pitch", 48.0)
    frequency = _midi_to_hz(pitch)

    cutoff_freq = ctx.param("cutoff_freq", 1800.0)
    filter_env_amt = ctx.param("filter_env_amt", 0.5)
    sub_level = ctx.param("sub_level", 0.2)
    decay_time = ctx.param("decay_time", 0.4)
    pulse_speed = ctx.param("pulse_speed", 0.5)
    pw_mod = ctx.param("pw_mod", 0.15)

    lfo = SinOsc.kr(frequency=pulse_speed) * pw_mod + 0.5  # type: ignore[attr-defined]
    pulse_osc = VarSaw.ar(frequency=frequency, width=lfo.clip(0.1, 0.9)) * 0.4  # type: ignore[attr-defined]
    sub_osc = VarSaw.ar(frequency=frequency * 0.5, width=0.5) * sub_level * 0.2  # type: ignore[attr-defined]

    sig = pulse_osc + sub_osc
    if ctx.has_input("excitation"):
        sig = sig + ctx.input("excitation") * 0.1

    filt_freq = (cutoff_freq * (1.0 + filter_env_amt * 2.0)).clip(80.0, 14000.0)
    filtered = LPF.ar(source=sig, frequency=filt_freq)  # type: ignore[attr-defined]
    filtered = HPF.ar(source=filtered, frequency=30.0)  # type: ignore[attr-defined]

    envelope = abs(filtered).lagged(0.01 + decay_time * 0.1)
    return {"out": [filtered * 0.45, filtered * 0.45], "env_follow": envelope}



