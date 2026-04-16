"""Tests for the flagship recovery_readiness_v1 end-to-end loop.

Covers:
- CLEAN: baseline derivation, missing-value propagation, RHR spike counting
- STATE: coverage banding, enum derivation, uncertainty token emission
- POLICY: insufficient-signal block, sparse-signal soften, diagnosis block,
  review-required block, bounded-action block, RHR spike escalation
- RECOMMEND: full-loop construction and policy trace preservation
- ACTION: idempotent writeback, writeback_locality enforcement
- REVIEW: scheduling and outcome recording

These tests run offline without any network or real Garmin data, using
the synthetic fixtures in clean.health_model.recovery_readiness_v1.fixtures.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_model.recovery_readiness_v1 import (
    build_recovery_state,
    build_training_recommendation,
    clean_inputs,
    perform_writeback,
    record_review_outcome,
    schedule_review,
)
from health_model.recovery_readiness_v1.fixtures import (
    garmin_pull_fixture,
    manual_readiness_fixture,
)
from health_model.recovery_readiness_v1.cli import run as cli_run


AS_OF = date(2026, 4, 16)
NOW = datetime(2026, 4, 16, 7, 15, tzinfo=timezone.utc)


def _run_cli(base_dir: Path, scenario: str, **kwargs) -> dict:
    """Invoke the CLI's `run` directly for end-to-end capture."""

    import argparse

    ns = argparse.Namespace(
        command="run",
        scenario=scenario,
        base_dir=str(base_dir),
        date=AS_OF.isoformat(),
        user_id=kwargs.get("user_id", "u_local_1"),
        now=NOW.isoformat(),
        record_review_outcome=kwargs.get("record_review_outcome"),
        emit_json=False,
    )
    return cli_run(ns)


def _build_state(scenario: str):
    pull = garmin_pull_fixture(AS_OF, scenario=scenario)
    manual = manual_readiness_fixture(AS_OF, scenario=scenario)
    evidence = clean_inputs(
        user_id="u_local_1",
        as_of_date=AS_OF,
        garmin_sleep=pull["sleep"],
        garmin_resting_hr_recent=pull["resting_hr"],
        garmin_hrv_recent=pull["hrv"],
        garmin_training_load_7d=pull["training_load"],
        manual_readiness=manual,
    )
    state = build_recovery_state(evidence, now=NOW)
    return evidence, state


# ---------------------------------------------------------------------------
# CLEAN layer
# ---------------------------------------------------------------------------

def test_clean_emits_baselines_and_trailing_load():
    evidence, _ = _build_state("mildly_impaired_with_hard_plan")
    assert evidence.resting_hr == 55.0
    assert evidence.resting_hr_baseline is not None
    assert evidence.trailing_7d_training_load is not None
    assert evidence.soreness_self_report == "moderate"


def test_clean_handles_missing_sleep():
    evidence, _ = _build_state("insufficient_signal")
    assert evidence.sleep_hours is None
    assert evidence.manual_readiness_submission_id is None


def test_clean_counts_rhr_spike_days():
    evidence, _ = _build_state("rhr_spike_three_days")
    assert evidence.resting_hr_spike_days >= 3


# ---------------------------------------------------------------------------
# STATE layer
# ---------------------------------------------------------------------------

def test_state_insufficient_when_sleep_missing():
    _, state = _build_state("insufficient_signal")
    assert state.signal_quality.coverage == "insufficient"
    assert state.recovery_status == "unknown"
    assert state.readiness_score is None
    assert "sleep_record_missing" in state.uncertainties


def test_state_sparse_when_hrv_missing_and_rhr_limited():
    _, state = _build_state("sparse_signal")
    assert state.signal_quality.coverage in {"partial", "sparse"}
    assert "hrv_unavailable" in state.uncertainties


def test_state_partial_full_coverage_on_normal_scenario():
    _, state = _build_state("mildly_impaired_with_hard_plan")
    assert state.signal_quality.coverage in {"full", "partial"}
    assert state.recovery_status in {"mildly_impaired", "impaired"}


# ---------------------------------------------------------------------------
# POLICY + RECOMMEND layer
# ---------------------------------------------------------------------------

def test_policy_blocks_on_insufficient_signal():
    _, state = _build_state("insufficient_signal")
    rec = build_training_recommendation(state, now=NOW, rhr_spike_days=0)
    assert rec.action == "defer_decision_insufficient_signal"
    assert rec.confidence == "low"
    ids = [d.rule_id for d in rec.policy_decisions]
    assert "require_min_coverage" in ids
    decision = next(d for d in rec.policy_decisions if d.rule_id == "require_min_coverage")
    assert decision.decision == "block"


