"""Cite-or-abstain retrieval over the local allowlist.

This is the only callable surface the grounded-expert skill reaches
through when it needs to back a substantive claim. It enforces three
invariants from ``docs/hai/grounded_expert_scope.md``:

- **Cite or abstain** (§4): every call returns either a non-empty
  ``sources`` list or an ``abstain_reason`` — never both empty, never
  both populated.
- **No user context travels** (§3.2): a query carries a topic token
  and nothing else. A flag that would attach user context to a query
  raises :class:`PrivacyViolation` unless the operator has also set
  the explicit operator-initiated flag. v0.1-F ships no code path
  that sets that flag.
- **No network** (§5.5): this module imports nothing from ``urllib``,
  ``requests``, ``httpx``, ``socket``, or any other IO-over-network
  library. The test suite asserts the module's source file contains no
  such import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from health_agent_infra.core.research.sources import (
    Source,
    by_topic,
    known_topics,
)


class PrivacyViolation(ValueError):
    """Raised when a query would send user context through retrieval.

    The prototype explicitly does not ship a retrieval path that carries
    user context. A query that sets ``user_context_sent=True`` without
    also setting ``operator_initiated=True`` is a scope regression and
    must fail loudly rather than silently leak.
    """


ALLOWLISTED_TOPICS: frozenset[str] = known_topics()


@dataclass(frozen=True)
class RetrievalQuery:
    """A bounded retrieval request.

    Only ``topic`` is load-bearing. ``user_context_sent`` and
    ``operator_initiated`` exist as explicit booleans so a future
    caller that wants to attach user state to a retrieval call has to
    opt in visibly — and still be refused by :func:`retrieve` in this
    phase because ``operator_initiated`` has no code path that sets it
    to true.
    """

    topic: str
    user_context_sent: bool = False
    operator_initiated: bool = False


@dataclass(frozen=True)
class RetrievalResult:
    """The outcome of a retrieval call.

    Exactly one of ``sources`` or ``abstain_reason`` is populated. A
    caller who finds both empty (or both set) has hit a bug, not a
    valid result — :func:`retrieve` guarantees the invariant.
    """

    topic: str
    sources: list[Source] = field(default_factory=list)
    abstain_reason: Optional[str] = None

    @property
    def is_abstain(self) -> bool:
        return self.abstain_reason is not None


def retrieve(query: RetrievalQuery) -> RetrievalResult:
    """Return matching sources for ``query.topic`` or an abstain.

    Raises :class:`PrivacyViolation` when the query asks to send user
    context but is not operator-initiated. In v0.1-F no caller sets
    ``operator_initiated=True``, so any query that flips
    ``user_context_sent`` is refused — this is the scope fence, not a
    branch with a future positive path yet.

    Two abstain paths:

    1. ``topic`` is not on :data:`ALLOWLISTED_TOPICS` — the prototype
       does not have a curated source for this question and is honest
       about that.
    2. ``topic`` is allowlisted but (for some reason — e.g. a source
       was archived) no source currently matches. Treated the same as
       (1) from the caller's perspective.
    """

    if query.user_context_sent and not query.operator_initiated:
        raise PrivacyViolation(
            "retrieval refuses user-context payload; see "
            "docs/hai/grounded_expert_scope.md §3 rule 2"
        )
    if query.user_context_sent and query.operator_initiated:
        raise PrivacyViolation(
            "v0.1-F ships no operator-initiated off-device retrieval "
            "path; see docs/hai/grounded_expert_scope.md §3 rule 3"
        )

    if query.topic not in ALLOWLISTED_TOPICS:
        return RetrievalResult(
            topic=query.topic,
            sources=[],
            abstain_reason=(
                f"topic {query.topic!r} is not on the allowlist; "
                f"see docs/hai/grounded_expert_scope.md §2"
            ),
        )

    matches = by_topic(query.topic)
    if not matches:
        return RetrievalResult(
            topic=query.topic,
            sources=[],
            abstain_reason=(
                f"topic {query.topic!r} is allowlisted but no source "
                f"currently covers it"
            ),
        )

    return RetrievalResult(topic=query.topic, sources=matches)
