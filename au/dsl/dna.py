"""L10 — Album-DNA (plan.md Paragraph 8.1 und 4.10).

Die DNA ist die einzige Quelle von Absicht im gesamten System: Charakter,
Innovationsebene, Negativregeln, Vokabularpolitik, Budgets und Zielmetriken.
Keine untere Ebene darf eine Absicht erfinden, die sich nicht aus der DNA
ableiten laesst.
"""

from __future__ import annotations

from typing import Self

from pydantic import BaseModel, Field, model_validator

from au.core.registry import VocabularyPolicy


class Character(BaseModel):
    """Charakterprofil (plan.md 8.1)."""

    model_config = {"frozen": True}

    descriptors: tuple[str, ...] = Field(min_length=1)
    emotional_temperature: tuple[float, float] = (0.3, 0.5)
    """(Start, Ende) auf [0, 1] — kalt bis warm."""
    spectral_brightness: tuple[float, float] = (0.35, 0.45)
    harmonic_tension_mean: float = 0.35
    spatial_width: float = 0.6
    spatial_depth: float = 0.6
    event_density_mean: float = 0.15
    tonal_ambiguity: float = 0.4
    silence_probability: float = 0.2
    repetition_memory: float = 0.4
    surprise_budget: float = 0.3


class InnovationVector(BaseModel):
    """Die fuenf Innovationsachsen (plan.md Paragraph 11)."""

    model_config = {"frozen": True}

    timbral: float = Field(default=0.4, ge=0.0, le=1.0)
    formal: float = Field(default=0.4, ge=0.0, le=1.0)
    harmonic: float = Field(default=0.4, ge=0.0, le=1.0)
    procedural: float = Field(default=0.4, ge=0.0, le=1.0)
    production: float = Field(default=0.4, ge=0.0, le=1.0)

    def mean(self) -> float:
        return (
            self.timbral + self.formal + self.harmonic + self.procedural + self.production
        ) / 5.0


class Comparator(BaseModel):
    """Ein struktureller Vergleich — bewusst kein String-Ausdruck.

    plan.md verlangt "maschinell auswertbare Praedikate, nicht Prosa". Ein
    freier Ausdruck (etwa ``"centroid_hz < 4000"``) waere entweder unsicher
    (``eval``) oder braucht einen eigenen Parser fuer wenig Gewinn. Eine
    Struktur aus Metrikname, Operator und Schwelle ist ebenso pruefbar,
    ohne beides.
    """

    model_config = {"frozen": True}

    metric: str
    operator: str = Field(pattern=r"^(<|<=|>|>=|==)$")
    threshold: float

    def check(self, value: float) -> bool:
        ops = {
            "<": value < self.threshold,
            "<=": value <= self.threshold,
            ">": value > self.threshold,
            ">=": value >= self.threshold,
            "==": value == self.threshold,
        }
        return ops[self.operator]


class NegativeRule(BaseModel):
    """Eine maschinell auswertbare Regel (plan.md: nie Prosa, immer Praedikat)."""

    model_config = {"frozen": True}

    id: str
    predicate: Comparator
    """Bekannte Metriknamen: siehe :data:`au.dsl.rules.KNOWN_METRICS`."""
    summary: str = ""


class GlobalBudgets(BaseModel):
    model_config = {"frozen": True}

    lufs_target_i: float = -16.0
    true_peak_max_dbtp: float = -1.0
    lra_corridor: tuple[float, float] = (8.0, 16.0)
    cpu_units_per_track: float = 180.0
    render_budget_minutes: float = 90.0


class TargetMetrics(BaseModel):
    model_config = {"frozen": True}

    track_count: tuple[int, int] = (6, 8)
    total_duration_s: tuple[float, float] = (2700.0, 3300.0)
    track_similarity_corridor: tuple[float, float] = (0.25, 0.62)
    identity_anchor_coverage: float = 0.6


class AlbumDNA(BaseModel):
    """Die verbindliche Verfassung eines Werks."""

    model_config = {"frozen": True}

    schema_version: str = "1.0"
    title: str
    seed_root: int
    character: Character
    innovation_vector: InnovationVector = Field(default_factory=InnovationVector)
    negative_rules: tuple[NegativeRule, ...] = ()
    vocabulary_policy: VocabularyPolicy = Field(default_factory=VocabularyPolicy)
    global_budgets: GlobalBudgets = Field(default_factory=GlobalBudgets)
    target_metrics: TargetMetrics = Field(default_factory=TargetMetrics)
    identity_anchors_intent: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _needs_minimum_negative_rules(self) -> Self:
        if len(self.negative_rules) < 1:
            raise ValueError(
                "Eine DNA ohne Negativregeln kann nicht geprueft werden "
                "(plan.md fordert mindestens 3 fuer ein vollstaendiges Werk; "
                "mindestens 1 fuer die Modellvalidierung)."
            )
        return self
