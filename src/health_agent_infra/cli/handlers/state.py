"""``hai state`` handler group — DB lifecycle + projection + backup/restore/export.

Owns: ``hai state init`` / ``migrate`` / ``read`` / ``snapshot`` / ``reproject``
plus the top-level ``hai backup`` / ``hai restore`` / ``hai export`` commands
(per W-29 boundary refresh §(d) — backup/restore/export co-locate with
state-lifecycle group; v0.1.13 boundary table did not enumerate them).

OQ-1 disposition (per refreshed boundary note): the F-PV14-02
``hai sync purge`` add (Phase 3 commit) lands in this same module
rather than a separate ``cli/handlers/sync.py``.

W-29.2.4 split: extracted from ``cli/__init__.py`` lines 3528-3899
(section header + 8 handler bodies). Cross-handler helpers used:
``_emit_json``, ``_dual_write_project`` (lazy-imported at call time
from ``health_agent_infra.cli`` to avoid module-load circularity).
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra.core import exit_codes
from health_agent_infra.core.paths import resolve_base_dir

# Lazy module-level imports from the partially-loaded cli/__init__.py.
# At W-29.2.4 commit time, cli/__init__.py defines `_emit_json` (line ~157)
# and `_dual_write_project` (line ~1153) BEFORE the line ~3528 import that
# pulls this module — so by the time Python resolves these names below, the
# referenced symbols are already bound. W-29.2 phase-end will move both
# helpers to cli/shared.py to make the dependency explicit.
from health_agent_infra.cli import _dual_write_project, _emit_json  # noqa: E402

# `_load_cleaned_bundle` is defined LATER in cli/__init__.py (line ~3549,
# after the W-29.2.4 import block at ~3528) — top-level importing it would
# trip the partially-initialized-module check. Lazy-imported at call time
# inside cmd_state_reproject below.


def cmd_state_init(args: argparse.Namespace) -> int:
    """Create the state DB file (if absent) and apply pending migrations."""

    from health_agent_infra.core.state import initialize_database, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    resolved, applied = initialize_database(db_path)
    _emit_json({
        "db_path": str(resolved),
        "created": applied,  # empty list if nothing was applied in this call
    })
    return exit_codes.OK


def cmd_state_read(args: argparse.Namespace) -> int:
    """Emit rows from one domain's canonical table within a civil-date range."""

    from health_agent_infra.core.state import (
        available_domains,
        open_connection,
        read_domain,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(f"state DB not found at {db_path}. Run `hai state init` first.",
              file=sys.stderr)
        return exit_codes.USER_INPUT

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
        except ValueError:
            print(
                f"unknown domain: {args.domain!r}. known: {available_domains()}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
    finally:
        conn.close()

    _emit_json({
        "domain": args.domain,
        "as_of_range": [since.isoformat(), until.isoformat()],
        "user_id": args.user_id,
        "rows": rows,
    })
    return exit_codes.OK


def cmd_state_snapshot(args: argparse.Namespace) -> int:
    """Emit the cross-domain state snapshot the agent consumes.

    When ``--evidence-json`` is supplied, the recovery block is expanded
    to the Phase 1 full-bundle shape: evidence + raw_summary +
    classified_state + policy_result (in addition to today/history/
    missingness). Without the flag, the recovery block keeps its v1.0
    shape so existing callers are unaffected.
    """

    from health_agent_infra.core.state import (
        build_snapshot,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(f"state DB not found at {db_path}. Run `hai state init` first.",
              file=sys.stderr)
        return exit_codes.USER_INPUT

    as_of = date.fromisoformat(args.as_of)

    evidence_bundle: Optional[dict] = None
    if args.evidence_json:
        from health_agent_infra.cli import _load_cleaned_bundle
        evidence, raw_summary, err = _load_cleaned_bundle(args.evidence_json)
        if err is not None:
            print(err, file=sys.stderr)
            return exit_codes.USER_INPUT
        evidence_bundle = {"cleaned_evidence": evidence, "raw_summary": raw_summary}

    conn = open_connection(db_path)
    try:
        snapshot = build_snapshot(
            conn,
            as_of_date=as_of,
            user_id=args.user_id,
            lookback_days=args.lookback_days,
            evidence_bundle=evidence_bundle,
        )
    finally:
        conn.close()

    _emit_json(snapshot)
    return exit_codes.OK


def cmd_state_reproject(args: argparse.Namespace) -> int:
    """Rebuild projected tables from the JSONL audit logs under ``--base-dir``.

    **Scoped by log group** (7C.1 patch + Phase B v0.1.4 extension). Only
    the table groups whose audit JSONLs are present in ``--base-dir`` are
    touched:

      - ``recommendation_log.jsonl`` / ``review_events.jsonl`` /
        ``review_outcomes.jsonl`` → recommendation + review tables.
      - ``gym_sessions.jsonl`` → ``gym_session`` + ``gym_set`` +
        ``accepted_resistance_training_state_daily``.
      - ``nutrition_intake.jsonl`` → ``nutrition_intake_raw`` +
        ``accepted_nutrition_state_daily``.
      - ``stress_manual.jsonl`` → ``stress_manual_raw`` plus surgical
        re-merge into ``accepted_stress_state_daily``.
      - ``context_notes.jsonl`` → ``context_notes`` table.
      - ``readiness_manual.jsonl`` → ``manual_readiness_raw``.
      - ``<domain>_proposals.jsonl`` (recovery, running, sleep, strength,
        stress, nutrition) → ``proposal_log``. Replay preserves D1
        revision chains in JSONL append order. Counts surface as
        ``proposals`` (replayed) and ``proposals_skipped_invalid``
        (corrupt or validation-failing lines, skipped not raised).

    Groups whose logs are absent are left alone. Replay happens inside
    one ``BEGIN EXCLUSIVE`` / ``COMMIT`` transaction; idempotent. Fail-
    closed on a base_dir with none of the expected JSONLs unless
    ``--allow-empty-reproject`` is passed.
    """

    from health_agent_infra.core.state import (
        ReprojectBaseDirError,
        ReprojectOrphansError,
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
        return exit_codes.USER_INPUT

    base_dir = resolve_base_dir(args.base_dir)
    if not base_dir.exists():
        print(f"base-dir not found at {base_dir}", file=sys.stderr)
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            counts = reproject_from_jsonl(
                conn, base_dir,
                allow_empty=args.allow_empty_reproject,
                cascade_synthesis=args.cascade_synthesis,
            )
        except ReprojectBaseDirError as exc:
            print(f"reproject refused: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
        except ReprojectOrphansError as exc:
            print(f"reproject refused: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
    finally:
        conn.close()
    _emit_json({
        "db_path": str(db_path),
        "base_dir": str(base_dir),
        "reprojected": counts,
    })
    return exit_codes.OK


def cmd_state_migrate(args: argparse.Namespace) -> int:
    """Apply any pending migrations against an existing state DB.

    Behaves like ``hai state init`` but explicitly intended for upgrading an
    already-initialised DB. Idempotent — re-running against a DB already at
    head returns an empty applied list.
    """

    from health_agent_infra.core.state import (
        apply_pending_migrations,
        current_schema_version,
        detect_schema_version_gaps,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    conn = open_connection(db_path)
    try:
        # v0.1.7 (W23 / Codex r3 P2): refuse to migrate a DB with gaps
        # in the applied migration set. The legacy max-version skip
        # logic in `apply_pending_migrations` would silently no-op on
        # such a DB, leaving the gaps in place. Doctor warns about
        # gaps but doesn't repair them; migrate is the natural enforcer.
        gaps = detect_schema_version_gaps(conn)
        if gaps:
            print(
                f"hai state migrate: refusing to migrate a DB with "
                f"gaps in the applied migration set (missing versions: "
                f"{gaps}). The DB looks current by MAX(version) but is "
                f"missing schema objects from those versions. Restore "
                f"from a known-good backup or run `hai state init` "
                f"against a fresh DB. Re-run `hai doctor` to confirm.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
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
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai backup / restore / export — v0.1.14 W-BACKUP
# ---------------------------------------------------------------------------

def cmd_backup(args: argparse.Namespace) -> int:
    """Write a versioned backup tarball of state DB + JSONL audit logs.

    See ``docs/hai/backup_and_recovery.md`` for the recovery contract.
    """

    from datetime import datetime, timezone

    from health_agent_infra.core.backup import BackupError, make_backup
    from health_agent_infra.core.paths import resolve_base_dir
    from health_agent_infra.core.state import resolve_db_path
    from health_agent_infra import __version__ as _hai_version

    state_db_path = resolve_db_path(args.db_path)
    base_dir = resolve_base_dir(args.base_dir)

    if args.dest:
        dest = Path(args.dest).expanduser()
    else:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = Path.cwd() / f"hai-backup-{ts}.tar.gz"

    try:
        manifest = make_backup(
            state_db_path=state_db_path,
            base_dir=base_dir,
            dest=dest,
            hai_version=_hai_version,
        )
    except BackupError as exc:
        print(
            f"hai backup: {exc}. Run `hai state init` first if the state "
            f"DB does not exist, or check the --db-path / --base-dir flags.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    _emit_json({
        "dest": str(dest),
        "manifest": manifest.to_dict(),
    })
    return exit_codes.OK


def cmd_restore(args: argparse.Namespace) -> int:
    """Restore from a backup tarball; refuse on schema mismatch.

    Caller is responsible for backing up the destination state first
    if it has data — restore overwrites.
    """

    from health_agent_infra.core.backup import (
        BackupError,
        SchemaMismatchError,
        restore_backup,
    )
    from health_agent_infra.core.paths import resolve_base_dir
    from health_agent_infra.core.state import resolve_db_path
    from health_agent_infra.core.state.store import discover_migrations

    bundle_path = Path(args.bundle).expanduser()
    state_db_path = resolve_db_path(args.db_path)
    base_dir = resolve_base_dir(args.base_dir)

    # Compute the wheel's head schema version. If state DB exists, we
    # can read its current head; otherwise we use the highest migration
    # version we know about. Either way, we want the *expected* head
    # the installed wheel can serve.
    expected = max(version for version, _, _ in discover_migrations())

    try:
        manifest = restore_backup(
            bundle_path=bundle_path,
            state_db_path=state_db_path,
            base_dir=base_dir,
            expected_schema_version=expected,
        )
    except SchemaMismatchError as exc:
        print(
            f"hai restore: schema mismatch — {exc} Install the matching "
            f"wheel or run `hai state migrate` to bring the bundle's data "
            f"forward against an empty target.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    except BackupError as exc:
        print(
            f"hai restore: {exc}. Verify the bundle path and re-run.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    _emit_json({
        "bundle": str(bundle_path),
        "state_db_path": str(state_db_path),
        "base_dir": str(base_dir),
        "manifest": manifest.to_dict(),
        "restored_schema_version": manifest.schema_version,
    })
    return exit_codes.OK


def cmd_export(args: argparse.Namespace) -> int:
    """Emit a unified JSONL stream of every audit log under base_dir."""

    from health_agent_infra.core.backup import export_jsonl
    from health_agent_infra.core.paths import resolve_base_dir

    base_dir = resolve_base_dir(args.base_dir)

    if args.dest:
        dest = Path(args.dest).expanduser()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("w", encoding="utf-8") as fh:
            count = export_jsonl(base_dir=base_dir, output_stream=fh)
        _emit_json({
            "base_dir": str(base_dir),
            "dest": str(dest),
            "lines_written": count,
        })
    else:
        count = export_jsonl(base_dir=base_dir, output_stream=sys.stdout)
        # Stdout already streamed; don't emit a JSON summary.
        _ = count
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai sync purge — F-PV14-02 surgical sync_run_log cleanup
# ---------------------------------------------------------------------------
# Per W-29 boundary refresh §(d) OQ-1 disposition: the `hai sync ...`
# namespace co-locates with the state-handlers group rather than getting
# its own `cli/handlers/sync.py` module. F-PV14-02 ships the only
# subcommand in this namespace today.

def cmd_sync_purge(args: argparse.Namespace) -> int:
    """Surgically delete sync_run_log rows that match the selectors.

    Default-deny: refuses if more than 5 rows match the selector tuple.
    Writes a runtime_event_log audit row with the deleted-row payloads
    on commit. ``--dry-run`` is the inspection mode (read-only).

    Out-of-scope (per ``carry_over_findings.md`` §F-PV14-02):
      - Tables other than sync_run_log.
      - Selector-less invocations ("nuke all sync rows for source X").
      - The broader --db-path/--base-dir symmetry rule (deferred to
        v0.1.19 W-FPV14-SYM per v0.1.15 IR F-IR-02).
    """

    from health_agent_infra.core.state import resolve_db_path, open_connection
    from health_agent_infra.core.sync import (
        MAX_PURGE_ROWS,
        PurgeRefusedError,
        purge_sync_rows,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        sys.stderr.write(
            f"hai sync purge: state DB not found at {db_path}. "
            f"Run `hai state init` first.\n"
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            result = purge_sync_rows(
                conn,
                source=args.source,
                for_date=args.for_date,
                started_after=args.started_after,
                user_id=args.user_id,
                dry_run=args.dry_run,
            )
        except PurgeRefusedError as exc:
            sys.stderr.write(
                f"hai sync purge: {exc} "
                f"Run with --dry-run to inspect the matches first; "
                f"recommend `hai backup` before any non-dry-run purge.\n"
            )
            return exit_codes.USER_INPUT

        _emit_json({
            "source": args.source,
            "selectors": {
                "for_date": args.for_date,
                "started_after": args.started_after,
                "user_id": args.user_id,
            },
            "matched_rows": [r.to_dict() for r in result.matched],
            "matched_count": len(result.matched),
            "deleted_count": result.deleted_count,
            "dry_run": result.dry_run,
            "runtime_event_id": result.runtime_event_id,
            "safety_cap": MAX_PURGE_ROWS,
        })
        return exit_codes.OK
    finally:
        conn.close()
