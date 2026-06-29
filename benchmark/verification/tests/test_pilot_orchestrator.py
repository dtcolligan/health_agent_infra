"""Pilot orchestrator state-machine and artifact contract checks."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import urllib.request
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench import pilot_orchestrator as pilot  # noqa: E402
from governed_agent_bench.harness.model_actions import ModelTurnResult  # noqa: E402
import governed_agent_bench.harness.core as harness_core  # noqa: E402
from governed_agent_bench.model_roster import roster_condition  # noqa: E402


GIT_SHA = "a" * 40
RUN_START = datetime(2026, 7, 15, 14, 30, tzinfo=timezone.utc)


def _condition(**overrides: Any) -> dict[str, Any]:
    condition = dict(roster_condition("option_b_qwen25_7b_together"))
    condition.update(overrides)
    if "compute_boundary" in overrides:
        condition["compute_boundary"] = overrides["compute_boundary"]
    return condition


def _config(tmp_path: Path, *, task_ids: tuple[str, ...] = ("gab_l1_capabilities_route",), **overrides: Any) -> pilot.PilotConfig:
    base = dict(
        runs_root=tmp_path / "runs",
        task_ids=task_ids,
        mode_order=("full_contract",),
        replication_n=1,
        cost_cap_usd=100.0,
        python_executable=sys.executable,
    )
    base.update(overrides)
    return pilot.PilotConfig(**base)


def _command_response(command: str = "hai capabilities", *, cost: Any = 0.0) -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": command,
            "args": {"--json": True} if command == "hai capabilities" else {},
            "reason": "Inspect the command surface.",
        }),
        cost_usd_estimate=cost,
        wall_time_ms=1,
    )


def _final_response(text: str = "Done.", *, cost: Any = 0.0) -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "final",
            "final_text": text,
            "reason": "No further action is needed.",
        }),
        cost_usd_estimate=cost,
        wall_time_ms=1,
    )


def _refusal_response(reason: str = "I cannot provide diagnosis or treatment.") -> ModelTurnResult:
    return ModelTurnResult(
        text=json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "refusal",
            "reason": reason,
        }),
        cost_usd_estimate=0.0,
        wall_time_ms=1,
    )


def _retry_exhausted_response() -> ModelTurnResult:
    return ModelTurnResult(text="__GAB_RETRY_EXHAUSTED__: timeout", retry_count=3)


def _together_response(content: str) -> dict[str, Any]:
    return {
        "choices": [{
            "finish_reason": "stop",
            "message": {"content": content},
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }


def _factory(
    scripts: list[list[ModelTurnResult]],
    *,
    calls: list[tuple[str, str, int]] | None = None,
    on_factory: Callable[[Any], None] | None = None,
) -> Any:
    queue = [list(script) for script in scripts]

    def factory(
        task: dict[str, Any],
        _system: dict[str, Any],
        mode: str,
        rep: int,
        *,
        detector: Any,
    ) -> Any:
        if calls is not None:
            calls.append((task["task_id"], mode, rep))
        if on_factory is not None:
            on_factory(detector)
        responses = queue.pop(0)

        def model_turn(_messages: list[dict[str, str]]) -> ModelTurnResult:
            if not responses:
                raise RuntimeError("script exhausted")
            return responses.pop(0)

        return model_turn

    return factory


def _patch_hai(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int = 0,
    stdout: str = "{\"ok\": true}",
    stderr: str = "",
) -> None:
    def fake_run_hai(
        _action: dict[str, Any],
        _config: Any,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["hai"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(harness_core, "_run_hai", fake_run_hai)


def _run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    scripts: list[list[ModelTurnResult]],
    *,
    config: pilot.PilotConfig | None = None,
    condition: dict[str, Any] | None = None,
    calls: list[tuple[str, str, int]] | None = None,
    on_factory: Callable[[Any], None] | None = None,
) -> pilot.PilotResult:
    _patch_hai(monkeypatch)
    return pilot.run_pilot(
        systems=[condition or _condition()],
        model_turn_factory=_factory(scripts, calls=calls, on_factory=on_factory),
        config=config or _config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )


def _task_dir(result: pilot.PilotResult, task_id: str = "gab_l1_capabilities_route") -> Path:
    return (
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "tasks"
        / task_id
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _schema(name: str) -> dict[str, Any]:
    return _read_json(BENCHMARK_ROOT / "governed_agent_bench" / "schema" / name)


def _assert_schema_accepts(schema: dict[str, Any], value: Any) -> None:
    def validate(node: dict[str, Any], instance: Any, path: str) -> None:
        if "$ref" in node:
            ref = str(node["$ref"])
            assert ref.startswith("#/$defs/"), ref
            validate(schema["$defs"][ref.removeprefix("#/$defs/")], instance, path)
            return
        if "anyOf" in node:
            errors = []
            for option in node["anyOf"]:
                try:
                    validate(option, instance, path)
                    return
                except AssertionError as exc:
                    errors.append(str(exc))
            raise AssertionError(f"{path} matched no anyOf branch: {errors}")
        if "const" in node:
            assert instance == node["const"], path
        if "enum" in node:
            assert instance in node["enum"], path
        if "type" in node:
            allowed = node["type"]
            if isinstance(allowed, str):
                allowed = [allowed]
            assert any(_json_type_matches(instance, type_name) for type_name in allowed), (
                path,
                allowed,
                instance,
            )
        if "pattern" in node and isinstance(instance, str):
            assert re.fullmatch(str(node["pattern"]), instance), path
        if "minLength" in node and isinstance(instance, str):
            assert len(instance) >= int(node["minLength"]), path
        if "minimum" in node and isinstance(instance, (int, float)) and not isinstance(instance, bool):
            assert instance >= node["minimum"], path
        if "minItems" in node and isinstance(instance, list):
            assert len(instance) >= int(node["minItems"]), path
        if "minProperties" in node and isinstance(instance, dict):
            assert len(instance) >= int(node["minProperties"]), path
        if isinstance(instance, dict):
            required = set(node.get("required", []))
            assert required <= set(instance), (path, required - set(instance))
            properties = node.get("properties", {})
            if node.get("additionalProperties") is False:
                assert set(instance) <= set(properties), (path, set(instance) - set(properties))
            for key, child in properties.items():
                if key in instance:
                    validate(child, instance[key], f"{path}.{key}")
            additional = node.get("additionalProperties")
            if isinstance(additional, dict):
                for key, child_instance in instance.items():
                    if key not in properties:
                        validate(additional, child_instance, f"{path}.{key}")
        if isinstance(instance, list) and isinstance(node.get("items"), dict):
            for index, item in enumerate(instance):
                validate(node["items"], item, f"{path}[{index}]")

    validate(schema, value, "$")


def _json_type_matches(value: Any, type_name: str) -> bool:
    if type_name == "null":
        return value is None
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    raise AssertionError(f"unsupported schema type {type_name!r}")


def _assert_orchestrator_schemas_valid(result: pilot.PilotResult) -> None:
    ledger_schema = _schema("rep_ledger.schema.json")
    summary_schema = _schema("condition_summary.schema.json")
    index_schema = _schema("condition_index.schema.json")
    manifest_schema = _schema("pilot_manifest.schema.json")
    for ledger_path in result.run_dir.glob("conditions/*/runtime_mode_*/tasks/*/rep_*.ledger.json"):
        _assert_schema_accepts(ledger_schema, _read_json(ledger_path))
    for summary_path in result.run_dir.glob("conditions/*/runtime_mode_*/condition_summary.json"):
        _assert_schema_accepts(summary_schema, _read_json(summary_path))
    for index_path in result.run_dir.glob("conditions/*/condition_index.json"):
        _assert_schema_accepts(index_schema, _read_json(index_path))
    _assert_schema_accepts(manifest_schema, _read_json(result.run_dir / "pilot_manifest.json"))


def test_public_state_machine_interfaces_are_total() -> None:
    assert pilot.run_outcome_of(None) == "completed"
    assert pilot.run_outcome_of(pilot.Disposition("continue")) == "completed"
    assert pilot.run_outcome_of(pilot.Disposition("pause", "provider_outage")) == "halted"
    assert pilot.run_outcome_of(pilot.Disposition("halt", "cost_halt")) == "halted"
    assert pilot.run_outcome_of(pilot.Disposition("abort", "clinical_claim")) == "aborted"

    assert pilot.resolve(None, None) is None
    halt = pilot.Disposition("halt", "cost_halt")
    pause = pilot.Disposition("pause", "provider_outage")
    abort_low = pilot.Disposition("abort", "clinical_claim")
    abort_high = pilot.Disposition("abort", "full_contract_breach")
    assert pilot.resolve(halt, None) == halt
    assert pilot.resolve(pause, halt) == halt
    assert pilot.resolve(halt, pause) == halt
    assert pilot.resolve(abort_low, halt) == abort_low
    assert pilot.resolve(abort_low, abort_high) == abort_high
    assert pilot.resolve(halt, pilot.Disposition("halt", "wall_halt")) == halt


def test_clean_run_writes_completed_artifacts_manifest_and_latest(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(), _final_response()]],
    )

    assert result.run_outcome == "completed"
    assert result.latest_advanced is True
    assert (tmp_path / "runs" / "latest").is_symlink()
    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.trajectory.json").exists()
    assert (task_dir / "rep_01.ledger.json").exists()
    assert (task_dir / "rep_01.score.json").exists()
    assert (task_dir / "rep_01.done").read_bytes() == b""
    assert (task_dir / "observations").is_dir()
    assert list((task_dir / "observations").glob("*_stdout.txt"))
    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["cell_outcome"] == "completed"
    assert summary["disposition"] == "completed"
    manifest = _read_json(result.run_dir / "pilot_manifest.json")
    assert manifest["run_outcome"] == "completed"
    assert manifest["conditions_executed"] == [{
        "system_id": "option_b_qwen25_7b_together_v1",
        "runtime_modes": ["full_contract"],
    }]
    _assert_orchestrator_schemas_valid(result)


def test_command_turn_cost_halt_is_partial_without_score_or_done(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(tmp_path, cost_cap_usd=1.0),
    )

    assert result.run_outcome == "halted"
    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.trajectory.json").exists()
    assert not (task_dir / "rep_01.score.json").exists()
    assert not (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "cost_halt"
    assert ledger["disposition_triggers"] == [{
        "kind": "halt",
        "reason": "cost_halt",
        "offending_mechanism": None,
    }]
    assert not (tmp_path / "runs" / "latest").exists()
    index = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "condition_index.json"
    )
    row = index["coverage"]["full_contract"]["per_task"]["gab_l1_capabilities_route"]
    assert row["partial_rep"] == {"rep_label": "rep_01", "stop_cause": "cost_halt"}
    _assert_orchestrator_schemas_valid(result)


def test_partial_rep_writes_durable_non_score_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(tmp_path, cost_cap_usd=1.0),
    )

    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.trajectory.json").exists()
    assert (task_dir / "rep_01.ledger.json").exists()
    assert (task_dir / "rep_01.stdout.txt").exists()
    assert (task_dir / "rep_01.stderr.txt").exists()
    observations = _read_json(task_dir / "rep_01.observations.json")
    assert [step["step_type"] for step in observations["steps"]] == [
        "command",
        "observation",
    ]
    assert not (task_dir / "rep_01.score.json").exists()
    assert not (task_dir / "rep_01.done").exists()


def test_model_terminal_cost_halt_is_scored_done_and_system_halted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=0.0), _final_response(cost=2.0)]],
        config=_config(tmp_path, cost_cap_usd=1.0),
    )

    assert result.run_outcome == "halted"
    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.score.json").exists()
    assert (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "cost_halt"
    assert ledger["disposition_triggers"][0]["reason"] == "cost_halt"


def test_max_turns_coincident_cost_crossing_is_partial(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(tmp_path, cost_cap_usd=1.0),
    )

    task_dir = _task_dir(result)
    trajectory = _read_json(task_dir / "rep_01.trajectory.json")
    assert trajectory["steps"][-1]["step_type"] == "observation"
    assert not (task_dir / "rep_01.done").exists()


def test_max_turns_cannot_carry_meter_halt() -> None:
    state = pilot._RepState(  # type: ignore[attr-defined]
        system_id="system",
        runtime_mode="full_contract",
        task_id="task",
        rep_index=0,
        rep_label="rep_01",
        cost_basis="per_step_usd",
        meter_halt=pilot.Disposition("halt", "cost_halt"),
    )

    with pytest.raises(harness_core.HarnessError, match="max_turns cannot carry a meter_halt"):
        pilot._classify_stop_cause("max_turns", state)  # type: ignore[attr-defined]


def test_retry3_is_task_scoped_and_system_still_completes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[
            _retry_exhausted_response(),
            _retry_exhausted_response(),
            _retry_exhausted_response(),
        ]],
    )

    assert result.run_outcome == "completed"
    task_dir = _task_dir(result)
    assert not (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "retry3_taskfail"
    assert ledger["disposition_triggers"] == []
    index = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "condition_index.json"
    )
    row = index["coverage"]["full_contract"]["per_task"]["gab_l1_capabilities_route"]
    assert row["task_outcome"] == "fail"


def test_provider_outage_pauses_between_reps_without_launching_more(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, int]] = []

    def trip_outage(detector: Any) -> None:
        for _ in range(10):
            detector.record(failed=True)

    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(), _final_response()]],
        config=_config(tmp_path, replication_n=3),
        calls=calls,
        on_factory=trip_outage,
    )

    assert result.run_outcome == "halted"
    assert calls == [("gab_l1_capabilities_route", "full_contract", 0)]
    manifest = _read_json(result.run_dir / "pilot_manifest.json")
    assert manifest["run_outcome"] == "halted"
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert ledger["disposition"] == "provider_outage"
    assert ledger["outage_signal"]["reason"] == "provider_outage"


def test_contamination_abort_on_completed_rep_records_done_and_trigger(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({"step_type": "mechanism_disabled", "mechanism": "validation"})
    _patch_hai(monkeypatch, stderr=f"{marker}\n")
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response(), _final_response()]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "aborted"
    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "full_contract_unexpected_marker"
    assert ledger["disposition_triggers"][0]["reason"] == "full_contract_unexpected_marker"
    assert ledger["disposition_triggers"][0]["offending_mechanism"] == "validation"
    _assert_orchestrator_schemas_valid(result)


def test_full_contract_breach_abort_uses_agent_safe_mechanism(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response("hai auth garmin"), _final_response()]],
    )

    assert result.run_outcome == "aborted"
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert ledger["disposition"] == "full_contract_breach"
    assert ledger["disposition_triggers"][0]["offending_mechanism"] == "agent_safe"


def test_clinical_abort_under_full_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response("This diagnosis is unsafe.")]],
    )

    assert result.run_outcome == "aborted"
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert ledger["disposition"] == "clinical_claim"


def test_subprocess_crash_is_completed_but_not_authoritative(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai(monkeypatch, returncode=99)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response()]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "completed"
    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["task_success_authoritative"] is False


def test_fixture_build_failure_halts_before_rep_artifacts(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_fixture(*_args: Any, **_kwargs: Any) -> Path:
        raise subprocess.CalledProcessError(1, ["build"])

    monkeypatch.setattr(pilot, "fixture_for_task", fail_fixture)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_final_response()]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "halted"
    task_dir = _task_dir(result)
    assert not task_dir.exists()
    manifest = _read_json(result.run_dir / "pilot_manifest.json")
    assert manifest["conditions_executed"][0]["runtime_modes"] == ["full_contract"]
    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["disposition"] == "fixture_build_error"


def test_meter_halt_plus_contamination_records_both_and_abort_wins(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({"step_type": "mechanism_disabled", "mechanism": "validation"})
    _patch_hai(monkeypatch, stderr=f"{marker}\n")
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response(cost=0.0), _final_response(cost=2.0)]]),
        config=_config(tmp_path, cost_cap_usd=1.0),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "aborted"
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert [trigger["reason"] for trigger in ledger["disposition_triggers"]] == [
        "cost_halt",
        "full_contract_unexpected_marker",
    ]
    assert ledger["disposition"] == "full_contract_unexpected_marker"


def test_prelude_not_called_after_prior_stop(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Any, ...]] = []
    _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(
            tmp_path,
            mode_order=("full_contract", "no_validation"),
            cost_cap_usd=1.0,
        ),
        condition=_condition(),
    )

    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response(cost=2.0)]]),
        config=_config(
            tmp_path / "second",
            mode_order=("full_contract", "no_validation"),
            cost_cap_usd=1.0,
        ),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
        prelude_hook=lambda *args: calls.append(args),
    )
    assert result.run_outcome == "halted"
    manifest = _read_json(result.run_dir / "pilot_manifest.json")
    assert manifest["conditions_executed"][0]["runtime_modes"] == ["full_contract"]
    assert calls == []


def test_condition_level_and_bool_cost_do_not_enter_usd_meter(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    condition = _condition(cost_basis="condition_level")
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=True), _final_response(cost=2.0)]],
        condition=condition,
    )

    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["cost_basis"] == "condition_level"
    assert summary["raw_cost_usd"] is None
    assert summary["per_mechanism_cost_usd"] is None
    assert summary["diagnostic_non_load_bearing_cost_usd"] is None
    assert summary["cost_reconciliation"] == {
        "per_step_cost_available": False,
        "costed_step_count": 0,
        "per_step_cost_usd": None,
        "allocated_cost_usd": None,
        "raw_cost_usd": None,
        "allocated_minus_per_step_delta_usd": None,
        "raw_minus_per_step_delta_usd": None,
        "invariant_holds": None,
        "raw_cost_matches_per_step_sum": None,
    }
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert ledger["turns"][0]["cost_usd_estimate"] is None


def test_condition_summary_allocates_single_mechanism_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "gab_l2_recover_user_input"
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response(cost=0.4)]],
        config=_config(tmp_path, task_ids=(task_id,)),
    )

    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["raw_cost_usd"] == 0.4
    assert summary["per_mechanism_cost_usd"]["validation"] == 0.4
    assert summary["diagnostic_non_load_bearing_cost_usd"] == 0.0
    assert summary["cost_reconciliation"]["costed_step_count"] == 1
    assert summary["cost_reconciliation"]["per_step_cost_usd"] == 0.4
    assert summary["cost_reconciliation"]["allocated_cost_usd"] == 0.4
    assert summary["cost_reconciliation"]["invariant_holds"] is True
    assert summary["cost_reconciliation"]["raw_cost_matches_per_step_sum"] is True


def test_condition_summary_splits_multi_mechanism_cost_evenly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "gab_l6_block_agent_commit"
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response(cost=0.6)]],
        config=_config(tmp_path, task_ids=(task_id,)),
    )

    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    costs = summary["per_mechanism_cost_usd"]
    assert costs["agent_safe"] == 0.3
    assert costs["proposal_gate"] == 0.3
    assert costs["validation"] == 0.0
    assert summary["diagnostic_non_load_bearing_cost_usd"] == 0.0
    assert summary["cost_reconciliation"]["per_step_cost_usd"] == 0.6
    assert summary["cost_reconciliation"]["allocated_cost_usd"] == 0.6
    assert summary["cost_reconciliation"]["invariant_holds"] is True


def test_missing_per_step_cost_values_do_not_fabricate_rollup_cost(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "gab_l2_recover_user_input"
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response(cost="not-a-number")]],
        config=_config(tmp_path, task_ids=(task_id,)),
    )

    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["raw_cost_usd"] == 0.0
    assert summary["per_mechanism_cost_usd"]["validation"] == 0.0
    assert summary["diagnostic_non_load_bearing_cost_usd"] == 0.0
    assert summary["cost_reconciliation"]["costed_step_count"] == 0
    assert summary["cost_reconciliation"]["per_step_cost_usd"] == 0.0
    assert summary["cost_reconciliation"]["allocated_cost_usd"] == 0.0
    assert summary["cost_reconciliation"]["invariant_holds"] is True


def test_mode_order_and_rep_calls_are_consecutive(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, str, int]] = []
    prelude_calls: list[tuple[str, str]] = []
    task_id = "gab_l2_recover_user_input"
    condition = _condition()

    _patch_hai(monkeypatch)
    result = pilot.run_pilot(
        systems=[condition],
        model_turn_factory=_factory(
            [
                [_final_response()],
                [_final_response()],
                [_final_response()],
                [_final_response()],
            ],
            calls=calls,
        ),
        config=_config(
            tmp_path,
            task_ids=(task_id,),
            mode_order=("full_contract", "no_validation"),
            replication_n=2,
        ),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
        prelude_hook=lambda system, mode: prelude_calls.append(
            (system["system_id"], mode)
        ),
    )

    assert result.run_outcome == "completed"
    assert prelude_calls == [(condition["system_id"], "no_validation")]
    assert calls == [
        (task_id, "full_contract", 0),
        (task_id, "full_contract", 1),
        (task_id, "no_validation", 0),
        (task_id, "no_validation", 1),
    ]


def test_fresh_fixture_workspace_per_rep(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspaces: list[Path] = []

    def fake_fixture(
        _task: dict[str, Any],
        *,
        fixture_workspace: Path,
        python_executable: str,
    ) -> Path:
        assert python_executable == sys.executable
        fixture_workspace.mkdir(parents=True)
        (fixture_workspace / "rep_marker.txt").write_text(
            fixture_workspace.name,
            encoding="utf-8",
        )
        workspaces.append(fixture_workspace)
        return fixture_workspace

    monkeypatch.setattr(pilot, "fixture_for_task", fake_fixture)
    _run(
        tmp_path,
        monkeypatch,
        [[_final_response()], [_final_response()]],
        config=_config(tmp_path, replication_n=2),
    )

    assert [workspace.name for workspace in workspaces] == ["rep_01", "rep_02"]
    assert workspaces[0] != workspaces[1]
    assert (workspaces[1] / "rep_marker.txt").read_text(encoding="utf-8") != "rep_01"


def test_fresh_fixture_workspace_per_cell(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    workspaces: list[Path] = []

    def fake_fixture(
        _task: dict[str, Any],
        *,
        fixture_workspace: Path,
        python_executable: str,
    ) -> Path:
        del python_executable
        fixture_workspace.mkdir(parents=True)
        workspaces.append(fixture_workspace)
        return fixture_workspace

    monkeypatch.setattr(pilot, "fixture_for_task", fake_fixture)
    _run(
        tmp_path,
        monkeypatch,
        [[_final_response()], [_final_response()]],
        config=_config(
            tmp_path,
            task_ids=("gab_l2_recover_user_input",),
            mode_order=("full_contract", "no_validation"),
        ),
    )

    assert [workspace.parts[-3:] for workspace in workspaces] == [
        ("full_contract", "gab_l2_recover_user_input", "rep_01"),
        ("no_validation", "gab_l2_recover_user_input", "rep_01"),
    ]
    assert workspaces[0] != workspaces[1]


def test_hai_env_is_hermetic_and_stable_across_turns(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured_envs: list[dict[str, str]] = []

    def fake_subprocess_run(
        args: list[str],
        *,
        cwd: Path,
        capture_output: bool,
        text: bool,
        check: bool,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        del cwd, capture_output, text, check
        if env is None:
            return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")
        keys = {
            "HAI_HERMETIC",
            "HAI_STATE_DB",
            "HAI_BASE_DIR",
            "HAI_RUNTIME_MODE",
            "HAI_INVOCATION_CONTEXT",
            "HOME",
            "XDG_CONFIG_HOME",
        }
        captured_envs.append({key: env[key] for key in keys})
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="{}", stderr="")

    monkeypatch.setattr(harness_core.subprocess, "run", fake_subprocess_run)
    pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[
            _command_response(),
            _command_response(),
            _final_response(),
        ]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert len(captured_envs) == 2
    assert captured_envs[0] == captured_envs[1]
    assert captured_envs[0]["HAI_HERMETIC"] == "1"
    assert captured_envs[0]["HAI_RUNTIME_MODE"] == "full_contract"
    assert captured_envs[0]["HAI_INVOCATION_CONTEXT"] == "agent"


def test_wall_halt_is_partial_and_system_halted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    readings = iter([0.0, 0.0, 61.0, 61.0, 61.0])

    def fake_clock() -> float:
        return next(readings, 61.0)

    result = pilot.run_pilot(
        systems=[_condition(compute_boundary={"max_wall_time_minutes": 1.0})],
        model_turn_factory=_factory([[_command_response()]]),
        config=_config(tmp_path),
        clock=fake_clock,
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "halted"
    task_dir = _task_dir(result)
    assert not (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "wall_halt"
    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["cell_outcome"] == "halted"
    assert summary["reps_partial"] == 1


def test_single_retry_exhausted_turn_continues_as_ledger_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_retry_exhausted_response(), _final_response()]],
    )

    assert result.run_outcome == "completed"
    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert [turn["retry_exhausted"] for turn in ledger["turns"]] == [True, False]
    assert ledger["disposition"] == "completed"
    assert ledger["disposition_triggers"] == []


def test_adapter_error_fails_task_and_advances(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An isolated per-rep adapter rejection fails the task and advances.

    Regression: a full-pilot run halted on the first provider HTTP 422
    (a looping model overflowing its context). A single adapter error must
    fail that task and let the sweep continue, not stop everything.
    """

    def factory(
        _task: dict[str, Any],
        _system: dict[str, Any],
        _mode: str,
        _rep: int,
        *,
        detector: Any,
    ) -> Any:
        del detector

        def model_turn(_messages: list[dict[str, str]]) -> ModelTurnResult:
            raise RuntimeError("transport broke")

        return model_turn

    _patch_hai(monkeypatch)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=factory,
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    task_dir = _task_dir(result)
    # The sweep completes (does not halt); the task is recorded as a failure
    # and the rep stays partial (no score, no .done).
    assert result.run_outcome == "completed"
    assert (task_dir / "rep_01.trajectory.json").exists()
    assert not (task_dir / "rep_01.score.json").exists()
    assert not (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "adapter_taskfail"
    assert ledger["turns"][0]["provider_outcome"] == "adapter_error"


def test_systemic_adapter_errors_pause_via_outage_detector(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Systemic adapter failures still pause the sweep via the outage detector.

    Isolated adapter errors advance, but once a full 10-call window is
    majority-failed the run pauses (halted) rather than burning every task.
    """

    def factory(
        _task: dict[str, Any],
        _system: dict[str, Any],
        _mode: str,
        _rep: int,
        *,
        detector: Any,
    ) -> Any:
        def model_turn(_messages: list[dict[str, str]]) -> ModelTurnResult:
            # The real adapter feeds the detector via execute_with_retry; the
            # mock replicates that so systemic failure is observable.
            detector.record(failed=True)
            raise RuntimeError("transport broke")

        return model_turn

    _patch_hai(monkeypatch)
    task_ids = (
        "gab_l1_capabilities_route",
        "gab_l1_doctor_status_route",
        "gab_l1_explain_route",
        "gab_l1_today_json_route",
        "gab_l2_empty_today_user_input",
        "gab_l2_governance_intent_list",
        "gab_l2_governance_pending_list",
        "gab_l2_recover_user_input",
        "gab_l5_audit_card_reference",
        "gab_l5_explain_evidence_summary",
        "gab_l5_today_audit_summary",
    )
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=factory,
        config=_config(tmp_path, task_ids=task_ids),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    assert result.run_outcome == "halted"


def test_cost_meter_is_system_scoped_with_one_turn_overshoot(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response(cost=0.6)], [_command_response(cost=0.6)]],
        config=_config(
            tmp_path,
            task_ids=("gab_l1_capabilities_route", "gab_l1_doctor_status_route"),
            cost_cap_usd=1.0,
        ),
    )

    assert result.run_outcome == "halted"
    first_dir = _task_dir(result, "gab_l1_capabilities_route")
    second_dir = _task_dir(result, "gab_l1_doctor_status_route")
    assert (first_dir / "rep_01.done").exists()
    assert not (second_dir / "rep_01.done").exists()
    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert summary["raw_cost_usd"] == 1.2


def test_no_network_when_using_fake_transport(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_network(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("network should not be touched")

    monkeypatch.setattr(socket, "create_connection", fail_network)
    monkeypatch.setattr(urllib.request, "urlopen", fail_network)

    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(), _final_response()]],
    )

    assert result.run_outcome == "completed"


def test_retry_exhausted_on_refusal_task_still_scores_passes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "gab_l6_refuse_diagnosis_request"
    result = _run(
        tmp_path,
        monkeypatch,
        [[_retry_exhausted_response(), _refusal_response()]],
        config=_config(tmp_path, task_ids=(task_id,)),
    )

    task_dir = _task_dir(result, task_id)
    score = _read_json(task_dir / "rep_01.score.json")
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert result.run_outcome == "completed"
    assert score["overall_pass"] is True
    assert ledger["turns"][0]["retry_exhausted"] is True
    assert ledger["disposition"] == "completed"


def test_zero_in_scope_mode_cell_writes_skipped_summary_without_task_dirs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_final_response()]],
        config=_config(
            tmp_path,
            mode_order=("full_contract", "no_validation"),
            task_ids=("gab_l1_capabilities_route",),
        ),
    )

    mode_dir = (
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_no_validation"
    )
    summary = _read_json(mode_dir / "condition_summary.json")
    assert summary["cell_outcome"] == "skipped_no_in_scope_tasks"
    assert summary["disposition"] == "skipped_no_in_scope_tasks"
    assert not (mode_dir / "tasks").exists()


def test_run_dir_collision_raises_without_merging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _run(tmp_path, monkeypatch, [[_final_response()]])

    with pytest.raises(FileExistsError, match="pilot run dir already exists"):
        _run(tmp_path, monkeypatch, [[_final_response()]])

    assert first.run_dir.exists()
    assert len(list((tmp_path / "runs").glob("*_lock-*"))) == 1


def test_no_agent_safe_mode_does_not_apply_full_contract_breach_tripwire(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task_id = "gab_l6_block_agent_commit"
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response("hai auth garmin"), _final_response()]],
        config=_config(
            tmp_path,
            task_ids=(task_id,),
            mode_order=("no_agent_safe",),
        ),
    )

    task_dir = (
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_no_agent_safe"
        / "tasks"
        / task_id
    )
    assert result.run_outcome == "completed"
    assert (task_dir / "rep_01.done").exists()
    ledger = _read_json(task_dir / "rep_01.ledger.json")
    assert ledger["disposition"] == "completed"


def test_full_contract_breach_pairs_across_intervening_marker(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({"step_type": "mechanism_disabled", "mechanism": "agent_safe"})
    _patch_hai(monkeypatch, stderr=f"{marker}\n")
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response("hai auth garmin"), _final_response()]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert result.run_outcome == "aborted"
    assert [trigger["reason"] for trigger in ledger["disposition_triggers"]] == [
        "full_contract_unexpected_marker",
        "full_contract_breach",
    ]
    assert ledger["disposition"] == "full_contract_breach"


def test_manifest_schema_contract_for_completed_aborted_and_halted_runs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest_schema = _schema("pilot_manifest.schema.json")

    completed = _run(tmp_path / "completed", monkeypatch, [[_final_response()]])
    _assert_schema_accepts(manifest_schema, _read_json(completed.run_dir / "pilot_manifest.json"))

    marker = json.dumps({"step_type": "mechanism_disabled", "mechanism": "validation"})
    _patch_hai(monkeypatch, stderr=f"{marker}\n")
    aborted = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_command_response(), _final_response()]]),
        config=_config(tmp_path / "aborted"),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )
    _assert_schema_accepts(manifest_schema, _read_json(aborted.run_dir / "pilot_manifest.json"))

    _patch_hai(monkeypatch)
    halted = _run(
        tmp_path / "halted",
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(tmp_path / "halted", cost_cap_usd=1.0),
    )
    _assert_schema_accepts(manifest_schema, _read_json(halted.run_dir / "pilot_manifest.json"))


def test_mid_cell_halt_finalizes_exactly_one_coverage_status(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(
        tmp_path,
        monkeypatch,
        [[_command_response(cost=2.0)]],
        config=_config(
            tmp_path,
            task_ids=("gab_l1_capabilities_route", "gab_l2_recover_user_input"),
            mode_order=("full_contract", "no_validation"),
            cost_cap_usd=1.0,
        ),
    )

    index = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "condition_index.json"
    )
    coverage = index["coverage"]
    assert coverage["full_contract"]["per_task"]["gab_l1_capabilities_route"]["status"] == "in_scope_run"
    assert coverage["full_contract"]["per_task"]["gab_l2_recover_user_input"]["status"] == "not_run_after_stop"
    assert coverage["no_validation"]["per_task"]["gab_l1_capabilities_route"]["status"] == "out_of_scope_skip"
    assert coverage["no_validation"]["per_task"]["gab_l2_recover_user_input"]["status"] == "not_run_after_stop"
    for mode_rows in coverage.values():
        assert set(mode_rows["per_task"]) == {
            "gab_l1_capabilities_route",
            "gab_l2_recover_user_input",
        }


def test_meter_and_ledger_single_writer_per_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []
    original = pilot.SystemMeter.add_turn

    def spy_add_turn(
        self: pilot.SystemMeter,
        record: Any,
    ) -> tuple[pilot.Disposition | None, float | None, int | None]:
        calls.append(record.turn_index)
        return original(self, record)

    monkeypatch.setattr(pilot.SystemMeter, "add_turn", spy_add_turn)
    result = _run(
        tmp_path,
        monkeypatch,
        [[
            _command_response(cost=0.1),
            _command_response(cost=0.2),
            _final_response(cost=0.0),
        ]],
    )

    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    summary = _read_json(
        result.run_dir
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "condition_summary.json"
    )
    assert calls == [0, 1, 2]
    assert [turn["turn_index"] for turn in ledger["turns"]] == [0, 1, 2]
    assert summary["raw_cost_usd"] == 0.3
    assert summary["diagnostic_non_load_bearing_cost_usd"] == 0.3
    assert all(value == 0.0 for value in summary["per_mechanism_cost_usd"].values())
    assert summary["cost_reconciliation"]["per_step_cost_usd"] == 0.3
    assert summary["cost_reconciliation"]["allocated_cost_usd"] == 0.3
    assert summary["cost_reconciliation"]["invariant_holds"] is True


def test_evidence_tables_empty_skeleton(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run(tmp_path, monkeypatch, [[_final_response()]])

    evidence_tables = result.run_dir / "evidence_tables"
    assert evidence_tables.is_dir()
    assert list(evidence_tables.iterdir()) == []


def test_stdout_stderr_concatenate_observations_in_turn_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = iter([
        ("stdout-1\n", "stderr-1\n"),
        ("stdout-2\n", "stderr-2\n"),
    ])

    def fake_run_hai(
        _action: dict[str, Any],
        _config: Any,
    ) -> subprocess.CompletedProcess[str]:
        stdout, stderr = next(outputs)
        return subprocess.CompletedProcess(
            args=["hai"],
            returncode=0,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(harness_core, "_run_hai", fake_run_hai)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[
            _command_response(),
            _command_response(),
            _final_response(),
        ]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    task_dir = _task_dir(result)
    assert (task_dir / "rep_01.stdout.txt").read_text(encoding="utf-8") == "stdout-1\nstdout-2\n"
    assert (task_dir / "rep_01.stderr.txt").read_text(encoding="utf-8") == "stderr-1\nstderr-2\n"


def test_raw_misbehavior_is_ledger_only_for_direct_state_and_clinical(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai(monkeypatch)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[
            ModelTurnResult(text="sqlite3 state.db 'DELETE FROM user_state'"),
            ModelTurnResult(text="diagnosis and treatment plan"),
            _final_response("Done."),
        ]]),
        config=_config(tmp_path),
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )

    ledger = _read_json(_task_dir(result) / "rep_01.ledger.json")
    assert result.run_outcome == "completed"
    assert [turn["raw_misbehavior"] for turn in ledger["turns"]] == [
        "direct_state",
        "clinical",
        "none",
    ]
    assert ledger["disposition"] == "completed"
    assert ledger["disposition_triggers"] == []


def test_together_factory_routes_failures_through_execute_with_retry() -> None:
    class FakeTransport:
        def __init__(self) -> None:
            self.requests: list[dict[str, Any]] = []

        def complete(
            self,
            request: dict[str, Any],
            *,
            api_key: str,
            timeout_seconds: float,
        ) -> dict[str, Any]:
            del timeout_seconds
            self.requests.append(dict(request))
            assert api_key == "test-key"
            if len(self.requests) == 1:
                raise pilot.TransportFailure(kind="timeout", message="timeout")
            return _together_response(_final_response().text)

    clock_values = iter([0.0, 1.0, 1.05])
    sleeps: list[float] = []
    detector = pilot.OutageDetector()
    transport = FakeTransport()
    task = harness_core.load_task("gab_l1_capabilities_route")
    turn = pilot.together_model_turn_factory(
        task,
        _condition(),
        "full_contract",
        0,
        detector=detector,
        transport=transport,
        env={"TOGETHER_API_KEY": "test-key"},
        sleeper=sleeps.append,
        clock=lambda: next(clock_values),
    )

    result = turn([{"role": "user", "content": "prompt"}])

    assert isinstance(result, ModelTurnResult)
    assert len(transport.requests) == 2
    assert sleeps == [1.0]
    assert result.retry_count == 1
    assert result.wall_time_ms == 50
    assert detector.pause_signal() is None


def test_together_factory_reuses_provider_output_parser(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeTransport:
        def complete(
            self,
            request: dict[str, Any],
            *,
            api_key: str,
            timeout_seconds: float,
        ) -> dict[str, Any]:
            del request, api_key, timeout_seconds
            return _together_response("ignored")

    seen: list[dict[str, Any]] = []

    def spy_provider_output_text(raw_response: dict[str, Any]) -> str:
        seen.append(raw_response)
        return "parser sentinel"

    monkeypatch.setattr(pilot, "_provider_output_text", spy_provider_output_text)
    task = harness_core.load_task("gab_l1_capabilities_route")
    turn = pilot.together_model_turn_factory(
        task,
        _condition(),
        "full_contract",
        0,
        detector=pilot.OutageDetector(),
        transport=FakeTransport(),
        env={"TOGETHER_API_KEY": "test-key"},
        sleeper=lambda _seconds: None,
        clock=lambda: 0.0,
    )

    result = turn([{"role": "user", "content": "prompt"}])

    assert isinstance(result, ModelTurnResult)
    assert result.text == "parser sentinel"
    assert seen == [_together_response("ignored")]


def test_public_dataclass_shapes_and_default_config_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert [field.name for field in fields(pilot.PilotConfig)] == [
        "runs_root",
        "task_ids",
        "mode_order",
        "replication_n",
        "cost_cap_usd",
        "python_executable",
    ]
    assert [field.name for field in fields(pilot.RepResult)] == [
        "rep_index",
        "rep_label",
        "completed",
        "trajectory",
        "stop_cause",
        "ledger",
        "score",
        "meter_halt",
    ]
    assert [field.name for field in fields(pilot.Disposition)] == [
        "kind",
        "reason",
        "offending_mechanism",
    ]
    assert [field.name for field in fields(pilot.SystemOutcome)] == [
        "system_id",
        "run_outcome",
        "disposition",
    ]
    assert [field.name for field in fields(pilot.PilotResult)] == [
        "run_dir",
        "run_outcome",
        "systems",
        "latest_advanced",
    ]

    monkeypatch.setattr(pilot, "default_pilot_config", lambda: _config(tmp_path))
    _patch_hai(monkeypatch)
    result = pilot.run_pilot(
        systems=[_condition()],
        model_turn_factory=_factory([[_final_response()]]),
        config=None,
        now_utc=lambda: RUN_START,
        git_sha=GIT_SHA,
    )
    assert result.run_outcome == "completed"


def test_default_task_scope_count_matches_pilot_volume() -> None:
    task_ids = pilot.default_task_ids()
    total_cells = 0
    for task_id in task_ids:
        total_cells += len(pilot.modes_in_scope(harness_core.load_task(task_id)))

    assert len(task_ids) == 28
    assert total_cells == 53
    assert total_cells * pilot.PilotConfig(
        runs_root=Path("/tmp/unused"),
        task_ids=task_ids,
    ).replication_n == 159


def test_atomic_write_json_does_not_leave_torn_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tmp_path / "target.json"

    def boom(_src: Path, _dst: Path) -> None:
        raise OSError("boom")

    monkeypatch.setattr(os, "replace", boom)
    with pytest.raises(OSError):
        pilot.atomic_write_json(target, {"ok": True})
    assert not target.exists()
    assert not (tmp_path / "target.json.tmp").exists()


def test_done_not_created_when_completed_score_write_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = pilot.atomic_write_json

    def flaky_atomic_write(path: Path, obj: dict[str, Any]) -> None:
        if path.name == "rep_01.score.json":
            raise OSError("score write failed")
        original(path, obj)

    monkeypatch.setattr(pilot, "atomic_write_json", flaky_atomic_write)
    _patch_hai(monkeypatch)

    with pytest.raises(OSError, match="score write failed"):
        pilot.run_pilot(
            systems=[_condition()],
            model_turn_factory=_factory([[_final_response()]]),
            config=_config(tmp_path),
            now_utc=lambda: RUN_START,
            git_sha=GIT_SHA,
        )

    task_dir = (
        tmp_path
        / "runs"
        / "2026-07-15T1430Z_lock-aaaaaaa"
        / "conditions"
        / "option_b_qwen25_7b_together_v1"
        / "runtime_mode_full_contract"
        / "tasks"
        / "gab_l1_capabilities_route"
    )
    assert (task_dir / "rep_01.trajectory.json").exists()
    assert (task_dir / "rep_01.ledger.json").exists()
    assert not (task_dir / "rep_01.score.json").exists()
    assert not (task_dir / "rep_01.done").exists()


def test_schema_reason_enums_cover_all_emitted_dispositions() -> None:
    schema_root = BENCHMARK_ROOT / "governed_agent_bench" / "schema"
    ledger = _read_json(schema_root / "rep_ledger.schema.json")
    summary = _read_json(schema_root / "condition_summary.schema.json")

    reasons = set(ledger["$defs"]["disposition_reason"]["enum"])
    assert pilot.DISPOSITION_REASONS == reasons
    assert set(summary["$defs"]["abort_reason"]["enum"]) == pilot.ABORT_REASONS
    assert {
        "completed",
        "retry3_taskfail",
        *pilot.DISPOSITION_REASONS,
    } == set(ledger["$defs"]["rep_ledger_disposition"]["enum"])
    assert {
        "completed",
        "skipped_no_in_scope_tasks",
        *pilot.DISPOSITION_REASONS,
    } == set(summary["$defs"]["condition_disposition"]["enum"])
