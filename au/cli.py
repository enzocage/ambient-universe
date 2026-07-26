"""Kommandozeile der Ambient-Universe-Maschine.

Der Befehlsbaum folgt dem Kompositionsworkflow aus plan.md Paragraph 9:

    au doctor                 Toolchain pruefen
    au dna new                Charakter + Innovationsebene prompten      (Phase 4)
    au blueprint              Verschaltungshierarchie ableiten           (Phase 5)
    au propose                Elementkandidaten vorschlagen + vorhoeren  (Phase 6)
    au modulate               Kandidat per Sprache modifizieren          (Phase 6)
    au freeze                 Element in die Bibliothek einfrieren       (Phase 6)
    au lib                    Bibliothek durchsuchen                     (Phase 7)
    au arrange                Layer + Relationen + Kohaerenz-Solver      (Phase 8)
    au sections / au render   Sektionen und Trackrendering               (Phase 9)
    au album / au verify      Album, Mastering, Reproduktionstest        (Phase 10)

Noch nicht implementierte Befehle melden das ausdruecklich mit Phasenverweis.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table
from rich.text import Text

from au import __version__
from au.core import doctor as doctor_mod
from au.core.config import get_config

app = typer.Typer(
    name="au",
    help="Ambient Universe — KI-gestuetzte Ambient-Kompositionsmaschine.",
    no_args_is_help=True,
    add_completion=False,
)
console = Console()

_STATUS_STYLE = {
    doctor_mod.Status.OK: ("[green]OK  [/green]", "green"),
    doctor_mod.Status.WARN: ("[yellow]WARN[/yellow]", "yellow"),
    doctor_mod.Status.FAIL: ("[red]FAIL[/red]", "red"),
}


@app.command()
def version() -> None:
    """Zeigt die Version."""
    console.print(f"Ambient Universe {__version__}")


@app.command()
def doctor(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Auch Pfade und Konfiguration."),
) -> None:
    """Prueft die Toolchain (Python, Pakete, scsynth, ffmpeg, Verzeichnisse)."""
    cfg = get_config()
    checks = doctor_mod.run_all(cfg)

    table = Table(title=f"au doctor  —  Projektwurzel: {cfg.root}", show_lines=False)
    table.add_column("Status", width=6, no_wrap=True)
    table.add_column("Pruefung", style="bold", no_wrap=True)
    table.add_column("Befund", overflow="fold")

    for chk in checks:
        marker, _ = _STATUS_STYLE[chk.status]
        table.add_row(marker, chk.name, chk.detail)
    console.print(table)

    remedies = [c for c in checks if c.remedy]
    if remedies:
        console.print()
        console.print(Text("Naechste Schritte:", style="bold"))
        for c in remedies:
            _, style = _STATUS_STYLE[c.status]
            # escape(): Abhilfetexte enthalten eckige Klammern (uv-Extras wie ".[audio]"),
            # die Rich sonst als Markup-Tag frisst.
            console.print(f"  [{style}]•[/{style}] {c.name}: {escape(c.remedy)}")

    if verbose:
        console.print()
        console.print(cfg.model_dump_json(indent=2))

    failures = [c for c in checks if c.blocking]
    console.print()
    if failures:
        console.print(f"[red]{len(failures)} blockierende(r) Befund(e).[/red]")
        raise typer.Exit(code=1)
    warnings = [c for c in checks if c.status is doctor_mod.Status.WARN]
    if warnings:
        console.print(f"[yellow]Bereit — mit {len(warnings)} Hinweis(en).[/yellow]")
    else:
        console.print("[green]Toolchain vollstaendig.[/green]")


@app.command()
def probe(
    kind: str = typer.Option("sine", "--kind", "-k", help="Referenzscore: sine oder stack."),
    duration: float = typer.Option(10.0, "--duration", "-d", help="Dauer in Sekunden."),
    repeat: int = typer.Option(1, "--repeat", "-r", help="Laeufe fuer den Determinismustest."),
    output: Path | None = typer.Option(None, "--output", "-o", help="Zieldatei."),
) -> None:
    """Rendert einen Referenzscore und misst Leistung und Determinismus."""
    from au.render.backend import BackendError
    from au.render.probe import render_probe

    cfg = get_config()
    target = output or (cfg.cache_dir / f"probe_{kind}.wav")

    results = []
    try:
        for i in range(max(1, repeat)):
            dest = target if repeat == 1 else target.with_stem(f"{target.stem}_{i}")
            results.append(render_probe(dest, duration=duration, kind=kind, cfg=cfg))
    except BackendError as exc:
        console.print(f"[red]{escape(str(exc))}[/red]")
        raise typer.Exit(code=1) from exc
    except ValueError as exc:
        console.print(f"[red]{escape(str(exc))}[/red]")
        raise typer.Exit(code=2) from exc

    for r in results:
        console.print(f"  {escape(r.summary())}")

    slowest = max(r.wallclock_s for r in results)
    factor = min(r.realtime_factor for r in results)
    console.print()
    console.print(f"Langsamster Lauf: {slowest:.2f}s  ({factor:.1f}x Echtzeit)")

    if repeat > 1:
        fingerprints = {r.audio_sha256 for r in results}
        if len(fingerprints) == 1:
            console.print(
                f"[green]Determinismus: {repeat} Laeufe, ein Audio-Fingerabdruck "
                f"({next(iter(fingerprints))[:16]}).[/green]"
            )
        else:
            console.print(
                f"[red]Determinismus verletzt: {len(fingerprints)} verschiedene "
                f"Fingerabdruecke in {repeat} Laeufen.[/red]"
            )
            raise typer.Exit(code=1)


@app.command()
def modules(
    level: int | None = typer.Option(None, "--level", "-l", help="Nur diese Organisationsebene."),
    category: str | None = typer.Option(None, "--category", "-c", help="Nur diese Kategorie."),
    tag: list[str] | None = typer.Option(None, "--tag", "-t", help="Muss alle Tags tragen."),
    show: str | None = typer.Option(None, "--show", "-s", help="Ein Modul im Detail."),
) -> None:
    """Listet den Modulkatalog oder zeigt ein Modul im Detail."""
    from au.core.manifest import Category
    from au.core.registry import ModuleNotFoundError, load_registry

    registry = load_registry(get_config())
    for err in registry.load_errors:
        console.print(f"[yellow]Manifest uebersprungen:[/yellow] {escape(err[:200])}")

    if show:
        try:
            m = registry.get(show)
        except ModuleNotFoundError as exc:
            console.print(f"[red]{escape(str(exc))}[/red]")
            raise typer.Exit(code=1) from exc
        console.print(f"[bold]{escape(m.id)}[/bold]  v{m.version}  L{m.level}  {m.category}")
        console.print(f"  {escape(m.display_name)} — {escape(m.summary.strip())}")
        console.print(
            f"  Band {m.guarantees.band_hz[0]:.0f}-{m.guarantees.band_hz[1]:.0f} Hz · "
            f"Spitze {m.guarantees.peak_ceiling_dbfs} dBFS · CPU {m.cost.cpu_units}"
        )
        if m.ports.inputs:
            console.print("  Eingaenge:")
            for p in m.ports.inputs:
                flag = " (Pflicht)" if p.required else ""
                console.print(f"    {p.name}: {p.type}{flag}")
        console.print("  Ausgaenge:")
        for p in m.ports.outputs:
            console.print(f"    {p.name}: {p.type}")
        if m.macros:
            console.print("  Makros:")
            for name, spec in sorted(m.macros.items()):
                console.print(f"    {name} -> {', '.join(spec.maps)}  (Vorgabe {spec.default})")
        if m.tags:
            console.print(f"  Tags: {', '.join(m.tags)}")
        return

    try:
        cat = Category(category) if category else None
    except ValueError as exc:
        console.print(
            f"[red]Unbekannte Kategorie {category!r}. "
            f"Moeglich: {', '.join(c.value for c in Category)}[/red]"
        )
        raise typer.Exit(code=2) from exc

    found = registry.query(level=level, category=cat, tags_all=tag or None)
    table = Table(title=f"Modulkatalog — {len(found)} von {len(registry)}")
    table.add_column("L", width=2, justify="right")
    table.add_column("ID", style="bold")
    table.add_column("CPU", width=4, justify="right")
    table.add_column("Name")
    table.add_column("Tags", overflow="fold")
    for m in found:
        table.add_row(
            str(m.level), m.id, f"{m.cost.cpu_units:.1f}", m.display_name, ", ".join(m.tags)
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Platzhalter fuer spaetere Phasen — melden ehrlich ihren Status.
# ---------------------------------------------------------------------------

_PLANNED: dict[str, tuple[str, str]] = {
    "dna": ("Phase 4", "Prompt -> album_dna.json (Charakter + Innovationsebene)"),
    "blueprint": ("Phase 5", "DNA -> 10-Level-Verschaltungshierarchie"),
    "propose": ("Phase 6", "Elementkandidaten erzeugen und vorhoeren"),
    "modulate": ("Phase 6", "Kandidat per natuerlicher Sprache modifizieren"),
    "freeze": ("Phase 6", "Element unveraenderlich in die Bibliothek legen"),
    "lib": ("Phase 7", "Elementbibliothek durchsuchen"),
    "arrange": ("Phase 8", "Layer platzieren, Relationen setzen, Solver laufen lassen"),
    "sections": ("Phase 9", "Sektionen und Uebergaenge bilden"),
    "render": ("Phase 9", "Track mit Stems rendern"),
    "album": ("Phase 10", "Album sequenzieren, mastern, exportieren"),
    "verify": ("Phase 10", "Reproduktionstest gegen manifest.json"),
    "audit": ("Phase 13", "Lizenzbericht aus den Modul-Manifesten"),
}


def _register_planned() -> None:
    for name, (phase, desc) in _PLANNED.items():

        def _make(n: str = name, p: str = phase, d: str = desc):  # type: ignore[no-untyped-def]
            def _cmd() -> None:
                console.print(f"[yellow]`au {n}` ist noch nicht implementiert.[/yellow]")
                console.print(f"  Geplant in {p}: {d}")
                console.print("  Siehe plan.md, Abschnitt 15 (Stufenplan).")
                raise typer.Exit(code=2)

            _cmd.__doc__ = f"[{p}] {d}"
            return _cmd

        app.command(name=name)(_make())


_register_planned()


if __name__ == "__main__":  # pragma: no cover
    app()
