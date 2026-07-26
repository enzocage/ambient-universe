"""Hashing fuer Reproduzierbarkeit (plan.md Paragraph 13.2).

``manifest.json`` haelt die Pruefsummen aller gerenderten Stems fest;
``au verify`` rendert neu und vergleicht.

**Warum nicht einfach die Datei hashen?**
libsndfile schreibt bei Float-WAVs einen ``PEAK``-Chunk mit einem Zeitstempel
in den Header. Zwei bit-identische Renderings, eine Sekunde auseinander,
haetten damit verschiedene Dateihashes. Der belastbare Fingerabdruck ist
deshalb :func:`sha256_audio` ueber den *dekodierten Audioinhalt* plus Format.
:func:`sha256_file` bleibt fuer Nicht-Audio-Artefakte (Plaene, Manifeste) und
zur Diagnose erhalten.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_CHUNK = 1 << 20  # 1 MiB
_AUDIO_BLOCK = 1 << 16  # Frames je Leseblock — haelt den Speicher konstant


def sha256_file(path: Path) -> str:
    """SHA-256 einer Datei, streamend gelesen."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(_CHUNK):
            h.update(chunk)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_audio(path: Path) -> str:
    """Fingerabdruck des *Audioinhalts* — unabhaengig von Container-Metadaten.

    Gehasht werden Abtastrate, Kanalzahl und die dekodierten Abtastwerte in
    kanonischer float64-Darstellung. Damit ist der Wert stabil gegenueber
    Header-Zeitstempeln und vergleichbar ueber Containerformate hinweg.

    Der Speicherbedarf ist konstant: die Datei wird blockweise gelesen, ein
    20-Minuten-Stem wird nicht am Stueck geladen.
    """
    import soundfile as sf

    with sf.SoundFile(str(path)) as snd:
        h = hashlib.sha256()
        h.update(f"sr={snd.samplerate};ch={snd.channels}".encode())
        while True:
            block = snd.read(_AUDIO_BLOCK, dtype="float64", always_2d=True)
            if block.shape[0] == 0:
                break
            # ascontiguousarray: garantiert dieselbe Bytefolge unabhaengig
            # davon, wie soundfile den Puffer intern angelegt hat.
            import numpy as np

            h.update(np.ascontiguousarray(block).tobytes())
    return h.hexdigest()


def sha256_json(obj: Any) -> str:
    """Stabiler Hash einer JSON-serialisierbaren Struktur.

    Schluessel werden sortiert und Trennzeichen normalisiert, damit derselbe
    Inhalt unabhaengig von der Einfuegereihenfolge denselben Hash ergibt.
    """
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(payload.encode("utf-8"))
