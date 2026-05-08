"""Deterministic + contract tests for health_agent_infra.

Judgment (state classification, policy, recommendation shaping) has moved
to agent-owned skills under ``skills/``. These tests cover only what the
runtime owns:

- PULL — Garmin adapter contract + real-export shape.
- CLEAN — baseline computation, missingness propagation, raw-summary aggregation.
- WRITEBACK — schema validation at the tool boundary, idempotency, locality.
- REVIEW — event scheduling, outcome persistence, summary counts.
- SCHEMAS — round-trip integrity.

Behavioural scenario tests from the pre-skill era were removed in commit 3.
Evaluating the skill-driven recommendation layer is done outside CI by
capturing agent outputs against golden scenarios.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    load_recovery_readiness_inputs,
)
from health_agent_infra.core.pull.protocol import FlagshipPullAdapter
from health_agent_infra.core.review.outcomes import (
    record_review_outcome,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    FollowUp,
    PolicyDecision,
    RECOMMENDATION_SCHEMA_VERSION,
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation


AS_OF = date(2026, 4, 16)
NOW = datetime(2026, 4, 16, 7, 15, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# CLEAN
# ---------------------------------------------------------------------------

def _baseline_week_rhr(as_of: date, base_bpm: float = 50.0) -> list[dict]:
    """Return 14 days of trailing RHR records around a baseline."""

    out = []
    for i in range(14, 0, -1):
        d = (as_of.fromordinal(as_of.toordinal() - i)).isoformat()
        out.append({"date": d, "bpm": base_bpm, "record_id": f"rhr_{d}"})
    return out


def _baseline_week_hrv(as_of: date, base_ms: float = 50.0) -> list[dict]:
    out = []
    for i in range(14, 0, -1):
        d = (as_of.fromordinal(as_of.toordinal() - i)).isoformat()
        out.append({"date": d, "rmssd_ms": base_ms, "record_id": f"hrv_{d}"})
    return out


def test_clean_emits_evidence_fields_from_inputs():
    evidence = clean_inputs(
        user_id="u_1",
        as_of_date=AS_OF,
        garmin_sleep={"duration_hours": 8.0, "record_id": "s_1"},
        garmin_resting_hr_recent=[{"date": AS_OF.isoformat(), "bpm": 55.0, "record_id": "rhr_today"}],
        garmin_hrv_recent=[{"date": AS_OF.isoformat(), "rmssd_ms": 60.0, "record_id": "hrv_today"}],
        garmin_training_load_7d=[{"date": AS_OF.isoformat(), "load": 400.0}],
        manual_readiness={
            "submission_id": "m_1",
            "soreness": "low",
            "energy": "moderate",
            "planned_session_type": "moderate",
            "active_goal": "strength_block",
        },
    )
    assert evidence.sleep_hours == 8.0
    assert evidence.sleep_record_id == "s_1"
    assert evidence.resting_hr == 55.0
    assert evidence.hrv_ms == 60.0
    assert evidence.trailing_7d_training_load == 400.0
    assert evidence.soreness_self_report == "low"
    assert evidence.active_goal == "strength_block"


def test_clean_handles_missing_sleep():
    evidence = clean_inputs(
        user_id="u_1",
        as_of_date=AS_OF,
        garmin_sleep=None,
        garmin_resting_hr_recent=[],
        garmin_hrv_recent=[],
        garmin_training_load_7d=[],
        manual_readiness=None,
    )
    assert evidence.sleep_hours is None
    assert evidence.sleep_record_id is None


def test_raw_summary_emits_baselines_and_ratios():
    rhr_history = _baseline_week_rhr(AS_OF, base_bpm=50.0)
    rhr_history.append({"date": AS_OF.isoformat(), "bpm": 58.0, "record_id": "rhr_today"})

    summary = build_raw_summary(
        user_id="u_1",
        as_of_date=AS_OF,
        garmin_sleep={"duration_hours": 7.0, "record_id": "s"},
        garmin_resting_hr_recent=rhr_history,
        garmin_hrv_recent=_baseline_week_hrv(AS_OF),
        garmin_training_load_7d=[],
    )
    assert summary.resting_hr == 58.0
    assert summary.resting_hr_baseline == pytest.approx(50.0)
    assert summary.resting_hr_ratio_vs_baseline == pytest.approx(58.0 / 50.0)
    assert summary.coverage_rhr_fraction == pytest.approx(7 / 7)  # 7 trailing days + today fit the window


def test_raw_summary_counts_rhr_spike_days():
    """3 consecutive days including today at >= 1.15x baseline == 3 spike days."""

    as_of = date(2026, 4, 16)
    history = _baseline_week_rhr(as_of - __import__("datetime").timedelta(days=3), base_bpm=50.0)
    # Spike the 3 most recent days (today + 2 prior)
    for i in range(3):
        d = (as_of.fromordinal(as_of.toordinal() - i)).isoformat()
        history.append({"date": d, "bpm": 60.0, "record_id": f"spike_{d}"})

    summary = build_raw_summary(
        user_id="u_1",
        as_of_date=as_of,
        garmin_sleep=None,
        garmin_resting_hr_recent=history,
        garmin_hrv_recent=[],
        garmin_training_load_7d=[],
    )
    assert summary.resting_hr_spike_days == 3


# ---------------------------------------------------------------------------
# PULL
# ---------------------------------------------------------------------------

def test_garmin_adapter_reads_committed_export_and_emits_fixture_shape():
    as_of = date(2026, 4, 8)
    pull = load_recovery_readiness_inputs(as_of)

    assert {"sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"} <= set(pull.keys())
    assert pull["sleep"] is not None
    assert "duration_hours" in pull["sleep"]
    assert any(row["date"] == as_of.isoformat() for row in pull["resting_hr"])
    # raw_daily_row carries the full CSV row for projection into
    # source_daily_garmin (state_model_v1.md §8, Phase 7A.3).
    assert pull["raw_daily_row"] is not None
    assert "resting_hr" in pull["raw_daily_row"]


def test_garmin_adapter_class_conforms_to_flagship_pull_protocol():
    adapter = GarminRecoveryReadinessAdapter()
    assert isinstance(adapter, FlagshipPullAdapter)
    assert adapter.source_name == "garmin"

    pull = adapter.load(date(2026, 4, 8))
    assert {"sleep", "resting_hr", "hrv", "training_load", "raw_daily_row"} <= set(pull.keys())


# ---------------------------------------------------------------------------
# WRITEBACK — contract (schema validation) + idempotency + locality
# ---------------------------------------------------------------------------

def _sample_recommendation(user_id: str = "u_1") -> TrainingRecommendation:
    return TrainingRecommendation(
        schema_version=RECOMMENDATION_SCHEMA_VERSION,
        recommendation_id=f"rec_{AS_OF.isoformat()}_{user_id}_01",
        user_id=user_id,
        issued_at=NOW,
        for_date=AS_OF,
        action="proceed_with_planned_session",
        action_detail={"active_goal": "strength_block"},
        rationale=["sleep_debt=none", "active_goal=strength_block"],
        confidence="high",
        uncertainty=[],
        follow_up=FollowUp(
            review_at=NOW.replace(day=17),
            review_question="Did today's session feel appropriate?",
            review_event_id=f"rev_2026-04-17_{user_id}_rec_{AS_OF.isoformat()}_{user_id}_01",
        ),
        policy_decisions=[
            PolicyDecision(rule_id="require_min_coverage", decision="allow", note="coverage=full"),
        ],
        bounded=True,
    )


# ---------------------------------------------------------------------------
# VALIDATOR — code-enforced boundary on agent-produced recommendation JSON.
# One test per stable invariant id. Each constructs a minimally malformed
# JSON violating only the target invariant and asserts the validator raises
# RecommendationValidationError with the matching id.
# ---------------------------------------------------------------------------

def _valid_recommendation_dict() -> dict:
    return _sample_recommendation().to_dict()


def test_validator_accepts_valid_recommendation():
    from health_agent_infra.core.validate import validate_recommendation_dict

    validate_recommendation_dict(_valid_recommendation_dict())  # must not raise


def test_validator_rejects_missing_required_fields():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict({"schema_version": "training_recommendation.v1"})
    assert exc.value.invariant == "required_fields_present"


def test_validator_rejects_wrong_schema_version():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["schema_version"] = "training_recommendation.v2"

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "schema_version"


def test_validator_rejects_unknown_action():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["action"] = "eat_a_sandwich"

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "action_enum"


def test_validator_rejects_unknown_confidence():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["confidence"] = "ultra_certain"

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "confidence_enum"


def test_validator_rejects_bounded_false():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["bounded"] = False

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "bounded_true"


@pytest.mark.parametrize(
    "token",
    ["diagnosis", "diagnose", "diagnosed", "syndrome", "disease",
     "disorder", "condition", "infection", "illness", "sick"],
)
def test_validator_rejects_banned_tokens_in_rationale(token: str):
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["rationale"] = [f"possible overtraining {token}"]

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "no_banned_tokens"


def test_validator_rejects_banned_tokens_in_action_detail():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["action_detail"] = {"caveat": "possible disorder flag"}

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "no_banned_tokens"


def test_validator_rejects_review_at_outside_24h_window():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    # issued_at is NOW (2026-04-16 07:15 UTC); push review_at to 2026-04-18 = ~42h
    data["follow_up"]["review_at"] = "2026-04-18T07:15:00+00:00"

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "review_at_within_24h"


def test_validator_rejects_review_at_before_issued_at():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    # review_at before issued_at (negative delta) also violates R4.
    data["follow_up"]["review_at"] = "2026-04-15T07:15:00+00:00"

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "review_at_within_24h"


# ---------------------------------------------------------------------------
# INTAKE — hai intake readiness composes with hai pull --manual-readiness-json
# ---------------------------------------------------------------------------

def _run_cli(argv: list[str], capsys) -> tuple[int, dict]:
    from health_agent_infra.cli import main
    rc = main(argv)
    out = capsys.readouterr().out
    return rc, json.loads(out) if out.strip() else {}


def test_intake_readiness_emits_valid_manual_readiness_dict(tmp_path: Path, capsys):
    rc, payload = _run_cli(
        [
            "intake", "readiness",
            "--soreness", "moderate",
            "--energy", "high",
            "--planned-session-type", "hard",
            "--active-goal", "strength_block",
            "--as-of", "2026-04-17",
            "--base-dir", str(tmp_path / "intake"),
        ],
        capsys,
    )
    assert rc == 0
    assert payload["soreness"] == "moderate"
    assert payload["energy"] == "high"
    assert payload["planned_session_type"] == "hard"
    assert payload["active_goal"] == "strength_block"
    assert payload["submission_id"].startswith("m_ready_2026-04-17_")


def test_intake_readiness_active_goal_is_optional(tmp_path: Path, capsys):
    rc, payload = _run_cli(
        [
            "intake", "readiness",
            "--soreness", "low",
            "--energy", "low",
            "--planned-session-type", "rest",
            "--base-dir", str(tmp_path / "intake"),
        ],
        capsys,
    )
    assert rc == 0
    assert "active_goal" not in payload  # absent when not supplied


def test_intake_readiness_rejects_bad_soreness_enum(tmp_path: Path, capsys):
    from health_agent_infra.cli import main
    with pytest.raises(SystemExit) as exc:
        main([
            "intake", "readiness",
            "--soreness", "extreme",
            "--energy", "high",
            "--planned-session-type", "hard",
            "--base-dir", str(tmp_path / "intake"),
        ])
    assert exc.value.code != 0  # argparse rejects before we ever produce JSON


def test_intake_readiness_output_feeds_hai_pull(tmp_path: Path, capsys):
    """The intake JSON must survive a round-trip through `hai pull
    --manual-readiness-json`: every field the intake emits lands in the
    pull payload's manual_readiness without loss."""

    from health_agent_infra.cli import main

    # 1. hai intake readiness -> stdout JSON
    rc = main([
        "intake", "readiness",
        "--soreness", "moderate",
        "--energy", "high",
        "--planned-session-type", "intervals",
        "--active-goal", "endurance_taper",
        "--as-of", "2026-04-08",
        "--base-dir", str(tmp_path / "intake"),
    ])
    assert rc == 0
    intake_json = capsys.readouterr().out
    readiness_file = tmp_path / "mr.json"
    readiness_file.write_text(intake_json, encoding="utf-8")

    # 2. hai pull --manual-readiness-json <that file>
    # F-PV14-01 (v0.1.15): default --source resolves to csv when no
    # intervals.icu credentials are configured; the guard refuses
    # against the canonical resolved DB unless we opt in.
    rc = main([
        "pull",
        "--date", "2026-04-08",
        "--user-id", "u_intake_test",
        "--manual-readiness-json", str(readiness_file),
        "--allow-fixture-into-real-state",
    ])
    assert rc == 0
    pull_payload = json.loads(capsys.readouterr().out)

    manual = pull_payload["manual_readiness"]
    assert manual["soreness"] == "moderate"
    assert manual["energy"] == "high"
    assert manual["planned_session_type"] == "intervals"
    assert manual["active_goal"] == "endurance_taper"
    assert manual["submission_id"].startswith("m_ready_2026-04-08_")


