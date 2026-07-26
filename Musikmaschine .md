Ja — das ist technisch sehr gut machbar. Ich würde die Musikmaschine allerdings nicht auf ein einziges Repository setzen. Die stärkste Lösung ist ein kontrollierbarer Hybrid:

* Ein LLM versteht den Prompt und erzeugt einen strukturierten Albumplan.  
* Eine Ambient-Wissensbasis liefert Regeln, Klangrezepte und Kompositionstechniken.  
* Ein symbolischer Generator erzeugt Form, Harmonik, Ereignisse und Variationen.  
* Ein echter Synthese- und DSP-Server rendert reproduzierbar hochwertige Audiodateien.  
* Ein Analyseagent bewertet jeden Entwurf und lässt problematische Passagen neu erzeugen.

Meine klare Hauptempfehlung wäre:

> **SuperCollider \+ Supriya \+ isobar/MusicLang \+ eigene Ambient-DSL.**  
> Später ergänzt durch Faust oder DaisySP für proprietäre, fest integrierte Klangerzeuger.

Stand der Recherche: 26\. Juli 2026\.

## **Priorisierte Gesamtliste**

Die Reihenfolge bewertet nicht nur den Klang, sondern die Eignung für deine konkrete promptbare Ambient-Album-Maschine.

| Rang | Repository | Hauptrolle | Lizenz | Urteil |
| ----- | ----- | ----- | ----- | ----- |
| 1 | [SuperCollider](https://github.com/supercollider/supercollider) | Synthese, Effekte, generative Komposition, Rendering | GPL-3.0 | Bester Gesamtkern |
| 2 | [Supriya](https://github.com/supriya-project/supriya) | Python-Steuerung für SuperCollider | MIT | Ideale KI-Schnittstelle |
| 3 | [Csound](https://github.com/csound/csound) | Sehr umfassende Synthese und Offline-Rendering | LGPL-2.1+ | Extrem mächtige Alternative |
| 4 | [Faust](https://github.com/grame-cncm/faust) | DSP-Entwicklung und Codegenerierung | LGPL-2.1+, Komponenten mit Ausnahmen | Beste langfristige DSP-Basis |
| 5 | [pyo](https://github.com/belangeo/pyo) | Python-native Klangerzeugung | LGPL-3.0+ | Schnellster KI-Prototyp |
| 6 | [ChucK](https://github.com/ccrma/chuck) | Präzise zeitbasierte Musikprogrammierung | MIT oder GPL-2.0+ | Sehr gute generative Laufzeit |
| 7 | [Tone.js](https://github.com/Tonejs/Tone.js) | Browser-Synthese und Webprodukt | MIT | Beste Weblösung |
| 8 | [Surge XT](https://github.com/surge-synthesizer/surge) | Ausgereifter hybrider Softsynth | GPL-3.0 | Hervorragende Klangquelle |
| 9 | [isobar](https://github.com/ideoforms/isobar) | Generative Patterns und Albumstruktur | MIT | Sehr guter Kompositionsmotor |
| 10 | [MusicLang](https://github.com/MusicLang/musiclang) | Tonale Grammatik, Transformation, symbolische KI | BSD-2-Clause | Gute Wissens- und Harmonikschicht |
| 11 | [DaisySP](https://github.com/electro-smith/DaisySP) | C++-DSP-Bausteine und Synthesemodelle | MIT | Sehr produktfreundlich |
| 12 | [STK](https://github.com/thestk/stk) | Physical Modeling und Instrumentenmodelle | MIT | Organische Ambient-Klänge |
| 13 | [FunDSP](https://github.com/SamiPerttu/fundsp) | Rust-DSP und prozedurale Audionetze | MIT/Apache-2.0 | Moderner kompakter Audiokern |
| 14 | [Vital](https://github.com/mtytel/vital) | Wavetable- und Spektralsynthese | GPL-3.0, kommerzielle Lizenz möglich | Klanglich stark, produktseitig riskanter |
| 15 | [AudioCraft](https://github.com/facebookresearch/audiocraft) | Text-to-Music und neuronale Audiogenerierung | Code MIT, Modellgewichte CC-BY-NC 4.0 | Ideengeber, nicht als kommerzieller Kern |

---

# **Die 15 Repositories im Detail**

## **1\. SuperCollider – der beste Gesamtkern**

[SuperCollider](https://github.com/supercollider/supercollider) besteht aus dem Echtzeit-Audioserver `scsynth`, dem parallelen Server `supernova`, der Sprache `sclang` und einer Entwicklungsumgebung. Es wurde ausdrücklich für Audiosynthese und algorithmische Komposition entwickelt.

### **Klangerzeugungsmethoden**

* Subtraktive Synthese mit Sägezahn, Rechteck, Puls, Dreieck und Rauschquellen.  
* Wavetable-Synthese mit frei definierbaren Wellenformtabellen.  
* Additive Synthese mit großen Gruppen einzelner Sinus-Oszillatoren.  
* FM-Synthese und Phasenmodulation.  
* Amplitudenmodulation und Ringmodulation.  
* Granularsynthese aus Samples, Wavetables oder synthetischen Quellen.  
* Granularsynthese mit festen oder zufälligen Grain-Positionen.  
* Pitch-synchrone und asynchrone Grains.  
* Sample-basierte Synthese mit Buffern.  
* Resampling und variable Abspielgeschwindigkeit.  
* Spektrale Synthese über FFT und Phase-Vocoder-UGens.  
* Spektrales Einfrieren, Verschieben, Verwischen und Filtern.  
* Karplus-Strong- und Plucked-String-Synthese.  
* Resonatorbanken für metallische, gläserne und perkussive Klänge.  
* Modale Synthese über `Klank`, `DynKlank`, `Ringz` und ähnliche Resonatoren.  
* Stochastische Synthese mit weißem, rosa, braunem und grauem Rauschen.  
* Impulsrauschen, Dust-Prozesse und zufällige Triggerfelder.  
* Chaotische Oszillatoren und nichtlineare Generatoren.  
* Feedback-Netzwerke.  
* Cross-Synthesis zwischen verschiedenen Signalen.  
* Convolution und Faltung mit Impulsantworten.  
* Formant- und Vokalsynthese.  
* Wavefolding, Clipping, Saturation und nichtlineare Verzerrung.  
* Mikrotonale und frei gestimmte Synthese.  
* Multichannel- und Ambisonics-kompatible Klangräume.

### **Für Ambient besonders wertvolle Funktionen**

* Sehr langsame Hüllkurven über Minuten.  
* Mehrere unabhängig laufende LFOs.  
* Zufällige Modulationen mit Glättung.  
* Brownian Motion für organische Parameterbewegungen.  
* Langsame Random Walks.  
* Wahrscheinlichkeitsgesteuerte Notenereignisse.  
* Unabhängige Zeitskalen pro Ebene.  
* Sehr lange Delaylines.  
* Kaskadierte Allpass-Netzwerke.  
* Comb-Filter und resonierende Echos.  
* Feedback-Delay-Netzwerke.  
* Algorithmische Hallräume.  
* `FreeVerb`, `GVerb` und weitere Hallmodelle.  
* Pitch-Shifting innerhalb von Feedbackschleifen.  
* Freeze- und Infinite-Reverb-artige Konstruktionen.  
* Automatische Stereo- und Mehrkanalverteilung.  
* Bewegliche Schallquellen.  
* Langsame Rotation im Stereofeld.  
* Frequenzabhängige Räumlichkeit.  
* Spektrales Ducking zwischen Ebenen.  
* Dynamische Filterfahrten.  
* Analoge Instabilität durch Drift, leichte Verstimmung und Rauschmodulation.  
* Reproduzierbarer Zufall durch feste Seeds.

### **Kompositionsfunktionen**

* `Pbind` verbindet Tonhöhe, Dauer, Lautstärke, Instrument und weitere Parameter.  
* `Pseq` erzeugt Sequenzen.  
* `Prand` zieht zufällige Elemente.  
* `Pwrand` verwendet gewichtete Zufallsentscheidungen.  
* `Pxrand` reduziert unmittelbare Wiederholungen.  
* `Pwhite` erzeugt gleichverteilte Zufallswerte.  
* `Pbrown` erzeugt langsam wandernde Werte.  
* `Pwalk` bewegt sich durch Listen oder Tonvorräte.  
* `Ppar` kombiniert Ebenen parallel.  
* `Pmono` steuert eine durchgehende Synthesizerstimme.  
* `Pdef` erlaubt austauschbare musikalische Prozesse.  
* Routinen und Tasks können eigenständige musikalische Zeitabläufe bilden.  
* Ereignisströme können im laufenden Betrieb verändert werden.  
* Regeln können auf Takte, Abschnitte, Tracks oder ein ganzes Album wirken.  
* Non-Realtime-Rendering erzeugt Dateien schneller oder langsamer als Echtzeit.  
* Einzelne Stems können getrennt gerendert werden.  
* OSC erlaubt eine saubere externe Steuerung durch Python oder andere Agenten.

### **Eignung für deine KI-Maschine**

Ein KI-Agent sollte nicht beliebigen SuperCollider-Code erzeugen und direkt ausführen. Sicherer wäre:

* Das LLM erzeugt einen validierten Albumplan als JSON.  
* Eine kontrollierte Übersetzungsschicht erzeugt daraus SynthDefs und Patterns.  
* Nur bekannte UGens und freigegebene Parameterbereiche werden erlaubt.  
* Jeder Track erhält einen festen Seed.  
* Der Renderer arbeitet in einem isolierten Prozess.  
* Audio- und CPU-Limits werden erzwungen.  
* Ein Analyseagent kontrolliert Klicks, Clipping, Lautheit und spektrale Balance.

### **Nachteile**

* Relativ hohe Lernkurve.  
* Die Sprache `sclang` ist außerhalb der Musiktechnologie wenig verbreitet.  
* GPL-3.0 muss bei einer kommerziellen Distribution sauber geprüft werden.  
* Für ein Closed-Source-Produkt ist eine getrennte Serverarchitektur naheliegend, aber keine automatische rechtliche Garantie.

**Gesamturteil:** Die reichhaltigste und musikalisch passendste Basis.

---

## **2\. Supriya – die ideale Brücke zwischen KI und SuperCollider**

[Supriya](https://github.com/supriya-project/supriya) ist eine MIT-lizenzierte Python-API für SuperCollider. Es kann den SuperCollider-Server starten, SynthDefs in Python erzeugen, Patterns planen und Echtzeit- oder Offline-Kompositionen rendern.

### **Kernfunktionen**

* Starten und Beenden eines SuperCollider-Servers aus Python.  
* Verbindung zu einem bereits laufenden `scsynth`.  
* Senden und Empfangen von OSC-Nachrichten.  
* Verwaltung von Gruppen, Synths, Bussen und Buffern.  
* Erzeugung von SuperCollider-SynthDefs direkt in Python.  
* Python-Abbildungen zahlreicher SuperCollider-UGens.  
* Echtzeitsteuerung.  
* Non-Realtime-Scores.  
* Tempo- und taktbasierte Clocks.  
* Pattern-System.  
* Ereignisplanung.  
* Callbacks.  
* Unterstützung für `asyncio`.  
* Integration in FastAPI- oder Agenten-Backends.  
* Integration in Jupyter und IPython.  
* Visualisierung von Synthesegraphen über Graphviz.  
* Trennung von abstraktem musikalischem Kontext und tatsächlichem Server.  
* Steuerung lokaler und entfernter Audio-Server.  
* Reproduzierbare Score- und Renderprozesse.  
* Python-seitige Tests von Kompositions- und Orchestrierungslogik.

### **Klangerzeugungsmöglichkeiten**

Supriya erzeugt nicht selbst den Klang. Es öffnet aber aus Python heraus praktisch den gesamten SuperCollider-Klangraum:

* Oszillatoren.  
* Noise-Generatoren.  
* Filter.  
* Granularsynthese.  
* Wavetable-Synthese.  
* Sample-Playback.  
* Resonatorbanken.  
* FM und AM.  
* FFT- und Phase-Vocoder-Prozesse.  
* Delay, Reverb und Modulationseffekte.  
* Mehrkanal- und räumliche Synthese.

### **Warum es für KI so wertvoll ist**

Python ist die natürliche Umgebung für:

* LLM-Aufrufe.  
* RAG.  
* Embeddings.  
* Wissensdatenbanken.  
* Pydantic-Schemata.  
* Evaluationsagenten.  
* Audioanalyse mit librosa, Essentia oder TorchAudio.  
* Web-APIs.  
* Job-Queues.  
* Rendering-Farmen.  
* Album- und Assetverwaltung.  
* Experiment-Tracking.  
* automatische Tests.

Ein LLM könnte beispielsweise keine Audiobefehle, sondern Folgendes erzeugen:

{  
  "track\_duration\_seconds": 540,  
  "seed": 48172,  
  "harmonic\_field": {  
    "root": "D",  
    "mode": "dorian",  
    "change\_rate\_bars": \[16, 48\]  
  },  
  "layers": \[  
    {  
      "role": "drone",  
      "synthesis": "wavetable\_resonator",  
      "density": 0.15,  
      "spectral\_center\_hz": 580,  
      "motion": "brownian\_slow"  
    },  
    {  
      "role": "particles",  
      "synthesis": "granular",  
      "density": 0.08,  
      "entry\_minute": 2.5  
    }  
  \]  
}

Supriya übersetzt dieses validierte Objekt dann in echte Synthese- und Patternstrukturen.

### **Nachteile**

* Benötigt SuperCollider als Audio-Backend.  
* Nicht jede neue SuperCollider-Erweiterung steht sofort als komfortable Python-Klasse bereit.  
* Die musikalische Wissensbasis muss weiterhin von dir entwickelt werden.

**Gesamturteil:** Für dein Vorhaben fast unverzichtbar, wenn SuperCollider der Klangkern wird.

---

## **3\. Csound – das größte klassische Syntheselabor**

[Csound](https://github.com/csound/csound) ist ein Sound- und Music-Computing-System mit einer enormen Zahl an sogenannten Opcodes. Das aktuelle Repository entwickelt Csound 7; Csound 6 ist laut Projekt EOL. Der Kern steht unter LGPL-2.1 oder später.

### **Grundelemente**

* Orchestra beschreibt Instrumente und Signalwege.  
* Score beschreibt musikalische Ereignisse.  
* Instrument Definitionen können beliebig parametrisiert werden.  
* Function Tables speichern Wellenformen, Samples, Hüllkurven und Spektren.  
* `i-rate` für Initialisierungswerte.  
* `k-rate` für Kontrollsignale.  
* `a-rate` für Audiosignale.  
* Globale Audiobusse.  
* Globale Steuerkanäle.  
* Echtzeit- und Offline-Betrieb.  
* C-, C++- und Python-APIs.  
* MIDI- und OSC-Steuerung.  
* Einbettung in Apps, Plugins, Browser- und Mobilplattformen.

### **Klangerzeugungsmethoden**

* Klassische subtraktive Synthese.  
* Additive Synthese.  
* Bandlimitierte Oszillatoren.  
* Wavetable- und Table-Lookup-Synthese.  
* FM-Synthese mit komplexen Operatornetzen.  
* Phasenmodulation.  
* Amplitudenmodulation.  
* Ringmodulation.  
* Waveshaping.  
* Wavefolding.  
* Pulsbreitenmodulation.  
* Hard Sync.  
* Analoge Drift und zufällige Verstimmung.  
* Zero-Delay-Feedback-Filter.  
* Ladder-Filter und analog modellierte Filter.  
* Granularsynthese mit `grain`, `grain3`, `syncgrain`, `partikkel` und verwandten Opcodes.  
* FOF- und Formant-Synthese.  
* Waveguide-Synthese.  
* Karplus-Strong.  
* Physikalische Instrumentenmodelle.  
* Scanned Synthesis.  
* Modal- und Resonatorsynthese.  
* Wave-Terrain-Synthese.  
* Vektorsynthese und Morphing.  
* Phase-Vocoder-Verarbeitung.  
* ATS-Analyse und Resynthese.  
* Spektrales Einfrieren.  
* Spektrales Strecken und Transponieren.  
* Cross-Synthesis.  
* Sample-Playback.  
* SoundFont-Nutzung.  
* Convolution.  
* Faltungshall.  
* Feedback-Delay-Netzwerke.  
* algorithmischer Hall.  
* Dynamikprozessoren.  
* Multichannel-Audio und räumliche Verteilung.

### **Ambient-spezifische Vorteile**

* Sehr lange deterministische Offline-Renderings.  
* Instrumente können über komplette Tracklängen laufen.  
* Präzise zeitliche Kontrolle.  
* Gut für große, sich sehr langsam verändernde Signalnetze.  
* Besonders leistungsfähig für Granular-, Resonator- und Spektralklänge.  
* Sehr gut für physikalische Modellierung imaginärer Instrumente.  
* Zahlreiche ungewöhnliche Syntheseverfahren außerhalb normaler Softsynths.  
* Ein kompletter Track kann als deklaratives `.csd`\-Dokument gespeichert werden.  
* Ein KI-Agent kann diese Dokumente erzeugen oder parametrisieren.  
* Ergebnisse sind durch Seeds und Scoredateien reproduzierbar.

### **Nachteile**

* Syntax und Denkmodell wirken teilweise historisch.  
* Parameterräume sind riesig; unkontrollierte KI-Generierung produziert schnell unmusikalische Ergebnisse.  
* Weniger komfortabel für moderne interaktive Oberflächen als Tone.js oder eine Python-Webanwendung.  
* Für gute Resultate braucht man kuratierte Instrumentenbibliotheken.

**Gesamturteil:** Ideal, wenn maximale Synthesetiefe und zuverlässiges Offline-Rendering wichtiger sind als eine moderne Entwickleroberfläche.

---

## **4\. Faust – eigene Synthesizer und Effekte bauen**

[Faust](https://github.com/grame-cncm/faust) ist keine fertige Ambient-Musikmaschine, sondern eine funktionale Sprache für Signalverarbeitung. Ein DSP-Programm kann unter anderem in C, C++, WebAssembly, LLVM IR, Java sowie verschiedene Plugin- und Hostformate übersetzt werden.

### **Grundprinzipien**

* Signalfluss wird funktional beschrieben.  
* Serielle Verschaltung.  
* Parallele Verschaltung.  
* Signalaufteilung.  
* Signalzusammenführung.  
* Feedback.  
* Rekursion.  
* Mathematische Operationen auf Sampleebene.  
* Wiederverwendbare DSP-Funktionen.  
* Parametrisierte Synthesizerbausteine.  
* Automatisch erzeugte Bedienoberflächen.  
* Metadaten für Parameter.  
* Kompilierung zu hochperformantem Code.  
* SIMD- und Parallelisierungsoptionen.  
* Einbettung über `libfaust`.  
* Just-in-Time-Kompilierung möglich.

### **Enthaltene bzw. realisierbare Klangerzeugung**

* Bandlimitierte Oszillatoren.  
* Wavetable-Oszillatoren.  
* Additive Oszillatorbanken.  
* FM- und PM-Synthese.  
* Subtraktive Synthese.  
* Rauschgeneratoren.  
* Nichtlineare Oszillatoren.  
* Resonatoren.  
* Modal-Synthese.  
* Karplus-Strong.  
* Waveguides.  
* Physikalische Modelle.  
* Filterbänke.  
* State-Variable-Filter.  
* Ladder-Filter.  
* Equalizer.  
* Crossover-Netzwerke.  
* Waveshaper.  
* Röhren- und Sättigungsmodelle.  
* Kompressoren und Limiter.  
* Chorus.  
* Flanger.  
* Phaser.  
* Delays.  
* Pitch-Shifting.  
* algorithmische Reverbs.  
* Faltungskomponenten.  
* Spektralanalysen.  
* LFOs.  
* Hüllkurven.  
* Parameter-Smoothing.  
* MIDI- und OSC-zuordenbare Parameter.  
* Polyphone Instrumente.

### **Produktvorteil**

Faust eignet sich sehr gut, um aus deinem verdichteten Ambient-Klangwissen eine proprietäre Sammlung kleiner DSP-Instrumente zu entwickeln:

* `slow_drift_pad`  
* `spectral_fog`  
* `unstable_tape_drone`  
* `metallic_resonance_cloud`  
* `granular_rain`  
* `infinite_feedback_space`  
* `breathing_noise_field`  
* `harmonic_dust`  
* `dark_modal_bell`  
* `submerged_choir_resonator`

Der KI-Agent wählt dann keine beliebigen Signalverbindungen, sondern eines dieser geprüften Instrumente und stellt dessen sicheren Parameterraum ein.

### **Lizenzhinweis**

Der Compiler steht im aktuellen Repository unter LGPL-2.1+. Bei Architekturdateien und Faust-Bibliotheken existieren zusätzliche Lizenztexte und teilweise Ausnahmen für erzeugten Code. Für ein kommerzielles Produkt muss jede tatsächlich eingebundene Bibliothek und Architekturdatei separat geprüft werden.

### **Nachteile**

* Keine eigentliche Albumkomposition.  
* Kein umfassendes Pattern-System.  
* Ein unbeschränktes LLM sollte nicht selbst beliebige DSP-Graphen kompilieren.  
* Entwicklungsaufwand höher als beim Nutzen fertiger SuperCollider-Instrumente.

**Gesamturteil:** Nicht der beste MVP-Kern, aber wahrscheinlich die beste langfristige Basis für eigene kommerzielle Klangtechnologie.

---

## **5\. pyo – komplette Audiosynthese direkt in Python**

[pyo](https://github.com/belangeo/pyo) ist ein in C implementiertes Python-DSP-Modul. Es verbindet Audioerzeugung, Effekte, Sequencing, MIDI, OSC, Spektralverarbeitung und Aufnahme direkt mit Python.

### **Oszillatoren und Generatoren**

* Sinusoszillatoren.  
* Bandlimitierte Oszillatoren.  
* Tabellenoszillatoren.  
* Supersaw-artige Generatoren.  
* Puls- und Rechteckgeneratoren.  
* `LFO` mit verschiedenen Wellenformen.  
* FM und Cross-FM.  
* Feedback-Sinusoszillatoren.  
* Loop-Oszillatoren.  
* Wavetable-Morphing.  
* Weißes, rosa und braunes Rauschen.  
* Zufallsimpulse.  
* Random Walks.  
* Chaosgeneratoren wie Lorenz-, Rössler- und Chen-Lee-Systeme.  
* Triggerbasierte Zufallstonhöhen.  
* Generative MIDI-Tonhöhenerzeugung.

### **Sampling und Granularsynthese**

* Laden von WAV- und AIFF-Dateien.  
* Tabellen als zentrale Sample- und Wellenformspeicher.  
* Granulator.  
* Mehrstimmige Granularsynthese.  
* Partikelgeneratoren.  
* Variable Grainposition.  
* Variable Graindauer.  
* Grain-Pitch-Verteilung.  
* Looper.  
* Table-Playback.  
* Time-Stretch-artige Konstruktionen.  
* Crossfades zwischen Tabellen.  
* Aufzeichnung in Tabellen.  
* Echtzeitmanipulation von Audiopuffern.

### **Filter und Effekte**

* Biquad-Filter.  
* Multi-Mode-Filter.  
* State-Variable-Filter.  
* Moog-artige Filter.  
* Resonatoren.  
* Filterbänke.  
* Equalizer.  
* Delays.  
* Smooth Delay.  
* Waveguide Delay.  
* Chorus.  
* Flanger.  
* Phaser.  
* Reverb.  
* `WGVerb`.  
* `STRev`.  
* Freeverb-artige Verfahren.  
* Convolution.  
* Dynamikbearbeitung.  
* Kompression.  
* Gate.  
* Expansion.  
* Distortion.  
* Degrade und Bitreduktion.  
* Frequency Shifting.  
* Harmonizer.  
* Pitch-Shifting.

### **Spektralverarbeitung**

* FFT-Analyse.  
* Phase-Vocoder-Analyse.  
* Resynthese.  
* Spektrales Transponieren.  
* Spektrale Filter.  
* Spektrale Delays.  
* Spektrales Morphing.  
* Cross-Synthesis.  
* Spektraler Hall.  
* Frequenzbasierte Manipulation einzelner Bins.

### **Komposition und Kontrolle**

* `Metro` für Trigger.  
* `Beat` für rhythmische Muster.  
* `Seq` für Sequenzen.  
* `Pattern` für wiederkehrende Python-Funktionen.  
* Events-System.  
* Hüllkurven und Breakpoint-Funktionen.  
* MIDI-Ein- und Ausgabe.  
* OSC.  
* Callbacks.  
* Mehrkanalaudio.  
* Multicore-Funktionen.  
* Offline- und Echtzeitaufnahme.

### **Vorteile**

* Sehr kurze Strecke zwischen LLM-Planer und Klang.  
* Direkter Zugriff auf NumPy, PyTorch und Audioanalyse.  
* Gut für Prototypen.  
* Kein zusätzlicher Musikserver zwingend notwendig.  
* Ambient-Parameter können direkt als Python-Datenklassen modelliert werden.

### **Nachteile**

* Python-Garbage-Collection und Anwendungslogik dürfen den Echtzeit-Audiothread nicht stören.  
* Für ein großes Produkt ist die Trennung zwischen Orchestrierung und DSP weniger sauber als bei Supriya plus `scsynth`.  
* LGPL-3.0 muss bei Distribution berücksichtigt werden.

**Gesamturteil:** Der schnellste Weg zu einem funktionierenden Python-Prototyp.

---

## **6\. ChucK – musikalische Zeit als Programmiersprache**

[ChucK](https://github.com/ccrma/chuck) ist eine „strongly timed“ Programmiersprache für Echtzeitklang und Musik. Zeit ist ein fester Teil des Sprachmodells. ChucK kann außerdem als Kern in C++-Hosts eingebettet und nach WebAssembly kompiliert werden.

### **Zeit- und Kompositionsmodell**

* Samplegenaue logische Zeit.  
* Explizites Fortschalten der Zeit.  
* Parallele musikalische Prozesse als „Shreds“.  
* `spork` startet gleichzeitig laufende Prozesse.  
* Prozesse können im Betrieb hinzugefügt werden.  
* Code kann live ersetzt werden.  
* Jeder Layer kann einen eigenen zeitlichen Ablauf besitzen.  
* Synchronisation über Events.  
* Dynamische Kontrollraten.  
* Tempo kann als eigene Zeitrelation modelliert werden.  
* Sehr gut für Phasing, Polyrhythmik und langsam auseinanderlaufende Ebenen.

### **Klangerzeugung**

* Sinus, Sägezahn, Rechteck, Puls und Dreieck.  
* Impuls- und Rauschgeneratoren.  
* Wavetable- und Sample-Playback.  
* FM, AM und Ringmodulation.  
* Hüllkurven und ADSR.  
* Filter.  
* Biquads.  
* Pole-Zero-Filter.  
* Resonatoren.  
* Feedback.  
* Delays und Echo.  
* Chorus.  
* algorithmische Hallmodelle.  
* Pitch-Shifting.  
* Physical-Modeling-Instrumente aus der STK-Tradition.  
* Mehrkanal-Audio.  
* Audioanalyse über sogenannte UAna-Objekte.  
* FFT.  
* RMS.  
* Spektraler Schwerpunkt.  
* Spektraler Flux.  
* Eigene Erweiterungen über ChuGins.

### **Produktintegration**

* C++-Host-Modus.  
* „Vanilla“-Kern ohne eigene Audio-I/O-Schicht.  
* Globale Variablen zur Kommunikation zwischen Host und ChucK.  
* Shred-Steuerung aus C++.  
* WebAssembly.  
* WebChucK.  
* MIDI.  
* OSC.  
* HID-Controller.  
* Integration in Unity, Unreal, Pure Data und andere Hosts.

### **Lizenzvorteil**

Der aktuelle ChucK-Kern ist dual lizenziert: Du kannst MIT oder GPL-2.0+ wählen. Damit ist ChucK wesentlich leichter in kommerzielle Produkte integrierbar als manche ältere Beschreibungen vermuten lassen.

### **Nachteile**

* Kleinere Entwicklergemeinde als Python oder JavaScript.  
* Eigene Sprache.  
* Weniger umfangreiche Synthesebibliothek als SuperCollider oder Csound.  
* Für LLMs existieren weniger Trainingsbeispiele als für Python.

**Gesamturteil:** Sehr interessant, wenn musikalische Prozesse live, autonom und präzise nebeneinander laufen sollen.

---

## **7\. Tone.js – beste Grundlage für eine Ambient-Webanwendung**

[Tone.js](https://github.com/Tonejs/Tone.js) ist ein MIT-lizenziertes Web-Audio-Framework mit DAW-artigem Transport, Synthesizern, Effekten und samplegenauer Ereignisplanung im Browser.

### **Synthesizer**

* `Synth`.  
* `MonoSynth`.  
* `PolySynth`.  
* `FMSynth`.  
* `AMSynth`.  
* `DuoSynth`.  
* `MembraneSynth`.  
* `MetalSynth`.  
* `NoiseSynth`.  
* `PluckSynth`.  
* `Sampler`.  
* Eigene Synthesegraphen aus Web-Audio-Nodes.

### **Klangquellen**

* Standardoszillator.  
* Fat Oscillator.  
* AM-Oszillator.  
* FM-Oszillator.  
* Omni-Oszillator.  
* Pulsoszillator.  
* PWM.  
* Rauschquellen.  
* Audio-Player.  
* Grain Player.  
* User-Media- und externe Eingänge.  
* Bufferbasierte Quellen.

### **Modulation und Steuerung**

* ADSR-Hüllkurven.  
* Amplituden- und Frequenzhüllkurven.  
* LFOs.  
* Follower.  
* Signalobjekte.  
* Parameter-Ramping.  
* Tempo-relative Zeitangaben.  
* Samplegenaue Vorausplanung.  
* Transport mit Start, Stop, Loop und Tempoautomation.  
* `Sequence`.  
* `Pattern`.  
* `Loop`.  
* `Part`.  
* Zufalls- und Wahrscheinlichkeitsfunktionen.  
* Offline-Rendering über einen separaten AudioContext.

### **Effekte**

* Reverb.  
* Freeverb-artige Modelle.  
* JC-Reverb.  
* Feedback Delay.  
* Ping-Pong Delay.  
* Chorus.  
* Phaser.  
* Flanger-Konstruktionen.  
* Tremolo.  
* Vibrato.  
* Auto Filter.  
* Auto Panner.  
* Auto Wah.  
* Distortion.  
* Chebyshev Waveshaping.  
* Bit Crusher.  
* Frequency Shifter.  
* Pitch Shift.  
* Stereo Widener.  
* EQ.  
* Compressor.  
* Limiter.  
* Multiband-Kompression.  
* Convolution über native Web-Audio-Faltung.

### **Vorteile**

* Perfekt für eine sofort benutzbare Website.  
* Prompt, Generierung und Wiedergabe in derselben Anwendung.  
* Kein lokaler Audio-Server.  
* MIT-Lizenz.  
* Sehr gut dokumentiert.  
* Leicht mit React, Next.js oder Vanilla TypeScript kombinierbar.  
* Gute visuelle Echtzeitdarstellung.  
* Benutzer können Parameter live verändern.

### **Nachteile**

* Browser benötigen eine Benutzeraktion, bevor Audio startet.  
* Lange Offline-Renderings und große Samplemengen belasten Speicher und Browser.  
* Die Klangtiefe liegt unter SuperCollider oder Csound.  
* Browser und AudioContext können sich je nach Plattform unterschiedlich verhalten.  
* Für endgültige Alben wäre ein serverseitiger Renderer zuverlässiger.

**Gesamturteil:** Erste Wahl für eine interaktive Webdemo; nicht zwingend erste Wahl für den finalen Albumrenderer.

---

## **8\. Surge XT – ausgereifter hybrider Synthesizer**

[Surge XT](https://github.com/surge-synthesizer/surge) ist ein großer, ausgereifter hybrider Open-Source-Synthesizer. Besonders interessant ist, dass das Repository Python-Bindings über `pybind` bereitstellt.

### **Klangerzeugung**

* Klassische virtuelle Analogoszillatoren.  
* Sägezahn, Rechteck, Puls, Sinus und weitere Wellenformen.  
* Wavetable-Oszillatoren.  
* Wavetable-Morphing.  
* Window-Oszillatoren.  
* Sample-and-Hold- und Noise-basierte Quellen.  
* FM-Verfahren.  
* Ringmodulation.  
* Oszillatorsynchronisation.  
* Unison.  
* Stereo-Unison.  
* Suboszillatoren.  
* Waveshaping.  
* Variable Oszillatorcharaktere.  
* Filter mit zahlreichen analogen und digitalen Modellen.  
* Multimode-Filter.  
* Serien- und Parallelschaltung von Filtern.  
* Resonanz bis in selbstoszillierende Bereiche.  
* Keytracking.  
* Drive und nichtlineare Filterstufen.

### **Modulation**

* Mehrere LFOs.  
* Step-Sequencer.  
* MSEG-artige komplexe Hüllkurven.  
* ADSR-Hüllkurven.  
* Zufallsmodulation.  
* Modulationsmatrix.  
* Modulation vieler Parameter auf Stimmenebene.  
* Makroregler.  
* Velocity, Aftertouch und andere MIDI-Quellen.  
* MPE-Unterstützung.  
* Mikrotonale Stimmungen.

### **Effekte**

* Delay.  
* Chorus.  
* Phaser.  
* Flanger.  
* Reverb.  
* Distortion.  
* Saturation.  
* EQ.  
* Dynamikprozessoren.  
* Frequency Shifting.  
* Modulationseffekte.  
* Effektketten auf Szenen- und globaler Ebene.  
* Separate Surge-FX-Varianten.

### **Eignung für Ambient**

* Sehr gute schwebende Pads.  
* Langsame Wavetablefahrten.  
* Komplexe modulierte Drones.  
* Große Unison-Flächen.  
* Bewegliche Filtertexturen.  
* Makroparameter können direkt aus einem KI-Plan gespeist werden.  
* Bestehende Presetstruktur kann als Zielrepräsentation dienen.  
* Python-Bindings ermöglichen direkte native Steuerung.

### **Nachteile**

* Sehr große C++-Codebasis.  
* Als kompletter Synthesizer schwerer zu zerlegen als DaisySP oder Faust.  
* GPL-3.0.  
* Für einen eigenen Closed-Source-Kern nicht ohne Weiteres geeignet.  
* Ein Host- oder Plugin-Workflow ist komplexer als die Steuerung von SuperCollider.

**Gesamturteil:** Sehr wertvoll als Klangquelle, Referenzimplementierung und Presetgenerator; weniger geeignet als kompletter Produktkern.

---

## **9\. isobar – generative Komposition in Python**

[isobar](https://github.com/ideoforms/isobar) wurde für algorithmische Komposition, generative Musik und Sonifikation entwickelt. Es erzeugt keine hochwertigen Klänge selbst, aber musikalische Ereignisse, MIDI, OSC und Dateien.

### **Grundelemente**

* `Timeline` als Zeitachse.  
* Internes Tempo.  
* Synchronisation zu externer Clock.  
* Patterns als Ereignisvorlagen.  
* Events mit Tonhöhe, Dauer, Velocity und Steuerwerten.  
* OutputDevices.  
* MIDI-Ausgabe.  
* MIDI-Dateien.  
* OSC.  
* frei definierbare Python-Aktionen.  
* Hintergrundbetrieb.  
* Ableton-Link- und MIDI-Clock-nahe Workflows.

### **Pattern-Familien**

* Feste Sequenzen.  
* Schleifen.  
* arithmetische Serien.  
* geometrische Serien.  
* Vorwärts-/Rückwärtsbewegung.  
* Ping-Pong.  
* Permutationen.  
* Teilsequenzen.  
* rotierende Sequenzen.  
* zufällige Auswahl.  
* gewichtete Zufallsauswahl.  
* White Noise.  
* Brownian Noise.  
* Random Walk.  
* Coin Toss.  
* probabilistisches Überspringen.  
* zufällige Vertauschungen.  
* exponentiell gewichtete Zufallswerte.  
* Euclidean Rhythms.  
* Markovketten.  
* L-Systeme.  
* stochastische L-Systeme.  
* Arpeggiatoren.  
* skalengebundene Tonhöhen.  
* Filterung nach Tonart.  
* nächster zulässiger Ton in einer Skala.  
* MIDI-Note-zu-Frequenz-Umwandlung.  
* Notenweises Ein- und Ausblenden.  
* zufälliges Ein- und Ausblenden.  
* Sinusförmige Tempoverformung.  
* Rallentando.  
* generierte Pattern-Generatoren.

### **Ambient-Anwendungen**

* Ereignisdichten, die sich über zehn Minuten langsam verändern.  
* Markovketten für harmonische Felder.  
* Brownian Motion für Filter, Tonhöhe und Panorama.  
* L-Systeme für langfristige Form.  
* probabilistische Auslassungen.  
* Euclidische Verteilungen für seltene Glocken- oder Impulsereignisse.  
* automatische Fade-in- und Fade-out-Strukturen.  
* voneinander unabhängige langsame Patterns.  
* Reaktion auf Wetter-, Sensor- oder Benutzerdaten.  
* Erzeugung von MIDI-Stems vor dem eigentlichen Rendering.

### **Vorteile**

* MIT-Lizenz.  
* Python-native.  
* Reif und fokussiert.  
* Leicht mit Supriya, Csound, Hardware oder Plugins verbindbar.  
* Regeln sind verständlich und prüfbar.  
* Sehr gut für deterministische Seeds.  
* Ein LLM kann Patternparameter leichter erzeugen als rohen DSP-Code.

### **Nachteile**

* Kein eigener Klangkern.  
* Musiktheoretische Tiefe begrenzt.  
* Albumdramaturgie muss darüber gebaut werden.  
* Pattern allein ergeben noch keine musikalisch überzeugende Langform.

**Gesamturteil:** Einer der besten Bausteine für den generativen Kompositionsagenten.

---

## **10\. MusicLang – tonale Grammatik und symbolische Transformation**

[MusicLang](https://github.com/MusicLang/musiclang) ist eine Python-Sprache zum Schreiben, Analysieren, Transformieren und Vorhersagen symbolischer Musik. Die aktuelle Lizenzdatei verwendet BSD-2-Clause. Die neuronalen Vorhersagekomponenten befinden sich in separaten Paketen und können anders lizenziert sein.

### **Musikalische Elemente**

* Tonarten.  
* Modi.  
* Skalen.  
* Stufenharmonik.  
* römische Stufenbezeichnungen.  
* Dur- und Mollakkorde.  
* Akkorderweiterungen.  
* Akkordfolgen.  
* relative Melodien.  
* absolute und relative Oktavlagen.  
* Notendauern.  
* Pausen.  
* Instrumente und Stimmen.  
* Dynamik.  
* Artikulation.  
* Taktarten.  
* mehrstimmige Scores.  
* harmonischer Kontext pro Abschnitt.

### **Transformationen**

* Transposition.  
* Wiederholung.  
* Verkürzung und Verlängerung.  
* Wechsel von Dur nach Moll.  
* Reharmonisierung.  
* Projektion eines Motivs auf eine neue Harmonie.  
* Oktavverschiebung.  
* Rhythmische Transformation.  
* automatische Begleitstimmen.  
* Counterpoint-Funktionen.  
* Erhalt einzelner fester Stimmen.  
* Import von MIDI.  
* Export nach MIDI.  
* Export nach MusicXML.  
* textuelle Darstellung musikalischer Strukturen.

### **KI-Eignung**

* Musikalische Strukturen besitzen eine kompakte Textrepräsentation.  
* Ein LLM kann diese Darstellung leichter bearbeiten als rohe MIDI-Bytes.  
* Harmonie kann unabhängig vom Sounddesign geplant werden.  
* Der Agent kann Teile maskieren und neu erzeugen.  
* Fortsetzung und Inpainting sind möglich.  
* Eine bestehende Passage kann in einem neuen harmonischen Kontext rekonstruiert werden.  
* Der symbolische Score bleibt interpretierbar.  
* Ergebnisse können vor dem Rendern geprüft werden.

### **Ambient-Einsatz**

* Modale Felder statt funktionaler Pop-Harmonik.  
* Akkorde mit langen Liegezeiten.  
* Pedaltöne.  
* Quart- und Quintschichtungen.  
* offene Voicings.  
* parallele Akkordbewegungen.  
* minimale harmonische Veränderung.  
* sanfte Voice-Leading-Regeln.  
* seltene harmonische Ereignisse.  
* geplante Aufhellung oder Verdunkelung über einen Track.  
* albumweite Wiederkehr bestimmter Intervalle oder Motive.  
* kontrollierte Variation desselben Materials über mehrere Tracks.

### **Companion-Projekt**

[M(AI)DI](https://github.com/MusicLang/maidi) ist ein Apache-2.0-lizenziertes Schwesterprojekt für MIDI-Manipulation, automatische Tags, Akkorderkennung sowie die Anbindung symbolischer Musik-KI-Modelle und APIs.

### **Nachteile**

* Kein Audio.  
* Kleinere Community als music21 oder etablierte Sequencer.  
* Fokus stärker auf tonale Musik als auf reine Klangflächen.  
* Vorhersagemodelle und externe APIs müssen separat bewertet werden.

**Gesamturteil:** Gute Grundlage für die harmonische Intelligenz der Maschine.

---

## **11\. DaisySP – produktfreundliche DSP-Bibliothek in C++**

[DaisySP](https://github.com/electro-smith/DaisySP) ist eine modulare MIT-lizenzierte C++-DSP-Bibliothek. Sie kann für Embedded Hardware, Plugins, mobile Apps und VCV-Rack-Module eingesetzt werden.

### **Kontrollgeneratoren**

* AD-Hüllkurven.  
* ADSR-Hüllkurven.  
* Phasor.  
* Liniengeneratoren.  
* Crossfade.  
* Random- und aleatorische Hilfsfunktionen.  
* Signal-Smoothing.  
* DC-Blocker.

### **Oszillatoren und Synthese**

* Standardoszillator.  
* bandlimitierte Oszillatoren.  
* FM mit zwei Operatoren.  
* Formantoszillator.  
* Harmonic Oscillator.  
* Oscillator Bank.  
* Grainlet.  
* Vosim.  
* Z-Oszillator.  
* Wavetable-nahe Verfahren.  
* additive Synthese.  
* subtraktive Synthese.  
* FM.  
* Wavefolding.  
* Physical Modeling.  
* Karplus-Strong.  
* Modal-Synthese.  
* Resonatoren.  
* String-Modelle.  
* Particle- und Dust-Generatoren.  
* Fractal Noise.  
* White Noise.  
* Clocked Noise.

### **Perkussive Modelle**

* analoge Bassdrum.  
* synthetische Bassdrum.  
* analoge Snare.  
* synthetische Snare.  
* Hi-Hat.  
* Drip.  
* modale perkussive Stimmen.

### **Filter**

* One-Pole Lowpass.  
* One-Pole Highpass.  
* Biquad.  
* State-Variable-Filter.  
* Ladder-Filter.  
* Moog-artige Filter.  
* FIR.  
* resonierende Filter.  
* ungewöhnliche SOAP-Filterkomponenten.

### **Effekte**

* Chorus.  
* DelayLine.  
* Decimator.  
* Flanger.  
* Phaser.  
* Tremolo.  
* Overdrive.  
* Wavefolder.  
* Pitch Shifter.  
* Sample Rate Reduction.  
* Limiter.  
* ReverbSc.  
* Looper.  
* Granular Player.

### **Vorteile**

* MIT-Lizenz.  
* Gut in Closed-Source-Produkte integrierbar.  
* Keine große Host-Anwendung nötig.  
* Kleine, austauschbare Bausteine.  
* Läuft auf Desktop, Mobilgerät und Embedded Hardware.  
* Gute Basis für ein späteres physisches Ambient-Gerät.  
* Parameter lassen sich gut in einer eigenen sicheren DSL kapseln.

### **Nachteile**

* Keine fertige Albumkomposition.  
* Kein großer Plugin-Host.  
* Viele Verbindungen, Polyphonie und Voice Management müssen selbst entwickelt werden.  
* Weniger fertige Hochglanzinstrumente als Surge XT.

**Gesamturteil:** Sehr gute Wahl für die zweite Produktgeneration mit eigenem Audiokern.

---

## **12\. STK – physikalisch modellierte und organische Klänge**

[STK](https://github.com/thestk/stk) ist das „Synthesis ToolKit in C++“ von Perry Cook und Gary Scavone. Es besteht aus portablen Echtzeit-DSP- und Syntheseklassen und steht unter einer sehr permissiven MIT-artigen Lizenz.

### **Physikalische Blasinstrumentmodelle**

* Klarinettenmodelle.  
* Flötenmodelle.  
* Saxofonmodelle.  
* Blechblasinstrumente.  
* Flaschen- und Hohlraumresonanzen.  
* Breath-Noise.  
* nichtlineare Rohrblattmodelle.  
* Rohr- und Bohrungsresonanzen.

### **Saitenmodelle**

* Plucked String.  
* Karplus-Strong.  
* steife Saiten.  
* Mandolinenmodelle.  
* Sitar-artige Modelle.  
* gestrichene Saiten.  
* Resonanzkörper.  
* gekoppelte Saiten.

### **Modale und perkussive Modelle**

* Modal Bar.  
* Banded Waveguide.  
* zweidimensionale Meshes.  
* Shaker-Modelle.  
* Resonatoren.  
* gestimmte Metallkörper.  
* Glockenartige FM-Modelle.  
* Tube Bell.  
* Rhodes- und Wurlitzer-artige Modelle.  
* Hammond-artige Modelle.  
* metallische FM-Klänge.

### **Signalverarbeitung**

* Filter.  
* Pole-Zero-Netze.  
* Biquads.  
* Delays.  
* Echo.  
* Chorus.  
* Pitch Shift.  
* JCRev.  
* NRev.  
* PRCRev.  
* FreeVerb-nahe Algorithmen.  
* Audioeingang und \-ausgang.  
* MIDI.  
* Socket- und Textsteuerung.  
* WAV-, AIFF-, RAW- und weitere Ausgaben.  
* Echtzeit- und Dateirendering.

### **Ambient-Potenzial**

* Fantasieinstrumente, die zwischen Glas, Metall und Holz liegen.  
* langsam angeregte Resonanzkörper.  
* kaum hörbare Breath-Noise-Flächen.  
* Saiten mit extrem langer Dämpfung.  
* modale Drones.  
* glockenartige Wolken.  
* resonierende Räume aus gekoppelten Instrumenten.  
* physikalisch glaubwürdige, aber nicht klar identifizierbare Klangobjekte.  
* Parameterdrift in Material, Dämpfung und Anregungsposition.  
* gute Grundlage für organische Klangpaletten jenseits typischer Wavetables.

### **Nachteile**

* Ältere C++-Architektur.  
* Weniger moderne Abstraktionen als DaisySP oder Faust.  
* Kein Kompositionssystem.  
* Für ein fertiges Produkt müssen Voice Management, Presets und moderne Plugin-Schnittstellen ergänzt werden.

**Gesamturteil:** Besonders wertvoll, wenn deine Maschine nicht nur Pads, sondern eigenständige organische Klangwelten erzeugen soll.

---

## **13\. FunDSP – moderner prozeduraler Audiokern in Rust**

[FunDSP](https://github.com/SamiPerttu/fundsp) ist eine Rust-Bibliothek für Audioverarbeitung und Synthese. DSP-Netzwerke werden mit einer kompakten algebraischen Graphnotation zusammengesetzt.

### **Architektur**

* AudioNodes.  
* statisch typisierte Ein- und Ausgänge.  
* serielle Verkettung.  
* parallele Verkettung.  
* Signalaufteilung.  
* Summierung.  
* Feedback.  
* Stack-allokierte und inlinbare Graphen.  
* Compile-Time-Prüfung der Verbindungen.  
* dynamische `Net`\-Graphen.  
* Echtzeitgeeignetes Frontend/Backend für Sequenceränderungen.  
* analytische Frequenzganganalyse linearer Netzwerke.  
* Latenzanalyse.  
* `no_std`\-Unterstützung für Embedded-Umgebungen.

### **Oszillatoren**

* Sinus.  
* bandlimitierter Sägezahn.  
* Rechteck.  
* Dreieck.  
* Puls.  
* Soft Saw.  
* PolyBLEP-Oszillatoren.  
* DSF-Saw.  
* DSF-Square.  
* Hammond-artige Wellenformen.  
* Orgelwellenformen.  
* Wavetables.  
* Rössler-Chaos.  
* FM als kompakter Signalgraph.

### **Noise und Zufall**

* White Noise.  
* Pink Noise.  
* Brown Noise.  
* MLS Noise.  
* deterministische Pseudorandom-Phasen.  
* Spline Noise.  
* Fractal Noise.  
* Ease Noise.  
* Seed-basierte Reproduzierbarkeit.

### **Filter**

* Lowpass.  
* Highpass.  
* Bandpass.  
* Notch.  
* Allpass.  
* Bell.  
* Low Shelf.  
* High Shelf.  
* Butterworth.  
* State-Variable-Filter.  
* morphende Filter.  
* Resonatoren.  
* FIR.  
* DC Blocker.  
* Attack-/Release-Follower.  
* nichtlineare „dirty“ Biquads.  
* Feedback-Biquads.  
* Moog-Ladder-Filter.

### **Effekte und Audiofunktionen**

* Chorus.  
* variable Delays.  
* Tapped Delays.  
* Waveshaping.  
* Resampling.  
* Frequenzbereichsresynthese.  
* 32-kanalige Feedback-Delay-Network-Reverbs.  
* modulierte Reverbs.  
* Allpass-Loop-Reverb.  
* WAV-Rendering.  
* Audioimport über Symphonia.  
* FIR-Sinc-Resampling.  
* Multichannel-Wave-Abstraktion.

### **Vorteile**

* MIT oder Apache-2.0.  
* Speichersicheres Rust.  
* Sehr gut für einen eigenen Server oder Desktopkern.  
* Deterministische prozedurale Erzeugung.  
* Kleine Deployment-Artefakte möglich.  
* Gut für langfristig wartbare proprietäre Produkte.  
* Gute Basis für Plugin- oder Game-Audio-Integration.

### **Nachteile**

* Keine umfassende Musikkomposition.  
* Kleinere Community.  
* Weniger fertige Instrumente als SuperCollider.  
* KI-Orchestrierung aus Python benötigt eine FFI-, IPC- oder API-Schicht.

**Gesamturteil:** Eine sehr attraktive technische Zukunftsbasis, wenn du einen eigenen Audio-Server in Rust entwickeln willst.

---

## **14\. Vital – spektakulärer Wavetable-Klang mit Lizenzhürden**

[Vital](https://github.com/mtytel/vital) ist ein Spectral-Warping-Wavetable-Synthesizer. Der Quellcode steht unter GPL-3.0; für proprietäre Produkte bietet der Autor eine gesonderte Lizenzierung an. Das Repository wird laut README zeitversetzt gegenüber Binärveröffentlichungen aktualisiert.

### **Klangerzeugung**

* hochwertige Wavetable-Oszillatoren.  
* Wavetable-Position als Modulationsziel.  
* Frequenz-Warping.  
* Wave-Warping.  
* spektrale Verformung.  
* saubere Nyquist-Begrenzung.  
* effizientes Unison.  
* Stereo-Unison.  
* FM zwischen Oszillatoren.  
* Phase Distortion-nahe Verformungen.  
* Sample-Import.  
* Noise- und zusätzliche Klangquellen.  
* zwei routbare Voice-Filter.  
* analoge und digitale Filtermodelle.  
* kontinuierliche Filtermorphs.  
* Audio-Rate-Modulation.  
* Filter-FM.  
* Waveshaping.  
* Distortion.  
* umfangreiche Effektsektion.

### **Modulation**

* frei zeichnbare LFOs.  
* Stereo-teilbare LFOs.  
* Keytracking.  
* Hüllkurven mit editierbaren Kurven.  
* Random-Modulatoren.  
* Makroparameter.  
* Modulationsmatrix.  
* Drag-and-Drop-Modulation.  
* mikrotonale Stimmungen.  
* Velocity- und Expression-Steuerung.

### **Ambient-Einsatz**

* lange, spektral wandernde Pads.  
* gläserne Texturen.  
* sich langsam verformende Drones.  
* breite Unison-Flächen.  
* komplexe Obertonspektren.  
* modulierte Filterfelder.  
* morphende Geräuschflächen.  
* starke Preset- und Makrostruktur als mögliches KI-Zielformat.

### **Besonderheit**

Der kommerzielle Vital-Dienst besitzt „Text-to-Wavetable“. Das bedeutet nicht automatisch, dass der offene GitHub-Code diesen Dienst oder dessen Modelle frei zur Weiterverwendung enthält.

### **Wichtige Einschränkungen**

* GPL-3.0.  
* Für Closed Source soll laut README eine separate Lizenz vereinbart werden.  
* Namen und Marken dürfen nicht einfach übernommen werden.  
* Mitgelieferte Presets stehen unter einer anderen Lizenz und dürfen nicht automatisch weiterverteilt werden.  
* Das Repository nimmt laut README keine Pull Requests an.  
* Der veröffentlichte Code kann gegenüber der aktuellen Binärversion zurückliegen.  
* Als Grundlage für ein neues kommerzielles Produkt besteht damit ein höheres Abhängigkeitsrisiko.

**Gesamturteil:** Klanglich hervorragend; eher als Inspirations-, Preset- und Referenzsystem als als unkritischer Produktkern.

---

## **15\. AudioCraft – neuronale Prompt-Musik als Zusatzsystem**

[AudioCraft](https://github.com/facebookresearch/audiocraft) ist Metas Bibliothek für Deep-Learning-basierte Audio- und Musikgenerierung. Sie enthält unter anderem MusicGen, AudioGen und EnCodec.

### **Bestandteile**

* `MusicGen` für textkonditionierte Musik.  
* Melody Conditioning.  
* Fortsetzung musikalischer Audiodaten.  
* `AudioGen` für allgemeine Geräusch- und Klanggenerierung.  
* `EnCodec` als neuronaler Audiocodec und Tokenizer.  
* autoregressive Audiotokenmodelle.  
* Trainings- und Inferenzcode.  
* Modellkonfigurationen.  
* Datenpipelines.  
* Abtastraten- und Codec-Konfigurationen.  
* Batchgenerierung.  
* verschiedene Modellgrößen.  
* Text- und Audiokonditionierung.  
* experimentelle Forschungskomponenten wie MAGNeT bzw. weitere im Framework veröffentlichte Modelle.

### **Sinnvolle Rolle in deiner Maschine**

* Prompts in erste akustische Moodboards verwandeln.  
* Referenztexturen erzeugen.  
* kurze atmosphärische Skizzen liefern.  
* semantisch testen, ob ein Prompt eher „kalt“, „warm“, „weit“ oder „mechanisch“ klingt.  
* Material für interne Klanganalysen erzeugen.  
* rhythmische oder klangliche Ideen vorschlagen.  
* eine Referenz erzeugen, die anschließend mit echter Synthese neu konstruiert wird.  
* Vergleichsbasis für einen Bewertungsagenten.

### **Warum nicht als Hauptkern?**

* Langfristige musikalische Form bleibt schwer steuerbar.  
* Mehrere Tracks eines Albums behalten nicht automatisch dieselbe klangliche Identität.  
* Exakte Harmonik, Modulation und Wiederholbarkeit sind begrenzt.  
* Direkt erzeugte Audiodaten sind schlechter editierbar als symbolische Scores und Syntheseparameter.  
* Lange Tracks benötigen erhebliche Rechenzeit und Speicher.  
* Die Erzeugung ganzer Alben ist eher „Audio aus einem Modell“ als eine nachvollziehbare Kompositionsmaschine.  
* Die Modellgewichte sind unter CC-BY-NC 4.0 veröffentlicht und damit nicht für eine normale kommerzielle Nutzung geeignet. Der Code selbst ist MIT-lizenziert.

**Gesamturteil:** Sehr gut als Forschungs- und Ideengeber, aber nicht als kommerzieller Hauptmotor.

---

# **Meine empfohlene Gesamtarchitektur**

flowchart TD  
    A\["Benutzerprompt \+ Seed"\] \--\> B\["LLM: strukturierter Albumplan"\]  
    K\["Ambient-Wissensbasis"\] \--\> B  
    B \--\> C\["MusicLang / isobar: musikalische Ereignisse"\]  
    C \--\> D\["Supriya: sichere Python-Steuerung"\]  
    D \--\> E\["SuperCollider: Synthese und Rendering"\]  
    E \--\> F\["Audioanalyse und Kritik"\]  
    F \--\>|Korrektur| C  
    F \--\> G\["Stems, WAV, FLAC und Metadaten"\]

## **1\. Prompt- und Planungsschicht**

Der Benutzer schreibt beispielsweise:

> „Erzeuge ein 48-minütiges dunkles Ambient-Album über das langsame Auftauen einer verlassenen Raumstation. Kaum Rhythmus, tiefe Drones, vereinzelte metallische Signale, ab Track vier etwas wärmer. Keine Stimmen.“

Das LLM erzeugt daraus keine Musikdatei, sondern:

* Albumtitel.  
* Anzahl der Tracks.  
* Tracklängen.  
* dramaturgische Funktion jedes Tracks.  
* spektrale Entwicklung.  
* harmonische Entwicklung.  
* Dichtekurven.  
* Rollen der Klangschichten.  
* erlaubte Syntheseverfahren.  
* Effekt- und Raumkonzept.  
* Seed-Hierarchie.  
* Regeln für Wiederkehr und Variation.  
* Negativregeln.  
* Übergänge.  
* Zielwerte für Analyse und Mastering.

## **2\. Ambient-Wissensbasis**

Das verdichtete Wissen sollte nicht nur aus Text-RAG bestehen. Es sollte in ausführbare Regeln überführt werden.

### **Klangdesignwissen**

* Welche Oszillatoren ergeben welche spektrale Wirkung?  
* Wie erzeugt man analoge Instabilität?  
* Wie langsam darf eine Modulation sein?  
* Wie verhindert man statische Drones?  
* Wie baut man Resonatorwolken?  
* Wie werden Granulartexturen weich statt klickend?  
* Wie vermeidet man harsche Höhen?  
* Wie erzeugt man Tiefe ohne kompletten Frequenzbrei?  
* Welche Delays funktionieren in Feedbackschleifen?  
* Wie bleibt Infinite Reverb numerisch stabil?  
* Welche Parameter dürfen audio-rate moduliert werden?  
* Welche Parameteränderungen benötigen Smoothing?  
* Wie verteilt man Klangereignisse räumlich?

### **Kompositionswissen**

* modale Harmonik.  
* Pedaltöne.  
* offene Quinten.  
* Quartschichtungen.  
* Cluster mit kontrollierter Rauigkeit.  
* sehr langsames Voice Leading.  
* harmonische Felder statt schneller Akkordfolgen.  
* motivische Wiederkehr ohne offensichtliche Loops.  
* Ereignisdichte als Formparameter.  
* Stille als musikalisches Ereignis.  
* Übergänge durch spektrale Überblendung.  
* Trackübergreifende Motive.  
* Albumweite Tonhöhenzentren.  
* Temperatur-, Helligkeits- und Dichtekurven.  
* kontrollierte Entropie.  
* Verhältnis von Wiederholung und Neuheit.  
* vorbereitete Höhepunkte.  
* Rücknahme nach einem Höhepunkt.  
* unterschiedliche Zeitskalen für Mikro-, Meso- und Makroform.

### **Produktionswissen**

* Headroom.  
* True Peak.  
* integrierte Lautheit.  
* Dynamikbereich.  
* Bassmanagement.  
* Mono-Kompatibilität.  
* Stereo-Korrelation.  
* DC Offset.  
* Klick- und Dropout-Erkennung.  
* übermäßige Resonanz.  
* Maskierung.  
* spektrale Ermüdung.  
* Abstände zwischen Klangereignissen.  
* Stems und Effektreturns.  
* Fade-Längen.  
* dithering- und Exportregeln.

## **3\. Eigene Ambient-DSL**

Das zentrale geistige Eigentum wäre nicht der verwendete Open-Source-Synthesizer. Es wäre deine eigene kontrollierte Ambient-Sprache.

Mögliche Elemente:

* `album_arc`  
* `track_function`  
* `emotional_temperature`  
* `spectral_brightness`  
* `harmonic_tension`  
* `event_density`  
* `motion_speed`  
* `spatial_width`  
* `depth`  
* `grain_activity`  
* `noise_ratio`  
* `tonal_ambiguity`  
* `repetition_memory`  
* `surprise_budget`  
* `silence_probability`  
* `transition_type`  
* `layer_role`  
* `synthesis_recipe`  
* `modulation_recipe`  
* `mixing_constraints`  
* `seed`

## **4\. Rollen der Klangebenen**

Jeder Track könnte aus kontrollierten Rollen zusammengesetzt werden:

* Fundament-Drone.  
* harmonische Drone.  
* bewegliche Padfläche.  
* granulare Textur.  
* atmosphärisches Rauschen.  
* resonierendes Objekt.  
* seltenes Signalmotiv.  
* subharmonischer Puls.  
* entfernte rhythmische Textur.  
* Field-Recording-Ebene.  
* Übergangsebene.  
* spektraler Schimmer.  
* räumlicher Effektreturn.  
* Kontrastebene.  
* Stille beziehungsweise negative Ebene.

## **5\. Bewertungsagent**

Nach jedem Rendering sollte ein Kritiksystem mindestens prüfen:

* Clipping.  
* True Peak.  
* Lautheit.  
* Dynamik.  
* DC Offset.  
* Klicks.  
* überlange digitale Stille.  
* zu hohe Stereokorrelation.  
* zu geringe Mono-Kompatibilität.  
* zu starke Bassenergie.  
* schmerzhafte Resonanzspitzen.  
* spektrale Monotonie.  
* zu viel konstante Energie.  
* fehlende Entwicklung.  
* zu schnelle harmonische Wechsel.  
* zu hohe Ereignisdichte.  
* erkennbare kurze Loops.  
* zu große Ähnlichkeit zwischen Tracks.  
* fehlende albumweite Identität.  
* Einhaltung des Prompts.  
* Einhaltung der Negativregeln.

---

# **Welche Kombination ich tatsächlich bauen würde**

## **MVP**

* **SuperCollider** als Audiokern.  
* **Supriya** als Python-Schnittstelle.  
* **isobar** für generative Ereignisse.  
* eigene Pydantic-Modelle als Ambient-DSL.  
* LLM plus RAG für Promptinterpretation.  
* librosa oder Essentia für Analyse.  
* FFmpeg für Export und Konvertierung.  
* PostgreSQL oder zunächst SQLite für Albumpläne, Seeds und Renderhistorie.  
* getrennte WAV-Stems.  
* Non-Realtime-Rendering.

Damit wäre ein erster überzeugender Prototyp realistisch.

## **Kommerzielle zweite Generation**

* Eigene besonders wichtige Synthesizer in **Faust** oder **DaisySP** neu implementieren.  
* SuperCollider zunächst als externer Renderer behalten.  
* Eigene kuratierte Klangbibliothek.  
* Eigene Preset- und Recipe-Sprache.  
* automatische Variations- und Mutationslogik.  
* lokaler Renderer oder Rendering-Cluster.  
* Versionierung jedes Albumplans.  
* Qualitätssicherung und Regressionstests für den Klang.

## **Was ich nicht tun würde**

* AudioCraft als alleinigen Albumgenerator verwenden.  
* ungeprüften LLM-Code direkt im Audioprozess ausführen.  
* das Produkt komplett auf Vital aufbauen, bevor eine kommerzielle Lizenz geklärt ist.  
* alle denkbaren Synthesearten sofort integrieren.  
* den Prompt direkt auf 500 unstrukturierte Synthesizerparameter abbilden.  
* Künstlernamen als zentrale Klangbeschreibung verwenden.  
* lange Tracks ausschließlich aus kurzen Loops zusammensetzen.  
* Zufall ohne Seeds und ohne musikalische Begrenzungen einsetzen.

# **Endfazit**

Die stärkste Basis ist nicht ein Text-to-Audio-Modell, sondern eine **wissensbasierte algorithmische Kompositionsmaschine mit echter Synthese**.

Die entscheidende Kombination lautet:

1. **SuperCollider** erzeugt den Klang.  
2. **Supriya** verbindet den Klangkern mit Python und der KI.  
3. **isobar und MusicLang** erzeugen kontrollierte musikalische Strukturen.  
4. Eine eigene **Ambient-DSL** verdichtet das Klang- und Kompositionswissen.  
5. **Faust oder DaisySP** liefern später einen eigenen, kommerziell leichter kontrollierbaren DSP-Kern.  
6. **AudioCraft** bleibt optionaler Ideengeber, nicht das Fundament.

Der eigentliche wirtschaftliche Wert läge dann nicht primär in den Open-Source-Repositories, sondern in deiner kuratierten Ambient-Wissensbasis, der Prompt-zu-Album-Übersetzung, den sicheren Syntheserezepten, der Bewertungslogik und der Fähigkeit, über 30 bis 90 Minuten eine kohärente musikalische Entwicklung zu erzeugen.

