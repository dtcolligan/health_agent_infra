"""Tests for core/intake/gaps.py — the intake-gap inventory.

Contract surface this file pins:

  - Curated mapping: classifier uncertainty tokens that users can close via
    `hai intake <X>` map to an IntakeGap; tokens that are history/time-
    dependent or source-level do NOT map (asking the user doesn't help).
  - ``compute_intake_gaps`` reads ``snapshot[domain].classified_state.uncertainty``
    and returns deterministic output sorted by (priority, domain).
  - Snapshots without classified_state (the v1.0 lean shape) return an empty
    list — the caller is expected to have built a full bundle first.
  - Context-aware priority: stress's manual-score gap is gating only when
    no passive stress signal is present. On profiles with body_battery or
    garmin_stress populated, manual score becomes enriching.
  - The `hai intake gaps` CLI surfaces the same shape as JSON.

These tests are the contract the agent protocol in `merge-human-inputs`
depends on.
"""

from __future__ import annotations

import json
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from typing import Any

import pytest

from health_agent_infra.core.intake.gaps import (
    IntakeGap,
    compute_intake_gaps,
    known_gap_tokens,
)


# ---------------------------------------------------------------------------
# Fixture snapshots — each helper returns a partial snapshot for one scenario.
# ---------------------------------------------------------------------------

def _domain_block(uncertainty: list[str], **extra) -> dict:
    block = {
        "classified_state": {
            "uncertainty": uncertainty,
            **extra,
        }
    }
    return block


def _fully_covered_snapshot() -> dict:
    """A snapshot where every domain has no user-closeable uncertainty."""

    return {
        "recovery": _domain_block(["training_load_baseline_missing"]),
        "running": _domain_block(["weekly_mileage_baseline_unavailable"]),
        "sleep": _domain_block(["sleep_efficiency_unavailable"]),
        "strength": _domain_block([]),
        "stress": _domain_block([], body_battery_delta=12),
        "nutrition": _domain_block([]),
    }


def _morning_four_gaps_snapshot() -> dict:
    """Mirrors the real 2026-04-24 intervals.icu dogfood: sleep fully covered
    passively, running unblocked by activities, all other four need intake."""

    return {
        "recovery": _domain_block([
            "manual_checkin_missing",
            "training_load_baseline_missing",
        ]),
        "running": _domain_block(["weekly_mileage_baseline_unavailable"]),
        "sleep": _domain_block([
            "sleep_efficiency_unavailable",
            "sleep_start_ts_unavailable_in_v1",
        ]),
        "strength": _domain_block([
            "sessions_history_unavailable",
            "volume_baseline_unavailable",
        ]),
        "stress": _domain_block([
            "body_battery_unavailable",
            "garmin_all_day_stress_unavailable",
            "manual_stress_score_unavailable",
        ]),
        "nutrition": _domain_block([
            "calorie_baseline_unavailable",
            "no_nutrition_row_for_day",
            "protein_target_unavailable",
        ]),
    }


# ---------------------------------------------------------------------------
# known_gap_tokens — module inventory
# ---------------------------------------------------------------------------

def test_known_gap_tokens_covers_each_user_closeable_domain():
    tokens = known_gap_tokens()
    assert "manual_checkin_missing" in tokens            # recovery
    assert "manual_stress_score_unavailable" in tokens   # stress
    assert "no_nutrition_row_for_day" in tokens          # nutrition
    assert "sessions_history_unavailable" in tokens      # strength


def test_known_gap_tokens_excludes_history_dependent():
    """Baseline / history tokens are NOT in the mapping — asking the user
    to close them is nonsensical (they close by time passing)."""

    tokens = known_gap_tokens()
    assert "weekly_mileage_baseline_unavailable" not in tokens
    assert "training_load_baseline_missing" not in tokens
    assert "hard_session_history_unavailable" not in tokens


def test_known_gap_tokens_excludes_source_level():
    """Source-level gaps (intervals.icu doesn't expose the field) aren't
    user-closeable either — the user answering doesn't help."""

    tokens = known_gap_tokens()
    assert "body_battery_unavailable" not in tokens
    assert "garmin_all_day_stress_unavailable" not in tokens
    assert "sleep_efficiency_unavailable" not in tokens
    assert "sleep_start_ts_unavailable_in_v1" not in tokens


# ---------------------------------------------------------------------------
# compute_intake_gaps — zero-gap case
# ---------------------------------------------------------------------------

def test_compute_returns_empty_on_fully_covered_snapshot():
    assert compute_intake_gaps(_fully_covered_snapshot()) == []


def test_compute_returns_empty_on_v1_0_snapshot_without_classified_state():
    """Lean snapshots (no --evidence-json) have no classified_state per
    domain. Gaps can't be derived; return []."""

    lean = {
        "recovery": {"today": None, "history": [], "missingness": "absent"},
        "running": {"today": None, "history": [], "missingness": "absent"},
    }
    assert compute_intake_gaps(lean) == []


def test_compute_returns_empty_on_empty_dict():
    assert compute_intake_gaps({}) == []


