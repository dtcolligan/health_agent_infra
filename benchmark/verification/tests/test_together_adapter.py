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
    OUTCOME_INVALID_JSON,
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
        exc: Exception | None = None,
    ) -> None:
        self.response = response or {}
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
        return self.response


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
    raw_response = _raw_together_response(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": "hai capabilities",
            "args": {"--json": True},
            "reason": "Inspect the command surface.",
        })
    )
    transport = FakeTransport(raw_response)

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
    assert result.parsed_action is not None
    assert result.parsed_action["command"] == "hai capabilities"
    assert result.trajectory is not None
    assert result.trajectory["model_class"] == "cloud"
    assert result.trajectory["system_id"] == condition["system_id"]
    assert result.token_usage == {
        "prompt_tokens": 1000,
        "completion_tokens": 500,
        "total_tokens": 1500,
    }
    assert result.cost_estimate["estimated_total_cost_usd"] == 0.00045

    assert transport.calls == [
        {
            "request": transport.calls[0]["request"],
            "api_key": "mock-api-key",
            "timeout_seconds": 12.5,
        }
    ]
    assert "mock-api-key" not in json.dumps(transport.calls[0]["request"])

    assert result.raw_provider_response_ref is not None
    raw_path = config.output_dir / result.raw_provider_response_ref
    assert json.loads(raw_path.read_text(encoding="utf-8")) == raw_response

    report_path = config.output_dir / result.provider_report_ref
    report_text = report_path.read_text(encoding="utf-8")
    report = json.loads(report_text)
    assert "mock-api-key" not in report_text
    assert report["outcome"] == OUTCOME_EXECUTED
    assert report["raw_provider_response_ref"] == result.raw_provider_response_ref
    assert report["parsed_action"] == result.parsed_action
    assert report["token_usage"] == result.token_usage
    assert report["cost_estimate"] == result.cost_estimate
    assert report["trajectory_id"] == result.trajectory["trajectory_id"]


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
    ("transport", "expected_outcome", "raw_expected"),
    [
        (
            FakeTransport(exc=TimeoutError("mock timeout")),
            OUTCOME_TIMEOUT,
            False,
        ),
        (
            FakeTransport(
                _raw_together_response("not json")
            ),
            OUTCOME_INVALID_JSON,
            True,
        ),
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
        ),
        (
            FakeTransport(exc=RuntimeError("mock adapter failure")),
            OUTCOME_ADAPTER_FAILURE,
            False,
        ),
    ],
)
def test_together_adapter_reports_failure_outcomes(
    tmp_path: Path,
    transport: FakeTransport,
    expected_outcome: str,
    raw_expected: bool,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    condition = _condition()
    config = _config(tmp_path, condition)

    result = run_together_model_action(
        task,
        condition,
        config,
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
    )

    assert result.outcome == expected_outcome
    assert result.reportable is True
    assert result.trajectory is None
    assert (result.raw_provider_response_ref is not None) is raw_expected

    report = json.loads(
        (config.output_dir / result.provider_report_ref).read_text(encoding="utf-8")
    )
    assert report["outcome"] == expected_outcome
    assert report["reportable"] is True
