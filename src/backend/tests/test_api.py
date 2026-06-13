from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timezone
import json

from app.main import app
from app.config import settings


client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_bootstrap_returns_seeded_answer() -> None:
    response = client.get("/assistant/bootstrap")
    assert response.status_code == 200

    payload = response.json()
    assert payload["profile"]["displayName"] == "Frantisek"
    assert payload["rules"]["dnaPolicy"] == "recommendation_only"
    assert payload["answer"]["selectedScope"]["mode"] == "core_plus_domain"


def test_daily_briefing_endpoint() -> None:
    response = client.get("/assistant/briefing")
    assert response.status_code == 200
    payload = response.json()
    assert "headline" in payload
    assert "summary" in payload
    assert "priorities" in payload
    assert "flaggedBiomarkerCount" in payload
    assert "biomarkerHighlights" in payload
    assert "activeCareRecommendationCount" in payload
    assert "careHighlights" in payload
    assert "routineHighlights" in payload
    assert "movementHighlights" in payload
    assert "movementGuardrails" in payload


def test_ubz_search_endpoint() -> None:
    response = client.get("/knowledge/ubz/search", params={"query": "dech regenerace"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "dech regenerace"
    assert len(payload["hits"]) >= 1
    assert payload["hits"][0]["title"] == "Pusty a dech v souvislostech"
    assert payload["hits"][0]["sourceMode"] in {"seed", "notion_live"}
    assert payload["hits"][0]["authorityTier"] == "ubz_primary"


def test_ubz_sync_endpoint() -> None:
    previous_token = settings.notion_api_token
    try:
        settings.notion_api_token = "test-token"
        with (
            patch(
                "app.services.ubz_knowledge_service._search_page_id",
                return_value="page-123",
            ),
            patch(
                "app.services.ubz_knowledge_service._fetch_block_children",
                return_value=["Dech vede ke stabilite.", "Regenerace potrebuje rytmus."],
            ),
        ):
            response = client.post("/knowledge/ubz/sync")

        assert response.status_code == 200
        payload = response.json()
        assert payload["syncedCount"] >= 1
        assert any(item["synced"] for item in payload["items"])
    finally:
        settings.notion_api_token = previous_token


def test_evidence_search_endpoint() -> None:
    response = client.get("/knowledge/evidence/search", params={"query": "biomarkery labor"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["query"] == "biomarkery labor"
    assert len(payload["hits"]) >= 1
    assert payload["hits"][0]["title"] in {
        "Blood Biomarkers - Source of Truth",
        "NotebookLM - Medical Fundation",
    }
    assert payload["hits"][0]["authorityTier"] == "evidence_primary"


def test_evidence_sync_endpoint() -> None:
    previous_token = settings.notion_api_token
    try:
        settings.notion_api_token = "test-token"
        with patch(
            "app.services.evidence_knowledge_service._fetch_block_children",
            return_value=["Biomarkery potrebuji kontext.", "NotebookLM je research vrstva."],
        ):
            response = client.post("/knowledge/evidence/sync")

        assert response.status_code == 200
        payload = response.json()
        assert payload["syncedCount"] >= 1
        assert any(item["synced"] for item in payload["items"])
    finally:
        settings.notion_api_token = previous_token


def test_genetic_import_draft_endpoint() -> None:
    response = client.post(
        "/genetics/import-draft",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "rawText": "Vysla horsi tolerance laktozy a vyssi citlivost na kofein.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceType"] == "google_doc"
    assert len(payload["markers"]) >= 2
    assert any(marker["key"] == "lactose_tolerance" for marker in payload["markers"])


def test_genetic_import_draft_expanded_domains() -> None:
    response = client.post(
        "/genetics/import-draft",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "rawText": (
                "FUT2 GG signalizuje B12. IL6 CC a FADS1 GT ukazuji zanet. "
                "SOD2 CC a GPX1 CT ukazuji oxidacni stres. "
                "PPARG CC, TCF7L2 CT a FTO AT ukazuji inzulinovou citlivost. "
                "LPL CC, CETP AA, APOE E3/E3 a PON1 AA se tykaji lipidu. "
                "ACE ID a AGT TC ukazuji citlivost na sul. "
                "BCO1 GG ukazuje vitamin A."
            ),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    keys = {marker["key"] for marker in payload["markers"]}
    assert "b12_absorption" in keys
    assert "inflammation_regulation" in keys
    assert "oxidative_stress_response" in keys
    assert "insulin_sensitivity" in keys
    assert "lipid_regulation" in keys
    assert "salt_pressure_response" in keys
    assert "vitamin_a_conversion" in keys


def test_biomarker_import_draft_from_csv_endpoint(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.8,mmol/l,exact,3.5,5.6,,high,List 1,57,date_inferred_from_header",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,vitamin_d_25oh,Vitamin D 25-OH,vitamins,131.8,nmol/L,exact,75,500,,optimal,List 1,33,date_inferred_from_header; unit_normalized_from_sheet_possible_typo",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,homocysteine,Homocystein,methylation,8.32,Î¼mol/l,exact,5.4,16.2,,optimal,List 1,30,",
                "2022-01-01,2022-01-01,RLP 2022,unknown,urea,Urea,kidney,7.6,mmol/l,exact,2.5,7.4,,high,List 1,2,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )

    response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceType"] == "google_sheets_normalized_csv"
    assert payload["reportCount"] == 2
    assert payload["observationCount"] == 4
    assert len(payload["reports"]) == 2
    assert any(
        report["report"]["labName"] == "SYNLAB_k 7.10.2021"
        and len(report["observations"]) == 3
        for report in payload["reports"]
    )
    assert any("date_inferred_from_header" in note for note in payload["unresolvedNotes"])
    synlab_report = next(
        report for report in payload["reports"] if report["report"]["labName"] == "SYNLAB_k 7.10.2021"
    )
    homocysteine = next(
        item for item in synlab_report["observations"] if item["markerKey"] == "homocysteine"
    )
    assert homocysteine["unit"] == "μmol/l"


def test_biomarker_confirm_import_endpoint(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.8,mmol/l,exact,3.5,5.6,,high,List 1,57,date_inferred_from_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.0,mmol/l,exact,3.5,5.6,,optimal,List 1,57,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,urea,Urea,kidney,7.6,mmol/l,exact,2.5,7.4,,high,List 1,2,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )

    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200

    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200
    payload = confirm_response.json()
    assert payload["reportCount"] == 2
    assert payload["observationCount"] == 3
    assert payload["trendCount"] == 2

    reports = client.get("/biomarkers/reports")
    observations = client.get("/biomarkers/observations")
    trends = client.get("/biomarkers/trends")
    assert reports.status_code == 200
    assert observations.status_code == 200
    assert trends.status_code == 200
    assert len(reports.json()) == 2
    assert len(observations.json()) == 3
    glucose_trend = next(item for item in trends.json() if item["markerKey"] == "glucose_fasting")
    assert glucose_trend["sampleCount"] == 2
    assert glucose_trend["trendDirection"] in {"up", "down", "stable"}


def test_biomarker_priorities_endpoint() -> None:
    response = client.get("/biomarkers/priorities")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 5
    assert payload[0]["markerKey"] == "ldl_c"
    assert payload[0]["priorityRank"] == 1
    assert "cholesterol" in payload[0]["title"].lower()
    assert len(payload[0]["watchFor"]) >= 1
    assert len(payload[0]["linkWith"]) >= 1
    assert len(payload[0]["alertWhen"]) >= 1


def test_biomarker_priorities_can_be_replaced() -> None:
    response = client.put(
        "/biomarkers/priorities",
        json={
            "markers": [
                {
                    "markerKey": "glucose_fasting",
                    "title": "Glukoza nalacno",
                    "category": "glucose_metabolism",
                    "priorityRank": 1,
                    "whyItMatters": "Prakticky fokus pro glukozovou oblast.",
                },
                {
                    "markerKey": "hba1c",
                    "title": "HbA1c",
                    "category": "glucose_metabolism",
                    "priorityRank": 2,
                    "whyItMatters": "Dlouhodobejsi glukozovy signal.",
                },
            ]
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload[0]["markerKey"] == "glucose_fasting"
    assert payload[1]["markerKey"] == "hba1c"

    restore = client.put(
        "/biomarkers/priorities",
        json={
            "markers": [
                {
                    "markerKey": "ldl_c",
                    "title": "LDL cholesterol",
                    "category": "lipids",
                    "priorityRank": 1,
                    "whyItMatters": "Primarni lipidovy marker pro vazbu na preventivni doporuceni doktorky a kardiometabolickou prioritu.",
                },
                {
                    "markerKey": "total_cholesterol",
                    "title": "Celkovy cholesterol",
                    "category": "lipids",
                    "priorityRank": 2,
                    "whyItMatters": "Dava rychly prehled lipidove oblasti a ma byt cteny spolu s LDL, HDL a triglyceridy.",
                },
                {
                    "markerKey": "triglycerides",
                    "title": "Triglyceridy",
                    "category": "lipids",
                    "priorityRank": 3,
                    "whyItMatters": "Pomahaji cist vztah mezi jidlem, metabolickym rytmem a celou lipidovou oblasti.",
                },
                {
                    "markerKey": "hdl_c",
                    "title": "HDL cholesterol",
                    "category": "lipids",
                    "priorityRank": 4,
                    "whyItMatters": "Doplnuje lipidovy panel a ma smysl ho cist spolu s ostatnimi lipidy, ne izolovane.",
                },
                {
                    "markerKey": "glucose_fasting",
                    "title": "Glukoza nalacno",
                    "category": "glucose_metabolism",
                    "priorityRank": 5,
                    "whyItMatters": "Ukazuje zakladni glukozovy signal a dobre se propojuje s jidlem, energii a rytmem dne.",
                },
                {
                    "markerKey": "hba1c",
                    "title": "HbA1c",
                    "category": "glucose_metabolism",
                    "priorityRank": 6,
                    "whyItMatters": "Dava dlouhodobejsi pohled na glukozovou oblast a doplnuje glukozu nalacno.",
                },
                {
                    "markerKey": "vitamin_d_25oh",
                    "title": "Vitamin D 25-OH",
                    "category": "vitamins",
                    "priorityRank": 7,
                    "whyItMatters": "Je dulezity pro celkovou vitalitu, imunitu a dlouhodobe fungovani v longevity vrstve.",
                },
                {
                    "markerKey": "vitamin_b12",
                    "title": "Vitamin B12",
                    "category": "vitamins",
                    "priorityRank": 8,
                    "whyItMatters": "Je prakticky dulezity pro energii, nervovy system a vazbu na DNA signal kolem B12.",
                },
                {
                    "markerKey": "homocysteine",
                    "title": "Homocystein",
                    "category": "methylation",
                    "priorityRank": 9,
                    "whyItMatters": "Dobre propojuje methylaci, B12, folat a dlouhodoby kardiometabolicky kontext.",
                },
                {
                    "markerKey": "ferritin",
                    "title": "Ferritin",
                    "category": "iron",
                    "priorityRank": 10,
                    "whyItMatters": "Pomaha cist zelezitou a energetickou vrstvu, ne jen akutni serum iron.",
                },
                {
                    "markerKey": "crp",
                    "title": "CRP",
                    "category": "inflammation",
                    "priorityRank": 11,
                    "whyItMatters": "Je dobry orientacni marker zanetlive zateze a hodne se opira o kontext symptomu a regenerace.",
                },
                {
                    "markerKey": "tsh",
                    "title": "TSH",
                    "category": "thyroid",
                    "priorityRank": 12,
                    "whyItMatters": "Je zakladni vstup do cteni stitne zlazy a ma smysl ho cist spolu s FT4 a FT3.",
                },
                {
                    "markerKey": "ft4",
                    "title": "FT4",
                    "category": "thyroid",
                    "priorityRank": 13,
                    "whyItMatters": "Doplnuje stitnou osu a pomaha odlisit orientacni interpretaci od jedne izolovane hodnoty.",
                },
                {
                    "markerKey": "ft3",
                    "title": "FT3",
                    "category": "thyroid",
                    "priorityRank": 14,
                    "whyItMatters": "Uzavira zakladni thyroid panel ve vazbe na energii a celkovou regulaci organismu.",
                },
            ]
        },
    )
    assert restore.status_code == 200


def test_upsert_genetic_profile_endpoint() -> None:
    response = client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "Prvni potvrzeny DNA profil.",
            "markers": [
                {
                    "id": "marker-lactose",
                    "key": "lactose_tolerance",
                    "label": "Tolerance laktózy",
                    "category": "nutrition",
                    "genotype": None,
                    "interpretation": "Horsi tolerance laktózy jako doporucujici signal.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["nutrition", "digestion"],
                }
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["sourceType"] == "google_doc"
    assert payload["markers"][0]["key"] == "lactose_tolerance"

    get_response = client.get("/genetics/profile")
    assert get_response.status_code == 200
    assert get_response.json()["summary"] == "Prvni potvrzeny DNA profil."



def test_genetic_priorities_endpoint() -> None:
    client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "Potvrzeny DNA profil pro priority view.",
            "markers": [
                {
                    "id": "marker-b12",
                    "key": "b12_absorption",
                    "label": "Vitamin B12 / absorpce",
                    "category": "vitamins",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem B12.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["vitamins", "energy", "biomarkers"],
                },
                {
                    "id": "marker-methylation",
                    "key": "methylation_folate",
                    "label": "Folat / methylace",
                    "category": "methylation",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem methylace.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["methylation", "biomarkers"],
                },
            ],
        },
    )

    response = client.get("/genetics/priorities")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 2
    returned_keys = {item["markerKey"] for item in payload}
    assert "b12_absorption" in returned_keys
    assert "methylation_folate" in returned_keys
    b12_item = next(item for item in payload if item["markerKey"] == "b12_absorption")
    methylation_item = next(item for item in payload if item["markerKey"] == "methylation_folate")
    assert b12_item["whyItMatters"]
    assert "watchFor" in methylation_item
    assert "linkWith" in methylation_item


def test_genetic_priorities_can_be_reordered() -> None:
    client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "Potvrzeny DNA profil pro reorder.",
            "markers": [
                {
                    "id": "marker-b12",
                    "key": "b12_absorption",
                    "label": "Vitamin B12 / absorpce",
                    "category": "vitamins",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem B12.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["vitamins", "energy", "biomarkers"],
                },
                {
                    "id": "marker-methylation",
                    "key": "methylation_folate",
                    "label": "Folat / methylace",
                    "category": "methylation",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem methylace.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["methylation", "biomarkers"],
                },
            ],
        },
    )

    put_response = client.put(
        "/genetics/priorities",
        json={
            "markers": [
                {
                    "markerKey": "methylation_folate",
                    "title": "Folat / methylace",
                    "category": "methylation",
                    "priorityRank": 1,
                    "whyItMatters": "Nejdriv chci drzet methylaci.",
                    "watchFor": ["homocystein"],
                    "linkWith": ["vitamin_b12"],
                    "alertWhen": ["trend jde proti B12"],
                    "confidence": "confirmed",
                    "recommendationStrength": "medium",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem methylace.",
                },
                {
                    "markerKey": "b12_absorption",
                    "title": "Vitamin B12 / absorpce",
                    "category": "vitamins",
                    "priorityRank": 2,
                    "whyItMatters": "B12 chci drzet hned za methylaci.",
                    "watchFor": ["energie"],
                    "linkWith": ["homocysteine"],
                    "alertWhen": ["B12 pada"],
                    "confidence": "confirmed",
                    "recommendationStrength": "medium",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem B12.",
                },
            ]
        },
    )
    assert put_response.status_code == 200
    reordered = put_response.json()
    assert reordered[0]["markerKey"] == "methylation_folate"
    assert reordered[0]["whyItMatters"] == "Nejdriv chci drzet methylaci."


def test_notion_sync_outbox_endpoints() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 5,
            "stress": 5,
            "sleepQuality": 6,
        },
    )

    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_checkins_database_id
    try:
        settings.notion_api_token = None
        settings.notion_daily_checkins_database_id = None

        response = client.post("/integrations/notion/sync/daily-check-ins")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "daily_check_ins"
        assert payload["mode"] == "outbox"
        assert payload["syncedCount"] >= 1
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_checkins_database_id = previous_db

    status = client.get("/integrations/notion/status")
    assert status.status_code == 200
    assert "daily_check_ins" in status.json()["syncCounts"]

    history = client.get("/integrations/notion/history")
    assert history.status_code == 200
    assert len(history.json()) >= 1

    preview = client.get("/integrations/notion/preview/daily_check_ins")
    assert preview.status_code == 200
    assert preview.json()["sourceType"] == "daily_check_ins"
    assert "Name" in preview.json()["propertyNames"]


def test_notion_daily_summary_sync_outbox_endpoint() -> None:
    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_summaries_database_id
    try:
        settings.notion_api_token = None
        settings.notion_daily_summaries_database_id = None

        response = client.post("/integrations/notion/sync/daily-summary")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "daily_summary"
        assert payload["mode"] == "outbox"
        assert payload["syncedCount"] == 1

        preview = client.get("/integrations/notion/preview/daily_summary")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["sourceType"] == "daily_summary"
        assert "Headline" in preview_payload["propertyNames"]
        assert "Summary" in preview_payload["propertyNames"]
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_summaries_database_id = previous_db


def test_notion_genetic_profile_sync_outbox_endpoint() -> None:
    profile_response = client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "Potvrzeny DNA profil pro save-back.",
            "markers": [
                {
                    "id": "marker-lactose",
                    "key": "lactose_tolerance",
                    "label": "Tolerance laktozy",
                    "category": "nutrition",
                    "genotype": None,
                    "interpretation": "Doporucujici signal pro traveni a reakci na mlecne produkty.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["nutrition", "digestion", "dna_conflict"],
                },
                {
                    "id": "marker-lipids",
                    "key": "lipid_regulation",
                    "label": "Lipidova regulace",
                    "category": "cardiometabolic",
                    "genotype": None,
                    "interpretation": "Doporucujici signal pro LDL, HDL a triglyceridy.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["cardiometabolic", "lipids", "biomarkers"],
                },
            ],
        },
    )
    assert profile_response.status_code == 200

    previous_token = settings.notion_api_token
    previous_db = settings.notion_genetic_profile_database_id
    try:
        settings.notion_api_token = None
        settings.notion_genetic_profile_database_id = None

        response = client.post("/integrations/notion/sync/genetic-profile")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "genetic_profile"
        assert payload["mode"] == "outbox"
        assert payload["syncedCount"] == 1

        preview = client.get("/integrations/notion/preview/genetic_profile")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["sourceType"] == "genetic_profile"
        assert "Marker Count" in preview_payload["propertyNames"]
        assert "Marker Keys" in preview_payload["propertyNames"]
        assert "Confidence Levels" in preview_payload["propertyNames"]
    finally:
        settings.notion_api_token = previous_token
        settings.notion_genetic_profile_database_id = previous_db


def test_notion_genetic_markers_sync_outbox_endpoint() -> None:
    profile_response = client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "Potvrzeny DNA profil pro marker save-back.",
            "markers": [
                {
                    "id": "marker-lactose",
                    "key": "lactose_tolerance",
                    "label": "Tolerance laktozy",
                    "category": "nutrition",
                    "genotype": None,
                    "interpretation": "Doporucujici signal pro traveni.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["nutrition", "digestion"],
                },
                {
                    "id": "marker-b12",
                    "key": "b12_absorption",
                    "label": "Vitamin B12 / absorpce",
                    "category": "vitamins",
                    "genotype": None,
                    "interpretation": "Doporucujici signal pro B12 a homocystein.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["vitamins", "energy", "biomarkers"],
                },
            ],
        },
    )
    assert profile_response.status_code == 200

    previous_token = settings.notion_api_token
    previous_db = settings.notion_genetic_markers_database_id
    try:
        settings.notion_api_token = None
        settings.notion_genetic_markers_database_id = None

        response = client.post("/integrations/notion/sync/genetic-markers")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "genetic_markers"
        assert payload["mode"] == "outbox"
        assert payload["syncedCount"] == 2

        preview = client.get("/integrations/notion/preview/genetic_markers")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["sourceType"] == "genetic_markers"
        assert "Marker Key" in preview_payload["propertyNames"]
        assert "Interpretation" in preview_payload["propertyNames"]
        assert "Related Domains" in preview_payload["propertyNames"]
    finally:
        settings.notion_api_token = previous_token
        settings.notion_genetic_markers_database_id = previous_db


