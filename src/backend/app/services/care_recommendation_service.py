from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from app.models import CareRecommendation, CreateCareRecommendationInput
from app.services.storage_service import read_json, write_json


STORAGE_FILE = "care-recommendations.json"


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_text(value: str | None) -> str:
    return " ".join((value or "").strip().lower().split())


def _normalize_markers(markers: Iterable[str]) -> tuple[str, ...]:
    return tuple(sorted(_normalize_text(marker) for marker in markers if _normalize_text(marker)))


def _care_signature(
    title: str,
    recommendation: str,
    priority: str,
    related_markers: Iterable[str],
) -> tuple[str, str, str]:
    return (
        _normalize_text(title),
        _normalize_text(recommendation),
        _normalize_text(priority),
    )


def _recommendation_score(item: CareRecommendation) -> tuple[int, int, int, int, int, str]:
    filled_fields = sum(
        1
        for value in [item.next_due, item.review_frequency, item.notes, item.active_from, item.source]
        if value
    )
    return (
        filled_fields,
        len(item.related_markers),
        1 if item.notes else 0,
        1 if item.next_due else 0,
        len(item.source or ""),
        item.id,
    )


def _merge_recommendations(items: list[CareRecommendation]) -> CareRecommendation:
    ranked = sorted(items, key=_recommendation_score, reverse=True)
    base = ranked[0].model_copy(deep=True)
    merged_markers = list(dict.fromkeys(base.related_markers))

    for item in ranked[1:]:
        for marker in item.related_markers:
            if marker not in merged_markers:
                merged_markers.append(marker)
        if not base.source and item.source:
            base.source = item.source
        if not base.category and item.category:
            base.category = item.category
        if not base.notes and item.notes:
            base.notes = item.notes
        if not base.active_from and item.active_from:
            base.active_from = item.active_from
        if not base.review_frequency and item.review_frequency:
            base.review_frequency = item.review_frequency
        if not base.next_due and item.next_due:
            base.next_due = item.next_due
        if not base.recommendation and item.recommendation:
            base.recommendation = item.recommendation
        if not base.title and item.title:
            base.title = item.title
        if not base.priority and item.priority:
            base.priority = item.priority
        if base.status != "active" and item.status == "active":
            base.status = "active"

    base.related_markers = merged_markers
    return base


def _contains_any(text: str | None, keywords: Iterable[str]) -> bool:
    normalized = _normalize_text(text)
    return any(keyword in normalized for keyword in keywords)


def _is_lipid_prevention(item: CareRecommendation) -> bool:
    marker_set = set(item.related_markers)
    return bool({"ldl_c", "total_cholesterol", "hdl_c", "triglycerides"} & marker_set) and (
        "prevention" in _normalize_text(item.category)
        or _contains_any(item.title, ["lipid", "cholesterol", "preventiv"])
    )


def _canonical_lipid_bucket(item: CareRecommendation) -> str:
    text = " ".join(
        [
            item.title,
            item.source,
            item.recommendation,
            item.notes or "",
        ]
    )
    if _contains_any(text, ["leky byly", "nebezpecny", "preventivni prohlidka", "rezimova zmena"]):
        return "authority"
    if _contains_any(text, ["reminder", "navazat dalsi kontrolou", "blizici se kontrola"]):
        return "reminder"
    if _contains_any(text, ["opakovat preventivni odbery", "panel pod kontrolou", "mudr.", "novakova"]):
        return "monitoring"
    return "lifestyle"


def _canonical_lipid_shape(bucket: str) -> dict[str, object]:
    if bucket == "authority":
        return {
            "title": "Preventivni lipidova kontrola a rezimova zmena",
            "source": "Prakticka doktorka - preventivni prohlidka",
            "category": "prevention_lipids",
            "priority": "high",
        }
    if bucket == "monitoring":
        return {
            "title": "Preventivni lipidova kontrola",
            "source": "MUDr. Novakova",
            "category": "prevention",
            "priority": "high",
        }
    if bucket == "reminder":
        return {
            "title": "Preventivni cholesterol reminder",
            "source": "Prakticka doktorka",
            "category": "prevention",
            "priority": "high",
        }
    return {
        "title": "Lipidova prevence a rezim",
        "source": "Prakticka doktorka",
        "category": "prevention",
        "priority": "high",
    }


