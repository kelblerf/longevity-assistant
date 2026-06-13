from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.config import settings


def ensure_runtime_dir() -> Path:
    settings.runtime_dir.mkdir(parents=True, exist_ok=True)
    return settings.runtime_dir


def read_json(filename: str, default: Any) -> Any:
    path = ensure_runtime_dir() / filename
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(filename: str, payload: Any) -> None:
    path = ensure_runtime_dir() / filename
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
