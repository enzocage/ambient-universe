# Ambient Universe – Umsetzungsplan 2

**Ziel:** Aus der bestehenden technisch funktionierenden Audio-Pipeline eine hierarchisch
organisierte Kompositions- und Produktionsmaschine entwickeln, die komplexe, innovative,
zusammenhängende und wohlklingende Musik erzeugt.

**Stand:** 26. Juli 2026  
**Bezug:** `plan.md`, `HANDOFF.md` und der aktuelle Repository-Zustand  
**Dokumenttyp:** Verbindlicher, stufenweise abzuarbeitender Implementierungsplan

---

## 1. Ausgangslage

Die Anwendung kann aktuell:

- einen Prompt in DNA und Rollen-Slots übersetzen,
- Kandidaten auswählen,
- Layer als SuperCollider-SynthDefs rendern,
- Stems und Mix erzeugen,
- Waveforms und Metadaten im Studio anzeigen,
- Ergebnisse mit Seeds reproduzierbar machen.

Das technisch erfolgreiche Rendering ist jedoch noch kein musikalisch überzeugendes Ergebnis.
Die wichtigsten Defizite sind:

1. Zu wenige vollständige Stimmen und zu geringe klangliche Differenzierung.
2. Einzelne Layer werden überwiegend unabhängig geplant.
3. Harmonie, Rhythmus und Dramaturgie beeinflussen Ereignisse nur schwach.
4. Motive, Phrasen, Voice Leading und orchestrale Interaktion fehlen oder sind rudimentär.
5. Die Form ist teilweise nur eine Dichte- oder Makrokurve.
6. Der Solver akzeptiert Ergebnisse mit musikalisch relevanten Restkonflikten.
7. Das Mixing besteht hauptsächlich aus Summierung und Begrenzung.
8. Die Qualitätssicherung prüft technische Existenz zuverlässiger als musikalische Qualität.
9. Promptbegriffe erscheinen in Metadaten, wirken aber nicht durchgängig auf alle Ebenen.

Dieser Plan setzt daher nicht bei einzelnen Klangparametern an, sondern bei der gesamten
Hierarchie:

```text
Prompt
  → Musikalische Intention
  → Klangidentität
  → Form
  → Harmonie und Zeit
  → Motive und Phrasen
  → Orchestrierung
  → Stimmen und Gesten
  → Synthese und Raum
  → Stems und Mix
  → Qualitätskritik
  → gezielte Revision
  → finaler Render
```

---

## 2. Verbindliche Entwicklungsregeln

Diese Regeln gelten in allen Stufen:

1. **Bestehende Arbeit schützen.** Vor jeder Stufe werden `git status`, betroffene Dateien
   und vorhandene Tests geprüft. Nicht zugehörige Änderungen werden weder verworfen noch
   überschrieben.
2. **Plan vor Audio.** Einzelne Layer dürfen keine übergeordneten Form-, Harmonie- oder
   Timingentscheidungen eigenmächtig treffen.
3. **Rezept statt fixem Audio.** Wiederverwendbare Elemente bleiben parametrische Rezepte.
4. **Seed-Hierarchie erhalten.** Jede Zufallsentscheidung wird aus einem benannten
   `SeedPath` abgeleitet.
5. **Manifest und Implementierung müssen übereinstimmen.** Ein Modul gilt nur dann als
   verfügbar, wenn es real kompiliert und rendert.
6. **Keine Qualitätsattrappen.** Dateiexistenz, grüne Tests oder eine attraktive Waveform
   ersetzen keine musikalischen Akzeptanzkriterien.
7. **Keine hart codierte Demo.** Testtracks müssen aus Prompt, Plan und Seed entstehen.
8. **Jede Stufe endet mit einem Gate.** Die nächste Stufe beginnt erst, wenn das Gate
   bestanden ist oder eine dokumentierte Ausnahme vorliegt.
9. **Kurze Feedbackschleifen.** Zuerst 12–20 Sekunden Solo/Ensemble, dann 60 Sekunden Track,
   erst danach lange Produktionen.
10. **Messung und Hörurteil ergänzen sich.** Metriken blockieren technische und grobe
    musikalische Fehler; ein Hörprotokoll bewertet Gestalt, Balance und Klangqualität.

---

## 3. Definition of Done für das Gesamtvorhaben

Das Vorhaben ist abgeschlossen, wenn drei deterministisch erzeugte Referenztracks von jeweils
mindestens 60 Sekunden alle folgenden Kriterien erfüllen:

### Musikalische Kriterien

- mindestens drei hörbar unterscheidbare Formabschnitte,
- mindestens ein wiederkehrendes Hauptmotiv,
- mindestens eine erkennbare Motivvariation,
- eine gemeinsame harmonische Entwicklung aller tonalen Rollen,
- kontrolliertes Voice Leading,
- mindestens drei konkrete Relationen zwischen Layern,
- ein geplanter Dichte- und Spannungsverlauf,
- keine langen unbeabsichtigten Leerstellen,
- keine dauerhaft statische Einzelnote als vollständiger Trackträger,
- Noise und Effekte unterstützen die Musik, ersetzen sie aber nicht.

### Klangliche Kriterien

