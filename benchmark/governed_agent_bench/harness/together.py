"""Together AI adapter for GovernedAgentBench model-action runs.

The adapter is deliberately thin: it renders the existing deployment
prompt, sends it through an injectable transport, records provider-call
metadata, parses the model output through ``parse_model_action``, and
delegates execution to the deterministic harness.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from governed_agent_bench.harness.core import (
    HarnessConfig,
    HarnessError,
    load_manifest_snapshot,
    render_prompt,
    run_operator_action,
)
from governed_agent_bench.harness.model_actions import parse_model_action
from governed_agent_bench.model_roster import roster_condition


TOGETHER_API_KEY_ENV = "TOGETHER_API_KEY"
TOGETHER_CHAT_COMPLETIONS_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_DEFAULT_CONDITION_ID = "option_b_qwen25_7b_together"
TOGETHER_DEFAULT_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct-Turbo"
SYNTHETIC_DATA_BOUNDARY = "synthetic_governed_agent_bench_fixtures_only"

OUTCOME_EXECUTED = "executed"
OUTCOME_TIMEOUT = "timeout"
OUTCOME_INVALID_JSON = "invalid_json"
OUTCOME_PROVIDER_REFUSAL = "provider_refusal"
OUTCOME_ADAPTER_FAILURE = "adapter_failure"
REPORTABLE_OUTCOMES = frozenset({
    OUTCOME_TIMEOUT,
    OUTCOME_INVALID_JSON,
    OUTCOME_PROVIDER_REFUSAL,
    OUTCOME_ADAPTER_FAILURE,
})

TOGETHER_QWEN25_7B_INPUT_USD_PER_1M_TOKENS = 0.30
TOGETHER_QWEN25_7B_OUTPUT_USD_PER_1M_TOKENS = 0.30
TOGETHER_QWEN25_7B_PRICING: dict[str, str | float] = {
    "currency": "USD",
    "input_usd_per_1m_tokens": TOGETHER_QWEN25_7B_INPUT_USD_PER_1M_TOKENS,
    "output_usd_per_1m_tokens": TOGETHER_QWEN25_7B_OUTPUT_USD_PER_1M_TOKENS,
    "pricing_snapshot_date": "2026-05-19",
    "pricing_source": "Together AI public pricing as of 2026-05-19",
}
_PROVIDER_REFUSAL_FINISH_REASONS = frozenset({
    "content_filter",
    "refusal",
    "safety",
})


class TogetherTransport(Protocol):
    """Transport boundary for Together chat-completion calls."""

    def complete(
        self,
        request: Mapping[str, Any],
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        """Return the raw provider response as a JSON object."""


class TogetherHTTPTransport:
    """Minimal stdlib HTTP transport for the Together chat API."""

    def __init__(self, endpoint: str = TOGETHER_CHAT_COMPLETIONS_URL) -> None:
        self.endpoint = endpoint

    def complete(
        self,
        request: Mapping[str, Any],
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        payload = json.dumps(request, separators=(",", ":")).encode("utf-8")
        http_request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(
                http_request,
                timeout=timeout_seconds,
            ) as response:
                body = response.read().decode("utf-8")
        except socket.timeout as exc:
            raise TimeoutError("Together request timed out") from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise TimeoutError("Together request timed out") from exc
            raise HarnessError(f"Together request failed: {exc}") from exc

        raw = json.loads(body)
        if not isinstance(raw, dict):
            raise HarnessError("Together response was not a JSON object")
        return raw


@dataclass(frozen=True)
class TogetherAdapterResult:
    """Outcome of one Together model-action adapter call."""

    outcome: str
    reportable: bool
    raw_provider_response_ref: str | None
    provider_report_ref: str
    provider_output_text: str | None
    parsed_action: dict[str, Any] | None
    token_usage: dict[str, int | None]
    cost_estimate: dict[str, Any]
    trajectory: dict[str, Any] | None
    error: str | None


def together_default_condition() -> dict[str, Any]:
    """Load the predeclared Together Option B default condition."""

    return roster_condition(TOGETHER_DEFAULT_CONDITION_ID)


def build_together_chat_request(
    task: dict[str, Any],
    condition: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build the Together chat request from the held-constant prompt."""

    _ensure_together_condition(condition)
    manifest_id = _manifest_id(task)
    prompt = render_prompt(
        task,
        load_manifest_snapshot(manifest_id),
        str(condition["prompt_id"]),
    )
    decoding = condition["decoding_settings"]
    request = {
        "model": condition["model_id"],
        "messages": _messages_from_rendered_prompt(prompt["rendered_prompt"]),
        "temperature": decoding["temperature"],
        "top_p": decoding["top_p"],
        "max_tokens": decoding["max_tokens"],
    }
    return request, {
        "prompt_template_id": prompt["prompt_template_id"],
        "prompt_template_hash": prompt["prompt_template_hash"],
        "prompt_template_file_hash": prompt["prompt_template_file_hash"],
    }


