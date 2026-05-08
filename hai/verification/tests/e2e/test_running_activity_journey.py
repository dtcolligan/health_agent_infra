"""E2E: intervals.icu /activities endpoint → running domain coverage unblocks.

Pins the v0.1.4 core-thesis unblock (acceptance criterion #16) end-to-end
against the isolated ``e2e_env`` harness. The test doesn't hit the network —
it synthesises a ``hai pull`` output JSON that carries the activity payload
in the same shape the intervals.icu adapter emits, then drives ``hai clean``
→ ``hai state snapshot`` → reads the running block.

Guards against:
  - Pull→clean seam silently dropping the activities array (the whole
    2026-04-24 dogfood regression).
  - Projector forgetting to persist structural fields (hr_zone_times_s,
    interval_summary).
  - Snapshot forgetting to attach activities_today / activities_history
    to the running block.
  - Classifier coverage gate staying ``insufficient`` when activities
    are clearly present.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest


AS_OF = "2026-04-24"
YESTERDAY = "2026-04-23"
USER = "u_local_1"


# ---------------------------------------------------------------------------
# Fixtures — synthesized pull payload that mirrors the real adapter shape
# ---------------------------------------------------------------------------

def _activity(
    *,
    activity_id: str,
    as_of: str,
    activity_type: str = "Run",
    distance_m: float = 6000.0,
    moving_time_s: float = 2400.0,
    hr_zone_times_s: list[int] | None = None,
    interval_summary: list[str] | None = None,
) -> dict:
    """Mirrors IntervalsIcuActivity.as_dict() with minimal required keys."""

    if hr_zone_times_s is None:
        hr_zone_times_s = [1200, 200, 600, 400, 0, 0, 0]
    if interval_summary is None:
        interval_summary = ["warmup 10m", "steady 30m"]
    return {
        "activity_id": activity_id,
        "user_id": USER,
        "as_of_date": as_of,
        "start_date_utc": f"{as_of}T10:00:00Z",
        "start_date_local": f"{as_of}T11:00:00",
        "source": "GARMIN_CONNECT",
        "external_id": f"g_{activity_id}",
        "activity_type": activity_type,
        "name": "Test Run",
        "distance_m": distance_m,
        "moving_time_s": moving_time_s,
        "elapsed_time_s": moving_time_s + 1.0,
        "average_hr": 155.0,
        "max_hr": 182.0,
        "athlete_max_hr": 202.0,
        "hr_zone_times_s": hr_zone_times_s,
        "hr_zones_bpm": [154, 163, 172, 182, 187, 192, 202],
        "interval_summary": interval_summary,
        "trimp": 67.5,
        "icu_training_load": 39.0,
        "hr_load": 39.0,
        "hr_load_type": "HRSS",
        "warmup_time_s": 300.0,
        "cooldown_time_s": 300.0,
        "lap_count": 5,
        "average_speed_mps": 2.8,
        "max_speed_mps": 3.6,
        "pace_s_per_m": 2.8,
        "average_cadence_spm": 84.0,
        "average_stride_m": 1.0,
        "calories": 520.0,
        "total_elevation_gain_m": 23.4,
        "total_elevation_loss_m": 24.4,
        "feel": 3,
        "icu_rpe": 7,
        "session_rpe": 279.0,
        "device_name": "Garmin Forerunner 265",
        "raw_json": "{}",
    }


def _pull_payload(
    *,
    as_of_date: str,
    activities: list[dict],
    include_raw_daily_row: bool = True,
) -> dict:
    """A hai-pull-shaped envelope carrying wellness + activities.

    The wellness raw_daily_row deliberately nulls distance + intensity
    minutes so the test proves activity aggregation fills them in —
    matching the real intervals.icu behaviour where the wellness
    endpoint doesn't populate those fields.
    """

    raw = None
    if include_raw_daily_row:
        raw = {
            "date": as_of_date,
            "steps": 12000,
            "distance_m": None,
            "moderate_intensity_min": None,
            "vigorous_intensity_min": None,
            "resting_hr": 50.0,
            "acute_load": 14.0,
            "chronic_load": 12.0,
            "health_hrv_value": 89.0,
            "health_hr_value": 50.0,
            "sleep_total_sec": 28188,
        }
    return {
        "as_of_date": as_of_date,
        "user_id": USER,
        "source": "intervals_icu",
        "pull": {
            "sleep": {"record_id": f"i_sleep_{as_of_date}", "duration_hours": 7.83},
            "resting_hr": [{"date": as_of_date, "bpm": 50.0,
                             "record_id": f"i_rhr_{as_of_date}"}],
            "hrv": [{"date": as_of_date, "rmssd_ms": 89.0,
                       "record_id": f"i_hrv_{as_of_date}"}],
            "training_load": [{"date": as_of_date, "load": 14.0,
                                "record_id": f"i_load_{as_of_date}"}],
            "raw_daily_row": raw,
            "activities": activities,
        },
        "manual_readiness": None,
    }


def _write(tmp: Path, name: str, payload: dict) -> str:
    p = tmp / name
    p.write_text(json.dumps(payload), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# Journey 1 — single-day pull with one rich activity → session persists
# ---------------------------------------------------------------------------

def test_single_activity_flows_pull_clean_snapshot(e2e_env):
    """Narrow integration guard: one activity end-to-end.

    Catches any seam that silently drops the activity:
      - pull JSON missing activities
      - cmd_clean ignoring the activities key
      - projector failing upsert
      - snapshot forgetting the activities_today attachment
    """

    activity = _activity(
        activity_id="i_e2e_1",
        as_of=YESTERDAY,
        hr_zone_times_s=[1312, 254, 550, 282, 0, 0, 0],
        interval_summary=["4x 9m29s 156bpm", "1x 2m7s 146bpm"],
        distance_m=6746.21,
        moving_time_s=2399.0,
    )
    pull_path = _write(
        e2e_env.tmp_root, "pull_yesterday.json",
        _pull_payload(as_of_date=YESTERDAY, activities=[activity]),
    )
    e2e_env.run_hai("clean", "--evidence-json", pull_path)

    # DB: activity persisted verbatim (zone times serialised to JSON).
    row = e2e_env.sql_one(
        "SELECT activity_id, distance_m, moving_time_s, hr_zone_times_s_json, "
        "       interval_summary_json, activity_type "
        "FROM running_activity WHERE activity_id = ?",
        "i_e2e_1",
    )
    assert row is not None
    assert row["activity_id"] == "i_e2e_1"
    assert row["distance_m"] == pytest.approx(6746.21)
    assert row["activity_type"] == "Run"
    assert json.loads(row["hr_zone_times_s_json"]) == [1312, 254, 550, 282, 0, 0, 0]
    assert "4x 9m29s 156bpm" in row["interval_summary_json"]

    # Accepted rollup carries activity-derived distance + intensity minutes.
    rollup = e2e_env.sql_one(
        "SELECT total_distance_m, moderate_intensity_min, vigorous_intensity_min "
        "FROM accepted_running_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        YESTERDAY, USER,
    )
    assert rollup["total_distance_m"] == pytest.approx(6746.21)
    # Z2+Z3 = 254+550 = 804s = 13.4 min; Z4+ = 282s = 4.7 min
    assert rollup["moderate_intensity_min"] == pytest.approx(804 / 60.0)
    assert rollup["vigorous_intensity_min"] == pytest.approx(282 / 60.0)


def test_snapshot_running_block_surfaces_activities(e2e_env):
    """The snapshot's running block must expose the activities so skills
    + downstream renderers can read structural data without an extra query."""

    activity = _activity(
        activity_id="i_snap_1",
        as_of=YESTERDAY,
        interval_summary=["8x 400m @ 5k pace"],
    )
    pull_path = _write(
        e2e_env.tmp_root, "pull.json",
        _pull_payload(as_of_date=YESTERDAY, activities=[activity]),
    )
    e2e_env.run_hai("clean", "--evidence-json", pull_path)

    # Snapshot anchored on YESTERDAY surfaces the activity under today.
    result = e2e_env.run_hai(
        "state", "snapshot",
        "--as-of", YESTERDAY, "--user-id", USER,
    )
    snap = result["stdout_json"]
    running = snap["running"]
    assert "activities_today" in running
    assert "activities_history" in running
    assert len(running["activities_today"]) == 1
    assert running["activities_today"][0]["activity_id"] == "i_snap_1"
    assert running["activities_today"][0]["interval_summary"] == ["8x 400m @ 5k pace"]


# ---------------------------------------------------------------------------
# Journey 2 — window of activities → coverage flips off `insufficient`
# ---------------------------------------------------------------------------

def test_window_of_activities_unblocks_coverage_gate(e2e_env):
    """With ≥3 activities in the 14-day window, the classifier's coverage
    relaxation kicks in and running stops being forced to defer.

    This is the v0.1.4 core-thesis unblock: before this fix, the running
    block returned ``coverage=insufficient`` and ``forced_action=defer``
    on every day because the wellness stream never populated the 28-day
    distance baseline. With activities, coverage resolves via the
    activity-count path and a real recommendation becomes possible.
    """

    # Seed 5 history days + today, spread across the 14-day window.
    history_days = [
        "2026-04-22", "2026-04-20", "2026-04-17", "2026-04-14", "2026-04-12",
    ]
    for i, d in enumerate(history_days):
        activity = _activity(
            activity_id=f"i_hist_{i}",
            as_of=d,
            distance_m=7000.0,
            moving_time_s=2700.0,
            hr_zone_times_s=[1200, 400, 800, 100, 0, 0, 0],  # moderate session
        )
        pull_path = _write(
            e2e_env.tmp_root, f"pull_{d}.json",
            _pull_payload(as_of_date=d, activities=[activity]),
        )
        e2e_env.run_hai("clean", "--evidence-json", pull_path)

    # Today's pull with the 4×4 hard session.
    today_activity = _activity(
        activity_id="i_today_e2e",
        as_of=AS_OF,
        hr_zone_times_s=[1312, 254, 550, 282, 0, 0, 0],
        interval_summary=["4x 9m29s 156bpm", "1x 2m7s 146bpm"],
        distance_m=6746.21,
        moving_time_s=2399.0,
    )
    today_pull = _pull_payload(as_of_date=AS_OF, activities=[today_activity])
    today_path = _write(e2e_env.tmp_root, "pull_today.json", today_pull)
    clean_result = e2e_env.run_hai("clean", "--evidence-json", today_path)

    # Pipe the clean output through snapshot with --evidence-json so the
    # classifier + policy run and we can read the resolved coverage.
    clean_bundle_path = e2e_env.tmp_root / "clean_bundle.json"
    clean_bundle_path.write_text(clean_result["stdout"], encoding="utf-8")
    snap_result = e2e_env.run_hai(
        "state", "snapshot",
        "--as-of", AS_OF, "--user-id", USER,
        "--evidence-json", str(clean_bundle_path),
    )
    running = snap_result["stdout_json"]["running"]

    # Coverage no longer insufficient: the activity-count path cleared the
    # gate even though the 28-day distance baseline is still sparse.
    assert running["classified_state"]["coverage_band"] != "insufficient", (
        f"coverage should not be insufficient with 6 activities in window; "
        f"got classified_state={running['classified_state']}"
    )
    # Forced defer is gone.
    assert running["policy_result"]["forced_action"] != "defer_decision_insufficient_signal"
    # Signals carry the activity-derived structural data.
    sig = running["signals"]
    assert sig["activity_count_14d"] == 6
    assert sig["z4_plus_seconds_today"] == 282
    assert sig["today_interval_summary"] == [
        "4x 9m29s 156bpm", "1x 2m7s 146bpm",
    ]


# ---------------------------------------------------------------------------
# Journey 3 — no activities in pull → no regression on legacy path
# ---------------------------------------------------------------------------

def test_wellness_only_pull_leaves_running_activity_table_empty(e2e_env):
    """When the upstream doesn't deliver an activities stream (e.g. garmin
    CSV adapter, or intervals.icu with /activities disabled), the clean
    pipeline must degrade cleanly: no rows in running_activity, no crash."""

    payload = _pull_payload(as_of_date=AS_OF, activities=[])
    # Force: drop the activities key entirely (older pull outputs).
    del payload["pull"]["activities"]
    pull_path = _write(e2e_env.tmp_root, "pull_no_activities.json", payload)
    e2e_env.run_hai("clean", "--evidence-json", pull_path)

    (count,) = e2e_env.sql_one("SELECT COUNT(*) FROM running_activity")
    assert count == 0


def test_repull_same_day_is_idempotent(e2e_env):
    """Upsert on intervals.icu activity_id means re-pulling the same day
    shouldn't duplicate rows. Guards the `hai pull` + `hai clean` chain's
    first-class idempotency for activities."""

    activity = _activity(activity_id="i_idemp", as_of=YESTERDAY)
    pull_path = _write(
        e2e_env.tmp_root, "pull.json",
        _pull_payload(as_of_date=YESTERDAY, activities=[activity]),
    )
    e2e_env.run_hai("clean", "--evidence-json", pull_path)
    e2e_env.run_hai("clean", "--evidence-json", pull_path)  # second pass

    (count,) = e2e_env.sql_one(
        "SELECT COUNT(*) FROM running_activity WHERE activity_id = ?",
        "i_idemp",
    )
    assert count == 1
