"""Powered-run driver: on-demand deployment lifecycle + per-condition sweep.

Ties the three built pieces together for the confound-break run:
  * ``powered_run_roster`` -- roster_v4 conditions (anchor + breadth) with bands.
  * ``fireworks_deployments`` -- bring a model up, guaranteed teardown.
  * ``pilot_orchestrator.run_pilot`` -- the offline-scored 2x2 sweep per model.

For an on-demand anchor condition the driver wraps the whole sweep in a
``deployment()`` context: create -> run every task/mode/rep against the live
deployment-qualified model -> tear down. Serverless breadth conditions skip the
deployment and use the provider's per-token endpoint directly.

Spend control: on-demand models are run one at a time (never provision two GPUs
at once); each deployment is deleted before the next is created; the run aborts
if the reported cost cap is exceeded.

This is live-run operational tooling; it is NOT on the offline-reproduce path.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable, Mapping

from governed_agent_bench.harness.fireworks import (
    FireworksHTTPTransport,
    FireworksTransport,
    _is_length_truncated,
    _is_provider_refusal,
    _provider_output_text,
    build_fireworks_chat_request,
    token_usage_from_fireworks_response,
)
from governed_agent_bench.harness.model_actions import ModelTurnResult
from governed_agent_bench.harness.retry import (
    OutageDetector,
    RetryExhausted,
    RetryPolicy,
    TransportFailure,
    execute_with_retry,
    is_context_overflow,
)
from governed_agent_bench.harness.core import HarnessError
from governed_agent_bench.pilot_orchestrator import (
    Clock,
    PilotConfig,
    Transport,
    _error_turn_result,
    run_pilot,
)
from governed_agent_bench.scripts.fireworks_deployments import (
    FIREWORKS_API_KEY_ENV,
    deployment,
)
from governed_agent_bench.scripts.powered_run_roster import (
    FIREWORKS_ACCOUNT_ID,
    PoweredCondition,
)


def make_fireworks_model_turn_factory(
    request_model: str,
    *,
    transport: FireworksTransport | None = None,
    env: Mapping[str, str] | None = None,
    timeout_seconds: float = 60.0,
    retry_policy: RetryPolicy | None = None,
    sleeper: Callable[[float], None] = time.sleep,
    clock: Clock = time.monotonic,
) -> Callable[..., Transport]:
    """A model_turn_factory bound to a LIVE deployment-qualified ``request_model``.

    Mirrors ``together_model_turn_factory`` but sends the on-demand wire model.
    On-demand billing is GPU-time, so per-turn ``cost_usd_estimate`` is None; the
    cost cap is enforced by deployment uptime, not per-token accounting.
    """

    provider = transport or FireworksHTTPTransport()
    policy = retry_policy or RetryPolicy()
    env_map = os.environ if env is None else env
    api_key = env_map.get(FIREWORKS_API_KEY_ENV, "").strip()

    def factory(
        task: dict[str, Any],
        system: dict[str, Any],
        _runtime_mode: str,
        _rep_index: int,
        *,
        detector: OutageDetector,
    ) -> Transport:
        request, _prompt_metadata = build_fireworks_chat_request(
            task, system, request_model=request_model
        )

        def model_turn(messages: list[dict[str, str]]) -> ModelTurnResult:
            if not api_key:
                return _error_turn_result(
                    "adapter_error",
                    f"{FIREWORKS_API_KEY_ENV} is required",
                    adapter_error=f"{FIREWORKS_API_KEY_ENV} is required",
                )
            request_for_turn = {**request, "messages": [dict(m) for m in messages]}
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
                    detector=detector,
                )
            except RetryExhausted as exc:
                return _error_turn_result(
                    "retry_exhausted",
                    str(exc.last_failure) or "retry exhausted",
                    retry_count=exc.retry_count,
                    retry_exhausted=True,
                )
            except TransportFailure as exc:
                if is_context_overflow(exc):
                    return _error_turn_result(
                        "context_overflow", str(exc), retry_count=exc.retry_count
                    )
                return _error_turn_result(
                    "adapter_error", str(exc),
                    retry_count=exc.retry_count, adapter_error=str(exc),
                )
            except Exception as exc:  # noqa: BLE001 - adapter boundary
                return _error_turn_result(
                    "adapter_error", str(exc), adapter_error=str(exc)
                )

            raw = retry_outcome.response
            usage = token_usage_from_fireworks_response(raw)
            if _is_provider_refusal(raw):
                return _error_turn_result(
                    "provider_filtered",
                    "provider safety filter (finish_reason/refusal detection)",
                    retry_count=retry_outcome.retry_count,
                )
            if _is_length_truncated(raw):
                return _error_turn_result(
                    "length_truncation",
                    "Fireworks response truncated by max_tokens budget",
                    retry_count=retry_outcome.retry_count,
                )
            try:
                text = _provider_output_text(raw)
            except HarnessError as exc:
                return _error_turn_result(
                    "adapter_error", str(exc),
                    retry_count=retry_outcome.retry_count, adapter_error=str(exc),
                )
            return ModelTurnResult(
                text=text,
                prompt_tokens=usage["prompt_tokens"],
                completion_tokens=usage["completion_tokens"],
                cost_usd_estimate=None,  # on-demand: GPU-time billed, not per-token
                wall_time_ms=retry_outcome.wall_time_ms,
                retry_count=retry_outcome.retry_count,
            )

        return model_turn

    return factory


def run_ondemand_condition(
    pc: PoweredCondition,
    *,
    task_ids: tuple[str, ...],
    runs_root: Path,
    replication_n: int,
    mode_order: tuple[str, ...],
    cost_cap_usd: float,
    api_key: str,
    account_id: str = FIREWORKS_ACCOUNT_ID,
    validate_only: bool = False,
    ready_timeout: float = 900.0,
    deployment_id_suffix: str | None = None,
    on_event: Callable[[str, dict[str, Any]], None] | None = None,
) -> Any:
    """Deploy one on-demand model, sweep it, and GUARANTEE teardown.

    With ``validate_only`` the deployment context does the $0 dry-run and the
    sweep is skipped (used to exercise wiring without GPU spend).

    The deployment id is made UNIQUE per invocation (a time-hex suffix unless
    ``deployment_id_suffix`` is given): Fireworks reserves a deployment name
    through its async cleanup, so re-using a fixed id across runs 409s
    ("already exists"). A fresh id per run sidesteps that; teardown still deletes
    exactly the id it created.
    """

    if pc.serving_mode != "on_demand" or pc.base_model is None:
        raise ValueError(f"{pc.condition['condition_id']} is not an on-demand condition")
    emit = on_event or (lambda _k, _d: None)
    suffix = deployment_id_suffix or format(int(time.time()), "x")[-6:]
    deployment_id = f"{pc.condition['condition_id'].replace('_', '-')}-{suffix}"
    with deployment(
        account_id,
        pc.base_model,
        deployment_id,
        api_key=api_key,
        accelerator_type=pc.accelerator_type,
        validate_only=validate_only,
        ready_timeout=ready_timeout,
        on_event=on_event,
    ) as handle:
        if validate_only:
            emit("sweep_skipped_validate_only", {"condition_id": pc.condition["condition_id"]})
            return None
        factory = make_fireworks_model_turn_factory(handle.invocation_model)
        config = PilotConfig(
            runs_root=runs_root,
            task_ids=task_ids,
            mode_order=mode_order,
            replication_n=replication_n,
            cost_cap_usd=cost_cap_usd,
        )
        emit("sweep_start", {
            "condition_id": pc.condition["condition_id"],
            "invocation_model": handle.invocation_model,
            "task_ids": list(task_ids),
        })
        result = run_pilot(
            systems=[pc.condition],
            model_turn_factory=factory,
            config=config,
        )
        emit("sweep_done", {"condition_id": pc.condition["condition_id"]})
        return result


__all__ = [
    "FIREWORKS_API_KEY_ENV",
    "make_fireworks_model_turn_factory",
    "run_ondemand_condition",
]
