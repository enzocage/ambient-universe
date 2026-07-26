# Plan 6 – Ableton-inspirierter Produktionsworkflow für bessere Synthmusik

## Ausgangslage

Die aktuelle Ausgabe klingt trotz vieler Generatoren wie eine gleichförmige Suppe. Der Grund:
Die Pipeline wählt und rendert Layer direkt in eine lineare Summe. Erfolgreiche Synthproduktionen
arbeiten dagegen mit Ideen-Containern, Szenen, Klangketten, Automation, Resampling und einem
gezielten Arrangementpass.

Abletons eigene Ressourcen betonen dafür mehrere wiederkehrende Arbeitsweisen: Session- und
Arrangement-Ansicht für Ideen und Form, Automation und Modulation als musikalische Bewegung,
Racks für gespeicherte Gerätekombinationen, Routing für Layering/Submixing/Resampling und
Resampling als eigenständige Sounddesignstufe. Das Projekt übernimmt diese Prinzipien als
abstrakte, backend-unabhängige Produktionsmodelle.

## 1. Ideenbank und Szenen statt sofortiger Dauerspur

Jeder Track beginnt mit mehreren kurzen, hörbaren Szenen:

- `seed_scene`: Klangkeim und Hauptmotiv
- `groove_scene`: Bass, Arpeggio und Percussion
- `harmony_scene`: Akkordfeld und Antwortstimme
- `texture_scene`: Bewegung, Raum und Übergang
- `peak_scene`: stärkste validierte Konstellation

Eine Szene ist ein reproduzierbares Paket aus Events, Rollen, Klanggesten, Automation und
Energie. Szenen werden zunächst solo, als Duo und als Ensemble auditiert. Erst erfolgreiche
Szenen dürfen in das Arrangement gelangen.

Die Auswahl wird nicht zufällig getroffen, sondern nach Klangqualität, musikalischer Funktion,
Kontrast zur vorherigen Szene, Nutzerbewertung und Neuheit priorisiert.

## 2. Rack-/Konstellationsmodell für funktionierende Klangketten

Ein `ProductionRack` speichert nicht nur einen Synth, sondern eine erfolgreiche Konstellation:

- Quelle oder Synthfamilie
- Artikulation und Hüllkurve
- Filter-/Resonanzbewegung
- Modulation
- Sättigung oder Verzerrung
- Raum-/Delay-Send
- Makroparameter
- Rolle und Register
- kompatible Partner
- objektiver Score und persönlicher Taste-Score

Jede Hauptrolle erhält drei bis fünf geprüfte Racks. Ein Arrangement wählt nicht zehn zufällige
Module, sondern wenige vollständige Konstellationen, die als Duo und Ensemble funktioniert haben.

## 3. Automation, Modulation und Resampling als Produktionsstufen

Jede Szene benötigt mindestens eine musikalisch relevante Automation:

- Filter-/Formantöffnung
- FM-Index oder Wavefold-Stärke
- Raumdistanz und Breite
- Delay-Feedback oder Tape-Drift
- Gate-/Dichtebewegung
- Ducking durch Bass oder Kickanker

Automation wird von der Form geplant und nicht nachträglich zufällig auf Layer gelegt.

Nach erfolgreichen Szenen folgt ein `ResamplePass`: eine Szene oder ein Stem wird als neues
Audio-/Texturobjekt behandelt. Das Resampling darf Zeit, Tonhöhe, Hüllkurve, Granularität,
Reverse und Filter verändern. Es erzeugt Übergänge, Antwortflächen und Peak-Material, ersetzt
aber nicht die Kernstimme.

## 4. Arrangementpass mit Locators, Kontrast und Energie

Das Arrangement wird als Szenenfolge mit Markern gebaut:

```text
INTRO → GROOVE → BUILD → CONTRAST/VACUUM → PEAK → TRANSFORM → OUTRO
```

Jede Szene besitzt:

- aktive und ruhende Rollen,
- Energie- und Dichteziel,
- Register-/Spektralprofil,
- Einstieg und Ausstieg,
- Automationsereignisse,
- Übergangsgeste,
- erwartete Rückkehr eines Motivs.

Benachbarte Szenen müssen sich in mindestens drei Eigenschaften unterscheiden. Alle 4–8 Takte
werden kleine Änderungen geplant; vor dem Peak gibt es eine echte Reduktion oder Pause.

## 5. Qualitätsgates und direkte Implementierung

Ein Track wird erst als fertig markiert, wenn:

- mindestens fünf Szenen auditiert wurden,
- mindestens drei Racks im Ensemble erfolgreich sind,
- jede Kernrolle mindestens eine Automation besitzt,
- mindestens ein Resample-Objekt sinnvoll eingesetzt wird,
- ein Motiv in mindestens drei Szenen wiederkehrt und variiert,
- der Peak nicht nur lauter, sondern dichter und kontrastreicher ist,
- Stem- und Mixvergleich die Szenenfolge hörbar bestätigt.

### Umsetzung im Repository

- `au/dsl/ableton_workflow.py`: Szenen, Racks, Automationslanes, ResamplePass und WorkflowPlan
- `au/integrator/compose.py`: Workflow vor dem finalen Render erzeugen und budgetabhängig vertiefen
- `au/studio/api.py`: Workflow-/Szenen-/Budgetdaten im Ergebnis anzeigen
- `tests/test_ableton_workflow.py`: Determinismus, Szenenkontrast, Rack- und Gateprüfungen
- `plan6.md`: Produktionsregeln und Referenzquellen

### Recherchegrundlage

- [Ableton Learn Live: Workflows](https://www.ableton.com/en/live/learn-live/workflows/)
- [Ableton Live Concepts: Racks, Routing, Layering und Resampling](https://www.ableton.com/en/manual/live-concepts/)
- [Ableton: Circuit Breaking – Five Creative Tools for Arrangements](https://www.ableton.com/en/blog/circuit-breaking-five-creative-tools-for-arrangements/)
- [Ableton: Automation and Editing Envelopes](https://www.ableton.com/en/live-manual/11/automation-and-editing-envelopes/)
- [Ableton: Keep it Simpler – Sounddesign, Warp und Loop](https://www.ableton.com/en/blog/keep-it-simpler-tips-synthesis-and-sound-design/)
- [Ableton Artist Quotes](https://www.ableton.com/en/pages/artists/artist_quotes/)
