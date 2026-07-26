"""Seed-Hierarchie (plan.md Paragraph 13.1).

Jede Ebene leitet ihre Seeds deterministisch aus der Ebene darueber ab:

    seed_root
     └─ seed_album      = H(seed_root, "album")
         └─ seed_track[i]   = H(seed_album, "track", i)
             └─ seed_section[j] = H(seed_track[i], "section", j)
                 └─ seed_layer[k]   = H(seed_section[j], "layer", k, element_id)

Folge: Das Aendern eines Elements in Track 3 veraendert nichts an Track 1 —
ohne diese Eigenschaft waere iteratives Arbeiten unertraeglich.

``H`` ist BLAKE2b, auf 64 Bit gekuerzt.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

_MASK64 = (1 << 64) - 1


def derive(parent: int, *parts: str | int) -> int:
    """Leitet einen Kindseed deterministisch aus Elternseed und Pfadteilen ab.

    >>> derive(42, "album") == derive(42, "album")
    True
    >>> derive(42, "album") != derive(43, "album")
    True
    """
    h = hashlib.blake2b(digest_size=8)
    h.update(parent.to_bytes(8, "big", signed=False))
    for part in parts:
        h.update(b"\x1f")  # Trennzeichen: verhindert Pfad-Kollisionen
        h.update(str(part).encode("utf-8"))
    return int.from_bytes(h.digest(), "big") & _MASK64


def to_numpy_seed(seed: int) -> int:
    """Numpy-Generatoren akzeptieren beliebig grosse Ints; hier nur Klarstellung."""
    return seed & _MASK64


def to_sc_seed(seed: int) -> int:
    """SuperCollider ``RandSeed`` erwartet einen 32-Bit-Wert."""
    return seed & 0x7FFF_FFFF


@dataclass(frozen=True, slots=True)
class SeedPath:
    """Ein benannter Punkt in der Seed-Hierarchie.

    Ermoeglicht lesbare Ableitungsketten:

    >>> root = SeedPath.root(481723)
    >>> layer = root.album().track(0).section(2).layer(1, "elm_0037")
    >>> layer.label
    'root/album/track:0/section:2/layer:1:elm_0037'
    """

    value: int
    label: str

    # -- Konstruktion --------------------------------------------------------

    @classmethod
    def root(cls, seed_root: int) -> SeedPath:
        return cls(value=seed_root & _MASK64, label="root")

    def child(self, *parts: str | int) -> SeedPath:
        suffix = ":".join(str(p) for p in parts)
        return SeedPath(value=derive(self.value, *parts), label=f"{self.label}/{suffix}")

    # -- Ebenen der Hierarchie ----------------------------------------------

    def album(self) -> SeedPath:
        return self.child("album")

    def track(self, index: int) -> SeedPath:
        return self.child("track", index)

    def section(self, index: int) -> SeedPath:
        return self.child("section", index)

    def layer(self, index: int, element_id: str) -> SeedPath:
        return self.child("layer", index, element_id)

    def events(self) -> SeedPath:
        return self.child("events")

    def gesture(self, index: int) -> SeedPath:
        return self.child("gesture", index)

    def element_candidate(self, slot: str, index: int) -> SeedPath:
        return self.child("candidate", slot, index)

    # -- Verwendung ----------------------------------------------------------

    @property
    def sc(self) -> int:
        """32-Bit-Seed fuer SuperCollider."""
        return to_sc_seed(self.value)

    def __int__(self) -> int:
        return self.value

    def __repr__(self) -> str:
        return f"SeedPath({self.label}, 0x{self.value:016x})"
