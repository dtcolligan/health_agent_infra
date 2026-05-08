"""W-FBC-2 multi-domain rollout: per-domain carryover-uncertainty tokens.

The recovery prototype in ``test_re_propose_all_recovery.py`` proves
the synthesis-side enforcement on the recovery domain. This file
parameterises the same shape across the other five domains
(running / sleep / stress / strength / nutrition) — each domain
emits its own ``<domain>_proposal_carryover_under_re_propose_all``
token when its envelope is stale + the operator passed
``--re-propose-all``.

Coverage shape per PLAN §2.A W-FBC-2 acceptance:

  - ``hai daily --re-propose-all`` produces re-proposed daily-plan
    rows across all 6 domains under verifiable test fixtures.
  - Each domain emits its own token, not a single global one.
  - Token is per-domain + scoped to that domain's recommendation row;
    a stale envelope on running does NOT add a carryover token to
    sleep / stress / strength / nutrition / recovery.

The tokens are independent. v0.1.13 W-FBC-2 ships option A (default)
per the archived
``hai/reporting/docs/archive/cycle_artifacts/supersede_domain_coverage.md``;
the per-domain
fingerprint primitive (option B) is NOT shipped this cycle.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import initialize_database
from health_agent_infra.core.synthesis import (
    RE_PROPOSE_ALL_FRESHNESS_THRESHOLD,
    run_synthesis,
)


_FOR_DATE = "2026-04-28"
_USER_ID = "u_multi_domain"
_SIX_DOMAINS: tuple[str, ...] = (
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
)


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _seed_proposal(conn, *, domain: str, authored_at: datetime) -> None:
    payload = {
        "schema_version": f"{domain}_proposal.v1",
        "proposal_id": f"prop_{_FOR_DATE}_{_USER_ID}_{domain}_01",
        "user_id": _USER_ID,
        "for_date": _FOR_DATE,
        "domain": domain,
        "action": "defer_decision_insufficient_signal",
        "action_detail": None,
        "rationale": [f"multi-domain fixture ({domain})"],
        "confidence": "low",
        "uncertainty": [],
        "policy_decisions": [
            {
                "rule_id": "require_min_coverage",
                "decision": "block",
                "note": "fixture",
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
            f"prop_{_FOR_DATE}_{_USER_ID}_{domain}_01",
            None,
            _USER_ID,
            domain,
            _FOR_DATE,
            f"{domain}_proposal.v1",
            "defer_decision_insufficient_signal",
            "low",
            json.dumps(payload),
            "agent",
            "claude_agent_v1",
            "claude_agent_v1",
            authored_at.isoformat(),
            authored_at.isoformat(),
            authored_at.isoformat(),
            1,
            None,
            None,
        ),
    )


def _read_uncertainty_by_domain(db_path: Path) -> dict[str, list[str]]:
    conn = open_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT payload_json FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ?",
            (_FOR_DATE, _USER_ID),
        ).fetchall()
    finally:
        conn.close()
    out: dict[str, list[str]] = {}
    for row in rows:
        rec = json.loads(row["payload_json"])
        out[rec["domain"]] = list(rec.get("uncertainty") or [])
    return out


@pytest.mark.parametrize("stale_domain", list(_SIX_DOMAINS))
def test_only_stale_domain_emits_its_own_carryover_token(
    fresh_db, stale_domain: str,
):
    """For each of the six domains: when only that domain's envelope
    is stale (others fresh) and the operator passed ``--re-propose-all``,
    that domain — and ONLY that domain — gets its carryover token.

    Six independent assertions, one per domain, parameterised so a
    regression on any single domain surfaces with a domain-tagged
    pytest failure id."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(seconds=10)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=30)

    conn = open_connection(fresh_db)
    try:
        for domain in _SIX_DOMAINS:
            _seed_proposal(
                conn,
                domain=domain,
                authored_at=stale if domain == stale_domain else fresh,
            )
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
    finally:
        conn.close()

    uncertainty_by_domain = _read_uncertainty_by_domain(fresh_db)
    expected_token = f"{stale_domain}_proposal_carryover_under_re_propose_all"

    assert expected_token in uncertainty_by_domain[stale_domain], (
        f"stale {stale_domain} envelope expected to fire "
        f"{expected_token!r}; got {uncertainty_by_domain[stale_domain]!r}"
    )
    for domain in _SIX_DOMAINS:
        if domain == stale_domain:
            continue
        token = f"{domain}_proposal_carryover_under_re_propose_all"
        assert token not in uncertainty_by_domain[domain], (
            f"fresh {domain} envelope must not fire {token!r}; "
            f"got {uncertainty_by_domain[domain]!r}"
        )


def test_all_six_stale_emits_six_distinct_carryover_tokens(fresh_db):
    """When every envelope is stale + flag set, each domain's
    recommendation gets its own (domain-specific) carryover token —
    six distinct tokens across six recommendations, never crossed."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=30)

    conn = open_connection(fresh_db)
    try:
        for domain in _SIX_DOMAINS:
            _seed_proposal(conn, domain=domain, authored_at=stale)
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
    finally:
        conn.close()

    uncertainty_by_domain = _read_uncertainty_by_domain(fresh_db)
    for domain in _SIX_DOMAINS:
        own_token = f"{domain}_proposal_carryover_under_re_propose_all"
        assert own_token in uncertainty_by_domain[domain], (
            f"{domain} missing own carryover token; "
            f"got {uncertainty_by_domain[domain]!r}"
        )
        for other in _SIX_DOMAINS:
            if other == domain:
                continue
            other_token = (
                f"{other}_proposal_carryover_under_re_propose_all"
            )
            assert other_token not in uncertainty_by_domain[domain], (
                f"{domain} carries cross-domain token {other_token!r}; "
                f"got {uncertainty_by_domain[domain]!r}"
            )


def test_all_six_fresh_emits_zero_carryover_tokens(fresh_db):
    """The negative-coverage case: every envelope fresh + flag set →
    zero carryover tokens emitted across all 6 domains. Proves the
    threshold check is the gate, not the flag alone."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(seconds=5)

    conn = open_connection(fresh_db)
    try:
        for domain in _SIX_DOMAINS:
            _seed_proposal(conn, domain=domain, authored_at=fresh)
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
    finally:
        conn.close()

    uncertainty_by_domain = _read_uncertainty_by_domain(fresh_db)
    for domain, tokens in uncertainty_by_domain.items():
        for token in tokens:
            assert "_proposal_carryover_under_re_propose_all" not in token, (
                f"{domain} fired carryover token {token!r} despite "
                f"fresh envelope"
            )
