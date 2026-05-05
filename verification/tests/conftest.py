"""Pytest bootstrap — make the installable package importable from ``src/``
and ensure the suite is hermetic with respect to the developer's local
intervals.icu credentials.

This avoids requiring ``pip install -e .`` for the test suite.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture(autouse=True)
def _disable_intervals_icu_auto_default(monkeypatch):
    """Default every test to the offline csv source.

    ``_resolve_pull_source`` in ``cli.py`` auto-selects ``intervals_icu``
    when credentials are reachable on the developer machine. That made
    eight tests (``test_intake_readiness``, ``test_intake_gaps``,
    ``test_recovery_readiness_v1``) hit the live API and 403 whenever
    the maintainer ran the suite with their real keychain populated —
    F-CDX-IR-03 from the v0.1.10 Codex implementation review.

    Forcing ``_intervals_icu_configured`` to ``False`` keeps the suite
    hermetic. Tests that exercise the resolver's auto-default path
    monkeypatch this back to ``True`` themselves.
    """

    # W-29.2.9: `_intervals_icu_configured` lives in cli.handlers.pull_clean
    # (re-exported via cli/__init__.py). Patching the source module is the
    # binding cmd_pull / _resolve_pull_source actually look up.
    monkeypatch.setattr(
        "health_agent_infra.cli.handlers.pull_clean._intervals_icu_configured",
        lambda: False,
        raising=True,
    )
    # Also patch the cli re-export so any test that imports the symbol
    # directly (`from health_agent_infra.cli import _intervals_icu_configured`)
    # observes the same False.
    monkeypatch.setattr(
        "health_agent_infra.cli._intervals_icu_configured",
        lambda: False,
        raising=True,
    )
