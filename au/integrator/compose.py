"""End-to-End-Kurzschluss: Prompt -> hoerbarer Track (fuer CLI/Demo).

Verbindet die bereits gebauten Phasen 4-9 zu einem einzigen Durchlauf, ohne
die interaktive Vorhoer-/Modulationsschleife aus Phase 6 (dafuer gibt es
`au propose` / `au freeze` einzeln). Waehlt je Rollen-Slot automatisch den
ersten Vorschlagskandidaten -- der Kompromiss, den ein einziger CLI-Aufruf
braucht, um ohne Nutzerinteraktion zu einem Ergebnis zu kommen.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from au.agents.dna_agent import derive_seed_root, generate_dna
from au.arrange.solver import SolveResult, solve
from au.core.config import Config, get_config
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.blueprint import Blueprint
from au.dsl.dna import AlbumDNA
from au.dsl.dramaturgy import DramaturgyArc, generate_arc
from au.dsl.element import ElementRecipe
from au.dsl.harmony import ChordTimeline, generate_chord_timeline
from au.dsl.layer import LayerInstance
from au.dsl.relations import Relation, RelationSet
from au.dsl.rhythm import Clock, tempo_from_character
from au.dsl.section import Section, TrackPlan
from au.integrator.blueprint import derive_blueprint
from au.integrator.proposals import propose_candidates
from au.render.track import TrackRenderResult, render_track

from au.analysis.metrics import MusicalQualityReport, analyze_musical_quality
from au.dsl.harmony import ChordProgression, ChordTimeline, generate_structured_chord_timeline
from au.dsl.motif import Motif, Phrase, generate_motif, generate_phrase
from au.dsl.section import Section, SectionArrangement, TrackPlan, generate_section_arrangement

#: Nur diese Relationskinds sind in der Relations-Algebra strukturell pruefbar
#: (plan.md 7.3, siehe au.dsl.relations); der Rest sind weiche L6-Ziele.
_STRUCTURAL_KINDS: frozenset[str] = frozenset({"supports", "answers", "avoids", "contrasts"})


@dataclass(frozen=True, slots=True)
class ComposeResult:
    dna: AlbumDNA
    blueprint: Blueprint
    recipes: dict[str, ElementRecipe]
    solve_result: SolveResult
    track: TrackRenderResult
    open_questions: list[str]
    chords: ChordTimeline
    clock: Clock
    dramaturgy: DramaturgyArc
    quality_report: MusicalQualityReport
    section_arrangement: SectionArrangement
    motifs: tuple[Motif, ...]


def compose_track(
    prompt: str,
    output_dir: Path,
    *,
    duration_s: float = 90.0,
    max_slots: int = 6,
    seed_root: int | None = None,
    registry: Registry | None = None,
    cfg: Config | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> ComposeResult:
    """Ein einziger Durchlauf: Prompt -> DNA -> Blueprint -> Sektionen -> Motive -> Layer -> Track."""
    import soundfile as sf

    report = on_progress or (lambda _msg: None)
    c = cfg or get_config()
    report("Lade Modulkatalog …")
    reg = registry or load_registry(c, strict=True)
    root_seed = SeedPath.root(seed_root if seed_root is not None else derive_seed_root(prompt))

    report("Erzeuge Album-DNA aus dem Prompt …")
    draft = generate_dna(prompt, seed_root=int(root_seed.value & 0xFFFF_FFFF))
    dna = draft.dna
    report(f"DNA: „{dna.title}“ — {', '.join(dna.character.descriptors[:5])}")

    blueprint = derive_blueprint(dna)
    slots = blueprint.role_slots[:max_slots]
    report(f"Blueprint: {len(slots)} Rollen-Slots ({', '.join(s.role for s in slots)})")

    # Musikalische Struktur-Planung: Sektionen, Akkorde & Motive VORAB erzeugen
    section_arr = generate_section_arrangement(duration_s)
    chord_prog = generate_structured_chord_timeline(duration_s, blueprint.field, seed=root_seed.child("harmony"))
    chords = chord_prog.timeline

    main_motif = generate_motif("motif_main", blueprint.field, root_seed.child("main_motif"), length=4)
    sec_motif = generate_motif("motif_sec", blueprint.field, root_seed.child("sec_motif"), length=3)
    main_phrase = generate_phrase("phrase_main", main_motif, root_seed.child("main_phrase"), repetitions=4, pause_s=3.0)

    recipes: dict[str, ElementRecipe] = {}
    layers: list[LayerInstance] = []
    role_to_layer: dict[str, str] = {}

    for slot in slots:
        report(f"Erzeuge Kandidaten für Slot „{slot.role}“ …")
        candidates = propose_candidates(
            slot, dna, blueprint.field, reg, seed=root_seed.child("propose", slot.slot_id), n=3
        )

        pattern_kind = "sustained" if slot.role in ("foundation", "harmonic_drone", "moving_pad") else "poisson"
        chosen = candidates[0].recipe.model_copy(
            update={
                "duration_s": duration_s,
                "id": f"{slot.slot_id}_elm",
                "pattern_kind": pattern_kind,
            }
        )
        recipes[chosen.id] = chosen

        layer_id = f"{slot.slot_id}_layer"
        role_to_layer[slot.role] = layer_id

        # Gated Layer Activity nach Sektionsplan
        entry_t = 0.0
        exit_t = duration_s
        if slot.role in ("subharmonic_pulse", "moving_pad"):
            entry_t = section_arr.build[0]
        elif slot.role in ("signal_motif", "resonant_object", "granular_texture", "arpeggiator"):
            entry_t = section_arr.peak[0]
            exit_t = section_arr.peak[1]

        layers.append(
            LayerInstance(
                layer_id=layer_id,
                element_id=chosen.id,
                role=slot.role,
                band_hz=slot.band_hz,
                entry_time_s=entry_t,
                exit_time_s=exit_t,
                tail_overhang_s=6.0,
                lufs_target=slot.lufs,
            )
        )

    relations = []
    for hint in blueprint.relation_hints:
        if hint.kind not in _STRUCTURAL_KINDS:
            continue
        a, b = role_to_layer.get(hint.from_role), role_to_layer.get(hint.to_role)
        if a and b and a != b:
            relations.append(Relation(kind=hint.kind, from_layer=a, to_layer=b))
    relation_set = RelationSet(relations=tuple(relations))

    report(f"Löse Verschaltung ({len(layers)} Schichten, {len(relations)} Relationen) …")
    result = solve(
        layers, relation_set, track_duration_s=duration_s, seed=int(root_seed.value & 0xFFFF)
    )
    report(f"Solver-Score: {result.score:.3f} ({len(result.conflicts)} Restkonflikt(e))")

    section = Section(
        section_id="sec_0",
        start_s=0.0,
        end_s=duration_s,
        layer_ids=tuple(layer.layer_id for layer in result.layers),
    )
    plan = TrackPlan(
        track_id="compose",
        duration_s=duration_s,
        arc_shape="emergence",
        sections=(section,),
        layers=result.layers,
    )

    tempo = tempo_from_character(
        dna.character.event_density_mean, dna.character.emotional_temperature[1]
    )
    clock = Clock(bpm=tempo)
    dramaturgy = generate_arc(duration_s, seed=root_seed.child("dramaturgy"))

    output_dir.mkdir(parents=True, exist_ok=True)
    report("Rendere Track (Layer, Stems, Mix) …")
    track = render_track(
        plan,
        recipes,
        reg,
        output_dir,
        seed=root_seed.track(0),
        cfg=c,
        chords=chords,
        clock=clock,
        dramaturgy=dramaturgy,
    )

    # Qualitätsanalyse des finalen Mixes
    mix_data, sr = sf.read(str(track.mix_path), dtype="float64", always_2d=True)
    quality = analyze_musical_quality(mix_data, sr)
    report(f"Musikalische Qualitätsanalyse: {quality.summary()}")

    return ComposeResult(
        dna=dna,
        blueprint=blueprint,
        recipes=recipes,
        solve_result=result,
        track=track,
        open_questions=draft.open_questions,
        chords=chords,
        clock=clock,
        dramaturgy=dramaturgy,
        quality_report=quality,
        section_arrangement=section_arr,
        motifs=(main_motif, sec_motif),
    )