def test_notion_daily_summary_direct_write_back_updates_existing_source_id() -> None:
    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_summaries_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_daily_summaries_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        existing_source_id = f"daily-summary-{datetime.now(timezone.utc).date().isoformat()}"
        existing_page_id = "page-123"

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Headline": {"type": "rich_text"},
                    "Summary": {"type": "rich_text"},
                    "Priorities": {"type": "rich_text"},
                    "Due Today Count": {"type": "number"},
                    "Due Now Count": {"type": "number"},
                    "Biomarker Alerts": {"type": "number"},
                    "Care Recommendation Count": {"type": "number"},
                    "Care Highlights": {"type": "rich_text"},
                    "Routine Highlights": {"type": "rich_text"},
                    "Movement Highlights": {"type": "rich_text"},
                    "Movement Guardrails": {"type": "rich_text"},
                    "Generated At": {"type": "date"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={existing_source_id: existing_page_id},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/daily-summary")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "daily_summary"
        assert payload["mode"] == "direct"
        assert payload["syncedCount"] == 1
        assert payload["syncedIds"] == [existing_source_id]
        assert not mocked_post.called
        assert mocked_patch.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_summaries_database_id = previous_db


def test_notion_care_recommendations_sync_outbox_endpoint() -> None:
    client.post(
        "/care-recommendations",
        json={
            "title": "Preventivni lipidova kontrola a rezim",
            "source": "Prakticka doktorka",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Omezit tuky, uzeniny a drzet vyssi pohyb.",
            "reviewFrequency": "rocne",
            "nextDue": "2027-01-15",
            "relatedMarkers": ["total_cholesterol", "ldl_c"],
            "notes": "Skutecne doporuceni.",
        },
    )

    previous_token = settings.notion_api_token
    previous_db = settings.notion_care_recommendations_database_id
    try:
        settings.notion_api_token = None
        settings.notion_care_recommendations_database_id = None

        response = client.post("/integrations/notion/sync/care-recommendations")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "care_recommendations"
        assert payload["mode"] == "outbox"
        assert payload["syncedCount"] >= 1

        preview = client.get("/integrations/notion/preview/care_recommendations")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["sourceType"] == "care_recommendations"
        assert "Recommendation" in preview_payload["propertyNames"]
        assert "Priority" in preview_payload["propertyNames"]
    finally:
        settings.notion_api_token = previous_token
        settings.notion_care_recommendations_database_id = previous_db


def test_notion_care_recommendations_direct_write_back_updates_existing_source_id() -> None:
    created = client.post(
        "/care-recommendations",
        json={
            "title": "Lipidova prevence",
            "source": "Prakticka doktorka",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Zamereni na zivotni styl a kontrolu lipidove oblasti.",
            "reviewFrequency": "rocne",
            "nextDue": "2027-01-15",
            "relatedMarkers": ["total_cholesterol", "ldl_c"],
        },
    ).json()

    previous_token = settings.notion_api_token
    previous_db = settings.notion_care_recommendations_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_care_recommendations_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Source": {"type": "rich_text"},
                    "Category": {"type": "select"},
                    "Priority": {"type": "select"},
                    "Recommendation": {"type": "rich_text"},
                    "Active From": {"type": "date"},
                    "Review Frequency": {"type": "rich_text"},
                    "Next Due": {"type": "date"},
                    "Related Markers": {"type": "rich_text"},
                    "Notes": {"type": "rich_text"},
                    "Status": {"type": "status"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={created["id"]: "page-456"},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/care-recommendations")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "care_recommendations"
        assert payload["mode"] == "direct"
        assert created["id"] in payload["syncedIds"]
        assert mocked_patch.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_care_recommendations_database_id = previous_db


def test_notion_biomarker_reports_sync_outbox_endpoint() -> None:
    previous_token = settings.notion_api_token
    previous_db = settings.notion_biomarker_reports_database_id
    try:
        settings.notion_api_token = None
        settings.notion_biomarker_reports_database_id = None

        response = client.post("/integrations/notion/sync/biomarker-reports")
        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "biomarker_reports"
        assert payload["mode"] == "outbox"

        preview = client.get("/integrations/notion/preview/biomarker_reports")
        assert preview.status_code == 200
        preview_payload = preview.json()
        assert preview_payload["sourceType"] == "biomarker_reports"
        assert "Lab Name" in preview_payload["propertyNames"]
        assert "Collected At" in preview_payload["propertyNames"]
    finally:
        settings.notion_api_token = previous_token
        settings.notion_biomarker_reports_database_id = previous_db


def test_notion_biomarker_trends_direct_write_back_updates_existing_source_id() -> None:
    client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(
                (
                    Path(__file__).resolve().parents[3]
                    / "notes"
                    / "biomarker-intake-draft-rozbor-krve.csv"
                )
            ),
        },
    )
    client.post("/biomarkers/confirm-import", json={})

    previous_token = settings.notion_api_token
    previous_db = settings.notion_biomarker_trends_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_biomarker_trends_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        existing_source_id = "biomarker-trend-glucose_fasting"

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Marker Key": {"type": "rich_text"},
                    "Latest Value": {"type": "number"},
                    "Latest Unit": {"type": "rich_text"},
                    "Latest Observed At": {"type": "date"},
                    "Previous Value": {"type": "number"},
                    "Delta Absolute": {"type": "number"},
                    "Delta Percent": {"type": "number"},
                    "Trend Direction": {"type": "select"},
                    "Sample Count": {"type": "number"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={existing_source_id: "page-789"},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/biomarker-trends")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "biomarker_trends"
        assert payload["mode"] == "direct"
        assert existing_source_id in payload["syncedIds"]
        assert mocked_patch.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_biomarker_trends_database_id = previous_db


def test_notion_direct_write_back_for_daily_check_ins() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 8,
            "stress": 3,
            "sleepQuality": 8,
        },
    )

    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_checkins_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_daily_checkins_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Check-in Type": {"type": "select"},
                    "Energy": {"type": "number"},
                    "Stress": {"type": "number"},
                    "Sleep Quality": {"type": "number"},
                    "Note": {"type": "rich_text"},
                    "Created At": {"type": "date"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
        ):
            response = client.post("/integrations/notion/sync/daily-check-ins")

        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] == "direct"
        assert mocked_post.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_checkins_database_id = previous_db


