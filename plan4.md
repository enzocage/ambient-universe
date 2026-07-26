# Ambient Universe – Plan 4: Hörbarer Puls, Bass, Arpeggio und drastisch höhere Musikqualität

**Stand:** 26. Juli 2026  
**Bezug:** `plan.md`, `plan2.md`, `plan3.md` und aktueller Repository-Zustand  
**Priorität:** Kritisch – vorhandene rhythmische Rollen sind im finalen Audio nicht zuverlässig hörbar  
**Dokumenttyp:** Verbindlicher Implementierungs-, Hörtest- und Abnahmeplan

---

## 1. Zielbild

Die Musikmaschine soll Ambient-Musik erzeugen, die gleichzeitig räumlich, organisch und
musikalisch klar gegliedert ist. Arpeggiator, Bass und Rhythmuselemente sollen nicht als
aufgesetzter Beat erscheinen, sondern als hörbare, miteinander gekoppelte Bewegung:

- Der **Bass** gibt Körper, harmonische Richtung und einen wiedererkennbaren Puls.
- Der **Arpeggiator** macht Akkorde, Motive und Formbewegung zeitlich hörbar.
- Die **Rhythmuselemente** erzeugen Groove, Akzente, Atem und Übergänge.
- Pads, Drones, Texturen und Objekte reagieren auf diese rhythmischen Rollen.
- Jeder Abschnitt besitzt eine eigene rhythmische Identität.
- Der Mix macht die Funktionen erkennbar, ohne die räumliche Ambient-Wirkung zu verlieren.

Das Ziel ist nicht „mehr Noten“ oder ein durchgehender Dance-Beat. Das Ziel ist ein
musikalischer Zeitfluss mit Erwartung, Wiedererkennung, Variation, Spannung und Entspannung.

---

## 2. Bestätigte Ursachen des aktuellen Problems

### 2.1 Rhythmische Rollen werden nicht zuverlässig in den Blueprint aufgenommen

`au/integrator/blueprint.py` wählt Rollen überwiegend nach allgemeinen Charakterwerten.
`bass_sequence`, `arpeggiator` und `subtle_percussive_background` werden dort aktuell nicht
systematisch aus rhythmischer Prompt-Intention abgeleitet.

Zusätzlich verwendet `compose_track()` standardmäßig `max_slots=6`. Die zuerst erzeugten
Slots sind meist Foundation, Drone, Noise, Textur, Pad und Objekt. Rhythmische Rollen können
deshalb selbst dann abgeschnitten werden, wenn sie später im Blueprint vorhanden wären.

**Folge:** Die Module existieren im Katalog, werden aber nicht Teil des Tracks.

### 2.2 Korrekte Pattern werden nachträglich überschrieben

`propose_candidates()` erzeugt für `arpeggiator`, `bass_sequence` und
`subtle_percussive_background` bereits Euklid-Pattern. In `compose_track()` wird
`pattern_kind` danach jedoch erneut gesetzt:

- Foundation/Drone/Pad → `sustained`
- alle anderen Rollen → `poisson`

Damit verlieren Arpeggiator, Bass und Percussion ihre geplante Taktstruktur.

**Folge:** Eine rhythmische Rolle wird zu zufällig verteilten Einzelereignissen.

### 2.3 Mehrere unabhängige Rhythmusgeneratoren konkurrieren

Die Trackebene erzeugt NoteEvents aus Clock und Euklid-Pattern. Einige Stimmen wie
`gen.arpeggio.euclidean_pulse` oder `gen.arpeggio.random_walk_seq` verwenden intern zusätzlich
`Dust`, `LFNoise0` oder eigene Geschwindigkeiten.

**Folge:** Das NoteEvent startet zwar auf dem Raster, aber der Klang innerhalb des Events folgt
einem zweiten, unkoordinierten Zufallsrhythmus. Der gemeinsame Groove wird verwischt.

### 2.4 Abschnittsprofile planen keine vollständige Rhythmusdramaturgie

Die vorhandenen Section Profiles enthalten überwiegend Foundation, Drone, Pad, Noise,
Textur und Objekte. Arpeggiator, Basssequenz und subtile Percussion sind nicht über Intro,
Build, Peak und Outro hinweg dramaturgisch geplant.

**Folge:** Rhythmus ist weder formbildend noch als Entwicklung hörbar.

### 2.5 Bass, Arpeggio und Percussion verschwinden im Stem- und Mixmodell

`STEM_BUCKETS` besitzt keine expliziten Einträge für `bass_sequence`, `arpeggiator` und
`subtle_percussive_background`. Unbekannte Rollen landen im Sammelstem `objects`.

Der Renderer summiert Stems anschließend ohne rollenbezogene Pegelregelung, Masking-Kontrolle,
Transientenbearbeitung oder Sidechain-Beziehungen.

**Folge:** Bass und Arpeggio können von Drones und Texturen maskiert werden. Eine gezielte
Soloanalyse oder Balancekorrektur ist nicht möglich.

### 2.6 Qualitätsmetriken messen nicht die geforderte Musik

Die aktuelle Qualitätsanalyse misst unter anderem Pegel, Aktivität, Clipping und grobe
harmonische Energie. Sie beantwortet aber nicht:

- Ist eine Basslinie vorhanden und hörbar?
- Gibt es einen stabilen Puls?
- Ist das Arpeggio akkordgebunden?
- Wiederholt sich ein rhythmisches Motiv?
- Gibt es Groove-Kontrast zwischen Abschnitten?
- Sind Kick-/Bass-ähnliche Impulse und Subfundament sauber getrennt?

**Folge:** Ein Track kann technisch akzeptiert werden, obwohl die gewünschten Rollen fehlen.

---

## 3. Verbindliche Architektur

```text
Prompt / DNA
  → RhythmIntent
  → GroovePlan + Harmonie + Form
  → Rollenpflichten je Abschnitt
  → BassPlan / ArpeggioPlan / PercussionPlan
  → gemeinsame EventTimeline
  → klangliche Ausführung durch Synth-Stimmen
  → rollengetrennte Stems
  → relationale Mischung
  → Rhythmus- und Musikqualitätskritiker
  → gezielte Revision
```

Wichtig: Die musikalische EventTimeline bestimmt **wann** und **welche Tonhöhe** erklingt.
Ein Synthesizer bestimmt **wie** dieses Ereignis klingt. Synth-interne Zufallstrigger dürfen
die geplante Zeitstruktur nicht ersetzen.

---

# STUFE 0 – Hörbare Diagnose und Referenzzustand

## Ziel

Vor jeder Änderung nachweisen, an welcher Stelle Bass, Arpeggio und Rhythmus verschwinden.

## Arbeitspakete

### 0.1 Fester Rhythmus-Diagnoseprompt

Mindestens einen verpflichtenden Prompt versionieren:

> Rhythmisch und sequenziert, tiefer bewegter Bass, warmes polymetrisches Arpeggio,
> subtile perkussive Impulse, atmosphärisch und weit, kein aggressiver Dance-Beat.

Feste Parameter:

- Dauer: 60 Sekunden
- drei Seeds
- feste Sample Rate
- vollständige Metadaten
- identische Lautheitsziele

### 0.2 Pipeline-Tracing

Pro Render protokollieren:

- erkannte `RhythmIntent`,
- gewünschte und tatsächlich ausgewählte Rollen,
- verworfene Rollen und Grund,
- PatternKind pro Layer,
- Eventzahl pro Rolle und Abschnitt,
- Eventzeiten, Tonhöhen, Dauern und Velocity,
- verwendeter Generator pro Rolle,
- Stem-Zuordnung,
- Stem-LUFS, Peak, RMS und aktive Zeit,
- Beitrag jedes Stems zum finalen Mix.

### 0.3 Diagnose-Render

Je Seed erzeugen:

- Bass solo,
- Arpeggiator solo,
- Percussion solo,
- Rhythmusgruppe ohne Pads,
- Pads/Drones ohne Rhythmusgruppe,
- vollständiger Mix,
- alternativer Mix mit Rhythmusgruppe +6 dB.

## Gate 0

- Für jede fehlende oder maskierte Rolle ist die Ursache eindeutig einer Pipeline-Stufe
  zugeordnet.
- Es ist dokumentiert, ob die Rolle nicht geplant, nicht gerendert, zu leise, spektral
  maskiert oder rhythmisch undeutlich ist.

---

# STUFE 1 – RhythmIntent und garantierte Rollenbesetzung

## Ziel

Rhythmische Prompts müssen zwingend rhythmische Rollen erzeugen. Slotlimits dürfen
Kernfunktionen nicht versehentlich entfernen.

## Arbeitspakete

### 1.1 `RhythmIntent` einführen

Neues Modell, mindestens mit:

- `presence`: 0–1
- `pulse_clarity`: 0–1
- `syncopation`: 0–1
- `density`: 0–1
- `groove_stability`: 0–1
- `bass_motion`: 0–1
- `arpeggio_activity`: 0–1
- `percussion_activity`: 0–1
- `ambient_softness`: 0–1
- `tempo_range_bpm`
- `preferred_subdivision`
- `forbidden_styles`, z. B. kein Four-on-the-floor

Promptbegriffe wie „rhythmisch“, „sequenziert“, „Puls“, „bewegter Bass“, „Arpeggio“,
„polyrhythmisch“, „perkussiv“ und „Beat“ müssen getrennte Achsen beeinflussen.

### 1.2 Pflichtrollen aus Intent ableiten

