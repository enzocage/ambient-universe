# Synth- und Presetquellen

Die Preset-Schicht verwendet eigene, deterministisch erzeugte Parameterdaten.
Damit werden keine fremden Factory-Bänke in das Repository kopiert. Jede
Preset-ID ist reproduzierbar und enthält `source` und `license` für spätere
Importe.

## Geprüfte Referenzen

- [Surge XT Repository](https://github.com/surge-synthesizer/surge): freie
  Open-Source-Synthese unter GPL-3.0; Architektur und offene Preset-/Patch-
  Konzepte dienen als Referenz.
- [Surge XT Manual](https://surge-synthesizer.github.io/manual-xt/index.html):
  beschreibt Wavetable-, FM-, Filter-, Modulations- und Preset-Konzepte.
- [Dexed Repository](https://github.com/asb2m10/dexed): GPL-3.0 und ein
  praktisches FM-/DX7-Parameter-Modell; wird als kompatible Quelle für eine
  spätere `.syx`-/DX7-Importbrücke geführt.
- [Vital](https://vital.audio/): Factory-Inhalte werden nicht kopiert. Die
  [Lizenzdiskussion](https://forum.vital.audio/t/sound-design-question/14601)
  zeigt, dass unveränderte Inhalte nicht als eigene Presetbank weitergegeben
  werden sollten.

## Implementierte Bank

`au.presets.catalog` enthält 30 renderbare Synth-Profile, die auf vorhandene
interne Generatoren abgebildet werden, sowie 36 eigene Klangarchetypen pro
Profil: insgesamt 1080 eindeutige Presets. Die Auswahl ist seed-stabil,
rollenbewusst und liefert Parameter plus Makros an die Vorschlags-Engine.
