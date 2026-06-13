from __future__ import annotations

from app.models import CareRecommendation, GeneticMarker, GeneticProfile, MealEntry
from app.services.text_normalization_service import normalize_text


_DNA_BIOMARKER_MAP: dict[str, dict[str, object]] = {
    "b12_absorption": {
        "biomarkers": ["vitamin_b12", "homocysteine"],
        "label": "B12 absorpce",
        "message": (
            "DNA signal kolem B12 dava smysl cist spolu s vitaminem B12 a homocysteinem, "
            "ne izolovane jen jako genetickou predispozici."
        ),
    },
    "methylation_folate": {
        "biomarkers": ["homocysteine", "vitamin_b12", "folate"],
        "label": "methylace a folat",
        "message": (
            "DNA signal kolem methylace ma smysl cist hlavne s homocysteinem, B12 a folatovou vrstvou."
        ),
    },
    "lipid_regulation": {
        "biomarkers": ["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"],
        "label": "lipidova regulace",
        "message": (
            "DNA signal kolem lipidove regulace ma smysl cist spolu s LDL, celkovym cholesterolem, "
            "HDL a triglyceridy."
        ),
    },
    "insulin_sensitivity": {
        "biomarkers": ["glucose_fasting", "hba1c", "triglycerides"],
        "label": "inzulinova citlivost",
        "message": (
            "DNA signal kolem inzulinove citlivosti ma smysl cist spolu s glukozou nalacno, HbA1c "
            "a casto i s triglyceridy."
        ),
    },
    "inflammation_regulation": {
        "biomarkers": ["crp"],
        "label": "zanetliva regulace",
        "message": (
            "DNA signal kolem zanetu ma smysl cist spolu s CRP a se symptomovou i regeneracni vrstvou."
        ),
    },
    "oxidative_stress_response": {
        "biomarkers": ["crp", "ferritin"],
        "label": "oxidacni stres",
        "message": (
            "DNA signal kolem oxidacniho stresu ma smysl cist s regeneraci, zanetlivou vrstvou a "
            "vybranymi biomarkery, ne jako samostatny verdikt."
        ),
    },
    "vitamin_a_conversion": {
        "biomarkers": [],
        "label": "vitamin A",
        "message": (
            "DNA signal kolem vitaminu A je zatim hlavne interpretacni vrstva a zatim nema v systemu "
            "silny pravy biomarkerovy protejsek."
        ),
    },
    "salt_pressure_response": {
        "biomarkers": [],
        "label": "sul a tlak",
        "message": (
            "DNA signal kolem soli a tlaku je zatim hlavne behavioralni a care vrstva, ne primarne "
            "biomarkerovy fokus v soucasnem modelu."
        ),
    },
}


def _normalize(text: str) -> str:
    return normalize_text(text)


def _message_focus_keys(message: str) -> list[str]:
    normalized = _normalize(message)
    focus: list[str] = []
    if any(keyword in normalized for keyword in ["cholesterol", "lipid", "ldl", "hdl", "trigly"]):
        focus.extend(["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"])
    if any(keyword in normalized for keyword in ["gluko", "glykem", "hba1c", "cukr"]):
        focus.extend(["glucose_fasting", "hba1c"])
    if any(keyword in normalized for keyword in ["b12", "homocyst", "folat", "methyl"]):
        focus.extend(["vitamin_b12", "homocysteine", "folate"])
    if any(keyword in normalized for keyword in ["ferritin", "zelezo", "iron"]):
        focus.extend(["ferritin", "iron_serum", "transferrin"])
    if any(keyword in normalized for keyword in ["crp", "zanet", "inflam"]):
        focus.extend(["crp"])
    return list(dict.fromkeys(focus))


def _matched_markers(profile: GeneticProfile | None, focus_keys: list[str]) -> list[GeneticMarker]:
    if profile is None:
        return []

    matched: list[GeneticMarker] = []
    focus_key_set = set(focus_keys)
    for marker in profile.markers:
        mapping = _DNA_BIOMARKER_MAP.get(marker.key)
        if mapping is None:
            continue
        biomarker_keys = set(mapping["biomarkers"])
        if biomarker_keys.intersection(focus_key_set):
            matched.append(marker)
    return matched


def _care_recency_score(item: CareRecommendation) -> int:
    if item.id.startswith("care-"):
        suffix = item.id.removeprefix("care-")
        if suffix.isdigit():
            return int(suffix)
    return 0