Regeln:

- `rhythm_presence >= 0.45` → `bass_sequence` oder `subharmonic_pulse`
- `arpeggio_activity >= 0.35` → `arpeggiator`
- `percussion_activity >= 0.25` → `subtle_percussive_background`
- `bass_motion >= 0.55` → `bass_sequence` zusätzlich zu `foundation`
- explizite Promptnennung einer Rolle → Rolle ist Pflicht, nicht optional

### 1.3 Slotbudget durch Funktionsbudgets ersetzen

`max_slots=6` darf keine Pflichtrolle abschneiden. Statt einer simplen Listenbegrenzung:

1. Pflichtrollen reservieren.
2. Fundament und Harmonie reservieren.
3. verbleibende Slots nach musikalischem Nutzen vergeben.
4. bei zu kleinem Budget optionale Texturen zuerst reduzieren.

Empfohlene Standardbesetzung für rhythmisches Ambient:

- Foundation
- Harmonic Drone oder Moving Pad
- Bass Sequence
- Arpeggiator
- Subtle Percussive Background
- Signal Motif
- eine Texture/Atmosphere-Rolle

## Gate 1

- Jeder explizit rhythmische Prompt enthält Bass, Arpeggiator und mindestens eine
  Rhythmusrolle im Blueprint.
- Diese Rollen bleiben auch bei kleinem Slotbudget erhalten.
- Tests prüfen nicht nur Rollennamen, sondern die später erzeugten Layer.

---

# STUFE 2 – Gemeinsamer GroovePlan

## Ziel

Alle rhythmischen Rollen beziehen sich auf dieselbe musikalische Uhr, besitzen aber
unterschiedliche, komplementäre Muster.

## Datenmodell

`GroovePlan` enthält:

- BPM und Taktart,
- Raster und Subdivision,
- Swing oder Microtiming,
- Taktanzahl pro Phrase,
- Hauptpuls und Nebenpuls,
- Accent Map,
- Silence Map,
- Fill-Positionen,
- Patternwechsel je Abschnitt,
- erlaubte Polymeter-Verhältnisse,
- Humanization-Budget,
- SeedPath.

## Regeln

- Bass, Arpeggio und Percussion teilen Downbeats und Phrasengrenzen.
- Nicht jede Rolle spielt jeden Puls.
- Akzente sind hierarchisch: Takt, Halbtakt, Beat, Subdivision.
- Humanization wird nach der Quantisierung angewendet und bleibt begrenzt.
- Polymetrik darf nur über gemeinsame Phrasengrenzen laufen.
- Tempoänderungen erfolgen abschnittsweise oder als kontrollierte Rampen.

## Patternbibliothek

Mindestens:

- Euklidisch 3/8, 5/8, 5/12, 7/16, 9/16, 11/16
- Downbeat-Anker
- Offbeat-Puls
- Tresillo-ähnliche Ambient-Figur
- sparse syncopation
- call-and-response
- additive Gruppen wie 3+3+2
- Halftime und Doubletime
- polymetrische Überlagerung 3 gegen 4
- Übergangsfill
- bewusster Takt Pause

## Gate 2

- Alle rhythmischen Events lassen sich auf einen GroovePlan zurückführen.
- Kein Synth-interner Zufallsprozess verschiebt die primären Onsets.
- Drei Rollen können verschiedene Muster besitzen und treffen dennoch an Phrasengrenzen
  kontrolliert zusammen.

---

# STUFE 3 – Pattern-Überschreibung und Doppeltrigger beseitigen

## Ziel

Die korrekt geplanten Patterns erreichen unverändert den Renderer.

## Arbeitspakete

### 3.1 Rollenbasierte Patternwahl zentralisieren

Eine einzige Funktion entscheidet PatternKind und Patternparameter, z. B.
`build_role_pattern(role, rhythm_intent, groove_plan, section)`.

`compose_track()` darf `pattern_kind` nicht pauschal überschreiben.

### 3.2 Event-gesteuerte Stimmen

Arpeggio- und Bassstimmen müssen auf externe NoteEvents reagieren:

- ein NoteEvent = ein klarer Onset,
- Pitch kommt aus Harmonie/Arpeggio/BassPlan,
- Gate und Velocity kommen aus GroovePlan,
- Synth-interne LFOs modulieren Timbre, nicht das primäre Timing,
- `Dust` nur für explizite Textur oder kontrollierte Ghost Notes.

### 3.3 Hüllkurven korrigieren

Der aktuelle Score setzt Amplitude nach Attack direkt auf Velocity und hält sie bis zum
Eventende nahezu konstant. Für rhythmische Klarheit werden echte Artikulationsprofile
benötigt:

- pluck,
- short pulse,
- soft mallet,
- bass stab,
- legato bass,
- swelling arp,
- ghost note.

Attack, Decay, Sustain und Release müssen getrennt modellierbar sein.

## Gate 3

- Eventzeiten aus dem Plan stimmen samplegenau mit hörbaren Onsets überein.
- Arpeggiator-Solo besitzt klar erkennbare Tonfolgen.
- Bass-Solo besitzt klare Notenwechsel statt einer modulierten Dauerfläche.
- Kein zufälliger Doppelrhythmus verwischt das Raster.

---

# STUFE 4 – Musikalische Bass-Engine

## Ziel

Der Bass ist gleichzeitig Fundament, Bewegung und harmonische Führung.

## `BassPlan`

Enthält:

- Register, bevorzugt MIDI 28–48,
- Root-, Fifth-, Octave- und Passing-Tone-Anteile,
- Rhythm Pattern,
- Note Length Pattern,
- Accent Pattern,
- Phrasekontur,
- Approach Notes,
- Pedal-Tone-Phasen,
- Silence/Fills,
- Klangfamilie pro Abschnitt,
- Beziehung zu Foundation und Percussion.

## Kompositionsregeln

1. Der Bass folgt der ChordTimeline, spielt aber nicht nur Grundtöne.
2. Akkordwechsel werden durch Root, Fifth, chromatische oder modale Annäherung vorbereitet.
3. Wiederkehrende Zwei- bis Vier-Takt-Figuren schaffen Identität.
4. Jede zweite oder vierte Wiederholung erhält eine kontrollierte Variation.
5. Tiefe Noten bekommen mehr Raum und längere Gates.
6. Schnelle Figuren wechseln in ein höheres Bassregister.
7. Foundation und Bass Sequence dürfen nicht dauerhaft denselben Ton halten.
8. Subharmonischer Puls wird aus Bassakzenten abgeleitet, nicht unabhängig erzeugt.

## Klangdesign

Mindestens vier validierte Basscharaktere:

- reiner Sub + leiser Obertonlayer,
- warmer Ladder/Minimoog-Bass,
- kurzer FM-/Pluck-Bass,
- gefalteter oder 303-artiger Bewegungsbass.

Jeder Bass erhält:

- kontrollierte Mono-Komponente unter etwa 120 Hz,
- hörbare Obertöne zwischen etwa 120 und 700 Hz,
- DC-/Subsonic-Schutz,
- Velocity-abhängige Helligkeit,
- notenabhängige Hüllkurve.

## Gate 4

- Bass ist auf kleinen Lautsprechern durch Obertöne erkennbar und auf großen Systemen
  körperlich.
- Bassnoten entsprechen der Harmonie.
- Mindestens eine wiedererkennbare Bassphrase und zwei Varianten pro Track.
- Kein dauerhaftes Masking mit Foundation.

---

# STUFE 4A – Priorisierungsmodul für Synthesizer und erfolgreiche Klangkonstellationen

## Ziel

Die Maschine darf Synthesizer, Grundeinstellungen und Kombinationen nicht mehr primär durch
zufällige Katalogauswahl bestimmen. Ein neues `SoundPriorityEngine`-Modul erkennt zuerst die
musikalisch und klanglich stärksten Kandidaten. Seed-basierte Variation findet anschließend
nur innerhalb eines validierten Erfolgspools statt.

Das Modul beantwortet vor der Komposition:

1. Welcher Synthesizer erzeugt für die gewünschte Rolle einen starken Einzelklang?
2. In welchem Register und mit welchen Grundeinstellungen funktioniert er zuverlässig?
3. Welche Artikulation und welches Pattern machen seinen Charakter hörbar?
4. Mit welchen anderen Stimmen ergänzt er sich?
5. Welche Konstellation passt zur aktuellen Harmonie, Form und Rhythmusintention?
6. Welche erfolgreiche Variante wurde in diesem Track noch nicht überbeansprucht?

## Leitregel

```text
gesamter Modulkatalog
  → rollenbezogene Eignungsprüfung
  → validierte Grundeinstellungen
  → Solo-Klangbewertung
  → Partner- und Arrangementbewertung
  → erfolgreicher Kandidatenpool
  → gewichtete deterministische Auswahl
  → kontrollierte Permutation erfolgreicher Parameter
```

Zufall darf niemals entscheiden, ob ein ungeprüfter Klang verwendet wird. Zufall darf nur:

- zwischen ähnlich starken validierten Kandidaten auswählen,
- die Reihenfolge erfolgreicher Varianten verändern,
- kompatible Partner neu kombinieren,
- Parameter innerhalb nachgewiesener Sweet Spots variieren,
- erfolgreiche Pattern, Artikulationen und Register kontrolliert permutieren.

## 4A.1 Neue Datenmodelle

### `SynthBasePreset`

