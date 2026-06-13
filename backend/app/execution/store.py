"""Live strategy deployment store."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..config import settings


def _store_path() -> Path:
    p = Path(settings.LIVE_STRATEGIES_FILE)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_all() -> dict[str, dict]:
    path = _store_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_all(strategies: dict[str, dict]) -> None:
    _store_path().write_text(json.dumps(strategies, indent=2, default=str), encoding="utf-8")


def get(strategy_id: str) -> dict | None:
    return load_all().get(strategy_id)


def upsert(strategy_id: str, record: dict) -> dict:
    all_s = load_all()
    all_s[strategy_id] = record
    save_all(all_s)
    return record


def delete(strategy_id: str) -> bool:
    all_s = load_all()
    if strategy_id not in all_s:
        return False
    del all_s[strategy_id]
    save_all(all_s)
    return True
