from __future__ import annotations

from datetime import datetime, timezone

from app.models import AssistantAnswer, DailyBriefing, SourceScopeSelection
from app.services.biomarker_insight_service import build_biomarker_insight
from app.services.care_biomarker_service import build_care_biomarker_context
from app.services.biomarker_confirm_service import (
    list_biomarker_observations,
    list_biomarker_trends,
)
from app.services.biomarker_priority_service import priority_marker_keys
from app.services.care_recommendation_service import (
    care_recommendation_highlights,
    list_active_care_recommendations,
)
from app.services.daily_check_in_service import list_daily_check_ins
from app.services.dna_biomarker_service import build_dna_biomarker_context
from app.services.evidence_knowledge_service import build_evidence_context
from app.services.follow_up_service import list_due_follow_ups, list_today_follow_ups
from app.services.food_biomarker_service import build_food_biomarker_context
from app.services.genetics_service import get_genetic_profile
from app.services.health_signal_service import list_health_signals
from app.services.meal_service import list_meal_entries
from app.services.routine_service import (
    list_movement_blocks,
    list_routines,
    movement_highlights,
    recommend_movement_plan,
    routine_highlights,
)
from app.services.source_scope_service import default_sources_for_scope, resolve_scope
from app.services.text_normalization_service import normalize_text
from app.services.ubz_knowledge_service import build_ubz_context


def _normalize(text: str) -> str:
    return normalize_text(text)


def _contains_any(message: str, keywords: list[str]) -> bool:
    normalized = _normalize(message)
    return any(keyword in normalized for keyword in keywords)