def test_notion_direct_write_back_skips_existing_source_ids() -> None:
    created = client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 7,
            "stress": 2,
            "sleepQuality": 8,
        },
    ).json()

    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_checkins_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_daily_checkins_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Check-in Type": {"type": "select"},
                    "Energy": {"type": "number"},
                    "Stress": {"type": "number"},
                    "Sleep Quality": {"type": "number"},
                    "Note": {"type": "rich_text"},
                    "Created At": {"type": "date"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={created["id"]: "page-123"},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/daily-check-ins")

        assert response.status_code == 200
        payload = response.json()
        assert payload["mode"] == "direct"
        assert created["id"] in payload["syncedIds"]
        assert payload["syncedCount"] == len(payload["syncedIds"])
        assert mocked_post.called
        assert not mocked_patch.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_checkins_database_id = previous_db


def test_notion_health_signals_direct_write_back_updates_existing_source_id() -> None:
    created = client.post(
        "/health-signals",
        json={
            "category": "stress",
            "title": "Napeti v tele",
            "severity": "medium",
            "notes": "po ranu",
        },
    ).json()

    previous_token = settings.notion_api_token
    previous_db = settings.notion_health_signals_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_health_signals_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Category": {"type": "select"},
                    "Severity": {"type": "select"},
                    "Notes": {"type": "rich_text"},
                    "Observed At": {"type": "date"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={created["id"]: "page-789"},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/health-signals")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "health_signals"
        assert payload["mode"] == "direct"
        assert created["id"] in payload["syncedIds"]
        assert mocked_patch.called
        assert mocked_post.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_health_signals_database_id = previous_db


def test_notion_follow_ups_direct_write_back_updates_existing_source_id() -> None:
    meal = client.post(
        "/meals",
        json={
            "title": "Kefir",
            "mealType": "breakfast",
            "notes": "test",
            "tags": ["lactose"],
        },
    ).json()
    created = client.post(f"/meals/{meal['id']}/follow-up").json()

    previous_token = settings.notion_api_token
    previous_db = settings.notion_follow_ups_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_follow_ups_database_id = "test-database-id"
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None

        with (
            patch(
                "app.services.notion_sync_service._database_properties",
                return_value={
                    "Name": {"type": "title"},
                    "Trigger Type": {"type": "select"},
                    "Message": {"type": "rich_text"},
                    "Delay Label": {"type": "rich_text"},
                    "Due At": {"type": "date"},
                    "Status": {"type": "status"},
                    "Related Id": {"type": "rich_text"},
                    "Source Id": {"type": "rich_text"},
                },
            ),
            patch(
                "app.services.notion_sync_service._existing_notion_source_pages",
                return_value={created["id"]: "page-987"},
            ),
            patch("app.services.notion_sync_service.httpx.post", return_value=mock_response) as mocked_post,
            patch("app.services.notion_sync_service.httpx.patch", return_value=mock_response) as mocked_patch,
        ):
            response = client.post("/integrations/notion/sync/follow-ups")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "follow_ups"
        assert payload["mode"] == "direct"
        assert created["id"] in payload["syncedIds"]
        assert mocked_patch.called
        assert mocked_post.called
    finally:
        settings.notion_api_token = previous_token
        settings.notion_follow_ups_database_id = previous_db


def test_notion_sync_direct_failure_returns_audit_result() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 6,
            "stress": 4,
            "sleepQuality": 7,
        },
    )

    previous_token = settings.notion_api_token
    previous_db = settings.notion_daily_checkins_database_id
    try:
        settings.notion_api_token = "test-token"
        settings.notion_daily_checkins_database_id = "test-database-id"

        with patch(
            "app.services.notion_sync_service._database_properties",
            side_effect=RuntimeError("Notion API unavailable"),
        ):
            response = client.post("/integrations/notion/sync/daily-check-ins")

        assert response.status_code == 200
        payload = response.json()
        assert payload["sourceType"] == "daily_check_ins"
        assert payload["mode"] == "direct"
        assert payload["deliveryState"] == "failed"
        assert payload["attemptedCount"] >= 1
        assert payload["syncedCount"] == 0
        assert payload["errorMessage"] == "Notion API unavailable"

        status = client.get("/integrations/notion/status")
        assert status.status_code == 200
        source_state = status.json()["sourceStates"]["daily_check_ins"]
        assert source_state["deliveryState"] == "failed"
        assert source_state["failureCount"] >= 1
        assert source_state["lastError"] == "Notion API unavailable"

        history = client.get("/integrations/notion/history")
        assert history.status_code == 200
        assert history.json()[0]["deliveryState"] == "failed"
        assert history.json()[0]["errorMessage"] == "Notion API unavailable"
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_checkins_database_id = previous_db


