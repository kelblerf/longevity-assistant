from __future__ import annotations

from app.models import (
    BiomarkerObservation,
    BiomarkerPriorityMarker,
    BiomarkerTrendSnapshot,
    CareRecommendation,
)
from app.services.biomarker_priority_service import list_priority_biomarkers, priority_marker_keys
from app.services.text_normalization_service import normalize_text


_FAMILY_KEYWORDS: list[tuple[list[str], list[str]]] = [
    (["cholesterol", "lipid", "ldl", "hdl", "trigly"], ["ldl_c", "total_cholesterol", "hdl_c", "triglycerides"]),
    (["gluko", "glykem", "hba1c", "cukr"], ["glucose_fasting", "hba1c"]),
    (["vitamin d", "vit d", "dcko"], ["vitamin_d_25oh"]),
    (["b12", "kobal", "homocyst", "folat"], ["vitamin_b12", "folate", "homocysteine"]),
    (["ferritin", "zelezo", "iron"], ["ferritin", "iron_serum", "transferrin"]),
    (["zanet", "crp", "inflam"], ["crp"]),
    (["stit", "thyroid", "tsh", "ft3", "ft4"], ["tsh", "ft4", "ft3"]),
]


def _normalize(text: str) -> str:
    return normalize_text(text)


def _latest_by_marker(observations: list[BiomarkerObservation]) -> dict[str, BiomarkerObservation]:
    latest: dict[str, BiomarkerObservation] = {}
    for observation in observations:
        current = latest.get(observation.marker_key)
        if current is None or observation.observed_at >= current.observed_at:
            latest[observation.marker_key] = observation
    return latest


def _trends_by_marker(trends: list[BiomarkerTrendSnapshot]) -> dict[str, BiomarkerTrendSnapshot]:
    return {trend.marker_key: trend for trend in trends}


def _matches_biomarker_query(message: str) -> bool:
    normalized = _normalize(message)
    keywords = [
        "biomarker",
        "krev",
        "labor",
        "cholesterol",
        "gluko",
        "vitamin",
        "ferritin",
        "homocyst",
        "crp",
        "tsh",
        "lipid",
    ]
    return any(keyword in normalized for keyword in keywords)


def _focus_keys_from_message(message: str) -> list[str]:
    normalized = _normalize(message)
    for keywords, marker_keys in _FAMILY_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return marker_keys
    return []


def _marker_text(observation: BiomarkerObservation, trend: BiomarkerTrendSnapshot | None) -> str:
    value_text = "bez hodnoty"
    if observation.value is not None:
        value_text = f"{observation.value} {observation.unit or ''}".strip()

    parts = [
        f"{observation.marker_label} je naposledy {value_text}",
        f"se statusem {observation.status}",
    ]

    if trend and trend.sample_count > 1:
        if trend.trend_direction == "stable" or trend.delta_absolute is None:
            parts.append(f"v trendu je zatim spise stabilni z {trend.sample_count} mereni")
        elif trend.delta_percent is not None:
            parts.append(
                f"v trendu jde {trend.trend_direction} o {abs(trend.delta_percent):.1f} %"
            )
        else:
            parts.append(f"v trendu jde {trend.trend_direction}")
    elif trend and trend.sample_count == 1:
        parts.append("zatim je k dispozici jen jedno potvrzene mereni")

    return ", ".join(parts) + "."


def _family_guidance(marker_keys: list[str]) -> str:
    marker_key_set = set(marker_keys)
    if {"ldl_c", "total_cholesterol", "hdl_c", "triglycerides"} & marker_key_set:
        return (
            "U lipidove oblasti je rozumne cist panel pohromade, spojit ho s jidlem, pohybem, "
            "vahou autority doporuceni doktorky a nevyvozovat zaver jen z jedne izolovane hodnoty."
        )
    if {"glucose_fasting", "hba1c"} & marker_key_set:
        return (
            "U glukozove oblasti dava smysl porovnat kratkodobe a dlouhodobe mereni, sledovat "
            "rytmus jidla, energii a teprve potom delat silnejsi interpretaci."
        )
    if {"vitamin_d_25oh", "vitamin_b12", "folate", "homocysteine"} & marker_key_set:
        return (
            "U vitaminove a methylacni oblasti je vhodne cist markery ve vazbe na energii, DNA predispozice "
            "a dlouhodobe fungovani, ne jen mechanicky podle jedne hranice."
        )
    if {"ferritin", "iron_serum", "transferrin"} & marker_key_set:
        return (
            "U zeleza a ferritinu je dobre cist skladovou vrstvu spolu s dalisimi souvisejicimi markery "
            "a nebrat nizsi nebo vyssi cislo bez kontextu."
        )
    if {"crp"} & marker_key_set:
        return (
            "U CRP je vhodne odlisit akutni signal od dlouhodobeho trendu a spojit ho se symptomy, stresem a regeneraci."
        )
    if {"tsh", "ft3", "ft4"} & marker_key_set:
        return (
            "U stitne zlazy je dobre cist TSH, FT4 a FT3 spolecne a spojit je s energii, teplotou, vahou a dalsim fungovanim."
        )
    return (
        "Vybrany marker je vhodne cist v trendu, ve vazbe na symptomy a oddelit mereny stav od pracovni interpretace."
    )


