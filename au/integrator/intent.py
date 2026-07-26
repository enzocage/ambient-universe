"""Prompt-zu-Intention Uebersetzer (plan2.md Stufe 4).

Uebersetzt Prompt-Schluesselwoerter in konkrete musikalische Zielgroessen
auf allen Ebenen (Identity, Form, Harmonie, Orchestrierung).
"""

from __future__ import annotations

from au.dsl.intent import ComplexityProfile, MusicalIntent, SonicIdentity

_WARM_TERMS = ("warm", "weich", "sanft", "golden", "sonnig", "gebettet", "samten")
_COLD_TERMS = ("kalt", "kuehl", "eisig", "eisige", "hohl", "metallisch", "frost", "gläsern", "glaesern")
_BRIGHT_TERMS = ("hell", "gleissend", "glitzernd", "glas", "gläsern", "glaesern", "leuchtend", "schimmer", "licht", "eisig", "eisige")
_DARK_TERMS = ("dunkel", "finster", "tief", "schwarz", "schatten", "unterwasser", "abgrund")
_DENSE_TERMS = ("dicht", "voll", "ueberladen", "textur", "wolke", "komplex")
_SPARSE_TERMS = ("karg", "sparsam", "leer", "reduziert", "vereinzelt", "minimal", "still")
_RHYTHMIC_TERMS = ("rhythmisch", "sequenziert", "pulse", "pulsierend", "beat", "takt")


def derive_musical_intent(prompt: str, *, duration_s: float = 60.0) -> MusicalIntent:
    """Extrahiert ein volles Intentionsmodell aus dem Prompttext."""
    text = prompt.lower()

    warmth = 0.5
    if any(t in text for t in _WARM_TERMS):
        warmth += 0.35
    if any(t in text for t in _COLD_TERMS):
        warmth -= 0.35
    warmth = max(0.0, min(1.0, warmth))

    brightness = 0.5
    if any(t in text for t in _BRIGHT_TERMS):
        brightness += 0.35
    if any(t in text for t in _DARK_TERMS):
        brightness -= 0.35
    brightness = max(0.0, min(1.0, brightness))

    density = 0.5
    if any(t in text for t in _DENSE_TERMS):
        density += 0.3
    if any(t in text for t in _SPARSE_TERMS):
        density -= 0.3
    density = max(0.0, min(1.0, density))

    is_rhythmic = any(t in text for t in _RHYTHMIC_TERMS)
    rhythmic_comp = 0.7 if is_rhythmic else 0.2

    identity = SonicIdentity(
        warmth=warmth,
        brightness=brightness,
        hardness=0.7 if warmth < 0.3 else 0.2,
        density=density,
        spatial_depth=0.8 if "weit" in text or "halldistanz" in text else 0.5,
    )

    complexity = ComplexityProfile(
        harmonic_complexity=0.7 if "komplex" in text or "reich" in text else 0.4,
        rhythmic_complexity=rhythmic_comp,
        timbral_complexity=0.6,
    )

    return MusicalIntent(
        prompt=prompt,
        identity=identity,
        complexity=complexity,
        target_lufs=-16.0,
        target_duration_s=duration_s,
    )
