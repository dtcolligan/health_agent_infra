"""Phase 7C.3 — `hai intake stress` + `hai intake note` tests.

Phase 3 step 1 moved manual_stress_score + all_day_stress +
body_battery_end_of_day off ``accepted_recovery_state_daily`` onto the
new ``accepted_stress_state_daily`` and ``accepted_sleep_state_daily``
tables. Contracts below are updated to target the new surface; the
behavioural invariants are unchanged.

Stress contracts pinned:

  1. Manual stress flows raw → accepted with proper provenance —
     stress_manual_raw row, then accepted_stress_state_daily UPSERT
     with `derived_from = [stress_submission_id]`, `source='user_manual'`,
     `corrected_at` set on update.
  2. Stress-before-clean creates a minimal stress row (only
     manual_stress_score populated, Garmin stress + body_battery NULL).
  3. Clean-before-stress merges into the existing stress row and
     preserves Garmin-sourced fields (garmin_all_day_stress,
     body_battery_end_of_day).
  4. Re-running stress is a correction: supersedes chain in JSONL,
     accepted row reflects latest score, corrected_at set.
  5. After stress is set, re-running `hai clean` does NOT wipe
     manual_stress_score.
  6. Score outside 1-5 rejected at CLI boundary (argparse choices).
  7. Snapshot stress.today_manual reflects the merged value, missingness
     becomes 'present' once both Garmin + manual are set.
  8. Atomic projection on intake; DB-absent fail-soft; reproject round-trip;
     scope guard preserves other groups.

Note contracts pinned:

  1. Append-only — each invocation creates a new note_id, multiple
     same-day notes coexist.
  2. Empty --text rejected.
  3. Snapshot's notes.recent surfaces them.
  4. Reproject round-trip; scope guard preserves other groups.
"""

from __future__ import annotations

import json
from contextlib import closing
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.state import (
    build_snapshot,
    initialize_database,
    open_connection,
    project_accepted_recovery_state_daily,
    project_accepted_sleep_state_daily,
    project_accepted_stress_state_daily,
    read_domain,
)


USER = "u_test"
AS_OF = date(2026, 4, 17)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _init_intake_dirs(tmp_path: Path) -> tuple[Path, Path]:
    base = tmp_path / "intake"
    base.mkdir(parents=True, exist_ok=True)
    db = _init_db(tmp_path)
    return base, db


def _full_garmin_raw_row() -> dict:
    """Reusable raw row for testing stress-merges-with-garmin scenarios."""

    return {
        "resting_hr": 52.0, "all_day_stress": 30,
        "sleep_deep_sec": 5400, "sleep_light_sec": 12600,
        "sleep_rem_sec": 5400, "acute_load": 400.0,
        "chronic_load": 380.0, "distance_m": 8500.0,
        "moderate_intensity_min": 35, "vigorous_intensity_min": 18,
        "health_hrv_value": 48.0, "body_battery": 65,
        "training_readiness_sleep_pct": 82.0,
        "training_readiness_hrv_pct": 70.0,
        "training_readiness_stress_pct": 75.0,
        "training_readiness_sleep_history_pct": 88.0,
        "training_readiness_load_pct": 65.0,
    }


def _seed_full_clean(conn, *, source_row_ids: list[str]) -> None:
    """Run the three clean projectors atomically inside a test.

    Mirrors ``_dual_write_clean_projection`` in cli.py without going
    through the CLI. Any test that wants the full post-clean accepted
    state (recovery + sleep + stress) should call this instead of
    invoking project_accepted_recovery_state_daily in isolation.
    """

    row = _full_garmin_raw_row()
    project_accepted_recovery_state_daily(
        conn, as_of_date=AS_OF, user_id=USER,
        raw_row=row, source_row_ids=source_row_ids,
    )
    project_accepted_sleep_state_daily(
        conn, as_of_date=AS_OF, user_id=USER,
        raw_row=row, source_row_ids=source_row_ids,
    )
    project_accepted_stress_state_daily(
        conn, as_of_date=AS_OF, user_id=USER,
        raw_row=row, source_row_ids=source_row_ids,
    )