Beschreibt keine starre Produktvoreinstellung, sondern einen validierten musikalischen
Startpunkt:

- `preset_id`
- `module_id`
- `source_family`
- `supported_roles`
- `base_params`
- `base_macros`
- `pitch_register`
- `velocity_range`
- `articulation_profile`
- `recommended_pattern_kinds`
- `recommended_note_length_range`
- `recommended_density_range`
- `spectral_profile`
- `transient_profile`
- `spatial_profile`
- `safe_parameter_ranges`
- `forbidden_parameter_zones`
- `compatible_processors`
- `cpu_cost`
- `validation_state`

### `SoundCandidateScore`

Bewertung eines Presets für einen konkreten musikalischen Kontext:

- `solo_character`
- `role_fitness`
- `prompt_fitness`
- `register_fitness`
- `articulation_clarity`
- `rhythmic_clarity`
- `harmonic_stability`
- `spectral_interest`
- `timbre_evolution`
- `mix_survivability`
- `partner_compatibility`
- `section_fitness`
- `novelty_without_instability`
- `technical_reliability`
- `total_score`
- `rejection_reasons`

### `SoundConstellation`

Eine bereits als Ensemble bewertete Kombination:

- Rollen und zugehörige Presets,
- Registeraufteilung,
- Patternfamilien,
- spektrale Slots,
- Transientenverteilung,
- Raumpositionen,
- geplante Beziehungen,
- bekannte Konflikte,
- validierte Sweet-Spot-Kombinationen,
- geeignete Formabschnitte,
- Qualitätswerte aus Solo-, Duo- und Ensembletests.

### `SuccessfulVariantPool`

Enthält ausschließlich Varianten, die alle Pflichtgates bestanden haben:

- validierte Einzelklänge,
- validierte Parameterbereiche,
- erfolgreiche Duo-Kombinationen,
- erfolgreiche Rhythmusgruppen,
- erfolgreiche Abschnittskonstellationen,
- Herkunft, Seed und Audio-Fingerprint,
- Messwerte und Hörbewertung,
- Einsatzhäufigkeit und letzte Verwendung.

## 4A.2 Synthesizer nicht nach Menge, sondern nach musikalischem Nutzen bewerten

Die Priorisierung erfolgt hierarchisch.

### Stufe A – Harte Eignung

Kandidat sofort ablehnen, wenn:

- Rolle oder Register nicht unterstützt werden,
- der Klang bei typischen Tonhöhen instabil oder praktisch leer ist,
- Pitch nicht zuverlässig folgt,
- Artikulation für die Rolle ungeeignet ist,
- notwendige Makros fehlen,
- CPU-Kosten das Abschnittsbudget überschreiten,
- technische Audio-Gates scheitern,
- der Synth nur durch extremen Pegel hörbar wird.

### Stufe B – Einzelklangqualität

Jeder SynthBasePreset wird mit standardisierten musikalischen Proben geprüft:

- einzelne tiefe, mittlere und hohe Note,
- kurze und lange Artikulation,
- drei Velocity-Stufen,
- Zwei- bis Vier-Noten-Phrase,
- Akkord oder Intervall, falls polyphon geeignet,
- Makrobewegung durch den sicheren Bereich.

Bewertet werden:

- charaktervolle Grundfarbe,
- Körper und Obertonstruktur,
- Transientenklarheit,
- kontrollierter Ausklang,
- Dynamikreaktion,
- spektrale Bewegung,
- Wiedererkennbarkeit,
- Abwesenheit störender Resonanzen,
- Hörbarkeit bei moderatem Pegel.

### Stufe C – Rollenqualität

Ein guter Klang ist nicht automatisch für jede Rolle geeignet:

- Bass braucht Substanz, Obertöne und klare Tonhöhen.
- Arpeggio braucht kurze Kontur, Pitch-Klarheit und kontrollierten Raum.
- Percussion braucht definierte Transienten und charaktervollen Körper.
- Pad und Drone brauchen Entwicklung ohne permanente Maskierung.
- Motivstimmen brauchen Wiedererkennbarkeit und Ausdruck.

### Stufe D – Partnerqualität

Die wichtigsten Kandidaten werden als Duo und Trio geprüft:

- Bass + Foundation,
- Bass + Low Pulse,
- Arpeggio + Pad,
- Arpeggio + Motiv,
- Percussion + Textur,
- Bass + Arpeggio + Percussion,
- vollständige Rhythmusgruppe + Harmonie.

Eine Kombination wird höher bewertet, wenn:

- Frequenzbereiche einander ergänzen,
- Transienten nicht gleichzeitig konkurrieren,
- rhythmische Muster komplementär sind,
- Klangfarben unterscheidbar bleiben,
- Rollenbeziehungen deutlich werden,
- die Gruppe schon ohne Mastering musikalisch funktioniert.

## 4A.3 Kontextabhängige Scorefunktion

Die Priorisierung darf nicht aus einem einzigen globalen Beliebtheitswert bestehen.

Empfohlene Grundform:

```text
PriorityScore =
    0.16 * role_fitness
  + 0.12 * prompt_fitness
  + 0.10 * solo_character
  + 0.10 * articulation_clarity
  + 0.10 * rhythmic_or_sustained_fitness
  + 0.10 * partner_compatibility
  + 0.08 * mix_survivability
  + 0.07 * harmonic_stability
  + 0.07 * timbre_evolution
  + 0.05 * section_fitness
  + 0.03 * technical_reliability
  + 0.02 * controlled_novelty
  - conflict_penalties
  - repetition_penalties
```

Die Gewichte werden pro Rolle angepasst. Bei Bass zählen Register, Harmoniestabilität und
Mix-Survivability stärker. Beim Arpeggio zählen Artikulation, Rhythmusklarheit und
Partnerkompatibilität stärker. Bei Texturen zählen Evolution und kontrollierte Neuheit.

## 4A.4 Auswahlstrategie: Qualität zuerst, Variation danach

Die Auswahl erfolgt in vier Schritten:

1. Alle ungeeigneten Kandidaten durch harte Regeln entfernen.
2. Verbleibende Kandidaten kontextabhängig bewerten.
3. Nur Kandidaten oberhalb eines Mindestwertes in den `SuccessfulVariantPool` übernehmen.
4. Innerhalb der besten Qualitätsgruppe seed-basiert auswählen.

Empfohlene Qualitätsgruppen:

- **S-Tier:** außergewöhnlich starke Kernklänge und Konstellationen
- **A-Tier:** zuverlässig musikalisch und mixfähig
- **B-Tier:** brauchbar für Variation oder Nebenrollen
- **C-Tier:** nur für gezielte Experimente
- **Rejected:** nicht für automatische Komposition zugelassen

Automatische Hauptrollen dürfen nur S- oder A-Tier verwenden. B-Tier ist für Nebenrollen,
Kontrast oder kontrollierte Variation erlaubt. C-Tier benötigt einen expliziten
Experimentmodus und darf keine tragende Rolle übernehmen.

## 4A.5 Erfolgreiche Permutation statt blinder Randomisierung

Für jeden validierten Preset werden Parameter in drei Klassen geteilt:

- **Identity parameters:** prägen die Klangidentität und bleiben eng begrenzt.
- **Expression parameters:** dürfen pro Phrase oder Abschnitt stärker variieren.
- **Risk parameters:** können den Klang zerstören und werden nur in validierten Bereichen
  verändert.

Eine Permutation ist nur zulässig, wenn:

- alle Parameter innerhalb validierter Sweet Spots bleiben,
- die resultierende Kombination technisch rendert,
- Rolle und Register weiterhin passen,
- Solo-Klangscore nicht unter den Mindestwert fällt,
- Partnerkompatibilität nicht wesentlich sinkt,
- keine verbotene Parameterkombination entsteht.

Beispiel Bass:

- Identität: Oszillatormischung, Grundfiltercharakter, Subanteil
- Ausdruck: Cutoff, Decay, Velocity, leichter Drive
- Risiko: Resonanz, extreme Fold-Stärke, zu tiefe Oktavierung

Beispiel Arpeggio:

- Identität: Klangfamilie, Transientenform, Grundregister
- Ausdruck: Gate, Helligkeit, Akzent, Oktavsprung, Raumanteil
- Risiko: zu langer Release, extremes Detuning, unkontrollierter Reverb

## 4A.6 Konstellationen vor Einzelkandidaten priorisieren

Das Modul wählt zuerst die wichtigste musikalische Konstellation des Tracks:

1. Rhythmisches Ambient: Bass + Arpeggio + Percussionanker
2. Drone Ambient: Foundation + Harmonie + bewegte Textur
3. Motivisches Ambient: Motiv + Antwortobjekt + harmonischer Träger

Danach werden ergänzende Rollen ausgewählt. So wird verhindert, dass sechs einzeln interessante
Synths zusammen einen chaotischen oder maskierten Mix ergeben.

Für rhythmische Tracks gilt:

- zuerst Basscharakter und Grooveanker bestimmen,
- dann kompatibles Arpeggio wählen,
- danach Percussion-Transienten ergänzen,
- anschließend Pad/Drone so wählen, dass die Rhythmusgruppe Platz behält,
- Texturen und Objekte zuletzt hinzufügen.

## 4A.7 Lernen aus Render- und Hörresultaten

Nach jedem validierten Render werden Ergebnisse in einer lokalen, versionierbaren
Erfolgsbibliothek gespeichert:

