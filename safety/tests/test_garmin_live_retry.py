"""M6 — Garmin live adapter retry + partial-day telemetry.

Contracts pinned:

  1. ``_safe_call_with_retry`` retries transient/rate-limit errors up
     to ``max_attempts``, returns None + error context on exhaustion.
  2. A 4xx-non-429 status code short-circuits to None after one try.
  3. A 429 response is retried when ``retry_on_rate_limit`` is on;
     skipped when it's off.
  4. ``Retry-After`` header surfaces as ``context.retry_after`` and
     the retry wait honours it (capped at ``max_delay_seconds``).
  5. ``GarminLiveAdapter.load()`` sets ``last_pull_partial`` +
     ``last_pull_failed_days`` when any per-day fetch exhausts retries.
  6. ``retry_config_from_thresholds`` reads from the ``[pull.garmin_live]``
     block; missing keys fall back to defaults.
  7. Happy-path: a client that succeeds on its first call returns
     cleanly with ``last_pull_partial == False``.
"""

from __future__ import annotations

from datetime import date
from typing import Any

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.core.pull.garmin_live import (
    GarminLiveAdapter,
    RetryConfig,
    _classify_http_error,
    _safe_call_with_retry,
    retry_config_from_thresholds,
)


class _NoSleep:
    """Replacement for the retry helper's sleep_fn — never actually waits.

    Records each call so tests can assert retry count without spending
    real wall time.
    """

    def __init__(self):
        self.calls: list[tuple[int, dict]] = []

    def __call__(self, attempt, config, context):
        self.calls.append((attempt, dict(context)))


# ---------------------------------------------------------------------------
# HTTP classifier
# ---------------------------------------------------------------------------


def test_classifier_recognises_429_as_rate_limit():
    class RateLimited(Exception):
        status_code = 429

    cat, code, _ctx = _classify_http_error(RateLimited("slow down"))
    assert cat == "rate_limit"
    assert code == 429


def test_classifier_recognises_500_range_as_transient():
    class ServerError(Exception):
        status_code = 503

    cat, code, _ = _classify_http_error(ServerError("bad gateway"))
    assert cat == "transient"
    assert code == 503


def test_classifier_recognises_400_non_429_as_permanent():
    class NotFound(Exception):
        status_code = 404

    cat, code, _ = _classify_http_error(NotFound("nope"))
    assert cat == "permanent"
    assert code == 404


def test_classifier_defaults_unknown_exceptions_to_transient():
    cat, code, _ = _classify_http_error(RuntimeError("network blip"))
    assert cat == "transient"
    assert code is None


def test_classifier_extracts_retry_after_header():
    class _Resp:
        status_code = 429
        headers = {"Retry-After": "7"}

    class RateLimited(Exception):
        response = _Resp()

    cat, _, ctx = _classify_http_error(RateLimited("slow"))
    assert cat == "rate_limit"
    assert ctx["retry_after"] == 7.0


# ---------------------------------------------------------------------------
# _safe_call_with_retry
# ---------------------------------------------------------------------------


def test_retry_returns_first_success_without_retrying():
    calls = 0

    def fn():
        nonlocal calls
        calls += 1
        return "ok"

    sleeper = _NoSleep()
    result, err = _safe_call_with_retry(
        fn, config=RetryConfig(max_attempts=3), sleep_fn=sleeper,
    )
    assert result == "ok"
    assert err is None
    assert calls == 1
    assert sleeper.calls == []


def test_retry_recovers_after_transient_failures():
    calls = 0

    def fn():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise RuntimeError("flake")
        return "ok"

    sleeper = _NoSleep()
    result, err = _safe_call_with_retry(
        fn, config=RetryConfig(max_attempts=3), sleep_fn=sleeper,
    )
    assert result == "ok"
    assert err is None
    assert calls == 3
    # Two sleeps between the three attempts.
    assert len(sleeper.calls) == 2


def test_retry_exhausts_and_returns_none_with_last_context():
    def fn():
        class Err(Exception):
            status_code = 503
        raise Err("server blew up")

    sleeper = _NoSleep()
    result, err = _safe_call_with_retry(
        fn, config=RetryConfig(max_attempts=3), sleep_fn=sleeper,
    )
    assert result is None
    assert err is not None
    assert err["category"] == "transient"
    assert len(sleeper.calls) == 2


def test_retry_short_circuits_on_permanent_4xx():
    calls = 0

    def fn():
        nonlocal calls
        calls += 1

        class Err(Exception):
            status_code = 403
        raise Err("forbidden")

    sleeper = _NoSleep()
    result, err = _safe_call_with_retry(
        fn, config=RetryConfig(max_attempts=5), sleep_fn=sleeper,
    )
    assert result is None
    assert err["category"] == "permanent"
    assert calls == 1
    assert sleeper.calls == []