FOOD_MESSAGE_KEYWORDS = [
    "lakto",
    "mlec",
    "jogurt",
    "syr",
    "kefir",
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

DAIRY_MESSAGE_KEYWORDS = [
    "lakto",
    "mlec",
    "jogurt",
    "syr",
    "kefir",
]


def _is_food_message(message: str) -> bool:
    return _contains_any(message, FOOD_MESSAGE_KEYWORDS)


def _is_dairy_message(message: str) -> bool:
    return _contains_any(message, DAIRY_MESSAGE_KEYWORDS)


def _clean_meal_title_text(title: str) -> str:
    cleaned = title.strip().strip(".!?")
    lowered = _normalize(cleaned)
    prefixes = [
        "dal jsem si ",
        "dala jsem si ",
        "snedl jsem ",
        "snezdl jsem ",
        "jedl jsem ",
        "jedla jsem ",
        "mel jsem ",
        "mela jsem ",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip().strip(".!?")
            break
    return cleaned or title.strip()


def _meal_title_text(meal: object | None) -> str:
    if meal is None:
        return ""
    return _clean_meal_title_text(str(getattr(meal, "title", "") or ""))


def _is_freeform_meal_title(meal: object) -> bool:
    title = _normalize(str(getattr(meal, "title", "")))
    return any(
        title.startswith(prefix)
        for prefix in [
            "dal jsem si ",
            "dala jsem si ",
            "snedl jsem ",
            "snezdl jsem ",
            "jedl jsem ",
            "jedla jsem ",
        ]
    )


def _meal_matching_terms(meal: object) -> list[str]:
    title = _normalize(_meal_title_text(meal))
    notes = _normalize(str(getattr(meal, "notes", "") or ""))
    tags = " ".join(_normalize(tag) for tag in getattr(meal, "tags", []))
    source_text = " ".join(part for part in [title, notes, tags] if part).strip()
    if not source_text:
        return []
    stopwords = {
        "jsem",
        "jídlo",
        "jidlo",
        "dnes",
        "trochou",
        "trochu",
        "nebo",
        "a",
        "s",
        "se",
        "si",
        "na",
        "je",
        "to",
        "pro",
        "me",
    }
    return [
        term
        for term in dict.fromkeys(source_text.split())
        if len(term) >= 4 and term not in stopwords
    ]


def _resolve_meal_for_message(message: str, meals: list[object]) -> object | None:
    if not meals:
        return None
    if not _is_food_message(message):
        return meals[0]

    normalized_message = _normalize(message)
    best_meal = meals[0]
    best_score = -1
    for meal in meals:
        title = _normalize(_meal_title_text(meal))
        score = 0
        if title and title in normalized_message:
            score += 1
        score += sum(1 for term in _meal_matching_terms(meal) if term in normalized_message)
        if getattr(meal, "tags", []):
            score += 1
        if _is_freeform_meal_title(meal):
            score -= 5
        if score > best_score or (
            score == best_score
            and len(getattr(meal, "tags", [])) > len(getattr(best_meal, "tags", []))
        ) or (
            score == best_score
            and _is_freeform_meal_title(best_meal)
            and not _is_freeform_meal_title(meal)
        ):
            best_meal = meal
            best_score = score
    return best_meal


def _is_biomarker_message(message: str) -> bool:
    return _contains_any(
        message,
        [
            "biomarker",
            "krev",
            "labor",
            "vitamin",
            "gluko",
            "cholesterol",
            "b12",
            "homocyst",
            "folat",
            "methyl",
            "ferritin",
            "zelezo",
            "iron",
            "crp",
            "tsh",
            "ft3",
            "ft4",
            "lipid",
        ],
    )


def _latest_flagged_biomarkers(observations: list) -> list:
    latest_by_marker: dict[str, object] = {}
    for observation in observations:
        current = latest_by_marker.get(observation.marker_key)
        if current is None or observation.observed_at >= current.observed_at:
            latest_by_marker[observation.marker_key] = observation

    flagged = [
        observation
        for observation in latest_by_marker.values()
        if observation.status in {"high", "low", "out_of_range"}
    ]
    return sorted(flagged, key=lambda item: (item.observed_at, item.marker_label), reverse=True)


def _latest_observations_by_marker(observations: list) -> dict[str, object]:
    latest_by_marker: dict[str, object] = {}
    for observation in observations:
        current = latest_by_marker.get(observation.marker_key)
        if current is None or observation.observed_at >= current.observed_at:
            latest_by_marker[observation.marker_key] = observation
    return latest_by_marker


def _format_observation_value(observation: object | None) -> str | None:
    if observation is None or observation.value is None:
        return None
    return f"{observation.value} {observation.unit or ''}".strip()


def _build_lipid_focus_summary(latest_by_marker: dict[str, object]) -> str | None:
    ldl = latest_by_marker.get("ldl_c")
    total = latest_by_marker.get("total_cholesterol")
    hdl = latest_by_marker.get("hdl_c")
    triglycerides = latest_by_marker.get("triglycerides")

    if not any([ldl, total, hdl, triglycerides]):
        return None

    high_priority: list[str] = []
    if ldl and ldl.status in {"high", "out_of_range"}:
        value = _format_observation_value(ldl)
        high_priority.append(
            f"LDL je hlavni fokus ({value})" if value else "LDL je hlavni fokus"
        )
    if total and total.status in {"high", "out_of_range"}:
        value = _format_observation_value(total)
        high_priority.append(
            f"celkovy cholesterol to potvrzuje ({value})"
            if value
            else "celkovy cholesterol to potvrzuje"
        )

    context_parts: list[str] = []
    if triglycerides:
        tri_value = _format_observation_value(triglycerides)
        if triglycerides.status in {"high", "out_of_range"}:
            context_parts.append(
                f"triglyceridy jsou take vyssi ({tri_value})" if tri_value else "triglyceridy jsou take vyssi"
            )
        elif tri_value:
            context_parts.append(f"triglyceridy jsou zatim spis kontext ({tri_value})")
    if hdl:
        hdl_value = _format_observation_value(hdl)
        if hdl.status in {"low", "out_of_range"}:
            context_parts.append(
                f"HDL si zada pozornost ({hdl_value})" if hdl_value else "HDL si zada pozornost"
            )
        elif hdl_value:
            context_parts.append(f"HDL je spis doplnujici kontext ({hdl_value})")

    if high_priority:
        summary = ", ".join(high_priority)
        if context_parts:
            summary += "; " + ", ".join(context_parts[:2])
        return summary + "."

    if context_parts:
        return (
            "Lipidový panel je vhodné číst pohromadě: "
            + ", ".join(context_parts[:2])
            + "."
        )

    return "Lipidový panel je načtený a má smysl ho číst pohromadě, ne podle jednoho čísla."


def _recent_operational_context(message: str) -> dict:
    meals = list_meal_entries()
    selected_meal = _resolve_meal_for_message(message, meals)
    signals = list_health_signals()
    check_ins = list_daily_check_ins()
    due_today = list_today_follow_ups()
    due_now = list_due_follow_ups()
    biomarker_trends = list_biomarker_trends()
    observations = list_biomarker_observations()
    latest_flagged = _latest_flagged_biomarkers(observations)
    care_recommendations = list_active_care_recommendations()
    routines = list_routines()
    movement_blocks = list_movement_blocks()
    movement_plan = recommend_movement_plan(
        check_ins[0] if check_ins else None,
        signals[0] if signals else None,
    )
    biomarker_insight = build_biomarker_insight(
        "",
        observations,
        biomarker_trends,
        care_recommendations,
    )
    care_biomarker_context = build_care_biomarker_context(
        "",
        care_recommendations,
        list(biomarker_insight["focusKeys"]),
    )
    food_biomarker_context = build_food_biomarker_context(selected_meal, "")
    return {
        "meal": selected_meal,
        "signal": signals[0] if signals else None,
        "check_in": check_ins[0] if check_ins else None,
        "due_today": due_today,
        "due_now": due_now,
        "biomarker_trends": biomarker_trends,
        "latest_flagged_biomarkers": latest_flagged,
        "care_recommendations": care_recommendations,
        "routines": routines,
        "movement_blocks": movement_blocks,
        "movement_plan": movement_plan,
        "biomarker_insight": biomarker_insight,
        "care_biomarker_context": care_biomarker_context,
        "food_biomarker_context": food_biomarker_context,
    }


def _refine_scope_with_context(
    scope: SourceScopeSelection,
    context: dict,
    biomarker_insight: dict,
) -> SourceScopeSelection:
    groups = list(scope.groups)
    reason_parts = [scope.reason] if scope.reason else []
    check_in = context["check_in"]

    if (
        context["latest_flagged_biomarkers"]
        and "app_health_data" in groups
        and "notebooklm_research" not in groups
    ):
        groups.append("notebooklm_research")
        reason_parts.append(
            "Aktivni biomarker signal doplnuje odpoved o evidence vrstvu i u obecnejsiho dotazu."
        )

    if (
        check_in
        and (check_in.energy <= 4 or check_in.stress >= 7)
        and "ubz_framework" not in groups
    ):
        groups.append("ubz_framework")
        reason_parts.append(
            "Zatizeny check-in pridava behavioralni UBZ oporu pro regulaci dne."
        )

    if context["signal"] and "ubz_framework" not in groups:
        groups.append("ubz_framework")
        reason_parts.append(
            "Aktivni zdravotni signal je vhodne cist i pres UBZ souvislosti."
        )

    if (
        biomarker_insight.get("isBiomarkerQuery")
        and "app_health_data" not in groups
    ):
        groups.append("app_health_data")
        reason_parts.append(
            "Biomarkerovy fokus pritahuje potvrzena runtime data do odpovedi."
        )

    return SourceScopeSelection(
        mode=scope.mode,
        groups=list(dict.fromkeys(groups)),
        locked=scope.locked,
        reason=" ".join(reason_parts).strip(),
    )


def _is_general_guidance_message(message: str) -> bool:
    return _contains_any(
        message,
        [
            "co je pro me dnes",
            "co je dnes",
            "na co si dnes",
            "co je nejdulezitejsi",
            "jaka je priorita",
            "priorita dne",
        ],
    )


def _top_knowledge_title(hits: list[object]) -> str | None:
    if not hits:
        return None
    title = str(getattr(hits[0], "title", "")).strip()
    return title or None


def _top_knowledge_guidance(hits: list[object]) -> str | None:
    if not hits:
        return None
    guidance = str(getattr(hits[0], "guidance", "") or "").strip()
    if guidance:
        return guidance
    excerpt = str(getattr(hits[0], "excerpt", "") or "").strip()
    return excerpt or None


def _knowledge_step_with_title(title: str, guidance: str | None, fallback: str) -> str:
    if guidance:
        return f"Zdrojem '{title}' se rídí tenhle krok: {guidance}"
    return fallback


def _prepend_unique_steps(existing: list[str], additions: list[str], limit: int = 4) -> list[str]:
    combined: list[str] = []
    for step in additions + existing:
        if step and step not in combined:
            combined.append(step)
    return combined[:limit]


def _enrich_answer_with_knowledge_signals(
    answer: AssistantAnswer,
    message: str,
    ubz_hits: list[object],
    evidence_hits: list[object],
) -> AssistantAnswer:
    ubz_title = _top_knowledge_title(ubz_hits)
    ubz_guidance = _top_knowledge_guidance(ubz_hits)
    evidence_title = _top_knowledge_title(evidence_hits)
    evidence_guidance = _top_knowledge_guidance(evidence_hits)
    if not ubz_title and not evidence_title:
        return answer

    is_regulation_query = _contains_any(
        message, ["dech", "stres", "regener", "energie", "span", "rytmus"]
    )
    is_biomarker_query = _is_biomarker_message(message)

    summary_additions: list[str] = []
    step_additions: list[str] = []
    interpretation_additions: list[str] = []

    if is_regulation_query:
        if ubz_title:
            summary_additions.append(f"UBZ fokus dnes taha '{ubz_title}'.")
            step_additions.append(
                _knowledge_step_with_title(
                    ubz_title,
                    ubz_guidance,
                    f"Jako UBZ kotvu si dnes drzte uzel '{ubz_title}'.",
                )
            )
            interpretation_additions.append(
                f"UBZ kotvu dnes drzi '{ubz_title}'."
                + (f" Prakticky z ni plyne: {ubz_guidance}" if ubz_guidance else "")
            )
        if evidence_title:
            summary_additions.append(f"Evidence oporu pridava '{evidence_title}'.")
            step_additions.append(
                _knowledge_step_with_title(
                    evidence_title,
                    evidence_guidance,
                    f"Jako evidence oporu berte '{evidence_title}' a overujte podle ni, zda jde vic o regulaci nebo pretizeni.",
                )
            )
            interpretation_additions.append(
                f"Evidence oporu pridava '{evidence_title}'."
                + (f" Prakticky z ni plyne: {evidence_guidance}" if evidence_guidance else "")
            )
    elif is_biomarker_query:
        if evidence_title:
            summary_additions.append(f"Evidence kotvu dnes drzi '{evidence_title}'.")
            step_additions.append(
                _knowledge_step_with_title(
                    evidence_title,
                    evidence_guidance,
                    f"Jako evidence kotvu si pri cteni trendu drzte zdroj '{evidence_title}'.",
                )
            )
            interpretation_additions.append(
                f"Evidence kotvu tu drzi '{evidence_title}'."
                + (f" Prakticky z ni plyne: {evidence_guidance}" if evidence_guidance else "")
            )
        if ubz_title:
            step_additions.append(
                _knowledge_step_with_title(
                    ubz_title,
                    ubz_guidance,
                    f"UBZ vrstvu berte jako kontextovou oporu pres uzel '{ubz_title}', ne jako vyssi autoritu nez mereny trend.",
                )
            )
    else:
        if ubz_title:
            summary_additions.append(f"UBZ fokus dnes taha '{ubz_title}'.")
            step_additions.append(
                _knowledge_step_with_title(
                    ubz_title,
                    ubz_guidance,
                    f"Jako UBZ kotvu si drzte uzel '{ubz_title}'.",
                )
            )
            interpretation_additions.append(
                f"UBZ kotvu drzi '{ubz_title}'."
                + (f" Prakticky z ni plyne: {ubz_guidance}" if ubz_guidance else "")
            )
        if evidence_title:
            summary_additions.append(f"Evidence oporu pridava '{evidence_title}'.")
            step_additions.append(
                _knowledge_step_with_title(
                    evidence_title,
                    evidence_guidance,
                    f"Jako evidence oporu drzte zdroj '{evidence_title}'.",
                )
            )
            interpretation_additions.append(
                f"Evidence oporu pridava '{evidence_title}'."
                + (f" Prakticky z ni plyne: {evidence_guidance}" if evidence_guidance else "")
            )

    if summary_additions:
        answer.summary = f"{answer.summary} {' '.join(summary_additions)}"

    if step_additions:
        answer.next_steps = _prepend_unique_steps(answer.next_steps, step_additions)

    if interpretation_additions:
        for section in answer.sections:
            if getattr(section, "kind", None) != "model_interpretation":
                continue
            section.content = f"{section.content} {' '.join(interpretation_additions)}"
            break

    return answer


def _build_knowledge_query(message: str, context: dict, biomarker_insight: dict) -> str:
    query_parts = [message]
    check_in = context["check_in"]
    meal = context["meal"]
    signal = context["signal"]
    message_targets_regulation = _contains_any(
        message,
        ["dech", "stres", "regener", "energie", "rytmus", "span"],
    )
    general_guidance = _is_general_guidance_message(message)
    message_targets_biomarkers = _is_biomarker_message(message)
    message_targets_food = _is_food_message(message)

    if (
        check_in
        and (check_in.energy <= 4 or check_in.stress >= 7)
        and (message_targets_regulation or general_guidance)
    ):
        query_parts.append("energie stres regenerace span rytmus")

    if signal and (message_targets_regulation or general_guidance):
        query_parts.extend(
            [
                signal.title,
                signal.category,
                signal.severity,
            ]
        )

    if meal and message_targets_food:
        query_parts.append(_meal_title_text(meal))
        if meal.tags:
            query_parts.extend(meal.tags[:3])

    if message_targets_biomarkers and biomarker_insight.get("highlights"):
        query_parts.extend(str(item) for item in biomarker_insight["highlights"][:3])

    if message_targets_biomarkers and biomarker_insight.get("focusKeys"):
        query_parts.extend(
            str(item).replace("_", " ")
            for item in list(biomarker_insight["focusKeys"])[:3]
        )

    care_recommendations = context["care_recommendations"]
    if care_recommendations and (message_targets_biomarkers or general_guidance):
        top_care = care_recommendations[0]
        query_parts.extend(
            [
                top_care.title,
                top_care.category,
            ]
        )
        query_parts.extend(top_care.related_markers[:2])

    deduped_parts: list[str] = []
    seen: set[str] = set()
    for part in query_parts:
        normalized = str(part).strip().lower()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        deduped_parts.append(str(part).strip())

    return " ".join(deduped_parts)


def _biomarker_context_text(message: str, context: dict) -> str:
    flagged = context["latest_flagged_biomarkers"]
    trends = context["biomarker_trends"]
    care_recommendations = context["care_recommendations"]
    insight = build_biomarker_insight(
        message,
        list_biomarker_observations(),
        trends,
        care_recommendations,
    )
    if insight["isBiomarkerQuery"]:
        return f"Biomarker vrstva teď ukazuje tento fokus: {insight['content']}"

    if flagged:
        highlights = ", ".join(
            f"{item.marker_label} ({item.value} {item.unit or ''}, {item.status})".strip()
            for item in flagged[:3]
        )
        return (
            f"Potvrzená biomarker vrstva ukazuje {len(flagged)} aktuálně významných odchylek. "
            f"Nejvíce vystupují: {highlights}."
        )

    return (
        f"Biomarker vrstva je potvrzená a obsahuje {len(trends)} trendových markerů, "
        "ale bez aktuálně výrazných high/low odchylek."
    )


def _routine_context_text(context: dict) -> str:
    routines = context["routines"]
    movement_blocks = context["movement_blocks"]
    movement_plan = context["movement_plan"]
    if not routines and not movement_blocks:
        return "Zatím není načtená rutina ani pohybové bloky."

    parts: list[str] = []
    if routines:
        routine = routines[0]
        first_steps = ", ".join(step.title for step in routine.steps[:3])
        parts.append(
            f"Aktivní rutina '{routine.title}' drží jádro dne přes kroky: {first_steps}."
        )
    if movement_blocks:
        block_names = ", ".join(block.title for block in movement_blocks[:3])
        parts.append(
            f"Pohybová vrstva je zatím postavená hlavně na blocích: {block_names}."
        )
    if movement_plan["recommendedTitles"]:
        parts.append(
            f"Dnešní pohybový režim je '{movement_plan['mode']}' a nejvíc se hodí: {', '.join(movement_plan['recommendedTitles'][:3])}."
        )
    if movement_plan["avoidedTitles"]:
        parts.append(
            f"Dočasně je vhodné ubrat nebo vynechat: {', '.join(movement_plan['avoidedTitles'][:2])}."
        )
    return " ".join(parts)


def _profile_context_text(context: dict) -> str:
    parts: list[str] = []
    check_in = context["check_in"]
    meal = context["meal"]
    signal = context["signal"]
    due_today = context["due_today"]
    due_now = context["due_now"]

    if check_in:
        parts.append(
            f"Poslední check-in je {check_in.check_in_type} s energií {check_in.energy}/10, "
            f"stresem {check_in.stress}/10 a spánkem {check_in.sleep_quality}/10."
        )
    else:
        parts.append("Zatím chybí nový denní check-in, takže kontext dne je stále slabý.")

    if meal:
        meal_tags = ", ".join(meal.tags) if meal.tags else "bez tagu"
        parts.append(f"Poslední zapsané jídlo je {_meal_title_text(meal)} ({meal_tags}).")
    else:
        parts.append("Zatím není zapsané poslední jídlo.")

    if signal:
        parts.append(
            f"Poslední zdravotní signál je {signal.title} se závažností {signal.severity}."
        )
    else:
        parts.append("Zatím není aktivní zdravotní signál.")

    if due_now:
        parts.append(f"Aktuálně je splatných {len(due_now)} follow-up reminderů.")
    elif due_today:
        parts.append(f"Na dnes je otevřeno {len(due_today)} follow-up reminderů.")

    flagged = context["latest_flagged_biomarkers"]
    care_recommendations = context["care_recommendations"]
    routines = context["routines"]
    if flagged:
        top = flagged[0]
        parts.append(
            f"V biomarker vrstvě je aktuálně významný signál u {top.marker_label} se statusem {top.status}."
        )
    if care_recommendations:
        top_care = care_recommendations[0]
        parts.append(
            f"Aktivní doporučení péče: {top_care.title} od zdroje {top_care.source} s prioritou {top_care.priority}."
        )
    if routines:
        top_routine = routines[0]
        parts.append(f"Rutinní kotva dne je {top_routine.title}.")

    return " ".join(parts)


def _workflow_context_text(context: dict, ubz_hits: list, evidence_hits: list) -> str:
    local_layers: list[str] = []
    if context["check_in"]:
        local_layers.append("check-in")
    if context["meal"]:
        local_layers.append("jidlo")
    if context["signal"]:
        local_layers.append("health signal")
    if context["biomarker_trends"]:
        local_layers.append("biomarker trendy")
    if context["care_recommendations"]:
        local_layers.append("care vrstva")
    if context["due_today"] or context["due_now"]:
        local_layers.append("follow-upy")
    if context.get("dna_biomarker_context") or get_genetic_profile():
        local_layers.append("DNA vrstva")

    local_text = (
        f"Lokalni runtime dnes bezi hlavne nad vrstvami: {', '.join(local_layers[:6])}."
        if local_layers
        else "Lokalni runtime vrstva je pripravená, ale dnes je zatim jen slabe naplnena provoznimi daty."
    )

    return (
        local_text
        + " Strukturovane zaznamy se do Notion posilaji az pri explicitni synchronizaci, takže Notion neni hlavni behove prostredi aplikace."
        + (
            f" UBZ vrstva dnes pridala {len(ubz_hits)} znalostni hit(y) a evidence vrstva {len(evidence_hits)} hit(y)."
            if ubz_hits or evidence_hits
            else " UBZ a evidence vrstva tu slouzi jako znalostni podklad pro odpoved, ne jako denni log uzivatele."
        )
        + " Knowledge a evidence vrstva maji pomahat s interpretaci a souvislostmi, zatimco operativa dne vznika primarne lokalne."
    )


def _dna_signal_text(message: str, context: dict) -> str:
    meal = context["meal"]
    dna_biomarker_context = context.get("dna_biomarker_context")
    if dna_biomarker_context and dna_biomarker_context["isRelevant"]:
        content = str(dna_biomarker_context["content"])
        care_recommendations = context["care_recommendations"]
        if care_recommendations and _is_biomarker_message(message):
            top_care = care_recommendations[0]
            if top_care.title not in content:
                content += f" Z care vrstvy se sem navíc propisuje: {top_care.title}."
        if meal and _is_biomarker_message(message) and _meal_title_text(meal) not in content:
            content += f" Poslední zapsané jídlo je {_meal_title_text(meal)}."
        return content
    if _is_dairy_message(message):
        meal_part = f" Poslední zapsané jídlo je {_meal_title_text(meal)}." if meal else ""
        return (
            "DNA vrstva se má číst jako doporučující signál. U mléčných produktů může "
            "naznačovat horší toleranci laktózy, ale nejde o definitivní zákaz."
            + meal_part
        )
    return (
        "DNA vrstva zůstává doporučující. Když se objeví konflikt mezi predispozicí a "
        "reálným chováním nebo jídlem, asistent má upozornit a vysvětlit souvislost."
    )


def _evidence_text(message: str, context: dict, evidence_content: str) -> str:
    signal = context["signal"]
    check_in = context["check_in"]
    flagged = context["latest_flagged_biomarkers"]
    care_recommendations = context["care_recommendations"]
    movement_blocks = context["movement_blocks"]
    food_biomarker_context = build_food_biomarker_context(context["meal"], message)
    dna_biomarker_context = context.get("dna_biomarker_context")
    care_biomarker_context = context.get("care_biomarker_context")
    if _contains_any(message, ["dech", "stres", "regener", "energie", "span"]):
        signal_part = (
            f" Aktuální signál {signal.title} může být ovlivněn i regulací stresu."
            if signal
            else ""
        )
        movement_part = ""
        if movement_blocks:
            movement_part = (
                f" Z routine vrstvy se sem hodí hlavně blok '{movement_blocks[0].title}'."
            )
        return (
            "Evidence vrstva podporuje to, že špatný spánek, stresová zátěž a "
            "přetížený rytmus běžně zhoršují energii, vnímání těla i regeneraci."
            + signal_part
            + movement_part
            + " "
            + evidence_content
        )
    if _is_dairy_message(message):
        return (
            "Tolerance jídla se má číst podle reálných symptomů, množství, formy "
            "potraviny a opakovatelnosti reakce, ne jen podle jednoho izolovaného dojmu."
            + (
                f" {food_biomarker_context['content']}"
                if food_biomarker_context["isRelevant"]
                else ""
            )
            + " "
            + evidence_content
        )
    if _is_biomarker_message(message):
        insight = build_biomarker_insight(
            message,
            list_biomarker_observations(),
            context["biomarker_trends"],
            care_recommendations,
        )
        biomarker_part = ""
        if flagged:
            top = flagged[0]
            biomarker_part = (
                f" Potvrzená data teď zvyšují pozornost hlavně u {top.marker_label} "
                f"({top.value} {top.unit or ''}, {top.status})."
            )
        elif insight["highlights"]:
            biomarker_part = (
                f" Fokus biomarker vrstvy se teď opírá hlavně o {', '.join(insight['highlights'][:2])}."
            )
        care_part = ""
        if care_recommendations:
            care_part = (
                f" Odborná vrstva péče navíc připomíná doporučení '{care_recommendations[0].title}'."
            )
        return (
            "Laboratorní hodnoty je vhodné číst v trendu, ne izolovaně po jednom odběru."
            + biomarker_part
            + care_part
            + (
                f" {care_biomarker_context['content']}"
                if care_biomarker_context and care_biomarker_context["isRelevant"]
                else ""
            )
            + (
                f" {dna_biomarker_context['content']}"
                if dna_biomarker_context and dna_biomarker_context["isRelevant"]
                else ""
            )
            + (
                f" {food_biomarker_context['content']}"
                if food_biomarker_context["isRelevant"]
                else ""
            )
            + " "
            + evidence_content
        )
    if _contains_any(message, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]):
        care_part = ""
        if care_recommendations:
            care_part = (
                f" Aktivní doporučení péče teď zahrnují například '{care_recommendations[0].title}'."
            )
        return (
            "Doporučení od lékaře mají mít vyšší prioritu než obecné tipy a mají se číst spolu s biomarkery a trendem v čase."
            + care_part
            + " "
            + evidence_content
        )
    if check_in:
        return (
            f"Poslední check-in s energií {check_in.energy}/10 a stresem {check_in.stress}/10 "
            "je dobrý signál pro to, jestli dnes jít víc do výkonu, nebo spíš do regulace."
            + " "
            + evidence_content
        )
    return evidence_content


def _model_interpretation_text(message: str, context: dict, ubz_content: str) -> str:
    flagged = context["latest_flagged_biomarkers"]
    care_recommendations = context["care_recommendations"]
    routines = context["routines"]
    movement_blocks = context["movement_blocks"]
    movement_plan = context["movement_plan"]
    food_biomarker_context = build_food_biomarker_context(context["meal"], message)
    dna_biomarker_context = context.get("dna_biomarker_context")
    care_biomarker_context = context.get("care_biomarker_context")
    if _is_food_message(message):
        return (
            "Nejrozumnější další krok je menší dávka, jednodušší forma potraviny a krátké "
            "sledování trávení, energie a reakce těla v čase."
        )
    if _contains_any(message, ["dech", "regener", "stres", "rytmus"]):
        routine_part = ""
        if routines:
            routine_part = f" Drzte rano kotvu '{routines[0].title}'."
        return (
            "Prakticky dnes dává smysl krátký dechový blok, menší tlak na výkon a vědomě "
            "jednodušší rytmus dne." + routine_part + " " + ubz_content
        )
    if _contains_any(message, ["soubor", "hdd", "disk", "adresar"]):
        return (
            "Dotaz potřebuje rozšířit source scope. Nejdřív zúžte oblast, potom nad ní pustíme "
            "cílené vyhledání a teprve pak závěry zapíšeme do kanonické vrstvy."
        )
    if _is_biomarker_message(message) and flagged:
        insight = build_biomarker_insight(
            message,
            list_biomarker_observations(),
            context["biomarker_trends"],
            care_recommendations,
        )
        top = flagged[0]
        if insight["highlights"]:
            return (
                f"Prakticky teď dává smysl vzít jako fokus {', '.join(insight['highlights'][:2])}, "
                "přečíst je v trendu, spojit s jídlem, energií a doporučeními doktorky a "
                "nevytvářet závěr jen z jedné hodnoty."
                + (
                    f" {care_biomarker_context['content']}"
                    if care_biomarker_context and care_biomarker_context["isRelevant"]
                    else ""
                )
                + (
                    f" {dna_biomarker_context['content']}"
                    if dna_biomarker_context and dna_biomarker_context["isRelevant"]
                    else ""
                )
                + (
                    f" {food_biomarker_context['content']}"
                    if food_biomarker_context["isRelevant"]
                    else ""
                )
            )
        return (
            f"Prakticky teď dává smysl vzít {top.marker_label} jako pracovní prioritu, "
            "přečíst ho v trendu, spojit s jídlem, energií a doporučeními doktorky a "
            "nevytvářet závěr jen z jedné hodnoty."
        )
    if _is_biomarker_message(message):
        insight = build_biomarker_insight(
            message,
            list_biomarker_observations(),
            context["biomarker_trends"],
            care_recommendations,
        )
        if insight["highlights"]:
            return (
                f"Prakticky teď dává smysl vzít jako fokus {', '.join(insight['highlights'][:2])}, "
                "přečíst je v trendu a oddělit měřený stav od pracovní interpretace."
            )
    if _contains_any(message, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]):
        if care_recommendations:
            top = care_recommendations[0]
            return (
                f"Prakticky teď dává smysl vzít doporučení '{top.title}' jako autoritativní vrstvu, "
                "spojit ho s biomarkery a nastavit konkrétní další kontrolu nebo termín."
            )
        return (
            "Prakticky teď dává smysl nejdřív zapsat konkrétní doporučení doktorky a teprve potom z něj dělat reminder a guidance logiku."
        )
    if _contains_any(message, ["rutina", "ranni rutina", "pohyb", "cviky", "kolo", "cykli", "chuze"]):
        movement_part = (
            movement_plan["recommendedTitles"][0]
            if movement_plan["recommendedTitles"]
            else (movement_blocks[0].title if movement_blocks else "krátký pohybový blok")
        )
        return (
            f"Prakticky dnes dává smysl držet ranní minimum a navázat blokem '{movement_part}', "
            f"v režimu '{movement_plan['mode']}', tedy podle energie, spánku a stavu zad nebo ramene."
        )
    return (
        "Asistent má dnes spojit provozní data s UBZ vrstvou: nehnat další výkon naslepo, "
        "ale nejdřív pojmenovat stav, zvolit další krok a pak sledovat odezvu."
    )


