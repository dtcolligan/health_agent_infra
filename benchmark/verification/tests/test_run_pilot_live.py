"""Ladder runner / live-pilot script checks (IB-1 phasing, IB-2 selection)."""

from __future__ import annotations

import io
import json
import socket
import sys
import urllib.request
from pathlib import Path
from typing import Any

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.canary_gate import (  # noqa: E402
    OPERATE_TASK_IDS,
    canary_task_ids,
)
from governed_agent_bench.harness.core import HarnessError, load_task  # noqa: E402
from governed_agent_bench.model_roster import load_model_roster  # noqa: E402
from governed_agent_bench.pilot_orchestrator import (  # noqa: E402
    MODE_ORDER,
    default_task_ids,
)
from governed_agent_bench.scripts import run_pilot_live  # noqa: E402


def test_smoke_slice_tasks_resolve_and_exercise_novel_paths() -> None:
    """Readiness SF-5: every smoke task id must resolve via load_task (the
    previous SMOKE_TASK_ID named a deleted task and would crash), be in
    scope at full_contract, and jointly exercise the untold render and
    hide_stdout live paths."""

    tasks = {}
    for task_id in run_pilot_live.SMOKE_TASK_IDS:
        task = load_task(task_id)  # raises HarnessError if missing
        assert "full_contract" in (task.get("runtime_modes_in_scope") or ["full_contract"])
        tasks[task_id] = task
    assert any(t.get("contract_arm") == "untold" for t in tasks.values()), (
        "smoke slice must exercise the untold render live"
    )
    assert any(t.get("hide_stdout") for t in tasks.values()), (
        "smoke slice must exercise hide_stdout live"
    )


def test_old_smoke_task_id_is_gone() -> None:
    with pytest.raises(HarnessError):
        load_task("gab_l1_doctor_status_route")
    assert not hasattr(run_pilot_live, "SMOKE_TASK_ID")


def test_build_smoke_config_is_single_cell_and_isolated(tmp_path: Path) -> None:
    config = run_pilot_live.build_smoke_config(tmp_path)

    assert config.task_ids == run_pilot_live.SMOKE_TASK_IDS
    assert config.mode_order == ("full_contract",)
    assert config.replication_n == 1
    assert config.runs_root == tmp_path / "_smoke"
    assert config.cost_cap_usd == 1.0


def test_ladder_selection_follows_roster_declared_order() -> None:
    roster = load_model_roster()
    # The paid runner's ladder is exactly the run_-prefixed Together
    # conditions (roster_v3 retains superseded conditions for provenance;
    # they must never be executable via --ladder).
    expected = [
        c["condition_id"]
        for c in roster["conditions"]
        if c.get("provider") == "Together AI"
        and str(c["condition_id"]).startswith("run_")
    ]
    assert expected == [
        "run_primary_qwen3_235b",
        "run_capable_llama33_70b",
        "run_nearfloor_qwen35_9b",
        "run_belowfloor_qwen25_7b",
    ]

    resolved = run_pilot_live.resolve_conditions(ladder=True, condition_ids=[])

    assert [c["condition_id"] for c in resolved] == expected
    assert run_pilot_live.PRIMARY_CONDITION_ID in expected
    assert run_pilot_live.DEFAULT_BELOW_FLOOR_CONDITION_ID in expected


def test_condition_id_selection_and_errors() -> None:
    resolved = run_pilot_live.resolve_conditions(
        ladder=False,
        condition_ids=[run_pilot_live.PRIMARY_CONDITION_ID],
    )
    assert [c["condition_id"] for c in resolved] == [
        run_pilot_live.PRIMARY_CONDITION_ID
    ]

    with pytest.raises(KeyError, match="not a Together roster condition"):
        run_pilot_live.resolve_conditions(
            ladder=False, condition_ids=["no_such_condition"]
        )
    # The Anthropic stretch condition is not runnable by this runner.
    with pytest.raises(KeyError, match="not a Together roster condition"):
        run_pilot_live.resolve_conditions(
            ladder=False, condition_ids=["option_c_stretch_claude_sonnet_46"]
        )
    with pytest.raises(ValueError, match="mutually exclusive"):
        run_pilot_live.resolve_conditions(
            ladder=True, condition_ids=[run_pilot_live.PRIMARY_CONDITION_ID]
        )


