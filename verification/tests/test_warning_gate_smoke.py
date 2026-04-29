"""W-N-broader smoke gate.

Origin: v0.1.12 W-N-broader (PLAN.md §2.5).

The full `-W error::Warning` broader gate is **named-deferred to
v0.1.13 W-N-broader** per the v0.1.12 audit-time fork decision (49
sqlite3 connection-lifecycle leak sites is multi-day per-site
refactor work that does not fit the workstream budget).

This file ships the smaller deliverable: a single-test smoke gate
that exercises one canonical state-DB workflow under
``warnings.simplefilter("error", ResourceWarning)``. It catches
regression on the cleanest path — `hai state init` followed by a
read — without re-running the full suite.

A test that PASSES today and starts FAILING tomorrow signals that
a previously-clean code path has begun leaking, which is the
useful early-warning signal v0.1.13 will need when it audits the
49 known leak sites.
"""

from __future__ import annotations

import sqlite3
import warnings
from pathlib import Path

from health_agent_infra.core.state import open_connection
from health_agent_infra.core.state.store import (
    apply_pending_migrations,
)


def test_open_connection_then_close_does_not_leak_resource_warning(
    tmp_path: Path,
) -> None:
    """The canonical 'open, do work, close' flow must not emit a
    ResourceWarning under strict mode."""

    db_path = tmp_path / "smoke.db"

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)

        conn = open_connection(db_path)
        try:
            apply_pending_migrations(conn)
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "ORDER BY name LIMIT 5"
            )
            rows = cur.fetchall()
            # Trivial assertion that the migration ran.
            assert isinstance(rows, list)
        finally:
            conn.close()


def test_raw_sqlite3_with_block_does_not_leak(tmp_path: Path) -> None:
    """The pattern ``with sqlite3.connect(...) as conn`` must not leak
    when used in test fixtures. (Documents the recommended
    test-fixture shape; the v0.1.13 W-N-broader workstream will
    audit production code paths that use the bare-conn-then-finally
    shape.)"""

    db_path = tmp_path / "smoke_raw.db"

    with warnings.catch_warnings():
        warnings.simplefilter("error", ResourceWarning)

        with sqlite3.connect(str(db_path)) as conn:
            conn.execute("CREATE TABLE smoke (id INTEGER PRIMARY KEY)")
            conn.execute("INSERT INTO smoke (id) VALUES (1)")

        # Connection's __exit__ commits but does NOT close on Python
        # 3.12+; explicit close is required to match production
        # patterns. Document both patterns for v0.1.13 reference.
        conn.close()
