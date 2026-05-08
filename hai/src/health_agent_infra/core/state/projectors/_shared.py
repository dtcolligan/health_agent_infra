"""Shared projector helpers.

Timestamp, boolean coercion, and per-dimension ``derived_from`` hygiene
used by every per-domain projector and by the orchestrator in
:mod:`health_agent_infra.core.state.projector`. Extracted in Phase 3
step 2 when the monolithic projector split into per-domain files.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Callable, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool_to_int(value: bool) -> int:
    return 1 if value else 0


def _opt_bool_to_int(value: Optional[bool]) -> Optional[int]:
    if value is None:
        return None
    return 1 if value else 0


def _is_stress_submission_id(rid: str) -> bool:
    """True for stress raw submission IDs (CLI naming: ``m_stress_*``)."""

    return rid.startswith("m_stress_")


def _is_intake_submission_id(rid: str) -> bool:
    """True for any user-intake submission id (``m_<kind>_<date>_*``)."""

    return rid.startswith("m_")


def _replace_dimension_in_derived_from(
    existing_json: Optional[str],
    *,
    new_ids: list[str],
    owns: Callable[[str], bool],
) -> str:
    """Per-dimension slot replacement for ``derived_from``.

    ``accepted_recovery_state_daily`` is co-owned by the Garmin-clean
    flow and the manual-stress merge. Each projector owns one dimension
    of contributor IDs (Garmin batch IDs vs ``m_stress_*`` submission
    IDs). On UPDATE the projector replaces its own dimension's IDs with
    the latest contributors; other dimensions' IDs are preserved.

    The ``owns(id)`` predicate decides which existing IDs belong to the
    caller's dimension. The result:

      - clean → derived_from = [garmin_batch]
      - stress → derived_from = [garmin_batch, m_stress_x]   ← garmin preserved
      - clean again → derived_from = [garmin_batch_b, m_stress_x]  ← stress preserved
      - stress correction → derived_from = [garmin_batch_b, m_stress_y]
        (m_stress_x evicted: superseded raw rows no longer contribute to
        the current accepted row, and the merge function picks only the
        latest non-superseded raw to source from.)

    Robust against absent / malformed prior values.
    """

    existing: list[str] = []
    if existing_json:
        try:
            parsed = json.loads(existing_json)
            if isinstance(parsed, list):
                existing = [str(x) for x in parsed]
        except (TypeError, json.JSONDecodeError):
            existing = []
    surviving = [rid for rid in existing if not owns(rid)]
    merged = sorted(set(surviving) | set(new_ids or []))
    return json.dumps(merged, sort_keys=True)
