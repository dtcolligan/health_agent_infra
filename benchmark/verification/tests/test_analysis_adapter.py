"""Adapter: powered-run run dirs -> AnalysisRow frame (rep->row provenance)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import pytest

from governed_agent_bench.analysis.adapter import (
    COMPLETED_DISPOSITION,
    INFRA_DROP_DISPOSITIONS,
    CoverageReport,
    MechanismAmbiguityError,
    ScorerPinError,
    build_analysis_rows,
    frame_from_run_dirs,
    rep_admittance,
)
from governed_agent_bench.analysis.frame import AnalysisRow
from governed_agent_bench.results.run_layout import LAYOUT_NESTED, RepRecord
from governed_agent_bench.scorer.core import SCORER_VERSION, scorer_config_hash

# --------------------------------------------------------------------------- #
# Test roster axes + a rep-metrics stub (avoids the scorer/manifest re-score).
# --------------------------------------------------------------------------- #

AXES: dict[str, dict[str, str]] = {
    "cap_v1": {
        "capability_band": "capable",
        "model_family": "qwen3",
        "provider": "Fireworks AI",
        "model_id": "qwen3-32b",
    },
    "weak_v1": {
        "capability_band": "weak",
        "model_family": "qwen3",
        "provider": "Fireworks AI",
        "model_id": "qwen3-8b",
    },
}

# task_id -> (contract_arm, condition, load_bearing_mechanisms)
TASK_SPECS: dict[str, tuple[str, str, list[str]]] = {
    "gab_l6_agentsafe_told": ("told", "base", ["agent_safe"]),
    "gab_l6_agentsafe_untold": ("untold", "base", ["agent_safe"]),
    "gab_l6_agentsafe_conflict": ("told", "goal_conflict", ["agent_safe"]),
    "gab_l6_refusal_told": ("told", "base", ["refusal"]),
    "gab_l6_proposalgate_told": ("told", "base", ["proposal_gate"]),
    "gab_l6_multi": ("told", "base", ["agent_safe", "refusal"]),
}

# (task_id, runtime_mode) -> unsafe_action_rate on each window. 0.0 => safe.
FIRST_ATTEMPT: dict[tuple[str, str], float] = {
    ("gab_l6_agentsafe_told", "no_runtime_enforcement"): 0.0,  # capable/self-enforce path
    ("gab_l6_agentsafe_told", "full_contract"): 0.0,
    ("gab_l6_agentsafe_untold", "no_runtime_enforcement"): 1.0,
    ("gab_l6_agentsafe_conflict", "no_runtime_enforcement"): 1.0,
}


def _rep_metrics_stub(record: RepRecord) -> Mapping[str, Any]:
    arm, condition, mechanisms = TASK_SPECS[record.task_id]
    # Weak model violates the gate in cell B (told + off); capable self-enforces.
    if (record.task_id, record.runtime_mode) in FIRST_ATTEMPT:
        value = FIRST_ATTEMPT[(record.task_id, record.runtime_mode)]
    else:
        value = 0.0
    if record.system_id == "weak_v1" and record.runtime_mode == "no_runtime_enforcement":
        value = 1.0
    refusal_metrics = {"clinical_claim_rate": 0.0, "refusal_accuracy": 1.0}
    metrics = {"unsafe_action_rate": value}
    if "refusal" in mechanisms:
        metrics.update(refusal_metrics)
    return {
        "task_id": record.task_id,
        "system_id": record.system_id,
        "runtime_mode": record.runtime_mode,
        "contract_arm": arm,
        "condition": condition,
        "load_bearing_mechanisms": list(mechanisms),
        "first_attempt": dict(metrics),
        "converged": dict(metrics),
    }


def _record(
    *,
    system_id: str = "cap_v1",
    runtime_mode: str = "no_runtime_enforcement",
    task_id: str = "gab_l6_agentsafe_told",
    disposition: str | None = COMPLETED_DISPOSITION,
    scorer_version: str = SCORER_VERSION,
    config_hash: str | None = None,
    rep_label: str = "rep_01",
) -> RepRecord:
    score = {
        "task_id": task_id,
        "system_id": system_id,
        "runtime_mode": runtime_mode,
        "scorer_version": scorer_version,
        "scorer_config_hash": scorer_config_hash() if config_hash is None else config_hash,
        "model_identity": {"model_id": "provider/" + system_id},
    }
    ledger = None if disposition is None else {
        "system_id": system_id,
        "runtime_mode": runtime_mode,
        "task_id": task_id,
        "rep_label": rep_label,
        "disposition": disposition,
    }
    return RepRecord(
        layout=LAYOUT_NESTED,
        system_id=system_id,
        runtime_mode=runtime_mode,
        task_id=task_id,
        rep_label=rep_label,
        score=score,
        trajectory={},
        ledger=ledger,
        observation_root=Path("."),
        score_path=Path(f"{system_id}/{task_id}/{rep_label}.score.json"),
        task_dir=None,
        mode_dir=None,
        system_dir=None,
    )


# --------------------------------------------------------------------------- #
# F1 + F6 admittance (pure over score + ledger).
# --------------------------------------------------------------------------- #


def test_infra_drop_dispositions_match_orchestrator() -> None:
    # Value-pin: the analysis-layer drop set must equal the orchestrator's
    # reportable stop causes, without importing the heavy orchestrator into the
    # analysis package itself. Imported here (test only) to catch drift.
    from governed_agent_bench.pilot_orchestrator import REPORTABLE_REP_STOP_CAUSES

    assert INFRA_DROP_DISPOSITIONS == frozenset(REPORTABLE_REP_STOP_CAUSES)


def test_admittance_completed() -> None:
    assert rep_admittance(_record(disposition="completed")) == (True, None)


@pytest.mark.parametrize("disposition", sorted(INFRA_DROP_DISPOSITIONS))
def test_admittance_infra_drop(disposition: str) -> None:
    admit, reason = rep_admittance(_record(disposition=disposition))
    assert admit is False
    assert reason == f"disposition:{disposition}"


@pytest.mark.parametrize("disposition", ["wall_halt", "cost_halt", "adapter_halt"])
def test_admittance_incomplete_drop(disposition: str) -> None:
    admit, reason = rep_admittance(_record(disposition=disposition))
    assert admit is False
    assert reason == f"disposition:{disposition}"


def test_admittance_scorer_version_mismatch_raises() -> None:
    with pytest.raises(ScorerPinError, match="must not mix scorer versions"):
        rep_admittance(_record(scorer_version="governed_agent_bench.scorer.OTHER"))


def test_admittance_scorer_hash_mismatch_raises() -> None:
    with pytest.raises(ScorerPinError):
        rep_admittance(_record(config_hash="deadbeef"))


def test_admittance_flat_layout_no_ledger_admits() -> None:
    assert rep_admittance(_record(disposition=None)) == (True, None)


# --------------------------------------------------------------------------- #
# Row construction via build_analysis_rows with an on-disk nested fixture.
# --------------------------------------------------------------------------- #


def _write_nested_fixture(
    root: Path,
    reps: list[dict[str, Any]],
) -> Path:
    """Write a minimal valid nested run dir load_rep_records can walk.

    Each rep dict: {system_id, runtime_mode, task_id, rep_label, disposition,
    scorer_version?, config_hash?}. Content of metrics/steps is irrelevant here
    because the row builder uses an injected rep_metrics_fn stub; only the
    cross-artifact identity fields and the disposition matter.
    """

    run_dir = root / "run"
    for rep in reps:
        sid = rep["system_id"]
        mode = rep["runtime_mode"]
        task = rep["task_id"]
        label = rep["rep_label"]
        traj_id = f"{task}_{sid}_{label}"
        task_dir = (
            run_dir / "conditions" / sid / f"runtime_mode_{mode}" / "tasks" / task
        )
        task_dir.mkdir(parents=True, exist_ok=True)
        score = {
            "task_id": task,
            "trajectory_id": traj_id,
            "system_id": sid,
            "runtime_mode": mode,
            "model_class": "cloud",
            "manifest_version": "hai_0_2_0",
            "scorer_version": rep.get("scorer_version", SCORER_VERSION),
            "scorer_config_hash": rep.get("config_hash", scorer_config_hash()),
            "overall_pass": True,
            "metrics": {},
            "model_identity": {"model_id": "provider/" + sid},
        }
        trajectory = {
            "trajectory_id": traj_id,
            "task_id": task,
            "system_id": sid,
            "runtime_mode": mode,
            "model_class": "cloud",
            "manifest_snapshot_id": "hai_0_2_0",
            "steps": [],
        }
        ledger = {
            "system_id": sid,
            "runtime_mode": mode,
            "task_id": task,
            "rep_label": label,
            "disposition": rep["disposition"],
        }
        (task_dir / f"{label}.score.json").write_text(json.dumps(score))
        (task_dir / f"{label}.trajectory.json").write_text(json.dumps(trajectory))
        (task_dir / f"{label}.ledger.json").write_text(json.dumps(ledger))
        (task_dir / f"{label}.done").write_text("")
    return run_dir


def test_build_rows_capability_crossover_and_coverage(tmp_path: Path) -> None:
    # A within-family pair: capable told/off self-enforces (safe), weak told/off
    # violates (unsafe); plus a full_contract enforced anchor for each.
    reps = [
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
        {"system_id": "weak_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
        {"system_id": "cap_v1", "runtime_mode": "full_contract",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
        # Excluded reps, one per reason slug:
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_conflict", "rep_label": "rep_01",
         "disposition": "completed"},  # condition_filtered:goal_conflict
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_refusal_told", "rep_label": "rep_01",
         "disposition": "completed"},  # mechanism_filtered:refusal
        {"system_id": "cap_v1", "runtime_mode": "full_contract",
         "task_id": "gab_l6_proposalgate_told", "rep_label": "rep_01",
         "disposition": "completed"},  # no_scored_mechanism
        {"system_id": "weak_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_02",
         "disposition": "length_truncation"},  # disposition:length_truncation
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    rows, cov = build_analysis_rows(
        [run_dir], axes=AXES, rep_metrics_fn=_rep_metrics_stub
    )

    assert cov.included == 3
    assert cov.excluded == {
        "condition_filtered:goal_conflict": 1,
        "mechanism_filtered:refusal": 1,
        "no_scored_mechanism": 1,
        "disposition:length_truncation": 1,
    }

    by_key = {(r.model_id, r.cell): r for r in rows}
    assert by_key[("qwen3-32b", "B")].safe is True   # capable self-enforces
    assert by_key[("qwen3-8b", "B")].safe is False    # weak violates
    assert by_key[("qwen3-32b", "A")].enforced is True
    cap_b = by_key[("qwen3-32b", "B")]
    assert cap_b.told is True and cap_b.enforced is False
    assert cap_b.model_family == "qwen3" and cap_b.provider == "Fireworks AI"
    assert cap_b.scenario_id == "gab_l6_agentsafe"  # arm suffix stripped


def test_untold_rep_is_cell_d(tmp_path: Path) -> None:
    reps = [
        {"system_id": "weak_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_untold", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    rows, _ = build_analysis_rows(
        [run_dir], axes=AXES, rep_metrics_fn=_rep_metrics_stub
    )
    assert len(rows) == 1
    assert rows[0].told is False and rows[0].enforced is False
    assert rows[0].cell == "D"


def test_not_in_2x2_cell_when_mode_is_neither_column(tmp_path: Path) -> None:
    # agent_safe's off-mode is no_runtime_enforcement; a no_refusal rep is neither
    # the enforced column nor the mutation gate's off column -> excluded.
    reps = [
        {"system_id": "cap_v1", "runtime_mode": "no_refusal",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    rows, cov = build_analysis_rows(
        [run_dir], axes=AXES, rep_metrics_fn=_rep_metrics_stub
    )
    assert rows == []
    assert cov.excluded == {"not_in_2x2_cell": 1}


def test_converged_window_can_differ_from_first_attempt(tmp_path: Path) -> None:
    def stub(record: RepRecord) -> Mapping[str, Any]:
        base = dict(_rep_metrics_stub(record))
        base["first_attempt"] = {"unsafe_action_rate": 1.0}  # violated first
        base["converged"] = {"unsafe_action_rate": 0.0}      # reverted later
        return base

    reps = [
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    first, _ = build_analysis_rows(
        [run_dir], axes=AXES, rep_metrics_fn=stub, window="first_attempt"
    )
    conv, _ = build_analysis_rows(
        [run_dir], axes=AXES, rep_metrics_fn=stub, window="converged"
    )
    assert first[0].safe is False   # first-attempt sees the violation (headline)
    assert conv[0].safe is True     # converged credits the late revert


def test_multi_mechanism_task_raises(tmp_path: Path) -> None:
    reps = [
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_multi", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    with pytest.raises(MechanismAmbiguityError):
        build_analysis_rows(
            [run_dir], axes=AXES, mechanisms=None, rep_metrics_fn=_rep_metrics_stub
        )


def test_unknown_system_id_raises(tmp_path: Path) -> None:
    reps = [
        {"system_id": "ghost_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    with pytest.raises(KeyError, match="not in the powered-run roster"):
        build_analysis_rows([run_dir], axes=AXES, rep_metrics_fn=_rep_metrics_stub)


def test_frame_two_bands_for_one_model_is_hard_error(tmp_path: Path) -> None:
    # A single model_id in two capability bands is a mislabelled roster row and
    # must fail (frame._validate_rows), not silently corrupt the band contrast.
    bad_axes = {
        "cap_v1": {**AXES["cap_v1"], "model_id": "collide"},
        "weak_v1": {**AXES["weak_v1"], "model_id": "collide"},
    }
    reps = [
        {"system_id": "cap_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
        {"system_id": "weak_v1", "runtime_mode": "no_runtime_enforcement",
         "task_id": "gab_l6_agentsafe_told", "rep_label": "rep_01",
         "disposition": "completed"},
    ]
    run_dir = _write_nested_fixture(tmp_path, reps)
    with pytest.raises(ValueError, match="two capability bands"):
        frame_from_run_dirs([run_dir], axes=bad_axes,
                            rep_metrics_fn=_rep_metrics_stub)


def test_coverage_report_serialises() -> None:
    cov = CoverageReport(
        included=3,
        excluded={"disposition:length_truncation": 1},
        scorer_version=SCORER_VERSION,
        scorer_config_hash=scorer_config_hash(),
        run_dirs=("a", "b"),
    )
    payload = cov.as_dict()
    assert payload["included"] == 3
    assert payload["excluded_total"] == 1
    assert payload["scorer_version"] == SCORER_VERSION
