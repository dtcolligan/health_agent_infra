"""D1 §review record behavior — outcome re-link on supersede.

Test coverage items #8 and #9 from
``reporting/plans/v0_1_4/D1_re_author_semantics.md``:

  #8 — Re-link happy path: an outcome recorded against a superseded
       plan's recommendation is persisted against the canonical leaf's
       matching-domain rec; both JSONL and DB row carry the
       ``re_linked_from_recommendation_id`` + ``re_link_note`` audit.

  #9 — Refuse path: when the canonical leaf has no matching-domain rec
       for the same ``for_date``, ``hai review record`` exits
       ``USER_INPUT`` with a clear stderr message; nothing is written.

Plus a few edge cases that tighten the contract:

  - Passthrough: non-superseded plan leaves the outcome untouched.
  - DB-absent: skip resolution, emit stderr hint, still write JSONL.
  - Chain walk: v1 → v2 → v3 re-links the outcome all the way to v3.
"""

from __future__ import annotations

import io
import json
import sqlite3
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

import pytest

from health_agent_infra.cli import main as cli_main
from health_agent_infra.core import exit_codes
from health_agent_infra.core.review.outcomes import (
    ReLinkResolution,
    resolve_review_relink,
)
from health_agent_infra.core.schemas import canonical_daily_plan_id
from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)


USER = "u_relink"
AS_OF = date(2026, 4, 23)


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


def _seed_plan(
    db: Path,
    *,
    plan_id: str,
    rec_ids_by_domain: dict[str, str],
) -> None:
    """Insert a ``daily_plan`` + one ``recommendation_log`` row per domain."""

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
                "2026-04-23T07:00:00+00:00",
                json.dumps(list(rec_ids_by_domain.values())),
                "2026-04-23T07:00:00+00:00",
                "2026-04-23T07:00:00+00:00",
            ),
        )
        for domain, rec_id in rec_ids_by_domain.items():
            payload = {
                "recommendation_id": rec_id,
                "domain": domain,
                "action": "proceed_with_planned_session",
                "confidence": "moderate",
                "rationale": [f"{domain}_ok"],
                "uncertainty": [],
                "follow_up": {"review_question": f"How was {domain} today?"},
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
                    rec_id, USER, AS_OF.isoformat(),
                    "2026-04-23T07:00:00+00:00",
                    payload["action"], payload["confidence"],
                    json.dumps(payload),
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    "2026-04-23T07:00:00+00:00",
                    domain, plan_id,
                ),
            )
        conn.commit()