- klar unterscheidbare Foundation-, Harmonic-, Motif-, Texture- und Object-Funktionen,
- keine dominante Pfeifresonanz,
- kein übermäßiges Breitbandrauschen,
- wahrnehmbare Entwicklung innerhalb wichtiger Stimmen,
- ausgewogene Registerverteilung,
- Vorder-, Mittel- und Hintergrund sind hörbar gestaffelt,
- die drei Referenztracks sind untereinander deutlich verschieden.

### Technische Kriterien

- Integrated Loudness im konfigurierten Zielbereich, zunächst `-18 bis -14 LUFS`,
- True Peak höchstens `-1 dBTP`,
- keine NaN-, Inf-, DC- oder Clipping-Fehler,
- mono-kompatibles Fundament,
- kein wichtiger Stem ist praktisch leer,
- identische Seeds erzeugen identische Audio-Fingerprints,
- unterschiedliche Seeds erzeugen unterscheidbare, weiterhin gültige Musik,
- alle schnellen Tests, Audio-Tests, Ruff und Mypy bestehen.

---

## 4. Stufenübersicht

| Stufe | Ergebnis | Abhängigkeit |
|---|---|---|
| 0 | Reproduzierbare Baseline und Hördiagnose | keine |
| 1 | Vollständige Capability-Matrix | 0 |
| 2 | Musikalische Qualitätsmetriken und Gates | 0 |
| 3 | Gemeinsames musikalisches Datenmodell | 1, 2 |
| 4 | Wirksame Prompt- und Klangidentitätsübersetzung | 3 |
| 5 | Form-, Harmonie- und Zeitplanung | 3, 4 |
| 6 | Motiv-, Phrasen- und Voice-Leading-Engine | 5 |
| 7 | Hierarchische Orchestrierung und Relationen | 5, 6 |
| 8 | Ausbau der Stimmen und Klangarchitekturen | 1, 7 |
| 9 | Ausführung musikalisch koordinierter Layer | 6, 7, 8 |
| 10 | Raum-, Mix- und Mastering-Hierarchie | 2, 9 |
| 11 | Kritiker- und Revisionsschleife | 2, 7, 10 |
| 12 | Studio-UI und Transparenz | 3–11 |
| 13 | Referenzproduktionen und finale Abnahme | alle |

Stufen 1 und 2 dürfen parallel vorbereitet werden. Stufe 8 kann mit Prototypen beginnen,
sobald Stufe 1 abgeschlossen ist; die endgültige Rollenzuordnung wartet jedoch auf Stufe 7.

---

# STUFE 0 – Baseline sichern und das Problem messbar machen

## Ziel

Den aktuellen Zustand reproduzierbar dokumentieren, bevor Architektur oder Klang verändert
werden. Die Baseline dient später als Vorher-Nachher-Vergleich.

## Arbeitspakete

### 0.1 Repository-Zustand erfassen

- `git status --short` sichern.
- Bereits geänderte und neue Dateien klassifizieren.
- Vorhandene Arbeiten aus `scratch/` prüfen, aber nicht automatisch übernehmen.
- Aktuelle Testzahl und bekannte Fehler dokumentieren.
- Python-, SuperCollider-, Supriya- und Audio-Backend-Versionen erfassen.

### 0.2 Drei feste Diagnoseprompts definieren

1. Warm, organisch, langsam atmend.
2. Kalt, gläsern, metallisch, räumlich.
3. Rhythmisch, sequenziert, elektronisch, aber ambient.

Für jeden Prompt werden Prompttext, Seed, Dauer und Konfiguration versioniert.

### 0.3 Baseline rendern

- Je Prompt einen 60-Sekunden-Track rendern.
- Mix und alle Stems aufbewahren.
- Events, DNA, Blueprint, Solver-Log und Trackplan speichern.
- Waveform und Spektrogramm erzeugen.
- Messwerte aus Stufe 2 zunächst mit vorhandenen Mitteln erfassen.

### 0.4 Hörprotokoll anlegen

Pro Track:

- musikalische Form,
- Hauptmaterial,
- harmonische Bewegung,
- rhythmischer Zusammenhang,
- Klangfarben,
- Leerstellen,
- Pfeifen und Resonanzprobleme,
- Noise-Anteil,
- Vorder-/Hintergrundstaffelung,
- Mixbalance,
- subjektiv stärkste und schwächste Passage.

## Artefakte

- `tests/golden/prompts/*.json`
- `projects/baseline/<case>/`
- `docs/audio-baseline.md`

## Gate 0

- Drei Baseline-Tracks sind reproduzierbar vorhanden.
- Jeder Track besitzt Messwerte und Hörprotokoll.
- Der Ausgangszustand kann nach späteren Änderungen erneut gerendert werden.

---

# STUFE 1 – Capability-Matrix aller Module

## Ziel

Feststellen, welche Klangerzeuger und Prozessoren tatsächlich existieren, funktionieren und
musikalisch eingesetzt werden können.

## Arbeitspakete

### 1.1 Registry-Audit

Für jedes Manifest erfassen:

- Modul-ID und Version,
- Kategorie und Level,
- Implementierungsstatus,
- Renderbarkeit,
- Ports,
- Makros,
- Parameter,
- Frequenzbereich,
- CPU-Kosten,
- garantierte Eigenschaften,
- empfohlene Partner,
- mögliche musikalische Rollen.

### 1.2 Implementierungsabgleich

- Manifest ohne `@implements` erkennen.
- Implementierung ohne Manifest erkennen.
- Deklarierte, aber nicht gelieferte Ports erkennen.
- Makroziele ohne wirksame Parameteränderung erkennen.
- Strukturelle Parameter identifizieren, die fälschlich automatisiert werden.