def _next_steps(message: str, context: dict) -> list[str]:
    steps: list[str] = []
    flagged = context["latest_flagged_biomarkers"]
    care_recommendations = context["care_recommendations"]
    routines = context["routines"]
    movement_blocks = context["movement_blocks"]
    movement_plan = context["movement_plan"]
    food_biomarker_context = build_food_biomarker_context(context["meal"], message)
    dna_biomarker_context = context.get("dna_biomarker_context")
    care_biomarker_context = context.get("care_biomarker_context")
    is_biomarker_message = _is_biomarker_message(message)
    if _is_food_message(message) and context["meal"]:
        steps.append(
            f"Zkontrolujte posledni jidlo '{context['meal'].title}' a doplnte priblizne mnozstvi."
        )
    if _is_food_message(message):
        steps.extend(
            [
                "Zaznamenejte potravinu a přibližné množství.",
                (
                    "Spojte poslední jídlo s lipidovou nebo glukózovou oblastí a sledujte, jestli podporuje aktuální biomarker fokus."
                    if is_biomarker_message and food_biomarker_context["isRelevant"]
                    else "Sledujte trávení, energii a případný signál v následujících hodinách."
                ),
                "Sledujte trávení, energii a případný signál v následujících hodinách.",
                "Při opakované reakci vytvořte nebo doplňte health signal.",
            ]
        )
    elif _contains_any(message, ["dech", "stres", "regener", "rytmus", "energie"]):
        steps.extend(
            [
                "Zařaďte krátký dechový blok před další náročnější činnost.",
                "Držte jednoduchý rytmus jídla a menší stimulační zátěž.",
                "Večer zkontrolujte energii, stres a subjektivní regeneraci.",
            ]
        )
    elif _is_biomarker_message(message):
        insight = build_biomarker_insight(
            message,
            list_biomarker_observations(),
            context["biomarker_trends"],
            care_recommendations,
        )
        if flagged:
            top = flagged[0]
            focus = ", ".join(insight["highlights"][:2]) if insight["highlights"] else top.marker_label
            steps.extend(
                [
                    f"Začněte markerem nebo dvojicí markerů {focus} a projděte jejich trend v čase.",
                    (
                        f"Spojte fokus hlavne s: {', '.join(insight['linkWith'][:3])}."
                        if insight["linkWith"]
                        else "Spojte ho s jídlem, energií, stresem a dalšími souvisejícími oblastmi."
                    ),
                    (
                        f"Zpozornete hlavne kdyz plati: {', '.join(insight['alertWhen'][:2])}."
                        if insight["alertWhen"]
                        else "Odlište, co je měřený stav, co je predispozice a co je jen pracovní interpretace."
                    ),
                ]
            )
            if dna_biomarker_context and dna_biomarker_context["isRelevant"]:
                bridge_steps = [
                    "Porovnejte fokus i s DNA vrstvou, ale biomarkery ponechte jako vyšší autoritu než predispozici."
                ]
                if dna_biomarker_context.get("relatedCareTitles"):
                    bridge_steps.append(
                        f"Ověřte, jestli se stejný směr potvrzuje i s care vrstvou: {', '.join(dna_biomarker_context['relatedCareTitles'][:2])}."
                    )
                if dna_biomarker_context.get("mealContext"):
                    bridge_steps.append("Přečtěte stejnou oblast i přes kontext zachycený posledním jídlem, ne jen přes laboratorní trend.")
                steps[1:1] = bridge_steps
            if care_biomarker_context and care_biomarker_context["isRelevant"]:
                steps.insert(
                    min(len(steps), 1),
                    f"Pracujte vedle biomarkerů i s care vrstvou: {', '.join(care_biomarker_context['relatedCareTitles'][:2])}.",
                )
            if food_biomarker_context["isRelevant"]:
                steps.append("Spojte fokus i s posledním jídlem a sledujte, jestli podporuje lipidovou nebo glukózovou zátěž.")
        elif insight["highlights"]:
            focus = ", ".join(insight["highlights"][:2])
            steps.extend(
                [
                    f"Začněte markerem nebo dvojicí markerů {focus} a projděte jejich trend v čase.",
                    (
                        f"Spojte je hlavne s: {', '.join(insight['linkWith'][:3])}."
                        if insight["linkWith"]
                        else "Spojte je s denním fungováním a s tím, co už říká care vrstva."
                    ),
                    (
                        f"Sledujte hlavne: {', '.join(insight['watchFor'][:3])}."
                        if insight["watchFor"]
                        else "Odlište trend, poslední hodnotu a praktický další krok."
                    ),
                ]
            )
            if dna_biomarker_context and dna_biomarker_context["isRelevant"]:
                bridge_steps = [
                    "Zkontrolujte, jestli DNA vrstva podporuje stejný směr interpretace, nebo jen rozšíří kontext."
                ]
                if dna_biomarker_context.get("relatedCareTitles"):
                    bridge_steps.append(
                        f"Spojte interpretaci i s care vrstvou: {', '.join(dna_biomarker_context['relatedCareTitles'][:2])}."
                    )
                if dna_biomarker_context.get("mealContext"):
                    bridge_steps.append("Porovnejte fokus i s posledním jídlem, aby byla vidět vazba mezi predispozicí a reálným dnem.")
                steps[1:1] = bridge_steps
            if care_biomarker_context and care_biomarker_context["isRelevant"]:
                steps.insert(
                    min(len(steps), 1),
                    f"Spojte marker i s care vrstvou: {', '.join(care_biomarker_context['relatedCareTitles'][:2])}.",
                )
            if food_biomarker_context["isRelevant"]:
                steps.append("Přečtěte poslední jídlo i jako praktickou stopu k lipidům nebo glukózové oblasti.")
        else:
            steps.extend(
                [
                    "Projděte hlavní markerové trendy v čase místo jednoho izolovaného výsledku.",
                    "Spojte laboratorní data s denním fungováním a symptomy.",
                    "Teprve potom určete, co je skutečná priorita pro další krok.",
                ]
            )
    elif _contains_any(message, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]):
        if care_recommendations:
            top = care_recommendations[0]
            steps.extend(
                [
                    f"Držte se doporučení '{top.title}' jako vysoké priority.",
                    "Spojte lékařovo doporučení s biomarkerovými trendy a dalším termínem kontroly.",
                    "Odlište, co je obecná rada a co už konkrétní individuální doporučení péče.",
                ]
            )
        else:
            steps.extend(
                [
                    "Sepište konkrétní doporučení doktorky do systému.",
                    "Doplňte zdroj, prioritu a případný termín další kontroly.",
                    "Pak je propojte s biomarkery a reminder vrstvou.",
                ]
            )
    elif _contains_any(message, ["rutina", "ranni rutina", "pohyb", "cviky", "kolo", "cykli", "chuze"]):
        if routines:
            steps.append(f"Držte jako minimum rutinu '{routines[0].title}'.")
        if movement_plan["recommendedTitles"]:
            steps.append(
                f"Vyberte dnes jeden pohybový blok z doporučené vrstvy: {movement_plan['recommendedTitles'][0]}."
            )
        elif movement_blocks:
            steps.append(f"Vyberte dnes jeden pohybový blok: {movement_blocks[0].title}.")
        if movement_plan["avoidedTitles"]:
            steps.append(
                f"Dnes raději nechte stranou: {', '.join(movement_plan['avoidedTitles'][:2])}."
            )
        steps.extend(
            [
                "Přizpůsobte intenzitu energii, stresu a aktuálnímu stavu těla.",
                "Večer zkontrolujte, jestli byl pohyb spíš aktivační, nebo přetěžující.",
            ]
        )
    elif _contains_any(message, ["soubor", "hdd", "disk", "adresar"]):
        steps.extend(
            [
                "Upřesněte, jakou složku nebo zdroj chcete otevřít.",
                "Omezte scope na jednu oblast pro vyšší relevanci.",
                "Nalezený materiál teprve potom zapisujte do kanonické vrstvy.",
            ]
        )
    else:
        steps.extend(
            [
                "Nejdřív doplňte nebo zkontrolujte denní check-in.",
                "Pojmenujte největší aktuální signál nebo prioritu dne.",
                "Navažte jedním konkrétním dalším krokem místo více paralelních změn.",
            ]
        )

    if context["due_now"]:
        steps.insert(0, "Nejdřív zpracujte aktuálně splatný follow-up reminder.")

    deduped: list[str] = []
    for step in steps:
        if step not in deduped:
            deduped.append(step)
    return deduped[:4]


