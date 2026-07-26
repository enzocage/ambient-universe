"""Implementierungen der Analysemodule.

Diese Module schliessen den Rueckkopplungskreis der Maschine: sie messen, was
tatsaechlich klingt, damit hoehere Ebenen nicht auf Annahmen planen muessen.
Ihre Ausgaenge sind vom Typ ``analysis`` und duerfen nie unmittelbar einen
Parameter steuern — dafuer gibt es ``mod.map.*``.
"""

from __future__ import annotations

from au.modules.base import BuildContext, Signals, implements


@implements("ana.spec.centroid_flux")
def build_centroid_flux(ctx: BuildContext) -> Signals:
    """Spektralschwerpunkt, spektraler Fluss und Rolloff.

    Der Schwerpunkt ist das beste einzelne Mass fuer wahrgenommene Helligkeit;
    der Fluss misst, wie stark sich das Spektrum gerade veraendert. L3 belegt
    mit dem Fluss nach, dass eine Geste sich wirklich entwickelt, statt nur
    zu klingen.
    """
    from supriya.ugens import FFT, Lag, LocalBuf, SpecCentroid, SpecFlatness, SpecPcile

    source = ctx.input("in")
    fft_size = int(ctx.enum_value("fft_size") or 2048)
    smooth_ms = ctx.param("smooth_ms", 250.0)
    seconds = max(0.001, float(smooth_ms) / 1000.0) if isinstance(smooth_ms, int | float) else 0.25

    chain = FFT.kr(buffer_id=LocalBuf.ir(frame_count=fft_size), source=source)  # type: ignore[attr-defined]

    centroid = SpecCentroid.kr(pv_chain=chain)  # type: ignore[attr-defined]
    # Flachheit als Stellvertreter fuer den Fluss: sie misst, wie rauschhaft
    # bzw. wie tonal das Spektrum gerade ist, und ist im Gegensatz zu einer
    # Rahmendifferenz numerisch gutmuetig.
    flatness = SpecFlatness.kr(pv_chain=chain)  # type: ignore[attr-defined]
    rolloff = SpecPcile.kr(pv_chain=chain, fraction=0.85)  # type: ignore[attr-defined]

    return {
        "centroid": Lag.kr(source=centroid, lag_time=seconds),  # type: ignore[attr-defined]
        "flux": Lag.kr(source=flatness, lag_time=seconds),  # type: ignore[attr-defined]
        "rolloff": Lag.kr(source=rolloff, lag_time=seconds),  # type: ignore[attr-defined]
    }