def test_chat_respond_for_lactose_conflict() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Dal jsem si jogurt a mlecny koktejl, je to v pohode?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "laktózy" in payload["answer"]["summary"] or "laktosy" in payload["answer"]["summary"]
    assert "app_nutrition_data" in payload["answer"]["selectedScope"]["groups"]
    section_kinds = [section["kind"] for section in payload["answer"]["sections"]]
    assert section_kinds[0] == "profile_context"
    assert section_kinds[1] == "workflow_context"
    assert "food_biomarker_context" in section_kinds
    assert "evidence_basis" in section_kinds
    assert "model_interpretation" in section_kinds


def test_chat_respond_explains_runtime_vs_notion_vs_knowledge_workflow() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Co je pro me dnes nejdulezitejsi?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    workflow_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "workflow_context"
    )
    normalized = workflow_section["content"].lower()
    assert "lokalni runtime" in normalized
    assert "notion" in normalized
    assert "knowledge" in normalized or "evidence" in normalized


def test_chat_respond_enriches_ubz_hits() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak dnes pracovat s dechem a regeneraci?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    ubz_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "ubz_basis"
    )
    assert "dech" in ubz_section["content"].lower()
    assert any(
        source["label"] == "Pusty a dech v souvislostech"
        for source in payload["answer"]["sources"]
    )
    assert any(
        source["authorityTier"] == "ubz_primary"
        for source in payload["answer"]["sources"]
        if source["type"] == "ubz_framework"
    )
    assert any(
        step
        for step in payload["answer"]["nextSteps"]
        if "dechový blok" in step.lower() or "dechovy blok" in step.lower()
    )


    section_kinds = [section["kind"] for section in payload["answer"]["sections"]]
    assert "routine_basis" in section_kinds
    assert "biomarker_insight" not in section_kinds


def test_chat_respond_surfaces_knowledge_titles_in_regulation_output() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak dnes pracovat s dechem a energii?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Pusty a dech v souvislostech" in payload["answer"]["summary"]
    assert any(
        "Pusty a dech v souvislostech" in step
        for step in payload["answer"]["nextSteps"]
    )
    interpretation_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "model_interpretation"
    )
    assert "Pusty a dech v souvislostech" in interpretation_section["content"]


def test_chat_respond_enriches_ubz_hits_with_diacritics() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak dnes pracovat s dýcháním a regenerací?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    ubz_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "ubz_basis"
    )
    assert "dech" in ubz_section["content"].lower()
    assert any(
        source["label"] == "Pusty a dech v souvislostech"
        for source in payload["answer"]["sources"]
    )


def test_chat_respond_enriches_evidence_hits() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak pracovat s biomarkery a laboratornimi hodnotami?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    evidence_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "evidence_basis"
    )
    assert "evidence" in evidence_section["content"].lower() or "biomarker" in evidence_section["content"].lower()
    assert any(
        source["type"] == "notebooklm_research"
        for source in payload["answer"]["sources"]
    )
    assert any(
        source["authorityTier"] == "evidence_primary"
        for source in payload["answer"]["sources"]
        if source["type"] == "notebooklm_research"
    )
    assert any(
        source["type"] == "app_health_data"
        for source in payload["answer"]["sources"]
    )


def test_chat_respond_surfaces_evidence_titles_in_biomarker_output() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak cist biomarkery, B12 a homocystein?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert "Blood Biomarkers - Source of Truth" in payload["answer"]["summary"]
    assert any(
        "Blood Biomarkers - Source of Truth" in step
        for step in payload["answer"]["nextSteps"]
    )
    assert any(
        "odlisit osobni kontext" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )


