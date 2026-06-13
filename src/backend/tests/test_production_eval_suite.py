from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)


@pytest.fixture()
def isolated_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    monkeypatch.setattr(settings, "runtime_dir", runtime_dir)
    return runtime_dir


def _conversation_id() -> str:
    bootstrap = client.get("/assistant/bootstrap")
    assert bootstrap.status_code == 200
    return bootstrap.json()["conversation"]["id"]


def test_eval_meal_to_chat_answer(isolated_runtime: Path, tmp_path: Path) -> None:
    meal_response = client.post(
        "/meals",
        json={
            "mealType": "lunch",
            "title": "Hovezi maso se spenatem",
            "tags": ["protein", "iron"],
        },
    )
    assert meal_response.status_code == 200

    csv_path = tmp_path / "eval-biomarkers.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,vitamin_b12,Vitamin B12,vitamins,220,pmol/l,exact,140,650,,optimal,List 1,60,",
                "2022-01-01,2022-01-01,RLP 2022,unknown,homocysteine,Homocystein,methylation,14.0,umol/l,exact,5,12,,high,List 1,61,",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ferritin,Ferritin,iron,35,ug/l,exact,30,400,,optimal,List 1,62,",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Eval biomarker import",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": _conversation_id(),
            "message": "Jak souvisi moje jidlo s B12, homocysteinem a ferritinem?",
        },
    )
    assert response.status_code == 200
    payload = response.json()["answer"]

    section_kinds = [section["kind"] for section in payload["sections"]]
    assert "food_biomarker_context" in section_kinds
    assert "evidence_basis" in section_kinds
    assert "model_interpretation" in section_kinds
    assert "app_nutrition_data" in payload["selectedScope"]["groups"]
    assert any(source["type"] == "app_health_data" for source in payload["sources"])
    assert any(
        step
        for step in payload["nextSteps"]
        if "jidlo" in step.lower() or "b12" in step.lower() or "biomarker" in step.lower()
    )


def test_eval_signal_to_chat_answer(isolated_runtime: Path) -> None:
    signal_response = client.post(
        "/health-signals",
        json={
            "category": "stress",
            "title": "Napeti v tele",
            "severity": "medium",
            "notes": "Po narocnem dni.",
        },
    )
    assert signal_response.status_code == 200

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": _conversation_id(),
            "message": "Citim dnes napeti v tele. Co je nejpraktictejsi dalsi krok?",
        },
    )
    assert response.status_code == 200
    payload = response.json()["answer"]

    section_kinds = [section["kind"] for section in payload["sections"]]
    assert "ubz_basis" in section_kinds
    assert "evidence_basis" in section_kinds
    assert "model_interpretation" in section_kinds
    assert any(source["type"] == "ubz_framework" for source in payload["sources"])
    assert any(
        step
        for step in payload["nextSteps"]
        if "signal" in step.lower() or "check-in" in step.lower() or "clovekologie" in step.lower()
    )


def test_eval_check_in_to_recommendation(isolated_runtime: Path) -> None:
    check_in_response = client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 3,
            "stress": 8,
            "sleepQuality": 4,
            "notes": "Nizka energie a vysoky stres.",
        },
    )
    assert check_in_response.status_code == 200

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": _conversation_id(),
            "message": "Udelal jsem ranni check-in s nizsi energii a vyssim stresem. Co je pro me dnes nejpraktictejsi dalsi krok?",
        },
    )
    assert response.status_code == 200
    payload = response.json()["answer"]

    assert "ubz_framework" in payload["selectedScope"]["groups"]
    section_kinds = [section["kind"] for section in payload["sections"]]
    assert "routine_basis" in section_kinds
    assert "model_interpretation" in section_kinds
    assert any(step for step in payload["nextSteps"] if "rezim" in step.lower() or "dech" in step.lower())


