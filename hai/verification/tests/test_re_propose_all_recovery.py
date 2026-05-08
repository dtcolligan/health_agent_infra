"""W-FBC-2 recovery prototype: --re-propose-all carryover-uncertainty token.

Per the archived
``hai/reporting/docs/archive/cycle_artifacts/supersede_domain_coverage.md``
(option A default):
when ``--re-propose-all`` is set, ``run_synthesis`` evaluates the
authored-at envelope of each canonical-leaf ``proposal_log`` row. Any
domain whose envelope is older than ``now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD``
gets a ``<domain>_proposal_carryover_under_re_propose_all`` token
appended to that recommendation's ``uncertainty[]`` list.

Three persona-style scenarios per the design doc (P1/P5/P9):

  - **P1 (Dom baseline)** — morning fresh-state synthesis with the flag
    set. Every proposal was authored within the session, so no domain
    triggers the carryover token. The recommendation's ``uncertainty[]``
    surface stays clean.
  - **P5 (female multi-sport)** — thin-history with a state delta. The
    flag is set; recovery's ``proposal_log`` envelope is stale (the
    agent did NOT re-author the recovery proposal in this synthesis
    cycle). The carryover token fires for recovery only — other
    domains stay clean because their envelopes are fresh.
  - **P9 (older female endurance)** — supersede-after-intake-change
    baseline. Flag is absent, so no domain triggers the carryover
    token regardless of envelope age — option A is opt-in via the
    operator flag, not implicit on every supersede.

The recovery prototype is the W-FBC-2 smoke surface; the multi-domain
rollout in ``test_re_propose_all_multi_domain.py`` walks the same
shape across running / sleep / stress / strength / nutrition.
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
_USER_ID = "u_persona_test"
_SIX_DOMAINS: tuple[str, ...] = (
    "recovery", "running", "sleep", "stress", "strength", "nutrition",
)


@pytest.fixture
def fresh_db(tmp_path) -> Path:
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    return db_path


def _seed_proposal(
    conn,
    *,
    domain: str,
    authored_at: datetime,
) -> None:
    """Seed one canonical-leaf proposal at a chosen ``authored_at``.

    The same timestamp lands in both ``produced_at`` and ``validated_at``
    so the envelope-authored-at lookup (``produced_at`` preferred,
    ``validated_at`` fallback) returns the test's chosen value
    deterministically. ``defer_decision_insufficient_signal`` is used
    across all six domains because it is the one action every domain
    enum accepts.
    """

    payload = {
        "schema_version": f"{domain}_proposal.v1",
        "proposal_id": f"prop_{_FOR_DATE}_{_USER_ID}_{domain}_01",
        "user_id": _USER_ID,
        "for_date": _FOR_DATE,
        "domain": domain,
        "action": "defer_decision_insufficient_signal",
        "action_detail": None,
        "rationale": [f"persona test rationale ({domain})"],
        "confidence": "low",
        "uncertainty": [],
        "policy_decisions": [
            {
                "rule_id": "require_min_coverage",
                "decision": "block",
                "note": "test fixture",
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


def _seed_six_domains_at(conn, *, authored_at_by_domain: dict[str, datetime]) -> None:
    """Seed all six domains; per-domain ``authored_at`` controls staleness."""

    for domain in _SIX_DOMAINS:
        _seed_proposal(
            conn, domain=domain, authored_at=authored_at_by_domain[domain],
        )


def _read_uncertainty_by_domain(db_path: Path) -> dict[str, list[str]]:
    """Return ``{domain: uncertainty[]}`` for the canonical plan's recommendations."""

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


# ---------------------------------------------------------------------------
# P1 — fresh-state, flag set, no carryover token expected
# ---------------------------------------------------------------------------


def test_p1_fresh_state_flag_set_no_carryover_token(fresh_db):
    """P1: Dom baseline. Flag set + every domain freshly authored within
    the session → no domain triggers the carryover token."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(seconds=10)  # well inside the 60s threshold
    authored = {d: fresh for d in _SIX_DOMAINS}

    conn = open_connection(fresh_db)
    try:
        _seed_six_domains_at(conn, authored_at_by_domain=authored)
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
    assert set(uncertainty_by_domain.keys()) == set(_SIX_DOMAINS)
    for domain, tokens in uncertainty_by_domain.items():
        carryover = f"{domain}_proposal_carryover_under_re_propose_all"
        assert carryover not in tokens, (
            f"P1 should produce zero carryover tokens, but {domain} got "
            f"{tokens!r}"
        )


# ---------------------------------------------------------------------------
# P5 — thin-history with state delta, flag set, recovery NOT re-authored
# ---------------------------------------------------------------------------


def test_p5_recovery_stale_flag_set_only_recovery_carryover(fresh_db):
    """P5: female multi-sport, thin-history with state delta. Flag set
    + recovery's envelope older than the freshness threshold while the
    other 5 domains are freshly authored → carryover token fires for
    recovery ONLY."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    fresh = now - timedelta(seconds=10)
    # Recovery is well outside the 60s threshold — represents the
    # state-delta case where the agent re-authored the other domains
    # but skipped recovery (stale envelope from a prior session).
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=30)
    authored = {d: fresh for d in _SIX_DOMAINS}
    authored["recovery"] = stale

    conn = open_connection(fresh_db)
    try:
        _seed_six_domains_at(conn, authored_at_by_domain=authored)
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
    assert (
        "recovery_proposal_carryover_under_re_propose_all"
        in uncertainty_by_domain["recovery"]
    ), (
        f"P5 expected carryover token on recovery; got "
        f"{uncertainty_by_domain['recovery']!r}"
    )
    for domain in _SIX_DOMAINS:
        if domain == "recovery":
            continue
        token = f"{domain}_proposal_carryover_under_re_propose_all"
        assert token not in uncertainty_by_domain[domain], (
            f"P5 expected zero carryover token on {domain} (fresh "
            f"envelope), got {uncertainty_by_domain[domain]!r}"
        )