def run_together_model_action(
    task: dict[str, Any],
    condition: dict[str, Any],
    config: HarnessConfig,
    *,
    transport: TogetherTransport | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 60.0,
    write_trajectory: bool = True,
) -> TogetherAdapterResult:
    """Call Together once and run the emitted operator action if valid."""

    _ensure_together_config(condition, config)
    request, prompt_metadata = build_together_chat_request(task, condition)
    call_id = _provider_call_id(task, condition, config, prompt_metadata)
    env_map = os.environ if env is None else env
    usage = _empty_usage()
    cost = estimate_together_cost(usage)

    try:
        api_key = _api_key_from_env(env_map)
    except HarnessError as exc:
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=None,
            provider_output_text=None,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )

    provider = transport or TogetherHTTPTransport()
    try:
        raw_response = provider.complete(
            request,
            api_key=api_key,
            timeout_seconds=timeout_seconds,
        )
    except TimeoutError as exc:
        return _record_adapter_result(
            outcome=OUTCOME_TIMEOUT,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=None,
            provider_output_text=None,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )
    except Exception as exc:
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=None,
            provider_output_text=None,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )

    usage = token_usage_from_together_response(raw_response)
    cost = estimate_together_cost(usage)
    if _is_provider_refusal(raw_response):
        return _record_adapter_result(
            outcome=OUTCOME_PROVIDER_REFUSAL,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=raw_response,
            provider_output_text=None,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error="Together response indicates provider-level refusal",
        )

    try:
        provider_output_text = _provider_output_text(raw_response)
    except HarnessError as exc:
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=raw_response,
            provider_output_text=None,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )

    try:
        parsed_action = parse_model_action(provider_output_text)
    except HarnessError as exc:
        return _record_adapter_result(
            outcome=OUTCOME_INVALID_JSON,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=raw_response,
            provider_output_text=provider_output_text,
            parsed_action=None,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )

    try:
        trajectory = run_operator_action(
            task,
            parsed_action,
            config,
            write_trajectory=write_trajectory,
        )
    except Exception as exc:
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_response=raw_response,
            provider_output_text=provider_output_text,
            parsed_action=parsed_action,
            token_usage=usage,
            cost_estimate=cost,
            trajectory=None,
            error=str(exc),
        )

    return _record_adapter_result(
        outcome=OUTCOME_EXECUTED,
        call_id=call_id,
        config=config,
        condition=condition,
        task=task,
        prompt_metadata=prompt_metadata,
        raw_response=raw_response,
        provider_output_text=provider_output_text,
        parsed_action=parsed_action,
        token_usage=usage,
        cost_estimate=cost,
        trajectory=trajectory,
        error=None,
    )


def token_usage_from_together_response(
    raw_response: Mapping[str, Any],
) -> dict[str, int | None]:
    """Extract token usage from a Together chat-completion response."""

    usage = raw_response.get("usage")
    if not isinstance(usage, Mapping):
        return _empty_usage()
    prompt_tokens = _nonnegative_int(usage.get("prompt_tokens"))
    completion_tokens = _nonnegative_int(
        usage.get("completion_tokens", usage.get("output_tokens"))
    )
    total_tokens = _nonnegative_int(usage.get("total_tokens"))
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
    }


def estimate_together_cost(
    token_usage: Mapping[str, int | None],
) -> dict[str, Any]:
    """Estimate Together spend from recorded usage and roster rates."""

    prompt_tokens = token_usage.get("prompt_tokens")
    completion_tokens = token_usage.get("completion_tokens")
    if prompt_tokens is None or completion_tokens is None:
        total_cost = None
        input_cost = None
        output_cost = None
    else:
        input_cost = (
            prompt_tokens
            * TOGETHER_QWEN25_7B_INPUT_USD_PER_1M_TOKENS
            / 1_000_000
        )
        output_cost = (
            completion_tokens
            * TOGETHER_QWEN25_7B_OUTPUT_USD_PER_1M_TOKENS
            / 1_000_000
        )
        total_cost = input_cost + output_cost
    return {
        **TOGETHER_QWEN25_7B_PRICING,
        "input_cost_usd": _round_cost(input_cost),
        "output_cost_usd": _round_cost(output_cost),
        "estimated_total_cost_usd": _round_cost(total_cost),
    }


def _record_adapter_result(
    *,
    outcome: str,
    call_id: str,
    config: HarnessConfig,
    condition: dict[str, Any],
    task: dict[str, Any],
    prompt_metadata: dict[str, str],
    raw_response: dict[str, Any] | None,
    provider_output_text: str | None,
    parsed_action: dict[str, Any] | None,
    token_usage: dict[str, int | None],
    cost_estimate: dict[str, Any],
    trajectory: dict[str, Any] | None,
    error: str | None,
) -> TogetherAdapterResult:
    raw_ref = (
        _write_json_artifact(
            config.output_dir,
            "provider_responses",
            f"{call_id}_raw",
            raw_response,
        )
        if raw_response is not None
        else None
    )
    report = {
        "schema_version": "governed_agent_bench.model_adapter_call.v1",
        "adapter": "together_ai_chat_completions",
        "outcome": outcome,
        "reportable": outcome in REPORTABLE_OUTCOMES,
        "task_id": task["task_id"],
        "condition_id": condition["condition_id"],
        "system_id": config.system_id,
        "runtime_mode": config.runtime_mode,
        "model_id": condition["model_id"],
        "provider": condition["provider"],
        "prompt_metadata": prompt_metadata,
        "raw_provider_response_ref": raw_ref,
        "parsed_action": parsed_action,
        "token_usage": token_usage,
        "cost_estimate": cost_estimate,
        "trajectory_id": trajectory["trajectory_id"] if trajectory else None,
        "error": error,
    }
    report_ref = _write_json_artifact(
        config.output_dir,
        "provider_reports",
        f"{call_id}_report",
        report,
    )
    return TogetherAdapterResult(
        outcome=outcome,
        reportable=outcome in REPORTABLE_OUTCOMES,
        raw_provider_response_ref=raw_ref,
        provider_report_ref=report_ref,
        provider_output_text=provider_output_text,
        parsed_action=parsed_action,
        token_usage=token_usage,
        cost_estimate=cost_estimate,
        trajectory=trajectory,
        error=error,
    )