- Kontext und Promptmerkmale,
- verwendete Presets und Parameter,
- Solo-, Stem- und Mixmetriken,
- Konflikte,
- angenommene oder abgelehnte Qualitätsgates,
- Hörbewertung,
- Revisionen und deren Wirkung.

Wichtig:

- Eine Konstellation gilt erst nach bestandenen Audio- und Hörgates als erfolgreich.
- Reine Renderbarkeit ist kein Erfolg.
- Häufige Nutzung erzeugt einen Wiederholungsmalus.
- Erfolg in einem Kontext wird nicht blind auf andere Rollen oder Register übertragen.
- Manuelle positive Hörbewertungen besitzen höheres Gewicht als schwache Proxy-Metriken.

## 4A.8 Exploration ohne Qualitätsverlust

Damit die Maschine nicht immer dieselben drei Konstellationen verwendet:

- 70 % Auswahl aus S-Tier,
- 25 % aus A-Tier,
- 5 % kontrollierte Kombination aus A-/B-Tier,
- nie ungeprüfte Hauptrollen im normalen Produktionsmodus.

Diese Prozentsätze bedeuten keine blinde Zufallsauswahl. Innerhalb jedes Tiers wird erneut
nach Kontextscore, Wiederholungsmalus und Partnerkompatibilität gewichtet.

Neue Kandidaten durchlaufen einen separaten `audition`-Modus:

1. standardisierte Solo-Proben,
2. Rollenprobe,
3. Duo-Probe,
4. 20-Sekunden-Ensembleprobe,
5. Metrik- und Hörgate,
6. erst danach Aufnahme in den Erfolgspool.

## 4A.9 Vorgeschlagene Module und Dateien

- `au/selection/sound_priority.py`
- `au/selection/scoring.py`
- `au/selection/constellations.py`
- `au/selection/success_pool.py`
- `au/dsl/synth_preset.py`
- `au/dsl/sound_constellation.py`
- `au/analysis/sound_quality.py`
- `knowledge/synth_presets/`
- `knowledge/sound_constellations/`
- `tests/test_sound_priority.py`
- `tests/test_success_pool.py`
- `tests/test_constellation_selection.py`

`propose_candidates()` soll langfristig keine ungeordnete Stimmenliste mehr rotieren, sondern
die besten Ergebnisse der `SoundPriorityEngine` anfordern. `select_diverse_source_ensemble()`
wird zu einer Diversitätsbedingung innerhalb hochwertiger Kandidaten, nicht zu einer
Alternative zur Qualitätsbewertung.

## 4A.10 Tests

Verbindliche Tests:

- derselbe Kontext und Seed erzeugen dieselbe Auswahl,
- verschiedene Seeds wählen unterschiedliche Kandidaten aus demselben Erfolgspool,
- kein abgelehnter Kandidat erreicht eine Hauptrolle,
- S-Tier wird vor A- und B-Tier priorisiert,
- Wiederholungsmalus verhindert permanente Nutzung desselben Presets,
- Bassauswahl bevorzugt Bass-Sweet-Spots,
- Arpeggioauswahl bevorzugt klare kurze Artikulationen,
- Partnerkonflikte reduzieren den Score,
- hohe Einzelklangbewertung kann schlechte Ensemblekompatibilität nicht überstimmen,
- ein neuer Synth wird erst nach vollständiger Audition automatisch zugelassen,
- Parameterpermutationen bleiben in validierten Bereichen,
- fehlender Erfolgspool führt zu einer klaren Diagnose statt Zufallsauswahl.

## Gate 4A

- Jede automatisch verwendete Hauptstimme stammt aus einem validierten S- oder A-Tier-Preset.
- Für Bass, Arpeggio, Percussion, Harmonie und Foundation existieren jeweils mindestens fünf
  hochwertige Grundeinstellungen aus mindestens drei Synthfamilien.
- Mindestens zehn validierte Bass-/Arpeggio-/Percussion-Konstellationen bestehen Solo-, Duo-,
  Ensemble- und Hörtests.
- Zufällige Seeds verändern Kombination und Ausdruck, aber nicht die grundlegende
  Klangqualität.
- Die Auswahlmetadaten erklären nachvollziehbar, warum eine Konstellation bevorzugt wurde.
- Ein Blindvergleich bestätigt, dass priorisierte Konstellationen häufiger zu starken
  Einzelklängen und klareren Arrangements führen als die bisherige Zufallsauswahl.

---

# STUFE 4B – Selbstlernender Learn/Train-Modus mit aktivem Nutzerfeedback

## Ziel

Die Klangpriorisierung erhält einen interaktiven Learn/Train-Modus. Dieser Modus baut über
viele Hörentscheidungen ein persönliches Geschmacksmodell auf, ohne technische Klangqualität
mit subjektiver Vorliebe zu verwechseln.

Der Modus:

- erzeugt gezielt informative Klangbeispiele,
- präsentiert sie im Studio mit direkter 1–10-Klickbewertung,
- speichert, was bereits gehört und bewertet wurde,
- vermeidet unnötige Wiederholungen,
- erkennt neue Synths, Presets, Parameterbereiche und Konstellationen,
- stellt neue Optionen ergänzend zu bereits bekannten Referenzen vor,
- lernt sowohl aus absoluten Bewertungen als auch aus relativen Präferenzen,
- aktualisiert die Priorisierung kontrolliert und nachvollziehbar,
- erhält ausreichend Vielfalt und Exploration.

Das Ergebnis sind zwei getrennte Bewertungsebenen:

```text
ObjectiveQualityScore
  = technische Qualität + Rollenfitness + Mixfähigkeit + musikalische Stabilität

PersonalTasteScore
  = gelernte Präferenz des Nutzers für Klangfarbe, Artikulation, Bewegung,
    Rhythmus, Raum, Dichte und Konstellationen

FinalPriorityScore
  = harte Qualitätsgates
  × kontextabhängige objektive Bewertung
  × vorsichtig gewichtete persönliche Präferenz
  × Diversitäts- und Neuheitskorrektur
```

Ein hoher persönlicher Wert darf technische Fehler nicht legitimieren. Ein technisch
perfekter, aber persönlich langweiliger Klang darf dagegen zugunsten eines ebenfalls gültigen,
stärker bevorzugten Klangs zurückgestuft werden.

## 4B.1 Betriebsarten

### `Learn Solo`

Bewertet einzelne SynthBasePresets in standardisierten musikalischen Proben:

- einzelne Note,
- kurze Phrase,
- lange Geste,
- drei Register,
- zwei Artikulationen,
- kontrollierte Makrobewegung.

Ziel: persönliche Vorlieben für Grundfarbe, Transienten, Helligkeit, Bewegung und Register
lernen.

### `Learn Role`

Bewertet einen Klang in einer konkreten Rolle:

- Bass,
- Arpeggio,
- Percussion,
- Foundation,
- Harmonie,
- Motiv,
- Textur,
- Objekt.

Ziel: erkennen, dass derselbe Synth als Pad gefallen, als Bass aber ungeeignet sein kann.

### `Learn Pair`

Präsentiert A/B- oder Duo-Beispiele:

- Bass A gegen Bass B im gleichen Groove,
- Arpeggio A gegen Arpeggio B über derselben Harmonie,
- Pad A mit Bass gegenüber Pad B mit demselben Bass,
- zwei Raum-/Artikulationsvarianten desselben Presets.

Ziel: relative Präferenzen zuverlässiger erfassen als nur durch isolierte Absolutwerte.

### `Learn Constellation`

Bewertet vollständige musikalische Kombinationen:

- Bass + Arpeggio,
- Bass + Percussion,
- Arpeggio + Pad,
- Rhythmusgruppe,
- Rhythmusgruppe + Harmonie,
- 12–20 Sekunden vollständiges Mini-Arrangement.

Ziel: Ensemblequalität und persönliche Arrangementvorlieben lernen.

### `Train New Options`

Wird automatisch angeboten, wenn neue oder geänderte Optionen erkannt wurden:

- neue Synthmodule,
- neue Manifestversionen,
- neue Presets,
- neue sichere Parameterbereiche,
- neue Effektketten,
- neue Patternfamilien,
- neue Klangkonstellationen.

Der Modus zeigt bevorzugt neue Optionen neben bekannten Referenzankern. Dadurch kann der
Nutzer eine neue Stimme relativ zu bereits bewerteten Favoriten einordnen.

## 4B.2 Bewertungsoberfläche

Jedes Beispiel erhält eine klare 1–10-Skala:

- **1:** unbrauchbar / unangenehm
- **2:** sehr schwach
- **3:** schwach
- **4:** eher uninteressant
- **5:** neutral / brauchbar
- **6:** ordentlich
- **7:** gut
- **8:** sehr gut
- **9:** außergewöhnlich
- **10:** Favorit / unbedingt häufiger verwenden

Die Skala muss mit einem Klick bedienbar sein. Tastaturkürzel `1` bis `0` dürfen ergänzend
verwendet werden, wobei `0` für 10 steht.

Zusätzliche optionale Aktionen:

- **Nochmal hören**
- **A/B vergleichen**
- **Überspringen**
- **Technischer Fehler**
- **Zu ähnlich zu vorher**
- **Als Referenz merken**
- **Nie automatisch verwenden**
- **Mehr Varianten davon**
- **Weniger Varianten davon**

Eine 1–10-Bewertung bleibt die primäre Pflichtinteraktion. Zusatzlabels sind optional und
helfen bei der Erklärung der Bewertung.