def test_phase_plans_partition_the_concentrated_sweep() -> None:
    # D-49: phase1 (canary) + phase2 partition the CONCENTRATED paid sweep, not
    # the full committed suite. Tier D scope tasks are covered offline, never
    # paid-swept.
    conditions = run_pilot_live.resolve_conditions(ladder=True, condition_ids=[])
    below_floor = run_pilot_live.DEFAULT_BELOW_FLOOR_CONDITION_ID
    concentrated = set(run_pilot_live.CONCENTRATED_SWEEP_TASK_IDS)
    for condition in conditions:
        p1_tasks, p1_modes = run_pilot_live.phase1_plan(
            condition, below_floor_condition_id=below_floor
        )
        p2_tasks = run_pilot_live.phase2_task_ids(p1_tasks)
        if condition["condition_id"] == below_floor:
            assert p1_tasks == tuple(OPERATE_TASK_IDS)
            assert p1_modes == ("full_contract",)
        else:
            assert p1_tasks == canary_task_ids()
            assert p1_modes == tuple(MODE_ORDER)
        assert set(p1_tasks).isdisjoint(p2_tasks)
        # Every paid task is in the concentrated set; phase1 canary tasks are a
        # concentrated subset, so the union is exactly the concentrated sweep.
        assert set(p1_tasks) <= concentrated
        assert set(p1_tasks) | set(p2_tasks) == concentrated


def test_concentrated_sweep_is_a_valid_headline_mapped_subset() -> None:
    # D-49: the paid selection must (a) exist in the committed suite, (b) put a
    # real off-mode under every Tier-A headline task, (c) exclude the Tier D
    # scope families, and (d) contain the canary + operate control tasks.
    concentrated = run_pilot_live.CONCENTRATED_SWEEP_TASK_IDS
    suite = set(default_task_ids())
    assert set(concentrated) <= suite
    assert len(set(concentrated)) == len(concentrated)  # no dupes

    tier_a = [t for t in concentrated if t.startswith(("gab_l6_agentsafe", "gab_l6_refusal"))]
    for task_id in tier_a:
        modes = run_pilot_live.modes_in_scope(load_task(task_id))
        off_modes = [m for m in modes if m != "full_contract"]
        assert off_modes, f"Tier-A task {task_id} has no off-mode lever: {modes}"

    # Tier D families are demoted to offline scope: never in the paid sweep.
    for task_id in concentrated:
        assert "validation" not in task_id
        assert "proposalgate" not in task_id
        assert "credential" not in task_id
        assert "export" not in task_id

    assert set(canary_task_ids()) <= set(concentrated)
    assert set(OPERATE_TASK_IDS) <= set(concentrated)


def test_wall_cap_warning_is_loud_and_projection_based() -> None:
    condition = run_pilot_live.resolve_conditions(
        ladder=False, condition_ids=[run_pilot_live.PRIMARY_CONDITION_ID]
    )[0]
    tiny = run_pilot_live.apply_wall_override(condition, 1.0)
    stream = io.StringIO()

    warned = run_pilot_live.warn_if_wall_cap_exceeded(
        label="main/test",
        condition=tiny,
        rep_count=100,
        assumed_rep_seconds=90.0,
        stream=stream,
    )

    assert warned is True
    output = stream.getvalue()
    assert "WARNING" in output
    assert "EXCEEDS max_wall_time_minutes" in output
    assert "ESTIMATE" in output

    quiet = io.StringIO()
    assert (
        run_pilot_live.warn_if_wall_cap_exceeded(
            label="main/test",
            condition=condition,  # roster cap: 240 min
            rep_count=10,
            assumed_rep_seconds=60.0,
            stream=quiet,
        )
        is False
    )
    assert quiet.getvalue() == ""


def test_wall_override_does_not_mutate_the_roster_condition() -> None:
    condition = run_pilot_live.resolve_conditions(
        ladder=False, condition_ids=[run_pilot_live.PRIMARY_CONDITION_ID]
    )[0]
    before = json.loads(json.dumps(condition))

    overridden = run_pilot_live.apply_wall_override(condition, 42.0)

    assert overridden["compute_boundary"]["max_wall_time_minutes"] == 42.0
    assert condition == before


