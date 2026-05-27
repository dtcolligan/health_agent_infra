"""Safety-constrained subset enumeration checks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
GAB_ROOT = BENCHMARK_ROOT / "governed_agent_bench"
SUBSET_PATH = GAB_ROOT / "safety_constrained_subset.json"
TASK_ROOT = GAB_ROOT / "tasks"
SCHEMA_VERSION = "governed_agent_bench.safety_constrained_subset.v1"
SAFETY_CONSTRAINED_MECHANISMS = {"refusal", "agent_safe", "proposal_gate"}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _subset() -> dict[str, Any]:
    return _load_json(SUBSET_PATH)


def _tasks_by_id() -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for path in sorted(TASK_ROOT.glob("l*/*.json")):
        task = _load_json(path)
        tasks[task["task_id"]] = task
    return tasks


def test_subset_tasks_declare_safety_constrained_mechanism() -> None:
    tasks = _tasks_by_id()

    for task_id in _subset()["task_ids"]:
        mechanisms = set(tasks[task_id]["load_bearing_mechanisms"])
        assert mechanisms & SAFETY_CONSTRAINED_MECHANISMS, task_id


def test_tasks_outside_subset_do_not_declare_safety_constrained_mechanism() -> None:
    subset_ids = set(_subset()["task_ids"])

    for task_id, task in _tasks_by_id().items():
        if task_id in subset_ids:
            continue
        mechanisms = set(task["load_bearing_mechanisms"])
        assert not mechanisms & SAFETY_CONSTRAINED_MECHANISMS, task_id


def test_subset_task_ids_exist_on_disk() -> None:
    tasks = _tasks_by_id()

    for task_id in _subset()["task_ids"]:
        assert task_id in tasks


def test_subset_task_count_matches_recorded_count() -> None:
    subset = _subset()

    assert subset["subset_task_count"] == 14
    assert len(subset["task_ids"]) == subset["subset_task_count"]


def test_subset_json_declares_schema_version() -> None:
    assert _subset()["schema_version"] == SCHEMA_VERSION
