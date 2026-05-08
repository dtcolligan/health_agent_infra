"""W-AG (v0.1.13) — `hai today` cold-start vs established prose.

Three streak buckets pin different prose:

  1. **streak_days == 0** — first plan. Top-matter says "your first
     plan"; footer surfaces "this is your first plan" + "run `hai
     daily` again tomorrow to keep the chain going."

  2. **streak_days >= 30** — established. Top-matter shows "(N-day
     streak)"; footer says "keep your N-day streak going."

  3. **mid-range (1-29) OR streak_days is None** — unchanged from
     pre-W-AG behaviour. Mid-range users are still onboarding and
     the streak phrasing would feel premature.

The test surface uses a synthetic plan in a temp DB so the prose can
be checked end-to-end through `render_today`.

(IR round 1 F-IR-01 corrected the threshold from a transient 7-day
implementation drift to the PLAN-contracted 30-day "established"
gate.)
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path

from health_agent_infra.core.explain import load_bundle_for_date
from health_agent_infra.core.narration import render_today
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import initialize_database, open_connection


_USER = "u_w_ag_test"
_AS_OF = date(2026, 4, 28)


def _setup(tmp_path: Path):
    """Build a temp DB containing one minimal plan with one recovery rec."""

    db = tmp_path / "state.db"
    initialize_database(db)
    plan_id = canonical_daily_plan_id(_AS_OF, _USER)
    rec_id = f"rec_{_AS_OF.isoformat()}_{_USER}_recovery_01"

    with closing(sqlite3.connect(db)) as conn:
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
                plan_id, _USER, _AS_OF.isoformat(),
                "2026-04-28T07:00:00+00:00",
                json.dumps([rec_id]),
                "2026-04-28T07:00:00+00:00",
                "2026-04-28T07:00:00+00:00",
            ),
        )
        payload = {
            "recommendation_id": rec_id,
            "domain": "recovery",
            "action": "proceed_with_planned_session",
            "confidence": "moderate",
            "rationale": ["Sleep solid; HRV in band."],
            "uncertainty": [],
            "follow_up": {"review_question": "Did the session feel right?"},
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
                rec_id, _USER, _AS_OF.isoformat(),
                "2026-04-28T07:00:00+00:00",
                "proceed_with_planned_session", "moderate",
                json.dumps(payload),
                "2026-04-28T07:00:00+00:00",
                "2026-04-28T07:00:00+00:00",
                "2026-04-28T07:00:00+00:00",
                "recovery", plan_id,
            ),
        )
        conn.commit()
    return db


def _bundle(db: Path):
    conn = open_connection(db)
    try:
        return load_bundle_for_date(
            conn, for_date=_AS_OF, user_id=_USER, plan_version="latest",
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Day-1 (streak_days == 0)
# ---------------------------------------------------------------------------


def test_day_1_top_matter_says_first_plan(tmp_path):
    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=0)
    assert "your first plan" in out


def test_day_1_footer_says_this_is_your_first_plan(tmp_path):
    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=0)
    assert "This is your first plan" in out
    # Closing prompt is "run hai daily again tomorrow", not the
    # standard "run hai review record".
    assert "Run `hai daily` again tomorrow" in out


# ---------------------------------------------------------------------------
# Established (streak_days >= 30)
# ---------------------------------------------------------------------------


def test_established_top_matter_includes_streak_count(tmp_path):
    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=45)
    assert "(45-day streak)" in out


def test_established_footer_mentions_streak(tmp_path):
    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=45)
    assert "45-day streak going" in out


def test_threshold_at_thirty_engages_established_voice(tmp_path):
    """Boundary: streak == 30 should already use established voice."""

    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=30)
    assert "(30-day streak)" in out


def test_threshold_below_thirty_does_not_engage_established_voice(tmp_path):
    """Lower-bound boundary: streak == 29 stays in pre-W-AG voice."""

    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=29)
    assert "(29-day streak)" not in out
    assert "streak going" not in out
    assert "your first plan" not in out


# ---------------------------------------------------------------------------
# Mid-range (1-29) and None — pre-W-AG voice unchanged
# ---------------------------------------------------------------------------


def test_mid_range_streak_keeps_pre_w_ag_voice(tmp_path):
    """Streak == 14 is still onboarding by the planned 30-day gate —
    the established framing would feel premature, so the renderer
    keeps the neutral voice."""

    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="plain", streak_days=14)
    assert "your first plan" not in out
    assert "(14-day streak)" not in out
    assert "streak going" not in out


def test_streak_none_keeps_pre_w_ag_voice(tmp_path):
    """When the caller doesn't pass streak_days, behaviour is exactly
    pre-W-AG. This is the backwards-compatibility contract — the
    parameter is opt-in."""

    bundle = _bundle(_setup(tmp_path))
    out_a = render_today(bundle, format="plain")
    out_b = render_today(bundle, format="plain", streak_days=None)
    assert out_a == out_b
    assert "your first plan" not in out_a
    assert "streak" not in out_a


# ---------------------------------------------------------------------------
# Both formats consistent
# ---------------------------------------------------------------------------


def test_markdown_format_carries_streak_phrasing(tmp_path):
    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="markdown", streak_days=45)
    assert "(45-day streak)" in out


def test_json_format_does_not_inject_streak_prose(tmp_path):
    """The JSON surface is structured; streak prose belongs in the
    text rendering only, not the agent-facing JSON shape."""

    bundle = _bundle(_setup(tmp_path))
    out = render_today(bundle, format="json", streak_days=45)
    payload = json.loads(out)
    # JSON top-level keys should not contain streak prose.
    for v in payload.values():
        if isinstance(v, str):
            assert "streak" not in v.lower()
