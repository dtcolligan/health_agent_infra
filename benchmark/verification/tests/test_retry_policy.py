"""WP-A5 retry / rate-limit / outage middleware checks.

Every retryable case injects a recording sleeper so no test ever waits.
The §5 rows are exercised at the provider-neutral ``retry`` layer; a few
adapter-level cases confirm the seam into ``run_together_model_action``
(retry_count threading, decoding immutability, no double-counting, and
the crash no-retry property).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping

import pytest


BENCHMARK_ROOT = Path(__file__).resolve().parents[2]
if str(BENCHMARK_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_ROOT))

import governed_agent_bench.harness.core as harness_core  # noqa: E402
from governed_agent_bench.harness import (  # noqa: E402
    TOGETHER_API_KEY_ENV,
    harness_config_for_roster_condition,
    load_task,
    run_together_model_action,
)
from governed_agent_bench.harness.retry import (  # noqa: E402
    OutageDetector,
    RetryExhausted,
    TransportFailure,
    classify_retry,
    execute_with_retry,
)
from governed_agent_bench.harness.together import (  # noqa: E402
    OUTCOME_ADAPTER_FAILURE,
    OUTCOME_EXECUTED,
    OUTCOME_TIMEOUT,
)
from governed_agent_bench.model_roster import (  # noqa: E402
    model_roster_hash,
    roster_condition,
)


# --------------------------------------------------------------------------- #
# Provider-neutral helpers
# --------------------------------------------------------------------------- #


class FakeCall:
    """A ``call`` thunk that replays a scripted sequence of outcomes.

    Each item is either an ``Exception`` (raised) or a ``dict`` (returned).
    """

    def __init__(self, outcomes: list[Any]) -> None:
        self._outcomes = list(outcomes)
        self.calls = 0

    def __call__(self) -> dict[str, Any]:
        self.calls += 1
        item = self._outcomes.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item


def _timeout() -> TransportFailure:
    return TransportFailure(kind="timeout", message="timeout")


def _http(status: int, retry_after: str | None = None) -> TransportFailure:
    return TransportFailure(
        kind="http_status", status_code=status, retry_after=retry_after
    )


def _ok() -> dict[str, Any]:
    return {"ok": True}


def _run(outcomes: list[Any], **kwargs: Any) -> tuple[Any, list[float], FakeCall]:
    sleeps: list[float] = []
    call = FakeCall(outcomes)
    try:
        result: Any = execute_with_retry(
            call, sleeper=sleeps.append, **kwargs
        )
    except (RetryExhausted, TransportFailure, Exception) as exc:  # noqa: BLE001
        result = exc
    return result, sleeps, call


# --------------------------------------------------------------------------- #
# §5 row coverage at the retry layer
# --------------------------------------------------------------------------- #


def test_timeout_retried_then_succeeds() -> None:
    result, sleeps, call = _run([_timeout(), _timeout(), _ok()])
    assert result.response == {"ok": True}
    assert result.retry_count == 2
    assert sleeps == [1.0, 2.0]
    assert call.calls == 3


def test_timeout_exhausted_after_four_attempts() -> None:
    result, sleeps, call = _run([_timeout(), _timeout(), _timeout(), _timeout()])
    assert isinstance(result, RetryExhausted)
    assert result.retry_count == 3
    assert result.last_failure.kind == "timeout"
    assert sleeps == [1.0, 2.0, 4.0]
    assert call.calls == 4


def test_http_503_retried_then_succeeds() -> None:
    result, sleeps, _ = _run([_http(503), _http(503), _ok()])
    assert result.retry_count == 2
    assert sleeps == [1.0, 2.0]


def test_http_504_retried_then_succeeds() -> None:
    result, sleeps, _ = _run([_http(504), _ok()])
    assert result.retry_count == 1
    assert sleeps == [1.0]


def test_http_429_honors_retry_after_seconds() -> None:
    result, sleeps, _ = _run([_http(429, retry_after="7"), _ok()])
    assert result.retry_count == 1
    assert sleeps == [7.0]


def test_http_429_without_retry_after_uses_exponential() -> None:
    result, sleeps, call = _run([_http(429), _http(429), _http(429), _http(429)])
    assert isinstance(result, RetryExhausted)
    assert result.retry_count == 3
    assert sleeps == [5.0, 10.0, 20.0]
    assert call.calls == 4


def test_http_429_http_date_retry_after_falls_back_to_exponential() -> None:
    result, sleeps, _ = _run(
        [_http(429, retry_after="Wed, 21 Oct 2026 07:28:00 GMT"), _ok()]
    )
    assert result.retry_count == 1
    assert sleeps == [5.0]


def test_rate_limit_cumulative_cap_clamps_then_exhausts() -> None:
    # Two honored 40s waits exceed the 60s rate-limit cap: second sleep is
    # clamped to the 20s remaining budget, then the next retry is refused.
    result, sleeps, call = _run(
        [_http(429, retry_after="40")] * 4
    )
    assert isinstance(result, RetryExhausted)
    assert sleeps == [40.0, 20.0]
    assert result.retry_count == 2
    assert call.calls == 3


def test_malformed_json_is_not_a_transport_failure_so_never_retried() -> None:
    # The malformed-JSON §5 row lives in the A1 parse path, not the
    # transport. The retry layer only sees transport exceptions; a value
    # error never reaches it, but if one did it is non-retryable.
    result, sleeps, call = _run([ValueError("not json")])
    assert isinstance(result, ValueError)
    assert sleeps == []
    assert call.calls == 1


def test_non_retryable_http_400_propagates_without_retry() -> None:
    result, sleeps, call = _run([_http(400)])
    assert isinstance(result, TransportFailure)
    assert not isinstance(result, RetryExhausted)
    assert result.status_code == 400
    assert result.retry_count == 0
    assert sleeps == []
    assert call.calls == 1


def test_non_retryable_after_retries_carries_retry_count() -> None:
    # Transient timeouts then a non-retryable 400: the propagated failure
    # carries the retries that preceded it (not 0).
    result, sleeps, call = _run([_timeout(), _timeout(), _http(400)])
    assert isinstance(result, TransportFailure)
    assert result.status_code == 400
    assert result.retry_count == 2
    assert sleeps == [1.0, 2.0]
    assert call.calls == 3


def test_runtime_error_is_non_retryable() -> None:
    result, sleeps, call = _run([RuntimeError("boom")])
    assert isinstance(result, RuntimeError)
    assert sleeps == []
    assert call.calls == 1


def test_builtin_timeout_error_is_retryable() -> None:
    result, sleeps, _ = _run([TimeoutError("socket timeout"), _ok()])
    assert result.retry_count == 1
    assert sleeps == [1.0]


# --------------------------------------------------------------------------- #
# classify_retry
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("exc", "expected"),
    [
        (TimeoutError(), "timeout_class"),
        (TransportFailure(kind="timeout"), "timeout_class"),
        (TransportFailure(kind="http_status", status_code=503), "timeout_class"),
        (TransportFailure(kind="http_status", status_code=504), "timeout_class"),
        (TransportFailure(kind="http_status", status_code=429), "rate_limit"),
        (TransportFailure(kind="http_status", status_code=400), "none"),
        (TransportFailure(kind="transport_error"), "none"),
        (RuntimeError(), "none"),
    ],
)
def test_classify_retry(exc: Exception, expected: str) -> None:
    assert classify_retry(exc) == expected


# --------------------------------------------------------------------------- #
# OutageDetector
# --------------------------------------------------------------------------- #


def test_outage_detector_pauses_above_half_on_full_window() -> None:
    detector = OutageDetector()
    for failed in [True] * 6 + [False] * 4:
        detector.record(failed=failed)
    assert detector.should_pause() is True
    signal = detector.pause_signal()
    assert signal is not None
    assert signal.reason == "provider_outage"
    assert signal.window_size == 10
    assert signal.failure_count == 6
    assert signal.failure_rate == 0.6


def test_outage_detector_requires_full_window() -> None:
    detector = OutageDetector()
    for _ in range(3):
        detector.record(failed=True)
    assert detector.should_pause() is False
    assert detector.pause_signal() is None


def test_outage_detector_exactly_half_does_not_pause() -> None:
    detector = OutageDetector()
    for failed in [True] * 5 + [False] * 5:
        detector.record(failed=failed)
    assert detector.should_pause() is False


def test_outage_detector_fed_per_attempt_by_retry_loop() -> None:
    detector = OutageDetector(window=4, threshold=0.5)
    _run([_timeout()] * 4, detector=detector)
    # Four failed attempts fill the window; >50% failed -> pause.
    assert detector.should_pause() is True
    signal = detector.pause_signal()
    assert signal is not None
    assert signal.failure_count == 4


def test_outage_detector_records_success() -> None:
    detector = OutageDetector(window=4, threshold=0.5)
    # Two failures then success: 2/3 of the window so far, window not full.
    _run([_timeout(), _timeout(), _ok()], detector=detector)
    assert detector.should_pause() is False


# --------------------------------------------------------------------------- #
# Adapter-level seam: together.py
# --------------------------------------------------------------------------- #


class SequenceTransport:
    """Transport replaying scripted per-call outcomes, recording requests."""

    def __init__(self, steps: list[Any]) -> None:
        self._steps = list(steps)
        self.calls: list[dict[str, Any]] = []

    def complete(
        self,
        request: Mapping[str, Any],
        *,
        api_key: str,
        timeout_seconds: float,
    ) -> dict[str, Any]:
        self.calls.append(dict(request))
        step = self._steps.pop(0)
        if isinstance(step, BaseException):
            raise step
        return step


def _condition() -> dict[str, Any]:
    return roster_condition("option_b_qwen25_7b_together")


def _config(tmp_path: Path) -> Any:
    return harness_config_for_roster_condition(
        _condition(),
        fixture_root=tmp_path / "fixture",
        output_dir=tmp_path / "out",
        runtime_mode="full_contract",
        claim_tier="T3",
        roster_hash=model_roster_hash(),
    )


def _raw(content: str, prompt: int = 1000, completion: int = 500) -> dict[str, Any]:
    return {
        "id": "mock",
        "choices": [
            {"finish_reason": "stop", "message": {"role": "assistant", "content": content}}
        ],
        "usage": {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
        },
    }


def _command_response(command: str = "hai capabilities") -> dict[str, Any]:
    return _raw(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "command",
            "command": command,
            "args": {},
        })
    )


def _final_response(text: str = "Done.") -> dict[str, Any]:
    return _raw(
        json.dumps({
            "schema_version": "governed_agent_bench.operator_action.v1",
            "action_type": "final",
            "final_text": text,
        })
    )


def test_adapter_retried_turn_threads_retry_count_without_double_counting(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport(
        [_timeout(), _timeout(), _command_response(), _final_response()]
    )

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome == OUTCOME_EXECUTED
    assert sleeps == [1.0, 2.0]  # only the first turn retried
    # The command action step carries retry_count from its turn.
    steps = result.trajectory["steps"]
    command_step = next(s for s in steps if s["step_type"] == "command")
    assert command_step["metadata"]["retry_count"] == 2
    final_step = next(s for s in steps if s["step_type"] == "final")
    assert final_step["metadata"]["retry_count"] == 0
    assert result.turn_records[0].retry_count == 2
    # Failed attempts contribute no raw responses and no token usage.
    assert len(result.raw_provider_response_refs) == 2
    assert result.token_usage == {
        "prompt_tokens": 2000,
        "completion_tokens": 1000,
        "total_tokens": 3000,
    }


def test_adapter_holds_decoding_settings_byte_identical_across_retries(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport(
        [_timeout(), _timeout(), _command_response(), _final_response()]
    )

    run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    retried_turn_calls = transport.calls[:3]
    assert len(retried_turn_calls) == 3
    decoding = [
        (c["temperature"], c["top_p"], c["max_tokens"]) for c in retried_turn_calls
    ]
    assert decoding[0] == decoding[1] == decoding[2]


def test_adapter_timeout_exhausted_surfaces_timeout_outcome(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_timeout()] * 4)

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome == OUTCOME_TIMEOUT
    assert result.trajectory is None
    assert result.raw_provider_response_ref is None
    assert len(transport.calls) == 4
    assert sleeps == [1.0, 2.0, 4.0]
    assert result.turn_records[-1].retry_count == 3


def test_adapter_http_429_exhausted_surfaces_adapter_failure(
    tmp_path: Path,
) -> None:
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_http(429)] * 4)

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    # A retry-exhausted 429 surfaces the same adapter_failure outcome a
    # non-timeout transport error produces today, just after 4 attempts.
    assert result.outcome == OUTCOME_ADAPTER_FAILURE
    assert len(transport.calls) == 4
    assert sleeps == [5.0, 10.0, 20.0]


def _refusal_response() -> dict[str, Any]:
    return {
        "id": "mock",
        "choices": [
            {"finish_reason": "content_filter", "message": {"role": "assistant", "content": ""}}
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 0},
    }


def test_adapter_retried_then_refusal_preserves_retry_count(
    tmp_path: Path,
) -> None:
    # A turn that retried twice then succeeded at the HTTP level but was a
    # provider refusal must still report the retries, not zero.
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_timeout(), _timeout(), _refusal_response()])

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome != OUTCOME_EXECUTED  # provider refusal
    assert len(transport.calls) == 3
    assert sleeps == [1.0, 2.0]
    assert result.turn_records[-1].retry_count == 2


def test_adapter_retried_then_bad_response_preserves_retry_count(
    tmp_path: Path,
) -> None:
    # A retried turn whose successful HTTP response has no text content
    # surfaces adapter_failure but still reports the retries.
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_timeout(), _timeout(), _raw("")])

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome == OUTCOME_ADAPTER_FAILURE
    assert len(transport.calls) == 3
    assert sleeps == [1.0, 2.0]
    assert result.turn_records[-1].retry_count == 2


def test_adapter_retried_then_non_retryable_preserves_retry_count(
    tmp_path: Path,
) -> None:
    # timeout x2 then HTTP 400 (non-retryable): adapter_failure, but the
    # already-failing turn still reports its retries through the seam.
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_timeout(), _timeout(), _http(400)])

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert result.outcome == OUTCOME_ADAPTER_FAILURE
    assert len(transport.calls) == 3
    assert sleeps == [1.0, 2.0]
    assert result.turn_records[-1].retry_count == 2


def test_adapter_subprocess_crash_makes_no_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A crash is an observation step from a non-normalized exit code, not a
    # transport exception, so the retry middleware structurally never sees
    # it. (A1 crash termination is covered by
    # test_model_action_harness.py::test_agent_loop_subprocess_crash_*.)
    def fake_run_hai(
        action: dict[str, Any], config: Any
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=["hai"], returncode=99, stdout="{}", stderr=""
        )

    monkeypatch.setattr(harness_core, "_run_hai", fake_run_hai)
    task = load_task("gab_l1_capabilities_route")
    sleeps: list[float] = []
    transport = SequenceTransport([_command_response()])

    result = run_together_model_action(
        task,
        _condition(),
        _config(tmp_path),
        transport=transport,
        env={TOGETHER_API_KEY_ENV: "mock-api-key"},
        sleeper=sleeps.append,
    )

    assert len(transport.calls) == 1
    assert sleeps == []
    steps = result.trajectory["steps"]
    assert steps[-1]["exit_code"] == "EXIT_99"
    command_step = next(s for s in steps if s["step_type"] == "command")
    assert command_step["metadata"]["retry_count"] == 0


# --------------------------------------------------------------------------- #
# Connection-reset retryability (full-pilot halt regression)
# --------------------------------------------------------------------------- #


def test_connection_reset_is_retryable() -> None:
    """Transient connection drops are retryable, not fatal adapter halts.

    Regression: a full-pilot run halted on turn 2 when a RemoteDisconnected
    fell through to a non-retryable adapter_halt.
    """
    import http.client

    assert classify_retry(ConnectionResetError("reset")) == "timeout_class"
    assert (
        classify_retry(
            http.client.RemoteDisconnected(
                "Remote end closed connection without response"
            )
        )
        == "timeout_class"
    )
    assert classify_retry(http.client.IncompleteRead(b"")) == "timeout_class"
    assert classify_retry(BrokenPipeError("broken pipe")) == "timeout_class"


def test_execute_with_retry_recovers_from_connection_reset() -> None:
    """A transient RemoteDisconnected is retried, then the call succeeds."""
    import http.client

    state = {"n": 0}

    def call() -> dict[str, Any]:
        state["n"] += 1
        if state["n"] < 3:
            raise http.client.RemoteDisconnected(
                "Remote end closed connection without response"
            )
        return {"ok": True}

    sleeps: list[float] = []
    outcome = execute_with_retry(call, sleeper=sleeps.append)
    assert outcome.response == {"ok": True}
    assert outcome.retry_count == 2
    assert state["n"] == 3
