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
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional

from health_agent_infra import __version__ as _PACKAGE_VERSION
from health_agent_infra.core import exit_codes
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
from health_agent_infra.core.review.outcomes import (
    persist_review_event,
    record_review_outcome,
    schedule_review,
    summarize_review_history,
)
from health_agent_infra.core.schemas import (
    FollowUp,
    PolicyDecision,
    ReviewEvent,
    ReviewOutcome,
)
from health_agent_infra.domains.recovery.schemas import TrainingRecommendation
from health_agent_infra.core.validate import (
    RecommendationValidationError,
    validate_recommendation_dict,
)
from health_agent_infra.core.writeback.recommendation import perform_writeback


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
    mode = "live" if getattr(args, "live", False) else "csv"
    # The source label is known up front for CSV (fixed adapter class);
    # for live pulls we still use "garmin_live" — _build_live_adapter
    # either returns a GarminLiveAdapter whose source_name is the
    # canonical label, or raises, in which case we log the attempt
    # against that same label.
    source_label = "garmin_live" if mode == "live" else GarminRecoveryReadinessAdapter.source_name

    sync_id = _open_sync_row(
        getattr(args, "db_path", None),
        source=source_label,
        user_id=args.user_id,
        mode=mode,
        for_date=as_of,
    )

    if mode == "live":
        try:
            adapter = _build_live_adapter(args)
        except GarminLiveError as exc:
            # Credential-resolution failure — the caller controls this
            # (run `hai auth garmin` or set env vars), so it's USER_INPUT
            # rather than a transient vendor issue.
            _close_sync_row_failed(args.db_path, sync_id, exc)
            print(f"live pull error: {exc}", file=sys.stderr)
            return exit_codes.USER_INPUT
    else:
        adapter = GarminRecoveryReadinessAdapter()

    try:
        pull = adapter.load(as_of)
    except GarminLiveError as exc:
        # Vendor API blip (5xx, rate limit, network) — a retry may fix it.
        _close_sync_row_failed(args.db_path, sync_id, exc)
        print(f"live pull error: {exc}", file=sys.stderr)
        return exit_codes.TRANSIENT

    manual = None
    if args.manual_readiness_json:
        manual = json.loads(Path(args.manual_readiness_json).read_text(encoding="utf-8"))
    elif args.use_default_manual_readiness:
        manual = default_manual_readiness(as_of)

    # rows_pulled: 1 if we got a daily summary row; 0 otherwise. This
    # maps "one logical day's evidence = one row" without pretending the
    # per-metric arrays are independent rows.
    rows = 1 if pull.get("raw_daily_row") is not None else 0
    _close_sync_row_ok(
        args.db_path,
        sync_id,
        rows_pulled=rows,
        rows_accepted=rows,
        duplicates_skipped=0,
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
    """

    store = CredentialStore.default()
    credentials = store.load_garmin()
    if credentials is None:
        raise GarminLiveError(
            "no Garmin credentials found. Run `hai auth garmin` or set "
            "HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD."
        )
    client = build_default_client(credentials)
    history_days = getattr(args, "history_days", 14)
    return GarminLiveAdapter(client=client, history_days=history_days)


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
            f"<writeback-root>` to recover.",
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
    return exit_codes.OK


def cmd_auth_status(args: argparse.Namespace) -> int:
    """Report credential presence only — never prints secrets."""

    store = _credential_store_for(args)
    status = store.garmin_status()
    status["backend"] = _backend_kind(store)
    _emit_json(status)
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


def cmd_writeback(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import project_recommendation

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
# hai propose — schema-validated DomainProposal persistence
# ---------------------------------------------------------------------------

def cmd_propose(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import project_proposal
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
        return 2
    except (ValueError, KeyError) as exc:
        print(f"propose rejected: {exc}", file=sys.stderr)
        return 2

    # JSONL audit first.
    record = perform_proposal_writeback(data, base_dir=Path(args.base_dir))

    # DB projection is best-effort; failure becomes a stderr warning.
    _dual_write_project(
        args.db_path,
        lambda conn: project_proposal(conn, data),
        "proposal",
    )

    _emit_json(record.to_dict())
    return 0


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
            else:
                bundle = load_bundle_for_date(
                    conn,
                    for_date=date.fromisoformat(args.for_date),
                    user_id=args.user_id,
                )
        except ExplainNotFoundError as exc:
            # Well-formed request, no matching row — NOT_FOUND, not user-input.
            print(f"hai explain: {exc}", file=sys.stderr)
            return exit_codes.NOT_FOUND
    finally:
        conn.close()

    if args.text:
        sys.stdout.write(render_bundle_text(bundle))
    else:
        _emit_json(bundle_to_dict(bundle))
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
        return 2

    try:
        category = validate_category(args.category)
        validate_value(args.value)
        domain = validate_domain(args.domain)
    except UserMemoryValidationError as exc:
        print(
            f"hai memory set rejected: invariant={exc.invariant}: {exc}",
            file=sys.stderr,
        )
        return 2

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
    return 0


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
        return 2

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
            return 2
    finally:
        conn.close()

    _emit_json(payload)
    return 0


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
        return 2

    conn = open_connection(db_path)
    try:
        existing = read_memory_entry(conn, memory_id=args.memory_id)
        if existing is None:
            print(
                f"hai memory archive: no entry with memory_id="
                f"{args.memory_id!r}",
                file=sys.stderr,
            )
            return 2
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
    return 0


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

    The payload is parsed generically rather than through the recovery-only
    ``_recommendation_from_dict`` validator — ``hai writeback`` is the
    validation boundary, and review scheduling trusts the already-persisted
    recommendation. ``domain`` is read from the payload (falling back to
    ``"recovery"`` for v1 rows that pre-date the domain column).
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
    return 0


def cmd_review_record(args: argparse.Namespace) -> int:
    from health_agent_infra.core.state import project_review_outcome

    data = json.loads(Path(args.outcome_json).read_text(encoding="utf-8"))
    domain = data.get("domain", "recovery")
    event = ReviewEvent(
        review_event_id=data["review_event_id"],
        recommendation_id=data["recommendation_id"],
        user_id=data["user_id"],
        review_at=_coerce_dt(data.get("review_at", datetime.now(timezone.utc).isoformat())),
        review_question=data.get("review_question", ""),
        domain=domain,
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
    domain_filter = getattr(args, "domain", None)
    if not outcomes_path.exists():
        _emit_json(summarize_review_history([], domain=domain_filter))
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
            domain=d.get("domain", "recovery"),
        ))
    _emit_json(summarize_review_history(outcomes, domain=domain_filter))
    return 0


# ---------------------------------------------------------------------------
# hai intake readiness — typed manual readiness intake, emits JSON to stdout
# ---------------------------------------------------------------------------

SORENESS_CHOICES = ("low", "moderate", "high")
ENERGY_CHOICES = ("low", "moderate", "high")
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
            f"reproject --base-dir <writeback-root>` to recover.",
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
        return 2

    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        print(
            f"state DB not found at {db_path}. Run `hai state init` first.",
            file=sys.stderr,
        )
        return 2

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
            return 2

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
    return 0


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

    from health_agent_infra.domains.stress.intake import (
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
    return 0


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
    return 0


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

    from health_agent_infra.core.state import initialize_database, resolve_db_path

    db_path = resolve_db_path(args.db_path)
    resolved, applied = initialize_database(db_path)
    _emit_json({
        "db_path": str(resolved),
        "created": applied,  # empty list if nothing was applied in this call
    })
    return 0


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
        return 2

    as_of = date.fromisoformat(args.as_of)

    evidence_bundle: Optional[dict] = None
    if args.evidence_json:
        evidence, raw_summary, err = _load_cleaned_bundle(args.evidence_json)
        if err is not None:
            print(err, file=sys.stderr)
            return 2
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

_SUPPORTED_CLASSIFY_DOMAINS = {"recovery"}


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


def cmd_classify(args: argparse.Namespace) -> int:
    if args.domain not in _SUPPORTED_CLASSIFY_DOMAINS:
        print(
            f"unsupported domain: {args.domain!r}; only {sorted(_SUPPORTED_CLASSIFY_DOMAINS)} supported in v1",
            file=sys.stderr,
        )
        return 2

    evidence, raw_summary, error = _load_cleaned_bundle(args.evidence_json)
    if error is not None:
        print(error, file=sys.stderr)
        return 2

    try:
        thresholds = load_thresholds(
            path=Path(args.thresholds_path).expanduser() if args.thresholds_path else None
        )
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    classified = classify_recovery_state(evidence, raw_summary, thresholds=thresholds)
    _emit_json({
        "domain": args.domain,
        "as_of_date": evidence.get("as_of_date"),
        "user_id": evidence.get("user_id"),
        "classified": classified,
    })
    return 0


def cmd_policy(args: argparse.Namespace) -> int:
    if args.domain not in _SUPPORTED_CLASSIFY_DOMAINS:
        print(
            f"unsupported domain: {args.domain!r}; only {sorted(_SUPPORTED_CLASSIFY_DOMAINS)} supported in v1",
            file=sys.stderr,
        )
        return 2

    evidence, raw_summary, error = _load_cleaned_bundle(args.evidence_json)
    if error is not None:
        print(error, file=sys.stderr)
        return 2

    try:
        thresholds = load_thresholds(
            path=Path(args.thresholds_path).expanduser() if args.thresholds_path else None
        )
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    classified = classify_recovery_state(evidence, raw_summary, thresholds=thresholds)
    policy = evaluate_recovery_policy(classified, raw_summary, thresholds=thresholds)
    _emit_json({
        "domain": args.domain,
        "as_of_date": evidence.get("as_of_date"),
        "user_id": evidence.get("user_id"),
        "classified": classified,
        "policy": policy,
    })
    return 0


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
        return 2

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
    return 0


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

    if getattr(args, "live", False):
        adapter = _build_live_adapter(args)
    else:
        adapter = GarminRecoveryReadinessAdapter()

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
        return 2

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
        return 2

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
        except GarminLiveError as exc:
            report["stages"]["pull"] = {"status": "failed", "error": str(exc)}
            report["overall_status"] = "failed"
            _emit_json(report)
            return 2
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
            return 0

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
            return 2
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
    # runs `hai auth garmin` separately for credential entry.
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
                "keyring, or set HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD "
                "for non-interactive use"
            )
        ),
    }

    _emit_json(report)
    return 0


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

    Reports what is present vs missing for each first-run piece — config,
    state DB + schema version, Garmin credentials, skills install — plus
    the package version. Does not mutate anything; every state-changing
    step belongs to ``hai init`` or a targeted subcommand.

    Exit code 0 for ``ok`` or ``warn`` overall; 2 for ``fail`` (malformed
    config on disk). ``warn`` is the normal pre-setup state so the check
    stays agent-friendly — an agent or shell script can run ``hai doctor
    && hai daily`` without getting blocked by a missing-auth warning.
    """

    from health_agent_infra.core.state import (
        current_schema_version,
        open_connection,
        resolve_db_path,
    )
    from health_agent_infra.core.state.store import discover_migrations

    report: dict[str, Any] = {
        "version": _PACKAGE_VERSION,
        "checks": {},
    }

    # ---- config ----
    thresholds_path = (
        Path(args.thresholds_path).expanduser()
        if args.thresholds_path
        else user_config_path()
    )
    if not thresholds_path.exists():
        report["checks"]["config"] = {
            "status": "warn",
            "path": str(thresholds_path),
            "reason": "thresholds file not present; defaults in effect",
            "hint": "run `hai init` or `hai config init`",
        }
    else:
        try:
            load_thresholds(path=thresholds_path)
            report["checks"]["config"] = {
                "status": "ok",
                "path": str(thresholds_path),
            }
        except ConfigError as exc:
            report["checks"]["config"] = {
                "status": "fail",
                "path": str(thresholds_path),
                "reason": str(exc),
                "hint": "repair the TOML or regenerate with `hai config init --force`",
            }

    # ---- state DB + migration state ----
    db_path = resolve_db_path(args.db_path)
    if not db_path.exists():
        report["checks"]["state_db"] = {
            "status": "warn",
            "path": str(db_path),
            "reason": "state DB file not present",
            "hint": "run `hai init` or `hai state init`",
        }
    else:
        conn = open_connection(db_path)
        try:
            current = current_schema_version(conn)
        finally:
            conn.close()
        packaged = discover_migrations()
        head = max((v for v, _, _ in packaged), default=0)
        if current < head:
            report["checks"]["state_db"] = {
                "status": "warn",
                "path": str(db_path),
                "schema_version": current,
                "head_version": head,
                "pending_migrations": head - current,
                "reason": f"{head - current} pending migration(s)",
                "hint": "run `hai state migrate`",
            }
        else:
            report["checks"]["state_db"] = {
                "status": "ok",
                "path": str(db_path),
                "schema_version": current,
                "head_version": head,
            }

    # ---- Garmin auth ----
    store = _credential_store_for(args)
    auth_status = store.garmin_status()
    if auth_status["credentials_available"]:
        if auth_status["keyring"]["password_present"]:
            source = "keyring"
        else:
            source = "env"
        report["checks"]["auth_garmin"] = {
            "status": "ok",
            "credentials_source": source,
        }
    else:
        report["checks"]["auth_garmin"] = {
            "status": "warn",
            "reason": "no Garmin credentials stored",
            "hint": (
                "run `hai auth garmin` (interactive) or set "
                "HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD in the environment"
            ),
        }

    # ---- skills ----
    dest = Path(args.skills_dest).expanduser()
    with _skills_source() as skills_source:
        packaged_names = (
            sorted(p.name for p in skills_source.iterdir() if p.is_dir())
            if skills_source.exists()
            else []
        )
    if not dest.exists():
        report["checks"]["skills"] = {
            "status": "warn",
            "dest": str(dest),
            "packaged_count": len(packaged_names),
            "installed_count": 0,
            "reason": "skills destination does not exist",
            "hint": "run `hai init` or `hai setup-skills`",
        }
    else:
        installed = sorted(p.name for p in dest.iterdir() if p.is_dir())
        missing = sorted(set(packaged_names) - set(installed))
        if missing:
            report["checks"]["skills"] = {
                "status": "warn",
                "dest": str(dest),
                "installed_count": len(installed),
                "packaged_count": len(packaged_names),
                "missing": missing,
                "hint": "run `hai setup-skills` to install missing skills",
            }
        else:
            report["checks"]["skills"] = {
                "status": "ok",
                "dest": str(dest),
                "installed_count": len(installed),
                "packaged_count": len(packaged_names),
            }

    # ---- domains (static — the six v1 domains ship with the wheel) ----
    report["checks"]["domains"] = {
        "status": "ok",
        "domains": sorted(_DAILY_SUPPORTED_DOMAINS),
    }

    overall = _worst_status(
        [c["status"] for c in report["checks"].values()]
    )
    report["overall_status"] = overall
    _emit_json(report)
    return 2 if overall == "fail" else 0


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
                        help="Fetch from Garmin Connect via stored credentials. "
                             "Default (flag omitted) continues to read the "
                             "committed CSV export.")
    p_pull.add_argument("--history-days", type=int, default=14,
                        help="Trailing window size for resting_hr / hrv / "
                             "training_load series (live pull only). Matches "
                             "the CSV adapter default.")
    p_pull.add_argument("--db-path", default=None,
                        help="State DB path for sync_run_log writes. Best-effort — "
                             "if the DB is absent, the pull still runs but the "
                             "sync row is skipped. Same semantics as `hai writeback`.")
    p_pull.set_defaults(func=cmd_pull)

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

    p_auth_status = auth_sub.add_parser(
        "status",
        help="Report whether credentials are configured (presence only, no secrets)",
    )
    p_auth_status.set_defaults(func=cmd_auth_status)

    p_clean = sub.add_parser("clean", help="Normalize pulled evidence + raw summary")
    p_clean.add_argument("--evidence-json", required=True,
                         help="Path to a JSON file produced by `hai pull`")
    p_clean.add_argument("--db-path", default=None,
                         help="State DB path (default: $HAI_STATE_DB or platform default). "
                              "If the DB is absent, projection is skipped with a stderr note; "
                              "stdout is unchanged.")
    p_clean.set_defaults(func=cmd_clean)

    p_wb = sub.add_parser(
        "writeback",
        help=(
            "Recovery-only standalone recommendation writeback. The "
            "canonical commit path for all six domains is `hai "
            "synthesize`, which atomically persists daily_plan + "
            "x_rule_firings + per-domain recommendations in one "
            "transaction. `hai writeback` is the legacy single-domain "
            "path that predates synthesis; it only accepts "
            "TrainingRecommendation payloads (recovery)."
        ),
    )
    p_wb.add_argument("--recommendation-json", required=True,
                      help="Path to a JSON file matching TrainingRecommendation (recovery-only).")
    p_wb.add_argument("--base-dir", required=True,
                      help="Writeback root (must contain 'recovery_readiness_v1')")
    p_wb.add_argument("--db-path", default=None,
                      help="State DB path (default: $HAI_STATE_DB or ~/.local/share/health_agent_infra/state.db). "
                           "If the DB is absent, projection is skipped with a stderr note.")
    p_wb.set_defaults(func=cmd_writeback)

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
                        help="State DB path (same semantics as `hai writeback --db-path`)")
    p_prop.set_defaults(func=cmd_propose)

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
                       help="State DB path (same semantics as `hai writeback --db-path`)")
    p_syn.set_defaults(func=cmd_synthesize)

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
    p_explain.add_argument(
        "--text", action="store_true",
        help="Render the bundle as a plain-text operator report instead "
             "of JSON.",
    )
    p_explain.add_argument("--db-path", default=None,
                           help="State DB path (same semantics as `hai writeback --db-path`)")
    p_explain.set_defaults(func=cmd_explain)

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
        help="State DB path (same semantics as `hai writeback --db-path`).",
    )
    p_mset.set_defaults(func=cmd_memory_set)

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
    p_rsum.add_argument("--domain", default=None,
                        help="Restrict counts to a single domain "
                             "(e.g. 'recovery' or 'running'). Omitted = all domains.")
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
    p_ssnap.add_argument("--evidence-json", default=None,
                         help="Optional path to a `hai clean` output JSON. When "
                              "present, the recovery block is expanded to the "
                              "full Phase 1 bundle shape (evidence + raw_summary "
                              "+ classified_state + policy_result). When absent, "
                              "the recovery block keeps its v1.0 shape.")
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
                         help="State DB path (same semantics as "
                              "`hai writeback --db-path`).")
    p_daily.add_argument("--live", action="store_true",
                         help="Fetch evidence via `python-garminconnect` "
                              "(requires `hai auth garmin`). Default uses "
                              "the committed CSV adapter.")
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

    p_setup = sub.add_parser("setup-skills", help="Copy packaged skills/ into ~/.claude/skills/")
    p_setup.add_argument("--dest", default=str(DEFAULT_CLAUDE_SKILLS_DIR))
    p_setup.add_argument("--force", action="store_true",
                         help="Overwrite existing skill directories of the same name")
    p_setup.set_defaults(func=cmd_setup_skills)

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
    p_init.set_defaults(func=cmd_init)

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
    p_doctor.set_defaults(func=cmd_doctor)

    p_classify = sub.add_parser(
        "classify",
        help="Run domain classifier against a cleaned-evidence bundle and print the result",
    )
    p_classify.add_argument("--domain", required=True, choices=sorted(_SUPPORTED_CLASSIFY_DOMAINS))
    p_classify.add_argument("--evidence-json", required=True,
                            help="Path to a JSON file produced by `hai clean`")
    p_classify.add_argument("--thresholds-path", default=None,
                            help="Override thresholds TOML path (default: platformdirs user_config_dir)")
    p_classify.set_defaults(func=cmd_classify)

    p_policy = sub.add_parser(
        "policy",
        help="Run classify + policy against a cleaned-evidence bundle and print both",
    )
    p_policy.add_argument("--domain", required=True, choices=sorted(_SUPPORTED_CLASSIFY_DOMAINS))
    p_policy.add_argument("--evidence-json", required=True,
                          help="Path to a JSON file produced by `hai clean`")
    p_policy.add_argument("--thresholds-path", default=None,
                          help="Override thresholds TOML path (default: platformdirs user_config_dir)")
    p_policy.set_defaults(func=cmd_policy)

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

    _register_eval_subparser(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv if argv is not None else sys.argv[1:])
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