### 1.3 Nutzungsanalyse

Für jedes renderbare Modul prüfen:

- Wird es von `_voices_for_slot()` jemals ausgewählt?
- Für welche Rollen?
- Wird es durch Bandfilter oder Scoring dauerhaft verdrängt?
- Kann sein notwendiger Input erzeugt werden?
- Erscheint es in einem realen Track?

### 1.4 Automatisierter Capability-Report

Ein CLI- oder Python-Report soll mindestens ausgeben:

```text
module_id
implemented
renderable
roles
audition_status
macro_effect_status
used_by_pipeline
blocking_reason
```

## Vorgesehene Dateien

- `au/core/registry.py`
- `au/modules/base.py`
- `au/analysis/capabilities.py` neu
- `au/cli.py`
- `tests/test_capabilities.py` neu

## Tests

- Jedes registrierte Modul ist eindeutig klassifiziert.
- Jedes als renderbar markierte Modul erzeugt ein valides Audition-Audio.
- Jede L2-Stimme besitzt den vollständigen Makrovertrag.
- Unbenutzbare Module werden nicht als Kandidaten angeboten.

## Gate 1

- Die Capability-Matrix ist vollständig und maschinenlesbar.
- Es existiert eine priorisierte Liste fehlender oder ungenutzter Klangmodule.
- Der Kandidatengenerator kann nur real renderbare Module auswählen.

---

# STUFE 2 – Musikalische Qualitätsmessung

## Ziel

Technisch gültige, aber musikalisch leere oder primitive Ergebnisse zuverlässig erkennen.

## Arbeitspakete

### 2.1 Technische Audiometriken

Implementieren oder vervollständigen:

- Peak,
- approximierter oder echter True Peak,
- RMS,
- Integrated und Short-Term LUFS,
- DC-Anteil,
- aktive Signalzeit,
- Stilleanteil,
- Crest Factor,
- Dynamikbereich,
- Stereo-Korrelation,
- spektraler Schwerpunkt,
- Energie pro Frequenzband,
- schmalbandige Resonanzspitzen,
- Noise-/Tonality-Schätzung.

### 2.2 Musikalische Planmetriken

Aus Plan und Events messen:

- Tonhöhenanzahl und Entropie,
- Registerspanne,
- Akkordabdeckung,
- harmonische Fremdtonquote,
- Voice-Leading-Kosten,
- Motivwiederkehr,
- Motivvariation,
- Phrasenanzahl,
- Abschnittskontrast,
- Layerabdeckung,
- Interaktionsanzahl,
- unbeabsichtigte Leerstellen,
- Dichteverlauf,
- Rollenbalance.

### 2.3 Qualitätsreport

Ein `MusicalQualityReport` bündelt:

- Rohmetriken,
- normalisierte Scores,
- Warnungen,
- blockierende Verstöße,
- Verbesserungsvorschläge,
- Gesamtentscheidung `accepted`, `revise` oder `rejected`.

### 2.4 Erstes Qualitätsgate

Konservative Schwellen definieren. Nicht versuchen, „Schönheit“ auf eine Zahl zu reduzieren.
Nur klare Fehler hart blockieren:

- wichtiger Stem leer,
- überwiegende ungeplante Stille,
- extreme Resonanz,
- nur eine Tonhöhe trotz verlangter Bewegung,
- fehlender harmonischer Träger,
- Loudness außerhalb sicherer Grenzen,
- ungelöste kritische Solver-Konflikte.

## Vorgesehene Dateien

- `au/analysis/metrics.py`
- `au/analysis/musical_quality.py` neu
- `au/dsl/quality.py` neu
- `tests/test_musical_quality.py`

## Gate 2

- Die Baseline-Probleme werden vom Report tatsächlich erkannt.
- Ein technisch sauberes Referenzsignal wird nicht fälschlich verworfen.
- Metriken sind deterministisch und in der UI serialisierbar.

---

# STUFE 3 – Gemeinsames musikalisches Datenmodell

## Ziel

Alle Ebenen erhalten explizite Verträge. Events entstehen zukünftig aus einem gemeinsamen
Trackplan und nicht aus isolierten Layerrezepten.

## Neue oder erweiterte Modelle

### 3.1 Intention und Identität

- `MusicalIntent`
- `SonicIdentity`
- `ComplexityProfile`
- `InnovationProfile`

### 3.2 Form und Zeit

- `FormPlan`
- `SectionPlan`
- `PhraseWindow`
- `DensityCurve`
- `TensionCurve`
- `GlobalClock`

### 3.3 Harmonie

- `HarmonicNarrative`
- `HarmonicEvent`
- `ChordVoicing`
- `VoiceLeadingConstraint`

### 3.4 Motivik

- `Motif`
- `MotifNote`
- `MotifTransformation`
- `Phrase`
- `VoiceLine`

### 3.5 Orchestrierung

- `OrchestrationPlan`
- `LayerAssignment`
- `RegisterAllocation`
- `AttentionBudget`
- `SpatialPlan`
- `MixIntent`

## Regeln

- Modelle sind immutable, sofern kein klarer Revisionsschritt erfolgt.
- IDs und Seeds bleiben stabil.
- JSON-Roundtrip ist verpflichtend.
- Jede tiefere Ebene referenziert ihren übergeordneten Plan.
- Bestehende DSL-Modelle werden migriert statt parallel dupliziert.