def _summary_text(message: str, context: dict) -> str:
    flagged = context["latest_flagged_biomarkers"]
    care_recommendations = context["care_recommendations"]
    routines = context["routines"]
    if _is_food_message(message) and context["meal"]:
        return (
            f"Po jidle '{_meal_title_text(context['meal'])}' ma dnes nejvetsi smysl cist traveni, "
            "energii a vazbu na biomarkerovou vrstvu, ne jen izolovany telesny signal."
        )
    if _is_dairy_message(message):
        return (
            "U mléčného produktu je vhodné zpozornět: DNA vrstva může naznačovat horší "
            "toleranci laktózy, ale rozhoduje hlavně reálná reakce těla."
        )
    if _contains_any(message, ["dech", "stres", "regener", "energie", "rytmus"]):
        return (
            "Dnes je nejdůležitější podržet klidný rytmus, dechovou stabilitu a "
            "nezahlcovat organismus dalším stresem."
        )
    if _is_biomarker_message(message):
        insight = build_biomarker_insight(
            message,
            list_biomarker_observations(),
            context["biomarker_trends"],
            care_recommendations,
        )
        if insight["highlights"]:
            return (
                f"Biomarker vrstva už je potvrzená a jako první fokus je dobré číst "
                f"{', '.join(insight['highlights'][:2])} v trendu, ne izolovaně."
            )
        if flagged:
            top = flagged[0]
            return (
                f"Biomarker vrstva už je potvrzená a jako první prioritu je dobré číst "
                f"{top.marker_label} v trendu, ne izolovaně."
            )
        return (
            "Biomarker vrstva je potvrzená a další krok je číst hodnoty hlavně v časovém trendu."
        )
    if _contains_any(message, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]):
        if care_recommendations:
            top = care_recommendations[0]
            return (
                f"V preventivní vrstvě je teď dobré držet doporučení '{top.title}' jako vyšší autoritu a spojit ho s měřenými daty."
            )
        return (
            "Vrstva doporučení doktorky je připravená, ale zatím v ní nejsou konkrétní aktivní záznamy."
        )
    if _contains_any(message, ["rutina", "ranni rutina", "pohyb", "cviky", "kolo", "cykli", "chuze"]):
        if routines:
            return (
                f"Dnes dává smysl držet rutinní kotvu '{routines[0].title}' a pohyb brát jako podporu rytmu, ne jako tlak na výkon."
            )
        return "Routine vrstva je připravená, ale zatím nemá načtenou aktivní osobní rutinu."
    if _contains_any(message, ["soubor", "hdd", "disk", "adresar"]):
        return (
            "Dotaz potřebuje rozšířený source scope, ale core truth zůstává autoritou pro "
            "osobní pravidla a interpretace."
        )
    if context["signal"]:
        return (
            f"Nejdůležitější je teď dobře přečíst signál '{context['signal'].title}' v "
            "souvislostech a navázat klidným dalším krokem."
        )
    return (
        "Asistent má dnes spojit provozní data, UBZ vrstvu a další krok tak, aby se den "
        "nepřetížil zbytečnou složitostí."
    )


