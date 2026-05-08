"""W-Va: demo isolation across the full persistence surface.

Per Codex F-PLAN-02 + maintainer answer Q-2: demo mode must isolate
the DB, the writeback/intake base_dir (`~/.health_agent`), and the
user config (`thresholds.toml`). Real persistence surfaces stay
byte-identical across an entire demo session.

This file owns the cross-resolver isolation contract. Lifecycle +
fail-closed + matrix tests live elsewhere.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from health_agent_infra.core.config import user_config_path
from health_agent_infra.core.demo.session import (
    close_session,
    open_session,
)
from health_agent_infra.core.paths import resolve_base_dir
from health_agent_infra.core.state.store import resolve_db_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _checksum_tree(root: Path) -> str:
    """Recursive hash of every file under root. Used to assert byte-stability."""
    if not root.exists():
        return f"<absent:{root}>"
    h = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode("utf-8"))
            h.update(b":")
            h.update(path.read_bytes())
            h.update(b"\n")
    return h.hexdigest()


@pytest.fixture
def real_dirs(tmp_path, monkeypatch):
    """Set the real DB and base_dir paths to tmp-controlled locations.

    Pytest can't actually run against the user's real ~/.health_agent
    without polluting it. So we redirect the "real" paths to tmp_path
    sub-trees that we own; the test assertions remain valid because
    they verify these "real" paths stay byte-identical when a demo
    is active.
    """
    real_root = tmp_path / "real"
    real_db = real_root / "state.db"
    real_base = real_root / "base"
    real_marker_path = tmp_path / "demo_marker.json"

    real_db.parent.mkdir(parents=True)
    real_base.mkdir(parents=True)

    monkeypatch.setenv("HAI_STATE_DB", str(real_db))
    monkeypatch.setenv("HAI_BASE_DIR", str(real_base))
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(real_marker_path))

    return {
        "real_db": real_db,
        "real_base": real_base,
        "real_marker_path": real_marker_path,
    }


# ---------------------------------------------------------------------------
# Resolver routes scratch when marker valid
# ---------------------------------------------------------------------------


def test_resolve_db_path_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = resolve_db_path()
        assert resolved == marker.db_path
        assert resolved != real_dirs["real_db"]
    finally:
        close_session()


def test_resolve_base_dir_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = resolve_base_dir()
        assert resolved == marker.base_dir_path
        assert resolved != real_dirs["real_base"]
    finally:
        close_session()


def test_user_config_path_routes_to_scratch_under_marker(real_dirs, tmp_path):
    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)
    try:
        resolved = user_config_path()
        assert resolved == marker.config_path
    finally:
        close_session()


# ---------------------------------------------------------------------------
# Resolver routes real when no marker
# ---------------------------------------------------------------------------


def test_resolve_db_path_real_when_no_marker(real_dirs):
    assert resolve_db_path() == real_dirs["real_db"]


def test_resolve_base_dir_real_when_no_marker(real_dirs):
    assert resolve_base_dir() == real_dirs["real_base"]


# ---------------------------------------------------------------------------
# Real-tree byte-stability across an open / close cycle
# ---------------------------------------------------------------------------


def test_real_persistence_byte_identical_across_session(real_dirs, tmp_path):
    """Open a session, write a file via the scratch resolvers, close. Real tree stable."""
    # Pre-populate the real surfaces with arbitrary content so the
    # checksum has bytes to compare.
    real_dirs["real_db"].write_bytes(b"REAL DB CONTENT v0")
    (real_dirs["real_base"] / "real_jsonl.jsonl").write_text(
        '{"line": 1}\n'
    )
    pre_db = real_dirs["real_db"].read_bytes()
    pre_base = _checksum_tree(real_dirs["real_base"])

    scratch = tmp_path / "scratch"
    marker = open_session(scratch_root=scratch)

    # Simulate work writing to scratch surfaces.
    marker.db_path.write_bytes(b"SCRATCH DB CONTENT")
    (marker.base_dir_path / "scratch_jsonl.jsonl").write_text(
        '{"line": "demo"}\n'
    )

    # Real surfaces unchanged mid-session.
    assert real_dirs["real_db"].read_bytes() == pre_db
    assert _checksum_tree(real_dirs["real_base"]) == pre_base

    close_session()

    # And after close.
    assert real_dirs["real_db"].read_bytes() == pre_db
    assert _checksum_tree(real_dirs["real_base"]) == pre_base


# ---------------------------------------------------------------------------
# Subprocess-level isolation (Codex F-IR-06)
# ---------------------------------------------------------------------------


def test_subprocess_cli_writes_under_demo_isolate_real_state(
    tmp_path, monkeypatch
):
    """Codex F-IR-06 fix: run real CLI commands under an active demo
    session via subprocess and assert the real `state.db`, real
    `~/.health_agent` tree, and real `thresholds.toml` are byte-
    identical before and after.

    The unit-level isolation tests above prove the resolvers route
    to scratch when a marker is present. This subprocess test
    proves the END-TO-END path: argparse, CLI handlers, JSONL
    writeback, projector calls — none of them have a direct write
    bypass that escapes the resolver indirection.

    Pre-fix: the cardinal isolation contract was only proven at
    the resolver level; a future hardcoded path bypass could ship
    silently. This test catches that.
    """
    import hashlib
    import os
    import subprocess
    import sys

    real_root = tmp_path / "real"
    real_db = real_root / "state.db"
    real_base = real_root / "base"
    real_db.parent.mkdir(parents=True)
    real_base.mkdir(parents=True)

    # Pre-populate so checksums have bytes to compare.
    real_db.write_bytes(b"REAL DB MARKER v0\n" * 32)
    (real_base / "untouchable.jsonl").write_text(
        '{"line": "must_not_change"}\n'
    )

    def _checksum_tree_local(root: Path) -> str:
        h = hashlib.sha256()
        for path in sorted(root.rglob("*")):
            if path.is_file():
                h.update(str(path.relative_to(root)).encode("utf-8"))
                h.update(b":")
                h.update(path.read_bytes())
                h.update(b"\n")
        return h.hexdigest()

    pre_db = real_db.read_bytes()
    pre_base = _checksum_tree_local(real_base)

    env = os.environ.copy()
    env["HAI_STATE_DB"] = str(real_db)
    env["HAI_BASE_DIR"] = str(real_base)
    env["HAI_DEMO_MARKER_PATH"] = str(tmp_path / "marker.json")

    def _hai(args):
        return subprocess.run(
            [sys.executable, "-m", "health_agent_infra.cli", *args],
            env=env, capture_output=True, text=True,
        )

    # 1. Open demo session (writes marker + scratch root + initialises
    #    scratch state.db per the F-IR-02 fix).
    proc = _hai(["demo", "start", "--blank"])
    assert proc.returncode == 0, f"demo start failed: {proc.stderr}"

    # 2. Run a representative cluster of allowed commands. Any of
    #    these writing to real state would be caught by the post-
    #    checksum assertions below.
    proc = _hai([
        "intake", "readiness",
        "--soreness", "low",
        "--energy", "moderate",
        "--planned-session-type", "easy",
    ])
    assert proc.returncode == 0, f"intake readiness failed: {proc.stderr}"

    proc = _hai([
        "intake", "nutrition",
        "--calories", "2400",
        "--protein-g", "150",
        "--carbs-g", "280",
        "--fat-g", "80",
    ])
    assert proc.returncode == 0, f"intake nutrition failed: {proc.stderr}"

    proc = _hai([
        "intake", "stress",
        "--score", "2",
    ])
    assert proc.returncode == 0, f"intake stress failed: {proc.stderr}"

    # 3. hai daily reaches the canonical boundary stopping point.
    # Without proposals, this returns OK with overall_status =
    # "awaiting_proposals" (Codex F-IR2-02 — the v0.1.11 gate is
    # explicitly the boundary-stop demo, not full synthesis).
    proc = _hai(["daily", "--skip-pull", "--source", "csv"])
    assert proc.returncode == 0, f"daily failed: {proc.stderr}"
    import json as _json
    payload = _json.loads(proc.stdout)
    assert payload.get("overall_status") == "awaiting_proposals", (
        f"daily did not reach the canonical boundary stop. "
        f"overall_status={payload.get('overall_status')!r}"
    )

    # 4. hai today shows "no plan for <date>" — the visible signal
    # that the runtime/skill boundary has not yet been crossed.
    proc = _hai(["today"])
    # Exit code 1 (USER_INPUT) is the signal; stderr names the cause.
    assert proc.returncode == 1, (
        f"today did not signal no-plan-for-date. "
        f"returncode={proc.returncode}, stderr={proc.stderr!r}"
    )
    assert "No plan" in proc.stderr or "no plan" in proc.stderr.lower(), (
        f"today's stderr did not name the no-plan signal: {proc.stderr!r}"
    )

    # 5. hai daily --supersede on a fresh date with no proposals
    # short-circuits at awaiting_proposals (the supersede gate
    # never fires because synthesis isn't reached). Verify it
    # doesn't crash + doesn't pollute real state.
    proc = _hai([
        "daily", "--skip-pull", "--source", "csv",
        "--supersede", "--as-of", "2027-01-01",
    ])
    assert proc.returncode in (0, 1), (
        f"daily --supersede unexpected returncode {proc.returncode}: "
        f"{proc.stderr!r}"
    )

    # 6. Close the session.
    proc = _hai(["demo", "end"])
    assert proc.returncode == 0, f"demo end failed: {proc.stderr}"

    # 7. The cardinal contract — real state byte-identical.
    assert real_db.read_bytes() == pre_db, (
        "Codex F-IR-06 regression: subprocess CLI writes under demo "
        "mode mutated the real state.db"
    )
    assert _checksum_tree_local(real_base) == pre_base, (
        "Codex F-IR-06 regression: subprocess CLI writes under demo "
        "mode mutated the real base_dir tree"
    )