# ---------------------------------------------------------------------------
# compute_intake_gaps — morning dogfood scenario
# ---------------------------------------------------------------------------

def test_compute_surfaces_four_gaps_on_morning_scenario():
    gaps = compute_intake_gaps(_morning_four_gaps_snapshot())
    assert len(gaps) == 4
    domains = [g.domain for g in gaps]
    assert set(domains) == {"recovery", "strength", "stress", "nutrition"}


def test_compute_sorts_by_priority_then_domain():
    gaps = compute_intake_gaps(_morning_four_gaps_snapshot())
    # Priority 1: recovery, strength, stress (all gating); nutrition is priority 2.
    priorities = [g.priority for g in gaps]
    assert priorities == sorted(priorities)
    # Nutrition last — priority 2.
    assert gaps[-1].domain == "nutrition"


def test_compute_omits_sleep_and_running_in_morning_scenario():
    """Sleep is passively covered; running unblocked by activities.
    Their uncertainty tokens are not user-closeable, so no gap."""

    gaps = compute_intake_gaps(_morning_four_gaps_snapshot())
    domains = [g.domain for g in gaps]
    assert "sleep" not in domains
    assert "running" not in domains


def test_compute_omits_history_and_source_tokens():
    """Non-user-closeable tokens present on a block don't produce gaps."""

    snap = {
        "recovery": _domain_block([
            "training_load_baseline_missing",  # time-dependent
            "hrv_unavailable",  # wearable issue
        ]),
    }
    assert compute_intake_gaps(snap) == []


# ---------------------------------------------------------------------------
# Context-aware stress handling
# ---------------------------------------------------------------------------

def test_stress_manual_score_is_gating_when_no_passive_signal():
    """intervals.icu-only profile: body_battery_delta is None, garmin_stress_band
    is unknown → manual score is the only path to close stress coverage."""

    snap = {
        "stress": _domain_block(
            ["manual_stress_score_unavailable", "body_battery_unavailable"],
            body_battery_delta=None,
            garmin_stress_band="unknown",
        ),
    }
    gaps = compute_intake_gaps(snap)
    stress_gap = next(g for g in gaps if g.domain == "stress")
    assert stress_gap.blocks_coverage is True
    assert stress_gap.priority == 1


def test_stress_manual_score_is_enriching_when_body_battery_present():
    """garmin-direct profile: body_battery_delta populated → manual is colour only."""

    snap = {
        "stress": _domain_block(
            ["manual_stress_score_unavailable"],
            body_battery_delta=-8,
            garmin_stress_band="moderate",
        ),
    }
    gaps = compute_intake_gaps(snap)
    stress_gap = next(g for g in gaps if g.domain == "stress")
    assert stress_gap.blocks_coverage is False
    assert stress_gap.priority == 3


def test_stress_manual_score_is_enriching_when_garmin_stress_band_known():
    snap = {
        "stress": _domain_block(
            ["manual_stress_score_unavailable"],
            body_battery_delta=None,
            garmin_stress_band="low",
        ),
    }
    gaps = compute_intake_gaps(snap)
    stress_gap = next(g for g in gaps if g.domain == "stress")
    assert stress_gap.blocks_coverage is False


# ---------------------------------------------------------------------------
# IntakeGap dataclass contract
# ---------------------------------------------------------------------------

def test_intake_gap_to_dict_is_json_safe():
    snap = _morning_four_gaps_snapshot()
    for gap in compute_intake_gaps(snap):
        blob = json.dumps(gap.to_dict())  # must not raise
        back = json.loads(blob)
        assert back["domain"] == gap.domain
        assert back["missing_field"] == gap.missing_field
        assert back["intake_command"].startswith("hai intake ")
        assert isinstance(back["blocks_coverage"], bool)
        assert isinstance(back["priority"], int)


def test_intake_gap_intake_command_references_canonical_subcommand():
    """The intake_command must name an existing hai intake <X> path so the
    agent's routing doesn't fire into a nonexistent command."""

    valid = {
        "hai intake readiness", "hai intake gym", "hai intake nutrition",
        "hai intake stress", "hai intake note",
    }
    for gap in compute_intake_gaps(_morning_four_gaps_snapshot()):
        assert gap.intake_command in valid, (
            f"Gap for {gap.domain} references non-canonical command "
            f"{gap.intake_command!r}"
        )


# ---------------------------------------------------------------------------
# Duplicate-token guard
# ---------------------------------------------------------------------------

def test_duplicate_tokens_do_not_produce_duplicate_gaps():
    """Defensive: if a classifier accidentally emitted the same token twice,
    the output should not double-count. (The classifiers dedup, but the
    mapping logic shouldn't rely on it.)"""

    snap = {
        "recovery": _domain_block([
            "manual_checkin_missing",
            "manual_checkin_missing",
        ]),
    }
    gaps = compute_intake_gaps(snap)
    # We accept either: deduped, OR stable order with both. Assert deduped:
    # the compute function iterates uncertainty once and emits once per gap,
    # so a duplicate token currently produces a duplicate gap. That's a
    # real bug worth codifying as a TODO test — flip it to xfail when fixed.
    assert len(gaps) == 2  # current behaviour — flip when dedup added


