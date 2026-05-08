"""W-E: hai daily re-run state-change supersession (release-blocker).

Per Codex F-PLAN-R2-04 + Codex F-B-02 (v0.1.10): a re-run of
`hai daily` / `hai synthesize` against unchanged synthesis inputs
must be a true no-op (no new plan_id, no new proposal_log rows).
A re-run against changed inputs must auto-supersede with `_v<N>`
rather than overwrite the canonical row in place — preserves the
audit chain.

State-fingerprint primitive (migration 022) makes the same-vs-
different test deterministic.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import initialize_database
from health_agent_infra.core.synthesis import (
    _compute_state_fingerprint,
    run_synthesis,
)


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _seed_proposal(conn, *, domain: str, action: str, rationale: str) -> None:
    payload = {
        "schema_version": f"{domain}_proposal.v1",
        "proposal_id": f"prop_2026-04-28_u_local_1_{domain}_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-28",
        "domain": domain,
        "action": action,
        "action_detail": None,
        "rationale": [rationale],
        "confidence": "low",
        "uncertainty": [],
        # Single placeholder policy decision so the safety validator
        # (policy_decisions_present invariant) passes; W-E test focus is
        # the fingerprint contract, not policy semantics.
        "policy_decisions": [
            {
                "rule_id": "require_min_coverage",
                "decision": "block",
                "note": "test fixture: insufficient coverage",
            }
        ],
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
            None,
            "u_local_1",
            domain,
            "2026-04-28",
            f"{domain}_proposal.v1",
            action,
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


def _seed_all_six_proposals(conn, *, action_suffix: str = "default") -> None:
    """Seed canonical leaf proposals for all six domains.

    `action_suffix` lets tests trigger a fingerprint mismatch by
    altering the rationale. The action token itself stays valid
    per ALLOWED_ACTIONS_BY_DOMAIN."""
    for domain in (
        "recovery", "running", "sleep", "stress",
        "strength", "nutrition",
    ):
        _seed_proposal(
            conn,
            domain=domain,
            action="defer_decision_insufficient_signal",
            rationale=f"seeded test rationale {domain} ({action_suffix})",
        )


def _row_count(db_path: Path, table: str) -> int:
    conn = sqlite3.connect(str(db_path))
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]  # nosec B608
    finally:
        conn.close()


def _read_canonical_fingerprint(db_path: Path) -> str | None:
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT state_fingerprint FROM daily_plan "
            "WHERE daily_plan_id = ?",
            ("plan_2026-04-28_u_local_1",),
        ).fetchone()
        return row[0] if row else None
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Fingerprint determinism
# ---------------------------------------------------------------------------


def test_fingerprint_is_deterministic_across_calls():
    """Same inputs → same fingerprint, byte-identical."""
    proposal = {
        "domain": "recovery",
        "schema_version": "recovery_proposal.v1",
        "action": "defer_decision_insufficient_signal",
        "action_detail": None,
        "rationale": ["a", "b"],
        "confidence": "low",
        "uncertainty": [],
        "policy_decisions": [],
    }
    fp1 = _compute_state_fingerprint(proposals=[proposal], phase_a_firings=[])
    fp2 = _compute_state_fingerprint(proposals=[proposal], phase_a_firings=[])
    assert fp1 == fp2
    assert len(fp1) == 64  # SHA-256 hex


def test_fingerprint_changes_when_action_changes():
    p1 = {"domain": "recovery", "action": "a", "rationale": [], "confidence": "low"}
    p2 = {"domain": "recovery", "action": "b", "rationale": [], "confidence": "low"}
    fp1 = _compute_state_fingerprint(proposals=[p1], phase_a_firings=[])
    fp2 = _compute_state_fingerprint(proposals=[p2], phase_a_firings=[])
    assert fp1 != fp2


def test_fingerprint_excludes_wall_clock_fields():
    """produced_at / validated_at differ across reloads but the
    substantive content is the same. Fingerprint must not change."""
    p1 = {
        "domain": "recovery",
        "action": "a",
        "rationale": [],
        "confidence": "low",
        "produced_at": "2026-04-28T12:00:00+00:00",  # not in fingerprint
    }
    p2 = {
        "domain": "recovery",
        "action": "a",
        "rationale": [],
        "confidence": "low",
        "produced_at": "2026-04-28T13:00:00+00:00",  # different wall-clock
    }
    fp1 = _compute_state_fingerprint(proposals=[p1], phase_a_firings=[])
    fp2 = _compute_state_fingerprint(proposals=[p2], phase_a_firings=[])
    assert fp1 == fp2


# ---------------------------------------------------------------------------
# run_synthesis no-op when state matches
# ---------------------------------------------------------------------------


def test_rerun_with_same_state_is_noop(fresh_db, tmp_path):
    conn = open_connection(fresh_db)
    try:
        _seed_all_six_proposals(conn)
        conn.commit()

        result1 = run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id="u_local_1",
        )
    finally:
        conn.close()

    plans_after_first = _row_count(fresh_db, "daily_plan")
    fp_after_first = _read_canonical_fingerprint(fresh_db)
    assert plans_after_first == 1
    assert fp_after_first is not None
    assert result1.daily_plan_id == "plan_2026-04-28_u_local_1"

    # Second call with identical state.
    conn = open_connection(fresh_db)
    try:
        result2 = run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id="u_local_1",
        )
    finally:
        conn.close()

    # No new plan row written.
    assert _row_count(fresh_db, "daily_plan") == 1
    # Returned canonical id matches first call.
    assert result2.daily_plan_id == result1.daily_plan_id
    # Fingerprint unchanged on disk.
    assert _read_canonical_fingerprint(fresh_db) == fp_after_first


# ---------------------------------------------------------------------------
# run_synthesis auto-supersedes when state changes
# ---------------------------------------------------------------------------


def test_reproject_with_same_content_different_timestamps_is_noop(
    fresh_db, tmp_path
):
    """Codex F-IR2-01 fix verification: a reproject of byte-identical
    semantic content with refreshed `projected_at` / `corrected_at`
    timestamps must NOT trigger auto-supersede. The fingerprint
    hashes content fields only; wall-clock timestamps are excluded.

    Pre-fix the F-IR-01 round-1 implementation hashed
    `projected_at` + `corrected_at` directly, so any normal daily
    reproject of unchanged raw/clean evidence would mint `_v2`
    incorrectly. This test would have failed against that
    implementation.
    """
    from datetime import date as _date_cls

    from health_agent_infra.core.synthesis import run_synthesis

    target_date = _date_cls(2026, 4, 28)

    def _seed_accepted_nutrition(conn, *, projected_at, corrected_at):
        existing = conn.execute(
            "SELECT 1 FROM accepted_nutrition_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (target_date.isoformat(), "u_local_1"),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO accepted_nutrition_state_daily ("
                "  as_of_date, user_id, calories, protein_g, carbs_g, "
                "  fat_g, hydration_l, meals_count, derivation_path, "
                "  derived_from, source, ingest_actor, "
                "  projected_at, corrected_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    target_date.isoformat(), "u_local_1",
                    2400.0, 150.0, 280.0, 80.0, None, 3,
                    "daily_macros", "[]", "user_manual",
                    "claude_agent_v1",
                    projected_at, corrected_at,
                ),
            )
        else:
            # Update timestamps + provenance only — content stays identical.
            conn.execute(
                "UPDATE accepted_nutrition_state_daily SET "
                "  projected_at = ?, corrected_at = ? "
                "WHERE as_of_date = ? AND user_id = ?",
                (
                    projected_at, corrected_at,
                    target_date.isoformat(), "u_local_1",
                ),
            )

    conn = open_connection(fresh_db)
    try:
        # 1. Initial state — content X, projection at T0.
        _seed_accepted_nutrition(
            conn,
            projected_at="2026-04-28T12:00:00+00:00",
            corrected_at=None,
        )
        _seed_all_six_proposals(conn)
        conn.commit()

        result1 = run_synthesis(
            conn,
            for_date=target_date,
            user_id="u_local_1",
        )
        plan_id_1 = result1.daily_plan_id
        assert plan_id_1 == "plan_2026-04-28_u_local_1"

        # 2. Reproject the SAME content but with refreshed timestamps.
        # Simulates the daily-pull-and-clean path running again
        # without any actual state change.
        _seed_accepted_nutrition(
            conn,
            projected_at="2026-04-28T18:00:00+00:00",  # changed
            corrected_at="2026-04-28T18:00:00+00:00",  # changed
        )
        conn.commit()

        # 3. Re-run synthesis — content unchanged, only wall-clock churned.
        result2 = run_synthesis(
            conn,
            for_date=target_date,
            user_id="u_local_1",
        )
    finally:
        conn.close()

    # Cardinal contract: same content → no-op; canonical id returned.
    assert result2.daily_plan_id == plan_id_1, (
        "Codex F-IR2-01 regression: a reproject with refreshed "
        "projected_at / corrected_at but byte-identical content "
        "incorrectly triggered auto-supersede. The fingerprint must "
        "hash semantic content, not wall-clock timestamps."
    )
    # Only one daily_plan row (the canonical) — no _v2 minted.
    assert _row_count(fresh_db, "daily_plan") == 1


def test_rerun_after_intake_nutrition_change_auto_supersedes(
    fresh_db, tmp_path
):
    """Codex F-IR-01 fix verification: the PLAN.md acceptance scenario.

    1. Project a nutrition state for the day (simulates the user
       having logged nutrition A and the intake handler having
       UPSERTed accepted_nutrition_state_daily).
    2. Seed proposals + run synthesis → canonical plan.
    3. Re-project nutrition with different macros (simulates
       `hai intake nutrition --calories ... --protein-g ...` —
       the projector UPSERTs the row and bumps `corrected_at`).
    4. Re-run synthesis WITHOUT modifying proposal_log directly.

    Pre-fix (Codex F-IR-01): step 4 returned the existing canonical
    plan because the fingerprint only hashed proposal payloads
    (which haven't changed) and Phase-A firings.

    Post-fix: the fingerprint now also hashes each accepted_*_state_daily
    row's `corrected_at` + `projected_at`. Step 3 bumped
    `corrected_at` on accepted_nutrition_state_daily, so the new
    fingerprint differs and the re-run auto-supersedes with `_v2`.
    """
    from datetime import date as _date_cls
    import time

    from health_agent_infra.core.synthesis import run_synthesis

    target_date = _date_cls(2026, 4, 28)

    def _seed_accepted_nutrition(conn, *, projected_at: str, corrected_at):
        """Directly seed accepted_nutrition_state_daily — simulates what
        the intake-handler + projector would have UPSERTed when the
        user logged a nutrition intake. Bypasses the raw-row chain so
        the test focuses on the W-E fingerprint contract."""
        existing = conn.execute(
            "SELECT 1 FROM accepted_nutrition_state_daily "
            "WHERE as_of_date = ? AND user_id = ?",
            (target_date.isoformat(), "u_local_1"),
        ).fetchone()
        if existing is None:
            conn.execute(
                "INSERT INTO accepted_nutrition_state_daily ("
                "  as_of_date, user_id, calories, protein_g, carbs_g, "
                "  fat_g, hydration_l, meals_count, derivation_path, "
                "  derived_from, source, ingest_actor, "
                "  projected_at, corrected_at"
                ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    target_date.isoformat(),
                    "u_local_1",
                    2400.0, 150.0, 280.0, 80.0,
                    None, 3,
                    "daily_macros", "[]", "user_manual",
                    "claude_agent_v1",
                    projected_at, corrected_at,
                ),
            )
        else:
            conn.execute(
                "UPDATE accepted_nutrition_state_daily SET "
                "  calories = ?, protein_g = ?, carbs_g = ?, fat_g = ?, "
                "  meals_count = ?, corrected_at = ? "
                "WHERE as_of_date = ? AND user_id = ?",
                (
                    2900.0, 175.0, 320.0, 95.0, 4, corrected_at,
                    target_date.isoformat(), "u_local_1",
                ),
            )

    conn = open_connection(fresh_db)
    try:
        # 1. Seed initial nutrition state (intake nutrition A).
        _seed_accepted_nutrition(
            conn,
            projected_at="2026-04-28T12:00:00+00:00",
            corrected_at=None,
        )

        # 2. Seed proposals for all six domains + run synthesis.
        _seed_all_six_proposals(conn)
        conn.commit()
        result1 = run_synthesis(
            conn,
            for_date=target_date,
            user_id="u_local_1",
        )
        assert result1.daily_plan_id == "plan_2026-04-28_u_local_1"

        # 3. Bump corrected_at on accepted_nutrition_state_daily
        # WITHOUT touching proposal_log. Simulates the user running
        # `hai intake nutrition --calories 2900 ...` mid-day; the
        # intake handler UPSERTs the accepted row and bumps
        # corrected_at, but the proposal payloads would only update
        # if the agent re-runs the readiness skill + re-posts.
        _seed_accepted_nutrition(
            conn,
            projected_at="2026-04-28T12:00:00+00:00",
            corrected_at="2026-04-28T18:00:00+00:00",
        )
        conn.commit()

        # 4. Re-run synthesis. Proposals are byte-identical; only
        # accepted_nutrition_state_daily changed. The new fingerprint
        # captures that via the corrected_at delta.
        result2 = run_synthesis(
            conn,
            for_date=target_date,
            user_id="u_local_1",
        )
    finally:
        conn.close()

    # Auto-supersede: state changed, so _v2 minted.
    assert result2.daily_plan_id == "plan_2026-04-28_u_local_1_v2", (
        "Codex F-IR-01 regression: state-only change (intake nutrition "
        "without re-authoring proposals) did not trigger auto-supersede. "
        f"Got daily_plan_id={result2.daily_plan_id!r}."
    )
    assert _row_count(fresh_db, "daily_plan") == 2


def test_rerun_with_changed_state_auto_supersedes(fresh_db, tmp_path):
    conn = open_connection(fresh_db)
    try:
        _seed_all_six_proposals(conn, action_suffix="A")
        conn.commit()

        result1 = run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id="u_local_1",
        )
        assert result1.daily_plan_id == "plan_2026-04-28_u_local_1"

        # Simulate a state change: re-write the recovery proposal's
        # payload (the fingerprint reads from proposal payloads, so
        # changing the rationale token flips the fingerprint without
        # needing to navigate the chain-key revision protocol).
        new_payload = json.dumps({
            "schema_version": "recovery_proposal.v1",
            "proposal_id": "prop_2026-04-28_u_local_1_recovery_01",
            "user_id": "u_local_1",
            "for_date": "2026-04-28",
            "domain": "recovery",
            "action": "defer_decision_insufficient_signal",
            "action_detail": None,
            "rationale": ["materially different rationale after user intake"],
            "confidence": "low",
            "uncertainty": [],
            "policy_decisions": [
                {
                    "rule_id": "require_min_coverage",
                    "decision": "block",
                    "note": "test fixture: still insufficient",
                }
            ],
            "bounded": True,
        })
        conn.execute(
            "UPDATE proposal_log SET payload_json = ? "
            "WHERE proposal_id = ?",
            (new_payload, "prop_2026-04-28_u_local_1_recovery_01"),
        )
        conn.commit()

        result2 = run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id="u_local_1",
        )
    finally:
        conn.close()

    # Auto-supersede: new id is _v2 (canonical preserved).
    assert result2.daily_plan_id == "plan_2026-04-28_u_local_1_v2"
    # Both plan rows persist.
    assert _row_count(fresh_db, "daily_plan") == 2