## Vorgesehene Dateien

- `au/dsl/intent.py` neu
- `au/dsl/form.py` neu
- `au/dsl/motif.py`
- `au/dsl/harmony.py`
- `au/dsl/rhythm.py`
- `au/dsl/section.py`
- `au/dsl/orchestration.py` neu
- `tests/test_musical_models.py` neu

## Gate 3

- Ein vollständiger Trackplan kann ohne Audio erzeugt, validiert und serialisiert werden.
- Jeder Layer kann auf Form, Harmonie, Phrase, Rolle und Raumplan zurückgeführt werden.
- Keine zyklischen oder mehrdeutigen Zuständigkeiten zwischen den Ebenen.

---

# STUFE 4 – Prompt zu wirksamer musikalischer Intention

## Ziel

Promptbegriffe beeinflussen nachweisbar Form, Harmonie, Orchestrierung, Synthese, Raum und Mix.

## Arbeitspakete

### 4.1 Merkmalsraum

Mindestens extrahieren:

- Wärme,
- Helligkeit,
- Härte,
- Körper,
- Dichte,
- Energie,
- Bewegung,
- organisch/synthetisch,
- tonal/geräuschhaft,
- konsonant/dissonant,
- intim/monumental,
- trocken/räumlich,
- statisch/transformativ,
- rhythmisch/schwebend,
- Komplexität,
- Innovationsgrad.

### 4.2 Übersetzungstabellen

Jedes Merkmal muss konkrete Zielgrößen beeinflussen:

| Merkmal | Form | Harmonie | Orchestrierung | Synthese | Raum/Mix |
|---|---|---|---|---|---|
| Wärme | weichere Übergänge | mehr gemeinsame Töne | mittlere Register | weniger harte Partials | kürzere, dunklere Räume |
| Bewegung | mehr Entwicklung | häufigere Wechsel | Rollenübergaben | stärkere Modulation | räumliche Automation |
| Komplexität | mehr Formebenen | reichere Voicings | mehr Relationen | komplexere Stimmen | größere Tiefenstaffelung |

Die vollständige Tabelle wird im Code und in der Dokumentation gepflegt.

### 4.3 Defaults und Unsicherheit

- Fehlende Merkmale kohärent ergänzen.
- Erkannte und ergänzte Werte getrennt markieren.
- Warnungen nur zeigen, wenn wirklich relevante Information fehlt.
- Ein Künstler- oder Stilbegriff darf keine bloße Tokenliste bleiben.

### 4.4 Wirkungstests

Paarweise Prompts mit gegensätzlichen Eigenschaften müssen messbar unterschiedliche Pläne
und Audioeigenschaften erzeugen.

## Vorgesehene Dateien

- `au/agents/dna_agent.py`
- `au/dsl/dna.py`
- `au/integrator/intent.py` neu
- `tests/test_prompt_intent.py` neu

## Gate 4

- Mindestens acht zentrale Promptmerkmale wirken auf drei oder mehr Hierarchieebenen.
- Gegensätzliche Prompts erzeugen deutlich unterschiedliche, aber valide Pläne.
- Die Warnung „Standardwerte verwendet“ erscheint nur bei tatsächlich fehlender Information.

---

# STUFE 5 – Form-, Harmonie- und Zeitplanung

## Ziel

Vor der Layererzeugung entsteht ein gemeinsamer musikalischer Zeit- und Spannungsplan.

## Arbeitspakete

### 5.1 Formgenerator

Mindestens unterstützen:

- Bogenform,
- kontinuierliche Transformation,
- Wellenform,
- schichtweise Akkumulation,
- episodische Form,
- zyklische Wiederkehr,
- Kontrastform.

Jede Form steuert:

- Abschnitte,
- Dichte,
- Spannung,
- Register,
- Rollenaktivität,
- Motivpräsenz,
- Klangfarbenhelligkeit,
- räumliche Tiefe.

### 5.2 Harmonic Narrative

- Akkord- oder Zustandsfolge planen.
- Modale Identität bewahren.
- Spannung und Auflösung modellieren.
- Pedaltöne und gemeinsame Töne einsetzen.
- Harmoniewechsel an Phrasen und Formgrenzen koppeln.
- Voicings mit Registergrenzen vorbereiten.

### 5.3 Gemeinsame Zeitstruktur

- Globaler Puls oder explizit pulsfreier Zeitfluss.
- Takte beziehungsweise Zeitgruppen.
- Phrasenlängen.
- gemeinsame Übergangspunkte.
- kontrollierte Mikroverschiebungen.
- Dichtekurve je Abschnitt.

„Pulsfrei“ bedeutet gemeinsame Zeitfenster ohne starres Raster, nicht unabhängigen Zufall.

## Vorgesehene Dateien

- `au/dsl/form.py`
- `au/dsl/harmony.py`
- `au/dsl/rhythm.py`
- `au/dsl/dramaturgy.py`
- `au/integrator/form.py` neu
- `au/integrator/harmony.py` neu
- `tests/test_form_harmony.py` neu

## Gate 5

- Ein 60-Sekunden-Plan besitzt mindestens drei unterscheidbare Abschnitte.
- Harmonieereignisse liegen auf musikalisch sinnvollen Grenzen.
- Dichte und Spannung verändern mehr als nur die Summenlautstärke.
- Gleiche Seeds reproduzieren denselben Plan.

---

