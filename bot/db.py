"""
db.py — SQLite schema and data access for the health logger.

Tables:
  users         – user accounts
  invite_codes  – invite-only registration
  messages      – raw input audit trail
  meal_items    – individual food items with calorie/macro estimates
  exercises     – exercise entries
  exercise_sets – individual sets for strength exercises
  subjective    – energy, mood, sleep quality, etc. (1-10 scale)
  daily_summary – cached daily totals, recomputed after each message
  targets       – per-user daily targets
"""

import secrets
import sqlite3
from datetime import datetime, timedelta
from .config import DB_PATH


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Create all tables if they don't exist, then run migrations."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            username        TEXT NOT NULL UNIQUE,
            display_name    TEXT NOT NULL,
            password_hash   TEXT NOT NULL,
            is_admin        INTEGER DEFAULT 0,
            daily_msg_cap   INTEGER DEFAULT 20,
            consent_given   INTEGER DEFAULT 0,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS invite_codes (
            code            TEXT PRIMARY KEY,
            created_by      INTEGER REFERENCES users(id),
            used_by         INTEGER REFERENCES users(id),
            used_at         TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS messages (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            raw_text        TEXT NOT NULL,
            parsed_json     TEXT,
            created_at      TEXT NOT NULL DEFAULT (datetime('now')),
            date_for        TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS meal_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            message_id      INTEGER NOT NULL REFERENCES messages(id),
            meal_type       TEXT NOT NULL,
            item_name       TEXT NOT NULL,
            quantity_desc   TEXT,
            calories        INTEGER,
            protein_g       REAL,
            carbs_g         REAL,
            fat_g           REAL,
            fiber_g         REAL,
            confidence      REAL DEFAULT 0.7,
            source          TEXT DEFAULT 'claude_estimate',
            notes           TEXT,
            date_for        TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS exercises (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            message_id      INTEGER NOT NULL REFERENCES messages(id),
            exercise_type   TEXT NOT NULL,
            subtype         TEXT,
            muscle_group    TEXT,
            duration_min    INTEGER,
            intensity       TEXT,
            calories_est    INTEGER,
            notes           TEXT,
            confidence      REAL DEFAULT 0.7,
            source          TEXT DEFAULT 'user_reported',
            date_for        TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS subjective (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            message_id      INTEGER NOT NULL REFERENCES messages(id),
            metric          TEXT NOT NULL,
            value           REAL,
            label           TEXT,
            notes           TEXT,
            date_for        TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS exercise_sets (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL DEFAULT 1,
            exercise_id     INTEGER NOT NULL REFERENCES exercises(id),
            set_number      INTEGER NOT NULL,
            reps            INTEGER,
            weight_kg       REAL,
            duration_sec    INTEGER,
            is_pr           INTEGER DEFAULT 0,
            notes           TEXT,
            date_for        TEXT NOT NULL,
            created_at      TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS daily_summary (
            user_id         INTEGER NOT NULL DEFAULT 1,
            date_for        TEXT NOT NULL,
            total_calories  INTEGER,
            total_protein_g REAL,
            total_carbs_g   REAL,
            total_fat_g     REAL,
            total_fiber_g   REAL,
            meal_count      INTEGER,
            exercise_min    INTEGER,
            exercise_types  TEXT,
            updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, date_for)
        );

        CREATE TABLE IF NOT EXISTS targets (
            user_id         INTEGER NOT NULL DEFAULT 1,
            metric          TEXT NOT NULL,
            value           REAL NOT NULL,
            updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (user_id, metric)
        );
    """)
    _run_migrations(conn)
    conn.commit()
    conn.close()


def _run_migrations(conn: sqlite3.Connection):
    """Idempotent migrations for existing databases."""
    # Migration: add user_id to tables that predate multi-user support
    for table in ['messages', 'meal_items', 'exercises', 'subjective', 'exercise_sets']:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN user_id INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass  # Column already exists

    # Migration: add muscle_group to exercises if missing
    try:
        conn.execute("ALTER TABLE exercises ADD COLUMN muscle_group TEXT")
    except sqlite3.OperationalError:
        pass

    # Migration: daily_summary PK change (date_for) → (user_id, date_for)
    # Check if the old single-column PK schema is still in place
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(daily_summary)").fetchall()]
    if "user_id" not in cols:
        rows = conn.execute("SELECT * FROM daily_summary").fetchall()
        conn.execute("DROP TABLE daily_summary")
        conn.execute("""
            CREATE TABLE daily_summary (
                user_id         INTEGER NOT NULL DEFAULT 1,
                date_for        TEXT NOT NULL,
                total_calories  INTEGER,
                total_protein_g REAL,
                total_carbs_g   REAL,
                total_fat_g     REAL,
                total_fiber_g   REAL,
                meal_count      INTEGER,
                exercise_min    INTEGER,
                exercise_types  TEXT,
                updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, date_for)
            )
        """)
        for r in rows:
            conn.execute(
                """INSERT INTO daily_summary
                   (user_id, date_for, total_calories, total_protein_g, total_carbs_g,
                    total_fat_g, total_fiber_g, meal_count, exercise_min, exercise_types, updated_at)
                   VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r["date_for"], r["total_calories"], r["total_protein_g"],
                 r["total_carbs_g"], r["total_fat_g"], r["total_fiber_g"],
                 r["meal_count"], r["exercise_min"], r["exercise_types"], r["updated_at"]),
            )

    # Migration: targets PK change (metric) → (user_id, metric)
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(targets)").fetchall()]
    if "user_id" not in cols:
        rows = conn.execute("SELECT * FROM targets").fetchall()
        conn.execute("DROP TABLE targets")
        conn.execute("""
            CREATE TABLE targets (
                user_id     INTEGER NOT NULL DEFAULT 1,
                metric      TEXT NOT NULL,
                value       REAL NOT NULL,
                updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (user_id, metric)
            )
        """)
        for r in rows:
            conn.execute(
                "INSERT INTO targets (user_id, metric, value, updated_at) VALUES (1, ?, ?, ?)",
                (r["metric"], r["value"], r["updated_at"]),
            )


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------

def create_user(username: str, display_name: str, password_hash: str,
                consent_given: bool) -> int:
    """Insert a new user, return user ID."""
    conn = get_conn()
    cur = conn.execute(
        """INSERT INTO users (username, display_name, password_hash, consent_given)
           VALUES (?, ?, ?, ?)""",
        (username, display_name, password_hash, 1 if consent_given else 0),
    )
    user_id = cur.lastrowid
    conn.commit()
    conn.close()
    return user_id


def get_user_by_username(username: str) -> dict | None:
    """Look up a user by username for login."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_id(user_id: int) -> dict | None:
    """Look up a user by ID (for Flask-Login's user_loader)."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_invite_code(created_by: int) -> str:
    """Generate and store an invite code. Returns the code string."""
    code = secrets.token_urlsafe(6)  # ~8 chars
    conn = get_conn()
    conn.execute(
        "INSERT INTO invite_codes (code, created_by) VALUES (?, ?)",
        (code, created_by),
    )
    conn.commit()
    conn.close()
    return code


def redeem_invite_code(code: str, user_id: int) -> bool:
    """Mark an invite code as used. Returns True if valid and unused."""
    conn = get_conn()
    row = conn.execute(
        "SELECT code FROM invite_codes WHERE code = ? AND used_by IS NULL",
        (code,),
    ).fetchone()
    if row is None:
        conn.close()
        return False
    conn.execute(
        "UPDATE invite_codes SET used_by = ?, used_at = datetime('now') WHERE code = ?",
        (user_id, code),
    )
    conn.commit()
    conn.close()
    return True


def get_message_count_today(user_id: int, date_for: str) -> int:
    """Count messages sent by a user for a date (for rate limiting)."""
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) AS cnt FROM messages WHERE user_id = ? AND date_for = ?",
        (user_id, date_for),
    ).fetchone()
    conn.close()
    return row["cnt"]


