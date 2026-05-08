"""W-Va: demo session lifecycle (open / use / end / cleanup).

Tests the marker file primitive, the resolver overrides, and the
banner emitted by ``hai`` when a session is active. Isolation
surfaces (real DB / real ~/.health_agent / real config) get their
own test file (``test_demo_isolation_surfaces.py``).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from health_agent_infra.core.demo.session import (
    DEMO_MARKER_SCHEMA_VERSION,
    DemoMarker,
    DemoMarkerError,
    cleanup_orphans,
    close_session,
    demo_marker_path,
    get_active_marker,
    is_demo_active,
    open_session,
)


# ---------------------------------------------------------------------------
# Marker-path resolution
# ---------------------------------------------------------------------------


def test_marker_path_uses_env_override(tmp_path, monkeypatch):
    explicit = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(explicit))
    assert demo_marker_path() == explicit


def test_marker_path_falls_back_to_xdg_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("HAI_DEMO_MARKER_PATH", raising=False)
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    assert demo_marker_path() == tmp_path / "hai" / "demo_session.json"


# ---------------------------------------------------------------------------
# open / close lifecycle
# ---------------------------------------------------------------------------


def test_open_session_writes_marker_and_scratch_paths(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )

    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch, persona="p1")

    # Marker file persisted with the correct schema.
    saved = json.loads((tmp_path / "marker.json").read_text())
    assert saved["schema_version"] == DEMO_MARKER_SCHEMA_VERSION
    assert saved["marker_id"] == marker.marker_id
    assert saved["scratch_root"] == str(scratch)
    assert saved["persona"] == "p1"

    # Scratch sub-paths created.
    assert scratch.exists()
    assert marker.base_dir_path.exists()
    assert marker.config_path.parent.exists()


def test_open_session_initializes_scratch_db(tmp_path, monkeypatch):
    """Codex F-IR-02 fix: hai demo start must initialise the scratch
    state.db so subsequent `hai intake *` commands don't fall back
    to JSONL-only and `hai daily` doesn't short-circuit.

    Pre-fix: open_session created the scratch_root + base_dir_path
    + config_path but NEVER ran initialize_database, leaving the
    DB file absent. The documented demo flow then failed.
    """
    import sqlite3
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )

    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch, persona=None)

    # state.db now exists (was the bug — only the path was set).
    assert marker.db_path.exists(), (
        "Codex F-IR-02 regression: demo start did not initialise "
        "the scratch state.db"
    )

    # Schema is applied — schema_migrations table is populated.
    conn = sqlite3.connect(str(marker.db_path))
    try:
        rows = conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        conn.close()
    versions = [r[0] for r in rows]
    assert versions, "no migrations applied to scratch DB"
    assert versions == sorted(versions)
    # Head should be at least migration 022 (the W-E
    # state_fingerprint column added this cycle).
    assert max(versions) >= 22


def test_open_session_refuses_when_marker_already_present(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )

    open_session(scratch_root=tmp_path / "first", persona=None)
    with pytest.raises(DemoMarkerError) as excinfo:
        open_session(scratch_root=tmp_path / "second", persona=None)
    assert "already active" in str(excinfo.value)


def test_close_session_removes_marker_and_returns_marker(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )

    opened = open_session(scratch_root=tmp_path / "scratch")
    closed = close_session()

    assert closed is not None
    assert closed.marker_id == opened.marker_id
    assert not (tmp_path / "marker.json").exists()


def test_close_session_idempotent_when_no_session(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )
    assert close_session() is None


# ---------------------------------------------------------------------------
# is_demo_active / get_active_marker
# ---------------------------------------------------------------------------


def test_is_demo_active_false_when_no_marker(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "missing.json")
    )
    assert is_demo_active() is False
    assert get_active_marker() is None


def test_is_demo_active_true_after_open(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "marker.json")
    )
    open_session(scratch_root=tmp_path / "scratch")
    assert is_demo_active() is True
    marker = get_active_marker()
    assert isinstance(marker, DemoMarker)


# ---------------------------------------------------------------------------
# cleanup_orphans
# ---------------------------------------------------------------------------


def test_cleanup_orphans_removes_corrupt_marker(tmp_path, monkeypatch):
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    marker_path.write_text("not valid json {")

    cleaned = cleanup_orphans()
    assert cleaned == ["<unparseable>"]
    assert not marker_path.exists()


def test_cleanup_orphans_removes_marker_with_missing_scratch(
    tmp_path, monkeypatch
):
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))

    open_session(scratch_root=tmp_path / "scratch")
    # Simulate scratch root deleted out from under us.
    import shutil
    shutil.rmtree(tmp_path / "scratch")

    cleaned = cleanup_orphans()
    assert len(cleaned) == 1
    assert cleaned[0].startswith("demo_")
    assert not marker_path.exists()


def test_cleanup_orphans_no_op_when_no_marker(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "HAI_DEMO_MARKER_PATH", str(tmp_path / "missing.json")
    )
    assert cleanup_orphans() == []
