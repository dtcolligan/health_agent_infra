"""Grounded-expert research surface — allowlisted, read-only, cite-or-abstain.

See ``hai/docs/grounded_expert_scope.md`` for the scope / policy
contract this module implements.
"""

from health_agent_infra.core.research.retrieval import (
    ALLOWLISTED_TOPICS,
    PrivacyViolation,
    RetrievalQuery,
    RetrievalResult,
    retrieve,
)
from health_agent_infra.core.research.sources import (
    ALLOWLISTED_SOURCE_CLASSES,
    SOURCES,
    Source,
    by_topic,
    known_topics,
)

__all__ = [
    "ALLOWLISTED_SOURCE_CLASSES",
    "ALLOWLISTED_TOPICS",
    "PrivacyViolation",
    "RetrievalQuery",
    "RetrievalResult",
    "SOURCES",
    "Source",
    "by_topic",
    "known_topics",
    "retrieve",
]
