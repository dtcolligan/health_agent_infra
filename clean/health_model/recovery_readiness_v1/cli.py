"""End-to-end CLI runner for the flagship recovery_readiness_v1 loop.

Usage:
    python -m clean.health_model.recovery_readiness_v1.cli run \
        --scenario mildly_impaired_with_hard_plan \
        --base-dir /tmp/recovery_readiness_v1 \
        --date 2026-04-16

The CLI executes PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
using synthetic fixtures for PULL. All artifacts land under `base-dir`.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from health_model.recovery_readiness_v1.action import perform_writeback
from health_model.recovery_readiness_v1.clean import clean_inputs
from health_model.recovery_readiness_v1.fixtures import (
    garmin_pull_fixture,
    manual_readiness_fixture,
)
from health_model.recovery_readiness_v1.recommend import build_training_recommendation
from health_model.recovery_readiness_v1.review import (
    record_review_outcome,
    schedule_review,
)
from health_model.recovery_readiness_v1.state import build_recovery_state


SCENARIOS = (
    "recovered_with_easy_plan",
    "mildly_impaired_with_hard_plan",
    "impaired_with_hard_plan",
    "rhr_spike_three_days",
    "insufficient_signal",
    "sparse_signal",
)


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="recovery_readiness_v1")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Run the flagship loop end-to-end")
    run.add_argument("--scenario", choices=SCENARIOS, default="mildly_impaired_with_hard_plan")
    run.add_argument("--base-dir", required=True, help="Writeback root (must contain 'recovery_readiness_v1')")
    run.add_argument("--date", default=None, help="As-of date, ISO-8601 (default: today UTC)")
    run.add_argument("--user-id", default="u_local_1")
    run.add_argument(
        "--now",
        default=None,
        help="Override 'now' for deterministic capture, ISO-8601 UTC",
    )
    run.add_argument(
        "--record-review-outcome",
        choices=("followed_and_improved", "followed_no_change", "not_followed"),
        default=None,
        help="Optionally record a synthetic review outcome immediately after scheduling",
    )
    run.add_argument(
        "--emit-json",
        action="store_true",
        help="Print the combined run artifact as JSON to stdout",
    )

    return parser.parse_args(argv)


def _coerce_dt(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def run(args: argparse.Namespace) -> dict:
    as_of = date.fromisoformat(args.date) if args.date else datetime.now(timezone.utc).date()
    now = _coerce_dt(args.now)

    pull = garmin_pull_fixture(as_of, scenario=args.scenario)
    manual = manual_readiness_fixture(as_of, scenario=args.scenario)

    evidence = clean_inputs(
        user_id=args.user_id,
        as_of_date=as_of,
        garmin_sleep=pull["sleep"],
        garmin_resting_hr_recent=pull["resting_hr"],
        garmin_hrv_recent=pull["hrv"],
        garmin_training_load_7d=pull["training_load"],
        manual_readiness=manual,
    )

    state = build_recovery_state(evidence, now=now)

    recommendation = build_training_recommendation(
        state,
        now=now,
        rhr_spike_days=evidence.resting_hr_spike_days,
        planned_session_type=evidence.planned_session_type,
        user_id=args.user_id,
    )

    base_dir = Path(args.base_dir)
    action_record = perform_writeback(recommendation, base_dir=base_dir, now=now)
    review_event = schedule_review(recommendation, base_dir=base_dir)

    review_outcome_dict = None
    if args.record_review_outcome:
        outcome = record_review_outcome(
            review_event,
            base_dir=base_dir,
            followed_recommendation=args.record_review_outcome != "not_followed",
            self_reported_improvement=(
                True if args.record_review_outcome == "followed_and_improved"
                else False if args.record_review_outcome == "followed_no_change"
                else None
            ),
            free_text=f"synthetic outcome: {args.record_review_outcome}",
            now=now,
        )
        review_outcome_dict = outcome.to_dict()

    run_artifact = {
        "run_metadata": {
            "scenario": args.scenario,
            "as_of_date": as_of.isoformat(),
            "user_id": args.user_id,
            "now": now.isoformat(),
            "base_dir": str(base_dir.resolve()),
        },
        "cleaned_evidence": _evidence_dict(evidence),
        "recovery_state": state.to_dict(),
        "training_recommendation": recommendation.to_dict(),
        "action_record": action_record.to_dict(),
        "review_event": review_event.to_dict(),
        "review_outcome": review_outcome_dict,
    }

    return run_artifact


def _evidence_dict(evidence) -> dict:
    data = asdict(evidence)
    data["as_of_date"] = evidence.as_of_date.isoformat()
    return data


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    artifact = run(args)
    if args.emit_json:
        print(json.dumps(artifact, indent=2, sort_keys=True))
    else:
        _print_human_summary(artifact)
    return 0


def _print_human_summary(artifact: dict) -> None:
    meta = artifact["run_metadata"]
    state = artifact["recovery_state"]
    rec = artifact["training_recommendation"]
    print(f"scenario:          {meta['scenario']}")
    print(f"as_of_date:        {meta['as_of_date']}")
    print(f"recovery_status:   {state['recovery_status']}")
    print(f"readiness_score:   {state['readiness_score']}")
    print(f"coverage:          {state['signal_quality']['coverage']}")
    print(f"uncertainties:     {', '.join(state['uncertainties']) or '(none)'}")
    print(f"action:            {rec['action']}")
    print(f"confidence:        {rec['confidence']}")
    print(f"policy_decisions:")
    for d in rec["policy_decisions"]:
        print(f"  - {d['rule_id']}: {d['decision']} — {d['note']}")
    print(f"review_at:         {rec['follow_up']['review_at']}")
    print(f"writeback:         {artifact['action_record']['writeback_path']}")


if __name__ == "__main__":
    sys.exit(main())
