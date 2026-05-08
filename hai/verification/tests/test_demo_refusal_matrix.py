"""W-Va: refusal matrix policy tests (per Codex F-PLAN-03).

Library-level tests against ``evaluate_demo_refusal``. The CLI
plumbs decisions to USER_INPUT exits; the matrix policy itself
lives in ``core/demo/refusal.py`` and is tested here in isolation
from argparse / subprocess overhead.
"""

from __future__ import annotations

import argparse

import pytest

from health_agent_infra.core.demo.refusal import (
    CLEANUP_ONLY_COMMANDS,
    DEMO_GATE_BYPASS,
    evaluate_demo_refusal,
)


def _ns(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


# ---------------------------------------------------------------------------
# Bypass commands (demo-system internals)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", sorted(DEMO_GATE_BYPASS))
def test_bypass_commands_always_allowed(cmd):
    decision = evaluate_demo_refusal(cmd, _ns())
    assert decision.allowed is True


@pytest.mark.parametrize("cmd", sorted(CLEANUP_ONLY_COMMANDS))
def test_cleanup_only_commands_in_bypass_set(cmd):
    # Cleanup-only is a subset of gate-bypass (they're allowed past
    # the marker too).
    assert cmd in DEMO_GATE_BYPASS


# ---------------------------------------------------------------------------
# Refused — credentials
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cmd", ["auth_garmin", "auth_intervals_icu"])
def test_auth_commands_refused_with_credentials_category(cmd):
    decision = evaluate_demo_refusal(cmd, _ns())
    assert decision.allowed is False
    assert decision.category == "credentials"


def test_init_with_auth_refused_credentials():
    decision = evaluate_demo_refusal("init", _ns(with_auth=True, with_first_pull=False))
    assert decision.allowed is False
    assert decision.category == "credentials"


def test_init_with_first_pull_refused_network():
    decision = evaluate_demo_refusal(
        "init", _ns(with_auth=False, with_first_pull=True)
    )
    assert decision.allowed is False
    assert decision.category == "network"


def test_init_plain_allowed():
    decision = evaluate_demo_refusal(
        "init", _ns(with_auth=False, with_first_pull=False)
    )
    assert decision.allowed is True


# ---------------------------------------------------------------------------
# Refused — operator/installer
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "state_init",
        "state_migrate",
        "state_reproject",
        "setup_skills",
        "config_init",
        "intent_commit",
        "intent_archive",
        "target_commit",
        "target_archive",
    ],
)
def test_operator_commands_refused(cmd):
    decision = evaluate_demo_refusal(cmd, _ns())
    assert decision.allowed is False
    assert decision.category == "operator"


# ---------------------------------------------------------------------------
# Refused — live network (pull / daily)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source",
    ["intervals_icu", "garmin_live"],
)
def test_pull_live_source_refused(source):
    decision = evaluate_demo_refusal(
        "pull", _ns(source=source, live=False)
    )
    assert decision.allowed is False
    assert decision.category == "network"


def test_pull_live_flag_refused():
    decision = evaluate_demo_refusal(
        "pull", _ns(source=None, live=True)
    )
    assert decision.allowed is False
    assert decision.category == "network"


def test_pull_csv_allowed():
    decision = evaluate_demo_refusal(
        "pull", _ns(source="csv", live=False)
    )
    assert decision.allowed is True


def test_pull_no_source_allowed():
    """No --source flag at all: argparse default is None; treat as csv (allowed)."""
    decision = evaluate_demo_refusal(
        "pull", _ns(source=None, live=False)
    )
    assert decision.allowed is True


def test_daily_with_live_source_refused():
    decision = evaluate_demo_refusal(
        "daily",
        _ns(source="intervals_icu", live=False, skip_pull=False),
    )
    assert decision.allowed is False
    assert decision.category == "network"


def test_daily_skip_pull_allowed_even_with_live_source():
    """Skip-pull never goes near the network; live source is irrelevant."""
    decision = evaluate_demo_refusal(
        "daily",
        _ns(source="intervals_icu", live=False, skip_pull=True),
    )
    assert decision.allowed is True


def test_daily_csv_allowed():
    decision = evaluate_demo_refusal(
        "daily", _ns(source="csv", live=False, skip_pull=False)
    )
    assert decision.allowed is True


# ---------------------------------------------------------------------------
# Default-allow commands
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cmd",
    [
        "today",
        "propose",
        "intake_gym",
        "intake_nutrition",
        "intake_readiness",
        "intake_stress",
        "intake_note",
        "intake_gaps",
        "intake_exercise",
        "explain",
        "state_read",
        "state_snapshot",
        "memory_set",
        "memory_list",
        "memory_archive",
        "intent_list",
        "target_list",
        "stats",
        "doctor",
        "review_record",
        "review_schedule",
        "review_summary",
        "synthesize",
        "clean",
        "config_show",
        "config_diff",
        "config_validate",
    ],
)
def test_default_allowed_commands(cmd):
    decision = evaluate_demo_refusal(cmd, _ns())
    assert decision.allowed is True
