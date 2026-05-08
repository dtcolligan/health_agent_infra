"""W-A — presence block + is_partial_day + target_status helpers.

v0.1.15 round-4 (per `hai/reporting/plans/v0_1_15/PLAN.md` §2.B).

The agent's structural problem before W-A: there was no single read
surface that answered "what HAS been logged today?" — every agent
either re-asked the user for state already in the DB, or read raw
JSONL. `hai intake gaps` already reported what was *missing*; this
module's `compute_presence_block` reports the symmetric *present*
side, plus two derived signals (`is_partial_day`, `target_status`)
that the W-D arm-1 nutrition-suppression policy reads.

Three contracts:

  - **Presence per domain** (`nutrition / gym / readiness / sleep /
    weigh_in`): `logged: bool` plus per-domain identifiers (submission
    or session id, meals/set count, source). Read directly from the raw
    intake tables for the (as_of, user_id) pair. `weigh_in` always
    emits `logged=false, reason="intake_surface_not_yet_implemented"`
    in v0.1.15 because W-B (intake weight surface) is deferred to
    v0.1.17 per F-PLAN-09 / W-E.

  - **`is_partial_day`**: pure time + meal-count signal,
    target-independent. True when as_of==today_local AND local_now
    < cutoff (default 18:00) AND meals_count < expected (default 3).
    Cutoff configurable via thresholds (future); defaults wired here.

  - **`target_status`**: three-valued enum reading the existing
    `target` table (in tree since migration 020). Per round-4
    F-PHASE0-01 Option A revision, no separate `nutrition_target`
    table exists; W-A queries the generic `target` table filtered by
    `domain='nutrition'` and the four macro `target_type` values.
    `present` = active row covers today; `absent` = nutrition rows
    exist historically but none cover today; `unavailable` = no
    nutrition target rows for the user at all.
"""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------


# v0.1.15 W-A defaults — also live in `core.config.DEFAULT_THRESHOLDS`
# under `gap_detection.presence_partial_day_cutoff_hour` /
# `presence_partial_day_expected_meals` per F-IR-03 round-1 IR fix.
# These module constants are the FALLBACK when no thresholds dict is
# loaded (testing surface + the rare call-site that does its own
# config-loading); production callers thread the loaded values through
# the kwargs.
DEFAULT_CUTOFF_HOUR = 18
DEFAULT_EXPECTED_MEALS = 3


def _load_partial_day_thresholds() -> tuple[int, int]:
    """Read W-A cutoff + expected_meals from thresholds.toml.

    Returns ``(cutoff_hour, expected_meals)``. Falls back to module
    defaults on any load/coerce failure (defensive — the runtime never
    hard-fails because the user's thresholds.toml is malformed).
    """

    try:
        from health_agent_infra.core.config import (
            coerce_int,
            load_thresholds,
        )
        t = load_thresholds().get("gap_detection", {})
        cutoff = coerce_int(
            t.get("presence_partial_day_cutoff_hour", DEFAULT_CUTOFF_HOUR),
            name="gap_detection.presence_partial_day_cutoff_hour",
        )
        expected = coerce_int(
            t.get("presence_partial_day_expected_meals", DEFAULT_EXPECTED_MEALS),
            name="gap_detection.presence_partial_day_expected_meals",
        )
        return cutoff, expected
    except Exception:  # noqa: BLE001 — defensive fallback to defaults
        return DEFAULT_CUTOFF_HOUR, DEFAULT_EXPECTED_MEALS

# Target types that count as "nutrition macro" rows for W-A's
# target_status query. Round-4 F-PHASE0-01 Option A: the existing
# `target` table (migration 020) carries calories_kcal + protein_g
# already; W-C (migration 025) extends the CHECK with carbs_g + fat_g.
# W-A reads all four so post-W-C the query lights up consistently.
NUTRITION_MACRO_TARGET_TYPES: tuple[str, ...] = (
    "calories_kcal", "protein_g", "carbs_g", "fat_g",
)


# ---------------------------------------------------------------------------
# is_partial_day
# ---------------------------------------------------------------------------


