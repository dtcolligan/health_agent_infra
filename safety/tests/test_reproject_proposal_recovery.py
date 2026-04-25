"""Phase B — proposal JSONL recovery tests (v0.1.4 blocking).

Pins the contract Codex flagged in the 2026-04-24 strategic report (P1 #2):
``hai propose`` writes ``<domain>_proposals.jsonl`` as the durable audit
boundary, but before this fix ``hai state reproject`` ignored those files.
Audit logs you can't replay are decorative.

Coverage required by the brief:
  - Replay covers each of the six per-domain proposal JSONL files.
  - Validation: corrupt/invalid lines are SKIPPED (counted), not raised —
    a single bad line in a long log doesn't abort the whole reproject.
  - Idempotency: re-running reproject on the same JSONL produces the
    same proposal_log state.
  - Recovery scenario: DB wiped → JSONL replayed → proposal_log restored.
  - Reproject counts include `proposals` and `proposals_skipped_invalid`.
  - Discovery: a base_dir containing ONLY proposal JSONLs (no other
    audit logs) is now valid (no longer raises ReprojectBaseDirError).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    reproject_from_jsonl,
)


FOR_DATE = date(2026, 4, 22)
USER = "u_phaseb"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_DEFAULT_ACTIONS: dict[str, str] = {
    "recovery": "proceed_with_planned_session",
    "running": "proceed_with_planned_run",
    "sleep": "maintain_schedule",
    "strength": "proceed_with_planned_session",
    "stress": "maintain_routine",
    "nutrition": "maintain_targets",
}

_PROPOSAL_SCHEMA: dict[str, str] = {
    "recovery": "recovery_proposal.v1",
    "running": "running_proposal.v1",
    "sleep": "sleep_proposal.v1",
    "strength": "strength_proposal.v1",
    "stress": "stress_proposal.v1",
    "nutrition": "nutrition_proposal.v1",
}


def _proposal(
    *,
    domain: str,
    proposal_id: str | None = None,
    rationale: list[str] | None = None,
    confidence: str = "high",
) -> dict:
    return {
        "schema_version": _PROPOSAL_SCHEMA[domain],
        "proposal_id": proposal_id or f"prop_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": _DEFAULT_ACTIONS[domain],
        "action_detail": None,
        "rationale": rationale if rationale is not None else ["seeded for replay"],
        "confidence": confidence,
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }


def _write_jsonl(base: Path, domain: str, *proposals: dict) -> Path:
    path = base / f"{domain}_proposals.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for p in proposals:
            fh.write(json.dumps(p, sort_keys=True) + "\n")
    return path


@pytest.fixture
def db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# 1. Discovery — base_dir with only proposal JSONLs is valid
# ---------------------------------------------------------------------------

def test_proposal_jsonl_alone_satisfies_discovery_gate(db, base_dir):
    """Pre-Phase-B, a base_dir containing ONLY proposal JSONLs would have
    raised ReprojectBaseDirError because no other group's JSONL was
    present. With Phase B, the proposals group counts as a valid group."""

    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))
    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 1
    assert counts["proposals_skipped_invalid"] == 0


# ---------------------------------------------------------------------------
# 2. Per-domain replay
# ---------------------------------------------------------------------------

def test_replay_covers_all_six_domains(db, base_dir):
    """One proposal per domain → six rows in proposal_log after replay."""

    for domain in ("recovery", "running", "sleep", "strength", "stress", "nutrition"):
        _write_jsonl(base_dir, domain, _proposal(domain=domain))

    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 6

    rows = db.execute(
        "SELECT domain FROM proposal_log ORDER BY domain"
    ).fetchall()
    assert [r["domain"] for r in rows] == [
        "nutrition", "recovery", "running", "sleep", "strength", "stress",
    ]


# ---------------------------------------------------------------------------
# 3. Idempotency
# ---------------------------------------------------------------------------

def test_replay_is_idempotent_on_proposal_id(db, base_dir):
    """Re-running reproject on the same JSONL produces the same proposal_log."""

    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))

    reproject_from_jsonl(db, base_dir)
    first_count = db.execute("SELECT COUNT(*) FROM proposal_log").fetchone()[0]

    reproject_from_jsonl(db, base_dir)
    second_count = db.execute("SELECT COUNT(*) FROM proposal_log").fetchone()[0]

    assert first_count == 1
    assert second_count == 1


# ---------------------------------------------------------------------------
# 4. Revision chains preserved from JSONL append order
# ---------------------------------------------------------------------------

def test_revision_chain_replays_in_jsonl_order(db, base_dir):
    """Two proposals on the same chain key replay as a 2-link chain:
    revision 1 + revision 2, with the leaf marker on rev 2."""

    p1 = _proposal(domain="recovery", rationale=["initial"])
    p2 = _proposal(
        domain="recovery", rationale=["revised"],
        proposal_id=f"prop_{FOR_DATE}_{USER}_recovery_02",
    )
    _write_jsonl(base_dir, "recovery", p1, p2)

    reproject_from_jsonl(db, base_dir)

    rows = db.execute(
        "SELECT proposal_id, revision, superseded_by_proposal_id "
        "FROM proposal_log "
        "WHERE domain = 'recovery' "
        "ORDER BY revision"
    ).fetchall()

    assert len(rows) == 2
    # First: revision 1, points to revision 2 via superseded_by.
    assert rows[0]["revision"] == 1
    assert rows[0]["superseded_by_proposal_id"] is not None
    # Second: revision 2 (the leaf), no forward pointer.
    assert rows[1]["revision"] == 2
    assert rows[1]["superseded_by_proposal_id"] is None


def test_canonical_leaf_after_replay_is_revision_2(db, base_dir):
    """The chain walker should resolve to the latest revision after replay."""

    p1 = _proposal(domain="running", rationale=["initial"])
    p2 = _proposal(
        domain="running", rationale=["revised"],
        proposal_id=f"prop_{FOR_DATE}_{USER}_running_02",
    )
    _write_jsonl(base_dir, "running", p1, p2)

    reproject_from_jsonl(db, base_dir)

    leaf_rows = db.execute(
        "SELECT proposal_id, revision FROM proposal_log "
        "WHERE domain = 'running' "
        "AND superseded_by_proposal_id IS NULL"
    ).fetchall()
    assert len(leaf_rows) == 1
    assert leaf_rows[0]["revision"] == 2


# ---------------------------------------------------------------------------
# 5. Validation: corrupt lines counted, not raised
# ---------------------------------------------------------------------------

def test_invalid_json_line_skipped_and_counted(db, base_dir):
    """A non-JSON line must not abort the reproject; it's counted as
    skipped and the rest of the file replays cleanly."""

    path = base_dir / "recovery_proposals.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(_proposal(domain="recovery")) + "\n")
        fh.write("this is not valid json\n")
        fh.write(json.dumps(_proposal(
            domain="recovery", rationale=["second valid line"],
            proposal_id=f"prop_{FOR_DATE}_{USER}_recovery_02",
        )) + "\n")

    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 2
    assert counts["proposals_skipped_invalid"] == 1


def test_validation_failure_skips_proposal(db, base_dir):
    """A proposal with a banned uncertainty token (or any validation
    failure) is skipped, not raised. Surfaces in the count."""

    bad = _proposal(domain="sleep")
    bad["confidence"] = "invalid_band"  # forces ProposalValidationError
    _write_jsonl(base_dir, "sleep", _proposal(domain="sleep"), bad)

    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 1
    assert counts["proposals_skipped_invalid"] == 1


def test_blank_lines_in_jsonl_skipped_silently(db, base_dir):
    """Trailing newlines / blank lines should not be counted as invalid."""

    path = base_dir / "stress_proposals.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(_proposal(domain="stress")) + "\n\n\n")

    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 1
    assert counts["proposals_skipped_invalid"] == 0


# ---------------------------------------------------------------------------
# 6. Recovery scenario: DB wipe → JSONL replay → restored state
# ---------------------------------------------------------------------------

def test_db_wipe_then_reproject_restores_proposal_log(db, base_dir):
    """The headline scenario: a user's DB gets corrupted; they run
    reproject from JSONL; proposal_log comes back."""

    p1 = _proposal(domain="recovery")
    p2 = _proposal(
        domain="strength", proposal_id="prop_strength_special",
    )
    _write_jsonl(base_dir, "recovery", p1)
    _write_jsonl(base_dir, "strength", p2)

    # Simulate the recovery: brand-new DB, only the JSONLs survive.
    counts = reproject_from_jsonl(db, base_dir)

    assert counts["proposals"] == 2
    surviving = db.execute(
        "SELECT proposal_id, domain FROM proposal_log ORDER BY domain"
    ).fetchall()
    assert len(surviving) == 2
    assert {r["domain"] for r in surviving} == {"recovery", "strength"}


def test_partial_jsonl_set_replays_only_present_domains(db, base_dir):
    """Operator JSONLs aren't always complete — only domains with files
    on disk get rebuilt."""

    _write_jsonl(base_dir, "running", _proposal(domain="running"))
    # No other domain JSONLs.

    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 1

    rows = db.execute("SELECT domain FROM proposal_log").fetchall()
    assert [r["domain"] for r in rows] == ["running"]


# ---------------------------------------------------------------------------
# 7. Atomicity: a mid-replay failure rolls back proposal_log
# ---------------------------------------------------------------------------

def test_replay_truncates_proposal_log_before_replaying(db, base_dir):
    """After Phase B, reproject TRUNCATES proposal_log before replaying.
    Pre-existing rows that aren't in the JSONL should be removed."""

    # Seed the DB with a stale row that isn't in any JSONL.
    db.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at,
            revision, superseded_by_proposal_id, superseded_at
        ) VALUES (
            'prop_stale', NULL, 'u_phaseb', 'recovery', '2026-01-01',
            'recovery_proposal.v1', 'proceed_with_planned_session', 'high',
            '{}', 'test', 'test', 'test', '2026-01-01T00:00:00+00:00',
            '2026-01-01T00:00:00+00:00', '2026-01-01T00:00:00+00:00',
            1, NULL, NULL
        )
        """
    )
    db.commit()

    # JSONL has a different proposal.
    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))

    reproject_from_jsonl(db, base_dir)

    rows = db.execute(
        "SELECT proposal_id FROM proposal_log"
    ).fetchall()
    ids = {r["proposal_id"] for r in rows}
    assert "prop_stale" not in ids
    assert len(ids) == 1


# ---------------------------------------------------------------------------
# 8. Orphan-prevention: refuse cleanly when synthesis-side tables would
# be stranded by a destructive proposal_log / recommendation_log delete.
# Regression for v0.1.6 W1 / B5 — the FK constraint failure observed in
# the 2026-04-25 user session.
# ---------------------------------------------------------------------------

def _seed_synthesis_tables(db) -> None:
    """Populate proposal_log + daily_plan + planned_recommendation to
    reproduce the FK-failure conditions. Schemas mirror the head-of-tree
    migrations 001–018 (verified against live DB schema)."""

    db.execute(
        """
        INSERT INTO proposal_log (
            proposal_id, daily_plan_id, user_id, domain, for_date,
            schema_version, action, confidence, payload_json,
            source, ingest_actor, agent_version,
            produced_at, validated_at, projected_at, revision
        ) VALUES (
            'prop_seed', NULL, 'u_phaseb', 'recovery', '2026-04-22',
            'recovery_proposal.v1', 'proceed_with_planned_session', 'high',
            '{}', 'test', 'test', 'test',
            '2026-04-22T00:00:00+00:00', '2026-04-22T00:00:00+00:00',
            '2026-04-22T00:00:00+00:00', 1
        )
        """
    )
    db.execute(
        """
        INSERT INTO daily_plan (
            daily_plan_id, user_id, for_date, synthesized_at,
            recommendation_ids_json, proposal_ids_json, x_rules_fired_json,
            source, ingest_actor, validated_at, projected_at
        ) VALUES (
            'plan_seed', 'u_phaseb', '2026-04-22',
            '2026-04-22T00:00:00+00:00',
            '[]', '["prop_seed"]', '[]',
            'test', 'test',
            '2026-04-22T00:00:00+00:00', '2026-04-22T00:00:00+00:00'
        )
        """
    )
    db.execute(
        """
        INSERT INTO planned_recommendation (
            planned_id, daily_plan_id, proposal_id,
            user_id, for_date, domain,
            action, confidence, action_detail_json,
            schema_version, source, ingest_actor, captured_at
        ) VALUES (
            'planned_seed', 'plan_seed', 'prop_seed',
            'u_phaseb', '2026-04-22', 'recovery',
            'proceed_with_planned_session', 'high', '{}',
            'planned_recommendation.v1', 'test', 'test',
            '2026-04-22T00:00:00+00:00'
        )
        """
    )
    db.commit()


def test_reproject_refuses_when_synthesis_tables_would_be_orphaned(
    db, base_dir,
):
    """Reproduces the 2026-04-25 user-session FK failure: a populated
    planned_recommendation table FKs into proposal_log (migration 011),
    so a naive `DELETE FROM proposal_log` raises sqlite3.IntegrityError
    mid-transaction. After v0.1.6 W1, reproject detects this BEFORE
    damage and raises ReprojectOrphansError naming the row counts +
    pointing at --cascade-synthesis."""

    from health_agent_infra.core.state import ReprojectOrphansError

    _seed_synthesis_tables(db)

    # Write a proposal JSONL so has_proposals_group is True and the
    # destructive path would be reached.
    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))

    with pytest.raises(ReprojectOrphansError) as exc_info:
        reproject_from_jsonl(db, base_dir)

    msg = str(exc_info.value)
    assert "planned_recommendation=1" in msg
    assert "daily_plan=1" in msg
    assert "--cascade-synthesis" in msg

    # Transaction was rolled back: synthesis tables still present.
    assert db.execute(
        "SELECT COUNT(*) FROM planned_recommendation"
    ).fetchone()[0] == 1
    assert db.execute(
        "SELECT COUNT(*) FROM proposal_log"
    ).fetchone()[0] == 1


def test_reproject_with_cascade_synthesis_clears_orphans_and_replays(
    db, base_dir,
):
    """Opt-in cascade: --cascade-synthesis deletes synthesis-side tables
    in dependency order, then proceeds with the normal replay. Operator
    must re-run `hai synthesize` afterwards to repopulate them."""

    _seed_synthesis_tables(db)
    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))

    counts = reproject_from_jsonl(db, base_dir, cascade_synthesis=True)
    assert counts["proposals"] == 1

    # Synthesis tables wiped.
    assert db.execute(
        "SELECT COUNT(*) FROM planned_recommendation"
    ).fetchone()[0] == 0
    assert db.execute(
        "SELECT COUNT(*) FROM x_rule_firing"
    ).fetchone()[0] == 0

    # proposal_log replayed from JSONL: seed row gone, JSONL row present.
    rows = db.execute("SELECT proposal_id FROM proposal_log").fetchall()
    ids = {r["proposal_id"] for r in rows}
    assert "prop_seed" not in ids
    assert any(pid.startswith("prop_") for pid in ids)


def test_reproject_succeeds_when_synthesis_tables_empty(db, base_dir):
    """No orphan check needed when planned_recommendation / daily_plan /
    x_rule_firing are empty — reproject behaves as before."""

    _write_jsonl(base_dir, "recovery", _proposal(domain="recovery"))
    counts = reproject_from_jsonl(db, base_dir)
    assert counts["proposals"] == 1
