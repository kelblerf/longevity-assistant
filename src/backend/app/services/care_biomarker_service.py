from __future__ import annotations

from app.models import CareRecommendation
from app.services.text_normalization_service import normalize_text


def _normalize(text: str) -> str:
    return normalize_text(text)


def _contains_any(text: str, keywords: list[str]) -> bool:
    normalized = _normalize(text)
    return any(keyword in normalized for keyword in keywords)


def _focus_keys_from_message(message: str) -> list[str]:
    focus: list[str] = []
    if _contains_any(message, ["cholesterol", "lipid", "ldl", "hdl", "trigly"]):
        focus.extend(["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"])
    if _contains_any(message, ["gluko", "glykem", "hba1c", "cukr"]):
        focus.extend(["glucose_fasting", "hba1c"])
    if _contains_any(message, ["b12", "homocyst", "folat", "methyl"]):
        focus.extend(["vitamin_b12", "homocysteine", "folate"])
    if _contains_any(message, ["ferritin", "zelezo", "iron"]):
        focus.extend(["ferritin", "iron_serum", "transferrin"])
    if _contains_any(message, ["crp", "zanet", "inflam"]):
        focus.extend(["crp"])
    if _contains_any(message, ["tsh", "ft3", "ft4", "stit", "thyroid"]):
        focus.extend(["tsh", "ft4", "ft3"])
    return list(dict.fromkeys(focus))


def _care_recency_score(item: CareRecommendation) -> int:
    if item.id.startswith("care-"):
        suffix = item.id.removeprefix("care-")
        if suffix.isdigit():
            return int(suffix)
    return 0


def _care_relevance_score(item: CareRecommendation, focus_keys: list[str]) -> tuple[int, int]:
    overlap = len(set(item.related_markers).intersection(focus_keys))
    text = " ".join(
        [item.title, item.recommendation, " ".join(item.related_markers), item.notes or ""]
    ).lower()
    domain_score = 0
    if {"ldl_c", "total_cholesterol", "hdl_c", "triglycerides"} & set(focus_keys):
        if any(key in text for key in ["cholesterol", "lipid", "triglycer", "ldl", "hdl"]):
            domain_score += 3
    if {"glucose_fasting", "hba1c"} & set(focus_keys):
        if any(key in text for key in ["gluk", "glykem", "cukr", "metabol"]):
            domain_score += 3
    if {"vitamin_b12", "homocysteine", "folate"} & set(focus_keys):
        if any(key in text for key in ["b12", "homocyst", "folat", "methyl"]):
            domain_score += 3
    return overlap, domain_score


def build_care_biomarker_context(
    message: str,
    care_recommendations: list[CareRecommendation],
    biomarker_focus_keys: list[str],
) -> dict[str, object]:
    if not care_recommendations:
        return {
            "isRelevant": False,
            "relatedCareTitles": [],
            "focusKeys": [],
            "content": "",
        }

    focus_keys = list(dict.fromkeys([*biomarker_focus_keys, *_focus_keys_from_message(message)]))
    if not focus_keys:
        return {
            "isRelevant": False,
            "relatedCareTitles": [],
            "focusKeys": [],
            "content": "",
        }

    related: list[CareRecommendation] = []
    for item in care_recommendations:
        overlap = set(item.related_markers).intersection(focus_keys)
        haystack = " ".join(
            [item.title, item.recommendation, " ".join(item.related_markers), item.notes or ""]
        ).lower()
        if overlap:
            related.append(item)
            continue
        if {"ldl_c", "total_cholesterol", "hdl_c", "triglycerides"} & set(focus_keys):
            if any(key in haystack for key in ["cholesterol", "lipid", "triglycer", "ldl", "hdl"]):
                related.append(item)
                continue
        if {"glucose_fasting", "hba1c"} & set(focus_keys):
            if any(key in haystack for key in ["gluk", "glykem", "cukr", "metabol"]):
                related.append(item)
                continue
        if {"vitamin_b12", "homocysteine", "folate"} & set(focus_keys):
            if any(key in haystack for key in ["b12", "homocyst", "folat", "methyl"]):
                related.append(item)
                continue

    deduped = list({item.id: item for item in related}.values())
    if not deduped:
        return {
            "isRelevant": False,
            "relatedCareTitles": [],
            "focusKeys": focus_keys,
            "content": "",
        }

    deduped.sort(
        key=lambda item: (
            _care_relevance_score(item, focus_keys)[0],
            _care_relevance_score(item, focus_keys)[1],
            _care_recency_score(item),
        ),
        reverse=True,
    )

    top = deduped[0]
    marker_text = ", ".join(top.related_markers[:4]) if top.related_markers else ", ".join(focus_keys[:4])
    content = (
        f"Care vrstva pro tenhle biomarker fokus drzi doporuceni '{top.title}' od zdroje {top.source}. "
        f"Prakticky se ma cist hlavne spolu s markery: {marker_text}. "
        f"Doporuceni zni: {top.recommendation}"
    )
    if top.next_due:
        content += f" Dalsi navazana kontrola je vedena k datu {top.next_due}."

    return {
        "isRelevant": True,
        "relatedCareTitles": [item.title for item in deduped[:3]],
        "focusKeys": focus_keys,
        "content": content,
    }
