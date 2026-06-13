from app.models import UserProfile
from app.services.storage_service import read_json, write_json


def _seed_profile() -> UserProfile:
    return UserProfile(
        id="default-user",
        displayName="Frantisek",
        ageGroup="60+",
        healthGoals=[
            "stabilni energie",
            "lepsi rytmus dne",
            "regenerace a dech",
        ],
        constraints=[
            "DNA je doporucujici vrstva, ne definitivni verdict",
        ],
        preferences=[
            "klidny a vysvetlujici ton",
            "UBZ jako hlavni behavioralni ramec",
        ],
        trustedSources=[
            "Blood Biomarkers - Source of Truth",
            "NotebookLM - Medical Fundation",
            "UBZ Energo evoluce 2025",
        ],
        guidanceStyle="osobni duverny radce",
        dailyRhythm="asistent dne",
        dnaUsagePolicy="contextual_warning_engine",
    )


def get_default_profile() -> UserProfile:
    payload = read_json("profile.json", default=None)
    if payload is None:
        profile = _seed_profile()
        write_json("profile.json", profile.model_dump(by_alias=True))
        return profile
    return UserProfile.model_validate(payload)
