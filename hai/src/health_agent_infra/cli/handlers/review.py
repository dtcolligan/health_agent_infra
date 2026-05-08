"""``hai review`` handler group — schedule + record + summary.

Owns: ``hai review schedule``, ``hai review record``, ``hai review summary``.

W-29.2.2 split: extracted from ``cli/__init__.py`` lines 2119-2306
(schedule + record), 2940-2972 (summary). The ``_walk_keys`` /
``_lookup`` / ``_MISSING`` / ``_review_summary_range_issues`` helpers
the boundary refresh §(c) provisionally co-located here actually belong
with ``cmd_config_validate`` + ``cmd_config_diff`` (verified at
``cli/__init__.py:4698`` + ``:4810`` + ``:4753`` — usage is config-side,
not review-side). Those move to ``cli/handlers/config_init.py`` at
W-29.2.7.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from typing import Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.review.outcomes import (
    ReLinkResolution,
    persist_review_event,
    record_review_outcome,
    resolve_review_relink,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


def cmd_review_schedule(args: argparse.Namespace) -> int:
    """Schedule a review event from a recommendation payload of any domain.

    The payload is parsed generically; ``hai propose`` / ``hai synthesize``
    is the validation boundary for recommendation shapes. Review
    scheduling trusts the already-persisted recommendation. ``domain``
    is read from the payload (falling back to ``"recovery"`` for v1 rows
    that pre-date the domain column).
    """

    from health_agent_infra.cli import (
        _coerce_dt,
        _dual_write_project,
        _emit_json,
        _load_json_arg,
    )
    from health_agent_infra.core.state import project_review_event

    data, err = _load_json_arg(
        args.recommendation_json,
        arg_name="--recommendation-json",
        command_label="hai review schedule",
    )
    if err is not None:
        return err
    follow_up = data["follow_up"]
    domain = data.get("domain", "recovery")
    event = ReviewEvent(
        review_event_id=follow_up["review_event_id"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        review_at=_coerce_dt(follow_up["review_at"]),
        review_question=follow_up["review_question"],
        domain=domain,
    )
    persist_review_event(event, base_dir=resolve_base_dir(args.base_dir))

    _dual_write_project(
        args.db_path,
        lambda conn: project_review_event(conn, event),
        "review event",
    )

    _emit_json(event.to_dict())
    return exit_codes.OK


def cmd_review_record(args: argparse.Namespace) -> int:
    from health_agent_infra.cli import (
        _coerce_dt,
        _dual_write_project,
        _emit_json,
        _load_json_arg,
    )
    from health_agent_infra.core.state import (
        open_connection,
        project_review_outcome,
        resolve_db_path,
    )

    from health_agent_infra.core.writeback.outcome import (
        ReviewOutcomeValidationError,
        validate_review_outcome_dict,
    )

    data, err = _load_json_arg(
        args.outcome_json,
        arg_name="--outcome-json",
        command_label="hai review record",
    )
    if err is not None:
        return err
    try:
        validate_review_outcome_dict(data)
    except ReviewOutcomeValidationError as exc:
        print(
            f"hai review record rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    domain = data.get("domain", "recovery")
    original_recommendation_id = data["recommendation_id"]

    # D1 §review record behavior — if the target rec belongs to a
    # superseded plan, re-link to the canonical leaf's matching-domain
    # rec before persisting. Refuse loudly when the leaf has no match;
    # orphaned outcomes are structurally disallowed. DB-absent: skip
    # resolution with a stderr note so offline review-record calls still
    # succeed; a later `hai state reproject` walks the JSONL through the
    # same writer (which, in the absence of a re-link, records the
    # outcome against the original rec).
    db_path = resolve_db_path(args.db_path)
    relink: ReLinkResolution = ReLinkResolution(
        recommendation_id=original_recommendation_id,
    )
    if db_path.exists():
        conn = open_connection(db_path)
        try:
            relink = resolve_review_relink(
                conn, recommendation_id=original_recommendation_id,
            )
        finally:
            conn.close()
        if relink.refuse:
            print(
                f"hai review record refused: {relink.refusal_reason}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        if relink.re_linked_from_recommendation_id is not None:
            print(
                f"note: {relink.re_link_note}",
                file=sys.stderr,
            )
    else:
        print(
            f"note: state DB not found at {db_path}; "
            f"skipping review-outcome re-link resolution. "
            f"JSONL audit record is durable; `hai state reproject` will "
            f"re-apply once the DB exists.",
            file=sys.stderr,
        )

    event = ReviewEvent(
        review_event_id=data["review_event_id"],
        recommendation_id=relink.recommendation_id,
        user_id=data["user_id"],
        review_at=_coerce_dt(data.get("review_at", datetime.now(timezone.utc).isoformat())),
        review_question=data.get("review_question", ""),
        domain=domain,
    )

    # M4 enrichment: CLI flags override the same key in --outcome-json
    # when both are present. Each resolution is explicit — we never
    # "merge" lists or coerce types silently.
    if args.completed is not None:
        completed_val: Optional[bool] = args.completed == "yes"
    else:
        completed_val = data.get("completed")

    intensity_delta = (
        args.intensity_delta
        if args.intensity_delta is not None
        else data.get("intensity_delta")
    )
    duration_minutes = (
        args.duration_minutes
        if args.duration_minutes is not None
        else data.get("duration_minutes")
    )
    pre_energy_score = (
        args.pre_energy
        if args.pre_energy is not None
        else data.get("pre_energy_score")
    )
    post_energy_score = (
        args.post_energy
        if args.post_energy is not None
        else data.get("post_energy_score")
    )

    if args.disagreed_firings is not None:
        disagreed_raw = args.disagreed_firings.strip()
        if disagreed_raw == "":
            # Explicit empty string = "I was asked and had no disagreements."
            # NULL in the column would mean "not asked," so preserve the
            # empty-list distinction.
            disagreed_firing_ids: Optional[list[str]] = []
        else:
            disagreed_firing_ids = [
                tok.strip() for tok in disagreed_raw.split(",") if tok.strip()
            ]
    else:
        disagreed_firing_ids = data.get("disagreed_firing_ids")

    outcome = record_review_outcome(
        event,
        base_dir=resolve_base_dir(args.base_dir),
        followed_recommendation=data["followed_recommendation"],
        self_reported_improvement=data.get("self_reported_improvement"),
        free_text=data.get("free_text"),
        now=_coerce_dt(data.get("recorded_at")),
        completed=completed_val,
        intensity_delta=intensity_delta,
        duration_minutes=duration_minutes,
        pre_energy_score=pre_energy_score,
        post_energy_score=post_energy_score,
        disagreed_firing_ids=disagreed_firing_ids,
        re_linked_from_recommendation_id=relink.re_linked_from_recommendation_id,
        re_link_note=relink.re_link_note,
    )

    _dual_write_project(
        args.db_path,
        lambda conn: project_review_outcome(conn, outcome),
        "review outcome",
    )

    _emit_json(outcome.to_dict())
    return exit_codes.OK


def cmd_review_summary(args: argparse.Namespace) -> int:
    from health_agent_infra.cli import _coerce_dt, _emit_json

    outcomes_path = resolve_base_dir(args.base_dir) / "review_outcomes.jsonl"
    domain_filter = getattr(args, "domain", None)
    if not outcomes_path.exists():
        _emit_json(summarize_review_history([], domain=domain_filter))
        return exit_codes.OK
    outcomes: list[ReviewOutcome] = []
    for line in outcomes_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        if args.user_id and d.get("user_id") != args.user_id:
            continue
        outcomes.append(ReviewOutcome(
            review_event_id=d["review_event_id"],
            recommendation_id=d["recommendation_id"],
            user_id=d["user_id"],
            recorded_at=_coerce_dt(d["recorded_at"]),
            followed_recommendation=d["followed_recommendation"],
            self_reported_improvement=d.get("self_reported_improvement"),
            free_text=d.get("free_text"),
            domain=d.get("domain", "recovery"),
            # M4 enrichment — pre-M4 JSONL rows don't carry these keys,
            # .get returns None, dataclass defaults align.
            completed=d.get("completed"),
            intensity_delta=d.get("intensity_delta"),
            duration_minutes=d.get("duration_minutes"),
            pre_energy_score=d.get("pre_energy_score"),
            post_energy_score=d.get("post_energy_score"),
            disagreed_firing_ids=d.get("disagreed_firing_ids"),
        ))
    _emit_json(summarize_review_history(outcomes, domain=domain_filter))
    return exit_codes.OK


def cmd_review_weekly(args: argparse.Namespace) -> int:
    """``hai review weekly`` — aggregate the past week's plan evidence
    and render either markdown (default) or JSON output.

    Per PLAN §2.D acceptance #1-#9: deterministic byte-stable output
    over fixture-week corpora; partial-week abstain branch when fewer
    than ``coverage_threshold`` days of canonical plans exist;
    supersession reconciliation surfaces both rows on multi-canonical
    days; data-quality rollup distinguishes ``stale_pull`` vs
    ``retrospective_manual``; ``--include-history`` flag (JSON-only)
    flips between canonical-latest and append-only history view.
    """

    from health_agent_infra.core.config import load_thresholds
    from health_agent_infra.core.review.prose_builder import (
        build_weekly_prose,
        emit_weekly_claim_cards,
    )
    from health_agent_infra.core.review.render import (
        render_json,
        render_markdown,
    )
    from health_agent_infra.core.review.weekly import (
        compute_data_quality_rollup,
        evaluate_weekly_coverage,
        iso_week_dates,
        load_weekly_aggregation,
    )
    from health_agent_infra.core.state import (
        open_connection,
        resolve_db_path,
    )

    iso_week = args.week
    # Validate the week shape eagerly so the user gets a clear
    # USER_INPUT exit rather than a stack trace on bad input.
    try:
        iso_week_dates(iso_week)
    except ValueError as exc:
        print(
            f"hai review weekly rejected: --week must be 'YYYY-Www' "
            f"(e.g. '2026-W18'); got {iso_week!r} ({exc})",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    if (
        getattr(args, "include_history", False)
        and getattr(args, "json", False) is False
    ):
        print(
            "hai review weekly rejected: --include-history is only "
            "valid with --json (markdown shows canonical-latest only).",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    user_id = getattr(args, "user_id", None) or "u_local_1"

    thresholds = load_thresholds()
    weekly_block = thresholds.get("policy", {}).get("review_weekly", {})
    coverage_threshold_days = (
        args.coverage_threshold
        if args.coverage_threshold is not None
        else weekly_block.get("coverage_threshold_days", 5)
    )
    stale_pull_hours = weekly_block.get("data_quality_stale_pull_hours", 48)

    db_path = resolve_db_path(getattr(args, "db_path", None))
    if not db_path.exists():
        # No state DB → equivalent to an empty week (zero plans). The
        # abstain branch fires; the user gets the standard guidance.
        print(
            f"hai review weekly: no state DB at {db_path} — emitting "
            f"abstain branch as if the week were empty.",
            file=sys.stderr,
        )

    conn = open_connection(db_path) if db_path.exists() else None
    try:
        if conn is not None:
            aggregation = load_weekly_aggregation(
                conn, iso_week=iso_week, user_id=user_id,
            )
        else:
            from health_agent_infra.core.review.weekly import (
                WeeklyAggregation,
            )
            aggregation = WeeklyAggregation(
                iso_week=iso_week, user_id=user_id,
                week_dates=[
                    d.isoformat() for d in iso_week_dates(iso_week)
                ],
                canonical_plans=[], recommendations=[],
                x_rule_firings=[], review_outcomes=[],
                evidence_cards=[], accepted_state_rows=[],
                data_quality_rows=[], sync_runs=[], runtime_events=[],
                intent_rows=[], target_rows=[],
            )

        coverage = evaluate_weekly_coverage(
            aggregation, coverage_threshold_days=coverage_threshold_days,
        )
        rollup = compute_data_quality_rollup(
            aggregation.sync_runs, stale_pull_hours=stale_pull_hours,
        )
        if conn is not None:
            bundle = build_weekly_prose(
                conn, aggregation, coverage, rollup,
            )
        else:
            bundle = build_weekly_prose(
                _NullConn(),  # type: ignore[arg-type]  # duck-typed Connection.execute for abstain path
                aggregation, coverage, rollup,
            )

        # v0.2.0 W58D — deterministic factuality gate. Runs against
        # every quantitative + comparative atom in non-abstain
        # prose. ``--bypass-factuality-gate`` skips the gate (logs
        # WARN; developer-only override). Abstain branch runs no
        # claim cards and no gate (validation is structurally simpler
        # via deterministic substitution per F-PHASE0-02 + F-PLAN-03).
        bypass = getattr(args, "bypass_factuality_gate", False)
        if (
            conn is not None
            and coverage.weekly_status == "ok"
            and not bypass
        ):
            from health_agent_infra.core.eval import (
                ClaimGateInput,
                run_factuality_gate,
            )

            claims = []
            for section in bundle.sections:
                for atom in section.atoms:
                    if atom.atom_type not in (
                        "quantitative", "comparative",
                    ):
                        continue
                    claims.append(ClaimGateInput(
                        atom_text=atom.atom_text,
                        atom_type=atom.atom_type,
                        locator_set=list(atom.locator_set),
                        audit_refs=dict(atom.audit_refs),
                        user_id=user_id,
                        claim_id=atom.atom_id,
                    ))
            outcome = run_factuality_gate(conn, claims)
            if not outcome.all_passed:
                first = outcome.first_block()
                assert first is not None, (
                    "all_passed=False implies first_block() returns a "
                    "ClaimGateResult"
                )
                print(
                    f"hai review weekly: factuality gate BLOCKED — "
                    f"atom {first.claim_id!r} failed to resolve "
                    f"({first.block_reason.value if first.block_reason else 'unknown'}): "
                    f"{first.block_detail}",
                    file=sys.stderr,
                )
                print(
                    f"  ({outcome.blocked} of "
                    f"{outcome.total - outcome.skipped} validated atoms "
                    f"blocked; rerun after data is corrected, or pass "
                    f"--bypass-factuality-gate for a developer-only "
                    f"render).",
                    file=sys.stderr,
                )
                return exit_codes.INTERNAL
        elif bypass:
            print(
                "hai review weekly: WARN — --bypass-factuality-gate "
                "skipped W58D validation. Output may cite stale or "
                "absent source state.",
                file=sys.stderr,
            )

        # Emit weekly_claim_card rows for every quantitative +
        # comparative atom in non-abstain prose (PLAN §2.D acceptance
        # #6). Append-only per W-EVCARD-WEEKLY: re-running for the
        # same week with corrected data appends new rows and the
        # canonical-latest view returns the newest set.
        if (
            conn is not None
            and coverage.weekly_status == "ok"
        ):
            emit_weekly_claim_cards(conn, bundle)

        if getattr(args, "json", False):
            print(render_json(
                bundle,
                conn=conn,
                include_history=getattr(args, "include_history", False),
            ), end="")
        else:
            print(render_markdown(bundle), end="")
    finally:
        if conn is not None:
            conn.close()

    return exit_codes.OK


class _NullConn:
    """Minimal sqlite3-shaped stub for the no-state-DB abstain path.

    The prose builder calls ``conn.execute(...)`` once for the
    primary_goal lookup; we simulate "no rows" by raising
    ``OperationalError`` which the loader catches.
    """

    def execute(self, *args, **kwargs):
        import sqlite3
        raise sqlite3.OperationalError("no state DB available")
