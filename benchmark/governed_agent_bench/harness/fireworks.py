"""Fireworks AI adapter for GovernedAgentBench model-action runs.

The D-O-01 fallback substrate. It mirrors ``together.py``: it renders the
held-constant deployment prompt, sends accumulated chat messages through
an injectable transport, records provider-call metadata, and delegates
loop execution to the provider-neutral model-action harness. The retry
algorithm itself is single-sourced in ``retry.py``; this adapter only
reuses it.

Two intentional divergences from ``together.py`` (ratified WP-A6):

- Cost. Qwen2.5-32B on Fireworks is served on-demand (GPU-hour billed),
  not serverless per-token, so this adapter emits NO per-token USD total.
  ``estimate_fireworks_cost`` reports the on-demand billing model plus a
  GPU-hour reference table; per-turn ``cost_usd_estimate`` is ``None``.
- Request model. On-demand OpenAI-compatible calls address a
  deployment-qualified model value that does not exist before a
  deployment is created. The wire ``model`` field is ``request_model or
  condition["model_id"]``; the guard validates the roster base id.
"""

from __future__ import annotations

import hashlib
import json
import os
import socket
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Protocol

from governed_agent_bench.harness.core import (
    HarnessConfig,
    HarnessError,
    load_manifest_snapshot,
    render_prompt,
)
from governed_agent_bench.harness.model_actions import (
    ModelTurnResult,
    TurnRecord,
    _messages_from_rendered_prompt,
    run_agent_loop,
)
from governed_agent_bench.harness.retry import (
    OutageDetector,
    RetryExhausted,
    RetryPolicy,
    TransportFailure,
    execute_with_retry,
)
from governed_agent_bench.model_roster import roster_condition


FIREWORKS_API_KEY_ENV = "FIREWORKS_API_KEY"
FIREWORKS_CHAT_COMPLETIONS_URL = (
    "https://api.fireworks.ai/inference/v1/chat/completions"
)
FIREWORKS_DEFAULT_CONDITION_ID = "option_b_fallback_qwen25_32b_fireworks"
FIREWORKS_DEFAULT_MODEL_ID = "accounts/fireworks/models/qwen2p5-32b-instruct"
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

# Qwen2.5-32B is on-demand only on Fireworks (serverless "Not supported";
# roster runtime "on-demand deployment"). On-demand is GPU-hour billed, so
# this adapter cannot derive a per-token USD total. The reference table is
# the documented anchor for B2's external wall-time x GPU-rate
# reconciliation; the actual GPU class is recorded at run time, never
# hardcoded into a cost computation.
FIREWORKS_ON_DEMAND_GPU_HOUR_REFERENCE: dict[str, str | float] = {
    "H100_80gb": 7.0,
    "H200_141gb": 7.0,
    "B200_180gb": 10.0,
    "B300_288gb": 12.0,
    "snapshot_date": "2026-06-03",
    "source": "Fireworks AI on-demand GPU pricing (fireworks.ai/pricing) as of 2026-06-03",
}
# Fireworks bills on-demand by GPU-second (per the on-demand deployments docs),
# not per token, so this adapter reports the billing model rather than a USD
# total. The label is precise and the granularity is explicit.
FIREWORKS_BILLING_MODEL = "on_demand_gpu_time"
FIREWORKS_BILLING_GRANULARITY = "gpu_second"
_PROVIDER_REFUSAL_FINISH_REASONS = frozenset({
    "content_filter",
    "refusal",
    "safety",
})


