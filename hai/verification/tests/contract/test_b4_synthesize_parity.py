"""v0.1.9 B4 — direct ``hai synthesize`` parity with ``hai daily``.

Codex 2026-04-26 caught two divergences between the daily and direct-
synthesize paths:

1. ``hai daily`` enforces an expected-domain proposal gate; direct
   ``hai synthesize`` only refused on zero proposals. Result: a direct
   synthesize could commit a partial-domain plan.
2. ``run_synthesis`` and ``build_synthesis_bundle`` called
   ``build_snapshot`` without ``evidence_bundle``, so per-domain
   ``classified_state`` was missing. X1 reads
   ``sleep.classified_state.sleep_debt_band``; absent bundle ⇒ X1
   silently never fired on the direct path even when ``hai daily`` would
   have softened or blocked the same hard proposal.

This file pins the v0.1.9 fixes:

  - ``run_synthesis`` accepts ``expected_domains`` and refuses on
    missing canonical-leaf proposals with invariant
    ``missing_expected_proposals``.
  - ``cmd_synthesize`` defaults expected_domains to the v1 six-domain
    set; ``--domains`` narrows; ``--domains ''`` opts out.
  - ``build_snapshot`` always populates ``classified_state`` on every
    domain block, regardless of evidence_bundle. X1 / X2 / X3 / X4 /
    X5 / X6 / X7 / X9 fire identically across daily and direct paths.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    initialize_database, open_connection, project_proposal,
)
from health_agent_infra.core.synthesis import (
    SynthesisError, V1_EXPECTED_DOMAINS, run_synthesis,
)
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 26)
USER = "u_b4_parity"


def _make_proposal(domain: str, **overrides) -> dict:
    actions = {
        "recovery": "proceed_with_planned_session",
        "running": "proceed_with_planned_run",
        "sleep": "maintain_schedule",
        "strength": "proceed_with_planned_session",
        "stress": "maintain_routine",
        "nutrition": "maintain_targets",
    }
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": actions[domain],
        "action_detail": None,
        "rationale": [f"{domain}_baseline"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "n"},
        ],
        "bounded": True,
    }
    base.update(overrides)
    return base


@pytest.fixture
def db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def _seed_six_proposals(db):
    for d in ("recovery", "running", "sleep", "strength", "stress", "nutrition"):
        project_proposal(db, _make_proposal(d))


# ---------------------------------------------------------------------------
# Expected-domain gate
# ---------------------------------------------------------------------------


def test_direct_synthesize_rejects_missing_expected_domain(db):
    """Missing recovery proposal with expected_domains=v1_six rejects."""

    for d in ("running", "sleep", "strength", "stress", "nutrition"):
        project_proposal(db, _make_proposal(d))

    with pytest.raises(SynthesisError) as exc_info:
        run_synthesis(
            db, for_date=FOR_DATE, user_id=USER,
            snapshot={"recovery": {}, "running": {}, "sleep": {}, "stress": {},
                      "strength": {}, "nutrition": {}},
            expected_domains=V1_EXPECTED_DOMAINS,
        )
    assert "missing_expected_proposals" in str(exc_info.value)
    assert "recovery" in str(exc_info.value)
    # No daily_plan landed.
    assert db.execute("SELECT COUNT(*) FROM daily_plan").fetchone()[0] == 0


def test_direct_synthesize_accepts_complete_six_domain_set(db):
    """All six expected proposals present → synthesis commits cleanly."""

    _seed_six_proposals(db)
    snapshot = {
        "recovery": {"classified_state": {"sleep_debt_band": "low"},
                     "today": {"acwr_ratio": 1.0}},
        "running": {},
        "sleep": {"classified_state": {"sleep_debt_band": "low"}},
        "stress": {"classified_state": {"garmin_stress_band": "low"},
                   "today_body_battery": 75},
        "strength": {},
        "nutrition": {},
    }
    result = run_synthesis(
        db, for_date=FOR_DATE, user_id=USER,
        snapshot=snapshot,
        expected_domains=V1_EXPECTED_DOMAINS,
    )
    assert len(result.recommendation_ids) == 6


def test_direct_synthesize_narrowed_domains_accepts_subset(db):
    """``expected_domains={'recovery', 'running'}`` accepts a 2-domain
    plan; the v1 six-domain default would have rejected it."""

    project_proposal(db, _make_proposal("recovery"))
    project_proposal(db, _make_proposal("running"))

    snapshot = {
        "recovery": {"classified_state": {"sleep_debt_band": "low"},
                     "today": {"acwr_ratio": 1.0}},
        "running": {},
        "sleep": {}, "stress": {"today_body_battery": 75},
        "strength": {}, "nutrition": {},
    }
    result = run_synthesis(
        db, for_date=FOR_DATE, user_id=USER,
        snapshot=snapshot,
        expected_domains=frozenset({"recovery", "running"}),
    )
    assert len(result.recommendation_ids) == 2


def test_direct_synthesize_default_no_gate_legacy_behavior(db):
    """``expected_domains=None`` (legacy default) keeps the pre-v0.1.9
    permissive behavior so test fixtures and the eval runner still
    work. ``hai synthesize`` (the CLI surface) defaults to the v1 six
    instead — this test pins that the runtime layer stays flexible."""

    project_proposal(db, _make_proposal("recovery"))
    snapshot = {
        "recovery": {"classified_state": {"sleep_debt_band": "low"},
                     "today": {"acwr_ratio": 1.0}},
        "running": {}, "sleep": {}, "stress": {},
        "strength": {}, "nutrition": {},
    }
    result = run_synthesis(
        db, for_date=FOR_DATE, user_id=USER, snapshot=snapshot,
    )
    assert len(result.recommendation_ids) == 1


# ---------------------------------------------------------------------------
# Snapshot classified_state always populated (X1 parity)
# ---------------------------------------------------------------------------


def test_build_snapshot_populates_classified_state_without_bundle(tmp_path: Path):
    """The most surgical X1 parity check: ``build_snapshot`` called
    without ``evidence_bundle`` (the path ``run_synthesis`` and
    ``build_synthesis_bundle`` use) must populate
    ``sleep.classified_state.sleep_debt_band``. Pre-v0.1.9 this key
    was absent, causing X1a / X1b to silently no-op."""

    from health_agent_infra.core.state.snapshot import build_snapshot

    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        snapshot = build_snapshot(
            conn, as_of_date=FOR_DATE, user_id=USER, lookback_days=14,
        )
    finally:
        conn.close()

    # classified_state must be present on every domain block.
    for domain in ("recovery", "running", "sleep", "stress",
                   "strength", "nutrition"):
        assert "classified_state" in snapshot[domain], (
            f"snapshot[{domain!r}] missing classified_state — direct "
            f"synthesize will silently miss X-rule firings"
        )
        assert "policy_result" in snapshot[domain], (
            f"snapshot[{domain!r}] missing policy_result"
        )

    # Sleep domain specifically — the X1 parity field.
    assert "sleep_debt_band" in snapshot["sleep"]["classified_state"]


def test_build_synthesis_bundle_includes_classified_state(tmp_path: Path):
    """The skill-overlay seam: ``build_synthesis_bundle`` returns the
    snapshot a synthesis skill reads. v0.1.9 B4 makes that snapshot
    consistent with the daily-path snapshot."""

    from health_agent_infra.core.synthesis import build_synthesis_bundle

    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        # Need at least one proposal so build_synthesis_bundle proceeds.
        project_proposal(conn, _make_proposal("recovery"))
        bundle = build_synthesis_bundle(
            conn, for_date=FOR_DATE, user_id=USER,
        )
    finally:
        conn.close()

    snapshot = bundle["snapshot"]
    assert "classified_state" in snapshot["sleep"]
    assert "sleep_debt_band" in snapshot["sleep"]["classified_state"]