# STUFE 6 – Motiv-, Phrasen- und Voice-Leading-Engine

## Ziel

Wiedererkennbarkeit, Entwicklung und tonaler Zusammenhang ersetzen unabhängige Zufallsnoten.

## Arbeitspakete

### 6.1 Motivgenerator

Pro Track:

- ein Hauptmotiv,
- optional ein Kontrastmotiv,
- definierte Kontur,
- Rhythmusprofil,
- Zielregister,
- harmonische Funktion.

### 6.2 Transformationen

Implementieren:

- Wiederholung,
- Transposition,
- Sequenz,
- rhythmische Variation,
- Augmentation,
- Diminution,
- Fragmentierung,
- Auslassung,
- Registerwechsel,
- Umkehrung,
- harmonische Reinterpretation,
- ornamentierte Wiederkehr.

### 6.3 Phrasenplanung

- Motive zu Frage, Antwort, Fortspinnung und Abschluss formen.
- Phrasenenden mit Harmonie und Objekt-Akzenten koppeln.
- Wiederholung und Variation begrenzen.
- Stille als geplante Phrasenfunktion markieren.

### 6.4 Voice Leading

- gemeinsame Töne bevorzugen,
- kleine Schritte bevorzugen,
- Sprünge funktional begründen,
- Stimmkreuzungen kontrollieren,
- Registergrenzen beachten,
- Dissonanzen vorbereiten und auflösen.

## Vorgesehene Dateien

- `au/dsl/motif.py`
- `au/dsl/phrase.py` neu
- `au/integrator/motifs.py` neu
- `au/integrator/voice_leading.py` neu
- `tests/test_motifs.py` neu
- `tests/test_voice_leading.py` neu

## Gate 6

- Das Hauptmotiv kehrt in einem 60-Sekunden-Plan mindestens zweimal wieder.
- Mindestens eine Wiederkehr ist transformiert.
- Tonale Stimmen erfüllen definierte Voice-Leading-Grenzen.
- Gleiche Seeds ergeben identische Motive und Phrasen.

---

# STUFE 7 – Hierarchische Orchestrierung und Relationen

## Ziel

Ein zentraler Orchestrator verteilt Aufgaben, Register, Aufmerksamkeit, Dichte und Raum.

## Arbeitspakete

### 7.1 Rollenmodell

Unterstützte Funktionen:

- Foundation,
- Bassbewegung,
- harmonischer Träger,
- Mittelstimme,
- motivische Hauptstimme,
- Gegenstimme,
- rhythmische Bewegung,
- Textur,
- resonante Objekte,
- Atmosphäre,
- Übergangs- und Akzentmaterial,
- Raumantworten.

### 7.2 Ressourcenbudgets

Je Abschnitt verteilen:

- Register,
- Frequenzbänder,
- Ereignisdichte,
- Lautheit,
- Aufmerksamkeit,
- Stereobreite,
- räumliche Tiefe,
- CPU.

### 7.3 Relationen operationalisieren

Mindestens:

- `supports`,
- `answers`,
- `doubles`,
- `contrasts`,
- `anticipates`,
- `follows`,
- `leaves_space_for`,
- `rhythmic_lock`,
- `harmonic_support`,
- `spectral_complement`,
- `foreground_background`,
- `shared_motif`.

Jede Relation erhält konkrete Auswirkungen auf Events, Register, Timing, Pegel oder Spektrum.

### 7.4 Konfliktklassen

- kritisch: blockiert,
- relevant: Revision erforderlich,
- gering: dokumentiert akzeptierbar.

Ein Track mit kritischen Restkonflikten darf nicht als fertig gelten.

## Vorgesehene Dateien

- `au/dsl/relations.py`
- `au/dsl/orchestration.py`
- `au/arrange/solver.py`
- `au/integrator/orchestrator.py` neu
- `tests/test_orchestration.py` neu
- `tests/test_solver.py`

## Gate 7

- Jeder aktive Layer besitzt eine eindeutige Funktion und ein Registerbudget.
- Mindestens drei Relationen sind in einem Referenzplan wirksam.
- Kritische Konflikte blockieren den Render.
- Zwei Layer reagieren nachweisbar aufeinander statt nur gleichzeitig zu spielen.

---

# STUFE 8 – Klanggeneratoren und vollständige Stimmen ausbauen

## Ziel

Jede zentrale Rolle erhält mehrere charakterlich verschiedene, musikalisch einsetzbare Stimmen.

## Priorität A: tragende Stimmen

- Sub/Fundament,
- bewegter Bass,
- harmonische Drone,
- polyphones Pad,
- weiche Mittelstimme.

## Priorität B: identitätsstiftende Stimmen

- motivische Lead-Stimme,
- Arpeggiator/Sequencer,
- modale oder gläserne Objekte,
- granulare Wolke,
- spektraler Shimmer.

## Priorität C: Raum und Übergang

- atmendes Noise-Feld,
- Impakt/Transition,
- Reverse- oder Freeze-Textur,
- Delay-basierte motivische Antwort.

## Anforderungen pro Stimme

- Manifest und Implementierung,
- eindeutige musikalische Rollen,
- mindestens zwei Klangquellen oder ein gleichwertig reiches Syntheseverfahren,
- Artikulationsmodell,
- Mikro-, Noten-, Phrasen- und Sektionsmodulation,
- wirksamer vollständiger Makrovertrag,
- kontrolliertes Register,
- Stereo- und Monoverhalten,
- Pegelkalibrierung,
- Audition-Render,
- Spektrum- und Resonanzprüfung.

