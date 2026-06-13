from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

import httpx

from app.config import settings
from app.models import (
    DailyBriefing,
    NotionMappingPreview,
    NotionSyncHistoryEntry,
    NotionSyncResult,
    NotionSyncSourceState,
    NotionSyncStatus,
)
from app.services.biomarker_confirm_service import (
    list_biomarker_reports,
    list_biomarker_trends,
)
from app.services.care_recommendation_service import list_care_recommendations
from app.services.daily_check_in_service import list_daily_check_ins
from app.services.follow_up_service import list_follow_ups
from app.services.genetics_service import get_genetic_profile
from app.services.guidance_service import build_daily_briefing
from app.services.health_signal_service import list_health_signals
from app.services.storage_service import read_json, write_json

SyncSource = Literal[
    "daily_check_ins",
    "health_signals",
    "follow_ups",
    "daily_summary",
    "care_recommendations",
    "biomarker_reports",
    "biomarker_trends",
    "genetic_profile",
    "genetic_markers",
]

_DATABASE_LABELS: dict[SyncSource, str] = {
    "daily_check_ins": "Daily Check-ins",
    "health_signals": "Health Signals",
    "follow_ups": "Follow-ups",
    "daily_summary": "Daily Summaries",
    "care_recommendations": "Care Recommendations",
    "biomarker_reports": "Biomarker Reports",
    "biomarker_trends": "Biomarker Trends",
    "genetic_profile": "Genetic Profile",
    "genetic_markers": "Genetic Markers",
}

_UPDATE_EXISTING_SOURCES: set[SyncSource] = {
    "health_signals",
    "follow_ups",
    "daily_summary",
    "care_recommendations",
    "biomarker_reports",
    "biomarker_trends",
    "genetic_profile",
    "genetic_markers",
}

_SOURCE_ID_QUERY_BATCH_SIZE = 25


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_outbox_dir() -> Path:
    settings.notion_outbox_dir.mkdir(parents=True, exist_ok=True)
    return settings.notion_outbox_dir


def _default_source_state(source_type: SyncSource) -> dict:
    return {
        "sourceType": source_type,
        "mode": _mode_for_source(source_type),
        "deliveryState": "idle",
        "syncedCount": 0,
        "attemptCount": 0,
        "failureCount": 0,
        "consecutiveFailures": 0,
        "lastAttemptAt": None,
        "lastSuccessAt": None,
        "lastError": None,
    }


def _state() -> dict:
    payload = read_json(
        "notion-sync-state.json",
        default={
            "lastSyncAt": None,
            "syncCounts": {key: 0 for key in _DATABASE_LABELS},
            "syncedIds": {key: [] for key in _DATABASE_LABELS},
            "sourceStates": {
                key: _default_source_state(key) for key in _DATABASE_LABELS
            },
        },
    )
    changed = False

    if "syncCounts" not in payload:
        payload["syncCounts"] = {key: 0 for key in _DATABASE_LABELS}
        changed = True
    for key in _DATABASE_LABELS:
        if key not in payload["syncCounts"]:
            payload["syncCounts"][key] = 0
            changed = True

    if "syncedIds" not in payload:
        payload["syncedIds"] = {key: [] for key in _DATABASE_LABELS}
        changed = True
    for key in _DATABASE_LABELS:
        if key not in payload["syncedIds"]:
            payload["syncedIds"][key] = []
            changed = True

    source_states = payload.get("sourceStates")
    if not isinstance(source_states, dict):
        source_states = {}
        payload["sourceStates"] = source_states
        changed = True
    for key in _DATABASE_LABELS:
        default_state = _default_source_state(key)
        current_state = source_states.get(key)
        if not isinstance(current_state, dict):
            source_states[key] = default_state
            changed = True
            continue
        next_state = dict(default_state)
        next_state.update(current_state)
        next_state["sourceType"] = key
        next_state["mode"] = _mode_for_source(key)
        if next_state != current_state:
            source_states[key] = next_state
            changed = True

    if changed:
        _save_state(payload)
    return payload


def _save_state(payload: dict) -> None:
    write_json("notion-sync-state.json", payload)


