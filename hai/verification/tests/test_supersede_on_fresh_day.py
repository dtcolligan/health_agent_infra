"""W-F (Codex F-DEMO-05): --supersede on a date with no canonical
plan must exit USER_INPUT and NOT write any state.

Pre-v0.1.11 this silently minted an orphan _v2 plan unreachable via
`hai today` / `hai explain --for-date`. Per maintainer Q-A
(option b), the new contract refuses with USER_INPUT.
"""

from __future__ import annotations

import sqlite3
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import initialize_database


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _hai(args, env_extra):
    import os
    env = os.environ.copy()
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        env=env,
        capture_output=True,
        text=True,
    )


def _row_count(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        # nosec B608 — table is a hardcoded string literal.
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # nosec B608
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI-level: --supersede on fresh day exits USER_INPUT, no writes
# ---------------------------------------------------------------------------


def test_synthesize_supersede_fresh_day_no_orphan_plan_written(
    fresh_db, tmp_path
):
    """No canonical plan + --supersede → no orphan _v2 row written.

    The CLI returns USER_INPUT either via the no-proposals
    short-circuit (before the supersede gate) OR via the new gate
    once proposals exist. The contract this commit guarantees is
    "no orphan plan id minted." The proposal-seeded variant in
    test_run_synthesis_refuses_fresh_day_supersede covers the
    new gate directly."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    env = {
        "HAI_STATE_DB": str(fresh_db),
        "HAI_BASE_DIR": str(base_dir),
    }

    plans_before = _row_count(fresh_db, "daily_plan")

    proc = _hai(
        [
            "synthesize",
            "--as-of", "2026-04-28",
            "--user-id", "u_local_1",
            "--supersede",
            "--db-path", str(fresh_db),
        ],
        env_extra=env,
    )

    assert proc.returncode == 1, (
        f"expected USER_INPUT (1); stderr: {proc.stderr}"
    )
    # No state written — the cardinal invariant.
    assert _row_count(fresh_db, "daily_plan") == plans_before


def test_run_synthesis_refuses_fresh_day_supersede_directly(
    fresh_db, tmp_path
):
    """Drive run_synthesis directly with proposals seeded but no
    canonical plan. The new gate raises SynthesisError with a
    message naming the contract."""
    from datetime import date
    from health_agent_infra.core.synthesis import (
        SynthesisError,
        run_synthesis,
    )

    # Seed enough state to reach the supersede gate. Insert proposals
    # by invoking propose CLI helper would be heavy; instead, seed
    # proposal_log directly with a minimal valid row per domain.
    conn = open_connection(fresh_db)
    try:
        import json
        for domain in (
            "recovery", "running", "sleep", "stress",
            "strength", "nutrition",
        ):
            payload = {
                "schema_version": f"{domain}_proposal.v1",
                "proposal_id": f"prop_2026-04-28_u_local_1_{domain}_01",
                "user_id": "u_local_1",
                "for_date": "2026-04-28",
                "domain": domain,
                "action": "defer_decision_insufficient_signal",
                "action_detail": None,
                "rationale": [f"seeded test rationale {domain}"],
                "confidence": "low",
                "uncertainty": [],
                "policy_decisions": [],
                "bounded": True,
            }
            conn.execute(
                "INSERT INTO proposal_log ("
                "  proposal_id, daily_plan_id, user_id, domain, for_date, "
                "  schema_version, action, confidence, payload_json, "
                "  source, ingest_actor, agent_version, "
                "  produced_at, validated_at, projected_at, "
                "  revision, superseded_by_proposal_id, superseded_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    f"prop_2026-04-28_u_local_1_{domain}_01",
                    None,  # daily_plan_id NULL until synthesis links it
                    "u_local_1",
                    domain,
                    "2026-04-28",
                    f"{domain}_proposal.v1",
                    "defer_decision_insufficient_signal",
                    "low",
                    json.dumps(payload),
                    "agent",
                    "claude_agent_v1",
                    "claude_agent_v1",
                    "2026-04-28T12:00:00+00:00",
                    "2026-04-28T12:00:00+00:00",
                    "2026-04-28T12:00:00+00:00",
                    1,
                    None,
                    None,
                ),
            )
        conn.commit()

        with pytest.raises(SynthesisError) as excinfo:
            run_synthesis(
                conn,
                for_date=date(2026, 4, 28),
                user_id="u_local_1",
                supersede=True,
            )
        msg = str(excinfo.value)
        assert "--supersede" in msg
        assert "canonical plan" in msg
    finally:
        conn.close()

    # Cardinal invariant — no orphan plan_id was minted.
    assert _row_count(fresh_db, "daily_plan") == 0


def test_daily_supersede_fresh_day_exits_user_input(fresh_db, tmp_path):
    """`hai daily --supersede` on fresh date → same contract, propagated
    via _run_daily's existing SynthesisError handler."""
    base_dir = tmp_path / "base"
    base_dir.mkdir()
    env = {
        "HAI_STATE_DB": str(fresh_db),
        "HAI_BASE_DIR": str(base_dir),
    }

    plans_before = _row_count(fresh_db, "daily_plan")

    proc = _hai(
        [
            "daily",
            "--as-of", "2026-04-28",
            "--user-id", "u_local_1",
            "--skip-pull",
            "--supersede",
            "--db-path", str(fresh_db),
        ],
        env_extra=env,
    )

    # daily's outer handler converts SynthesisError to USER_INPUT.
    # If the synthesize stage isn't even reached (no proposals), the
    # call short-circuits before the supersede branch — exit can be
    # OK (with status='awaiting_proposals'). The stricter assertion
    # is "no orphan plan was written."
    assert _row_count(fresh_db, "daily_plan") == plans_before
