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
    HarnessError,
    build_together_chat_request,
    estimate_together_cost,
    harness_config_for_roster_condition,
    load_task,
    run_together_model_action,
)
from governed_agent_bench.harness.retry import TransportFailure  # noqa: E402
from governed_agent_bench.harness.together import (  # noqa: E402
    OUTCOME_ADAPTER_FAILURE,
    OUTCOME_CONTEXT_OVERFLOW,
    OUTCOME_EXECUTED,
    OUTCOME_LENGTH_TRUNCATION,
    OUTCOME_PROVIDER_REFUSAL,
    OUTCOME_TIMEOUT,
    TOGETHER_ALLOWED_MODEL_IDS,
    TOGETHER_DEFAULT_MODEL_ID,
    TOGETHER_QWEN3_235B_INSTRUCT_MODEL_ID,
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
    task = load_task("gab_l1_operate_route")
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
    assert prompt_metadata["prompt_template_id"] == "deployment_full_v2"
    assert len(prompt_metadata["prompt_template_hash"]) == 64


def test_together_adapter_records_raw_response_usage_cost_and_trajectory(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
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
        "usage_complete": True,
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
    task = load_task("gab_l2_validation_told")
    condition = _condition()
    config = _config(tmp_path, condition)
    transport = FakeTransport(
        responses=[
            _command_response("hai capabilities"),
            _command_response("hai today"),
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
    task = load_task("gab_l1_operate_route")
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
    task = load_task("gab_l1_operate_route")
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
    task = load_task("gab_l1_operate_route")
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
        # IB-3: HTTP 422 (context overflow) is deterministic (no retry) and
        # reports as its own outcome, never a generic adapter failure.
        (
            FakeTransport(
                exc=TransportFailure(
                    kind="http_status",
                    status_code=422,
                    message=(
                        'Together HTTP 422: {"error": {"message": '
                        '"tokens + max_new_tokens must be <= context length"}}'
                    ),
                )
            ),
            OUTCOME_CONTEXT_OVERFLOW,
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
    task = load_task("gab_l1_operate_route")
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


def test_together_adapter_records_raw_422_body_in_error(tmp_path: Path) -> None:
    """IB-3: the provider's raw 422 error body is recorded with the
    context_overflow outcome, not discarded."""

    body = '{"error": {"message": "input tokens exceed the model context"}}'
    transport = FakeTransport(
        exc=TransportFailure(
            kind="http_status",
            status_code=422,
            message=f"Together HTTP 422: {body}",
        )
    )
    result = run_together_model_action(
        load_task("gab_l1_operate_route"),
        _condition(),
        _config(tmp_path, _condition()),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_CONTEXT_OVERFLOW
    assert result.reportable is True
    assert body in str(result.error)
    assert result.turn_records[-1].provider_outcome == OUTCOME_CONTEXT_OVERFLOW


# --- Audit fix A1: cost routing by model_id -----------------------------------


def test_estimate_together_cost_routes_rates_by_model_id() -> None:
    usage = {"prompt_tokens": 1_000_000, "completion_tokens": 1_000_000, "total_tokens": 2_000_000}

    qwen7b = estimate_together_cost(usage, TOGETHER_DEFAULT_MODEL_ID)
    assert qwen7b["input_cost_usd"] == 0.30
    assert qwen7b["output_cost_usd"] == 0.30
    assert qwen7b["estimated_total_cost_usd"] == 0.60

    qwen235b = estimate_together_cost(usage, TOGETHER_QWEN3_235B_INSTRUCT_MODEL_ID)
    assert qwen235b["input_cost_usd"] == 0.20
    assert qwen235b["output_cost_usd"] == 0.60
    assert qwen235b["estimated_total_cost_usd"] == 0.80
    assert "Qwen3 235B" in str(qwen235b["pricing_source"])


def test_estimate_together_cost_rejects_unknown_model_id() -> None:
    # A metered run must never silently misprice: an unpriced model raises.
    with pytest.raises(HarnessError, match="no Together pricing entry"):
        estimate_together_cost(
            {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
            "mistralai/Mistral-Small-24B-Instruct-2501",
        )


def test_together_adapter_prices_primary_condition_with_its_own_rates(
    tmp_path: Path,
) -> None:
    # D-56: the primary is now MiniMax-M3 ($0.30/$1.20); the deprecated 235B is
    # non-run_-prefixed and no longer dispatchable via the allowlist.
    task = load_task("gab_l1_operate_route")
    condition = roster_condition("run_primary_minimax_m3")
    config = _config(tmp_path, condition)
    transport = FakeTransport(responses=[_final_response()])

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    # 1000 prompt * $0.30/1M + 500 completion * $1.20/1M, per-model rates (NOT a
    # flat rate applied to every model).
    assert result.cost_estimate["input_cost_usd"] == 0.0003
    assert result.cost_estimate["output_cost_usd"] == 0.0006
    assert result.cost_estimate["estimated_total_cost_usd"] == 0.0009
    assert result.cost_estimate["input_usd_per_1m_tokens"] == 0.30
    assert result.cost_estimate["output_usd_per_1m_tokens"] == 1.20


# --- Audit fix A2: per-rep raw-response artifacts must not collide ------------


def test_together_adapter_reps_write_distinct_provider_artifacts(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
    condition = _condition()
    config = _config(tmp_path, condition)

    results = []
    for rep in range(2):
        results.append(
            run_together_model_action(
                task,
                condition,
                config,
                rep=rep,
                transport=FakeTransport(responses=[_final_response(f"rep {rep}")]),
                env={TOGETHER_API_KEY_ENV: "mock-api-key"},
            )
        )

    refs = [result.raw_provider_response_refs[0] for result in results]
    assert refs[0] != refs[1]
    assert "_rep0_" in refs[0] and "_rep1_" in refs[1]
    assert results[0].provider_report_ref != results[1].provider_report_ref
    # Both artifacts exist side by side: rep 1 did not overwrite rep 0.
    for ref, rep in zip(refs, range(2)):
        raw = json.loads((config.output_dir / ref).read_text(encoding="utf-8"))
        assert f"rep {rep}" in raw["choices"][0]["message"]["content"]
    # Trajectories are per-rep too.
    assert (
        results[0].trajectory["trajectory_id"] != results[1].trajectory["trajectory_id"]
    )


def test_together_adapter_rejects_negative_rep(tmp_path: Path) -> None:
    task = load_task("gab_l1_operate_route")
    condition = _condition()
    with pytest.raises(HarnessError, match="rep must be non-negative"):
        run_together_model_action(
            task,
            condition,
            _config(tmp_path, condition),
            rep=-1,
            transport=FakeTransport(responses=[_final_response()]),
            env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        )


# --- Audit fix A3: finish_reason=length is a reportable truncation outcome ----


def test_together_adapter_reports_length_truncation_not_invalid_output(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    truncated = {
        "id": "mock-truncated",
        "choices": [
            {
                "finish_reason": "length",
                "message": {
                    "role": "assistant",
                    "content": '{"action_type": "final", "final_te',
                },
            }
        ],
        "usage": {"prompt_tokens": 1000, "completion_tokens": 2048},
    }
    transport = FakeTransport(responses=[truncated])

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    # A harness budget artifact, reported like timeout -- never scored as a
    # model formatting violation via the invalid_output path.
    assert result.outcome == OUTCOME_LENGTH_TRUNCATION
    assert result.reportable is True
    assert len(transport.calls) == 1  # deterministic: no retry
    assert result.turn_records[-1].provider_outcome == OUTCOME_LENGTH_TRUNCATION
    assert result.turn_records[-1].stop_reason == OUTCOME_LENGTH_TRUNCATION
    assert result.turn_records[-1].invalid_output is None
    assert result.trajectory is None
    report = json.loads(
        (config.output_dir / result.provider_report_ref).read_text(encoding="utf-8")
    )
    assert report["outcome"] == OUTCOME_LENGTH_TRUNCATION
    assert report["reportable"] is True
    # Truncated usage still counts toward the aggregate (real spend).
    assert result.token_usage["completion_tokens"] == 2048


# --- Audit fix A7: decoding pass-through ---------------------------------------


def test_build_together_request_passes_vendor_decoding_through_allowlist() -> None:
    task = load_task("gab_l1_operate_route")
    condition = dict(_condition())
    condition["decoding_settings"] = {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "min_p": 0.0,
        "repetition_penalty": 1.05,
        "max_tokens": 2048,
        "seed": 1234,
        "stop": ["</answer>"],
    }

    request, _ = build_together_chat_request(task, condition)

    assert request["temperature"] == 0.7
    assert request["top_p"] == 0.8
    assert request["top_k"] == 20
    assert request["min_p"] == 0.0
    assert request["repetition_penalty"] == 1.05
    assert request["max_tokens"] == 2048
    assert request["seed"] == 1234
    assert request["stop"] == ["</answer>"]


def test_build_together_request_skips_non_numeric_seed_placeholder() -> None:
    task = load_task("gab_l1_operate_route")
    condition = _condition()
    assert condition["decoding_settings"]["seed"] == "provider_does_not_support_seed"

    request, _ = build_together_chat_request(task, condition)

    assert "seed" not in request
    assert request["temperature"] == 0
    assert request["top_p"] == 1
    assert request["max_tokens"] == 2048


def test_build_together_request_rejects_unknown_decoding_key() -> None:
    task = load_task("gab_l1_operate_route")
    condition = dict(_condition())
    condition["decoding_settings"] = {
        **condition["decoding_settings"],
        "typical_p": 0.9,
    }

    with pytest.raises(HarnessError, match="unsupported keys.*typical_p"):
        build_together_chat_request(task, condition)


# --- Audit fix A8: allowlist derived from the roster ---------------------------


def test_together_allowlist_is_derived_from_roster_conditions() -> None:
    # D-56/D-55.1: the allowlist derives from the run_-prefixed ladder only.
    # The current primary (MiniMax-M3) and below-floor (7B) are allowed...
    assert "MiniMaxAI/MiniMax-M3" in TOGETHER_ALLOWED_MODEL_IDS
    assert TOGETHER_DEFAULT_MODEL_ID in TOGETHER_ALLOWED_MODEL_IDS
    # ...the deprecated 235B (non-run_, retained only for provenance) is NOT
    # certifiable, and roster-excluded smoke candidates stay gone.
    assert TOGETHER_QWEN3_235B_INSTRUCT_MODEL_ID not in TOGETHER_ALLOWED_MODEL_IDS
    assert "mistralai/Mistral-Small-24B-Instruct-2501" not in TOGETHER_ALLOWED_MODEL_IDS
    assert "google/gemma-4-31B-it" not in TOGETHER_ALLOWED_MODEL_IDS


def test_together_adapter_rejects_non_roster_model_id() -> None:
    task = load_task("gab_l1_operate_route")
    condition = dict(_condition())
    condition["model_id"] = "mistralai/Mistral-Small-24B-Instruct-2501"

    with pytest.raises(HarnessError, match="model_id must be one of"):
        build_together_chat_request(task, condition)


# --- Audit fix A9: partial usage sums available turns --------------------------


def test_together_adapter_partial_usage_sums_turns_and_flags_incomplete(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_operate_route")
    condition = _condition()
    config = _config(tmp_path, condition)
    missing_usage = _command_response()
    del missing_usage["usage"]
    transport = FakeTransport(responses=[missing_usage, _final_response()])

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == OUTCOME_EXECUTED
    # The turn with usage is still counted (old behavior nulled the whole
    # aggregate, silently under-counting the cost cap); the flag marks the
    # aggregate as a lower bound.
    assert result.token_usage == {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
        "usage_complete": False,
    }
    assert result.cost_estimate["estimated_total_cost_usd"] == 0.00045
