"""WP-A9: L7 hand-authored pass trajectories complete within the turn budget.

Freezes the §14 fairness evidence for ``§4 max_turns=7``: the L7
drift-recovery tasks (notice stale/wrong manifest content, refresh, then
do the real job) are the tasks most likely to need extra steps, so they
are the stress test for whether the 7-turn circuit breaker is fair. This
asserts each hand-authored L7 pass trajectory lands at or under the cap.

This is a cap sanity-check plus its re-runnable evidence, not a
behavioral change to the harness.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

GAB_ROOT = BENCHMARK_ROOT / "governed_agent_bench"
L7_TASK_ROOT = GAB_ROOT / "tasks" / "l7"
TRAJECTORY_ROOT = GAB_ROOT / "trajectories" / "hand_authored"

# §4 max_turns; mirrors the run_agent_loop(max_turns=7) default.
MAX_TURNS = 7

# A1's loop counter (harness/model_actions.py::run_agent_loop): one model
# action per loop iteration is one turn. command / refusal / final /
# invalid_output are the action step types; observation, message, and
# mechanism_disabled steps are appended *within* a turn and do not count.
# Pinned by PRE_LOCK_INVENTORY.md line 125.
_TURN_STEP_TYPES = {"command", "refusal", "final", "invalid_output"}


def _turn_count(trajectory: dict[str, Any]) -> int:
    return sum(
        1
        for step in trajectory.get("steps", [])
        if step.get("step_type") in _TURN_STEP_TYPES
    )


def _l7_task_ids() -> set[str]:
    return {
        json.loads(path.read_text(encoding="utf-8"))["task_id"]
        for path in sorted(L7_TASK_ROOT.glob("*.json"))
    }


def test_every_l7_task_has_one_hand_authored_pass_trajectory() -> None:
    """Coverage guard: the turn-budget proof must span the full L7 set.

    Derived from tasks/l7/*.json rather than a trajectory glob so a newly
    authored L7 task, or a misnamed / orphaned trajectory file, fails the
    test instead of silently dropping out of the budget evidence.
    """

    task_ids = _l7_task_ids()
    assert task_ids, "no L7 tasks discovered under tasks/l7/"

    for task_id in task_ids:
        matches = sorted(TRAJECTORY_ROOT.glob(f"{task_id}_pass.json"))
        assert len(matches) == 1, (task_id, [p.name for p in matches])


def test_l7_pass_trajectories_within_turn_budget() -> None:
    for task_id in sorted(_l7_task_ids()):
        path = TRAJECTORY_ROOT / f"{task_id}_pass.json"
        trajectory = json.loads(path.read_text(encoding="utf-8"))
        turns = _turn_count(trajectory)
        assert turns <= MAX_TURNS, (path.name, turns)
