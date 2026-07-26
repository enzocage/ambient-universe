"""Modulregistry: Auffinden, Versionieren, Abfragen (plan.md Paragraph 5.3).

Der Master-Integrator waehlt Module nie ueber Importe, sondern ausschliesslich
ueber Abfragen an die Registry. Damit ist der Modulraum jeder Ebene durch
Filter beschreibbar — und die Vokabularpolitik der Album-DNA (erlauben,
bevorzugen, verbieten) laesst sich als Abfrage ausdruecken statt als
Sonderfall im Code.
"""

from __future__ import annotations

import difflib
from collections.abc import Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from au.core.config import Config, get_config
from au.core.manifest import Category, ModuleManifest


@dataclass(frozen=True, slots=True)
class VocabularyPolicy:
    """Die Vokabularpolitik eines Werks (plan.md Paragraph 8.1).

    Muster duerfen auf ``*`` enden, etwa ``gen.drone.*``.
    ``forbid`` schlaegt ``allow``; ``prefer`` sortiert nur, es filtert nicht.
    """

    prefer: tuple[str, ...] = ()
    allow: tuple[str, ...] = ()
    forbid: tuple[str, ...] = ()

    @staticmethod
    def _matches(module_id: str, patterns: Iterable[str]) -> bool:
        for p in patterns:
            if p.endswith("*") and module_id.startswith(p[:-1]):
                return True
            if module_id == p:
                return True
        return False

    def permits(self, module_id: str) -> bool:
        if self._matches(module_id, self.forbid):
            return False
        if not self.allow and not self.prefer:
            return True
        return self._matches(module_id, self.allow) or self._matches(module_id, self.prefer)

    def is_preferred(self, module_id: str) -> bool:
        return self._matches(module_id, self.prefer)


@dataclass(frozen=True, slots=True)
class LicensePolicy:
    """Lizenzschranke fuer die Modulauswahl."""

    allow_nc_weights: bool = False
    """Modelle unter nicht-kommerzieller Lizenz zulassen (faerbt das Werk)."""


def _version_key(version: str) -> tuple[int, ...]:
    """Sortierschluessel fuer semantische Versionen; unparsbares hinten."""
    parts: list[int] = []
    for chunk in version.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts) or (0,)


class ModuleNotFoundError(LookupError):
    """Ein angefordertes Modul liegt nicht in der Registry."""


