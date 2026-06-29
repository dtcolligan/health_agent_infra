"""Provider-neutral retry / rate-limit middleware and outage detection.

Implements PILOT_PROTOCOL.md §5 as a transport-agnostic layer so each
provider adapter (Together, Fireworks, ...) can reuse the identical
policy, typed transport errors, and outage detector. The module performs
no provider calls of its own: it wraps a caller-supplied ``call`` thunk.

Design contract (WP-A5):
- The retry loop is PER TURN (one model call), never per task.
- Retries do not mutate the request; the caller passes the same thunk.
- Backoff sleeps go through an injected ``sleeper`` so tests never wait,
  and sleep durations never enter trajectory bytes.
- ``RetryOutcome.wall_time_ms`` measures the SUCCESSFUL call only.
- The outage detector is condition-scoped: the caller (A2) owns it and
  injects it; this module only records per-attempt outcomes and exposes
  a typed pause signal.
"""

from __future__ import annotations

import http.client
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Literal


RetryClass = Literal["timeout_class", "rate_limit", "none"]


@dataclass(frozen=True)
class RetryPolicy:
    """§5 retry policy constants. ``max_attempts`` = 1 initial + 3 retries."""

    max_attempts: int = 4
    timeout_backoff_start_s: float = 1.0
    timeout_total_cap_s: float = 30.0
    rate_limit_backoff_start_s: float = 5.0
    rate_limit_total_cap_s: float = 60.0


@dataclass
class TransportFailure(Exception):
    """Typed transport-boundary failure carrying retry-relevant status.

    Provider transports raise this instead of collapsing every network
    error into one opaque type, so the retry layer can branch 429 vs
    503/504 vs other and read ``Retry-After``.
    """

    kind: Literal["timeout", "http_status", "transport_error"]
    status_code: int | None = None
    retry_after: str | None = None
    message: str = ""
    # Retries completed before this failure aborted the turn. Stamped by
    # execute_with_retry when a non-retryable failure propagates after one
    # or more retries, so the adapter can report the true count rather
    # than 0. Providers raising TransportFailure leave this at the default.
    retry_count: int = 0

    def __post_init__(self) -> None:
        super().__init__(self.message or self.kind)


@dataclass
class RetryExhausted(Exception):
    """Raised when a retryable failure exhausts the policy.

    Carries the last failure (for outcome mapping) and the retry count so
    the adapter can record the same failure outcome it produces today,
    just after N attempts.
    """

    last_failure: TransportFailure
    retry_count: int

    def __post_init__(self) -> None:
        super().__init__(
            f"retry exhausted after {self.retry_count} retries: "
            f"{self.last_failure}"
        )


@dataclass(frozen=True)
class RetryOutcome:
    """Successful call plus its retry bookkeeping."""

    response: dict[str, Any]
    retry_count: int
    wall_time_ms: int


@dataclass(frozen=True)
class OutagePauseSignal:
    """Typed signal the A2 disposition tree consumes to pause a condition."""

    reason: str
    window_size: int
    failure_count: int
    failure_rate: float


class OutageDetector:
    """Condition-scoped provider-outage detector over the last N calls.

    ``should_pause`` is true once a FULL window of ``window`` calls has
    accumulated and strictly more than ``threshold`` of them failed, so a
    single bad turn at start cannot trip it. A5 builds and feeds this; A2
    owns the instance and decides what to do with the pause signal.
    """

    def __init__(self, window: int = 10, threshold: float = 0.5) -> None:
        if window < 1:
            raise ValueError("window must be >= 1")
        self._window = window
        self._threshold = threshold
        self._outcomes: deque[bool] = deque(maxlen=window)

    def record(self, *, failed: bool) -> None:
        self._outcomes.append(bool(failed))

    def _failure_count(self) -> int:
        return sum(1 for failed in self._outcomes if failed)

    def should_pause(self) -> bool:
        if len(self._outcomes) < self._window:
            return False
        return self._failure_count() / self._window > self._threshold

    def pause_signal(self) -> OutagePauseSignal | None:
        if not self.should_pause():
            return None
        failures = self._failure_count()
        return OutagePauseSignal(
            reason="provider_outage",
            window_size=self._window,
            failure_count=failures,
            failure_rate=failures / self._window,
        )


def classify_retry(exc: Exception) -> RetryClass:
    """Map a transport exception to its §5 retry class."""

    if isinstance(exc, TimeoutError):
        return "timeout_class"
    if isinstance(exc, (ConnectionError, http.client.IncompleteRead)):
        # Transient connection drops (RemoteDisconnected / reset / broken
        # pipe) are retryable like timeouts, not fatal adapter errors.
        return "timeout_class"
    if isinstance(exc, TransportFailure):
        if exc.kind == "timeout":
            return "timeout_class"
        if exc.kind == "http_status":
            # Transient server/gateway failures (incl. Cloudflare 52x) are
            # retryable; 4xx (e.g. 422 input-too-long) are deterministic and
            # fall through to a per-rep failure.
            if exc.status_code in (500, 502, 503, 504, 520, 521, 522, 523, 524):
                return "timeout_class"
            if exc.status_code == 429:
                return "rate_limit"
        return "none"
    return "none"


