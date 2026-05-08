"""Live Garmin pull adapter.

Fetches per-day data from Garmin Connect and normalises into the same
evidence dict the CSV adapter emits, so ``hai pull --live`` is a drop-in
substitute for CSV pull for downstream ``clean`` / projection code.

The evidence-shape contract this adapter conforms to (identical to
``core.pull.garmin.load_recovery_readiness_inputs``):

    {
        "sleep": {record_id, duration_hours} | None,
        "resting_hr":    [{date, bpm,       record_id}, ...],
        "hrv":           [{date, rmssd_ms,  record_id}, ...],
        "training_load": [{date, load,      record_id}, ...],
        "raw_daily_row": {...full CSV-row fields for as_of...} | None,
    }

Upstream client is ``python-garminconnect``. The adapter itself is
library-agnostic: it depends on a ``GarminLiveClient`` Protocol with a
single ``fetch_day(day)`` method. Tests inject a mock client; production
code builds a real client via ``build_default_client(credentials)``, which
is the only place the ``garminconnect`` module is imported. The adapter
conforms to the pull Protocol historically named ``FlagshipPullAdapter``.

Design constraints from the plan:

- No redesign of Phase 2 if Garmin auth changes. Upstream weirdness
  surfaces as ``GarminLiveError``; the CSV adapter is the always-working
  escape hatch.
- Evidence shape must match CSV exactly, so `hai clean` and all
  downstream projectors work unchanged.
- Per-field upstream failures degrade to None rather than failing the
  whole pull; the raw_daily_row simply carries fewer populated keys.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Iterable, Optional, Protocol

from health_agent_infra.core.pull.auth import GarminCredentials


# Canonical raw-daily-row columns (mirror of the CSV export header).
# Live pulls populate what's available and leave the rest None so the
# downstream projector sees the same key set whether the source is CSV or
# the live API.
RAW_DAILY_ROW_COLUMNS: tuple[str, ...] = (
    "date",
    "steps",
    "distance_m",
    "active_kcal",
    "total_kcal",
    "moderate_intensity_min",
    "vigorous_intensity_min",
    "resting_hr",
    "min_hr_day",
    "max_hr_day",
    "floors_ascended_m",
    "all_day_stress",
    "body_battery",
    "avg_environment_altitude_m",
    "sleep_deep_sec",
    "sleep_light_sec",
    "sleep_rem_sec",
    "sleep_awake_sec",
    "sleep_total_sec",
    "avg_sleep_respiration",
    "avg_sleep_stress",
    "awake_count",
    "sleep_score_overall",
    "sleep_score_quality",
    "sleep_score_duration",
    "sleep_score_recovery",
    "training_readiness_level",
    "training_recovery_time_hours",
    "training_readiness_sleep_pct",
    "training_readiness_hrv_pct",
    "training_readiness_stress_pct",
    "training_readiness_sleep_history_pct",
    "training_readiness_load_pct",
    "training_readiness_hrv_weekly_avg",
    "training_readiness_valid_sleep",
    "acute_load",
    "chronic_load",
    "acwr_status",
    "acwr_status_feedback",
    "training_status",
    "training_status_feedback",
    "health_hrv_value",
    "health_hrv_status",
    "health_hrv_baseline_low",
    "health_hrv_baseline_high",
    "health_hr_value",
    "health_hr_status",
    "health_hr_baseline_low",
    "health_hr_baseline_high",
    "health_spo2_value",
    "health_spo2_status",
    "health_spo2_baseline_low",
    "health_spo2_baseline_high",
    "health_skin_temp_c_value",
    "health_skin_temp_c_status",
    "health_skin_temp_c_baseline_low",
    "health_skin_temp_c_baseline_high",
    "health_respiration_value",
    "health_respiration_status",
    "health_respiration_baseline_low",
    "health_respiration_baseline_high",
)


class GarminLiveError(RuntimeError):
    """Raised when live pull cannot proceed.

    Covers the bounded-blocker surface: missing ``garminconnect`` install,
    login failure, or an upstream client that raises on every call.
    CSV pull remains available either way.

    ``context`` carries rate-limit / HTTP headers when the underlying
    error surface exposed them — e.g. ``{"retry_after": 30}`` on a 429.
    Callers that want to report "upstream asked us to wait 30s" can
    read this without parsing the exception message string.
    """

    def __init__(self, message: str, *, context: Optional[dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.context: dict[str, Any] = dict(context) if context else {}


# ---------------------------------------------------------------------------
# Retry + classification helpers (M6)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RetryConfig:
    """Knobs for the per-field retry wrapper.

    Defaults mirror the ``[pull.garmin_live]`` block in
    :data:`core.config.DEFAULT_THRESHOLDS`. The CLI passes a merged
    config through :func:`retry_config_from_thresholds` so a user TOML
    can tune these without code edits.
    """

    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 4.0
    retry_on_rate_limit: bool = True


def retry_config_from_thresholds(thresholds: Optional[dict[str, Any]]) -> RetryConfig:
    """Derive a :class:`RetryConfig` from a merged thresholds dict."""

    from health_agent_infra.core.config import coerce_bool, coerce_float, coerce_int

    cfg = ((thresholds or {}).get("pull") or {}).get("garmin_live") or {}
    return RetryConfig(
        max_attempts=coerce_int(
            cfg.get("max_attempts", 3),
            name="pull.garmin_live.max_attempts",
        ),
        base_delay_seconds=coerce_float(
            cfg.get("base_delay_seconds", 1.0),
            name="pull.garmin_live.base_delay_seconds",
        ),
        max_delay_seconds=coerce_float(
            cfg.get("max_delay_seconds", 4.0),
            name="pull.garmin_live.max_delay_seconds",
        ),
        retry_on_rate_limit=coerce_bool(
            cfg.get("retry_on_rate_limit", True),
            name="pull.garmin_live.retry_on_rate_limit",
        ),
    )


def _classify_http_error(exc: BaseException) -> tuple[str, Optional[int], dict[str, Any]]:
    """Return ``(category, status_code, context)`` for a raised exception.

    Category is one of:
      - ``"rate_limit"``: HTTP 429. Retry respects ``retry_on_rate_limit``.
      - ``"transient"``: HTTP 5xx, network-like failures, or unclassifiable
        exceptions (permissive default — a flake shouldn't fail a pull).
      - ``"permanent"``: HTTP 4xx-non-429. Retrying won't help; stop.

    The classification looks for ``.status_code`` first (common on
    direct HTTP exception types), then ``.response.status_code``
    (wrapper-style). Absent either, the exception is treated as
    transient.

    Context may include a ``retry_after`` key (seconds) when the
    upstream response carried a ``Retry-After`` header — passed
    through verbatim so the caller can surface it in logs /
    ``GarminLiveError.context``.
    """

    status_code = getattr(exc, "status_code", None)
    response = getattr(exc, "response", None)
    if status_code is None and response is not None:
        status_code = getattr(response, "status_code", None)

    context: dict[str, Any] = {}
    headers = None
    if response is not None:
        headers = getattr(response, "headers", None) or {}
    if headers:
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after is not None:
            try:
                context["retry_after"] = float(retry_after)
            except (TypeError, ValueError):
                context["retry_after"] = retry_after

    if status_code is None:
        return "transient", None, context
    try:
        code = int(status_code)
    except (TypeError, ValueError):
        return "transient", None, context

    if code == 429:
        return "rate_limit", code, context
    if 500 <= code < 600:
        return "transient", code, context
    if 400 <= code < 500:
        return "permanent", code, context
    return "transient", code, context


def _retry_sleep(
    attempt: int, config: RetryConfig, context: dict[str, Any],
) -> None:
    """Sleep for the nth retry.

    If ``context`` carries a numeric ``retry_after`` the caller honours
    it (capped at ``max_delay_seconds`` to keep pulls from wedging for
    minutes on a single 429). Otherwise: exponential backoff from
    ``base_delay_seconds``, capped at ``max_delay_seconds``, ±25%
    jitter.
    """

    retry_after = context.get("retry_after")
    if isinstance(retry_after, (int, float)):
        delay = min(float(retry_after), config.max_delay_seconds)
    else:
        delay = min(
            config.base_delay_seconds * (2 ** (attempt - 1)),
            config.max_delay_seconds,
        )
    # ±25% jitter so retries don't synchronise with other clients
    # hitting the same rate-limited endpoint.
    jitter = delay * 0.25 * (random.random() * 2 - 1)
    total = max(0.0, delay + jitter)
    if total > 0:
        time.sleep(total)


def _safe_call_with_retry(
    fn, *args, config: RetryConfig, sleep_fn=_retry_sleep, **kwargs,
) -> tuple[Any, Optional[dict[str, Any]]]:
    """Invoke ``fn``, retry on transient/rate-limit errors per ``config``.

    Returns ``(result, error_context)`` where ``result`` is either the
    successful return value or ``None`` when every attempt failed, and
    ``error_context`` is ``None`` on success or the last exception's
    classified context dict on failure. A field that failed every
    attempt becomes a partial-day signal: the caller propagates it
    upward so the sync row can land ``status='partial'``.
    """

    last_ctx: dict[str, Any] = {}
    last_category = "transient"
    for attempt in range(1, max(1, config.max_attempts) + 1):
        try:
            return fn(*args, **kwargs), None
        except Exception as exc:  # noqa: BLE001 — classifier handles shapes
            category, _code, ctx = _classify_http_error(exc)
            last_ctx = ctx
            last_category = category
            if category == "permanent":
                break
            if category == "rate_limit" and not config.retry_on_rate_limit:
                break
            if attempt < config.max_attempts:
                sleep_fn(attempt, config, ctx)
                continue
    return None, {"category": last_category, **last_ctx}


class GarminLiveClient(Protocol):
    """Per-day fetcher the adapter depends on.

    Implementations MUST return a dict shaped like ``RAW_DAILY_ROW_COLUMNS``
    — missing fields may be None or absent; the adapter fills missing keys
    with None. The returned dict's ``date`` field may be a string or
    absent; the adapter canonicalises to ISO-8601 regardless.
    """

    def fetch_day(self, day: date) -> dict: ...


@dataclass
class GarminLiveAdapter:
    """FlagshipPullAdapter over live Garmin Connect responses.

    Source name is ``garmin_live`` so provenance in emitted payloads
    distinguishes live from CSV, while downstream projectors continue to
    key state rows on ``source='garmin'`` (that's hardcoded in the
    projector and independent of adapter provenance).

    ``retry_config`` (M6) threads through per-field retry behavior —
    the default mirrors :data:`core.config.DEFAULT_THRESHOLDS`'
    ``[pull.garmin_live]``. The CLI passes a merged thresholds dict
    down via :func:`retry_config_from_thresholds`.
    """

    client: GarminLiveClient
    history_days: int = 14
    source_name: str = "garmin_live"
    retry_config: RetryConfig = field(default_factory=RetryConfig)
    # M6 — partial-day telemetry updated each call to :meth:`load`.
    # Kept off the returned pull dict so the CSV-contract key set stays
    # byte-identical to the passive adapter; callers read these
    # directly from the adapter instance when they need the telemetry.
    last_pull_partial: bool = field(default=False, init=False, repr=False)
    last_pull_failed_days: list[str] = field(
        default_factory=list, init=False, repr=False,
    )

    def load(self, as_of: date) -> dict:
        """Return the normalised pull dict for ``as_of``.

        When one or more upstream field-calls exhaust their retry
        budget, the adapter still returns whatever succeeded (same
        partial-field shape as the CSV adapter emits when CSV cells are
        blank). The per-run telemetry (whether any day was partial,
        which days failed) lands on :attr:`last_pull_partial` and
        :attr:`last_pull_failed_days`; the CLI reads these to stamp
        ``sync_run_log.status='partial'``.
        """

        days = _window_days(as_of, self.history_days)
        rows: list[dict] = []
        partial = False
        failed_days: list[str] = []
        for day in days:
            raw, err = _safe_call_with_retry(
                self.client.fetch_day, day, config=self.retry_config,
            )
            if err is not None:
                # A day that exhausted retries drops out of the raw
                # series entirely — whether it's the target day (breaks
                # raw_daily_row) or a historical day (shortens the
                # per-metric series). Either way we mark partial so the
                # operator knows the coverage is incomplete.
                partial = True
                failed_days.append(day.isoformat())
            rows.append(_normalise_row(day, raw))

        self.last_pull_partial = partial
        self.last_pull_failed_days = failed_days

        return {
            "sleep": _extract_sleep(rows, as_of),
            "resting_hr": _series(
                rows, column="resting_hr", out_field="bpm", record_prefix="g_rhr"
            ),
            "hrv": _series(
                rows, column="health_hrv_value", out_field="rmssd_ms", record_prefix="g_hrv"
            ),
            "training_load": _series(
                rows, column="acute_load", out_field="load", record_prefix="g_load"
            ),
            "raw_daily_row": _extract_raw_daily_row(rows, as_of),
        }


def _window_days(as_of: date, history_days: int) -> list[date]:
    start = as_of - timedelta(days=history_days)
    return [start + timedelta(days=i) for i in range((as_of - start).days + 1)]


def _normalise_row(day: date, raw: Optional[dict]) -> dict:
    """Return a dict with every RAW_DAILY_ROW_COLUMNS key and ISO date.

    Missing fields map to None. Extra keys the upstream included are
    preserved but the canonical columns always come first so the row is
    predictable for downstream consumers.
    """

    out: dict = {col: None for col in RAW_DAILY_ROW_COLUMNS}
    if raw:
        for k, v in raw.items():
            out[k] = v
    out["date"] = day.isoformat()
    return out


def _extract_sleep(rows: Iterable[dict], as_of: date) -> Optional[dict]:
    iso = as_of.isoformat()
    row = next((r for r in rows if r.get("date") == iso), None)
    if row is None:
        return None
    total_sec = 0.0
    seen = False
    for col in ("sleep_deep_sec", "sleep_light_sec", "sleep_rem_sec"):
        v = row.get(col)
        if v is None:
            continue
        try:
            total_sec += float(v)
            seen = True
        except (TypeError, ValueError):
            continue
    if not seen or total_sec <= 0:
        return None
    return {
        "record_id": f"g_sleep_{iso}",
        "duration_hours": round(total_sec / 3600.0, 2),
    }


def _series(
    rows: Iterable[dict],
    *,
    column: str,
    out_field: str,
    record_prefix: str,
) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        v = row.get(column)
        if v is None:
            continue
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if f == 0:
            continue
        d = row.get("date")
        if not d:
            continue
        out.append({"date": d, out_field: f, "record_id": f"{record_prefix}_{d}"})
    return out


def _extract_raw_daily_row(rows: Iterable[dict], as_of: date) -> Optional[dict]:
    iso = as_of.isoformat()
    row = next((r for r in rows if r.get("date") == iso), None)
    if row is None:
        return None
    # Return a plain dict (already None-filled) — keep a stable key set even
    # if the client omitted some fields.
    return dict(row)


# ---------------------------------------------------------------------------
# Real client (garminconnect shim)
# ---------------------------------------------------------------------------


def build_default_client(
    credentials: GarminCredentials,
    *,
    retry_config: Optional[RetryConfig] = None,
) -> GarminLiveClient:
    """Construct a live ``garminconnect``-backed client.

    Imports the upstream library lazily so tests (which mock at the
    ``GarminLiveClient`` Protocol) don't pay the import cost and don't
    require ``garminconnect`` to be installed at test time.

    Any import or login failure is wrapped in ``GarminLiveError`` so
    callers can report a bounded blocker without catching a zoo of
    upstream exception types. Login is also retry-guarded per
    ``retry_config`` — rate-limited logins are the most annoying
    failure mode in dev.
    """

    try:
        from garminconnect import Garmin  # type: ignore
    except ImportError as exc:
        raise GarminLiveError(
            "python-garminconnect is not installed. Install it "
            "(`pip install garminconnect`) or fall back to CSV pull."
        ) from exc

    cfg = retry_config if retry_config is not None else RetryConfig()

    last_exc: dict[str, Any] = {"message": None}

    def _do_login():
        client = Garmin(credentials.email, credentials.password)
        try:
            client.login()
        except Exception as exc:
            last_exc["message"] = str(exc)
            raise
        return client

    client, err = _safe_call_with_retry(_do_login, config=cfg)
    if client is None:
        detail = last_exc.get("message")
        suffix = f": {detail}" if detail else ""
        raise GarminLiveError(
            f"Garmin login failed after {cfg.max_attempts} attempt(s){suffix}",
            context=err or {},
        )
    return _GarminConnectClient(client, retry_config=cfg)


class _GarminConnectClient:
    """Shim from ``garminconnect.Garmin`` into ``GarminLiveClient.fetch_day``.

    Each upstream call is wrapped so a single flaky endpoint degrades to
    missing fields rather than failing the whole pull. Field mapping is
    deliberately conservative: only the fields downstream code reads are
    populated; everything else stays None and can be added as needed.

    M6: per-endpoint calls retry on transient / rate-limit errors per
    ``retry_config``. A 4xx-non-429 still short-circuits to None
    (classifier marks it ``permanent``).
    """

    def __init__(
        self,
        client,
        *,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:  # client: garminconnect.Garmin
        self._client = client
        self._retry_config = retry_config if retry_config is not None else RetryConfig()

    def _call(self, fn, *args, **kwargs):
        result, _err = _safe_call_with_retry(
            fn, *args, config=self._retry_config, **kwargs,
        )
        return result

    def fetch_day(self, day: date) -> dict:
        iso = day.isoformat()
        row: dict = {"date": iso}

        stats = self._call(self._client.get_stats, iso) or {}
        row["steps"] = stats.get("totalSteps")
        row["distance_m"] = stats.get("totalDistanceMeters")
        row["active_kcal"] = stats.get("activeKilocalories")
        row["total_kcal"] = stats.get("totalKilocalories")
        row["moderate_intensity_min"] = stats.get("moderateIntensityMinutes")
        row["vigorous_intensity_min"] = stats.get("vigorousIntensityMinutes")
        row["resting_hr"] = stats.get("restingHeartRate")
        row["min_hr_day"] = stats.get("minHeartRate")
        row["max_hr_day"] = stats.get("maxHeartRate")
        row["floors_ascended_m"] = stats.get("floorsAscendedInMeters")
        row["all_day_stress"] = stats.get("averageStressLevel")
        row["body_battery"] = stats.get("bodyBatteryMostRecentValue")

        sleep = self._call(self._client.get_sleep_data, iso) or {}
        dto = sleep.get("dailySleepDTO") or {}
        row["sleep_deep_sec"] = dto.get("deepSleepSeconds")
        row["sleep_light_sec"] = dto.get("lightSleepSeconds")
        row["sleep_rem_sec"] = dto.get("remSleepSeconds")
        row["sleep_awake_sec"] = dto.get("awakeSleepSeconds")
        row["awake_count"] = dto.get("awakeCount")
        scores = dto.get("sleepScores") or {}
        row["sleep_score_overall"] = (scores.get("overall") or {}).get("value")
        row["sleep_score_quality"] = (scores.get("qualityScore") or {}).get("value")
        row["sleep_score_duration"] = (scores.get("durationScore") or {}).get("value")
        row["sleep_score_recovery"] = (scores.get("recoveryScore") or {}).get("value")
        row["avg_sleep_respiration"] = dto.get("averageRespirationValue")
        row["avg_sleep_stress"] = dto.get("avgSleepStress")

        hrv = self._call(self._client.get_hrv_data, iso) or {}
        hrv_summary = hrv.get("hrvSummary") or {}
        row["health_hrv_value"] = hrv_summary.get("lastNightAvg")
        row["health_hrv_baseline_low"] = (
            (hrv_summary.get("baseline") or {}).get("lowUpper")
        )
        row["health_hrv_baseline_high"] = (
            (hrv_summary.get("baseline") or {}).get("balancedHigh")
        )

        tr = self._call(self._client.get_training_readiness, iso)
        if isinstance(tr, list):
            tr = tr[0] if tr else {}
        tr = tr or {}
        row["training_readiness_level"] = tr.get("level")
        row["training_readiness_sleep_pct"] = tr.get("sleepScore")
        row["training_readiness_hrv_pct"] = tr.get("hrvScore")
        row["training_readiness_stress_pct"] = tr.get("recoveryScore")
        row["training_readiness_sleep_history_pct"] = tr.get("sleepHistoryScore")
        row["training_readiness_load_pct"] = tr.get("acuteLoadScore")
        row["training_readiness_hrv_weekly_avg"] = tr.get("hrvScore")
        row["training_readiness_valid_sleep"] = tr.get("validSleep")

        status = self._call(self._client.get_training_status, iso) or {}
        most_recent = (status.get("mostRecentTrainingLoadBalance") or {})
        metrics = (most_recent.get("metricsTrainingLoadBalanceDTOMap") or {})
        # metrics is a dict keyed by device id; pick the first entry
        first_metrics: dict[str, Any] = (
            next(iter(metrics.values()), {}) if metrics else {}
        )
        row["acute_load"] = first_metrics.get("monthlyLoadAerobicLow") or first_metrics.get("acuteLoad")
        row["chronic_load"] = first_metrics.get("chronicLoad")
        row["acwr_status"] = first_metrics.get("trainingBalanceFeedbackPhrase")
        row["training_status"] = (
            (status.get("mostRecentTrainingStatus") or {})
            .get("latestTrainingStatusData", {})
        )
        # training_status gets nested; flatten to a string when possible.
        ts_inner = row["training_status"]
        if isinstance(ts_inner, dict):
            # device-id-keyed map again
            first_ts: dict[str, Any] = next(iter(ts_inner.values()), {})
            if isinstance(first_ts, dict):
                row["training_status"] = first_ts.get("trainingStatus")
            else:
                row["training_status"] = None

        return row
