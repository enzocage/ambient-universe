"""Der Editor-Agent: natuerliche Sprache -> Mutations-Operationen (plan.md Phase 6).

**Vorbehalt wie beim DNA-Agenten:** plan.md sieht ein LLM vor, das die
kleinste Menge sicherer Aenderungen waehlt und automatische Folgeanpassungen
vornimmt. Diese Umgebung hat keinen LLM-Zugriff zur Laufzeit. Implementiert
ist eine **Stichwort-zu-Mutation-Uebersetzung** mit demselben Sicherheits-
prinzip wie im Original vorgesehen: jede Aenderung ist ein deklarierter,
begrenzter Schritt, nie eine freie Parameteraenderung, und wird mit Begruendung
zurueckgemeldet.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from au.dsl.element import ElementRecipe

#: (Stichwoerter, Makro, Delta). Erkennt der Text eines der Stichwoerter,
#: wird das Makro um Delta verschoben (geklemmt auf [0, 1]).
_MACRO_RULES: tuple[tuple[tuple[str, ...], str, float], ...] = (
    (("wärmer", "waermer", "warm"), "brightness", -0.15),
    (("heller", "brillanter", "glänzender", "glaenzender"), "brightness", 0.15),
    (("dunkler", "kälter", "kaelter"), "brightness", -0.2),
    (("kräftiger", "kraeftiger", "voller", "körperhafter", "koerperhafter"), "body", 0.15),
    (("dünner", "duenner", "zarter", "leiser vom körper", "schlanker"), "body", -0.15),
    (("rauschiger", "mehr rauschen", "texturierter"), "noise_ratio", 0.15),
    (("klarer", "weniger rauschen", "sauberer"), "noise_ratio", -0.15),
    (("bewegter", "lebendiger", "unruhiger"), "motion", 0.15),
    (("ruhiger", "stiller", "weniger bewegung", "statischer"), "motion", -0.15),
)

#: (Stichwoerter, Rezeptfeld, Faktor oder additiver Betrag, Modus).
_STRUCTURAL_RULES: tuple[tuple[tuple[str, ...], str, float, str], ...] = (
    (
        (
            "länger nachklingend",
            "laenger nachklingend",
            "mehr nachhall",
            "längerer ausklang",
            "laengerer ausklang",
        ),
        "release_s",
        2.0,
        "mul",
    ),
    (("kürzerer ausklang", "kuerzerer ausklang", "trockener"), "release_s", 0.5, "mul"),
    (("dichter", "mehr ereignisse", "häufiger", "haeufiger"), "lambda_per_min", 1.6, "mul"),
    (("sparsamer", "weniger ereignisse", "seltener"), "lambda_per_min", 0.6, "mul"),
    (("länger", "laenger", "ausgedehnter"), "duration_s", 1.4, "mul"),
    (("kürzer", "kuerzer", "kompakter"), "duration_s", 0.7, "mul"),
)


@dataclass(slots=True)
class MutationResult:
    recipe: ElementRecipe
    applied: list[str] = field(default_factory=list)
    unrecognized: bool = False


def apply_instruction(recipe: ElementRecipe, instruction: str) -> MutationResult:
    """Wendet eine natuerlichsprachliche Anweisung auf ein Rezept an.

    Mehrere Regeln koennen gleichzeitig greifen (etwa "waermer und dichter").
    Jede angewendete Aenderung wird als Klartextzeile zurueckgemeldet — das
    Transparenzversprechen aus plan.md Etappe 4.
    """
    text = instruction.lower()
    applied: list[str] = []

    macros = dict(recipe.voice_macros)
    for keywords, macro, delta in _MACRO_RULES:
        if any(k in text for k in keywords):
            current = macros.get(macro, 0.5)
            new_value = max(0.0, min(1.0, current + delta))
            if abs(new_value - current) > 1e-9:
                macros[macro] = new_value
                applied.append(f"macro.{macro}  {current:.2f} -> {new_value:.2f}")

    updates: dict[str, float] = {}
    for keywords, field_name, factor, mode in _STRUCTURAL_RULES:
        if any(k in text for k in keywords):
            current = float(getattr(recipe, field_name))
            new_value = current * factor if mode == "mul" else current + factor
            updates[field_name] = new_value
            applied.append(f"{field_name}  {current:.2f} -> {new_value:.2f}")

    new_recipe = recipe.model_copy(update={**updates, "voice_macros": macros})
    return MutationResult(recipe=new_recipe, applied=applied, unrecognized=not applied)