## 4B.3 Bewertungsdatensatz

Jede Nutzerentscheidung wird als unveränderliches `RatingEvent` gespeichert:

- `rating_id`
- `user_profile_id`
- `timestamp`
- `session_id`
- `presentation_id`
- `candidate_id`
- `audio_fingerprint`
- `module_id` und Modulversion
- `preset_id` und Presetversion
- vollständiger Parameterfingerprint
- Rolle
- Abschnittstyp
- Pattern- und Artikulationsprofil
- Partnerkonstellation
- Prompt-/Intent-Kontext
- Wiedergabereihenfolge
- Lautheitsnormalisierung
- Bewertung 1–10
- optionale Labels
- Anzahl der Wiederholungen
- Hörzeit vor der Bewertung
- Modellversion, welche das Beispiel ausgewählt hat

Bewertungen werden nicht überschrieben. Eine spätere Neubewertung erzeugt ein neues Event.
So bleiben Geschmacksänderungen und Modellfehler nachvollziehbar.

## 4B.4 Präsentationsgedächtnis

Das System benötigt ein dauerhaftes `PresentationMemory`.

Es speichert:

- welche exakte Audiodatei gezeigt wurde,
- welche Kandidatenkonfiguration dahinterstand,
- wann und wie oft sie präsentiert wurde,
- in welchem Kontext sie gezeigt wurde,
- ob sie bewertet, übersprungen oder abgebrochen wurde,
- welche Vergleichspartner gleichzeitig gezeigt wurden,
- ob das Beispiel eine neue Option oder ein Kontrollbeispiel war,
- ob die Nutzerbewertung stabil oder widersprüchlich war.

### Identität eines Beispiels

Mehrere Fingerprints unterscheiden verschiedene Ebenen:

- `module_fingerprint`: Synth und Version
- `preset_fingerprint`: Grundeinstellungen
- `parameter_fingerprint`: konkrete Parameter
- `pattern_fingerprint`: Events und Artikulation
- `constellation_fingerprint`: Partner und Rollen
- `audio_fingerprint`: tatsächlich gerendertes Audio

Dadurch erkennt das System sowohl exakte Wiederholungen als auch nur leicht veränderte
Varianten.

### Wiederholungsregeln

- Exakt identisches Audio wird normalerweise nicht erneut gezeigt.
- Sehr ähnliche Varianten erhalten einen starken Präsentationsmalus.
- Kontrollwiederholungen sind selten erlaubt, um Bewertungsstabilität zu messen.
- Favoriten dürfen als bekannte Referenzanker wiederkehren.
- Nach einer wesentlichen Modell-, Synth- oder Rendereränderung kann eine Neubewertung
  angefordert werden.
- Übersprungene Beispiele dürfen später erneut erscheinen, aber nicht in derselben Sitzung.

## 4B.5 Erkennung neuer Optionen

Ein `CatalogChangeDetector` vergleicht den aktuellen Katalog mit dem letzten bekannten
Trainingsstand.

Er erkennt:

- hinzugefügte und entfernte Module,
- Manifest- und Implementierungsänderungen,
- neue oder geänderte Makros,
- neue Presets und Sweet Spots,
- geänderte Audio-Fingerprints bei identischer Konfiguration,
- neue Rollenfreigaben,
- neue Pattern und Artikulationsprofile,
- neue kompatible Prozessoren,
- neue validierte Konstellationen.

Jede Änderung erhält eine Priorität:

- **hoch:** neue Synthfamilie, starke Implementierungsänderung oder neue Kernrolle
- **mittel:** neues Preset, neue Artikulation oder neue Partnerkonstellation
- **niedrig:** kleine Parameterbereichs- oder Metadatenänderung

Neue Optionen werden nicht automatisch als gut eingestuft. Sie gelangen zuerst in eine
`unrated_new_options`-Queue, bestehen technische Vorprüfungen und werden anschließend durch
aktives Lernen gezielt vorgestellt.

## 4B.6 Aktives Lernen: Welche Beispiele werden als Nächstes gezeigt?

Der Modus soll nicht einfach zufällig Kandidaten abspielen. Eine
`ActiveLearningSelector`-Komponente berechnet für jedes mögliche Beispiel einen
`PresentationValue`.

Empfohlene Faktoren:

```text
PresentationValue =
    model_uncertainty
  + expected_information_gain
  + new_option_bonus
  + role_coverage_gap
  + constellation_coverage_gap
  + disagreement_between_quality_and_taste
  + boundary_candidate_bonus
  + diversity_bonus
  - similarity_to_recent_examples
  - presentation_frequency_penalty
  - listener_fatigue_penalty
```

Bevorzugt werden:

- neue Optionen,
- Kandidaten, bei denen das Geschmacksmodell unsicher ist,
- Kandidaten nahe der Grenze zwischen bevorzugt und abgelehnt,
- Gegenbeispiele, welche aktuelle Modellannahmen prüfen,
- unterrepräsentierte Rollen und Synthfamilien,
- Kombinationen mit hoher objektiver Qualität, aber unbekannter persönlicher Eignung,
- Kombinationen, bei denen objektive und persönliche Bewertung auseinanderliegen.

## 4B.7 Sitzungsaufbau

Eine Trainingssitzung soll kurz und fokussiert sein.

Empfohlene Standardstruktur für 12 Beispiele:

1. bekannter Referenzanker,
2. neuer informativer Kandidat,
3. kontrastierender Kandidat,
4. relative A/B-Frage,
5. neue Option,
6. bekannte hochwertige Konstellation,
7. unsicherer Grenzkandidat,
8. neue Konstellation,
9. Diversitätsbeispiel außerhalb der bisherigen Favoriten,
10. verkürzte Kontrollwiederholung,
11. bestes bisher unbekanntes Beispiel,
12. Abschlussvergleich der zwei stärksten Kandidaten.

Nach sechs Beispielen wird eine Pause angeboten. Die Sitzung endet automatisch, wenn
Bewertungszeit oder Übersprungrate auf Hörermüdung hindeuten.

## 4B.8 Trennung objektiver Qualität und persönlicher Präferenz

### Objektives Modell

Wird trainiert aus:

- technischen Audio-Gates,
- Pitch- und Timingtreue,
- Rollenfitness,
- Masking,
- Dynamik,
- Stabilität,
- Ensemblekompatibilität,
- kuratierten Qualitätsregeln,
- validierten Hörtests zur handwerklichen Qualität.

Es entscheidet, ob ein Kandidat überhaupt automatisch zugelassen werden darf.

### Persönliches Geschmacksmodell

Wird ausschließlich aus Nutzerbewertungen und freiwilligen Präferenzlabels trainiert.

Es lernt unter anderem:

- bevorzugte Synthfamilien,
- Helligkeit und Rauheit,
- harmonisch versus inharmonisch,
- kurze versus weiche Transienten,
- statisch versus stark bewegt,
- trocken versus räumlich,
- einfache versus komplexe Patterns,
- Basscharakter,
- Arpeggioart,
- bevorzugte Partnerkombinationen,
- Präferenzen je Prompt, Rolle und Abschnitt.

### Kombinationsregel

- Technisch abgelehnte Kandidaten bleiben gesperrt.
- Persönlicher Geschmack sortiert nur innerhalb technisch gültiger Kandidaten.
- Eine kleine kontrollierte Exploration bleibt erhalten.
- Das Modell darf keine negative Bewertung auf eine ganze Synthfamilie übertragen, wenn nur
  ein einzelnes schlechtes Preset bewertet wurde.
- Kontextbewertungen haben Vorrang vor globalen Bewertungen.

## 4B.9 Lernmodell

Die erste Version soll bewusst robust und erklärbar bleiben:

1. normalisierte Merkmale aus Preset, Klangmetrik, Rolle und Kontext,
2. gewichtete Regression für erwartete 1–10-Bewertung,
3. Unsicherheitsschätzung je Kandidat,
4. rollen- und kontextspezifische Teilmodelle,
5. paarweise Präferenzableitung aus A/B-Vergleichen,
6. zeitlich gewichtete Aktualisierung bei veränderten Vorlieben.

Erst bei ausreichender Datenmenge dürfen komplexere Modelle eingesetzt werden. Ein
kompliziertes Modell ohne genügend Bewertungen wäre Scheingenauigkeit.

### Datenmengen

- unter 30 Bewertungen: Cold Start, breite Exploration
- 30–100 Bewertungen: erste rollenbezogene Präferenzen
- 100–300 Bewertungen: Konstellations- und Kontextlernen
- über 300 Bewertungen: feinere Interaktionen und zeitliche Präferenzentwicklung

## 4B.10 Schutz vor Geschmacksblase und Modellverengung

Damit nicht nur immer ähnlich klingende Favoriten gezeigt und produziert werden:

- mindestens 15 % der Trainingsbeispiele stammen aus diversen, aber technisch guten
  Gegenbeispielen,
- jede Kernrolle und jede relevante Synthfamilie erhält Mindestabdeckung,
- neue Optionen erhalten zeitlich begrenzten Erkundungsbonus,
- Ähnlichkeitscluster begrenzen die Häufigkeit nahezu identischer Presets,
- häufig verwendete Favoriten erhalten einen Sättigungsmalus,
- ein Teil der Bewertungen wird als verborgenes Validierungsset zurückgehalten,
- Modellverbesserung wird gegen eine einfache Baseline geprüft,
- Nutzer kann Exploration zwischen konservativ, ausgewogen und neugierig einstellen.

