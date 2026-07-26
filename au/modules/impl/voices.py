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
    from supriya.ugens import HPF, LPF, DelayN, LFNoise2, SinOsc

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


# ---------------------------------------------------------------------------
# gen.fm.dual_operator
# ---------------------------------------------------------------------------


@implements("gen.fm.dual_operator")
def build_fm_dual_operator(ctx: BuildContext) -> Signals:
    """Zwei-Operator FM-Synthesizer."""
    from supriya.ugens import HPF, LPF, LFNoise2, SinOsc

    pitch = ctx.input("pitch", 57.0)
    freq = _midi_to_hz(pitch)

    mod_index = ctx.param("mod_index", 2.0)
    sub_mix = ctx.param("sub_mix", 0.4)
    lfo_rate = ctx.param("lfo_rate", 0.15)
    harmonic_ratio = ctx.param("harmonic_ratio", 2.0)

    lfo = LFNoise2.kr(frequency=lfo_rate) * 0.5 + 1.0  # type: ignore[attr-defined]
    mod_freq = freq * harmonic_ratio
    modulator = SinOsc.ar(frequency=mod_freq) * (mod_freq * mod_index * lfo)  # type: ignore[attr-defined]

    carrier = SinOsc.ar(frequency=freq + modulator) * 0.35  # type: ignore[attr-defined]
    sub = SinOsc.ar(frequency=freq * 0.5) * sub_mix * 0.25  # type: ignore[attr-defined]

    sig = carrier + sub
    sig = HPF.ar(source=sig, frequency=35.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=12000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.additive.harmonic_partials
# ---------------------------------------------------------------------------


@implements("gen.additive.harmonic_partials")
def build_additive_harmonic_partials(ctx: BuildContext) -> Signals:
    """Additive Synthese aus 8 Sinus-Teiltoenen."""
    from supriya.ugens import HPF, LPF, LFNoise2, SinOsc

    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)

    partial_tilt = ctx.param("partial_tilt", 0.0)
    fundamental_gain = ctx.param("fundamental_gain", 0.8)
    detune_spread = ctx.param("detune_spread", 0.015)
    lfo_rate = ctx.param("lfo_rate", 0.2)

    lfo = LFNoise2.kr(frequency=lfo_rate) * detune_spread  # type: ignore[attr-defined]
    sig = SinOsc.ar(frequency=freq * (1.0 + lfo)) * fundamental_gain * 0.3  # type: ignore[attr-defined]

    for harmonic in range(2, 7):
        gain = (1.0 / (harmonic ** (1.0 - partial_tilt * 0.5))) * 0.15
        detune = (harmonic % 2 - 0.5) * detune_spread
        p_sig = SinOsc.ar(frequency=freq * harmonic * (1.0 + detune)) * gain  # type: ignore[attr-defined]
        sig = sig + p_sig

    sig = HPF.ar(source=sig, frequency=30.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=14000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.physical.plucked_string
# ---------------------------------------------------------------------------


@implements("gen.physical.plucked_string")
def build_plucked_string(ctx: BuildContext) -> Signals:
    """Karplus-Strong Physical Modeling einer gezupften Saite."""
    from supriya.ugens import HPF, LPF, Pluck, WhiteNoise

    pitch = ctx.input("pitch", 60.0)
    freq = _midi_to_hz(pitch)

    damping = ctx.param("damping", 0.5)
    decay_time = ctx.param("decay_time", 3.0)
    exciter_noise = ctx.param("exciter_noise", 0.2)

    trig = ctx.input("excitation") if ctx.has_input("excitation") else 1.0
    pluck_sig = Pluck.ar(  # type: ignore[attr-defined]
        source=WhiteNoise.ar() * exciter_noise,  # type: ignore[attr-defined]
        trigger=trig,

        maximum_delay_time=0.1,
        delay_time=1.0 / freq,
        decay_time=decay_time,
        coefficient=damping,
    )
    sig = HPF.ar(source=pluck_sig, frequency=40.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=11000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig * 0.4, sig * 0.4], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.vocal.formant_pad
# ---------------------------------------------------------------------------


@implements("gen.vocal.formant_pad")
def build_formant_pad(ctx: BuildContext) -> Signals:
    """Chorale Formantsynthese mit Vokal-Resonanzen."""
    from supriya.ugens import BPF, HPF, Saw, WhiteNoise

    pitch = ctx.input("pitch", 55.0)
    freq = _midi_to_hz(pitch)

    formant_shift = ctx.param("formant_shift", 1.0)
    breath_mix = ctx.param("breath_mix", 0.08)

    raw_saw = Saw.ar(frequency=freq) * 0.2  # type: ignore[attr-defined]
    breath = WhiteNoise.ar() * breath_mix * 0.15  # type: ignore[attr-defined]
    src = raw_saw + breath

    f1 = BPF.ar(source=src, frequency=600.0 * formant_shift, reciprocal_of_q=0.15) * 0.4  # type: ignore[attr-defined]
    f2 = BPF.ar(source=src, frequency=1200.0 * formant_shift, reciprocal_of_q=0.15) * 0.3  # type: ignore[attr-defined]
    f3 = BPF.ar(source=src, frequency=2400.0 * formant_shift, reciprocal_of_q=0.15) * 0.2  # type: ignore[attr-defined]

    sig = HPF.ar(source=f1 + f2 + f3, frequency=50.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.08)
    return {"out": [sig * 0.5, sig * 0.5], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.spectral.phase_freeze
# ---------------------------------------------------------------------------


@implements("gen.spectral.phase_freeze")
def build_phase_freeze(ctx: BuildContext) -> Signals:
    """Phase Vocoder Spectral Freeze Simulator."""
    from supriya.ugens import BPF, HPF, LFNoise2, PinkNoise, SinOsc

    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)

    spectral_blur = ctx.param("blur_amount", 0.3)
    lfo = LFNoise2.kr(frequency=0.1) * spectral_blur  # type: ignore[attr-defined]

    s1 = SinOsc.ar(frequency=freq * (1.0 + lfo)) * 0.25  # type: ignore[attr-defined]
    s2 = SinOsc.ar(frequency=freq * 1.5 * (1.0 - lfo)) * 0.15  # type: ignore[attr-defined]
    noise = BPF.ar(source=PinkNoise.ar(), frequency=freq * 2.0, reciprocal_of_q=0.2) * 0.1  # type: ignore[attr-defined]

    sig = HPF.ar(source=s1 + s2 + noise, frequency=40.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.1)
    return {"out": [sig * 0.4, sig * 0.4], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.synth.wavefolder
# ---------------------------------------------------------------------------


@implements("gen.synth.wavefolder")
def build_wavefolder(ctx: BuildContext) -> Signals:
    """Non-linear Analog Wavefolder Oszillator."""
    from supriya.ugens import HPF, LPF, Fold, SinOsc

    pitch = ctx.input("pitch", 40.0)
    freq = _midi_to_hz(pitch)

    fold_drive = ctx.param("fold_drive", 2.0)
    sub_octave = ctx.param("sub_octave", 0.5)

    base_osc = SinOsc.ar(frequency=freq) * fold_drive  # type: ignore[attr-defined]
    folded = Fold.ar(source=base_osc, minimum=-0.8, maximum=0.8) * 0.3  # type: ignore[attr-defined]
    sub = SinOsc.ar(frequency=freq * 0.5) * sub_octave * 0.25  # type: ignore[attr-defined]

    sig = HPF.ar(source=folded + sub, frequency=30.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=8000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)

    return {"out": [sig, sig], "env_follow": env}


# ---------------------------------------------------------------------------
# gen.noise.stochastic_trigger
# ---------------------------------------------------------------------------


@implements("gen.noise.stochastic_trigger")
def build_stochastic_trigger(ctx: BuildContext) -> Signals:
    """Stochastischer Dust- & Crackle-Resonanz-Generator."""
    from supriya.ugens import BPF, HPF, LPF, Dust, PinkNoise

    density_hz = ctx.param("density_hz", 12.0)
    resonance_freq = ctx.param("resonance_freq", 2400.0)
    crackle_mix = ctx.param("crackle_mix", 0.2)

    dust_trig = Dust.ar(density=density_hz) * 0.8  # type: ignore[attr-defined]
    dust_filtered = BPF.ar(source=dust_trig, frequency=resonance_freq, reciprocal_of_q=0.1)  # type: ignore[attr-defined]

    crackle = PinkNoise.ar() * crackle_mix * 0.08  # type: ignore[attr-defined]
    sig = HPF.ar(source=dust_filtered + crackle, frequency=100.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=12000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig * 1.2, sig * 1.2], "env_follow": env}


# ---------------------------------------------------------------------------
# 28 Neue L2 Synthesizer-Familien (Musikmaschine.md & Repositories.md)
# ---------------------------------------------------------------------------


@implements("gen.synth.juno_chorus")
def build_juno_chorus(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, DelayN, LFNoise1, Pulse, Saw
    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)
    pwm = ctx.param("pwm", 0.5)
    cutoff = ctx.param("cutoff", 3500.0)
    saw = Saw.ar(frequency=freq) * 0.4  # type: ignore[attr-defined]
    pulse = Pulse.ar(frequency=freq, width=pwm) * 0.4  # type: ignore[attr-defined]
    raw = LPF.ar(source=saw + pulse, frequency=cutoff)  # type: ignore[attr-defined]
    mod = LFNoise1.kr(frequency=0.4) * 0.003  # type: ignore[attr-defined]
    delay_l = DelayN.ar(source=raw, maximum_delay_time=0.05, delay_time=0.015 + mod)  # type: ignore[attr-defined]
    delay_r = DelayN.ar(source=raw, maximum_delay_time=0.05, delay_time=0.022 - mod)  # type: ignore[attr-defined]
    env = abs(raw).lagged(0.05)
    return {"out": [raw + delay_l * 0.5, raw + delay_r * 0.5], "env_follow": env}


@implements("gen.synth.prophet_lead")
def build_prophet_lead(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise2, Saw
    pitch = ctx.input("pitch", 60.0)
    freq = _midi_to_hz(pitch)
    detune = ctx.param("detune", 1.008)
    saw1 = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    saw2 = Saw.ar(frequency=freq * detune) * 0.35  # type: ignore[attr-defined]
    filter_mod = LFNoise2.kr(frequency=0.2) * 1500.0 + 2500.0  # type: ignore[attr-defined]
    sig = LPF.ar(source=saw1 + saw2, frequency=filter_mod)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.ladder_bass")
def build_ladder_bass(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Pulse, SinOsc
    pitch = ctx.input("pitch", 36.0)
    freq = _midi_to_hz(pitch)
    cutoff = ctx.param("cutoff", 450.0)
    sub = SinOsc.ar(frequency=freq * 0.5) * 0.5  # type: ignore[attr-defined]
    pulse = Pulse.ar(frequency=freq, width=0.3) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=sub + pulse, frequency=cutoff)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=cutoff * 1.2)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig * 0.9, sig * 0.9], "env_follow": env}