def test_chat_respond_surfaces_practical_ubz_guidance_in_output() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak dnes pracovat s dechem a regeneraci?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert any(
        "jemnou regulaci dechu" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )
    interpretation_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "model_interpretation"
    )
    assert "prakticky z ni plyne" in interpretation_section["content"].lower()


def test_chat_respond_enriches_evidence_hits_with_diacritics() -> None:
    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak číst krevní biomarkery a glukózu?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    evidence_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "evidence_basis"
    )
    assert "evidence" in evidence_section["content"].lower() or "biomarker" in evidence_section["content"].lower()
    assert any(
        source["type"] == "notebooklm_research"
        for source in payload["answer"]["sources"]
    )


def test_chat_respond_uses_operational_context() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 4,
            "stress": 7,
            "sleepQuality": 5,
            "notes": "Narocny start dne",
        },
    )
    client.post(
        "/health-signals",
        json={
            "category": "stress",
            "title": "Napeti v tele",
            "severity": "medium",
            "notes": "po ranu",
        },
    )

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Co je pro me dnes nejdulezitejsi?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    profile_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "profile_context"
    )
    assert "4/10" in profile_section["content"]
    assert "Napeti v tele" in profile_section["content"]


def test_chat_respond_uses_runtime_context_for_ubz_retrieval() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 3,
            "stress": 8,
            "sleepQuality": 4,
            "notes": "Pretizeny start dne",
        },
    )
    client.post(
        "/health-signals",
        json={
            "category": "stress",
            "title": "Napeti v tele",
            "severity": "medium",
            "notes": "po ranu",
        },
    )

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Co je pro me dnes nejdulezitejsi?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    ubz_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "ubz_basis"
    )
    assert "Clovekologie" in ubz_section["content"] or "Pusty a dech v souvislostech" in ubz_section["content"]
    assert any(
        source["label"] in {"Clovekologie", "Pusty a dech v souvislostech"}
        for source in payload["answer"]["sources"]
    )


def test_daily_briefing_and_chat_use_confirmed_biomarkers(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.8,mmol/l,exact,3.5,5.6,,high,List 1,57,date_inferred_from_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.0,mmol/l,exact,3.5,5.6,,optimal,List 1,57,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,total_cholesterol,Celkovy cholesterol,lipids,6.2,mmol/l,exact,2.9,5.0,,high,List 1,26,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )

    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200

    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    briefing_response = client.get("/assistant/briefing")
    assert briefing_response.status_code == 200
    briefing = briefing_response.json()
    assert briefing["flaggedBiomarkerCount"] >= 1
    assert any("Celkovy cholesterol" in item or "Glukoza v plazme" in item for item in briefing["biomarkerHighlights"])

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    chat_response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak mam cist biomarkery a krevni trendy?",
        },
    )
    assert chat_response.status_code == 200
    payload = chat_response.json()
    biomarker_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "extended_context"
    )
    assert "biomarker vrstva" in biomarker_section["content"].lower()
    assert "Celkovy cholesterol" in biomarker_section["content"] or "Glukoza v plazme" in biomarker_section["content"]


def test_biomarker_insight_composer_for_cholesterol_family(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,total_cholesterol,Celkovy cholesterol,lipids,5.4,mmol/l,exact,2.9,5.0,,high,List 1,26,date_inferred_from_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,total_cholesterol,Celkovy cholesterol,lipids,6.2,mmol/l,exact,2.9,5.0,,high,List 1,26,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ldl_c,LDL cholesterol,lipids,4.0,mmol/l,exact,1.2,3.0,,high,List 1,27,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,hdl_c,HDL cholesterol,lipids,1.3,mmol/l,exact,1.0,5.0,,optimal,List 1,28,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )

    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak si stojim s cholesterolem a lipidy?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    insight_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "biomarker_insight"
    )
    assert "Celkovy cholesterol" in insight_section["content"]
    assert "LDL cholesterol" in insight_section["content"]
    assert "lipidove oblasti" in insight_section["content"]
    assert "Co sledovat:" in insight_section["content"]
    assert "S cim spojovat:" in insight_section["content"]
    assert "Kdy zpozornet:" in insight_section["content"]


def test_biomarker_insight_composer_for_glucose_family(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2021-10-07,2021-10-07,SYNLAB_k 7.10.2021,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.8,mmol/l,exact,3.5,5.6,,high,List 1,57,date_inferred_from_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.0,mmol/l,exact,3.5,5.6,,optimal,List 1,57,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,hba1c,HbA1c,glucose_metabolism,36.0,mmol/mol,exact,20,39,,optimal,List 1,58,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )

    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Co mi rika glukoza a HbA1c?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    insight_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "biomarker_insight"
    )
    assert "Glukoza v plazme" in insight_section["content"]
    assert "HbA1c" in insight_section["content"]
    assert "glukozove oblasti" in insight_section["content"]
    assert "Co sledovat:" in insight_section["content"]
    assert "S cim spojovat:" in insight_section["content"]


def test_food_to_biomarker_context_is_used_for_glucose_and_lipids(tmp_path: Path) -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "breakfast",
            "title": "Sladky jogurt s ovocem",
            "tags": ["lactose", "protein", "sugar"],
        },
    )
    assert meal_response.status_code == 200

    csv_path = tmp_path / "biomarker-draft.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,glucose_fasting,Glukoza v plazme,glucose_metabolism,5.8,mmol/l,exact,3.5,5.6,,high,List 1,57,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,total_cholesterol,Celkovy cholesterol,lipids,6.2,mmol/l,exact,2.9,5.0,,high,List 1,26,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak souvisi moje jidlo s glukozou a cholesterolem?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    evidence_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "evidence_basis"
    )
    food_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "food_biomarker_context"
    )
    assert "Posledni zapsane jidlo je Sladky jogurt s ovocem" in evidence_section["content"]
    assert "Posledni zapsane jidlo je Sladky jogurt s ovocem" in food_section["content"]
    assert "glukozovou oblast" in evidence_section["content"] or "lipidovou oblast" in evidence_section["content"]
    assert any(
        "poslednim jidlem" in step.lower()
        or "posledni jidlo" in step.lower()
        or "posledním jídlem" in step.lower()
        or "poslední jídlo" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )


def test_food_to_biomarker_context_is_used_for_b12_homocysteine_and_ferritin(tmp_path: Path) -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "lunch",
            "title": "Hovezi maso se spenatem",
            "tags": ["protein", "iron"],
        },
    )
    assert meal_response.status_code == 200

    csv_path = tmp_path / "biomarker-draft-b12.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,vitamin_b12,Vitamin B12,vitamins,220,pmol/l,exact,140,650,,optimal,List 1,60,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,homocysteine,Homocystein,methylation,14.0,umol/l,exact,5,12,,high,List 1,61,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ferritin,Ferritin,iron,35,ug/l,exact,30,400,,optimal,List 1,62,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak souvisi moje jidlo s B12, homocysteinem a ferritinem?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    evidence_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "evidence_basis"
    )
    food_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "food_biomarker_context"
    )
    assert "Hovezi maso se spenatem" in evidence_section["content"]
    assert "Hovezi maso se spenatem" in food_section["content"]
    assert "B12 a homocystein" in evidence_section["content"]
    assert "ferritin a zelezitou vrstvu" in evidence_section["content"]


def test_specific_meal_query_beats_generic_signal_fallback(tmp_path: Path) -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "lunch",
            "title": "Hovezi maso se spenatem",
            "tags": ["protein", "iron"],
        },
    )
    assert meal_response.status_code == 200

    signal_response = client.post(
        "/health-signals",
        json={
            "title": "slabe chveni kolem zaludku",
            "category": "digestion",
            "severity": "medium",
        },
    )
    assert signal_response.status_code == 200

    csv_path = tmp_path / "biomarker-draft-meal-priority.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,vitamin_b12,Vitamin B12,vitamins,220,pmol/l,exact,140,650,,optimal,List 1,60,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,homocysteine,Homocystein,methylation,14.0,umol/l,exact,5,12,,high,List 1,61,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Dal jsem si hovezi maso se spenatem a trochou ryze. Je to pro me dnes v pohode a na co si dat pozor?",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert "slabe chveni kolem zaludku" not in payload["answer"]["summary"].lower()
    assert "hovezi maso se spenatem" in payload["answer"]["summary"].lower()

    food_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "food_biomarker_context"
    )
    assert "Hovezi maso se spenatem" in food_section["content"]
    assert any(
        "posledni jidlo" in step.lower() or "hovezi maso se spenatem" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )


