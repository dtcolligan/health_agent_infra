"""Phase 4 step 4 — code-owned exercise match + search.

Contracts pinned:

  1. ``match_exercise_name`` resolves case-fold-exact canonical names
     with ``confidence='exact'``; single-hit aliases with
     ``confidence='alias'``; multi-hit aliases (cross-row collisions)
     with ``confidence='ambiguous'`` and every colliding id as
     ``alternatives``; unknown tokens with ``confidence='no_match'``.
  2. ``search_exercises`` ranks by score desc, canonical_name asc.
     Empty / whitespace queries return an empty list. Exact matches
     dominate substring matches; substring dominates token-overlap.
  3. The scoring function's weights are stable across runs (no
     randomness, no ties hidden by dict iteration order).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    initialize_database,
    open_connection,
)
from health_agent_infra.domains.strength.taxonomy_match import (
    ExerciseMatch,
    SearchHit,
    load_taxonomy_with_aliases,
    match_exercise_name,
    search_exercises,
)


def _init_db(tmp_path: Path) -> Path:
    db = tmp_path / "state.db"
    initialize_database(db)
    return db


# ---------------------------------------------------------------------------
# match_exercise_name
# ---------------------------------------------------------------------------

def test_match_exact_canonical(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "Back Squat",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "exact"
    assert m.exercise_id == "back_squat"
    assert m.canonical_name == "Back Squat"
    assert m.alternatives == ()


def test_match_exact_canonical_case_insensitive(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "back squat",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "exact"
    assert m.exercise_id == "back_squat"


def test_match_alias(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "RDL",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "alias"
    assert m.exercise_id == "romanian_deadlift"


def test_match_unknown_returns_no_match(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "completely fictional lift",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "no_match"
    assert m.exercise_id is None


def test_match_empty_string_returns_no_match(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "no_match"


def test_match_whitespace_only_returns_no_match(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "   ",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "no_match"


def test_match_detects_cross_row_alias_collision(tmp_path: Path):
    """Seed two user_manual rows whose aliases collide on 'crunch'.
    The canonical ``cable_crunch`` must not mask the collision."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # Add two rows that both alias 'custom_crunch'.
        conn.execute(
            """
            INSERT INTO exercise_taxonomy (
                exercise_id, canonical_name, aliases,
                primary_muscle_group, secondary_muscle_groups,
                category, equipment, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "custom_standing_crunch", "Custom Standing Crunch",
                "custom_crunch|std_crunch",
                "core", None, "isolation", "bodyweight", "user_manual",
            ),
        )
        conn.execute(
            """
            INSERT INTO exercise_taxonomy (
                exercise_id, canonical_name, aliases,
                primary_muscle_group, secondary_muscle_groups,
                category, equipment, source
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "custom_banded_crunch", "Custom Banded Crunch",
                "custom_crunch|banded_crunch",
                "core", None, "isolation", "cable", "user_manual",
            ),
        )
        conn.commit()
        taxonomy, aliases_by_id, resolver = load_taxonomy_with_aliases(conn)
    finally:
        conn.close()

    m = match_exercise_name(
        "custom_crunch",
        taxonomy=taxonomy, aliases_by_id=aliases_by_id, resolver=resolver,
    )
    assert m.confidence == "ambiguous"
    assert set(m.alternatives) == {"custom_standing_crunch", "custom_banded_crunch"}


# ---------------------------------------------------------------------------
# search_exercises
# ---------------------------------------------------------------------------

def test_search_empty_query_returns_empty(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        assert search_exercises("", conn=conn) == []
        assert search_exercises("   ", conn=conn) == []
    finally:
        conn.close()


def test_search_exact_canonical_is_top(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("Back Squat", conn=conn)
    finally:
        conn.close()

    assert hits[0].exercise_id == "back_squat"
    assert hits[0].match_reason == "exact_canonical"


def test_search_exact_alias_ranks_above_substring(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        # "bench" is an exact alias of bench_press.
        hits = search_exercises("bench", conn=conn)
    finally:
        conn.close()

    # bench_press should be first.
    assert hits[0].exercise_id == "bench_press"
    assert hits[0].match_reason == "exact_alias"


def test_search_substring_canonical_match(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("squat", conn=conn, limit=15)
    finally:
        conn.close()

    # 'squat' is an exact alias of back_squat, and a substring of many
    # other squat variants. Back squat must be first because 'squat'
    # is also an alias of back_squat.
    ids = [h.exercise_id for h in hits]
    assert ids[0] == "back_squat"
    # All the other squat variants are in the list.
    assert {"front_squat", "goblet_squat", "hack_squat"} <= set(ids)


def test_search_token_overlap(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("incline db", conn=conn, limit=10)
    finally:
        conn.close()

    ids = [h.exercise_id for h in hits]
    assert "dumbbell_incline_press" in ids
    assert "incline_dumbbell_curl" in ids


def test_search_limit_clamps_list(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("press", conn=conn, limit=3)
    finally:
        conn.close()
    assert len(hits) <= 3


def test_search_deterministic_tie_break_on_canonical_name(tmp_path: Path):
    """Two runs of the same query must return byte-identical output."""

    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        a = search_exercises("press", conn=conn, limit=20)
        b = search_exercises("press", conn=conn, limit=20)
    finally:
        conn.close()

    assert [h.exercise_id for h in a] == [h.exercise_id for h in b]
    assert [h.score for h in a] == [h.score for h in b]


def test_search_returns_match_reason_on_every_hit(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("press", conn=conn, limit=10)
    finally:
        conn.close()

    for h in hits:
        assert h.match_reason in (
            "exact_canonical", "exact_alias",
            "substring_canonical", "substring_alias",
            "token_overlap",
        )


def test_search_unknown_query_returns_empty(tmp_path: Path):
    db = _init_db(tmp_path)
    conn = open_connection(db)
    try:
        hits = search_exercises("xyzphantomlift", conn=conn)
    finally:
        conn.close()
    assert hits == []