## 4B.11 Training, Validierung und Modellversionierung

Training darf Bewertungen nicht unkontrolliert sofort in Produktionsentscheidungen
übernehmen.

Ablauf:

1. neue RatingEvents speichern,
2. Datensatz validieren,
3. Train-/Validierungsaufteilung nach Zeit und Kandidatengruppe,
4. neues Geschmacksmodell trainieren,
5. gegen bisheriges Modell und einfache Baseline vergleichen,
6. Kalibrierung und Rankingqualität prüfen,
7. nur bei Verbesserung als `candidate_model` speichern,
8. Nutzer kann das Modell aktivieren oder automatisch freigeben lassen,
9. vorherige Modelle bleiben wiederherstellbar.

Zu speichern:

- Modellversion,
- Trainingszeitpunkt,
- verwendete RatingEvent-IDs,
- Featureversion,
- Katalogversion,
- Validierungsmetriken,
- bekannte Schwächen,
- Aktivierungsstatus.

## 4B.12 Studio-UI

Neue Studioansicht `Learn / Train`:

- große Play-/Pause-Schaltfläche,
- sichtbare Rolle und Vergleichsmodus,
- 1–10-Klickleiste,
- optional A/B-Umschaltung,
- Fortschritt der Sitzung,
- Kennzeichnung „neu“, „Referenz“, „Kontrolle“ oder „unsicher“,
- kurze Erklärung, warum dieses Beispiel gezeigt wird,
- Anzeige bereits gelernter Präferenzen,
- Abdeckung nach Rolle und Synthfamilie,
- neue noch unbewertete Optionen,
- Modellunsicherheit,
- Verlauf der Modellversionen,
- Lösch-, Export- und Zurücksetzfunktion für persönliche Bewertungen.

Synthname und Parameter können im Blindmodus zunächst verborgen bleiben, damit visuelle
Erwartungen die Bewertung nicht beeinflussen. Nach der Bewertung dürfen Details eingeblendet
werden.

## 4B.13 Datenschutz und Kontrolle

- Bewertungen und Modelle bleiben standardmäßig lokal.
- Nutzerprofile werden getrennt gespeichert.
- Export und Import erfolgen in einem dokumentierten Format.
- Einzelne Bewertungen, Sitzungen oder das gesamte Geschmacksmodell können gelöscht werden.
- Produktionsentscheidungen zeigen objektiven und persönlichen Score getrennt an.
- Der Nutzer kann persönliche Priorisierung jederzeit deaktivieren.
- Kein Rating wird stillschweigend aus Klickdauer oder Abbruch abgeleitet; solche Signale
  dienen höchstens als Unsicherheitsindikator.

## 4B.14 Vorgeschlagene Module und Dateien

- `au/learning/rating.py`
- `au/learning/presentation_memory.py`
- `au/learning/catalog_changes.py`
- `au/learning/active_selector.py`
- `au/learning/taste_model.py`
- `au/learning/trainer.py`
- `au/learning/model_registry.py`
- `au/studio/learning_api.py`
- `knowledge/ratings/`
- `knowledge/presentation_memory/`
- `knowledge/taste_models/`
- `tests/test_rating_store.py`
- `tests/test_presentation_memory.py`
- `tests/test_catalog_change_detector.py`
- `tests/test_active_learning.py`
- `tests/test_taste_model.py`

## 4B.15 Tests

Verbindliche Tests:

- eine Bewertung von 1 bis 10 wird vollständig und unveränderlich gespeichert,
- exaktes Audio wird nicht versehentlich erneut präsentiert,
- ähnliche Varianten erhalten einen Wiederholungsmalus,
- neue Module und Presets werden erkannt,
- technische Fehler können nicht durch hohe Geschmackswerte freigegeben werden,
- persönlicher Geschmack verändert das Ranking technisch gültiger Kandidaten,
- neue Optionen erhalten Erkundungspriorität,
- unterrepräsentierte Rollen werden aktiv nachtrainiert,
- verschiedene Nutzerprofile bleiben vollständig getrennt,
- identische Daten und Modellversionen erzeugen identische Vorhersagen,
- Modellupdate wird bei schlechterer Validierung nicht aktiviert,
- Referenzanker und Kontrollwiederholungen messen Bewertungsstabilität,
- der Selector verhindert zwölf nahezu identische Beispiele in einer Sitzung,
- Löschen und Exportieren persönlicher Daten funktionieren vollständig.

## Gate 4B

- Die Studiooberfläche ermöglicht eine vollständige 12-Beispiele-Sitzung ohne
  Terminalinteraktion.
- Jede Bewertung ist mit Audio-, Kandidaten-, Kontext- und Modellfingerprint verknüpft.
- Das Präsentationsgedächtnis verhindert unnötige Wiederholungen über Sitzungen hinweg.
- Neue Synths, Presets und Konstellationen erscheinen automatisch in der Trainingsqueue.
- Objektive Qualität und persönliche Präferenz werden separat gespeichert, trainiert und
  angezeigt.
- Nach mindestens 100 Bewertungen sagt das Modell persönliche Rankings deutlich besser als
  eine Zufalls- oder globale Durchschnittsbaseline voraus.
- Mindestens 15 % kontrollierte Exploration verhindern eine enge Geschmacksblase.
- Produktionsauswahl nutzt persönliche Präferenz nur innerhalb technisch validierter
  Kandidaten.
- Nutzer kann jederzeit nachvollziehen, warum ein Beispiel gezeigt und warum ein Klang
  priorisiert wurde.

---

# STUFE 4C – Referenzmuster als ganzheitliche Produktionssprache

## Ziel

Die 50 beschriebenen Klangmomente werden als kuratierte `SonicPattern`-Bibliothek genutzt.
Sie sind keine bloße Ideensammlung und keine ungeprüften Presets, sondern beschreiben eine
musikalische Geste aus Quelle, Bewegung, Artikulation, Raum und dramaturgischer Funktion.

Die Bibliothek ist nach fünf Familien organisiert:

- Oszillator-, Sync- und Modulationsgesten: Hard Sync, Supersaw Drift, FM-Pluck, PWM-Bass,
  Ringmod-Arpeggio, Glide und Audio-Rate-Pitch.
- Filter- und Resonanzgesten: Filter Ping, Formantbewegung, Acid Accent, Comb-Pluck,
  Tracking-Notch und resonanter Unterwasser-Bass.
- Raum-, Delay- und Hallgesten: Shimmer, ungerades Ping-Pong, Freeze, Gated Reverb,
  Tape-Drift, Reverse Bloom, Haas und Multi-Tap.
- Dynamik-, Sättigungs- und Lo-Fi-Gesten: Sidechain-Pump, Tape-Wave-Crush, Vinyl Flutter,
  Bitcrush, Unisono-Wall, Transient-Bass, Rhythm-Gate und Multiband-Platzierung.
- Komplexe Modulationsgesten: Sample-and-Hold, Shepherd-Rise, Verstärkeratem,
  selektives Legato, invertierte Hüllkurve, Chorus-Drift, Micro-Delay und Wavetable-Rise.

## Produktionsregeln

1. Jede Geste erhält eine Rolle, einen Abschnittsfit, erforderliche Module und einen Risikowert.
2. Eine Geste wird zuerst als Einzelklang, dann als Rollenpaar und erst danach im Arrangement
   validiert.
3. Hohe Risiken wie Selbstoszillation, starkes Feedback, Audio-Rate-FM und extreme
   Downsampling-Effekte werden nur auf Höhepunkt-, Übergangs- oder Kontrastrollen verwendet.
4. Niedrigrisiko-Gesten wie Supersaw Drift, Amplifier Breath, Tape Drift und Multiband-Platz
   dürfen Foundation, Drone und Outro tragen.
5. Jede Produktion benötigt mindestens eine klare Körpergeste, eine Bewegungs-/Atemgeste,
   eine artikulierte Rhythmusgeste und eine räumliche Geste.
6. Keine zwei benachbarten Abschnitte verwenden dieselbe dominante Geste ohne Transformation.
7. Rhythmusrollen bevorzugen Gummi-Bass, FM-Pluck, Acid Accent, Odd Ping-Pong,
   Transient-Bass, Rhythmic Gate und Legato-Reset nur in passenden Dichten.
8. Der Weltenbrand-Aufbau ist eine Formgeste über acht Takte, kein Dauerpreset.

## Priorisierung

`SoundPriorityEngine` erhält pro Kandidat zusätzlich:

- `pattern_family`,
- `function`,
- `section_fit`,
- `risk`,
- `requires`,
- bereits validierte Nutzer- und Ensemblebewertungen.

Eine Geste wird bevorzugt, wenn sie die aktuelle musikalische Funktion erfüllt, eine
unterrepräsentierte Klangdimension ergänzt und mit den bereits gewählten Stimmen kompatibel
ist. Zufall darf nur erfolgreiche Gesten innerhalb derselben Qualitäts- und Risikoklasse
permutieren.

## Abnahme

Ein 60-Sekunden-Track besteht dieses Gate nur, wenn mindestens vier unterschiedliche Gesten
hörbar nachweisbar sind, darunter:

- eine Bass- oder Körpergeste,
- eine melodisch/arithmetische Bewegungs- oder Arpeggiogeste,
- eine Transienten- oder Groovegeste,
- eine Raum-/Nachgeste.

