# Ambient Universe – Plan 3: Klangvielfalt, Bewegung und musikalische Rekombination

**Ziel:** Die Musik soll nicht mehr wie dieselbe Klangfläche mit leicht anderen Parametern wirken, sondern wie eine bewusst orchestrierte Komposition aus unterschiedlichen, sich entwickelnden Klangidentitäten.

**Ausgangsdiagnose:** Es gibt bereits mehrere brauchbare Klanggeneratoren. Die Monotonie entsteht vor allem durch ihre Nutzung: Auswahl und Preset-Variation sind zu schwach, Stimmen bleiben zu lange statisch, Ereignisse sind nur lose gekoppelt, und Klangquellen werden nicht konsequent mit musikalischen Funktionen, Formabschnitten und Kontrastregeln verbunden.

## 1. Leitprinzipien

1. **Klangquelle ist nicht gleich Musik.** Jeder Generator bekommt eine musikalische Funktion, eine Bewegungsstrategie und erlaubte Partner.
2. **Jede tragende Stimme muss sich verändern.** Veränderung kann Tonhöhe, Rhythmus, Timbre, Artikulation, Register, Raum oder Dichte betreffen.
3. **Kontrast wird geplant.** Zwei benachbarte Abschnitte dürfen nicht dieselbe Kombination aus Register, Spektrum, Artikulation und Dichte behalten.
4. **Rekombination statt Zufall.** Klangrezepte werden aus Bausteinen (Quelle, Hüllkurve, Modulation, Filter, Raum, Artikulation) deterministisch neu kombiniert.
5. **Ein Generator darf nicht automatisch eine vollständige Stimme sein.** Gute Musik entsteht aus Rollenverbund und Übergabe zwischen Rollen.

## 2. Sofortige Ursachenanalyse

### 2.1 Baseline hörbar zerlegen

Für drei Prompts werden je 20–30 Sekunden gerendert: voller Mix, einzelne Stems und einzelne Generatorfamilien. Zu protokollieren sind:

- welche Generatoren tatsächlich gewählt werden,
- wie viele Stimmen länger als 8 Sekunden unverändert bleiben,
- spektrale und dynamische Entwicklung pro Stimme,
- Wiederholung identischer Events und Parameterverläufe,
- Anteil von Sinus/Noise gegenüber charaktervollen Quellen,
- ob Formabschnitte wirklich neue Klangfarben einführen.

**Gate:** Die Ursache der Monotonie ist pro Referenztrack an mindestens fünf konkreten Stellen belegt.

### 2.2 Capability-Matrix aktualisieren

Vorhandene Quellen explizit als nutzbare Klangfamilien erfassen:

- analog/wavefolded: `gen.osc.bandlimited`, `gen.synth.wavefolder`,
- FM/additiv: `gen.fm.dual_operator`, `gen.additive.harmonic_partials`,
- resonant/physikalisch: `gen.drone.wavetable_resonator`, `gen.object.modal_bell`, `gen.physical.plucked_string`,
- vokal/spektral: `gen.vocal.formant_pad`, `gen.spectral.phase_freeze`,
- granular/ereignishaft: `gen.texture.granular_cloud`, `gen.noise.stochastic_trigger`,
- rhythmisch: `gen.arpeggio.pulse_sequence`,
- Fundament: `gen.drone.sub_bass`.

Für jede Quelle werden hörbare Stärken, Schwächen, passende Register, maximale Dauer ohne Variation und geeignete Prozessoren dokumentiert.

**Gate:** Jede Generatorfamilie besitzt mindestens zwei validierte Klangrezepte und eine empfohlene musikalische Rolle.

## 3. Klang- und Rekombinationsarchitektur

### 3.1 Klang-DNA statt einzelner Presets

Ein `ToneDNA`-Modell einführen mit mindestens:

- source family und source module,
- spectral profile,
- transient/articulation,
- envelope shape,
- modulation character,
- harmonicity/noisiness,
- register and density,
- spatial identity,
- evolution budget.

Ein Rezept wird aus dieser DNA kompiliert. Kleine Mutationen erzeugen kontrollierte Varianten; große Mutationen wechseln die Klangfamilie oder Artikulation. SeedPaths bleiben die einzige Zufallsquelle.

### 3.2 Source banks und Partnerregeln

Klangbanken pro Funktion anlegen: Fundament, Bassbewegung, Harmonie, Motiv, Textur, Objekt und Übergang. Jede Bank enthält mehrere Generatorfamilien, nicht nur Parameterkopien desselben Oszillators.

Beispiele:

- Bass: Subbass + FM-Transient + Tape-Sättigung,
- Harmonie: Formant-Pad + additive Partials + langsam wechselnder Resonator,
- Motiv: Plucked String + Modal Bell + Pulse Sequence,
- Textur: Granular Cloud + Phase Freeze + gezielt gefilterte Stochastic Trigger.

**Gate:** Ein Prompt erzeugt pro Abschnitt mindestens vier unterschiedliche Quellenfamilien; keine Familie darf automatisch mehr als zwei tragende Rollen dominieren.

## 4. Bewegungs- und Anti-Monotonie-Engine

### 4.1 Mehrdimensionale Evolution

Für jede Stimme eine `EvolutionPlan`-Kurve erzeugen. Sie steuert unabhängig:

- Timbre: Wellenform, FM-Index, Partials, Fold amount, Formanten,
- Harmonie: Akkordton, Spannung, Voice Leading,
- Zeit: Eventabstände, Gate-Längen, Pulsdichte,
- Artikulation: Attack, Release, Pluck-Anteil, Transient,
- Raum: Breite, Delay, Reverb-Sends, Distanz,
- Energie: Lautstärke, Register und Dichte.

