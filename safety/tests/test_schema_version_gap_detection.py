"""Regression test for v0.1.6 W20 / Codex C7: schema-version gap
detection.

Background: ``current_schema_version`` returns ``MAX(version)`` from
``schema_migrations``, which can hide gaps. A DB that's been
manually edited or partially restored can look "current" while
missing schema objects from skipped lower versions.

After v0.1.6:
  - ``applied_schema_versions(conn)`` returns the SET of applied
    versions (not just the max).
  - ``detect_schema_version_gaps(conn)`` returns any versions in
    ``[1..head]`` that are NOT applied.
  - ``hai doctor`` surfaces gaps as a warn with a clear hint, ahead
    of the legacy "pending migrations" check.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from health_agent_infra.core.state import (
    applied_schema_versions,
    current_schema_version,
    detect_schema_version_gaps,
    initialize_database,
    open_connection,
)


@pytest.fixture
def db(tmp_path: Path):
    db_path = tmp_path / "state.db"
    initialize_database(db_path)
    conn = open_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def test_detect_no_gaps_in_clean_init(db):
    """A freshly-initialised DB has every version applied — no gaps."""

    head = current_schema_version(db)
    applied = applied_schema_versions(db)
    assert applied == set(range(1, head + 1))
    assert detect_schema_version_gaps(db) == []


def test_detect_gap_when_lower_migration_missing(db):
    """If a lower migration row is removed (simulating manual edit /
    partial restore), gap detection surfaces it even though
    current_schema_version still reports the max."""

    # Remove migration 5 to simulate a gap.
    db.execute("DELETE FROM schema_migrations WHERE version = 5")
    db.commit()

    head = current_schema_version(db)
    assert head > 5  # the max is unchanged

    gaps = detect_schema_version_gaps(db)
    assert gaps == [5]


def test_detect_multiple_gaps(db):
    db.execute("DELETE FROM schema_migrations WHERE version IN (3, 7, 11)")
    db.commit()

    gaps = detect_schema_version_gaps(db)
    assert gaps == [3, 7, 11]


def test_empty_migrations_table_yields_no_gaps(db):
    """If no migrations are applied at all, there's no head to compare
    against — return empty (the caller's "is the DB initialized?" check
    handles this case separately)."""

    db.execute("DELETE FROM schema_migrations")
    db.commit()

    assert applied_schema_versions(db) == set()
    assert detect_schema_version_gaps(db) == []


def test_doctor_surfaces_gap_as_warn(tmp_path):
    """Integration: hai doctor's state_db check returns status=warn
    with applied_gaps populated when the DB has gaps."""

    from health_agent_infra.core.doctor.checks import check_state_db

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        conn.execute("DELETE FROM schema_migrations WHERE version = 8")
        conn.commit()
    finally:
        conn.close()

    result = check_state_db(db_path)
    assert result["status"] == "warn"
    assert result["applied_gaps"] == [8]
    assert "missing schema objects" in result["hint"]


# ---------------------------------------------------------------------------
# v0.1.7 W23: hai state migrate refuses gappy DBs; apply_pending_migrations
# strict mode raises SchemaVersionGapError.
# ---------------------------------------------------------------------------

def test_cmd_state_migrate_refuses_gappy_db(tmp_path):
    """Regression for v0.1.7 W23: hai state migrate must refuse a DB
    with gaps in the applied set, naming the missing versions."""

    from contextlib import redirect_stderr
    from io import StringIO
    from health_agent_infra.cli import main as cli_main
    from health_agent_infra.core import exit_codes

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        conn.execute("DELETE FROM schema_migrations WHERE version IN (4, 9)")
        conn.commit()
    finally:
        conn.close()

    err_buf = StringIO()
    with redirect_stderr(err_buf):
        rc = cli_main(["state", "migrate", "--db-path", str(db_path)])
    assert rc == exit_codes.USER_INPUT
    stderr = err_buf.getvalue()
    assert "gaps" in stderr
    assert "4" in stderr and "9" in stderr
    assert "MAX(version)" in stderr or "looks current" in stderr


def test_apply_pending_migrations_strict_raises_on_gaps(tmp_path):
    """Lower-level guard: apply_pending_migrations(strict=True) raises
    SchemaVersionGapError when the applied set has gaps. Default
    behaviour (strict=False) preserves legacy max-version skip logic."""

    from health_agent_infra.core.state import (
        SchemaVersionGapError,
        apply_pending_migrations,
    )
    import pytest as _pytest

    db_path = tmp_path / "state.db"
    initialize_database(db_path)

    conn = open_connection(db_path)
    try:
        conn.execute("DELETE FROM schema_migrations WHERE version = 7")
        conn.commit()

        with _pytest.raises(SchemaVersionGapError) as exc_info:
            apply_pending_migrations(conn, strict=True)
        assert "[7]" in str(exc_info.value)

        # Legacy default still no-ops silently — back-compat preserved.
        applied = apply_pending_migrations(conn)
        assert applied == []
    finally:
        conn.close()