Mindestens eine Geste muss über mehrere Abschnitte transformiert werden. Beschreibungen dürfen
nicht als wörtliche klangliche Behauptung gelten: Nur gerenderte und gehörte Ergebnisse werden
in den `SuccessfulVariantPool` aufgenommen.

---

# STUFE 5 – Musikalische Arpeggio-Engine

## Ziel

Der Arpeggiator spielt erkennbare, harmonisch sinnvolle Figuren statt zufälliger Einzelnoten.

## `ArpeggioPlan`

Enthält:

- Akkordstufen und Voicing,
- Laufrichtung: up, down, up-down, outside-in, pendulum,
- Oktavbereich,
- Rhythm Pattern,
- Gate Pattern,
- Accent Pattern,
- Wiederholungslänge,
- Mutationstakt,
- Motivverknüpfung,
- Register und Klangfarbe je Abschnitt.

## Kompositionsregeln

1. Noten stammen primär aus dem aktiven Akkord.
2. Skalenfremde Durchgangstöne sind selten und lösen sich hörbar auf.
3. Voice Leading minimiert unnötige Sprünge zwischen Akkordwechseln.
4. Eine Grundfigur bleibt mindestens zwei Phrasen erkennbar.
5. Variationen ändern jeweils nur eine oder zwei Dimensionen.
6. Pausen und ausgelassene Steps sind Bestandteil der Figur.
7. Arpeggio und Hauptmotiv dürfen sich ergänzen, aber nicht dauerhaft verdoppeln.
8. Der Arpeggiator wechselt zwischen Vordergrund, Mittelgrund und fast subliminaler Rolle.

## Klangdesign

Validierte Charaktere:

- weicher analoger Puls,
- Karplus-/Pluck-Arpeggio,
- gläserne FM-Figur,
- Marimba/Modal-Resonanz,
- gefiltertes Noise-/Click-Arpeggio für abstrakte Passagen.

## Gate 5

- Im Solo ist eine wiederkehrende Figur nach spätestens acht Sekunden erkennbar.
- Im Mix bleibt mindestens der Hauptakzent der Figur hörbar.
- Akkordwechsel verändern das Tonmaterial kontrolliert.
- Arpeggio-Variation ist erkennbar, ohne die Identität zu verlieren.

---

# STUFE 6 – Perkussion und rhythmische Textur

## Ziel

Rhythmus wird fühlbar, ohne Ambient in einen generischen Drumloop zu verwandeln.

## Rollen

- `low_pulse`: tiefer, weicher Körperimpuls
- `mid_click`: Holz, Rim, kurzer Resonator
- `high_tick`: leiser Tick, Noise oder metallischer Partikel
- `ghost_texture`: sehr leise Zwischenbewegung
- `transition_hit`: markiert Formwechsel
- `reverse_breath`: leitet Akzente oder neue Abschnitte ein

## Regeln

- Percussion verwendet denselben GroovePlan.
- Mindestens eine Rolle trägt den Puls, eine andere erzeugt Synkope.
- Ghost Notes sind pegelbegrenzt und dürfen keine Hauptakzente ersetzen.
- Fills treten vor Abschnittswechseln auf, nicht zufällig.
- Dichte steigt nicht nur durch mehr Hits, sondern auch durch kürzere Abstände,
  hellere Klangfarbe und größere räumliche Nähe.
- Im Outro werden zuerst hohe und mittlere Impulse entfernt; tiefer Puls und Atem bleiben.

## Gate 6

- Der Puls ist im Mix fühlbar, selbst wenn die Percussion leise ist.
- Keine perkussive Rolle klingt wie unbehandeltes weißes Rauschen.
- Übergänge werden durch musikalisch vorbereitete Events markiert.

---

# STUFE 7 – Abschnittsdramaturgie und Arrangement

## Ziel

Bass, Arpeggio und Rhythmus formen den Track und erscheinen nicht nur am Höhepunkt.

## Empfohlenes 60-Sekunden-Modell

### Intro – 0–12 s

- Foundation oder Drone
- vereinzelte High Ticks oder Atemimpulse
- Bassmotiv nur fragmentarisch ankündigen
- Arpeggio als zwei bis drei entfernte Noten andeuten

### Build – 12–28 s

- Bassphrase vollständig einführen
- klaren, aber weichen Puls etablieren
- Arpeggio mit reduzierter Notenzahl beginnen
- Pad auf Bassakzente reagieren lassen

### Peak – 28–48 s

- vollständiges Bass-/Arpeggio-Zusammenspiel
- zusätzliche Synkope oder Polymeter
- Motiv und Arpeggio antworten einander
- Percussion markiert Phrasengrenzen
- höchste spektrale und rhythmische Aktivität

### Outro – 48–60 s

- Arpeggio fragmentieren oder Tempo halbieren
- Bass auf Pedalton oder Schlussfigur reduzieren
- Rhythmuselemente nacheinander entfernen
- ein letztes Motiv- oder Resonanzereignis schließt die Form

## Rollenrelationen

Mindestens fünf hörbare Relationen:

- Bassakzent → Low Pulse
- Bassnotenwechsel → Pad-Filterbewegung
- Akkordwechsel → Arpeggio-Voicingwechsel
- Arpeggio-Phrasenende → resonante Antwort
- Percussion-Fill → Abschnittswechsel
- Motivpause → Arpeggio tritt kurz in den Vordergrund
- steigende Dichte → kürzere Bassgates und hellere Arpeggio-Artikulation

## Gate 7

- Die vier Abschnitte sind im Blindtest anhand von Rhythmus und Orchestrierung unterscheidbar.
- Bass und Arpeggio entwickeln sich über den Track.
- Der Peak ist nicht nur lauter, sondern rhythmisch und harmonisch dichter.

---

# STUFE 8 – Stem-Architektur und Mix

## Ziel

Jede musikalische Funktion bleibt messbar, mischbar und hörbar.

## Neue Stems

- `foundation`
- `bass`
- `harmony`
- `arpeggio_motif`
- `percussion`
- `texture`
- `objects`
- optional `space_fx`

Verbindliche Zuordnung:

- `bass_sequence` → `bass`
- `subharmonic_pulse` → je nach Funktion `bass` oder `foundation`
- `arpeggiator` → `arpeggio_motif`
- `signal_motif` → `arpeggio_motif`
- `subtle_percussive_background` → `percussion`

## Mixregeln

### Bass/Foundation

- unter 120 Hz überwiegend mono,
- Foundation dynamisch absenken, wenn Bassnoten einsetzen,
- Bass-Obertöne erhalten, nicht nur Subenergie,
- gemeinsame Energiegrenze für Foundation + Bass.

### Arpeggio/Harmonie

- Harmonie bei Arpeggio-Onsets leicht ducken oder spektral ausweichen,
- Arpeggio nicht durch überlangen Reverb verschmieren,
- Pre-Delay und kurze Early Reflections für Kontur,
- Stereo-Bewegung langsam und phasensicher.

### Percussion/Textur

- Transienten vor breitbandiger Textur schützen,
- hohe Textur bei wichtigen Ticks kurz ausdünnen,
- Percussion-Reverb getrennt vom Pad-Reverb steuern.

### Gesamtmix

- Stem-Ziele nicht nur als statische LUFS-Werte, sondern abschnittsweise,
- True Peak höchstens −1 dBTP,
- Zielbereich zunächst −18 bis −14 LUFS,
- Limiter darf Groove-Transienten nicht einebnen,
- A/B-Mix mit Rhythmusgruppe ±3 dB automatisch erzeugen.

## Gate 8

- Jede Kernrolle ist im Solo, in der Rhythmusgruppe und im Gesamtmix hörbar.
- Kein Kernstem liegt mehr als 12 dB unter seinem geplanten Ziel.
- Bass und Percussion bleiben mono-kompatibel.
- Arpeggio-Onsets bleiben nach Reverb und Mastering erkennbar.

---

# STUFE 9 – Musikalische Qualitätskritiker

## Ziel

Ein technisch gültiger, aber musikalisch langweiliger Track darf nicht mehr akzeptiert werden.

## Neue Metriken

### Rollenpräsenz

- aktive Zeit pro Rolle,
- Stem-LUFS pro Abschnitt,
- Onsetzahl pro Rolle,
- hörbarer Beitrag zum Mix durch Mute-Differenz.

### Groove

- Onset-Stabilität relativ zum GroovePlan,
- Accent-Korrelation,
- Phrasengrenzen-Treffer,
- Syncopation-Verteilung,
- Wiederholungs- und Variationsabstand.

### Bass

- Tonhöhenübereinstimmung mit ChordTimeline,
- Root/Fifth/Passing-Tone-Verteilung,
- Subenergie und Obertonenergie,
- Masking mit Foundation,
- Bassphrasen-Wiederkehr.

### Arpeggio

- Akkordtonquote,
- Registerspanne,
- Patternwiederkehr,
- kontrollierte Variationsdistanz,
- Onset-Erkennbarkeit im Mix.

### Form und Monotonie

- rhythmische Dichte pro Abschnitt,
- Kontrast benachbarter Abschnitte,
- maximale Zeit ohne neues Ereignis oder hörbare Veränderung,
- Veränderung von Register, Timbre, Artikulation und Raum,
- Anteil identischer Patternwiederholungen ohne Variation.

## Harte Ablehnungsregeln

Ein rhythmisch angeforderter Track wird abgelehnt, wenn:

