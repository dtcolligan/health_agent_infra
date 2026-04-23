"""Live Intervals.icu pull adapter.

Fetches per-day wellness data from the Intervals.icu REST API and normalises
it into the same evidence dict shape the CSV and Garmin-live adapters emit,
so ``hai pull --source intervals-icu`` is a drop-in substitute for
downstream ``clean`` / projection code.

Intervals.icu is the recommended primary source: it holds a real OAuth
authorisation from the user to Garmin, so we never touch Garmin's hostile
login endpoints ourselves. Auth is HTTP Basic with a fixed username
``"API_KEY"`` and the user's personal API key as the password (see
https://forum.intervals.icu/t/api-access-to-intervals-icu/609).

Evidence-shape contract (identical to the Garmin adapters):

    {
        "sleep": {record_id, duration_hours} | None,
        "resting_hr":    [{date, bpm,       record_id}, ...],
        "hrv":           [{date, rmssd_ms,  record_id}, ...],
        "training_load": [{date, load,      record_id}, ...],
        "raw_daily_row": {...Garmin-shaped columns for as_of, None where
                          Intervals.icu does not provide the metric...}
                         | None,
    }

The upstream client is library-agnostic: the adapter depends on an
``IntervalsIcuClient`` Protocol with a single ``fetch_wellness_range``
method. Tests inject a replay client; production code builds a real
client via ``build_default_client(credentials)``.
"""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Iterable, Optional, Protocol

from health_agent_infra.core.pull.auth import IntervalsIcuCredentials


DEFAULT_BASE_URL = "https://intervals.icu"


# Canonical raw-daily-row columns mirroring the Garmin CSV export header.
# Kept identical to ``garmin_live.RAW_DAILY_ROW_COLUMNS`` so the downstream
# projector sees the same key set regardless of source. Columns Intervals.icu
# does not provide (Body Battery, training readiness breakdown, stress
# minutes, etc.) are populated with None and degrade gracefully at the
# classifier layer.
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


class IntervalsIcuError(RuntimeError):
    """Raised when an Intervals.icu pull cannot proceed.

    Covers auth failure, network error, malformed response, and HTTP
    non-2xx returns. The error message is operator-facing; no secret
    material ever appears in it.
    """


class IntervalsIcuClient(Protocol):
    """Minimal upstream client contract the adapter consumes.

    Implementations return a list of wellness records (dicts) for the
    given inclusive date range. The adapter does not care about the
    underlying HTTP library — tests inject a replay client.
    """

    def fetch_wellness_range(self, oldest: date, newest: date) -> list[dict]: ...


@dataclass
class HttpIntervalsIcuClient:
    """HTTP client hitting Intervals.icu's wellness range endpoint.

    Uses stdlib ``urllib.request`` to avoid adding ``requests`` as a
    dependency. Intervals.icu accepts HTTP Basic with username
    literally ``"API_KEY"`` and the user's personal API key as
    password; the client encodes that once at construction.
    """

    credentials: IntervalsIcuCredentials
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        token = f"API_KEY:{self.credentials.api_key}".encode("utf-8")
        self._auth_header = "Basic " + base64.b64encode(token).decode("ascii")

    def fetch_wellness_range(self, oldest: date, newest: date) -> list[dict]:
        qs = urllib.parse.urlencode(
            {"oldest": oldest.isoformat(), "newest": newest.isoformat()}
        )
        url = (
            f"{self.base_url}/api/v1/athlete/"
            f"{urllib.parse.quote(self.credentials.athlete_id, safe='')}"
            f"/wellness.json?{qs}"
        )
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": self._auth_header,
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            raise IntervalsIcuError(
                f"Intervals.icu wellness fetch failed: HTTP {exc.code} {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise IntervalsIcuError(
                f"Intervals.icu wellness fetch failed: {exc.reason}"
            ) from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise IntervalsIcuError(
                "Intervals.icu wellness response was not valid JSON"
            ) from exc
        if not isinstance(data, list):
            raise IntervalsIcuError(
                "Intervals.icu wellness response was not a JSON array"
            )
        return data


def build_default_client(credentials: IntervalsIcuCredentials) -> IntervalsIcuClient:
    """Construct the production HTTP client. Single import site."""

    return HttpIntervalsIcuClient(credentials=credentials)