def test_eval_sync_failure_exposes_audit_state(isolated_runtime: Path) -> None:
    created = client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 6,
            "stress": 4,
            "sleepQuality": 7,
        },
    )
    assert created.status_code == 200

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
        assert payload["deliveryState"] == "failed"
        assert payload["attemptedCount"] >= 1
        assert payload["errorMessage"] == "Notion API unavailable"

        status = client.get("/integrations/notion/status")
        assert status.status_code == 200
        source_state = status.json()["sourceStates"]["daily_check_ins"]
        assert source_state["deliveryState"] == "failed"
        assert source_state["attemptCount"] >= 1
        assert source_state["lastError"] == "Notion API unavailable"
    finally:
        settings.notion_api_token = previous_token
        settings.notion_daily_checkins_database_id = previous_db


def test_eval_daily_briefing_protective_mode(isolated_runtime: Path) -> None:
    check_in_response = client.post(
        "/daily-check-ins",
        json={
            "checkInType": "morning",
            "energy": 4,
            "stress": 7,
            "sleepQuality": 5,
            "notes": "Eval briefing protective mode.",
        },
    )
    assert check_in_response.status_code == 200

    signal_response = client.post(
        "/health-signals",
        json={
            "category": "stress",
            "title": "Napeti v tele",
            "severity": "medium",
            "notes": "Eval signal for briefing.",
        },
    )
    assert signal_response.status_code == 200

    briefing = client.get("/assistant/briefing")
    assert briefing.status_code == 200
    payload = briefing.json()

    assert payload["headline"] == "Ranní briefing"
    assert any("lehčí režim" in item or "lehci rezim" in item for item in payload["priorities"])
    assert any("protective" in item for item in payload["priorities"]) or "protective" in payload["summary"]
    assert any("Napeti v tele" in item for item in payload["priorities"]) or "Napeti v tele" in payload["summary"]
    assert any("dech" in item.lower() for item in payload["movementGuardrails"])


def test_eval_biomarker_interpretation_b12_homocysteine(isolated_runtime: Path, tmp_path: Path) -> None:
    csv_path = tmp_path / "eval-biomarker-interpretation.csv"
    csv_path.write_text(
        "\n".join(
            [
                "report_date,reported_date,lab_name,fasting_state,marker_key,marker_label,category,value,unit,comparator,reference_low,reference_high,reference_text,status,source_sheet,source_row,notes",
                "2022-01-01,2022-01-01,RLP 2022,unknown,vitamin_b12,Vitamin B12,vitamins,220,pmol/l,exact,140,650,,optimal,List 1,60,",
                "2022-01-01,2022-01-01,RLP 2022,unknown,homocysteine,Homocystein,methylation,14.0,umol/l,exact,5,12,,high,List 1,61,",
                "2022-01-01,2022-01-01,RLP 2022,unknown,ferritin,Ferritin,iron,35,ug/l,exact,30,400,,optimal,List 1,62,",
            ]
        ),
        encoding="utf-8",
    )
    draft_response = client.post(
        "/biomarkers/import-draft",
        json={
            "sourceType": "google_sheets_normalized_csv",
            "sourceLabel": "Eval biomarker interpretation import",
            "filePath": str(csv_path),
        },
    )
    assert draft_response.status_code == 200
    confirm_response = client.post("/biomarkers/confirm-import", json={})
    assert confirm_response.status_code == 200

    response = client.post(
        "/chat/respond",
        json={
            "conversationId": _conversation_id(),
            "message": "Co dnes cist v biomarkerech kolem B12 a homocysteinu?",
        },
    )
    assert response.status_code == 200
    payload = response.json()["answer"]

    assert payload["selectedScope"]["mode"] == "full_research"
    assert "app_health_data" in payload["selectedScope"]["groups"]
    assert "notebooklm_research" in payload["selectedScope"]["groups"]
    section_kinds = [section["kind"] for section in payload["sections"]]
    assert "biomarker_insight" in section_kinds
    assert "evidence_basis" in section_kinds
    assert "model_interpretation" in section_kinds

    biomarker_section = next(
        section for section in payload["sections"] if section["kind"] == "biomarker_insight"
    )
    evidence_section = next(
        section for section in payload["sections"] if section["kind"] == "evidence_basis"
    )
    assert "Vitamin B12" in biomarker_section["content"]
    assert "Homocystein" in biomarker_section["content"]
    assert "Blood Biomarkers - Source of Truth" in evidence_section["content"]
    assert any(
        step for step in payload["nextSteps"] if "Vitamin B12" in step or "Homocystein" in step
    )