def _history() -> list[dict]:
    payload = read_json("notion-sync-history.json", default=[])
    changed = False
    normalized: list[dict] = []
    for item in payload:
        next_item = dict(item)
        if "mode" not in next_item:
            next_item["mode"] = "outbox"
            changed = True
        if "deliveryState" not in next_item:
            next_item["deliveryState"] = (
                "queued" if next_item.get("mode") == "outbox" else "synced"
            )
            changed = True
        if "attemptedCount" not in next_item:
            next_item["attemptedCount"] = next_item.get("syncedCount", 0)
            changed = True
        if "createdCount" not in next_item:
            next_item["createdCount"] = next_item.get("syncedCount", 0)
            changed = True
        if "updatedCount" not in next_item:
            next_item["updatedCount"] = 0
            changed = True
        if "skippedCount" not in next_item:
            next_item["skippedCount"] = 0
            changed = True
        if "attemptNumber" not in next_item:
            next_item["attemptNumber"] = 1
            changed = True
        if "errorMessage" not in next_item:
            next_item["errorMessage"] = None
            changed = True
        normalized.append(next_item)
    if changed:
        write_json("notion-sync-history.json", normalized)
    return normalized


def _save_history(entries: list[dict]) -> None:
    write_json("notion-sync-history.json", entries)


def _records_for_source(source_type: SyncSource) -> list[dict]:
    if source_type == "daily_check_ins":
        return [item.model_dump(by_alias=True) for item in list_daily_check_ins()]
    if source_type == "health_signals":
        return [item.model_dump(by_alias=True) for item in list_health_signals()]
    if source_type == "daily_summary":
        return [_daily_summary_record(build_daily_briefing())]
    if source_type == "care_recommendations":
        return [item.model_dump(by_alias=True) for item in list_care_recommendations()]
    if source_type == "biomarker_reports":
        return [item.model_dump(by_alias=True) for item in list_biomarker_reports()]
    if source_type == "biomarker_trends":
        return [_biomarker_trend_record(item.model_dump(by_alias=True)) for item in list_biomarker_trends()]
    if source_type == "genetic_profile":
        profile = get_genetic_profile()
        return [_genetic_profile_record(profile)] if profile else []
    if source_type == "genetic_markers":
        profile = get_genetic_profile()
        return _genetic_marker_records(profile) if profile else []
    return [item.model_dump(by_alias=True) for item in list_follow_ups()]


def _daily_summary_record(briefing: DailyBriefing) -> dict:
    summary_date = briefing.generated_at[:10]
    return {
        "id": f"daily-summary-{summary_date}",
        "generatedAt": briefing.generated_at,
        "headline": briefing.headline,
        "summary": briefing.summary,
        "priorities": briefing.priorities,
        "dueTodayCount": briefing.due_today_count,
        "dueNowCount": briefing.due_now_count,
        "flaggedBiomarkerCount": briefing.flagged_biomarker_count,
        "activeCareRecommendationCount": briefing.active_care_recommendation_count,
        "careHighlights": briefing.care_highlights,
        "routineHighlights": briefing.routine_highlights,
        "movementHighlights": briefing.movement_highlights,
        "movementGuardrails": briefing.movement_guardrails,
    }


def _biomarker_trend_record(trend: dict) -> dict:
    marker_key = trend["markerKey"]
    latest_observed_at = trend.get("latestObservedAt") or "unknown-date"
    return {
        "id": f"biomarker-trend-{marker_key}",
        "markerKey": marker_key,
        "latestValue": trend.get("latestValue"),
        "latestUnit": trend.get("latestUnit"),
        "latestObservedAt": latest_observed_at,
        "previousValue": trend.get("previousValue"),
        "deltaAbsolute": trend.get("deltaAbsolute"),
        "deltaPercent": trend.get("deltaPercent"),
        "trendDirection": trend.get("trendDirection"),
        "sampleCount": trend.get("sampleCount"),
    }


def _genetic_profile_record(profile) -> dict:
    return {
        "id": profile.id,
        "sourceType": profile.source_type,
        "sourceLabel": profile.source_label,
        "importedAt": profile.imported_at,
        "summary": profile.summary,
        "markerCount": len(profile.markers),
        "markerKeys": [marker.key for marker in profile.markers],
        "markerOverview": [
            f"{marker.label}: {marker.interpretation}"
            for marker in profile.markers
        ],
        "confidenceLevels": sorted({marker.confidence for marker in profile.markers}),
    }