## Mindestvielfalt

Mindestens diese Synthesefamilien real nutzbar machen:

- subtraktiv/wavetable,
- additiv,
- FM,
- modal/resonant,
- granular,
- Noise/Textur,
- Puls/Sequenz,
- optional spektral, sofern Backend und Aufwand vertretbar sind.

## Vermeidung

- kein Rohoszillator als fertige L2-Stimme,
- kein reines Noise ohne rollenbezogene Formung,
- keine dauerhafte schmalbandige Resonanz,
- keine identische Artikulation für alle Ereignisse,
- keine Makros ohne hörbare Wirkung.

## Vorgesehene Dateien

- `au/modules/gen/**`
- `au/modules/impl/voices.py`
- bei wachsendem Umfang Aufteilung in `voices_*.py`
- `au/render/sweep.py`
- `tests/test_sweep.py`
- `tests/test_voice_catalog.py` neu

## Gate 8

- Jede Kernrolle besitzt mindestens zwei geeignete Stimmen.
- Alle Stimmen bestehen Solo-Audition, Makro-Sweep und Resonanzprüfung.
- Stimmen unterschiedlicher Rollen sind anhand von Features unterscheidbar.
- Die Capability-Matrix zeigt keine fälschlich verfügbaren Stimmen.

---

# STUFE 9 – Koordinierte Event- und Layerausführung

## Ziel

Der Renderer setzt den gemeinsamen musikalischen Plan um, statt Events pro Layer unabhängig zu
würfeln.

## Arbeitspakete

### 9.1 Eventableitung

Events werden aus folgenden Quellen abgeleitet:

- Abschnitt,
- Phrase,
- Motivtransformation,
- Harmonieereignis,
- Rollenfunktion,
- Relation,
- Artikulationsprofil.

### 9.2 Ausdrucksdaten

Jedes Event kann enthalten:

- Pitch oder Voicing,
- Start und Dauer,
- Velocity,
- Artikulation,
- Timbrevariation,
- Akzent,
- Raumtiefe,
- Pan-Ziel,
- Phrase- und Motivreferenz.

### 9.3 Polyphonie und Lebenszyklus

- polyphone Pads und Akkorde ermöglichen,
- Stimmenzahl budgetieren,
- saubere Attack-/Release-Überlappung,
- keine unendlichen Synths,
- Tail-Länge aus Effektplan ableiten,
- Übergänge zwischen Sektionen glätten.

### 9.4 Layerinteraktion

- Texturen reduzieren sich bei Vordergrundmotiven.
- Bass bereitet Harmoniewechsel vor.
- Objekte markieren Phrasenenden.
- Pads halten gemeinsame Töne.
- Arpeggien übernehmen Motivfragmente.

## Vorgesehene Dateien

- `au/render/element.py`
- `au/render/track.py`
- `au/dsl/pattern.py`
- `au/integrator/compose.py`
- `au/integrator/events.py` neu
- `tests/test_event_realization.py` neu
- `tests/test_compose.py`

## Gate 9

- Eventlisten mehrerer Layer referenzieren denselben Form- und Harmonieplan.
- Motivische Wiederkehr ist im Eventmaterial nachweisbar.
- Tragende Layer besitzen die geplante Abdeckung.
- Keine wichtigen Layer entstehen mehr aus unkoordiniertem Poisson-Sampling.

---

# STUFE 10 – Raum-, Mix- und Mastering-Hierarchie

## Ziel

Aus guten Layern wird ein ausgewogener, tiefer und dynamischer Gesamtmix.

## Arbeitspakete

### 10.1 Gain-Staging

Kalibrierung auf:

- Voice,
- Event,
- Phrase,
- Layer,
- Stem,
- Bus,
- Master.

Pauschale, verstreute Multiplikationsfaktoren werden inventarisiert und durch dokumentierte
Gain-Ziele ersetzt.

### 10.2 Stem-Busse

Mindestens:

- Foundation,
- Harmonic,
- Motif,
- Rhythm,
- Texture,
- Objects,
- Space Returns.

### 10.3 Gemeinsamer Raumplan

- Vorder-, Mittel- und Hintergrund,
- Send-/Return-Räume,
- Tiefenstaffelung über Pegel, Spektrum, Pre-Delay und Transienten,
- frequenzabhängige Stereobreite,
- mono-kompatibles Low-End,
- Delay als musikalische Antwort.

### 10.4 Maskierung und Dynamik

- spektrale Konflikte erkennen,
- statische oder sanft dynamische Absenkung,
- Hauptmotiv priorisieren,
- Subbereich aufräumen,
- harsche Resonanzen kontrollieren,
- Bus-Glue nur bei Bedarf.

### 10.5 Master

- DC-/Subsonic-Kontrolle,
- sanfte Summenformung,
- True-Peak-Limiter,
- Loudness-Normalisierung,
- Messreport vor und nach Mastering.

## Vorgesehene Dateien

- `au/render/track.py`
- `au/render/mix.py` neu
- `au/render/master.py` neu
- `au/dsl/orchestration.py`
- `au/analysis/metrics.py`
- `tests/test_mix.py` neu
- `tests/test_track.py`

## Gate 10

