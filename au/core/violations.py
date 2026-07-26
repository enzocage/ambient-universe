"""Verstossobjekte und Eskalationen.

Grundsatz aus plan.md: Eine Ablehnung ist nie nur ein "nein". Sie benennt die
verletzte Regel, den Fundort und mindestens eine Handlungsoption. Nur so kann
der Editor-Agent (Phase 6) automatisch reagieren, statt zu raten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    ERROR = "error"
    """Blockiert. Der Graph darf nicht gerendert werden."""

    WARNING = "warning"
    """Zulaessig, aber verdaechtig. Wird protokolliert."""


@dataclass(frozen=True, slots=True)
class Violation:
    """Ein einzelner Regelverstoss."""

    rule: str
    """Regelkennung, etwa ``L4-T2`` oder ``PORT-TYPE``."""

    message: str
    """Was verletzt wurde, in einem Satz."""

    where: str = ""
    """Fundort: Knoten-ID, Kantenbeschreibung oder Modul-ID."""

    options: tuple[str, ...] = ()
    """Konkrete Handlungsoptionen, aus denen ein Agent waehlen kann."""

    severity: Severity = Severity.ERROR

    def render(self) -> str:
        """Mehrzeilige, menschenlesbare Darstellung."""
        head = f"{'x' if self.severity is Severity.ERROR else '!'} [{self.rule}]"
        if self.where:
            head += f" bei {self.where}"
        lines = [head, f"  {self.message}"]
        if self.options:
            lines.append("  Optionen:")
            lines.extend(f"    ({chr(97 + i)}) {opt}" for i, opt in enumerate(self.options))
        return "\n".join(lines)


@dataclass(slots=True)
class ValidationReport:
    """Sammelergebnis einer Pruefung."""

    violations: list[Violation] = field(default_factory=list)

    def add(self, violation: Violation) -> None:
        self.violations.append(violation)

    def extend(self, others: list[Violation]) -> None:
        self.violations.extend(others)

    @property
    def errors(self) -> list[Violation]:
        return [v for v in self.violations if v.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Violation]:
        return [v for v in self.violations if v.severity is Severity.WARNING]

    @property
    def ok(self) -> bool:
        """Wahr, wenn kein blockierender Verstoss vorliegt."""
        return not self.errors

    def render(self) -> str:
        if not self.violations:
            return "Keine Beanstandungen."
        return "\n".join(v.render() for v in self.violations)

    def raise_if_failed(self, context: str = "") -> None:
        if self.ok:
            return
        prefix = f"{context}\n" if context else ""
        raise GraphValidationError(prefix + self.render(), report=self)


class GraphValidationError(ValueError):
    """Ein Graph oder Manifest hat die Pruefung nicht bestanden."""

    def __init__(self, message: str, report: ValidationReport | None = None) -> None:
        super().__init__(message)
        self.report = report or ValidationReport()
