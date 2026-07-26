"""Capability-Matrix aller Klang- und Prozessormodule (plan2.md Stufe 1).

Prueft alle registrierten Manifeste auf Vollstaendigkeit, Implementierung,
Renderbarkeit, Portdeklaration und Rolleneignung.
"""

from __future__ import annotations

from dataclasses import dataclass

from au.core.config import Config, get_config
from au.core.registry import Registry, load_registry
from au.modules.base import has_implementation, implemented_ids


@dataclass(frozen=True, slots=True)
class ModuleCapability:
    """Die Maschinelle Capability-Beschreibung eines Moduls."""

    module_id: str
    version: str
    category: str
    level: int
    has_manifest: bool
    has_impl: bool
    is_renderable: bool
    ports_in: tuple[str, ...]
    ports_out: tuple[str, ...]
    macros: tuple[str, ...]
    cpu_units: float
    band_hz: tuple[float, float]
    suggested_roles: tuple[str, ...]
    blocking_reasons: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CapabilityMatrix:
    """Gesamte Capability-Matrix des Modulkatalogs."""

    modules: tuple[ModuleCapability, ...]

    @property
    def total_count(self) -> int:
        return len(self.modules)

    @property
    def renderable_count(self) -> int:
        return sum(1 for m in self.modules if m.is_renderable)

    @property
    def missing_impl_count(self) -> int:
        return sum(1 for m in self.modules if not m.has_impl)

    def summary(self) -> str:
        return (
            f"Modulkatalog: {self.total_count} Manifeste · "
            f"{self.renderable_count} renderbar ({self.missing_impl_count} ohne Implementierung)"
        )


def audit_capability_matrix(
    registry: Registry | None = None, cfg: Config | None = None
) -> CapabilityMatrix:
    """Erzeugt eine vollstaendige Capability-Matrix aller Module."""
    c = cfg or get_config()
    reg = registry or load_registry(c, strict=True)
    all_impls = set(implemented_ids())

    capabilities: list[ModuleCapability] = []

    for manifest in reg:
        mod_id = manifest.id
        has_impl = mod_id in all_impls or has_implementation(mod_id)

        reasons: list[str] = []
        if not has_impl:
            reasons.append("Keine @implements-Funktion registriert")

        ports_in = tuple(p.name for p in manifest.ports.inputs)
        ports_out = tuple(p.name for p in manifest.ports.outputs)
        macros = tuple(manifest.macros.keys())

        # Rollenzuordnung aus Familie & Kategorie schaetzen
        roles: list[str] = []
        if manifest.family == "sub_bass":
            roles.extend(["foundation", "subharmonic_pulse"])
        elif manifest.family in ("drone", "sine_cluster"):
            roles.extend(["foundation", "harmonic_drone"])
        elif manifest.family in ("granular", "cloud"):
            roles.extend(["granular_texture", "atmospheric_noise"])
        elif manifest.family in ("arpeggio", "sequence"):
            roles.extend(["signal_motif", "arpeggiator"])
        else:
            roles.append("harmonic_drone")

        capabilities.append(
            ModuleCapability(
                module_id=mod_id,
                version=manifest.version,
                category=manifest.category.value if hasattr(manifest.category, "value") else str(manifest.category),
                level=manifest.level,
                has_manifest=True,
                has_impl=has_impl,
                is_renderable=has_impl and len(ports_out) > 0,
                ports_in=ports_in,
                ports_out=ports_out,
                macros=macros,
                cpu_units=manifest.cost.cpu_units,
                band_hz=manifest.guarantees.band_hz or (20.0, 20000.0),
                suggested_roles=tuple(roles),
                blocking_reasons=tuple(reasons),
            )
        )

    return CapabilityMatrix(modules=tuple(capabilities))
