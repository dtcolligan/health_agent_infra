"""Fixture-liveness guard: for every fixture whose enforce lever is a
synthesis-under-mode rejection (pending_synthesis + synthesis_may_reject), the
2x2 cell must be NON-degenerate -- the constraint action is genuinely REJECTED
under full_contract and ACCEPTED under the off mode. A cell where both arms
produce the same state (the degeneracy class the instrument audit found) is a
hard test failure, so it can never silently ship again.
"""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

import pytest

BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.baselines.rule_baseline import fixture_for_task  # noqa: E402


# (fixture_id, off_mode) whose enforce lever is a synthesis-under-mode rejection.
_ENFORCE_LEVER_FIXTURES = [
    ("adversarial_user", "no_refusal"),        # M7 clinical-boundary refusal
    ("validation_pending_user", "no_validation"),  # M4 recommendation validation
]


def _plan_count(root: Path, for_date: str = "2026-05-03") -> int:
    db = sqlite3.connect(str(root / "state.db"))
    try:
        return db.execute(
            "select count(*) from daily_plan where for_date = ?", (for_date,)
        ).fetchone()[0]
    finally:
        db.close()


@pytest.mark.parametrize("fixture_id,off_mode", _ENFORCE_LEVER_FIXTURES)
def test_enforce_lever_is_non_degenerate(fixture_id: str, off_mode: str) -> None:
    task = {"allowed_context": {"fixture_refs": [fixture_id]}}
    for_date = "2026-05-05" if fixture_id == "adversarial_user" else "2026-05-03"

    ws_on = Path(tempfile.mkdtemp())
    on = fixture_for_task(
        task, fixture_workspace=ws_on, python_executable=sys.executable,
        runtime_mode="full_contract",
    )
    ws_off = Path(tempfile.mkdtemp())
    off = fixture_for_task(
        task, fixture_workspace=ws_off, python_executable=sys.executable,
        runtime_mode=off_mode,
    )

    on_plans = _plan_count(on, for_date)
    off_plans = _plan_count(off, for_date)

    # full_contract REJECTS the constraint-violating recommendation -> no plan.
    assert on_plans == 0, (
        f"{fixture_id}: full_contract should REJECT (0 plans), got {on_plans}"
    )
    # the off mode ACCEPTS it -> a plan is written.
    assert off_plans == 1, (
        f"{fixture_id}/{off_mode}: off mode should ACCEPT (1 plan), got {off_plans}"
    )
    # and the two arms MUST diverge (the whole point of a non-degenerate cell).
    assert on_plans != off_plans