def test_dry_run_ladder_makes_no_network_call(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_network(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("dry-run must not touch the network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(urllib.request, "urlopen", fail_network)
    monkeypatch.delenv(run_pilot_live.TOGETHER_API_KEY_ENV, raising=False)

    exit_code = run_pilot_live.main(["--dry-run", "--ladder"])

    assert exit_code == run_pilot_live.EXIT_OK
    output = capsys.readouterr().out
    assert "dry-run: no API call made." in output
    assert "canary phase" in output
    assert "decoding" in output
    assert "cost cap USD" in output
    assert "n=4" in output


def test_dry_run_smoke_prints_slice_without_network(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def fail_network(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("dry-run must not touch the network")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    exit_code = run_pilot_live.main(["--dry-run", "--smoke"])

    assert exit_code == run_pilot_live.EXIT_OK
    output = capsys.readouterr().out
    assert "smoke slice" in output
    assert "gab_l5_audit_blind" in output


def test_bad_condition_id_exits_with_selection_error(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_pilot_live.main(["--dry-run", "--condition-id", "nope"])

    assert exit_code == run_pilot_live.EXIT_BAD_SELECTION
    assert "not a Together roster condition" in capsys.readouterr().err


class _FakeResult:
    def __init__(self, run_dir: Path, run_outcome: str = "completed") -> None:
        self.run_dir = run_dir
        self.run_outcome = run_outcome
        self.latest_advanced = False


def _recording_runner(calls: list[dict[str, Any]]) -> Any:
    def fake_run_pilot(*, systems: list[dict[str, Any]], model_turn_factory: Any, config: Any) -> _FakeResult:
        del model_turn_factory
        run_dir = Path(config.runs_root) / "fake_run"
        run_dir.mkdir(parents=True, exist_ok=True)
        calls.append({
            "condition_id": systems[0]["condition_id"],
            "task_ids": tuple(config.task_ids),
            "mode_order": tuple(config.mode_order),
            "runs_root": Path(config.runs_root),
            "replication_n": config.replication_n,
            "cost_cap_usd": config.cost_cap_usd,
        })
        return _FakeResult(run_dir)

    return fake_run_pilot


def test_run_ladder_is_canary_first_with_gate_then_main(tmp_path: Path) -> None:
    conditions = run_pilot_live.resolve_conditions(ladder=True, condition_ids=[])
    below_floor = run_pilot_live.DEFAULT_BELOW_FLOOR_CONDITION_ID
    calls: list[dict[str, Any]] = []
    gate_calls: list[dict[str, Any]] = []

    def passing_gate(**kwargs: Any) -> dict[str, Any]:
        gate_calls.append(kwargs)
        return {"overall_status": "pass", "components": []}

    exit_code, gate_report = run_pilot_live.run_ladder(
        conditions,
        ladder_root=tmp_path / "ladder",
        below_floor_condition_id=below_floor,
        pilot_runner=_recording_runner(calls),
        gate_evaluator=passing_gate,
    )

    assert exit_code == run_pilot_live.EXIT_OK
    assert gate_report == {"overall_status": "pass", "components": []}
    n = len(conditions)
    canary_calls, main_calls = calls[:n], calls[n:]
    assert len(main_calls) == n
    # Phase 1 runs every model's canary plan before ANY main invocation.
    for call in canary_calls:
        assert call["runs_root"].parts[-2] == "canary"
        if call["condition_id"] == below_floor:
            assert call["task_ids"] == tuple(OPERATE_TASK_IDS)
            assert call["mode_order"] == ("full_contract",)
        else:
            assert call["task_ids"] == canary_task_ids()
    for call in main_calls:
        assert call["runs_root"].parts[-2] == "main"
        assert set(call["task_ids"]).isdisjoint(
            canary_task_ids()
            if call["condition_id"] != below_floor
            else OPERATE_TASK_IDS
        )
        assert call["replication_n"] == 4
    # The gate saw one canary run dir per condition and its report is durable.
    assert len(gate_calls) == 1
    assert set(gate_calls[0]["ladder_run_dirs"]) == {
        c["condition_id"] for c in conditions
    }
    report_path = tmp_path / "ladder" / "canary_gate_report.json"
    assert json.loads(report_path.read_text(encoding="utf-8"))[
        "overall_status"
    ] == "pass"


def test_run_ladder_hard_stops_on_gate_failure(tmp_path: Path) -> None:
    conditions = run_pilot_live.resolve_conditions(ladder=True, condition_ids=[])
    calls: list[dict[str, Any]] = []

    def failing_gate(**_kwargs: Any) -> dict[str, Any]:
        return {
            "overall_status": "fail",
            "components": [
                {"component": "untold_floor", "status": "fail", "detail": "no movement"}
            ],
        }

    exit_code, gate_report = run_pilot_live.run_ladder(
        conditions,
        ladder_root=tmp_path / "ladder",
        below_floor_condition_id=run_pilot_live.DEFAULT_BELOW_FLOOR_CONDITION_ID,
        pilot_runner=_recording_runner(calls),
        gate_evaluator=failing_gate,
    )

    assert exit_code == run_pilot_live.EXIT_CANARY_GATE_FAILED
    assert gate_report is not None and gate_report["overall_status"] == "fail"
    # HARD STOP: only the canary-phase invocations happened.
    assert len(calls) == len(conditions)
    assert all(call["runs_root"].parts[-2] == "canary" for call in calls)
    report_path = tmp_path / "ladder" / "canary_gate_report.json"
    assert report_path.exists()


def _resume_recording_runner(calls: list[dict[str, Any]]) -> Any:
    def fake_run_pilot(*, systems: list[dict[str, Any]], model_turn_factory: Any, config: Any) -> _FakeResult:
        del model_turn_factory
        run_dir = (
            Path(config.resume_run_dir)
            if config.resume_run_dir is not None
            else Path(config.runs_root) / "2026-07-05T1200Z_lock-aaaaaaa"
        )
        run_dir.mkdir(parents=True, exist_ok=True)
        calls.append({
            "condition_id": systems[0]["condition_id"],
            "runs_root": Path(config.runs_root),
            "resume_run_dir": config.resume_run_dir,
        })
        return _FakeResult(run_dir)

    return fake_run_pilot


def test_run_ladder_resume_targets_each_invocations_existing_run_dir(
    tmp_path: Path,
) -> None:
    """IC-2 threading: on --resume each per-condition, per-phase invocation
    resumes ITS OWN previously-created run dir; invocations that never
    started run fresh (resume_run_dir=None)."""

    conditions = run_pilot_live.resolve_conditions(ladder=True, condition_ids=[])
    below_floor = run_pilot_live.DEFAULT_BELOW_FLOOR_CONDITION_ID
    ladder_root = tmp_path / "ladder"
    first_id = str(conditions[0]["condition_id"])
    # Pre-existing canary run dir for the FIRST condition only.
    existing = ladder_root / "canary" / first_id / "2026-07-05T1100Z_lock-bbbbbbb"
    existing.mkdir(parents=True)

    calls: list[dict[str, Any]] = []
    exit_code, _ = run_pilot_live.run_ladder(
        conditions,
        ladder_root=ladder_root,
        below_floor_condition_id=below_floor,
        pilot_runner=_resume_recording_runner(calls),
        gate_evaluator=lambda **_kwargs: {"overall_status": "pass", "components": []},
        resume=True,
    )

    assert exit_code == run_pilot_live.EXIT_OK
    n = len(conditions)
    canary_calls, main_calls = calls[:n], calls[n:]
    by_id = {c["condition_id"]: c for c in canary_calls}
    assert by_id[first_id]["resume_run_dir"] == existing
    for condition_id, call in by_id.items():
        if condition_id != first_id:
            assert call["resume_run_dir"] is None
    # Main phase had no prior run dirs: all fresh.
    assert all(call["resume_run_dir"] is None for call in main_calls)


def test_resumable_run_dir_selection() -> None:
    import tempfile

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        assert run_pilot_live.resumable_run_dir(root / "missing") is None
        assert run_pilot_live.resumable_run_dir(root) is None
        only = root / "2026-07-05T1200Z_lock-aaaaaaa"
        only.mkdir()
        assert run_pilot_live.resumable_run_dir(root) == only
        (root / "2026-07-05T1201Z_lock-aaaaaaa").mkdir()
        with pytest.raises(ValueError, match="multiple run dirs"):
            run_pilot_live.resumable_run_dir(root)


def test_resume_flag_rejects_smoke_and_dry_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = run_pilot_live.main(
        ["--dry-run", "--resume", str(tmp_path)]
    )
    assert exit_code == run_pilot_live.EXIT_BAD_SELECTION
    assert "--resume" in capsys.readouterr().err


def test_capable_movement_pool_excludes_floor_points_and_fails_closed() -> None:
    # F5 (analysis-layer audit): the pooled movement contrasts pool over the
    # CAPABLE models only; a near-floor / below-floor point must be excluded so
    # it cannot dilute the movement and hard-stop the run for a pooling reason.
    ladder = [
        "run_primary_qwen3_235b",
        "run_capable_llama33_70b",
        "run_nearfloor_qwen35_9b",
        "run_belowfloor_qwen25_7b",
    ]
    capable = run_pilot_live.capable_movement_condition_ids(ladder)
    assert capable == ["run_primary_qwen3_235b", "run_capable_llama33_70b"]
    # order and dict inputs both work; a renamed/unknown id is excluded (fails
    # closed) rather than silently pooled in.
    assert run_pilot_live.capable_movement_condition_ids(
        {"run_nearfloor_qwen35_9b": None, "renamed_capable_model": None}
    ) == []


def test_capable_movement_pool_matches_locked_roster_run_ladder() -> None:
    # The prefix heuristic must actually select the capable tier of the real
    # locked roster, not just a hand-built list.
    ids = [c["condition_id"] for c in run_pilot_live.together_ladder_conditions()]
    capable = run_pilot_live.capable_movement_condition_ids(ids)
    assert capable, "roster must expose at least one capable run condition"
    assert all(
        c.startswith(("run_primary", "run_capable")) for c in capable
    )
    assert not any("nearfloor" in c or "belowfloor" in c for c in capable)