- Mix erreicht den konfigurierten Loudness- und Peakbereich.
- Stems summieren sich gemäß dokumentierter Buslogik.
- Foundation bleibt mono-kompatibel.
- Keine wichtige Stimme wird durch Maskierung unhörbar.
- Mastering erzeugt keine dauerhafte starke Begrenzung.

---

# STUFE 11 – Kritiker- und Revisionsschleife

## Ziel

Fehler werden vor dem finalen Status erkannt und gezielt an der richtigen Ebene korrigiert.

## Arbeitspakete

### 11.1 Kritiker auf Ebenen verteilen

- Voice Critic,
- Phrase Critic,
- Harmony Critic,
- Orchestration Critic,
- Mix Critic,
- Form Critic.

### 11.2 Typisierte Revisionen

Beispiele:

- `replace_voice`,
- `shift_register`,
- `reduce_density`,
- `repair_voice_leading`,
- `vary_motif`,
- `strengthen_harmonic_carrier`,
- `reduce_noise`,
- `notch_resonance`,
- `rebalance_stem`,
- `reshape_section`.

### 11.3 Deterministischer Revisionszyklus

- maximale Revisionszahl konfigurieren,
- jede Revision protokollieren,
- Seed-Unterpfad pro Revision,
- Qualitätswerte vorher/nachher vergleichen,
- Verschlechterungen zurückweisen,
- bei anhaltendem kritischem Fehler Ergebnis blockieren.

## Vorgesehene Dateien

- `au/critics/` neu
- `au/dsl/quality.py`
- `au/integrator/revision.py` neu
- `au/integrator/compose.py`
- `tests/test_revision.py` neu

## Gate 11

- Mindestens vier Fehlerklassen lösen passende Revisionen aus.
- Revisionen verbessern die adressierte Metrik ohne kritische Regression.
- Kritische Restfehler verhindern den Status „Fertig“.
- Der Ablauf bleibt reproduzierbar.

---

# STUFE 12 – Studio-UI und Nachvollziehbarkeit

## Ziel

Die Oberfläche zeigt die musikalische Architektur und Qualitätsentscheidung verständlich an.

## Anzeigen

### 12.1 Intention

- erkannte Merkmale,
- ergänzte Defaults,
- Klangidentität,
- Komplexitäts- und Innovationsprofil.

### 12.2 Form

- Sektionen auf einer Timeline,
- Spannungs- und Dichtekurve,
- aktive Rollen,
- Höhepunkt und Rücknahme.

### 12.3 Musik

- Harmonieverlauf,
- Haupt- und Kontrastmotiv,
- Motivwiederkehr und Transformation,
- Phrasen,
- Registerverteilung.

### 12.4 Orchestrierung

- Generator pro Layer,
- Rollenfunktion,
- Beziehungen zwischen Layern,
- Vorder-/Mittel-/Hintergrund,
- Aktivitätskurven.

### 12.5 Qualität

- Stem- und Mixwerte,
- Warnungen,
- blockierende Konflikte,
- Revisionen,
- Gründe für Annahme oder Ablehnung.

## API

Neue strukturierte Endpunkte oder Felder für:

- Plan,
- Motive,
- Harmonien,
- Orchestrierung,
- Quality Report,
- Revision Log.

## Vorgesehene Dateien

- `au/studio/api.py`
- `au/studio/static/index.html`
- optional Aufteilung des Frontends in kleinere Module
- `tests/test_studio.py`

## Gate 12

- Die UI zeigt ausschließlich real erzeugte Daten.
- Der Nutzer kann erklären, warum ein Layer spielt und welche Funktion er erfüllt.
- „Fertig“ wird nur bei bestandenem finalem Gate angezeigt.
- Fehlerzustände und Revisionen sind sichtbar.

---

# STUFE 13 – Referenzproduktionen und finale Abnahme

## Ziel

Die Gesamtarchitektur an realen, deutlich unterschiedlichen Produktionen beweisen.

## Referenztrack A – warm und organisch

- langsame Transformation,
- körperhafte Foundation,
- weiche harmonische Bewegung,
- organische Modulation,
- zurückhaltende motivische Stimme,
- dunkler gemeinsamer Raum.

## Referenztrack B – kalt und gläsern

- metallische und modale Körper,
- kontrollierte Dissonanz,
- deutliche räumliche Tiefe,
- glitzernde Texturen,
- keine dominante Pfeifresonanz.

## Referenztrack C – rhythmisch elektronisch

- gemeinsames Raster,
- Bassbewegung,
- Sequenz oder Arpeggio,
- motivische Verknüpfung,
- ambienttaugliche Dynamik und Raumtiefe.

## Abnahmeablauf

1. Trackplan erzeugen und archivieren.
2. Mix und alle Stems rendern.
3. `MusicalQualityReport` erzeugen.
4. Automatische Revisionen abschließen.
5. Waveform und Spektrogramm prüfen.
6. Strukturiertes Hörprotokoll erstellen.
7. Baseline-Vergleich durchführen.
8. Seed-Reproduktion prüfen.
9. Unterschiedlichkeit der drei Tracks messen.
10. Vollständige Testsuite ausführen.

## Finale Kommandos

```powershell
.venv\Scripts\python.exe -m pytest -q -m "not audio"
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m mypy au
```

## Gate 13

Die Definition of Done aus Abschnitt 3 ist für alle drei Tracks erfüllt. Abweichungen müssen
im Abschlussbericht konkret begründet und als verbleibende Arbeit priorisiert werden.