def test_food_query_prefers_matching_meal_over_other_recent_meal() -> None:
    older_meal_response = client.post(
        "/meals",
        json={
            "mealType": "lunch",
            "title": "Hovezi maso se spenatem",
            "tags": ["protein", "iron"],
            "occurredAt": "2026-06-12T10:00:00Z",
        },
    )
    assert older_meal_response.status_code == 200

    newer_meal_response = client.post(
        "/meals",
        json={
            "mealType": "dinner",
            "title": "Losos s avokadem",
            "tags": ["omega3", "protein"],
            "occurredAt": "2026-06-12T18:00:00Z",
        },
    )
    assert newer_meal_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Dal jsem si lososa s avokadem. Je to pro me dnes v pohode?",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert "losos s avokadem" in payload["answer"]["summary"].lower()
    assert "hovezi maso se spenatem" not in payload["answer"]["summary"].lower()

    food_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "food_biomarker_context"
    )
    assert "Losos s avokadem" in food_section["content"]
    assert "Hovezi maso se spenatem" not in food_section["content"]


def test_food_query_prefers_structured_meal_over_freeform_sentence_title() -> None:
    structured_meal_response = client.post(
        "/meals",
        json={
            "mealType": "dinner",
            "title": "Losos s avokadem",
            "tags": ["omega3", "protein"],
            "occurredAt": "2026-06-12T18:00:00Z",
        },
    )
    assert structured_meal_response.status_code == 200

    freeform_meal_response = client.post(
        "/meals",
        json={
            "mealType": "breakfast",
            "title": "Dal jsem si lososa s avokadem.",
            "tags": [],
            "occurredAt": "2026-06-12T18:10:00Z",
        },
    )
    assert freeform_meal_response.status_code == 200
    assert freeform_meal_response.json()["title"] == "lososa s avokadem"

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Dal jsem si lososa s avokadem. Je to pro me dnes v pohode?",
        },
    )
    assert response.status_code == 200
    payload = response.json()

    assert "losos s avokadem" in payload["answer"]["summary"].lower()
    assert "dal jsem si lososa s avokadem" not in payload["answer"]["summary"].lower()

    food_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "food_biomarker_context"
    )
    assert "Losos s avokadem" in food_section["content"]
    assert "Dal jsem si lososa s avokadem" not in food_section["content"]


def test_dna_to_biomarker_context_is_used_for_b12_and_homocysteine(tmp_path: Path) -> None:
    genetic_response = client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "DNA profil pro B12 a methylaci.",
            "markers": [
                {
                    "id": "marker-b12",
                    "key": "b12_absorption",
                    "label": "Vitamin B12 / absorpce",
                    "category": "vitamins",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem B12.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["vitamins", "energy", "biomarkers"],
                },
                {
                    "id": "marker-methylation",
                    "key": "methylation_folate",
                    "label": "Folat / methylace",
                    "category": "methylation",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem methylace.",
                    "recommendationStrength": "medium",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["methylation", "biomarkers"],
                },
            ],
        },
    )
    assert genetic_response.status_code == 200

    csv_path = tmp_path / "biomarker-draft-dna.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,vitamin_b12,Vitamin B12,vitamins,220,pmol/l,exact,140,650,,optimal,List 1,60,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,homocysteine,Homocystein,methylation,14.0,umol/l,exact,5,12,,high,List 1,61,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak souvisi moje DNA s B12 a homocysteinem?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    dna_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "dna_biomarker_context"
    )
    assert "Vitamin B12 / absorpce" in dna_section["content"]
    assert "methylace" in dna_section["content"].lower()
    assert "biomarkery maji vyssi vahu" in dna_section["content"]
    assert any("dna vrstvou" in step.lower() or "predispozici" in step.lower() for step in payload["answer"]["nextSteps"])


def test_dna_to_biomarker_context_bridges_biomarker_care_and_meal(tmp_path: Path) -> None:
    genetic_response = client.put(
        "/genetics/profile",
        json={
            "sourceType": "google_doc",
            "sourceLabel": "DNA rozbor - Google dokument",
            "summary": "DNA profil pro lipidy a glukozu.",
            "markers": [
                {
                    "id": "marker-lipid",
                    "key": "lipid_regulation",
                    "label": "Lipidova regulace",
                    "category": "cardiometabolic",
                    "genotype": None,
                    "interpretation": "Vyssi peclivost kolem lipidu.",
                    "recommendationStrength": "high",
                    "confidence": "confirmed",
                    "sourceRef": "DNA rozbor - Google dokument",
                    "relatedDomains": ["cardiometabolic", "lipids", "biomarkers"],
                }
            ],
        },
    )
    assert genetic_response.status_code == 200

    care_response = client.post(
        "/care-recommendations",
        json={
            "title": "Preventivni lipidova kontrola a rezimova zmena",
            "source": "Prakticka doktorka - preventivni prohlidka",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Omezit tuky a uzeniny, zvysit pohyb a hlidat lipidovy trend.",
            "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides", "hdl_c"],
        },
    )
    assert care_response.status_code == 200

    meal_response = client.post(
        "/meals",
        json={
            "mealType": "dinner",
            "title": "Uzeny talir se syrem",
            "tags": ["fat", "processed", "lactose"],
        },
    )
    assert meal_response.status_code == 200

    csv_path = tmp_path / "biomarker-draft-dna-lipids.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,total_cholesterol,Celkovy cholesterol,lipids,6.2,mmol/l,exact,2.9,5.0,,high,List 1,26,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ldl_c,LDL cholesterol,lipids,4.0,mmol/l,exact,1.2,3.0,,high,List 1,27,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak souvisi moje DNA s cholesterolem a co s tim delat?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    dna_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "dna_biomarker_context"
    )
    assert "Lipidova regulace" in dna_section["content"]
    assert "Preventivni lipidova kontrola a rezimova zmena" in dna_section["content"]
    assert "Posledni zapsane jidlo je Uzeny talir se syrem" in dna_section["content"]
    assert any(
        "care vrstvou" in step.lower()
        or "care vrstvu" in step.lower()
        or "poslednim jidlem" in step.lower()
        or "posledním jídlem" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )


def test_care_recommendation_endpoints_and_guidance() -> None:
    created = client.post(
        "/care-recommendations",
        json={
            "title": "Preventivni lipidova kontrola",
            "source": "MUDr. Novakova",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Drzet lipidovy panel pod kontrolou a opakovat preventivni odbery.",
            "reviewFrequency": "rocne",
            "nextDue": "2026-11-30",
            "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides"],
            "notes": "Navazat na preventivni prohlidku.",
        },
    )
    assert created.status_code == 200
    created_payload = created.json()
    assert created_payload["title"] == "Preventivni lipidova kontrola"

    listed = client.get("/care-recommendations")
    assert listed.status_code == 200
    assert any(item["title"] == "Preventivni lipidova kontrola" for item in listed.json())

    briefing = client.get("/assistant/briefing")
    assert briefing.status_code == 200
    briefing_payload = briefing.json()
    assert briefing_payload["activeCareRecommendationCount"] >= 1
    assert any("Preventivni lipidova kontrola" in item for item in briefing_payload["careHighlights"])

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak mam pracovat s doporucenim doktorky a preventivni prohlidkou?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    profile_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "profile_context"
    )
    assert "Preventivni lipidova kontrola" in profile_section["content"]
    assert any(
        "Preventivni lipidova kontrola" in step for step in payload["answer"]["nextSteps"]
    )


def test_care_to_biomarker_context_is_present_for_lipid_focus(tmp_path: Path) -> None:
    created = client.post(
        "/care-recommendations",
        json={
            "title": "Preventivni lipidova kontrola a rezimova zmena",
            "source": "Prakticka doktorka",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Omezit tuky a uzeniny, zvysit pohyb a hlidat lipidovy trend.",
            "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides", "hdl_c"],
        },
    )
    assert created.status_code == 200

    csv_path = tmp_path / "biomarker-draft-care-lipids.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,total_cholesterol,Celkovy cholesterol,lipids,6.2,mmol/l,exact,2.9,5.0,,high,List 1,26,date_approximated_from_year_header",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ldl_c,LDL cholesterol,lipids,4.0,mmol/l,exact,1.2,3.0,,high,List 1,27,date_approximated_from_year_header",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak mam cist cholesterol a co na to rika doporuceni doktorky?",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    care_section = next(
        section
        for section in payload["answer"]["sections"]
        if section["kind"] == "care_biomarker_context"
    )
    assert "Preventivni lipidova kontrola a rezimova zmena" in care_section["content"]
    assert "Celkovy cholesterol" not in care_section["content"] or "LDL" in care_section["content"] or "ldl_c" in care_section["content"].lower()
    assert any(
        "care vrstvu" in step.lower() or "care vrstvou" in step.lower()
        for step in payload["answer"]["nextSteps"]
    )


