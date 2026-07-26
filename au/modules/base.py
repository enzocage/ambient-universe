"""Die Implementierungsschicht der Module.

Ein Modul besteht aus zwei Haelften: dem Manifest (deklarativ, YAML) und der
Implementierung (Python, hier registriert). Der SynthDef-Compiler kennt nur
diese Schnittstelle — er weiss nie, wie ein Modul intern arbeitet.

Eine Implementierung bekommt aufgeloeste Parameter und verbundene Eingaenge
und liefert benannte Ausgaenge. Sie kuemmert sich **nicht** um Glaettung,
DC-Sperre oder Begrenzung: das erledigt der Compiler nach den Regeln aus
``knowledge/dsp_rules.yaml``, damit keine Implementierung es vergessen kann.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from au.core.manifest import ModuleManifest
from au.core.seeds import SeedPath

#: Was aus einer Implementierung herausfliesst: benannte Signale.
Signals = dict[str, Any]


@dataclass(slots=True)
class BuildContext:
    """Alles, was eine Implementierung ueber ihren Einbauort wissen darf."""

    manifest: ModuleManifest
    node_id: str
    params: dict[str, Any]
    """Aufgeloeste Parameter: Konstante oder bereits geglaettetes Signal."""
    inputs: Signals
    """Verbundene Eingaenge, nach Portnamen. Unverbundene fehlen."""
    seed: SeedPath
    sample_rate: int
    channels: int = 2
    extras: dict[str, Any] = field(default_factory=dict)

    # -- Bequemlichkeit ------------------------------------------------------

    def param(self, name: str, default: Any = None) -> Any:
        """Parameterwert; faellt auf den Manifest-Default zurueck."""
        if name in self.params:
            return self.params[name]
        spec = self.manifest.params.get(name)
        if spec is not None and spec.default is not None:
            return spec.default
        return default

    def enum_index(self, name: str) -> int:
        """Index eines Auswahlparameters, robust gegen Zahl oder Text."""
        spec = self.manifest.params.get(name)
        choices = list(spec.enum or []) if spec else []
        value = self.param(name)
        if isinstance(value, str):
            return choices.index(value) if value in choices else 0
        try:
            return max(0, min(len(choices) - 1, int(round(float(value)))))
        except (TypeError, ValueError):
            return 0

    def enum_value(self, name: str) -> str:
        spec = self.manifest.params.get(name)
        choices = list(spec.enum or []) if spec else []
        if not choices:
            return ""
        return choices[self.enum_index(name)]

    def input(self, name: str, default: Any = None) -> Any:
        return self.inputs.get(name, default)

    def has_input(self, name: str) -> bool:
        return name in self.inputs

    @property
    def rng_seed(self) -> int:
        """32-Bit-Seed fuer die Zufallsquellen dieses Knotens."""
        return self.seed.child(self.node_id).sc


#: Signatur einer Modulimplementierung.
Builder = Callable[[BuildContext], Signals]

_IMPLEMENTATIONS: dict[str, Builder] = {}


class ImplementationMissingError(LookupError):
    """Fuer ein Manifest gibt es keine Implementierung."""


def implements(module_id: str) -> Callable[[Builder], Builder]:
    """Registriert eine Implementierung fuer eine Modul-ID.

    >>> @implements("gen.osc.bandlimited")           # doctest: +SKIP
    ... def build(ctx: BuildContext) -> Signals: ...
    """

    def decorator(fn: Builder) -> Builder:
        _IMPLEMENTATIONS[module_id] = fn
        return fn

    return decorator


def get_implementation(module_id: str) -> Builder:
    load_implementations()
    if module_id not in _IMPLEMENTATIONS:
        load_implementations(force_reload=True)
    if module_id in _IMPLEMENTATIONS:
        return _IMPLEMENTATIONS[module_id]

    # Fallback fuer prozedural erzeugte 500+ Katalog-Module
    from au.dsl.dsp_factory import build_procedural_module
    return build_procedural_module


def has_implementation(module_id: str) -> bool:
    load_implementations()
    if module_id not in _IMPLEMENTATIONS:
        load_implementations(force_reload=True)
    return module_id in _IMPLEMENTATIONS or ".v" in module_id


def implemented_ids() -> list[str]:
    load_implementations()
    return sorted(_IMPLEMENTATIONS)


_LOADED = False


def load_implementations(*, force_reload: bool = False) -> None:
    """Importiert alle Implementierungsmodule.

    Wenn ``force_reload=True``, werden die Module neu geladen.
    """
    global _LOADED
    if _LOADED and not force_reload:
        return
    _LOADED = True
    import importlib

    for name in (
        "au.modules.impl.generators",
        "au.modules.impl.processors",
        "au.modules.impl.modulators",
        "au.modules.impl.analysis",
        "au.modules.impl.voices",
    ):
        mod = importlib.import_module(name)
        if force_reload:
            importlib.reload(mod)

