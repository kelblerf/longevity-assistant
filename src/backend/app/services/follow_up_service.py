from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.models import CareRecommendation, DailyCheckIn, FollowUpSuggestion, HealthSignal, MealEntry
from app.services.care_recommendation_service import dedupe_care_recommendations, list_care_recommendations
from app.services.daily_check_in_service import list_daily_check_ins
from app.services.health_signal_service import list_health_signals
from app.services.meal_service import list_meal_entries
from app.services.storage_service import read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(value: str) -> datetime:
    return datetime.fromisoformat(value)


def _due_from_delay(hours: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _load_follow_ups() -> list[FollowUpSuggestion]:
    payload = read_json("follow-ups.json", default=[])
    care_aliases = dedupe_care_recommendations()
    migrated: list[dict] = []
    changed = False
    now = datetime.now(timezone.utc)
    pending_seen: dict[tuple[str, str], FollowUpSuggestion] = {}
    completed_seen: set[tuple[str, str, str, str, str]] = set()

    for item in payload:
        next_item = dict(item)
        if "dueAt" not in next_item:
            next_item["dueAt"] = next_item.get("suggestedAt", _now_iso())
            changed = True
        if "status" not in next_item:
            next_item["status"] = "pending"
            changed = True
        if (
            next_item.get("triggerType") == "care_recommendation"
            and next_item.get("relatedId") in care_aliases
            and care_aliases[next_item["relatedId"]] != next_item["relatedId"]
        ):
            next_item["relatedId"] = care_aliases[next_item["relatedId"]]
            changed = True

        suggestion = FollowUpSuggestion.model_validate(next_item)

        # Operational reminders are short-lived and should not flood the dashboard days later.
        if (
            suggestion.status == "pending"
            and suggestion.trigger_type in {"meal", "health_signal", "daily_check_in"}
            and _parse_iso(suggestion.due_at) < now - timedelta(hours=24)
        ):
            changed = True
            continue

        if suggestion.status == "pending":
            signature = (suggestion.trigger_type, suggestion.related_id)
            existing = pending_seen.get(signature)
            if existing is None:
                pending_seen[signature] = suggestion
            else:
                changed = True
                existing_due = _parse_iso(existing.due_at)
                candidate_due = _parse_iso(suggestion.due_at)
                if candidate_due < existing_due or (
                    candidate_due == existing_due and suggestion.suggested_at > existing.suggested_at
                ):
                    pending_seen[signature] = suggestion
            continue

        completed_signature = (
            suggestion.trigger_type,
            suggestion.related_id,
            suggestion.title,
            suggestion.message,
            suggestion.status,
        )
        if completed_signature in completed_seen:
            changed = True
            continue
        completed_seen.add(completed_signature)
        migrated.append(suggestion.model_dump(by_alias=True))

    migrated.extend(
        item.model_dump(by_alias=True)
        for item in sorted(
            pending_seen.values(),
            key=lambda suggestion: suggestion.suggested_at,
        )
    )
    migrated.sort(key=lambda item: item["suggestedAt"])
    if changed:
        write_json("follow-ups.json", migrated)

    return [FollowUpSuggestion.model_validate(item) for item in migrated]


def _find_pending_by_trigger_and_related(
    trigger_type: str,
    related_id: str,
) -> FollowUpSuggestion | None:
    for item in _load_follow_ups():
        if item.trigger_type == trigger_type and item.related_id == related_id and item.status == "pending":
            return item
    return None


def _save_follow_ups(items: list[FollowUpSuggestion]) -> None:
    write_json("follow-ups.json", [item.model_dump(by_alias=True) for item in items])


def list_follow_ups() -> list[FollowUpSuggestion]:
    return sorted(_load_follow_ups(), key=lambda item: item.suggested_at, reverse=True)


def list_due_follow_ups() -> list[FollowUpSuggestion]:
    now = datetime.now(timezone.utc)
    items = [
        item
        for item in _load_follow_ups()
        if item.status == "pending" and _parse_iso(item.due_at) <= now
    ]
    return sorted(items, key=lambda item: item.due_at)


def list_today_follow_ups() -> list[FollowUpSuggestion]:
    today = datetime.now(timezone.utc).date()
    items = [
        item
        for item in _load_follow_ups()
        if item.status == "pending" and _parse_iso(item.due_at).date() == today
    ]
    return sorted(items, key=lambda item: item.due_at)


def mark_follow_up_done(follow_up_id: str) -> FollowUpSuggestion:
    items = _load_follow_ups()
    for index, item in enumerate(items):
        if item.id == follow_up_id:
            updated = item.model_copy(update={"status": "done"})
            items[index] = updated
            _save_follow_ups(items)
            return updated
    raise ValueError(f"Follow-up '{follow_up_id}' not found")


def create_follow_up_for_meal(meal_id: str) -> FollowUpSuggestion:
    meals = list_meal_entries()
    meal = next(item for item in meals if item.id == meal_id)
    delay_label = "Za 1-3 hodiny"
    message = (
        f"Zkontrolujte po jídle '{meal.title}' trávení, energii a klid těla. "
        "Pokud šlo o potenciální DNA konflikt, zapisujte reakci jemně a bez ukvapených závěrů."
    )
    if any(tag.lower() in {"lactose", "mlecne", "mliko"} for tag in meal.tags):
        message = (
            f"Po jídle '{meal.title}' sledujte toleranci laktózy, nadýmání a energii. "
            "Pokud se reakce opakuje, vytvořte zdravotní signál nebo navazující poznámku."
        )

    suggestion = FollowUpSuggestion(
        id=f"follow-{uuid4().hex[:12]}",
        triggerType="meal",
        relatedId=meal.id,
        title="Follow-up po jídle",
        message=message,
        delayLabel=delay_label,
        suggestedAt=_now_iso(),
        dueAt=_due_from_delay(2),
        status="pending",
    )
    items = _load_follow_ups()
    items.append(suggestion)
    _save_follow_ups(items)
    return suggestion


def create_follow_up_for_signal(signal_id: str) -> FollowUpSuggestion:
    signals = list_health_signals()
    signal = next(item for item in signals if item.id == signal_id)
    delay_label = "Dnes večer"
    due_at = (datetime.now(timezone.utc).replace(hour=18, minute=0, second=0, microsecond=0))
    if due_at <= datetime.now(timezone.utc):
        due_at = datetime.now(timezone.utc) + timedelta(hours=2)
    message = (
        f"Vraťte se k signálu '{signal.title}' a zhodnoťte, zda se intenzita mění. "
        "Dobré je doplnit souvislost s jídlem, stresem, dechem nebo spánkem."
    )
    if signal.severity == "high":
        delay_label = "Za 60-90 minut"
        due_at = datetime.now(timezone.utc) + timedelta(minutes=90)
        message = (
            f"Signál '{signal.title}' má vyšší prioritu. Zkontrolujte brzy znovu intenzitu, "
            "spouštěče a to, zda pomohl dechový nebo regenerační zásah."
        )

    suggestion = FollowUpSuggestion(
        id=f"follow-{uuid4().hex[:12]}",
        triggerType="health_signal",
        relatedId=signal.id,
        title="Follow-up ke zdravotnímu signálu",
        message=message,
        delayLabel=delay_label,
        suggestedAt=_now_iso(),
        dueAt=due_at.isoformat(),
        status="pending",
    )
    items = _load_follow_ups()
    items.append(suggestion)
    _save_follow_ups(items)
    return suggestion


def create_follow_up_for_check_in(check_in_id: str) -> FollowUpSuggestion:
    check_ins = list_daily_check_ins()
    check_in = next(item for item in check_ins if item.id == check_in_id)
    if check_in.check_in_type == "morning":
        delay_label = "Dnes večer"
        due_at = datetime.now(timezone.utc).replace(hour=19, minute=0, second=0, microsecond=0)
        if due_at <= datetime.now(timezone.utc):
            due_at = datetime.now(timezone.utc) + timedelta(hours=4)
        message = (
            "Večer se vraťte k rannímu check-inu a zhodnoťte, jestli se energie, stres "
            "a rytmus dne vyvíjely podle očekávání."
        )
        title = "Večerní návrat k rannímu check-inu"
    else:
        delay_label = "Zítra ráno"
        due_at = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
            hour=7, minute=30, second=0, microsecond=0
        )
        message = (
            "Ráno navažte na večerní reflexi a zkontrolujte, jak se propsal spánek, "
            "stres a regenerace do startu dalšího dne."
        )
        title = "Ranní navázání na večerní check-in"

    suggestion = FollowUpSuggestion(
        id=f"follow-{uuid4().hex[:12]}",
        triggerType="daily_check_in",
        relatedId=check_in.id,
        title=title,
        message=message,
        delayLabel=delay_label,
        suggestedAt=_now_iso(),
        dueAt=due_at.isoformat(),
        status="pending",
    )
    items = _load_follow_ups()
    items.append(suggestion)
    _save_follow_ups(items)
    return suggestion