def test_daily_briefing_adds_practical_lipid_focus_summary(tmp_path: Path) -> None:
    csv_path = tmp_path / "biomarker-draft-lipid-briefing.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2026-01-05,2026-01-05,RLP2026,unknown,total_cholesterol,Celkovy cholesterol,lipids,7.5,mmol/l,exact,2.9,5.0,,high,List 1,26,",
                "2026-01-05,2026-01-05,RLP2026,unknown,ldl_c,LDL cholesterol,lipids,5.11,mmol/l,exact,1.2,3.0,,high,List 1,28,",
                "2026-01-05,2026-01-05,RLP2026,unknown,hdl_c,HDL cholesterol,lipids,1.96,mmol/l,exact,1.0,2.1,,optimal,List 1,27,",
                "2026-01-05,2026-01-05,RLP2026,unknown,triglycerides,Triglyceridy,lipids,1.19,mmol/l,exact,0.0,1.7,,optimal,List 1,29,",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Rozbor krve normalized draft",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    briefing = client.get("/assistant/briefing")
    assert briefing.status_code == 200
    payload = briefing.json()
    assert any("Lipidovy fokus:" in item for item in payload["priorities"])
    assert any("LDL je hlavni fokus" in item for item in payload["priorities"])
    assert "V lipidove vrstve ted plati:" in payload["summary"]


def test_care_recommendations_are_deduped_on_read(monkeypatch, tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    monkeypatch.setattr(settings, "runtime_dir", runtime_dir)
    (runtime_dir / "care-recommendations.json").write_text(
        json.dumps(
            [
                {
                    "id": "care-1",
                    "title": "Preventivni lipidova kontrola",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Drzet lipidovy panel pod kontrolou.",
                    "activeFrom": None,
                    "reviewFrequency": None,
                    "nextDue": "2026-11-30",
                    "relatedMarkers": ["ldl_c", "total_cholesterol"],
                    "notes": None,
                    "status": "active",
                },
                {
                    "id": "care-2",
                    "title": "Preventivni lipidova kontrola",
                    "source": "Prakticka doktorka - preventivni prohlidka",
                    "category": "prevention_lipids",
                    "priority": "high",
                    "recommendation": "Drzet lipidovy panel pod kontrolou.",
                    "activeFrom": "2026-01-01",
                    "reviewFrequency": "rocne",
                    "nextDue": None,
                    "relatedMarkers": ["total_cholesterol", "ldl_c", "hdl_c"],
                    "notes": "Dulezita poznamka.",
                    "status": "active",
                },
            ],
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    response = client.get("/care-recommendations")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "care-2"
    assert "hdl_c" in payload[0]["relatedMarkers"]
    assert payload[0]["notes"] == "Dulezita poznamka."


def test_follow_ups_cleanup_removes_stale_and_remaps_care_duplicates(monkeypatch, tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    monkeypatch.setattr(settings, "runtime_dir", runtime_dir)
    (runtime_dir / "care-recommendations.json").write_text(
        json.dumps(
            [
                {
                    "id": "care-1",
                    "title": "Preventivni cholesterol reminder",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Drzet pozornost na lipidovou oblast.",
                    "activeFrom": None,
                    "reviewFrequency": None,
                    "nextDue": "2026-12-20",
                    "relatedMarkers": ["total_cholesterol", "ldl_c"],
                    "notes": None,
                    "status": "active",
                },
                {
                    "id": "care-2",
                    "title": "Preventivni cholesterol reminder",
                    "source": "Prakticka doktorka - preventivni prohlidka",
                    "category": "prevention_lipids",
                    "priority": "high",
                    "recommendation": "Drzet pozornost na lipidovou oblast.",
                    "activeFrom": None,
                    "reviewFrequency": None,
                    "nextDue": "2026-12-20",
                    "relatedMarkers": ["ldl_c", "total_cholesterol", "triglycerides"],
                    "notes": "Vyssi priorita.",
                    "status": "active",
                },
            ],
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )
    (runtime_dir / "follow-ups.json").write_text(
        json.dumps(
            [
                {
                    "id": "follow-old-meal",
                    "triggerType": "meal",
                    "relatedId": "meal-1",
                    "title": "Follow-up po jidle",
                    "message": "Stary reminder.",
                    "delayLabel": "Za 1-3 hodiny",
                    "suggestedAt": "2026-06-01T08:00:00+00:00",
                    "dueAt": "2026-06-01T10:00:00+00:00",
                    "status": "pending",
                },
                {
                    "id": "follow-care-1",
                    "triggerType": "care_recommendation",
                    "relatedId": "care-1",
                    "title": "Reminder k doporuceni doktorky",
                    "message": "Stejny care reminder.",
                    "delayLabel": "30 dni pred kontrolou",
                    "suggestedAt": "2026-06-10T08:00:00+00:00",
                    "dueAt": "2026-12-01T09:00:00+00:00",
                    "status": "pending",
                },
                {
                    "id": "follow-care-2",
                    "triggerType": "care_recommendation",
                    "relatedId": "care-2",
                    "title": "Reminder k doporuceni doktorky",
                    "message": "Stejny care reminder.",
                    "delayLabel": "30 dni pred kontrolou",
                    "suggestedAt": "2026-06-11T08:00:00+00:00",
                    "dueAt": "2026-12-01T09:00:00+00:00",
                    "status": "pending",
                },
            ],
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    response = client.get("/follow-ups")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["relatedId"] == "care-2"
    assert payload[0]["triggerType"] == "care_recommendation"

    saved_follow_ups = json.loads((runtime_dir / "follow-ups.json").read_text(encoding="utf-8"))
    assert len(saved_follow_ups) == 1


def test_compact_care_recommendations_reduces_lipid_variants(monkeypatch, tmp_path: Path) -> None:
    from app.services.care_recommendation_service import compact_care_recommendations

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    monkeypatch.setattr(settings, "runtime_dir", runtime_dir)
    (runtime_dir / "care-recommendations.json").write_text(
        json.dumps(
            [
                {
                    "id": "care-a",
                    "title": "Preventivni lipidova kontrola",
                    "source": "MUDr. Novakova",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Drzet lipidovy panel pod kontrolou a opakovat preventivni odbery.",
                    "activeFrom": None,
                    "reviewFrequency": "rocne",
                    "nextDue": "2026-11-30",
                    "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides"],
                    "notes": "Navazat na preventivni prohlidku.",
                    "status": "active",
                },
                {
                    "id": "care-b",
                    "title": "Preventivni cholesterol reminder",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Drzet pozornost na lipidovou oblast a navazat dalsi kontrolou.",
                    "activeFrom": None,
                    "reviewFrequency": None,
                    "nextDue": "2026-12-20",
                    "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides"],
                    "notes": None,
                    "status": "active",
                },
                {
                    "id": "care-c",
                    "title": "Lipidova prevence",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Zamereni na zivotni styl a kontrolu lipidove oblasti.",
                    "activeFrom": None,
                    "reviewFrequency": "rocne",
                    "nextDue": "2027-01-15",
                    "relatedMarkers": ["total_cholesterol", "ldl_c"],
                    "notes": None,
                    "status": "active",
                },
                {
                    "id": "care-d",
                    "title": "Preventivni lipidova kontrola a rezim",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Omezit tuky, uzeniny a drzet vyssi pohyb.",
                    "activeFrom": None,
                    "reviewFrequency": "rocne",
                    "nextDue": "2027-01-15",
                    "relatedMarkers": ["total_cholesterol", "ldl_c"],
                    "notes": "Skutecne doporuceni.",
                    "status": "active",
                },
                {
                    "id": "care-e",
                    "title": "Preventivni lipidova kontrola a rezimova zmena",
                    "source": "Prakticka doktorka - preventivni prohlidka",
                    "category": "prevention_lipids",
                    "priority": "high",
                    "recommendation": "Vyssi cholesterol brat vazne, omezit tuky a uzene, zvysit pohyb a celkove se zamerit na zdravy zivotni styl. Leky byly puvodne navrzeny, ale zatim byla domluvena rezimova cesta.",
                    "activeFrom": "2026-01-01",
                    "reviewFrequency": "prubezne + pri dalsi kontrole / odberu",
                    "nextDue": None,
                    "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides", "hdl_c"],
                    "notes": "Zaznam z preventivni prohlidky. Zvyseny cholesterol byl doktorkou povazovan za opravdu nebezpecny.",
                    "status": "active",
                },
                {
                    "id": "care-f",
                    "title": "Preventivni lipidova kontrola a rezimova zmena",
                    "source": "Prakticka doktorka",
                    "category": "prevention",
                    "priority": "high",
                    "recommendation": "Omezit tuky a uzeniny, zvysit pohyb a hlidat lipidovy trend.",
                    "activeFrom": None,
                    "reviewFrequency": None,
                    "nextDue": None,
                    "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides", "hdl_c"],
                    "notes": None,
                    "status": "active",
                },
            ],
            ensure_ascii=True,
            indent=2,
        ),
        encoding="utf-8",
    )

    removed = compact_care_recommendations()
    payload = client.get("/care-recommendations").json()
    titles = [item["title"] for item in payload]

    assert removed == 2
    assert len(payload) == 4
    assert "Preventivni lipidova kontrola a rezimova zmena" in titles
    assert "Lipidova prevence a rezim" in titles
    assert "Preventivni lipidova kontrola" in titles
    assert "Preventivni cholesterol reminder" in titles


def test_care_recommendation_follow_up_creation_and_dedup() -> None:
    created = client.post(
        "/care-recommendations",
        json={
            "title": "Preventivni cholesterol reminder",
            "source": "Prakticka doktorka",
            "category": "prevention",
            "priority": "high",
            "recommendation": "Drzet pozornost na lipidovou oblast a navazat dalsi kontrolou.",
            "nextDue": "2026-12-20",
            "relatedMarkers": ["total_cholesterol", "ldl_c", "triglycerides"],
        },
    )
    assert created.status_code == 200
    recommendation = created.json()

    first_follow_up = client.post(f"/care-recommendations/{recommendation['id']}/follow-up")
    second_follow_up = client.post(f"/care-recommendations/{recommendation['id']}/follow-up")

    assert first_follow_up.status_code == 200
    assert second_follow_up.status_code == 200
    first_payload = first_follow_up.json()
    second_payload = second_follow_up.json()
    assert first_payload["triggerType"] == "care_recommendation"
    assert first_payload["relatedId"] == recommendation["id"]
    assert "total_cholesterol" in first_payload["message"]
    assert first_payload["id"] == second_payload["id"]


def test_routine_layer_is_exposed_and_used_in_guidance() -> None:
    routines = client.get("/routines")
    movement = client.get("/movement-blocks")
    assert routines.status_code == 200
    assert movement.status_code == 200
    assert len(routines.json()) >= 1
    assert len(movement.json()) >= 1
    assert len(movement.json()[0]["minimumVariant"]) >= 1
    assert len(movement.json()[0]["fullVariant"]) >= 1
    assert len(movement.json()[0]["sequenceSteps"]) >= 1
    strength_block = next(item for item in movement.json() if item["id"] == "movement-strength")
    regulation_block = next(item for item in movement.json() if item["id"] == "movement-regulation")
    bike_block = next(item for item in movement.json() if item["id"] == "movement-bike")
    barefoot_block = next(item for item in movement.json() if item["id"] == "movement-barefoot")
    assert any("drep u zdi" in step.lower() for step in strength_block["minimumVariant"])
    assert any("hlubok" in step.lower() for step in strength_block["fullVariant"])
    assert any("dech" in step.lower() for step in regulation_block["minimumVariant"])
    assert any("pasivni" in step.lower() and "vis" in step.lower() for step in regulation_block["fullVariant"])
    assert any("klidna jizda" in step.lower() for step in bike_block["minimumVariant"])
    assert any("vykonoveho" in step.lower() or "souteziveho" in step.lower() for step in bike_block["fullVariant"])
    assert any("naboso" in step.lower() for step in barefoot_block["minimumVariant"])
    assert any("chodidel" in step.lower() or "podlozk" in step.lower() for step in barefoot_block["fullVariant"])

    briefing = client.get("/assistant/briefing")
    assert briefing.status_code == 200
    briefing_payload = briefing.json()
    assert len(briefing_payload["routineHighlights"]) >= 1
    assert len(briefing_payload["movementHighlights"]) >= 1

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak mam dnes pracovat s ranní rutinou a pohybem?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    routine_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "routine_basis"
    )
    assert "Ranni longevity rutina" in routine_section["content"]
    assert "pohybova vrstva" in routine_section["content"].lower()
    assert any("ranni longevity rutina" in step.lower() for step in payload["answer"]["nextSteps"])


def test_movement_constraints_shift_guidance_to_protective_mode() -> None:
    client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 3,
            "stress": 8,
            "sleepQuality": 4,
            "notes": "Zada jsou pretizena po vcerejsku",
        },
    )
    client.post(
        "/health-signals",
        json={
            "category": "movement",
            "title": "Pretizena zada",
            "severity": "medium",
            "notes": "Nechci hluboke drepy.",
        },
    )

    briefing = client.get("/assistant/briefing")
    assert briefing.status_code == 200
    briefing_payload = briefing.json()
    assert any("silovy blok" in item.lower() for item in briefing_payload["movementGuardrails"])
    assert any("hluboke drepy" in item.lower() for item in briefing_payload["movementGuardrails"])

    bootstrap = client.get("/assistant/bootstrap").json()
    conversation_id = bootstrap["conversation"]["id"]
    response = client.post(
        "/chat/respond",
        json={
            "conversationId": conversation_id,
            "message": "Jak mam dnes pracovat s pohybem a cviky?",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    routine_section = next(
        section for section in payload["answer"]["sections"] if section["kind"] == "routine_basis"
    )
    assert "protective" in routine_section["content"].lower() or "minimum" in routine_section["content"].lower()
    assert any("nechte stranou" in step.lower() for step in payload["answer"]["nextSteps"])


def test_create_meal_and_health_signal() -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "breakfast",
            "title": "Jogurt s ovocem",
            "notes": "test meal",
            "tags": ["lactose", "protein"],
        },
    )
    assert meal_response.status_code == 200
    assert meal_response.json()["title"] == "Jogurt s ovocem"

    signal_response = client.post(
        "/health-signals",
        json={
            "category": "digestion",
            "title": "Nadymani po snidani",
            "severity": "medium",
            "notes": "test signal",
        },
    )
    assert signal_response.status_code == 200
    assert signal_response.json()["severity"] == "medium"

    meals = client.get("/meals")
    signals = client.get("/health-signals")
    assert meals.status_code == 200
    assert signals.status_code == 200
    assert len(meals.json()) >= 1
    assert len(signals.json()) >= 1