# ---------------------------------------------------------------------------
# P9 — supersede-after-intake-change baseline, flag ABSENT
# ---------------------------------------------------------------------------


def test_p9_flag_absent_no_carryover_regardless_of_age(fresh_db):
    """P9: older female endurance. Flag is absent. Even with a stale
    recovery envelope, no carryover token fires — option A is operator-
    opt-in via the flag, not implicit on every supersede."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(minutes=10)
    authored = {d: stale for d in _SIX_DOMAINS}

    conn = open_connection(fresh_db)
    try:
        _seed_six_domains_at(conn, authored_at_by_domain=authored)
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=False,  # the load-bearing assertion
        )
    finally:
        conn.close()

    uncertainty_by_domain = _read_uncertainty_by_domain(fresh_db)
    for domain, tokens in uncertainty_by_domain.items():
        carryover = f"{domain}_proposal_carryover_under_re_propose_all"
        assert carryover not in tokens, (
            f"P9 must produce zero carryover tokens (flag absent), "
            f"but {domain} got {tokens!r}"
        )


# ---------------------------------------------------------------------------
# Edge cases the persona scenarios don't directly cover
# ---------------------------------------------------------------------------


def test_carryover_token_additive_with_existing_uncertainty(fresh_db):
    """The carryover token is appended to whatever ``uncertainty[]`` the
    proposal/skill already produced. A skill-authored uncertainty token
    must survive alongside the runtime-emitted carryover token — they
    are independent signals."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=5)

    conn = open_connection(fresh_db)
    try:
        for domain in _SIX_DOMAINS:
            payload = {
                "schema_version": f"{domain}_proposal.v1",
                "proposal_id": f"prop_{_FOR_DATE}_{_USER_ID}_{domain}_01",
                "user_id": _USER_ID,
                "for_date": _FOR_DATE,
                "domain": domain,
                "action": "defer_decision_insufficient_signal",
                "action_detail": None,
                "rationale": ["fixture"],
                "confidence": "low",
                # Pre-existing uncertainty token from the proposing skill.
                "uncertainty": ["thin_history_window"],
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
                    stale.isoformat(),
                    stale.isoformat(),
                    stale.isoformat(),
                    1,
                    None,
                    None,
                ),
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
    for domain, tokens in uncertainty_by_domain.items():
        assert "thin_history_window" in tokens, (
            f"{domain} lost the proposal-authored uncertainty token; "
            f"got {tokens!r}"
        )
        carryover = f"{domain}_proposal_carryover_under_re_propose_all"
        assert carryover in tokens, (
            f"{domain} missing carryover token despite stale envelope; "
            f"got {tokens!r}"
        )


def test_carryover_token_idempotent_on_rerun(fresh_db):
    """Re-running synthesis with a stale envelope + the flag must not
    duplicate the carryover token. The token-emission code dedups by
    membership check before append."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=5)
    authored = {d: stale for d in _SIX_DOMAINS}

    conn = open_connection(fresh_db)
    try:
        _seed_six_domains_at(conn, authored_at_by_domain=authored)
        conn.commit()
    finally:
        conn.close()

    # First synthesis run — emits carryover tokens, writes canonical plan.
    conn = open_connection(fresh_db)
    try:
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
    finally:
        conn.close()

    # Second run with the same inputs would normally short-circuit on
    # state_fingerprint match, but pass `now` slightly later so the
    # carryover semantics still cover the re-run path. We force a
    # supersede so the new plan id is fresh.
    later = now + timedelta(seconds=1)
    conn = open_connection(fresh_db)
    try:
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=later,
            re_propose_all=True,
            supersede=True,
        )
    finally:
        conn.close()

    # Read the *canonical leaf* recommendations (the second run wrote
    # a `_v2` plan; recommendation_log carries both plans' rows). The
    # check is "no row carries the carryover token twice", not "only
    # one row exists".
    conn = open_connection(fresh_db)
    try:
        rows = conn.execute(
            "SELECT payload_json FROM recommendation_log "
            "WHERE for_date = ? AND user_id = ?",
            (_FOR_DATE, _USER_ID),
        ).fetchall()
    finally:
        conn.close()
    for row in rows:
        rec = json.loads(row["payload_json"])
        token = (
            f"{rec['domain']}_proposal_carryover_under_re_propose_all"
        )
        occurrences = sum(1 for u in rec.get("uncertainty") or [] if u == token)
        assert occurrences <= 1, (
            f"recommendation {rec['recommendation_id']} has the "
            f"carryover token {occurrences} times; expected at most 1"
        )