# ---------------------------------------------------------------------------
# Message logging
# ---------------------------------------------------------------------------

def save_message(user_id: int, raw_text: str, date_for: str,
                 parsed_json: str | None = None) -> int:
    """Insert a raw message and return its ID."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO messages (user_id, raw_text, parsed_json, date_for) VALUES (?, ?, ?, ?)",
        (user_id, raw_text, parsed_json, date_for),
    )
    msg_id = cur.lastrowid
    conn.commit()
    conn.close()
    return msg_id


def update_message_json(msg_id: int, parsed_json: str):
    """Attach the full Claude response JSON to a message (for debugging)."""
    conn = get_conn()
    conn.execute(
        "UPDATE messages SET parsed_json = ? WHERE id = ?",
        (parsed_json, msg_id),
    )
    conn.commit()
    conn.close()


def save_entries(user_id: int, msg_id: int, parsed_data: dict, date_for: str):
    """Save structured output from Claude into meal_items, exercises, subjective.

    Then recompute the daily_summary for this user+date.
    """
    conn = get_conn()
    try:
        for meal in parsed_data.get("meals", []):
            meal_type = meal["meal_type"]
            for item in meal.get("items", []):
                conn.execute(
                    """INSERT INTO meal_items
                       (user_id, message_id, meal_type, item_name, quantity_desc,
                        calories, protein_g, carbs_g, fat_g, fiber_g,
                        confidence, notes, date_for)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, msg_id, meal_type, item["item_name"],
                     item.get("quantity_desc"), item.get("calories"),
                     item.get("protein_g"), item.get("carbs_g"),
                     item.get("fat_g"), item.get("fiber_g"),
                     item.get("confidence", 0.7), item.get("notes"),
                     date_for),
                )

        for ex in parsed_data.get("exercises", []):
            cur = conn.execute(
                """INSERT INTO exercises
                   (user_id, message_id, exercise_type, subtype, muscle_group, duration_min,
                    intensity, calories_est, notes, confidence, date_for)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, msg_id, ex["exercise_type"], ex.get("subtype"),
                 ex.get("muscle_group"), ex.get("duration_min"),
                 ex.get("intensity"), ex.get("calories_est"), ex.get("notes"),
                 ex.get("confidence", 0.7), date_for),
            )
            exercise_id = cur.lastrowid
            for i, s in enumerate(ex.get("sets", []), 1):
                conn.execute(
                    """INSERT INTO exercise_sets
                       (user_id, exercise_id, set_number, reps, weight_kg,
                        duration_sec, is_pr, notes, date_for)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (user_id, exercise_id, i, s.get("reps"), s.get("weight_kg"),
                     s.get("duration_sec"), 1 if s.get("is_pr") else 0,
                     s.get("notes"), date_for),
                )

        for sub in parsed_data.get("subjective", []):
            conn.execute(
                """INSERT INTO subjective
                   (user_id, message_id, metric, value, label, notes, date_for)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user_id, msg_id, sub["metric"], sub.get("value"),
                 sub.get("label"), sub.get("notes"), date_for),
            )

        _recompute_daily_summary(conn, user_id, date_for)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _recompute_daily_summary(conn: sqlite3.Connection, user_id: int, date_for: str):
    """Aggregate meal_items and exercises into daily_summary cache."""
    row = conn.execute("""
        SELECT
            COALESCE(SUM(calories), 0) AS total_calories,
            COALESCE(SUM(protein_g), 0) AS total_protein_g,
            COALESCE(SUM(carbs_g), 0) AS total_carbs_g,
            COALESCE(SUM(fat_g), 0) AS total_fat_g,
            COALESCE(SUM(fiber_g), 0) AS total_fiber_g,
            COUNT(*) AS meal_count
        FROM meal_items WHERE user_id = ? AND date_for = ?
    """, (user_id, date_for)).fetchone()

    ex_row = conn.execute("""
        SELECT
            COALESCE(SUM(duration_min), 0) AS exercise_min,
            GROUP_CONCAT(DISTINCT exercise_type) AS exercise_types
        FROM exercises WHERE user_id = ? AND date_for = ?
    """, (user_id, date_for)).fetchone()

    if row["meal_count"] == 0 and not ex_row["exercise_types"]:
        conn.execute(
            "DELETE FROM daily_summary WHERE user_id = ? AND date_for = ?",
            (user_id, date_for),
        )
        return

    conn.execute("""
        INSERT INTO daily_summary
            (user_id, date_for, total_calories, total_protein_g, total_carbs_g,
             total_fat_g, total_fiber_g, meal_count, exercise_min,
             exercise_types, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(user_id, date_for) DO UPDATE SET
            total_calories = excluded.total_calories,
            total_protein_g = excluded.total_protein_g,
            total_carbs_g = excluded.total_carbs_g,
            total_fat_g = excluded.total_fat_g,
            total_fiber_g = excluded.total_fiber_g,
            meal_count = excluded.meal_count,
            exercise_min = excluded.exercise_min,
            exercise_types = excluded.exercise_types,
            updated_at = excluded.updated_at
    """, (
        user_id, date_for, row["total_calories"], row["total_protein_g"],
        row["total_carbs_g"], row["total_fat_g"], row["total_fiber_g"],
        row["meal_count"], ex_row["exercise_min"], ex_row["exercise_types"],
    ))


# ---------------------------------------------------------------------------
# Delete operations
# ---------------------------------------------------------------------------

def delete_last_entry(user_id: int, date_for: str) -> str | None:
    """Delete all structured data from the most recent message for a user+date.

    Returns the raw_text of the deleted message, or None if nothing to delete.
    """
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, raw_text FROM messages WHERE user_id = ? AND date_for = ? ORDER BY id DESC LIMIT 1",
            (user_id, date_for),
        ).fetchone()
        if row is None:
            return None

        msg_id = row["id"]
        raw_text = row["raw_text"]

        conn.execute("DELETE FROM meal_items WHERE message_id = ?", (msg_id,))
        conn.execute(
            "DELETE FROM exercise_sets WHERE exercise_id IN "
            "(SELECT id FROM exercises WHERE message_id = ?)", (msg_id,))
        conn.execute("DELETE FROM exercises WHERE message_id = ?", (msg_id,))
        conn.execute("DELETE FROM subjective WHERE message_id = ?", (msg_id,))
        conn.execute("DELETE FROM messages WHERE id = ?", (msg_id,))

        _recompute_daily_summary(conn, user_id, date_for)
        conn.commit()
        return raw_text
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_item(user_id: int, item_id: int, item_type: str) -> dict | None:
    """Delete a single item (meal, exercise, or subjective) by its ID.

    Checks user_id ownership to prevent cross-user deletion.
    Returns dict with deleted item name and date_for, or None if not found.
    """
    conn = get_conn()
    try:
        if item_type == "meal":
            row = conn.execute(
                "SELECT item_name, date_for FROM meal_items WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            ).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM meal_items WHERE id = ?", (item_id,))
            deleted_name = row["item_name"]
            date_for = row["date_for"]

        elif item_type == "exercise":
            row = conn.execute(
                "SELECT exercise_type, subtype, date_for FROM exercises WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            ).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM exercise_sets WHERE exercise_id = ?", (item_id,))
            conn.execute("DELETE FROM exercises WHERE id = ?", (item_id,))
            deleted_name = row["subtype"] or row["exercise_type"]
            date_for = row["date_for"]

        elif item_type == "subjective":
            row = conn.execute(
                "SELECT metric, date_for FROM subjective WHERE id = ? AND user_id = ?",
                (item_id, user_id),
            ).fetchone()
            if not row:
                return None
            conn.execute("DELETE FROM subjective WHERE id = ?", (item_id,))
            deleted_name = row["metric"]
            date_for = row["date_for"]

        else:
            return None

        _recompute_daily_summary(conn, user_id, date_for)
        conn.commit()
        return {"deleted_name": deleted_name, "date_for": date_for}
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Read operations (all filtered by user_id)
# ---------------------------------------------------------------------------

def get_daily_summary(user_id: int, date_for: str) -> dict | None:
    """Fetch the cached daily summary for a user+date."""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM daily_summary WHERE user_id = ? AND date_for = ?",
        (user_id, date_for),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def get_subjective_entries(user_id: int, date_for: str) -> list[dict]:
    """Fetch all subjective entries for a user+date."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, metric, value, label, notes FROM subjective WHERE user_id = ? AND date_for = ?",
        (user_id, date_for),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_exercise_entries(user_id: int, date_for: str) -> list[dict]:
    """Fetch all exercise entries for a user+date."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, exercise_type, subtype, duration_min, intensity, calories_est, notes "
        "FROM exercises WHERE user_id = ? AND date_for = ?",
        (user_id, date_for),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_exercise_sets(user_id: int, date_for: str) -> list[dict]:
    """Fetch exercises with their individual sets for a user+date."""
    conn = get_conn()
    exercises = conn.execute(
        "SELECT id, exercise_type, subtype, muscle_group, duration_min, intensity, calories_est, notes "
        "FROM exercises WHERE user_id = ? AND date_for = ? ORDER BY id",
        (user_id, date_for),
    ).fetchall()

    result = []
    for ex in exercises:
        ex_dict = dict(ex)
        sets = conn.execute(
            "SELECT set_number, reps, weight_kg, duration_sec, is_pr, notes "
            "FROM exercise_sets WHERE exercise_id = ? ORDER BY set_number",
            (ex["id"],),
        ).fetchall()
        ex_dict["sets"] = [dict(s) for s in sets]
        result.append(ex_dict)

    conn.close()
    return result


def get_gym_summary(user_id: int, date_for: str) -> dict:
    """Compute gym summary stats for a user+date."""
    conn = get_conn()
    vol_row = conn.execute(
        """SELECT COALESCE(SUM(weight_kg * reps), 0) AS total_volume,
                  COUNT(*) AS total_sets,
                  COALESCE(SUM(is_pr), 0) AS pr_count
           FROM exercise_sets WHERE user_id = ? AND date_for = ?""",
        (user_id, date_for),
    ).fetchone()

    dur_row = conn.execute(
        "SELECT COALESCE(SUM(duration_min), 0) AS total_duration "
        "FROM exercises WHERE user_id = ? AND date_for = ?",
        (user_id, date_for),
    ).fetchone()

    conn.close()
    return {
        "total_volume": vol_row["total_volume"],
        "total_sets": vol_row["total_sets"],
        "pr_count": vol_row["pr_count"],
        "total_duration": dur_row["total_duration"],
    }


def get_exercise_history(user_id: int, limit: int = 14) -> list[dict]:
    """Get daily gym stats for recent days (for chart)."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT
            dur.date_for,
            dur.total_duration,
            COALESCE(vol.total_volume, 0) AS total_volume,
            COALESCE(vol.total_sets, 0) AS total_sets,
            COALESCE(vol.pr_count, 0) AS pr_count
        FROM (
            SELECT date_for, COALESCE(SUM(duration_min), 0) AS total_duration
            FROM exercises WHERE user_id = ? GROUP BY date_for
        ) dur
        LEFT JOIN (
            SELECT date_for,
                   SUM(weight_kg * reps) AS total_volume,
                   COUNT(*) AS total_sets,
                   SUM(is_pr) AS pr_count
            FROM exercise_sets WHERE user_id = ? GROUP BY date_for
        ) vol ON vol.date_for = dur.date_for
        ORDER BY dur.date_for DESC
        LIMIT ?
    """, (user_id, user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_time_prs(user_id: int) -> list[dict]:
    """Get all-time personal records for a user: heaviest weight per exercise."""
    conn = get_conn()
    rows = conn.execute("""
        SELECT exercise_name, weight_kg AS best_weight, reps, date_for
        FROM (
            SELECT e.subtype AS exercise_name,
                   es.weight_kg,
                   es.reps,
                   es.date_for,
                   ROW_NUMBER() OVER (
                       PARTITION BY e.subtype
                       ORDER BY es.weight_kg DESC, es.reps DESC
                   ) AS rn
            FROM exercise_sets es
            JOIN exercises e ON e.id = es.exercise_id
            WHERE es.weight_kg IS NOT NULL AND e.subtype IS NOT NULL
                  AND e.user_id = ?
        )
        WHERE rn = 1
        ORDER BY best_weight DESC
    """, (user_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_muscle_groups(user_id: int, date_for: str) -> list[str]:
    """Get distinct muscle groups trained on a given user+date."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT muscle_group FROM exercises "
        "WHERE user_id = ? AND date_for = ? AND muscle_group IS NOT NULL",
        (user_id, date_for),
    ).fetchall()
    conn.close()
    return [r["muscle_group"] for r in rows]


def get_meal_items(user_id: int, date_for: str) -> list[dict]:
    """Fetch all meal items for a user+date."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, meal_type, item_name, quantity_desc, calories, protein_g "
        "FROM meal_items WHERE user_id = ? AND date_for = ? ORDER BY id",
        (user_id, date_for),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_dates(user_id: int, limit: int = 7) -> list[str]:
    """Get the most recent dates that have logged data for a user."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT date_for FROM daily_summary WHERE user_id = ? ORDER BY date_for DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [r["date_for"] for r in rows]


def get_targets(user_id: int) -> dict:
    """Fetch all targets as {metric: value} dict for a user."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT metric, value FROM targets WHERE user_id = ?", (user_id,)
    ).fetchall()
    conn.close()
    return {r["metric"]: r["value"] for r in rows}


def set_target(user_id: int, metric: str, value: float):
    """Set or update a target value for a user."""
    conn = get_conn()
    conn.execute(
        """INSERT INTO targets (user_id, metric, value, updated_at)
           VALUES (?, ?, ?, datetime('now'))
           ON CONFLICT(user_id, metric) DO UPDATE SET
               value = excluded.value,
               updated_at = excluded.updated_at""",
        (user_id, metric, value),
    )
    conn.commit()
    conn.close()


def get_weekly_summary(user_id: int, end_date: str) -> dict | None:
    """Aggregate the last 7 days of data for a user's weekly digest."""
    end = datetime.strptime(end_date, "%Y-%m-%d")
    start = (end - timedelta(days=6)).strftime("%Y-%m-%d")

    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM daily_summary WHERE user_id = ? AND date_for BETWEEN ? AND ? ORDER BY date_for",
        (user_id, start, end_date),
    ).fetchall()
    conn.close()

    if not rows:
        return None

    rows = [dict(r) for r in rows]
    n = len(rows)

    cals = [r["total_calories"] or 0 for r in rows]
    return {
        "days_logged": n,
        "start_date": start,
        "end_date": end_date,
        "avg_calories": sum(cals) / n,
        "avg_protein": sum((r["total_protein_g"] or 0) for r in rows) / n,
        "avg_carbs": sum((r["total_carbs_g"] or 0) for r in rows) / n,
        "avg_fat": sum((r["total_fat_g"] or 0) for r in rows) / n,
        "total_exercise_min": sum((r["exercise_min"] or 0) for r in rows),
        "exercise_sessions": sum(1 for r in rows if (r["exercise_min"] or 0) > 0),
        "best_day": max(rows, key=lambda r: r["total_calories"] or 0)["date_for"],
        "worst_day": min(rows, key=lambda r: r["total_calories"] or 0)["date_for"],
    }


def get_logging_streak(user_id: int, today: str) -> int:
    """Count consecutive days with logged data ending at `today` for a user."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT DISTINCT date_for FROM daily_summary WHERE user_id = ? ORDER BY date_for DESC",
        (user_id,),
    ).fetchall()
    conn.close()

    dates = [r["date_for"] for r in rows]
    if not dates or dates[0] != today:
        return 0

    streak = 1
    for i in range(1, len(dates)):
        expected = (datetime.strptime(dates[i - 1], "%Y-%m-%d")
                    - timedelta(days=1)).strftime("%Y-%m-%d")
        if dates[i] == expected:
            streak += 1
        else:
            break
    return streak


if __name__ == "__main__":
    init_db()
    print(f"Database created at {DB_PATH}")
    conn = get_conn()
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    print(f"Tables: {[t['name'] for t in tables]}")
    conn.close()
