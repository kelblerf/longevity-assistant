from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import CreateMealEntryInput, MealEntry
from app.services.storage_service import read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_meal_title(title: str) -> str:
    cleaned = title.strip().strip(".!?")
    lowered = cleaned.lower()
    prefixes = [
        "dal jsem si ",
        "dala jsem si ",
        "snedl jsem ",
        "sne dl jsem ",
        "jedl jsem ",
        "jedla jsem ",
    ]
    for prefix in prefixes:
        if lowered.startswith(prefix):
            cleaned = cleaned[len(prefix):].strip().strip(".!?")
            break
    return cleaned or title.strip()


def _load_meals() -> list[MealEntry]:
    payload = read_json("meal-entries.json", default=[])
    meals = [MealEntry.model_validate(item) for item in payload]
    normalized_meals: list[MealEntry] = []
    changed = False
    for meal in meals:
        normalized_title = _normalize_meal_title(meal.title)
        if normalized_title != meal.title:
            changed = True
            normalized_meals.append(
                meal.model_copy(update={"title": normalized_title})
            )
        else:
            normalized_meals.append(meal)
    if changed:
        _save_meals(normalized_meals)
    return normalized_meals


def _save_meals(meals: list[MealEntry]) -> None:
    write_json("meal-entries.json", [item.model_dump(by_alias=True) for item in meals])


def list_meal_entries() -> list[MealEntry]:
    return sorted(_load_meals(), key=lambda item: item.occurred_at, reverse=True)


def delete_meal_entry(meal_id: str) -> MealEntry | None:
    meals = _load_meals()
    remaining = [meal for meal in meals if meal.id != meal_id]
    if len(remaining) == len(meals):
        return None
    removed = next(meal for meal in meals if meal.id == meal_id)
    _save_meals(remaining)
    return removed


def create_meal_entry(payload: CreateMealEntryInput) -> MealEntry:
    meals = _load_meals()
    meal = MealEntry(
        id=f"meal-{uuid4().hex[:12]}",
        mealType=payload.meal_type,
        title=_normalize_meal_title(payload.title),
        notes=payload.notes,
        tags=payload.tags,
        occurredAt=payload.occurred_at or _now_iso(),
    )
    meals.append(meal)
    _save_meals(meals)
    return meal