# ---------------------------------------------------------------------------
# Validator — policy_decisions_present
# ---------------------------------------------------------------------------


def test_validator_rejects_empty_policy_decisions():
    from health_agent_infra.core.validate import (
        RecommendationValidationError,
        validate_recommendation_dict,
    )

    data = _valid_recommendation_dict()
    data["policy_decisions"] = []

    with pytest.raises(RecommendationValidationError) as exc:
        validate_recommendation_dict(data)
    assert exc.value.invariant == "policy_decisions_present"


# ---------------------------------------------------------------------------
# REVIEW
# ---------------------------------------------------------------------------

def test_schedule_and_record_review(tmp_path: Path):
    base = tmp_path / "writeback"
    rec = _sample_recommendation()

    event = schedule_review(rec, base_dir=base)
    assert event.review_event_id == rec.follow_up.review_event_id

    outcome = record_review_outcome(
        event,
        base_dir=base,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="felt good",
        now=NOW,
    )
    assert outcome.followed_recommendation is True
    assert (base / "review_outcomes.jsonl").exists()


def test_summarize_review_history_on_empty_returns_zeroed_counts():
    summary = summarize_review_history([])
    assert summary == {
        "total": 0,
        "followed_improved": 0,
        "followed_no_change": 0,
        "followed_unknown": 0,
        "not_followed": 0,
    }


