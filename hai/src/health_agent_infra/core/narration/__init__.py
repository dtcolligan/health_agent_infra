"""User-facing narration surface (D3).

Renders an :class:`~health_agent_infra.core.explain.ExplainBundle` in the
voice the ``reporting`` skill specifies — plain, first-person, no
medical language, no rule IDs leaked. Consumed by ``hai today`` directly
and by the ``reporting`` skill for agent-mediated conversation so both
stay in voice.

Public surface:

- :func:`render_today` — the full top-matter + per-domain + footer
  renderer in ``markdown`` / ``plain`` / ``json`` modes.
- :data:`DOMAIN_ORDER` — canonical section order.
- :data:`ACTION_CLASS_EMOJI` — action-class → emoji mapping.
"""

from health_agent_infra.core.narration.render import (
    render_today,
    render_today_json,
)
from health_agent_infra.core.narration.templates import (
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
from health_agent_infra.core.narration.voice import (
    LintFinding,
    lint_narration,
)

__all__ = [
    "ACTION_CLASS_EMOJI",
    "ACTION_CLASS_PLAIN_MARKERS",
    "DEFER_REVIEW_QUESTION_TEMPLATES",
    "DOMAIN_ORDER",
    "LintFinding",
    "action_class_for",
    "cold_start_footer",
    "cold_start_nutrition_defer_hint",
    "defer_unblock_hint",
    "humanize_action",
    "lint_narration",
    "render_today",
    "render_today_json",
]
