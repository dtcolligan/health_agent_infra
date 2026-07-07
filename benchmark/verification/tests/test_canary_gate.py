"""Canary-gate evaluation checks (IB-1, locked decision 9)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.canary_gate import (  # noqa: E402
    BLIND_TWIN_BLIND_TASK_ID,
    BLIND_TWIN_SIGHTED_TASK_ID,
    OPERATE_TASK_IDS,
    UNTOLD_FLOOR_TASK_IDS,
    canary_task_ids,
    evaluate_canary_gate,
)


LADDER_MODEL = "primary_qwen3_235b_together"
LADDER_SYSTEM = "primary_qwen3_235b_together_v1"
BELOW_FLOOR = "option_b_qwen25_7b_together"
BELOW_FLOOR_SYSTEM = "option_b_qwen25_7b_together_v1"


def _write_rep(
    run_dir: Path,
    *,
    system_id: str,
    mode: str,
    task_id: str,
    rep: int,
    overall_pass: bool | None,
) -> None:
    """Write a ledger (always) and, unless partial, a score for one rep.

    ``overall_pass=None`` synthesizes an unscored partial rep (ledger only),
    e.g. a context_overflow.
    """

    task_dir = (
        run_dir / "conditions" / system_id / f"runtime_mode_{mode}" / "tasks" / task_id
    )
    task_dir.mkdir(parents=True, exist_ok=True)
    label = f"rep_{rep + 1:02d}"
    (task_dir / f"{label}.ledger.json").write_text(
        json.dumps({"disposition": "completed" if overall_pass is not None else "context_overflow"}),
        encoding="utf-8",
    )
    if overall_pass is not None:
        (task_dir / f"{label}.score.json").write_text(
            json.dumps({"overall_pass": overall_pass}),
            encoding="utf-8",
        )


def _seed_ladder_canary_run(
    run_dir: Path,
    *,
    enforced_pass: bool,
    unenforced_pass: bool,
    told_pass: bool,
    blind_pass: bool,
    reps: int = 2,
) -> None:
    """Seed a ladder model's canary run dir with uniform outcomes."""

    untold_unenforced_modes = {
        "gab_l6_agentsafe_untold": ("no_runtime_enforcement",),
    }
    for rep in range(reps):
        for task_id in UNTOLD_FLOOR_TASK_IDS:
            _write_rep(
                run_dir,
                system_id=LADDER_SYSTEM,
                mode="full_contract",
                task_id=task_id,
                rep=rep,
                overall_pass=enforced_pass,
            )
            for mode in untold_unenforced_modes[task_id]:
                _write_rep(
                    run_dir,
                    system_id=LADDER_SYSTEM,
                    mode=mode,
                    task_id=task_id,
                    rep=rep,
                    overall_pass=unenforced_pass,
                )
        _write_rep(
            run_dir,
            system_id=LADDER_SYSTEM,
            mode="full_contract",
            task_id=BLIND_TWIN_SIGHTED_TASK_ID,
            rep=rep,
            overall_pass=told_pass,
        )
        _write_rep(
            run_dir,
            system_id=LADDER_SYSTEM,
            mode="full_contract",
            task_id=BLIND_TWIN_BLIND_TASK_ID,
            rep=rep,
            overall_pass=blind_pass,
        )


def _seed_below_floor_run(
    run_dir: Path,
    *,
    operate_passes: int,
    operate_fails: int,
    unscored_partials: int = 0,
) -> None:
    rep = 0
    for task_id in OPERATE_TASK_IDS:
        for _ in range(operate_passes):
            _write_rep(
                run_dir,
                system_id=BELOW_FLOOR_SYSTEM,
                mode="full_contract",
                task_id=task_id,
                rep=rep,
                overall_pass=True,
            )
            rep += 1
        for _ in range(operate_fails):
            _write_rep(
                run_dir,
                system_id=BELOW_FLOOR_SYSTEM,
                mode="full_contract",
                task_id=task_id,
                rep=rep,
                overall_pass=False,
            )
            rep += 1
        for _ in range(unscored_partials):
            _write_rep(
                run_dir,
                system_id=BELOW_FLOOR_SYSTEM,
                mode="full_contract",
                task_id=task_id,
                rep=rep,
                overall_pass=None,
            )
            rep += 1


def _component(report: dict[str, Any], name: str) -> dict[str, Any]:
    return next(c for c in report["components"] if c["component"] == name)


def test_canary_task_ids_are_tag_derived_and_exactly_the_locked_set() -> None:
    # D-48: the canary set is the blind twin (sighted + blind) plus the
    # mutation-gate untold floor. proposalgate_untold was retired (folded into
    # the mutation gate, isolable only at the all-off floor).
    assert set(canary_task_ids()) == {
        "gab_l5_audit_blind",
        "gab_l5_audit_told",
        "gab_l6_agentsafe_untold",
    }


def test_gate_passes_on_clear_movement_and_inoperative_control(
    tmp_path: Path,
) -> None:
    ladder_dir = tmp_path / "canary" / LADDER_MODEL
    _seed_ladder_canary_run(
        ladder_dir,
        enforced_pass=True,
        unenforced_pass=False,
        told_pass=True,
        blind_pass=False,
    )
    floor_dir = tmp_path / "canary" / BELOW_FLOOR
    _seed_below_floor_run(floor_dir, operate_passes=0, operate_fails=2)

    report = evaluate_canary_gate(
        ladder_run_dirs={LADDER_MODEL: ladder_dir, BELOW_FLOOR: floor_dir},
        below_floor_condition_id=BELOW_FLOOR,
    )

    assert report["overall_status"] == "pass"
    untold = _component(report, "untold_floor")
    assert untold["status"] == "pass"
    assert untold["movement"] == 1.0
    assert untold["enforced_full_contract"]["scored"] == 2
    assert untold["unenforced_modes"]["scored"] == 2
    twin = _component(report, "blind_twin")
    assert twin["status"] == "pass"
    assert twin["movement"] == 1.0
    floor = _component(report, "below_floor_operate")
    assert floor["status"] == "pass"
    assert floor["operate_rate_over_attempted"] == 0.0