def is_partial_day(
    *,
    as_of: date,
    meals_count: int,
    cutoff_hour: int = DEFAULT_CUTOFF_HOUR,
    expected_meals: int = DEFAULT_EXPECTED_MEALS,
    now_local: Optional[datetime] = None,
) -> tuple[bool, str]:
    """Return (is_partial, reason) for the given as_of date and meal count.

    Per PLAN §2.B: `is_partial_day == True` iff the call is for *today*
    AND the local time is before the cutoff AND fewer than the expected
    number of meals have been logged. Past-day or future-day calls are
    never partial — the day is closed (or hasn't started).

    `now_local` defaults to `datetime.now()` (test-injectable).
    """

    now_local = now_local if now_local is not None else datetime.now()
    today_local = now_local.date()

    if as_of != today_local:
        return (
            False,
            f"as_of={as_of.isoformat()} != today={today_local.isoformat()} "
            "(past or future day; closed by definition)",
        )

    before_cutoff = now_local.hour < cutoff_hour
    meals_under_expected = meals_count < expected_meals

    if before_cutoff and meals_under_expected:
        return (
            True,
            f"timestamp {now_local.strftime('%H:%M')} < end-of-day "
            f"cutoff {cutoff_hour:02d}:00 AND meals_count={meals_count} "
            f"< expected={expected_meals}",
        )
    if not before_cutoff and not meals_under_expected:
        return (
            False,
            f"past cutoff {cutoff_hour:02d}:00 AND meals met "
            f"({meals_count}>={expected_meals})",
        )
    if not before_cutoff:
        return (
            False,
            f"past cutoff {cutoff_hour:02d}:00 (timestamp "
            f"{now_local.strftime('%H:%M')})",
        )
    return (
        False,
        f"meals already met ({meals_count}>={expected_meals}; before cutoff)",
    )


# ---------------------------------------------------------------------------
# target_status — three-valued enum
# ---------------------------------------------------------------------------


def compute_target_status(
    conn: sqlite3.Connection, *, as_of: date, user_id: str,
) -> str:
    """Return `present` | `absent` | `unavailable` for nutrition macros.

    Reads the generic `target` table (migration 020). Per round-4
    F-PHASE0-01 Option A, no separate `nutrition_target` table exists;
    W-A reads the same surface W-C writes to.

    - `present`: an active, non-superseded row with `domain='nutrition'`
      and a macro `target_type` exists whose effective window covers
      `as_of`.
    - `absent`: at least one nutrition target row exists for the user
      (historical context exists), but none covers `as_of` today.
    - `unavailable`: no nutrition target rows for the user at all.
    """

    placeholders = ",".join("?" for _ in NUTRITION_MACRO_TARGET_TYPES)

    # Active-window query. f-string interpolates only the literal "?" placeholder
    # count derived from the module constant NUTRITION_MACRO_TARGET_TYPES; every
    # value (user_id, target_type values, as_of dates) is bound. Same safe-
    # interpolation rationale as `core/target/store.py:223`, `:275`, and `:419`
    # (D15 IR round-3 F-IR-R3-01 citation correction; the original draft cited
    # the pre-W-C-add_targets_atomic line numbers `:218` / `:359` which drifted
    # when migration 025 + the new helper landed).
    active_row = conn.execute(
        f"SELECT 1 FROM target "  # nosec B608
        f"WHERE user_id=? AND domain='nutrition' "
        f"AND target_type IN ({placeholders}) "
        f"AND status='active' AND superseded_by_target_id IS NULL "
        f"AND date(effective_from) <= date(?) "
        f"AND (effective_to IS NULL OR date(effective_to) >= date(?)) "
        f"LIMIT 1",
        (user_id, *NUTRITION_MACRO_TARGET_TYPES,
         as_of.isoformat(), as_of.isoformat()),
    ).fetchone()
    if active_row is not None:
        return "present"

    # Broader query: any nutrition target row in any status.
    any_row = conn.execute(
        f"SELECT 1 FROM target "  # nosec B608 - same constant-placeholder rationale
        f"WHERE user_id=? AND domain='nutrition' "
        f"AND target_type IN ({placeholders}) "
        f"LIMIT 1",
        (user_id, *NUTRITION_MACRO_TARGET_TYPES),
    ).fetchone()
    if any_row is not None:
        return "absent"
    return "unavailable"


# ---------------------------------------------------------------------------
# Per-domain presence queries
# ---------------------------------------------------------------------------


def _nutrition_presence(
    conn: sqlite3.Connection, *, as_of: date, user_id: str,
) -> dict[str, Any]:
    """Latest non-superseded nutrition_intake_raw row for (as_of, user)."""
    row = conn.execute(
        "SELECT submission_id, meals_count FROM nutrition_intake_raw "
        "WHERE user_id=? AND as_of_date=? "
        "AND submission_id NOT IN ("
        "  SELECT supersedes_submission_id FROM nutrition_intake_raw "
        "  WHERE supersedes_submission_id IS NOT NULL"
        ") "
        "ORDER BY ingested_at DESC LIMIT 1",
        (user_id, as_of.isoformat()),
    ).fetchone()
    if row is None:
        return {"logged": False, "meals_count": 0}
    return {
        "logged": True,
        "submission_id": row["submission_id"],
        "meals_count": row["meals_count"] or 0,
    }


