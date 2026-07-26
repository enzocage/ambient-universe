"""Implementierungen der Signalformer und Sicherheitsmodule (L1)."""

from __future__ import annotations

from typing import Any

from au.modules.base import BuildContext, Signals, implements

#: Teiltonverhaeltnisse je Material. Die Reihen bestimmen, ob ein Koerper wie
#: Glas, Metall oder Holz klingt — mehr als jede Huellkurve.
MATERIAL_RATIOS: dict[str, tuple[float, ...]] = {
    # Ganzzahlig: klingt tonal, fast wie eine Saite.
    "harmonic": (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0),
    # Gestreckt und unregelmaessig: glasig, hell, ohne klaren Grundton.
    "glass": (1.0, 2.32, 4.25, 6.63, 9.38, 12.4, 15.7, 19.3),
    # Glockenreihe: metallisch, mit ausgepraegter Schwebung.
    "metal": (1.0, 2.76, 5.40, 8.93, 13.3, 18.4, 24.2, 30.8),
    # Gedaempft und eng: hoelzern, kurz, warm.
    "wood": (1.0, 1.61, 2.34, 3.09, 3.87, 4.71, 5.62, 6.58),
    # Bewusst nicht physikalisch: ein Koerper, den es nicht gibt.
    "imaginary": (1.0, 1.41, 2.24, 3.16, 4.12, 5.10, 6.08, 7.07),
}


def resonator_bank(
    source: Any,
    fundamental: Any,
    ratios: tuple[float, ...],
    *,
    decay_base: Any,
    amplitude_tilt: Any = -1.0,
    detune: Any = 0.0,
    ceiling: float = 1.0,
) -> Any:
    """Summe gestimmter Resonatoren — der gemeinsame Koerper aller Materialien.

    Supriya 26.3 kennt kein ``DynKlank``; ``Ringz`` je Teilton ist ohnehin
    flexibler, weil Frequenz und Abklingzeit dann signalratenfaehig sind und
    damit driften duerfen.

    Hoehere Teiltoene klingen kuerzer und leiser. Ohne dieses Gefaelle klaenge
    die Bank wie eine Orgel, nicht wie ein Koerper.

    **Warum ein harter Deckel noetig ist:** ``Ringz`` ist bei kontinuierlicher
    Anregung ein getriebener Resonator, kein Impulsschlag. Faellt die Anregung
    *exakt* mit einer Resonanzfrequenz zusammen — etwa weil ``ratios[0] = 1.0``
    genau den Fundamentalton trifft, den eine harmonisch reiche Quelle stark
    enthaelt —, baut die eingeschwungene Amplitude proportional zur Guete
    ``Q = pi * frequency * decay_time`` auf. Gemessen: ein Fundamentalton von
    27.5 Hz mit 4.8 s Nachklang und phasenfester harmonischer Anregung
    erreichte unnormiert das 67-Fache der Eingangsamplitude.

    Eine generelle Guete-Normierung ist trotzdem der falsche Hebel: sie trifft
    rauschangeregte Koerper (wie den Glockenkoerper) genauso hart, obwohl deren
    Guete bei gleichem Nachklang sogar *hoeher* liegen kann, ohne dass ihre
    Amplitude explodiert — Rauschen konzentriert seine Energie nicht auf eine
    einzelne Frequenz, ein Sinuston schon. Eine Q-basierte Formel machte den
    Glockenkoerper deshalb im Test praktisch stumm (Spitze < 1e-5), obwohl er
    nie ein Sicherheitsproblem hatte.

    Die Loesung ist ein Deckel auf dem *Ergebnis*, nicht auf der Ursache: die
    milde, weiterhin decay-basierte Grundnormierung bleibt (sie ist fuer den
    Normalfall ausreichend), und eine ``tanh``-Kennlinie begrenzt das
    Bankresultat hart auf ``ceiling``. Fuer alle ueblichen Pegel (deutlich
    unter dem Deckel) ist ``tanh`` na­hezu linear und veraendert den Klang
    kaum; nur der pathologische Resonanzfall wird sichtbar (und hoerbar)
    begrenzt, statt den Prozess zu sprengen.
    """
    from supriya.ugens import Ringz

    voices = []
    for index, ratio in enumerate(ratios):
        frequency = fundamental * ratio * (1.0 + detune)
        decay = decay_base / (1.0 + 0.55 * index)
        if isinstance(amplitude_tilt, int | float):
            # tilt = -1: steiler Abfall (dunkel, hohl); tilt = +1: flach (hell).
            weight = 1.0 / (1.0 + 0.9 * index) ** (1.0 - float(amplitude_tilt) * 0.5)
        else:
            weight = 1.0 / (1.0 + 0.9 * index)
        normalized = weight / (1.0 + 2.0 * decay)
        voices.append(Ringz.ar(source=source, frequency=frequency, decay_time=decay) * normalized)  # type: ignore[attr-defined]
    summed = sum(voices) * (1.0 / len(ratios) ** 0.5)
    return (summed / ceiling).tanh() * ceiling