def _selected_section_kinds(
    message: str,
    context: dict,
    food_biomarker_context: dict,
    care_biomarker_context: dict,
    dna_biomarker_context: dict,
) -> list[str]:
    selected = ["profile_context", "workflow_context"]
    is_biomarker_query = _is_biomarker_message(message)
    is_food_query = _is_food_message(message)
    is_regulation_query = _contains_any(
        message, ["dech", "stres", "regener", "energie", "span", "rytmus"]
    )
    is_routine_query = _contains_any(
        message, ["rutina", "ranni rutina", "pohyb", "cviky", "kolo", "cykli", "chuze"]
    )
    is_care_query = _contains_any(
        message, ["doktor", "doktork", "prohlid", "preventiv", "lekar", "screening"]
    )

    if is_biomarker_query:
        selected.extend(["extended_context", "biomarker_insight"])
        if food_biomarker_context["isRelevant"]:
            selected.append("food_biomarker_context")
        if care_biomarker_context["isRelevant"]:
            selected.append("care_biomarker_context")
        if dna_biomarker_context["isRelevant"]:
            selected.append("dna_biomarker_context")
        selected.extend(["ubz_basis", "evidence_basis", "model_interpretation"])
        return selected

    if is_food_query:
        if context["biomarker_trends"]:
            selected.append("extended_context")
        if food_biomarker_context["isRelevant"]:
            selected.append("food_biomarker_context")
        selected.extend(["ubz_basis", "dna_signal", "evidence_basis", "model_interpretation"])
        return selected

    if is_regulation_query or is_routine_query:
        selected.extend(["routine_basis", "ubz_basis", "evidence_basis", "model_interpretation"])
        return selected

    if is_care_query:
        if care_biomarker_context["isRelevant"]:
            selected.append("care_biomarker_context")
        selected.extend(["routine_basis", "evidence_basis", "model_interpretation"])
        return selected

    if context["biomarker_trends"]:
        selected.append("extended_context")
    selected.extend(["routine_basis", "ubz_basis", "evidence_basis", "model_interpretation"])
    return selected


