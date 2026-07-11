"""Together AI adapter for GovernedAgentBench model-action runs.

The adapter is deliberately thin: it renders the existing deployment
prompt, sends accumulated chat messages through an injectable transport,
records provider-call metadata, and delegates loop execution to the
provider-neutral model-action harness.
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
from governed_agent_bench.harness.decoding import decoding_request_fields
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
    _http_error_message,
    execute_with_retry,
    is_context_overflow,
)
from governed_agent_bench.model_roster import load_model_roster, roster_condition


TOGETHER_API_KEY_ENV = "TOGETHER_API_KEY"
TOGETHER_CHAT_COMPLETIONS_URL = "https://api.together.xyz/v1/chat/completions"
TOGETHER_DEFAULT_CONDITION_ID = "option_b_qwen25_7b_together"
TOGETHER_DEFAULT_MODEL_ID = "Qwen/Qwen2.5-7B-Instruct-Turbo"
# roster_v2 primary (D-33): Qwen3 235B-A22B Instruct-2507 is a NON-thinking MoE
# (fast like a small model, capable like a large one, 256k context). The earlier
# Mistral Small 24B / Gemma 4 31B smoke candidates were roster-excluded; see git
# history and PAPER.md D-33 for the selection trail.
TOGETHER_QWEN3_235B_INSTRUCT_MODEL_ID = "Qwen/Qwen3-235B-A22B-Instruct-2507-tput"


def _together_roster_model_ids() -> frozenset[str]:
    """Model ids of every roster condition served by Together AI.

    Audit fix A8: the allowlist is derived from the committed roster instead
    of a hand-accreted literal, so a roster amendment (e.g. the pending
    ladder additions) extends the guard automatically and roster-excluded
    smoke candidates are rejected.
    """

    roster = load_model_roster()
    return frozenset(
        str(condition["model_id"])
        for condition in roster.get("conditions", [])
        if condition.get("provider") == "Together AI"
        # D-55.1 (delta-audit defense-in-depth): only the run_-prefixed ladder
        # conditions may be dispatched, so the allowlist must not certify a
        # non-run condition's model id -- e.g. the deprecated 235B, now removed
        # from serverless, retained only for provenance.
        and str(condition.get("condition_id", "")).startswith("run_")
    )


TOGETHER_ALLOWED_MODEL_IDS = _together_roster_model_ids()
SYNTHETIC_DATA_BOUNDARY = "synthetic_governed_agent_bench_fixtures_only"

OUTCOME_EXECUTED = "executed"
OUTCOME_TIMEOUT = "timeout"
OUTCOME_INVALID_JSON = "invalid_json"
OUTCOME_PROVIDER_REFUSAL = "provider_refusal"
OUTCOME_ADAPTER_FAILURE = "adapter_failure"
# Audit fix A3: finish_reason="length" is a harness budget artifact (the
# max_tokens ceiling truncated the output), reported as its own outcome like
# timeout -- never allowed to fall through to JSON parsing where it would be
# recorded as a model formatting violation.
OUTCOME_LENGTH_TRUNCATION = "length_truncation"
# IB-3 (readiness SF-3): HTTP 422 is the provider's context-overflow
# rejection. It is a REPORTABLE outcome like timeout -- never a generic
# adapter failure, which would inflate small-model failure exactly at the
# operate floor. The raw provider error body travels in the message.
OUTCOME_CONTEXT_OVERFLOW = "context_overflow"
REPORTABLE_OUTCOMES = frozenset({
    OUTCOME_TIMEOUT,
    OUTCOME_INVALID_JSON,
    OUTCOME_PROVIDER_REFUSAL,
    OUTCOME_ADAPTER_FAILURE,
    OUTCOME_LENGTH_TRUNCATION,
    OUTCOME_CONTEXT_OVERFLOW,
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
# roster_v2 primary condition (D-33): vendor-verified live by Dom on the
# Together model page, 2026-07-05.
# D-41 ladder additions, vendor-verified live by Dom on the Together model
# pages, 2026-07-05.
TOGETHER_LLAMA33_70B_PRICING: dict[str, str | float] = {
    "currency": "USD",
    "input_usd_per_1m_tokens": 1.04,
    "output_usd_per_1m_tokens": 1.04,
    "pricing_snapshot_date": "2026-07-05",
    "pricing_source": "Together AI model page (Llama 3.3 70B) as of 2026-07-05",
}
TOGETHER_QWEN35_9B_PRICING: dict[str, str | float] = {
    "currency": "USD",
    "input_usd_per_1m_tokens": 0.17,
    "output_usd_per_1m_tokens": 0.25,
    "pricing_snapshot_date": "2026-07-05",
    "pricing_source": "Together AI model page (Qwen3.5 9B) as of 2026-07-05",
}
TOGETHER_QWEN3_235B_PRICING: dict[str, str | float] = {
    "currency": "USD",
    "input_usd_per_1m_tokens": 0.20,
    "output_usd_per_1m_tokens": 0.60,
    "pricing_snapshot_date": "2026-07-05",
    "pricing_source": (
        "Together AI model page (Qwen3 235B A22B Instruct 2507 FP8 Throughput)"
        " as of 2026-07-05"
    ),
}
# D-56: MiniMax-M3 is the deprecation-forced PRIMARY replacement after Together
# removed Qwen3-235B-...-tput from serverless (2026-07-10).
TOGETHER_MINIMAX_M3_PRICING: dict[str, str | float] = {
    "currency": "USD",
    "input_usd_per_1m_tokens": 0.30,
    "output_usd_per_1m_tokens": 1.20,
    "pricing_snapshot_date": "2026-07-11",
    "pricing_source": "Together AI /v1/models (MiniMaxAI/MiniMax-M3) as of 2026-07-11",
}
# Audit fix A1: cost estimation routes by the condition's model_id. An
# unknown model_id raises -- a metered run must never silently misprice.
TOGETHER_PRICING_BY_MODEL_ID: dict[str, dict[str, str | float]] = {
    TOGETHER_DEFAULT_MODEL_ID: TOGETHER_QWEN25_7B_PRICING,
    TOGETHER_QWEN3_235B_INSTRUCT_MODEL_ID: TOGETHER_QWEN3_235B_PRICING,
    "MiniMaxAI/MiniMax-M3": TOGETHER_MINIMAX_M3_PRICING,
    "meta-llama/Llama-3.3-70B-Instruct-Turbo": TOGETHER_LLAMA33_70B_PRICING,
    "Qwen/Qwen3.5-9B": TOGETHER_QWEN35_9B_PRICING,
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
                # urllib's default UA ("Python-urllib/x.y") is blocked by the
                # provider WAF with HTTP 403; set an explicit UA.
                "User-Agent": "GovernedAgentBench/1.0",
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
                kind="timeout", message="Together request timed out"
            ) from exc
        except urllib.error.HTTPError as exc:
            # HTTPError is a URLError subclass and must be caught first so
            # the status code and Retry-After survive for the retry layer.
            # The error body is captured (bounded) so a 422 context-overflow
            # classification records the provider's raw message (IB-3).
            raise TransportFailure(
                kind="http_status",
                status_code=exc.code,
                retry_after=exc.headers.get("Retry-After") if exc.headers else None,
                message=_http_error_message("Together", exc),
            ) from exc
        except urllib.error.URLError as exc:
            if isinstance(exc.reason, socket.timeout):
                raise TransportFailure(
                    kind="timeout", message="Together request timed out"
                ) from exc
            if isinstance(exc.reason, ConnectionError):
                raise TransportFailure(
                    kind="timeout",
                    message=f"Together connection error: {exc}",
                ) from exc
            raise TransportFailure(
                kind="transport_error",
                message=f"Together request failed: {exc}",
            ) from exc

        raw = json.loads(body)
        if not isinstance(raw, dict):
            raise HarnessError("Together response was not a JSON object")
        return raw


class _TogetherTurnFailure(RuntimeError):
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
class TogetherAdapterResult:
    """Outcome of one Together model-action adapter call."""

    outcome: str
    reportable: bool
    raw_provider_response_ref: str | None
    raw_provider_response_refs: list[str]
    provider_report_ref: str
    provider_output_text: str | None
    provider_output_texts: list[str]
    turn_records: list[TurnRecord]
    token_usage: dict[str, int | bool | None]
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
    # Audit fix A7: the condition's full decoding_settings dict passes
    # through an explicit allowlist (unknown keys raise; non-numeric
    # placeholders like the roster's seed sentinel are skipped, not sent).
    request = {
        "model": condition["model_id"],
        "messages": _messages_from_rendered_prompt(prompt["rendered_prompt"]),
        **decoding_request_fields(condition["decoding_settings"]),
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
    rep: int = 0,
    transport: TogetherTransport | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 60.0,
    write_trajectory: bool = True,
    retry_policy: RetryPolicy | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.perf_counter,
    outage_detector: OutageDetector | None = None,
) -> TogetherAdapterResult:
    """Run a Together-backed bounded model-action loop for one task.

    ``rep`` is the replication index (audit fix A2): it is part of the
    provider call id and trajectory id, so n>1 reps of the same cell write
    distinct raw-response / report / trajectory artifacts instead of
    overwriting each other. ``sleeper`` / ``clock`` are injectable so retry
    backoff is testable without real waits. ``outage_detector`` is
    condition-scoped and owned by the caller (A2); this adapter only feeds
    per-attempt outcomes into it. ``retry_policy`` defaults to the §5
    policy.
    """

    if rep < 0:
        raise HarnessError("rep must be non-negative")
    _ensure_together_config(condition, config)
    request, prompt_metadata = build_together_chat_request(task, condition)
    model_id = str(condition["model_id"])
    call_id = _provider_call_id(task, condition, config, prompt_metadata, rep)
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
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=[],
            token_usage=usage,
            cost_estimate=estimate_together_cost(usage, model_id),
            trajectory=None,
            error=str(exc),
        )

    provider = transport or TogetherHTTPTransport()
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
            raise _TogetherTurnFailure(
                outcome,
                str(exc.last_failure) or "retry exhausted",
                None,
                retry_count=exc.retry_count,
            ) from exc
        except TransportFailure as exc:
            if is_context_overflow(exc):
                # IB-3: 422 context overflow is its own reportable outcome
                # (like timeout); the raw provider body rides in str(exc).
                outcome = OUTCOME_CONTEXT_OVERFLOW
            elif exc.kind == "timeout":
                outcome = OUTCOME_TIMEOUT
            else:
                outcome = OUTCOME_ADAPTER_FAILURE
            raise _TogetherTurnFailure(
                outcome, str(exc), None, retry_count=exc.retry_count
            ) from exc
        except TimeoutError as exc:
            raise _TogetherTurnFailure(OUTCOME_TIMEOUT, str(exc), None) from exc
        except Exception as exc:
            raise _TogetherTurnFailure(
                OUTCOME_ADAPTER_FAILURE,
                str(exc),
                None,
            ) from exc

        raw_response = retry_outcome.response
        raw_responses.append(raw_response)
        usage = token_usage_from_together_response(raw_response)
        token_usage_by_turn.append(usage)
        if _is_provider_refusal(raw_response):
            raise _TogetherTurnFailure(
                OUTCOME_PROVIDER_REFUSAL,
                "Together response indicates provider-level refusal",
                raw_response,
                retry_count=retry_outcome.retry_count,
            )
        if _is_length_truncated(raw_response):
            # A3: budget truncation is a harness artifact, reported as its
            # own outcome; the truncated text must not reach JSON parsing
            # where it would score as a model formatting violation.
            raise _TogetherTurnFailure(
                OUTCOME_LENGTH_TRUNCATION,
                "Together response truncated by max_tokens budget "
                "(finish_reason=length)",
                raw_response,
                retry_count=retry_outcome.retry_count,
            )
        try:
            provider_output_text = _provider_output_text(raw_response)
        except HarnessError as exc:
            raise _TogetherTurnFailure(
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
            cost_usd_estimate=estimate_together_cost(usage, model_id)[
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
            rep=rep,
            after_turn=after_turn,
            write_trajectory=write_trajectory,
        )
    except _TogetherTurnFailure as exc:
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
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=turn_records,
            token_usage=usage,
            cost_estimate=estimate_together_cost(usage, model_id),
            trajectory=None,
            error=exc.error,
        )
    except Exception as exc:
        usage = _aggregate_token_usage(token_usage_by_turn)
        return _record_adapter_result(
            outcome=OUTCOME_ADAPTER_FAILURE,
            call_id=call_id,
            config=config,
            condition=condition,
            task=task,
            prompt_metadata=prompt_metadata,
            raw_responses=raw_responses,
            provider_output_texts=provider_output_texts,
            turn_records=[],
            token_usage=usage,
            cost_estimate=estimate_together_cost(usage, model_id),
            trajectory=None,
            error=str(exc),
        )

    usage = _aggregate_token_usage(token_usage_by_turn)
    return _record_adapter_result(
        outcome=OUTCOME_EXECUTED,
        call_id=call_id,
        config=config,
        condition=condition,
        task=task,
        prompt_metadata=prompt_metadata,
        raw_responses=raw_responses,
        provider_output_texts=provider_output_texts,
        turn_records=loop_result.turn_records,
        token_usage=usage,
        cost_estimate=estimate_together_cost(usage, model_id),
        trajectory=loop_result.trajectory,
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
    token_usage: Mapping[str, int | bool | None],
    model_id: str,
) -> dict[str, Any]:
    """Estimate Together spend from recorded usage and the model's rates.

    Audit fix A1: rates are selected by ``model_id`` from
    ``TOGETHER_PRICING_BY_MODEL_ID``. An unknown model_id raises rather
    than silently applying another model's rates to a metered run.
    """

    pricing = TOGETHER_PRICING_BY_MODEL_ID.get(model_id)
    if pricing is None:
        raise HarnessError(
            f"no Together pricing entry for model_id={model_id!r}; known: "
            f"{sorted(TOGETHER_PRICING_BY_MODEL_ID)}"
        )
    input_rate = float(pricing["input_usd_per_1m_tokens"])
    output_rate = float(pricing["output_usd_per_1m_tokens"])
    prompt_tokens = token_usage.get("prompt_tokens")
    completion_tokens = token_usage.get("completion_tokens")
    if not isinstance(prompt_tokens, int) or isinstance(prompt_tokens, bool):
        prompt_tokens = None
    if not isinstance(completion_tokens, int) or isinstance(completion_tokens, bool):
        completion_tokens = None
    if prompt_tokens is None or completion_tokens is None:
        total_cost = None
        input_cost = None
        output_cost = None
    else:
        input_cost = prompt_tokens * input_rate / 1_000_000
        output_cost = completion_tokens * output_rate / 1_000_000
        total_cost = input_cost + output_cost
    return {
        **pricing,
        "input_cost_usd": _round_cost(input_cost),
        "output_cost_usd": _round_cost(output_cost),
        "estimated_total_cost_usd": _round_cost(total_cost),
    }


def _aggregate_token_usage(
    token_usage_by_turn: list[dict[str, int | None]],
) -> dict[str, int | bool | None]:
    """Sum per-turn usage; flag incompleteness instead of nulling the sum.

    Audit fix A9: a single turn without a usage object must not erase the
    other turns' counts (that silently under-counts the real-time cost
    cap). Available turns are summed and ``usage_complete: false`` marks
    the aggregate as a lower bound.
    """

    aggregate: dict[str, int | bool | None] = {}
    complete = True
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        values = [usage.get(key) for usage in token_usage_by_turn]
        present = [value for value in values if value is not None]
        if len(present) != len(values):
            complete = False
        aggregate[key] = sum(present) if present else None
    aggregate["usage_complete"] = complete
    return aggregate


def _record_adapter_result(
    *,
    outcome: str,
    call_id: str,
    config: HarnessConfig,
    condition: dict[str, Any],
    task: dict[str, Any],
    prompt_metadata: dict[str, str],
    raw_responses: list[dict[str, Any]],
    provider_output_texts: list[str],
    turn_records: list[TurnRecord],
    token_usage: dict[str, int | bool | None],
    cost_estimate: dict[str, Any],
    trajectory: dict[str, Any] | None,
    error: str | None,
) -> TogetherAdapterResult:
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
    return TogetherAdapterResult(
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
    api_key = env.get(TOGETHER_API_KEY_ENV, "").strip()
    if not api_key:
        raise HarnessError(f"{TOGETHER_API_KEY_ENV} is required")
    return api_key


def _ensure_together_condition(condition: dict[str, Any]) -> None:
    if condition.get("provider") != "Together AI":
        raise HarnessError("Together adapter requires provider='Together AI'")
    if condition.get("model_id") not in TOGETHER_ALLOWED_MODEL_IDS:
        raise HarnessError(
            "Together adapter model_id must be one of "
            f"{sorted(TOGETHER_ALLOWED_MODEL_IDS)}"
        )
    if condition.get("data_boundary") != SYNTHETIC_DATA_BOUNDARY:
        raise HarnessError("Together adapter requires synthetic benchmark data only")
    if condition.get("prompt_id") not in (
        "deployment_full_v1", "deployment_full_v2", "deployment_full_v3"
    ):
        raise HarnessError(
            "Together adapter requires deployment_full_v1, v2, or v3"
        )


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


def _provider_call_id(
    task: dict[str, Any],
    condition: dict[str, Any],
    config: HarnessConfig,
    prompt_metadata: Mapping[str, str],
    rep: int,
) -> str:
    # A2: rep is part of the digest AND visible in the id so n=3 reps of the
    # same cell write distinct provider_responses/ and provider_reports/
    # artifacts instead of overwriting each other.
    digest = hashlib.sha256(
        json.dumps(
            {
                "task_id": task["task_id"],
                "condition_id": condition["condition_id"],
                "system_id": config.system_id,
                "runtime_mode": config.runtime_mode,
                "prompt_template_hash": prompt_metadata["prompt_template_hash"],
                "rep": rep,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:12]
    return f"{task['task_id']}_{config.system_id}_rep{rep}_{digest}"


def _finish_reason(raw_response: Mapping[str, Any]) -> str:
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, Mapping):
        return ""
    return str(first.get("finish_reason", "")).lower()


def _is_length_truncated(raw_response: Mapping[str, Any]) -> bool:
    """True when the provider stopped generation at the max_tokens budget."""

    return _finish_reason(raw_response) == "length"


def _is_provider_refusal(raw_response: Mapping[str, Any]) -> bool:
    error = raw_response.get("error")
    if isinstance(error, Mapping):
        error_type = str(error.get("type", "")).lower()
        error_code = str(error.get("code", "")).lower()
        if error_type in _PROVIDER_REFUSAL_FINISH_REASONS:
            return True
        if error_code in _PROVIDER_REFUSAL_FINISH_REASONS:
            return True
    if _finish_reason(raw_response) in _PROVIDER_REFUSAL_FINISH_REASONS:
        return True
    choices = raw_response.get("choices")
    if not isinstance(choices, list) or not choices:
        return False
    first = choices[0]
    if not isinstance(first, Mapping):
        return False
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
