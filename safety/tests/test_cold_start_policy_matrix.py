"""W24 — pin the per-domain cold-start decisions documented in
``reporting/docs/cold_start_policy_matrix.md``.

The matrix preserves an intentional asymmetry:

  - Running, strength, stress: have ``cold_start_relaxation`` rules
    that allow non-defer recommendations during the first 14 days.
  - Recovery, sleep, nutrition: do NOT relax — their `insufficient`
    coverage means missing headline evidence; the right response is
    `intake_required`, not relaxation.

If a future change adds a relaxation hook to a "no" domain (or
removes one from a "yes" domain), this test fails and forces a
matrix update.
"""

from __future__ import annotations

import inspect

import pytest


# ---------------------------------------------------------------------------
# "Yes" — domains that DO have a cold-start relaxation hook
# ---------------------------------------------------------------------------

def test_running_policy_accepts_cold_start_context():
    """Running should accept cold_start_context in its policy
    evaluator and have a relaxation helper."""

    from health_agent_infra.domains.running import policy as running_policy
    sig = inspect.signature(running_policy.evaluate_running_policy)
    assert "cold_start_context" in sig.parameters
    assert hasattr(running_policy, "_running_cold_start_relax"), (
        "running policy should expose a cold-start relaxation helper"
    )


def test_strength_policy_accepts_cold_start_context():
    from health_agent_infra.domains.strength import policy as strength_policy
    sig = inspect.signature(strength_policy.evaluate_strength_policy)
    assert "cold_start_context" in sig.parameters
    assert hasattr(strength_policy, "_strength_cold_start_relax")


def test_stress_policy_accepts_cold_start_context():
    from health_agent_infra.domains.stress import policy as stress_policy
    sig = inspect.signature(stress_policy.evaluate_stress_policy)
    assert "cold_start_context" in sig.parameters
    assert hasattr(stress_policy, "_stress_cold_start_relax")


# ---------------------------------------------------------------------------
# "No" — domains that intentionally DO NOT have a cold-start relaxation
# ---------------------------------------------------------------------------

def test_recovery_policy_does_not_accept_cold_start_context():
    """Recovery's `insufficient` coverage means missing sleep_hours OR
    soreness self-report — the right response is intake_required, not
    relaxation. If a future change adds a cold_start_context parameter,
    this test fails so the matrix doc + the asymmetry rationale can be
    revisited intentionally."""

    from health_agent_infra.domains.recovery import policy as recovery_policy
    # Recovery's classify is the entry point for the policy gate;
    # the per-domain policy decision shape doesn't take a relaxation
    # context. If this changes, it's an intentional asymmetry shift.
    candidates = [
        attr for attr in dir(recovery_policy)
        if "cold_start" in attr.lower() and not attr.startswith("_")
    ]
    assert candidates == [], (
        f"recovery policy should not expose cold-start relaxation; "
        f"found: {candidates}. Update cold_start_policy_matrix.md "
        f"if this asymmetry is being deliberately changed."
    )


def test_sleep_policy_does_not_accept_cold_start_context():
    from health_agent_infra.domains.sleep import policy as sleep_policy
    candidates = [
        attr for attr in dir(sleep_policy)
        if "cold_start" in attr.lower() and not attr.startswith("_")
    ]
    assert candidates == [], (
        f"sleep policy should not expose cold-start relaxation; "
        f"found: {candidates}. Update cold_start_policy_matrix.md "
        f"if this asymmetry is being deliberately changed."
    )


def test_nutrition_policy_does_not_accept_cold_start_context():
    from health_agent_infra.domains.nutrition import policy as nutrition_policy
    candidates = [
        attr for attr in dir(nutrition_policy)
        if "cold_start" in attr.lower() and not attr.startswith("_")
    ]
    assert candidates == [], (
        f"nutrition policy should not expose cold-start relaxation; "
        f"found: {candidates}. Nutrition non-relaxation is also "
        f"covered by test_nutrition_cold_start_non_relaxation.py."
    )


# ---------------------------------------------------------------------------
# Matrix doc exists + names every domain
# ---------------------------------------------------------------------------

def test_matrix_doc_exists_and_covers_all_six_domains():
    from pathlib import Path
    matrix_path = (
        Path(__file__).resolve().parents[2]
        / "reporting" / "docs" / "cold_start_policy_matrix.md"
    )
    assert matrix_path.exists(), (
        "v0.1.7 W24: cold_start_policy_matrix.md must exist"
    )
    text = matrix_path.read_text(encoding="utf-8")
    for domain in ("recovery", "running", "sleep", "stress", "strength",
                   "nutrition"):
        assert domain in text.lower(), (
            f"matrix doc missing per-domain rationale for {domain}"
        )
