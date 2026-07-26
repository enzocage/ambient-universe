# Ambient Universe (AU)

KI-gestützte Ambient-Kompositionsmaschine aus flexibel verschaltbaren Funktionsmodulen,
orchestriert von einem **Master-Integrator über 10 hierarchische Organisationslevel** —
von der Klangerzeugung auf Sampleebene bis zum fertigen, gemasterten Album.

> Architektur, Organisationsdefinitionen und Stufenplan: **[plan.md](plan.md)**

## Der Kompositionsworkflow

1. **Prompt** — eine KI definiert ganzheitlich Charakter und Innovationsebene des Albums (`au dna`)
2. **Blueprint** — der Master-Integrator leitet daraus die Verschaltungshierarchie ab (`au blueprint`)
3. **Vorschlag** — die Maschine schlägt fertige Klangelemente zum Vorhören vor (`au propose`)
4. **Modulation** — per natürlicher Sprache verändern und erneut hören (`au modulate`)
5. **Ablage** — zufriedenstellende Elemente einfrieren (`au freeze` → `elements/`)
6. **Orchestrierung** — sequenziell und parallel rekombinieren, mit expliziten Bezügen
   zwischen den Elementen (`au arrange` → `au render` → `au album`)

## Schnellstart

```bash
uv venv --python 3.12
uv pip install -e ".[dev,audio]"
au doctor
```

`au doctor` prüft Python, Pakete, `scsynth`, `ffmpeg` und die Arbeitsverzeichnisse und nennt
für jeden Befund die konkrete Abhilfe.

Weitere Befehle, die heute schon laufen:

```bash
au probe --kind stack --duration 60 --repeat 3   # NRT-Render, Leistung, Determinismus
au modules --level 2                             # Modulkatalog
au modules --show gen.object.modal_bell          # Modul im Detail
```

### Voraussetzungen

| Werkzeug | Zweck | Installation (Windows) |
|----------|-------|------------------------|
| Python ≥ 3.12 | Kern | — |
| SuperCollider ≥ 3.13 | Audio-Backend (NRT-Rendering) | `winget install --id SuperCollider.SuperCollider` |
| ffmpeg | Export (ab Phase 10) | `winget install --id Gyan.FFmpeg` |

SuperCollider steht unter GPL-3.0 und läuft bewusst als **eigener Prozess** — der Python-Kern
spricht ausschließlich über NRT-Score-Dateien und OSC mit ihm.

## Projektstruktur

```
au/            Python-Kern (core, dsl, modules, integrator, arrange, render, analysis, library)
knowledge/     Ausführbare Ambient-Wissensbasis (DSP-, Kompositions-, Produktionsregeln)
elements/      Die Elementbibliothek — eingefrorene, wiederverwendbare Klangelemente
projects/      Alben (dna, blueprint, arrangement, renders, master)
synthdefs/     SynthDef-Cache
tests/         Tests inkl. Grammatik-, Determinismus- und Klangregressionstests
```

## Stand der Umsetzung

| Phase | Inhalt | Status |
|-------|--------|--------|
| 0 | Fundament, Konfiguration, `au doctor`, NRT-Render | **fertig** |
| 1 | Modulkontrakt, Porttypen, PatchGraph, Registry, 15 Manifeste | **fertig** |
| 2 | L1–L3: SynthDef-Compiler, Klangatom, Stimme, Geste | als Nächstes |
| 3 | L4: Klangelement, Vorhör-Renderer | offen |
| 4–5 | Album-DNA-Agent, Blueprint-Generator | offen |
| 6–7 | Element-Studio, KI-Modulation, Bibliothek | offen |
| 8 | L5/L6: Relationen, Kohärenz-Solver | offen |
| 9–10 | Sektionen, Track, Album, Mastering | offen |
| 11–13 | Kritik/Reparatur, DAW-Brücke, Härtung | offen |

## Lizenz

Proprietär. Abhängigkeiten und deren Auflagen: siehe [plan.md § 18](plan.md#18-lizenzmatrix).