def compact_care_recommendations() -> int:
    items = _load()
    lipid_items = [item for item in items if _is_lipid_prevention(item) and item.status == "active"]
    other_items = [item for item in items if item not in lipid_items]
    if len(lipid_items) <= 4:
        return 0

    buckets: dict[str, list[CareRecommendation]] = {
        "authority": [],
        "lifestyle": [],
        "monitoring": [],
        "reminder": [],
    }
    for item in lipid_items:
        buckets[_canonical_lipid_bucket(item)].append(item)

    compacted: list[CareRecommendation] = []
    for bucket_name, bucket_items in buckets.items():
        if not bucket_items:
            continue
        merged = _merge_recommendations(bucket_items)
        shape = _canonical_lipid_shape(bucket_name)
        merged.title = str(shape["title"])
        merged.source = str(shape["source"])
        merged.category = str(shape["category"])
        merged.priority = str(shape["priority"])
        compacted.append(merged)

    compacted.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item.priority, 9),
            item.next_due or "9999-12-31",
            item.title.lower(),
        ),
    )
    _save([*other_items, *compacted])
    return len(lipid_items) - len(compacted)


def dedupe_care_recommendations() -> dict[str, str]:
    payload = read_json(STORAGE_FILE, [])
    items = [CareRecommendation.model_validate(item) for item in payload]
    grouped: dict[tuple[str, str, str], list[CareRecommendation]] = {}
    for item in items:
        signature = _care_signature(
            item.title,
            item.recommendation,
            item.priority,
            item.related_markers,
        )
        grouped.setdefault(signature, []).append(item)

    deduped: list[CareRecommendation] = []
    alias_map: dict[str, str] = {}
    changed = False

    for group in grouped.values():
        merged = _merge_recommendations(group)
        deduped.append(merged)
        for item in group:
            alias_map[item.id] = merged.id
        if len(group) > 1:
            changed = True

    deduped.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item.priority, 9),
            item.next_due or "9999-12-31",
            item.title.lower(),
        ),
    )
    if changed or len(deduped) != len(items):
        _save(deduped)
    return alias_map


def _load() -> list[CareRecommendation]:
    dedupe_care_recommendations()
    payload = read_json(STORAGE_FILE, [])
    return [CareRecommendation.model_validate(item) for item in payload]


def _save(items: list[CareRecommendation]) -> None:
    write_json(STORAGE_FILE, [item.model_dump(mode="json", by_alias=True) for item in items])


def list_care_recommendations() -> list[CareRecommendation]:
    items = _load()
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        items,
        key=lambda item: (
            priority_rank.get(item.priority, 9),
            item.next_due or "9999-12-31",
            item.title.lower(),
        ),
    )


def create_care_recommendation(payload: CreateCareRecommendationInput) -> CareRecommendation:
    items = _load()
    signature = _care_signature(
        payload.title,
        payload.recommendation,
        payload.priority,
        payload.related_markers,
    )
    for item in items:
        if _care_signature(item.title, item.recommendation, item.priority, item.related_markers) == signature:
            return item
    recommendation = CareRecommendation(
        id=f"care-{int(datetime.now(UTC).timestamp() * 1000)}",
        title=payload.title,
        source=payload.source,
        category=payload.category,
        priority=payload.priority,
        recommendation=payload.recommendation,
        activeFrom=payload.active_from,
        reviewFrequency=payload.review_frequency,
        nextDue=payload.next_due,
        relatedMarkers=payload.related_markers,
        notes=payload.notes,
        status="active",
    )
    items.append(recommendation)
    _save(items)
    return recommendation


def list_active_care_recommendations() -> list[CareRecommendation]:
    return [item for item in list_care_recommendations() if item.status == "active"]


def care_recommendation_highlights(limit: int = 3) -> list[str]:
    items = list_active_care_recommendations()
    highlights: list[str] = []
    for item in items[:limit]:
        due = f", dalsi kontrola {item.next_due}" if item.next_due else ""
        highlights.append(f"{item.title} [{item.priority}] - {item.source}{due}")
    return highlights