@implements("prc.util.dcblock")
def build_dcblock(ctx: BuildContext) -> Signals:
    """Entfernt den Gleichanteil. Pflicht in jeder Rueckkopplungsschleife."""
    from supriya.ugens import LeakDC

    cutoff = ctx.param("cutoff_hz", 10.0)
    # LeakDC arbeitet ueber einen Koeffizienten nahe 1; die Eckfrequenz wird
    # daraus genaehert (coef ~ 1 - 2*pi*fc/sr).
    if isinstance(cutoff, int | float):
        coefficient = max(0.9, min(0.9999, 1.0 - 6.2832 * float(cutoff) / ctx.sample_rate))
    else:
        coefficient = 0.995
    return {"out": LeakDC.ar(source=ctx.input("in"), coefficient=coefficient)}  # type: ignore[attr-defined]


@implements("prc.util.softclip")
def build_softclip(ctx: BuildContext) -> Signals:
    """Weiche, monotone Begrenzung ohne harte Kante.

    ``hardness`` blendet zwischen einer tanh-Kennlinie (sehr weich) und einer
    Kennlinie knapp unter hartem Clipping. Beide sind stetig — ein Sweep ueber
    ``hardness`` erzeugt keinen Sprung.
    """
    source = ctx.input("in")
    ceiling = ctx.param("ceiling", 0.5)
    hardness = ctx.param("hardness", 0.3)

    normalized = source / ceiling
    soft = normalized.tanh()
    hard = normalized.clip(-1.0, 1.0)
    blended = soft * (1.0 - hardness) + hard * hardness
    return {"out": blended * ceiling}


@implements("prc.filter.svf_morph")
def build_svf_morph(ctx: BuildContext) -> Signals:
    """Stufenlos morphendes State-Variable-Filter.

    Die drei Charakteristiken laufen parallel und werden ueberblendet, statt
    umgeschaltet zu werden — nur so ist ein Morph-Sweep artefaktfrei.
    """
    from supriya.ugens import BPF, HPF, RLPF

    source = ctx.input("in")
    cutoff = ctx.input("cutoff", ctx.param("cutoff", 1200.0))
    resonance = ctx.input("resonance", ctx.param("resonance", 0.2))
    morph = ctx.param("morph", 0.0)

    # RLPF erwartet einen Guetefaktor als Kehrwert: 1.0 = keine Resonanz.
    rq = (
        (1.0 - resonance * 0.98).clip(0.02, 1.0)
        if not isinstance(resonance, float)
        else max(0.02, 1.0 - resonance * 0.98)
    )

    low = RLPF.ar(source=source, frequency=cutoff, reciprocal_of_q=rq)  # type: ignore[attr-defined]
    band = BPF.ar(source=source, frequency=cutoff, reciprocal_of_q=rq)  # type: ignore[attr-defined]
    high = HPF.ar(source=source, frequency=cutoff)  # type: ignore[attr-defined]

    if isinstance(morph, int | float):
        m = float(morph)
        w_low = max(0.0, 1.0 - 2.0 * m)
        w_band = 1.0 - abs(2.0 * m - 1.0)
        w_high = max(0.0, 2.0 * m - 1.0)
    else:
        w_low = (1.0 - morph * 2.0).clip(0.0, 1.0)
        w_band = 1.0 - abs(morph * 2.0 - 1.0)
        w_high = (morph * 2.0 - 1.0).clip(0.0, 1.0)

    return {"out": low * w_low + band * w_band + high * w_high}


