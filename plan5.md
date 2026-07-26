# Plan 5 – Hierarchische Musikproduktion statt Layer-Sammlung

**Ziel:** Die Maschine soll nicht länger viele unabhängige Klangschichten addieren, sondern aus wenigen starken musikalischen Keimen über mehrere Ebenen Wiedererkennung, Variation, Erwartung, Spannung und Auflösung entwickeln.

Die bisherigen Ergebnisse wirken primitiv, weil Klang, Pattern, Arrangement und Mix zu flach gekoppelt sind. Ein gutes Preset erzeugt noch keine gute Musik. Plan 5 ersetzt deshalb die Layerlogik durch eine hierarchische Produktionslogik.

## 1. Hierarchisches Musikmodell mit klaren Eigentümern

Fünf Ebenen werden eingeführt:

```text
L0 Klangkeim / Sound Gesture
L1 Ereignis / Note / Transient
L2 Motiv / Bassfigur / Groove
L3 Phrase / Frage-Antwort / 4–8-Takt-Gruppe
L4 Abschnitt / Energie / Orchestrierung
L5 Gesamtform / Erwartung / Höhepunkt / Schluss
```

Jede Ebene besitzt einen eigenen Plan und darf nur definierte Parameter der darunterliegenden Ebene verändern. Ein Ereignis referenziert deshalb immer `form_id`, `section_id`, `phrase_id`, `motif_id` und `gesture_id`.

- L0 entscheidet Klangidentität, Register und Artikulation.
- L1 entscheidet Tonhöhe, Onset, Gate, Velocity und Mikro-Timing.
- L2 entscheidet Wiederholbarkeit, Akzente und Variation.
- L3 entscheidet Frage, Antwort, Vorhalt, Auflösung, Pause und Fill.
- L4 entscheidet Rollen, Dichte, Spektrum, Raum und Energie.
- L5 entscheidet Rückkehr, Höhepunkt und Schlusswirkung.

Die Rückkopplung läuft nach oben und unten: Bassakzente beeinflussen Ducking und Filter, Motive beeinflussen Events, Abschnittsenergie aktiviert Rollen, und der Kritiker meldet Probleme an die höchste Ebene zurück, die sie beheben kann. Keine untere Ebene darf fehlende Form durch Zufallsereignisse ersetzen.

**Implementierung:** `HierarchicalScore`, `MotifGraph`, `PhrasePlan`, `SectionPlan` und `FormPlan` als deterministische Modelle einführen.

**Gate:** Für jedes hörbare Ereignis kann bis zum Formabschnitt zurückverfolgt werden, warum es existiert.

## 2. Produktions- und Struktur-Patterns als Transformationsgrammatik

Die 50 Klangbeschreibungen und kuratierte Produktionsanalysen aus dem Internet werden nicht als fertige Presets importiert, sondern als versionierte Transformationsregeln. Ein `PatternGrammar`-Eintrag enthält Funktion, Hierarchieebene, Triggerquelle, zulässige Bewegung, Spannungsziel, Partner, Abschnittsfit, Risiko und Abbruchbedingungen.

Die wichtigsten Produktionsmuster:

- Wiederholung mit Variation: gleiche Figur, aber neues Register, Gate, Ende, Timbre oder Instrument.
- Addition/Subtraktion: alle 4–8 Takte eine Rolle hinzufügen, entfernen oder nur andeuten.
- Call and Response: Arpeggio/Motiv stellt eine Frage, Bass, Resonator oder Pad antwortet.
- Layered Ostinato: kurze und lange Perioden überlagern sich kontrolliert.
- Register- und Dichtewelle: Material wird schrittweise höher, heller oder dichter und danach wieder reduziert.
- Antizipation und Verzögerung: Bass oder Arpeggio kündigt einen Akkordwechsel an oder hält darüber hinaus.
- Fill und Vakuum: Vor dem Wechsel steigt die Aktivität; auf der Eins folgt ein neuer Impuls oder bewusst Platz.
- Klangkeim-Transformation: derselbe Keim erscheint als trockener Pluck, resonantes Objekt, Fläche und Hallfahne.

Jedes Pattern muss mindestens zwei Hierarchieebenen verbinden. Ein isolierter LFO gilt nicht als musikalische Entwicklung.

Ein `ReferencePatternImporter` darf aus öffentlich dokumentierten Produktionsanalysen abstrakte Daten übernehmen: Abschnittsfolge, Energiekurve, Rollenwechsel, Patternlängen, Übergangsgesten, Register- und Spektralkontrast sowie Wiederholungs-/Variationsabstände. Es werden keine geschützten Audioinhalte, Melodien oder identifizierbaren Songkopien übernommen. Jede Quelle erhält Herkunft, Stilkontext und Unsicherheit.

**Gate:** Jede neue Referenzregel wird zuerst in einem 20-Sekunden-Testarrangement gehört und erst danach produktiv zugelassen.

## 3. Aufschaukeln durch Energie-, Erwartungs- und Beziehungsgraph

Ein `EscalationGraph` beschreibt, wie mehrere Ebenen gemeinsam wachsen:

```text
Motiv-Wiederholung
→ Variation am Phrasenende
→ Bass-Antizipation
→ Gegenstimme
→ höhere Akzentdichte / kürzere Gates
→ helleres Spektrum / größere Nähe
→ Fill und Erwartungspause
→ Peak mit bekanntem Kern und verändertem Umfeld
```

