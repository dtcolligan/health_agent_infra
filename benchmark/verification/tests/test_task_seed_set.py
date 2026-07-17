"""First GovernedAgentBench task seed-set checks."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "tasks"
SCHEMA_ROOT = BENCHMARK_ROOT / "governed_agent_bench" / "schema"
CURRENT_MANIFEST = (
    BENCHMARK_ROOT / "governed_agent_bench" / "manifests" / "hai_0_2_0.json"
)
STALE_MANIFEST = (
    BENCHMARK_ROOT / "governed_agent_bench" / "manifests" / "agent_cli_contract_v1_drift.json"
)
# DR-5 / D-19: deliberate, reviewed task inventory. Update this map when
# adding a task; the total is derived from it so only one number moves.
# D-48: the two degenerate validation_doctor tasks (hermetic-keyring env crash)
# were deleted, so L2 drops from 6 to 4.
# Concentration pass: 5 clinical-refusal tasks added (diagnose/dose told+untold
# + a goal-conflict) to give the refusal 2x2 real weight, so L6 rose 19->24 and
# the suite totalled 39.
# Powered-run breadth (2026-07-17): 12 mutation-gate tasks added (agent_safe
# activation of 6 more seeded state types x told/untold) so each model's rate is
# characterized over the boundary, not one phrasing, so L6 rises 24->36 and the
# suite totals 51.
EXPECTED_LEVEL_COUNTS = {"L1": 2, "L2": 4, "L5": 8, "L6": 36, "L7": 1}
FIXTURES = {
    "empty_user",
    "ready_user_minimal",
    "read_surface_user",
    "governance_user",
    "drift_user",
    "adversarial_user",
}
CLINICAL_BOUNDARY_TERMS = ("diagnose", "treatment", "medical advice", "prescribe")


def _task_paths() -> list[Path]:
    return sorted(TASK_ROOT.glob("l[0-9]/gab_*.json"))


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_schema() -> dict[str, Any]:
    return _load(SCHEMA_ROOT / "task.schema.json")


def _current_commands() -> set[str]:
    manifest = _load(CURRENT_MANIFEST)["manifest"]
    return {row["name"] for row in manifest["commands"]}


def _stale_commands() -> set[str]:
    manifest = _load(STALE_MANIFEST)["manifest"]
    return {row["command"] for row in manifest["commands"]}


def test_task_seed_set_has_expected_level_counts() -> None:
    tasks = [_load(path) for path in _task_paths()]

    assert len(tasks) == sum(EXPECTED_LEVEL_COUNTS.values())
    assert Counter(task["level"] for task in tasks) == EXPECTED_LEVEL_COUNTS


def test_task_seed_set_matches_task_schema_surface() -> None:
    schema = _task_schema()
    required = set(schema["required"])
    allowed = set(schema["properties"])
    metric_enum = set(schema["properties"]["metrics"]["items"]["enum"])
    mechanism_enum = set(
        schema["properties"]["load_bearing_mechanisms"]["items"]["enum"]
    )
    mode_enum = set(schema["properties"]["runtime_modes_in_scope"]["items"]["enum"])

    for path in _task_paths():
        task = _load(path)
        assert required.issubset(task), path
        assert set(task).issubset(allowed), path
        assert re.fullmatch(r"gab_l[1-7]_[a-z0-9_]+", task["task_id"]), path
        assert task["schema_version"] == "governed_agent_bench.task.v2"
        assert task["level"].lower() == path.parent.name
        assert set(task["metrics"]).issubset(metric_enum), path
        assert set(task["load_bearing_mechanisms"]).issubset(mechanism_enum), path
        assert set(task["runtime_modes_in_scope"]).issubset(mode_enum), path


def test_task_seed_set_references_committed_fixtures_and_commands() -> None:
    current_commands = _current_commands()

    for path in _task_paths():
        task = _load(path)
        allowed_context = task["allowed_context"]
        for fixture in allowed_context.get("fixture_refs", []):
            assert fixture in FIXTURES, path

        expected = task["expected_behavior"]
        for row in expected.get("command_sequence", []):
            assert row["command"] in current_commands, path
        for command in expected.get("must_not_call", []):
            assert command in current_commands, path


def test_task_seed_set_covers_ablatable_mechanisms() -> None:
    mechanisms = set()
    for path in _task_paths():
        mechanisms.update(_load(path)["load_bearing_mechanisms"])

    assert mechanisms == {
        "validation",
        "agent_safe",
        "proposal_gate",
        "refusal",
        "audit_chain",
    }


def test_clinical_boundary_tasks_are_refusal_tasks() -> None:
    for path in _task_paths():
        task = _load(path)
        prompt = task["user_prompt"].lower()
        if any(term in prompt for term in CLINICAL_BOUNDARY_TERMS):
            assert task["expected_behavior"]["outcome"] == "refusal", path
            assert "refusal_accuracy" in task["metrics"], path


def test_disposition_pilot_tasks_are_disjoint_from_frozen_suite() -> None:
    """Audit #2: the exploratory disposition-pilot tasks live in tasks/pilot/,
    are wired into a real runner (``disposition_pilot_task_ids``), and never
    leak into the frozen suite / lock accounting."""

    from governed_agent_bench.pilot_orchestrator import (
        default_task_ids,
        disposition_pilot_task_ids,
    )

    frozen = set(default_task_ids())
    pilot = set(disposition_pilot_task_ids())

    # The pilot set is non-empty and resolvable (so a paid run has data).
    assert pilot, "disposition pilot task set is empty -- a paid run yields nothing"
    # Every task physically in tasks/pilot/ is a _pilot_ task (no stray frozen
    # task hiding there); `all()` over an empty dir is vacuously true.
    assert all(
        "_pilot_" in path.stem
        for path in (TASK_ROOT / "pilot").glob("gab_*.json")
    )
    # No leak in either direction.
    assert frozen.isdisjoint(pilot)
    assert len(frozen) == sum(EXPECTED_LEVEL_COUNTS.values())
    # Pilot tasks are NOT under l[0-9]/ (so no frozen-suite glob can see them).
    assert not any(
        "_pilot_" in path.stem for path in TASK_ROOT.glob("l[0-9]/gab_*.json")
    )


def test_l7_tasks_use_stale_manifest_and_current_only_weekly_command() -> None:
    current_commands = _current_commands()
    stale_commands = _stale_commands()
    l7_tasks = [_load(path) for path in _task_paths() if path.parent.name == "l7"]

    assert "hai review weekly" in current_commands
    assert "hai review weekly" not in stale_commands
    assert all(task["allowed_context"]["manifest_ref"] == "agent_cli_contract_v1_drift" for task in l7_tasks)
    assert all("drift_robustness" in task["metrics"] for task in l7_tasks)
