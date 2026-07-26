"""Track-Rendering: Layer -> Stems -> Mix (plan.md Paragraph 4.8, Phase 9).

Jeder Layer referenziert ein Element-Rezept mit passender Dauer. Diese Phase
rendert jeden Layer einzeln (mit seiner Transposition), summiert ihn an
seiner geplanten Position in die Trackzeitachse und buendelt das Ergebnis in
Stems nach Rolle. Die volle Uebergangs-DSP-Kette (plan.md trn.*) und die
Sektions-Mixkette (Summen-EQ, Glue) folgen mit dem weiteren Ausbau; hier
steht die Summierung selbst, sauber und nachpruefbar.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import soundfile as sf

from au.core.config import Config, get_config
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.section import STEM_BUCKETS, TrackPlan
from au.render.element import render_element

if TYPE_CHECKING:  # pragma: no cover
    from au.core.registry import Registry
    from au.dsl.dramaturgy import DramaturgyArc
    from au.dsl.harmony import ChordTimeline
    from au.dsl.rhythm import Clock

#: Rollen, deren Makro-Grundstellung der Dramaturgie-Bogen modulieren darf.
#: Beschraenkt auf die Schichten, die den Track TRAGEN (plan.md
#: _CONTINUOUS_ROLES in au.integrator.proposals) -- ein Bogen auf einem
#: seltenen Einzelereignis (resonant_object) haette kaum Wirkung, weil das
#: Ereignis meist laengst vorbei ist, wenn sich die Intensitaet aendert.
_DRAMATURGY_ROLES: frozenset[str] = frozenset(
    {
        "foundation",
        "harmonic_drone",
        "moving_pad",
        "atmospheric_noise",
        "space_noise_elements",
        "harmonic_sphere",
        "subharmonic_pulse",
    }
)


@dataclass(frozen=True, slots=True)
class TrackRenderResult:
    mix_path: Path
    stem_paths: dict[str, Path]
    duration_s: float
    sample_rate: int


def render_track(
    plan: TrackPlan,
    recipes: dict[str, ElementRecipe],
    registry: Registry,
    output_dir: Path,
    *,
    seed: SeedPath,
    tail_s: float = 8.0,
    cfg: Config | None = None,
    chords: ChordTimeline | None = None,
    clock: Clock | None = None,
    dramaturgy: DramaturgyArc | None = None,
) -> TrackRenderResult:
    """Rendert einen vollstaendigen Track aus geloesten Layern.

    Args:
        recipes: Element-ID -> Rezept. Jedes in ``plan.layers`` referenzierte
            ``element_id`` muss hier vorkommen.
        chords: geteilte Akkordfolge (au.dsl.harmony) -- alle Layer, deren
            Muster eine Stufe braucht, ziehen aus demselben aktiven Akkord.
        clock: geteiltes Zeitraster (au.dsl.rhythm) fuer Ereigniszeitpunkte.
        dramaturgy: der Gesamtbogen (au.dsl.dramaturgy), moduliert die
            Makro-Grundstellung der tragenden Schichten ueber die Trackdauer.

    Raises:
        KeyError: Wenn ein Layer kein passendes Rezept findet.
    """
    c = cfg or get_config()
    output_dir.mkdir(parents=True, exist_ok=True)
    sample_rate = c.audio.sample_rate

    total_frames = int(round((plan.duration_s + tail_s) * sample_rate))
    stem_buffers: dict[str, np.ndarray] = {
        bucket: np.zeros((total_frames, c.audio.channels)) for bucket in set(STEM_BUCKETS.values())
    }

    for layer in plan.layers:
        if layer.element_id not in recipes:
            raise KeyError(
                f"Kein Rezept fuer Layer {layer.layer_id!r} (element_id {layer.element_id!r})"
            )
        base_recipe = recipes[layer.element_id]
        recipe = base_recipe.transposed(layer.transposition).model_copy(
            update={"duration_s": layer.duration_s, "id": f"{plan.track_id}_{layer.layer_id}"}
        )

        layer_seed = seed.layer(plan.layers.index(layer), layer.element_id)
        layer_path = output_dir / f"_layer_{layer.layer_id}.wav"

        intensity_curve = None
        if dramaturgy is not None and layer.role in _DRAMATURGY_ROLES:
            # Nur innerhalb der Layerdauer sampeln -- der Bogen selbst deckt
            # die volle Trackdauer ab (inklusive Schweif anderer Layer).
            n_points = max(4, int(layer.duration_s / 4.0))
            intensity_curve = [
                (t, dramaturgy.intensity_at(t))
                for t in np.linspace(0.0, layer.duration_s, n_points)
            ]

        render_element(
            recipe,
            registry,
            layer_path,
            seed=layer_seed,
            tail_s=tail_s,
            chords=chords,
            clock=clock,
            intensity_curve=intensity_curve,
        )

        data, sr = sf.read(str(layer_path), dtype="float64", always_2d=True)
        if sr != sample_rate:
            raise ValueError(f"Layer {layer.layer_id}: Abtastrate {sr} != Track-Rate {sample_rate}")

        start_frame = int(round(layer.entry_time_s * sample_rate))
        end_frame = min(total_frames, start_frame + len(data))
        usable = end_frame - start_frame
        if usable <= 0:
            continue

        bucket = STEM_BUCKETS.get(layer.role, "objects")
        stem_buffers[bucket][start_frame:end_frame, :] += data[:usable, : c.audio.channels]
        layer_path.unlink(missing_ok=True)

    stem_paths: dict[str, Path] = {}
    mix = np.zeros((total_frames, c.audio.channels))
    for bucket, buffer in stem_buffers.items():
        path = output_dir / f"stem_{bucket}.wav"
        sf.write(str(path), buffer, sample_rate, subtype="FLOAT")
        stem_paths[bucket] = path
        mix += buffer

    # Target Loudness Normalization (ca. -16 LUFS / RMS ~ 0.11)
    current_rms = float(np.sqrt(np.mean(np.square(mix))))
    if current_rms > 1e-6:
        target_rms = 0.11
        gain = min(3.5, max(0.5, target_rms / current_rms))
        mix = mix * gain

    # Master Soft Limiter (-1 dBFS Ceiling)
    ceiling = 0.89
    mix = np.tanh(mix / ceiling) * ceiling

    mix_path = output_dir / "mix.wav"
    sf.write(str(mix_path), mix, sample_rate, subtype="FLOAT")

    return TrackRenderResult(
        mix_path=mix_path,
        stem_paths=stem_paths,
        duration_s=plan.duration_s + tail_s,
        sample_rate=sample_rate,
    )

