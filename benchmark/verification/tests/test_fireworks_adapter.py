"""Mocked Fireworks AI adapter checks (D-O-01 fallback substrate).

Mirrors test_together_adapter.py. Two intentional divergences from the
Together adapter are asserted here: the on-demand GPU-hour cost model
(no per-token USD total) and the deployment-qualified request-model
override. No live Fireworks calls anywhere.
"""

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
    FIREWORKS_API_KEY_ENV,
    HarnessConfig,
    HarnessError,
    build_fireworks_chat_request,
    estimate_fireworks_cost,
    harness_config_for_roster_condition,
    load_task,
    run_fireworks_model_action,
)
from governed_agent_bench.harness.fireworks import (  # noqa: E402
    FIREWORKS_DEFAULT_MODEL_ID,
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


# Execution requires a deployment/router-qualified model string; the roster
# base id is rejected (R4). Mocked runs use a fake deployment value.
MOCK_DEPLOYMENT_MODEL = "accounts/fireworks/deployments/mock-deploy"


def _condition() -> dict[str, Any]:
    return roster_condition("option_b_fallback_qwen25_32b_fireworks")


def _config(tmp_path: Path, condition: dict[str, Any]) -> HarnessConfig:
    return harness_config_for_roster_condition(
        condition,
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )


def _raw_fireworks_response(content: str) -> dict[str, Any]:
    return {
        "id": "mock-fireworks-response",
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
    return _raw_fireworks_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": command,
            "args": {"--json": True} if command == "hai capabilities" else {},
            "reason": "Inspect the command surface.",
        })
    )


def _final_response(text: str = "Done.") -> dict[str, Any]:
    return _raw_fireworks_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "final",
            "final_text": text,
            "reason": "No further action is needed.",
        })
    )


def _refusal_response() -> dict[str, Any]:
    return _raw_fireworks_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "refusal",
            "reason": "The request is outside the governed surface.",
            "final_text": "I cannot do that.",
        })
    )


def test_build_fireworks_request_uses_deployment_prompt() -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()

    request, prompt_metadata = build_fireworks_chat_request(task, condition)

    assert request["model"] == FIREWORKS_DEFAULT_MODEL_ID
    assert request["temperature"] == 0
    assert request["top_p"] == 1
    assert request["max_tokens"] == 2048
    assert request["messages"][0]["role"] == "system"
    assert "CAPABILITIES MANIFEST" in request["messages"][0]["content"]
    assert request["messages"][1]["role"] == "user"
    assert task["user_prompt"] in request["messages"][1]["content"]
    assert prompt_metadata["prompt_template_id"] == "deployment_full_v1"
    assert len(prompt_metadata["prompt_template_hash"]) == 64


def test_fireworks_request_model_override_sets_wire_model_only() -> None:
    # On-demand serving (D1): the deployment-qualified model string is
    # supplied at run time; the guard still validates the roster base id.
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    deployment_model = f"{FIREWORKS_DEFAULT_MODEL_ID}#dom-pilot-deploy"

    request, _ = build_fireworks_chat_request(
        task, condition, request_model=deployment_model
    )
    assert request["model"] == deployment_model

    # Default (no override) falls back to the roster base id.
    default_request, _ = build_fireworks_chat_request(task, condition)
    assert default_request["model"] == FIREWORKS_DEFAULT_MODEL_ID


@pytest.mark.parametrize(
    "bad_request_model",
    [
        None,
        "",
        "   ",
        FIREWORKS_DEFAULT_MODEL_ID,
        f"  {FIREWORKS_DEFAULT_MODEL_ID}  ",
    ],
)
def test_fireworks_execution_rejects_unqualified_request_model(
    tmp_path: Path,
    bad_request_model: str | None,
) -> None:
    # R4: execution requires a deployment/router-qualified model on every path.
    # None, empty/whitespace (which `request_model or base_id` would silently
    # fall back to the base id), and the non-serverless base id (even padded)
    # are rejected LOCALLY before any network call, independent of transport.
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(_final_response("should not run"))

    with pytest.raises(HarnessError):
        run_fireworks_model_action(
            task,
            condition,
            config,
            transport=transport,
            request_model=bad_request_model,
            env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
        )
    assert transport.calls == []


def test_fireworks_wire_model_provenance_classifies_and_hashes_distinctly(
    tmp_path: Path,
) -> None:
    # R5: a router-form value classifies as "router"; distinct wire models
    # produce distinct hashes; the raw string never enters the report.
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    router_model = "accounts/fireworks/routers/mock-router"

    def _run(request_model: str) -> dict[str, Any]:
        config = _config(tmp_path / request_model.replace("/", "_"), condition)
        result = run_fireworks_model_action(
            task,
            condition,
            config,
            transport=FakeTransport(_final_response("Done.")),
            request_model=request_model,
            env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
        )
        report_text = (
            config.output_dir / result.provider_report_ref
        ).read_text(encoding="utf-8")
        assert request_model not in report_text
        return json.loads(report_text)

    router_report = _run(router_model)
    deployment_report = _run(MOCK_DEPLOYMENT_MODEL)

    assert router_report["wire_model_ref_type"] == "router"
    assert router_report["wire_model_is_deployment_qualified"] is True
    assert deployment_report["wire_model_ref_type"] == "deployment"
    assert (
        router_report["wire_model_sha256"]
        != deployment_report["wire_model_sha256"]
    )


