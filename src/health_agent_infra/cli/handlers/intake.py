"""``hai intake`` handler group — typed user inputs.

Owns: ``hai intake gym``, ``hai intake exercise``, ``hai intake nutrition``,
``hai intake stress``, ``hai intake note``, ``hai intake readiness``,
``hai intake gaps``. Plus the per-domain ``_project_*_submission_into_state``
helpers and ``_resolve_prior_nutrition_submission``.

Module-level constants extracted with the handlers: ``SORENESS_CHOICES``,
``ENERGY_CHOICES``, ``INTENSITY_DELTA_CHOICES``, ``EXERCISE_CATEGORY_CHOICES``,
``EXERCISE_EQUIPMENT_CHOICES``.

W-29.2.10 split: extracted from cli/__init__.py 735-1868.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir

# Cli-private helpers defined before line 735.
from health_agent_infra.cli import (  # noqa: E402
    _close_sync_row_failed,
    _close_sync_row_ok,
    _coerce_date,
    _coerce_dt,
    _dual_write_project,
    _emit_json,
    _load_json_arg,
    _open_sync_row,
    _sync_if_db,
)


# ---------------------------------------------------------------------------
# hai intake readiness — typed manual readiness intake, emits JSON to stdout
# ---------------------------------------------------------------------------

SORENESS_CHOICES = ("low", "moderate", "high")
ENERGY_CHOICES = ("low", "moderate", "high")
# M4 — intensity_delta ordinal axis. Kept here (not inside the review
# module) so the CLI-facing choices list lives next to other CLI enums.
# summarize_review_history imports this via the mapping below so there's
# one source of truth.
INTENSITY_DELTA_CHOICES = (
    "much_lighter", "lighter", "same", "harder", "much_harder",
)
EXERCISE_CATEGORY_CHOICES = ("compound", "isolation")
EXERCISE_EQUIPMENT_CHOICES = (
    "barbell", "dumbbell", "cable", "bodyweight", "machine", "kettlebell",
)


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

    from health_agent_infra.domains.strength.intake import (
        GymSessionSubmission,
        GymSet,
        append_submission_jsonl,
        parse_bulk_session_json,
    )

    base_dir = resolve_base_dir(args.base_dir)

    if args.session_json:
        try:
            payload = json.loads(
                Path(args.session_json).expanduser().read_text(encoding="utf-8")
            )
            parse_bulk_session_json(payload)
        except (json.JSONDecodeError, ValueError) as exc:
            print(f"intake gym rejected: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
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
            return exit_codes.USER_INPUT
        if args.reps is None and args.weight_kg is None:
            print(
                "intake gym: at least one of --reps or --weight-kg must be given",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
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

    with _sync_if_db(
        args.db_path,
        source="gym_manual",
        user_id=submission.user_id,
        mode="manual",
        for_date=submission.as_of_date,
    ) as run:
        # JSONL audit first (durable boundary). If this fails, nothing landed.
        jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)

        # DB projection is atomic + fail-soft.
        _project_gym_submission_into_state(args.db_path, submission)

        run["rows_pulled"] = len(submission.sets)
        run["rows_accepted"] = len(submission.sets)
        run["duplicates_skipped"] = 0

    _emit_json({
        "submission_id": submission.submission_id,
        "session_id": submission.session_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "sets_logged": len(submission.sets),
        "jsonl_path": str(jsonl_path),
    })
    return exit_codes.OK


def _project_gym_submission_into_state(db_path_arg, submission) -> None:
    """Project a gym submission into the state DB atomically (fail-soft).

    Pattern: same as ``_project_clean_into_state``. All three writes
    (gym_session, one-or-more gym_set rows, recomputed
    accepted_resistance_training_state_daily) land inside a single
    ``BEGIN IMMEDIATE``/``COMMIT``. A mid-flight failure rolls back; the
    JSONL audit write already happened so ``hai state reproject
    --base-dir <d>`` can rebuild the DB.
    """

    from health_agent_infra.domains.strength.intake import (
        _norm_token,
        deterministic_set_id,
    )
    from health_agent_infra.domains.strength.taxonomy_match import (
        load_taxonomy_with_aliases,
        match_exercise_name,
    )
    from health_agent_infra.core.state import (
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
        # Build the taxonomy resolver once per invocation so every set
        # in the submission shares a single consistent view. Only
        # high-confidence matches (exact canonical or single-alias)
        # stamp ``gym_set.exercise_id``; ambiguous or no-match sets
        # leave exercise_id NULL — the projector re-resolves by name
        # anyway, and stamping an arbitrary pick would corrupt audit.
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
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
                match = match_exercise_name(
                    s.exercise_name,
                    taxonomy=taxonomy,
                    aliases_by_id=aliases_by_id,
                    resolver=resolver,
                )
                stamped_id = (
                    match.exercise_id
                    if match.confidence in ("exact", "alias")
                    else None
                )
                project_gym_set(
                    conn,
                    set_id=deterministic_set_id(
                        submission.session_id,
                        _norm_token(s.exercise_name),
                        s.set_number,
                    ),
                    session_id=submission.session_id,
                    set_number=s.set_number,
                    exercise_name=s.exercise_name,
                    weight_kg=s.weight_kg,
                    reps=s.reps,
                    rpe=s.rpe,
                    exercise_id=stamped_id,
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
            f"reproject --base-dir <base-dir>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


def cmd_intake_exercise(args: argparse.Namespace) -> int:
    """Insert a user-defined exercise-taxonomy row into the state DB.

    This is the deliberate extension path strength skills surface when
    unmatched exercise tokens appear. It writes directly to
    ``exercise_taxonomy`` with ``source='user_manual'``; no JSONL audit
    exists for taxonomy rows in v1, so the DB row is the canonical record.
    """

    from health_agent_infra.core.state import (
        open_connection,
        project_exercise_taxonomy_entry,
        resolve_db_path,
    )
    from health_agent_infra.domains.strength.intake import (
        build_manual_taxonomy_row,
    )

    try:
        row = build_manual_taxonomy_row(
            canonical_name=args.name,
            primary_muscle_group=args.primary_muscle_group,
            category=args.category,
            equipment=args.equipment,
            exercise_id=args.exercise_id,
            aliases=args.aliases,
            secondary_muscle_groups=args.secondary_muscle_groups,
        )
    except ValueError as exc:
        print(f"intake exercise rejected: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # Exercise-taxonomy entries are global (not per-user), so sync rows
    # here use a "global" sentinel — the snapshot's user-scoped
    # freshness query won't surface them, which is intentional: these
    # are config-shaped events, not data-ingest ones.
    sync_id = _open_sync_row(
        args.db_path,
        source="exercise_taxonomy_manual",
        user_id="global",
        mode="manual",
        for_date=None,
    )

    conn = open_connection(db_path)
    try:
        # F-A-07 fix per W-H1: build_manual_taxonomy_row validates the
        # required fields upstream, but mypy sees the row dict's values
        # as Optional. Pull required fields into local non-Optional
        # bindings so the projector call sees narrowed types.
        from typing import cast as _cast
        exercise_id_v = _cast(str, row["exercise_id"])
        canonical_name_v = _cast(str, row["canonical_name"])
        primary_muscle_group_v = _cast(str, row["primary_muscle_group"])
        category_v = _cast(str, row["category"])
        equipment_v = _cast(str, row["equipment"])
        try:
            inserted = project_exercise_taxonomy_entry(
                conn,
                exercise_id=exercise_id_v,
                canonical_name=canonical_name_v,
                aliases=row["aliases"],
                primary_muscle_group=primary_muscle_group_v,
                secondary_muscle_groups=row["secondary_muscle_groups"],
                category=category_v,
                equipment=equipment_v,
                source="user_manual",
            )
        except sqlite3.IntegrityError as exc:
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(f"intake exercise rejected: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT

        saved = conn.execute(
            """
            SELECT exercise_id, canonical_name, aliases,
                   primary_muscle_group, secondary_muscle_groups,
                   category, equipment, source
            FROM exercise_taxonomy
            WHERE exercise_id = ?
            """,
            (row["exercise_id"],),
        ).fetchone()
    finally:
        conn.close()

    _close_sync_row_ok(
        args.db_path,
        sync_id,
        rows_pulled=1 if inserted else 0,
        rows_accepted=1 if inserted else 0,
        duplicates_skipped=0 if inserted else 1,
    )

    _emit_json({
        "inserted": inserted,
        "exercise_id": saved["exercise_id"],
        "canonical_name": saved["canonical_name"],
        "aliases": saved["aliases"].split("|") if saved["aliases"] else [],
        "primary_muscle_group": saved["primary_muscle_group"],
        "secondary_muscle_groups": (
            saved["secondary_muscle_groups"].split("|")
            if saved["secondary_muscle_groups"]
            else []
        ),
        "category": saved["category"],
        "equipment": saved["equipment"],
        "source": saved["source"],
    })
    return exit_codes.OK


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

    from health_agent_infra.domains.nutrition.intake import (
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
            return exit_codes.USER_INPUT
        if value < 0:
            print(f"intake nutrition: --{name.replace('_', '-')} must be >= 0",
                  file=sys.stderr)
            return exit_codes.USER_INPUT
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
            return exit_codes.USER_INPUT

    as_of = _coerce_date(args.as_of)
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    submission_id = f"m_nut_{as_of.isoformat()}_{suffix}"

    base_dir = resolve_base_dir(args.base_dir)

    # Auto-detect supersedes chain from the JSONL (the durable boundary).
    # Reading from the DB would be faster but would break correction chains
    # when the DB is absent at write time — subsequent reproject would
    # faithfully replay `supersedes = None` and leave orphaned raw rows.
    # JSONL resolution preserves the chain regardless of DB state.
    supersedes_id = _resolve_prior_nutrition_submission(
        base_dir=base_dir, as_of_date=as_of, user_id=args.user_id,
    )

    # v0.1.7 (W34 / Codex r2 W6 revived): nutrition is a daily total,
    # not per-meal. A second same-day write supersedes the prior row
    # silently — fine when the user is correcting a typo, dangerous
    # when the agent (or a confused operator) is treating the command
    # as a per-meal logger. Refuse with USER_INPUT unless --replace is
    # explicit so the supersede is always conscious.
    if supersedes_id is not None and not args.replace:
        print(
            f"hai intake nutrition: refusing to silently supersede an "
            f"existing nutrition row for ({as_of.isoformat()}, "
            f"{args.user_id}). The prior submission "
            f"({supersedes_id}) would become a superseded entry in "
            f"the JSONL chain. Nutrition is a DAILY TOTAL — log it "
            f"once at end of day, not per-meal. If you genuinely "
            f"intend to correct the prior row, re-run with --replace. "
            f"If you wanted a per-meal scratchpad, use `hai intake "
            f"note --tags nutrition,<meal>` instead.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

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

    with _sync_if_db(
        args.db_path,
        source="nutrition_manual",
        user_id=submission.user_id,
        mode="manual",
        for_date=submission.as_of_date,
    ) as run:
        # JSONL audit first (durable boundary). base_dir was resolved above for
        # correction-chain lookup; re-use it here.
        jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)

        # DB projection is atomic + fail-soft.
        _project_nutrition_submission_into_state(args.db_path, submission)

        run["rows_pulled"] = 1
        run["rows_accepted"] = 1
        run["duplicates_skipped"] = 0

    _emit_json({
        "submission_id": submission.submission_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "supersedes_submission_id": submission.supersedes_submission_id,
        "jsonl_path": str(jsonl_path),
    })
    return exit_codes.OK


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

    from health_agent_infra.domains.nutrition.intake import (
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

    from health_agent_infra.core.state import (
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
            f"`hai state reproject --base-dir <base-dir>` to recover.",
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

    from health_agent_infra.domains.stress.intake import (
        StressSubmission,
        append_submission_jsonl,
        latest_submission_id_from_jsonl,
    )

    if args.score is None or args.score not in (1, 2, 3, 4, 5):
        # argparse choices already enforces, but defensive:
        print(
            "intake stress: --score must be one of {1,2,3,4,5}; "
            "rerun with `--score <n>` where n is in that range.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    tags: Optional[list[str]] = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if not tags:
            tags = None

    as_of = _coerce_date(args.as_of)
    base_dir = resolve_base_dir(args.base_dir)
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

    with _sync_if_db(
        args.db_path,
        source="stress_manual",
        user_id=submission.user_id,
        mode="manual",
        for_date=submission.as_of_date,
    ) as run:
        jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)
        _project_stress_submission_into_state(args.db_path, submission)

        run["rows_pulled"] = 1
        run["rows_accepted"] = 1
        run["duplicates_skipped"] = 0

    _emit_json({
        "submission_id": submission.submission_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "score": submission.score,
        "supersedes_submission_id": submission.supersedes_submission_id,
        "jsonl_path": str(jsonl_path),
    })
    return exit_codes.OK


def _project_stress_submission_into_state(db_path_arg, submission) -> None:
    """Project stress raw + merge into accepted stress atomically.

    Two writes inside one ``BEGIN IMMEDIATE`` / ``COMMIT``:
      1. INSERT into ``stress_manual_raw`` (append-only).
      2. UPDATE/INSERT into ``accepted_stress_state_daily`` with
         ``manual_stress_score`` + ``stress_tags_json`` set to the latest
         non-superseded raw row for this (day, user). Garmin fields
         (``garmin_all_day_stress``, ``body_battery_end_of_day``)
         preserved on UPDATE — the clean projector owns that dimension.
    """

    from health_agent_infra.core.state import (
        merge_manual_stress_into_accepted_stress,
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
            merge_manual_stress_into_accepted_stress(
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

    from health_agent_infra.core.intake.note import (
        ContextNote,
        append_note_jsonl,
    )

    if not args.text or not args.text.strip():
        print(
            "intake note: --text must be a non-empty string; "
            "rerun with `--text \"<your note>\"`.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    tags: Optional[list[str]] = None
    if args.tags:
        tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if not tags:
            tags = None

    as_of = _coerce_date(args.as_of)
    recorded_at = _coerce_dt(args.recorded_at) if args.recorded_at else datetime.now(timezone.utc)
    base_dir = resolve_base_dir(args.base_dir)

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

    with _sync_if_db(
        args.db_path,
        source="note_manual",
        user_id=note.user_id,
        mode="manual",
        for_date=note.as_of_date,
    ) as run:
        jsonl_path = append_note_jsonl(note, base_dir=base_dir)
        _project_context_note_into_state(args.db_path, note)

        run["rows_pulled"] = 1
        run["rows_accepted"] = 1
        run["duplicates_skipped"] = 0

    _emit_json({
        "note_id": note.note_id,
        "user_id": note.user_id,
        "as_of_date": note.as_of_date.isoformat(),
        "recorded_at": note.recorded_at.isoformat(),
        "jsonl_path": str(jsonl_path),
    })
    return exit_codes.OK


def _project_context_note_into_state(db_path_arg, note) -> None:
    """Project a context note into the state DB. Single-row insert; no
    accepted-layer derivation, so no transaction needed for atomicity
    (nothing to roll back across)."""

    from health_agent_infra.core.state import (
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
    """Persist a typed manual-readiness entry.

    Per D2 (``reporting/plans/v0_1_4/D2_intake_write_paths.md``):
    readiness is no longer a stdout-only composer. It appends a JSONL
    audit line to ``<base_dir>/readiness_manual.jsonl`` and projects
    into ``manual_readiness_raw`` (migration 015). ``hai pull`` auto-
    reads same-day rows so the intake actually moves today's plan —
    fixing the 2026-04-23 footgun where users ran ``hai intake readiness``
    and the classifier silently ignored it.

    Composes the same way as before: the echoed stdout payload matches
    the shape ``--manual-readiness-json`` has always consumed, so the
    agent-composer path with an explicit override file keeps working.
    """

    from health_agent_infra.domains.recovery.readiness_intake import (
        ReadinessSubmission,
        append_submission_jsonl,
        latest_submission_id_from_jsonl,
    )

    as_of = _coerce_date(args.as_of)
    base_dir = resolve_base_dir(args.base_dir)
    issued_at = datetime.now(timezone.utc)
    suffix = issued_at.strftime("%H%M%S%f")
    submission_id = f"m_ready_{as_of.isoformat()}_{suffix}"

    # Resolve prior tail from the durable JSONL audit (DB-independent
    # chain resolution — same discipline as stress/nutrition intake).
    supersedes_id = latest_submission_id_from_jsonl(
        base_dir, as_of_date=as_of, user_id=args.user_id,
    )

    submission = ReadinessSubmission(
        submission_id=submission_id,
        user_id=args.user_id,
        as_of_date=as_of,
        soreness=args.soreness,
        energy=args.energy,
        planned_session_type=args.planned_session_type,
        active_goal=args.active_goal,
        ingest_actor=args.ingest_actor,
        submitted_at=issued_at,
        supersedes_submission_id=supersedes_id,
    )

    with _sync_if_db(
        args.db_path,
        source="readiness_manual",
        user_id=submission.user_id,
        mode="manual",
        for_date=submission.as_of_date,
    ) as run:
        jsonl_path = append_submission_jsonl(submission, base_dir=base_dir)
        _project_readiness_submission_into_state(args.db_path, submission)

        run["rows_pulled"] = 1
        run["rows_accepted"] = 1
        run["duplicates_skipped"] = 0

    payload: dict[str, Any] = {
        "submission_id": submission.submission_id,
        "user_id": submission.user_id,
        "as_of_date": submission.as_of_date.isoformat(),
        "soreness": submission.soreness,
        "energy": submission.energy,
        "planned_session_type": submission.planned_session_type,
        "supersedes_submission_id": submission.supersedes_submission_id,
        "jsonl_path": str(jsonl_path),
    }
    if submission.active_goal:
        payload["active_goal"] = submission.active_goal
    _emit_json(payload)
    return exit_codes.OK


def cmd_intake_gaps(args: argparse.Namespace) -> int:
    """Emit the list of user-closeable intake gaps for the snapshot.

    Read-only. ``--evidence-json`` is required: without the cleaned
    bundle, ``build_snapshot`` produces a lean snapshot that lacks
    per-domain ``classified_state``, and ``compute_intake_gaps`` then
    silently returns ``[]``. That zero is indistinguishable from a true
    "no gaps" answer — a footgun that bit a real user session in
    2026-04-25 (see ``reporting/plans/v0_1_6/PLAN.md`` B6). The CLI
    refuses with USER_INPUT in that case rather than emit the
    misleading shape; the OK path emits ``"computed": true`` so callers
    can pattern-match on the field instead of guessing.
    """

    from health_agent_infra.core.intake.gaps import (
        StalenessRefusal,
        compute_intake_gaps,
        compute_intake_gaps_from_state_snapshot,
    )
    from health_agent_infra.core.intake.presence import (
        compute_presence_block,
    )
    from health_agent_infra.core.state import (
        build_snapshot,
        open_connection,
        resolve_db_path,
    )

    as_of = _coerce_date(args.as_of)
    user_id = args.user_id

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai intake gaps: state DB not found at {db_path}. Run "
            f"`hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # v0.1.15 W-A: compute the presence block once per invocation. Both
    # output paths (--from-state-snapshot and --evidence-json) get the
    # same `present` + `is_partial_day` + `target_status` keys so an
    # agent driving the CLI can rely on the W-A contract regardless of
    # which derivation source the caller picked.
    presence_conn = open_connection(db_path)
    try:
        presence_block = compute_presence_block(
            presence_conn, as_of=as_of, user_id=user_id,
        )
    finally:
        presence_conn.close()

    # v0.1.11 W-W: --from-state-snapshot is the new offline-derivation
    # path (Codex F-DEMO-04). Mutually exclusive with --evidence-json.
    if getattr(args, "from_state_snapshot", False):
        if args.evidence_json:
            print(
                "hai intake gaps: --from-state-snapshot is mutually "
                "exclusive with --evidence-json. Pick one source.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        # D12: coerce the staleness threshold from thresholds.toml
        from health_agent_infra.core.config import (
            coerce_int,
            load_thresholds,
        )
        thresholds = load_thresholds()
        max_hours = coerce_int(
            thresholds.get("gap_detection", {}).get(
                "snapshot_staleness_max_hours", 48
            ),
            name="gap_detection.snapshot_staleness_max_hours",
        )
        try:
            payload = compute_intake_gaps_from_state_snapshot(
                db_path=db_path,
                as_of_date=as_of,
                user_id=user_id,
                allow_stale=getattr(args, "allow_stale_snapshot", False),
                staleness_max_hours=max_hours,
            )
        except StalenessRefusal as exc:
            print(f"hai intake gaps: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
        # v0.1.15 W-A: merge the presence block into the payload.
        payload.update(presence_block)
        _emit_json(payload)
        return exit_codes.OK

    if not args.evidence_json:
        print(
            "hai intake gaps: --evidence-json is required for gap "
            "detection (or pass --from-state-snapshot to derive from "
            "the latest accepted state offline). Without either flag "
            "the snapshot lacks per-domain classified_state, so no "
            "uncertainty tokens are available and the gap detector can "
            "only return an empty list — which is indistinguishable "
            "from a true zero.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    from health_agent_infra.cli import _load_cleaned_bundle  # lazy: defined later in cli/__init__.py
    evidence, raw_summary, err = _load_cleaned_bundle(args.evidence_json)
    if err is not None:
        print(f"hai intake gaps: {err}", file=sys.stderr)
        return exit_codes.USER_INPUT
    evidence_bundle = {
        "cleaned_evidence": evidence, "raw_summary": raw_summary,
    }

    conn = open_connection(db_path)
    try:
        snapshot = build_snapshot(
            conn, as_of_date=as_of, user_id=user_id,
            evidence_bundle=evidence_bundle,
        )
    finally:
        conn.close()

    gaps = compute_intake_gaps(snapshot)
    # v0.1.11 W-W: distinguish source for audit-trail clarity.
    gap_dicts = []
    for g in gaps:
        d = g.to_dict()
        d["derived_from"] = "pull_evidence"
        gap_dicts.append(d)
    payload = {
        "as_of_date": as_of.isoformat(),
        "user_id": user_id,
        "computed": True,
        "derived_from": "pull_evidence",
        "gaps": gap_dicts,
        "gap_count": len(gaps),
        "gating_gap_count": sum(1 for g in gaps if g.blocks_coverage),
    }
    # v0.1.15 W-A: presence block + is_partial_day + target_status.
    payload.update(presence_block)
    _emit_json(payload)
    return exit_codes.OK


def _project_readiness_submission_into_state(db_path_arg, submission) -> None:
    """Project a readiness submission into ``manual_readiness_raw``.

    Best-effort: matches the stress/nutrition projector pattern so a
    user without a state DB still gets a durable JSONL audit line
    (emitted just before this call) and a stderr hint about enabling
    DB dual-write via ``hai state init``.
    """

    from health_agent_infra.core.state import (
        open_connection,
        project_manual_readiness_raw,
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
        project_manual_readiness_raw(
            conn,
            submission_id=submission.submission_id,
            user_id=submission.user_id,
            as_of_date=submission.as_of_date,
            soreness=submission.soreness,
            energy=submission.energy,
            planned_session_type=submission.planned_session_type,
            active_goal=submission.active_goal,
            ingest_actor=submission.ingest_actor,
            supersedes_submission_id=submission.supersedes_submission_id,
        )
    except Exception as exc:  # noqa: BLE001
        print(
            f"warning: readiness intake projection into state DB failed: "
            f"{exc}. JSONL audit is durable; run `hai state reproject "
            f"--base-dir <intake-root>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# hai state init / hai state migrate — SQLite substrate (7A.1)
# ---------------------------------------------------------------------------
# W-29.2.4: handler bodies live in cli/handlers/state.py.


# ---------------------------------------------------------------------------
# hai intake weight — W-B (v0.1.17 §2.H) body-composition intake
# ---------------------------------------------------------------------------

def cmd_intake_weight(args: argparse.Namespace) -> int:
    """Record a body-composition measurement (weight + optional body-fat %).

    User-authored only (per F-PLAN-09 round-1 ratification): the manifest
    declares ``agent_safe=False`` and the runtime trusts that. Multiple
    measurements per day are valid (fasted morning + post-meal evening
    are different observations); idempotency is "append, not replace".

    Audit: writes one JSONL row to
    ``<base_dir>/body_comp_intake.jsonl`` and one row to the
    ``body_comp`` table (dual-write for byte-stable replay parity).
    """

    from health_agent_infra.core.body_comp import (
        BodyCompValidationError,
        add_body_comp,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    # Resolve measured_at + as_of_date.
    if args.measured_at:
        try:
            measured_at = _coerce_dt(args.measured_at)
        except ValueError as exc:
            sys.stderr.write(
                f"hai intake weight: --measured-at must be ISO-8601: {exc}\n"
            )
            return exit_codes.USER_INPUT
    else:
        measured_at = datetime.now(timezone.utc)

    if args.as_of:
        try:
            as_of_date = _coerce_date(args.as_of)
        except ValueError as exc:
            sys.stderr.write(
                f"hai intake weight: --as-of must be YYYY-MM-DD: {exc}\n"
            )
            return exit_codes.USER_INPUT
    else:
        # Default: local civil date of measured_at. Use UTC date here
        # for determinism — the user can pass --as-of explicitly to
        # disambiguate timezone-edge cases.
        as_of_date = measured_at.date()

    # Validate + persist.
    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        sys.stderr.write(
            f"hai intake weight: state DB not found at {db_path}. "
            f"Run `hai state init` first.\n"
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            record = add_body_comp(
                conn,
                user_id=args.user_id,
                measured_at=measured_at,
                as_of_date=as_of_date,
                weight_kg=args.kg,
                body_fat_pct=args.body_fat_pct,
                ingest_actor=args.ingest_actor,
                notes=args.notes,
            )
        except BodyCompValidationError as exc:
            sys.stderr.write(f"hai intake weight: {exc}\n")
            return exit_codes.USER_INPUT
    finally:
        conn.close()

    # JSONL audit log (mirrors the existing intake-jsonl pattern).
    base_dir = resolve_base_dir(args.base_dir)
    jsonl_path = base_dir / "body_comp_intake.jsonl"
    base_dir.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record.to_row(), sort_keys=True) + "\n")

    _emit_json(record.to_row())
    return exit_codes.OK
