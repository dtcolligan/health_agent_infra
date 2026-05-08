"""v0.1.14.1 W-GARMIN-MANIFEST-SIGNAL — runtime breadcrumb.

Contract: when ``_resolve_pull_source`` resolves to ``garmin_live``,
emit a single stderr line warning that Garmin live is unreliable. The
warning catches programmatic callers who never read the capabilities
manifest and never see the help text.

Pinned:

  1. ``--source garmin_live`` and the legacy ``--live`` flag both
     trigger the warning.
  2. ``--source intervals_icu`` and ``--source csv`` do NOT trigger
     the warning.
  3. The warning fires exactly once per resolution call.
  4. The warning text references intervals.icu as the alternative and
     points at the capabilities manifest's structured signal.
"""

from __future__ import annotations

import argparse

import pytest

from health_agent_infra.cli import _resolve_pull_source, _GARMIN_LIVE_WARNING


def _resolve_with_capture(args_namespace: argparse.Namespace, capsys: pytest.CaptureFixture[str]) -> tuple[str, str]:
    capsys.readouterr()  # drain anything prior
    resolved = _resolve_pull_source(args_namespace)
    captured = capsys.readouterr()
    return resolved, captured.err


def test_garmin_live_via_source_emits_warning(capsys):
    args = argparse.Namespace(source="garmin_live", live=False)
    resolved, stderr = _resolve_with_capture(args, capsys)
    assert resolved == "garmin_live"
    assert _GARMIN_LIVE_WARNING in stderr


def test_garmin_live_via_legacy_flag_emits_warning(capsys):
    args = argparse.Namespace(source=None, live=True)
    resolved, stderr = _resolve_with_capture(args, capsys)
    assert resolved == "garmin_live"
    assert _GARMIN_LIVE_WARNING in stderr


def test_intervals_icu_does_not_emit_warning(capsys):
    args = argparse.Namespace(source="intervals_icu", live=False)
    resolved, stderr = _resolve_with_capture(args, capsys)
    assert resolved == "intervals_icu"
    assert stderr == ""


def test_csv_does_not_emit_warning(capsys):
    args = argparse.Namespace(source="csv", live=False)
    resolved, stderr = _resolve_with_capture(args, capsys)
    assert resolved == "csv"
    assert stderr == ""


def test_warning_fires_exactly_once(capsys):
    args = argparse.Namespace(source="garmin_live", live=False)
    _, stderr = _resolve_with_capture(args, capsys)
    # Count occurrences of the leading "WARN [hai pull]" prefix to make
    # this insensitive to any formatting drift in the body.
    assert stderr.count("WARN [hai pull]") == 1


def test_warning_text_points_at_alternatives():
    """The warning string itself should mention intervals.icu and the
    capabilities manifest — these are the two surfaces an agent should
    consult next."""

    assert "intervals.icu" in _GARMIN_LIVE_WARNING
    assert "capabilities" in _GARMIN_LIVE_WARNING
    assert "AGENTS.md" in _GARMIN_LIVE_WARNING