@dataclass
class IntervalsIcuAdapter:
    """Pull adapter over the Intervals.icu wellness API.

    Conforms structurally to ``FlagshipPullAdapter``. Injects an upstream
    client (tests pass a replay client; production passes
    ``HttpIntervalsIcuClient``).
    """

    client: IntervalsIcuClient
    history_days: int = 14
    last_pull_partial: bool = field(default=False, init=False)
    last_pull_failed_days: list[str] = field(default_factory=list, init=False)

    source_name: str = "intervals_icu"

    def load(self, as_of: date) -> dict:
        self.last_pull_partial = False
        self.last_pull_failed_days = []

        oldest = as_of - timedelta(days=self.history_days)
        records = self.client.fetch_wellness_range(oldest=oldest, newest=as_of)
        records_by_date = _index_records_by_date(records)

        sleep = _extract_sleep(records_by_date.get(as_of), as_of)
        resting_hr = _series_from_records(
            records,
            field_name="restingHR",
            out_field="bpm",
            record_prefix="i_rhr",
        )
        hrv = _series_from_records(
            records,
            field_name="hrv",
            out_field="rmssd_ms",
            record_prefix="i_hrv",
        )
        training_load = _series_from_records(
            records,
            field_name="atl",
            out_field="load",
            record_prefix="i_load",
        )
        raw_daily_row = _extract_raw_daily_row(records_by_date.get(as_of), as_of)

        if records_by_date.get(as_of) is None:
            self.last_pull_partial = True
            self.last_pull_failed_days.append(as_of.isoformat())

        return {
            "sleep": sleep,
            "resting_hr": resting_hr,
            "hrv": hrv,
            "training_load": training_load,
            "raw_daily_row": raw_daily_row,
        }


def _index_records_by_date(records: Iterable[dict]) -> dict[date, dict]:
    """Group wellness records by their ``id`` date (ISO-8601 string)."""

    out: dict[date, dict] = {}
    for rec in records:
        iso = rec.get("id") or rec.get("date")
        if not iso:
            continue
        try:
            d = date.fromisoformat(str(iso))
        except ValueError:
            continue
        out[d] = rec
    return out


def _extract_sleep(rec: Optional[dict], as_of: date) -> Optional[dict]:
    if not rec:
        return None
    secs = rec.get("sleepSecs")
    if isinstance(secs, (int, float)) and secs > 0:
        return {
            "record_id": f"i_sleep_{as_of.isoformat()}",
            "duration_hours": round(float(secs) / 3600.0, 2),
        }
    hours = rec.get("sleepHours")
    if isinstance(hours, (int, float)) and hours > 0:
        return {
            "record_id": f"i_sleep_{as_of.isoformat()}",
            "duration_hours": round(float(hours), 2),
        }
    return None


def _series_from_records(
    records: Iterable[dict],
    *,
    field_name: str,
    out_field: str,
    record_prefix: str,
) -> list[dict]:
    out: list[dict] = []
    for rec in records:
        iso = rec.get("id") or rec.get("date")
        if not iso:
            continue
        v = rec.get(field_name)
        if not isinstance(v, (int, float)) or v == 0:
            continue
        out.append(
            {
                "date": str(iso),
                out_field: float(v),
                "record_id": f"{record_prefix}_{iso}",
            }
        )
    out.sort(key=lambda r: r["date"])
    return out


def _extract_raw_daily_row(rec: Optional[dict], as_of: date) -> Optional[dict]:
    """Map Intervals.icu wellness record into the Garmin-shaped raw row.

    Keys unavailable from Intervals.icu stay None so the downstream
    projector sees a consistent column set across sources.
    """

    if not rec:
        return None
    out: dict[str, Any] = {col: None for col in RAW_DAILY_ROW_COLUMNS}
    out["date"] = as_of.isoformat()
    out["steps"] = _as_number(rec.get("steps"))
    out["resting_hr"] = _as_number(rec.get("restingHR"))
    sleep_secs = _as_number(rec.get("sleepSecs"))
    if sleep_secs is None:
        hours = _as_number(rec.get("sleepHours"))
        if hours is not None:
            sleep_secs = hours * 3600.0
    # Intervals.icu provides total sleep duration but no stage breakdown.
    # The sleep projector sums deep+light+rem when present; sleep_total_sec
    # is the fallback when only the aggregate is available.
    out["sleep_total_sec"] = sleep_secs
    out["sleep_score_overall"] = _as_number(rec.get("sleepScore"))
    out["acute_load"] = _as_number(rec.get("atl"))
    out["chronic_load"] = _as_number(rec.get("ctl"))
    out["health_hrv_value"] = _as_number(rec.get("hrv"))
    out["health_hr_value"] = _as_number(rec.get("restingHR"))
    out["health_respiration_value"] = _as_number(rec.get("respiration"))
    out["health_spo2_value"] = _as_number(rec.get("spO2"))
    return out


def _as_number(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    return None
