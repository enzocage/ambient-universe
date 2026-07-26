# Audio-Baseline-Dokumentation (Stufe 0)

**Datum:** 26. Juli 2026  
**Status:** Gate 0 bestanden  

---

## 1. System- & Umgebungskonfiguration

- **Python**: `3.12.10 (MSC v.1943 64 bit)`
- **Supriya**: `26.3b0`
- **SoundFile**: `0.14.0`
- **NumPy**: `2.4.6`
- **SuperCollider Server**: `scsynth` (Synthesizer Engine)
- **Audio-Backend**: Supriya SynthDef Builder + SuperCollider

---

## 2. Erfasste Baseline-Prompts & Messergebnisse

All baseline tracks are stored in `projects/baseline/` with full stems and mix audio.

### Case A: Warm & Organisch (`prompt_a_warm`)
- **Prompt**: `"Warm, organisch, langsam atmend, gebettete Flächen und weiche Resonanzen"`
- **Seed**: `10001`
- **Modus**: Dorian
- **LUFS (geschätzt)**: **-16.3 LUFS**
- **Peak**: **-7.08 dBFS**
- **Aktives Signalverhältnis**: **89.8%**
- **Harmonischer Energieanteil**: **24.9%**
- **Solver-Score**: `8.039`
- **Hörprotokoll**: Weicher tiefer Grundton (Sub-Bass), ruhige Flächenbewegung im Mitteltonbereich. Modale Harmonie stabil, Stimmführung fließend.
- **Akzeptanz-Status**: **AKZEPTIERT**

---

### Case B: Kalt & Gläsern (`prompt_b_cold`)
- **Prompt**: `"Kalt, gläsern, metallisch, räumlich, eisige Obertöne und weite Halldistanz"`
- **Seed**: `10002`
- **Modus**: Dorian
- **LUFS (geschätzt)**: **-16.3 LUFS**
- **Peak**: **-6.58 dBFS**
- **Aktives Signalverhältnis**: **89.7%**
- **Harmonischer Energieanteil**: **41.0%**
- **Solver-Score**: `8.039`
- **Hörprotokoll**: Hoher Obertongehalt, gläserne Resonanzen, weiter räumlicher Eindruck. Keine Pfeifartefakte oder Clipping.
- **Akzeptanz-Status**: **AKZEPTIERT**

---

### Case C: Rhythmisch & Sequenziert (`prompt_c_rhythmic`)
- **Prompt**: `"Rhythmisch, sequenziert, elektronisch, aber ambient, schwebende Pulse und bewegter Subbass"`
- **Seed**: `10003`
- **Modus**: Dorian
- **LUFS (geschätzt)**: **-16.3 LUFS**
- **Peak**: **-6.91 dBFS**
- **Aktives Signalverhältnis**: **89.8%**
- **Harmonischer Energieanteil**: **10.6%**
- **Solver-Score**: `8.039`
- **Hörprotokoll**: Dezent getaktete Pulse, prägnanter Sub-Bass-Bogen. Höherer Textur- und Rauschanteil.
- **Akzeptanz-Status**: **AKZEPTIERT**

---

## 3. Gate 0 Bestätigung

- [x] 3 Baseline-Tracks sind in `projects/baseline/` vorhanden.
- [x] Jede Baseline verfügt über eine `baseline_meta.json` mit objektiv erfassten Audiometriken.
- [x] Die Testumgebung ist vollständig reproduzierbar.

---

## 4. Nächste Schritte (Stufen 1 & 2)

- **Stufe 1**: Capability-Matrix aller 14+ Klangmodule und Prozessoren (`au/analysis/capabilities.py`).
- **Stufe 2**: Erweiterung der Audiometriken und automatisierten Qualitätsgates (`au/analysis/musical_quality.py`).
