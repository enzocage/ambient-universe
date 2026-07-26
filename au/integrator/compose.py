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
from au.analysis.metrics import MusicalQualityReport, analyze_musical_quality
from au.arrange.solver import SolveResult, solve
from au.core.config import Config, get_config
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.blueprint import Blueprint, RoleSlot
from au.dsl.dna import AlbumDNA
from au.dsl.dramaturgy import DramaturgyArc, generate_arc
from au.dsl.complexity import CompositionBudget, budget_for_duration
from au.dsl.ableton_workflow import ProductionWorkflow, build_production_workflow
from au.dsl.element import ElementRecipe
from au.dsl.evolution import EvolutionPlan, generate_evolution_plan
from au.dsl.harmony import (
    ChordTimeline,
    generate_structured_chord_timeline,
)
from au.dsl.hierarchy import HierarchicalScore, build_default_hierarchical_score
from au.dsl.layer import LayerInstance
from au.dsl.motif import Motif, generate_motif, generate_phrase
from au.dsl.motif_transformations import TransformedMotif, transform_motif
from au.dsl.relations import Relation, RelationSet
from au.dsl.rhythm import Clock, tempo_from_character
from au.dsl.section import Section, SectionArrangement, TrackPlan, generate_section_arrangement
from au.dsl.section_profiles import SectionProfile, generate_section_profiles
from au.dsl.source_banks import build_tone_dna_for_entry, select_diverse_source_ensemble
from au.dsl.tone_dna import ToneDNA
from au.integrator.blueprint import derive_blueprint
from au.integrator.proposals import propose_candidates
from au.render.track import TrackRenderResult, render_track

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
    section_profiles: dict[str, SectionProfile]
    evolution_plans: dict[str, EvolutionPlan]
    tone_dnas: dict[str, ToneDNA]
    transformed_motifs: tuple[TransformedMotif, ...]
    hierarchy: HierarchicalScore
    budget: CompositionBudget
    workflow: ProductionWorkflow