def _api_key_from_env(env: Mapping[str, str]) -> str:
    api_key = env.get(TOGETHER_API_KEY_ENV, "").strip()
    if not api_key:
        raise HarnessError(f"{TOGETHER_API_KEY_ENV} is required")
    return api_key


def _ensure_together_condition(condition: dict[str, Any]) -> None:
    if condition.get("provider") != "Together AI":
        raise HarnessError("Together adapter requires provider='Together AI'")
    if condition.get("model_id") != TOGETHER_DEFAULT_MODEL_ID:
        raise HarnessError(
            f"Together adapter is scoped to {TOGETHER_DEFAULT_MODEL_ID!r}"
        )
    if condition.get("data_boundary") != SYNTHETIC_DATA_BOUNDARY:
        raise HarnessError("Together adapter requires synthetic benchmark data only")
    if condition.get("prompt_id") != "deployment_full_v1":
        raise HarnessError("Together adapter requires deployment_full_v1")


def _ensure_together_config(
    condition: dict[str, Any],
    config: HarnessConfig,
) -> None:
    _ensure_together_condition(condition)
    if config.model_class != "cloud":
        raise HarnessError("Together adapter requires model_class='cloud'")
    if config.invocation_context != "agent":
        raise HarnessError("Together adapter requires invocation_context='agent'")
    if config.system_id != condition["system_id"]:
        raise HarnessError("HarnessConfig.system_id must match roster condition")
    if config.prompt_template_id != condition["prompt_id"]:
        raise HarnessError("HarnessConfig.prompt_template_id must match condition")


def _manifest_id(task: dict[str, Any]) -> str:
    try:
        return str(task["allowed_context"]["manifest_ref"])
    except KeyError as exc:
        raise HarnessError("task missing allowed_context.manifest_ref") from exc


def _messages_from_rendered_prompt(rendered_prompt: str) -> list[dict[str, str]]:
    marker = "\nUSER:\n"
    try:
        system_text, user_text = rendered_prompt.rsplit(marker, 1)
    except ValueError as exc:
        raise HarnessError("rendered deployment prompt missing USER block") from exc
    return [
        {"role": "system", "content": system_text},
        {"role": "user", "content": user_text},
    ]


def _provider_call_id(
    task: dict[str, Any],
    condition: dict[str, Any],
    config: HarnessConfig,
    prompt_metadata: Mapping[str, str],
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "task_id": task["task_id"],
                "condition_id": condition["condition_id"],
                "system_id": config.system_id,
                "runtime_mode": config.runtime_mode,
                "prompt_template_hash": prompt_metadata["prompt_template_hash"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"{task['task_id']}_{config.system_id}_{digest}"


def _is_provider_refusal(raw_response: Mapping[str, Any]) -> bool:
    error = raw_response.get("error")
    if isinstance(error, Mapping):
        error_type = str(error.get("type", "")).lower()
        error_code = str(error.get("code", "")).lower()
        if error_type in _PROVIDER_REFUSAL_FINISH_REASONS:
            return True
        if error_code in _PROVIDER_REFUSAL_FINISH_REASONS:
            return True
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return False
    first = choices[0]
    if not isinstance(first, Mapping):
        return False
    finish_reason = str(first.get("finish_reason", "")).lower()
    if finish_reason in _PROVIDER_REFUSAL_FINISH_REASONS:
        return True
    message = first.get("message")
    return isinstance(message, Mapping) and bool(message.get("refusal"))


def _provider_output_text(raw_response: Mapping[str, Any]) -> str:
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        raise HarnessError("Together response has no choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise HarnessError("Together response choice is not an object")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise HarnessError("Together response choice has no message object")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    raise HarnessError("Together response message has no text content")


def _empty_usage() -> dict[str, int | None]:
    return {
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_tokens": None,
    }


def _nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value >= 0:
        return value
    return None


def _round_cost(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 8)


def _write_json_artifact(
    output_dir: Path,
    subdir: str,
    stem: str,
    payload: Mapping[str, Any],
) -> str:
    artifact_dir = output_dir / subdir
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{stem}.json"
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path.relative_to(output_dir).as_posix()
