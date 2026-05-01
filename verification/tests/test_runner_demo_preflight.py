"""F-IR-03: persona-runner pre-flight refuses on active demo markers.

v0.1.14 IR round 1 found that the original implementation only
refused on orphan markers, missing the high-risk valid-marker case
(scratch root still exists; cleanup_orphans leaves it alone). The
runner must refuse on any active marker.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from health_agent_infra.core.demo.session import (
    close_session,
    open_session,
)

# Add repo root to sys.path so `verification.dogfood.runner` is importable.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def test_preflight_refuses_on_valid_active_marker(tmp_path, monkeypatch):
    """A valid (non-orphan) active marker MUST cause refuse."""

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    # Open a session with an explicit scratch_root in tmp_path so we
    # don't pollute /tmp on the host. open_session writes the marker
    # AND creates the scratch root; cleanup_orphans will see this as
    # a *valid* marker (scratch root exists) and leave it alone.
    scratch = tmp_path / "scratch"
    open_session(scratch_root=scratch, persona=None)
    try:
        from verification.dogfood.runner import _preflight_demo_session_check

        with pytest.raises(SystemExit) as exc:
            _preflight_demo_session_check()
        assert exc.value.code == 2
    finally:
        close_session()


def test_preflight_passes_when_no_marker(tmp_path, monkeypatch):
    """No active marker, no orphan → preflight returns silently."""

    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))

    from verification.dogfood.runner import _preflight_demo_session_check

    # No session opened — should return without raising.
    _preflight_demo_session_check()
