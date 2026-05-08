"""v0.1.9 B3 — strict text-shape validation on proposal + recommendation.

Pre-v0.1.9 the validators only checked field *presence*; Codex 2026-04-26
confirmed that string values for ``rationale`` and ``uncertainty``
passed today, leaving the audit text shape vulnerable to skill drift.
This file pins the new strict shape-check invariants and asserts that
both validators (proposal-time + recommendation-time) reject identical
malformed payloads.

Invariant ids:
  - ``rationale_list_of_strings`` — list (may be empty); items all str
  - ``uncertainty_list_of_strings`` — list (may be empty); items all str
  - ``policy_decision_shape`` — list of dicts with str rule_id, decision,
    and (optional) str note
  - ``review_question_string`` — recommendation only; non-empty str
"""

from __future__ import annotations

import pytest

from health_agent_infra.core.validate import (
    RecommendationValidationError,
    validate_recommendation_dict,
)
from health_agent_infra.core.writeback.proposal import (
    PROPOSAL_SCHEMA_VERSIONS,
    ProposalValidationError,
    validate_proposal_dict,
)


FOR_DATE = "2026-04-26"
USER = "u_shape"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _clean_proposal(domain: str = "recovery", **overrides) -> dict:
    base = {
        "schema_version": PROPOSAL_SCHEMA_VERSIONS[domain],
        "proposal_id": f"prop_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "for_date": FOR_DATE,
        "domain": domain,
        "action": "proceed_with_planned_session" if domain == "recovery" else "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["clean baseline"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "clean"},
        ],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _clean_recommendation(domain: str = "recovery", **overrides) -> dict:
    base = {
        "schema_version": "training_recommendation.v1" if domain == "recovery" else f"{domain}_recommendation.v1",
        "recommendation_id": f"rec_{FOR_DATE}_{USER}_{domain}_01",
        "user_id": USER,
        "issued_at": "2026-04-26T08:00:00+00:00",
        "for_date": FOR_DATE,
        "domain": domain,
        "action": "proceed_with_planned_session" if domain == "recovery" else "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["clean baseline"],
        "confidence": "high",
        "uncertainty": [],
        "follow_up": {
            "review_at": "2026-04-27T07:00:00+00:00",
            "review_question": "How did the session feel?",
            "review_event_id": "rev_001",
        },
        "policy_decisions": [
            {"rule_id": "r1", "decision": "allow", "note": "clean"},
        ],
        "bounded": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# rationale_list_of_strings
# ---------------------------------------------------------------------------


def test_proposal_rejects_string_rationale():
    """Pre-v0.1.9: a string rationale passed silently. v0.1.9 rejects."""

    bad = _clean_proposal(rationale="this is a string, not a list")
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "rationale_list_of_strings"


def test_proposal_rejects_non_string_rationale_items():
    bad = _clean_proposal(rationale=["valid line", 42, "another valid line"])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "rationale_list_of_strings"


def test_recommendation_rejects_string_rationale():
    bad = _clean_recommendation(rationale="this is a string")
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "rationale_list_of_strings"


def test_recommendation_rejects_non_string_rationale_items():
    bad = _clean_recommendation(rationale=["clean", {"nested": "dict"}])
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "rationale_list_of_strings"


def test_empty_rationale_list_is_accepted():
    """Empty rationale is legitimate (defer-only proposals, eval
    fixtures). Type safety is the contract; non-empty is a UX standard
    enforced in skill prose, not in the validator."""

    proposal = _clean_proposal(rationale=[])
    validate_proposal_dict(proposal)  # no raise

    rec = _clean_recommendation(rationale=[])
    validate_recommendation_dict(rec)  # no raise


# ---------------------------------------------------------------------------
# uncertainty_list_of_strings
# ---------------------------------------------------------------------------


def test_proposal_rejects_string_uncertainty():
    bad = _clean_proposal(uncertainty="raw string token")
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "uncertainty_list_of_strings"


def test_proposal_rejects_non_string_uncertainty_items():
    bad = _clean_proposal(uncertainty=["ok", 1, "ok2"])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "uncertainty_list_of_strings"


def test_recommendation_rejects_string_uncertainty():
    bad = _clean_recommendation(uncertainty="solo string")
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "uncertainty_list_of_strings"


# ---------------------------------------------------------------------------
# policy_decision_shape
# ---------------------------------------------------------------------------


def test_proposal_rejects_policy_decision_with_non_string_rule_id():
    bad = _clean_proposal(policy_decisions=[
        {"rule_id": 1, "decision": "allow"},
    ])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_proposal_rejects_policy_decision_missing_decision():
    bad = _clean_proposal(policy_decisions=[
        {"rule_id": "r1"},
    ])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_proposal_rejects_policy_decision_with_non_string_note():
    bad = _clean_proposal(policy_decisions=[
        {"rule_id": "r1", "decision": "allow", "note": 42},
    ])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_proposal_rejects_policy_decision_with_null_note():
    bad = _clean_proposal(policy_decisions=[
        {"rule_id": "r1", "decision": "allow", "note": None},
    ])
    with pytest.raises(ProposalValidationError) as exc_info:
        validate_proposal_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_recommendation_rejects_policy_decision_with_non_dict_entry():
    bad = _clean_recommendation(policy_decisions=["this is a string, not a dict"])
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_recommendation_rejects_policy_decision_with_null_note():
    bad = _clean_recommendation(policy_decisions=[
        {"rule_id": "r1", "decision": "allow", "note": None},
    ])
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "policy_decision_shape"


def test_policy_decision_with_no_note_is_accepted():
    """``note`` is optional. Decision without a note still passes."""

    proposal = _clean_proposal(policy_decisions=[
        {"rule_id": "r1", "decision": "allow"},
    ])
    validate_proposal_dict(proposal)  # no raise


# ---------------------------------------------------------------------------
# review_question_string (recommendation-only)
# ---------------------------------------------------------------------------


def test_recommendation_rejects_non_string_review_question():
    bad = _clean_recommendation()
    bad["follow_up"]["review_question"] = 42
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "review_question_string"


def test_recommendation_rejects_empty_review_question():
    bad = _clean_recommendation()
    bad["follow_up"]["review_question"] = "   "
    with pytest.raises(RecommendationValidationError) as exc_info:
        validate_recommendation_dict(bad)
    assert exc_info.value.invariant == "review_question_string"


# ---------------------------------------------------------------------------
# Both validators reject the same malformed payload (lockstep proof)
# ---------------------------------------------------------------------------


def test_both_validators_reject_string_rationale_with_same_invariant():
    """Lockstep proof: a malformed rationale fails both validators with
    the SAME invariant id, confirming the shared shape-check helper."""

    bad_p = _clean_proposal(rationale="raw string")
    bad_r = _clean_recommendation(rationale="raw string")

    with pytest.raises(ProposalValidationError) as p_exc:
        validate_proposal_dict(bad_p)
    with pytest.raises(RecommendationValidationError) as r_exc:
        validate_recommendation_dict(bad_r)

    assert p_exc.value.invariant == r_exc.value.invariant == "rationale_list_of_strings"


def test_both_validators_reject_string_uncertainty_with_same_invariant():
    bad_p = _clean_proposal(uncertainty="raw string")
    bad_r = _clean_recommendation(uncertainty="raw string")

    with pytest.raises(ProposalValidationError) as p_exc:
        validate_proposal_dict(bad_p)
    with pytest.raises(RecommendationValidationError) as r_exc:
        validate_recommendation_dict(bad_r)

    assert p_exc.value.invariant == r_exc.value.invariant == "uncertainty_list_of_strings"


def test_both_validators_share_banned_token_coverage():
    """Lockstep proof for the refactored banned-token sweep: a banned
    token in rationale fails both validators."""

    bad_p = _clean_proposal(rationale=["user has a sleep disorder"])
    bad_r = _clean_recommendation(rationale=["user has a sleep disorder"])

    with pytest.raises(ProposalValidationError) as p_exc:
        validate_proposal_dict(bad_p)
    with pytest.raises(RecommendationValidationError) as r_exc:
        validate_recommendation_dict(bad_r)

    assert p_exc.value.invariant == r_exc.value.invariant == "no_banned_tokens"
