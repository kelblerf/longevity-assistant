from __future__ import annotations

from app.models import (
    AnswerSource,
    EvidenceKnowledgeHit,
    SourceScopeSelection,
    UzbKnowledgeHit,
)


def _contains_any(message: str, keywords: list[str]) -> bool:
    return any(keyword in message for keyword in keywords)


FOOD_MESSAGE_KEYWORDS = [
    "lakto",
    "mlec",
    "jogurt",
    "syr",
    "jidlo",
    "strava",
    "hovezi",
    "kure",
    "kurci",
    "losos",
    "vejce",
    "ryze",
    "brambor",
    "spenat",
    "avokad",
    "oves",
    "banan",
    "ovoce",
    "zelen",
    "maso",
    "protein",
]


def resolve_scope(message: str) -> SourceScopeSelection:
    normalized = message.lower()
    groups = ["profile"]
    reason_parts: list[str] = []
    mode = "core_plus_domain"

    if _contains_any(normalized, ["dech", "stres", "regener", "rytmus", "span", "energie"]):
        groups.extend(["app_health_data", "ubz_framework", "notebooklm_research"])
        reason_parts.append("Dotaz miri na rytmus, regulaci a zdravotni kontext.")

    if _contains_any(normalized, FOOD_MESSAGE_KEYWORDS):
        groups.extend(["app_genetics_data", "app_nutrition_data", "notebooklm_research"])
        reason_parts.append("Dotaz zahrnuje vyzivu a mozny DNA konflikt.")

    if _contains_any(normalized, ["biomarker", "krev", "labor", "vitamin", "gluko", "cholesterol"]):
        groups.extend(["app_health_data", "notebooklm_research", "web_evidence"])
        mode = "full_research"
        reason_parts.append("Dotaz vyzaduje silnejsi evidence vrstvu.")

    if _contains_any(normalized, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]):
        groups.extend(["app_health_data", "notebooklm_research"])
        reason_parts.append("Dotaz miri na odbornou nebo preventivni vrstvu pece.")

    if _contains_any(normalized, ["notion", "druhy mozek", "druhy", "temata", "ubz"]):
        groups.extend(["notion_structured", "notion_extended"])
        reason_parts.append("Dotaz miri do znalostni vrstvy Notion.")

    if _contains_any(normalized, ["onenote", "poznam", "reflex", "denik"]):
        groups.append("onenote_reflection")
        reason_parts.append("Dotaz muze vyuzit reflexivni osobni zapisy.")

    if _contains_any(normalized, ["soubor", "disk", "hdd", "pc", "adresar"]):
        groups.extend(["local_files", "external_drive_files"])
        mode = "core_plus_extended"
        reason_parts.append("Dotaz muze potrebovat lokalni soubory nebo externi disk.")

    if _contains_any(normalized, ["internet", "web", "studie", "vyzkum", "research"]):
        groups.extend(["notebooklm_research", "web_evidence"])
        mode = "full_research"
        reason_parts.append("Dotaz chce rozsireny research scope.")

    if len(groups) == 1:
        groups.extend(["app_health_data", "ubz_framework"])
        reason_parts.append("Vychozi rezim drzi jadro a behaviorni vrstvu.")

    deduped_groups = list(dict.fromkeys(groups))
    reason = " ".join(reason_parts) if reason_parts else "Vychozi jadro + chytre rozsireni."
    return SourceScopeSelection(mode=mode, groups=deduped_groups, locked=False, reason=reason)


def default_sources_for_scope(
    scope: SourceScopeSelection,
    ubz_hits: list[UzbKnowledgeHit] | None = None,
    evidence_hits: list[EvidenceKnowledgeHit] | None = None,
) -> list[AnswerSource]:
    sources: list[AnswerSource] = []

    if "profile" in scope.groups:
        sources.append(
            AnswerSource(
                label="Core profile",
                type="profile",
                reference=None,
                authorityTier="core_truth",
            )
        )
    if "app_health_data" in scope.groups:
        sources.append(
            AnswerSource(
                label="Confirmed biomarker trends",
                type="app_health_data",
                reference="Runtime biomarker reports and trends",
                authorityTier="core_truth",
            )
        )
    if "ubz_framework" in scope.groups:
        sources.append(
            AnswerSource(
                label="UBZ / Pusty a dech v souvislostech",
                type="ubz_framework",
                reference="Digitalni druhy mozek / Temata / UBZ Energo evoluce 2025",
                authorityTier="ubz_primary",
            )
        )
        for hit in ubz_hits or []:
            sources.append(
                AnswerSource(
                    label=hit.title,
                    type="ubz_framework",
                    reference=hit.notion_path,
                    authorityTier=hit.authority_tier,
                )
            )
    if "notebooklm_research" in scope.groups:
        sources.append(
            AnswerSource(
                label="NotebookLM - Medical Fundation",
                type="notebooklm_research",
                reference="Notion",
                authorityTier="evidence_primary",
            )
        )
        for hit in evidence_hits or []:
            sources.append(
                AnswerSource(
                    label=hit.title,
                    type="notebooklm_research",
                    reference=hit.notion_path,
                    authorityTier=hit.authority_tier,
                )
            )
    if "web_evidence" in scope.groups:
        sources.append(
            AnswerSource(
                label="Web evidence",
                type="web_evidence",
                reference="External research scope",
                authorityTier="evidence_supporting",
            )
        )
    if "notion_extended" in scope.groups:
        sources.append(
            AnswerSource(
                label="Extended Notion knowledge",
                type="notion_extended",
                reference="Digitalni druhy mozek",
                authorityTier="knowledge_supporting",
            )
        )
    if "local_files" in scope.groups:
        sources.append(
            AnswerSource(
                label="Local files",
                type="local_files",
                reference="PC and project folders",
                authorityTier="local_supporting",
            )
        )
    if "external_drive_files" in scope.groups:
        sources.append(
            AnswerSource(
                label="External drive files",
                type="external_drive_files",
                reference="Attached HDD",
                authorityTier="external_supporting",
            )
        )

    deduped: list[AnswerSource] = []
    seen: set[tuple[str, str, str | None]] = set()
    for source in sources:
        key = (source.type, source.label, source.reference)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(source)

    return deduped
