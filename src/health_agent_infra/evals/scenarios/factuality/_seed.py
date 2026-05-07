"""Baseline DB seed for the W58D factuality corpus (v0.2.0 §2.F).

Seeds an in-memory sqlite3 connection with the minimum row set the
factuality fixtures need:

  * One ``accepted_recovery_state_daily`` row exposing ``row_version``
    so locator-pass + locator-row-missing + locator-row-version-drift
    fixtures can all be expressed against the same shared schema.
  * One ``daily_plan`` row, one ``recommendation_log`` row, and one
    ``x_rule_firing`` row for audit-ref pass + audit-ref-orphan
    fixtures.
  * One ``review_outcome`` row carrying a ``disagreed_firing_ids``
    JSON list so x-rule-conflict-user-disagreed fixtures resolve.

Used by both the corpus generator (``_build_corpus.py`` for inline
verification) and the step-6 scoring runner. Step 3 ships this seed
alongside the corpus so fixtures are independently verifiable
without depending on the broader runtime state schema.
"""

from __future__ import annotations

import json
import sqlite3


SEED_USER_ID = "u_factuality_corpus"
SEED_DATE = "2026-04-28"
SEED_ROW_VERSION = "2026-04-28T19:00Z"

SEED_DAILY_PLAN_ID = "plan_2026-04-28_factuality"
SEED_RECOMMENDATION_ID = "rec_2026-04-28_recovery_factuality"
SEED_RESOLVABLE_FIRING_ID = 9001
SEED_DISAGREED_FIRING_ID = 9002
SEED_REVIEW_EVENT_ID = "review_event_2026-W18_factuality"


def seed_factuality_baseline(conn: sqlite3.Connection) -> None:
    """Seed the in-memory DB with the W58D factuality corpus baseline.

    Idempotent: re-running over the same connection is a no-op (each
    CREATE TABLE uses ``IF NOT EXISTS``; INSERTs use ``OR IGNORE``).
    """

    conn.execute(
        "CREATE TABLE IF NOT EXISTS accepted_recovery_state_daily ("
        " as_of_date TEXT NOT NULL,"
        " user_id TEXT NOT NULL,"
        " row_version TEXT NOT NULL,"
        " resting_hr INTEGER,"
        " hrv_rmssd INTEGER,"
        " PRIMARY KEY (as_of_date, user_id))"
    )
    conn.execute(
        "INSERT OR IGNORE INTO accepted_recovery_state_daily VALUES "
        "(?, ?, ?, 52, 65)",
        (SEED_DATE, SEED_USER_ID, SEED_ROW_VERSION),
    )
    # NULL-signal rows for the source_signal_conflict (column-value-
    # NULL) sub-category. Each row has at least one signal column
    # NULL so locator-with-column citations against these dates fire
    # the SOURCE_SIGNAL_CONFLICT lane.
    conn.execute(
        "INSERT OR IGNORE INTO accepted_recovery_state_daily VALUES "
        "(?, ?, ?, NULL, 60)",
        ("2026-04-29", SEED_USER_ID, "2026-04-29T19:00Z"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO accepted_recovery_state_daily VALUES "
        "(?, ?, ?, 50, NULL)",
        ("2026-04-30", SEED_USER_ID, "2026-04-30T19:00Z"),
    )
    conn.execute(
        "INSERT OR IGNORE INTO accepted_recovery_state_daily VALUES "
        "(?, ?, ?, NULL, NULL)",
        ("2026-05-01", SEED_USER_ID, "2026-05-01T19:00Z"),
    )

    conn.execute(
        "CREATE TABLE IF NOT EXISTS daily_plan ("
        " daily_plan_id TEXT PRIMARY KEY, user_id TEXT, for_date TEXT)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO daily_plan VALUES (?, ?, ?)",
        (SEED_DAILY_PLAN_ID, SEED_USER_ID, SEED_DATE),
    )

    conn.execute(
        "CREATE TABLE IF NOT EXISTS recommendation_log ("
        " recommendation_id TEXT PRIMARY KEY, user_id TEXT, for_date TEXT)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO recommendation_log VALUES (?, ?, ?)",
        (SEED_RECOMMENDATION_ID, SEED_USER_ID, SEED_DATE),
    )

    conn.execute(
        "CREATE TABLE IF NOT EXISTS x_rule_firing ("
        " firing_id INTEGER PRIMARY KEY, daily_plan_id TEXT,"
        " user_id TEXT, x_rule_id TEXT)"
    )
    # Resolvable + disagreed firings are BOTH present in x_rule_firing.
    # The disagreed lane is not "row missing" — the firing exists; the
    # user just marked it "I disagree this should have fired."
    conn.execute(
        "INSERT OR IGNORE INTO x_rule_firing VALUES (?, ?, ?, 'X1')",
        (SEED_RESOLVABLE_FIRING_ID, SEED_DAILY_PLAN_ID, SEED_USER_ID),
    )
    conn.execute(
        "INSERT OR IGNORE INTO x_rule_firing VALUES (?, ?, ?, 'X2')",
        (SEED_DISAGREED_FIRING_ID, SEED_DAILY_PLAN_ID, SEED_USER_ID),
    )

    conn.execute(
        "CREATE TABLE IF NOT EXISTS review_outcome ("
        " outcome_id INTEGER PRIMARY KEY AUTOINCREMENT,"
        " review_event_id TEXT, recommendation_id TEXT,"
        " user_id TEXT, recorded_at TEXT,"
        " followed_recommendation INTEGER,"
        " disagreed_firing_ids TEXT)"
    )
    conn.execute(
        "INSERT OR IGNORE INTO review_outcome ("
        " review_event_id, recommendation_id, user_id, recorded_at,"
        " followed_recommendation, disagreed_firing_ids"
        ") VALUES (?, ?, ?, ?, 1, ?)",
        (
            SEED_REVIEW_EVENT_ID, SEED_RECOMMENDATION_ID, SEED_USER_ID,
            "2026-05-04T20:00:00Z",
            json.dumps([SEED_DISAGREED_FIRING_ID]),
        ),
    )

    # proposal_log + runtime_event_log + sync_run_log are referenced
    # by audit-ref-orphan fixtures (cited rows that DON'T exist).
    # Tables must exist so the gate's PK existence query doesn't
    # fail-closed via OperationalError.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS proposal_log "
        "(proposal_id TEXT PRIMARY KEY, domain TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS runtime_event_log "
        "(event_id INTEGER PRIMARY KEY, command TEXT)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sync_run_log "
        "(sync_id INTEGER PRIMARY KEY, source TEXT)"
    )
    conn.commit()