def _parse_due_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        if "T" in value:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        return datetime.fromisoformat(f"{value}T09:00:00+00:00").astimezone(timezone.utc)
    except ValueError:
        return None


def _care_follow_up_due_at(recommendation: CareRecommendation) -> tuple[str, datetime]:
    now = datetime.now(timezone.utc)
    next_due = _parse_due_date(recommendation.next_due)

    if next_due:
        days_until = (next_due.date() - now.date()).days
        if days_until > 30:
            return "30 dní před kontrolou", next_due - timedelta(days=30)
        if days_until > 14:
            return "14 dní před kontrolou", next_due - timedelta(days=14)
        if days_until > 7:
            return "7 dní před kontrolou", next_due - timedelta(days=7)
        if days_until >= 0:
            return "Blížící se kontrola", now + timedelta(hours=1)

    if recommendation.priority == "high":
        return "Týdenní návrat", now + timedelta(days=7)
    if recommendation.priority == "medium":
        return "Kontrola za 14 dní", now + timedelta(days=14)
    return "Měsíční návrat", now + timedelta(days=30)


def create_follow_up_for_care_recommendation(recommendation_id: str) -> FollowUpSuggestion:
    existing = _find_pending_by_trigger_and_related("care_recommendation", recommendation_id)
    if existing:
        return existing

    recommendations = list_care_recommendations()
    recommendation = next(item for item in recommendations if item.id == recommendation_id)
    delay_label, due_at = _care_follow_up_due_at(recommendation)

    marker_part = ""
    if recommendation.related_markers:
        marker_part = f" Propojte to hlavně s markery: {', '.join(recommendation.related_markers[:4])}."

    message = (
        f"Vraťte se k doporučení '{recommendation.title}' od zdroje {recommendation.source}. "
        "Zkontrolujte, jestli se propisuje do běžného dne, pohybu, jídla a další kontroly."
        + marker_part
    )
    if recommendation.priority == "high":
        message += " Jde o vysokou prioritu, tak to neberte jen jako archivní poznámku."

    suggestion = FollowUpSuggestion(
        id=f"follow-{uuid4().hex[:12]}",
        triggerType="care_recommendation",
        relatedId=recommendation.id,
        title="Reminder k doporučení doktorky",
        message=message,
        delayLabel=delay_label,
        suggestedAt=_now_iso(),
        dueAt=due_at.isoformat(),
        status="pending",
    )
    items = _load_follow_ups()
    items.append(suggestion)
    _save_follow_ups(items)
    return suggestion
