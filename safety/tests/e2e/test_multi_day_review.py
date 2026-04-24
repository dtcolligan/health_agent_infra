"""E2E scenario 5 — multi-day review journey (v0.1.4 WS-E).

Scenario: day 1 user receives a plan + review event; day 2 user
records the outcome of yesterday's recommendation; day 2's
``hai state snapshot`` + ``hai explain`` see the outcome attached
to the canonical-leaf recommendation.

This validates the end-to-end audit-chain spine:

  day 1 : hai propose × 6 → hai synthesize → review_event scheduled
  day 2 : hai review record → review_outcome appended
          hai state snapshot → reviews.recent carries the outcome
          hai explain → reviews list carries the outcome

Outcomes are append-only, so re-running review record for the same
event is a legitimate operator action (not a bug). The test seeds
the day-1 plan via direct CLI calls so we're testing the review
pipeline against realistic persisted state.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from .conftest import E2EEnv


USER_ID = "u_multi_day"
DAY_1 = date(2026, 4, 22)
DAY_2 = DAY_1 + timedelta(days=1)


def _seed_six_domain_plan(env: E2EEnv, *, as_of: date) -> None:
    """Run `hai propose` × 6 + `hai synthesize` to land a canonical plan."""

    domain_defaults = {
        "recovery":  "proceed_with_planned_session",
        "running":   "proceed_with_planned_run",
        "sleep":     "maintain_schedule",
        "strength":  "proceed_with_planned_session",
        "stress":    "maintain_routine",
        "nutrition": "maintain_targets",
    }
    schemas = {
        "recovery":  "recovery_proposal.v1",
        "running":   "running_proposal.v1",
        "sleep":     "sleep_proposal.v1",
        "strength":  "strength_proposal.v1",
        "stress":    "stress_proposal.v1",
        "nutrition": "nutrition_proposal.v1",
    }
    for domain, action in domain_defaults.items():
        payload = {
            "schema_version": schemas[domain],
            "proposal_id": f"prop_{as_of}_{USER_ID}_{domain}_01",
            "user_id": USER_ID,
            "for_date": str(as_of),
            "domain": domain,
            "action": action,
            "action_detail": None,
            "rationale": [f"{domain}_baseline"],
            "confidence": "moderate",
            "uncertainty": [],
            "policy_decisions": [
                {"rule_id": "r_baseline", "decision": "allow", "note": "ok"},
            ],
            "bounded": True,
        }
        path = env.tmp_root / f"prop_{as_of}_{domain}.json"
        path.write_text(json.dumps(payload))
        env.run_hai(
            "propose", "--domain", domain,
            "--proposal-json", str(path),
            "--base-dir", str(env.base_dir),
        )
    env.run_hai(
        "synthesize",
        "--as-of", str(as_of), "--user-id", USER_ID,
    )


def test_day_2_snapshot_sees_day_1_review_outcome(e2e_env: E2EEnv) -> None:
    """Day 1's review outcome must surface on day 2's state snapshot
    under ``reviews.recent``. This is the path the per-domain skills
    read to condition tomorrow's recommendations on yesterday's
    outcome."""

    # --- Day 1: seed a plan, schedule the review event.
    _seed_six_domain_plan(e2e_env, as_of=DAY_1)

    recovery_rec_id = f"rec_{DAY_1}_{USER_ID}_recovery_01"
    # Schedule the review event via CLI so JSONL + DB are in sync.
    rec_row = e2e_env.sql_one(
        "SELECT payload_json FROM recommendation_log WHERE recommendation_id = ?",
        recovery_rec_id,
    )
    assert rec_row is not None
    rec_payload = json.loads(rec_row[0])
    rec_file = e2e_env.tmp_root / "day1_recovery_rec.json"
    rec_file.write_text(json.dumps(rec_payload), encoding="utf-8")
    e2e_env.run_hai(
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(e2e_env.base_dir),
    )

    # --- Day 2 morning: user logs yesterday's outcome. Pin
    # ``recorded_at`` to day 1 so the snapshot's lookback window
    # (history = [lookback_start, as_of - 1]) sees it — otherwise
    # wall-clock ``now`` would sit past the lookback's upper bound.
    outcome_payload = {
        "review_event_id": rec_payload["follow_up"]["review_event_id"],
        "recommendation_id": recovery_rec_id,
        "user_id": USER_ID,
        "domain": "recovery",
        "followed_recommendation": True,
        "self_reported_improvement": True,
        "free_text": "felt good, hit all intervals",
        "recorded_at": f"{DAY_1}T20:00:00+00:00",
    }
    outcome_file = e2e_env.tmp_root / "outcome.json"
    outcome_file.write_text(json.dumps(outcome_payload))
    e2e_env.run_hai(
        "review", "record",
        "--outcome-json", str(outcome_file),
        "--base-dir", str(e2e_env.base_dir),
    )

    # --- Day 2 snapshot — reviews.recent includes the outcome.
    snap_result = e2e_env.run_hai(
        "state", "snapshot",
        "--as-of", str(DAY_2), "--user-id", USER_ID,
    )
    snap = snap_result["stdout_json"]
    recent = snap["reviews"]["recent"]
    outcome_ids = [r["recommendation_id"] for r in recent]
    assert recovery_rec_id in outcome_ids

    # --- hai review summary — counts the outcome.
    summary_result = e2e_env.run_hai(
        "review", "summary",
        "--base-dir", str(e2e_env.base_dir),
        "--user-id", USER_ID,
        "--domain", "recovery",
    )
    summary = summary_result["stdout_json"]
    assert summary["total"] == 1
    assert summary["followed_improved"] == 1


def test_day_1_hai_explain_surfaces_the_outcome(e2e_env: E2EEnv) -> None:
    """``hai explain --for-date <day_1>`` must include the review
    outcome recorded against day 1's recommendation in its ``reviews``
    list. That's the auditability contract — a past plan + its
    outcome are jointly reconstructible."""

    _seed_six_domain_plan(e2e_env, as_of=DAY_1)
    recovery_rec_id = f"rec_{DAY_1}_{USER_ID}_recovery_01"
    rec_row = e2e_env.sql_one(
        "SELECT payload_json FROM recommendation_log WHERE recommendation_id = ?",
        recovery_rec_id,
    )
    rec_payload = json.loads(rec_row[0])
    rec_file = e2e_env.tmp_root / "rec.json"
    rec_file.write_text(json.dumps(rec_payload))
    e2e_env.run_hai(
        "review", "schedule",
        "--recommendation-json", str(rec_file),
        "--base-dir", str(e2e_env.base_dir),
    )

    outcome_payload = {
        "review_event_id": rec_payload["follow_up"]["review_event_id"],
        "recommendation_id": recovery_rec_id,
        "user_id": USER_ID,
        "domain": "recovery",
        "followed_recommendation": False,
        "self_reported_improvement": None,
        "free_text": "skipped",
        "recorded_at": f"{DAY_1}T20:00:00+00:00",
    }
    outcome_file = e2e_env.tmp_root / "outcome.json"
    outcome_file.write_text(json.dumps(outcome_payload))
    e2e_env.run_hai(
        "review", "record",
        "--outcome-json", str(outcome_file),
        "--base-dir", str(e2e_env.base_dir),
    )

    explain = e2e_env.run_hai(
        "explain",
        "--for-date", str(DAY_1), "--user-id", USER_ID,
    )
    bundle = explain["stdout_json"]

    # explain bundle carries reviews linked to the canonical plan.
    reviews = bundle.get("reviews") or []
    assert any(
        r.get("recommendation_id") == recovery_rec_id for r in reviews
    ), f"recovery outcome not surfaced in explain bundle; reviews={reviews}"