def _seed_review_event(
    db: Path,
    *,
    review_event_id: str,
    recommendation_id: str,
    domain: str = "recovery",
) -> None:
    """Seed a ``review_event`` row — required for the FK on ``review_outcome``."""

    with sqlite3.connect(db) as conn:
        conn.execute(
            """
            INSERT INTO review_event (
                review_event_id, recommendation_id, user_id,
                review_at, review_question, domain, projected_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                review_event_id, recommendation_id, USER,
                "2026-04-24T07:00:00+00:00",
                "How did yesterday land?", domain,
                "2026-04-24T07:00:00+00:00",
            ),
        )
        conn.commit()


def _link_supersede(db: Path, *, from_id: str, to_id: str) -> None:
    with sqlite3.connect(db) as conn:
        conn.execute(
            "UPDATE daily_plan SET superseded_by_plan_id = ?, "
            "superseded_at = ? WHERE daily_plan_id = ?",
            (to_id, "2026-04-23T12:00:00+00:00", from_id),
        )
        conn.commit()


def _run_review_record(
    db: Path,
    base_dir: Path,
    outcome_json_path: Path,
) -> tuple[int, str, str]:
    argv = [
        "review", "record",
        "--outcome-json", str(outcome_json_path),
        "--base-dir", str(base_dir),
        "--db-path", str(db),
    ]
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
        rc = cli_main(argv)
    return rc, stdout_buf.getvalue(), stderr_buf.getvalue()


def _write_outcome_json(
    tmp_path: Path,
    *,
    review_event_id: str,
    recommendation_id: str,
    domain: str = "recovery",
    followed: bool = True,
    improved: bool = True,
) -> Path:
    path = tmp_path / f"{review_event_id}_outcome.json"
    path.write_text(json.dumps({
        "review_event_id": review_event_id,
        "recommendation_id": recommendation_id,
        "user_id": USER,
        "domain": domain,
        "followed_recommendation": followed,
        "self_reported_improvement": improved,
        "free_text": None,
    }), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Resolver-level: exercised directly against a connection
# ---------------------------------------------------------------------------


def test_resolver_passthrough_on_canonical_leaf(tmp_path: Path):
    db = _init_db(tmp_path)
    plan_id = canonical_daily_plan_id(AS_OF, USER)
    rec_id = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    _seed_plan(db, plan_id=plan_id, rec_ids_by_domain={"recovery": rec_id})

    with open_connection(db) as conn:
        resolution = resolve_review_relink(conn, recommendation_id=rec_id)

    assert resolution == ReLinkResolution(recommendation_id=rec_id)


def test_resolver_re_links_to_canonical_leaf_when_plan_superseded(tmp_path: Path):
    """D1 unit test #8 — the happy path.

    Seed a v1 → v2 supersede chain where both plans have a recovery rec.
    Resolve re-link for the v1 rec id; expect the v2 rec id back plus the
    audit fields.
    """

    db = _init_db(tmp_path)
    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"
    v1_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    v2_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01_v2"

    _seed_plan(db, plan_id=v1_id, rec_ids_by_domain={"recovery": v1_rec})
    _seed_plan(db, plan_id=v2_id, rec_ids_by_domain={"recovery": v2_rec})
    _link_supersede(db, from_id=v1_id, to_id=v2_id)

    with open_connection(db) as conn:
        resolution = resolve_review_relink(conn, recommendation_id=v1_rec)

    assert resolution.recommendation_id == v2_rec
    assert resolution.re_linked_from_recommendation_id == v1_rec
    assert resolution.re_link_note is not None
    assert v1_rec in resolution.re_link_note
    assert v2_rec in resolution.re_link_note
    assert resolution.refuse is False


def test_resolver_refuses_when_leaf_has_no_matching_domain(tmp_path: Path):
    """D1 unit test #9 — refuse path.

    v1 has a recovery rec; v2 has NO recovery rec (only a sleep rec).
    The resolver returns a refuse=True resolution rather than
    silently picking a non-matching domain.
    """

    db = _init_db(tmp_path)
    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"
    v1_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    v2_rec_sleep = f"rec_{AS_OF.isoformat()}_{USER}_sleep_01_v2"

    _seed_plan(db, plan_id=v1_id, rec_ids_by_domain={"recovery": v1_rec})
    _seed_plan(db, plan_id=v2_id, rec_ids_by_domain={"sleep": v2_rec_sleep})
    _link_supersede(db, from_id=v1_id, to_id=v2_id)

    with open_connection(db) as conn:
        resolution = resolve_review_relink(conn, recommendation_id=v1_rec)

    assert resolution.refuse is True
    assert resolution.refusal_reason is not None
    assert v1_rec in resolution.refusal_reason
    assert "recovery" in resolution.refusal_reason


def test_resolver_walks_multi_step_chain_to_final_leaf(tmp_path: Path):
    """v1 → v2 → v3; re-link should target v3's rec, not v2's."""

    db = _init_db(tmp_path)
    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"
    v3_id = f"{v1_id}_v3"
    v1_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    v2_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01_v2"
    v3_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01_v3"

    _seed_plan(db, plan_id=v1_id, rec_ids_by_domain={"recovery": v1_rec})
    _seed_plan(db, plan_id=v2_id, rec_ids_by_domain={"recovery": v2_rec})
    _seed_plan(db, plan_id=v3_id, rec_ids_by_domain={"recovery": v3_rec})
    _link_supersede(db, from_id=v1_id, to_id=v2_id)
    _link_supersede(db, from_id=v2_id, to_id=v3_id)

    with open_connection(db) as conn:
        resolution = resolve_review_relink(conn, recommendation_id=v1_rec)

    assert resolution.recommendation_id == v3_rec
    assert resolution.re_linked_from_recommendation_id == v1_rec


# ---------------------------------------------------------------------------
# CLI-level: `hai review record` end-to-end
# ---------------------------------------------------------------------------


def test_cli_review_record_re_links_outcome_on_superseded_plan(tmp_path: Path):
    """End-to-end: running ``hai review record`` against a v1 rec while v2
    exists writes the outcome against the v2 rec in both the JSONL and
    the state DB projection, with re-link audit populated.
    """

    db = _init_db(tmp_path)
    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"
    v1_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    v2_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01_v2"

    _seed_plan(db, plan_id=v1_id, rec_ids_by_domain={"recovery": v1_rec})
    _seed_plan(db, plan_id=v2_id, rec_ids_by_domain={"recovery": v2_rec})
    _link_supersede(db, from_id=v1_id, to_id=v2_id)

    review_event_id = f"rev_{AS_OF.isoformat()}_{USER}_recovery"
    _seed_review_event(
        db,
        review_event_id=review_event_id,
        recommendation_id=v1_rec,
    )

    outcome_json = _write_outcome_json(
        tmp_path,
        review_event_id=review_event_id,
        recommendation_id=v1_rec,
    )

    rc, out, err = _run_review_record(db, base_dir, outcome_json)
    assert rc == exit_codes.OK, err
    assert f"re-linked from {v1_rec} to {v2_rec}" in err

    # JSONL is rewritten to the leaf rec.
    outcomes_path = base_dir / "review_outcomes.jsonl"
    lines = outcomes_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    outcome = json.loads(lines[0])
    assert outcome["recommendation_id"] == v2_rec
    assert outcome["re_linked_from_recommendation_id"] == v1_rec
    assert outcome["re_link_note"] is not None

    # stdout echo of the outcome matches the JSONL.
    stdout_obj = json.loads(out)
    assert stdout_obj["recommendation_id"] == v2_rec
    assert stdout_obj["re_linked_from_recommendation_id"] == v1_rec

    # DB row carries the re-link audit columns.
    with sqlite3.connect(db) as conn:
        row = conn.execute(
            "SELECT recommendation_id, re_linked_from_recommendation_id, "
            "re_link_note FROM review_outcome WHERE review_event_id = ?",
            (review_event_id,),
        ).fetchone()
    assert row is not None
    assert row[0] == v2_rec
    assert row[1] == v1_rec
    assert row[2] is not None


def test_cli_review_record_refuses_when_leaf_has_no_matching_domain(tmp_path: Path):
    """End-to-end: the refuse path exits USER_INPUT and writes nothing.

    Neither the JSONL nor the DB row should appear when the leaf has no
    matching-domain rec — a partial write here would produce the exact
    orphan D1 was written to prevent.
    """

    db = _init_db(tmp_path)
    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    v1_id = canonical_daily_plan_id(AS_OF, USER)
    v2_id = f"{v1_id}_v2"
    v1_rec = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    v2_rec_sleep = f"rec_{AS_OF.isoformat()}_{USER}_sleep_01_v2"

    _seed_plan(db, plan_id=v1_id, rec_ids_by_domain={"recovery": v1_rec})
    _seed_plan(db, plan_id=v2_id, rec_ids_by_domain={"sleep": v2_rec_sleep})
    _link_supersede(db, from_id=v1_id, to_id=v2_id)

    review_event_id = f"rev_{AS_OF.isoformat()}_{USER}_recovery"
    _seed_review_event(
        db,
        review_event_id=review_event_id,
        recommendation_id=v1_rec,
    )

    outcome_json = _write_outcome_json(
        tmp_path,
        review_event_id=review_event_id,
        recommendation_id=v1_rec,
    )

    rc, _out, err = _run_review_record(db, base_dir, outcome_json)
    assert rc == exit_codes.USER_INPUT
    assert "refused" in err
    assert v1_rec in err
    assert "recovery" in err

    assert not (base_dir / "review_outcomes.jsonl").exists()
    with sqlite3.connect(db) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM review_outcome WHERE review_event_id = ?",
            (review_event_id,),
        ).fetchone()[0]
    assert count == 0


def test_cli_review_record_passthrough_on_canonical_leaf(tmp_path: Path):
    """Common-path sanity: non-superseded plan → no re-link, no stderr
    noise, outcome records against the original rec id.
    """

    db = _init_db(tmp_path)
    base_dir = tmp_path / "writeback"
    base_dir.mkdir()

    plan_id = canonical_daily_plan_id(AS_OF, USER)
    rec_id = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    _seed_plan(db, plan_id=plan_id, rec_ids_by_domain={"recovery": rec_id})

    review_event_id = f"rev_{AS_OF.isoformat()}_{USER}_recovery"
    _seed_review_event(
        db,
        review_event_id=review_event_id,
        recommendation_id=rec_id,
    )

    outcome_json = _write_outcome_json(
        tmp_path,
        review_event_id=review_event_id,
        recommendation_id=rec_id,
    )

    rc, _out, err = _run_review_record(db, base_dir, outcome_json)
    assert rc == exit_codes.OK, err
    assert "re-linked" not in err

    lines = (base_dir / "review_outcomes.jsonl").read_text(
        encoding="utf-8",
    ).splitlines()
    outcome = json.loads(lines[0])
    assert outcome["recommendation_id"] == rec_id
    assert outcome["re_linked_from_recommendation_id"] is None
    assert outcome["re_link_note"] is None


def test_cli_review_record_db_absent_skips_relink_with_stderr_note(tmp_path: Path):
    """DB-absent: the re-link resolver is skipped (can't walk the chain),
    stderr gets a note, JSONL still lands with the original rec id.
    """

    base_dir = tmp_path / "writeback"
    base_dir.mkdir()
    missing_db = tmp_path / "does_not_exist.db"
    assert not missing_db.exists()

    review_event_id = f"rev_{AS_OF.isoformat()}_{USER}_recovery"
    rec_id = f"rec_{AS_OF.isoformat()}_{USER}_recovery_01"
    outcome_json = _write_outcome_json(
        tmp_path,
        review_event_id=review_event_id,
        recommendation_id=rec_id,
    )

    rc, _out, err = _run_review_record(missing_db, base_dir, outcome_json)
    assert rc == exit_codes.OK, err
    assert "state DB not found" in err

    outcome = json.loads((
        base_dir / "review_outcomes.jsonl"
    ).read_text(encoding="utf-8").splitlines()[0])
    assert outcome["recommendation_id"] == rec_id
    assert outcome["re_linked_from_recommendation_id"] is None
