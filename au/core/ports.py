"""Porttypsystem und Verbindungsregeln (plan.md Paragraph 5.2).

Das Typsystem ist die erste Verteidigungslinie gegen unsinnige Verschaltungen.
Es haelt einen Fehler auf, bevor er Klang wird.

Die wichtigste Regel ist die Sperre ``analysis -> param``: ein Merkmalsstrom
darf nie unmittelbar einen Parameter steuern. Der Zwang, ein ``mod.map.*``
dazwischenzusetzen, erzwingt eine deklarierte, begrenzte und geglaettete
Abbildung — und verhindert damit die klassische Rueckkopplungsexplosion.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class PortType(StrEnum):
    """Die acht Signalarten, die zwischen Modulen fliessen koennen."""

    AUDIO = "audio"
    """Audiosignal, a-rate."""

    CTRL = "ctrl"
    """Steuersignal, k-rate."""

    EVENT = "event"
    """Notenereignis (Stufe, Dauer, Velocity, Artikulation), ereignisdiskret."""

    FIELD = "field"
    """Harmonischer Kontext (Grundton, Modus, Stimmung, Pedaltoene)."""

    SPECTRAL = "spectral"
    """FFT-Rahmen. Nur innerhalb einer zusammenhaengenden FFT-Kette."""

    ANALYSIS = "analysis"
    """Merkmalsstrom (Lautheit, Centroid, Dichte), k-rate."""

    TIME = "time"
    """Takt, Phase, Clock."""

    BUS = "bus"
    """Send-/Return-Referenz."""


#: Erlaubte Ziel-Typen je Quell-Typ.
_ALLOWED: dict[PortType, frozenset[PortType]] = {
    PortType.AUDIO: frozenset({PortType.AUDIO}),
    PortType.CTRL: frozenset({PortType.CTRL}),
    PortType.EVENT: frozenset({PortType.EVENT}),
    PortType.FIELD: frozenset({PortType.FIELD}),
    PortType.SPECTRAL: frozenset({PortType.SPECTRAL}),
    # analysis -> ctrl ist zulaessig, aber ausschliesslich ueber mod.map.*
    PortType.ANALYSIS: frozenset({PortType.ANALYSIS, PortType.CTRL}),
    PortType.TIME: frozenset({PortType.TIME}),
    PortType.BUS: frozenset({PortType.BUS}),
}

#: Modulpraefix, das eine Analyse-nach-Steuerung-Abbildung vornehmen darf.
MAPPER_PREFIX = "mod.map."


class ConnectionRule(StrEnum):
    """Ergebnis einer Typpruefung zwischen zwei Ports."""

    OK = "ok"
    """Direkt zulaessig."""

    NEEDS_MAPPER = "needs_mapper"
    """Zulaessig, aber nur wenn das Zielmodul ein ``mod.map.*`` ist."""

    FORBIDDEN = "forbidden"
    """Typkombination ist ausgeschlossen."""


def connection_rule(src: PortType, dst: PortType) -> ConnectionRule:
    """Prueft eine Typkombination, ohne den Graphkontext zu kennen.

    >>> connection_rule(PortType.AUDIO, PortType.AUDIO)
    <ConnectionRule.OK: 'ok'>
    >>> connection_rule(PortType.ANALYSIS, PortType.CTRL)
    <ConnectionRule.NEEDS_MAPPER: 'needs_mapper'>
    >>> connection_rule(PortType.AUDIO, PortType.EVENT)
    <ConnectionRule.FORBIDDEN: 'forbidden'>
    """
    if dst not in _ALLOWED[src]:
        return ConnectionRule.FORBIDDEN
    if src is PortType.ANALYSIS and dst is PortType.CTRL:
        return ConnectionRule.NEEDS_MAPPER
    return ConnectionRule.OK


def explain_forbidden(src: PortType, dst: PortType) -> str:
    """Erklaert in einem Satz, warum eine Verbindung nicht zulaessig ist."""
    if src is PortType.ANALYSIS and dst is not PortType.CTRL:
        return (
            f"Ein Merkmalsstrom ({src}) kann nur nach {PortType.ANALYSIS} oder — "
            f"ueber ein {MAPPER_PREFIX}*-Modul — nach {PortType.CTRL} fliessen."
        )
    if src is PortType.SPECTRAL or dst is PortType.SPECTRAL:
        return (
            "FFT-Rahmen duerfen die Spektralkette nicht verlassen. "
            "Fuer den Ruecktritt in die Zeitdomaene ein Resynthese-Modul einsetzen."
        )
    allowed = ", ".join(sorted(_ALLOWED[src])) or "nichts"
    return f"{src} kann nur nach {allowed} verbunden werden, nicht nach {dst}."


class Port(BaseModel):
    """Ein benannter Ein- oder Ausgang eines Moduls."""

    model_config = {"frozen": True, "extra": "forbid"}

    name: str
    type: PortType
    channels: int = Field(default=1, ge=1, le=64)
    required: bool = False
    """Nur fuer Eingaenge bedeutsam: der Graph ist ungueltig, solange dieser
    Port unverbunden ist."""
    unit: str | None = None
    """Freitext zur Dokumentation, etwa ``midinote``, ``hz``, ``db``."""
    summary: str | None = None


class PortSet(BaseModel):
    """Die Ein- und Ausgaenge eines Moduls."""

    model_config = {"frozen": True, "extra": "forbid", "populate_by_name": True}

    # Im Manifest heissen die Felder kurz "in" und "out"; im Code sind das
    # reservierte bzw. missverstaendliche Namen.
    inputs: list[Port] = Field(default_factory=list, alias="in")
    outputs: list[Port] = Field(default_factory=list, alias="out")

    @model_validator(mode="after")
    def _names_unique(self) -> PortSet:
        for label, ports in (("Eingaenge", self.inputs), ("Ausgaenge", self.outputs)):
            names = [p.name for p in ports]
            duplicates = {n for n in names if names.count(n) > 1}
            if duplicates:
                raise ValueError(f"Doppelte Portnamen bei {label}: {sorted(duplicates)}")
        return self

    def input(self, name: str) -> Port | None:
        return next((p for p in self.inputs if p.name == name), None)

    def output(self, name: str) -> Port | None:
        return next((p for p in self.outputs if p.name == name), None)

    @property
    def required_inputs(self) -> list[Port]:
        return [p for p in self.inputs if p.required]