Pro Eskalationsstufe dürfen höchstens zwei Hauptdimensionen stark verändert werden: Dichte, harmonische Spannung, Register, Helligkeit, Lautheit, Transienten, Raum oder aktive Rollen. Dadurch bleibt die Entwicklung kausal hörbar.

Verbindliche Dramaturgie:

- Wiederholung 1: Hauptmotiv klar und fast unverändert.
- Wiederholung 2: Bassende oder Arpeggioakzent variieren.
- Wiederholung 3: Antwortstimme oder Gegenrhythmus ergänzen.
- Wiederholung 4: Klanggeste, Register oder Artikulation transformieren.
- Vor dem Peak: Reduktion oder Stille als Erwartung.
- Peak: stärkste Kombination aus bekanntem Motiv und neuem Umfeld.
- Danach: zuerst hohe Bewegung, dann Percussion, dann Arpeggio, zuletzt Bass/Foundation abbauen.

Mindestens sechs hörbare Relationen müssen den Peak tragen: Bass→Ducking, Bass→Filter/Wavefold, Arpeggio→Resonator, Motivpause→Antwort, Fill→Delay/Reverb, Dichte→Raumdistanz, Akkordwechsel→Patternmutation oder Abschnittswechsel→Klangfamilienübergabe.

**Gate:** Wird eine Relation stummgeschaltet, muss sich das Audio hörbar verändern. Metadaten allein zählen nicht.

## 4. Neue Produktionsreihenfolge: erst Musik, dann Klang, dann Mix

Die Pipeline wird in fünf Pässe geteilt:

1. **Formkern:** Peak zuerst als 8–16-Takt-Kern entwerfen; Hauptmotiv, Bassphrase, Grooveanker, Harmonie und Register festlegen.
2. **Hierarchie:** Aus dem Kern vier Abschnittsvarianten ableiten; Rollen hinzufügen/entfernen, Motivvarianten, Antworten, Übergänge und Vakuumstellen planen.
3. **Klangbesetzung:** Erst jetzt `SoundPriorityEngine` aufrufen; pro Rolle mehrere validierte SoundPatterns testen; Klangidentität über Abschnitte transformieren.
4. **Performance:** Artikulationsprofile, Microtiming, Ghost Notes, Vorhalte, selektives Legato und begrenzte Imperfektion ausarbeiten.
5. **Arrangementmix:** Rollenbusse getrennt mischen, Frequenz-/Raumstaffelung und Übergänge herstellen, erst danach Loudness und Mastering.

Wenn der Peak keinen Kontrast besitzt, wird der Abschnittsplan revidiert und nicht bloß lauter gemastert.

## 5. Struktur-Learn/Train, Kritik und Abnahme

Der bestehende Learn/Train-Modus bewertet künftig nacheinander Klangkeim, Motiv, Bass-/Arpeggio-Paar, 4-Takt-Phrase, Abschnittsübergang, 20-Sekunden-Arrangement und vollständigen Mix. Jede Bewertung bleibt getrennt nach objektiver Qualität, musikalischer Verständlichkeit, Spannung/Erwartung, emotionaler Wirkung, persönlichem Geschmack und Arrangementqualität.

Neue harte Gates:

- Nach 8 Sekunden ist ein Kernmotiv oder Grooveanker erkennbar.
- Jede Wiederkehr verändert mindestens eine Dimension.
- Eine Frage-Antwort- oder Vorhalt-Auflösung-Beziehung ist hörbar.
- Benachbarte Abschnitte unterscheiden sich in mindestens drei Dimensionen.
- Der Peak besitzt höhere Erwartung und Dichte, nicht nur mehr RMS.
- Mindestens sechs Layer-Relationen verändern das Audio tatsächlich.
- Eine Reduktion oder Pause schafft Platz für den nächsten Abschnitt.
- Das Ende beantwortet oder transformiert den Anfang.

Der Kritiker setzt immer nur die fehlerhafte Ebene zurück: Klangproblem→SoundPattern, Artikulation→Performance, Motivproblem→Phrase, Übergang→Abschnitt, Formproblem→Gesamtform. Nach drei erfolglosen Revisionen wird die Variante verworfen und der Fehlerbericht gespeichert.

**Umsetzungsreihenfolge:** HierarchicalScore und MotifGraph, Peak-first-Kern, PatternGrammar und ReferencePatternImporter, EscalationGraph, hierarchischer Renderer, strukturelles Nutzertraining, gezielte Ebenenrevision.

**Erfolg:** In drei Blindtests erkennen Hörer innerhalb von 20 Sekunden Motiv oder Groove, nach 40 Sekunden Entwicklung und vor dem Peak eine Erwartungspause. Der Peak erscheint als Konsequenz des Materials und nicht als zufällig eingehängter neuer Klang.

### Recherchegrundlage

- [Open University: Repetition, Contrast and Variation](https://www.open.edu/openlearn/history-the-arts/introduction-music-theory-1-form/content-section-3.1)
- [Columbia Current Musicology: Habituation–Fluency Theory of Repetition](https://journals.library.columbia.edu/index.php/currentmusicology/article/view/5312)
- [MIT Open Encyclopedia of Cognitive Science: Music Cognition](https://oecs.mit.edu/pub/x1cmpaio/release/1)
- [iZotope: Arranging Music for Better Mixdowns](https://www.izotope.com/community/blog/arranging-music-for-better-mixdown)
- [iZotope: Better Transitions in a Mix](https://www.izotope.com/community/blog/how-to-create-better-transitions-in-your-mix)
- [Carnegie Mellon: Intro to Music Concepts](https://www.cs.cmu.edu/~music/cmp/archives/cmsip/readings/music-theory.htm)
