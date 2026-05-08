"""Read-shape helper for exposing user memory to snapshot + explain.

The raw ``user_memory`` table is already a read-only surface via
:func:`health_agent_infra.core.memory.store.list_memory_entries`. This
module wraps that read into the shape the snapshot + explain JSON
bundles expect, so both consumers share one projection:

    {
      "as_of": "YYYY-MM-DDTHH:MM:SS+00:00" | "YYYY-MM-DD" | null,
      "counts": {
        "goal": <int>, "preference": <int>,
        "constraint": <int>, "context": <int>,
        "total": <int>,
      },
      "entries": [
        {memory_id, user_id, category, key, value, domain,
         created_at, archived_at, source, ingest_actor},
        ...
      ],
    }

The ``as_of`` field is echoed so the downstream JSON reader can tell
whether the bundle represents "active now" or "active at plan date".
``counts`` is included so a UI/agent can render category totals without
walking the entries list.

No writes, no recomputation — this is pure read-and-shape.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from typing import Any, Optional

from health_agent_infra.core.memory.schemas import (
    USER_MEMORY_CATEGORIES,
    UserMemoryEntry,
)
from health_agent_infra.core.memory.store import list_memory_entries


@dataclass(frozen=True)
class UserMemoryBundle:
    """Shaped snapshot/explain view of active user memory.

    ``as_of`` is the point-in-time the bundle represents: the
    snapshot's ``as_of_date`` (end-of-day UTC) or the plan's
    ``for_date`` (end-of-day UTC). ``None`` means "currently active"
    without time-travel filtering (the ``hai memory list`` default).
    """

    as_of: Optional[datetime]
    entries: tuple[UserMemoryEntry, ...]

    def counts(self) -> dict[str, int]:
        # mypy: Literal-keyed dict refuses "total"; widen via
        # explicit dict[str, int] before adding the synthetic key.
        # v0.1.12 W-H2.
        out: dict[str, int] = {
            category: 0 for category in USER_MEMORY_CATEGORIES
        }
        for entry in self.entries:
            out[entry.category] = out.get(entry.category, 0) + 1
        out["total"] = len(self.entries)
        return out


def build_user_memory_bundle(
    conn: sqlite3.Connection,
    *,
    user_id: str,
    as_of: Optional[date | datetime] = None,
) -> UserMemoryBundle:
    """Return the active user-memory bundle for ``user_id``.

    When ``as_of`` is a :class:`date`, the bundle reflects entries that
    were active at end-of-day UTC on that date (``23:59:59+00:00``) —
    the framing snapshot + explain use so an entry created the morning
    of ``for_date`` still shows up in that day's bundle. When ``as_of``
    is a :class:`datetime`, it is used verbatim. When ``None``, no
    time-travel filter is applied and only currently-active entries are
    returned.

    Archived entries are excluded unconditionally — snapshot and
    explain expose only bounded, currently-applicable context. An
    operator who needs the archived history uses
    ``hai memory list --include-archived`` instead.
    """

    as_of_dt = _coerce_as_of(as_of)
    entries = list_memory_entries(
        conn,
        user_id=user_id,
        include_archived=False,
        as_of=as_of_dt,
    )
    return UserMemoryBundle(as_of=as_of_dt, entries=tuple(entries))


def bundle_to_dict(bundle: UserMemoryBundle) -> dict[str, Any]:
    """Return a JSON-ready dict for the bundle.

    Exposed as a free function so snapshot and explain callers don't
    depend on the dataclass shape directly; a future bundle field can
    land here without touching the callers.
    """

    return {
        "as_of": bundle.as_of.isoformat() if bundle.as_of else None,
        "counts": bundle.counts(),
        "entries": [_entry_to_dict(entry) for entry in bundle.entries],
    }


def _entry_to_dict(entry: UserMemoryEntry) -> dict[str, Any]:
    return {
        "memory_id": entry.memory_id,
        "user_id": entry.user_id,
        "category": entry.category,
        "key": entry.key,
        "value": entry.value,
        "domain": entry.domain,
        "created_at": entry.created_at.isoformat(),
        "archived_at": (
            entry.archived_at.isoformat() if entry.archived_at else None
        ),
        "source": entry.source,
        "ingest_actor": entry.ingest_actor,
    }


def _coerce_as_of(value: Optional[date | datetime]) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    # ``date`` → end-of-day UTC so an entry recorded earlier on that
    # civil date is considered active for the day.
    return datetime.combine(value, time(23, 59, 59), tzinfo=timezone.utc)