def test_retry_respects_retry_on_rate_limit_false():
    calls = 0

    def fn():
        nonlocal calls
        calls += 1

        class Err(Exception):
            status_code = 429
        raise Err("rate")

    sleeper = _NoSleep()
    result, err = _safe_call_with_retry(
        fn,
        config=RetryConfig(max_attempts=5, retry_on_rate_limit=False),
        sleep_fn=sleeper,
    )
    assert result is None
    assert err["category"] == "rate_limit"
    assert calls == 1
    assert sleeper.calls == []


def test_retry_surfaces_retry_after_to_sleep_fn():
    calls = 0

    def fn():
        nonlocal calls
        calls += 1
        if calls == 1:
            class _Resp:
                status_code = 429
                headers = {"Retry-After": "2"}

            class Err(Exception):
                response = _Resp()
            raise Err("rate")
        return "ok"

    sleeper = _NoSleep()
    _safe_call_with_retry(
        fn, config=RetryConfig(max_attempts=3), sleep_fn=sleeper,
    )
    assert sleeper.calls[0][1]["retry_after"] == 2.0


# ---------------------------------------------------------------------------
# retry_config_from_thresholds
# ---------------------------------------------------------------------------


def test_retry_config_reads_from_thresholds():
    cfg = retry_config_from_thresholds({
        "pull": {"garmin_live": {
            "max_attempts": 5,
            "base_delay_seconds": 0.5,
            "max_delay_seconds": 8.0,
            "retry_on_rate_limit": False,
        }},
    })
    assert cfg.max_attempts == 5
    assert cfg.base_delay_seconds == 0.5
    assert cfg.max_delay_seconds == 8.0
    assert cfg.retry_on_rate_limit is False


def test_retry_config_falls_back_to_defaults_on_missing_keys():
    cfg = retry_config_from_thresholds(None)
    assert cfg.max_attempts == 3
    assert cfg.base_delay_seconds == 1.0
    assert cfg.max_delay_seconds == 4.0
    assert cfg.retry_on_rate_limit is True


def test_default_thresholds_has_garmin_live_section():
    """Pin the shape the config loader and adapter agree on."""

    garmin = DEFAULT_THRESHOLDS["pull"]["garmin_live"]
    assert set(garmin.keys()) == {
        "max_attempts",
        "base_delay_seconds",
        "max_delay_seconds",
        "retry_on_rate_limit",
    }


# ---------------------------------------------------------------------------
# GarminLiveAdapter partial-pull telemetry
# ---------------------------------------------------------------------------


class _FlakyDaysClient:
    """Fake client that fails specific days and succeeds on others.

    ``fails_until``: per-day attempt count at which success returns.
    Any day not listed is treated as ``1`` (succeeds on first attempt).
    """

    def __init__(self, fails_until: dict[date, int]):
        self._fails_until = fails_until
        self._attempts: dict[date, int] = {}

    def fetch_day(self, day: date) -> dict:
        n = self._attempts.get(day, 0) + 1
        self._attempts[day] = n
        threshold = self._fails_until.get(day, 1)
        if n < threshold:
            raise RuntimeError(f"flake day={day} attempt={n}")
        return {"date": day.isoformat()}


def test_adapter_load_clean_run_sets_last_pull_partial_false():
    as_of = date(2026, 4, 17)
    client = _FlakyDaysClient({})
    adapter = GarminLiveAdapter(
        client=client, history_days=0,
        retry_config=RetryConfig(max_attempts=3, base_delay_seconds=0, max_delay_seconds=0),
    )
    adapter.load(as_of)
    assert adapter.last_pull_partial is False
    assert adapter.last_pull_failed_days == []


def test_adapter_load_marks_partial_when_a_day_exhausts_retries():
    as_of = date(2026, 4, 17)
    # Day fails 10 times → exhausts max_attempts=2.
    client = _FlakyDaysClient({as_of: 10})
    adapter = GarminLiveAdapter(
        client=client, history_days=0,
        retry_config=RetryConfig(max_attempts=2, base_delay_seconds=0, max_delay_seconds=0),
    )
    adapter.load(as_of)
    assert adapter.last_pull_partial is True
    assert adapter.last_pull_failed_days == [as_of.isoformat()]


def test_adapter_load_recovers_after_one_retry():
    as_of = date(2026, 4, 17)
    # Fails once, succeeds on retry.
    client = _FlakyDaysClient({as_of: 2})
    adapter = GarminLiveAdapter(
        client=client, history_days=0,
        retry_config=RetryConfig(max_attempts=3, base_delay_seconds=0, max_delay_seconds=0),
    )
    pull = adapter.load(as_of)
    assert adapter.last_pull_partial is False
    assert pull["raw_daily_row"]["date"] == as_of.isoformat()
