"""Live Intervals.icu pull adapter.

Fetches per-day wellness data + per-session activity data from the
Intervals.icu REST API and normalises both into the evidence dict shape
the CSV and Garmin-live adapters emit, so ``hai pull --source intervals-icu``
is a drop-in substitute for downstream ``clean`` / projection code.

Intervals.icu is the recommended primary source: it holds a real OAuth
authorisation from the user to Garmin, so we never touch Garmin's hostile
login endpoints ourselves. Auth is HTTP Basic with a fixed username
``"API_KEY"`` and the user's personal API key as the password (see
https://forum.intervals.icu/t/api-access-to-intervals-icu/609).

Evidence-shape contract (superset of the Garmin adapters):

    {
        "sleep": {record_id, duration_hours} | None,
        "resting_hr":    [{date, bpm,       record_id}, ...],
        "hrv":           [{date, rmssd_ms,  record_id}, ...],
        "training_load": [{date, load,      record_id}, ...],
        "raw_daily_row": {...Garmin-shaped columns for as_of, None where
                          Intervals.icu does not provide the metric...}
                         | None,
        "activities":   [IntervalsIcuActivity.as_dict(), ...]
                        — per-session structural data (distance, HR zones,
                        interval summaries, TRIMP). Empty list when the
                        /activities endpoint returns nothing for the
                        window.
    }

Wellness is a daily-rollup stream; activities is the per-session stream
that actually carries the session structure (HR zone times, interval
blocks, TRIMP, warmup/cooldown splits). Running and strength domains
consume activities first; wellness is the fallback when activity
granularity is missing.

The upstream client is library-agnostic: the adapter depends on an
``IntervalsIcuClient`` Protocol with two methods — ``fetch_wellness_range``
and ``fetch_activities_range``. Tests inject a replay client; production
code builds a real client via ``build_default_client(credentials)``.
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


@dataclass(frozen=True)
class IntervalsIcuActivity:
    """Structured per-session record from intervals.icu's /activities stream.

    Fields map one-to-one to populated columns observed on a live Garmin
    Connect-sourced run (see docs at the top of this module). Fields the
    upstream record did not populate arrive as None; the full upstream
    payload is preserved in ``raw_json`` as an escape hatch for
    downstream skills that want fields we haven't typed yet.

    ``activity_id`` is the intervals.icu primary key (e.g. ``"i142248964"``).
    ``external_id`` is the upstream-of-intervals-icu id when present (e.g.
    the Garmin Connect activity id). Both are string-typed because
    intervals.icu returns them as strings and we don't want to silently
    coerce 64-bit ids through float.
    """

    activity_id: str
    user_id: str
    as_of_date: str
    start_date_utc: Optional[str]
    start_date_local: Optional[str]
    source: Optional[str]
    external_id: Optional[str]
    activity_type: Optional[str]
    name: Optional[str]
    distance_m: Optional[float]
    moving_time_s: Optional[float]
    elapsed_time_s: Optional[float]
    average_hr: Optional[float]
    max_hr: Optional[float]
    athlete_max_hr: Optional[float]
    hr_zone_times_s: Optional[list[int]]
    hr_zones_bpm: Optional[list[int]]
    interval_summary: Optional[list[str]]
    trimp: Optional[float]
    icu_training_load: Optional[float]
    hr_load: Optional[float]
    hr_load_type: Optional[str]
    warmup_time_s: Optional[float]
    cooldown_time_s: Optional[float]
    lap_count: Optional[int]
    average_speed_mps: Optional[float]
    max_speed_mps: Optional[float]
    pace_s_per_m: Optional[float]
    average_cadence_spm: Optional[float]
    average_stride_m: Optional[float]
    calories: Optional[float]
    total_elevation_gain_m: Optional[float]
    total_elevation_loss_m: Optional[float]
    feel: Optional[int]
    icu_rpe: Optional[int]
    session_rpe: Optional[float]
    device_name: Optional[str]
    raw_json: str

    def as_dict(self) -> dict:
        """Serialise to a JSON-safe dict for pull output + projection."""

        return {
            "activity_id": self.activity_id,
            "user_id": self.user_id,
            "as_of_date": self.as_of_date,
            "start_date_utc": self.start_date_utc,
            "start_date_local": self.start_date_local,
            "source": self.source,
            "external_id": self.external_id,
            "activity_type": self.activity_type,
            "name": self.name,
            "distance_m": self.distance_m,
            "moving_time_s": self.moving_time_s,
            "elapsed_time_s": self.elapsed_time_s,
            "average_hr": self.average_hr,
            "max_hr": self.max_hr,
            "athlete_max_hr": self.athlete_max_hr,
            "hr_zone_times_s": list(self.hr_zone_times_s) if self.hr_zone_times_s is not None else None,
            "hr_zones_bpm": list(self.hr_zones_bpm) if self.hr_zones_bpm is not None else None,
            "interval_summary": list(self.interval_summary) if self.interval_summary is not None else None,
            "trimp": self.trimp,
            "icu_training_load": self.icu_training_load,
            "hr_load": self.hr_load,
            "hr_load_type": self.hr_load_type,
            "warmup_time_s": self.warmup_time_s,
            "cooldown_time_s": self.cooldown_time_s,
            "lap_count": self.lap_count,
            "average_speed_mps": self.average_speed_mps,
            "max_speed_mps": self.max_speed_mps,
            "pace_s_per_m": self.pace_s_per_m,
            "average_cadence_spm": self.average_cadence_spm,
            "average_stride_m": self.average_stride_m,
            "calories": self.calories,
            "total_elevation_gain_m": self.total_elevation_gain_m,
            "total_elevation_loss_m": self.total_elevation_loss_m,
            "feel": self.feel,
            "icu_rpe": self.icu_rpe,
            "session_rpe": self.session_rpe,
            "device_name": self.device_name,
            "raw_json": self.raw_json,
        }


class IntervalsIcuClient(Protocol):
    """Minimal upstream client contract the adapter consumes.

    Implementations return a list of records (dicts) for the given inclusive
    date range. The adapter does not care about the underlying HTTP library —
    tests inject a replay client.
    """

    def fetch_wellness_range(self, oldest: date, newest: date) -> list[dict]: ...
    def fetch_activities_range(self, oldest: date, newest: date) -> list[dict]: ...


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
        return self._fetch_json_array(
            path=(
                f"/api/v1/athlete/"
                f"{urllib.parse.quote(self.credentials.athlete_id, safe='')}"
                f"/wellness.json"
            ),
            query={"oldest": oldest.isoformat(), "newest": newest.isoformat()},
            endpoint_label="wellness",
        )

    def fetch_activities_range(self, oldest: date, newest: date) -> list[dict]:
        return self._fetch_json_array(
            path=(
                f"/api/v1/athlete/"
                f"{urllib.parse.quote(self.credentials.athlete_id, safe='')}"
                f"/activities"
            ),
            query={"oldest": oldest.isoformat(), "newest": newest.isoformat()},
            endpoint_label="activities",
        )

    def _fetch_json_array(
        self,
        *,
        path: str,
        query: dict[str, str],
        endpoint_label: str,
    ) -> list[dict]:
        qs = urllib.parse.urlencode(query)
        url = f"{self.base_url}{path}?{qs}"
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
                f"Intervals.icu {endpoint_label} fetch failed: HTTP {exc.code} {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise IntervalsIcuError(
                f"Intervals.icu {endpoint_label} fetch failed: {exc.reason}"
            ) from exc
        try:
            data = json.loads(body)
        except json.JSONDecodeError as exc:
            raise IntervalsIcuError(
                f"Intervals.icu {endpoint_label} response was not valid JSON"
            ) from exc
        if not isinstance(data, list):
            raise IntervalsIcuError(
                f"Intervals.icu {endpoint_label} response was not a JSON array"
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
    user_id: str = "u_local_1"
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

        activities = self._fetch_activities_safe(
            oldest=oldest, newest=as_of, user_id=self.user_id,
        )

        if records_by_date.get(as_of) is None:
            self.last_pull_partial = True
            self.last_pull_failed_days.append(as_of.isoformat())

        return {
            "sleep": sleep,
            "resting_hr": resting_hr,
            "hrv": hrv,
            "training_load": training_load,
            "raw_daily_row": raw_daily_row,
            "activities": [a.as_dict() for a in activities],
        }

    def _fetch_activities_safe(
        self, *, oldest: date, newest: date, user_id: str,
    ) -> list[IntervalsIcuActivity]:
        """Fetch activities, parse, and swallow endpoint-absent errors.

        A 404 or rejected activities endpoint should NOT fail the whole pull —
        wellness is the primary signal and we want `hai pull` to keep working
        even if an intervals.icu account has /activities disabled or the
        adapter hits a transient upstream error on the activities endpoint.
        The wellness-level partial flag still reflects wellness status only;
        activities failures log into ``last_pull_failed_days`` via the
        ``activities_endpoint`` sentinel so dogfooders can see the gap.
        """

        try:
            raw = self.client.fetch_activities_range(oldest=oldest, newest=newest)
        except IntervalsIcuError as exc:
            self.last_pull_failed_days.append(f"activities_endpoint:{exc}")
            return []

        return _parse_activities(raw, user_id=user_id)


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


def _as_int(v: Any) -> Optional[int]:
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return None


def _as_str_list(v: Any) -> Optional[list[str]]:
    if not isinstance(v, list):
        return None
    return [str(x) for x in v]


def _as_int_list(v: Any) -> Optional[list[int]]:
    if not isinstance(v, list):
        return None
    out: list[int] = []
    for x in v:
        if isinstance(x, bool):
            continue
        if isinstance(x, int):
            out.append(x)
        elif isinstance(x, float):
            out.append(int(x))
        else:
            return None
    return out


def _parse_activities(
    records: Iterable[dict], *, user_id: str,
) -> list[IntervalsIcuActivity]:
    """Map the raw /activities JSON array into typed IntervalsIcuActivity.

    Records missing an activity id or a usable date are skipped silently —
    intervals.icu occasionally returns placeholder shells. The full upstream
    record is preserved in ``raw_json`` so downstream skills can peek at
    fields we haven't typed.
    """

    out: list[IntervalsIcuActivity] = []
    for rec in records:
        if not isinstance(rec, dict):
            continue
        activity_id = rec.get("id")
        if not activity_id:
            continue
        as_of = _activity_as_of(rec)
        if as_of is None:
            continue
        raw_json = json.dumps(rec, sort_keys=True, default=str)
        out.append(
            IntervalsIcuActivity(
                activity_id=str(activity_id),
                user_id=user_id,
                as_of_date=as_of,
                start_date_utc=_as_optional_str(rec.get("start_date")),
                start_date_local=_as_optional_str(rec.get("start_date_local")),
                source=_as_optional_str(rec.get("source")),
                external_id=_as_optional_str(rec.get("external_id")),
                activity_type=_as_optional_str(rec.get("type")),
                name=_as_optional_str(rec.get("name")),
                distance_m=_as_number(rec.get("distance")) or _as_number(rec.get("icu_distance")),
                moving_time_s=_as_number(rec.get("moving_time")),
                elapsed_time_s=_as_number(rec.get("elapsed_time")),
                average_hr=_as_number(rec.get("average_heartrate")),
                max_hr=_as_number(rec.get("max_heartrate")),
                athlete_max_hr=_as_number(rec.get("athlete_max_hr")),
                hr_zone_times_s=_as_int_list(rec.get("icu_hr_zone_times")),
                hr_zones_bpm=_as_int_list(rec.get("icu_hr_zones")),
                interval_summary=_as_str_list(rec.get("interval_summary")),
                trimp=_as_number(rec.get("trimp")),
                icu_training_load=_as_number(rec.get("icu_training_load")),
                hr_load=_as_number(rec.get("hr_load")),
                hr_load_type=_as_optional_str(rec.get("hr_load_type")),
                warmup_time_s=_as_number(rec.get("icu_warmup_time")),
                cooldown_time_s=_as_number(rec.get("icu_cooldown_time")),
                lap_count=_as_int(rec.get("icu_lap_count")),
                average_speed_mps=_as_number(rec.get("average_speed")),
                max_speed_mps=_as_number(rec.get("max_speed")),
                pace_s_per_m=_as_number(rec.get("pace")),
                average_cadence_spm=_as_number(rec.get("average_cadence")),
                average_stride_m=_as_number(rec.get("average_stride")),
                calories=_as_number(rec.get("calories")),
                total_elevation_gain_m=_as_number(rec.get("total_elevation_gain")),
                total_elevation_loss_m=_as_number(rec.get("total_elevation_loss")),
                feel=_as_int(rec.get("feel")),
                icu_rpe=_as_int(rec.get("icu_rpe")),
                session_rpe=_as_number(rec.get("session_rpe")),
                device_name=_as_optional_str(rec.get("device_name")),
                raw_json=raw_json,
            )
        )
    out.sort(key=lambda a: (a.as_of_date, a.start_date_utc or "", a.activity_id))
    return out


def _activity_as_of(rec: dict) -> Optional[str]:
    """Derive the civil date (activity's local day) from an activities record.

    Prefers ``start_date_local`` (already in the athlete's local zone), falls
    back to ``start_date`` (UTC), and last resort parses the numeric id.
    Returns the ISO-8601 date string or None if nothing parseable.
    """

    for k in ("start_date_local", "start_date"):
        v = rec.get(k)
        if isinstance(v, str) and len(v) >= 10:
            try:
                return date.fromisoformat(v[:10]).isoformat()
            except ValueError:
                continue
    return None


def _as_optional_str(v: Any) -> Optional[str]:
    if v is None:
        return None
    if isinstance(v, str):
        return v if v else None
    return str(v)
