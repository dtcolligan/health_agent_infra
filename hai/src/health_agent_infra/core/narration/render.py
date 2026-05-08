"""``hai today`` renderer — plain-language per-domain narration.

Takes the canonical :class:`~health_agent_infra.core.explain.ExplainBundle`
for ``(for_date, user_id)`` and produces the user-facing prose the
``reporting`` skill's voice section specifies. Markdown is the TTY
default; ``plain`` strips emojis/headers for TTS; ``json`` emits the
structured shape so agents can compose richer narration.

Voice (copied from D3 and enforced here by convention — the linter
module is a follow-on acceptance item):

- Plain, direct, first-person.
- No medical language (see ``BANNED_MEDICAL_TOKENS`` in the validate
  module — the renderer never synthesises new language, it only
  surfaces rationale the skill authored, which is already
  banned-token-checked at propose time).
- No rule IDs in prose (R1, X3b, require_min_coverage).
- No raw numbers beyond what the rationale explicitly names.
- Always end each section with the follow-up question.
"""

from __future__ import annotations

import json
from typing import Any, Optional

from health_agent_infra.core.explain import ExplainBundle
from health_agent_infra.core.narration.templates import (
    ACTION_CLASS_DEFER,
    ACTION_CLASS_EMOJI,
    ACTION_CLASS_PLAIN_MARKERS,
    DEFER_REVIEW_QUESTION_TEMPLATES,
    DOMAIN_ORDER,
    action_class_for,
    cold_start_footer,
    cold_start_nutrition_defer_hint,
    defer_unblock_hint,
    humanize_action,
)


_DOMAIN_DISPLAY_NAME: dict[str, str] = {
    "recovery": "Recovery",
    "sleep": "Sleep",
    "running": "Running",
    "strength": "Strength",
    "stress": "Stress",
    "nutrition": "Nutrition",
}


def render_today(
    bundle: ExplainBundle,
    *,
    format: str = "markdown",
    domain_filter: Optional[str] = None,
    cold_start_by_domain: Optional[dict[str, dict[str, Any]]] = None,
    streak_days: Optional[int] = None,
) -> str:
    """Render an explain bundle as the ``hai today`` user surface.

    ``format`` is one of ``markdown`` (default), ``plain``, or ``json``.
    ``domain_filter``, when set to one of the six domain names, narrows
    the output to that single domain section (top-matter + summary +
    footer are still emitted so a filtered run reads coherently).

    ``cold_start_by_domain`` is the D4 hook. When supplied, shape:

        {"recovery": {"cold_start": bool, "history_days": int},
         "running":  {"cold_start": bool, "history_days": int},
         ...}

    The renderer uses it for two things:
      1. Cold-start + nutrition defer → the "I'd be making it up"
         hint replaces the generic unblock hint.
      2. Each cold-start domain adds a one-line "history accumulates"
         footer so first-run users know why confidence is capped and
         when it'll improve.

    When the dict is None or a domain is absent, the renderer behaves
    exactly as pre-D4 (no cold-start framing).

    ``streak_days`` is the v0.1.13 W-AG hook for cold-start prose.
    When None, behaves exactly as pre-W-AG. When 0, the renderer
    surfaces "first plan" framing in top-matter + footer. When ≥30,
    it surfaces "X-day streak" framing. Mid-range (1-29) keeps
    pre-W-AG voice — the user is still onboarding and either framing
    would feel forced. (The 30-day threshold is the planned
    "established" gate per PLAN.md §2.B; v0.1.13 IR r1 F-IR-01
    corrected a transient 7-day implementation drift.)
    """

    if format == "json":
        return render_today_json(bundle, domain_filter=domain_filter)
    if format not in ("markdown", "plain"):
        raise ValueError(
            f"render_today: unknown format {format!r}; use markdown|plain|json"
        )
    use_markdown = format == "markdown"
    return _render_prose(
        bundle,
        use_markdown=use_markdown,
        domain_filter=domain_filter,
        cold_start_by_domain=cold_start_by_domain or {},
        streak_days=streak_days,
    )