def _genetic_marker_records(profile) -> list[dict]:
    return [
        {
            "id": marker.id,
            "profileId": profile.id,
            "sourceLabel": profile.source_label,
            "importedAt": profile.imported_at,
            "key": marker.key,
            "label": marker.label,
            "category": marker.category,
            "genotype": marker.genotype,
            "interpretation": marker.interpretation,
            "recommendationStrength": marker.recommendation_strength,
            "confidence": marker.confidence,
            "sourceRef": marker.source_ref,
            "relatedDomains": marker.related_domains,
        }
        for marker in profile.markers
    ]


def _filename_for_source(source_type: SyncSource) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{source_type}.json"


def _normalize_record(source_type: SyncSource, record: dict) -> dict:
    if source_type == "daily_check_ins":
        return {
            "Name": f"{record['checkInType']} check-in",
            "Check-in Type": record["checkInType"],
            "Energy": record["energy"],
            "Stress": record["stress"],
            "Sleep Quality": record["sleepQuality"],
            "Note": record.get("notes"),
            "Created At": record["createdAt"],
            "Source Id": record["id"],
        }
    if source_type == "health_signals":
        return {
            "Name": record["title"],
            "Category": record["category"],
            "Severity": record["severity"],
            "Notes": record.get("notes"),
            "Observed At": record["observedAt"],
            "Source Id": record["id"],
        }
    if source_type == "daily_summary":
        return {
            "Name": f"{record['headline']} - {record['generatedAt'][:10]}",
            "Headline": record["headline"],
            "Summary": record["summary"],
            "Priorities": " | ".join(record["priorities"]),
            "Due Today Count": record["dueTodayCount"],
            "Due Now Count": record["dueNowCount"],
            "Biomarker Alerts": record["flaggedBiomarkerCount"],
            "Care Recommendation Count": record["activeCareRecommendationCount"],
            "Care Highlights": " | ".join(record["careHighlights"]),
            "Routine Highlights": " | ".join(record["routineHighlights"]),
            "Movement Highlights": " | ".join(record["movementHighlights"]),
            "Movement Guardrails": " | ".join(record["movementGuardrails"]),
            "Generated At": record["generatedAt"],
            "Source Id": record["id"],
        }
    if source_type == "care_recommendations":
        return {
            "Name": record["title"],
            "Source": record["source"],
            "Category": record["category"],
            "Priority": record["priority"],
            "Recommendation": record["recommendation"],
            "Active From": record.get("activeFrom"),
            "Review Frequency": record.get("reviewFrequency"),
            "Next Due": record.get("nextDue"),
            "Related Markers": " | ".join(record.get("relatedMarkers", [])),
            "Notes": record.get("notes"),
            "Status": record["status"],
            "Source Id": record["id"],
        }
    if source_type == "biomarker_reports":
        return {
            "Name": record["labName"] or record["id"],
            "Profile Id": record["profileId"],
            "Source Type": record["sourceType"],
            "Source Label": record["sourceLabel"],
            "Source Ref": record.get("sourceRef"),
            "Lab Name": record.get("labName"),
            "Collected At": record.get("collectedAt"),
            "Reported At": record.get("reportedAt"),
            "Fasting State": record.get("fastingState"),
            "Notes": record.get("notes"),
            "Created At": record["createdAt"],
            "Updated At": record["updatedAt"],
            "Source Id": record["id"],
        }
    if source_type == "biomarker_trends":
        return {
            "Name": record["markerKey"],
            "Marker Key": record["markerKey"],
            "Latest Value": record.get("latestValue"),
            "Latest Unit": record.get("latestUnit"),
            "Latest Observed At": record.get("latestObservedAt"),
            "Previous Value": record.get("previousValue"),
            "Delta Absolute": record.get("deltaAbsolute"),
            "Delta Percent": record.get("deltaPercent"),
            "Trend Direction": record.get("trendDirection"),
            "Sample Count": record.get("sampleCount"),
            "Source Id": record["id"],
        }
    if source_type == "genetic_profile":
        return {
            "Name": f"DNA profil - {record['sourceLabel']}",
            "Source Type": record["sourceType"],
            "Source Label": record["sourceLabel"],
            "Imported At": record["importedAt"],
            "Summary": record["summary"],
            "Marker Count": record["markerCount"],
            "Marker Keys": " | ".join(record["markerKeys"]),
            "Marker Overview": " || ".join(record["markerOverview"]),
            "Confidence Levels": " | ".join(record["confidenceLevels"]),
            "Source Id": record["id"],
        }
    if source_type == "genetic_markers":
        return {
            "Name": record["label"],
            "Profile Id": record["profileId"],
            "Source Label": record["sourceLabel"],
            "Imported At": record["importedAt"],
            "Marker Key": record["key"],
            "Category": record["category"],
            "Genotype": record.get("genotype"),
            "Interpretation": record["interpretation"],
            "Recommendation Strength": record["recommendationStrength"],
            "Confidence": record["confidence"],
            "Source Ref": record.get("sourceRef"),
            "Related Domains": " | ".join(record["relatedDomains"]),
            "Source Id": record["id"],
        }
    return {
        "Name": record["title"],
        "Trigger Type": record["triggerType"],
        "Message": record["message"],
        "Delay Label": record["delayLabel"],
        "Due At": record["dueAt"],
        "Status": record["status"],
        "Related Id": record["relatedId"],
        "Source Id": record["id"],
    }