class FireworksTransport(Protocol):
    """Transport boundary for Fireworks chat-completion calls."""

    def complete(
        self,
        request: Mapping[str, Any],
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        """Return the raw provider response as a JSON object."""


class FireworksHTTPTransport:
    """Minimal stdlib HTTP transport for the Fireworks chat API."""

    def __init__(self, endpoint: str = FIREWORKS_CHAT_COMPLETIONS_URL) -> None:
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
            raise TransportFailure(
                kind="timeout", message="Fireworks request timed out"
            ) from exc
        except urllib.error.HTTPError as exc:
            # HTTPError is a URLError subclass and must be caught first so
            # the status code and Retry-After survive for the retry layer.
            raise TransportFailure(
                kind="http_status",
                status_code=exc.code,
                retry_after=exc.headers.get("Retry-After") if exc.headers else None,
                message=f"Fireworks HTTP {exc.code}",
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise TransportFailure(
                    kind="timeout", message="Fireworks request timed out"
                ) from exc
            raise TransportFailure(
                kind="transport_error",
                message=f"Fireworks request failed: {exc}",
            ) from exc

        raw = json.loads(body)
        if not isinstance(raw, dict):
            raise HarnessError("Fireworks response was not a JSON object")
        return raw


class _FireworksTurnFailure(RuntimeError):
    def __init__(
        self,
        outcome: str,
        error: str,
        raw_response: dict[str, Any] | None,
        retry_count: int = 0,
    ) -> None:
        super().__init__(error)
        self.outcome = outcome
        self.error = error
        self.raw_response = raw_response
        self.retry_count = retry_count


@dataclass(frozen=True)
class FireworksAdapterResult:
    """Outcome of one Fireworks model-action adapter call."""

    outcome: str
    reportable: bool
    raw_provider_response_ref: str | None
    raw_provider_response_refs: list[str]
    provider_report_ref: str
    provider_output_text: str | None
    provider_output_texts: list[str]
    turn_records: list[TurnRecord]
    token_usage: dict[str, int | None]
    cost_estimate: dict[str, Any]
    trajectory: dict[str, Any] | None
    error: str | None


def fireworks_default_condition() -> dict[str, Any]:
    """Load the predeclared Fireworks D-O-01 fallback condition."""

    return roster_condition(FIREWORKS_DEFAULT_CONDITION_ID)


def build_fireworks_chat_request(
    task: dict[str, Any],
    condition: dict[str, Any],
    *,
    request_model: str | None = None,
) -> tuple[dict[str, Any], dict[str, str]]:
    """Build the Fireworks chat request from the held-constant prompt.

    ``request_model`` overrides only the wire ``model`` value (the pilot
    supplies a deployment-qualified string for on-demand serving); it
    defaults to the roster base id. The condition guard always validates
    ``condition["model_id"]``, never the override.
    """

    _ensure_fireworks_condition(condition)
    manifest_id = _manifest_id(task)
    prompt = render_prompt(
        task,
        load_manifest_snapshot(manifest_id),
        str(condition["prompt_id"]),
    )
    decoding = condition["decoding_settings"]
    request = {
        "model": request_model or condition["model_id"],
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


def run_fireworks_model_action(
    task: dict[str, Any],
    condition: dict[str, Any],
    config: HarnessConfig,
    *,
    request_model: str | None = None,
    transport: FireworksTransport | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 60.0,
    write_trajectory: bool = True,
    retry_policy: RetryPolicy | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.perf_counter,
    outage_detector: OutageDetector | None = None,
) -> FireworksAdapterResult:
    """Run a Fireworks-backed bounded model-action loop for one task.

    ``request_model`` is the deployment-qualified model string for
    on-demand serving (defaults to the roster base id). ``sleeper`` /
    ``clock`` are injectable so retry backoff is testable without real
    waits. ``outage_detector`` is condition-scoped and owned by the caller
    (A2); this adapter only feeds per-attempt outcomes into it.
    ``retry_policy`` defaults to the §5 policy.
    """

    _ensure_fireworks_config(condition, config)
    _ensure_request_model(condition, request_model)
    request, prompt_metadata = build_fireworks_chat_request(
        task, condition, request_model=request_model
    )
    call_id = _provider_call_id(task, condition, config, prompt_metadata)
    env_map = os.environ if env is None else env
    raw_responses: list[dict[str, Any]] = []
    provider_output_texts: list[str] = []
    token_usage_by_turn: list[dict[str, int | None]] = []
    completed_turn_records: list[TurnRecord] = []

    try:
        api_key = _api_key_from_env(env_map)
    except HarnessError as exc:
        usage = _aggregate_token_usage(token_usage_by_turn)
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            wire_model=request["model"],
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=[],
            token_usage=usage,
            cost_estimate=estimate_fireworks_cost(usage),
            trajectory=None,
            error=str(exc),
        )

    provider = transport or FireworksHTTPTransport()
    policy = retry_policy or RetryPolicy()

    def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
        request_for_turn = {
            **request,
            "messages": [dict(message) for message in messages],
        }
        try:
            retry_outcome = execute_with_retry(
                lambda: provider.complete(
                    request_for_turn,
                    api_key=api_key,
                    timeout_seconds=timeout_seconds,
                ),
                policy=policy,
                sleeper=sleeper,
                clock=clock,
                detector=outage_detector,
            )
        except RetryExhausted as exc:
            outcome = (
                OUTCOME_TIMEOUT
                if exc.last_failure.kind == "timeout"
                else OUTCOME_ADAPTER_FAILURE
            )
            raise _FireworksTurnFailure(
                outcome,
                str(exc.last_failure) or "retry exhausted",
                None,
                retry_count=exc.retry_count,
            ) from exc
        except TransportFailure as exc:
            outcome = (
                OUTCOME_TIMEOUT if exc.kind == "timeout" else OUTCOME_ADAPTER_FAILURE
            )
            raise _FireworksTurnFailure(
                outcome, str(exc), None, retry_count=exc.retry_count
            ) from exc
        except TimeoutError as exc:
            raise _FireworksTurnFailure(OUTCOME_TIMEOUT, str(exc), None) from exc
        except Exception as exc:
            raise _FireworksTurnFailure(
                OUTCOME_ADAPTER_FAILURE,
                str(exc),
                None,
            ) from exc

        raw_response = retry_outcome.response
        raw_responses.append(raw_response)
        usage = token_usage_from_fireworks_response(raw_response)
        token_usage_by_turn.append(usage)
        if _is_provider_refusal(raw_response):
            raise _FireworksTurnFailure(
                OUTCOME_PROVIDER_REFUSAL,
                "Fireworks response indicates provider-level refusal",
                raw_response,
                retry_count=retry_outcome.retry_count,
            )
        try:
            provider_output_text = _provider_output_text(raw_response)
        except HarnessError as exc:
            raise _FireworksTurnFailure(
                OUTCOME_ADAPTER_FAILURE,
                str(exc),
                raw_response,
                retry_count=retry_outcome.retry_count,
            ) from exc
        provider_output_texts.append(provider_output_text)
        return ModelTurnResult(
            text=provider_output_text,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            cost_usd_estimate=estimate_fireworks_cost(usage)[
                "estimated_total_cost_usd"
            ],
            wall_time_ms=retry_outcome.wall_time_ms,
            retry_count=retry_outcome.retry_count,
        )

    def after_turn(
        record: TurnRecord,
        _trajectory_so_far: dict[str, Any],
    ) -> Literal["continue"]:
        completed_turn_records.append(record)
        return "continue"

    try:
        loop_result = run_agent_loop(
            task,
            config,
            model_turn,
            after_turn=after_turn,
            write_trajectory=write_trajectory,
        )
    except _FireworksTurnFailure as exc:
        usage = _aggregate_token_usage(token_usage_by_turn)
        turn_records = [
            *completed_turn_records,
            TurnRecord(
                turn_index=len(completed_turn_records),
                provider_outcome=exc.outcome,
                raw_output=None,
                parsed_action=None,
                invalid_output=None,
                executed_step_ids=[],
                stop_reason=exc.outcome,
                retry_count=exc.retry_count,
            ),
        ]
        return _record_adapter_result(
            outcome=exc.outcome,
            call_id=call_id,
            wire_model=request["model"],
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=turn_records,
            token_usage=usage,
            cost_estimate=estimate_fireworks_cost(usage),
            trajectory=None,
            error=exc.error,
        )
    except Exception as exc:
        usage = _aggregate_token_usage(token_usage_by_turn)
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            wire_model=request["model"],
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=[],
            token_usage=usage,
            cost_estimate=estimate_fireworks_cost(usage),
            trajectory=None,
            error=str(exc),
        )

    usage = _aggregate_token_usage(token_usage_by_turn)
    return _record_adapter_result(
        outcome=OUTCOME_EXECUTED,
        call_id=call_id,
        wire_model=request["model"],
        config=config,
        condition=condition,
        task=task,
        prompt_metadata=prompt_metadata,
        raw_responses=raw_responses,
        provider_output_texts=provider_output_texts,
        turn_records=loop_result.turn_records,
        token_usage=usage,
        cost_estimate=estimate_fireworks_cost(usage),
        trajectory=loop_result.trajectory,
        error=None,
    )


def token_usage_from_fireworks_response(
    raw_response: Mapping[str, Any],
) -> dict[str, int | None]:
    """Extract token usage from a Fireworks chat-completion response.

    Fireworks is OpenAI-compatible, so the usage shape matches Together's.
    """

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


def estimate_fireworks_cost(
    token_usage: Mapping[str, int | None],
) -> dict[str, Any]:
    """Report Fireworks cost semantics for the on-demand fallback.

    On-demand serving is GPU-second billed, not per-token, and the GPU class
    is recorded at run time. So no per-token USD total is derivable here:
    the cost fields are ``None``. ``per_step_usd_available=False`` and
    ``cost_basis="condition_level"`` are machine-readable signals so a
    downstream rollup (B2) branches instead of summing ``None`` as zero, and
    A2 enforces the §3 cap by deployment time rather than per-step cost. The
    run-time actuals (accelerator class, GPU count, active replica-seconds,
    rate snapshot) are A2's to record, not this adapter's. ``token_usage`` is
    accepted for signature parity with the per-token adapters but is not
    multiplied into USD.
    """

    return {
        "billing_model": FIREWORKS_BILLING_MODEL,
        "billing_granularity": FIREWORKS_BILLING_GRANULARITY,
        "per_step_usd_available": False,
        "cost_basis": "condition_level",
        "on_demand_gpu_hour_reference": dict(FIREWORKS_ON_DEMAND_GPU_HOUR_REFERENCE),
        "estimated_total_cost_usd": None,
        "input_cost_usd": None,
        "output_cost_usd": None,
    }


def _aggregate_token_usage(
    token_usage_by_turn: list[dict[str, int | None]],
) -> dict[str, int | None]:
    if not token_usage_by_turn:
        return _empty_usage()
    aggregate: dict[str, int | None] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        values = [usage.get(key) for usage in token_usage_by_turn]
        aggregate[key] = (
            sum(value for value in values if value is not None)
            if all(value is not None for value in values)
            else None
        )
    return aggregate


def _record_adapter_result(
    *,
    outcome: str,
    call_id: str,
    wire_model: str,
    config: HarnessConfig,
    condition: dict[str, Any],
    task: dict[str, Any],
    prompt_metadata: dict[str, str],
    raw_responses: list[dict[str, Any]],
    provider_output_texts: list[str],
    turn_records: list[TurnRecord],
    token_usage: dict[str, int | None],
    cost_estimate: dict[str, Any],
    trajectory: dict[str, Any] | None,
    error: str | None,
) -> FireworksAdapterResult:
    raw_refs = [
        _write_json_artifact(
            config.output_dir,
            "provider_responses",
            f"{call_id}_turn{index}_raw",
            raw_response,
        )
        for index, raw_response in enumerate(raw_responses)
    ]
    raw_ref = raw_refs[0] if raw_refs else None
    report = {
        "schema_version": "governed_agent_bench.model_adapter_call.v1",
        "adapter": "fireworks_ai_chat_completions",
        "outcome": outcome,
        "reportable": outcome in REPORTABLE_OUTCOMES,
        "task_id": task["task_id"],
        "condition_id": condition["condition_id"],
        "system_id": config.system_id,
        "runtime_mode": config.runtime_mode,
        "model_id": condition["model_id"],
        "provider": condition["provider"],
        **_wire_model_provenance(wire_model, str(condition["model_id"])),
        "prompt_metadata": prompt_metadata,
        "raw_provider_response_ref": raw_ref,
        "raw_provider_response_refs": raw_refs,
        "turn_records": [asdict(record) for record in turn_records],
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
    return FireworksAdapterResult(
        outcome=outcome,
        reportable=outcome in REPORTABLE_OUTCOMES,
        raw_provider_response_ref=raw_ref,
        raw_provider_response_refs=raw_refs,
        provider_report_ref=report_ref,
        provider_output_text=(
            provider_output_texts[-1] if provider_output_texts else None
        ),
        provider_output_texts=provider_output_texts,
        turn_records=turn_records,
        token_usage=token_usage,
        cost_estimate=cost_estimate,
        trajectory=trajectory,
        error=error,
    )


def _api_key_from_env(env: Mapping[str, str]) -> str:
    api_key = env.get(FIREWORKS_API_KEY_ENV, "").strip()
    if not api_key:
        raise HarnessError(f"{FIREWORKS_API_KEY_ENV} is required")
    return api_key


def _ensure_fireworks_condition(condition: dict[str, Any]) -> None:
    if condition.get("provider") != "Fireworks AI":
        raise HarnessError("Fireworks adapter requires provider='Fireworks AI'")
    if condition.get("model_id") != FIREWORKS_DEFAULT_MODEL_ID:
        raise HarnessError(
            f"Fireworks adapter is scoped to {FIREWORKS_DEFAULT_MODEL_ID!r}"
        )
    if condition.get("data_boundary") != SYNTHETIC_DATA_BOUNDARY:
        raise HarnessError("Fireworks adapter requires synthetic benchmark data only")
    if condition.get("prompt_id") != "deployment_full_v1":
        raise HarnessError("Fireworks adapter requires deployment_full_v1")


def _ensure_fireworks_config(
    condition: dict[str, Any],
    config: HarnessConfig,
) -> None:
    _ensure_fireworks_condition(condition)
    if config.model_class != "cloud":
        raise HarnessError("Fireworks adapter requires model_class='cloud'")
    if config.invocation_context != "agent":
        raise HarnessError("Fireworks adapter requires invocation_context='agent'")
    if config.system_id != condition["system_id"]:
        raise HarnessError("HarnessConfig.system_id must match roster condition")
    if config.prompt_template_id != condition["prompt_id"]:
        raise HarnessError("HarnessConfig.prompt_template_id must match condition")


def _ensure_request_model(
    condition: dict[str, Any],
    request_model: str | None,
) -> None:
    """Fail fast (locally, pre-network) on an unusable on-demand model value.

    Qwen2.5-32B is served on-demand only, so a real call must address a
    deployment/router model string, never the non-serverless roster base id.
    The two statically-known-bad cases are rejected on EVERY execution path,
    independent of transport type: ``None`` (no deployment supplied) and the
    base id itself. An arbitrary non-base string cannot be proven a valid live
    deployment without a network call, so authoritative deployment-vs-roster
    verification stays with C1/A2; this guard only stops the silent
    base-id-to-provider failure. ``build_fireworks_chat_request`` keeps the
    base-id default for its own build-only test, which never executes a call.
    """

    # Reject None AND falsy/whitespace strings: `request_model or model_id` in
    # build_fireworks_chat_request would otherwise let "" fall back to the base
    # id silently. Compare on the stripped value so a whitespace-padded base id
    # is rejected too.
    stripped = "" if request_model is None else request_model.strip()
    if not stripped or stripped == condition["model_id"]:
        raise HarnessError(
            "Fireworks on-demand requires a deployment/router-qualified "
            "request_model, not the base model id"
        )


def _wire_model_provenance(wire_model: str, base_model_id: str) -> dict[str, Any]:
    """Sanitized provenance for the actual wire model used.

    A deployment string can embed an account id (maintainer data barred from
    artifacts), so the raw value never enters the report: only a SHA-256 hash,
    a best-effort structural ``ref_type`` hint, and a boolean that the value is
    not the bare base id. ``ref_type`` is a hint, not authoritative; C1/A2 hold
    the real deployment-vs-roster check via the expected hash.
    """

    if wire_model == base_model_id:
        ref_type = "base"
    elif "#" in wire_model or "/deployments/" in wire_model:
        ref_type = "deployment"
    elif "/routers/" in wire_model:
        ref_type = "router"
    else:
        ref_type = "other"
    return {
        "wire_model_sha256": hashlib.sha256(wire_model.encode("utf-8")).hexdigest(),
        "wire_model_ref_type": ref_type,
        "wire_model_is_deployment_qualified": wire_model != base_model_id,
    }


def _manifest_id(task: dict[str, Any]) -> str:
    try:
        return str(task["allowed_context"]["manifest_ref"])
    except KeyError as exc:
        raise HarnessError("task missing allowed_context.manifest_ref") from exc


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
        raise HarnessError("Fireworks response has no choices")
    first = choices[0]
    if not isinstance(first, Mapping):
        raise HarnessError("Fireworks response choice is not an object")
    message = first.get("message")
    if not isinstance(message, Mapping):
        raise HarnessError("Fireworks response choice has no message object")
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    raise HarnessError("Fireworks response message has no text content")


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