def render_today_json(
    bundle: ExplainBundle,
    *,
    domain_filter: Optional[str] = None,
) -> str:
    """JSON serialisation of what prose rendering consumes.

    Useful for agents that want to compose their own narration or for
    downstream tools that need the bundle in a flat shape rather than
    the operator-oriented explain JSON.
    """

    sections = []
    for domain in DOMAIN_ORDER:
        if domain_filter and domain != domain_filter:
            continue
        rec = _find_recommendation(bundle, domain)
        if rec is None:
            continue
        sections.append(_section_dict(domain, rec))

    payload = {
        "daily_plan_id": bundle.plan.daily_plan_id,
        "user_id": bundle.plan.user_id,
        "for_date": bundle.plan.for_date,
        "synthesized_at": bundle.plan.synthesized_at,
        "sections": sections,
        "summary": _summary_stats(bundle, domain_filter=domain_filter),
    }
    return json.dumps(payload, indent=2, sort_keys=True)


# ---------------------------------------------------------------------------
# Prose rendering
# ---------------------------------------------------------------------------


def _render_prose(
    bundle: ExplainBundle,
    *,
    use_markdown: bool,
    domain_filter: Optional[str],
    cold_start_by_domain: dict[str, dict[str, Any]],
    streak_days: Optional[int] = None,
) -> str:
    lines: list[str] = []
    lines.extend(_render_top_matter(
        bundle, use_markdown=use_markdown, streak_days=streak_days,
    ))
    lines.extend(_render_summary(bundle, domain_filter=domain_filter))

    rendered_any = False
    for domain in DOMAIN_ORDER:
        if domain_filter and domain != domain_filter:
            continue
        rec = _find_recommendation(bundle, domain)
        if rec is None:
            # Domain absent from the plan entirely — render a short
            # honest stub rather than silently skipping, so the reader
            # can tell "missing" apart from "just not yet filtered in."
            lines.append("")
            lines.extend(_render_missing_domain(
                domain, use_markdown=use_markdown,
            ))
            continue
        lines.append("")
        lines.extend(_render_section(
            domain, rec,
            use_markdown=use_markdown,
            cold_start=cold_start_by_domain.get(domain, {}).get("cold_start", False),
        ))
        rendered_any = True

    if domain_filter and not rendered_any:
        # Filter requested a domain that isn't in the plan. Honest
        # surface rather than silent empty output.
        lines.append("")
        lines.append(
            f"No {domain_filter} recommendation in today's plan "
            f"({bundle.plan.daily_plan_id})."
        )

    # D4 cold-start footers — one per cold-start domain the render
    # included, so the reader knows why confidence looks thin and
    # when it'll improve. Rendered after all domain sections so the
    # footers read as a group, not scattered through the plan.
    lines.extend(
        _render_cold_start_footers(
            cold_start_by_domain,
            rendered_domains=_rendered_domain_set(
                bundle, domain_filter=domain_filter,
            ),
        )
    )

    lines.append("")
    lines.extend(_render_footer(
        bundle, use_markdown=use_markdown, streak_days=streak_days,
    ))
    return "\n".join(lines) + "\n"


def _rendered_domain_set(
    bundle: ExplainBundle,
    *,
    domain_filter: Optional[str],
) -> set[str]:
    """Which DOMAIN_ORDER entries actually made it into the output?
    Cold-start footers should only emit for domains the user actually
    saw — not for filtered-out or missing ones.
    """

    seen: set[str] = set()
    for domain in DOMAIN_ORDER:
        if domain_filter and domain != domain_filter:
            continue
        if _find_recommendation(bundle, domain) is not None:
            seen.add(domain)
    return seen


def _render_cold_start_footers(
    cold_start_by_domain: dict[str, dict[str, Any]],
    *,
    rendered_domains: set[str],
) -> list[str]:
    lines: list[str] = []
    emitted = False
    for domain in DOMAIN_ORDER:
        if domain not in rendered_domains:
            continue
        meta = cold_start_by_domain.get(domain)
        if not meta or not meta.get("cold_start"):
            continue
        if not emitted:
            lines.append("")
            emitted = True
        lines.append(
            cold_start_footer(
                domain=domain,
                history_days=int(meta.get("history_days", 0)),
            )
        )
    return lines