def test_delete_meal_and_health_signal() -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "dinner",
            "title": "Losos s avokadem",
            "notes": "delete meal",
            "tags": ["omega3"],
        },
    )
    signal_response = client.post(
        "/health-signals",
        json={
            "category": "energy",
            "title": "Unava po veceri",
            "severity": "low",
            "notes": "delete signal",
        },
    )

    meal_id = meal_response.json()["id"]
    signal_id = signal_response.json()["id"]

    delete_meal_response = client.delete(f"/meals/{meal_id}")
    delete_signal_response = client.delete(f"/health-signals/{signal_id}")

    assert delete_meal_response.status_code == 200
    assert delete_signal_response.status_code == 200
    assert delete_meal_response.json()["id"] == meal_id
    assert delete_signal_response.json()["id"] == signal_id

    meals = client.get("/meals")
    signals = client.get("/health-signals")

    assert all(meal["id"] != meal_id for meal in meals.json())
    assert all(signal["id"] != signal_id for signal in signals.json())


def test_follow_up_suggestions_are_generated() -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "snack",
            "title": "Jogurt",
            "tags": ["lactose"],
        },
    )
    signal_response = client.post(
        "/health-signals",
        json={
            "category": "digestion",
            "title": "Nadymani",
            "severity": "high",
        },
    )

    meal_follow_up = client.post(f"/meals/{meal_response.json()['id']}/follow-up")
    signal_follow_up = client.post(
        f"/health-signals/{signal_response.json()['id']}/follow-up"
    )

    assert meal_follow_up.status_code == 200
    assert signal_follow_up.status_code == 200
    assert meal_follow_up.json()["triggerType"] == "meal"
    assert signal_follow_up.json()["triggerType"] == "health_signal"
    assert "laktózy" in meal_follow_up.json()["message"] or "laktosy" in meal_follow_up.json()["message"]
    assert meal_follow_up.json()["status"] == "pending"
    assert meal_follow_up.json()["dueAt"]


def test_due_and_complete_follow_up() -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "snack",
            "title": "Kefir",
            "tags": ["lactose"],
        },
    )
    follow_up = client.post(f"/meals/{meal_response.json()['id']}/follow-up").json()

    due_today = client.get("/follow-ups/today")
    assert due_today.status_code == 200
    assert any(item["id"] == follow_up["id"] for item in due_today.json())

    completed = client.post(f"/follow-ups/{follow_up['id']}/complete")
    assert completed.status_code == 200
    assert completed.json()["status"] == "done"


def test_daily_check_in_and_follow_up() -> None:
    check_in_response = client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 6,
            "stress": 4,
            "sleepQuality": 7,
            "notes": "Klidny start dne",
        },
    )
    assert check_in_response.status_code == 200
    assert check_in_response.json()["checkInType"] == "morning"

    follow_up_response = client.post(
        f"/daily-check-ins/{check_in_response.json()['id']}/follow-up"
    )
    assert follow_up_response.status_code == 200
    assert follow_up_response.json()["triggerType"] == "daily_check_in"
