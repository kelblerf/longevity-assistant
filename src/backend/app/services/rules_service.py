from app.models import AssistantRules
from app.services.storage_service import read_json, write_json


def _seed_rules() -> AssistantRules:
    return AssistantRules(
        profileId="default-user",
        assistantIdentity="osobni duverny radce",
        voiceMode="text_first",
        sourceScopeDefault="core_plus_domain",
        ubzPriority="primary_behavioral_layer",
        notebookLmRole="evidence_research_layer",
        dnaPolicy="recommendation_only",
        warningTone="calm_explanatory",
    )


def get_assistant_rules() -> AssistantRules:
    payload = read_json("assistant-rules.json", default=None)
    if payload is None:
        rules = _seed_rules()
        write_json("assistant-rules.json", rules.model_dump(by_alias=True))
        return rules
    return AssistantRules.model_validate(payload)
