"""Serialize an :class:`ExplainBundle` to JSON or human-readable text.

Two outputs, one bundle:

- :func:`bundle_to_dict` returns a JSON-ready dict whose key names are
  stable across phases. Agents can consume it programmatically.
- :func:`render_bundle_text` returns a plain-text block with one section
  per audit layer (plan header → proposals → firings → recommendations
  → reviews). Suitable for ``hai explain`` operator output.

Neither function reads from SQLite or recomputes anything — they are
pure functions of the bundle.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from health_agent_infra.core.explain.queries import (
    ExplainBundle,
    ExplainPlan,
    ExplainProposal,
    ExplainRecommendation,
    ExplainReview,
    ExplainUserMemory,
    ExplainXRuleFiring,
)


# ---------------------------------------------------------------------------
# JSON
# ---------------------------------------------------------------------------


def bundle_to_dict(bundle: ExplainBundle) -> dict[str, Any]:
    """Return a JSON-ready dict view of the bundle.

    Field names mirror the dataclass attributes so a caller can rely on
    the same shape across phases. Empty lists / dicts are emitted
    explicitly rather than omitted, so consumers can treat absence as
    "the runtime did not write that" rather than "the explain surface
    forgot to render it."
    """

    return {
        "plan": _plan_to_dict(bundle.plan),
        "proposals": [_proposal_to_dict(p) for p in bundle.proposals],
        "x_rule_firings": {
            "phase_a": [_firing_to_dict(f) for f in bundle.phase_a_firings],
            "phase_b": [_firing_to_dict(f) for f in bundle.phase_b_firings],
        },
        "recommendations": [
            _recommendation_to_dict(r) for r in bundle.recommendations
        ],
        "reviews": [_review_to_dict(r) for r in bundle.reviews],
        "user_memory": _user_memory_to_dict(bundle.user_memory),
    }


def _plan_to_dict(plan: ExplainPlan) -> dict[str, Any]:
    return {
        "daily_plan_id": plan.daily_plan_id,
        "user_id": plan.user_id,
        "for_date": plan.for_date,
        "synthesized_at": plan.synthesized_at,
        "agent_version": plan.agent_version,
        "supersedes": plan.supersedes,
        "superseded_by": plan.superseded_by,
        "x_rules_fired": list(plan.x_rules_fired),
        "synthesis_meta": dict(plan.synthesis_meta),
    }


def _proposal_to_dict(proposal: ExplainProposal) -> dict[str, Any]:
    return asdict(proposal)


def _firing_to_dict(firing: ExplainXRuleFiring) -> dict[str, Any]:
    return asdict(firing)


def _recommendation_to_dict(rec: ExplainRecommendation) -> dict[str, Any]:
    return asdict(rec)


def _review_to_dict(review: ExplainReview) -> dict[str, Any]:
    return {
        "review_event_id": review.review_event_id,
        "recommendation_id": review.recommendation_id,
        "domain": review.domain,
        "review_at": review.review_at,
        "review_question": review.review_question,
        "outcomes": [asdict(o) for o in review.outcomes],
    }


def _user_memory_to_dict(memory: ExplainUserMemory) -> dict[str, Any]:
    return {
        "as_of": memory.as_of,
        "counts": dict(memory.counts),
        "entries": [dict(entry) for entry in memory.entries],
    }


# ---------------------------------------------------------------------------
# Text
# ---------------------------------------------------------------------------


def render_bundle_text(bundle: ExplainBundle) -> str:
    """Render the bundle as a plain-text operator report.

    Sections appear in the order the audit chain runs: plan header →
    proposals → Phase A firings → Phase B firings → recommendations →
    reviews. Empty sections are still printed with an explicit "(none
    recorded)" marker so the reader can tell "no proposals were
    written" apart from "the explain surface dropped them."
    """

    plan = bundle.plan
    lines: list[str] = []
    lines.append(f"daily_plan_id : {plan.daily_plan_id}")
    lines.append(f"user_id       : {plan.user_id}")
    lines.append(f"for_date      : {plan.for_date}")
    lines.append(f"synthesized_at: {plan.synthesized_at}")
    if plan.agent_version:
        lines.append(f"agent_version : {plan.agent_version}")
    if plan.supersedes:
        lines.append(f"supersedes    : {plan.supersedes}")
    if plan.superseded_by:
        lines.append(f"superseded_by : {plan.superseded_by}")
    if plan.x_rules_fired:
        lines.append(f"x_rules_fired : {', '.join(plan.x_rules_fired)}")
    else:
        lines.append("x_rules_fired : (none)")
    lines.append("")

    lines.append(_section("Proposals", bundle.proposals, _format_proposal))
    lines.append("")
    lines.append(
        _section(
            "Phase A X-rule firings (pre-skill)",
            bundle.phase_a_firings,
            _format_firing,
        )
    )
    lines.append("")
    lines.append(
        _section(
            "Phase B X-rule firings (post-skill, action_detail only)",
            bundle.phase_b_firings,
            _format_firing,
        )
    )
    lines.append("")
    lines.append(
        _section(
            "Final recommendations",
            bundle.recommendations,
            _format_recommendation,
        )
    )
    lines.append("")
    lines.append(_section("Reviews", bundle.reviews, _format_review))
    lines.append("")
    lines.append(_format_user_memory_section(bundle.user_memory))

    return "\n".join(lines).rstrip() + "\n"


def _section(title: str, items: list, formatter) -> str:
    header = f"## {title}"
    if not items:
        return f"{header}\n  (none recorded)"
    body = "\n".join(formatter(item) for item in items)
    return f"{header}\n{body}"


def _format_proposal(p: ExplainProposal) -> str:
    parts = [
        f"- [{p.domain}] {p.proposal_id}",
        f"    action     : {p.action}",
        f"    confidence : {p.confidence}",
    ]
    if p.action_detail not in (None, {}, []):
        parts.append(f"    action_detail: {_compact_json(p.action_detail)}")
    if p.rationale:
        parts.append(f"    rationale  : {_format_list(p.rationale)}")
    if p.uncertainty:
        parts.append(f"    uncertainty: {_format_list(p.uncertainty)}")
    if p.policy_decisions:
        parts.append(
            f"    policy_decisions: {_compact_json(p.policy_decisions)}"
        )
    return "\n".join(parts)


def _format_firing(f: ExplainXRuleFiring) -> str:
    header = (
        f"- {f.rule_id} [{f.public_name}] ({f.tier}) → {f.affected_domain}"
        if f.public_name
        else f"- {f.rule_id} ({f.tier}) → {f.affected_domain}"
    )
    if f.orphan:
        header += "  [orphan]"
    parts = [
        header,
        f"    trigger    : {f.trigger_note}",
    ]
    if f.mutation not in (None, {}, []):
        parts.append(f"    mutation   : {_compact_json(f.mutation)}")
    if f.source_signals:
        parts.append(f"    signals    : {_compact_json(f.source_signals)}")
    parts.append(f"    fired_at   : {f.fired_at}")
    return "\n".join(parts)


def _format_recommendation(r: ExplainRecommendation) -> str:
    parts = [
        f"- [{r.domain}] {r.recommendation_id}",
        f"    action     : {r.action}",
        f"    confidence : {r.confidence}",
    ]
    if r.action_detail not in (None, {}, []):
        parts.append(f"    action_detail: {_compact_json(r.action_detail)}")
    if r.rationale:
        parts.append(f"    rationale  : {_format_list(r.rationale)}")
    if r.uncertainty:
        parts.append(f"    uncertainty: {_format_list(r.uncertainty)}")
    if r.review_event_id:
        parts.append(f"    review_event_id: {r.review_event_id}")
    if r.review_question:
        parts.append(f"    review_question: {r.review_question}")
    if r.supersedes:
        parts.append(f"    supersedes : {r.supersedes}")
    if r.superseded_by:
        parts.append(f"    superseded_by: {r.superseded_by}")
    return "\n".join(parts)


def _format_review(rv: ExplainReview) -> str:
    parts = [
        f"- [{rv.domain}] {rv.review_event_id} → {rv.recommendation_id}",
        f"    review_at  : {rv.review_at}",
        f"    question   : {rv.review_question}",
    ]
    if not rv.outcomes:
        parts.append("    outcomes   : (no outcome recorded yet)")
    else:
        parts.append("    outcomes   :")
        for outcome in rv.outcomes:
            followed = "yes" if outcome.followed_recommendation else "no"
            improvement = (
                "?" if outcome.self_reported_improvement is None
                else ("yes" if outcome.self_reported_improvement else "no")
            )
            line = (
                f"      - recorded_at={outcome.recorded_at} "
                f"followed={followed} improvement={improvement}"
            )
            if outcome.free_text:
                line += f" note={outcome.free_text!r}"
            parts.append(line)
    return "\n".join(parts)


def _format_user_memory_section(memory: ExplainUserMemory) -> str:
    header = "## User memory (active at for_date)"
    if not memory.entries:
        return f"{header}\n  (none recorded)"
    lines: list[str] = [header]
    counts = memory.counts or {}
    total = counts.get("total", len(memory.entries))
    lines.append(f"  active: {total}")
    for entry in memory.entries:
        category = entry.get("category", "?")
        key = entry.get("key")
        value = entry.get("value", "")
        domain = entry.get("domain")
        handle = f" ({key})" if key else ""
        scope = f" [{domain}]" if domain else ""
        lines.append(f"  - [{category}]{handle}{scope} {value}")
    return "\n".join(lines)


def _format_list(items: list[Any]) -> str:
    return ", ".join(str(item) for item in items)


def _compact_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ": "))
