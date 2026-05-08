"""W-FBC-2 rendering: carryover token surfaces through ``hai today``.

PLAN §2.A acceptance: "demonstrate carryover-uncertainty token in
``proposal_log`` rows AND in rationale prose surfaced via ``hai today``."

The recovery + multi-domain tests assert the carryover token persists
in ``recommendation_log.payload_json``. This file completes the
acceptance contract by asserting the token also appears in the
``hai today`` rendered surface — the user-facing audit signal.

Two independent assertions:

  1. ``render_today`` (the in-process renderer ``cmd_today`` calls)
     surfaces the per-domain carryover token in its prose output.
  2. ``render_today_json`` (the JSON surface) carries the token in
     each section's ``uncertainty[]`` field.

Both layers must surface the token, not just the DB. If rendering
were to silently drop runtime-emitted uncertainty tokens, the
operator would lose the audit signal even though it persists in
state — a true partial-closure that the PLAN acceptance prevents.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from health_agent_infra.core.explain import load_bundle_for_date
from health_agent_infra.core.narration import render_today
from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import initialize_database
from health_agent_infra.core.synthesis import (
    RE_PROPOSE_ALL_FRESHNESS_THRESHOLD,
    run_synthesis,
)


_FOR_DATE = "2026-04-28"
_USER_ID = "u_render_test"
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
        "rationale": [f"render fixture ({domain})"],
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


def _seed_with_stale_recovery(conn, *, now: datetime) -> None:
    """Seed a P5-shape: recovery stale, others fresh."""

    fresh = now - timedelta(seconds=10)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(seconds=30)
    for domain in _SIX_DOMAINS:
        _seed_proposal(
            conn,
            domain=domain,
            authored_at=stale if domain == "recovery" else fresh,
        )


def test_carryover_token_surfaces_in_hai_today_prose(fresh_db):
    """The recovery carryover token must appear literally in
    ``render_today``'s markdown surface — that is the user-visible
    audit signal the PLAN acceptance gate names."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)

    conn = open_connection(fresh_db)
    try:
        _seed_with_stale_recovery(conn, now=now)
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
        bundle = load_bundle_for_date(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            plan_version="latest",
        )
    finally:
        conn.close()

    rendered_markdown = render_today(bundle, format="markdown")
    rendered_plain = render_today(bundle, format="plain")

    expected_token = "recovery_proposal_carryover_under_re_propose_all"
    assert expected_token in rendered_markdown, (
        f"carryover token missing from markdown render; output was:\n"
        f"{rendered_markdown}"
    )
    assert expected_token in rendered_plain, (
        f"carryover token missing from plain render; output was:\n"
        f"{rendered_plain}"
    )


def test_carryover_token_surfaces_in_hai_today_json(fresh_db):
    """The JSON surface (``hai today --format json``) must also carry
    the token — agents that consume the structured surface depend on
    the same audit signal as the prose readers."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)

    conn = open_connection(fresh_db)
    try:
        _seed_with_stale_recovery(conn, now=now)
        conn.commit()
        run_synthesis(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            now=now,
            re_propose_all=True,
        )
        bundle = load_bundle_for_date(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            plan_version="latest",
        )
    finally:
        conn.close()

    json_blob = render_today(bundle, format="json")
    parsed = json.loads(json_blob)
    sections_by_domain = {
        s["domain"]: s for s in parsed.get("sections", [])
    }
    assert (
        "recovery_proposal_carryover_under_re_propose_all"
        in sections_by_domain["recovery"]["uncertainty"]
    ), (
        f"recovery section uncertainty[] missing carryover token; "
        f"got {sections_by_domain['recovery']!r}"
    )

    # The 5 fresh domains must NOT carry their own token.
    for domain in _SIX_DOMAINS:
        if domain == "recovery":
            continue
        token = f"{domain}_proposal_carryover_under_re_propose_all"
        assert token not in sections_by_domain[domain]["uncertainty"], (
            f"{domain} section unexpectedly carries {token!r}"
        )


def test_no_carryover_token_in_render_when_flag_absent(fresh_db):
    """Negative: flag absent → no carryover token in any render mode,
    even when every envelope is stale. Mirrors the P9 contract at the
    rendering layer."""

    now = datetime(2026, 4, 28, 12, 0, 0, tzinfo=timezone.utc)
    stale = now - RE_PROPOSE_ALL_FRESHNESS_THRESHOLD - timedelta(minutes=5)

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
            re_propose_all=False,
        )
        bundle = load_bundle_for_date(
            conn,
            for_date=date(2026, 4, 28),
            user_id=_USER_ID,
            plan_version="latest",
        )
    finally:
        conn.close()

    for fmt in ("markdown", "plain", "json"):
        out = render_today(bundle, format=fmt)
        assert "_proposal_carryover_under_re_propose_all" not in out, (
            f"{fmt} render unexpectedly carries a carryover token "
            f"despite re_propose_all=False; output was:\n{out}"
        )