def _database_id_for_source(source_type: SyncSource) -> str | None:
    if source_type == "daily_check_ins":
        return settings.notion_daily_checkins_database_id
    if source_type == "health_signals":
        return settings.notion_health_signals_database_id
    if source_type == "daily_summary":
        return settings.notion_daily_summaries_database_id
    if source_type == "care_recommendations":
        return settings.notion_care_recommendations_database_id
    if source_type == "biomarker_reports":
        return settings.notion_biomarker_reports_database_id
    if source_type == "biomarker_trends":
        return settings.notion_biomarker_trends_database_id
    if source_type == "genetic_profile":
        return settings.notion_genetic_profile_database_id
    if source_type == "genetic_markers":
        return settings.notion_genetic_markers_database_id
    return settings.notion_follow_ups_database_id


def _mode_for_source(source_type: SyncSource) -> Literal["outbox", "direct"]:
    if settings.notion_api_token and _database_id_for_source(source_type):
        return "direct"
    return "outbox"


def _write_outbox(source_type: SyncSource, normalized: list[dict]) -> Path:
    outbox_dir = _ensure_outbox_dir()
    outbox_path = outbox_dir / _filename_for_source(source_type)
    outbox_path.write_text(
        json.dumps(
            {
                "database": _DATABASE_LABELS[source_type],
                "sourceType": source_type,
                "generatedAt": _now_iso(),
                "records": normalized,
            },
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )
    return outbox_path


def _notion_property_value(name: str, value: str | int | None) -> dict:
    if name == "Name":
        return {
            "title": [
                {
                    "text": {
                        "content": str(value or ""),
                    }
                }
            ]
        }
    if value is None:
        return {"rich_text": []}
    if isinstance(value, int):
        return {"number": value}
    if name.endswith("At"):
        return {"date": {"start": value}}
    return {
        "rich_text": [
            {
                "text": {
                    "content": str(value),
                }
            }
        ]
    }


def _database_properties(database_id: str) -> dict[str, dict]:
    response = httpx.get(
        f"https://api.notion.com/v1/databases/{database_id}",
        headers={
            "Authorization": f"Bearer {settings.notion_api_token}",
            "Notion-Version": settings.notion_version,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("properties", {})


def _notion_property_value_for_type(
    property_type: str,
    value: str | int | None,
) -> dict:
    if property_type == "title":
        return {
            "title": [
                {
                    "text": {
                        "content": str(value or ""),
                    }
                }
            ]
        }
    if value is None:
        if property_type in {"rich_text", "title"}:
            return {property_type: []}
        if property_type in {"select", "status"}:
            return {property_type: None}
        if property_type == "date":
            return {"date": None}
        return {property_type: None}
    if property_type == "number":
        return {"number": value}
    if property_type == "date":
        return {"date": {"start": str(value)}}
    if property_type in {"select", "status"}:
        return {property_type: {"name": str(value)}}
    if property_type == "rich_text":
        return {
            "rich_text": [
                {
                    "text": {
                        "content": str(value),
                    }
                }
            ]
        }
    return _notion_property_value("", value)


def _build_notion_properties(
    record: dict[str, str | int | None],
    database_properties: dict[str, dict],
) -> dict:
    properties: dict[str, dict] = {}
    for key, value in record.items():
        property_meta = database_properties.get(key)
        if not property_meta:
            continue
        properties[key] = _notion_property_value_for_type(property_meta["type"], value)
    return properties


def _chunked(values: list[str], size: int) -> list[list[str]]:
    return [values[index : index + size] for index in range(0, len(values), size)]


def _create_notion_page(database_id: str, properties: dict) -> None:
    response = httpx.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {settings.notion_api_token}",
            "Notion-Version": settings.notion_version,
            "Content-Type": "application/json",
        },
        json={
            "parent": {
                "database_id": database_id,
            },
            "properties": properties,
        },
        timeout=30.0,
    )
    response.raise_for_status()


def _update_notion_page(page_id: str, properties: dict) -> None:
    response = httpx.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers={
            "Authorization": f"Bearer {settings.notion_api_token}",
            "Notion-Version": settings.notion_version,
            "Content-Type": "application/json",
        },
        json={
            "properties": properties,
        },
        timeout=30.0,
    )
    response.raise_for_status()


