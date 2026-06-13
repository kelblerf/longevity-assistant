from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import CreateDailyCheckInInput, DailyCheckIn
from app.services.storage_service import read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_check_ins() -> list[DailyCheckIn]:
    payload = read_json("daily-check-ins.json", default=[])
    return [DailyCheckIn.model_validate(item) for item in payload]


def _save_check_ins(items: list[DailyCheckIn]) -> None:
    write_json("daily-check-ins.json", [item.model_dump(by_alias=True) for item in items])


def list_daily_check_ins() -> list[DailyCheckIn]:
    return sorted(_load_check_ins(), key=lambda item: item.created_at, reverse=True)


def create_daily_check_in(payload: CreateDailyCheckInInput) -> DailyCheckIn:
    items = _load_check_ins()
    check_in = DailyCheckIn(
        id=f"checkin-{uuid4().hex[:12]}",
        checkInType=payload.check_in_type,
        energy=payload.energy,
        stress=payload.stress,
        sleepQuality=payload.sleep_quality,
        notes=payload.notes,
        createdAt=payload.created_at or _now_iso(),
    )
    items.append(check_in)
    _save_check_ins(items)
    return check_in
