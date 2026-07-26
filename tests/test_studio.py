"""Phase-6/7-Akzeptanz: Vorschlaege, Editor-Agent, Bibliothek.

Aus plan.md Phase 6: Kandidaten sind nachweislich verschieden; Editor-Agent
haelt Safe-Bounds ein; Aenderungsprotokoll benennt jede Aenderung.
Aus plan.md Phase 7: Suche liefert plausible Treffer; eingefrorene Elemente
sind auf Dateisystemebene unveraenderlich (kein zweites Einfrieren derselben ID).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from au.agents.dna_agent import generate_dna
from au.agents.editor_agent import apply_instruction
from au.core.config import Config
from au.core.registry import Registry, load_registry
from au.core.seeds import SeedPath
from au.dsl.element import ElementRecipe
from au.dsl.field import HarmonicField
from au.integrator.blueprint import derive_blueprint
from au.integrator.proposals import propose_candidates
from au.library import index as lib_index
from au.library.store import freeze_element

pytestmark = pytest.mark.audio


@pytest.fixture(scope="module")
def registry() -> Registry:
    return load_registry(strict=True)


@pytest.fixture
def base_recipe() -> ElementRecipe:
    return ElementRecipe(
        id="elm_studio_test",
        name="Studio Test",
        voice_module_id="gen.object.modal_bell",
        field=HarmonicField(root_midi=57, mode="dorian"),
        lambda_per_min=6.0,
        duration_s=20.0,
    )


# -- Vorschlags-Engine -------------------------------------------------------


def test_candidates_have_distinct_theses(registry: Registry) -> None:
    dna = generate_dna("Ein kaltes, hohles Album.", seed_root=1).dna
    bp = derive_blueprint(dna)
    slot = bp.slot("resonant_object#0") or bp.role_slots[0]
    candidates = propose_candidates(slot, dna, bp.field, registry, seed=SeedPath.root(1), n=5)
    assert len({c.thesis for c in candidates}) == 5
    assert len({c.recipe.voice_module_id for c in candidates}) >= 1


def test_candidates_are_deterministic(registry: Registry) -> None:
    dna = generate_dna("Ein kaltes Album.", seed_root=1).dna
    bp = derive_blueprint(dna)
    slot = bp.role_slots[0]
    a = propose_candidates(slot, dna, bp.field, registry, seed=SeedPath.root(2), n=3)
    b = propose_candidates(slot, dna, bp.field, registry, seed=SeedPath.root(2), n=3)
    assert [c.recipe.model_dump() for c in a] == [c.recipe.model_dump() for c in b]


# -- Editor-Agent -------------------------------------------------------------


def test_warmer_lowers_brightness(base_recipe: ElementRecipe) -> None:
    result = apply_instruction(base_recipe, "mach es waermer")
    assert result.applied
    assert result.recipe.voice_macros.get("brightness", 0.5) < 0.5


def test_denser_increases_lambda(base_recipe: ElementRecipe) -> None:
    result = apply_instruction(base_recipe, "bitte dichter und mehr Ereignisse")
    assert result.recipe.lambda_per_min > base_recipe.lambda_per_min


def test_unrecognized_instruction_changes_nothing(base_recipe: ElementRecipe) -> None:
    result = apply_instruction(base_recipe, "xyzzy quux")
    assert result.unrecognized
    assert result.recipe.model_dump() == base_recipe.model_dump()


def test_macro_deltas_stay_within_bounds(base_recipe: ElementRecipe) -> None:
    """Safe-Bounds: wiederholtes 'waermer' darf 0.0 nie unterschreiten."""
    recipe = base_recipe
    for _ in range(20):
        recipe = apply_instruction(recipe, "waermer").recipe
    assert 0.0 <= recipe.voice_macros["brightness"] <= 1.0


def test_change_log_names_the_change(base_recipe: ElementRecipe) -> None:
    result = apply_instruction(base_recipe, "heller und laenger")
    assert any("brightness" in line for line in result.applied)
    assert any("duration_s" in line for line in result.applied)


# -- Bibliothek ---------------------------------------------------------------


def test_freeze_and_search_roundtrip(
    base_recipe: ElementRecipe, registry: Registry, tmp_path: Path
) -> None:
    cfg = Config(root=tmp_path)
    seed = SeedPath.root(42).child("element", base_recipe.id)
    element_dir = freeze_element(base_recipe, registry, seed=seed, cfg=cfg)

    assert (element_dir / "recipe.json").is_file()
    assert (element_dir / "card.md").is_file()
    assert (element_dir / "preview_solo.wav").is_file()

    lib_index.register_element(element_dir, cfg=cfg)
    results = lib_index.search("studio", cfg=cfg)
    assert any(r.id == base_recipe.id for r in results)


def test_freezing_twice_is_rejected(
    base_recipe: ElementRecipe, registry: Registry, tmp_path: Path
) -> None:
    cfg = Config(root=tmp_path)
    seed = SeedPath.root(43).child("element", base_recipe.id)
    freeze_element(base_recipe, registry, seed=seed, cfg=cfg)
    with pytest.raises(FileExistsError):
        freeze_element(base_recipe, registry, seed=seed, cfg=cfg)


def test_search_finds_by_voice_similarity(
    base_recipe: ElementRecipe, registry: Registry, tmp_path: Path
) -> None:
    cfg = Config(root=tmp_path)
    seed = SeedPath.root(44).child("element", base_recipe.id)
    element_dir = freeze_element(base_recipe, registry, seed=seed, cfg=cfg)
    lib_index.register_element(element_dir, cfg=cfg)

    similar = lib_index.find_similar_by_voice("gen.object.modal_bell", cfg=cfg)
    assert any(r.id == base_recipe.id for r in similar)
