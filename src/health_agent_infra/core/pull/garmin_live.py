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
is the only place the ``garminconnect`` module is imported.

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

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Iterable, Optional, Protocol

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
    """


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
    """

    client: GarminLiveClient
    history_days: int = 14
    source_name: str = "garmin_live"

    def load(self, as_of: date) -> dict:
        days = _window_days(as_of, self.history_days)
        rows = [_normalise_row(day, self.client.fetch_day(day)) for day in days]

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


def build_default_client(credentials: GarminCredentials) -> GarminLiveClient:
    """Construct a live ``garminconnect``-backed client.

    Imports the upstream library lazily so tests (which mock at the
    ``GarminLiveClient`` Protocol) don't pay the import cost and don't
    require ``garminconnect`` to be installed at test time.

    Any import or login failure is wrapped in ``GarminLiveError`` so
    callers can report a bounded blocker without catching a zoo of
    upstream exception types.
    """

    try:
        from garminconnect import Garmin  # type: ignore
    except ImportError as exc:
        raise GarminLiveError(
            "python-garminconnect is not installed. Install it "
            "(`pip install garminconnect`) or fall back to CSV pull."
        ) from exc

    try:
        client = Garmin(credentials.email, credentials.password)
        client.login()
    except Exception as exc:  # upstream exceptions vary by version
        raise GarminLiveError(f"Garmin login failed: {exc}") from exc
    return _GarminConnectClient(client)


class _GarminConnectClient:
    """Shim from ``garminconnect.Garmin`` into ``GarminLiveClient.fetch_day``.

    Each upstream call is wrapped so a single flaky endpoint degrades to
    missing fields rather than failing the whole pull. Field mapping is
    deliberately conservative: only the fields downstream code reads are
    populated; everything else stays None and can be added as needed.
    """

    def __init__(self, client) -> None:  # client: garminconnect.Garmin
        self._client = client

    def fetch_day(self, day: date) -> dict:
        iso = day.isoformat()
        row: dict = {"date": iso}

        stats = _safe_call(self._client.get_stats, iso) or {}
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

        sleep = _safe_call(self._client.get_sleep_data, iso) or {}
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

        hrv = _safe_call(self._client.get_hrv_data, iso) or {}
        hrv_summary = hrv.get("hrvSummary") or {}
        row["health_hrv_value"] = hrv_summary.get("lastNightAvg")
        row["health_hrv_baseline_low"] = (
            (hrv_summary.get("baseline") or {}).get("lowUpper")
        )
        row["health_hrv_baseline_high"] = (
            (hrv_summary.get("baseline") or {}).get("balancedHigh")
        )

        tr = _safe_call(self._client.get_training_readiness, iso)
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

        status = _safe_call(self._client.get_training_status, iso) or {}
        most_recent = (status.get("mostRecentTrainingLoadBalance") or {})
        metrics = (most_recent.get("metricsTrainingLoadBalanceDTOMap") or {})
        # metrics is a dict keyed by device id; pick the first entry
        first_metrics = next(iter(metrics.values()), {}) if metrics else {}
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
            first_ts = next(iter(ts_inner.values()), {})
            if isinstance(first_ts, dict):
                row["training_status"] = first_ts.get("trainingStatus")
            else:
                row["training_status"] = None

        return row


def _safe_call(fn, *args, **kwargs):
    """Call ``fn`` and swallow any exception into ``None``.

    Every upstream field we pull is optional — a single endpoint flaking
    should not fail the whole pull. The adapter's raw_daily_row degrades
    to None for missing fields, which is the same shape the CSV adapter
    emits when the CSV has blank cells.
    """

    try:
        return fn(*args, **kwargs)
    except Exception:
        return None
