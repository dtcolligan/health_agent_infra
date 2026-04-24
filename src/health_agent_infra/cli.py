"""`hai` CLI — thin subcommands over the deterministic runtime.

Subcommands:

    hai pull      — acquire Garmin evidence for a date, emit JSON
    hai clean     — normalize evidence into CleanedEvidence + RawSummary JSON
    hai propose   — append a DomainProposal to proposal_log
    hai synthesize — atomically commit the per-domain proposals as a daily plan
    hai review    — schedule review events, record outcomes, summarize history
    hai setup-skills — copy the packaged skills/ directory to ~/.claude/skills/

All judgment (state classification, policy, recommendation shaping) lives in
the markdown skills shipped with this package. This CLI is a tooling surface
for an agent to call; it does not reason about evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra import __version__ as _PACKAGE_VERSION
from health_agent_infra.core import exit_codes
from health_agent_infra.core.capabilities import (
    annotate_contract,
    build_manifest,
)
from health_agent_infra.core.capabilities.render import render_markdown
from health_agent_infra.core.clean import build_raw_summary, clean_inputs
from health_agent_infra.core.config import (
    ConfigError,
    load_thresholds,
    scaffold_thresholds_toml,
    user_config_path,
)
from health_agent_infra.domains.recovery import (
    classify_recovery_state,
    evaluate_recovery_policy,
)
from health_agent_infra.core.pull.auth import (
    CredentialStore,
    KeyringUnavailableError,
)
from health_agent_infra.core.pull.garmin import (
    GarminRecoveryReadinessAdapter,
    default_manual_readiness,
)
from health_agent_infra.core.pull.garmin_live import (
    GarminLiveAdapter,
    GarminLiveError,
    build_default_client,
)
from health_agent_infra.core.pull.intervals_icu import (
    IntervalsIcuAdapter,
    IntervalsIcuError,
    build_default_client as build_intervals_icu_client,
)
from health_agent_infra.core.review.outcomes import (
    ReLinkResolution,
    persist_review_event,
    record_review_outcome,
    resolve_review_relink,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    ReviewEvent,
    ReviewOutcome,
)


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
    source = _resolve_pull_source(args)
    # Mode still tracks csv vs live for sync_run_log — both live sources
    # share the "live" label so existing freshness checks don't need to
    # grow a new enum value.
    mode = "csv" if source == "csv" else "live"
    source_label = {
        "csv": GarminRecoveryReadinessAdapter.source_name,
        "garmin_live": "garmin_live",
        "intervals_icu": "intervals_icu",
    }[source]

    sync_id = _open_sync_row(
        getattr(args, "db_path", None),
        source=source_label,
        user_id=args.user_id,
        mode=mode,
        for_date=as_of,
    )

    if source == "csv":
        adapter = GarminRecoveryReadinessAdapter()
    elif source == "garmin_live":
        try:
            adapter = _build_live_adapter(args)
        except GarminLiveError as exc:
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(f"live pull error: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
    else:  # intervals_icu
        try:
            adapter = _build_intervals_icu_adapter(args)
        except IntervalsIcuError as exc:
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(f"intervals.icu pull error: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT

    try:
        pull = adapter.load(as_of)
    except (GarminLiveError, IntervalsIcuError) as exc:
        _close_sync_row_failed(args.db_path, sync_id, exc)
        print(f"live pull error: {exc}", file=sys.stderr)
        return exit_codes.TRANSIENT

    manual = None
    if args.manual_readiness_json:
        manual = json.loads(Path(args.manual_readiness_json).read_text(encoding="utf-8"))
    elif args.use_default_manual_readiness:
        manual = default_manual_readiness(as_of)
    else:
        # D2 §pull adapter integration: auto-read same-day
        # manual_readiness_raw when no explicit override is passed. The
        # --manual-readiness-json file path and --use-default-manual-readiness
        # flag both remain explicit overrides that win against the DB.
        manual = _autoread_manual_readiness(
            getattr(args, "db_path", None),
            user_id=args.user_id,
            as_of=as_of,
        )

    # rows_pulled: 1 if we got a daily summary row; 0 otherwise. This
    # maps "one logical day's evidence = one row" without pretending the
    # per-metric arrays are independent rows.
    rows = 1 if pull.get("raw_daily_row") is not None else 0
    # M6: the live adapter exposes partial-pull telemetry on its
    # instance so the pull dict's key set stays byte-identical to the
    # CSV adapter. The CSV adapter has no partial concept, so attribute
    # absence means "ok" by default.
    partial = getattr(adapter, "last_pull_partial", False)
    sync_status = "partial" if partial else "ok"
    _close_sync_row_ok(
        args.db_path,
        sync_id,
        rows_pulled=rows,
        rows_accepted=rows,
        duplicates_skipped=0,
        status=sync_status,
    )

    payload = {
        "as_of_date": as_of.isoformat(),
        "user_id": args.user_id,
        "source": adapter.source_name,
        "pull": pull,
        "manual_readiness": manual,
    }
    _emit_json(payload)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# Sync-log CLI shim — best-effort wrappers around core/state/sync_log
#
# All three helpers silently skip if the DB file is absent. Sync logging
# is lighter-weight telemetry than the accepted-state projections
# (which emit stderr warnings on failure) — an operator who hasn't run
# `hai state init` shouldn't see stderr noise every time they pull.
# ---------------------------------------------------------------------------


def _autoread_manual_readiness(
    db_path_arg,
    *,
    user_id: str,
    as_of: date,
) -> Optional[dict]:
    """Return the canonical same-day readiness row from the state DB, or None.

    Called by ``hai pull`` when neither ``--manual-readiness-json``
    nor ``--use-default-manual-readiness`` is set. Silent on DB-absent
    (pre-``hai state init`` users) and on pre-migration-015 DBs — the
    caller treats both as "no readiness to propagate."
    """

    from health_agent_infra.core.state import (
        open_connection,
        read_latest_manual_readiness,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return None
    conn = open_connection(db_path)
    try:
        return read_latest_manual_readiness(
            conn, user_id=user_id, as_of_date=as_of,
        )
    finally:
        conn.close()


def _open_sync_row(
    db_path_arg,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date,
):
    from health_agent_infra.core.state import (
        begin_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return None
    conn = open_connection(db_path)
    try:
        return begin_sync(
            conn,
            source=source,
            user_id=user_id,
            mode=mode,
            for_date=for_date,
        )
    except sqlite3.OperationalError:
        # Pre-migration-008 DB: skip quietly.
        return None
    finally:
        conn.close()


def _close_sync_row_ok(
    db_path_arg,
    sync_id,
    *,
    rows_pulled,
    rows_accepted,
    duplicates_skipped,
    status: str = "ok",
) -> None:
    if sync_id is None:
        return
    from health_agent_infra.core.state import (
        complete_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return
    conn = open_connection(db_path)
    try:
        complete_sync(
            conn,
            sync_id,
            rows_pulled=rows_pulled,
            rows_accepted=rows_accepted,
            duplicates_skipped=duplicates_skipped,
            status=status,
        )
    except sqlite3.OperationalError:
        return
    finally:
        conn.close()


def _close_sync_row_failed(db_path_arg, sync_id, exc: BaseException) -> None:
    if sync_id is None:
        return
    from health_agent_infra.core.state import (
        fail_sync,
        open_connection,
        resolve_db_path,
    )

    db_path = resolve_db_path(db_path_arg)
    if not db_path.exists():
        return
    conn = open_connection(db_path)
    try:
        fail_sync(
            conn,
            sync_id,
            error_class=type(exc).__name__,
            error_message=str(exc),
        )
    except sqlite3.OperationalError:
        return
    finally:
        conn.close()


def _sync_if_db(
    db_path_arg,
    *,
    source: str,
    user_id: str,
    mode: str,
    for_date=None,
):
    """Context manager: write a sync_run_log row if the DB exists, else no-op.

    Yields a mutable dict the caller fills in before exit
    (``run["rows_pulled"] = N`` etc.). Exceptions re-raise after the
    row is closed with ``fail_sync``. When the DB is absent or predates
    migration 008 the yielded dict has no ``sync_id`` and nothing is
    written.
    """

    from contextlib import contextmanager

    @contextmanager
    def _cm():
        sync_id = _open_sync_row(
            db_path_arg,
            source=source,
            user_id=user_id,
            mode=mode,
            for_date=for_date,
        )
        run: dict = {
            "sync_id": sync_id,
            "rows_pulled": None,
            "rows_accepted": None,
            "duplicates_skipped": None,
            "status": "ok",
        }
        try:
            yield run
        except Exception as exc:
            _close_sync_row_failed(db_path_arg, sync_id, exc)
            raise
        else:
            _close_sync_row_ok(
                db_path_arg,
                sync_id,
                rows_pulled=run.get("rows_pulled"),
                rows_accepted=run.get("rows_accepted"),
                duplicates_skipped=run.get("duplicates_skipped"),
                status=run.get("status", "ok"),
            )

    return _cm()


def _build_live_adapter(args: argparse.Namespace):
    """Resolve credentials → live client → adapter, or raise GarminLiveError.

    Pulled into a helper so tests can monkeypatch the client-building step
    while exercising the real CLI arg parsing and credential flow.

    M6: the adapter + client share a :class:`RetryConfig` derived from
    the merged thresholds. A user TOML ``[pull.garmin_live]`` section
    tunes attempts / backoff / rate-limit behavior without code edits.
    """

    from health_agent_infra.core.pull.garmin_live import (
        retry_config_from_thresholds,
    )

    store = CredentialStore.default()
    credentials = store.load_garmin()
    if credentials is None:
        raise GarminLiveError(
            "no Garmin credentials found. Run `hai auth garmin` or set "
            "HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD."
        )
    try:
        thresholds = load_thresholds()
    except ConfigError:
        # Malformed TOML is a config-level concern hai doctor surfaces;
        # for a pull, fall back to packaged defaults rather than failing.
        thresholds = None
    retry_cfg = retry_config_from_thresholds(thresholds)
    client = build_default_client(credentials, retry_config=retry_cfg)
    history_days = getattr(args, "history_days", 14)
    return GarminLiveAdapter(
        client=client,
        history_days=history_days,
        retry_config=retry_cfg,
    )


def _build_intervals_icu_adapter(args: argparse.Namespace) -> IntervalsIcuAdapter:
    """Resolve Intervals.icu credentials → client → adapter, or raise IntervalsIcuError."""

    store = CredentialStore.default()
    credentials = store.load_intervals_icu()
    if credentials is None:
        raise IntervalsIcuError(
            "no Intervals.icu credentials found. Run `hai auth intervals-icu` "
            "or set HAI_INTERVALS_ATHLETE_ID + HAI_INTERVALS_API_KEY."
        )
    client = build_intervals_icu_client(credentials)
    history_days = getattr(args, "history_days", 14)
    return IntervalsIcuAdapter(client=client, history_days=history_days)


def _resolve_pull_source(args: argparse.Namespace) -> str:
    """Pick the pull source: explicit --source beats legacy --live beats default csv."""

    explicit = getattr(args, "source", None)
    if explicit is not None:
        return explicit
    if getattr(args, "live", False):
        return "garmin_live"
    return "csv"


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
    return exit_codes.OK


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
    tables stayed empty — and unlike review, `hai clean` has no JSONL
    audit log, so there would be no reproject path.

    **Scope.** Only Garmin-sourced fields land here. Manual stress,
    nutrition, gym, notes flow through their own ``hai intake`` commands
    (7C) with their own raw-evidence tables; they never enter accepted
    state via ``hai clean``.

    **Fail-soft at the CLI boundary.** DB absent or transaction rolled back
    ⇒ stderr warning and return. stdout is unaffected. Same pattern as
    ``_dual_write_project``, adapted for the three-table recovery path.
    """

    from health_agent_infra.core.state import (
        open_connection,
        project_accepted_recovery_state_daily,
        project_accepted_running_state_daily,
        project_accepted_sleep_state_daily,
        project_accepted_stress_state_daily,
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
            project_accepted_sleep_state_daily(
                conn,
                as_of_date=as_of_date,
                user_id=user_id,
                raw_row=raw_row,
                source_row_ids=[source_row_id],
                commit_after=False,
            )
            project_accepted_stress_state_daily(
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


def _dual_write_project(db_path_arg, project_fn, label: str) -> None:
    """Run a projector against the resolved state DB.

    Fails soft: if the DB doesn't exist or the projector raises, we print a
    stderr warning and return. The JSONL write is the audit boundary; the DB
    is a queryable projection that ``hai state reproject`` can rebuild.
    ``project_fn`` receives the open connection.
    """

    from health_agent_infra.core.state import open_connection, resolve_db_path

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
            f"<base-dir>` to recover.",
            file=sys.stderr,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# hai auth garmin / hai auth status
# ---------------------------------------------------------------------------

def cmd_auth_garmin(args: argparse.Namespace) -> int:
    """Store Garmin credentials in the OS keyring.

    Non-interactive callers (agents, tests) supply ``--email`` and either
    ``--password-stdin`` (reads one password line from stdin) or the
    ``HAI_GARMIN_PASSWORD`` env var. Interactive callers are prompted via
    ``input()`` / ``getpass``. The password is never echoed or logged.
    """

    import getpass

    email = args.email
    password = None

    if args.password_stdin:
        password = sys.stdin.readline().rstrip("\n")
    elif args.password_env:
        password = os.environ.get(args.password_env)
        if not password:
            print(
                f"auth error: env var {args.password_env} is not set or empty",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    if email is None:
        try:
            email = input("Garmin email: ").strip()
        except EOFError:
            print("auth error: no email provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not email:
        print("auth error: email must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    if password is None:
        try:
            password = getpass.getpass("Garmin password: ")
        except EOFError:
            print("auth error: no password provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not password:
        print("auth error: password must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    store = _credential_store_for(args)
    try:
        store.store_garmin(email, password)
    except KeyringUnavailableError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except ValueError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    # Emit a non-secret confirmation. Email presence is fine to surface so
    # the operator sees which account was stored; password is never shown.
    _emit_json({
        "stored": True,
        "service": "garmin",
        "email": email,
        "backend": _backend_kind(store),
    })
    _print_keychain_acl_hint(store, service="Garmin")
    return exit_codes.OK


def cmd_auth_intervals_icu(args: argparse.Namespace) -> int:
    """Store Intervals.icu credentials in the OS keyring.

    Non-interactive callers supply ``--athlete-id`` and either
    ``--api-key-stdin`` or ``--api-key-env``. Interactive callers are
    prompted via ``input()`` / ``getpass``. The API key is never echoed.
    """

    import getpass

    athlete_id = args.athlete_id
    api_key = None

    if args.api_key_stdin:
        api_key = sys.stdin.readline().rstrip("\n")
    elif args.api_key_env:
        api_key = os.environ.get(args.api_key_env)
        if not api_key:
            print(
                f"auth error: env var {args.api_key_env} is not set or empty",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

    if athlete_id is None:
        try:
            athlete_id = input("Intervals.icu athlete id (e.g. i123456): ").strip()
        except EOFError:
            print("auth error: no athlete id provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not athlete_id:
        print("auth error: athlete id must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    if api_key is None:
        try:
            api_key = getpass.getpass("Intervals.icu API key: ")
        except EOFError:
            print("auth error: no API key provided", file=sys.stderr)
            return exit_codes.USER_INPUT
    if not api_key:
        print("auth error: API key must be non-empty", file=sys.stderr)
        return exit_codes.USER_INPUT

    store = _credential_store_for(args)
    try:
        store.store_intervals_icu(athlete_id, api_key)
    except KeyringUnavailableError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    except ValueError as exc:
        print(f"auth error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT

    _emit_json({
        "stored": True,
        "service": "intervals_icu",
        "athlete_id": athlete_id,
        "backend": _backend_kind(store),
    })
    _print_keychain_acl_hint(store, service="Intervals.icu")
    return exit_codes.OK


def _print_keychain_acl_hint(store, *, service: str) -> None:
    """Print a one-line stderr hint about macOS Keychain 'Always Allow'
    so users aren't surprised by the re-prompt each time ``hai pull
    --live`` wakes the keyring.

    Only fires when the backend is the macOS Keychain (``KeychainKeyring``
    class from the ``keyring`` package). Linux Secret Service + the
    in-memory test backend don't have this UX issue, so we don't clutter
    their stderr.
    """

    if _backend_kind(store) != "KeychainKeyring":
        return
    print(
        f"note: macOS will prompt the first time `hai pull --live` "
        f"reads the {service} credentials. Click 'Always Allow' so "
        f"subsequent pulls run without re-prompting.",
        file=sys.stderr,
    )


def cmd_auth_status(args: argparse.Namespace) -> int:
    """Report credential presence only — never prints secrets."""

    store = _credential_store_for(args)
    _emit_json({
        "backend": _backend_kind(store),
        "garmin": store.garmin_status(),
        "intervals_icu": store.intervals_icu_status(),
    })
    return exit_codes.OK


def _credential_store_for(args: argparse.Namespace) -> CredentialStore:
    # Tests set ``_credential_store_override`` via monkeypatching to inject
    # a backend; production falls through to the real keyring + env.
    override = getattr(args, "_credential_store_override", None)
    if override is not None:
        return override
    return CredentialStore.default()


def _backend_kind(store: CredentialStore) -> str:
    return type(store.backend).__name__


# ---------------------------------------------------------------------------
# hai propose — schema-validated DomainProposal persistence
# ---------------------------------------------------------------------------

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

    data = json.loads(Path(args.proposal_json).read_text(encoding="utf-8"))
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
    record = perform_proposal_writeback(data, base_dir=Path(args.base_dir))

    # DB projection: ProposalReplaceRequired is the one exception class
    # whose semantics demand a hard CLI failure rather than a stderr
    # warning. Every other projector exception stays best-effort.
    def _project(conn) -> None:
        try:
            project_proposal(conn, data, replace=args.replace)
        except ProposalReplaceRequired:
            # This should not happen after the pre-flight check above,
            # but guard for the thin race window (concurrent writer).
            # Re-raise so _dual_write_project surfaces it as a warning;
            # the user can rerun with --replace if appropriate.
            raise

    _dual_write_project(args.db_path, _project, "proposal")

    _emit_json(record.to_dict())
    return exit_codes.OK


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
        conn = open_connection(db_path)
        try:
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

    conn = open_connection(db_path)
    try:
        result = run_synthesis(
            conn,
            for_date=for_date,
            user_id=user_id,
            skill_drafts=skill_drafts,
            agent_version=args.agent_version,
            supersede=args.supersede,
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

def cmd_explain(args: argparse.Namespace) -> int:
    """Reconstruct the audit chain for a committed plan, read-only.

    Two key forms:

    - ``--daily-plan-id <id>`` returns the bundle for an exact plan,
      including ``_v<N>`` superseded variants.
    - ``--for-date <d> --user-id <u>`` returns the canonical plan for
      that key. The bundle's ``supersedes`` / ``superseded_by`` fields
      let a caller walk any supersession chain by reissuing
      ``hai explain --daily-plan-id``.

    Output is JSON by default (machine-readable for agents). Pass
    ``--text`` for the operator-facing report. Nothing in this command
    opens a write transaction.
    """

    from health_agent_infra.core.explain import (
        ExplainNotFoundError,
        bundle_to_dict,
        load_bundle_by_daily_plan_id,
        load_bundle_chain_for_date,
        load_bundle_for_date,
        render_bundle_text,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    if args.daily_plan_id and (args.for_date or args.user_id):
        print(
            "hai explain rejected: pass either --daily-plan-id OR "
            "(--for-date and --user-id), not both.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    if not args.daily_plan_id and not (args.for_date and args.user_id):
        print(
            "hai explain rejected: provide --daily-plan-id, or both "
            "--for-date and --user-id.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # --plan-version is ignored when an exact --daily-plan-id is given;
    # that form always returns the specified plan's bundle.
    if args.daily_plan_id and args.plan_version != "latest":
        print(
            "hai explain rejected: --plan-version is incompatible with "
            "--daily-plan-id; the id already pins the specific plan.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai explain requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            if args.daily_plan_id:
                bundle = load_bundle_by_daily_plan_id(
                    conn, daily_plan_id=args.daily_plan_id,
                )
                bundles = [bundle]
            elif args.plan_version == "all":
                bundles = load_bundle_chain_for_date(
                    conn,
                    for_date=date.fromisoformat(args.for_date),
                    user_id=args.user_id,
                )
            else:
                bundle = load_bundle_for_date(
                    conn,
                    for_date=date.fromisoformat(args.for_date),
                    user_id=args.user_id,
                    plan_version=args.plan_version,
                )
                bundles = [bundle]
        except ExplainNotFoundError as exc:
            # Well-formed request, no matching row — NOT_FOUND, not user-input.
            print(f"hai explain: {exc}", file=sys.stderr)
            return exit_codes.NOT_FOUND
    finally:
        conn.close()

    # D3: ``--operator`` is canonical; ``--text`` stays as a deprecated
    # alias until the next release. Either flag selects the operator
    # text report. Emit a deprecation hint on stderr when the alias is
    # used so scripts get a nudge during the deprecation window.
    if args.text and not args.operator:
        print(
            "hai explain: --text is deprecated; use --operator. "
            "The alias will be removed in a future release.",
            file=sys.stderr,
        )
    operator_output = args.operator or args.text

    if operator_output:
        for bundle in bundles:
            sys.stdout.write(render_bundle_text(bundle))
    else:
        if args.plan_version == "all" and not args.daily_plan_id:
            _emit_json([bundle_to_dict(b) for b in bundles])
        else:
            _emit_json(bundle_to_dict(bundles[0]))
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai today — user-facing narration of the canonical plan (D3)
# ---------------------------------------------------------------------------


def cmd_today(args: argparse.Namespace) -> int:
    """Render today's plan in plain language.

    Per D3 (``reporting/plans/v0_1_4/D3_user_surface.md``), ``hai today``
    is the non-agent-mediated user surface for reading the canonical
    plan. It reads the canonical leaf of the supersede chain via
    :func:`load_bundle_for_date` (D1) and renders six per-domain sections
    in the voice the ``reporting`` skill specifies.

    Exit code ``USER_INPUT`` when no plan exists for the target date —
    with a stderr hint pointing the user at ``hai daily`` to produce
    one. Stable output contract for snapshot tests: same plan in the DB
    → byte-identical stdout.
    """

    from health_agent_infra.core.explain import (
        ExplainNotFoundError,
        load_bundle_for_date,
    )
    from health_agent_infra.core.narration import DOMAIN_ORDER, render_today
    from health_agent_infra.core.state import open_connection, resolve_db_path

    if args.domain is not None and args.domain not in DOMAIN_ORDER:
        print(
            f"hai today: --domain {args.domain!r} not in {list(DOMAIN_ORDER)}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    # Format default: markdown when stdout is a TTY, plain otherwise.
    # Explicit flag wins.
    fmt = args.format
    if fmt is None:
        fmt = "markdown" if sys.stdout.isatty() else "plain"

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai today requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    as_of = _coerce_date(args.as_of)
    conn = open_connection(db_path)
    try:
        try:
            bundle = load_bundle_for_date(
                conn, for_date=as_of, user_id=args.user_id,
                plan_version="latest",
            )
        except ExplainNotFoundError:
            print(
                f"No plan for {as_of.isoformat()}. Run `hai daily` first.",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT

        # D4 cold-start flags — one counting query per domain, <1ms
        # on realistic DB sizes. Threaded into render_today so the
        # nutrition defer message + per-domain footer reflect the
        # user's actual history window. On a cold-start-clean user
        # the renderer silently behaves as pre-D4.
        from health_agent_infra.core.state.snapshot import _cold_start_flags
        cold_start_by_domain = _cold_start_flags(
            conn, user_id=args.user_id, as_of_date=as_of,
        )
    finally:
        conn.close()

    output = render_today(
        bundle,
        format=fmt,
        domain_filter=args.domain,
        cold_start_by_domain=cold_start_by_domain,
    )
    sys.stdout.write(output)
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai memory — explicit user-memory CRUD (Phase D)
# ---------------------------------------------------------------------------

def _memory_id_for(
    *,
    user_id: str,
    category: str,
    now: datetime,
) -> str:
    """Deterministic, sortable memory id: ``umem_<user>_<category>_<ts>``.

    Uses microsecond resolution so rapid reruns from a test or script
    don't collide. Callers may pass ``--memory-id`` to override for
    scripted reruns that want replay-idempotency.
    """

    suffix = now.strftime("%Y%m%dT%H%M%S%f")
    return f"umem_{user_id}_{category}_{suffix}"


def cmd_memory_set(args: argparse.Namespace) -> int:
    """Append one user-memory entry (goal / preference / constraint / context).

    Always inserts a fresh row — to change a preference the operator
    runs ``archive`` on the old entry and ``set`` for the replacement.
    This keeps the write surface honest: every change is visible as a
    distinct row + archive timestamp, no silent overwrites.
    """

    from health_agent_infra.core.memory import (
        UserMemoryEntry,
        UserMemoryValidationError,
        insert_memory_entry,
        validate_category,
    )
    from health_agent_infra.core.memory.schemas import (
        validate_domain,
        validate_value,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory set requires an initialized state DB; not found "
            f"at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    try:
        category = validate_category(args.category)
        validate_value(args.value)
        domain = validate_domain(args.domain)
    except UserMemoryValidationError as exc:
        print(
            f"hai memory set rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    now = datetime.now(timezone.utc)
    memory_id = args.memory_id or _memory_id_for(
        user_id=args.user_id, category=category, now=now,
    )
    entry = UserMemoryEntry(
        memory_id=memory_id,
        user_id=args.user_id,
        category=category,
        value=args.value,
        key=args.key,
        domain=domain,
        created_at=now,
        archived_at=None,
        source=args.source,
        ingest_actor=args.ingest_actor,
    )

    conn = open_connection(db_path)
    try:
        inserted = insert_memory_entry(conn, entry)
    finally:
        conn.close()

    _emit_json({
        "inserted": inserted,
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "category": entry.category,
        "key": entry.key,
        "value": entry.value,
        "domain": entry.domain,
        "created_at": entry.created_at.isoformat(),
        "archived_at": None,
        "source": entry.source,
        "ingest_actor": entry.ingest_actor,
    })
    return exit_codes.OK


def cmd_memory_list(args: argparse.Namespace) -> int:
    """List user-memory entries, optionally filtered by user / category.

    Emits a JSON object with ``entries`` (array) + ``counts`` (category
    totals). The default excludes archived rows; ``--include-archived``
    returns everything so an operator can audit their own memory
    history.
    """

    from health_agent_infra.core.memory import (
        UserMemoryValidationError,
        build_user_memory_bundle,
        list_memory_entries,
    )
    from health_agent_infra.core.memory.projector import bundle_to_dict
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory list requires an initialized state DB; not found "
            f"at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            if args.include_archived or args.category:
                # Raw list surface — supports category filter + archived.
                entries = list_memory_entries(
                    conn,
                    user_id=args.user_id,
                    category=args.category,
                    include_archived=args.include_archived,
                )
                payload = {
                    "user_id": args.user_id,
                    "category": args.category,
                    "include_archived": args.include_archived,
                    "entries": [_memory_entry_to_dict(e) for e in entries],
                    "counts": _memory_counts(entries),
                }
            else:
                # Default: active-now bundle. Matches the snapshot /
                # explain shape so the same consumer code can parse
                # both outputs.
                if args.user_id is None:
                    # Bundle surface needs a user_id; without it, fall
                    # back to the raw list with no filter.
                    entries = list_memory_entries(
                        conn, user_id=None, include_archived=False,
                    )
                    payload = {
                        "user_id": None,
                        "category": None,
                        "include_archived": False,
                        "entries": [_memory_entry_to_dict(e) for e in entries],
                        "counts": _memory_counts(entries),
                    }
                else:
                    bundle = build_user_memory_bundle(
                        conn, user_id=args.user_id, as_of=None,
                    )
                    payload = {
                        "user_id": args.user_id,
                        "category": None,
                        "include_archived": False,
                        **bundle_to_dict(bundle),
                    }
        except UserMemoryValidationError as exc:
            print(
                f"hai memory list rejected: invariant={exc.invariant}: {exc}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
    finally:
        conn.close()

    _emit_json(payload)
    return exit_codes.OK


def cmd_memory_archive(args: argparse.Namespace) -> int:
    """Soft-delete a user-memory entry by stamping ``archived_at``.

    Exits 2 when ``--memory-id`` is unknown. Re-archiving an already-
    archived entry is a no-op (returns ``archived=False``) — the CLI
    reports this honestly instead of erroring, since the desired end
    state is already satisfied.
    """

    from health_agent_infra.core.memory import (
        archive_memory_entry,
        read_memory_entry,
    )
    from health_agent_infra.core.state import open_connection, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai memory archive requires an initialized state DB; not "
            f"found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        existing = read_memory_entry(conn, memory_id=args.memory_id)
        if existing is None:
            print(
                f"hai memory archive: no entry with memory_id="
                f"{args.memory_id!r}",
                file=sys.stderr,
            )
            return exit_codes.USER_INPUT
        archived = archive_memory_entry(conn, memory_id=args.memory_id)
        refreshed = read_memory_entry(conn, memory_id=args.memory_id)
    finally:
        conn.close()

    payload = {
        "archived": archived,
        "memory_id": args.memory_id,
    }
    if refreshed is not None:
        payload["archived_at"] = (
            refreshed.archived_at.isoformat()
            if refreshed.archived_at else None
        )
    _emit_json(payload)
    return exit_codes.OK


def _memory_entry_to_dict(entry) -> dict[str, Any]:
    return {
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "category": entry.category,
        "key": entry.key,
        "value": entry.value,
        "domain": entry.domain,
        "created_at": entry.created_at.isoformat(),
        "archived_at": (
            entry.archived_at.isoformat() if entry.archived_at else None
        ),
        "source": entry.source,
        "ingest_actor": entry.ingest_actor,
    }


def _memory_counts(entries) -> dict[str, int]:
    from health_agent_infra.core.memory.schemas import USER_MEMORY_CATEGORIES

    out = {category: 0 for category in USER_MEMORY_CATEGORIES}
    for entry in entries:
        out[entry.category] = out.get(entry.category, 0) + 1
    out["total"] = len(entries)
    return out


# ---------------------------------------------------------------------------
# hai review
# ---------------------------------------------------------------------------

def cmd_review_schedule(args: argparse.Namespace) -> int:
    """Schedule a review event from a recommendation payload of any domain.

    The payload is parsed generically; ``hai propose`` / ``hai synthesize``
    is the validation boundary for recommendation shapes. Review
    scheduling trusts the already-persisted recommendation. ``domain``
    is read from the payload (falling back to ``"recovery"`` for v1 rows
    that pre-date the domain column).
    """

    from health_agent_infra.core.state import project_review_event

    data = json.loads(Path(args.recommendation_json).read_text(encoding="utf-8"))
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
    persist_review_event(event, base_dir=Path(args.base_dir))

    _dual_write_project(
        args.db_path,
        lambda conn: project_review_event(conn, event),
        "review event",
    )

    _emit_json(event.to_dict())
    return exit_codes.OK


def cmd_review_record(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import (
        open_connection,
        project_review_outcome,
        resolve_db_path,
    )

    data = json.loads(Path(args.outcome_json).read_text(encoding="utf-8"))
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
        base_dir=Path(args.base_dir),
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
    outcomes_path = Path(args.base_dir) / "review_outcomes.jsonl"
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

    base_dir = Path(args.base_dir).expanduser()

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

    from health_agent_infra.domains.strength.intake import deterministic_set_id
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
                        submission.session_id, s.set_number,
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
        try:
            inserted = project_exercise_taxonomy_entry(
                conn,
                exercise_id=row["exercise_id"],
                canonical_name=row["canonical_name"],
                aliases=row["aliases"],
                primary_muscle_group=row["primary_muscle_group"],
                secondary_muscle_groups=row["secondary_muscle_groups"],
                category=row["category"],
                equipment=row["equipment"],
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
        print("intake stress: --score must be one of {1,2,3,4,5}",
              file=sys.stderr)
        return exit_codes.USER_INPUT

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
        print("intake note: --text must be a non-empty string", file=sys.stderr)
        return exit_codes.USER_INPUT

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
    base_dir = Path(args.base_dir).expanduser()
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
        except ValueError as exc:
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

    base_dir = Path(args.base_dir)
    if not base_dir.exists():
        print(f"base-dir not found at {base_dir}", file=sys.stderr)
        return exit_codes.USER_INPUT

    conn = open_connection(db_path)
    try:
        try:
            counts = reproject_from_jsonl(
                conn, base_dir, allow_empty=args.allow_empty_reproject,
            )
        except ReprojectBaseDirError as exc:
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
# hai setup-skills
# ---------------------------------------------------------------------------


def _load_cleaned_bundle(path_str: str) -> tuple[dict, dict, Optional[str]]:
    """Load a `hai clean` output JSON. Returns (evidence, raw_summary, error)."""

    path = Path(path_str).expanduser()
    if not path.exists():
        return {}, {}, f"evidence-json not found at {path}"
    try:
        bundle = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {}, {}, f"evidence-json is not valid JSON ({exc})"
    if "cleaned_evidence" not in bundle or "raw_summary" not in bundle:
        return {}, {}, (
            "evidence-json missing cleaned_evidence or raw_summary; "
            "did you pass the output of `hai clean`?"
        )
    return bundle["cleaned_evidence"], bundle["raw_summary"], None


def cmd_config_init(args: argparse.Namespace) -> int:
    dest = Path(args.path).expanduser() if args.path else user_config_path()
    if dest.exists() and not args.force:
        print(
            f"config file already exists at {dest}; pass --force to overwrite",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(scaffold_thresholds_toml(), encoding="utf-8")
    _emit_json({"written": str(dest), "overwrote": bool(args.force and dest.exists())})
    return exit_codes.OK


def cmd_config_show(args: argparse.Namespace) -> int:
    path = Path(args.path).expanduser() if args.path else None
    try:
        merged = load_thresholds(path=path)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return exit_codes.USER_INPUT
    effective_path = path if path is not None else user_config_path()
    _emit_json({
        "source_path": str(effective_path),
        "source_exists": effective_path.exists(),
        "effective_thresholds": merged,
    })
    return exit_codes.OK


def cmd_exercise_search(args: argparse.Namespace) -> int:
    """Rank top taxonomy hits for a free-text exercise name.

    Code-owned ranking + scoring (see
    ``domains.strength.taxonomy_match``). The strength-intake skill
    calls this CLI when it needs to disambiguate a user-supplied
    exercise reference; the CLI surface never evaluates heuristics in
    markdown.

    Output shape::

        {
            "query": "<input>",
            "hits": [
                {
                    "exercise_id": "back_squat",
                    "canonical_name": "Back Squat",
                    "aliases": ["back squat", "squat", ...],
                    "primary_muscle_group": "quads",
                    "secondary_muscle_groups": ["glutes", "core"],
                    "category": "compound",
                    "equipment": "barbell",
                    "score": 100,
                    "match_reason": "exact_canonical"
                },
                ...
            ]
        }
    """

    from health_agent_infra.core.state import open_connection, resolve_db_path
    from health_agent_infra.domains.strength.taxonomy_match import (
        search_exercises,
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
        hits = search_exercises(args.query, conn=conn, limit=args.limit)
    finally:
        conn.close()

    _emit_json({
        "query": args.query,
        "hits": [
            {
                "exercise_id": h.exercise_id,
                "canonical_name": h.canonical_name,
                "aliases": list(h.aliases),
                "primary_muscle_group": h.primary_muscle_group,
                "secondary_muscle_groups": list(h.secondary_muscle_groups),
                "category": h.category,
                "equipment": h.equipment,
                "score": h.score,
                "match_reason": h.match_reason,
            }
            for h in hits
        ],
    })
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai daily — one-shot morning orchestration of the real runtime
# ---------------------------------------------------------------------------

# Six v1 domains. Kept in lockstep with
# ``core.writeback.proposal.SUPPORTED_DOMAINS``; duplicated here only so the
# CLI can validate the ``--domains`` flag without importing proposal.py at
# module import time (other subcommands resolve validator state lazily).
_DAILY_SUPPORTED_DOMAINS: frozenset[str] = frozenset({
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
})


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
) -> tuple[str, bool]:
    """Run the pull + state projection path ``hai pull`` + ``hai clean`` run.

    Reuses the adapters + ``_project_clean_into_state`` already shipped so
    ``hai daily`` does not duplicate acquisition or cleaning logic. No
    stdout emission (the outer command emits a single orchestration
    report). Returns ``(source_name, projected_raw_daily)``. Raises
    :class:`GarminLiveError` on failure so the caller can classify.
    """

    source = _resolve_pull_source(args)
    if source == "csv":
        adapter = GarminRecoveryReadinessAdapter()
    elif source == "garmin_live":
        adapter = _build_live_adapter(args)
    else:  # intervals_icu
        adapter = _build_intervals_icu_adapter(args)

    pull = adapter.load(as_of)
    raw_row = pull.get("raw_daily_row")
    if raw_row is not None:
        _project_clean_into_state(
            db_path,
            as_of_date=as_of,
            user_id=user_id,
            raw_row=raw_row,
        )
    return adapter.source_name, raw_row is not None


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
        rc = _run_daily(args)
        evt["exit_code"] = rc
    return rc


def _run_daily(args: argparse.Namespace) -> int:
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
    base_dir = Path(args.base_dir).resolve()
    base_dir.mkdir(parents=True, exist_ok=True)

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"hai daily requires an initialized state DB; not found at "
            f"{db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return exit_codes.USER_INPUT

    report: dict[str, Any] = {
        "as_of_date": as_of.isoformat(),
        "user_id": user_id,
        "base_dir": str(base_dir),
        "db_path": str(db_path),
        "expected_domains": sorted(expected_domains),
        "stages": {},
    }

    # Stage 1 + 2: pull + clean (skippable for offline / already-populated runs)
    if args.skip_pull:
        report["stages"]["pull"] = {"status": "skipped"}
        report["stages"]["clean"] = {"status": "skipped"}
    else:
        try:
            source_name, projected = _daily_pull_and_project(
                args, as_of=as_of, user_id=user_id, db_path=db_path,
            )
        except (GarminLiveError, IntervalsIcuError) as exc:
            report["stages"]["pull"] = {"status": "failed", "error": str(exc)}
            report["overall_status"] = "failed"
            _emit_json(report)
            return exit_codes.USER_INPUT
        report["stages"]["pull"] = {"status": "ran", "source": source_name}
        report["stages"]["clean"] = {
            "status": "ran" if projected else "no_raw_daily_row",
        }

    conn = open_connection(db_path)
    try:
        # Stage 3: snapshot — the cross-domain bundle the agent reads
        snapshot = build_snapshot(
            conn, as_of_date=as_of, user_id=user_id, lookback_days=14,
        )
        report["stages"]["snapshot"] = {
            "status": "ran",
            "domains_in_bundle": sorted(
                k for k in snapshot.keys() if k in _DAILY_SUPPORTED_DOMAINS
            ),
        }

        # Stage 4: proposal gate — honest check, no faking
        proposals = read_proposals_for_plan_key(
            conn, for_date=as_of.isoformat(), user_id=user_id,
        )
        present_domains = sorted({p["domain"] for p in proposals})
        missing_expected = sorted(set(expected_domains) - set(present_domains))
        gate_ok = bool(proposals)
        report["stages"]["proposal_gate"] = {
            "status": "complete" if gate_ok else "awaiting_proposals",
            "expected": sorted(expected_domains),
            "present": present_domains,
            "missing": missing_expected,
        }
        if not gate_ok:
            report["stages"]["synthesize"] = {
                "status": "skipped_awaiting_proposals",
                "hint": (
                    "Agent must post DomainProposal rows via `hai propose` "
                    "for the expected domains, then rerun `hai daily`."
                ),
            }
            report["stages"]["reviews"] = {"status": "skipped"}
            report["overall_status"] = "awaiting_proposals"
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


def cmd_setup_skills(args: argparse.Namespace) -> int:
    dest = Path(args.dest).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    copied: list[str] = []
    with _skills_source() as skills_source:
        if not skills_source.exists():
            print(f"skills/ not found at {skills_source}", file=sys.stderr)
            return exit_codes.USER_INPUT
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
    return exit_codes.OK


# ---------------------------------------------------------------------------
# hai init — first-run setup wizard (idempotent, non-interactive)
# ---------------------------------------------------------------------------


def cmd_init(args: argparse.Namespace) -> int:
    """First-run setup for the actual v1 product. Idempotent and safe to
    rerun.

    Three pieces of real v1 setup happen here, each re-using the same
    underlying surface the single-purpose subcommands call:

        1. Thresholds TOML (``hai config init`` path + scaffolder).
        2. State DB + migrations (``hai state init`` — creates file,
           applies any pending migration, no-op at head).
        3. Skills copied to the Claude skills directory (``hai
           setup-skills`` — skips existing unless ``--force``).

    Garmin credentials are reported as a status only. ``hai init`` stays
    non-interactive so agents and tests can drive it; the existing
    ``hai auth garmin`` command owns interactive credential entry.

    No nutrition / meal-level setup — v1 nutrition is macros-only and
    nothing here needs scaffolding per the Phase 2.5 retrieval gate.
    """

    from health_agent_infra.core.state import (
        current_schema_version,
        initialize_database,
        open_connection,
        resolve_db_path,
    )

    report: dict[str, Any] = {
        "version": _PACKAGE_VERSION,
        "steps": {},
    }

    # 1. thresholds TOML
    thresholds_path = (
        Path(args.thresholds_path).expanduser()
        if args.thresholds_path
        else user_config_path()
    )
    if thresholds_path.exists() and not args.force:
        report["steps"]["config"] = {
            "status": "already_present",
            "path": str(thresholds_path),
        }
    else:
        thresholds_path.parent.mkdir(parents=True, exist_ok=True)
        overwrote = thresholds_path.exists()
        thresholds_path.write_text(scaffold_thresholds_toml(), encoding="utf-8")
        report["steps"]["config"] = {
            "status": "overwrote" if overwrote else "created",
            "path": str(thresholds_path),
        }

    # 2. state DB + migrations
    db_path = resolve_db_path(args.db_path)
    db_existed_before = db_path.exists()
    version_before = 0
    if db_existed_before:
        conn = open_connection(db_path)
        try:
            version_before = current_schema_version(conn)
        finally:
            conn.close()
    resolved, applied = initialize_database(db_path)
    if not db_existed_before:
        db_status = "created"
    elif applied:
        db_status = "migrated"
    else:
        db_status = "already_at_head"
    report["steps"]["state_db"] = {
        "status": db_status,
        "path": str(resolved),
        "schema_version_before": version_before,
        "applied_migrations": [
            {"version": v, "filename": f} for v, f in applied
        ],
    }

    # 3. skills copy (idempotent unless --force)
    if args.skip_skills:
        report["steps"]["skills"] = {"status": "skipped"}
    else:
        dest = Path(args.skills_dest).expanduser()
        dest.mkdir(parents=True, exist_ok=True)
        copied: list[str] = []
        already: list[str] = []
        with _skills_source() as skills_source:
            if not skills_source.exists():
                report["steps"]["skills"] = {
                    "status": "failed",
                    "dest": str(dest),
                    "error": f"skills/ not found at {skills_source}",
                }
            else:
                for skill_dir in skills_source.iterdir():
                    if not skill_dir.is_dir():
                        continue
                    target = dest / skill_dir.name
                    if target.exists():
                        if not args.force:
                            already.append(str(target))
                            continue
                        shutil.rmtree(target)
                    shutil.copytree(skill_dir, target)
                    copied.append(str(target))
                report["steps"]["skills"] = {
                    "status": "ran",
                    "dest": str(dest),
                    "copied": copied,
                    "already_present": already,
                }

    # 4. Garmin auth — report presence only, never prompt. The operator
    # runs `hai auth garmin` separately for credential entry, or passes
    # --with-auth (step 5) for one-shot interactive onboarding.
    store = _credential_store_for(args)
    auth_status = store.garmin_status()
    configured = bool(auth_status["credentials_available"])
    report["steps"]["auth_garmin"] = {
        "status": "configured" if configured else "missing",
        "credentials_available": configured,
        "hint": (
            None
            if configured
            else (
                "run `hai auth garmin` to store credentials in the OS "
                "keyring, or pass --with-auth to prompt interactively, "
                "or set HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD for "
                "non-interactive use"
            )
        ),
    }

    # 5. optional: interactive Garmin auth. Off by default so agents and
    # tests can drive `hai init` non-interactively; opt in with --with-auth
    # for human onboarding.
    if getattr(args, "with_auth", False):
        report["steps"]["interactive_auth"] = _run_interactive_auth(
            args, already_configured=configured,
        )

    # 6. optional: first-pull today via the live adapter. One adapter call
    # (not a loop), `history_days`-wide window (default 1 → 5 API calls).
    # See _run_first_pull_backfill's docstring for why the 0.1.1 loop was
    # replaced.
    if getattr(args, "with_first_pull", False):
        # Re-check credentials: step 5 may have just populated them.
        store_now = _credential_store_for(args)
        creds_now = bool(store_now.garmin_status()["credentials_available"])
        report["steps"]["first_pull"] = _run_first_pull_backfill(
            args,
            db_path=resolved,
            user_id=getattr(args, "user_id", "u_local_1"),
            history_days=int(getattr(args, "history_days", 1) or 1),
            credentials_available=creds_now,
        )

    _emit_json(report)
    return exit_codes.OK


def _run_interactive_auth(
    args: argparse.Namespace, *, already_configured: bool,
) -> dict[str, Any]:
    """Prompt for Garmin credentials; hand them to ``cmd_auth_garmin``.

    Prompts are written by this wrapper (to stderr) rather than by
    ``cmd_auth_garmin``'s own ``input()`` / ``getpass()``. Reason: we
    redirect ``cmd_auth_garmin``'s stdout to suppress its JSON emission
    (so ``hai init`` stays a single-document stream), and Python's
    ``input()`` writes its prompt to stdout — which would get swallowed
    by the same redirect, leaving the user staring at a blank cursor.
    Routing prompts to stderr keeps them visible and leaves stdout
    unambiguous.

    The collected email + password are passed to ``cmd_auth_garmin`` via
    ``--email`` and ``--password-env`` so no further prompting happens
    downstream; the env var is scrubbed on exit.

    No-op if credentials are already present.
    """

    if already_configured:
        return {"status": "already_configured"}

    import getpass as _getpass
    import io
    import os as _os
    from contextlib import redirect_stdout

    sys.stderr.write("Garmin email: ")
    sys.stderr.flush()
    try:
        email = input().strip()
    except EOFError:
        return {"status": "user_skipped", "reason": "no input (EOF on email)"}
    if not email:
        return {"status": "user_skipped", "reason": "empty email"}
    try:
        password = _getpass.getpass("Garmin password: ")
    except EOFError:
        return {"status": "user_skipped", "reason": "no input (EOF on password)"}
    if not password:
        return {"status": "user_skipped", "reason": "empty password"}

    env_name = "_HAI_INIT_WITH_AUTH_PW"
    _os.environ[env_name] = password
    try:
        auth_args = argparse.Namespace(
            email=email,
            password_stdin=False,
            password_env=env_name,
            _credential_store_override=getattr(
                args, "_credential_store_override", None,
            ),
        )
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = cmd_auth_garmin(auth_args)
    finally:
        _os.environ.pop(env_name, None)

    if rc == exit_codes.OK:
        return {"status": "configured"}
    if rc == exit_codes.USER_INPUT:
        return {"status": "user_skipped", "exit_code": int(rc)}
    return {"status": "failed", "exit_code": int(rc)}


def _run_first_pull_backfill(
    args: argparse.Namespace,
    *,
    db_path: Path,
    user_id: str,
    history_days: int,
    credentials_available: bool,
) -> dict[str, Any]:
    """Pull + project today's state via a single live-adapter call.

    **Why one call, not a loop.** Each ``fetch_day`` makes ~5 Garmin
    API requests, and the adapter internally fetches a `history_days`
    window of days. So one ``adapter.load(today)`` with
    `history_days=1` = 5 requests; with the default `history_days=14`
    it's 70 requests. A multi-day backfill loop calling ``adapter.load``
    N times (the 0.1.1 design) produced N*5*14 requests — hundreds in a
    burst — which reliably triggered Garmin's rate limiter and left
    many users unable to complete setup.

    The replacement: one call, small default history window, explicit
    opt-in for larger. The historical-series arrays (resting_hr, hrv,
    training_load) come from the same call's history window, so wider
    windows still surface baseline context when the user wants it —
    they just incur a bigger burst.
    """

    if not credentials_available:
        return {
            "status": "skipped",
            "reason": (
                "no Garmin credentials available; run `hai auth garmin` "
                "(or pass --with-auth) before --with-first-pull"
            ),
        }
    if not db_path.exists():
        return {
            "status": "skipped",
            "reason": f"state DB not found at {db_path}",
        }
    if history_days < 1:
        return {
            "status": "skipped",
            "reason": f"invalid --history-days: {history_days}",
        }

    today = datetime.now(timezone.utc).date()

    # _daily_pull_and_project reads args.history_days when building the
    # live adapter, so routing the config through that attribute is how
    # the history window reaches the adapter without broadening the
    # helper's signature.
    pull_args = argparse.Namespace(
        live=True,
        db_path=str(db_path),
        user_id=user_id,
        history_days=history_days,
    )

    sync_id = _open_sync_row(
        db_path,
        source="garmin_live",
        user_id=user_id,
        mode="live",
        for_date=today,
    )
    try:
        source_name, projected = _daily_pull_and_project(
            pull_args, as_of=today, user_id=user_id, db_path=db_path,
        )
    except GarminLiveError as exc:
        _close_sync_row_failed(db_path, sync_id, exc)
        return {
            "status": "failed",
            "date": today.isoformat(),
            "history_days": history_days,
            "approx_api_calls": 5 * history_days,
            "error_class": type(exc).__name__,
            "error": str(exc),
            "hint": (
                "429 / rate-limit errors are common on Garmin's API. "
                "Wait 30–60 minutes before retrying; consider "
                "--history-days 1 (5 requests) to minimise burst size."
            ),
        }

    rows = 1 if projected else 0
    _close_sync_row_ok(
        db_path,
        sync_id,
        rows_pulled=rows,
        rows_accepted=rows,
        duplicates_skipped=0,
        status="ok",
    )
    return {
        "status": "ok",
        "date": today.isoformat(),
        "history_days": history_days,
        "approx_api_calls": 5 * history_days,
        "source": source_name,
        "projected_raw_daily": bool(projected),
    }


# ---------------------------------------------------------------------------
# hai doctor — read-only runtime diagnostics
# ---------------------------------------------------------------------------


def _worst_status(statuses: list[str]) -> str:
    order = {"ok": 0, "warn": 1, "fail": 2}
    if not statuses:
        return "ok"
    worst = max(order[s] for s in statuses)
    return {0: "ok", 1: "warn", 2: "fail"}[worst]


def cmd_doctor(args: argparse.Namespace) -> int:
    """Read-only diagnostics against the actual v1 runtime surfaces.

    Seven checks: config, state DB + schema version + size, Garmin
    credentials, skills install, domain registry, per-source sync
    freshness (from sync_run_log, M2), and today's proposal /
    recommendation / pending-review counts (M5).

    Default output is human-readable text. Pass ``--json`` for the
    structured dict an agent can parse.

    Exit code: 0 for ``ok`` or ``warn`` overall; 2 for ``fail``
    (malformed config on disk). ``warn`` is the normal pre-setup state
    so ``hai doctor && hai daily`` isn't blocked by a missing-auth
    warning.
    """

    from health_agent_infra.core.doctor import build_report, render_text
    from health_agent_infra.core.state import resolve_db_path

    thresholds_path = (
        Path(args.thresholds_path).expanduser()
        if args.thresholds_path
        else user_config_path()
    )
    db_path = resolve_db_path(args.db_path)
    skills_dest = Path(args.skills_dest).expanduser()

    with _skills_source() as skills_source:
        packaged_names = (
            sorted(p.name for p in skills_source.iterdir() if p.is_dir())
            if skills_source.exists()
            else []
        )

    as_of_date = _coerce_date(getattr(args, "as_of", None))

    report = build_report(
        version=_PACKAGE_VERSION,
        thresholds_path=thresholds_path,
        db_path=db_path,
        skills_dest=skills_dest,
        packaged_skill_names=packaged_names,
        domain_names=sorted(_DAILY_SUPPORTED_DOMAINS),
        credential_store=_credential_store_for(args),
        user_id=getattr(args, "user_id", "u_local_1"),
        as_of_date=as_of_date,
    )

    if getattr(args, "json", False):
        _emit_json(report.to_dict())
    else:
        sys.stdout.write(render_text(report))

    # doctor "fail" means a user-fixable state precondition (DB not
    # initialised, creds missing, etc.) — maps to USER_INPUT per the
    # exit-code taxonomy ("state precondition the caller controls").
    return exit_codes.USER_INPUT if report.overall_status == "fail" else exit_codes.OK


# ---------------------------------------------------------------------------
# hai stats — local, read-only onboarding + engagement signal
# ---------------------------------------------------------------------------


def cmd_stats(args: argparse.Namespace) -> int:
    """Summarise sync_run_log + runtime_event_log for the user's own DB.

    Read-only. Three sections:

      1. Sync freshness — last successful pull per source.
      2. Recent command runs — last N rows from runtime_event_log.
      3. Command + streak summary — counts per command, consecutive-day
         streak for `hai daily` (UTC calendar dates).

    Default output is human-readable text; pass ``--json`` for the
    structured dict. Text stays stable enough for eyeballing; JSON is
    the machine surface.

    No telemetry leaves the device — this command reads local SQLite
    only. The user can paste the JSON into a bug report; nothing here
    is auto-sent anywhere.
    """

    from health_agent_infra.core.state import (
        command_summary,
        latest_successful_sync_per_source,
        open_connection,
        recent_events,
        resolve_db_path,
    )

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        if getattr(args, "json", False):
            _emit_json({
                "db_path": str(db_path),
                "status": "db_missing",
                "hint": "run `hai init` to create the state DB",
            })
        else:
            print(
                f"hai stats: no state DB at {db_path}. "
                f"Run `hai init` first.",
                file=sys.stderr,
            )
        return exit_codes.USER_INPUT

    user_id = getattr(args, "user_id", "u_local_1")
    limit = max(1, int(getattr(args, "limit", 7) or 7))

    conn = open_connection(db_path)
    try:
        freshness = latest_successful_sync_per_source(conn, user_id=user_id)
        recent = recent_events(conn, limit=limit)
        summary = command_summary(conn)
        streak = _daily_streak_from_events(conn)
    finally:
        conn.close()

    # D4 #5 — cred-awareness. If a source's most recent successful
    # sync came from a live adapter and that adapter's credentials
    # are no longer present (user rotated keys, keyring reset,
    # migrated machines), mark the source's freshness entry as
    # `stale_credentials`. The sync timestamp itself stays accurate;
    # this is a UX hint that the next `hai pull --live` will fail.
    cred_store = _credential_store_for(args)
    cred_status_by_source = {
        "garmin_live": cred_store.garmin_status().get(
            "credentials_available", False,
        ),
        "intervals_icu": cred_store.intervals_icu_status().get(
            "credentials_available", False,
        ),
    }

    report: dict[str, Any] = {
        "db_path": str(db_path),
        "user_id": user_id,
        "sync_freshness": {
            source: {
                "started_at": row.get("started_at"),
                "completed_at": row.get("completed_at"),
                "status": (
                    "stale_credentials"
                    if (
                        source in cred_status_by_source
                        and cred_status_by_source[source] is False
                        and row.get("status") == "ok"
                    )
                    else row.get("status")
                ),
                "credentials_available": cred_status_by_source.get(source),
                "for_date": row.get("for_date"),
                "mode": row.get("mode"),
            }
            for source, row in freshness.items()
        },
        "recent_events": [
            {
                "event_id": r["event_id"],
                "command": r["command"],
                "started_at": r["started_at"],
                "completed_at": r["completed_at"],
                "status": r["status"],
                "exit_code": r["exit_code"],
                "duration_ms": r["duration_ms"],
                "error_class": r["error_class"],
                "error_message": r["error_message"],
            }
            for r in recent
        ],
        "command_summary": summary,
        "daily_streak_days": streak,
    }

    if getattr(args, "json", False):
        _emit_json(report)
    else:
        sys.stdout.write(_render_stats_text(report))
    return exit_codes.OK


def _daily_streak_from_events(conn: sqlite3.Connection) -> int:
    """Consecutive UTC calendar days ending today with ≥1 successful `hai daily`.

    Returns 0 if today doesn't have a successful run. The streak is
    counted backward from today (inclusive) — missing any intervening
    day breaks the chain. Robust to a pre-migration-012 DB: returns 0
    rather than crashing.
    """

    try:
        rows = conn.execute(
            "SELECT DISTINCT substr(started_at, 1, 10) AS day "
            "FROM runtime_event_log "
            "WHERE command = 'daily' AND status = 'ok' "
            "ORDER BY day DESC"
        ).fetchall()
    except sqlite3.OperationalError:
        return 0

    days_with_ok = {row["day"] for row in rows}
    if not days_with_ok:
        return 0

    streak = 0
    today = datetime.now(timezone.utc).date()
    cursor = today
    while cursor.isoformat() in days_with_ok:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def _render_stats_text(report: dict[str, Any]) -> str:
    """Human-readable `hai stats` view. Stable enough for eyeballing."""

    lines: list[str] = []
    lines.append(f"hai stats  —  db: {report['db_path']}")
    lines.append(f"             user: {report['user_id']}")
    lines.append("")

    # Sync freshness
    lines.append("Sync freshness (last successful pull per source):")
    fresh = report["sync_freshness"]
    if not fresh:
        lines.append("  (no successful syncs yet — run `hai pull --live` or `hai daily`)")
    else:
        for source in sorted(fresh):
            row = fresh[source]
            started = row.get("started_at") or "—"
            for_date = row.get("for_date") or ""
            suffix = f"  for {for_date}" if for_date else ""
            lines.append(f"  {source:16s} {started}  {row.get('status'):<8s}{suffix}")
    lines.append("")

    # Recent events
    lines.append(f"Recent runs (runtime_event_log, last {len(report['recent_events'])}):")
    events = report["recent_events"]
    if not events:
        lines.append("  (no logged runs yet — `hai daily` starts recording once the DB exists)")
    else:
        for evt in events:
            started = evt.get("started_at") or "—"
            cmd = evt.get("command", "?")
            status = evt.get("status", "?")
            dur = evt.get("duration_ms")
            dur_s = f"{dur} ms" if dur is not None else "—"
            line = f"  {started}  {cmd:<8s} {status:<6s} {dur_s:>8s}"
            if evt.get("error_class"):
                line += f"   {evt['error_class']}: {evt.get('error_message', '')}"
            lines.append(line)
    lines.append("")

    # Command summary + streak
    lines.append("Command summary:")
    summary = report["command_summary"]
    if not summary:
        lines.append("  (no commands logged yet)")
    else:
        for cmd in sorted(summary):
            counts = summary[cmd]
            lines.append(
                f"  {cmd:<10s} ok: {counts.get('ok', 0):<4d} "
                f"failed: {counts.get('failed', 0):<4d} "
                f"total: {counts.get('total', 0)}"
            )
    lines.append("")

    streak = report["daily_streak_days"]
    streak_suffix = " (run `hai daily` today to start one)" if streak == 0 else ""
    lines.append(f"Daily streak: {streak} day(s){streak_suffix}")
    lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------


def _register_eval_subparser(sub: argparse._SubParsersAction) -> None:
    """Register ``hai eval`` against the packaged eval framework.

    The framework lives inside the wheel at
    ``health_agent_infra.evals`` (runner + cli + scenarios + rubrics
    as package data). Registration is unconditional — the same surface
    is available in source checkouts and wheel installs.
    """

    from health_agent_infra.evals.cli import register_eval_subparser

    register_eval_subparser(sub)


# ---------------------------------------------------------------------------
# hai capabilities — emit the agent contract manifest
# ---------------------------------------------------------------------------


def cmd_capabilities(args: argparse.Namespace) -> int:
    """Emit the agent-CLI-contract manifest as JSON or markdown.

    The manifest is built by walking the very parser the user just
    invoked, so the output reflects the exact CLI surface this process
    exposes — no risk of the manifest describing a different build.
    """

    manifest = build_manifest(build_parser())
    if getattr(args, "markdown", False):
        # Text form for operator-facing review; the --json form stays the
        # canonical machine-readable surface.
        print(render_markdown(manifest), end="")
    else:
        _emit_json(manifest)
    return exit_codes.OK


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hai", description="Health Agent Infra CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"hai {_PACKAGE_VERSION}",
        help="Print the installed package version and exit",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_pull = sub.add_parser("pull", help="Pull Garmin evidence for a date")
    p_pull.add_argument("--date", default=None, help="As-of date, ISO-8601 (default today UTC)")
    p_pull.add_argument("--user-id", default="u_local_1")
    p_pull.add_argument("--manual-readiness-json", default=None,
                        help="Path to a JSON file with manual readiness fields")
    p_pull.add_argument("--use-default-manual-readiness", action="store_true",
                        help="Use a neutral manual readiness default (for offline runs)")
    p_pull.add_argument("--live", action="store_true",
                        help="Legacy flag: equivalent to --source garmin_live. "
                             "Default (no --live and no --source) reads the "
                             "committed CSV export.")
    p_pull.add_argument(
        "--source",
        choices=("csv", "garmin_live", "intervals_icu"),
        default=None,
        help="Evidence source. csv reads the committed fixture; garmin_live "
             "scrapes Garmin Connect (rate-limited, unreliable); "
             "intervals_icu pulls from Intervals.icu's wellness API — "
             "stable and the best live option today, but scoped to "
             "what that service exposes (HRV + RHR + sleep + load; no "
             "per-session running granularity yet). Defaults to csv "
             "unless --live is also set.",
    )
    p_pull.add_argument("--history-days", type=int, default=14,
                        help="Trailing window size for resting_hr / hrv / "
                             "training_load series (live pull only). Matches "
                             "the CSV adapter default.")
    p_pull.add_argument("--db-path", default=None,
                        help="State DB path for sync_run_log writes. Best-effort — "
                             "if the DB is absent, the pull still runs but the "
                             "sync row is skipped. Default: `$HAI_STATE_DB` or "
                             "`~/.local/share/health_agent_infra/state.db`.")
    p_pull.set_defaults(func=cmd_pull)
    annotate_contract(
        p_pull,
        mutation="writes-sync-log",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT", "TRANSIENT"),
        agent_safe=True,
        description=(
            "Acquire Garmin evidence (CSV fixture by default, live via "
            "--live) for a date and emit cleaned evidence JSON. Writes a "
            "sync_run_log row; does not touch the main state tables."
        ),
    )

    p_auth = sub.add_parser("auth", help="Credential management for external sources")
    auth_sub = p_auth.add_subparsers(dest="auth_command", required=True)

    p_auth_garmin = auth_sub.add_parser(
        "garmin",
        help="Store Garmin credentials in the OS keyring (interactive by default)",
    )
    p_auth_garmin.add_argument("--email", default=None,
                               help="Garmin account email (prompts if omitted)")
    p_auth_garmin.add_argument("--password-stdin", action="store_true",
                               help="Read the Garmin password from a single "
                                    "line on stdin (for non-interactive use)")
    p_auth_garmin.add_argument("--password-env", default=None,
                               help="Read the Garmin password from the named "
                                    "environment variable")
    p_auth_garmin.set_defaults(func=cmd_auth_garmin)
    annotate_contract(
        p_auth_garmin,
        mutation="writes-credentials",
        idempotent="yes",  # replacing stored credentials with same pair is a no-op
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,  # interactive password prompt
        description=(
            "Store Garmin credentials in the OS keyring. Interactive by "
            "default; operator-only (requires a live password)."
        ),
    )

    p_auth_intervals_icu = auth_sub.add_parser(
        "intervals-icu",
        help="Store Intervals.icu credentials in the OS keyring (interactive by default)",
    )
    p_auth_intervals_icu.add_argument("--athlete-id", default=None,
                                      help="Intervals.icu athlete id (prompts if omitted)")
    p_auth_intervals_icu.add_argument("--api-key-stdin", action="store_true",
                                      help="Read the Intervals.icu API key from a "
                                           "single line on stdin (for non-interactive use)")
    p_auth_intervals_icu.add_argument("--api-key-env", default=None,
                                      help="Read the Intervals.icu API key from the "
                                           "named environment variable")
    p_auth_intervals_icu.set_defaults(func=cmd_auth_intervals_icu)
    annotate_contract(
        p_auth_intervals_icu,
        mutation="writes-credentials",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,
        description=(
            "Store Intervals.icu credentials in the OS keyring. "
            "Interactive by default; operator-only (requires a live API key)."
        ),
    )

    p_auth_status = auth_sub.add_parser(
        "status",
        help="Report whether credentials are configured (presence only, no secrets)",
    )
    p_auth_status.set_defaults(func=cmd_auth_status)
    annotate_contract(
        p_auth_status,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Report whether Garmin and Intervals.icu credentials are "
            "configured. Presence only — never emits the secret itself."
        ),
    )

    p_clean = sub.add_parser("clean", help="Normalize pulled evidence + raw summary")
    p_clean.add_argument("--evidence-json", required=True,
                         help="Path to a JSON file produced by `hai pull`")
    p_clean.add_argument("--db-path", default=None,
                         help="State DB path (default: $HAI_STATE_DB or platform default). "
                              "If the DB is absent, projection is skipped with a stderr note; "
                              "stdout is unchanged.")
    p_clean.set_defaults(func=cmd_clean)
    annotate_contract(
        p_clean,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Normalize pulled evidence into CleanedEvidence + RawSummary "
            "JSON and project accepted state rows. Best-effort projection "
            "when --db-path is absent."
        ),
    )

    p_prop = sub.add_parser(
        "propose",
        help="Validate and persist a DomainProposal JSON to proposal_log",
    )
    # Source choices from the validator's SUPPORTED_DOMAINS so the
    # parser and the invariant can never drift — any new supported
    # domain appears here automatically.
    from health_agent_infra.core.writeback.proposal import (
        SUPPORTED_DOMAINS as _PROPOSAL_DOMAINS,
    )
    p_prop.add_argument("--domain", required=True,
                        choices=sorted(_PROPOSAL_DOMAINS),
                        help="Domain whose proposal is being written")
    p_prop.add_argument("--proposal-json", required=True,
                        help="Path to a JSON file matching DomainProposal shape")
    p_prop.add_argument("--base-dir", required=True,
                        help="Writeback root; <domain>_proposals.jsonl will be appended here")
    p_prop.add_argument("--db-path", default=None,
                        help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_prop.add_argument(
        "--replace", action="store_true", default=False,
        help=(
            "Revise an existing canonical proposal for "
            "(for_date, user_id, domain). Without --replace, a second "
            "propose for the same chain key exits USER_INPUT. With "
            "--replace, a new revision is inserted and the prior leaf's "
            "superseded_by_proposal_id is updated in a single "
            "transaction. If the new payload is byte-identical to the "
            "current leaf, --replace is a no-op. "
            "See reporting/plans/v0_1_4/D1_re_author_semantics.md."
        ),
    )
    p_prop.set_defaults(func=cmd_propose)
    annotate_contract(
        p_prop,
        mutation="writes-state",
        idempotent="yes-with-replace",  # revision chain under --replace
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Validate a DomainProposal and append it to proposal_log. "
            "One of the three determinism boundaries the runtime "
            "enforces."
        ),
        preconditions=[
            "state_db_initialized",
            "proposal_json_validates_against_domain_schema",
        ],
        output_schema={
            "OK": {
                "shape": "JSON confirmation of the persisted proposal.",
                "json_keys": [
                    "proposal_id", "domain", "for_date", "user_id",
                    "revision", "superseded_by_proposal_id",
                ],
                "notes": (
                    "revision=1 on first-write; >1 after --replace. "
                    "superseded_by_proposal_id is NULL on the canonical "
                    "leaf."
                ),
            },
        },
    )

    p_syn = sub.add_parser(
        "synthesize",
        help="Read proposals + snapshot, run X-rules, atomically commit daily_plan + recommendations + firings",
    )
    p_syn.add_argument("--as-of", required=True,
                       help="Civil date to synthesize for, ISO-8601 YYYY-MM-DD")
    p_syn.add_argument("--user-id", required=True,
                       help="User whose proposals to reconcile")
    p_syn.add_argument("--drafts-json", default=None,
                       help="Optional JSON array of skill-authored draft recommendations. "
                            "When present, overlays rationale + uncertainty + review_question "
                            "onto the mechanical drafts. action / action_detail / confidence "
                            "are runtime-owned after Phase A and cannot be changed by the skill.")
    p_syn.add_argument("--supersede", action="store_true",
                       help="Keep the prior canonical plan and write a fresh suffixed "
                            "plan id. Default is atomic replacement.")
    p_syn.add_argument("--bundle-only", action="store_true",
                       help="Emit the synthesis bundle (snapshot + proposals + "
                            "Phase A firings) as JSON and exit. Read-only — "
                            "does not commit. This is the skill seam: the "
                            "daily-plan-synthesis skill reads the bundle, "
                            "composes a rationale overlay, and feeds it back "
                            "via a second call with --drafts-json.")
    p_syn.add_argument("--agent-version", default="claude_agent_v1",
                       help="Agent version string to record on every row "
                            "(not part of the canonical plan idempotency key)")
    p_syn.add_argument("--db-path", default=None,
                       help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_syn.set_defaults(func=cmd_synthesize)
    annotate_contract(
        p_syn,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT", "INTERNAL"),
        agent_safe=True,
        description=(
            "Run synthesis end-to-end inside one atomic SQLite "
            "transaction: daily_plan + x_rule_firings + "
            "planned_recommendation + recommendation_log. --supersede "
            "versions the plan instead of replacing it."
        ),
        preconditions=[
            "state_db_initialized",
            "proposal_log_has_row_for_each_target_domain",
            "state_snapshot_available_for_as_of",
        ],
        output_schema={
            "OK": {
                "shape": "JSON SynthesisResult confirmation.",
                "json_keys": [
                    "daily_plan_id", "recommendation_ids",
                    "proposal_ids", "phase_a_firings",
                    "phase_b_firings", "superseded_prior",
                ],
                "notes": (
                    "superseded_prior is NULL on canonical-replace "
                    "commits and set to the prior leaf's daily_plan_id "
                    "when --supersede was passed."
                ),
            },
        },
    )

    p_explain = sub.add_parser(
        "explain",
        help=(
            "Read-only audit-chain reconstruction for a committed plan: "
            "proposals, X-rule firings, final recommendations, "
            "supersession linkage, and review records."
        ),
    )
    p_explain.add_argument(
        "--daily-plan-id", default=None,
        help="Exact plan id to explain (e.g. 'plan_2026-04-17_u_local_1' "
             "or its '_v<N>' supersession variants). Mutually exclusive "
             "with --for-date / --user-id.",
    )
    p_explain.add_argument(
        "--for-date", default=None,
        help="Civil date of the canonical plan to explain, ISO-8601. "
             "Pair with --user-id.",
    )
    p_explain.add_argument(
        "--user-id", default=None,
        help="User whose canonical plan to explain. Pair with --for-date.",
    )
    # D3 §hai explain --operator — the dense text report is an operator/
    # debug surface, distinct from the user-facing ``hai today``. The
    # canonical flag is ``--operator`` as of v0.1.4; ``--text`` stays as
    # a deprecated alias for one release cycle so scripts don't break
    # mid-upgrade.
    p_explain.add_argument(
        "--operator", action="store_true",
        help="Render the bundle as a dense plain-text operator report "
             "instead of JSON. For end-user prose, use `hai today`.",
    )
    p_explain.add_argument(
        "--text", action="store_true",
        help="Deprecated alias for --operator. Will be removed in a "
             "future release; update scripts to use --operator.",
    )
    p_explain.add_argument(
        "--plan-version",
        choices=("latest", "first", "all"),
        default="latest",
        help=(
            "Which plan in a supersede chain to explain when "
            "--for-date is used. 'latest' (default) resolves the "
            "canonical leaf. 'first' returns the chain head. 'all' "
            "emits the full chain as a JSON array (or sequential "
            "text blocks with --text). Incompatible with "
            "--daily-plan-id, which already pins a specific plan. "
            "See reporting/plans/v0_1_4/D1_re_author_semantics.md."
        ),
    )
    p_explain.add_argument("--db-path", default=None,
                           help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_explain.set_defaults(func=cmd_explain)
    annotate_contract(
        p_explain,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-out",  # JSON default; --operator (or deprecated --text) suppresses
        exit_codes=("OK", "USER_INPUT", "NOT_FOUND"),
        agent_safe=True,
        description=(
            "Reconstruct the full audit chain (planned / adapted / "
            "firings / performed) for a committed plan. Strictly "
            "read-only — never recomputes runtime state."
        ),
    )

    p_today = sub.add_parser(
        "today",
        help=(
            "Read today's plan in plain language. First-class non-agent-"
            "mediated user surface — no SQLite reading required."
        ),
    )
    p_today.add_argument(
        "--as-of", default=None,
        help="Civil date to read, ISO-8601. Default: today UTC.",
    )
    p_today.add_argument(
        "--user-id", default="u_local_1",
        help="User whose plan to read (default: u_local_1).",
    )
    p_today.add_argument(
        "--format", default=None, choices=("markdown", "plain", "json"),
        help=(
            "Output format. Defaults to 'markdown' on a TTY, 'plain' "
            "otherwise. 'json' emits the structured section shape."
        ),
    )
    p_today.add_argument(
        "--domain", default=None,
        choices=("recovery", "running", "sleep", "strength", "stress", "nutrition"),
        help="Narrow output to a single domain section.",
    )
    p_today.add_argument(
        "--db-path", default=None,
        help="State DB path (same semantics as other state commands).",
    )
    p_today.set_defaults(func=cmd_today)
    annotate_contract(
        p_today,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # markdown/plain default; --format json opts in
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Render today's canonical plan in plain language — the "
            "non-agent-mediated user surface. Read-only."
        ),
        preconditions=[
            "state_db_initialized",
            "daily_plan_exists_for_as_of",
        ],
        output_schema={
            "OK": {
                "shape": "one of markdown|plain text (default) or a JSON "
                         "object with top_matter + summary + sections[].",
                "json_keys": [
                    "as_of_date", "user_id", "daily_plan_id",
                    "top_matter", "summary", "sections",
                ],
                "notes": "JSON format only emitted when --format json.",
            },
        },
    )

    # --- hai memory (Phase D) ---
    from health_agent_infra.core.memory.schemas import USER_MEMORY_CATEGORIES

    p_memory = sub.add_parser(
        "memory",
        help=(
            "Explicit user memory — goals, preferences, constraints, "
            "and durable context notes. Local SQLite state, read by "
            "`hai state snapshot` and `hai explain`."
        ),
    )
    memory_sub = p_memory.add_subparsers(dest="memory_command", required=True)

    p_mset = memory_sub.add_parser(
        "set",
        help="Append one user-memory entry (append-only; use `archive` "
             "+ `set` to replace).",
    )
    p_mset.add_argument(
        "--category", required=True,
        choices=sorted(USER_MEMORY_CATEGORIES),
        help="Memory kind: goal | preference | constraint | context.",
    )
    p_mset.add_argument(
        "--value", required=True,
        help="Durable content (e.g. 'build strength through June', "
             "'no early-morning hard runs'). Non-empty.",
    )
    p_mset.add_argument(
        "--key", default=None,
        help="Optional short handle within the category "
             "(e.g. 'primary_goal', 'injury_left_knee').",
    )
    p_mset.add_argument(
        "--domain", default=None,
        help="Optional scoping domain (recovery | running | sleep | "
             "stress | strength | nutrition). Global if omitted.",
    )
    p_mset.add_argument(
        "--user-id", default="u_local_1",
        help="User the memory attaches to (default: u_local_1).",
    )
    p_mset.add_argument(
        "--memory-id", default=None,
        help="Optional explicit memory_id (default: "
             "deterministic `umem_<user>_<category>_<timestamp>`).",
    )
    p_mset.add_argument(
        "--source", default="user_manual",
        help="Fact origin (default: user_manual).",
    )
    p_mset.add_argument(
        "--ingest-actor", default="hai_cli_direct",
        choices=("hai_cli_direct", "claude_agent_v1"),
        help="Transport identity (default: hai_cli_direct).",
    )
    p_mset.add_argument(
        "--db-path", default=None,
        help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`).",
    )
    p_mset.set_defaults(func=cmd_memory_set)
    annotate_contract(
        p_mset,
        mutation="writes-memory",
        idempotent="no",  # append-only user_memory rows
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Append a user_memory entry (goal / preference / constraint "
            "/ context). Append-only — replace by archiving the old row "
            "and setting a new one."
        ),
    )

    p_mlist = memory_sub.add_parser(
        "list",
        help="List user-memory entries (active only by default).",
    )
    p_mlist.add_argument(
        "--user-id", default=None,
        help="Restrict to one user (default: every user).",
    )
    p_mlist.add_argument(
        "--category", default=None,
        choices=sorted(USER_MEMORY_CATEGORIES),
        help="Restrict to one category (default: every category).",
    )
    p_mlist.add_argument(
        "--include-archived", action="store_true",
        help="Also return archived entries (default: exclude).",
    )
    p_mlist.add_argument("--db-path", default=None)
    p_mlist.set_defaults(func=cmd_memory_list)
    annotate_contract(
        p_mlist,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "List user_memory entries active at a given date, grouped "
            "by category."
        ),
    )

    p_march = memory_sub.add_parser(
        "archive",
        help="Stamp `archived_at` on an active entry. Soft-delete; the "
             "row stays on disk so `list --include-archived` can audit.",
    )
    p_march.add_argument(
        "--memory-id", required=True,
        help="Memory id to archive.",
    )
    p_march.add_argument("--db-path", default=None)
    p_march.set_defaults(func=cmd_memory_archive)
    annotate_contract(
        p_march,
        mutation="writes-memory",
        idempotent="yes",  # re-archiving an already-archived row is a no-op
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Mark a user_memory entry archived (soft delete). The row "
            "itself stays for audit; read surfaces filter it out."
        ),
    )

    p_review = sub.add_parser("review", help="Review scheduling + outcome persistence")
    review_sub = p_review.add_subparsers(dest="review_command", required=True)

    p_rs = review_sub.add_parser("schedule", help="Persist a pending review event for a recommendation")
    p_rs.add_argument("--recommendation-json", required=True)
    p_rs.add_argument("--base-dir", required=True)
    p_rs.add_argument("--db-path", default=None,
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_rs.set_defaults(func=cmd_review_schedule)
    annotate_contract(
        p_rs,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Persist a pending review_event for a recommendation "
            "(used to schedule the next-day review question)."
        ),
    )

    p_rr = review_sub.add_parser("record", help="Record a review outcome")
    p_rr.add_argument("--outcome-json", required=True)
    p_rr.add_argument("--base-dir", required=True)
    p_rr.add_argument("--db-path", default=None,
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    # M4 enrichment flags. All optional; each overrides the same key in
    # --outcome-json when both are provided. Omitted flags + JSON-absent
    # fields land NULL in the DB, which is the pre-M4 shape.
    p_rr.add_argument(
        "--completed", choices=("yes", "no"), default=None,
        help="Whether the user completed the recommended session.",
    )
    p_rr.add_argument(
        "--intensity-delta",
        choices=INTENSITY_DELTA_CHOICES, default=None,
        help=(
            "Intensity the user applied relative to the recommendation. "
            "Ordinals used by summary aggregation: "
            "much_lighter=-2, lighter=-1, same=0, harder=1, much_harder=2."
        ),
    )
    p_rr.add_argument(
        "--duration-minutes", type=int, default=None,
        help="Actual session duration in whole minutes.",
    )
    p_rr.add_argument(
        "--pre-energy", type=int, choices=range(1, 6), default=None,
        help="Self-reported energy score before the session, 1–5.",
    )
    p_rr.add_argument(
        "--post-energy", type=int, choices=range(1, 6), default=None,
        help="Self-reported energy score after the session, 1–5.",
    )
    p_rr.add_argument(
        "--disagreed-firings", default=None,
        help=(
            "Comma-separated x_rule_firing.firing_id list the user "
            "marked as 'should not have fired'. Empty string records an "
            "explicit empty list (the question was asked, no disagreement)."
        ),
    )
    p_rr.set_defaults(func=cmd_review_record)
    annotate_contract(
        p_rr,
        mutation="writes-state",
        idempotent="no",  # append-only review_outcome rows
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Record a review_outcome against a review_event. Carries "
            "the migration-010 enrichment columns (completed, "
            "intensity_delta, pre/post_energy, disagreed_firing_ids)."
        ),
        preconditions=[
            "review_event_exists_for_event_id",
            "recommendation_exists_for_recommendation_id",
        ],
        output_schema={
            "OK": {
                "shape": "JSON confirmation of the persisted outcome.",
                "json_keys": [
                    "review_event_id", "recommendation_id", "user_id",
                    "domain", "followed_recommendation",
                    "self_reported_improvement",
                    "re_linked_from_recommendation_id", "re_link_note",
                ],
                "notes": (
                    "When the target rec's plan has been superseded, "
                    "recommendation_id is the leaf rec and "
                    "re_linked_from_recommendation_id is the original. "
                    "Refusal (leaf has no matching-domain rec) exits "
                    "USER_INPUT with no write."
                ),
            },
        },
    )

    p_rsum = review_sub.add_parser("summary", help="Summarize outcome history counts")
    p_rsum.add_argument("--base-dir", required=True)
    p_rsum.add_argument("--user-id", default=None)
    p_rsum.add_argument("--domain", default=None,
                        help="Restrict counts to a single domain "
                             "(e.g. 'recovery' or 'running'). Omitted = all domains.")
    p_rsum.set_defaults(func=cmd_review_summary)
    annotate_contract(
        p_rsum,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Summarize review_outcome counts (followed / not-followed, "
            "per-domain tallies)."
        ),
    )

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
                      help="State DB path (default: `$HAI_STATE_DB` or `~/.local/share/health_agent_infra/state.db`)")
    p_ig.set_defaults(func=cmd_intake_gym)
    annotate_contract(
        p_ig,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a gym session (sets + exercises) as typed human-input.",
    )

    p_ie = intake_sub.add_parser(
        "exercise",
        help="Add a user-defined exercise-taxonomy row for future matching",
    )
    p_ie.add_argument("--name", required=True,
                      help="Canonical display name for the new lift")
    p_ie.add_argument("--primary-muscle-group", required=True,
                      help="Primary muscle group label stored on the taxonomy row")
    p_ie.add_argument("--category", required=True,
                      choices=EXERCISE_CATEGORY_CHOICES,
                      help="Taxonomy category: compound | isolation")
    p_ie.add_argument("--equipment", required=True,
                      choices=EXERCISE_EQUIPMENT_CHOICES,
                      help="Equipment bucket used in exercise search")
    p_ie.add_argument("--exercise-id", default=None,
                      help="Optional explicit taxonomy id. Defaults to a "
                           "deterministic snake_case slug of --name")
    p_ie.add_argument("--aliases", default=None,
                      help="Optional comma- or pipe-separated aliases")
    p_ie.add_argument("--secondary-muscle-groups", default=None,
                      help="Optional comma- or pipe-separated secondary groups")
    p_ie.add_argument("--db-path", default=None,
                      help="State DB path (default: platformdirs user_data_dir)")
    p_ie.set_defaults(func=cmd_intake_exercise)
    annotate_contract(
        p_ie,
        mutation="writes-state",
        idempotent="yes",  # upserts the taxonomy entry by slug
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Upsert an exercise taxonomy entry.",
    )

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
    annotate_contract(
        p_in,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a macros-only nutrition intake entry.",
    )

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
    annotate_contract(
        p_is,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a manual stress observation (used when Garmin stress is absent).",
    )

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
    annotate_contract(
        p_inote,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Attach a free-text context note to a day.",
    )

    p_ir = intake_sub.add_parser(
        "readiness",
        help="Record a typed manual-readiness entry (writes to state)",
    )
    p_ir.add_argument("--soreness", required=True, choices=SORENESS_CHOICES,
                      help="Subjective soreness band: low | moderate | high")
    p_ir.add_argument("--energy", required=True, choices=ENERGY_CHOICES,
                      help="Subjective energy band: low | moderate | high")
    p_ir.add_argument("--planned-session-type", required=True,
                      help="Planned session type (free text; e.g. easy, moderate, hard, intervals, race, rest)")
    p_ir.add_argument("--active-goal", default=None,
                      help="Optional active training goal (free text)")
    p_ir.add_argument("--as-of", default=None,
                      help="As-of date the intake pertains to (ISO-8601, default today UTC)")
    p_ir.add_argument("--user-id", default="u_local_1",
                      help="User this intake attaches to (default: u_local_1)")
    p_ir.add_argument("--base-dir", required=True,
                      help="Intake root (readiness_manual.jsonl lands here)")
    p_ir.add_argument("--db-path", default=None,
                      help="State DB path (defaults to HAI_STATE_DB or ~/.health_agent/state.db)")
    p_ir.add_argument("--ingest-actor", default="hai_cli_direct",
                      choices=("hai_cli_direct", "claude_agent_v1"),
                      help="Transport identity for provenance (default: hai_cli_direct)")
    p_ir.set_defaults(func=cmd_intake_readiness)
    annotate_contract(
        p_ir,
        mutation="writes-state",
        idempotent="no",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Record a manual readiness self-report entry.",
    )

    p_state = sub.add_parser("state", help="Local SQLite state store management")
    state_sub = p_state.add_subparsers(dest="state_command", required=True)

    p_si = state_sub.add_parser("init", help="Create the state DB and apply pending migrations")
    p_si.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_si.set_defaults(func=cmd_state_init)
    annotate_contract(
        p_si,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Create the local SQLite state DB and apply all pending "
            "migrations. Idempotent — safe to call repeatedly."
        ),
    )

    p_sm = state_sub.add_parser("migrate", help="Apply pending migrations against an existing state DB")
    p_sm.add_argument("--db-path", default=None,
                      help="Path to state.db (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db)")
    p_sm.set_defaults(func=cmd_state_migrate)
    annotate_contract(
        p_sm,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Apply any pending schema migrations to an already-"
            "initialized state DB."
        ),
    )

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
    annotate_contract(
        p_sread,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Read a per-domain accepted-state row for a given date.",
    )

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
    p_ssnap.add_argument("--evidence-json", default=None,
                         help="Optional path to a `hai clean` output JSON. When "
                              "present, the recovery block is expanded to the "
                              "full Phase 1 bundle shape (evidence + raw_summary "
                              "+ classified_state + policy_result). When absent, "
                              "the recovery block keeps its v1.0 shape.")
    p_ssnap.set_defaults(func=cmd_state_snapshot)
    annotate_contract(
        p_ssnap,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Emit the cross-domain state snapshot the synthesis / skills "
            "layer consumes for a (for_date, user_id) pair."
        ),
    )

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
    annotate_contract(
        p_sr,
        mutation="writes-state",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Rebuild the accepted_*_state_daily tables from the raw "
            "evidence JSONL. Deterministic projection — safe to re-run."
        ),
    )

    p_daily = sub.add_parser(
        "daily",
        help=(
            "One-shot morning orchestration over the existing runtime "
            "(pull → clean → snapshot → proposal-gate → synthesize → "
            "schedule reviews). Stops honestly at the agent seam when "
            "proposals are not yet in proposal_log."
        ),
    )
    p_daily.add_argument("--base-dir", required=True,
                         help="Writeback/intake root. review_events.jsonl "
                              "is appended here after synthesis.")
    p_daily.add_argument("--as-of", default=None,
                         help="Civil date to orchestrate for, ISO-8601. "
                              "Default: today UTC.")
    p_daily.add_argument("--user-id", default="u_local_1",
                         help="User whose plan to generate.")
    p_daily.add_argument("--db-path", default=None,
                         help="State DB path (default: `$HAI_STATE_DB` or "
                              "`~/.local/share/health_agent_infra/state.db`).")
    p_daily.add_argument("--live", action="store_true",
                         help="Legacy flag: equivalent to --source garmin_live. "
                              "Default (no --live and no --source) uses the "
                              "committed CSV adapter.")
    p_daily.add_argument(
        "--source",
        choices=("csv", "garmin_live", "intervals_icu"),
        default=None,
        help="Evidence source for the pull stage. Same semantics as "
             "`hai pull --source`. Defaults to csv unless --live is set.",
    )
    p_daily.add_argument("--history-days", type=int, default=14,
                         help="Trailing window for live pull series "
                              "(matches `hai pull --history-days`).")
    p_daily.add_argument("--skip-pull", action="store_true",
                         help="Skip the pull + clean stages. Assumes "
                              "state already populated for --as-of.")
    p_daily.add_argument("--domains", default=None,
                         help="Optional CSV subset of expected domains "
                              "(recovery, running, sleep, stress, "
                              "strength, nutrition). Filters the "
                              "proposal-gate expected-vs-present report "
                              "only; synthesis still runs over whatever "
                              "proposals are present in proposal_log.")
    p_daily.add_argument("--agent-version", default="claude_agent_v1",
                         help="Agent version string stamped on "
                              "committed rows.")
    p_daily.add_argument("--supersede", action="store_true",
                         help="Keep prior canonical plan and write a "
                              "fresh _v<N> id. Default is atomic replace.")
    p_daily.add_argument("--skip-reviews", action="store_true",
                         help="Skip review-event scheduling after "
                              "synthesis.")
    p_daily.set_defaults(func=cmd_daily)
    annotate_contract(
        p_daily,
        mutation="writes-state",
        idempotent="yes-with-supersede",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Morning orchestrator: pull → clean → reproject → propose → "
            "synthesize → daily_plan in one invocation."
        ),
        preconditions=[
            "state_db_initialized",
            "garmin_credentials_optional",
        ],
        output_schema={
            "OK": {
                "shape": "JSON report of the orchestration run.",
                "json_keys": [
                    "as_of_date", "user_id", "base_dir", "db_path",
                    "expected_domains", "stages", "overall_status",
                ],
                "overall_status_values": [
                    "complete", "awaiting_proposals", "failed",
                ],
                "notes": (
                    "When overall_status=awaiting_proposals the agent "
                    "must post DomainProposal rows via hai propose for "
                    "each missing domain, then rerun."
                ),
            },
        },
    )

    p_setup = sub.add_parser("setup-skills", help="Copy packaged skills/ into ~/.claude/skills/")
    p_setup.add_argument("--dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR))
    p_setup.add_argument("--force", action="store_true",
                         help="Overwrite existing skill directories of the same name")
    p_setup.set_defaults(func=cmd_setup_skills)
    annotate_contract(
        p_setup,
        mutation="writes-skills-dir",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Copy the packaged skills/ tree to ~/.claude/skills/ so "
            "Claude Code discovers them."
        ),
    )

    p_init = sub.add_parser(
        "init",
        help=(
            "First-run setup: scaffold thresholds, init state DB + apply "
            "migrations, copy skills, report Garmin auth status. "
            "Idempotent; safe to rerun."
        ),
    )
    p_init.add_argument("--thresholds-path", default=None,
                        help="Override thresholds TOML destination "
                             "(default: platformdirs user_config_dir).")
    p_init.add_argument("--db-path", default=None,
                        help="Override state DB path (default: "
                             "$HAI_STATE_DB or platform default).")
    p_init.add_argument("--skills-dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR),
                        help="Destination for skills/ (default: ~/.claude/skills/).")
    p_init.add_argument("--skip-skills", action="store_true",
                        help="Skip copying skills (useful when the agent "
                             "harness is not Claude Code).")
    p_init.add_argument("--force", action="store_true",
                        help="Overwrite an existing thresholds TOML and "
                             "existing skills directories of the same name.")
    p_init.add_argument("--with-auth", action="store_true",
                        help="After the non-interactive setup, prompt for "
                             "Garmin credentials and store them in the OS "
                             "keyring (equivalent to running `hai auth "
                             "garmin` afterward). Requires a TTY.")
    p_init.add_argument("--with-first-pull", action="store_true",
                        help="After setup (and --with-auth, if used), do "
                             "a single live-adapter pull for today so "
                             "`hai daily` has state to reason over. One "
                             "network call, configurable history window "
                             "via --history-days. Requires Garmin creds.")
    p_init.add_argument("--history-days", type=int, default=1,
                        help="How many days of historical context the "
                             "first-pull adapter fetches (default: 1 → "
                             "~5 Garmin API calls). Larger windows give "
                             "richer baselines but risk rate-limiting: "
                             "each extra day adds ~5 API calls. Ignored "
                             "without --with-first-pull.")
    p_init.add_argument("--user-id", default="u_local_1",
                        help="User id to record against the backfill's "
                             "sync_run_log rows (default: u_local_1).")
    p_init.set_defaults(func=cmd_init)
    annotate_contract(
        p_init,
        mutation="interactive",
        idempotent="no",
        json_output="none",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=False,  # interactive wizard
        description="First-run wizard: state init, config scaffolding, auth setup.",
    )

    p_doctor = sub.add_parser(
        "doctor",
        help=(
            "Read-only runtime diagnostics: config, state DB, Garmin "
            "auth, and skills install. Exits 0 for ok/warn, 2 for fail."
        ),
    )
    p_doctor.add_argument("--thresholds-path", default=None,
                          help="Override thresholds TOML path (default: "
                               "platformdirs user_config_dir).")
    p_doctor.add_argument("--db-path", default=None,
                          help="Override state DB path (default: "
                               "$HAI_STATE_DB or platform default).")
    p_doctor.add_argument("--skills-dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR),
                          help="Skills destination to inspect (default: "
                               "~/.claude/skills/).")
    p_doctor.add_argument("--user-id", default="u_local_1",
                          help="Which user's sync history + today counts to "
                               "report. Default: u_local_1.")
    p_doctor.add_argument("--as-of", default=None,
                          help="Anchor date for freshness + today counts, "
                               "ISO-8601. Default: today (UTC).")
    p_doctor.add_argument("--json", action="store_true",
                          help="Emit the structured report dict as JSON "
                               "instead of the human-readable text view.")
    p_doctor.set_defaults(func=cmd_doctor)
    annotate_contract(
        p_doctor,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # text default, JSON via flag
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Report runtime health: DB present, migrations up to date, "
            "per-source freshness, today's accepted counts."
        ),
    )

    p_stats = sub.add_parser(
        "stats",
        help=(
            "Summarise local sync + command-invocation history from the "
            "state DB. Read-only, never leaves the device."
        ),
    )
    p_stats.add_argument("--db-path", default=None,
                         help="Override state DB path (default: "
                              "$HAI_STATE_DB or platform default).")
    p_stats.add_argument("--user-id", default="u_local_1",
                         help="Whose sync freshness to report. "
                              "Default: u_local_1.")
    p_stats.add_argument("--limit", type=int, default=7,
                         help="Number of recent runtime_event_log rows "
                              "to include (default: 7).")
    p_stats.add_argument("--json", action="store_true",
                         help="Emit the structured report dict as JSON "
                              "instead of the human-readable text view.")
    p_stats.set_defaults(func=cmd_stats)
    annotate_contract(
        p_stats,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-in",  # text default, JSON via flag
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description=(
            "Summarise sync_run_log (last pull per source) + "
            "runtime_event_log (recent commands, daily streak) from the "
            "user's local DB. No telemetry leaves the device."
        ),
    )

    # D4 ADR (reporting/plans/v0_1_4/adr_classify_policy_cli.md): the
    # legacy `hai classify` / `hai policy` recovery-only debug CLIs
    # were removed in v0.1.4. Their behaviour is subsumed by
    # `hai state snapshot --evidence-json`, which emits
    # classified_state + policy_result for every domain in one call.

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
    annotate_contract(
        p_ci,
        mutation="writes-config",
        idempotent="yes",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Scaffold a default thresholds.toml at the user-config path.",
    )

    p_cs = config_sub.add_parser(
        "show",
        help="Print the merged effective thresholds (defaults + user overrides)",
    )
    p_cs.add_argument("--path", default=None,
                      help="Override source path (default: platformdirs user_config_dir)")
    p_cs.set_defaults(func=cmd_config_show)
    annotate_contract(
        p_cs,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Print the effective merged threshold configuration (defaults + overrides).",
    )

    p_exercise = sub.add_parser(
        "exercise",
        help="Exercise-taxonomy helpers (search, lookup)",
    )
    exercise_sub = p_exercise.add_subparsers(dest="exercise_command", required=True)

    p_esearch = exercise_sub.add_parser(
        "search",
        help="Rank top taxonomy matches for a free-text exercise name",
    )
    p_esearch.add_argument("--query", required=True,
                           help="Free-text exercise name to resolve")
    p_esearch.add_argument("--limit", type=int, default=10,
                           help="Max hits to return (default 10)")
    p_esearch.add_argument("--db-path", default=None,
                           help="Path to state DB (default: platformdirs user_data_dir)")
    p_esearch.set_defaults(func=cmd_exercise_search)
    annotate_contract(
        p_esearch,
        mutation="read-only",
        idempotent="n/a",
        json_output="default",
        exit_codes=("OK", "USER_INPUT"),
        agent_safe=True,
        description="Rank top exercise-taxonomy matches for a free-text query.",
    )

    _register_eval_subparser(sub)

    p_caps = sub.add_parser(
        "capabilities",
        help="Emit the agent-CLI-contract manifest (JSON by default, "
             "--markdown for the human-readable form)",
    )
    p_caps.add_argument(
        "--markdown", action="store_true",
        help="Render the manifest as the contract markdown doc on stdout "
             "instead of JSON. Used by the doc regenerator.",
    )
    p_caps.set_defaults(func=cmd_capabilities)
    annotate_contract(
        p_caps,
        mutation="read-only",
        idempotent="n/a",
        json_output="opt-out",  # JSON default; --markdown suppresses
        exit_codes=("OK",),
        agent_safe=True,
        description=(
            "Emit the agent-CLI-contract manifest describing every "
            "subcommand's mutation class, idempotency, JSON output, and "
            "exit codes. The authoritative surface the routing skill "
            "consumes."
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
