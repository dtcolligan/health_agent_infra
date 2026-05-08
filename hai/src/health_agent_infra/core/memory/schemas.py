"""Write-surface contract for explicit user memory.

Defines the :class:`UserMemoryEntry` dataclass + the allowed category
enum. The dataclass mirrors the shape of the `user_memory` row on disk
(migration 007) with one difference: ``created_at`` / ``archived_at``
use Python :class:`datetime` instances at the API boundary and are
serialised to ISO-8601 strings only at the SQLite border.

Validation lives here (and not at the CLI) so the store, the snapshot
projector, and any future callers share the same invariants.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional


UserMemoryCategory = Literal["goal", "preference", "constraint", "context"]

USER_MEMORY_CATEGORIES: tuple[UserMemoryCategory, ...] = (
    "goal",
    "preference",
    "constraint",
    "context",
)


class UserMemoryValidationError(ValueError):
    """Raised when a proposed memory entry violates an invariant.

    Carries the same ``invariant`` field style as
    :class:`health_agent_infra.core.validate.RecommendationValidationError`
    so the CLI can render a consistent ``invariant=<id>`` error line.
    """

    def __init__(self, invariant: str, message: str) -> None:
        super().__init__(message)
        self.invariant = invariant


@dataclass(frozen=True)
class UserMemoryEntry:
    """A single row of explicit user memory.

    Fields:

    - ``memory_id`` — deterministic or caller-supplied id, PK.
    - ``user_id`` — the user the memory attaches to.
    - ``category`` — one of :data:`USER_MEMORY_CATEGORIES`.
    - ``value`` — the durable content (e.g. "build strength block
      through June", "no early-morning hard runs",
      "left-knee tendonitis still sensitive"). Required, non-empty.
    - ``key`` — optional short handle within the category
      (e.g. ``primary_goal``, ``injury_left_knee``). Not unique.
    - ``domain`` — optional scoping to one of the six domains. ``None``
      means global.
    - ``created_at`` — ISO-8601 UTC timestamp. Author time, not ingest
      time — the moment the operator recorded the memory.
    - ``archived_at`` — ``None`` while active; set when the operator
      archives the entry via ``hai memory archive``.
    - ``source`` — fact origin (typically ``user_manual``).
    - ``ingest_actor`` — transport identity (typically
      ``hai_cli_direct`` or ``claude_agent_v1``).
    """

    memory_id: str
    user_id: str
    category: UserMemoryCategory
    value: str
    key: Optional[str]
    domain: Optional[str]
    created_at: datetime
    archived_at: Optional[datetime]
    source: str
    ingest_actor: str


def validate_category(raw: str) -> UserMemoryCategory:
    """Return ``raw`` narrowed to :data:`UserMemoryCategory` or raise.

    Kept as a function (rather than Python's :class:`enum.Enum`) so the
    CLI, the store, and the projector all share one validation path
    without dragging an enum class through every dict-shaped read.
    """

    if raw not in USER_MEMORY_CATEGORIES:
        raise UserMemoryValidationError(
            "category_enum",
            f"category must be one of {list(USER_MEMORY_CATEGORIES)!r}; "
            f"got {raw!r}",
        )
    return raw  # type: ignore[return-value]


def validate_value(raw: str) -> str:
    """Reject empty / whitespace-only values."""

    stripped = raw.strip() if isinstance(raw, str) else ""
    if not stripped:
        raise UserMemoryValidationError(
            "value_non_empty",
            "value must be a non-empty string after stripping whitespace",
        )
    return raw


def validate_domain(raw: Optional[str]) -> Optional[str]:
    """Normalise optional domain scope.

    v1 accepts any non-empty string; we do not pin the enum here because
    ``domain`` is advisory metadata (the store only indexes it) and
    pinning would couple this schema to the six-domain registry's
    spelling. Empty string is treated the same as ``None``.
    """

    if raw is None:
        return None
    stripped = raw.strip()
    return stripped or None
