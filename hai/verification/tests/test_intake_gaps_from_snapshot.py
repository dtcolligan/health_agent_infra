"""W-W: hai intake gaps --from-state-snapshot (Codex F-DEMO-04).

Tests the new offline gap-derivation path:
- Reads the latest accepted state without fresh evidence.
- 48h staleness gate (default) with --allow-stale-snapshot override.
- BEGIN IMMEDIATE single-read-transaction contract.
- derived_from + snapshot_read_at audit fields on every emitted gap.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.intake.gaps import (
    StalenessRefusal,
    compute_intake_gaps_from_state_snapshot,
)
from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import initialize_database


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    """A migrated empty state DB."""
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _seed_sync_run(db_path: Path, age_hours: float, status: str = "ok") -> None:
    """Insert a sync_run_log row at <age_hours> in the past."""
    conn = sqlite3.connect(str(db_path))
    try:
        completed_at = (
            datetime.now(timezone.utc) - timedelta(hours=age_hours)
        ).isoformat()
        # Pull the actual sync_run_log column shape from the DB and
        # insert the minimum we need.
        cols_rows = conn.execute(
            "PRAGMA table_info(sync_run_log)"
        ).fetchall()
        cols = [r[1] for r in cols_rows]
        # Build a minimal-required-fields insert; cols vary across
        # migrations. Provide a reasonable value for required ones.
        values = {
            "sync_run_id": f"srun_{int(age_hours)}",
            "source": "intervals_icu",
            "user_id": "u_local_1",
            "for_date": str(date.today()),
            "started_at": completed_at,
            "completed_at": completed_at,
            "status": status,
            "rows_pulled": 1,
            "rows_accepted": 1,
            "duplicates_skipped": 0,
            "mode": "live",
            "error_class": None,
            "error_message": None,
        }
        used = [c for c in cols if c in values]
        placeholders = ", ".join(["?"] * len(used))
        col_list = ", ".join(used)
        conn.execute(
            f"INSERT INTO sync_run_log ({col_list}) VALUES ({placeholders})",  # nosec B608
            tuple(values[c] for c in used),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Staleness gate
# ---------------------------------------------------------------------------


def test_recent_pull_within_48h_passes_gate(fresh_db):
    """30h-old pull < 48h threshold → derivation succeeds."""
    _seed_sync_run(fresh_db, age_hours=30, status="ok")
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
        allow_stale=False,
        staleness_max_hours=48,
    )
    assert payload["computed"] is True
    assert payload["derived_from"] == "state_snapshot"
    assert "snapshot_read_at" in payload
    assert "staleness_warning" not in payload


def test_pull_older_than_48h_refused_without_override(fresh_db):
    """50h-old pull > 48h threshold + no override → StalenessRefusal."""
    _seed_sync_run(fresh_db, age_hours=50, status="ok")
    with pytest.raises(StalenessRefusal) as excinfo:
        compute_intake_gaps_from_state_snapshot(
            db_path=fresh_db,
            as_of_date=date.today(),
            user_id="u_local_1",
            allow_stale=False,
            staleness_max_hours=48,
        )
    assert "50" in str(excinfo.value) or "older" in str(excinfo.value).lower()
    assert "--allow-stale-snapshot" in str(excinfo.value)


def test_allow_stale_lets_old_pull_through_with_warning(fresh_db):
    """50h-old pull + --allow-stale-snapshot → succeeds with warning."""
    _seed_sync_run(fresh_db, age_hours=50, status="ok")
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
        allow_stale=True,
        staleness_max_hours=48,
    )
    assert payload["computed"] is True
    assert "staleness_warning" in payload


def test_pull_at_47h_passes_gate(fresh_db):
    """Boundary at 47h — under the 48h threshold, derivation succeeds."""
    _seed_sync_run(fresh_db, age_hours=47, status="ok")
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
        allow_stale=False,
        staleness_max_hours=48,
    )
    assert payload["computed"] is True
    assert "staleness_warning" not in payload


def test_pull_at_49h_refused_by_gate(fresh_db):
    """Boundary at 49h — over the 48h threshold, derivation refuses."""
    _seed_sync_run(fresh_db, age_hours=49, status="ok")
    with pytest.raises(StalenessRefusal):
        compute_intake_gaps_from_state_snapshot(
            db_path=fresh_db,
            as_of_date=date.today(),
            user_id="u_local_1",
            allow_stale=False,
            staleness_max_hours=48,
        )


def test_concurrency_100_trials_deterministic(fresh_db):
    """W-W single-read-transaction contract: 100 sequential gap
    derivations against the same DB snapshot produce the same
    output every time. The original PLAN.md spec called for a
    100-trial concurrency test with multiprocessing-injected
    writes; that path tests the SQLite read-isolation guarantee
    `BEGIN IMMEDIATE` provides.

    Codex F-IR-03 fix: this test asserts deterministic output
    across 100 sequential trials against a stable DB. The
    cross-process write-during-read scenario the original spec
    described would require a JSONL tail consumer (not present
    in v0.1.11 — see PLAN § 2.16 narrowed contract)."""
    _seed_sync_run(fresh_db, age_hours=10, status="ok")
    fingerprints = set()
    for _ in range(100):
        payload = compute_intake_gaps_from_state_snapshot(
            db_path=fresh_db,
            as_of_date=date.today(),
            user_id="u_local_1",
        )
        # Hash the gap shape (excluding wall-clock snapshot_read_at).
        shape = tuple(
            (g.get("domain"), g.get("missing_field"), g.get("derived_from"))
            for g in payload["gaps"]
        )
        fingerprints.add(shape)
    assert len(fingerprints) == 1, (
        f"100 trials produced {len(fingerprints)} distinct shapes; "
        f"expected exactly 1 (deterministic)."
    )


def test_no_sync_run_history_refuses_without_override(fresh_db):
    """Codex F-IR2-03: no sync history → refuse unless override.

    Pre-fix this passed permissively; PLAN.md § 2.16 calls for
    fail-closed behaviour ("within the last 48h" strictly implies
    at least one successful sync). The no-history case is
    indistinguishable from "infinitely stale" and refuses by
    default."""
    with pytest.raises(StalenessRefusal) as excinfo:
        compute_intake_gaps_from_state_snapshot(
            db_path=fresh_db,
            as_of_date=date.today(),
            user_id="u_local_1",
            allow_stale=False,
            staleness_max_hours=48,
        )
    assert "no successful sync" in str(excinfo.value).lower()
    assert "--allow-stale-snapshot" in str(excinfo.value)


def test_no_sync_run_history_passes_with_override(fresh_db):
    """No sync history + --allow-stale-snapshot → derivation
    proceeds with a staleness_warning surface."""
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
        allow_stale=True,
        staleness_max_hours=48,
    )
    assert payload["computed"] is True
    assert "staleness_warning" in payload
    assert "no sync" in payload["staleness_warning"].lower()


# ---------------------------------------------------------------------------
# Audit fields on emitted gaps
# ---------------------------------------------------------------------------


def test_emitted_gaps_carry_derived_from_state_snapshot(fresh_db):
    """Every gap emitted by the snapshot path is tagged for audit."""
    _seed_sync_run(fresh_db, age_hours=10, status="ok")
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
        allow_stale=False,
        staleness_max_hours=48,
    )
    for gap in payload["gaps"]:
        assert gap["derived_from"] == "state_snapshot"
        assert "snapshot_read_at" in gap


def test_top_level_payload_carries_audit_fields(fresh_db):
    # Need a successful sync_run_log entry so the staleness gate
    # passes (post-Codex-F-IR2-03 no-history-refuses-by-default).
    _seed_sync_run(fresh_db, age_hours=10, status="ok")
    payload = compute_intake_gaps_from_state_snapshot(
        db_path=fresh_db,
        as_of_date=date.today(),
        user_id="u_local_1",
    )
    assert payload["derived_from"] == "state_snapshot"
    # snapshot_read_at must be a parseable ISO-8601 timestamp.
    parsed = datetime.fromisoformat(payload["snapshot_read_at"])
    assert parsed.tzinfo is not None
