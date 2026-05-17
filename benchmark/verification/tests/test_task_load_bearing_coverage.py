"""Mechanism-load-bearing coverage + D-17 isolation checks.

Oracle pairs and the isolation verdict live in
``governed_agent_bench.oracles`` (single source, also consumed by the
isolation-matrix generator). This module asserts coverage and that
every oracle pair satisfies the D-17 (mode-aware) isolation criterion.
"""

from __future__ import annotations

import sys
from pathlib import Path


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import load_task  # noqa: E402
from governed_agent_bench.oracles import (  # noqa: E402
    COMPOSITE_OFF_MODE,
    COMPOSITE_PROOF_CASES,
    MECHANISM_OFF_MODES,
    iter_mechanism_cases,
    isolation_verdict,
)


def test_mvp_tasks_declare_every_ablatable_mechanism() -> None:
    declared: dict[str, set[str]] = {
        mechanism: set() for mechanism in MECHANISM_OFF_MODES
    }

    for _mechanism, case in iter_mechanism_cases():
        task = load_task(case["task_id"])
        for mechanism in task["load_bearing_mechanisms"]:
            if mechanism in declared:
                declared[mechanism].add(task["task_id"])

    assert all(declared.values()), declared
    # DR-5 / D-19: >=3 load-bearing tasks per ablatable mechanism.
    for mechanism, task_ids in declared.items():
        assert len(task_ids) >= 3, (mechanism, sorted(task_ids))


def test_load_bearing_mechanisms_have_scored_full_vs_off_deltas() -> None:
    for mechanism, case in iter_mechanism_cases():
        off_mode = MECHANISM_OFF_MODES[mechanism]
        task = load_task(case["task_id"])

        assert mechanism in task["load_bearing_mechanisms"], case["task_id"]
        assert "full_contract" in task["runtime_modes_in_scope"], case["task_id"]
        assert off_mode in task["runtime_modes_in_scope"], case["task_id"]

        verdict = isolation_verdict(case, label=mechanism, off_mode=off_mode)
        assert verdict["isolated"], verdict


def test_composite_no_runtime_enforcement_sanity_floor() -> None:
    assert len(COMPOSITE_PROOF_CASES) >= 2

    for case in COMPOSITE_PROOF_CASES:
        task = load_task(case["task_id"])
        assert "full_contract" in task["runtime_modes_in_scope"], case["task_id"]
        assert COMPOSITE_OFF_MODE in task["runtime_modes_in_scope"], case["task_id"]

        verdict = isolation_verdict(
            case, label="composite", off_mode=COMPOSITE_OFF_MODE
        )
        assert verdict["isolated"], verdict