# W-AG (v0.1.13): streak threshold above which the "X-day streak"
# framing engages. Per PLAN.md §1.2 + §2.B (W-AG): "different language
# for day-1 vs day-30+ users." Below 30 the user is still onboarding;
# the streak phrase would feel premature. At/above 30 the streak is a
# real-signal habit worth surfacing. v0.1.13 IR round 1 F-IR-01
# corrected the value from a transient 7-day implementation drift to
# the planned 30-day contract.
_STREAK_ESTABLISHED_THRESHOLD = 30


def _render_top_matter(
    bundle: ExplainBundle,
    *,
    use_markdown: bool,
    streak_days: Optional[int] = None,
) -> list[str]:
    if streak_days is not None and streak_days == 0:
        # Day-1 / cold-start framing. The user has either never run
        # `hai daily` successfully OR hasn't yet today.
        header = f"Today, {bundle.plan.for_date} — your first plan"
    elif (
        streak_days is not None
        and streak_days >= _STREAK_ESTABLISHED_THRESHOLD
    ):
        header = (
            f"Today, {bundle.plan.for_date} — your plan "
            f"({streak_days}-day streak)"
        )
    else:
        header = f"Today, {bundle.plan.for_date} — your plan"
    if use_markdown:
        return [f"# {header}"]
    return [header, "=" * len(header)]


def _render_summary(
    bundle: ExplainBundle,
    *,
    domain_filter: Optional[str],
) -> list[str]:
    stats = _summary_stats(bundle, domain_filter=domain_filter)
    n_prescriptions = stats["prescriptions"]
    n_defers = stats["defers"]
    if n_prescriptions == 0 and n_defers == 0:
        return ["", "No recommendations in this plan."]
    parts = []
    if n_prescriptions:
        parts.append(f"{n_prescriptions} prescription{'s' if n_prescriptions != 1 else ''}")
    if n_defers:
        parts.append(f"{n_defers} defer{'s' if n_defers != 1 else ''}")
    summary = ", ".join(parts) + "."
    return ["", summary]


def _render_section(
    domain: str,
    rec,
    *,
    use_markdown: bool,
    cold_start: bool = False,
) -> list[str]:
    action_class = action_class_for(rec.action)
    prefix = (
        ACTION_CLASS_EMOJI[action_class]
        if use_markdown else ACTION_CLASS_PLAIN_MARKERS[action_class]
    )
    title = _DOMAIN_DISPLAY_NAME.get(domain, domain.capitalize())
    action_summary = humanize_action(domain, rec.action)

    lines: list[str] = []
    if use_markdown:
        lines.append(f"## {prefix} {title} — {action_summary}")
    else:
        lines.append(f"{prefix} {title} — {action_summary}")
        lines.append("-" * len(lines[-1]))

    # Defer sections get the unblock hint in place of rationale prose —
    # a defer by definition has nothing useful to cite. D4 swaps in a
    # nutrition-cold-start-specific "I'd be making it up" message when
    # both conditions hold.
    if action_class == ACTION_CLASS_DEFER:
        lines.append("")
        if domain == "nutrition" and cold_start:
            lines.append(cold_start_nutrition_defer_hint())
        else:
            lines.append(defer_unblock_hint(domain))
    elif rec.rationale:
        lines.append("")
        lines.append(_rationale_prose(rec.rationale))

    # Confidence + uncertainty, one sentence.
    lines.append("")
    lines.append(_confidence_sentence(rec))

    # Follow-up question — fall back to the per-domain template if the
    # recommendation's stored review_question is empty (shouldn't happen
    # after D3 but defensive).
    follow_up = rec.review_question or DEFER_REVIEW_QUESTION_TEMPLATES.get(
        domain, "I'll check in tomorrow."
    )
    lines.append("")
    lines.append(f"Follow-up: {follow_up}")
    return lines