@implements("prc.resonator.klank_bank")
def build_klank_bank(ctx: BuildContext) -> Signals:
    """Bank gestimmter Resonatoren — aus Rauschen wird ein Koerper.

    Die Teiltonverhaeltnisse sind ein Aufbauparameter: ein Materialwechsel zur
    Laufzeit waere ein Sprung durch den gesamten Klang, kein Morph.
    """
    source = ctx.input("in")
    fundamental = ctx.input("fundamental", ctx.param("fundamental", 220.0))
    damp = ctx.param("damp", 0.7)
    spread = ctx.param("spread", 0.3)

    ratios = MATERIAL_RATIOS[ctx.enum_value("ratios_set") or "glass"]
    count = (
        int(ctx.param("partials", 8.0))
        if isinstance(ctx.param("partials", 8.0), int | float)
        else 8
    )
    ratios = ratios[: max(3, min(len(ratios), count))]

    decay_base = 0.05 + 12.0 * damp**3
    normalized = resonator_bank(source, fundamental, ratios, decay_base=decay_base) * 0.6

    if ctx.channels >= 2:
        # Teiltoene leicht auseinanderziehen, ohne die Mitte zu verlieren.
        from supriya.ugens import DelayN

        widened = DelayN.ar(source=normalized, maximum_delay_time=0.02, delay_time=0.008)  # type: ignore[attr-defined]
        left = normalized * (1.0 - spread * 0.5) + widened * (spread * 0.5)
        right = normalized * (1.0 - spread * 0.5) - widened * (spread * 0.5)
        return {"out": [left, right]}
    return {"out": normalized}


@implements("prc.saturation.tape")
def build_tape_saturation(ctx: BuildContext) -> Signals:
    """Weiche Saettigung nach Bandvorbild.

    ``bias`` verschiebt den Arbeitspunkt und erzeugt dadurch geradzahlige
    Obertoene — der Grund, warum Band waermer klingt als reine Uebersteuerung.
    """
    from supriya.ugens import LPF

    source = ctx.input("in")
    drive = ctx.param("drive", 0.25)
    bias = ctx.param("bias", 0.0)
    rolloff = ctx.param("hf_rolloff", 0.2)
    trim = ctx.param("output_trim", 0.0)

    import math

    driven = (source * (1.0 + drive * 8.0)) + bias
    bias_tanh = math.tanh(bias) if isinstance(bias, int | float) else bias.tanh()
    saturated = driven.tanh() - bias_tanh

    if isinstance(rolloff, int | float):
        cutoff = 18000.0 * (1.0 - 0.85 * float(rolloff))
    else:
        cutoff = (1.0 - rolloff * 0.85) * 18000.0
    filtered = LPF.ar(source=saturated, frequency=cutoff)  # type: ignore[attr-defined]

    gain = 10.0 ** (trim / 20.0) if isinstance(trim, int | float) else trim.db_to_amplitude()
    # Pegelausgleich: mehr Drive soll waermer klingen, nicht lauter.
    compensation = 1.0 / (1.0 + drive * 3.0)
    return {"out": filtered * compensation * gain}