def test_summarize_review_history_counts_each_category():
    def _outcome(i: int, followed: bool, improvement) -> ReviewOutcome:
        return ReviewOutcome(
            review_event_id=f"rev_{i}",
            recommendation_id=f"rec_{i}",
            user_id="u_1",
            recorded_at=NOW,
            followed_recommendation=followed,
            self_reported_improvement=improvement,
        )

    outcomes = [
        _outcome(1, True, True),
        _outcome(2, True, True),
        _outcome(3, True, False),
        _outcome(4, True, None),
        _outcome(5, False, None),
    ]
    summary = summarize_review_history(outcomes)
    assert summary == {
        "total": 5,
        "followed_improved": 2,
        "followed_no_change": 1,
        "followed_unknown": 1,
        "not_followed": 1,
    }


# ---------------------------------------------------------------------------
# SCHEMAS — round-trip
# ---------------------------------------------------------------------------

def test_training_recommendation_round_trip():
    rec = _sample_recommendation()
    data = rec.to_dict()
    # Serialize to JSON and back — must not raise
    s = json.dumps(data, sort_keys=True)
    parsed = json.loads(s)
    assert parsed["action"] == "proceed_with_planned_session"
    assert parsed["policy_decisions"][0]["rule_id"] == "require_min_coverage"