---

## 5. Empfohlene Commit- und Lieferstruktur

Jede Stufe wird separat abgeschlossen:

```text
phase2-00-baseline
phase2-01-capability-matrix
phase2-02-quality-gates
phase2-03-musical-models
phase2-04-prompt-intent
phase2-05-form-harmony-time
phase2-06-motifs-phrases
phase2-07-orchestration
phase2-08-voice-catalog
phase2-09-event-realization
phase2-10-mix-master
phase2-11-revision-loop
phase2-12-studio-transparency
phase2-13-reference-tracks
```

Vor jedem Commit:

- nur zur Stufe gehörende Dateien prüfen,
- schnelle Tests ausführen,
- relevante Audio-Tests ausführen,
- Ergebnis und bekannte Grenzen dokumentieren,
- keine fremden Arbeitsbaumänderungen aufnehmen.

---

## 6. Prioritäten bei begrenzter Zeit

Falls nicht alle Stufen sofort umgesetzt werden können:

### Muss zuerst

1. Baseline und Qualitätsmetriken,
2. gemeinsamer Form-/Harmonieplan,
3. Motive und Phrasen,
4. Orchestrierung,
5. mindestens zwei Stimmen pro Kernrolle,
6. koordiniertes Event-Rendering,
7. Gain-Staging und Loudness.

### Danach

8. automatische Revision,
9. tiefere räumliche Komposition,
10. vollständige UI-Visualisierung,
11. exotische Synthesefamilien.

Eine große Stimmenbibliothek ohne musikalische Hierarchie hat geringere Priorität als eine
kleinere, gut orchestrierte Bibliothek.

---

## 7. Hauptrisiken und Gegenmaßnahmen

| Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|
| Zu viele parallele Abstraktionen | Lange Entwicklung ohne hörbaren Fortschritt | Jede Stufe endet mit kurzem realem Render |
| Metriken werden zum Selbstzweck | Tests bestehen, Musik bleibt schlecht | Hörprotokoll und drei Referenzästhetiken |
| Stimmenkatalog wächst unkontrolliert | Hohe Wartung, geringe Differenzierung | Capability-Matrix und Rollen-Auditions |
| Zufall zerstört Zusammenhang | Unverbundene Events | Zufall nur innerhalb von Form, Phrase und Relation |
| Solver wird zu komplex | Keine Lösung oder lange Laufzeit | Harte/softe Constraints und gestufte Revision |
| Lautheit verdeckt musikalische Defizite | Lauter wirkt kurzfristig besser | Vorher-Nachher auch loudness-matched vergleichen |
| Bestehende Änderungen kollidieren | Arbeit geht verloren | Statusprüfung und kleine, stufenbezogene Patches |
| CPU-Kosten explodieren | Vorschau wird unbrauchbar | Voice-, Layer- und Trackbudgets messen |
| Harte Resonanzen | Pfeifen trotz komplexerer Stimmen | Resonanzmetriken, Registergrenzen und dynamische Kontrolle |
| UI läuft dem Backend voraus | Attraktive, aber falsche Darstellung | UI ausschließlich aus serialisierten Plandaten |

---

## 8. Fortschrittsprotokoll

Nach jeder Stufe wird dieser Abschnitt aktualisiert:

| Stufe | Status | Datum | Tests | Hörartefakt | Offene Punkte |
|---|---|---|---|---|---|
| 0 | abgeschlossen | 26.07.2026 | tests/golden/prompts/*.json | projects/baseline/*/mix.wav | keine |
| 1 | abgeschlossen | 26.07.2026 | tests/test_capabilities.py | Capability-Report ok | keine |
| 2 | abgeschlossen | 26.07.2026 | tests/test_musical_quality.py | LUFS/Peak/Active-Metriken ok | keine |
| 3 | abgeschlossen | 26.07.2026 | tests/test_musical_models.py | Domain Models ok | keine |
| 4 | abgeschlossen | 26.07.2026 | tests/test_prompt_intent.py | Intent-Uebersetzung ok | keine |
| 5 | abgeschlossen | 26.07.2026 | tests/test_musical_quality.py | Sektions-Plan ok | keine |
| 6 | abgeschlossen | 26.07.2026 | tests/test_voice_leading.py | Voice Leading & Motive ok | keine |
| 7 | abgeschlossen | 26.07.2026 | tests/test_solver.py | Relationen & Solver ok | keine |
| 8 | abgeschlossen | 26.07.2026 | tests/test_sweep.py | Stimmenkatalog ok | keine |
| 9 | abgeschlossen | 26.07.2026 | tests/test_compose.py | Event-Realisation ok | keine |
| 10 | abgeschlossen | 26.07.2026 | tests/test_track.py | Mix & Limiter ok | keine |
| 11 | abgeschlossen | 26.07.2026 | tests/test_revision.py | Revisions-Schleife ok | keine |
| 12 | abgeschlossen | 26.07.2026 | tests/test_studio.py | Web Studio UI ok | keine |
| 13 | abgeschlossen | 26.07.2026 | test_musical_quality.py | scratch/ref_tracks/*/mix.wav | Keine |


---

## 9. Abschlussbericht

Der vollständige Abschlussbericht gemäß allen 14 Kriterien ist dokumentiert unter:  
[docs/abschlussbericht.md](file:///c:/Users/enzoc/Desktop/AI%20Code/anmbiet_universe/docs/abschlussbericht.md)

