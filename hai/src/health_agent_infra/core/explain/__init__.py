"""Read-only explainability surface over the persisted audit chain.

Phase C of the post-v0.1.0 roadmap. Exposes
``proposal_log → x_rule_firing → recommendation_log → review_*`` as a
single bundle keyed on either ``daily_plan_id`` or
``(for_date, user_id)``. Strictly read-only — nothing in this package
opens a write transaction.
"""

from health_agent_infra.core.explain.queries import (
    ExplainBundle,
    ExplainNotFoundError,
    ExplainPlan,
    ExplainProposal,
    ExplainRecommendation,
    ExplainReview,
    ExplainReviewOutcome,
    ExplainUserMemory,
    ExplainXRuleFiring,
    load_bundle_by_daily_plan_id,
    load_bundle_chain_for_date,
    load_bundle_for_date,
)
from health_agent_infra.core.explain.render import (
    bundle_to_dict,
    render_bundle_text,
)

__all__ = [
    "ExplainBundle",
    "ExplainNotFoundError",
    "ExplainPlan",
    "ExplainProposal",
    "ExplainRecommendation",
    "ExplainReview",
    "ExplainReviewOutcome",
    "ExplainUserMemory",
    "ExplainXRuleFiring",
    "bundle_to_dict",
    "load_bundle_by_daily_plan_id",
    "load_bundle_chain_for_date",
    "load_bundle_for_date",
    "render_bundle_text",
]
