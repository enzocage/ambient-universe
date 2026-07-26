"""Das Modul-Manifest (plan.md Paragraph 5.1).

Jedes Funktionsmodul besteht aus einem deklarativen Manifest (YAML) und einer
Implementierung (Python). Das Manifest ist die einzige Quelle der Wahrheit
darueber, was ein Modul kann, was es kostet und was es garantiert. Der
Master-Integrator plant ausschliesslich gegen Manifeste — er liest nie Code.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Any, Self

import yaml
from pydantic import BaseModel, Field, model_validator

from au.core.ports import PortSet


class Category(StrEnum):
    """Modulkategorie. Bestimmt das ID-Praefix."""

    GENERATOR = "generator"
    PROCESSOR = "processor"
    SPACE = "space"
    MODULATOR = "modulator"
    SYMBOLIC = "symbolic"
    ANALYSIS = "analysis"
    CRITIC = "critic"
    REPAIR = "repair"
    TRANSITION = "transition"
    IO = "io"


#: Zuordnung ID-Praefix -> Kategorie. Die ID traegt die Kategorie sichtbar.
PREFIX_BY_CATEGORY: dict[Category, str] = {
    Category.GENERATOR: "gen",
    Category.PROCESSOR: "prc",
    Category.SPACE: "spc",
    Category.MODULATOR: "mod",
    Category.SYMBOLIC: "sym",
    Category.ANALYSIS: "ana",
    Category.CRITIC: "crt",
    Category.REPAIR: "rep",
    Category.TRANSITION: "trn",
    Category.IO: "io",
}

#: Makros, die jede Stimme (Level >= 2, Kategorie generator) fuehren muss.
#: plan.md Paragraph 4.2: das Makroversprechen an alle hoeheren Ebenen.
REQUIRED_VOICE_MACROS: frozenset[str] = frozenset(
    {"brightness", "body", "noise_ratio", "motion", "material"}
)


class Curve(StrEnum):
    """Abbildungskennlinie eines Parameters oder Makros."""

    LIN = "lin"
    EXP = "exp"
    LOG = "log"
    STEP = "step"


class ParamSpec(BaseModel):
    """Ein steuerbarer Parameter mit sicherem Wertebereich."""

    model_config = {"frozen": True, "extra": "forbid"}

    min: float | None = None
    max: float | None = None
    default: float | str | None = None
    unit: str | None = None
    curve: Curve = Curve.LIN
    smooth_ms: float = Field(default=0.0, ge=0.0)
    """Glaettungszeit. L1 setzt sie automatisch durch; 0 nur fuer Parameter,
    die nie zur Laufzeit veraendert werden."""
    audio_rate_safe: bool = False
    """Ob dieser Parameter mit Audiorate moduliert werden darf."""
    structural: bool = False
    """Der Parameter bestimmt die *Form* des Signalgraphen (Zahl der
    Resonatoren, Unison-Stimmen, Materialreihe, FFT-Groesse) und wird zur
    Uebersetzungszeit auf eine Konstante festgelegt.

    Ein Makro darf einen strukturellen Parameter steuern, aber sein Wert steht
    dann beim Bauen der SynthDef fest und aendert sich zur Laufzeit nicht mehr.
    Alles andere waere ein Umbau des Graphen mitten im Klang — hoerbar als
    Schnitt, nicht als Morph. Enum-Parameter sind immer strukturell."""
    enum: list[str] | None = None
    """Alternativ zu min/max: eine geschlossene Auswahl."""
    summary: str | None = None

    @model_validator(mode="after")
    def _coherent(self) -> Self:
        if self.enum is not None:
            if self.min is not None or self.max is not None:
                raise ValueError("enum und min/max schliessen einander aus")
            if self.default is not None and self.default not in self.enum:
                raise ValueError(f"default {self.default!r} liegt nicht in enum {self.enum}")
            return self
        if self.min is None or self.max is None:
            raise ValueError("numerische Parameter brauchen min und max")
        if self.min > self.max:
            raise ValueError(f"min ({self.min}) ist groesser als max ({self.max})")
        if isinstance(self.default, str):
            raise ValueError("numerischer Parameter mit Text-Default")
        if self.default is not None and not (self.min <= self.default <= self.max):
            raise ValueError(f"default {self.default} liegt ausserhalb [{self.min}, {self.max}]")
        return self

    @property
    def is_enum(self) -> bool:
        return self.enum is not None

    @property
    def is_structural(self) -> bool:
        """Enums sind immer strukturell; sonst entscheidet das Flag."""
        return self.structural or self.is_enum

    def clamp(self, value: float) -> float:
        """Begrenzt einen Wert auf den sicheren Bereich."""
        if self.min is None or self.max is None:
            return value
        return max(self.min, min(self.max, value))


class MacroTarget(BaseModel):
    """Wohin ein Makro einen einzelnen Parameter fuehrt.

    ``from`` ist der Wert bei Makrostellung 0, ``to`` der bei Stellung 1.
    ``from > to`` ist ausdruecklich erlaubt und der Normalfall bei invertierten
    Beziehungen — mehr Helligkeit bedeutet *weniger* Daempfung.
    """

    model_config = {"frozen": True, "extra": "forbid", "populate_by_name": True}

    start: float = Field(alias="from")
    end: float = Field(alias="to")

    def at(self, position: float) -> float:
        """Linearer Wert an der Makrostellung ``position`` aus [0, 1]."""
        p = max(0.0, min(1.0, position))
        return self.start + (self.end - self.start) * p


class MacroSpec(BaseModel):
    """Ein Makro: eine benannte, monotone Abbildung auf mehrere Parameter.

    ``maps`` darf in zwei Formen stehen:

    * als Zuordnung ``{param: {from, to}}`` — die ausdrucksstarke Form, die
      Richtung und Teilbereich festlegt;
    * als blosse Liste ``[param, ...]`` — Kurzform fuer "ueber den ganzen
      deklarierten Parameterbereich, aufsteigend".

    Die Kurzform wird beim Laden in die lange ueberfuehrt, sobald der
    Parameterbereich bekannt ist (siehe :meth:`ModuleManifest.resolved_macro`).
    """

    model_config = {"frozen": True, "extra": "forbid"}

    maps: dict[str, MacroTarget] | list[str] = Field(min_length=1)
    curve: Curve = Curve.LIN
    default: float = Field(default=0.5, ge=0.0, le=1.0)
    summary: str | None = None

    @property
    def targets(self) -> list[str]:
        """Die Namen der bewegten Parameter, unabhaengig von der Schreibform."""
        return list(self.maps) if isinstance(self.maps, dict) else list(self.maps)

    def shaped(self, position: float) -> float:
        """Wendet die Kennlinie auf eine Makrostellung an."""
        p = max(0.0, min(1.0, position))
        if self.curve is Curve.EXP:
            return p * p
        if self.curve is Curve.LOG:
            return float(p**0.5)
        if self.curve is Curve.STEP:
            return p
        return p


class Guarantees(BaseModel):
    """Zusagen, die das Modul allen hoeheren Ebenen gibt."""

    model_config = {"frozen": True, "extra": "forbid"}

    band_hz: tuple[float, float] = (20.0, 20_000.0)
    peak_ceiling_dbfs: float = -6.0
    dc_free: bool = True
    latency_samples: int = Field(default=0, ge=0)
    deterministic: bool = True

    @model_validator(mode="after")
    def _band_ordered(self) -> Self:
        low, high = self.band_hz
        if low <= 0 or high <= low:
            raise ValueError(f"band_hz muss aufsteigend und positiv sein, war {self.band_hz}")
        return self


class Cost(BaseModel):
    """Ressourcenverbrauch, relativ zu einem kalibrierten Referenzmodul."""

    model_config = {"frozen": True, "extra": "forbid"}

    cpu_units: float = Field(default=1.0, gt=0.0)
    voices_max: int = Field(default=1, ge=1)


class LicenseInfo(BaseModel):
    """Lizenzrelevante Eigenschaften. ``au audit`` aggregiert diese."""

    model_config = {"frozen": True, "extra": "forbid"}

    backend: str = "supercollider"
    nc_weights: bool = False
    """Wahr, wenn das Modul Modellgewichte unter nicht-kommerzieller Lizenz
    verwendet (etwa AudioCraft, CC-BY-NC-4.0). Faerbt das ganze Werk."""
    note: str | None = None


class Compatibility(BaseModel):
    model_config = {"frozen": True, "extra": "forbid"}

    requires_backend: list[str] = Field(default_factory=list)
    conflicts_with: list[str] = Field(default_factory=list)
    recommended_partners: list[str] = Field(default_factory=list)


class ModuleManifest(BaseModel):
    """Die vollstaendige Beschreibung eines Funktionsmoduls."""

    model_config = {"frozen": True, "extra": "forbid"}

    id: str
    version: str = "1.0.0"
    level: int = Field(ge=1, le=10)
    category: Category
    family: str | None = None
    display_name: str
    summary: str = ""

    ports: PortSet = Field(default_factory=PortSet)
    macros: dict[str, MacroSpec] = Field(default_factory=dict)
    params: dict[str, ParamSpec] = Field(default_factory=dict)

    guarantees: Guarantees = Field(default_factory=Guarantees)
    cost: Cost = Field(default_factory=Cost)

    tags: list[str] = Field(default_factory=list)
    semantic_vectors: dict[str, float] = Field(default_factory=dict)

    license: LicenseInfo = Field(default_factory=LicenseInfo)
    compatibility: Compatibility = Field(default_factory=Compatibility)

    # -- Validierung ---------------------------------------------------------

    @model_validator(mode="after")
    def _id_matches_category(self) -> Self:
        expected = PREFIX_BY_CATEGORY[self.category]
        if not self.id.startswith(f"{expected}."):
            raise ValueError(
                f"Modul-ID {self.id!r} passt nicht zur Kategorie {self.category}: "
                f"erwartetes Praefix {expected!r}"
            )
        if self.id.count(".") < 2:
            raise ValueError(
                f"Modul-ID {self.id!r} braucht mindestens drei Ebenen, etwa {expected}.familie.name"
            )
        return self

    @model_validator(mode="after")
    def _macros_reference_existing_params(self) -> Self:
        for macro_name, macro in self.macros.items():
            unknown = [p for p in macro.targets if p not in self.params]
            if unknown:
                raise ValueError(
                    f"Makro {macro_name!r} verweist auf unbekannte Parameter: {unknown}. "
                    f"Bekannt sind: {sorted(self.params)}"
                )
        return self

    @model_validator(mode="after")
    def _macro_targets_stay_in_range(self) -> Self:
        """Ein Makro darf nie aus dem sicheren Parameterbereich hinausfuehren."""
        for macro_name, macro in self.macros.items():
            if not isinstance(macro.maps, dict):
                continue
            for param_name, target in macro.maps.items():
                spec = self.params[param_name]
                if spec.is_enum:
                    continue
                assert spec.min is not None and spec.max is not None
                for label, value in (("from", target.start), ("to", target.end)):
                    if not (spec.min <= value <= spec.max):
                        raise ValueError(
                            f"Makro {macro_name!r} fuehrt {param_name} auf {label}={value}, "
                            f"ausserhalb des sicheren Bereichs [{spec.min}, {spec.max}]."
                        )
        return self

    @model_validator(mode="after")
    def _voices_declare_the_canonical_macros(self) -> Self:
        """L2-Stimmen muessen das Makroversprechen einloesen (plan.md 4.2)."""
        if self.level >= 2 and self.category is Category.GENERATOR:
            missing = REQUIRED_VOICE_MACROS - set(self.macros)
            if missing:
                raise ValueError(
                    f"Stimme {self.id!r} (Level {self.level}) fehlen Pflichtmakros: "
                    f"{sorted(missing)}. Jede Stimme muss ueber "
                    f"{sorted(REQUIRED_VOICE_MACROS)} ansteuerbar sein."
                )
        return self

    @model_validator(mode="after")
    def _has_at_least_one_output(self) -> Self:
        if not self.ports.outputs:
            raise ValueError(f"Modul {self.id!r} hat keinen Ausgang")
        return self

    # -- Bequemlichkeit ------------------------------------------------------

    @property
    def prefix(self) -> str:
        """Das ID-Praefix, etwa ``gen``."""
        return self.id.split(".", 1)[0]

    def matches(self, pattern: str) -> bool:
        """Prueft die ID gegen ein Muster wie ``gen.drone.*`` oder ``gen.*``."""
        if pattern.endswith("*"):
            return self.id.startswith(pattern[:-1])
        return self.id == pattern

    def default_params(self) -> dict[str, float | str]:
        return {
            name: spec.default for name, spec in self.params.items() if spec.default is not None
        }

    def default_macros(self) -> dict[str, float]:
        return {name: spec.default for name, spec in self.macros.items()}

    def resolved_macro(self, macro_name: str) -> dict[str, MacroTarget]:
        """Die Makroabbildung in ausgeschriebener Form.

        Die Kurzform ``maps: [param]`` wird hier auf den vollen deklarierten
        Parameterbereich ausgedehnt. Enum-Parameter laufen ueber ihre Indizes.
        """
        macro = self.macros[macro_name]
        if isinstance(macro.maps, dict):
            return dict(macro.maps)
        expanded: dict[str, MacroTarget] = {}
        for param_name in macro.maps:
            spec = self.params[param_name]
            if spec.is_enum:
                expanded[param_name] = MacroTarget.model_validate(
                    {"from": 0.0, "to": float(len(spec.enum or []) - 1)}
                )
            else:
                assert spec.min is not None and spec.max is not None
                expanded[param_name] = MacroTarget.model_validate(
                    {"from": spec.min, "to": spec.max}
                )
        return expanded

    def macro_value(self, macro_name: str, position: float, param_name: str) -> float:
        """Der Wert, den ``param_name`` bei dieser Makrostellung annimmt."""
        macro = self.macros[macro_name]
        return self.resolved_macro(macro_name)[param_name].at(macro.shaped(position))

    # -- Laden ---------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: Path) -> ModuleManifest:
        """Laedt und validiert ein Manifest; nennt bei Fehlern den Dateipfad."""
        try:
            raw: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise ValueError(f"{path}: YAML nicht lesbar: {exc}") from exc
        if not isinstance(raw, dict):
            raise ValueError(f"{path}: Manifest muss eine Zuordnung auf oberster Ebene sein")
        try:
            return cls.model_validate(raw)
        except Exception as exc:
            raise ValueError(f"{path}: {exc}") from exc