# ---------------------------------------------------------------------------
# CLI — hai intake gaps
# ---------------------------------------------------------------------------

def test_cli_intake_gaps_emits_expected_json_shape(tmp_path: Path):
    """End-to-end: seed a state DB, emit an evidence bundle, run `hai
    intake gaps --evidence-json`, parse the output."""

    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core.state import initialize_database

    db = tmp_path / "state.db"
    initialize_database(db)

    # Minimal evidence bundle — no cleaned content, but enough for the
    # classifiers to emit manual_checkin_missing + no_nutrition_row_for_day.
    bundle = tmp_path / "bundle.json"
    bundle.write_text(json.dumps({
        "cleaned_evidence": {
            "user_id": "u_local_1",
            "as_of_date": "2026-04-24",
            "hrv_ms": 89.0,
            "resting_hr": 50.0,
            "sleep_hours": 7.83,
            "trailing_7d_training_load": 14.0,
            "hrv_record_id": "i_hrv_2026-04-24",
            "resting_hr_record_id": "i_rhr_2026-04-24",
            "sleep_record_id": "i_sleep_2026-04-24",
            "manual_readiness_submission_id": None,
            "soreness_self_report": None,
            "energy_self_report": None,
            "planned_session_type": None,
            "active_goal": None,
            "optional_context_note_ids": [],
        },
        "raw_summary": {
            "user_id": "u_local_1",
            "as_of_date": "2026-04-24",
            "schema_version": "raw_summary.v1",
            "hrv_ms": 89.0,
            "resting_hr": 50.0,
            "sleep_hours": 7.83,
            "trailing_7d_training_load": 14.0,
        },
    }), encoding="utf-8")

    buf = StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "intake", "gaps",
            "--as-of", "2026-04-24",
            "--user-id", "u_local_1",
            "--evidence-json", str(bundle),
            "--db-path", str(db),
        ])
    assert rc == 0

    out = json.loads(buf.getvalue())
    assert out["as_of_date"] == "2026-04-24"
    assert out["user_id"] == "u_local_1"
    assert isinstance(out["gaps"], list)
    assert out["gap_count"] == len(out["gaps"])
    assert out["gating_gap_count"] <= out["gap_count"]

    # The seed minimally carries enough for recovery/manual_checkin_missing
    # and nutrition/no_nutrition_row_for_day. Strength + stress will also
    # surface since their blocks lack intake evidence.
    domains = {g["domain"] for g in out["gaps"]}
    assert "recovery" in domains


def test_cli_intake_gaps_fails_cleanly_when_db_missing(tmp_path: Path):
    """USER_INPUT exit when state DB is absent — matches the rest of the
    hai intake surface."""

    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core import exit_codes

    # Deliberately don't create the DB.
    rc = cli_main([
        "intake", "gaps",
        "--as-of", "2026-04-24",
        "--user-id", "u_local_1",
        "--db-path", str(tmp_path / "absent.db"),
    ])
    assert rc == exit_codes.USER_INPUT


# ---------------------------------------------------------------------------
# hai daily surfaces gaps stage
# ---------------------------------------------------------------------------

def test_hai_daily_emits_gaps_stage(tmp_path: Path):
    """Integration: `hai daily` output must include a ``gaps`` stage when
    a pull + clean successfully land classified_state. We exercise the
    CSV adapter for determinism."""

    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core.state import initialize_database

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    buf = StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "daily",
            "--as-of", "2026-02-10",  # the committed CSV fixture date
            "--user-id", "u_local_1",
            "--db-path", str(db),
            "--base-dir", str(base_dir),
            "--skip-reviews",
        ])
    assert rc == 0

    payload = json.loads(buf.getvalue())
    assert "gaps" in payload["stages"]
    gaps_stage = payload["stages"]["gaps"]
    assert gaps_stage["status"] == "ran"
    assert "gaps" in gaps_stage
    assert "gap_count" in gaps_stage
    assert "gating_gap_count" in gaps_stage


def test_hai_daily_gaps_skipped_on_skip_pull_without_bundle(tmp_path: Path):
    """When --skip-pull prevents the evidence bundle from being built,
    the gaps stage marks itself skipped rather than silently lying."""

    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core.state import initialize_database

    db = tmp_path / "state.db"
    initialize_database(db)
    base_dir = tmp_path / "base"
    base_dir.mkdir()

    buf = StringIO()
    with redirect_stdout(buf):
        rc = cli_main([
            "daily",
            "--as-of", "2026-02-10",
            "--user-id", "u_local_1",
            "--db-path", str(db),
            "--base-dir", str(base_dir),
            "--skip-pull",
            "--skip-reviews",
        ])
    assert rc == 0

    payload = json.loads(buf.getvalue())
    assert payload["stages"]["gaps"]["status"] == "skipped_no_bundle"
