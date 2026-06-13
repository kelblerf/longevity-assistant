from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.models import CreateHealthSignalInput, HealthSignal
from app.services.storage_service import read_json, write_json


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_signals() -> list[HealthSignal]:
    payload = read_json("health-signals.json", default=[])
    return [HealthSignal.model_validate(item) for item in payload]


def _save_signals(signals: list[HealthSignal]) -> None:
    write_json("health-signals.json", [item.model_dump(by_alias=True) for item in signals])


def list_health_signals() -> list[HealthSignal]:
    return sorted(_load_signals(), key=lambda item: item.observed_at, reverse=True)


def delete_health_signal(signal_id: str) -> HealthSignal | None:
    signals = _load_signals()
    remaining = [signal for signal in signals if signal.id != signal_id]
    if len(remaining) == len(signals):
        return None
    removed = next(signal for signal in signals if signal.id == signal_id)
    _save_signals(remaining)
    return removed


def create_health_signal(payload: CreateHealthSignalInput) -> HealthSignal:
    signals = _load_signals()
    signal = HealthSignal(
        id=f"signal-{uuid4().hex[:12]}",
        category=payload.category,
        title=payload.title,
        severity=payload.severity,
        notes=payload.notes,
        observedAt=payload.observed_at or _now_iso(),
    )
    signals.append(signal)
    _save_signals(signals)
    return signal