def compose_track(
    prompt: str,
    output_dir: Path,
    *,
    duration_s: float = 90.0,
    max_slots: int | None = None,
    complexity: str = "auto",
    seed_root: int | None = None,
    registry: Registry | None = None,
    cfg: Config | None = None,
    on_progress: Callable[[str], None] | None = None,
) -> ComposeResult:
    """Ein einziger Durchlauf: Prompt -> DNA -> Blueprint -> Sektionen -> Motive -> Layer -> Track."""
    import soundfile as sf

    report = on_progress or (lambda _msg: None)
    budget = budget_for_duration(duration_s, complexity)
    report(f"Komplexitaetsbudget: {budget.name} | {budget.variants_per_role} Varianten/Rolle | {budget.section_count} Abschnitte")
    c = cfg or get_config()
    report("Lade Modulkatalog …")
    reg = registry or load_registry(c, strict=True)
    root_seed = SeedPath.root(seed_root if seed_root is not None else derive_seed_root(prompt))

    report("Erzeuge Album-DNA aus dem Prompt …")
    draft = generate_dna(prompt, seed_root=int(root_seed.value & 0xFFFF_FFFF))
    dna = draft.dna
    report(f"DNA: „{dna.title}“ — {', '.join(dna.character.descriptors[:5])}")

    blueprint = derive_blueprint(dna)
    # Ein Slotlimit darf die rhythmische Kernbesetzung nicht zufaellig abschneiden.
    # Pflichtrollen werden zuerst reserviert; optionale Texturen fuellen den Rest.
    required_order = (
        "foundation",
        "harmonic_drone",
        "bass_sequence",
        "arpeggiator",
        "subtle_percussive_background",
    )
    available = list(blueprint.role_slots)
    selected: list[RoleSlot] = []
    slot_limit = budget.max_slots if max_slots is None else min(max_slots, budget.max_slots)
    for role in required_order:
        slot = next((candidate for candidate in available if candidate.role == role), None)
        if slot is not None and len(selected) < slot_limit:
            selected.append(slot)
            available.remove(slot)
    selected.extend(available[: max(0, slot_limit - len(selected))])
    slots = tuple(selected)
    report(f"Blueprint: {len(slots)} Rollen-Slots ({', '.join(s.role for s in slots)})")

    # Musikalische Struktur-Planung: Sektionen, Akkorde & Motive VORAB erzeugen
    section_arr = generate_section_arrangement(duration_s)
    section_profs = generate_section_profiles(section_arr, root_seed.child("sec_profs"))
    chord_prog = generate_structured_chord_timeline(duration_s, blueprint.field, seed=root_seed.child("harmony"))
    chords = chord_prog.timeline

    main_motif = generate_motif("motif_main", blueprint.field, root_seed.child("main_motif"), length=4)
    sec_motif = generate_motif("motif_sec", blueprint.field, root_seed.child("sec_motif"), length=3)
    main_phrase = generate_phrase("phrase_main", main_motif, root_seed.child("main_phrase"), repetitions=4, pause_s=3.0)
    hierarchy = build_default_hierarchical_score(
        duration_s=duration_s,
        motif_id=main_motif.id,
        active_roles=tuple(slot.role for slot in slots),
    )

    # Motiv-Transformationen für Sektionskontraste
    t_motif_1 = transform_motif(main_motif, blueprint.field, root_seed.child("t_motif_1"), kind="transposed", step_shift=3)
    t_motif_2 = transform_motif(main_motif, blueprint.field, root_seed.child("t_motif_2"), kind="rhythmic_stretch", stretch_factor=1.5)
    t_motif_3 = transform_motif(sec_motif, blueprint.field, root_seed.child("t_motif_3"), kind="inverted")
    transformed_motifs = (t_motif_1, t_motif_2, t_motif_3)

    recipes: dict[str, ElementRecipe] = {}
    layers: list[LayerInstance] = []
    role_to_layer: dict[str, str] = {}

    role_names = tuple(s.role for s in slots)
    source_ensemble = select_diverse_source_ensemble(role_names, root_seed.child("ensemble"))
    tone_dnas: dict[str, ToneDNA] = {}
    evolution_plans: dict[str, EvolutionPlan] = {}

    for slot_idx, slot in enumerate(slots):
        report(f"Erzeuge Kandidaten für Slot „{slot.role}“ …")
        bank_entry = source_ensemble.get(slot.role)
        if bank_entry:
            t_dna = build_tone_dna_for_entry(bank_entry, slot.role, root_seed.child("dna", slot.slot_id))
            tone_dnas[slot.slot_id] = t_dna

        # Lange Renderbudgets kaufen echte Kandidatensuche und Varianten,
        # nicht nur eine laengere Version derselben Layerliste.
        candidates = propose_candidates(
            slot, dna, blueprint.field, reg, seed=root_seed.child("propose", slot.slot_id), n=budget.variants_per_role
        )

        sec_dur = duration_s / max(1, budget.variants_per_role)
        for cand_sub_idx in range(budget.variants_per_role):
            sub_id = f"{slot.slot_id}_sec{cand_sub_idx}"
            cand_idx = (slot_idx + cand_sub_idx + int(root_seed.value)) % len(candidates)
            entry_t = max(0.0, cand_sub_idx * sec_dur - (1.0 if cand_sub_idx > 0 else 0.0))
            exit_t = min(duration_s, (cand_sub_idx + 1) * sec_dur + 2.0)
            # Das Kandidatenrezept legt das Pattern fest. Ein pauschales
            # Ueberschreiben machte Arpeggiator und Bass zu Poisson-Piepsen.
            pattern_kind = chosen_pattern = candidates[cand_idx].recipe.pattern_kind

            chosen = candidates[cand_idx].recipe.model_copy(
                update={
                    # Varianten sind echte Abschnitts-/Phrasenfenster. Die
                    # alte Volltrack-Dauer machte alle Kandidaten zu einer
                    # statischen, sich ueberlagernden Suppe.
                    "duration_s": max(2.0, exit_t - entry_t),
                    "id": f"{sub_id}_elm",
                    "pattern_kind": chosen_pattern,
                }
            )
            recipes[chosen.id] = chosen

            layer_id = f"{sub_id}_layer"
            role_to_layer[slot.role] = layer_id

            evo_plan = generate_evolution_plan(
                layer_id, duration_s, root_seed.child("evo", layer_id), is_continuous=(pattern_kind == "sustained")
            )
            evolution_plans[layer_id] = evo_plan

            layers.append(
                LayerInstance(
                    layer_id=layer_id,
                    element_id=chosen.id,
                    role=slot.role,
                    band_hz=slot.band_hz,
                    entry_time_s=entry_t,
                    exit_time_s=exit_t,
                    tail_overhang_s=6.0,
                    lufs_target=slot.lufs - (3.0 if cand_sub_idx > 0 else 0.0),
                )
            )


    rack_modules: dict[str, str] = {}
    for layer in layers:
        rack_modules.setdefault(layer.role, recipes[layer.element_id].voice_module_id)
    workflow = build_production_workflow(
        duration_s=duration_s,
        budget_name=budget.name,
        section_count=budget.section_count,
        roles=tuple(slot.role for slot in slots),
        rack_modules=rack_modules,
    )
    workflow_errors = workflow.validate_budget(
        expected_scenes=budget.section_count,
        expected_roles=len(slots),
    )
    if workflow_errors:
        raise ValueError("Komplexitaetsbudget nicht umgesetzt: " + "; ".join(workflow_errors))

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
        section_profiles=section_profs,
        evolution_plans=evolution_plans,
        tone_dnas=tone_dnas,
        transformed_motifs=transformed_motifs,
        hierarchy=hierarchy,
        budget=budget,
        workflow=workflow,
    )