- Bass, Arpeggiator oder Rhythmusrolle im Blueprint fehlen,
- ein Pflichtstem praktisch leer ist,
- Arpeggio oder Bass überwiegend Poisson statt geplantem Pattern verwenden,
- der Onsetfehler gegenüber dem GroovePlan zu hoch ist,
- Bass und Foundation dauerhaft maskiert sind,
- zwischen Build und Peak kein messbarer Rhythmuskontrast besteht,
- ein einzelnes statisches Pad den Mix dominiert,
- der Blind-Hörtest keinen stabilen Puls oder keine Bassbewegung erkennt.

## Gate 9

- Qualitätsbericht nennt konkrete Zeitstellen und betroffene Rollen.
- Revision verändert nur die fehlerhafte Ebene: Auswahl, Pattern, Pegel, Arrangement oder Mix.
- Nach maximal drei Revisionen wird entweder akzeptiert oder mit nachvollziehbarem Grund
  verworfen.

---

# STUFE 10 – Hörtests und Referenzproduktionen

## Testmatrix

Mindestens drei Charaktere:

1. warm, organisch, langsam pulsierend,
2. kalt, gläsern, polymetrisch,
3. dunkel, bassbetont, sequenziert.

Je Charakter:

- drei Seeds,
- 20-Sekunden-Ensembleprobe,
- 60-Sekunden-Referenztrack,
- Solo-Stems,
- Rhythmusgruppenmix,
- Finalmix,
- Baseline-A/B.

## Hörfragen

Ohne Metadaten beantworten:

1. Ist innerhalb von acht Sekunden eine zeitliche Ordnung erkennbar?
2. Ist eine Bassbewegung hörbar?
3. Ist das Arpeggio als Figur erkennbar?
4. Reagieren andere Stimmen auf die Rhythmusgruppe?
5. Ändert sich der Groove zwischen den Abschnitten?
6. Gibt es Pausen, Vorhalte und Auflösungen?
7. Wirkt der Peak musikalisch dichter statt nur lauter?
8. Bleibt das Stück atmosphärisch?
9. Ist nach 60 Sekunden ein Motiv oder Pattern erinnerbar?
10. Klingt jeder der drei Seeds wie ein anderer Track?

## Gate 10

- Mindestens 80 % der Hörfragen werden je Track positiv beantwortet.
- Alle Pflichtrollen werden von mindestens zwei Hörern oder in zwei getrennten
  Blinddurchgängen erkannt.
- Plan-4-Version schlägt die Baseline in Puls, Bassklarheit, Arpeggio-Erkennbarkeit,
  Form, Klangvielfalt und Gesamtqualität.

---

## 4. Konkrete Implementierungsreihenfolge

### Phase A – Sofort hörbar machen

1. Rhythmische Rollen im Blueprint garantieren.
2. Slotlimit durch Pflichtrollenreservierung ersetzen.
3. Pattern-Überschreibung in `compose_track()` entfernen.
4. Arpeggio, Bass und Percussion den richtigen PatternKind behalten lassen.
5. eigene Stems und Pegelmessungen hinzufügen.
6. einen 20-Sekunden-Rhythmusgruppen-Test rendern.

**Erwarteter Nutzen:** Die heute fehlenden Rollen werden erstmals zuverlässig hörbar.

### Phase B – Musikalisch machen

7. `SynthBasePreset`, Scoremodell und `SuccessfulVariantPool` implementieren.
8. vorhandene Synths durch standardisierte Solo- und Rollenproben bewerten.
9. erste hochwertige Bass-/Arpeggio-/Percussion-Konstellationen validieren.
10. `propose_candidates()` an die `SoundPriorityEngine` anbinden.
11. RatingStore, PresentationMemory und CatalogChangeDetector implementieren.
12. Learn/Train-UI mit 1–10-Klickbewertung implementieren.
13. ActiveLearningSelector und erklärbares erstes Geschmacksmodell implementieren.
14. GroovePlan implementieren.
15. BassPlan und ArpeggioPlan implementieren.
16. interne Zufallstrigger aus event-gesteuerten Stimmen entfernen.
17. ADSR-/Artikulationsprofile ergänzen.
18. Akkordbindung, Voice Leading und Patternvariation einführen.
19. Percussionrollen und Übergangsereignisse ergänzen.

**Erwarteter Nutzen:** Aus einzelnen Pulsen werden Basslinien, Arpeggien und Groove.

### Phase C – In Form und Mix integrieren

20. Section Profiles um Rhythmusdramaturgie erweitern.
21. kontextabhängige Konstellationswahl pro Abschnitt integrieren.
22. persönliche Präferenz als begrenzten Faktor in die Produktionsauswahl integrieren.
23. hörbare Relationen zwischen Rhythmusgruppe und Flächen ausführen.
24. Bass/Foundation- und Arpeggio/Pad-Masking kontrollieren.
25. abschnittsweise Stem-Ziele und Raumstaffelung einführen.
26. Musikqualitätskritiker und automatische Revision ergänzen.

**Erwarteter Nutzen:** Rhythmus wird Teil der Komposition statt zusätzliche Schicht.

### Phase D – Abnahme

27. mindestens 100 Nutzerbewertungen über mehrere Learn/Train-Sitzungen sammeln.
28. Geschmacksmodell gegen Zufalls- und Durchschnittsbaseline validieren.
29. drei Charaktere × drei Seeds rendern.
30. priorisierte und personalisierte Auswahl gegen bisherige Katalogrotation vergleichen.
31. Metriken, Stem-Audits und Blind-Hörtests durchführen.
32. erfolgreiche Konstellationen versioniert in den Erfolgspool übernehmen.
33. Baseline-Vergleich dokumentieren.
34. nur nach bestandenem Hör-Gate als neue Standardpipeline aktivieren.

---

## 5. Definition of Done

Plan 4 ist abgeschlossen, wenn alle folgenden Bedingungen erfüllt sind:

### Funktion

- Explizite Bass-, Arpeggio- und Rhythmusprompts erzeugen garantiert passende Rollen.
- Kein Slotlimit entfernt Pflichtrollen.
- Alle rhythmischen Rollen verwenden den gemeinsamen GroovePlan.
- Event-gesteuerte Synths erzeugen keine konkurrierenden Zufallsonsets.
- Hauptrollen verwenden ausschließlich validierte S- oder A-Tier-Presets.
- Zufall permutiert nur erfolgreiche Kandidaten und sichere Parameterbereiche.
- Die Auswahl ist anhand gespeicherter Scores und Ablehnungsgründe erklärbar.
- Nutzerbewertungen von 1 bis 10 werden dauerhaft mit vollständigem Kontext gespeichert.
- Bereits präsentierte Beispiele und ähnliche Varianten werden sitzungsübergreifend erkannt.
- Neue Synths, Presets, Pattern und Konstellationen werden automatisch zur Bewertung
  vorgeschlagen.

### Musik

- Jeder rhythmische Referenztrack besitzt eine erinnerbare Bassphrase.
- Jeder Track besitzt ein erkennbares Arpeggio mit mindestens zwei Variationen.
- Mindestens drei komplementäre Rhythmusfunktionen sind hörbar.
- Mindestens vier Formabschnitte unterscheiden sich rhythmisch und klanglich.
- Mindestens fünf Relationen verbinden Rhythmusgruppe, Harmonie, Motiv und Textur.
- Der Track enthält bewusst gesetzte Pausen, Fills, Übergaben und Schlussgesten.

### Klang

- Bass besitzt Körper und hörbare Obertöne.
- Arpeggio bleibt trotz Raumanteil artikuliert.
- Percussion ist weich, charaktervoll und nicht bloß Noise.
- Drones und Pads maskieren die Rhythmusgruppe nicht dauerhaft.
- Rhythmusgruppe wirkt integriert und nicht aufgeklebt.

### Qualitätssicherung

- Pflichtstems sind nicht leer und erreichen ihre Abschnittsziele.
- Onsets stimmen mit GroovePlan und Phrasengrenzen überein.
- Bass- und Arpeggionoten stimmen mit Harmonie und Voice Leading überein.
- Einzelklänge, Duo-Partner und vollständige Konstellationen bestehen getrennte Gates.
- Schlechte Ensemblekompatibilität kann nicht durch einen hohen Solo-Score verdeckt werden.
- Wiederholungsmali verhindern, dass dieselben erfolgreichen Presets jeden Track dominieren.
- Objektive Qualitätsbewertung und persönliches Geschmacksmodell bleiben strikt getrennt.
- Persönliche Vorhersagen schlagen nach ausreichendem Training einfache Baselines.
- Aktives Lernen deckt neue, unsichere und unterrepräsentierte Optionen gezielt ab.
- Diversitäts- und Explorationsquoten verhindern eine selbstverstärkende Geschmacksblase.
- Technische Tests, Audio-Gates, Ruff und Mypy bestehen.
- Neun 60-Sekunden-Referenztracks bestehen die Hör- und Messgates.

### Entscheidender Erfolgsnachweis

In einem Blindvergleich muss die Plan-4-Version innerhalb der ersten 15 Sekunden als
rhythmisch geordnet erkannt werden. Innerhalb von 30 Sekunden müssen Bassbewegung,
Arpeggiofigur und mindestens ein reagierendes weiteres Layer benennbar sein. Nach 60 Sekunden
muss eine musikalische Entwicklung erinnerbar sein. Wenn nur „mehr Klänge“ oder „mehr Pulse“
zu hören sind, ist Plan 4 nicht bestanden.
