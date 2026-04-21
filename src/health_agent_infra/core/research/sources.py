"""Allowlisted source registry for the grounded-expert prototype.

Every row in :data:`SOURCES` is a citation the prototype is allowed to
emit. The registry is frozen at import time — a later commit cannot add
an *external* source without touching this file and
``reporting/docs/grounded_expert_scope.md`` together, so the scope and
the retrieval surface never drift apart silently.

Three load-bearing invariants hold across every record:

1. Each ``origin_path`` points to a file that exists in this repository.
2. Each ``excerpt`` appears verbatim inside that file. The test suite
   (``safety/tests/test_expert_research.py``) asserts both at import
   time so a future edit that renames a section or reflows a sentence
   fails *before* the retrieval surface starts citing a stale excerpt.
3. Every source's ``source_class`` is drawn from
   :data:`ALLOWLISTED_SOURCE_CLASSES`. There is no "other" bucket.

See ``reporting/docs/grounded_expert_scope.md`` §2 for the policy this
module enforces.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

SourceClass = Literal[
    "internal_state_model",
    "internal_x_rules",
    "internal_skill_contract",
]

ALLOWLISTED_SOURCE_CLASSES: tuple[SourceClass, ...] = (
    "internal_state_model",
    "internal_x_rules",
    "internal_skill_contract",
)


@dataclass(frozen=True)
class Source:
    """A single citable record.

    Fields:

    - ``source_id`` — stable handle. Used by the retrieval surface and
      by scenario expectations so a test can pin the citation.
    - ``title`` — human-readable label for the excerpt's subject.
    - ``source_class`` — one of :data:`ALLOWLISTED_SOURCE_CLASSES`.
    - ``origin_path`` — repo-relative path. Resolvable against the repo
      root; the test suite asserts the file exists.
    - ``excerpt`` — a literal substring of the file at ``origin_path``.
      Keep to a single line of plain characters so verification is
      ``substring in file.read_text()``.
    - ``topics`` — the topic tokens this source covers. A retrieval
      query selects sources by topic.
    """

    source_id: str
    title: str
    source_class: SourceClass
    origin_path: str
    excerpt: str
    topics: tuple[str, ...]


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

# One entry per citable claim. Topics are the agent-facing tokens that
# :func:`retrieve` looks up; source_ids are stable so scenarios can
# assert on them.
SOURCES: tuple[Source, ...] = (
    Source(
        source_id="state_model_sleep_debt_band",
        title="Recovery domain's sleep_debt_band enum",
        source_class="internal_state_model",
        origin_path="src/health_agent_infra/domains/recovery/classify.py",
        excerpt=(
            "**sleep_debt_band**: {none, mild, moderate, elevated, unknown}, from"
        ),
        topics=("sleep_debt",),
    ),
    Source(
        source_id="x_rules_x1a_sleep_debt_softens",
        title="X1a — moderate sleep debt softens a hard proposal",
        source_class="internal_x_rules",
        origin_path="reporting/docs/x_rules.md",
        excerpt=(
            "X1a | sleep-debt-softens-hard | "
            "``sleep.classified_state.sleep_debt_band == moderate``"
        ),
        topics=("sleep_debt",),
    ),
    Source(
        source_id="x_rules_x1b_sleep_debt_blocks",
        title="X1b — elevated sleep debt blocks a hard proposal",
        source_class="internal_x_rules",
        origin_path="reporting/docs/x_rules.md",
        excerpt=(
            "X1b | sleep-debt-blocks-hard | "
            "``sleep.classified_state.sleep_debt_band == elevated``"
        ),
        topics=("sleep_debt",),
    ),
    Source(
        source_id="x_rules_x2_nutrition_deficit_softens_strength",
        title="X2 — low protein or calorie deficit softens strength / recovery",
        source_class="internal_x_rules",
        origin_path="reporting/docs/x_rules.md",
        excerpt=(
            "X2 | underfuelling-softens-hard | "
            "``nutrition.classified_state.calorie_deficit_kcal ≥ 500``"
            " OR ``protein_ratio < 0.7``"
        ),
        topics=("protein_ratio_strength",),
    ),
    Source(
        source_id="recovery_skill_body_battery_passive",
        title="body_battery_end_of_day is a Garmin passive aggregate",
        source_class="internal_skill_contract",
        origin_path="src/health_agent_infra/skills/recovery-readiness/SKILL.md",
        excerpt=(
            "`body_battery_end_of_day` — passive aggregates."
            " Informational only in rationale."
        ),
        topics=("body_battery",),
    ),
    Source(
        source_id="x_rules_x6a_low_battery_softens",
        title="X6a — body battery under 30 softens a hard proposal",
        source_class="internal_x_rules",
        origin_path="reporting/docs/x_rules.md",
        excerpt=(
            "X6a | body-battery-low-softens-hard | "
            "``stress.today_body_battery < 30``"
        ),
        topics=("body_battery",),
    ),
)


def by_topic(topic: str) -> list[Source]:
    """Return every source that declares ``topic`` in its topics tuple.

    Linear scan; the registry is O(10) entries and callers usually want
    all matches, not one. Returns an empty list (not ``None``) when no
    source matches — callers treat that as the abstain signal.
    """

    return [s for s in SOURCES if topic in s.topics]


def known_topics() -> frozenset[str]:
    """Every topic token covered by at least one source.

    Used by :data:`retrieval.ALLOWLISTED_TOPICS` so the abstain contract
    is derived, not duplicated. A source added here automatically
    extends the allowlist — but a topic that no source covers is, by
    construction, not on the allowlist.
    """

    tokens: set[str] = set()
    for source in SOURCES:
        tokens.update(source.topics)
    return frozenset(tokens)
