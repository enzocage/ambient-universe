"""Der DNA-Agent: Prompt -> Album-DNA (plan.md Phase 4).

**Wichtiger Vorbehalt zum Umfang dieser Implementierung**

plan.md sieht hier ein LLM vor, das mit der Ambient-Wissensbasis argumentiert
und bei Unterbestimmtheit bis zu vier Rueckfragen stellt. Diese Codebasis hat
keinen Zugriff auf einen LLM-Dienst zur Laufzeit (keine API-Anbindung im
Ausfuehrungskontext). Implementiert ist deshalb ein **regelbasierter
Text-zu-DNA-Uebersetzer**: eine Stichwortanalyse des Prompts gegen ein
Vokabular von Charakterachsen, kombiniert mit den Vorgaben aus
``knowledge/composition_rules.yaml``.

Das ist ehrliches Engineering fuer die gegebene Umgebung, kein Ersatz fuer den
in plan.md beschriebenen Dialog. Die Schnittstelle (`generate_dna`) ist so
geschnitten, dass ein echter LLM-Aufruf sie ohne Aenderung am Aufrufer
ersetzen kann: er muesste nur dieselbe :class:`AlbumDNA` zurueckgeben.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from au.core.registry import VocabularyPolicy
from au.core.seeds import SeedPath
from au.dsl.dna import (
    AlbumDNA,
    Character,
    Comparator,
    GlobalBudgets,
    InnovationVector,
    NegativeRule,
    TargetMetrics,
)

#: Woerter, die eine Achse in eine Richtung ziehen. Bewusst klein und explizit
#: gehalten statt eines Embedding-Modells — nachvollziehbar und ohne
#: Netzwerkzugriff lauffaehig.
_WARMTH_WORDS = ("warm", "weich", "sanft", "golden", "sonnig", "gebettet")
_COLD_WORDS = ("kalt", "kuehl", "eisig", "hohl", "metallisch", "frost", "verlassen")
_BRIGHT_WORDS = ("hell", "gleissend", "glitzernd", "glas", "leuchtend", "schimmer")
_DARK_WORDS = ("dunkel", "finster", "tief", "schwarz", "schatten", "unterwasser")
_DENSE_WORDS = ("dicht", "voll", "ueberladen", "textur", "wolke")
_SPARSE_WORDS = ("karg", "sparsam", "leer", "reduziert", "vereinzelt", "minimal")
_WIDE_WORDS = ("weit", "raeumlich", "hallend", "unendlich", "kathedrale", "weite")
_INTIMATE_WORDS = ("nah", "intim", "eng", "trocken", "klein")
_INNOVATIVE_WORDS = ("experimentell", "ungewoehnlich", "neuartig", "fremd", "innovativ")
_CONVENTIONAL_WORDS = ("klassisch", "vertraut", "konventionell", "traditionell", "sanft")
_TENSE_WORDS = ("dissonant", "reibung", "spannung", "cluster", "unruhig")
_CONSONANT_WORDS = ("konsonant", "ruhig", "friedlich", "harmonisch", "still")

#: Standard-Negativregeln, die praktisch jedes Ambient-Werk teilt.
_BASE_NEGATIVE_RULES: tuple[NegativeRule, ...] = (
    NegativeRule(
        id="no_clipping",
        predicate=Comparator(metric="peak", operator="<", threshold=0.98),
        summary="Kein Signal darf die Vollaussteuerung erreichen.",
    ),
    NegativeRule(
        id="no_dc_offset",
        predicate=Comparator(metric="dc_offset_abs", operator="<", threshold=1e-3),
        summary="Kein hoerbarer Gleichanteil.",
    ),
    NegativeRule(
        id="no_short_loop",
        predicate=Comparator(metric="loop_visible_s", operator=">", threshold=180.0),
        summary="Keine Wiederholung wird vor drei Minuten hoerbar.",
    ),
)


def _score(text: str, words: tuple[str, ...]) -> float:
    """Anteil der Treffer, geglaettet auf [0, 1]."""
    hits = sum(1 for w in words if w in text)
    return min(1.0, hits / 2.0)


@dataclass(slots=True)
class DnaDraft:
    """Zwischenergebnis vor der Nutzerbestaetigung — entspricht dem kurzen
    Dialog aus plan.md, hier als strukturierte Rueckgabe statt als Chat."""

    dna: AlbumDNA
    open_questions: list[str] = field(default_factory=list)
    """Nicht-blockierende Hinweise auf Unterbestimmtheit, keine Pflichtantwort."""


def _extract_title(prompt: str) -> str:
    match = re.search(r'["„»]([^"“»]{3,60})["“«]', prompt)
    if match:
        return match.group(1).strip()
    words = re.findall(r"[A-Za-zÄÖÜäöüß]+", prompt)
    return " ".join(w.capitalize() for w in words[:3]) or "Untitled"


def generate_dna(prompt: str, *, seed_root: int, title: str | None = None) -> DnaDraft:
    """Uebersetzt einen freien Prompt in eine valide, geschlossene Album-DNA.

    Deterministisch bei gleichem Prompt und ``seed_root`` — kein Zufall in
    der Analyse selbst, nur in der spaeteren Nutzung des Seeds durch tiefere
    Ebenen.
    """
    text = prompt.lower()

    warmth = 0.5 + 0.5 * (_score(text, _WARMTH_WORDS) - _score(text, _COLD_WORDS))
    warmth = max(0.0, min(1.0, warmth))
    brightness = 0.5 + 0.5 * (_score(text, _BRIGHT_WORDS) - _score(text, _DARK_WORDS))
    brightness = max(0.0, min(1.0, brightness))
    density = 0.5 + 0.5 * (_score(text, _DENSE_WORDS) - _score(text, _SPARSE_WORDS))
    density = max(0.05, min(0.9, density * 0.3))  # Ambient-Dichte bleibt strukturell niedrig
    width = 0.5 + 0.5 * (_score(text, _WIDE_WORDS) - _score(text, _INTIMATE_WORDS))
    width = max(0.0, min(1.0, width))
    tension = 0.5 + 0.5 * (_score(text, _TENSE_WORDS) - _score(text, _CONSONANT_WORDS))
    tension = max(0.0, min(1.0, tension))
    innovation_level = 0.4 + 0.5 * (
        _score(text, _INNOVATIVE_WORDS) - _score(text, _CONVENTIONAL_WORDS)
    )
    innovation_level = max(0.0, min(1.0, innovation_level))

    descriptors = tuple(
        w for w in re.findall(r"[A-Za-zÄÖÜäöüß]{4,}", prompt) if w.lower() not in {"eine", "eines"}
    )[:12] or ("ambient",)

    character = Character(
        descriptors=descriptors,
        emotional_temperature=(warmth * 0.8, warmth),
        spectral_brightness=(brightness * 0.9, brightness),
        harmonic_tension_mean=tension,
        spatial_width=width,
        spatial_depth=max(0.3, width * 0.9),
        event_density_mean=density,
        tonal_ambiguity=0.3 + 0.3 * tension,
        silence_probability=0.35 - 0.2 * density,
        repetition_memory=0.4,
        surprise_budget=0.2 + 0.3 * innovation_level,
    )

    innovation = InnovationVector(
        timbral=innovation_level,
        formal=innovation_level * 0.8,
        harmonic=min(1.0, tension * 0.6 + innovation_level * 0.4),
        procedural=innovation_level * 0.6,
        production=innovation_level * 0.5,
    )

    no_voice = NegativeRule(
        id="no_voice_formants",
        predicate=Comparator(metric="spectral_centroid_hz", operator="<", threshold=4500.0),
        summary="Keine stimmaehnlichen Formanten im oberen Mittenband.",
    )
    negative_rules = (*_BASE_NEGATIVE_RULES, no_voice)

    vocabulary = VocabularyPolicy(
        prefer=("gen.drone.*", "gen.object.*"),
        allow=("gen.*", "prc.*", "mod.*"),
        forbid=("gen.neural.*",) if innovation_level < 0.7 else (),
    )

    dna = AlbumDNA(
        title=title or _extract_title(prompt),
        seed_root=seed_root,
        character=character,
        innovation_vector=innovation,
        negative_rules=negative_rules,
        vocabulary_policy=vocabulary,
        global_budgets=GlobalBudgets(),
        target_metrics=TargetMetrics(),
        identity_anchors_intent={},
    )

    questions: list[str] = []
    if len(descriptors) <= 1:
        questions.append(
            "Der Prompt liefert wenig Charaktervokabular — magst du 3-5 Adjektive ergaenzen?"
        )
    if warmth in (0.5,) and brightness in (0.5,):
        questions.append(
            "Weder Waerme noch Helligkeit sind erkennbar festgelegt — Standardwerte verwendet."
        )

    # Echte Widersprueche werden dem Menschen vorgelegt, nicht still aufgeloest
    # (plan.md 4.10, MI-L10-Direktive: "loese den Widerspruch nicht heimlich auf").
    if _score(text, _TENSE_WORDS) > 0 and _score(text, _CONSONANT_WORDS) > 0:
        questions.append(
            "Der Prompt fordert gleichzeitig Reibung/Dissonanz und Ruhe/Konsonanz — "
            "das ist ein Zielkonflikt auf der harmonischen Achse. Bitte eine Richtung "
            "bevorzugen oder festlegen, wie sich beides im Bogen abwechseln soll."
        )
    if _score(text, _INNOVATIVE_WORDS) > 0 and _score(text, _CONVENTIONAL_WORDS) > 0:
        questions.append(
            "Der Prompt fordert gleichzeitig Experimentelles und Vertrautes — "
            "das ist ein Zielkonflikt auf der Innovationsachse. Bitte praezisieren, "
            "welche Dimension (Klang, Form, Harmonik) experimentell sein soll."
        )

    return DnaDraft(dna=dna, open_questions=questions)


def derive_seed_root(prompt: str, salt: int = 0) -> int:
    """Deterministischer Seed aus dem Prompt, falls keiner vorgegeben ist."""
    return SeedPath.root(salt).child("dna", prompt).value