@implements("gen.synth.biquad_sweep")
def build_biquad_sweep(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LFNoise1, PinkNoise, Saw
    pitch = ctx.input("pitch", 55.0)
    freq = _midi_to_hz(pitch)
    sweep_rate = ctx.param("sweep_rate", 0.1)
    saw = Saw.ar(frequency=freq) * 0.3  # type: ignore[attr-defined]
    noise = PinkNoise.ar() * 0.1  # type: ignore[attr-defined]
    center = LFNoise1.kr(frequency=sweep_rate) * 2000.0 + 3000.0  # type: ignore[attr-defined]
    filtered = BPF.ar(source=saw + noise, frequency=center, reciprocal_of_q=0.2)  # type: ignore[attr-defined]
    env = abs(filtered).lagged(0.05)
    return {"out": [filtered * 1.5, filtered * 1.5], "env_follow": env}


@implements("gen.synth.sallen_key")
def build_sallen_key(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Fold, Saw
    pitch = ctx.input("pitch", 50.0)
    freq = _midi_to_hz(pitch)
    drive = ctx.param("drive", 2.5)
    saw = Saw.ar(frequency=freq) * drive  # type: ignore[attr-defined]
    saturated = Fold.ar(source=saw, minimum=-0.9, maximum=0.9) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=saturated, frequency=3000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.vector_pad")
def build_vector_pad(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, Pulse, Saw, SinOsc
    pitch = ctx.input("pitch", 57.0)
    freq = _midi_to_hz(pitch)
    mix_x = LFNoise1.kr(frequency=0.15) * 0.5 + 0.5  # type: ignore[attr-defined]
    mix_y = LFNoise1.kr(frequency=0.22) * 0.5 + 0.5  # type: ignore[attr-defined]
    osc_a = SinOsc.ar(frequency=freq)  # type: ignore[attr-defined]
    osc_b = Saw.ar(frequency=freq * 1.001)  # type: ignore[attr-defined]
    osc_c = Pulse.ar(frequency=freq * 0.999, width=0.25)  # type: ignore[attr-defined]
    osc_d = SinOsc.ar(frequency=freq * 2.0) * 0.5  # type: ignore[attr-defined]
    top = osc_a * (1.0 - mix_x) + osc_b * mix_x
    bot = osc_c * (1.0 - mix_x) + osc_d * mix_x
    sig = (top * (1.0 - mix_y) + bot * mix_y) * 0.35
    sig = LPF.ar(source=sig, frequency=4500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.wavetable_morph")
def build_wavetable_morph(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Blip, LFNoise1
    pitch = ctx.input("pitch", 52.0)
    freq = _midi_to_hz(pitch)
    harmonics = LFNoise1.kr(frequency=0.1) * 20.0 + 22.0  # type: ignore[attr-defined]
    sig = Blip.ar(frequency=freq, harmonic_count=harmonics) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=6000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.folding_drone")
def build_folding_drone(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Fold, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 43.0)
    freq = _midi_to_hz(pitch)
    mod_drive = LFNoise1.kr(frequency=0.08) * 3.0 + 3.5  # type: ignore[attr-defined]
    sine = SinOsc.ar(frequency=freq) * mod_drive  # type: ignore[attr-defined]
    folded = Fold.ar(source=sine, minimum=-0.85, maximum=0.85) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=folded, frequency=4000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.chebyshev_drive")
def build_chebyshev_drive(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Fold, SinOsc
    pitch = ctx.input("pitch", 47.0)
    freq = _midi_to_hz(pitch)
    drive = ctx.param("drive", 3.0)
    sine = SinOsc.ar(frequency=freq) * drive  # type: ignore[attr-defined]
    shaped = Fold.ar(source=sine, minimum=-0.75, maximum=0.75) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=shaped, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.fm.four_operator")
def build_four_operator(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, SinOsc
    pitch = ctx.input("pitch", 57.0)
    freq = _midi_to_hz(pitch)
    op4 = SinOsc.ar(frequency=freq * 4.0) * freq * 1.5  # type: ignore[attr-defined]
    op3 = SinOsc.ar(frequency=freq * 2.0 + op4) * freq * 1.0  # type: ignore[attr-defined]
    op2 = SinOsc.ar(frequency=freq * 1.0 + op3) * freq * 0.5  # type: ignore[attr-defined]
    op1 = SinOsc.ar(frequency=freq + op2) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=op1, frequency=7000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.fm.feedback_drone")
def build_feedback_drone(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 38.0)
    freq = _midi_to_hz(pitch)
    mod_index = LFNoise1.kr(frequency=0.05) * 2.5 + 2.5  # type: ignore[attr-defined]
    op2 = SinOsc.ar(frequency=freq * 0.5) * freq * mod_index  # type: ignore[attr-defined]
    op1 = SinOsc.ar(frequency=freq + op2) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=op1, frequency=3000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.fm.bell_chime")
def build_bell_chime(ctx: BuildContext) -> Signals:
    from supriya.ugens import SinOsc
    pitch = ctx.input("pitch", 72.0)
    freq = _midi_to_hz(pitch)
    carrier_freq = freq
    mod_freq = freq * 3.5
    modulator = SinOsc.ar(frequency=mod_freq) * freq * 2.0  # type: ignore[attr-defined]
    carrier = SinOsc.ar(frequency=carrier_freq + modulator) * 0.3  # type: ignore[attr-defined]
    env = abs(carrier).lagged(0.02)
    return {"out": [carrier, carrier], "env_follow": env}


@implements("gen.fm.phase_mod_pad")
def build_phase_mod_pad(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 53.0)
    freq = _midi_to_hz(pitch)
    phase_shift = LFNoise1.kr(frequency=0.1) * 3.14  # type: ignore[attr-defined]
    mod = SinOsc.ar(frequency=freq * 1.002, phase=phase_shift) * freq * 0.8  # type: ignore[attr-defined]
    car = SinOsc.ar(frequency=freq + mod) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=car, frequency=5500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.additive.organ_partials")
def build_organ_partials(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, SinOsc
    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)
    p1 = SinOsc.ar(frequency=freq * 1.0) * 0.4  # type: ignore[attr-defined]
    p2 = SinOsc.ar(frequency=freq * 2.0) * 0.25  # type: ignore[attr-defined]
    p3 = SinOsc.ar(frequency=freq * 3.0) * 0.15  # type: ignore[attr-defined]
    p4 = SinOsc.ar(frequency=freq * 4.0) * 0.1  # type: ignore[attr-defined]
    sig = LPF.ar(source=p1 + p2 + p3 + p4, frequency=6000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.additive.bell_partials")
def build_bell_partials(ctx: BuildContext) -> Signals:
    from supriya.ugens import SinOsc
    pitch = ctx.input("pitch", 69.0)
    freq = _midi_to_hz(pitch)
    p1 = SinOsc.ar(frequency=freq * 1.0) * 0.4  # type: ignore[attr-defined]
    p2 = SinOsc.ar(frequency=freq * 2.756) * 0.25  # type: ignore[attr-defined]
    p3 = SinOsc.ar(frequency=freq * 5.404) * 0.15  # type: ignore[attr-defined]
    p4 = SinOsc.ar(frequency=freq * 8.93) * 0.08  # type: ignore[attr-defined]
    sig = p1 + p2 + p3 + p4
    env = abs(sig).lagged(0.02)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.spectral.spectral_blur")
def build_spectral_blur(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, HPF, LPF, LFNoise1, PinkNoise
    noise = PinkNoise.ar() * 0.3  # type: ignore[attr-defined]
    center = LFNoise1.kr(frequency=0.2) * 1500.0 + 2000.0  # type: ignore[attr-defined]
    filtered = BPF.ar(source=noise, frequency=center, reciprocal_of_q=0.15)  # type: ignore[attr-defined]
    sig = HPF.ar(source=filtered, frequency=150.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=8000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig * 1.4, sig * 1.4], "env_follow": env}


@implements("gen.spectral.frequency_shifter")
def build_frequency_shifter(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 50.0)
    freq = _midi_to_hz(pitch)
    shift = LFNoise1.kr(frequency=0.1) * 15.0  # type: ignore[attr-defined]
    carrier = SinOsc.ar(frequency=freq + shift) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=carrier, frequency=4000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.physical.bowed_string")
def build_bowed_string(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Dust, Pluck
    pitch = ctx.input("pitch", 55.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=1.5)  # type: ignore[attr-defined]
    plucked = Pluck.ar(  # type: ignore[attr-defined]
        source=trig,
        trigger=trig,
        maximum_delay_time=0.1,
        delay_time=1.0 / freq,
        decay_time=6.0,
        coefficient=0.1,
    ) * 0.5
    sig = LPF.ar(source=plucked, frequency=3500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.physical.marimba_bar")
def build_marimba_bar(ctx: BuildContext) -> Signals:
    from supriya.ugens import Dust, Pluck
    pitch = ctx.input("pitch", 62.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=1.0)  # type: ignore[attr-defined]
    bar = Pluck.ar(  # type: ignore[attr-defined]

        source=trig,
        trigger=trig,
        maximum_delay_time=0.1,
        delay_time=1.0 / freq,
        decay_time=2.5,
        coefficient=0.65,
    ) * 0.6
    env = abs(bar).lagged(0.02)
    return {"out": [bar, bar], "env_follow": env}


@implements("gen.physical.flute_pipe")
def build_flute_pipe(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LPF, LFNoise1, PinkNoise, SinOsc
    pitch = ctx.input("pitch", 67.0)
    freq = _midi_to_hz(pitch)
    air_noise = PinkNoise.ar() * 0.15  # type: ignore[attr-defined]
    air_filtered = BPF.ar(source=air_noise, frequency=freq * 2.0, reciprocal_of_q=0.3)  # type: ignore[attr-defined]
    vibrato = SinOsc.kr(frequency=5.0) * 3.0  # type: ignore[attr-defined]
    core_tone = SinOsc.ar(frequency=freq + vibrato) * 0.3  # type: ignore[attr-defined]
    sig = LPF.ar(source=core_tone + air_filtered, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.physical.karplus_ensemble")
def build_karplus_ensemble(ctx: BuildContext) -> Signals:
    from supriya.ugens import Dust, Pluck
    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)
    t1 = Dust.ar(density=1.0)  # type: ignore[attr-defined]
    t2 = Dust.ar(density=1.2)  # type: ignore[attr-defined]
    s1 = Pluck.ar(source=t1, trigger=t1, maximum_delay_time=0.1, delay_time=1.0 / freq, decay_time=5.0, coefficient=0.2)  # type: ignore[attr-defined]
    s2 = Pluck.ar(source=t2, trigger=t2, maximum_delay_time=0.1, delay_time=1.0 / (freq * 1.002), decay_time=5.0, coefficient=0.2)  # type: ignore[attr-defined]

    sig = (s1 + s2) * 0.4
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.vocal.choir_vowels")
def build_choir_vowels(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LPF, LFNoise1, Saw
    pitch = ctx.input("pitch", 57.0)
    freq = _midi_to_hz(pitch)
    saw = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]

    f1 = BPF.ar(source=saw, frequency=600.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    f2 = BPF.ar(source=saw, frequency=1200.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    f3 = BPF.ar(source=saw, frequency=2400.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    sig = LPF.ar(source=f1 + f2 + f3, frequency=4000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig * 1.2, sig * 1.2], "env_follow": env}


@implements("gen.vocal.whisper_noise")
def build_whisper_noise(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, HPF, LPF, LFNoise1, PinkNoise
    noise = PinkNoise.ar() * 0.25  # type: ignore[attr-defined]
    center = LFNoise1.kr(frequency=0.3) * 800.0 + 1500.0  # type: ignore[attr-defined]
    formant = BPF.ar(source=noise, frequency=center, reciprocal_of_q=0.15)  # type: ignore[attr-defined]
    sig = HPF.ar(source=formant, frequency=300.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=6000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig * 1.3, sig * 1.3], "env_follow": env}


@implements("gen.texture.grain_cloud_dense")
def build_grain_cloud_dense(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, HPF, LPF, Dust, PinkNoise
    pitch = ctx.input("pitch", 60.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=25.0) * 0.5  # type: ignore[attr-defined]
    grain = BPF.ar(source=trig, frequency=freq, reciprocal_of_q=0.08)  # type: ignore[attr-defined]
    sig = HPF.ar(source=grain, frequency=150.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=8000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.03)
    return {"out": [sig * 1.5, sig * 1.5], "env_follow": env}


@implements("gen.noise.pink_crackle")
def build_pink_crackle(ctx: BuildContext) -> Signals:
    from supriya.ugens import HPF, LPF, Dust, PinkNoise
    pink = PinkNoise.ar() * 0.08  # type: ignore[attr-defined]
    crackle = Dust.ar(density=18.0) * 0.4  # type: ignore[attr-defined]
    sig = HPF.ar(source=pink + crackle, frequency=100.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=10000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.noise.brownian_drift")
def build_brownian_drift(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise2, PinkNoise
    pink = PinkNoise.ar() * 0.35  # type: ignore[attr-defined]
    cutoff = LFNoise2.kr(frequency=0.1) * 300.0 + 400.0  # type: ignore[attr-defined]
    sig = LPF.ar(source=pink, frequency=cutoff)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.arpeggio.euclidean_pulse")
def build_euclidean_pulse(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Dust, SinOsc
    pitch = ctx.input("pitch", 64.0)
    freq = _midi_to_hz(pitch)
    pulse_trig = Dust.ar(density=4.0)  # type: ignore[attr-defined]
    tone = SinOsc.ar(frequency=freq) * pulse_trig * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=tone, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.arpeggio.random_walk_seq")
def build_random_walk_seq(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Dust, LFNoise0, SinOsc
    base_pitch = ctx.input("pitch", 60.0)
    base_freq = _midi_to_hz(base_pitch)
    step = LFNoise0.kr(frequency=3.0) * 12.0  # type: ignore[attr-defined]
    freq = base_freq * (2.0 ** (step / 12.0))
    trig = Dust.ar(density=3.0)  # type: ignore[attr-defined]
    tone = SinOsc.ar(frequency=freq) * trig * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=tone, frequency=6000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig, sig], "env_follow": env}


# ---------------------------------------------------------------------------
# 28 Weitere L2 Synthesizer-Familien (2. 10-fach Erweiterung)
# ---------------------------------------------------------------------------


@implements("gen.chaos.lorenz_attractor")
def build_lorenz_attractor(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LPF, LFNoise2, PinkNoise
    mod = LFNoise2.kr(frequency=0.2) * 800.0 + 1200.0  # type: ignore[attr-defined]
    noise = PinkNoise.ar() * 0.4  # type: ignore[attr-defined]
    sig = BPF.ar(source=noise, frequency=mod, reciprocal_of_q=0.08)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig * 1.5, sig * 1.5], "env_follow": env}


@implements("gen.chaos.rossler_chaos")
def build_rossler_chaos(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 45.0)
    freq = _midi_to_hz(pitch)
    chaos_mod = LFNoise1.kr(frequency=0.5) * freq * 0.5  # type: ignore[attr-defined]
    sig = SinOsc.ar(frequency=freq + chaos_mod) * 0.35  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.chaos.logistic_map")
def build_logistic_map(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Dust, SinOsc
    trig = Dust.ar(density=8.0)  # type: ignore[attr-defined]
    sig = SinOsc.ar(frequency=800.0) * trig * 0.35  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.02)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.chaos.chua_circuit")
def build_chua_circuit(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Fold, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 40.0)
    freq = _midi_to_hz(pitch)
    drive = LFNoise1.kr(frequency=0.1) * 3.0 + 3.0  # type: ignore[attr-defined]
    core = SinOsc.ar(frequency=freq) * drive  # type: ignore[attr-defined]
    sig = Fold.ar(source=core, minimum=-0.8, maximum=0.8) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=4000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.tb303_acid_bass")
def build_tb303_acid_bass(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise2, Pulse, Saw
    pitch = ctx.input("pitch", 36.0)
    freq = _midi_to_hz(pitch)
    saw = Saw.ar(frequency=freq) * 0.4  # type: ignore[attr-defined]
    cutoff_mod = LFNoise2.kr(frequency=0.4) * 1200.0 + 400.0  # type: ignore[attr-defined]
    sig = LPF.ar(source=saw, frequency=cutoff_mod)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.03)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.minimoog_sub")
def build_minimoog_sub(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Pulse, Saw, SinOsc
    pitch = ctx.input("pitch", 34.0)
    freq = _midi_to_hz(pitch)
    osc1 = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    osc2 = Pulse.ar(frequency=freq * 1.002, width=0.4) * 0.35  # type: ignore[attr-defined]
    sub = SinOsc.ar(frequency=freq * 0.5) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=osc1 + osc2 + sub, frequency=600.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.oberheim_sem_pad")
def build_oberheim_sem_pad(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, Pulse, Saw
    pitch = ctx.input("pitch", 55.0)
    freq = _midi_to_hz(pitch)
    saw = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    pulse = Pulse.ar(frequency=freq * 0.999, width=0.5) * 0.35  # type: ignore[attr-defined]
    cutoff = LFNoise1.kr(frequency=0.1) * 2000.0 + 2500.0  # type: ignore[attr-defined]
    sig = LPF.ar(source=saw + pulse, frequency=cutoff)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.ms20_ring_mod")
def build_ms20_ring_mod(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Pulse, Saw
    pitch = ctx.input("pitch", 50.0)
    freq = _midi_to_hz(pitch)
    car = Saw.ar(frequency=freq)  # type: ignore[attr-defined]
    mod = Pulse.ar(frequency=freq * 1.5, width=0.5)  # type: ignore[attr-defined]
    ring = car * mod * 0.35
    sig = LPF.ar(source=ring, frequency=4500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.fm.six_operator_pad")
def build_six_operator_pad(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, SinOsc
    pitch = ctx.input("pitch", 57.0)
    freq = _midi_to_hz(pitch)
    op6 = SinOsc.ar(frequency=freq * 6.0) * freq * 1.0  # type: ignore[attr-defined]
    op5 = SinOsc.ar(frequency=freq * 5.0 + op6) * freq * 0.8  # type: ignore[attr-defined]
    op4 = SinOsc.ar(frequency=freq * 4.0 + op5) * freq * 0.6  # type: ignore[attr-defined]
    op3 = SinOsc.ar(frequency=freq * 3.0 + op4) * freq * 0.4  # type: ignore[attr-defined]
    op2 = SinOsc.ar(frequency=freq * 2.0 + op3) * freq * 0.2  # type: ignore[attr-defined]
    op1 = SinOsc.ar(frequency=freq + op2) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=op1, frequency=6500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.fm.six_operator_bell")
def build_six_operator_bell(ctx: BuildContext) -> Signals:
    from supriya.ugens import SinOsc
    pitch = ctx.input("pitch", 74.0)
    freq = _midi_to_hz(pitch)
    mod = SinOsc.ar(frequency=freq * 3.5) * freq * 2.5  # type: ignore[attr-defined]
    car = SinOsc.ar(frequency=freq + mod) * 0.3  # type: ignore[attr-defined]
    env = abs(car).lagged(0.02)
    return {"out": [car, car], "env_follow": env}


@implements("gen.fm.six_operator_drone")
def build_six_operator_drone(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 41.0)
    freq = _midi_to_hz(pitch)
    mod_index = LFNoise1.kr(frequency=0.04) * 3.0 + 3.0  # type: ignore[attr-defined]
    mod = SinOsc.ar(frequency=freq * 0.5) * freq * mod_index  # type: ignore[attr-defined]
    car = SinOsc.ar(frequency=freq + mod) * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=car, frequency=2800.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.additive.partials_32")
def build_partials_32(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, SinOsc
    pitch = ctx.input("pitch", 50.0)
    freq = _midi_to_hz(pitch)
    p1 = SinOsc.ar(frequency=freq * 1.0) * 0.4  # type: ignore[attr-defined]
    p2 = SinOsc.ar(frequency=freq * 2.0) * 0.25  # type: ignore[attr-defined]
    p3 = SinOsc.ar(frequency=freq * 3.0) * 0.15  # type: ignore[attr-defined]
    sig = LPF.ar(source=p1 + p2 + p3, frequency=5500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.additive.drawbar_bank")
def build_drawbar_bank(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, SinOsc
    pitch = ctx.input("pitch", 53.0)
    freq = _midi_to_hz(pitch)
    sub = SinOsc.ar(frequency=freq * 0.5) * 0.3  # type: ignore[attr-defined]
    fund = SinOsc.ar(frequency=freq * 1.0) * 0.4  # type: ignore[attr-defined]
    fifth = SinOsc.ar(frequency=freq * 1.5) * 0.2  # type: ignore[attr-defined]
    oct = SinOsc.ar(frequency=freq * 2.0) * 0.15  # type: ignore[attr-defined]
    sig = LPF.ar(source=sub + fund + fifth + oct, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.additive.spectral_tilt")
def build_spectral_tilt(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 52.0)
    freq = _midi_to_hz(pitch)
    tilt = LFNoise1.kr(frequency=0.1) * 0.3 + 0.3  # type: ignore[attr-defined]
    p1 = SinOsc.ar(frequency=freq) * 0.4  # type: ignore[attr-defined]
    p2 = SinOsc.ar(frequency=freq * 2.0) * tilt  # type: ignore[attr-defined]
    sig = LPF.ar(source=p1 + p2, frequency=4500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.physical.steel_pan")
def build_steel_pan(ctx: BuildContext) -> Signals:
    from supriya.ugens import Dust, Pluck
    pitch = ctx.input("pitch", 67.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=1.2)  # type: ignore[attr-defined]
    pan = Pluck.ar(  # type: ignore[attr-defined]
        source=trig,
        trigger=trig,
        maximum_delay_time=0.1,
        delay_time=1.0 / freq,
        decay_time=2.0,
        coefficient=0.5,
    ) * 0.5
    env = abs(pan).lagged(0.02)
    return {"out": [pan, pan], "env_follow": env}


@implements("gen.physical.tubular_bell")
def build_tubular_bell(ctx: BuildContext) -> Signals:
    from supriya.ugens import Dust, Pluck
    pitch = ctx.input("pitch", 70.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=0.8)  # type: ignore[attr-defined]
    bell = Pluck.ar(  # type: ignore[attr-defined]
        source=trig,
        trigger=trig,
        maximum_delay_time=0.1,
        delay_time=1.0 / freq,
        decay_time=4.5,
        coefficient=0.3,
    ) * 0.6
    env = abs(bell).lagged(0.02)
    return {"out": [bell, bell], "env_follow": env}


@implements("gen.physical.glass_harmonica")
def build_glass_harmonica(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 76.0)
    freq = _midi_to_hz(pitch)
    shimmer = SinOsc.kr(frequency=6.0) * 2.0  # type: ignore[attr-defined]
    glass = SinOsc.ar(frequency=freq + shimmer) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=glass, frequency=8000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.physical.water_drop")
def build_water_drop(ctx: BuildContext) -> Signals:
    from supriya.ugens import Dust, SinOsc
    trig = Dust.ar(density=2.5)  # type: ignore[attr-defined]
    drop = SinOsc.ar(frequency=1200.0) * trig * 0.4  # type: ignore[attr-defined]
    env = abs(drop).lagged(0.01)
    return {"out": [drop, drop], "env_follow": env}


@implements("gen.texture.reverse_grain")
def build_reverse_grain(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, Dust
    pitch = ctx.input("pitch", 62.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=12.0)  # type: ignore[attr-defined]
    grain = BPF.ar(source=trig, frequency=freq, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    env = abs(grain).lagged(0.03)
    return {"out": [grain * 1.2, grain * 1.2], "env_follow": env}


@implements("gen.texture.pitch_shift_grain")
def build_pitch_shift_grain(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, Dust, LFNoise1
    pitch = ctx.input("pitch", 58.0)
    freq = _midi_to_hz(pitch)
    shift_mod = LFNoise1.kr(frequency=0.2) * 300.0  # type: ignore[attr-defined]
    trig = Dust.ar(density=15.0)  # type: ignore[attr-defined]
    grain = BPF.ar(source=trig, frequency=freq + shift_mod, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    env = abs(grain).lagged(0.03)
    return {"out": [grain * 1.3, grain * 1.3], "env_follow": env}


@implements("gen.texture.softcut_tape")
def build_softcut_tape(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, PinkNoise
    pink = PinkNoise.ar() * 0.2  # type: ignore[attr-defined]
    drift = LFNoise1.kr(frequency=0.15) * 800.0 + 1200.0  # type: ignore[attr-defined]
    sig = LPF.ar(source=pink, frequency=drift)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.vocal.soprano_formant")
def build_soprano_formant(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LPF, Saw
    pitch = ctx.input("pitch", 72.0)
    freq = _midi_to_hz(pitch)
    saw = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    f1 = BPF.ar(source=saw, frequency=800.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    f2 = BPF.ar(source=saw, frequency=1600.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    sig = LPF.ar(source=f1 + f2, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig * 1.2, sig * 1.2], "env_follow": env}


@implements("gen.vocal.tenor_formant")
def build_tenor_formant(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, LPF, Saw
    pitch = ctx.input("pitch", 48.0)
    freq = _midi_to_hz(pitch)
    saw = Saw.ar(frequency=freq) * 0.35  # type: ignore[attr-defined]
    f1 = BPF.ar(source=saw, frequency=400.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    f2 = BPF.ar(source=saw, frequency=900.0, reciprocal_of_q=0.1)  # type: ignore[attr-defined]
    sig = LPF.ar(source=f1 + f2, frequency=3000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig * 1.2, sig * 1.2], "env_follow": env}


@implements("gen.vocal.whispering_rain")
def build_whispering_rain(ctx: BuildContext) -> Signals:
    from supriya.ugens import BPF, HPF, LPF, PinkNoise
    noise = PinkNoise.ar() * 0.25  # type: ignore[attr-defined]
    sig = HPF.ar(source=noise, frequency=400.0)  # type: ignore[attr-defined]
    sig = LPF.ar(source=sig, frequency=7000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.03)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.casio_cz_pd")
def build_casio_cz_pd(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, SinOsc
    pitch = ctx.input("pitch", 52.0)
    freq = _midi_to_hz(pitch)
    pd_mod = LFNoise1.kr(frequency=0.2) * 2.0  # type: ignore[attr-defined]
    car = SinOsc.ar(frequency=freq, phase=pd_mod) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=car, frequency=5000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.04)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.vector_3d_pad")
def build_vector_3d_pad(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, LFNoise1, Saw, SinOsc
    pitch = ctx.input("pitch", 54.0)
    freq = _midi_to_hz(pitch)
    mix = LFNoise1.kr(frequency=0.1) * 0.5 + 0.5  # type: ignore[attr-defined]
    s1 = SinOsc.ar(frequency=freq)  # type: ignore[attr-defined]
    s2 = Saw.ar(frequency=freq * 1.002)  # type: ignore[attr-defined]
    sig = (s1 * (1.0 - mix) + s2 * mix) * 0.35
    sig = LPF.ar(source=sig, frequency=4500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.synth.chebyshev_bank")
def build_chebyshev_bank(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Fold, SinOsc
    pitch = ctx.input("pitch", 49.0)
    freq = _midi_to_hz(pitch)
    sine = SinOsc.ar(frequency=freq) * 3.5  # type: ignore[attr-defined]
    shaped = Fold.ar(source=sine, minimum=-0.8, maximum=0.8) * 0.35  # type: ignore[attr-defined]
    sig = LPF.ar(source=shaped, frequency=4000.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.05)
    return {"out": [sig, sig], "env_follow": env}


@implements("gen.arpeggio.subharmonic_seq")
def build_subharmonic_seq(ctx: BuildContext) -> Signals:
    from supriya.ugens import LPF, Dust, SinOsc
    pitch = ctx.input("pitch", 40.0)
    freq = _midi_to_hz(pitch)
    trig = Dust.ar(density=2.0)  # type: ignore[attr-defined]
    sub = SinOsc.ar(frequency=freq * 0.5) * trig * 0.4  # type: ignore[attr-defined]
    sig = LPF.ar(source=sub, frequency=2500.0)  # type: ignore[attr-defined]
    env = abs(sig).lagged(0.03)
    return {"out": [sig, sig], "env_follow": env}