def _stress_args(base: Path, db: Path, *, score: int = 3,
                  as_of: str = AS_OF.isoformat(), tags: str | None = None) -> list[str]:
    args = [
        "intake", "stress",
        "--score", str(score),
        "--as-of", as_of, "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]
    if tags:
        args.extend(["--tags", tags])
    return args


def _note_args(base: Path, db: Path, *, text: str = "Felt great today",
                tags: str | None = None) -> list[str]:
    args = [
        "intake", "note",
        "--text", text,
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]
    if tags:
        args.extend(["--tags", tags])
    return args


# ---------------------------------------------------------------------------
# STRESS: raw + merge into accepted_stress_state_daily
# ---------------------------------------------------------------------------

def test_stress_intake_writes_jsonl_and_raw_and_merges_into_accepted(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main(_stress_args(base, db, score=3, tags="work,deadline"))
    assert rc == 0

    # JSONL captured.
    jsonl = base / "stress_manual.jsonl"
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["score"] == 3
    # Tags preserved in user-supplied order (json.dumps sort_keys only
    # affects dict keys, not list elements).
    assert lines[0]["tags"] == ["work", "deadline"]
    assert lines[0]["source"] == "user_manual"

    conn = open_connection(db)
    try:
        raw = conn.execute(
            "SELECT submission_id, score, tags FROM stress_manual_raw "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
        accepted = conn.execute(
            "SELECT manual_stress_score, stress_tags_json, derived_from, "
            "       source, ingest_actor, corrected_at "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    # Raw row written:
    assert raw["score"] == 3
    assert json.loads(raw["tags"]) == ["work", "deadline"]

    # Accepted stress row was INSERTed (no clean had run yet):
    assert accepted["manual_stress_score"] == 3
    assert json.loads(accepted["stress_tags_json"]) == ["work", "deadline"]
    # derived_from points back to the raw submission_id — provenance chain held.
    assert json.loads(accepted["derived_from"]) == [raw["submission_id"]]
    assert accepted["source"] == "user_manual"
    assert accepted["ingest_actor"] == "hai_cli_direct"
    assert accepted["corrected_at"] is None  # first insert


def test_stress_before_clean_creates_minimal_stress_row_with_null_garmin(tmp_path: Path):
    """Stress logged before any Garmin pull → stress row exists with
    only manual_stress_score populated. Snapshot tags Garmin stress
    fields as `unavailable_at_source`."""

    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_stress_args(base, db, score=4)) == 0

    conn = open_connection(db)
    try:
        stress_row = conn.execute(
            "SELECT manual_stress_score, garmin_all_day_stress, "
            "       body_battery_end_of_day "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
        recovery_row = conn.execute(
            "SELECT resting_hr, training_readiness_component_mean_pct "
            "FROM accepted_recovery_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert stress_row["manual_stress_score"] == 4
    assert stress_row["garmin_all_day_stress"] is None
    assert stress_row["body_battery_end_of_day"] is None
    # Recovery accepted row is untouched by the stress flow now — no
    # Garmin clean has run, so no recovery row exists.
    assert recovery_row is None

    # Stress block: Garmin null + manual present
    assert snap["stress"]["today_manual"] == 4
    assert snap["stress"]["missingness"] == "unavailable_at_source:garmin_all_day_stress"


def test_stress_after_clean_merges_into_existing_row_preserving_garmin(tmp_path: Path):
    """Run hai clean-style projection first, then hai intake stress.
    Manual stress merges in; Garmin stress + body battery untouched;
    corrected_at set."""

    base, db = _init_intake_dirs(tmp_path)

    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["batch_a:0"])
        before = conn.execute(
            "SELECT garmin_all_day_stress, body_battery_end_of_day, "
            "       manual_stress_score, source "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    assert before["garmin_all_day_stress"] == 30
    assert before["body_battery_end_of_day"] == 65
    assert before["manual_stress_score"] is None
    assert before["source"] == "garmin"

    # Now stress intake.
    assert cli_main(_stress_args(base, db, score=2)) == 0

    conn = open_connection(db)
    try:
        after = conn.execute(
            "SELECT manual_stress_score, garmin_all_day_stress, "
            "       body_battery_end_of_day, source, ingest_actor, corrected_at "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    # Manual stress merged:
    assert after["manual_stress_score"] == 2
    # Garmin-sourced fields preserved:
    assert after["garmin_all_day_stress"] == 30
    assert after["body_battery_end_of_day"] == 65
    # Source/ingest reflect the most recent write (the stress merge):
    assert after["source"] == "user_manual"
    assert after["ingest_actor"] == "hai_cli_direct"
    assert after["corrected_at"] is not None  # update set it


def test_clean_re_run_after_stress_does_not_wipe_manual_stress(tmp_path: Path):
    """Clean's UPDATE path must NOT touch manual_stress_score. After
    stress merges into accepted_stress_state_daily, a second clean run
    must keep manual_stress_score intact (now preserved by omission in
    the stress projector's UPDATE)."""

    base, db = _init_intake_dirs(tmp_path)

    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["a:0"])
    finally:
        conn.close()

    # Stress merges in.
    assert cli_main(_stress_args(base, db, score=4)) == 0

    # Second clean (e.g. user re-pulled).
    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["b:0"])
        row = conn.execute(
            "SELECT manual_stress_score, garmin_all_day_stress, "
            "       body_battery_end_of_day "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert row["manual_stress_score"] == 4, (
        "clean re-run wiped manual_stress_score — preservation contract broken"
    )
    assert row["garmin_all_day_stress"] == 30
    assert row["body_battery_end_of_day"] == 65


def test_stress_correction_chain_via_jsonl_supersedes(tmp_path: Path):
    """Two stress intakes same day: second supersedes first in JSONL,
    accepted manual_stress_score reflects latest, corrected_at set."""

    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_stress_args(base, db, score=2)) == 0
    assert cli_main(_stress_args(base, db, score=4)) == 0

    lines = [
        json.loads(l) for l in
        (base / "stress_manual.jsonl").read_text().splitlines() if l.strip()
    ]
    assert len(lines) == 2
    assert lines[0]["supersedes_submission_id"] is None
    assert lines[1]["supersedes_submission_id"] == lines[0]["submission_id"]

    conn = open_connection(db)
    try:
        raws = conn.execute(
            "SELECT submission_id, score, supersedes_submission_id "
            "FROM stress_manual_raw ORDER BY ingested_at"
        ).fetchall()
        accepted = conn.execute(
            "SELECT manual_stress_score, corrected_at, derived_from "
            "FROM accepted_stress_state_daily WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert len(raws) == 2
    assert raws[0]["supersedes_submission_id"] is None
    assert raws[1]["supersedes_submission_id"] == raws[0]["submission_id"]
    assert accepted["manual_stress_score"] == 4
    assert accepted["corrected_at"] is not None
    # derived_from points at the latest non-superseded raw
    assert json.loads(accepted["derived_from"]) == [raws[1]["submission_id"]]


def test_stress_db_absent_still_builds_correction_chain(tmp_path: Path):
    """Same DB-absent chain integrity contract as nutrition (7C.2 patch)."""

    base = tmp_path / "intake"
    base.mkdir()
    missing_db = tmp_path / "no_db.db"

    assert cli_main(_stress_args(base, missing_db, score=2)) == 0
    assert cli_main(_stress_args(base, missing_db, score=4)) == 0

    lines = [
        json.loads(l) for l in
        (base / "stress_manual.jsonl").read_text().splitlines() if l.strip()
    ]
    assert lines[0]["supersedes_submission_id"] is None
    assert lines[1]["supersedes_submission_id"] == lines[0]["submission_id"], (
        "DB-absent chain broken: stress chain resolver must read JSONL"
    )


def test_stress_score_out_of_range_rejected(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    with pytest.raises(SystemExit) as excinfo:
        cli_main([
            "intake", "stress", "--score", "0",
            "--as-of", AS_OF.isoformat(), "--user-id", USER,
            "--base-dir", str(base), "--db-path", str(db),
        ])
    assert excinfo.value.code == 2
    assert not (base / "stress_manual.jsonl").exists()


def test_stress_intake_atomic_on_middle_failure(tmp_path, monkeypatch):
    base, db = _init_intake_dirs(tmp_path)
    import health_agent_infra.core.state as state_pkg

    def boom(*a, **kw):
        raise RuntimeError("injected merge failure")

    monkeypatch.setattr(
        state_pkg, "merge_manual_stress_into_accepted_stress", boom,
    )
    rc = cli_main(_stress_args(base, db, score=3))
    assert rc == 0  # fail-soft

    # JSONL captured (audit before DB).
    assert (base / "stress_manual.jsonl").exists()

    conn = open_connection(db)
    try:
        n_raw = conn.execute("SELECT COUNT(*) FROM stress_manual_raw").fetchone()[0]
        n_stress_accepted = conn.execute(
            "SELECT COUNT(*) FROM accepted_stress_state_daily"
        ).fetchone()[0]
    finally:
        conn.close()
    # Both rolled back together.
    assert n_raw == 0
    assert n_stress_accepted == 0


def test_stress_snapshot_present_when_garmin_and_manual_both_set(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["g:0"])
    finally:
        conn.close()
    assert cli_main(_stress_args(base, db, score=3)) == 0

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    assert snap["stress"]["today_garmin"] == 30
    assert snap["stress"]["today_manual"] == 3
    assert snap["stress"]["today_body_battery"] == 65
    assert snap["stress"]["missingness"] == "present"


# ---------------------------------------------------------------------------
# NOTES: append-only, no chain
# ---------------------------------------------------------------------------

def test_note_intake_writes_jsonl_and_db(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main(_note_args(
        base, db, text="Slept poorly, big work day", tags="sleep,work",
    ))
    assert rc == 0

    jsonl = base / "context_notes.jsonl"
    lines = [json.loads(l) for l in jsonl.read_text().splitlines() if l.strip()]
    assert len(lines) == 1
    assert lines[0]["text"] == "Slept poorly, big work day"
    assert lines[0]["tags"] == ["sleep", "work"]

    with closing(open_connection(db)) as conn:
        rows = read_domain(
            conn,
            domain="notes", since=AS_OF, until=AS_OF, user_id=USER,
        )
    assert len(rows) == 1
    assert rows[0]["text"] == "Slept poorly, big work day"
    assert json.loads(rows[0]["tags"]) == ["sleep", "work"]


def test_note_multiple_same_day_accumulate(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_note_args(base, db, text="Morning: woke up tired")) == 0
    assert cli_main(_note_args(base, db, text="Lunch: heavy meal, sluggish")) == 0
    assert cli_main(_note_args(base, db, text="Evening: feeling better")) == 0

    with closing(open_connection(db)) as conn:
        rows = read_domain(
            conn,
            domain="notes", since=AS_OF, until=AS_OF, user_id=USER,
        )
    assert len(rows) == 3
    # All distinct note_ids:
    assert len({r["note_id"] for r in rows}) == 3


def test_note_empty_text_rejected(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    rc = cli_main([
        "intake", "note", "--text", "   ",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ])
    assert rc == exit_codes.USER_INPUT
    assert not (base / "context_notes.jsonl").exists()


def test_note_snapshot_recent_lookback(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_note_args(base, db, text="Today's note")) == 0
    # A note from 5 days ago.
    assert cli_main([
        "intake", "note", "--text", "Older note",
        "--as-of", "2026-04-12", "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]) == 0

    conn = open_connection(db)
    try:
        snap = build_snapshot(
            conn, as_of_date=AS_OF, user_id=USER, lookback_days=14,
            now_local=datetime(2026, 5, 1, 10, 0),
        )
    finally:
        conn.close()

    # Recent notes show the older note (within lookback window).
    # Today's note is in `today` semantically but the snapshot's notes
    # block is `recent` (history-only), so we verify the older one lands.
    recent = snap["notes"]["recent"]
    texts = [n["text"] for n in recent]
    assert "Older note" in texts


# ---------------------------------------------------------------------------
# Provenance: derived_from carries both Garmin + stress contributors
# (7C.3 patch — per-dimension slot replacement, now on accepted_stress_state_daily)
# ---------------------------------------------------------------------------

def test_derived_from_carries_both_garmin_and_stress_after_clean_then_stress(tmp_path: Path):
    """After clean populates Garmin stress fields and intake merges manual
    score, derived_from on the stress row must list BOTH the garmin
    contributor AND the stress submission_id. The state model says
    accepted state lists every raw row that contributed to its current
    values."""

    base, db = _init_intake_dirs(tmp_path)
    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["garmin_batch_a:0"])
    finally:
        conn.close()

    assert cli_main(_stress_args(base, db, score=4)) == 0

    conn = open_connection(db)
    try:
        row = conn.execute(
            "SELECT derived_from, manual_stress_score FROM "
            "accepted_stress_state_daily WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    derived = json.loads(row["derived_from"])
    assert "garmin_batch_a:0" in derived, (
        "Garmin contributor evicted by stress merge — derived_from is "
        "supposed to be cumulative across dimensions"
    )
    stress_ids = [d for d in derived if d.startswith("m_stress_")]
    assert len(stress_ids) == 1, (
        f"expected exactly one stress submission in derived_from, got {derived}"
    )
    assert row["manual_stress_score"] == 4


def test_derived_from_evicts_old_garmin_when_clean_re_runs(tmp_path: Path):
    """clean → stress → clean must end with [latest_garmin, latest_stress]
    on the stress accepted row. The first garmin batch is replaced by the
    second; the stress slot is preserved across the second clean."""

    base, db = _init_intake_dirs(tmp_path)

    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["garmin_batch_a:0"])
    finally:
        conn.close()

    assert cli_main(_stress_args(base, db, score=3)) == 0

    conn = open_connection(db)
    try:
        # Second Garmin clean (e.g. user re-pulled).
        _seed_full_clean(conn, source_row_ids=["garmin_batch_b:0"])
        row = conn.execute(
            "SELECT derived_from, manual_stress_score FROM "
            "accepted_stress_state_daily WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    derived = json.loads(row["derived_from"])
    # Latest garmin batch only (first batch evicted).
    assert "garmin_batch_b:0" in derived
    assert "garmin_batch_a:0" not in derived, (
        "old Garmin batch ID survived a re-clean — per-dimension replacement "
        "should evict prior contributors in the same dimension"
    )
    # Stress slot preserved across the second clean.
    stress_ids = [d for d in derived if d.startswith("m_stress_")]
    assert len(stress_ids) == 1, (
        f"stress contributor lost on clean re-run: derived_from = {derived}"
    )
    # And the score persists.
    assert row["manual_stress_score"] == 3


def test_derived_from_evicts_superseded_stress_on_correction(tmp_path: Path):
    """Stress correction (sub_b supersedes sub_a) must leave only
    [garmin_contributor, sub_b] on the stress accepted row — sub_a is no
    longer a current contributor (the merge function pulls only the
    latest non-superseded raw to source from)."""

    base, db = _init_intake_dirs(tmp_path)

    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["garmin_only:0"])
    finally:
        conn.close()

    assert cli_main(_stress_args(base, db, score=2)) == 0
    assert cli_main(_stress_args(base, db, score=4)) == 0  # correction

    conn = open_connection(db)
    try:
        raws = conn.execute(
            "SELECT submission_id FROM stress_manual_raw "
            "WHERE user_id = ? AND as_of_date = ? ORDER BY ingested_at",
            (USER, AS_OF.isoformat()),
        ).fetchall()
        derived = json.loads(conn.execute(
            "SELECT derived_from FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()["derived_from"])
    finally:
        conn.close()

    sub_a_id, sub_b_id = raws[0]["submission_id"], raws[1]["submission_id"]
    assert sub_a_id not in derived, (
        f"superseded stress submission survived in derived_from: {derived}"
    )
    assert sub_b_id in derived
    assert "garmin_only:0" in derived  # garmin slot preserved


# ---------------------------------------------------------------------------
# Reproject hygiene: drop manual_stress_score for days no longer in JSONL
# (7C.3 patch — co-owned column orphan cleanup, now on stress table)
# ---------------------------------------------------------------------------

def test_reproject_clears_manual_stress_for_days_dropped_from_jsonl(tmp_path: Path):
    """Stress reproject must NULL out manual_stress_score on
    accepted_stress_state_daily for any row whose day is no longer in the
    replayed stress_manual.jsonl. Without this, accepted has data with
    no raw backing — the "accepted derives from raw" invariant breaks."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_intake_dirs(tmp_path)

    # Two days of stress.
    assert cli_main(_stress_args(base, db, score=2, as_of="2026-04-17")) == 0
    assert cli_main(_stress_args(base, db, score=4, as_of="2026-04-18")) == 0

    # Replace the JSONL with one that ONLY mentions 2026-04-18.
    # Match the as_of_date field directly — a naive `"2026-04-18" in l`
    # substring match also catches `ingested_at` timestamps when the test
    # runs on that calendar day, which would silently keep both rows.
    full = (base / "stress_manual.jsonl").read_text().splitlines()
    keep = [
        l for l in full
        if l.strip() and json.loads(l).get("as_of_date") == "2026-04-18"
    ]
    (base / "stress_manual.jsonl").write_text("\n".join(keep) + "\n")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        rows = conn.execute(
            "SELECT as_of_date, manual_stress_score, derived_from "
            "FROM accepted_stress_state_daily ORDER BY as_of_date"
        ).fetchall()
        n_raw = conn.execute("SELECT COUNT(*) FROM stress_manual_raw").fetchone()[0]
    finally:
        conn.close()

    # Raw layer reflects the trimmed JSONL.
    assert n_raw == 1
    # Accepted layer: 2026-04-17 (dropped from JSONL) must have NULL
    # manual_stress_score now; 2026-04-18 keeps its score from the merge.
    by_date = {r["as_of_date"]: r for r in rows}
    assert by_date["2026-04-17"]["manual_stress_score"] is None, (
        "orphaned manual_stress_score survived stress reproject — accepted "
        "no longer derives from raw for this day"
    )
    # Stress IDs stripped from derived_from for the dropped day.
    derived_17 = json.loads(by_date["2026-04-17"]["derived_from"])
    assert all(not d.startswith("m_stress_") for d in derived_17), (
        f"stale stress submission IDs survived in derived_from: {derived_17}"
    )
    assert by_date["2026-04-18"]["manual_stress_score"] == 4
    derived_18 = json.loads(by_date["2026-04-18"]["derived_from"])
    assert any(d.startswith("m_stress_") for d in derived_18)
    assert counts["accepted_stress_manual_merged"] == 1


def test_reproject_hygiene_restores_garmin_provenance_when_stress_dropped(tmp_path: Path):
    """After stress hygiene strips the manual contributor, source +
    ingest_actor on the stress accepted row must reflect the surviving
    garmin contributor — not the stale 'user_manual'/'hai_cli_direct'
    values left by the evicted stress merge."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_intake_dirs(tmp_path)

    # Seed with garmin clean, then merge in a stress score.
    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["garmin_keep:0"])
    finally:
        conn.close()
    assert cli_main(_stress_args(base, db, score=4)) == 0

    conn = open_connection(db)
    try:
        before = conn.execute(
            "SELECT source, ingest_actor, manual_stress_score "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()
    # Pre-state: stress merge dominates provenance.
    assert before["source"] == "user_manual"
    assert before["ingest_actor"] == "hai_cli_direct"
    assert before["manual_stress_score"] == 4

    # Replay a stress JSONL that doesn't mention this day. The stress
    # contributor is removed; the garmin contributor survives.
    (base / "stress_manual.jsonl").write_text(json.dumps({
        "submission_id": "m_stress_2099-01-01_zzz",
        "user_id": "u_other", "as_of_date": "2099-01-01",
        "score": 1, "tags": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2099-01-01T00:00:00+00:00",
        "supersedes_submission_id": None,
    }) + "\n")

    conn = open_connection(db)
    try:
        reproject_from_jsonl(conn, base)
        after = conn.execute(
            "SELECT manual_stress_score, derived_from, source, ingest_actor "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert after["manual_stress_score"] is None
    derived = json.loads(after["derived_from"])
    assert "garmin_keep:0" in derived
    assert all(not d.startswith("m_stress_") for d in derived)
    # The fix: source/ingest reset to reflect the surviving Garmin contributor.
    assert after["source"] == "garmin", (
        f"stale user_manual source survived stress hygiene; got {after['source']!r}"
    )
    assert after["ingest_actor"] == "garmin_csv_adapter", (
        f"stale hai_cli_direct ingest_actor survived; got {after['ingest_actor']!r}"
    )


def test_reproject_preserves_garmin_contributors_on_stress_hygiene(tmp_path: Path):
    """The reproject hygiene step must only strip stress IDs from the
    stress table's derived_from; Garmin contributor IDs must survive."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_intake_dirs(tmp_path)

    # Pre-seed with both Garmin + stress contributors on the stress row.
    conn = open_connection(db)
    try:
        _seed_full_clean(conn, source_row_ids=["garmin_keepme:0"])
    finally:
        conn.close()
    assert cli_main(_stress_args(base, db, score=3)) == 0

    # Inject a single-line stress JSONL for an unrelated day so the
    # stress group is "present" without affecting AS_OF.
    (base / "stress_manual.jsonl").write_text(json.dumps({
        "submission_id": "m_stress_2099-01-01_zzz",
        "user_id": "u_other",
        "as_of_date": "2099-01-01",
        "score": 1, "tags": None,
        "source": "user_manual", "ingest_actor": "hai_cli_direct",
        "submitted_at": "2099-01-01T00:00:00+00:00",
        "supersedes_submission_id": None,
    }) + "\n")

    conn = open_connection(db)
    try:
        reproject_from_jsonl(conn, base)
        row = conn.execute(
            "SELECT manual_stress_score, derived_from "
            "FROM accepted_stress_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
    finally:
        conn.close()

    assert row["manual_stress_score"] is None
    derived = json.loads(row["derived_from"])
    assert "garmin_keepme:0" in derived, (
        f"Garmin contributor ID was stripped during stress hygiene: {derived}"
    )
    assert all(not d.startswith("m_stress_") for d in derived)


# ---------------------------------------------------------------------------
# REPROJECT: stress + notes
# ---------------------------------------------------------------------------

def test_reproject_rebuilds_stress_and_merges_into_accepted(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    # Two-day stress log with a same-day correction on day one.
    assert cli_main(_stress_args(base, db, score=2, as_of="2026-04-17")) == 0
    assert cli_main(_stress_args(base, db, score=4, as_of="2026-04-17")) == 0
    assert cli_main(_stress_args(base, db, score=3, as_of="2026-04-18")) == 0

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base), "--db-path", str(db),
    ])
    assert rc == 0

    conn = open_connection(db)
    try:
        raw_count = conn.execute("SELECT COUNT(*) FROM stress_manual_raw").fetchone()[0]
        days = conn.execute(
            "SELECT as_of_date, manual_stress_score FROM accepted_stress_state_daily "
            "ORDER BY as_of_date"
        ).fetchall()
    finally:
        conn.close()

    assert raw_count == 3
    assert [(r["as_of_date"], r["manual_stress_score"]) for r in days] == [
        ("2026-04-17", 4),  # latest non-superseded wins
        ("2026-04-18", 3),
    ]


def test_reproject_rebuilds_context_notes(tmp_path: Path):
    base, db = _init_intake_dirs(tmp_path)
    assert cli_main(_note_args(base, db, text="A")) == 0
    assert cli_main(_note_args(base, db, text="B")) == 0

    rc = cli_main([
        "state", "reproject",
        "--base-dir", str(base), "--db-path", str(db),
    ])
    assert rc == 0
    with closing(open_connection(db)) as conn:
        rows = read_domain(
            conn,
            domain="notes", since=AS_OF, until=AS_OF, user_id=USER,
        )
    assert {r["text"] for r in rows} == {"A", "B"}


def test_reproject_stress_only_preserves_other_groups(tmp_path: Path):
    """Scope-guard regression: stress-only base_dir doesn't wipe nutrition,
    gym, recommendation tables."""

    from health_agent_infra.core.state import reproject_from_jsonl

    base, db = _init_intake_dirs(tmp_path)
    # Seed a nutrition row via its full CLI path (writes nutrition_intake.jsonl).
    assert cli_main([
        "intake", "nutrition",
        "--calories", "2200", "--protein-g", "180",
        "--carbs-g", "260", "--fat-g", "70",
        "--as-of", AS_OF.isoformat(), "--user-id", USER,
        "--base-dir", str(base), "--db-path", str(db),
    ]) == 0

    # Seed a stress row.
    assert cli_main(_stress_args(base, db, score=3)) == 0

    # Move nutrition JSONL out so the next reproject only sees stress.
    (base / "nutrition_intake.jsonl").rename(tmp_path / "moved_nut.jsonl")

    conn = open_connection(db)
    try:
        counts = reproject_from_jsonl(conn, base)
        nut_n = conn.execute("SELECT COUNT(*) FROM nutrition_intake_raw").fetchone()[0]
        nut_accepted = conn.execute(
            "SELECT calories FROM accepted_nutrition_state_daily "
            "WHERE user_id = ? AND as_of_date = ?",
            (USER, AS_OF.isoformat()),
        ).fetchone()
        stress_n = conn.execute("SELECT COUNT(*) FROM stress_manual_raw").fetchone()[0]
    finally:
        conn.close()

    assert counts["nutrition_intake_raw"] == 0  # group untouched
    assert counts["stress_manual_raw"] == 1
    assert nut_n == 1, "nutrition wiped by stress-only reproject"
    assert nut_accepted["calories"] == 2200
    assert stress_n == 1
