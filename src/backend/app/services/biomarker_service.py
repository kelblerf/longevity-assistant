from __future__ import annotations

import csv
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path

from app.models import (
    BiomarkerCsvImportInput,
    BiomarkerImportDraft,
    BiomarkerImportDraftBatch,
    BiomarkerObservation,
    BiomarkerReport,
)
from app.services.storage_service import write_json


REQUIRED_HEADERS = {
    "report_date",
    "reported_date",
    "lab_name",
    "fasting_state",
    "marker_key",
    "marker_label",
    "category",
    "value",
    "unit",
    "comparator",
    "reference_low",
    "reference_high",
    "reference_text",
    "status",
    "source_sheet",
    "source_row",
    "notes",
}

REVIEW_NOTE_MARKERS = (
    "date_approximated_from_year_header",
    "date_inferred_from_header",
    "fallback_report_date_used",
    "unit_normalized_from_sheet_possible_typo",
)

TEXT_NORMALIZATION_MAP = {
    "Î¼": "μ",
    "ÎĽ": "μ",
    "Ë†": "^",
    "âˆ’": "-",
    "Ã¡": "á",
    "Ã©": "é",
    "Ãě": "ě",
    "Ãí": "í",
    "Ãó": "ó",
    "Ãř": "ř",
    "Ãš": "Ú",
    "Ãů": "ů",
    "Ãý": "ý",
    "Ä›": "ě",
    "ÄŤ": "č",
    "Ĺ™": "ř",
    "Ĺˇ": "š",
    "Ăˇ": "á",
    "Ă©": "é",
    "Ă­": "í",
    "Ăł": "ó",
    "Ăş": "ú",
    "Ă˝": "ý",
    "ĂˇkladnĂ­": "ákladní",
}

UNIT_NORMALIZATION_MAP = {
    "10^9/l": "10^9/l",
    "10ˆ9/l": "10^9/l",
    "gigal/l": "gigal/l",
    "μg/l": "μg/l",
    "μkat/l": "μkat/l",
    "μmol/l": "μmol/l",
}


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _slug(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def _to_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    return float(text)


def _parse_notes(raw: str | None) -> list[str]:
    if raw is None:
        return []
    return [part.strip() for part in raw.split(";") if part.strip()]


def _normalize_text(raw: str | None) -> str | None:
    if raw is None:
        return None

    normalized = raw.strip()
    if not normalized:
        return None

    for source, target in TEXT_NORMALIZATION_MAP.items():
        normalized = normalized.replace(source, target)

    return normalized


def _normalize_unit(raw: str | None) -> str | None:
    normalized = _normalize_text(raw)
    if normalized is None:
        return None
    return UNIT_NORMALIZATION_MAP.get(normalized, normalized)


def _validate_headers(fieldnames: list[str] | None) -> None:
    if not fieldnames:
        raise ValueError("CSV draft nema zadne hlavicky.")

    missing = REQUIRED_HEADERS.difference(fieldnames)
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise ValueError(f"CSV draft nema povinne sloupce: {missing_text}")


def _build_report_id(profile_id: str, lab_name: str, report_date: str) -> str:
    return f"biomarker-report-{_slug(profile_id)}-{_slug(lab_name)}-{report_date}"


def _build_observation_id(report_id: str, marker_key: str, source_row: str) -> str:
    return f"{report_id}-{_slug(marker_key)}-{source_row}"


def build_biomarker_import_draft_from_csv(
    payload: BiomarkerCsvImportInput,
) -> BiomarkerImportDraftBatch:
    csv_path = Path(payload.file_path)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV draft nebyl nalezen: {csv_path}")

    imported_at = _now_iso()
    grouped_rows: dict[tuple[str, str, str, str], list[dict[str, str]]] = defaultdict(list)

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        _validate_headers(reader.fieldnames)
        for row in reader:
            marker_key = (row.get("marker_key") or "").strip()
            report_date = (row.get("report_date") or "").strip()
            lab_name = (row.get("lab_name") or "").strip()
            value = (row.get("value") or "").strip()
            if not marker_key or not report_date or not lab_name or not value:
                continue

            reported_date = (row.get("reported_date") or report_date).strip()
            fasting_state = (row.get("fasting_state") or "unknown").strip() or "unknown"
            grouped_rows[(lab_name, report_date, reported_date, fasting_state)].append(row)

    reports: list[BiomarkerImportDraft] = []
    batch_notes: list[str] = []

    for (lab_name, report_date, reported_date, fasting_state), rows in grouped_rows.items():
        report_id = _build_report_id(payload.profile_id, lab_name, report_date)
        report_notes = sorted(
            {
                note
                for row in rows
                for note in _parse_notes(row.get("notes"))
                if note in REVIEW_NOTE_MARKERS
            }
        )
        report = BiomarkerReport(
            id=report_id,
            profileId=payload.profile_id,
            sourceType=payload.source_type,
            sourceLabel=payload.source_label,
            sourceRef=str(csv_path),
            labName=lab_name,
            collectedAt=report_date,
            reportedAt=reported_date,
            fastingState=fasting_state,
            notes="; ".join(report_notes) if report_notes else None,
            rawText=None,
            createdAt=imported_at,
            updatedAt=imported_at,
        )

        observations: list[BiomarkerObservation] = []
        unresolved_notes: list[str] = []

        for row in rows:
            row_notes = _parse_notes(row.get("notes"))
            source_row = (row.get("source_row") or "").strip()
            observation = BiomarkerObservation(
                id=_build_observation_id(report_id, row["marker_key"], source_row or "row"),
                reportId=report_id,
                markerKey=row["marker_key"],
                markerLabel=_normalize_text(row["marker_label"]) or row["marker_label"],
                category=row["category"],
                value=_to_float(row.get("value")),
                unit=_normalize_unit(row.get("unit")),
                comparator=(row.get("comparator") or "exact").strip() or "exact",
                referenceLow=_to_float(row.get("reference_low")),
                referenceHigh=_to_float(row.get("reference_high")),
                referenceText=_normalize_text(row.get("reference_text")),
                status=(row.get("status") or "unknown").strip() or "unknown",
                measurementContext=(row.get("fasting_state") or "unknown").strip() or "unknown",
                observedAt=report_date,
                sourceLine=f"{row.get('source_sheet', '')}:{source_row}".strip(":"),
                confidence="parsed_high" if not row_notes else "parsed_medium",
            )
            observations.append(observation)

            if row_notes:
                unresolved_notes.append(
                    f"{row['marker_label']} ({lab_name}, {report_date}): {', '.join(row_notes)}"
                )

        reports.append(
            BiomarkerImportDraft(
                report=report,
                observations=observations,
                unresolvedNotes=sorted(set(unresolved_notes)),
            )
        )
        batch_notes.extend(unresolved_notes)

    batch = BiomarkerImportDraftBatch(
        profileId=payload.profile_id,
        sourceType=payload.source_type,
        sourceLabel=payload.source_label,
        filePath=str(csv_path),
        importedAt=imported_at,
        reportCount=len(reports),
        observationCount=sum(len(item.observations) for item in reports),
        reports=reports,
        unresolvedNotes=sorted(set(batch_notes)),
    )

    write_json(
        "biomarker-import-draft-latest.json",
        batch.model_dump(mode="json", by_alias=True),
    )
    return batch