def _as_transport_failure(exc: Exception) -> TransportFailure:
    if isinstance(exc, TransportFailure):
        return exc
    if isinstance(exc, TimeoutError):
        return TransportFailure(kind="timeout", message=str(exc))
    if isinstance(exc, (ConnectionError, http.client.IncompleteRead)):
        return TransportFailure(
            kind="timeout", message=str(exc) or exc.__class__.__name__
        )
    return TransportFailure(kind="transport_error", message=str(exc))


def _parse_retry_after_seconds(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header as integer seconds, else ``None``.

    HTTP-date form is intentionally NOT parsed: it would require reading a
    wall-clock "now", reintroducing nondeterminism. Unparseable values
    fall back to the exponential schedule.
    """

    if value is None:
        return None
    text = value.strip()
    if text.isdigit():
        return float(text)
    return None


def _next_backoff(
    retry_class: RetryClass,
    retry_index: int,
    failure: TransportFailure,
    policy: RetryPolicy,
    cumulative: float,
) -> float | None:
    """Backoff for the next retry, clamped to the remaining cumulative cap.

    Returns ``None`` when the cumulative budget is exhausted (stop
    retrying). ``retry_index`` is 0-based for the upcoming retry.
    """

    if retry_class == "rate_limit":
        cap = policy.rate_limit_total_cap_s
        honored = _parse_retry_after_seconds(failure.retry_after)
        scheduled = (
            honored
            if honored is not None
            else policy.rate_limit_backoff_start_s * (2 ** retry_index)
        )
    else:  # timeout_class
        cap = policy.timeout_total_cap_s
        scheduled = policy.timeout_backoff_start_s * (2 ** retry_index)

    remaining = cap - cumulative
    if remaining <= 0:
        return None
    return min(scheduled, remaining)


def execute_with_retry(
    call: Callable[[], dict[str, Any]],
    *,
    policy: RetryPolicy = RetryPolicy(),
    sleeper: Callable[[float], None] = time.sleep,
    clock: Callable[[], float] = time.perf_counter,
    detector: OutageDetector | None = None,
) -> RetryOutcome:
    """Run ``call`` under the §5 retry policy.

    On success returns a ``RetryOutcome``. On a retryable failure that
    exhausts the policy (by attempts or by cumulative backoff budget)
    raises ``RetryExhausted``. A non-retryable failure propagates
    unchanged so the adapter maps it to its existing outcome.
    """

    retry_count = 0
    retry_class: RetryClass | None = None
    cumulative_backoff = 0.0
    last_failure: TransportFailure | None = None

    for attempt in range(policy.max_attempts):
        start = clock()
        try:
            response = call()
        except Exception as exc:  # noqa: BLE001 - re-raised or wrapped below
            if detector is not None:
                detector.record(failed=True)
            failure = _as_transport_failure(exc)
            last_failure = failure
            failure_class = classify_retry(exc)
            if failure_class == "none":
                # Carry the accumulated retry count on the propagated failure
                # when it is our own typed error (``failure is exc`` here), so
                # a non-retryable failure that aborts mid-sequence still
                # reports the retries that preceded it. Foreign exception
                # types (e.g. RuntimeError) propagate unchanged.
                if isinstance(exc, TransportFailure):
                    exc.retry_count = retry_count
                raise
            # Fix the retry class on the first retryable failure of the turn.
            if retry_class is None:
                retry_class = failure_class
            if attempt == policy.max_attempts - 1:
                raise RetryExhausted(
                    last_failure=failure, retry_count=retry_count
                ) from exc
            sleep_s = _next_backoff(
                retry_class, retry_count, failure, policy, cumulative_backoff
            )
            if sleep_s is None:
                raise RetryExhausted(
                    last_failure=failure, retry_count=retry_count
                ) from exc
            cumulative_backoff += sleep_s
            retry_count += 1
            sleeper(sleep_s)
            continue
        else:
            wall_time_ms = int(round((clock() - start) * 1000))
            if detector is not None:
                detector.record(failed=False)
            return RetryOutcome(
                response=response,
                retry_count=retry_count,
                wall_time_ms=wall_time_ms,
            )

    # Unreachable: the loop always returns or raises. Defensive only.
    raise RetryExhausted(
        last_failure=last_failure or TransportFailure(kind="transport_error"),
        retry_count=retry_count,
    )