@dataclass
class Registry:
    """Ein durchsuchbarer Katalog von Modul-Manifesten."""

    _by_id: dict[str, dict[str, ModuleManifest]] = field(default_factory=dict)
    _sources: dict[tuple[str, str], Path] = field(default_factory=dict)
    load_errors: list[str] = field(default_factory=list)

    # -- Befuellen -----------------------------------------------------------

    def register(self, manifest: ModuleManifest, source: Path | None = None) -> None:
        versions = self._by_id.setdefault(manifest.id, {})
        if manifest.version in versions:
            raise ValueError(
                f"{manifest.id} Version {manifest.version} ist bereits registriert "
                f"(aus {self._sources.get((manifest.id, manifest.version), '?')})"
            )
        versions[manifest.version] = manifest
        if source is not None:
            self._sources[(manifest.id, manifest.version)] = source

    def discover(self, roots: Sequence[Path], *, strict: bool = False) -> Registry:
        """Laedt alle ``*.yaml``-Manifeste unterhalb der angegebenen Wurzeln.

        Args:
            strict: Wenn wahr, wirft ein fehlerhaftes Manifest sofort. Sonst
                wird es in :attr:`load_errors` vermerkt und uebersprungen —
                ein kaputtes Modul soll den ganzen Katalog nicht lahmlegen.
        """
        for root in roots:
            if not root.is_dir():
                continue
            for path in sorted(root.rglob("*.yaml")):
                if path.name.startswith("_"):
                    continue  # Vorlagen und Teilstuecke
                try:
                    manifest = ModuleManifest.from_yaml(path)
                    self.register(manifest, source=path)
                except (ValueError, OSError) as exc:
                    if strict:
                        raise
                    self.load_errors.append(str(exc))
        return self

    # -- Zugriff -------------------------------------------------------------

    def try_get(self, module_id: str, version: str | None = None) -> ModuleManifest | None:
        versions = self._by_id.get(module_id)
        if not versions:
            return None
        if version is not None:
            return versions.get(version)
        newest = max(versions, key=_version_key)
        return versions[newest]

    def get(self, module_id: str, version: str | None = None) -> ModuleManifest:
        manifest = self.try_get(module_id, version)
        if manifest is None:
            hint = self.suggest(module_id, limit=3)
            suffix = f" Meintest du: {', '.join(hint)}?" if hint else ""
            raise ModuleNotFoundError(f"Unbekanntes Modul {module_id!r}.{suffix}")
        return manifest

    def source_of(self, manifest: ModuleManifest) -> Path | None:
        return self._sources.get((manifest.id, manifest.version))

    def suggest(self, module_id: str, limit: int = 3) -> list[str]:
        """Naheliegende IDs fuer eine Tippfehlerkorrektur."""
        return difflib.get_close_matches(module_id, list(self._by_id), n=limit, cutoff=0.5)

    def __len__(self) -> int:
        return len(self._by_id)

    def __iter__(self) -> Iterator[ModuleManifest]:
        for versions in self._by_id.values():
            yield versions[max(versions, key=_version_key)]

    @property
    def ids(self) -> list[str]:
        return sorted(self._by_id)

    # -- Abfrage -------------------------------------------------------------

    def query(
        self,
        *,
        level: int | None = None,
        max_level: int | None = None,
        category: Category | None = None,
        family: str | None = None,
        tags_any: Sequence[str] | None = None,
        tags_all: Sequence[str] | None = None,
        semantic_near: dict[str, float] | None = None,
        cpu_budget: float | None = None,
        band_within: tuple[float, float] | None = None,
        vocabulary: VocabularyPolicy | None = None,
        license_policy: LicensePolicy | None = None,
        exclude: Sequence[str] | None = None,
    ) -> list[ModuleManifest]:
        """Filtert den Katalog. Alle Kriterien sind konjunktiv verknuepft.

        Die Reihenfolge des Ergebnisses ist deterministisch: bevorzugte Module
        zuerst, dann nach semantischer Naehe, dann nach ID. Ohne diese
        Festlegung waere die Modulwahl nicht reproduzierbar.
        """
        result: list[ModuleManifest] = []
        for manifest in self:
            if level is not None and manifest.level != level:
                continue
            if max_level is not None and manifest.level > max_level:
                continue
            if category is not None and manifest.category is not category:
                continue
            if family is not None and manifest.family != family:
                continue
            if tags_all and not set(tags_all).issubset(manifest.tags):
                continue
            if tags_any and not set(tags_any) & set(manifest.tags):
                continue
            if cpu_budget is not None and manifest.cost.cpu_units > cpu_budget:
                continue
            if band_within is not None:
                low, high = band_within
                mlow, mhigh = manifest.guarantees.band_hz
                if mlow < low or mhigh > high:
                    continue
            if vocabulary is not None and not vocabulary.permits(manifest.id):
                continue
            if (
                license_policy is not None
                and manifest.license.nc_weights
                and not license_policy.allow_nc_weights
            ):
                continue
            if exclude and VocabularyPolicy._matches(manifest.id, exclude):
                continue
            result.append(manifest)

        def sort_key(m: ModuleManifest) -> tuple[int, float, str]:
            preferred = 0 if (vocabulary and vocabulary.is_preferred(m.id)) else 1
            distance = _semantic_distance(m, semantic_near) if semantic_near else 0.0
            return (preferred, distance, m.id)

        return sorted(result, key=sort_key)

    # -- Berichte ------------------------------------------------------------

    def license_summary(self) -> dict[str, list[str]]:
        """Gruppiert Module nach Backend; listet NC-belastete gesondert."""
        by_backend: dict[str, list[str]] = {}
        for m in self:
            by_backend.setdefault(m.license.backend, []).append(m.id)
        nc = [m.id for m in self if m.license.nc_weights]
        if nc:
            by_backend["__nicht_kommerziell__"] = sorted(nc)
        return {k: sorted(v) for k, v in by_backend.items()}


def _semantic_distance(manifest: ModuleManifest, target: dict[str, float]) -> float:
    """Euklidischer Abstand im semantischen Raum; fehlende Achsen zaehlen 0.5."""
    total = 0.0
    for axis, wanted in target.items():
        have = float(manifest.semantic_vectors.get(axis, 0.5))
        total += (have - wanted) ** 2
    return float(total**0.5)


def load_registry(cfg: Config | None = None, *, strict: bool = False) -> Registry:
    """Baut die Registry aus dem konfigurierten Modulverzeichnis."""
    c = cfg or get_config()
    return Registry().discover([c.modules_dir], strict=strict)
