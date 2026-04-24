"""D4 tests #8 + #9 — cold-start rendering in ``hai today``.

Two visible effects:

1. **Nutrition defer gets D4's "I'd be making it up" framing** when
   ``nutrition.cold_start`` is True and the action is defer. A
   graduated user (``cold_start=False``) sees the generic unblock
   hint.

2. **Per-cold-start-domain footer** appears once per domain (not
   once per run, not once per section). The footer is rendered in
   DOMAIN_ORDER after all per-domain sections so the reader reads
   the plan first, then the framing.

Graduation test: when a domain's ``cold_start`` is False, no footer
fires and no rendering change for that domain.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.core.explain import load_bundle_for_date
from health_agent_infra.core.narration import render_today
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database, open_connection


USER = "u_cs_render"
AS_OF = date(2026, 4, 24)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_plan(
    db: Path,
    *,
    recs: list[dict],
) -> str:
    plan_id = canonical_daily_plan_id(AS_OF, USER)
    rec_ids = [r["recommendation_id"] for r in recs]
    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO daily_plan (
                daily_plan_id, user_id, for_date, synthesized_at,
                recommendation_ids_json, proposal_ids_json,
                x_rules_fired_json, synthesis_meta_json,
                source, ingest_actor, validated_at, projected_at
            ) VALUES (?, ?, ?, ?, ?, '[]', '[]', NULL,
                      'test', 'test', ?, ?)
            """,
            (
                plan_id, USER, AS_OF.isoformat(),
                "2026-04-24T07:00:00+00:00",
                json.dumps(rec_ids),
                "2026-04-24T07:00:00+00:00",
                "2026-04-24T07:00:00+00:00",
            ),
        )
        for rec in recs:
            payload = {
                "recommendation_id": rec["recommendation_id"],
                "domain": rec["domain"],
                "action": rec["action"],
                "confidence": rec.get("confidence", "moderate"),
                "rationale": rec.get("rationale", []),
                "uncertainty": rec.get("uncertainty", []),
                "follow_up": {"review_question": rec.get("review_question", "?")},
            }
            conn.execute(
                """
                INSERT INTO recommendation_log (
                    recommendation_id, user_id, for_date, issued_at,
                    action, confidence, bounded, payload_json,
                    source, ingest_actor, produced_at, validated_at,
                    projected_at, domain, daily_plan_id
                ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'test', 'test',
                          ?, ?, ?, ?, ?)
                """,
                (
                    rec["recommendation_id"], USER, AS_OF.isoformat(),
                    "2026-04-24T07:00:00+00:00",
                    rec["action"], payload["confidence"],
                    json.dumps(payload),
                    "2026-04-24T07:00:00+00:00",
                    "2026-04-24T07:00:00+00:00",
                    "2026-04-24T07:00:00+00:00",
                    rec["domain"], plan_id,
                ),
            )
        conn.commit()
    return plan_id


def _bundle(db: Path):
    conn = open_connection(db)
    try:
        return load_bundle_for_date(
            conn, for_date=AS_OF, user_id=USER, plan_version="latest",
        )
    finally:
        conn.close()


def _all_six_domain_recs() -> list[dict]:
    return [
        {
            "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_{dom}_01",
            "domain": dom,
            "action": action,
        }
        for dom, action in (
            ("recovery", "proceed_with_planned_session"),
            ("sleep", "maintain_schedule"),
            ("running", "proceed_with_planned_run"),
            ("strength", "proceed_with_planned_session"),
            ("stress", "maintain_routine"),
            ("nutrition", "maintain_targets"),
        )
    ]


# ---------------------------------------------------------------------------
# Per-domain cold-start footer
# ---------------------------------------------------------------------------