def _prune_sections(sections: list[dict], selected_kinds: list[str]) -> list[dict]:
    selected_set = set(selected_kinds)
    filtered = [section for section in sections if section["kind"] in selected_set]
    filtered.sort(
        key=lambda section: selected_kinds.index(section["kind"])
        if section["kind"] in selected_set
        else 999
    )
    return filtered


def _build_answer(message: str) -> AssistantAnswer:
    context = _recent_operational_context(message)
    biomarker_insight = build_biomarker_insight(
        message,
        list_biomarker_observations(),
        context["biomarker_trends"],
        context["care_recommendations"],
    )
    scope = _refine_scope_with_context(resolve_scope(message), context, biomarker_insight)
    knowledge_query = _build_knowledge_query(message, context, biomarker_insight)
    ubz_content, ubz_hits = build_ubz_context(knowledge_query)
    evidence_content, evidence_hits = build_evidence_context(knowledge_query)
    care_biomarker_context = build_care_biomarker_context(
        message,
        context["care_recommendations"],
        list(biomarker_insight["focusKeys"]),
    )
    food_biomarker_context = build_food_biomarker_context(context["meal"], message)
    genetic_profile = get_genetic_profile()
    dna_biomarker_context = build_dna_biomarker_context(
        message,
        genetic_profile,
        list(biomarker_insight["focusKeys"]),
        care_recommendations=context["care_recommendations"],
        meal=context["meal"],
    )
    context["care_biomarker_context"] = care_biomarker_context
    context["dna_biomarker_context"] = dna_biomarker_context

    sections = [
        {
            "kind": "profile_context",
            "title": "Co o vas system vi",
            "content": _profile_context_text(context),
        },
        {
            "kind": "workflow_context",
            "title": "Jak pracuje lokalni beh, Notion a knowledge vrstva",
            "content": _workflow_context_text(context, ubz_hits, evidence_hits),
        },
        {
            "kind": "extended_context",
            "title": "Co ukazuji biomarker trendy",
            "content": _biomarker_context_text(message, context),
        },
        {
            "kind": "biomarker_insight",
            "title": "Jak cist fokusni biomarker",
            "content": str(biomarker_insight["content"]),
        },
    ]
    if food_biomarker_context["isRelevant"]:
        sections.append(
            {
                "kind": "food_biomarker_context",
                "title": "Jak jídlo vstupuje do biomarkeru",
                "content": str(food_biomarker_context["content"]),
            }
        )
    if care_biomarker_context["isRelevant"]:
        sections.append(
            {
                "kind": "care_biomarker_context",
                "title": "Jak care vrstva vstupuje do biomarkeru",
                "content": str(care_biomarker_context["content"]),
            }
        )
    if dna_biomarker_context["isRelevant"]:
        sections.append(
            {
                "kind": "dna_biomarker_context",
                "title": "Jak DNA vstupuje do biomarkeru",
                "content": _dna_signal_text(message, context),
            }
        )
    sections.extend(
        [
            {
                "kind": "routine_basis",
                "title": "Co drží vaše routine vrstva",
                "content": _routine_context_text(context),
            },
            {
                "kind": "ubz_basis",
                "title": "Co říká UBZ rámec",
                "content": ubz_content,
            },
            {
                "kind": "dna_signal",
                "title": "Co naznačuje DNA",
                "content": _dna_signal_text(message, context),
            },
            {
                "kind": "evidence_basis",
                "title": "Co podporuje evidence vrstva",
                "content": _evidence_text(message, context, evidence_content),
            },
            {
                "kind": "model_interpretation",
                "title": "Doporučený další krok",
                "content": _model_interpretation_text(message, context, ubz_content),
            },
        ]
    )

    selected_kinds = _selected_section_kinds(
        message,
        context,
        food_biomarker_context,
        care_biomarker_context,
        dna_biomarker_context,
    )

    answer = AssistantAnswer(
        summary=_summary_text(message, context),
        selectedScope=scope.model_dump(by_alias=True),
        sections=_prune_sections(sections, selected_kinds),
        nextSteps=_next_steps(message, context),
        sources=[
            source.model_dump()
            for source in default_sources_for_scope(scope, ubz_hits, evidence_hits)
        ],
    )
    return _enrich_answer_with_knowledge_signals(answer, message, ubz_hits, evidence_hits)


