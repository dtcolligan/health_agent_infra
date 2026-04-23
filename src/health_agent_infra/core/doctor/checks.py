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
    if current < head:
        base.update({
            "status": "warn",
            "pending_migrations": head - current,
            "reason": f"{head - current} pending migration(s)",
            "hint": "run `hai state migrate`",
        })
    else:
        base["status"] = "ok"
    return base


def check_auth_garmin(store: Any) -> dict[str, Any]:
    """Credential presence only — never reads the secret value."""

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
    return {"status": "ok", "credentials_source": source}


def check_auth_intervals_icu(store: Any) -> dict[str, Any]:
    """Credential presence only — never reads the API key."""

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
    return {"status": "ok", "credentials_source": source}


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
) -> DoctorReport:
    """Run every check and return a :class:`DoctorReport`.

    Order matters only for presentation — status roll-up is symmetric.
    The "today" counts use ``as_of_date`` (defaults to today UTC) so
    an operator debugging yesterday's state can pass ``--as-of``
    without rewiring the rest of the checks.
    """

    as_of = as_of_date if as_of_date is not None else datetime.now(timezone.utc).date()

    checks: dict[str, dict[str, Any]] = {
        "config": check_config(thresholds_path),
        "state_db": check_state_db(db_path),
        "auth_garmin": check_auth_garmin(credential_store),
        "auth_intervals_icu": check_auth_intervals_icu(credential_store),
        "skills": check_skills(skills_dest, packaged_skill_names),
        "domains": check_domains(domain_names),
        "sources": check_sources(db_path, user_id=user_id, as_of_date=as_of),
        "today": check_today(db_path, user_id=user_id, as_of_date=as_of),
    }

    overall = worst_status([c["status"] for c in checks.values()])
    return DoctorReport(
        version=version,
        overall_status=overall,
        checks=checks,
    )