def test_cold_start_footer_appears_once_per_cold_start_domain(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=_all_six_domain_recs())
    bundle = _bundle(db)

    cold_start_by_domain = {
        "recovery": {"cold_start": False, "history_days": 14},
        "sleep":    {"cold_start": False, "history_days": 20},
        "running":  {"cold_start": True,  "history_days": 3},
        "strength": {"cold_start": True,  "history_days": 0},
        "stress":   {"cold_start": True,  "history_days": 5},
        "nutrition":{"cold_start": True,  "history_days": 1},
    }

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain=cold_start_by_domain,
    )

    # Four cold-start footers should appear (running, strength, stress,
    # nutrition). Recovery + sleep have graduated — no footer for them.
    assert out.count("first 14 days of using the agent") == 4
    assert "my running recommendations will get more specific" in out.lower()
    assert "my strength recommendations will get more specific" in out.lower()
    assert "my stress recommendations will get more specific" in out.lower()
    assert "my nutrition recommendations will get more specific" in out.lower()
    # Graduated domains must not fire a footer.
    assert "my recovery recommendations will get more specific" not in out.lower()
    assert "my sleep recommendations will get more specific" not in out.lower()


def test_cold_start_footer_surfaces_history_day_count(tmp_path: Path):
    """Footers include progress toward the 14-day window so the
    user sees how close they are to graduating."""

    db = _init_db(tmp_path)
    _seed_plan(db, recs=_all_six_domain_recs())
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain={
            "running": {"cold_start": True, "history_days": 7},
        },
    )

    # "7/14 days so far" or similar; exact wording is in
    # templates.cold_start_footer but the substring guarantees visibility.
    assert "7/14 days" in out


def test_no_footer_when_all_domains_have_graduated(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=_all_six_domain_recs())
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain={
            dom: {"cold_start": False, "history_days": 30}
            for dom in ("recovery", "sleep", "running", "strength", "stress", "nutrition")
        },
    )
    assert "first 14 days" not in out


def test_no_footer_when_cold_start_by_domain_is_none(tmp_path: Path):
    """Pre-D4 callers that don't pass ``cold_start_by_domain`` see
    identical output to before — no cold-start surface shift."""

    db = _init_db(tmp_path)
    _seed_plan(db, recs=_all_six_domain_recs())
    bundle = _bundle(db)

    out = render_today(bundle, format="plain")
    assert "first 14 days" not in out


def test_footer_only_emits_for_rendered_domains(tmp_path: Path):
    """Domain filter narrows output to one domain; footer must only
    fire for that one, not for every cold-start domain in the
    context dict."""

    db = _init_db(tmp_path)
    _seed_plan(db, recs=_all_six_domain_recs())
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        domain_filter="running",
        cold_start_by_domain={
            "running":  {"cold_start": True, "history_days": 2},
            "strength": {"cold_start": True, "history_days": 0},
        },
    )
    # Running footer present, strength footer absent (not rendered).
    assert "my running recommendations will get more specific" in out.lower()
    assert "my strength recommendations will get more specific" not in out.lower()


# ---------------------------------------------------------------------------
# Nutrition cold-start defer framing
# ---------------------------------------------------------------------------


def test_nutrition_defer_under_cold_start_uses_make_up_language(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {
            "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_nutrition_01",
            "domain": "nutrition",
            "action": "defer_decision_insufficient_signal",
        },
    ])
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain={
            "nutrition": {"cold_start": True, "history_days": 0},
        },
    )
    lowered = out.lower()
    assert "made up" in lowered
    assert "hai intake nutrition" in out


def test_nutrition_defer_without_cold_start_uses_generic_hint(tmp_path: Path):
    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {
            "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_nutrition_01",
            "domain": "nutrition",
            "action": "defer_decision_insufficient_signal",
        },
    ])
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain={
            "nutrition": {"cold_start": False, "history_days": 30},
        },
    )
    lowered = out.lower()
    assert "made up" not in lowered
    # Generic hint includes the intake command too.
    assert "hai intake nutrition" in out


def test_non_nutrition_defer_ignores_cold_start_flag(tmp_path: Path):
    """Running / strength / stress defers under cold-start should
    still use the domain-specific generic unblock hint, not the
    nutrition make-up language."""

    db = _init_db(tmp_path)
    _seed_plan(db, recs=[
        {
            "recommendation_id": f"rec_{AS_OF.isoformat()}_{USER}_running_01",
            "domain": "running",
            "action": "defer_decision_insufficient_signal",
        },
    ])
    bundle = _bundle(db)

    out = render_today(
        bundle, format="plain",
        cold_start_by_domain={
            "running": {"cold_start": True, "history_days": 0},
        },
    )
    assert "made up" not in out.lower()
