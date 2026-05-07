"""Explicit user memory — goals, preferences, constraints, durable notes.

Phase D of the post-v0.1.0 roadmap. Adds a local, inspectable layer of
user-memory state alongside the existing accepted / decision / outcome
layers. See ``docs/hai/memory_model.md`` §2.1 and
``reporting/plans/historical/post_v0_1_roadmap.md`` §5 Phase D for framing.

Three bounded concerns:

- :mod:`schemas` — the :class:`UserMemoryEntry` dataclass + allowed
  category enum. This is the write-surface contract the CLI and store
  share.
- :mod:`store` — SQLite writer / reader. Append-only inserts,
  ``archived_at`` soft-delete, active-rows filter.
- :mod:`projector` — read helper that shapes an active-entries bundle
  for ``hai state snapshot`` and ``hai explain``. Kept as a bounded
  read surface so the snapshot / explain callers never inline raw SQL.

Nothing in this module feeds thresholds, classifiers, policy, or
X-rules — see the locked non-goal in
``reporting/plans/historical/post_v0_1_roadmap.md`` §3.1 decision 4.
"""

from health_agent_infra.core.memory.projector import (
    UserMemoryBundle,
    build_user_memory_bundle,
    bundle_to_dict,
)
from health_agent_infra.core.memory.schemas import (
    USER_MEMORY_CATEGORIES,
    UserMemoryCategory,
    UserMemoryEntry,
    UserMemoryValidationError,
    validate_category,
)
from health_agent_infra.core.memory.store import (
    archive_memory_entry,
    insert_memory_entry,
    list_memory_entries,
    read_memory_entry,
)

__all__ = [
    "USER_MEMORY_CATEGORIES",
    "UserMemoryBundle",
    "UserMemoryCategory",
    "UserMemoryEntry",
    "UserMemoryValidationError",
    "archive_memory_entry",
    "build_user_memory_bundle",
    "bundle_to_dict",
    "insert_memory_entry",
    "list_memory_entries",
    "read_memory_entry",
    "validate_category",
]