def _gym_presence(
    conn: sqlite3.Connection, *, as_of: date, user_id: str,
) -> dict[str, Any]:
    """Latest gym_session for (as_of, user) + its set count."""
    row = conn.execute(
        "SELECT session_id FROM gym_session "
        "WHERE user_id=? AND as_of_date=? "
        "ORDER BY ingested_at DESC LIMIT 1",
        (user_id, as_of.isoformat()),
    ).fetchone()
    if row is None:
        return {"logged": False}
    session_id = row["session_id"]
    set_count_row = conn.execute(
        "SELECT COUNT(*) AS n FROM gym_set WHERE session_id=?",
        (session_id,),
    ).fetchone()
    return {
        "logged": True,
        "session_id": session_id,
        "set_count": set_count_row["n"] if set_count_row else 0,
    }


def _readiness_presence(
    conn: sqlite3.Connection, *, as_of: date, user_id: str,
) -> dict[str, Any]:
    """Latest manual_readiness_raw row for (as_of, user)."""
    row = conn.execute(
        "SELECT submission_id FROM manual_readiness_raw "
        "WHERE user_id=? AND as_of_date=? "
        "ORDER BY ingested_at DESC LIMIT 1",
        (user_id, as_of.isoformat()),
    ).fetchone()
    if row is None:
        return {"logged": False}
    return {"logged": True, "submission_id": row["submission_id"]}


def _sleep_presence(
    conn: sqlite3.Connection, *, as_of: date, user_id: str,
) -> dict[str, Any]:
    """Sleep is sourced from accepted_sleep_state_daily — populated by
    the wearable pull path, not a manual intake. logged=true means the
    accepted row exists for today (i.e., a successful sync produced
    sleep evidence)."""
    row = conn.execute(
        "SELECT source FROM accepted_sleep_state_daily "
        "WHERE user_id=? AND as_of_date=? LIMIT 1",
        (user_id, as_of.isoformat()),
    ).fetchone()
    if row is None:
        return {"logged": False}
    return {"logged": True, "source": row["source"]}


def _weigh_in_presence() -> dict[str, Any]:
    """Always returns `logged=false` in v0.1.15 — W-B (intake weight
    surface) is deferred to v0.1.17 per F-PLAN-09 / W-E. The skill
    contract per PLAN §2.F explicitly excludes branching on this."""
    return {
        "logged": False,
        "reason": "intake_surface_not_yet_implemented",
    }


# ---------------------------------------------------------------------------
# Top-level: compute the full presence block
# ---------------------------------------------------------------------------


def compute_presence_block(
    conn: sqlite3.Connection,
    *,
    as_of: date,
    user_id: str,
    cutoff_hour: Optional[int] = None,
    expected_meals: Optional[int] = None,
    now_local: Optional[datetime] = None,
) -> dict[str, Any]:
    """Return the full W-A presence block dict.

    Output shape (per PLAN §2.B):

        {
            "present": {
                "nutrition": {...},
                "gym": {...},
                "readiness": {...},
                "sleep": {...},
                "weigh_in": {"logged": False, "reason": "..."},
            },
            "is_partial_day": <bool>,
            "is_partial_day_reason": <str>,
            "target_status": "present" | "absent" | "unavailable",
        }

    Pure read-side; never mutates state.
    """

    nutrition = _nutrition_presence(conn, as_of=as_of, user_id=user_id)
    gym = _gym_presence(conn, as_of=as_of, user_id=user_id)
    readiness = _readiness_presence(conn, as_of=as_of, user_id=user_id)
    sleep = _sleep_presence(conn, as_of=as_of, user_id=user_id)
    weigh_in = _weigh_in_presence()

    # F-IR-03 (round-1 IR fix): load cutoff + expected_meals from
    # thresholds.toml when not explicitly passed. PLAN §2.B promises
    # the cutoff is "configurable via thresholds; default 18:00
    # user-local" — the threshold lookup honours that contract.
    if cutoff_hour is None or expected_meals is None:
        loaded_cutoff, loaded_expected = _load_partial_day_thresholds()
        if cutoff_hour is None:
            cutoff_hour = loaded_cutoff
        if expected_meals is None:
            expected_meals = loaded_expected

    partial, partial_reason = is_partial_day(
        as_of=as_of,
        meals_count=int(nutrition.get("meals_count") or 0),
        cutoff_hour=cutoff_hour,
        expected_meals=expected_meals,
        now_local=now_local,
    )
    target_status = compute_target_status(conn, as_of=as_of, user_id=user_id)

    return {
        "present": {
            "nutrition": nutrition,
            "gym": gym,
            "readiness": readiness,
            "sleep": sleep,
            "weigh_in": weigh_in,
        },
        "is_partial_day": partial,
        "is_partial_day_reason": partial_reason,
        "target_status": target_status,
    }