def test_policy_softens_high_to_moderate_on_sparse_scenario():
    """End-to-end: sparse coverage produces a visible R2 soften audit entry."""

    evidence, state = _build_state("sparse_signal")
    assert state.signal_quality.coverage == "sparse"
    rec = build_training_recommendation(
        state,
        now=NOW,
        rhr_spike_days=evidence.resting_hr_spike_days,
        planned_session_type=evidence.planned_session_type,
    )
    soften_decisions = [
        d for d in rec.policy_decisions
        if d.rule_id == "no_high_confidence_on_sparse_signal"
    ]
    assert soften_decisions, "R2 must emit a soften audit entry on sparse coverage"
    assert soften_decisions[0].decision == "soften"
    assert rec.confidence == "moderate"


def test_policy_r2_soften_is_proven_directly():
    """Unit-style: calling evaluate_policy with high confidence on sparse state."""

    from health_model.recovery_readiness_v1.policy import Proposal, evaluate_policy

    _, state = _build_state("sparse_signal")
    assert state.signal_quality.coverage == "sparse"
    proposal = Proposal(
        action="proceed_with_planned_session",
        action_detail=None,
        rationale=["sleep_debt=none"],
        confidence="high",
        uncertainty=list(state.uncertainties),
        follow_up_present=True,
        follow_up_within_24h=True,
    )
    evaluation = evaluate_policy(state, proposal, rhr_spike_days=0)
    assert not evaluation.blocked
    assert evaluation.mutated.confidence == "moderate"
    rule_ids = [d.rule_id for d in evaluation.decisions]
    assert "no_high_confidence_on_sparse_signal" in rule_ids
    soften = next(d for d in evaluation.decisions if d.rule_id == "no_high_confidence_on_sparse_signal")
    assert soften.decision == "soften"


def test_policy_escalates_on_rhr_spike_three_days():
    """R4 ties to state.resting_hr_vs_baseline == 'well_above' via the shared threshold."""

    evidence, state = _build_state("rhr_spike_three_days")
    assert state.resting_hr_vs_baseline == "well_above", (
        "R4 doctrine requires state.resting_hr_vs_baseline == 'well_above'; "
        "CLEAN spike threshold must match the STATE well_above band"
    )
    assert evidence.resting_hr_spike_days >= 3
    rec = build_training_recommendation(
        state,
        now=NOW,
        rhr_spike_days=evidence.resting_hr_spike_days,
        planned_session_type=evidence.planned_session_type,
    )
    assert rec.action == "escalate_for_user_review"
    ids = [d.rule_id for d in rec.policy_decisions]
    assert "resting_hr_spike_escalation" in ids


def test_policy_blocks_on_diagnosis_language():
    """A rationale containing diagnosis-shaped tokens must be blocked."""

    from health_model.recovery_readiness_v1.policy import Proposal, evaluate_policy

    _, state = _build_state("mildly_impaired_with_hard_plan")
    bad = Proposal(
        action="rest_day_recommended",
        action_detail=None,
        rationale=["likely overtraining syndrome today"],
        confidence="moderate",
        uncertainty=[],
        follow_up_present=True,
        follow_up_within_24h=True,
    )
    evaluation = evaluate_policy(state, bad, rhr_spike_days=0)
    assert evaluation.blocked
    rule_ids = [d.rule_id for d in evaluation.decisions]
    assert "no_diagnosis" in rule_ids


def test_policy_blocks_on_missing_follow_up():
    from health_model.recovery_readiness_v1.policy import Proposal, evaluate_policy

    _, state = _build_state("mildly_impaired_with_hard_plan")
    bad = Proposal(
        action="rest_day_recommended",
        action_detail=None,
        rationale=["sleep_debt=moderate"],
        confidence="moderate",
        uncertainty=[],
        follow_up_present=False,
        follow_up_within_24h=False,
    )
    evaluation = evaluate_policy(state, bad, rhr_spike_days=0)
    assert evaluation.blocked
    rule_ids = [d.rule_id for d in evaluation.decisions]
    assert "review_required" in rule_ids