def _existing_notion_source_pages(
    database_id: str,
    source_ids: list[str],
    database_properties: dict[str, dict],
) -> dict[str, str]:
    if not source_ids or "Source Id" not in database_properties:
        return {}

    existing: dict[str, str] = {}
    property_type = database_properties["Source Id"]["type"]
    if property_type not in {"rich_text", "title"}:
        return existing

    filter_key = "rich_text" if property_type == "rich_text" else "title"
    unique_source_ids = list(dict.fromkeys(source_ids))

    for batch in _chunked(unique_source_ids, _SOURCE_ID_QUERY_BATCH_SIZE):
        filters = [
            {
                "property": "Source Id",
                filter_key: {
                    "equals": source_id,
                },
            }
            for source_id in batch
        ]
        response = httpx.post(
            f"https://api.notion.com/v1/databases/{database_id}/query",
            headers={
                "Authorization": f"Bearer {settings.notion_api_token}",
                "Notion-Version": settings.notion_version,
                "Content-Type": "application/json",
            },
            json={
                "filter": {
                    "or": filters,
                },
                "page_size": len(batch),
            },
            timeout=30.0,
        )
        response.raise_for_status()
        results = response.json().get("results", [])
        for result in results:
            properties = result.get("properties", {})
            source_property = properties.get("Source Id", {})
            fragments = source_property.get(property_type, [])
            source_id = "".join(
                fragment.get("plain_text", "")
                for fragment in fragments
                if isinstance(fragment, dict)
            )
            if source_id:
                existing[source_id] = result["id"]
    return existing


def _record_sync_attempt(
    *,
    source_type: SyncSource,
    mode: Literal["outbox", "direct"],
    outbox_path: Path,
    synced_ids: list[str],
    attempted_count: int,
    created_count: int,
    updated_count: int,
    skipped_count: int,
    delivery_state: Literal["queued", "synced", "failed"],
    error_message: str | None,
) -> NotionSyncResult:
    state = _state()
    source_state = dict(state["sourceStates"].get(source_type, _default_source_state(source_type)))
    source_state["sourceType"] = source_type
    source_state["mode"] = mode
    source_state["deliveryState"] = delivery_state
    source_state["syncedCount"] = len(synced_ids)
    source_state["attemptCount"] = int(source_state.get("attemptCount", 0)) + 1
    source_state["lastAttemptAt"] = _now_iso()
    source_state["lastError"] = error_message

    if delivery_state in {"queued", "synced"}:
        source_state["lastSuccessAt"] = source_state["lastAttemptAt"]
        source_state["consecutiveFailures"] = 0
    else:
        source_state["failureCount"] = int(source_state.get("failureCount", 0)) + 1
        source_state["consecutiveFailures"] = int(
            source_state.get("consecutiveFailures", 0)
        ) + 1

    state["sourceStates"][source_type] = source_state
    state["syncCounts"][source_type] = len(synced_ids)
    state["syncedIds"][source_type] = synced_ids
    if delivery_state in {"queued", "synced"}:
        state["lastSyncAt"] = source_state["lastAttemptAt"]
    _save_state(state)

    result = NotionSyncResult(
        sourceType=source_type,
        syncedCount=len(synced_ids),
        attemptedCount=attempted_count,
        createdCount=created_count,
        updatedCount=updated_count,
        skippedCount=skipped_count,
        outboxPath=str(outbox_path),
        databaseLabel=_DATABASE_LABELS[source_type],
        mode=mode,
        deliveryState=delivery_state,
        syncedIds=synced_ids,
        syncedAt=source_state["lastAttemptAt"],
        errorMessage=error_message,
    )
    history = _history()
    history.append(
        {
            "sourceType": result.source_type,
            "syncedCount": result.synced_count,
            "attemptedCount": result.attempted_count,
            "createdCount": result.created_count,
            "updatedCount": result.updated_count,
            "skippedCount": result.skipped_count,
            "outboxPath": result.outbox_path,
            "syncedAt": result.synced_at,
            "mode": result.mode,
            "deliveryState": result.delivery_state,
            "attemptNumber": source_state["attemptCount"],
            "errorMessage": result.error_message,
        }
    )
    _save_history(history[-50:])
    return result


