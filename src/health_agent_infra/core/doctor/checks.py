"""Read-only diagnostic checks aggregated by ``hai doctor``.

Every check returns a plain dict with a ``status`` in
``{"ok", "warn", "fail"}``. The orchestrator (:func:`build_report`)
runs each check in turn and returns a :class:`DoctorReport` mapping
check names to their result dicts, plus an ``overall_status`` derived
from the worst individual status via :func:`worst_status`.

Pure read: nothing in this module opens a write transaction, touches
the filesystem beyond reads, or mutates credential state. Failure
inside one check is local — the outer report still carries results
for every other check so the operator sees the whole picture in one
pass.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, TypedDict


class CheckResult(TypedDict, total=False):
    status: str


@dataclass
class DoctorReport:
    version: str
    overall_status: str
    checks: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "overall_status": self.overall_status,
            "checks": self.checks,
        }


_STATUS_ORDER: dict[str, int] = {"ok": 0, "warn": 1, "fail": 2}


def worst_status(statuses: list[str]) -> str:
    """Return the worst of a list of statuses. Empty list → ``'ok'``."""

    if not statuses:
        return "ok"
    worst = max(_STATUS_ORDER[s] for s in statuses)
    return {0: "ok", 1: "warn", 2: "fail"}[worst]


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def check_config(thresholds_path: Path) -> dict[str, Any]:
    """Config file present? Parseable? Malformed?"""

    from health_agent_infra.core.config import ConfigError, load_thresholds

    if not thresholds_path.exists():
        return {
            "status": "warn",
            "path": str(thresholds_path),
            "reason": "thresholds file not present; defaults in effect",
            "hint": "run `hai init` or `hai config init`",
        }
    try:
        load_thresholds(path=thresholds_path)
    except ConfigError as exc:
        return {
            "status": "fail",
            "path": str(thresholds_path),
            "reason": str(exc),
            "hint": "repair the TOML or regenerate with `hai config init --force`",
        }
    return {"status": "ok", "path": str(thresholds_path)}


def check_state_db(db_path: Path) -> dict[str, Any]:
    """DB present + at schema HEAD? Also carries file size for ops visibility."""

    from health_agent_infra.core.state import (
        current_schema_version,
        detect_schema_version_gaps,
        open_connection,
    )
    from health_agent_infra.core.state.store import discover_migrations

    if not db_path.exists():
        return {
            "status": "warn",
            "path": str(db_path),
            "reason": "state DB file not present",
            "hint": "run `hai init` or `hai state init`",
        }

    conn = open_connection(db_path)
    try:
        current = current_schema_version(conn)
        # v0.1.6 (W20 / Codex C7): MAX(version) can hide gaps below the
        # head if the migrations table was manually edited or partially
        # restored. Treat the applied set as a contiguous range and
        # surface any gap as a warn — the DB might appear current but
        # be missing schema objects from skipped lower versions.
        applied_gaps = detect_schema_version_gaps(conn)
    finally:
        conn.close()

    packaged = discover_migrations()
    head = max((v for v, _, _ in packaged), default=0)
    # DB size is the raw file size of the main DB file. SQLite's WAL and
    # shm sidecars aren't included — they're transient and inflate the
    # number for an operator trying to read "how much space is my data
    # taking."
    size_bytes = db_path.stat().st_size

    base = {
        "path": str(db_path),
        "schema_version": current,
        "head_version": head,
        "size_bytes": size_bytes,
    }
    if applied_gaps:
        base.update({
            "status": "warn",
            "applied_gaps": applied_gaps,
            "reason": (
                f"applied migrations have gaps below head: "
                f"{applied_gaps}"
            ),
            "hint": (
                "the DB looks current by MAX(version) but is missing "
                "schema objects from those versions; restore from a "
                "known-good backup or run `hai state init` against a "
                "fresh DB"
            ),
        })
    elif current < head:
        base.update({
            "status": "warn",
            "pending_migrations": head - current,
            "reason": f"{head - current} pending migration(s)",
            "hint": "run `hai state migrate`",
        })
    else:
        base["status"] = "ok"
    return base


def check_auth_garmin(
    store: Any, *, probe_result: Any = None
) -> dict[str, Any]:
    """Credential presence only — never reads the secret value.

    v0.1.11 W-X: when ``probe_result`` is supplied (i.e. the operator
    passed ``--deep``), the probe outcome attaches as a ``probe``
    sub-dict and the row's ``status`` reflects the probe's success/
    failure. Without ``--deep`` the row keeps its credentials-only
    semantics for backwards compatibility.
    """

    status = store.garmin_status()
    if not status["credentials_available"]:
        return {
            "status": "warn",
            "reason": "no Garmin credentials stored",
            "hint": (
                "run `hai auth garmin` (interactive) or set "
                "HAI_GARMIN_EMAIL + HAI_GARMIN_PASSWORD in the environment"
            ),
        }
    source = "keyring" if status["keyring"]["password_present"] else "env"
    out: dict[str, Any] = {"status": "ok", "credentials_source": source}
    if probe_result is not None:
        out["probe"] = probe_result.to_dict()
        if not probe_result.ok:
            out["status"] = "fail"
            out["reason"] = (
                f"Garmin --deep probe failed: "
                f"{probe_result.error_message or 'unknown error'}"
            )
    return out


def check_auth_intervals_icu(
    store: Any, *, probe_result: Any = None
) -> dict[str, Any]:
    """Credential presence only — never reads the API key.

    v0.1.11 W-X: ``probe_result`` adds a ``probe`` sub-dict and may
    flip the row to ``fail`` when the probe rejects.

    v0.1.13 W-AE: when ``probe_result`` carries an ``outcome_class``,
    surface it on the row alongside an actionable ``next_step`` from
    `OUTCOME_NEXT_STEPS`. The class string is the contract surface
    that `reporting/docs/intervals_icu_403_triage.md` references.
    """

    status = store.intervals_icu_status()
    if not status["credentials_available"]:
        return {
            "status": "warn",
            "reason": "no Intervals.icu credentials stored",
            "hint": (
                "run `hai auth intervals-icu` (interactive) or set "
                "HAI_INTERVALS_ATHLETE_ID + HAI_INTERVALS_API_KEY in the environment"
            ),
        }
    source = "keyring" if status["keyring"]["api_key_present"] else "env"
    out: dict[str, Any] = {"status": "ok", "credentials_source": source}
    if probe_result is not None:
        out["probe"] = probe_result.to_dict()
        outcome_class = getattr(probe_result, "outcome_class", None)
        if outcome_class is not None:
            from health_agent_infra.core.doctor.probe import OUTCOME_NEXT_STEPS

            out["outcome_class"] = outcome_class
            out["next_step"] = OUTCOME_NEXT_STEPS.get(
                outcome_class, OUTCOME_NEXT_STEPS["OTHER"],
            )
        if not probe_result.ok:
            out["status"] = "fail"
            out["reason"] = (
                f"intervals.icu --deep probe failed: "
                f"{probe_result.error_message or 'unknown error'}"
            )
            # Outcome-class-specific hint takes precedence over the
            # generic "probe failed" hint when classification ran.
            if outcome_class is not None:
                out["hint"] = out["next_step"]
    return out


def check_skills(skills_dest: Path, packaged_names: list[str]) -> dict[str, Any]:
    """Skills destination populated with every packaged skill?"""

    if not skills_dest.exists():
        return {
            "status": "warn",
            "dest": str(skills_dest),
            "packaged_count": len(packaged_names),
            "installed_count": 0,
            "reason": "skills destination does not exist",
            "hint": "run `hai init` or `hai setup-skills`",
        }
    installed = sorted(p.name for p in skills_dest.iterdir() if p.is_dir())
    missing = sorted(set(packaged_names) - set(installed))
    base = {
        "dest": str(skills_dest),
        "installed_count": len(installed),
        "packaged_count": len(packaged_names),
    }
    if missing:
        base.update({
            "status": "warn",
            "missing": missing,
            "hint": "run `hai setup-skills` to install missing skills",
        })
    else:
        base["status"] = "ok"
    return base


def check_domains(domains: list[str]) -> dict[str, Any]:
    """Static check — the six v1 domains ship with the wheel; always ok."""

    return {"status": "ok", "domains": sorted(domains)}


def check_sources(
    db_path: Path,
    *,
    user_id: str,
    as_of_date: date,
) -> dict[str, Any]:
    """Per-source last-successful-sync timestamps + staleness hours.

    Built on the same sync_run_log reader the snapshot ``sources``
    block uses (M2). Status is informational only — sources without a
    sync row yet surface as ``unknown`` rather than ``warn`` because
    "I haven't pulled Garmin on this machine yet" is a normal first-
    run state, not a malfunction.
    """

    if not db_path.exists():
        return {
            "status": "warn",
            "reason": "state DB not initialised — no sync history to read",
            "hint": "run `hai state init`",
            "sources": {},
        }

    try:
        from health_agent_infra.core.state import open_connection
        from health_agent_infra.core.state.sync_log import (
            latest_successful_sync_per_source,
        )
    except ImportError:
        return {
            "status": "ok",
            "sources": {},
            "reason": "sync_run_log unavailable in this build",
        }

    conn = open_connection(db_path)
    try:
        rows = latest_successful_sync_per_source(conn, user_id=user_id)
    except sqlite3.OperationalError:
        # Pre-migration-008 DB.
        rows = {}
    finally:
        conn.close()

    anchor = datetime.combine(
        as_of_date + timedelta(days=1), time.min, tzinfo=timezone.utc,
    )
    sources: dict[str, Any] = {}
    for source, row in rows.items():
        completed_at_raw = row.get("completed_at") or row.get("started_at")
        # F-A-11 fix per W-H1: fromisoformat doesn't accept None.
        if completed_at_raw is None:
            staleness = None
        else:
            try:
                completed_at = datetime.fromisoformat(completed_at_raw)
                if completed_at.tzinfo is None:
                    completed_at = completed_at.replace(tzinfo=timezone.utc)
                staleness = round(
                    (anchor - completed_at).total_seconds() / 3600.0, 2,
                )
            except (TypeError, ValueError):
                staleness = None
        sources[source] = {
            "last_successful_sync_at": completed_at_raw,
            "staleness_hours": staleness,
        }

    if not sources:
        return {
            "status": "ok",
            "sources": {},
            "reason": "no sync history yet (run `hai pull` or `hai intake *`)",
        }
    return {"status": "ok", "sources": sources}


def check_today(
    db_path: Path,
    *,
    user_id: str,
    as_of_date: date,
) -> dict[str, Any]:
    """Counts of proposals / recommendations / pending reviews for today.

    Pending reviews = review_event rows whose review_at <= end-of-day
    UTC on as_of_date and whose review_event_id has no matching
    review_outcome yet. These are the actions an operator might want to
    surface to the user today.
    """

    if not db_path.exists():
        return {
            "status": "warn",
            "reason": "state DB not initialised",
            "hint": "run `hai state init`",
        }

    from health_agent_infra.core.state import open_connection

    conn = open_connection(db_path)
    try:
        try:
            proposals = conn.execute(
                "SELECT COUNT(*) AS n FROM proposal_log "
                "WHERE for_date = ? AND user_id = ?",
                (as_of_date.isoformat(), user_id),
            ).fetchone()["n"]
            recommendations = conn.execute(
                "SELECT COUNT(*) AS n FROM recommendation_log "
                "WHERE for_date = ? AND user_id = ?",
                (as_of_date.isoformat(), user_id),
            ).fetchone()["n"]
            # A "pending review" is scheduled on or before as_of_date's
            # end-of-day AND has no outcome row yet.
            review_ceiling = datetime.combine(
                as_of_date + timedelta(days=1), time.min, tzinfo=timezone.utc,
            ).isoformat()
            pending_reviews = conn.execute(
                "SELECT COUNT(*) AS n FROM review_event re "
                "WHERE re.user_id = ? "
                "  AND re.review_at <= ? "
                "  AND NOT EXISTS ("
                "    SELECT 1 FROM review_outcome ro "
                "    WHERE ro.review_event_id = re.review_event_id"
                "  )",
                (user_id, review_ceiling),
            ).fetchone()["n"]
        except sqlite3.OperationalError as exc:
            return {
                "status": "warn",
                "reason": f"schema read failed: {exc}",
                "hint": "run `hai state migrate`",
            }
    finally:
        conn.close()

    return {
        "status": "ok",
        "for_date": as_of_date.isoformat(),
        "user_id": user_id,
        "proposals": int(proposals),
        "recommendations": int(recommendations),
        "pending_reviews": int(pending_reviews),
    }


def check_onboarding_readiness(
    db_path: Path,
    *,
    user_id: str,
    as_of_date: date,
) -> dict[str, Any]:
    """W-AE (v0.1.13): does this user look like they have completed onboarding?

    Three preconditions for a user to get value from `hai daily`:
      1. At least one active intent row (something to plan against).
      2. At least one active target row (a measurable to compare to).
      3. At least one successful wellness pull (signal to score).

    Each missing piece surfaces a separate `missing` reason + actionable
    hint. The row's overall status is `warn` when anything is missing
    (these are friendly warnings, not failures — a fresh install hits
    all three).
    """

    if not db_path.exists():
        return {
            "status": "warn",
            "reason": "state DB not initialised",
            "hint": "run `hai init`",
        }

    from health_agent_infra.core.intent import list_active_intent
    from health_agent_infra.core.state import open_connection
    from health_agent_infra.core.state.sync_log import (
        latest_successful_sync_per_source,
    )
    from health_agent_infra.core.target import list_active_target

    missing: list[str] = []
    hints: list[str] = []

    conn = open_connection(db_path)
    try:
        try:
            intent_rows = list_active_intent(
                conn, user_id=user_id, as_of_date=as_of_date,
            )
            target_rows = list_active_target(
                conn, user_id=user_id, as_of_date=as_of_date,
            )
            sync_rows = latest_successful_sync_per_source(conn, user_id=user_id)
        except sqlite3.OperationalError as exc:
            return {
                "status": "warn",
                "reason": f"schema read failed: {exc}",
                "hint": "run `hai state migrate`",
            }
    finally:
        conn.close()

    intent_count = len(intent_rows)
    target_count = len(target_rows)
    wellness_sources = [s for s in sync_rows if s in {"intervals_icu", "garmin"}]
    has_wellness_pull = any(sync_rows.get(s) for s in wellness_sources)

    if intent_count == 0:
        missing.append("intent")
        hints.append(
            "no active intent rows — run `hai intent training add-session` "
            "or `hai intent sleep set-window` to author a goal",
        )
    if target_count == 0:
        missing.append("target")
        hints.append(
            "no active target rows — run `hai target set` to commit a "
            "measurable wellness target",
        )
    if not has_wellness_pull:
        missing.append("wellness_pull")
        hints.append(
            "no successful wellness pull yet — run `hai pull --source "
            "intervals_icu` (preferred) or `hai pull --source garmin`",
        )

    base: dict[str, Any] = {
        "intent_count": intent_count,
        "target_count": target_count,
        "has_wellness_pull": has_wellness_pull,
    }
    if missing:
        base["status"] = "warn"
        base["missing"] = missing
        # First missing piece dominates the hint; full list also
        # surfaced under `missing` so a renderer can show them all.
        base["hint"] = hints[0]
        base["all_hints"] = hints
    else:
        base["status"] = "ok"
    return base


def check_intake_gaps(
    db_path: Path,
    *,
    user_id: str,
    as_of_date: date,
) -> dict[str, Any]:
    """W-AE (v0.1.13): list user-closeable intake gaps for today.

    Builds the snapshot the synthesis layer would consume and runs the
    same `compute_intake_gaps` the agent surfaces via
    `hai intake gaps`. Failures are non-fatal — gap detection is a
    diagnostic; if it can't run, the row reports `unknown` rather
    than blocking the doctor report.
    """

    if not db_path.exists():
        return {
            "status": "warn",
            "reason": "state DB not initialised",
            "hint": "run `hai init`",
        }

    try:
        from health_agent_infra.core.intake.gaps import (
            compute_intake_gaps_from_state_snapshot,
        )
    except ImportError:
        return {"status": "ok", "gaps": [], "reason": "gap detection unavailable"}

    try:
        gap_payload = compute_intake_gaps_from_state_snapshot(
            db_path=db_path,
            user_id=user_id,
            as_of_date=as_of_date,
            allow_stale=True,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "warn",
            "reason": f"gap detection failed: {type(exc).__name__}: {exc}",
            "hint": "re-run `hai doctor` after `hai state migrate`",
        }

    gap_rows = gap_payload.get("gaps", []) or []
    blocking = [g for g in gap_rows if g.get("blocks_coverage", True)]
    base: dict[str, Any] = {
        "gap_count": gap_payload.get("gap_count", len(gap_rows)),
        "blocking_gap_count": gap_payload.get(
            "gating_gap_count", len(blocking),
        ),
        "gaps": [
            {
                "domain": g.get("domain"),
                "missing_field": g.get("missing_field"),
                "blocks_coverage": g.get("blocks_coverage", True),
                "intake_command": g.get("intake_command"),
            }
            for g in gap_rows
        ],
    }
    if blocking:
        base["status"] = "warn"
        first = blocking[0]
        cmd = first.get("intake_command")
        domain = first.get("domain")
        missing = first.get("missing_field")
        base["hint"] = (
            f"close {missing!r} in domain {domain!r}: run `{cmd}`"
            if cmd
            else f"close the {missing!r} gap in domain {domain!r}"
        )
    else:
        base["status"] = "ok"
    return base


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def build_report(
    *,
    version: str,
    thresholds_path: Path,
    db_path: Path,
    skills_dest: Path,
    packaged_skill_names: list[str],
    domain_names: list[str],
    credential_store: Any,
    user_id: str,
    as_of_date: Optional[date] = None,
    deep: bool = False,
    probe: Any = None,
) -> DoctorReport:
    """Run every check and return a :class:`DoctorReport`.

    Order matters only for presentation — status roll-up is symmetric.
    The "today" counts use ``as_of_date`` (defaults to today UTC) so
    an operator debugging yesterday's state can pass ``--as-of``
    without rewiring the rest of the checks.

    v0.1.11 W-X: when ``deep=True``, run live or fixture probes
    against the auth surfaces. The ``probe`` argument lets callers
    inject an explicit :class:`Probe` (test override or demo-mode
    FixtureProbe). When ``probe`` is None and ``deep=True``, this
    function selects via ``resolve_probe(demo_active=...)``.
    """

    as_of = as_of_date if as_of_date is not None else datetime.now(timezone.utc).date()

    probe_results: dict[str, Any] = {}
    if deep:
        from health_agent_infra.core.demo.session import is_demo_active
        from health_agent_infra.core.doctor.probe import (
            resolve_probe,
            run_deep_probes,
        )

        active_probe = probe if probe is not None else resolve_probe(
            demo_active=is_demo_active(),
        )
        probe_results = run_deep_probes(
            probe=active_probe,
            credential_store=credential_store,
        )

    checks: dict[str, dict[str, Any]] = {
        "config": check_config(thresholds_path),
        "state_db": check_state_db(db_path),
        "auth_garmin": check_auth_garmin(
            credential_store,
            probe_result=probe_results.get("garmin"),
        ),
        "auth_intervals_icu": check_auth_intervals_icu(
            credential_store,
            probe_result=probe_results.get("intervals_icu"),
        ),
        "skills": check_skills(skills_dest, packaged_skill_names),
        "domains": check_domains(domain_names),
        "sources": check_sources(db_path, user_id=user_id, as_of_date=as_of),
        "today": check_today(db_path, user_id=user_id, as_of_date=as_of),
        "onboarding_readiness": check_onboarding_readiness(
            db_path, user_id=user_id, as_of_date=as_of,
        ),
        "intake_gaps": check_intake_gaps(
            db_path, user_id=user_id, as_of_date=as_of,
        ),
    }

    overall = worst_status([c["status"] for c in checks.values()])
    return DoctorReport(
        version=version,
        overall_status=overall,
        checks=checks,
    )