def test_policy_blocks_unknown_action():
    from health_model.recovery_readiness_v1.policy import Proposal, evaluate_policy

    _, state = _build_state("mildly_impaired_with_hard_plan")
    bad = Proposal(
        action="order_bloodwork",  # type: ignore[arg-type]
        action_detail=None,
        rationale=["sleep_debt=moderate"],
        confidence="moderate",
        uncertainty=[],
        follow_up_present=True,
        follow_up_within_24h=True,
    )
    evaluation = evaluate_policy(state, bad, rhr_spike_days=0)
    assert evaluation.blocked
    rule_ids = [d.rule_id for d in evaluation.decisions]
    assert "bounded_action_envelope" in rule_ids


# ---------------------------------------------------------------------------
# ACTION layer
# ---------------------------------------------------------------------------

def test_writeback_is_idempotent(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    _, state = _build_state("mildly_impaired_with_hard_plan")
    rec = build_training_recommendation(
        state, now=NOW, rhr_spike_days=0, planned_session_type="hard"
    )
    first = perform_writeback(rec, base_dir=base, now=NOW)
    second = perform_writeback(rec, base_dir=base, now=NOW)
    assert first.recommendation_id == second.recommendation_id

    log_path = Path(first.writeback_path)
    lines = [
        line for line in log_path.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    assert len(lines) == 1
    assert json.loads(lines[0])["recommendation_id"] == rec.recommendation_id


def test_writeback_locality_enforced_outside_allowed_root(tmp_path: Path):
    outside = tmp_path / "elsewhere"
    _, state = _build_state("mildly_impaired_with_hard_plan")
    rec = build_training_recommendation(
        state, now=NOW, rhr_spike_days=0, planned_session_type="hard"
    )
    with pytest.raises(ValueError):
        perform_writeback(rec, base_dir=outside, now=NOW)


# ---------------------------------------------------------------------------
# REVIEW layer
# ---------------------------------------------------------------------------

def test_schedule_and_record_review(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    _, state = _build_state("mildly_impaired_with_hard_plan")
    rec = build_training_recommendation(
        state, now=NOW, rhr_spike_days=0, planned_session_type="hard"
    )
    perform_writeback(rec, base_dir=base, now=NOW)
    event = schedule_review(rec, base_dir=base)
    outcome = record_review_outcome(
        event,
        base_dir=base,
        followed_recommendation=True,
        self_reported_improvement=True,
        free_text="session felt easier than expected",
        now=NOW,
    )
    assert outcome.recommendation_id == rec.recommendation_id
    assert (base / "review_events.jsonl").exists()
    assert (base / "review_outcomes.jsonl").exists()


# ---------------------------------------------------------------------------
# End-to-end CLI
# ---------------------------------------------------------------------------

def test_cli_end_to_end_mildly_impaired(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    artifact = _run_cli(base, "mildly_impaired_with_hard_plan",
                        record_review_outcome="followed_and_improved")
    assert artifact["recovery_state"]["recovery_status"] in {"mildly_impaired", "impaired"}
    assert artifact["training_recommendation"]["action"] in {
        "downgrade_hard_session_to_zone_2",
        "downgrade_session_to_mobility_only",
        "rest_day_recommended",
    }
    assert artifact["training_recommendation"]["bounded"] is True
    assert artifact["action_record"]["recommendation_id"] == artifact["training_recommendation"]["recommendation_id"]
    assert artifact["review_event"]["recommendation_id"] == artifact["training_recommendation"]["recommendation_id"]
    assert artifact["review_outcome"]["followed_recommendation"] is True


def test_cli_end_to_end_insufficient(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    artifact = _run_cli(base, "insufficient_signal")
    assert artifact["recovery_state"]["signal_quality"]["coverage"] == "insufficient"
    assert artifact["training_recommendation"]["action"] == "defer_decision_insufficient_signal"
    assert artifact["training_recommendation"]["confidence"] == "low"


def test_cli_end_to_end_recovered(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    artifact = _run_cli(base, "recovered_with_easy_plan")
    assert artifact["recovery_state"]["recovery_status"] == "recovered"
    assert artifact["training_recommendation"]["action"] == "proceed_with_planned_session"


def test_cli_end_to_end_rhr_spike(tmp_path: Path):
    base = tmp_path / "recovery_readiness_v1"
    artifact = _run_cli(base, "rhr_spike_three_days")
    assert artifact["training_recommendation"]["action"] == "escalate_for_user_review"
    assert artifact["training_recommendation"]["action_detail"]["reason_token"] == "resting_hr_spike_3_days_running"