def sync_source_to_outbox(source_type: SyncSource) -> NotionSyncResult:
    records = _records_for_source(source_type)
    normalized = [_normalize_record(source_type, record) for record in records]
    outbox_path = _write_outbox(source_type, normalized)
    mode = _mode_for_source(source_type)
    created_source_ids: list[str] = []
    updated_source_ids: list[str] = []
    matched_source_ids: list[str] = []
    error_message: str | None = None

    if mode == "direct":
        try:
            database_id = _database_id_for_source(source_type)
            if not database_id:
                raise ValueError(f"Missing Notion database ID for source '{source_type}'")
            database_properties = _database_properties(database_id)
            source_ids = [
                record["Source Id"]
                for record in normalized
                if isinstance(record.get("Source Id"), str)
            ]
            existing_source_pages = _existing_notion_source_pages(
                database_id,
                source_ids,
                database_properties,
            )
            for record in normalized:
                source_id = record.get("Source Id")
                if source_id in existing_source_pages:
                    if source_type in _UPDATE_EXISTING_SOURCES:
                        _update_notion_page(
                            existing_source_pages[source_id],
                            _build_notion_properties(record, database_properties),
                        )
                        if isinstance(source_id, str):
                            updated_source_ids.append(source_id)
                    elif isinstance(source_id, str):
                        matched_source_ids.append(source_id)
                    continue
                _create_notion_page(
                    database_id,
                    _build_notion_properties(record, database_properties),
                )
                if isinstance(source_id, str):
                    created_source_ids.append(source_id)
        except Exception as exc:
            error_message = str(exc)

    if mode == "outbox":
        synced_ids = [
            record["Source Id"]
            for record in normalized
            if isinstance(record.get("Source Id"), str)
        ]
        return _record_sync_attempt(
            source_type=source_type,
            mode=mode,
            outbox_path=outbox_path,
            synced_ids=synced_ids,
            attempted_count=len(normalized),
            created_count=len(synced_ids),
            updated_count=0,
            skipped_count=0,
            delivery_state="queued",
            error_message=None,
        )

    synced_ids = created_source_ids + updated_source_ids + matched_source_ids
    return _record_sync_attempt(
        source_type=source_type,
        mode=mode,
        outbox_path=outbox_path,
        synced_ids=synced_ids,
        attempted_count=len(normalized),
        created_count=len(created_source_ids),
        updated_count=len(updated_source_ids),
        skipped_count=len(matched_source_ids),
        delivery_state="failed" if error_message else "synced",
        error_message=error_message,
    )


def notion_sync_status() -> NotionSyncStatus:
    state = _state()
    _ensure_outbox_dir()
    return NotionSyncStatus(
        availableSources=list(_DATABASE_LABELS.keys()),
        lastSyncAt=state.get("lastSyncAt"),
        syncCounts=state.get("syncCounts", {}),
        outboxDir=str(settings.notion_outbox_dir),
        sourceStates={
            key: NotionSyncSourceState.model_validate(value)
            for key, value in state.get("sourceStates", {}).items()
        },
    )


def notion_sync_history() -> list[NotionSyncHistoryEntry]:
    entries = [NotionSyncHistoryEntry.model_validate(item) for item in _history()]
    return sorted(entries, key=lambda item: item.synced_at, reverse=True)


def notion_mapping_preview(source_type: SyncSource) -> NotionMappingPreview:
    records = _records_for_source(source_type)
    normalized = [_normalize_record(source_type, record) for record in records]
    property_names = list(normalized[0].keys()) if normalized else []
    sample_records = normalized[:3]
    return NotionMappingPreview(
        sourceType=source_type,
        databaseLabel=_DATABASE_LABELS[source_type],
        propertyNames=property_names,
        sampleRecords=sample_records,
        totalRecords=len(normalized),
    )