def _care_relevance_score(
    item: CareRecommendation,
    focus_keys: list[str],
    matched_keys: set[str],
) -> tuple[int, int]:
    overlap = len(set(item.related_markers).intersection(focus_keys))
    text = " ".join(
        [
            item.title,
            item.recommendation,
            " ".join(item.related_markers),
            item.notes or "",
        ]
    ).lower()
    domain_score = 0
    if "lipid_regulation" in matched_keys and any(
        key in text for key in ["cholesterol", "lipid", "triglycer", "ldl", "hdl", "uzen"]
    ):
        domain_score += 3
    if "insulin_sensitivity" in matched_keys and any(
        key in text for key in ["gluk", "metabol", "cukr", "glykem"]
    ):
        domain_score += 3
    if any(key in matched_keys for key in {"b12_absorption", "methylation_folate"}) and any(
        key in text for key in ["b12", "homocyst", "folat", "methyl"]
    ):
        domain_score += 3
    return overlap, domain_score


def build_dna_biomarker_context(
    message: str,
    profile: GeneticProfile | None,
    biomarker_focus_keys: list[str],
    care_recommendations: list[CareRecommendation] | None = None,
    meal: MealEntry | None = None,
) -> dict[str, object]:
    focus_keys = list(dict.fromkeys([*biomarker_focus_keys, *_message_focus_keys(message)]))
    if not focus_keys or profile is None or not profile.markers:
        return {
            "isRelevant": False,
            "matchedMarkerKeys": [],
            "content": "",
            "watchLinks": [],
        }

    matched_markers = _matched_markers(profile, focus_keys)
    if not matched_markers:
        return {
            "isRelevant": False,
            "matchedMarkerKeys": [],
            "content": "",
            "watchLinks": [],
        }

    watch_links: list[str] = []
    parts: list[str] = []
    for marker in matched_markers:
        mapping = _DNA_BIOMARKER_MAP.get(marker.key)
        if mapping is None:
            continue
        label = str(mapping["label"])
        message_text = str(mapping["message"])
        parts.append(
            f"DNA marker '{marker.label}' se tu potkava s biomarkerovou oblasti pro {label}. {message_text}"
        )
        watch_links.extend(mapping["biomarkers"])

    watch_links = list(dict.fromkeys(watch_links))
    related_care_titles: list[str] = []
    matched_keys = {marker.key for marker in matched_markers}
    related_care_items: list[CareRecommendation] = []
    if care_recommendations:
        for item in care_recommendations:
            haystack = " ".join(
                [
                    item.title,
                    item.recommendation,
                    " ".join(item.related_markers),
                    item.notes or "",
                ]
            ).lower()
            if any(key in haystack for key in ["cholesterol", "lipid", "triglycer", "ldl", "hdl"]):
                if "lipid_regulation" in matched_keys:
                    related_care_items.append(item)
            if any(key in haystack for key in ["b12", "homocyst", "folat"]):
                if any(
                    marker.key in {"b12_absorption", "methylation_folate"}
                    for marker in matched_markers
                ):
                    related_care_items.append(item)
            if any(key in haystack for key in ["gluk", "metabol", "cukr"]):
                if "insulin_sensitivity" in matched_keys:
                    related_care_items.append(item)

    deduped_care_items = {item.id: item for item in related_care_items}
    sorted_care_items = sorted(
        deduped_care_items.values(),
        key=lambda item: (
            _care_relevance_score(item, focus_keys, matched_keys)[0],
            _care_relevance_score(item, focus_keys, matched_keys)[1],
            _care_recency_score(item),
        ),
        reverse=True,
    )
    related_care_titles = [item.title for item in sorted_care_items]

    if not related_care_titles and care_recommendations:
        if "lipid_regulation" in matched_keys:
            related_care_titles = [item.title for item in care_recommendations[:1]]
        elif "insulin_sensitivity" in matched_keys:
            related_care_titles = [item.title for item in care_recommendations[:1]]

    if related_care_titles:
        parts.append(
            f"Z care vrstvy se sem primo propisuje: {', '.join(related_care_titles[:2])}."
        )

    meal_context = ""
    if meal is not None:
        meal_context = f" Posledni zapsane jidlo je {meal.title}."
        if "lipid_regulation" in matched_keys:
            meal_context += " U lipidove vrstvy ma smysl cist ho hlavne pres kvalitu tuku a uzeniny."
        elif "insulin_sensitivity" in matched_keys:
            meal_context += " U glukozove vrstvy ma smysl cist ho pres glykemickou odezvu a energii po jidle."
        elif {"methylation_folate", "b12_absorption"} & matched_keys:
            meal_context += " U B12 a methylace ma smysl cist ho i pres kvalitu vyzivy, ne jen pres kalorie."
        parts.append(meal_context.strip())

    parts.append(
        "DNA se tu ma cist jen jako doporucujici vrstva a biomarkery maji vyssi vahu jako merena realita."
    )

    return {
        "isRelevant": True,
        "matchedMarkerKeys": [marker.key for marker in matched_markers],
        "content": " ".join(parts),
        "watchLinks": watch_links,
        "relatedCareTitles": related_care_titles,
        "mealContext": meal_context.strip(),
    }
