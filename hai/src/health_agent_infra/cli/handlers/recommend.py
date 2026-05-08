"""``hai recommend`` group — propose + synthesize + daily orchestration.

Owns: ``hai propose``, ``hai synthesize``, ``hai daily``. Plus the
``_read_proposal_projection_meta`` helper, the daily-orchestration
helpers ``_parse_daily_domains`` / ``_daily_pull_and_project`` /
``_schedule_reviews_for_daily_plan``, and the large ``_run_daily``
orchestration body (~340 LOC) that ``cmd_daily`` delegates to.

W-29.2.11 split: extracted from cli/__init__.py 2 ranges
(271-644 cmd_propose + cmd_synthesize, 822-1424 _parse/_daily_pull/
_schedule + cmd_daily + _run_daily). Largest of the W-29.2 splits.

Test-infra note: tests that monkeypatch ``_daily_pull_and_project``
or ``_run_daily`` must target ``cli.handlers.recommend.X`` post-W-29.2.11.
``_build_intervals_icu_adapter`` (lives in pull_clean) is referenced by
``_daily_pull_and_project``; tests that patch the cli re-export still
work because cli/__init__.py imports both handlers via the W-29.2.9
re-export block before this module loads.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import uuid
from contextlib import contextmanager
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Literal, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.pull.garmin_live import GarminLiveError
from health_agent_infra.core.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    default_manual_readiness,
)
from health_agent_infra.core.pull.intervals_icu import IntervalsIcuError
from health_agent_infra.core.review.outcomes import (
    persist_review_event,
)
from health_agent_infra.core.schemas import ReviewEvent

# Cli-private helpers defined before line 267.
from health_agent_infra.cli import (  # noqa: E402
    _DailyPullRefusal,
    _PROJECTION_RESULT_FAILED,
    _PROJECTION_RESULT_OK,
    _PROJECTION_RESULT_SKIPPED_DB_ABSENT,
    _autoread_manual_readiness,
    _build_intervals_icu_adapter,
    _build_live_adapter,
    _close_sync_row_failed,
    _close_sync_row_ok,
    _coerce_date,
    _coerce_dt,
    _dual_write_project,
    _emit_json,
    _enrich_raw_row_with_activity_aggregate,
    _evidence_hash,
    _f_pv14_csv_canonical_guard,
    _intervals_icu_configured,
    _load_json_arg,
    _open_sync_row,
    _project_clean_into_state,
    _resolve_pull_source,
    _sync_if_db,
)
# Direct imports for symbols whose re-export blocks sit LATER in
# cli/__init__.py than this W-29.2.11 import (partial-module-load avoidance).
from health_agent_infra.cli.handlers.inspect import _build_daily_explain_block  # noqa: E402
from health_agent_infra.cli.handlers.tools import _DAILY_SUPPORTED_DOMAINS  # noqa: E402


def cmd_propose(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import (
        ProposalReplaceRequired,
        open_connection,
        project_proposal,
        resolve_db_path,
    )
    from health_agent_infra.core.writeback.proposal import (
        ProposalValidationError,
        perform_proposal_writeback,
        validate_proposal_dict,
    )

    data, err = _load_json_arg(
        args.proposal_json,
        arg_name="--proposal-json",
        command_label="hai propose",
    )
    if err is not None:
        return err
    try:
        validate_proposal_dict(data, expected_domain=args.domain)
    except ProposalValidationError as exc:
        print(
            f"propose rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    except (ValueError, KeyError) as exc:
        print(f"propose rejected: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    # Pre-flight the --replace contract against the DB before any
    # append to JSONL. A rejected revise must not leave a JSONL line
    # that outlives the rejected DB transaction. If the DB is absent,
    # there is no canonical leaf to revise and we fall through to the
    # JSONL-only path (best-effort DB is preserved from pre-D1).
    db_path = resolve_db_path(args.db_path)
    if db_path.exists():
        conn = open_connection(db_path)
        try:
            leaf = conn.execute(
                "SELECT proposal_id, revision FROM proposal_log "
                "WHERE for_date = ? AND user_id = ? AND domain = ? "
                "AND superseded_by_proposal_id IS NULL",
                (data["for_date"], data["user_id"], data["domain"]),
            ).fetchone()
            if leaf is not None and not args.replace:
                print(
                    f"propose rejected: existing canonical proposal "
                    f"{leaf['proposal_id']!r} (revision {leaf['revision']}) "
                    f"for ({data['for_date']}, {data['user_id']}, "
                    f"{data['domain']}); pass --replace to revise.",
                    file=sys.stderr,
                )
                return exit_codes.USER_INPUT
        finally:
            conn.close()

    # JSONL audit first (per the pre-D1 contract — append-only audit is
    # the durability boundary; DB is a queryable projection).
    record = perform_proposal_writeback(data, base_dir=resolve_base_dir(args.base_dir))

    # DB projection. v0.1.6 (W15 / Codex C2): cmd_propose handles its
    # own projection inline rather than routing through
    # `_dual_write_project`, because the swallowing pattern in that
    # helper would let `ProposalReplaceRequired` (a thin race window
    # past the pre-flight check) AND any other unexpected projection
    # failure fall through silently. With the inline handling here:
    #   - DB-absent → JSONL is durable; print the legacy stderr note
    #     and return OK with a `db_projection_skipped` flag in the
    #     stdout payload.
    #   - ProposalReplaceRequired → fatal USER_INPUT exit (rare race).
    #   - Any other projection exception → INTERNAL exit with a clear
    #     "JSONL written, DB out of sync — run `hai state reproject`"
    #     message. The audit chain has not silently forked.
    db_projection_status: str
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to "
            f"enable DB dual-write.",
            file=sys.stderr,
        )
        db_projection_status = "skipped_db_absent"
    else:
        conn = open_connection(db_path)
        try:
            try:
                project_proposal(conn, data, replace=args.replace)
                db_projection_status = "ok"
            except ProposalReplaceRequired as exc:
                print(
                    f"propose rejected: projection raised "
                    f"ProposalReplaceRequired (concurrent writer race "
                    f"past the pre-flight canonical-leaf check): {exc}. "
                    f"JSONL audit record IS durable but DB is out of "
                    f"sync; rerun with --replace or run "
                    f"`hai state reproject` to reconcile.",
                    file=sys.stderr,
                )
                return exit_codes.USER_INPUT
            except Exception as exc:  # noqa: BLE001
                print(
                    f"propose: DB projection FAILED ({type(exc).__name__}: "
                    f"{exc}). JSONL audit record IS durable at "
                    f"{record.writeback_path} but the SQLite projection "
                    f"is now out of sync. Run `hai state reproject` to "
                    f"replay the JSONL into the DB.",
                    file=sys.stderr,
                )
                return exit_codes.INTERNAL
        finally:
            conn.close()

    # Post-write DB read for projection metadata (proposal_id as landed,
    # revision, superseded_by_proposal_id). Codex r2/r3 pushback: the
    # agent contract documents these fields on the stdout payload, and
    # under D1 revision semantics the DB-landed proposal_id may differ
    # from the input payload's id (project_proposal renames to
    # `prop_<date>_<user>_<domain>_<rev:02d>` on revision). The lookup
    # resolves the canonical leaf for (for_date, user_id, domain) so the
    # stdout echoes what ACTUALLY landed, not the pre-rename input.
    projection_meta = _read_proposal_projection_meta(
        args.db_path,
        for_date=data["for_date"],
        user_id=data["user_id"],
        domain=data["domain"],
        fallback_proposal_id=data["proposal_id"],
    )
    payload = record.to_dict()
    payload["for_date"] = data["for_date"]
    payload["user_id"] = data["user_id"]
    # v0.1.6 (W15): db_projection_status surfaces the dual-write
    # outcome on every successful exit. Agents can pattern-match on
    # this without reparsing stderr: "ok" means JSONL + SQLite agree;
    # "skipped_db_absent" means JSONL is durable and a future
    # `hai state reproject` will reconcile.
    payload["db_projection_status"] = db_projection_status
    # proposal_id echoes the DB leaf's id (post-rename on revision). On
    # the DB-absent path, falls back to the input payload id (legacy
    # single-source-of-truth was the JSONL's id).
    if projection_meta.get("proposal_id") is not None:
        payload["proposal_id"] = projection_meta["proposal_id"]
        payload["idempotency_key"] = projection_meta["proposal_id"]
    payload["revision"] = projection_meta.get("revision")
    payload["superseded_by_proposal_id"] = projection_meta.get(
        "superseded_by_proposal_id",
    )
    _emit_json(payload)
    return exit_codes.OK


def _read_proposal_projection_meta(
    db_path_arg,
    *,
    for_date: str,
    user_id: str,
    domain: str,
    fallback_proposal_id: str,
) -> dict[str, Any]:
    """Return the canonical-leaf projection metadata for a just-written
    proposal, or an empty dict when the DB is absent.

    Best-effort: DB-absent + projection failures return ``{}`` so the
    ``hai propose`` command still emits a well-formed stdout payload
    (the revision/superseded-by keys drop to None). The DB is the
    source of truth when present; the JSONL audit has the proposal_id
    but not the post-projection metadata.

    Under D1's revision semantics, the ``--replace`` path auto-generates
    a new proposal_id (``prop_..._<rev:02d>``), so the id we were
    passed in ``data`` may no longer be the live row's id. Resolution
    order:

      1. Canonical leaf for ``(for_date, user_id, domain)`` — the
         authoritative shape. Picks up both fresh inserts (rev=1) and
         post-replace rows (rev≥2 with the runtime-assigned id).
      2. Direct lookup on ``fallback_proposal_id`` — covers any edge
         case where the canonical-leaf query returns no row but the
         input id does (shouldn't happen by construction; kept as a
         defensive fallback).
      3. Empty dict — DB absent or both lookups miss.
    """

    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return {}
    try:
        conn = open_connection(db_path)
    except Exception:
        return {}
    try:
        leaf = conn.execute(
            "SELECT proposal_id, revision, superseded_by_proposal_id "
            "FROM proposal_log "
            "WHERE for_date = ? AND user_id = ? AND domain = ? "
            "  AND superseded_by_proposal_id IS NULL",
            (for_date, user_id, domain),
        ).fetchone()
        if leaf is not None:
            return {
                "proposal_id": leaf["proposal_id"],
                "revision": leaf["revision"],
                "superseded_by_proposal_id": leaf["superseded_by_proposal_id"],
            }
        row = conn.execute(
            "SELECT proposal_id, revision, superseded_by_proposal_id "
            "FROM proposal_log WHERE proposal_id = ?",
            (fallback_proposal_id,),
        ).fetchone()
        if row is not None:
            return {
                "proposal_id": row["proposal_id"],
                "revision": row["revision"],
                "superseded_by_proposal_id": row["superseded_by_proposal_id"],
            }
        return {}
    except Exception:
        return {}
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# hai synthesize — atomic Phase A + Phase B plan commit
# ---------------------------------------------------------------------------

def cmd_synthesize(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import open_connection, resolve_db_path
    from health_agent_infra.core.synthesis import (
        SynthesisError,
        build_synthesis_bundle,
        run_synthesis,
    )
    from health_agent_infra.core.synthesis_policy import XRuleWriteSurfaceViolation

    for_date = _coerce_date(args.as_of)
    user_id = args.user_id

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai synthesize requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # --bundle-only is the skill seam: read-only emission of
    # (snapshot, proposals, phase_a_firings) so the daily-plan-synthesis
    # skill can compose a rationale overlay and return via `hai synthesize
    # --drafts-json`. It never mutates state.
    if args.bundle_only:
        if args.drafts_json or args.supersede:
            print(
                "hai synthesize rejected: --bundle-only is read-only and "
                "cannot be combined with --drafts-json or --supersede.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        # v0.1.6 (W13 / B4): bundle-only is the post-proposal skill
        # seam, not a pre-proposal inspection surface. Without
        # proposals in proposal_log there's nothing for the synthesis
        # skill to overlay rationale onto, and emitting an empty
        # bundle would silently bypass the same "no proposals"
        # contract `hai synthesize` enforces on the commit path.
        # Refuse explicitly so the agent gets a governed USER_INPUT
        # instead of a misleading empty payload.
        from health_agent_infra.core.state import (
            read_proposals_for_plan_key,
        )
        conn = open_connection(db_path)
        try:
            existing = read_proposals_for_plan_key(
                conn, for_date=for_date.isoformat(), user_id=user_id,
            )
            if not existing:
                print(
                    f"hai synthesize rejected: --bundle-only requires "
                    f"at least one DomainProposal in proposal_log for "
                    f"({for_date}, {user_id}), but none were found. "
                    f"Bundle-only is the post-proposal skill overlay "
                    f"seam — post proposals via `hai propose --domain "
                    f"<d>` first, then re-run.",
                    file=sys.stderr,
                )
                return exit_codes.USER_INPUT
            bundle = build_synthesis_bundle(
                conn, for_date=for_date, user_id=user_id,
            )
        finally:
            conn.close()
        _emit_json(bundle)
        return exit_codes.OK

    skill_drafts: Optional[list[dict]] = None
    if args.drafts_json:
        try:
            skill_drafts = json.loads(
                Path(args.drafts_json).read_text(encoding="utf-8"),
            )
        except (json.JSONDecodeError, OSError) as exc:
            print(
                f"hai synthesize rejected: could not read drafts JSON "
                f"({args.drafts_json}): {exc}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        if not isinstance(skill_drafts, list):
            print(
                f"hai synthesize rejected: drafts JSON must be a JSON array; "
                f"got {type(skill_drafts).__name__}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    # v0.1.9 B4: enforce expected-domain completeness on direct
    # synthesize. ``--domains`` defaults to the v1 six-domain set; pass
    # ``--domains ''`` to opt out (matches pre-v0.1.9 permissive
    # behavior — should be rare).
    from health_agent_infra.core.synthesis import V1_EXPECTED_DOMAINS
    domains_arg = getattr(args, "domains", None)
    if domains_arg is None:
        expected_domains = V1_EXPECTED_DOMAINS
    elif domains_arg == "":
        expected_domains = None
    else:
        names = [n.strip() for n in domains_arg.split(",") if n.strip()]
        unknown = [n for n in names if n not in V1_EXPECTED_DOMAINS]
        if unknown:
            print(
                f"hai synthesize rejected: --domains contains unknown "
                f"domain(s) {unknown}. Allowed: {sorted(V1_EXPECTED_DOMAINS)}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        expected_domains = frozenset(names)

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=for_date,
            user_id=user_id,
            skill_drafts=skill_drafts,
            agent_version=args.agent_version,
            supersede=args.supersede,
            expected_domains=expected_domains,
        )
    except SynthesisError as exc:
        print(f"hai synthesize rejected: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except XRuleWriteSurfaceViolation as exc:
        # A write-surface violation means a Phase B rule tried to touch a
        # field the guard disallows — a bug in the rule implementation,
        # not anything the caller did. INTERNAL, not USER_INPUT.
        print(
            f"hai synthesize rejected: write_surface_violation: {exc}",
            file=sys.stderr,
        )
        return exit_codes.INTERNAL
    finally:
        conn.close()

    _emit_json(result.to_dict())
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai explain — read-only audit-chain reconstruction (Phase C)
# ---------------------------------------------------------------------------


def _parse_daily_domains(domains_arg: Optional[str]) -> tuple[frozenset[str], Optional[str]]:
    """Parse ``--domains d1,d2,...`` → (valid_set, error_message).

    Empty / missing input resolves to the full v1 domain set so the default
    run covers all six. Unknown tokens return an error message for the
    caller to surface on stderr; no exception so cmd_daily can emit its own
    structured failure report.
    """

    if not domains_arg:
        return frozenset(_DAILY_SUPPORTED_DOMAINS), None
    raw = [v.strip() for v in domains_arg.split(",") if v.strip()]
    if not raw:
        return frozenset(), "empty --domains value"
    unknown = sorted(set(raw) - _DAILY_SUPPORTED_DOMAINS)
    if unknown:
        return frozenset(), (
            f"unsupported --domains value(s): {unknown}. "
            f"Valid: {sorted(_DAILY_SUPPORTED_DOMAINS)}"
        )
    return frozenset(raw), None


def _daily_pull_and_project(
    args: argparse.Namespace,
    *,
    as_of: date,
    user_id: str,
    db_path: Path,
) -> tuple[str, bool, Optional[dict]]:
    """Run the pull + state projection path ``hai pull`` + ``hai clean`` run.

    Reuses the adapters + ``_project_clean_into_state`` already shipped so
    ``hai daily`` does not duplicate acquisition or cleaning logic. No
    stdout emission (the outer command emits a single orchestration
    report). Returns ``(source_name, projected_raw_daily, evidence_bundle)``
    where ``evidence_bundle`` is the ``{cleaned_evidence, raw_summary}``
    dict — exposed so the orchestrator can feed it into
    ``build_snapshot(evidence_bundle=...)`` and compute intake gaps
    without a duplicate clean pass. Raises :class:`GarminLiveError` on
    failure so the caller can classify.
    """

    source = _resolve_pull_source(args)

    # F-PV14-01 default-deny (F-IR-02 round-1 IR fix): same guard
    # `cmd_pull` enforces. The daily orchestrator is the path most
    # likely to be used in a foreign-user gate, so it must NOT silently
    # bypass the canonical-DB protection. Refuse before any adapter
    # construction or sync-row write.
    refused = _f_pv14_csv_canonical_guard(
        args, source=source, command_label="hai daily",
    )
    if refused is not None:
        # Outer caller (cmd_daily) treats USER_INPUT raised this way as
        # a clean refusal; bubble through the existing exit-code path.
        raise _DailyPullRefusal(refused)

    # F-A-03 fix per W-H1 — see annotated comment in cmd_pull.
    adapter: Any
    if source == "csv":
        adapter = GarminRecoveryReadinessAdapter()
    elif source == "garmin_live":
        adapter = _build_live_adapter(args)
    else:  # intervals_icu
        adapter = _build_intervals_icu_adapter(args)

    # v0.1.9 B5: hai daily now writes to sync_run_log via the same path
    # `hai pull` uses. Pre-v0.1.9 daily called the adapter directly,
    # bypassing freshness telemetry — so `hai stats --funnel` and the
    # data-quality projector saw inconsistent provenance depending on
    # whether the user ran `hai pull` followed by `hai daily`, or just
    # `hai daily` alone.
    mode = "csv" if source == "csv" else "live"
    source_label = {
        "csv": adapter.source_name,
        "garmin_live": "garmin_live",
        "intervals_icu": "intervals_icu",
    }[source]
    sync_id = _open_sync_row(
        getattr(args, "db_path", None),
        source=source_label,
        user_id=user_id,
        mode=mode,
        for_date=as_of,
    )

    try:
        pull = adapter.load(as_of)
    except Exception as exc:
        _close_sync_row_failed(getattr(args, "db_path", None), sync_id, exc)
        raise

    raw_row = pull.get("raw_daily_row")
    activities = pull.get("activities") or []
    if raw_row is not None and activities:
        _enrich_raw_row_with_activity_aggregate(
            raw_row=raw_row,
            activities=[
                a for a in activities
                if a.get("as_of_date") == as_of.isoformat()
            ],
        )
    if raw_row is not None:
        # v0.1.9 B5: inspect projection result and bubble failure up.
        # Pre-v0.1.9 ``hai daily`` swallowed projection failures as
        # warnings and kept planning over potentially stale state.
        projection_result = _project_clean_into_state(
            db_path,
            as_of_date=as_of,
            user_id=user_id,
            raw_row=raw_row,
            activities=activities,
        )
        if projection_result["status"] == _PROJECTION_RESULT_FAILED:
            _close_sync_row_failed(
                getattr(args, "db_path", None),
                sync_id,
                RuntimeError(projection_result["error"] or "projection failed"),
            )
            raise RuntimeError(
                f"clean projection into state DB failed: "
                f"{projection_result['error_type']}: "
                f"{projection_result['error']}. `hai daily` cannot plan "
                f"over stale or absent accepted-state rows; either "
                f"resolve the DB error and rerun, or invoke `hai pull` "
                f"+ `hai clean` manually to surface the failure."
            )

    # Close the sync row on success. Counts mirror what cmd_pull records:
    # raw rows pulled and accepted into state; duplicates skipped. Preserve
    # adapter partial-pull telemetry as cmd_pull does, otherwise a daily run
    # with intervals.icu wellness present but activities unavailable would look
    # fully fresh in sync_run_log.
    rows_pulled = 1 if raw_row is not None else 0
    rows_accepted = 1 if raw_row is not None else 0
    partial = getattr(adapter, "last_pull_partial", False)
    sync_status_daily: Literal["ok", "partial", "failed"] = (
        "partial" if partial else "ok"
    )
    _close_sync_row_ok(
        getattr(args, "db_path", None),
        sync_id,
        rows_pulled=rows_pulled,
        rows_accepted=rows_accepted,
        duplicates_skipped=0,
        status=sync_status_daily,
    )

    evidence_bundle: Optional[dict] = None
    manual = None
    if raw_row is not None:
        # Autoread readiness so the cleaned evidence picks up today's
        # manual checkin when one exists (matches cmd_pull's behaviour).
        manual = _autoread_manual_readiness(
            getattr(args, "db_path", None), user_id=user_id, as_of=as_of,
        )
        evidence = clean_inputs(
            user_id=user_id,
            as_of_date=as_of,
            garmin_sleep=pull.get("sleep"),
            garmin_resting_hr_recent=pull.get("resting_hr", []),
            garmin_hrv_recent=pull.get("hrv", []),
            garmin_training_load_7d=pull.get("training_load", []),
            manual_readiness=manual,
        )
        summary = build_raw_summary(
            user_id=user_id,
            as_of_date=as_of,
            garmin_sleep=pull.get("sleep"),
            garmin_resting_hr_recent=pull.get("resting_hr", []),
            garmin_hrv_recent=pull.get("hrv", []),
            garmin_training_load_7d=pull.get("training_load", []),
            raw_daily_row=raw_row,
        )
        evidence_bundle = {
            "cleaned_evidence": evidence.to_dict(),
            "raw_summary": summary.to_dict(),
        }

    return adapter.source_name, raw_row is not None, evidence_bundle


def _schedule_reviews_for_daily_plan(
    conn: sqlite3.Connection,
    *,
    daily_plan_id: str,
    base_dir: Path,
) -> list[str]:
    """Schedule a ``ReviewEvent`` for each recommendation in ``daily_plan``.

    Reads the recommendation payloads the synthesis transaction just
    committed, rebuilds a ``ReviewEvent`` from each payload's ``follow_up``
    block, appends JSONL, and projects into ``review_event``. Both writes
    are idempotent on ``review_event_id`` so reruns of ``hai daily`` stay
    safe. Returns the list of scheduled ids in stable order.

    DB projection is best-effort: a failure becomes a stderr warning and
    the JSONL audit line is kept — parallel to how ``hai review schedule``
    uses ``_dual_write_project``.
    """

    from health_agent_infra.core.state import project_review_event

    rows = conn.execute(
        "SELECT payload_json FROM recommendation_log "
        "WHERE json_extract(payload_json, '$.daily_plan_id') = ? "
        "ORDER BY recommendation_id",
        (daily_plan_id,),
    ).fetchall()

    scheduled: list[str] = []
    for row in rows:
        payload = json.loads(row["payload_json"])
        follow_up = payload["follow_up"]
        event = ReviewEvent(
            review_event_id=follow_up["review_event_id"],
            recommendation_id=payload["recommendation_id"],
            user_id=payload["user_id"],
            review_at=_coerce_dt(follow_up["review_at"]),
            review_question=follow_up["review_question"],
            domain=payload.get("domain", "recovery"),
        )
        persist_review_event(event, base_dir=base_dir)
        try:
            project_review_event(conn, event)
        except Exception as exc:  # noqa: BLE001
            print(
                f"warning: review event projection failed for "
                f"{event.review_event_id}: {exc}. JSONL record is durable.",
                file=sys.stderr,
            )
        scheduled.append(event.review_event_id)
    return scheduled


def cmd_daily(args: argparse.Namespace) -> int:
    """Thin wrapper around :func:`_run_daily` that records a runtime event.

    Every invocation writes one row to ``runtime_event_log`` (migration 012)
    with started_at, exit_code, duration_ms, and status. The wrapper is
    best-effort: a missing state DB silently skips logging rather than
    blocking the run. The orchestration logic lives unchanged in
    :func:`_run_daily`.
    """

    from health_agent_infra.core.state import resolve_db_path, runtime_event

    db_path_resolved = resolve_db_path(args.db_path)
    user_id = getattr(args, "user_id", "u_local_1")
    with runtime_event(
        db_path_resolved, command="daily", user_id=user_id,
    ) as evt:
        rc = _run_daily(args, runtime_event_dict=evt)
        evt["exit_code"] = rc
    return rc


def _run_daily(
    args: argparse.Namespace,
    *,
    runtime_event_dict: Optional[dict] = None,
) -> int:
    """Orchestrate the morning sequence over the existing runtime surfaces.

    Stages: pull → clean → snapshot → proposal-gate → synthesize →
    schedule reviews. The proposal gate is the agent seam: skills are
    judgment-only, so when ``proposal_log`` has no rows for
    ``(for_date, user_id)`` the command exits 0 with
    ``overall_status=awaiting_proposals`` rather than faking proposals or
    escalating to a hard error. After the agent posts proposals via
    ``hai propose``, rerunning ``hai daily`` completes the remaining
    stages (synthesize is idempotent on the canonical key; review
    scheduling is idempotent on ``review_event_id``).
    """

    from health_agent_infra.core.state import (
        open_connection,
        read_proposals_for_plan_key,
        resolve_db_path,
    )
    from health_agent_infra.core.state.snapshot import build_snapshot
    from health_agent_infra.core.synthesis import (
        SynthesisError,
        run_synthesis,
    )
    from health_agent_infra.core.synthesis_policy import (
        XRuleWriteSurfaceViolation,
    )

    expected_domains, domains_err = _parse_daily_domains(args.domains)
    if domains_err is not None:
        print(f"hai daily rejected: {domains_err}", file=sys.stderr)
        return exit_codes.USER_INPUT

    as_of = _coerce_date(args.as_of)
    user_id = args.user_id
    base_dir = resolve_base_dir(args.base_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai daily requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # v0.1.13 W-FBC-2 closure: --re-propose-all is now a runtime signal
    # to the synthesis-side carryover-uncertainty detector. Pre-v0.1.13
    # the flag was report-surface-only (v0.1.12 W-FBC partial closure);
    # v0.1.13 wires it through ``run_synthesis(re_propose_all=...)``,
    # which emits a per-domain
    # ``<domain>_proposal_carryover_under_re_propose_all`` token on
    # any recommendation whose proposal envelope is older than
    # ``now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD`` (default 60s).
    re_propose_all_requested = bool(getattr(args, "re_propose_all", False))
    report: dict[str, Any] = {
        "as_of_date": as_of.isoformat(),
        "user_id": user_id,
        "base_dir": str(base_dir),
        "db_path": str(db_path),
        "expected_domains": sorted(expected_domains),
        "re_propose_all_requested": re_propose_all_requested,
        "stages": {},
    }

    # Stage 1 + 2: pull + clean (skippable for offline / already-populated runs)
    evidence_bundle: Optional[dict] = None
    if args.skip_pull:
        report["stages"]["pull"] = {"status": "skipped"}
        report["stages"]["clean"] = {"status": "skipped"}
    else:
        try:
            source_name, projected, evidence_bundle = _daily_pull_and_project(
                args, as_of=as_of, user_id=user_id, db_path=db_path,
            )
        except _DailyPullRefusal as refusal:
            # F-PV14-01 (F-IR-02 round-1 IR fix): the daily orchestrator
            # refuses CSV→canonical writes by the same rule cmd_pull
            # uses. Surface the refusal as a structured stage failure
            # so the report shape stays inspectable.
            report["stages"]["pull"] = {
                "status": "refused",
                "reason": (
                    "F-PV14-01: --source csv against canonical state DB "
                    "without --allow-fixture-into-real-state, hai demo, "
                    "or non-canonical --db-path / HAI_STATE_DB"
                ),
            }
            report["overall_status"] = "refused"
            _emit_json(report)
            return refusal.exit_code
        except (GarminLiveError, IntervalsIcuError) as exc:
            report["stages"]["pull"] = {"status": "failed", "error": str(exc)}
            report["overall_status"] = "failed"
            _emit_json(report)
            return exit_codes.USER_INPUT
        except RuntimeError as exc:
            # v0.1.9 B5: clean projection failure now bubbles up as a
            # RuntimeError from ``_daily_pull_and_project``. ``hai daily``
            # must not plan over stale or absent accepted-state rows.
            report["stages"]["pull"] = {"status": "ran"}
            report["stages"]["clean"] = {
                "status": "failed", "error": str(exc),
            }
            report["overall_status"] = "failed"
            _emit_json(report)
            return exit_codes.INTERNAL
        report["stages"]["pull"] = {"status": "ran", "source": source_name}
        report["stages"]["clean"] = {
            "status": "ran" if projected else "no_raw_daily_row",
        }

    conn = open_connection(db_path)
    try:
        # Stage 3: snapshot — the cross-domain bundle the agent reads.
        # Pass the evidence_bundle when available so per-domain classified_state
        # + policy_result land in the snapshot — which is what the intake-gaps
        # stage reads to surface user-closeable prompts.
        snapshot = build_snapshot(
            conn, as_of_date=as_of, user_id=user_id, lookback_days=14,
            evidence_bundle=evidence_bundle,
        )
        # v0.1.8 W43 / Codex P2-1 fix: populate the snapshot stage
        # block with the per-domain bands + missingness +
        # review_summary tokens so the `--auto --explain` block has
        # the W48 signal it was supposed to surface. Reads
        # already-built snapshot data; no recomputation.
        _domains_present = sorted(
            k for k in snapshot.keys() if k in _DAILY_SUPPORTED_DOMAINS
        )
        _missingness_per_domain = {
            d: (snapshot.get(d, {}) or {}).get("missingness")
            for d in _domains_present
        }
        _classified_bands_per_domain: dict[str, dict[str, Any]] = {}
        _review_summary_tokens_per_domain: dict[str, list[str]] = {}
        for d in _domains_present:
            block = snapshot.get(d, {}) or {}
            classified = block.get("classified_state") or {}
            if isinstance(classified, dict):
                _classified_bands_per_domain[d] = {
                    k: v for k, v in classified.items()
                    if isinstance(k, str) and k.endswith("_band")
                }
            review_summary = block.get("review_summary") or {}
            if isinstance(review_summary, dict):
                _review_summary_tokens_per_domain[d] = list(
                    review_summary.get("tokens") or []
                )
        report["stages"]["snapshot"] = {
            "status": "ran",
            "domains_present": _domains_present,
            # Backward-compatible alias for any pre-W43 consumer.
            "domains_in_bundle": _domains_present,
            "full_bundle": evidence_bundle is not None,
            "missingness_per_domain": _missingness_per_domain,
            "classified_bands_per_domain": _classified_bands_per_domain,
            "review_summary_tokens_per_domain": _review_summary_tokens_per_domain,
        }

        # Stage 3b: intake gaps — the agent reads this to compose one
        # consolidated prompt for the user at session start. Empty list
        # when every gap is closed (the zero-friction case: no question
        # to ask, just synthesize). Only populated when the snapshot was
        # built with classified_state (i.e. evidence_bundle was present).
        from health_agent_infra.core.intake.gaps import compute_intake_gaps
        gaps = compute_intake_gaps(snapshot)
        report["stages"]["gaps"] = {
            "status": "ran" if evidence_bundle is not None else "skipped_no_bundle",
            "gaps": [g.to_dict() for g in gaps],
            "gap_count": len(gaps),
            "gating_gap_count": sum(1 for g in gaps if g.blocks_coverage),
        }

        # Stage 4: proposal gate — honest check, no faking
        proposals = read_proposals_for_plan_key(
            conn, for_date=as_of.isoformat(), user_id=user_id,
        )
        present_domains = sorted({p["domain"] for p in proposals})
        missing_expected = sorted(set(expected_domains) - set(present_domains))
        # v0.1.6 (B1 fix): the gate is "all expected domains present,"
        # not "any proposals at all." A 1-of-6 plan is no longer
        # silently `complete` — synthesis is blocked until the agent
        # supplies proposals for every expected domain (or narrows
        # `expected_domains` via `--domains`). Three statuses:
        #   - awaiting_proposals: zero proposals
        #   - incomplete:         some proposals, missing >=1 expected
        #   - complete:           every expected domain present
        if not proposals:
            gate_status = "awaiting_proposals"
        elif missing_expected:
            gate_status = "incomplete"
        else:
            gate_status = "complete"
        gate_ok = gate_status == "complete"
        report["stages"]["proposal_gate"] = {
            "status": gate_status,
            "expected": sorted(expected_domains),
            "present": present_domains,
            "missing": missing_expected,
        }
        # v0.1.7 (W21 telemetry / Codex r2 gap L): persist the gate
        # outcome to runtime_event_log.context_json so W28's funnel
        # can query past `incomplete` / `awaiting_proposals` / complete
        # days from durable state instead of reconstructing from
        # transient stdout.
        if runtime_event_dict is not None:
            runtime_event_dict["context"] = {
                "stage": "proposal_gate",
                "overall_status": gate_status,
                "expected_domains": sorted(expected_domains),
                "present_domains": present_domains,
                "missing_domains": missing_expected,
            }
        if not gate_ok:
            if gate_status == "awaiting_proposals":
                hint = (
                    "Agent must post DomainProposal rows via `hai propose` "
                    "for the expected domains, then rerun `hai daily`."
                )
            else:
                hint = (
                    f"Synthesis blocked: missing proposals for "
                    f"{missing_expected}. Either post DomainProposal rows "
                    f"for those domains via `hai propose`, OR narrow the "
                    f"expected set via `hai daily --domains <csv>`."
                )
            report["stages"]["synthesize"] = {
                "status": "skipped_awaiting_proposals",
                "hint": hint,
            }
            report["stages"]["reviews"] = {"status": "skipped"}
            report["overall_status"] = gate_status
            # v0.1.7 W21: when --auto, attach the typed next_actions
            # manifest so an agent can route on it without prose-parsing.
            if getattr(args, "auto", False):
                from health_agent_infra.core.intake.next_actions import (
                    build_next_actions_payload,
                )
                gaps_for_manifest = (
                    report["stages"].get("gaps", {}).get("gaps") or []
                )
                report["next_actions_manifest"] = build_next_actions_payload(
                    for_date=as_of.isoformat(),
                    user_id=user_id,
                    overall_status=gate_status,
                    expected_domains=sorted(expected_domains),
                    present_domains=present_domains,
                    missing_domains=missing_expected,
                    intake_gaps=gaps_for_manifest,
                )
            if getattr(args, "auto", False) and getattr(args, "explain", False):
                report["explain"] = _build_daily_explain_block(report)
            _emit_json(report)
            return exit_codes.OK

        # Stage 5: synthesize — atomic Phase A + Phase B commit
        try:
            result = run_synthesis(
                conn,
                for_date=as_of,
                user_id=user_id,
                snapshot=snapshot,
                agent_version=args.agent_version,
                supersede=args.supersede,
                re_propose_all=re_propose_all_requested,
            )
        except (SynthesisError, XRuleWriteSurfaceViolation) as exc:
            report["stages"]["synthesize"] = {
                "status": "failed",
                "error": str(exc),
            }
            report["overall_status"] = "failed"
            _emit_json(report)
            return exit_codes.USER_INPUT
        report["stages"]["synthesize"] = {
            "status": "ran",
            "daily_plan_id": result.daily_plan_id,
            "recommendation_ids": list(result.recommendation_ids),
            "proposal_ids": list(result.proposal_ids),
            "phase_a_count": len(result.phase_a_firings),
            "phase_b_count": len(result.phase_b_firings),
            "superseded_prior": result.superseded_prior,
        }

        # Stage 6: schedule reviews
        if args.skip_reviews:
            report["stages"]["reviews"] = {"status": "skipped"}
        else:
            scheduled = _schedule_reviews_for_daily_plan(
                conn, daily_plan_id=result.daily_plan_id, base_dir=base_dir,
            )
            report["stages"]["reviews"] = {
                "status": "ran",
                "scheduled_event_ids": scheduled,
            }
    finally:
        conn.close()

    report["overall_status"] = "complete"
    # v0.1.7 W21: emit the next_actions manifest in --auto mode even on
    # the complete path; the terminal action is `narrate_ready` so the
    # agent knows to invoke the reporting skill (and later record
    # outcomes via `hai review record`).
    if getattr(args, "auto", False):
        from health_agent_infra.core.intake.next_actions import (
            build_next_actions_payload,
        )
        report["next_actions_manifest"] = build_next_actions_payload(
            for_date=as_of.isoformat(),
            user_id=user_id,
            overall_status="complete",
            expected_domains=sorted(expected_domains),
            present_domains=sorted({p["domain"] for p in proposals}),
            missing_domains=[],
            intake_gaps=[],
        )
    if getattr(args, "auto", False) and getattr(args, "explain", False):
        report["explain"] = _build_daily_explain_block(report)
    _emit_json(report)
    # D3 §hai daily hint — when stderr is an interactive TTY, surface
    # `hai today` as the next step so new users discover the user
    # surface without having to read the docs. Skipped on non-TTY
    # (tests, CI, piped callers) so scraped stderr stays byte-stable.
    if sys.stderr.isatty():
        as_of_iso = report.get("as_of_date", "")
        print(
            f"\nnext: read today's plan in plain language — "
            f"`hai today --as-of {as_of_iso} --user-id {user_id}` "
            f"(or just `hai today`).",
            file=sys.stderr,
        )
    return exit_codes.OK


# cmd_setup_skills + cmd_init + onboarding helpers moved to cli/handlers/config_init.py at W-29.2.7.


# ---------------------------------------------------------------------------
# hai doctor — read-only runtime diagnostics