def test_fireworks_cost_estimate_reports_on_demand_semantics() -> None:
    # Qwen2.5-32B is on-demand GPU-second billed, not serverless per-token,
    # so no USD total is derivable from token usage (C1). per_step_usd_available
    # / cost_basis are the signals that keep B2 from summing None as zero (R2).
    estimate = estimate_fireworks_cost({
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
    })
    assert estimate["billing_model"] == "on_demand_gpu_time"
    assert estimate["billing_granularity"] == "gpu_second"
    assert estimate["per_step_usd_available"] is False
    assert estimate["cost_basis"] == "condition_level"
    assert estimate["estimated_total_cost_usd"] is None
    assert estimate["input_cost_usd"] is None
    assert estimate["output_cost_usd"] is None
    reference = estimate["on_demand_gpu_hour_reference"]
    assert reference["H100_80gb"] == 7.0
    assert reference["B200_180gb"] == 10.0
    assert reference["B300_288gb"] == 12.0
    assert reference["snapshot_date"] == "2026-06-03"
    assert "fireworks.ai/pricing" in reference["source"]


def test_fireworks_adapter_records_raw_response_usage_cost_and_trajectory(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    raw_responses = [_command_response(), _final_response()]
    transport = FakeTransport(responses=raw_responses)

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
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
    # On-demand cost: no per-token USD total, even with usage present.
    assert result.cost_estimate["billing_model"] == "on_demand_gpu_time"
    assert result.cost_estimate["per_step_usd_available"] is False
    assert result.cost_estimate["estimated_total_cost_usd"] is None

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
    # cost_usd_estimate is present but None for the on-demand adapter.
    assert command_meta["cost_usd_estimate"] is None
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
    # Turn records round-trip the per-turn (None) cost into the report.
    assert result.turn_records[0].cost_usd_estimate is None
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
    assert report["adapter"] == "fireworks_ai_chat_completions"
    # R5: wire-model provenance is recorded without leaking the raw string.
    assert MOCK_DEPLOYMENT_MODEL not in report_text
    assert "mock-deploy" not in report_text
    assert len(report["wire_model_sha256"]) == 64
    assert report["wire_model_ref_type"] == "deployment"
    assert report["wire_model_is_deployment_qualified"] is True
    assert report["outcome"] == OUTCOME_EXECUTED
    assert report["raw_provider_response_ref"] == result.raw_provider_response_ref
    assert report["raw_provider_response_refs"] == result.raw_provider_response_refs
    assert report["turn_records"][0]["parsed_action"]["command"] == "hai capabilities"
    assert report["token_usage"] == result.token_usage
    assert report["cost_estimate"] == result.cost_estimate
    assert report["trajectory_id"] == result.trajectory["trajectory_id"]


def test_fireworks_adapter_preserves_ordered_cross_turn_steps(
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

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
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
def test_fireworks_adapter_terminates_on_final_or_refusal(
    tmp_path: Path,
    raw_response: dict[str, Any],
    expected_step_type: str,
    expected_stop_reason: str,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(raw_response)

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert result.trajectory is not None
    assert len(transport.calls) == 1
    assert [step["step_type"] for step in result.trajectory["steps"]] == [
        expected_step_type
    ]
    assert result.turn_records[-1].stop_reason == expected_stop_reason


def test_fireworks_adapter_records_malformed_output_as_invalid_output(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(
        responses=[
            _raw_fireworks_response("not json"),
            _final_response("Recovered after parse feedback."),
        ]
    )

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
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


def test_fireworks_adapter_reads_api_key_from_environment_only(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(_raw_fireworks_response("{}"))

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={},
    )

    assert result.outcome == OUTCOME_ADAPTER_FAILURE
    assert result.reportable is True
    assert FIREWORKS_API_KEY_ENV in str(result.error)
    assert transport.calls == []


@pytest.mark.parametrize(
    ("transport", "expected_outcome", "raw_expected", "expected_calls"),
    [
        # A timeout is retried to exhaustion (1 initial + 3 retries) but
        # still surfaces the same OUTCOME_TIMEOUT after N attempts.
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
def test_fireworks_adapter_reports_failure_outcomes(
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

    result = run_fireworks_model_action(
        task,
        condition,
        config,
        transport=transport,
        request_model=MOCK_DEPLOYMENT_MODEL,
        env={FIREWORKS_API_KEY_ENV: "mock-api-key"},
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
