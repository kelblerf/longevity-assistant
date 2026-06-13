from __future__ import annotations

from app.models import MealEntry
from app.services.text_normalization_service import normalize_text

FOOD_MESSAGE_KEYWORDS = [
    "jidlo",
    "snidl",
    "jogurt",
    "kefir",
    "mlec",
    "strava",
    "hovezi",
    "kure",
    "kurci",
    "losos",
    "vejce",
    "ryze",
    "brambor",
    "spenat",
    "avokad",
    "oves",
    "banan",
    "ovoce",
    "zelen",
    "maso",
    "protein",
]


def _normalize(text: str) -> str:
    return normalize_text(text)


def _contains_any(text: str, keywords: list[str]) -> bool:
    normalized = _normalize(text)
    return any(keyword in normalized for keyword in keywords)


def _display_meal_title(title: str) -> str:
    cleaned = title.strip().strip(".!?")
    normalized = _normalize(cleaned)
    prefixes = [
        "dal jsem si ",
        "dala jsem si ",
        "snedl jsem ",
        "snezdl jsem ",
        "jedl jsem ",
        "jedla jsem ",
    ]
    for prefix in prefixes:
        if normalized.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip().strip(".!?")
            break
    return cleaned or title.strip()


def build_food_biomarker_context(meal: MealEntry | None, message: str) -> dict[str, object]:
    if meal is None:
        return {
            "isRelevant": False,
            "lipidSignals": [],
            "glucoseSignals": [],
            "content": "Zatim neni zapsane posledni jidlo, takze food-to-biomarker vazba nema z ceho vychazet.",
        }

    tags = [tag.lower() for tag in meal.tags]
    display_title = _display_meal_title(meal.title)
    title = _normalize(display_title)
    notes = _normalize(meal.notes or "")
    combined = " ".join([title, notes, *tags])

    lipid_signals: list[str] = []
    glucose_signals: list[str] = []
    b12_homocysteine_signals: list[str] = []
    ferritin_signals: list[str] = []

    if _contains_any(combined, ["uzen", "slanina", "klobas", "salam", "mast", "saturated", "syr", "smetan"]):
        lipid_signals.append("jidlo muze tlacit hlavne na lipidovou oblast")
    if _contains_any(combined, ["slad", "cukr", "ovoc", "peciv", "mouka", "susenk", "med", "dzem", "juice"]):
        glucose_signals.append("jidlo muze zvedat glukozovou zatez")
    if _contains_any(combined, ["protein", "jogurt", "kefir", "vejce", "tvaroh"]):
        glucose_signals.append("v jidle je i sycici nebo proteinova slozka, takze reakce nemusi byt jen glukozova")
    if _contains_any(combined, ["lactose", "jogurt", "kefir", "mlec", "syr"]):
        glucose_signals.append("u mlecne formy ma smysl sledovat traveni i energii, ne jen cukr")
    if _contains_any(combined, ["maso", "vejce", "ryba", "jatra", "tvaroh", "kefir", "jogurt"]):
        b12_homocysteine_signals.append("jidlo muze byt relevantni pro B12 nebo methylacni vrstvu")
    if _contains_any(combined, ["listov", "spenat", "brokol", "fazole", "lusten", "zelen"]):
        b12_homocysteine_signals.append("jidlo muze souviset i s folatovou a methylacni vrstvou")
    if _contains_any(combined, ["hov", "cervene maso", "jatra", "lusten", "spenat", "zelezo", "iron"]):
        ferritin_signals.append("jidlo muze byt relevantni pro zelezitou a ferritinovou oblast")

    is_lipid_query = _contains_any(message, ["cholesterol", "lipid", "ldl", "hdl", "trigly"])
    is_glucose_query = _contains_any(message, ["gluko", "hba1c", "cukr", "glykem"])
    is_b12_query = _contains_any(message, ["b12", "homocyst", "methyl", "folat"])
    is_ferritin_query = _contains_any(message, ["ferritin", "zelezo", "iron"])
    is_food_query = _contains_any(message, FOOD_MESSAGE_KEYWORDS)

    content_parts: list[str] = [
        f"Posledni zapsane jidlo je {display_title}."
    ]
    if lipid_signals and (is_lipid_query or is_food_query):
        content_parts.append(f"Pro lipidovou oblast je relevantni to, ze {', '.join(lipid_signals)}.")
    if glucose_signals and (is_glucose_query or is_food_query):
        content_parts.append(f"Pro glukozovou oblast je relevantni to, ze {', '.join(glucose_signals)}.")
    if b12_homocysteine_signals and (is_b12_query or is_food_query):
        content_parts.append(
            f"Pro B12 a homocystein je relevantni to, ze {', '.join(b12_homocysteine_signals)}."
        )
    if ferritin_signals and (is_ferritin_query or is_food_query):
        content_parts.append(
            f"Pro ferritin a zelezitou vrstvu je relevantni to, ze {', '.join(ferritin_signals)}."
        )

    if not lipid_signals and not glucose_signals and not b12_homocysteine_signals and not ferritin_signals:
        content_parts.append(
            "Z tohohle zapisu zatim neni silny signal pro lipidy ani glukozu, takze je vhodne hlavne sledovat odezvu tela."
        )

    return {
        "isRelevant": bool(lipid_signals or glucose_signals or b12_homocysteine_signals or ferritin_signals),
        "lipidSignals": lipid_signals,
        "glucoseSignals": glucose_signals,
        "b12HomocysteineSignals": b12_homocysteine_signals,
        "ferritinSignals": ferritin_signals,
        "content": " ".join(content_parts),
    }
