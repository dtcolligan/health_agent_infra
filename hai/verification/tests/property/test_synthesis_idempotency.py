"""M7 — synthesis idempotency property test.

Running ``run_synthesis`` twice on identical inputs must produce
byte-equal persisted rows (modulo timestamp / autoincrement columns
the runtime stamps per call). If this breaks, the canonical-plan
replacement path is leaking state somewhere.

Uses a small random sweep over proposal sets + snapshots — the
invariant should hold regardless of how many domains or which X-rule
configuration fires.
"""

from __future__ import annotations

import copy
import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

import pytest

try:
    from hypothesis import given, settings, strategies as st
except ImportError:
    pytest.skip("hypothesis not installed", allow_module_level=True)

from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
    project_proposal,
)
from health_agent_infra.core.synthesis import run_synthesis
from health_agent_infra.core.writeback.proposal import PROPOSAL_SCHEMA_VERSIONS


FOR_DATE = date(2026, 4, 17)
USER = "u_prop"


# Columns the runtime stamps per call — they legitimately differ
# between re-runs and must be excluded from the equality check.
_VOLATILE_COLUMNS: frozenset[str] = frozenset({
    "synthesized_at",
    "fired_at",
    "issued_at",
    "produced_at",
    "validated_at",
    "projected_at",
    "firing_id",
    "outcome_id",
    "sync_id",
    "started_at",
    "completed_at",
    "captured_at",
})


def _strip_volatile(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    for k in list(d.keys()):
        if k in _VOLATILE_COLUMNS:
            d.pop(k)
    # payload_json carries timestamps embedded in its JSON blob;
    # normalise by re-dumping with volatile fields stripped.
    if "payload_json" in d and d["payload_json"]:
        try:
            payload = json.loads(d["payload_json"])
        except (TypeError, ValueError):
            return d
        if isinstance(payload, dict):
            for k in list(payload.keys()):
                if k in _VOLATILE_COLUMNS:
                    payload.pop(k)
            # Also strip nested follow_up.review_at which is derived
            # from issued_at + a fixed delta.
            fu = payload.get("follow_up")
            if isinstance(fu, dict):
                fu.pop("review_at", None)
            d["payload_json"] = json.dumps(payload, sort_keys=True)
    # synthesis_meta_json includes the run's wall-clock synthesized_at;
    # strip that before compare.
    if "synthesis_meta_json" in d and d["synthesis_meta_json"]:
        try:
            meta = json.loads(d["synthesis_meta_json"])
        except (TypeError, ValueError):
            return d
        if isinstance(meta, dict):
            meta.pop("synthesized_at", None)
            d["synthesis_meta_json"] = json.dumps(meta, sort_keys=True)
    return d


def _snapshot_db(conn: sqlite3.Connection) -> dict[str, list[dict]]:
    """Read every row from every synthesis table into plain dicts.

    Synthesis writes to three tables: daily_plan, recommendation_log,
    x_rule_firing (and updates proposal_log.daily_plan_id). We capture
    all four so a leak anywhere surfaces.
    """

    snap: dict[str, list[dict]] = {}
    for table in (
        "daily_plan",
        "recommendation_log",
        "x_rule_firing",
        "planned_recommendation",
    ):
        rows = conn.execute(
            f"SELECT * FROM {table} ORDER BY 1"  # noqa: S608 — fixed list
        ).fetchall()
        snap[table] = [_strip_volatile(r) for r in rows]
    proposal_rows = conn.execute(
        "SELECT proposal_id, daily_plan_id FROM proposal_log "
        "ORDER BY proposal_id"
    ).fetchall()
    snap["proposal_log"] = [dict(r) for r in proposal_rows]
    return snap


def _make_proposal(domain: str, index: int) -> dict[str, Any]:
    action_by_domain = {
        "recovery": "proceed_with_planned_session",
        "running": "proceed_with_planned_run",
        "strength": "proceed_with_planned_session",
        "sleep": "maintain_schedule",
        "stress": "maintain_routine",
        "nutrition": "maintain_targets",
    }
    return {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_{index:02d}",
        "user_id": USER,
        "for_date": FOR_DATE.isoformat(),
        "domain": domain,
        "action": action_by_domain[domain],
        "action_detail": None,
        "rationale": [f"{domain}_baseline"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "n"}],
        "bounded": True,
    }


def _stressful_snapshot() -> dict[str, Any]:
    return {
        "recovery": {
            "classified_state": {"sleep_debt_band": "moderate"},
            "today": {"acwr_ratio": 1.0},
        },
        "sleep": {"classified_state": {"sleep_debt_band": "moderate"}},
        "stress": {
            "classified_state": {"garmin_stress_band": "high"},
            "today": {"garmin_all_day_stress": 65, "body_battery_end_of_day": 45},
            "today_garmin": 65, "today_body_battery": 45,
        },
        "running": {},
    }


@settings(derandomize=True, max_examples=5, deadline=None)
@given(
    domains=st.lists(
        st.sampled_from(("recovery", "running", "sleep", "stress", "strength", "nutrition")),
        min_size=1, max_size=6, unique=True,
    ),
)
def test_run_synthesis_twice_produces_equal_state(
    tmp_path_factory, domains: list[str],
):
    # Each Hypothesis example gets a fresh tmp DB so runs don't
    # interfere. max_examples is small because a full run_synthesis
    # cycle is ~10ms + two DB setups.
    tmp_path = tmp_path_factory.mktemp("prop")
    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    proposals = [_make_proposal(d, i + 1) for i, d in enumerate(domains)]

    # First synthesis.
    conn = open_connection(db_path)
    try:
        for p in proposals:
            project_proposal(conn, p)
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_stressful_snapshot(),
        )
        snap_first = _snapshot_db(conn)
    finally:
        conn.close()

    # Second synthesis — canonical-plan replacement. Proposals already
    # exist (idempotent projection), so we just call run_synthesis
    # again.
    conn = open_connection(db_path)
    try:
        run_synthesis(
            conn, for_date=FOR_DATE, user_id=USER,
            snapshot=_stressful_snapshot(),
        )
        snap_second = _snapshot_db(conn)
    finally:
        conn.close()

    # After stripping volatile columns, the two snapshots must be equal.
    assert snap_first == snap_second, (
        "run_synthesis produced divergent persisted state across two runs"
    )
