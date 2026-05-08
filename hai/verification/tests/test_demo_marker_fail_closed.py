"""W-Va: marker fail-closed contract (per Codex F-PLAN-03).

When a marker file exists but is invalid (corrupt JSON, missing
required field, schema-version mismatch, dead scratch root), every
CLI command must refuse with USER_INPUT *except* ``hai demo end``
and ``hai demo cleanup``.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from health_agent_infra.core.demo.session import (
    DEMO_MARKER_SCHEMA_VERSION,
    DemoMarkerError,
    get_active_marker,
    open_session,
)


def _hai(args, env_extra=None, expect_code=None):
    """Invoke `hai <args>` with HAI_DEMO_MARKER_PATH already set in env_extra."""
    import os
    env = os.environ.copy()
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "-m", "health_agent_infra.cli", *args],
        env=env,
        capture_output=True,
        text=True,
    )
    if expect_code is not None:
        assert proc.returncode == expect_code, (
            f"hai {' '.join(args)} → exit {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )
    return proc


def _write_marker(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


# ---------------------------------------------------------------------------
# Library-level fail-closed tests (faster than subprocess)
# ---------------------------------------------------------------------------


def test_corrupt_json_raises_demo_marker_error(tmp_path, monkeypatch):
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))
    _write_marker(marker_path, "{not valid json")

    with pytest.raises(DemoMarkerError):
        get_active_marker()


def test_missing_required_field_raises(tmp_path, monkeypatch):
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))
    _write_marker(
        marker_path,
        json.dumps({"schema_version": DEMO_MARKER_SCHEMA_VERSION}),
    )

    with pytest.raises(DemoMarkerError) as excinfo:
        get_active_marker()
    assert "missing required fields" in str(excinfo.value)


def test_schema_version_mismatch_raises(tmp_path, monkeypatch):
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))
    bogus = {
        "schema_version": "demo_marker.v999",
        "marker_id": "demo_x",
        "scratch_root": str(tmp_path),
        "db_path": str(tmp_path / "db"),
        "base_dir_path": str(tmp_path / "bd"),
        "config_path": str(tmp_path / "cf"),
        "started_at": "2026-04-28T00:00:00+00:00",
    }
    _write_marker(marker_path, json.dumps(bogus))

    with pytest.raises(DemoMarkerError) as excinfo:
        get_active_marker()
    assert "schema_version" in str(excinfo.value)


def test_missing_scratch_root_raises(tmp_path, monkeypatch):
    """Marker valid in shape but scratch_root path is gone."""
    marker_path = tmp_path / "marker.json"
    monkeypatch.setenv("HAI_DEMO_MARKER_PATH", str(marker_path))

    open_session(scratch_root=tmp_path / "scratch")
    shutil.rmtree(tmp_path / "scratch")

    with pytest.raises(DemoMarkerError) as excinfo:
        get_active_marker()
    assert "scratch root" in str(excinfo.value)


# ---------------------------------------------------------------------------
# CLI-level fail-closed tests (each runs `hai` as a subprocess)
# ---------------------------------------------------------------------------


def test_cli_refuses_under_corrupt_marker_except_cleanup(tmp_path):
    marker_path = tmp_path / "marker.json"
    _write_marker(marker_path, "{not valid json")

    env = {"HAI_DEMO_MARKER_PATH": str(marker_path)}

    # `hai today` must refuse with USER_INPUT (exit 1 per exit_codes.USER_INPUT).
    proc = _hai(["today"], env_extra=env)
    assert proc.returncode == 1, f"expected USER_INPUT; stderr: {proc.stderr}"
    assert "demo marker" in proc.stderr.lower() or "unreadable" in proc.stderr.lower()

    # Marker still exists — fail-closed didn't auto-delete.
    assert marker_path.exists()


def test_cli_demo_cleanup_works_under_corrupt_marker(tmp_path):
    marker_path = tmp_path / "marker.json"
    _write_marker(marker_path, "{not valid json")
    env = {"HAI_DEMO_MARKER_PATH": str(marker_path)}

    proc = _hai(["demo", "cleanup"], env_extra=env, expect_code=0)
    assert not marker_path.exists()
    payload = json.loads(proc.stdout)
    assert payload["status"] == "cleaned"
    assert "<unparseable>" in payload["removed_marker_ids"]


def test_cli_demo_end_works_under_corrupt_marker(tmp_path):
    marker_path = tmp_path / "marker.json"
    _write_marker(marker_path, "{not valid json")
    env = {"HAI_DEMO_MARKER_PATH": str(marker_path)}

    proc = _hai(["demo", "end"], env_extra=env, expect_code=0)
    # close_session removes the marker even when invalid.
    assert not marker_path.exists()