def _related_care_text(marker_keys: list[str], care_recommendations: list[CareRecommendation]) -> str:
    marker_key_set = set(marker_keys)
    for recommendation in care_recommendations:
        if marker_key_set.intersection(recommendation.related_markers):
            return (
                f" Aktivni care vrstva k tomu navic drzi doporuceni '{recommendation.title}' "
                f"od zdroje {recommendation.source}."
            )
    return ""


def _priority_marker_map() -> dict[str, BiomarkerPriorityMarker]:
    return {item.marker_key: item for item in list_priority_biomarkers()}


def _action_block(focus_keys: list[str]) -> dict[str, list[str]]:
    priority_map = _priority_marker_map()
    watch_for: list[str] = []
    link_with: list[str] = []
    alert_when: list[str] = []

    for key in focus_keys:
        marker = priority_map.get(key)
        if marker is None:
            continue
        watch_for.extend(marker.watch_for)
        link_with.extend(marker.link_with)
        alert_when.extend(marker.alert_when)

    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))

    return {
        "watchFor": _dedupe(watch_for)[:4],
        "linkWith": _dedupe(link_with)[:5],
        "alertWhen": _dedupe(alert_when)[:4],
    }


def _default_focus_keys(
    message: str,
    latest_by_marker: dict[str, BiomarkerObservation],
    trends_by_marker: dict[str, BiomarkerTrendSnapshot],
) -> list[str]:
    focus_from_message = _focus_keys_from_message(message)
    if focus_from_message:
        return [key for key in focus_from_message if key in latest_by_marker or key in trends_by_marker]

    flagged = [
        item
        for item in latest_by_marker.values()
        if item.status in {"high", "low", "out_of_range"}
    ]
    if flagged:
        ordered = sorted(flagged, key=lambda item: (item.observed_at, item.marker_label), reverse=True)
        return [ordered[0].marker_key]

    priority_keys = [key for key in priority_marker_keys() if key in latest_by_marker or key in trends_by_marker]
    if priority_keys:
        return [priority_keys[0]]

    if trends_by_marker:
        return [sorted(trends_by_marker)[0]]

    return []


def build_biomarker_insight(
    message: str,
    observations: list[BiomarkerObservation],
    trends: list[BiomarkerTrendSnapshot],
    care_recommendations: list[CareRecommendation],
) -> dict[str, object]:
    latest = _latest_by_marker(observations)
    trend_map = _trends_by_marker(trends)
    is_biomarker_query = _matches_biomarker_query(message)
    focus_keys = _default_focus_keys(message, latest, trend_map)

    if not latest and not trend_map:
        return {
            "isBiomarkerQuery": is_biomarker_query,
            "focusKeys": [],
            "content": "Zatim neni potvrzena biomarker vrstva nebo z ni nejsou nactene zadne hodnoty.",
            "highlights": [],
            "watchFor": [],
            "linkWith": [],
            "alertWhen": [],
        }

    focus_observations = [latest[key] for key in focus_keys if key in latest][:3]
    insight_lines = [
        _marker_text(observation, trend_map.get(observation.marker_key))
        for observation in focus_observations
    ]

    if not insight_lines and focus_keys:
        insight_lines.append(
            "Vybrany marker ma zatim jen trendovy zaznam bez dostatecne citelne posledni observation vrstvy."
        )

    family_guidance = _family_guidance(focus_keys)
    care_text = _related_care_text(focus_keys, care_recommendations)
    actions = _action_block(focus_keys)
    content = " ".join(insight_lines) if insight_lines else (
        f"Potvrzena biomarker vrstva obsahuje {len(trend_map)} trendovych markeru, ale zatim bez jednoznacneho fokusniho markeru."
    )
    action_parts: list[str] = []
    if actions["watchFor"]:
        action_parts.append(f"Co sledovat: {', '.join(actions['watchFor'])}.")
    if actions["linkWith"]:
        action_parts.append(f"S cim spojovat: {', '.join(actions['linkWith'])}.")
    if actions["alertWhen"]:
        action_parts.append(f"Kdy zpozornet: {', '.join(actions['alertWhen'])}.")
    content = f"{content} {family_guidance}{care_text} {' '.join(action_parts)}".strip()

    highlights = [observation.marker_label for observation in focus_observations]

    return {
        "isBiomarkerQuery": is_biomarker_query,
        "focusKeys": focus_keys,
        "content": content,
        "highlights": highlights,
        "watchFor": actions["watchFor"],
        "linkWith": actions["linkWith"],
        "alertWhen": actions["alertWhen"],
    }
