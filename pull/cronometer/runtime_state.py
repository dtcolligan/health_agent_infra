from __future__ import annotations

import json
from pathlib import Path


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "runs": [],
            "slice_status": {},
            "day_hashes": {},
            "last_successful_day": None,
            "last_receipt_hash": None,
        }
    return json.loads(path.read_text())


def save_state(path: Path, state: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
    return path
