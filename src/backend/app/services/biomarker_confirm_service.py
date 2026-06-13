from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.config import settings
from app.models import (
    BiomarkerConfirmImportInput,
    BiomarkerConfirmImportResult,
    BiomarkerImportDraftBatch,
    BiomarkerObservation,
    BiomarkerReport,
    BiomarkerTrendSnapshot,
)
from app.services.storage_service import read_json, write_json


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _draft_path_from_payload(payload: BiomarkerConfirmImportInput) -> Path:
    if payload.draft_path:
        path = Path(payload.draft_path)
        if not path.is_absolute():
            path = settings.project_root / path
        return path
    return settings.runtime_dir / "biomarker-import-draft-latest.json"


def _read_draft_batch(path: Path) -> BiomarkerImportDraftBatch:
    if not path.exists():
        raise FileNotFoundError(f"Biomarker draft nebyl nalezen: {path}")
    return BiomarkerImportDraftBatch.model_validate_json(path.read_text(encoding="utf-8"))


def _build_trend_snapshots(
    observations: list[BiomarkerObservation],
) -> list[BiomarkerTrendSnapshot]:
    grouped: dict[str, list[BiomarkerObservation]] = {}
    for observation in observations:
        grouped.setdefault(observation.marker_key, []).append(observation)

    trends: list[BiomarkerTrendSnapshot] = []
    for marker_key, items in grouped.items():
        ordered = sorted(items, key=lambda item: item.observed_at)
        latest = ordered[-1]
        previous = ordered[-2] if len(ordered) > 1 else None

        delta_absolute = None
        delta_percent = None
        trend_direction = "unknown"

        if (
            previous is not None
            and latest.value is not None
            and previous.value is not None
            and latest.unit == previous.unit
        ):
            delta_absolute = latest.value - previous.value
            if previous.value != 0:
                delta_percent = (delta_absolute / previous.value) * 100
            if delta_absolute > 0:
                trend_direction = "up"
            elif delta_absolute < 0:
                trend_direction = "down"
            else:
                trend_direction = "stable"

        trends.append(
            BiomarkerTrendSnapshot(
                markerKey=marker_key,
                latestValue=latest.value,
                latestUnit=latest.unit,
                latestObservedAt=latest.observed_at,
                previousValue=previous.value if previous is not None else None,
                deltaAbsolute=delta_absolute,
                deltaPercent=delta_percent,
                trendDirection=trend_direction,
                sampleCount=len(ordered),
            )
        )

    return sorted(trends, key=lambda item: item.marker_key)


def confirm_biomarker_import(
    payload: BiomarkerConfirmImportInput,
) -> BiomarkerConfirmImportResult:
    draft_path = _draft_path_from_payload(payload)
    batch = _read_draft_batch(draft_path)

    reports = [item.report for item in batch.reports]
    observations = [obs for item in batch.reports for obs in item.observations]
    trends = _build_trend_snapshots(observations)

    write_json(
        "biomarker-reports.json",
        [item.model_dump(mode="json", by_alias=True) for item in reports],
    )
    write_json(
        "biomarker-observations.json",
        [item.model_dump(mode="json", by_alias=True) for item in observations],
    )
    write_json(
        "biomarker-trend-snapshots.json",
        [item.model_dump(mode="json", by_alias=True) for item in trends],
    )
    write_json(
        "biomarker-confirmed-state.json",
        {
            "confirmedAt": _now_iso(),
            "draftPath": str(draft_path),
            "replaceExisting": payload.replace_existing,
            "reportCount": len(reports),
            "observationCount": len(observations),
            "trendCount": len(trends),
        },
    )

    return BiomarkerConfirmImportResult(
        confirmedAt=_now_iso(),
        draftPath=str(draft_path),
        replacedExisting=payload.replace_existing,
        reportCount=len(reports),
        observationCount=len(observations),
        trendCount=len(trends),
    )


def list_biomarker_reports() -> list[BiomarkerReport]:
    payload = read_json("biomarker-reports.json", [])
    return [BiomarkerReport.model_validate(item) for item in payload]


def list_biomarker_observations() -> list[BiomarkerObservation]:
    payload = read_json("biomarker-observations.json", [])
    return [BiomarkerObservation.model_validate(item) for item in payload]


def list_biomarker_trends() -> list[BiomarkerTrendSnapshot]:
    payload = read_json("biomarker-trend-snapshots.json", [])
    return [BiomarkerTrendSnapshot.model_validate(item) for item in payload]