def get_sample_answer() -> AssistantAnswer:
    return _build_answer("energie dech regenerace")


def build_answer_for_message(message: str) -> AssistantAnswer:
    return _build_answer(message)


def build_daily_briefing() -> DailyBriefing:
    observations = list_biomarker_observations()
    recent_meals = list_meal_entries()[:1]
    recent_signals = list_health_signals()[:1]
    recent_check_ins = list_daily_check_ins()[:1]
    due_today = list_today_follow_ups()
    due_now = list_due_follow_ups()
    flagged_biomarkers = _latest_flagged_biomarkers(observations)
    latest_observations = _latest_observations_by_marker(observations)
    priority_keys = priority_marker_keys()
    ordered_flagged = sorted(
        flagged_biomarkers,
        key=lambda item: (
            priority_keys.index(item.marker_key) if item.marker_key in priority_keys else 999,
            item.marker_label,
        ),
    )
    biomarker_highlights = [
        f"{item.marker_label}: {item.value} {item.unit or ''} ({item.status})".strip()
        for item in ordered_flagged[:3]
    ]
    routine_items = routine_highlights()
    movement_items = movement_highlights()
    movement_plan = recommend_movement_plan(
        recent_check_ins[0] if recent_check_ins else None,
        recent_signals[0] if recent_signals else None,
    )
    lipid_focus_summary = _build_lipid_focus_summary(latest_observations)
    food_biomarker_context = build_food_biomarker_context(
        recent_meals[0] if recent_meals else None,
        "biomarker cholesterol glukóza jídlo",
    )
    care_highlights = care_recommendation_highlights()

    priorities: list[str] = []
    if due_now:
        priorities.append(
            f"Nejdřív zpracujte {len(due_now)} splatný follow-up, ať nezůstává otevřená akutní věc."
        )
    elif due_today:
        priorities.append(
            f"Dnes máte {len(due_today)} otevřený follow-up; držte ho v záběru během dne."
        )

    if not recent_check_ins:
        priorities.append("Začněte krátkým ranním check-inem a pojmenujte energii, stres a rytmus dne.")
    elif recent_check_ins[0].energy <= 4 or recent_check_ins[0].stress >= 7:
        priorities.append(
            f"Check-in ukazuje energii {recent_check_ins[0].energy}/10 a stres {recent_check_ins[0].stress}/10, takže dnes držte spíš lehčí režim."
        )
    else:
        priorities.append(
            f"Poslední check-in drží energii {recent_check_ins[0].energy}/10 a stres {recent_check_ins[0].stress}/10."
        )

    if movement_plan["recommendedTitles"]:
        priorities.append(
            f"Pohyb dnes držte v režimu '{movement_plan['mode']}' a opřete ho o {movement_plan['recommendedTitles'][0]}."
        )

    if recent_signals:
        priorities.append(
            f"Sledujte signál '{recent_signals[0].title}' a navažte na něj klidnou regulaci."
        )
    elif recent_meals:
        priorities.append(
            f"Po posledním jídle '{recent_meals[0].title}' má smysl krátce zkontrolovat trávení a energii."
        )

    if lipid_focus_summary:
        priorities.append(f"Lipidový fokus: {lipid_focus_summary}")
    elif biomarker_highlights:
        priorities.append(f"Biomarker vrstva dnes zvedá pozornost hlavně u {biomarker_highlights[0]}.")

    if food_biomarker_context["isRelevant"]:
        priorities.append(str(food_biomarker_context["content"]))

    if care_highlights:
        priorities.append(f"V péči dnes držte hlavně doporučení '{care_highlights[0]}'.")

    if routine_items:
        priorities.append(f"Ranní kotvu dnes drží: {routine_items[0]}.")

    priorities = priorities[:6] or [
        "Začněte krátkým ranním check-inem a jedním vědomým dechovým blokem."
    ]

    headline = "Ranní briefing"
    if recent_check_ins and recent_check_ins[0].check_in_type == "evening":
        headline = "Denní briefing po večerní reflexi"

    summary_parts = [
        f"Dnes máte {len(due_today)} otevřených follow-upů, z toho {len(due_now)} je splatných hned.",
        f"Biomarker vrstva drží {len(flagged_biomarkers)} aktivních high/low signálů.",
    ]
    if recent_signals:
        summary_parts.append(f"V provozu je i signál '{recent_signals[0].title}'.")
    elif recent_meals:
        summary_parts.append(f"Poslední jídlo bylo '{recent_meals[0].title}'.")
    if lipid_focus_summary:
        summary_parts.append(f"Lipidová vrstva teď říká: {lipid_focus_summary}")
    if care_highlights:
        summary_parts.append(f"Vrstva péče obsahuje {len(care_highlights)} aktivní doporučení.")
    if movement_plan["recommendedTitles"]:
        summary_parts.append(
            f"Dnešní pohybový režim je '{movement_plan['mode']}' s oporou o {movement_plan['recommendedTitles'][0]}."
        )
    summary = " ".join(summary_parts)

    return DailyBriefing(
        generatedAt=datetime.now(timezone.utc).isoformat(),
        headline=headline,
        summary=summary,
        priorities=priorities,
        dueTodayCount=len(due_today),
        dueNowCount=len(due_now),
        latestCheckInType=recent_check_ins[0].check_in_type if recent_check_ins else None,
        latestCheckInEnergy=recent_check_ins[0].energy if recent_check_ins else None,
        flaggedBiomarkerCount=len(flagged_biomarkers),
        biomarkerHighlights=biomarker_highlights,
        activeCareRecommendationCount=len(list_active_care_recommendations()),
        careHighlights=care_highlights,
        routineHighlights=routine_items,
        movementHighlights=movement_items,
        movementGuardrails=movement_plan["guardrails"],
    )
