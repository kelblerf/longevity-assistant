import os
from pathlib import Path

from pydantic import BaseModel


def _load_project_env() -> None:
    env_path = Path(__file__).resolve().parents[3] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_project_env()


class AppConfig(BaseModel):
    app_name: str = "Longevity-assistant API"
    environment: str = "development"
    profile_mode: str = "hybrid"
    project_root: Path = Path(__file__).resolve().parents[3]
    runtime_dir: Path = Path(__file__).resolve().parents[3] / "data" / "runtime"
    knowledge_dir: Path = Path(__file__).resolve().parents[3] / "data" / "knowledge"
    notion_outbox_dir: Path = Path(__file__).resolve().parents[3] / "integrations" / "notion" / "outbox"
    notion_api_token: str | None = os.getenv("NOTION_API_TOKEN")
    notion_version: str = os.getenv("NOTION_VERSION", "2022-06-28")
    notion_daily_checkins_database_id: str | None = os.getenv("NOTION_DAILY_CHECKINS_DATABASE_ID")
    notion_health_signals_database_id: str | None = os.getenv("NOTION_HEALTH_SIGNALS_DATABASE_ID")
    notion_follow_ups_database_id: str | None = os.getenv("NOTION_FOLLOW_UPS_DATABASE_ID")
    notion_daily_summaries_database_id: str | None = os.getenv("NOTION_DAILY_SUMMARIES_DATABASE_ID")
    notion_care_recommendations_database_id: str | None = os.getenv("NOTION_CARE_RECOMMENDATIONS_DATABASE_ID")
    notion_biomarker_reports_database_id: str | None = os.getenv("NOTION_BIOMARKER_REPORTS_DATABASE_ID")
    notion_biomarker_trends_database_id: str | None = os.getenv("NOTION_BIOMARKER_TRENDS_DATABASE_ID")
    notion_genetic_profile_database_id: str | None = os.getenv("NOTION_GENETIC_PROFILE_DATABASE_ID")
    notion_genetic_markers_database_id: str | None = os.getenv("NOTION_GENETIC_MARKERS_DATABASE_ID")


settings = AppConfig()
