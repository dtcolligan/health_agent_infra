"""Integration test for v0.1.10 W-C wire (F-CDX-IR-01).

The W-C partial-day gate was implemented at the policy boundary in
v0.1.10 but never plumbed into ``build_snapshot``. The Codex
implementation review caught it: ``test_partial_day_nutrition_gate``
passed (the gate worked in isolation), yet the production snapshot
path still escalated breakfast-only nutrition rows because it called
``evaluate_nutrition_policy`` without ``meals_count`` or
``is_end_of_day``.

These tests exercise the snapshot path itself, asserting:

  1. A single-meal high-deficit row at 06:32 does NOT escalate.
  2. The same row evaluated at 21:30 DOES escalate (full day).
  3. The same row evaluated for a past date DOES escalate
     (closed day, regardless of clock).
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
)


USER = "u_partial_day_wire"


def _init_dirs(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = tmp_path / "state.db"
    initialize_database(db)
    return base, db


def _log_breakfast_only(
    base: Path,
    db: Path,
    as_of: date,
) -> None:
    """One meal logged: 350 kcal, 25 g protein, 35 g carbs, 12 g fat,
    meals_count=1. Against a 2200 kcal / 180 g protein target this
    yields a 1850 kcal "deficit" and a 0.14 protein ratio — the
    morning-briefing breakfast-only false positive shape."""

    rc = cli_main([
        "intake", "nutrition",
        "--calories", "350",
        "--protein-g", "25",
        "--carbs-g", "35",
        "--fat-g", "12",
        "--meals-count", "1",
        "--as-of", as_of.isoformat(),
        "--user-id", USER,
        "--base-dir", str(base),
        "--db-path", str(db),
    ])
    assert rc == 0


def _nutrition_policy(snap: dict) -> dict:
    block = snap["nutrition"]
    assert "policy_result" in block, (
        "snapshot must carry nutrition.policy_result"
    )
    return block["policy_result"]


class TestPartialDayWireIntoSnapshot:
    """v0.1.10 W-C wire (F-CDX-IR-01) — gate must activate from
    ``build_snapshot``, not just the policy boundary."""

    def test_breakfast_only_morning_does_not_escalate(
        self, tmp_path: Path,
    ) -> None:
        as_of = date(2026, 4, 28)
        base, db = _init_dirs(tmp_path)
        _log_breakfast_only(base, db, as_of)

        conn = open_connection(db)
        try:
            snap = build_snapshot(
                conn,
                as_of_date=as_of,
                user_id=USER,
                now_local=datetime(2026, 4, 28, 6, 32),
            )
        finally:
            conn.close()

        policy = _nutrition_policy(snap)
        assert policy.get("forced_action") != "escalate_for_user_review", (
            "breakfast-only at 06:32 must not escalate — partial-day "
            "gate must activate from the snapshot path"
        )

    def test_one_meal_at_evening_does_escalate(
        self, tmp_path: Path,
    ) -> None:
        as_of = date(2026, 4, 28)
        base, db = _init_dirs(tmp_path)
        _log_breakfast_only(base, db, as_of)

        conn = open_connection(db)
        try:
            snap = build_snapshot(
                conn,
                as_of_date=as_of,
                user_id=USER,
                now_local=datetime(2026, 4, 28, 21, 30),
            )
        finally:
            conn.close()

        policy = _nutrition_policy(snap)
        assert policy.get("forced_action") == "escalate_for_user_review", (
            "one meal at 21:30 should escalate — end-of-day reached"
        )

    def test_one_meal_for_past_date_does_escalate(
        self, tmp_path: Path,
    ) -> None:
        past = date(2026, 4, 20)
        base, db = _init_dirs(tmp_path)
        _log_breakfast_only(base, db, past)

        conn = open_connection(db)
        try:
            snap = build_snapshot(
                conn,
                as_of_date=past,
                user_id=USER,
                now_local=datetime(2026, 4, 28, 6, 32),
            )
        finally:
            conn.close()

        policy = _nutrition_policy(snap)
        assert policy.get("forced_action") == "escalate_for_user_review", (
            "past-dated snapshot is always end-of-day; one-meal day "
            "should escalate regardless of clock"
        )

    def test_eod_threshold_is_overridable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """User can shift the end-of-day cutover via thresholds.toml."""

        from health_agent_infra.core import config as _config

        as_of = date(2026, 4, 28)
        base, db = _init_dirs(tmp_path)
        _log_breakfast_only(base, db, as_of)

        # Push end-of-day to 23 — at 21:30 the gate should suppress.
        original = _config.load_thresholds

        def _patched(path=None):
            t = original(path)
            t.setdefault("policy", {}).setdefault("nutrition", {})
            t["policy"]["nutrition"][
                "r_extreme_deficiency_end_of_day_local_hour"
            ] = 23
            return t

        monkeypatch.setattr(_config, "load_thresholds", _patched)
        # build_snapshot imports load_thresholds inside the wire block,
        # so monkeypatching the module-level binding is enough.
        monkeypatch.setattr(
            "health_agent_infra.core.state.snapshot.load_thresholds",
            _patched,
            raising=False,
        )

        conn = open_connection(db)
        try:
            snap = build_snapshot(
                conn,
                as_of_date=as_of,
                user_id=USER,
                now_local=datetime(2026, 4, 28, 21, 30),
            )
        finally:
            conn.close()

        policy = _nutrition_policy(snap)
        assert policy.get("forced_action") != "escalate_for_user_review", (
            "with end-of-day pushed to 23:00, 21:30 must still suppress"
        )
