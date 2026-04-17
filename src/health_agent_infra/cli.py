"""`hai` CLI — thin subcommands over the deterministic runtime.

Subcommands:

    hai pull      — acquire Garmin evidence for a date, emit JSON
    hai clean     — normalize evidence into CleanedEvidence + RawSummary JSON
    hai writeback — schema-validate a recommendation JSON and persist
    hai review    — schedule review events, record outcomes, summarize history
    hai setup-skills — copy the packaged skills/ directory to ~/.claude/skills/

All judgment (state classification, policy, recommendation shaping) lives in
the markdown skills shipped with this package. This CLI is a tooling surface
for an agent to call; it does not reason about evidence.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.config import (
    ConfigError,
    load_thresholds,
    scaffold_thresholds_toml,
    user_config_path,
)
from health_agent_infra.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    default_manual_readiness,
)
from health_agent_infra.review.outcomes import (
    record_review_outcome,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.schemas import (
    FollowUp,
    PolicyDecision,
    ReviewEvent,
    ReviewOutcome,
    TrainingRecommendation,
)
from health_agent_infra.validate import (
    RecommendationValidationError,
    validate_recommendation_dict,
)
from health_agent_infra.writeback.recommendation import perform_writeback


from importlib.resources import as_file, files

PACKAGE_ROOT = Path(__file__).resolve().parent
# Skills ship inside the package at src/health_agent_infra/skills/. Resolved
# via importlib.resources so `hai setup-skills` works in both editable and
# installed-wheel modes. Callers use ``_skills_source()`` as a context manager
# to materialise a real filesystem path (needed for shutil.copytree).
DEFAULT_CLAUDE_SKILLS_DIR = Path.home() / ".claude" / "skills"


def _skills_source():
    """Context manager yielding a filesystem Path to the packaged skills/ dir."""

    return as_file(files("health_agent_infra").joinpath("skills"))


def _coerce_date(value: str | None) -> date:
    if value is None:
        return datetime.now(timezone.utc).date()
    return date.fromisoformat(value)


def _coerce_dt(value: str | None) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _emit_json(obj: Any) -> None:
    def default(o):
        if is_dataclass(o):
            return asdict(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        raise TypeError(f"not serializable: {type(o).__name__}")

    print(json.dumps(obj, default=default, indent=2, sort_keys=True))


# ---------------------------------------------------------------------------
# hai pull
# ---------------------------------------------------------------------------

def cmd_pull(args: argparse.Namespace) -> int:
    as_of = _coerce_date(args.date)
    adapter = GarminRecoveryReadinessAdapter()
    pull = adapter.load(as_of)

    manual = None
    if args.manual_readiness_json:
        manual = json.loads(Path(args.manual_readiness_json).read_text(encoding="utf-8"))
    elif args.use_default_manual_readiness:
        manual = default_manual_readiness(as_of)

    payload = {
        "as_of_date": as_of.isoformat(),
        "user_id": args.user_id,
        "source": adapter.source_name,
        "pull": pull,
        "manual_readiness": manual,
    }
    _emit_json(payload)
    return 0


# ---------------------------------------------------------------------------
# hai clean
# ---------------------------------------------------------------------------

def cmd_clean(args: argparse.Namespace) -> int:
    pulled = json.loads(Path(args.evidence_json).read_text(encoding="utf-8"))
    as_of = _coerce_date(pulled["as_of_date"])
    user_id = pulled["user_id"]
    pull = pulled["pull"]
    manual = pulled.get("manual_readiness")

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
        raw_daily_row=pull.get("raw_daily_row"),
    )

    raw_row = pull.get("raw_daily_row")
    if raw_row is not None:
        _project_clean_into_state(
            args.db_path,
            as_of_date=as_of,
            user_id=user_id,
            raw_row=raw_row,
        )

    _emit_json({
        "cleaned_evidence": evidence.to_dict(),
        "raw_summary": summary.to_dict(),
    })
    return 0


def _project_clean_into_state(
    db_path_arg,
    *,
    as_of_date: date,
    user_id: str,
    raw_row: dict,
) -> None:
    """Project Garmin raw row + two accepted-state rows into the state DB.

    **Atomicity contract.** All three INSERT/UPDATE operations land in a
    single ``BEGIN IMMEDIATE`` transaction: either every row commits, or
    none do. A failure mid-projection rolls back, leaving the DB in the
    same shape it was before ``hai clean`` started. Without this, a
    partial failure could persist source_daily_garmin while both accepted
    tables stayed empty — and unlike writeback/review, `hai clean` has no
    JSONL audit log, so there would be no reproject path.

    **Scope.** Only Garmin-sourced fields land here. Manual stress,
    nutrition, gym, notes flow through their own ``hai intake`` commands
    (7C) with their own raw-evidence tables; they never enter accepted
    state via ``hai clean``.

    **Fail-soft at the CLI boundary.** DB absent or transaction rolled back
    ⇒ stderr warning and return. stdout is unaffected. Same pattern as
    ``_dual_write_project``, adapted for the three-table recovery path.
    """

    from health_agent_infra.state import (
        open_connection,
        project_accepted_recovery_state_daily,
        project_accepted_running_state_daily,
        project_source_daily_garmin,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"`hai clean` stdout is still emitted. Run `hai state init` to "
            f"enable DB dual-write.",
            file=sys.stderr,
        )
        return

    # export_batch_id stamps the pull run so corrections land as new raw rows
    # per state_model_v1.md §3. A re-pull with newer Garmin data gets a fresh
    # id; a rerun with the same id is an idempotent no-op.
    export_batch_id = f"live_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')}"
    source_row_id = f"{export_batch_id}:0"

    conn = open_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            project_source_daily_garmin(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                export_batch_id=export_batch_id,
                commit_after=False,
            )
            project_accepted_recovery_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            project_accepted_running_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception as exc:  # noqa: BLE001 — any DB failure becomes a warning
        print(
            f"warning: clean projection into state DB failed and was rolled "
            f"back: {exc}. `hai clean` output is still durable on stdout.",
            file=sys.stderr,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# hai writeback — schema-validated recommendation persistence
# ---------------------------------------------------------------------------

def _recommendation_from_dict(data: dict) -> TrainingRecommendation:
    """Construct a TrainingRecommendation from agent-produced JSON.

    Calls ``validate_recommendation_dict`` first — that pure function owns
    every code-enforced invariant. This function is straight deserialization
    after the validator has accepted the input; it carries no policy checks
    of its own.
    """

    validate_recommendation_dict(data)

    follow_up_data = data["follow_up"]
    follow_up = FollowUp(
        review_at=_coerce_dt(follow_up_data["review_at"]),
        review_question=follow_up_data["review_question"],
        review_event_id=follow_up_data["review_event_id"],
    )
    policy_decisions = [
        PolicyDecision(rule_id=d["rule_id"], decision=d["decision"], note=d["note"])
        for d in data["policy_decisions"]
    ]
    return TrainingRecommendation(
        schema_version=data["schema_version"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        issued_at=_coerce_dt(data["issued_at"]),
        for_date=date.fromisoformat(data["for_date"]),
        action=data["action"],
        action_detail=data.get("action_detail"),
        rationale=list(data["rationale"]),
        confidence=data["confidence"],
        uncertainty=list(data["uncertainty"]),
        follow_up=follow_up,
        policy_decisions=policy_decisions,
        bounded=data["bounded"],
    )


def _dual_write_project(db_path_arg, project_fn, label: str) -> None:
    """Run a projector against the resolved state DB.

    Fails soft: if the DB doesn't exist or the projector raises, we print a
    stderr warning and return. The JSONL write is the audit boundary; the DB
    is a queryable projection that ``hai state reproject`` can rebuild.
    ``project_fn`` receives the open connection.
    """

    from health_agent_infra.state import open_connection, resolve_db_path

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to enable "
            f"DB dual-write.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        project_fn(conn)
    except Exception as exc:  # noqa: BLE001 — any DB failure becomes a warning
        print(
            f"warning: {label} projection into state DB failed: {exc}. "
            f"JSONL record is durable; run `hai state reproject --base-dir "
            f"<writeback-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_writeback(args: argparse.Namespace) -> int:
    from health_agent_infra.state import project_recommendation

    data = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    try:
        recommendation = _recommendation_from_dict(data)
    except RecommendationValidationError as exc:
        print(
            f"writeback rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return 2
    except (ValueError, KeyError) as exc:
        print(f"writeback rejected: {exc}", file=sys.stderr)
        return 2

    # JSONL is the audit boundary. Always happens first.
    record = perform_writeback(recommendation, base_dir=Path(args.base_dir))

    # DB projection is best-effort. Failure => stderr warning + exit 0.
    _dual_write_project(
        args.db_path,
        lambda conn: project_recommendation(conn, recommendation),
        "recommendation",
    )

    _emit_json(record.to_dict())
    return 0


# ---------------------------------------------------------------------------
# hai review
# ---------------------------------------------------------------------------

def cmd_review_schedule(args: argparse.Namespace) -> int:
    from health_agent_infra.state import project_review_event

    data = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
    recommendation = _recommendation_from_dict(data)
    event = schedule_review(recommendation, base_dir=Path(args.base_dir))

    _dual_write_project(
        args.db_path,
        lambda conn: project_review_event(conn, event),
        "review event",
    )

    _emit_json(event.to_dict())
    return 0


def cmd_review_record(args: argparse.Namespace) -> int:
    from health_agent_infra.state import project_review_outcome

    data = json.loads(Path(args.outcome_json).read_text(encoding="utf-8"))
    event = ReviewEvent(
        review_event_id=data["review_event_id"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        review_at=_coerce_dt(data.get("review_at", datetime.now(timezone.utc).isoformat())),
        review_question=data.get("review_question", ""),
    )
    outcome = record_review_outcome(
        event,
        base_dir=Path(args.base_dir),
        followed_recommendation=data["followed_recommendation"],
        self_reported_improvement=data.get("self_reported_improvement"),
        free_text=data.get("free_text"),
        now=_coerce_dt(data.get("recorded_at")),
    )

    _dual_write_project(
        args.db_path,
        lambda conn: project_review_outcome(conn, outcome),
        "review outcome",
    )

    _emit_json(outcome.to_dict())
    return 0


def cmd_review_summary(args: argparse.Namespace) -> int:
    outcomes_path = Path(args.base_dir) / "review_outcomes.jsonl"
    if not outcomes_path.exists():
        _emit_json(summarize_review_history([]))
        return 0
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
        ))
    _emit_json(summarize_review_history(outcomes))
    return 0


# ---------------------------------------------------------------------------
# hai intake readiness — typed manual readiness intake, emits JSON to stdout
# ---------------------------------------------------------------------------

SORENESS_CHOICES = ("low", "moderate", "high")
ENERGY_CHOICES = ("low", "moderate", "high")


def cmd_intake_gym(args: argparse.Namespace) -> int:
    """Log a gym session (or one set of a session) as raw user-reported evidence.

    Two modes:

      - **Per-set flags**: ``--session-id --exercise --set-number --weight-kg
        --reps [--rpe]``. Multiple invocations with the same session_id
        accumulate sets under one session. Deterministic ``set_id =
        f"set_{session_id}_{set_number:03d}"`` makes re-invocation idempotent.
      - **Bulk JSON**: ``--session-json <path>`` with ``{session_id,
        session_name?, as_of_date?, notes?, sets: [...]}``. Session_id in the
        JSON takes precedence over ``--session-id`` if both are given.

    Writes:
      - JSONL audit (always first): ``<base_dir>/gym_sessions.jsonl`` with
        one line per set.
      - DB projection (fail-soft, atomic): ``gym_session`` + ``gym_set`` +
        recomputed ``accepted_resistance_training_state_daily`` for the day,
        all inside a single ``BEGIN IMMEDIATE`` / ``COMMIT``.
    """

    from health_agent_infra.intake.gym import (
        GymSessionSubmission,
        GymSet,
        append_submission_jsonl,
        parse_bulk_session_json,
    )

    base_dir = Path(args.base_dir).expanduser()

    if args.session_json:
        try:
            payload = json.loads(
                Path(args.session_json).expanduser().read_text(encoding="utf-8")
            )
            parse_bulk_session_json(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"intake gym rejected: {exc}", file=sys.stderr)
            return 2
        session_id = payload["session_id"]
        session_name = payload.get("session_name")
        notes = payload.get("notes")
        as_of = _coerce_date(payload.get("as_of_date", args.as_of))
        sets = [
            GymSet(
                set_number=int(s["set_number"]),
                exercise_name=str(s["exercise_name"]),
                weight_kg=s.get("weight_kg"),
                reps=s.get("reps"),
                rpe=s.get("rpe"),
                supersedes_set_id=s.get("supersedes_set_id"),
            )
            for s in payload["sets"]
        ]
    else:
        missing = [
            f for f in ("session_id", "exercise", "set_number")
            if getattr(args, f.replace("-", "_"), None) in (None, "")
        ]
        if missing:
            print(
                "intake gym requires per-set flags or --session-json. "
                f"Missing: {missing}",
                file=sys.stderr,
            )
            return 2
        if args.reps is None and args.weight_kg is None:
            print(
                "intake gym: at least one of --reps or --weight-kg must be given",
                file=sys.stderr,
            )
            return 2
        session_id = args.session_id
        session_name = args.session_name
        notes = args.notes
        as_of = _coerce_date(args.as_of)
        sets = [
            GymSet(
                set_number=int(args.set_number),
                exercise_name=args.exercise,
                weight_kg=args.weight_kg,
                reps=args.reps,
                rpe=args.rpe,
            )
        ]

    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    submission = GymSessionSubmission(
        session_id=session_id,
        user_id=args.user_id,
        as_of_date=as_of,
        session_name=session_name,
        notes=notes,
        sets=sets,
        submission_id=f"m_gym_{as_of.isoformat()}_{suffix}",
        ingest_actor=args.ingest_actor,
        submitted_at=issued_at,
    )

    # JSONL audit first (durable boundary). If this fails, nothing landed.
    jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)

    # DB projection is atomic + fail-soft.
    _project_gym_submission_into_state(args.db_path, submission)

    _emit_json({
        "submission_id": submission.submission_id,
        "session_id": submission.session_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "sets_logged": len(submission.sets),
        "jsonl_path": str(jsonl_path),
    })
    return 0


def _project_gym_submission_into_state(db_path_arg, submission) -> None:
    """Project a gym submission into the state DB atomically (fail-soft).

    Pattern: same as ``_project_clean_into_state``. All three writes
    (gym_session, one-or-more gym_set rows, recomputed
    accepted_resistance_training_state_daily) land inside a single
    ``BEGIN IMMEDIATE``/``COMMIT``. A mid-flight failure rolls back; the
    JSONL audit write already happened so ``hai state reproject
    --base-dir <d>`` can rebuild the DB.
    """

    from health_agent_infra.intake.gym import deterministic_set_id
    from health_agent_infra.state import (
        open_connection,
        project_accepted_resistance_training_state_daily,
        project_gym_session,
        project_gym_set,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to enable "
            f"DB dual-write.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            project_gym_session(
                conn,
                session_id=submission.session_id,
                user_id=submission.user_id,
                as_of_date=submission.as_of_date,
                session_name=submission.session_name,
                notes=submission.notes,
                submission_id=submission.submission_id,
                ingest_actor=submission.ingest_actor,
                commit_after=False,
            )
            for s in submission.sets:
                project_gym_set(
                    conn,
                    set_id=deterministic_set_id(
                        submission.session_id, s.set_number,
                    ),
                    session_id=submission.session_id,
                    set_number=s.set_number,
                    exercise_name=s.exercise_name,
                    weight_kg=s.weight_kg,
                    reps=s.reps,
                    rpe=s.rpe,
                    supersedes_set_id=s.supersedes_set_id,
                    commit_after=False,
                )
            project_accepted_resistance_training_state_daily(
                conn,
                as_of_date=submission.as_of_date,
                user_id=submission.user_id,
                ingest_actor=submission.ingest_actor,
                commit_after=False,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: gym intake projection into state DB failed and was "
            f"rolled back: {exc}. JSONL audit is durable; run `hai state "
            f"reproject --base-dir <writeback-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_intake_nutrition(args: argparse.Namespace) -> int:
    """Log a day's nutrition aggregate as raw user-reported evidence.

    Nutrition is daily-grain ("I ate X calories today"). Re-running for
    the same ``(as_of_date, user_id)`` is treated as a **correction**:

      - A new ``nutrition_intake_raw`` row is appended with
        ``supersedes_submission_id`` pointing at the previous row.
      - ``accepted_nutrition_state_daily`` is UPSERTed; ``corrected_at``
        is set on update, NULL on first insert (state_model_v1.md §3).

    Writes:
      - JSONL audit: ``<base_dir>/nutrition_intake.jsonl`` (one line per
        invocation, append-only, the durable boundary).
      - DB projection: ``nutrition_intake_raw`` (append-only) +
        ``accepted_nutrition_state_daily`` (UPSERT) inside one
        ``BEGIN IMMEDIATE`` / ``COMMIT``.
    """

    from health_agent_infra.intake.nutrition import (
        NutritionSubmission,
        append_submission_jsonl,
    )

    # Required macros: reject missing, reject negative.
    for name, value in (
        ("calories", args.calories),
        ("protein_g", args.protein_g),
        ("carbs_g", args.carbs_g),
        ("fat_g", args.fat_g),
    ):
        if value is None:
            print(
                f"intake nutrition requires --{name.replace('_', '-')}",
                file=sys.stderr,
            )
            return 2
        if value < 0:
            print(f"intake nutrition: --{name.replace('_', '-')} must be >= 0",
                  file=sys.stderr)
            return 2
    # Optional fields: if supplied, reject negatives too. Same boundary
    # discipline as the required macros; silently accepting negatives here
    # would land bad data in the accepted row.
    for name, value in (
        ("hydration_l", args.hydration_l),
        ("meals_count", args.meals_count),
    ):
        if value is not None and value < 0:
            print(f"intake nutrition: --{name.replace('_', '-')} must be >= 0",
                  file=sys.stderr)
            return 2

    as_of = _coerce_date(args.as_of)
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    submission_id = f"m_nut_{as_of.isoformat()}_{suffix}"

    base_dir = Path(args.base_dir).expanduser()

    # Auto-detect supersedes chain from the JSONL (the durable boundary).
    # Reading from the DB would be faster but would break correction chains
    # when the DB is absent at write time — subsequent reproject would
    # faithfully replay `supersedes = None` and leave orphaned raw rows.
    # JSONL resolution preserves the chain regardless of DB state.
    supersedes_id = _resolve_prior_nutrition_submission(
        base_dir=base_dir, as_of_date=as_of, user_id=args.user_id,
    )

    submission = NutritionSubmission(
        submission_id=submission_id,
        user_id=args.user_id,
        as_of_date=as_of,
        calories=float(args.calories),
        protein_g=float(args.protein_g),
        carbs_g=float(args.carbs_g),
        fat_g=float(args.fat_g),
        hydration_l=float(args.hydration_l) if args.hydration_l is not None else None,
        meals_count=int(args.meals_count) if args.meals_count is not None else None,
        ingest_actor=args.ingest_actor,
        submitted_at=issued_at,
        supersedes_submission_id=supersedes_id,
    )

    # JSONL audit first (durable boundary). base_dir was resolved above for
    # correction-chain lookup; re-use it here.
    jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)

    # DB projection is atomic + fail-soft.
    _project_nutrition_submission_into_state(args.db_path, submission)

    _emit_json({
        "submission_id": submission.submission_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "supersedes_submission_id": submission.supersedes_submission_id,
        "jsonl_path": str(jsonl_path),
    })
    return 0


def _resolve_prior_nutrition_submission(
    *, base_dir: Path, as_of_date: date, user_id: str,
) -> Optional[str]:
    """Return the tail-of-chain submission_id for ``(as_of_date, user_id)``.

    Reads **from the JSONL audit log** (the durable source of truth per
    state_model_v1.md §3), not the DB. This matters because `hai intake
    nutrition` can run without a DB (fail-soft write path): if we
    resolved from the DB only and it were absent, the second write for
    the same day would stamp ``supersedes_submission_id=None``, and a
    later reproject would faithfully replay a broken chain. Reading from
    JSONL closes that gap — chain correctness is independent of DB state.
    """

    from health_agent_infra.intake.nutrition import (
        latest_submission_id_from_jsonl,
    )

    return latest_submission_id_from_jsonl(
        base_dir, as_of_date=as_of_date, user_id=user_id,
    )


def _project_nutrition_submission_into_state(db_path_arg, submission) -> None:
    """Project a nutrition submission into the state DB atomically.

    Same fail-soft + BEGIN IMMEDIATE / COMMIT pattern as
    ``_project_gym_submission_into_state``. A mid-flight failure rolls
    back both tables; the JSONL audit already landed so
    ``hai state reproject --base-dir <d>`` can recover.
    """

    from health_agent_infra.state import (
        open_connection,
        project_accepted_nutrition_state_daily,
        project_nutrition_intake_raw,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to enable "
            f"DB dual-write.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            project_nutrition_intake_raw(
                conn,
                submission_id=submission.submission_id,
                user_id=submission.user_id,
                as_of_date=submission.as_of_date,
                calories=submission.calories,
                protein_g=submission.protein_g,
                carbs_g=submission.carbs_g,
                fat_g=submission.fat_g,
                hydration_l=submission.hydration_l,
                meals_count=submission.meals_count,
                ingest_actor=submission.ingest_actor,
                supersedes_submission_id=submission.supersedes_submission_id,
                commit_after=False,
            )
            project_accepted_nutrition_state_daily(
                conn,
                as_of_date=submission.as_of_date,
                user_id=submission.user_id,
                ingest_actor=submission.ingest_actor,
                commit_after=False,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: nutrition intake projection into state DB failed "
            f"and was rolled back: {exc}. JSONL audit is durable; run "
            f"`hai state reproject --base-dir <writeback-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_intake_stress(args: argparse.Namespace) -> int:
    """Log a subjective stress score (1–5) for a day.

    Closes the manual-stress provenance loop deferred in the 7A.3 patch:
    user stress lands in ``stress_manual_raw`` (raw evidence) THEN merges
    into ``accepted_recovery_state_daily.manual_stress_score`` with a
    proper derived_from chain back to the raw row.

    Re-running for the same day is a correction (supersedes chain in JSONL
    + corrected_at on the merged row). Chain resolution reads from
    ``<base_dir>/stress_manual.jsonl`` (the durable boundary), so
    DB-absent writes still preserve chains.
    """

    from health_agent_infra.intake.stress import (
        StressSubmission,
        append_submission_jsonl,
        latest_submission_id_from_jsonl,
    )

    if args.score is None or args.score not in (1, 2, 3, 4, 5):
        # argparse choices already enforces, but defensive:
        print("intake stress: --score must be one of {1,2,3,4,5}",
              file=sys.stderr)
        return 2

    tags: Optional[list[str]] = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if not tags:
            tags = None

    as_of = _coerce_date(args.as_of)
    base_dir = Path(args.base_dir).expanduser()
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    submission_id = f"m_stress_{as_of.isoformat()}_{suffix}"

    supersedes_id = latest_submission_id_from_jsonl(
        base_dir, as_of_date=as_of, user_id=args.user_id,
    )

    submission = StressSubmission(
        submission_id=submission_id,
        user_id=args.user_id,
        as_of_date=as_of,
        score=int(args.score),
        tags=tags,
        ingest_actor=args.ingest_actor,
        submitted_at=issued_at,
        supersedes_submission_id=supersedes_id,
    )

    jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)

    _project_stress_submission_into_state(args.db_path, submission)

    _emit_json({
        "submission_id": submission.submission_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "score": submission.score,
        "supersedes_submission_id": submission.supersedes_submission_id,
        "jsonl_path": str(jsonl_path),
    })
    return 0


def _project_stress_submission_into_state(db_path_arg, submission) -> None:
    """Project stress raw + merge into accepted recovery atomically.

    Two writes inside one ``BEGIN IMMEDIATE`` / ``COMMIT``:
      1. INSERT into ``stress_manual_raw`` (append-only).
      2. UPDATE/INSERT into ``accepted_recovery_state_daily`` with
         ``manual_stress_score`` set to the latest non-superseded raw
         score for this (day, user). Garmin fields preserved on UPDATE
         (the clean projector reciprocally preserves manual_stress_score).
    """

    from health_agent_infra.state import (
        merge_manual_stress_into_accepted_recovery,
        open_connection,
        project_stress_manual_raw,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable. Run `hai state init` to enable "
            f"DB dual-write.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        try:
            project_stress_manual_raw(
                conn,
                submission_id=submission.submission_id,
                user_id=submission.user_id,
                as_of_date=submission.as_of_date,
                score=submission.score,
                tags=submission.tags,
                ingest_actor=submission.ingest_actor,
                supersedes_submission_id=submission.supersedes_submission_id,
                commit_after=False,
            )
            merge_manual_stress_into_accepted_recovery(
                conn,
                as_of_date=submission.as_of_date,
                user_id=submission.user_id,
                ingest_actor=submission.ingest_actor,
                commit_after=False,
            )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: stress intake projection into state DB failed and "
            f"was rolled back: {exc}. JSONL audit is durable; run "
            f"`hai state reproject --base-dir <intake-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_intake_note(args: argparse.Namespace) -> int:
    """Log a free-text context note (append-only).

    Notes are raw evidence; there is no accepted-layer projection — the
    raw row IS the canonical state per state_model_v1.md §1. Snapshot
    surfaces them via the `notes.recent` lookback window.

    No correction chain in v1: each invocation makes a new note_id.
    """

    from health_agent_infra.intake.note import (
        ContextNote,
        append_note_jsonl,
    )

    if not args.text or not args.text.strip():
        print("intake note: --text must be a non-empty string", file=sys.stderr)
        return 2

    tags: Optional[list[str]] = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if not tags:
            tags = None

    as_of = _coerce_date(args.as_of)
    recorded_at = _coerce_dt(args.recorded_at) if args.recorded_at else datetime.now(timezone.utc)
    base_dir = Path(args.base_dir).expanduser()

    suffix = datetime.now(timezone.utc).strftime("%H%M%S%f")
    note_id = f"note_{as_of.isoformat()}_{suffix}"

    note = ContextNote(
        note_id=note_id,
        user_id=args.user_id,
        as_of_date=as_of,
        recorded_at=recorded_at,
        text=args.text,
        tags=tags,
        ingest_actor=args.ingest_actor,
    )

    jsonl_path = append_note_jsonl(note, base_dir=base_dir)
    _project_context_note_into_state(args.db_path, note)

    _emit_json({
        "note_id": note.note_id,
        "user_id": note.user_id,
        "as_of_date": note.as_of_date.isoformat(),
        "recorded_at": note.recorded_at.isoformat(),
        "jsonl_path": str(jsonl_path),
    })
    return 0


def _project_context_note_into_state(db_path_arg, note) -> None:
    """Project a context note into the state DB. Single-row insert; no
    accepted-layer derivation, so no transaction needed for atomicity
    (nothing to roll back across)."""

    from health_agent_infra.state import (
        open_connection,
        project_context_note,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        print(
            f"note: state DB projection skipped ({db_path} not found). "
            f"JSONL audit record is durable.",
            file=sys.stderr,
        )
        return

    conn = open_connection(db_path)
    try:
        project_context_note(
            conn,
            note_id=note.note_id,
            user_id=note.user_id,
            as_of_date=note.as_of_date,
            recorded_at=note.recorded_at,
            text=note.text,
            tags=note.tags,
            ingest_actor=note.ingest_actor,
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: note projection into state DB failed: {exc}. "
            f"JSONL audit is durable; run `hai state reproject --base-dir "
            f"<intake-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_intake_readiness(args: argparse.Namespace) -> int:
    """Emit a typed manual-readiness JSON blob to stdout.

    Composes with ``hai pull --manual-readiness-json <path>`` so an agent can
    capture structured readiness without hand-authoring JSON.
    """

    as_of = _coerce_date(args.as_of)
    # Microsecond timestamp in the submission_id keeps it unique across
    # rapid same-day re-invocations without pulling in uuid.
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    payload: dict[str, Any] = {
        "submission_id": f"m_ready_{as_of.isoformat()}_{suffix}",
        "soreness": args.soreness,
        "energy": args.energy,
        "planned_session_type": args.planned_session_type,
    }
    if args.active_goal:
        payload["active_goal"] = args.active_goal
    _emit_json(payload)
    return 0


# ---------------------------------------------------------------------------
# hai state init / hai state migrate — SQLite substrate (7A.1)
# ---------------------------------------------------------------------------

def cmd_state_init(args: argparse.Namespace) -> int:
    """Create the state DB file (if absent) and apply pending migrations."""

    from health_agent_infra.state import initialize_database, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    resolved, applied = initialize_database(db_path)
    _emit_json({
        "db_path": str(resolved),
        "created": applied,  # empty list if nothing was applied in this call
    })
    return 0


def cmd_state_read(args: argparse.Namespace) -> int:
    """Emit rows from one domain's canonical table within a civil-date range."""

    from health_agent_infra.state import (
        available_domains,
        open_connection,
        read_domain,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(f"state DB not found at {db_path}. Run `hai state init` first.",
              file=sys.stderr)
        return 2

    since = date.fromisoformat(args.since)
    until = date.fromisoformat(args.until) if args.until else since

    conn = open_connection(db_path)
    try:
        try:
            rows = read_domain(
                conn,
                domain=args.domain,
                since=since,
                until=until,
                user_id=args.user_id,
            )
        except ValueError as exc:
            print(
                f"unknown domain: {args.domain!r}. known: {available_domains()}",
                file=sys.stderr,
            )
            return 2
    finally:
        conn.close()

    _emit_json({
        "domain": args.domain,
        "as_of_range": [since.isoformat(), until.isoformat()],
        "user_id": args.user_id,
        "rows": rows,
    })
    return 0


def cmd_state_snapshot(args: argparse.Namespace) -> int:
    """Emit the cross-domain state snapshot the agent consumes."""

    from health_agent_infra.state import (
        build_snapshot,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(f"state DB not found at {db_path}. Run `hai state init` first.",
              file=sys.stderr)
        return 2

    as_of = date.fromisoformat(args.as_of)

    conn = open_connection(db_path)
    try:
        snapshot = build_snapshot(
            conn,
            as_of_date=as_of,
            user_id=args.user_id,
            lookback_days=args.lookback_days,
        )
    finally:
        conn.close()

    _emit_json(snapshot)
    return 0


def cmd_state_reproject(args: argparse.Namespace) -> int:
    """Rebuild projected tables from the JSONL audit logs under ``--base-dir``.

    **Scoped by log group** (7C.1 patch). Only the table groups whose
    audit JSONLs are present in ``--base-dir`` are touched:

      - ``recommendation_log.jsonl`` / ``review_events.jsonl`` /
        ``review_outcomes.jsonl`` → recommendation + review tables.
      - ``gym_sessions.jsonl`` → ``gym_session`` + ``gym_set`` +
        ``accepted_resistance_training_state_daily``.
      - ``nutrition_intake.jsonl`` → ``nutrition_intake_raw`` +
        ``accepted_nutrition_state_daily``.

    Groups whose logs are absent are left alone. Replay happens inside
    one ``BEGIN EXCLUSIVE`` / ``COMMIT`` transaction; idempotent. Fail-
    closed on a base_dir with none of the expected JSONLs unless
    ``--allow-empty-reproject`` is passed.
    """

    from health_agent_infra.state import (
        ReprojectBaseDirError,
        open_connection,
        reproject_from_jsonl,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return 2

    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"base-dir not found at {base_dir}", file=sys.stderr)
        return 2

    conn = open_connection(db_path)
    try:
        try:
            counts = reproject_from_jsonl(
                conn, base_dir, allow_empty=args.allow_empty_reproject,
            )
        except ReprojectBaseDirError as exc:
            print(f"reproject refused: {exc}", file=sys.stderr)
            return 2
    finally:
        conn.close()
    _emit_json({
        "db_path": str(db_path),
        "base_dir": str(base_dir),
        "reprojected": counts,
    })
    return 0


def cmd_state_migrate(args: argparse.Namespace) -> int:
    """Apply any pending migrations against an existing state DB.

    Behaves like ``hai state init`` but explicitly intended for upgrading an
    already-initialised DB. Idempotent — re-running against a DB already at
    head returns an empty applied list.
    """

    from health_agent_infra.state import (
        apply_pending_migrations,
        current_schema_version,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return 2
    conn = open_connection(db_path)
    try:
        before = current_schema_version(conn)
        applied = apply_pending_migrations(conn)
        after = current_schema_version(conn)
    finally:
        conn.close()
    _emit_json({
        "db_path": str(db_path),
        "schema_version_before": before,
        "schema_version_after": after,
        "applied": applied,
    })
    return 0


# ---------------------------------------------------------------------------
# hai setup-skills
# ---------------------------------------------------------------------------

def cmd_config_init(args: argparse.Namespace) -> int:
    dest = Path(args.path).expanduser() if args.path else user_config_path()
    if dest.exists() and not args.force:
        print(
            f"config file already exists at {dest}; pass --force to overwrite",
            file=sys.stderr,
        )
        return 2
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(scaffold_thresholds_toml(), encoding="utf-8")
    _emit_json({"written": str(dest), "overwrote": bool(args.force and dest.exists())})
    return 0


def cmd_config_show(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser() if args.path else None
    try:
        merged = load_thresholds(path=path)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    effective_path = path if path is not None else user_config_path()
    _emit_json({
        "source_path": str(effective_path),
        "source_exists": effective_path.exists(),
        "effective_thresholds": merged,
    })
    return 0


def cmd_setup_skills(args: argparse.Namespace) -> int:
    dest = Path(args.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    with _skills_source() as skills_source:
        if not skills_source.exists():
            print(f"skills/ not found at {skills_source}", file=sys.stderr)
            return 2
        for skill_dir in skills_source.iterdir():
            if not skill_dir.is_dir():
                continue
            target = dest / skill_dir.name
            if target.exists():
                if not args.force:
                    print(f"skipping existing skill: {target} (pass --force to overwrite)")
                    continue
                shutil.rmtree(target)
            shutil.copytree(skill_dir, target)
            copied.append(str(target))
    _emit_json({"copied": copied, "dest": str(dest)})
    return 0


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hai", description="Health Agent Infra CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pull = sub.add_parser("pull", help="Pull Garmin evidence for a date")
    p_pull.add_argument("--date", default=None, help="As-of date, ISO-8601 (default today UTC)")
    p_pull.add_argument("--user-id", default="u_local_1")
    p_pull.add_argument("--manual-readiness-json", default=None,
                        help="Path to a JSON file with manual readiness fields")
    p_pull.add_argument("--use-default-manual-readiness", action="store_true",
                        help="Use a neutral manual readiness default (for offline runs)")
    p_pull.set_defaults(func=cmd_pull)

    p_clean = sub.add_parser("clean", help="Normalize pulled evidence + raw summary")
    p_clean.add_argument("--evidence-json", required=True,
                         help="Path to a JSON file produced by `hai pull`")
    p_clean.add_argument("--db-path", default=None,
                         help="State DB path (default: $HAI_STATE_DB or platform default). "
                              "If the DB is absent, projection is skipped with a stderr note; "
                              "stdout is unchanged.")
    p_clean.set_defaults(func=cmd_clean)

    p_wb = sub.add_parser("writeback", help="Schema-validate and persist a recommendation")
    p_wb.add_argument("--recommendation-json", required=True,
                      help="Path to a JSON file matching TrainingRecommendation")
    p_wb.add_argument("--base-dir", required=True,
                      help="Writeback root (must contain 'recovery_readiness_v1')")
    p_wb.add_argument("--db-path", default=None,
                      help="State DB path (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db). "
                           "If the DB is absent, projection is skipped with a stderr note.")
    p_wb.set_defaults(func=cmd_writeback)

    p_review = sub.add_parser("review", help="Review scheduling + outcome persistence")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_rs = review_sub.add_parser("schedule", help="Persist a pending review event for a recommendation")
    p_rs.add_argument("--recommendation-json", required=True)
    p_rs.add_argument("--base-dir", required=True)
    p_rs.add_argument("--db-path", default=None,
                      help="State DB path (same semantics as `hai writeback --db-path`)")
    p_rs.set_defaults(func=cmd_review_schedule)

    p_rr = review_sub.add_parser("record", help="Record a review outcome")
    p_rr.add_argument("--outcome-json", required=True)
    p_rr.add_argument("--base-dir", required=True)
    p_rr.add_argument("--db-path", default=None,
                      help="State DB path (same semantics as `hai writeback --db-path`)")
    p_rr.set_defaults(func=cmd_review_record)

    p_rsum = review_sub.add_parser("summary", help="Summarize outcome history counts")
    p_rsum.add_argument("--base-dir", required=True)
    p_rsum.add_argument("--user-id", default=None)
    p_rsum.set_defaults(func=cmd_review_summary)

    p_intake = sub.add_parser("intake", help="Typed human-input intake surfaces")
    intake_sub = p_intake.add_subparsers(dest="intake_command", required=True)

    p_ig = intake_sub.add_parser(
        "gym",
        help="Log a gym session (or one set) as raw user-reported evidence",
    )
    # Per-set mode
    p_ig.add_argument("--session-id", default=None,
                      help="Stable identifier for the session; multiple invocations "
                           "with the same id accumulate sets under one session")
    p_ig.add_argument("--session-name", default=None,
                      help="Human-readable label (e.g. 'Bench day')")
    p_ig.add_argument("--notes", default=None,
                      help="Free-text notes for the session header")
    p_ig.add_argument("--exercise", default=None,
                      help="Exercise name for this set (e.g. 'Bench Press')")
    p_ig.add_argument("--set-number", type=int, default=None,
                      help="1-based set ordinal within the session")
    p_ig.add_argument("--weight-kg", type=float, default=None,
                      help="Weight lifted in kilograms (omit for bodyweight)")
    p_ig.add_argument("--reps", type=int, default=None,
                      help="Reps completed in this set")
    p_ig.add_argument("--rpe", type=float, default=None,
                      help="Rate of perceived exertion (1-10). Optional.")
    # Bulk mode
    p_ig.add_argument("--session-json", default=None,
                      help="Path to a JSON file with {session_id, session_name?, "
                           "as_of_date?, notes?, sets: [...]}. Bulk alternative to "
                           "per-set flags.")
    # Common
    p_ig.add_argument("--as-of", default=None,
                      help="Civil date this session belongs to (ISO-8601, "
                           "default today UTC)")
    p_ig.add_argument("--user-id", default="u_local_1")
    p_ig.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"),
                      help="Transport identity. 'hai_cli_direct' for typed-by-user; "
                           "'claude_agent_v1' when the agent mediates.")
    p_ig.add_argument("--base-dir", required=True,
                      help="Intake root (where gym_sessions.jsonl will be appended)")
    p_ig.add_argument("--db-path", default=None,
                      help="State DB path (same semantics as `hai writeback --db-path`)")
    p_ig.set_defaults(func=cmd_intake_gym)

    p_in = intake_sub.add_parser(
        "nutrition",
        help="Log a day's nutrition aggregate (calories + macros) as raw "
             "user-reported evidence. Re-running for the same day is a "
             "correction (supersedes chain + corrected_at).",
    )
    p_in.add_argument("--calories", type=float, required=True,
                      help="Total calories consumed that day")
    p_in.add_argument("--protein-g", type=float, required=True,
                      help="Total protein in grams")
    p_in.add_argument("--carbs-g", type=float, required=True,
                      help="Total carbohydrates in grams")
    p_in.add_argument("--fat-g", type=float, required=True,
                      help="Total fat in grams")
    p_in.add_argument("--hydration-l", type=float, default=None,
                      help="Total hydration in litres. Optional.")
    p_in.add_argument("--meals-count", type=int, default=None,
                      help="Number of distinct meals. Optional.")
    p_in.add_argument("--as-of", default=None,
                      help="Civil date this intake belongs to (ISO-8601, "
                           "default today UTC)")
    p_in.add_argument("--user-id", default="u_local_1")
    p_in.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"))
    p_in.add_argument("--base-dir", required=True,
                      help="Intake root (nutrition_intake.jsonl lands here)")
    p_in.add_argument("--db-path", default=None,
                      help="State DB path (same semantics as other intake cmds)")
    p_in.set_defaults(func=cmd_intake_nutrition)

    p_is = intake_sub.add_parser(
        "stress",
        help="Log a subjective stress score (1-5) for a day. Re-running "
             "for the same day is a correction.",
    )
    p_is.add_argument("--score", type=int, choices=(1, 2, 3, 4, 5),
                      required=True,
                      help="Subjective stress band: 1=very low, 5=very high")
    p_is.add_argument("--tags", default=None,
                      help="Comma-separated tags (e.g. 'work,deadline')")
    p_is.add_argument("--as-of", default=None,
                      help="Civil date this score belongs to (ISO-8601, "
                           "default today UTC)")
    p_is.add_argument("--user-id", default="u_local_1")
    p_is.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"))
    p_is.add_argument("--base-dir", required=True,
                      help="Intake root (stress_manual.jsonl lands here)")
    p_is.add_argument("--db-path", default=None)
    p_is.set_defaults(func=cmd_intake_stress)

    p_inote = intake_sub.add_parser(
        "note",
        help="Log a free-text context note. Append-only; no corrections.",
    )
    p_inote.add_argument("--text", required=True,
                         help="Free-text note body. Cannot be empty.")
    p_inote.add_argument("--tags", default=None,
                         help="Comma-separated tags")
    p_inote.add_argument("--recorded-at", default=None,
                         help="Optional ISO-8601 timestamp; defaults to now UTC")
    p_inote.add_argument("--as-of", default=None,
                         help="Civil date this note belongs to (default today UTC)")
    p_inote.add_argument("--user-id", default="u_local_1")
    p_inote.add_argument("--ingest-actor", default="hai_cli_direct",
                         choices=("hai_cli_direct", "claude_agent_v1"))
    p_inote.add_argument("--base-dir", required=True,
                         help="Intake root (context_notes.jsonl lands here)")
    p_inote.add_argument("--db-path", default=None)
    p_inote.set_defaults(func=cmd_intake_note)

    p_ir = intake_sub.add_parser("readiness",
                                 help="Emit a typed manual-readiness JSON to stdout")
    p_ir.add_argument("--soreness", required=True, choices=SORENESS_CHOICES,
                      help="Subjective soreness band: low | moderate | high")
    p_ir.add_argument("--energy", required=True, choices=ENERGY_CHOICES,
                      help="Subjective energy band: low | moderate | high")
    p_ir.add_argument("--planned-session-type", required=True,
                      help="Planned session type (free text; e.g. easy, moderate, hard, intervals, race, rest)")
    p_ir.add_argument("--active-goal", default=None,
                      help="Optional active training goal (free text)")
    p_ir.add_argument("--as-of", default=None,
                      help="As-of date for submission_id (ISO-8601, default today UTC)")
    p_ir.set_defaults(func=cmd_intake_readiness)

    p_state = sub.add_parser("state", help="Local SQLite state store management")
    state_sub = p_state.add_subparsers(dest="state_command", required=True)

    p_si = state_sub.add_parser("init", help="Create the state DB and apply pending migrations")
    p_si.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_si.set_defaults(func=cmd_state_init)

    p_sm = state_sub.add_parser("migrate", help="Apply pending migrations against an existing state DB")
    p_sm.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_sm.set_defaults(func=cmd_state_migrate)

    p_sread = state_sub.add_parser(
        "read",
        help="Per-domain read (introspection): rows from one canonical table within a date range",
    )
    p_sread.add_argument("--domain", required=True,
                         help="One of: recovery, running, gym, nutrition, stress, notes, "
                              "recommendations, reviews, goals")
    p_sread.add_argument("--since", required=True,
                         help="Inclusive civil-date lower bound, ISO-8601")
    p_sread.add_argument("--until", default=None,
                         help="Inclusive civil-date upper bound (default: same as --since)")
    p_sread.add_argument("--user-id", default=None,
                         help="Filter to a single user (default: no filter)")
    p_sread.add_argument("--db-path", default=None)
    p_sread.set_defaults(func=cmd_state_read)

    p_ssnap = state_sub.add_parser(
        "snapshot",
        help="Cross-domain snapshot: the primary read surface the agent consumes",
    )
    p_ssnap.add_argument("--as-of", required=True,
                         help="Civil date to snapshot, ISO-8601")
    p_ssnap.add_argument("--user-id", required=True,
                         help="User whose state to snapshot")
    p_ssnap.add_argument("--lookback-days", type=int, default=14,
                         help="Days of history to include (default: 14)")
    p_ssnap.add_argument("--db-path", default=None)
    p_ssnap.set_defaults(func=cmd_state_snapshot)

    p_sr = state_sub.add_parser(
        "reproject",
        help="Rebuild projected tables from JSONL audit logs, scoped to the "
             "log groups present under --base-dir (recommendation/review, "
             "gym, nutrition).",
    )
    p_sr.add_argument("--base-dir", required=True,
                      help="Writeback/intake root. Recognised audit files: "
                           "recommendation_log.jsonl, review_events.jsonl, "
                           "review_outcomes.jsonl, gym_sessions.jsonl, "
                           "nutrition_intake.jsonl. Only the groups whose "
                           "files are present get truncated and rebuilt.")
    p_sr.add_argument("--db-path", default=None,
                      help="State DB path (default: $HAI_STATE_DB or platform default)")
    p_sr.add_argument("--allow-empty-reproject", action="store_true",
                      help="Allow reproject to truncate the projection tables even when "
                           "the base-dir contains none of the expected JSONL audit logs. "
                           "Refuses by default to guard against typo-driven data loss.")
    p_sr.set_defaults(func=cmd_state_reproject)

    p_setup = sub.add_parser("setup-skills", help="Copy packaged skills/ into ~/.claude/skills/")
    p_setup.add_argument("--dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR))
    p_setup.add_argument("--force", action="store_true",
                         help="Overwrite existing skill directories of the same name")
    p_setup.set_defaults(func=cmd_setup_skills)

    p_config = sub.add_parser("config", help="Inspect or scaffold runtime thresholds")
    config_sub = p_config.add_subparsers(dest="config_command", required=True)

    p_ci = config_sub.add_parser(
        "init",
        help="Scaffold a thresholds.toml at the user config path (platformdirs)",
    )
    p_ci.add_argument("--path", default=None,
                      help="Override destination path (default: platformdirs user_config_dir)")
    p_ci.add_argument("--force", action="store_true",
                      help="Overwrite an existing thresholds.toml")
    p_ci.set_defaults(func=cmd_config_init)

    p_cs = config_sub.add_parser(
        "show",
        help="Print the merged effective thresholds (defaults + user overrides)",
    )
    p_cs.add_argument("--path", default=None,
                      help="Override source path (default: platformdirs user_config_dir)")
    p_cs.set_defaults(func=cmd_config_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