def _render_missing_domain(
    domain: str, *, use_markdown: bool,
) -> list[str]:
    title = _DOMAIN_DISPLAY_NAME.get(domain, domain.capitalize())
    prefix = (
        ACTION_CLASS_EMOJI[ACTION_CLASS_DEFER]
        if use_markdown else ACTION_CLASS_PLAIN_MARKERS[ACTION_CLASS_DEFER]
    )
    line = f"{prefix} {title} — no recommendation in today's plan."
    if use_markdown:
        return [f"## {line}"]
    return [line, "-" * len(line)]


def _render_footer(
    bundle: ExplainBundle,
    *,
    use_markdown: bool,
    streak_days: Optional[int] = None,
) -> list[str]:
    base = (
        f"Recorded as plan {bundle.plan.daily_plan_id}. "
        f"Run `hai review record` tomorrow morning to log how today went."
    )
    if streak_days is not None and streak_days == 0:
        base = (
            f"Recorded as plan {bundle.plan.daily_plan_id}. "
            f"This is your first plan — confidence will sharpen as the "
            f"system sees more of your training. Run `hai daily` again "
            f"tomorrow to keep the chain going."
        )
    elif (
        streak_days is not None
        and streak_days >= _STREAK_ESTABLISHED_THRESHOLD
    ):
        base = (
            f"Recorded as plan {bundle.plan.daily_plan_id}. "
            f"Run `hai review record` tomorrow morning to log how today "
            f"went and keep your {streak_days}-day streak going."
        )
    return [base]


def _rationale_prose(rationale: list[str]) -> str:
    """Flatten a list of rationale tokens into one or two sentences.

    Tokens are already skill-authored free-text (see the reporting skill's
    voice contract), so the renderer just joins them with sensible
    punctuation rather than synthesising new copy.
    """

    cleaned = [r.strip() for r in rationale if r and r.strip()]
    if not cleaned:
        return ""
    return " ".join(_ensure_terminal_period(c) for c in cleaned)


def _ensure_terminal_period(text: str) -> str:
    if not text:
        return text
    return text if text[-1] in ".!?" else text + "."


def _confidence_sentence(rec) -> str:
    """One-sentence confidence + uncertainty line.

    Structure: "Confidence: <level>.[ Uncertainty: <joined>.]" — short,
    consistent, drops the uncertainty clause when there's nothing to
    surface.
    """

    parts = [f"Confidence: {rec.confidence}."]
    if rec.uncertainty:
        uncertainty_joined = ", ".join(rec.uncertainty)
        parts.append(f"Uncertainty: {uncertainty_joined}.")
    return " ".join(parts)


# ---------------------------------------------------------------------------
# JSON payload helpers
# ---------------------------------------------------------------------------


def _section_dict(domain: str, rec) -> dict[str, Any]:
    return {
        "domain": domain,
        "action": rec.action,
        "action_class": action_class_for(rec.action),
        "action_summary": humanize_action(domain, rec.action),
        "confidence": rec.confidence,
        "rationale": list(rec.rationale),
        "uncertainty": list(rec.uncertainty),
        "follow_up": rec.review_question or DEFER_REVIEW_QUESTION_TEMPLATES.get(
            domain, "",
        ),
        "recommendation_id": rec.recommendation_id,
    }


def _summary_stats(
    bundle: ExplainBundle,
    *,
    domain_filter: Optional[str],
) -> dict[str, int]:
    prescriptions = 0
    defers = 0
    for rec in bundle.recommendations:
        if domain_filter and rec.domain != domain_filter:
            continue
        if action_class_for(rec.action) == ACTION_CLASS_DEFER:
            defers += 1
        else:
            prescriptions += 1
    return {"prescriptions": prescriptions, "defers": defers}


# ---------------------------------------------------------------------------
# Internal lookup
# ---------------------------------------------------------------------------


def _find_recommendation(bundle: ExplainBundle, domain: str):
    for rec in bundle.recommendations:
        if rec.domain == domain:
            return rec
    return None