Eine Stimme darf nicht nur lauter oder leiser werden. Für kontinuierliche Rollen gilt: mindestens zwei Parameterdimensionen müssen sich innerhalb von 8–12 Sekunden merklich entwickeln.

### 4.2 Variation ohne Identitätsverlust

Motive und Klang-DNA werden getrennt variiert. Für Wiederkehr gelten Transformationsarten wie Transposition, rhythmische Dehnung, Fragmentierung, Dichtewechsel, Registertausch, Gegenbewegung und neue Artikulation.

**Gate:** Jeder Referenztrack enthält ein wiedererkennbares Motiv, mindestens drei Varianten und mindestens einen Abschnitt, in dem eine Rolle an eine andere Klangfamilie übergeben wird.

### 4.3 Ereignis- und Übergangsereignisse

Statische Dauertöne werden durch begrenzte Phrasen, Atempausen, Antwortphrasen, Crescendo-/Decrescendo-Gesten und Übergangsobjekte ergänzt. Übergänge dürfen neue Materialklassen ankündigen, aber nicht als zufällige Geräuschfüllung erscheinen.

## 5. Orchestrierung und Form

### 5.1 Abschnittsprofile

Jeder Formabschnitt erhält ein Profil aus:

- aktiven und ruhenden Rollen,
- bevorzugten Klangfamilien,
- Registerverteilung,
- rhythmischer Aktivität,
- spektraler Helligkeit,
- Raumtiefe und Stereobreite,
- Spannungsziel.

Mindestens drei kontrastierende Profile pro 60-Sekunden-Track: Entstehung, Entwicklung, Transformation/Abklingen.

### 5.2 Relationen als Kompositionsregeln

Mindestens drei explizite Relationen pro Abschnitt erzwingen, etwa:

- Motivnoten triggern Modal-Bell-Antworten,
- Basswechsel öffnet oder schließt das Pad-Filter,
- Granularwolke übernimmt Partials des Harmonieplans,
- Pulssequenz bestimmt die Gate-Längen einer zweiten Stimme,
- ein Objekt beendet eine Phrase und verändert die nächste Klang-DNA.

## 6. Mix und Klangtrennung

Erst nach der musikalischen Verbesserung werden Stems gezielt bearbeitet:

- Fundament mono- und phasensicher halten,
- Rollen durch Register und spektrale Slots trennen,
- Ducking/Masking dynamisch aus musikalischen Relationen ableiten,
- Raum als Vorder-/Mittel-/Hintergrund-Komposition verwenden,
- Sättigung, Resonatoren und Reverb pro Klangfamilie dosieren.

Keine globale Lautheitsnormalisierung darf Unterschiede zwischen Stems kaschieren.

## 7. Tests und Qualitätsgates

Neue Tests prüfen:

- Generatorfamilien-Verteilung pro Track und Abschnitt,
- maximale unveränderte Dauer einer Stimme,
- minimale Zahl hörbarer Evolutionen,
- Motivwiederkehr und Variationsabstand,
- Register- und Spektralkontrast benachbarter Abschnitte,
- Relationserfüllung zwischen Layern,
- identische Seeds = identischer Plan und Audio-Fingerprint,
- andere Seeds = andere, aber gültige Orchestrierung.

Zusätzlich bleibt ein Hörtest verbindlich: 30 Sekunden ohne sichtbare Metadaten anhören und Monotonie, Klangcharakter, Formkontrast, Vordergrund und Übergänge bewerten.

## 8. Umsetzungsreihenfolge

1. Baseline zerlegen und Capability-Matrix vervollständigen.
2. `ToneDNA`, Source Banks und Generator-Scoring implementieren.
3. `EvolutionPlan` und Anti-Monotonie-Gates implementieren.
4. Motivvarianten und Layer-Relationen an den gemeinsamen Harmonie-/Rhythmusplan anbinden.
5. Abschnittsprofile und Orchestrierungswechsel einführen.
6. 20-Sekunden-Ensembletests, dann 60-Sekunden-Referenztracks rendern.
7. Mix-/Raumregeln auf die nun musikalisch unterschiedlichen Stems anwenden.
8. Hördokumentation, Metriken und Abschlussbericht aktualisieren.

## 9. Definition of Done für Plan 3

Plan 3 ist bestanden, wenn drei Seeds je drei Referenztracks erzeugen, bei denen:

- mindestens fünf unterschiedliche Generatorfamilien pro Track hörbar vorkommen,
- kein tragender Layer länger als 12 Sekunden ohne relevante Veränderung bleibt,
- mindestens drei Formabschnitte durch Klangfarbe und Orchestrierung unterscheidbar sind,
- ein Motiv mit mindestens drei Varianten wiederkehrt,
- mindestens drei Layer-Relationen hörbar wirksam sind,
- kein Track primär aus statischem Sinus, statischem Noise oder globalem Pad besteht,
- die Tracks untereinander deutlich verschiedene Klangidentitäten besitzen,
- technische Audio-Gates und alle bestehenden Tests weiterhin bestehen.

Der entscheidende Erfolgsnachweis ist nicht eine längere Generatorliste, sondern ein Blind-Hörvergleich gegen die aktuelle Baseline: Die neue Version muss innerhalb der ersten 20 Sekunden als bewegter, kontrastreicher und klanglich individueller erkennbar sein.
