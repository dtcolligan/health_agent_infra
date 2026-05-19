"""Helpers for the committed GovernedAgentBench model roster."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parent
MODEL_ROSTER_PATH = BENCHMARK_ROOT / "model_roster.md"
_JSON_BLOCK_RE = re.compile(r"```json\n(.*?)\n```", re.DOTALL)


def model_roster_hash(path: Path = MODEL_ROSTER_PATH) -> str:
    """Return the SHA-256 hash of the roster markdown bytes."""

    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_model_roster(path: Path = MODEL_ROSTER_PATH) -> dict[str, Any]:
    """Load the machine-readable JSON block from model_roster.md."""

    text = path.read_text(encoding="utf-8")
    match = _JSON_BLOCK_RE.search(text)
    if match is None:
        raise ValueError(f"{path} has no fenced json roster block")
    payload = json.loads(match.group(1))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} roster block must be a JSON object")
    return payload


def roster_condition(condition_id: str, *, path: Path = MODEL_ROSTER_PATH) -> dict[str, Any]:
    """Return one predeclared roster condition by id."""

    roster = load_model_roster(path)
    for condition in roster.get("conditions", []):
        if condition.get("condition_id") == condition_id:
            return condition
    raise KeyError(f"model roster condition not found: {condition_id}")
