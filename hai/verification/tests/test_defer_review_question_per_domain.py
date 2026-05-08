"""D3 test #8 — per-domain defer review_question templates.

Regression for the 2026-04-23 bug where every defer rec's
``review_question`` was the recovery-flavoured
``"Did you decide on a session yesterday? How did it go?"`` — leaking
session-language into nutrition, stress, sleep, and every other
non-recovery domain's defer.

Two-layer check:

1. **Unit.** ``_default_review_question("defer_decision_insufficient_signal", "<domain>")``
   returns the domain-specific template from
   ``core.narration.templates.DEFER_REVIEW_QUESTION_TEMPLATES``.
2. **Integration.** Building a recommendation from a defer proposal via
   ``_proposal_to_recommendation`` lands the domain-specific question
   on the ``follow_up`` block — what actually gets persisted on the
   canonical recommendation the agent later reads.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from health_agent_infra.core.narration.templates import (
    DEFER_REVIEW_QUESTION_TEMPLATES,
    DOMAIN_ORDER,
)
from health_agent_infra.core.synthesis import (
    _default_review_question,
    _mechanical_draft,
)


NOW = datetime(2026, 4, 24, 7, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("domain", DOMAIN_ORDER)
def test_default_review_question_uses_per_domain_defer_template(domain: str):
    """Each of the six canonical domains resolves its own defer template."""

    assert domain in DEFER_REVIEW_QUESTION_TEMPLATES, (
        f"domain {domain!r} missing from DEFER_REVIEW_QUESTION_TEMPLATES"
    )
    expected = DEFER_REVIEW_QUESTION_TEMPLATES[domain]

    actual = _default_review_question(
        "defer_decision_insufficient_signal", domain,
    )
    assert actual == expected


def test_default_review_question_non_defer_still_uses_action_map():
    """Sanity: the action-only map still wins for non-defer actions."""

    assert _default_review_question(
        "proceed_with_planned_session", "recovery",
    ) == "Did today's session feel appropriate for your recovery?"


def test_default_review_question_unknown_domain_falls_through_to_generic():
    """An unmapped domain on defer falls through — the resolver must not
    raise, and the generic fallback is loud enough to catch at review.
    """

    result = _default_review_question(
        "defer_decision_insufficient_signal", "not_a_real_domain",
    )
    # Falls through past the defer block, then past the action-only map
    # (which no longer has defer_decision_insufficient_signal after D3),
    # and hits the generic catch-all.
    assert result == "How did yesterday's plan work out?"


@pytest.mark.parametrize("domain", DOMAIN_ORDER)
def test_mechanical_draft_stamps_per_domain_defer_question(domain: str):
    """End-to-end: a defer proposal surfaces the domain's template on the
    persisted ``follow_up.review_question``.
    """

    proposal = {
        "proposal_id": f"prop_2026-04-24_u_1_{domain}_01",
        "user_id": "u_1",
        "for_date": "2026-04-24",
        "domain": domain,
        "action": "defer_decision_insufficient_signal",
        "confidence": "low",
        "rationale": ["coverage_insufficient"],
        "uncertainty": [],
        "policy_decisions": [
            {
                "rule_id": "require_min_coverage",
                "decision": "block",
                "note": "coverage=insufficient",
            },
        ],
    }

    draft = _mechanical_draft(
        proposal,
        daily_plan_id="plan_2026-04-24_u_1",
        issued_at=NOW,
        agent_version="claude_agent_v1",
    )

    assert draft["follow_up"]["review_question"] == (
        DEFER_REVIEW_QUESTION_TEMPLATES[domain]
    )
