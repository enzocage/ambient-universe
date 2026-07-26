"""Tests der Seed-Hierarchie (plan.md Paragraph 13.1)."""

from __future__ import annotations

import pytest

from au.core.seeds import SeedPath, derive, to_sc_seed

pytestmark = pytest.mark.smoke


def test_derive_is_deterministic() -> None:
    assert derive(42, "album") == derive(42, "album")


def test_derive_depends_on_parent() -> None:
    assert derive(42, "album") != derive(43, "album")


def test_derive_depends_on_path() -> None:
    assert derive(42, "album") != derive(42, "track")


def test_derive_has_no_path_collisions() -> None:
    """Die Trennzeichen muessen ("ab", "c") von ("a", "bc") unterscheiden."""
    assert derive(1, "ab", "c") != derive(1, "a", "bc")


def test_track_seeds_are_independent() -> None:
    """Kernanforderung: Aenderungen in Track 3 duerfen Track 1 nicht beruehren."""
    album = SeedPath.root(481_723).album()
    seeds = {album.track(i).value for i in range(16)}
    assert len(seeds) == 16, "Trackseeds muessen paarweise verschieden sein"


def test_sibling_layers_differ_by_element_id() -> None:
    section = SeedPath.root(7).album().track(0).section(0)
    a = section.layer(0, "elm_a")
    b = section.layer(0, "elm_b")
    assert a.value != b.value


def test_label_records_the_derivation_path() -> None:
    p = SeedPath.root(481_723).album().track(0).section(2).layer(1, "elm_0037")
    assert p.label == "root/album/track:0/section:2/layer:1:elm_0037"


def test_sc_seed_fits_in_31_bits() -> None:
    for i in range(64):
        value = SeedPath.root(i).album().track(i).value
        assert 0 <= to_sc_seed(value) <= 0x7FFF_FFFF


def test_seed_stays_in_64_bit_range() -> None:
    p = SeedPath.root(2**63 + 12345)
    assert 0 <= p.value < 2**64
    assert 0 <= p.album().value < 2**64