def test_gate_fails_when_untold_floor_does_not_move(tmp_path: Path) -> None:
    ladder_dir = tmp_path / "canary" / LADDER_MODEL
    # Enforcement changes nothing: same pass rate in both arms.
    _seed_ladder_canary_run(
        ladder_dir,
        enforced_pass=True,
        unenforced_pass=True,
        told_pass=True,
        blind_pass=False,
    )
    floor_dir = tmp_path / "canary" / BELOW_FLOOR
    _seed_below_floor_run(floor_dir, operate_passes=0, operate_fails=2)

    report = evaluate_canary_gate(
        ladder_run_dirs={LADDER_MODEL: ladder_dir, BELOW_FLOOR: floor_dir},
        below_floor_condition_id=BELOW_FLOOR,
    )

    assert _component(report, "untold_floor")["status"] == "fail"
    assert _component(report, "untold_floor")["movement"] == 0.0
    assert report["overall_status"] == "fail"


def test_gate_fails_when_below_floor_control_operates(tmp_path: Path) -> None:
    ladder_dir = tmp_path / "canary" / LADDER_MODEL
    _seed_ladder_canary_run(
        ladder_dir,
        enforced_pass=True,
        unenforced_pass=False,
        told_pass=True,
        blind_pass=False,
    )
    floor_dir = tmp_path / "canary" / BELOW_FLOOR
    # The "below-floor" model actually operates: gate must fail.
    _seed_below_floor_run(floor_dir, operate_passes=2, operate_fails=0)

    report = evaluate_canary_gate(
        ladder_run_dirs={LADDER_MODEL: ladder_dir, BELOW_FLOOR: floor_dir},
        below_floor_condition_id=BELOW_FLOOR,
    )

    floor = _component(report, "below_floor_operate")
    assert floor["status"] == "fail"
    assert floor["operate_rate_over_attempted"] == 1.0
    assert report["overall_status"] == "fail"


def test_unscored_partials_count_against_operate_but_not_contrasts(
    tmp_path: Path,
) -> None:
    """A context_overflow (ledger, no score) is a failure to operate for the
    below-floor control (attempted denominator) but never fabricates a
    scored data point in the movement contrasts."""

    ladder_dir = tmp_path / "canary" / LADDER_MODEL
    _seed_ladder_canary_run(
        ladder_dir,
        enforced_pass=True,
        unenforced_pass=False,
        told_pass=True,
        blind_pass=False,
    )
    # Extra unscored partial rep on a contrast cell: reported, not pooled.
    _write_rep(
        ladder_dir,
        system_id=LADDER_SYSTEM,
        mode="full_contract",
        task_id=BLIND_TWIN_SIGHTED_TASK_ID,
        rep=7,
        overall_pass=None,
    )
    floor_dir = tmp_path / "canary" / BELOW_FLOOR
    # One scored pass + three overflow partials: 1/4 attempted = 0.25 < 0.5.
    _seed_below_floor_run(
        floor_dir, operate_passes=1, operate_fails=0, unscored_partials=3
    )

    report = evaluate_canary_gate(
        ladder_run_dirs={LADDER_MODEL: ladder_dir, BELOW_FLOOR: floor_dir},
        below_floor_condition_id=BELOW_FLOOR,
    )

    twin = _component(report, "blind_twin")
    assert twin["sighted_told"]["scored"] == 2
    assert twin["sighted_told"]["unscored_partial"] == 1
    assert twin["movement"] == 1.0
    floor = _component(report, "below_floor_operate")
    assert floor["attempted"] == 8  # (1 pass + 3 partials) x 2 operate tasks
    assert floor["operate_rate_over_attempted"] == 0.25
    assert floor["status"] == "pass"
    assert report["overall_status"] == "pass"


def test_gate_fails_closed_on_missing_below_floor_run_dir(tmp_path: Path) -> None:
    ladder_dir = tmp_path / "canary" / LADDER_MODEL
    _seed_ladder_canary_run(
        ladder_dir,
        enforced_pass=True,
        unenforced_pass=False,
        told_pass=True,
        blind_pass=False,
    )

    report = evaluate_canary_gate(
        ladder_run_dirs={LADDER_MODEL: ladder_dir},
        below_floor_condition_id=BELOW_FLOOR,
    )

    assert _component(report, "below_floor_operate")["status"] == "fail"
    assert report["overall_status"] == "fail"


def test_gate_fails_closed_on_empty_run_dirs(tmp_path: Path) -> None:
    """No scored reps at all -> every component fails; the gate never passes
    on vacuous data."""

    report = evaluate_canary_gate(
        ladder_run_dirs={
            LADDER_MODEL: tmp_path / "empty_a",
            BELOW_FLOOR: tmp_path / "empty_b",
        },
        below_floor_condition_id=BELOW_FLOOR,
    )

    assert report["overall_status"] == "fail"
    for component in report["components"]:
        assert component["status"] == "fail"
