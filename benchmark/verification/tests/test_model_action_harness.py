"""Model-emitted operator action harness plumbing."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import (  # noqa: E402
    HarnessConfig,
    HarnessError,
    ModelTurnResult,
    harness_config_for_roster_condition,
    load_task,
    parse_model_action,
    run_agent_loop,
    run_model_response_action,
)
import governed_agent_bench.harness.core as harness_core  # noqa: E402
from governed_agent_bench.model_roster import (  # noqa: E402
    model_roster_hash,
    roster_condition,
)


def test_parse_model_action_accepts_structured_command() -> None:
    action = parse_model_action(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Inspect the command surface.",
        })
    )

    assert action["command"] == "hai capabilities"
    assert action["args"] == {"--json": True}


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        "[{\"action_type\": \"final\"}]",
        json.dumps({"action_type": "command", "command": "sqlite3 state.db", "args": {}}),
        json.dumps({"action_type": "command", "command": "hai today", "args": "bad"}),
        json.dumps({"action_type": "refusal", "reason": "No", "args": {}}),
        json.dumps({"action_type": "final", "command": "hai today", "final_text": "Done"}),
        json.dumps({"action_type": "final", "final_text": "Done", "extra": True}),
    ],
)
def test_parse_model_action_rejects_non_contract_shapes(response: str) -> None:
    with pytest.raises(HarnessError):
        parse_model_action(response)


def test_harness_requires_identity_for_model_backed_runs(tmp_path: Path) -> None:
    task = load_task("gab_l1_capabilities_route")

    with pytest.raises(HarnessError, match="requires model_identity"):
        run_model_response_action(
            task,
            json.dumps({
                "action_type": "command",
                "command": "hai capabilities",
                "args": {"--json": True},
            }),
            HarnessConfig(
                fixture_root=tmp_path / "fixture",
                output_dir=tmp_path / "out",
                model_class="cloud",
                invocation_context="agent",
            ),
        )


def test_model_response_action_records_roster_identity_and_hash(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = roster_condition("option_b_qwen25_7b_together")
    roster_hash = model_roster_hash()
    config = harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=roster_hash,
    )

    trajectory = run_model_response_action(
        task,
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Inspect the command surface.",
        }),
        config,
    )

    assert trajectory["model_class"] == "cloud"
    assert trajectory["invocation_context"] == "agent"
    assert trajectory["system_id"] == condition["system_id"]
    assert trajectory["claim_tier"] == "T3"
    assert trajectory["model_roster_hash"] == roster_hash
    assert trajectory["model_identity"] == {
        "model_family": "qwen2.5-instruct",
        "model_id": "Qwen/Qwen2.5-7B-Instruct-Turbo",
        "parameter_count": "7B",
        "quantization": "FP8 provider serving",
        "provider_snapshot": "Together AI@2026-05-19",
        "decoding_settings": {
            "temperature": 0,
            "top_p": 1,
            "max_tokens": 2048,
            "seed": "provider_does_not_support_seed",
        },
    }
    assert trajectory["steps"][0]["step_type"] == "command"
    assert trajectory["steps"][-1]["step_type"] == "observation"
    assert trajectory["steps"][-1]["exit_code"] == "OK"


def _config(tmp_path: Path) -> HarnessConfig:
    condition = roster_condition("option_b_qwen25_7b_together")
    return harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )


def _command_response(command: str = "hai capabilities") -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "command",
        "command": command,
        "args": {"--json": True} if command == "hai capabilities" else {},
        "reason": "Inspect the command surface.",
    })


def _final_response(text: str = "Done.") -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "final",
        "final_text": text,
        "reason": "No further action is needed.",
    })


def _scripted_model_turn(
    responses: list[str],
    seen_messages: list[list[dict[str, str]]],
) -> Any:
    def model_turn(messages: list[dict[str, str]]) -> str:
        seen_messages.append(json.loads(json.dumps(messages)))
        return responses.pop(0)

    return model_turn


def _patch_hai_completed(
    monkeypatch: pytest.MonkeyPatch,
    *,
    returncode: int = 0,
    stdout: str = "{\"ok\": true}",
    stderr: str = "",
) -> None:
    def fake_run_hai(
        action: dict[str, Any],
        config: HarnessConfig,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["hai"],
            returncode=returncode,
            stdout=stdout,
            stderr=stderr,
        )

    monkeypatch.setattr(harness_core, "_run_hai", fake_run_hai)


def test_agent_loop_feeds_observation_back_as_user_message(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({
        "step_type": "mechanism_disabled",
        "mechanism": "validation",
        "runtime_mode": "no_validation",
    })
    _patch_hai_completed(monkeypatch, stderr=f"{marker}\n")
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
    )

    assert result.stop_reason == "final"
    assert len(seen_messages) == 2
    turn_2_messages = seen_messages[1]
    assert turn_2_messages[-2] == {
        "role": "assistant",
        "content": _command_response(),
    }
    assert turn_2_messages[-1]["role"] == "user"
    feedback = turn_2_messages[-1]["content"]
    assert '"exit_code": "OK"' in feedback
    assert '"stdout_ref":' in feedback
    assert '"step_type": "mechanism_disabled"' in feedback
    assert '"mechanism": "validation"' in feedback
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        "command",
        "mechanism_disabled",
        "observation",
        "final",
    ]


def test_agent_loop_records_invalid_output_and_feedback(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(["not json", _final_response()], seen_messages),
    )

    invalid_step = result.trajectory["steps"][0]
    assert invalid_step["step_type"] == "invalid_output"
    assert invalid_step["raw_output"] == "not json"
    assert "model response is not a JSON object" in invalid_step["parse_error"]
    assert seen_messages[1][-1]["role"] == "user"
    assert "model response is not a JSON object" in seen_messages[1][-1]["content"]
    assert result.turn_records[0].invalid_output == {
        "raw_output": "not json",
        "parse_error": invalid_step["parse_error"],
    }
    assert result.stop_reason == "final"


def test_agent_loop_stops_at_exactly_max_turns(tmp_path: Path) -> None:
    task = load_task("gab_l1_capabilities_route")
    calls = 0

    def model_turn(messages: list[dict[str, str]]) -> str:
        nonlocal calls
        calls += 1
        return "not json"

    result = run_agent_loop(task, _config(tmp_path), model_turn)

    assert calls == 7
    assert len(result.turn_records) == 7
    assert result.stop_reason == "max_turns"
    assert result.turn_records[-1].stop_reason == "max_turns"
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
        "invalid_output",
    ]


def test_agent_loop_subprocess_crash_terminates_before_next_turn(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai_completed(monkeypatch, returncode=99)
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
    )

    assert len(seen_messages) == 1
    assert result.stop_reason == "subprocess_crash"
    assert result.turn_records[-1].stop_reason == "subprocess_crash"
    assert result.trajectory["steps"][-1]["exit_code"] == "EXIT_99"


def test_agent_loop_after_turn_stop_signal_terminates(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_hai_completed(monkeypatch)
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []
    records_seen = []

    def after_turn(record: Any, trajectory_so_far: dict[str, Any]) -> str:
        records_seen.append((record, trajectory_so_far))
        return "stop"

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn([_command_response(), _final_response()], seen_messages),
        after_turn=after_turn,
    )

    assert len(seen_messages) == 1
    assert len(records_seen) == 1
    assert records_seen[0][0].executed_step_ids == [0, 1]
    assert records_seen[0][1]["steps"] == result.trajectory["steps"]
    assert result.stop_reason == "after_turn_stop"
    assert result.turn_records[-1].stop_reason == "after_turn_stop"


_METADATA_KEYS = (
    "wall_time_ms",
    "prompt_tokens",
    "completion_tokens",
    "cost_usd_estimate",
)


def _refusal_response(
    reason: str = "Outside the governed surface.",
    final_text: str = "I cannot do that.",
) -> str:
    return json.dumps({
        "schema_version": "governed_agent_bench.operator_action.v1",
        "action_type": "refusal",
        "reason": reason,
        "final_text": final_text,
    })


def _scripted_meta_turns(
    turns: list[ModelTurnResult],
    seen_messages: list[list[dict[str, str]]],
) -> Any:
    def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
        seen_messages.append(json.loads(json.dumps(messages)))
        return turns.pop(0)

    return model_turn


def test_agent_loop_stamps_numeric_metadata_on_action_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    marker = json.dumps({
        "step_type": "mechanism_disabled",
        "mechanism": "validation",
        "runtime_mode": "no_validation",
    })
    _patch_hai_completed(monkeypatch, stderr=f"{marker}\n")
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []
    turns = [
        ModelTurnResult(
            text=_command_response(),
            prompt_tokens=1200,
            completion_tokens=340,
            cost_usd_estimate=0.00046,
            wall_time_ms=128,
        ),
        ModelTurnResult(
            text=_final_response(),
            prompt_tokens=1500,
            completion_tokens=12,
            cost_usd_estimate=0.00045,
            wall_time_ms=90,
        ),
    ]

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_meta_turns(turns, seen_messages),
    )

    steps = result.trajectory["steps"]
    assert [step["step_type"] for step in steps] == [
        "command",
        "mechanism_disabled",
        "observation",
        "final",
    ]
    # The model-call metadata lands on the command action step only.
    assert steps[0]["metadata"] == {
        "wall_time_ms": 128,
        "prompt_tokens": 1200,
        "completion_tokens": 340,
        "cost_usd_estimate": 0.00046,
        "retry_count": 0,
    }
    # Neither the mechanism marker nor the observation (a different clock)
    # carries the per-turn cost/token keys -> one cost per turn.
    for non_action in (steps[1], steps[2]):
        for key in _METADATA_KEYS:
            assert key not in non_action["metadata"]
    # The final action step gets its own turn's metadata.
    assert steps[3]["metadata"]["wall_time_ms"] == 90
    assert steps[3]["metadata"]["cost_usd_estimate"] == 0.00045
    # Turn records round-trip the same numbers (feeds the provider report).
    assert result.turn_records[0].cost_usd_estimate == 0.00046
    assert result.turn_records[0].wall_time_ms == 128
    assert result.turn_records[1].prompt_tokens == 1500


@pytest.mark.parametrize(
    ("responses", "action_index", "action_type"),
    [
        ([_final_response()], 0, "final"),
        ([_refusal_response()], 0, "refusal"),
        (["not json", _final_response()], 0, "invalid_output"),
    ],
)
def test_agent_loop_str_turn_stamps_present_none_metadata(
    tmp_path: Path,
    responses: list[str],
    action_index: int,
    action_type: str,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_model_turn(list(responses), seen_messages),
    )

    step = result.trajectory["steps"][action_index]
    assert step["step_type"] == action_type
    # A bare-str turn is still the model path: keys present, value None.
    for key in _METADATA_KEYS:
        assert key in step["metadata"]
        assert step["metadata"][key] is None


def test_agent_loop_coerces_non_numeric_metadata_to_none(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    seen_messages: list[list[dict[str, str]]] = []
    turns = [
        ModelTurnResult(
            text=_final_response(),
            prompt_tokens=10,
            completion_tokens=5,
            cost_usd_estimate="not-a-number",  # type: ignore[arg-type]
            wall_time_ms=True,  # type: ignore[arg-type]
        ),
    ]

    result = run_agent_loop(
        task,
        _config(tmp_path),
        _scripted_meta_turns(turns, seen_messages),
    )

    metadata = result.trajectory["steps"][0]["metadata"]
    # Runtime guard drops non-numeric / bool values to None; no leak.
    assert metadata["cost_usd_estimate"] is None
    assert metadata["wall_time_ms"] is None
    assert metadata["prompt_tokens"] == 10
    assert metadata["completion_tokens"] == 5


def test_run_model_response_action_omits_turn_metadata(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")

    trajectory = run_model_response_action(
        task,
        _command_response(),
        _config(tmp_path),
    )

    # The single-response helper performs no provider call, so it is
    # outside WP-A4 turn-metadata stamping: keys absent (like rule_baseline).
    command_step = trajectory["steps"][0]
    assert command_step["step_type"] == "command"
    for key in _METADATA_KEYS:
        assert key not in command_step.get("metadata", {})
