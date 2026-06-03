"""Mocked Together AI adapter checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

from governed_agent_bench.harness import (  # noqa: E402
    TOGETHER_API_KEY_ENV,
    HarnessConfig,
    build_together_chat_request,
    harness_config_for_roster_condition,
    load_task,
    run_together_model_action,
)
from governed_agent_bench.harness.together import (  # noqa: E402
    OUTCOME_ADAPTER_FAILURE,
    OUTCOME_EXECUTED,
    OUTCOME_PROVIDER_REFUSAL,
    OUTCOME_TIMEOUT,
)
from governed_agent_bench.model_roster import (  # noqa: E402
    model_roster_hash,
    roster_condition,
)


class FakeTransport:
    def __init__(
        self,
        response: dict[str, Any] | None = None,
        responses: list[dict[str, Any]] | None = None,
        exc: Exception | None = None,
    ) -> None:
        self.responses = list(responses if responses is not None else [response or {}])
        self.exc = exc
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        request: Mapping[str, Any],
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.calls.append({
            "request": dict(request),
            "api_key": api_key,
            "timeout_seconds": timeout_seconds,
        })
        if self.exc is not None:
            raise self.exc
        if not self.responses:
            raise RuntimeError("fake transport response queue exhausted")
        return self.responses.pop(0)


def _condition() -> dict[str, Any]:
    return roster_condition("option_b_qwen25_7b_together")


def _config(tmp_path: Path, condition: dict[str, Any]) -> HarnessConfig:
    return harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )


def _raw_together_response(content: str) -> dict[str, Any]:
    return {
        "id": "mock-together-response",
        "choices": [
            {
                "finish_reason": "stop",
                "message": {
                    "role": "assistant",
                    "content": content,
                },
            }
        ],
        "usage": {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
        },
    }


def _command_response(command: str = "hai capabilities") -> dict[str, Any]:
    return _raw_together_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": command,
            "args": {"--json": True} if command == "hai capabilities" else {},
            "reason": "Inspect the command surface.",
        })
    )


def _final_response(text: str = "Done.") -> dict[str, Any]:
    return _raw_together_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "final",
            "final_text": text,
            "reason": "No further action is needed.",
        })
    )


def _refusal_response() -> dict[str, Any]:
    return _raw_together_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "refusal",
            "reason": "The request is outside the governed surface.",
            "final_text": "I cannot do that.",
        })
    )


def test_build_together_request_uses_deployment_prompt() -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()

    request, prompt_metadata = build_together_chat_request(task, condition)

    assert request["model"] == "Qwen/Qwen2.5-7B-Instruct-Turbo"
    assert request["temperature"] == 0
    assert request["top_p"] == 1
    assert request["max_tokens"] == 2048
    assert request["messages"][0]["role"] == "system"
    assert "CAPABILITIES MANIFEST" in request["messages"][0]["content"]
    assert request["messages"][1]["role"] == "user"
    assert task["user_prompt"] in request["messages"][1]["content"]
    assert prompt_metadata["prompt_template_id"] == "deployment_full_v1"
    assert len(prompt_metadata["prompt_template_hash"]) == 64


def test_together_adapter_records_raw_response_usage_cost_and_trajectory(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    raw_responses = [_command_response(), _final_response()]
    transport = FakeTransport(responses=raw_responses)

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        timeout_seconds=12.5,
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert result.reportable is False
    assert len(result.turn_records) == 2
    assert result.turn_records[0].parsed_action is not None
    assert result.turn_records[0].parsed_action["command"] == "hai capabilities"
    assert result.turn_records[1].stop_reason == "final"
    assert result.trajectory is not None
    assert result.trajectory["model_class"] == "cloud"
    assert result.trajectory["system_id"] == condition["system_id"]
    assert result.token_usage == {
        "prompt_tokens": 2000,
        "completion_tokens": 1000,
        "total_tokens": 3000,
    }
    assert result.cost_estimate["estimated_total_cost_usd"] == 0.0009

    # Per-turn model-call metadata is stamped on the command action step.
    steps = result.trajectory["steps"]
    assert [step["step_type"] for step in steps] == [
        "command",
        "observation",
        "final",
    ]
    command_meta = steps[0]["metadata"]
    assert command_meta["prompt_tokens"] == 1000
    assert command_meta["completion_tokens"] == 500
    assert command_meta["cost_usd_estimate"] == 0.00045
    assert isinstance(command_meta["wall_time_ms"], int)
    assert command_meta["wall_time_ms"] >= 0
    # WP-A5: a non-retried turn records zero retries through the A4 seam.
    assert command_meta["retry_count"] == 0
    assert result.turn_records[0].retry_count == 0
    # The observation (HAI subprocess) is a different clock: no cost keys.
    for key in ("prompt_tokens", "completion_tokens", "cost_usd_estimate", "wall_time_ms"):
        assert key not in steps[1]["metadata"]
    # The final action step carries its own turn's metadata.
    assert steps[2]["metadata"]["prompt_tokens"] == 1000
    # Turn records round-trip the per-turn cost into the provider report.
    assert result.turn_records[0].cost_usd_estimate == 0.00045
    assert isinstance(result.turn_records[0].wall_time_ms, int)

    assert len(transport.calls) == len(result.turn_records)
    for call in transport.calls:
        assert call["api_key"] == "mock-api-key"
        assert call["timeout_seconds"] == 12.5
        assert "mock-api-key" not in json.dumps(call["request"])

    assert result.raw_provider_response_ref is not None
    assert len(result.raw_provider_response_refs) == 2
    for raw_ref, raw_response in zip(result.raw_provider_response_refs, raw_responses):
        raw_path = config.output_dir / raw_ref
        assert json.loads(raw_path.read_text(encoding="utf-8")) == raw_response

    report_path = config.output_dir / result.provider_report_ref
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert "mock-api-key" not in report_text
    assert report["outcome"] == OUTCOME_EXECUTED
    assert report["raw_provider_response_ref"] == result.raw_provider_response_ref
    assert report["raw_provider_response_refs"] == result.raw_provider_response_refs
    assert report["turn_records"][0]["parsed_action"]["command"] == "hai capabilities"
    assert report["token_usage"] == result.token_usage
    assert report["cost_estimate"] == result.cost_estimate
    assert report["trajectory_id"] == result.trajectory["trajectory_id"]


def test_together_adapter_preserves_ordered_cross_turn_steps(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_doctor_status_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(
        responses=[
            _command_response("hai capabilities"),
            _command_response("hai doctor"),
            _final_response("Runtime status checked."),
        ]
    )

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert result.trajectory is not None
    assert len(transport.calls) == 3
    assert len(result.turn_records) == 3
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        "command",
        "observation",
        "command",
        "observation",
        "final",
    ]
    turn_2_messages = transport.calls[1]["request"]["messages"]
    assert turn_2_messages[-1]["role"] == "user"
    assert '"exit_code": "OK"' in turn_2_messages[-1]["content"]
    assert '"stdout_ref":' in turn_2_messages[-1]["content"]
    assert transport.calls[2]["request"]["messages"][-2]["role"] == "assistant"
    assert result.turn_records[-1].stop_reason == "final"


@pytest.mark.parametrize(
    ("raw_response", "expected_step_type", "expected_stop_reason"),
    [
        (_final_response("Finished."), "final", "final"),
        (_refusal_response(), "refusal", "refusal"),
    ],
)
def test_together_adapter_terminates_on_final_or_refusal(
    tmp_path: Path,
    raw_response: dict[str, Any],
    expected_step_type: str,
    expected_stop_reason: str,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(raw_response)

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert result.trajectory is not None
    assert len(transport.calls) == 1
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        expected_step_type
    ]
    assert result.turn_records[-1].stop_reason == expected_stop_reason


def test_together_adapter_records_malformed_output_as_invalid_output(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(
        responses=[
            _raw_together_response("not json"),
            _final_response("Recovered after parse feedback."),
        ]
    )

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert result.reportable is False
    assert result.trajectory is not None
    assert len(transport.calls) == 2
    assert result.trajectory["steps"][0]["step_type"] == "invalid_output"
    assert result.trajectory["steps"][0]["raw_output"] == "not json"
    assert "model response is not a JSON object" in (
        result.trajectory["steps"][0]["parse_error"]
    )
    assert result.turn_records[0].parsed_action is None
    assert result.turn_records[0].invalid_output is not None
    assert transport.calls[1]["request"]["messages"][-1]["role"] == "user"
    assert "model response is not a JSON object" in (
        transport.calls[1]["request"]["messages"][-1]["content"]
    )


def test_together_adapter_reads_api_key_from_environment_only(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(_raw_together_response("{}"))

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={},
    )

    assert result.outcome == OUTCOME_ADAPTER_FAILURE
    assert result.reportable is True
    assert TOGETHER_API_KEY_ENV in str(result.error)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("transport", "expected_outcome", "raw_expected", "expected_calls"),
    [
        # A timeout is now retried to exhaustion (1 initial + 3 retries),
        # but still surfaces the same OUTCOME_TIMEOUT after N attempts.
        (
            FakeTransport(exc=TimeoutError("mock timeout")),
            OUTCOME_TIMEOUT,
            False,
            4,
        ),
        # A provider refusal arrives on a successful HTTP call: no retry.
        (
            FakeTransport({
                "choices": [
                    {
                        "finish_reason": "content_filter",
                        "message": {"role": "assistant", "content": ""},
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 0},
            }),
            OUTCOME_PROVIDER_REFUSAL,
            True,
            1,
        ),
        # A bare RuntimeError is non-retryable: it propagates on attempt 1.
        (
            FakeTransport(exc=RuntimeError("mock adapter failure")),
            OUTCOME_ADAPTER_FAILURE,
            False,
            1,
        ),
    ],
)
def test_together_adapter_reports_failure_outcomes(
    tmp_path: Path,
    transport: FakeTransport,
    expected_outcome: str,
    raw_expected: bool,
    expected_calls: int,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    sleeps: list[float] = []

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome == expected_outcome
    assert result.reportable is True
    assert result.trajectory is None
    assert (result.raw_provider_response_ref is not None) is raw_expected
    assert len(transport.calls) == expected_calls

    report = json.loads(
        (config.output_dir / result.provider_report_ref).read_text(encoding="utf-8")
    )
    assert report["outcome"] == expected_outcome
    assert report["reportable"] is True
