# Übergabebericht — Ambient Universe (AU)

**Stand:** 26. Juli 2026 · Commit `214dbdd` · `main` auf
[github.com/enzocage/ambient-universe](https://github.com/enzocage/ambient-universe)
**Für:** Fortsetzung der Arbeit durch eine andere KI-Instanz oder Entwicklerin/Entwickler,
ohne Rückgriff auf den bisherigen Gesprächsverlauf.

Dieses Dokument ist der Einstiegspunkt. Für die volle Architektur siehe
[plan.md](plan.md) (Sollzustand, 10-Level-Organisationsmodell); für den
tatsächlichen Stand siehe dieses Dokument und [README.md](README.md).

---

## 1. Was funktioniert — jetzt, geprüft, hörbar

```bash
cd anmbiet_universe
uv pip install -e ".[dev,audio,analysis,symbolic,studio]"
au doctor          # muss "Toolchain vollstaendig" melden
au serve           # Web-Studio unter http://127.0.0.1:8000
# oder:
au compose "Ein kaltes, metallisches Album ueber eine verlassene Raumstation." -d 60
```

**154 Tests, alle grün** (`.venv/Scripts/python.exe -m pytest -q`, ca. 60–85 s), `ruff check`
bis auf bekannte kosmetische Altlasten sauber, `mypy au` strict ohne Befund.

Ein Prompt läuft heute vollständig durch: Album-DNA → Blueprint (Rollen-Slots) →
Vorschlags-Engine → Kohärenz-Solver → Harmonik-/Rhythmus-/Dramaturgie-Engine →
Trackrendering (Stems + Mix) → Web-Oberfläche mit echter Waveform-Anzeige.

---

## 2. Architektur-Karte (wo was liegt)

```
au/
├─ core/          Modulmanifest, Porttypen, PatchGraph+Validator, Registry, Seeds, Config
├─ dsl/           Pydantic-Modelle je Organisationsebene:
│                   dna.py (L10) · blueprint.py (L9→L4-Rollen) · element.py (L4)
│                   gesture.py (L3) · field.py/pattern.py (Symbolik)
│                   harmony.py / rhythm.py / dramaturgy.py (album-/trackweite Konsistenz)
│                   layer.py / relations.py (L5) · section.py (L7/L8)
├─ modules/       Modul-Manifeste (YAML) + Implementierungen (impl/*.py)
├─ render/        compiler.py (PatchGraph→SynthDef) · element.py · track.py · voice.py
│                   backend.py (scsynth-Aufruf, Artefaktpruefung statt Exit-Code)
├─ integrator/    blueprint.py (Generator) · proposals.py (Vorschlags-Engine) · compose.py (E2E)
├─ arrange/       solver.py (Kohaerenz-Solver, Relations-Constraints)
├─ agents/        dna_agent.py · editor_agent.py (beide regelbasiert, siehe §4)
├─ library/       store.py (Freeze) · index.py (SQLite-Suche)
├─ analysis/      metrics.py · arc.py (Bogenform-Messung)
└─ studio/        api.py (FastAPI) · jobs.py (Hintergrund-Threads) · static/index.html (UI)

knowledge/       dsp_rules.yaml — ausfuehrbare Regeln (Glaettung, Sicherheitsgrenzen)
tests/           Ein Testfile pro Feature-Bereich, siehe §6
plan.md          Der vollstaendige Soll-Architekturplan (10 Ebenen, siehe dort)
```

Jede Datei unter `au/dsl/` hat einen Docstring, der auf den plan.md-Paragraphen verweist,
den sie umsetzt, und explizit sagt, was **bewusst reduziert** ist gegenüber dem Vollplan.

---

## 3. Kernentscheidungen, die beim Weiterbauen zu respektieren sind

1. **Rezept statt Audio** (`ElementRecipe`): Ein Element speichert Parameter, nie eine
   gerenderte Datei. `recipe.transposed(n)` erzeugt eine neue, unveränderte Kopie. Das ist
   die Grundlage für Wiederverwendbarkeit — nicht aufweichen.
2. **Seed-Hierarchie** (`au/core/seeds.py`): Jeder Renderpfad bekommt seinen Seed über
   `SeedPath.child(...)`, nie über globalen Zufall. Neue Zufallsquellen müssen durch diese
   Kette laufen, sonst bricht die Reproduzierbarkeit (siehe Bug #1 unten).
3. **Modul-Manifest vor Code**: Ein neues Klangmodul braucht zuerst ein YAML-Manifest unter
   `au/modules/<kategorie>/<familie>/<name>.yaml`, dann eine Implementierung in
   `au/modules/impl/*.py` via `@implements("<id>")`. Der Compiler kennt nur das Manifest.
4. **Makros sind ein Vertrag**: Jede L2-Stimme muss `brightness, body, noise_ratio, motion,
   material` als Makros führen (erzwungen in `ModuleManifest`-Validierung). Ein Makro-Sweep
   0→1 muss klick- und clipfrei bleiben (`au/render/sweep.py`).
5. **Trackkontext lebt nicht im Rezept**: Akkordfolge (`ChordTimeline`), Zeitraster (`Clock`)
   und Dramaturgie-Bogen (`DramaturgyArc`) werden von `compose_track()` erzeugt und als
   Parameter durchgereicht (`chords=`, `clock=`, `intensity_curve=`), nicht im Rezept
   gespeichert — sonst wäre ein Element nicht mehr kontextfrei wiederverwendbar.

---

## 4. Bewusste Vereinfachungen gegenüber `plan.md` (nicht versehentlich, sondern dokumentiert)

| Bereich | Plan-Soll | Ist-Zustand | Datei |
|---|---|---|---|
| DNA-/Editor-Agent | LLM im Dialog, bis zu 4 Rückfragen | Regelbasierter Stichwort-Übersetzer, gleiche Schnittstelle | `au/agents/dna_agent.py`, `editor_agent.py` |
| Kohärenz-Solver | Volle spektrale Terzband-Maskierungskarte + Rauheitsmodell | Strukturelle Band×Zeit-Konfliktfunktion, empirisch verifiziert | `au/arrange/solver.py` |
| Bogenform-Gate | arc_fit ≥ 0.7 auf jedem Track | Metrik selbst erreicht das auf synthetischen Signalen; auf spärlichen Testfixtures ist die Schwelle nicht aussagekräftig (dokumentiert in `tests/test_track.py`) | `au/analysis/arc.py` |
| L2-Stimmenkatalog | Reichhaltige Bibliothek | **Nur 2 vollständige L2-Stimmen** (`gen.drone.wavetable_resonator`, `gen.object.modal_bell`) | `au/modules/gen/` |
| Web-UI | Volle grafische Verschaltungsansicht + Parameterregler + Live-Vorhören | **Noch nicht gebaut** — nächster Schritt, siehe §7 |
| Album-Ebene (Phase 10+) | Mehrere Tracks, Mastering-Kette, Reproduktionstest | **Nicht begonnen** — `compose_track()` erzeugt einen einzelnen Track |

---

## 5. Reale Bugs, gefunden und behoben (wichtig für die Fehlersuche später)

**Bug 1 — Determinismus bei rauschbasierten Modulen.**
`BrownNoise`/`PinkNoise`/`WhiteNoise`/`Dust` in SuperCollider ziehen aus einem
node-ID-abhängigen internen RNG-Strom, nicht aus unserer Seed-Hierarchie. Zwei
Renderläufe mit identischem Rezept erzeugten unterschiedliches Audio. **Fix:**
`RandSeed.ir(trigger=1, seed=seed.sc)` wird beim Aufbau jeder SynthDef gesetzt
(`au/render/compiler.py`, Suche nach `RandSeed`). Regressionstest:
`tests/test_sweep.py::test_noise_driven_voices_are_deterministic_across_separate_renders`.
**Wenn ein neues Modul Zufall verwendet, prüfen, ob dieser Fix greift.**

**Bug 2 — Musikalität: „nur Piepsen und Rauschen mit viel Leere".**
Jede Rolle — auch `foundation`/`harmonic_drone`, die den Track tragen sollen — wurde über
spärliches Poisson-Sampling angesteuert; die meiste Zeit war der Track still. **Fix:**
neuer `pattern_kind="sustained"` (`au/dsl/pattern.py::sustained_events`) für tragende
Rollen; Stimmenauswahl (`au/integrator/proposals.py::_voices_for_slot`) lässt keine rohen
L1-Oszillatoren mehr als „Stimme" durch. Gemessen: 91 % hörbare Abdeckung statt
überwiegender Stille. Regressionstest:
`tests/test_compose.py::test_compose_track_is_mostly_audible_not_sparse_silence`.

**Bug 3 (kleiner, UI) — Blueprint-Slot-Tabelle zeigte unbenutzte Rollen.**
`au compose`/`au serve` besetzt aus Geschwindigkeitsgründen nur `max_slots` der vom
Blueprint vorgeschlagenen Rollen; die API filterte anfangs nicht. Fix in
`au/studio/api.py::_job_summary` (`used_roles`-Filter).

---

## 6. Tests — Übersicht nach Datei

```
test_seeds.py, test_modules.py, test_graph.py     Phase 1: Kern, Registry, PatchGraph
test_sweep.py, test_gesture.py                     Phase 2: Makro-Sweep, L3-Gesten, Noise-Determinismus
test_element.py                                    Phase 3: L4-Element, Transposition, MIDI
test_dna.py                                         Phase 4: DNA-Agent, Negativregeln, Innovation
test_blueprint.py                                   Phase 5: Blueprint-Generator
test_studio.py                                      Phase 6/7: Vorschläge, Editor, Bibliothek
test_solver.py                                       Phase 8: Relations-Algebra, Kohärenz-Solver
test_track.py                                        Phase 9: Trackrendering, Bogenform
test_compose.py                                      End-to-End: compose_track(), Determinismus, Abdeckung
test_harmony_rhythm_dramaturgy.py                    Harmonik/Rhythmus/Dramaturgie
test_render_smoke.py                                 Phase 0: NRT-Backend, Determinismus-Fingerabdruck
```

Marker: `@pytest.mark.audio` (braucht scsynth), `@pytest.mark.slow`. Schneller Lauf ohne
Audio: `pytest -m "not audio"`. Voller Lauf dauert ca. 55–65 s.

---

## 7. Nächste Schritte, priorisiert

**Vom Nutzer explizit angefordert, noch nicht umgesetzt:**

1. **Web-UI: grafische Verschaltungsansicht + Parameterregler + schnelles Vorhören.**
   Vorschlag: `GET /api/jobs/{id}/graph` liefert Knoten/Kanten je Layer (Pitch-Quelle →
   Stimme, Rolle, Band, aktuelle Makrowerte) als JSON; Frontend zeichnet ein einfaches
   SVG-Diagramm (kein Drag-and-Drop nötig, siehe Zeitbudget-Hinweis unten). Für „schnelles
   Vorhören": ein neuer Endpunkt `POST /api/jobs/{id}/layers/{layer_id}/preview` mit
   `{macro_overrides, oscillations: [{macro, rate_hz, depth}]}`, der über
   `au.render.voice.build_automated_score` (bereits vorhanden, siehe `AutomationTrack`) eine
   kurze (~10–15 s) Solo-Version des Layers mit sinusförmiger Makro-Modulation rendert und
   zurückgibt. Die Bausteine (Automation, Solo-Rendering) existieren bereits; es fehlt die
   Verdrahtung zu einem Preview-Endpunkt und die UI-Regler.
2. **Mehr L2-Stimmen.** Aktuell nur 2 — jede neue Rolle im erweiterten Vokabular
   (`bass_sequence`, `arpeggiator`, `harmonic_sphere`, `melody_element`, …) verwendet
   zwangsläufig eine der beiden bestehenden Stimmen. Neue Manifeste + Implementierungen
   nach dem Muster von `gen.object.modal_bell` würden die klangliche Vielfalt am direktesten
   erhöhen.
3. **Phase 10+**: Mehrere Tracks zu einem Album sequenzieren, Mastering-Kette,
   Reproduktionstest (`au verify`), DAW-Export (Ableton-Projekt, siehe plan.md Phase 12).

**Aus eigener Beobachtung, nicht explizit gefordert, aber wirkungsvoll:**

- Das `_RHYTHMIC_ROLES`-Timing (`arpeggiator`, `bass_sequence`,
  `subtle_percussive_background`) ist verdrahtet, aber noch nicht durch einen Hörtest
  bestätigt — lohnt sich vor dem nächsten Feature-Schub kurz zu prüfen.
- Die Dramaturgie-Wirkung ist strukturell verifiziert (OSC-Bundle, siehe Bug-Sektion), aber
  noch nicht auf einem vollständigen Mehrschicht-Track per Ohr geprüft.

---

## 8. Kommandos zum schnellen Wiedereinstieg

```bash
# Umgebung
uv venv --python 3.12 && uv pip install -e ".[dev,audio,analysis,symbolic,studio]"
au doctor

# Tests
.venv/Scripts/python.exe -m pytest -q                  # alles, ~60s
.venv/Scripts/python.exe -m pytest -q -m "not audio"   # ohne scsynth, <1s
.venv/Scripts/python.exe -m ruff format . && ruff check .
.venv/Scripts/python.exe -m mypy au

# Ausprobieren
au compose "Ein helles Glasalbum mit sparsamen Glockentoenen." -d 45
au serve --port 8000        # http://127.0.0.1:8000 im Browser oeffnen

# Git
git log --oneline -12       # Commit-Historie mit ausfuehrlichen Begruendungen je Phase
```

Jeder Commit dieser Historie hat eine lange, konkrete Beschreibung (was gebaut wurde, welche
Abstriche bewusst gemacht wurden, welche Bugs gefunden wurden) — bei Unklarheiten lohnt sich
`git log -p <phase-stichwort>` mehr als eine erneute Analyse des Codes von Grund auf.
