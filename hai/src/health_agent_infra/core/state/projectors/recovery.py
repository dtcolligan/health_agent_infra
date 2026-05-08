"""Accepted recovery state projector.

After Phase 3 (migration 004) the recovery accepted-state table carries
only the recovery-domain signals: resting_hr, hrv_ms, acute + chronic
load, acwr, and the training-readiness component mean. Sleep fields are
owned by :mod:`.sleep` and stress / body-battery fields by :mod:`.stress`.

Callers composing a full "clean" write should run recovery + sleep +
stress + running under one transaction (see ``_dual_write_clean_projection``
in :mod:`health_agent_infra.cli`).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import date
from typing import Optional

from health_agent_infra.core.state.projectors._shared import (
    _is_intake_submission_id,
    _now_iso,
    _replace_dimension_in_derived_from,
)


def _acwr_ratio_from_raw(raw_row: dict) -> Optional[float]:
    """Compute acute/chronic ratio when both fields present and chronic > 0."""

    acute = raw_row.get("acute_load")
    chronic = raw_row.get("chronic_load")
    if acute is None or chronic is None or chronic == 0:
        return None
    return round(float(acute) / float(chronic), 3)


_TRAINING_READINESS_COMPONENT_COLUMNS = (
    "training_readiness_sleep_pct",
    "training_readiness_hrv_pct",
    "training_readiness_stress_pct",
    "training_readiness_sleep_history_pct",
    "training_readiness_load_pct",
)


def _training_readiness_component_mean_pct_from_raw(raw_row: dict) -> Optional[float]:
    """Mean of the five Garmin readiness component pcts; None if any missing.

    **Not** Garmin's own overall readiness score. Garmin's CSV doesn't
    export that value, only the five dimension pcts and a categorical
    `training_readiness_level`. A plain arithmetic mean is the simplest
    summary; it can disagree with Garmin's categorical level because
    Garmin weights internally. Agents must treat this as a local proxy,
    cross-check against `training_readiness_level`, and surface any
    disagreement in their rationale.
    """

    vals: list[float] = []
    for col in _TRAINING_READINESS_COMPONENT_COLUMNS:
        v = raw_row.get(col)
        if v is None:
            return None
        try:
            vals.append(float(v))
        except (TypeError, ValueError):
            return None
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def project_accepted_recovery_state_daily(
    conn: sqlite3.Connection,
    *,
    as_of_date: date,
    user_id: str,
    raw_row: dict,
    source_row_ids: Optional[list[str]] = None,
    source: str = "garmin",
    ingest_actor: str = "garmin_csv_adapter",
    commit_after: bool = True,
) -> bool:
    """UPSERT one day's accepted recovery state from a Garmin raw row.

    First write sets ``projected_at``; subsequent writes set ``corrected_at``
    per the hybrid correction grammar (state_model_v1.md §3). Returns
    ``True`` if this was an insert, ``False`` on update.

    **Scope after Phase 3 (migration 004).** Recovery accepted state now
    carries only the recovery-domain signals: resting_hr, hrv_ms, acute
    and chronic load + acwr, and the training readiness component mean.
    Sleep fields are owned by ``accepted_sleep_state_daily`` and stress /
    body-battery fields by ``accepted_stress_state_daily``; those are
    written by :func:`.sleep.project_accepted_sleep_state_daily` and
    :func:`.stress.project_accepted_stress_state_daily` respectively.
    Callers composing a full "clean" write should run all three in one
    transaction (see ``_dual_write_clean_projection`` in cli.py).

    ``training_readiness_component_mean_pct`` is populated as the
    arithmetic mean of the five Garmin readiness component pcts. It is
    **not** Garmin's own overall Training Readiness score — that number
    isn't exported in the daily CSV. None if any component is missing.

    ``commit_after``: set False when composing inside an outer transaction.
    """

    now_iso = _now_iso()
    new_ids = list(source_row_ids or [])

    existing = conn.execute(
        "SELECT derived_from FROM accepted_recovery_state_daily "
        "WHERE as_of_date = ? AND user_id = ?",
        (as_of_date.isoformat(), user_id),
    ).fetchone()
    is_insert = existing is None

    acwr = _acwr_ratio_from_raw(raw_row)
    readiness_mean = _training_readiness_component_mean_pct_from_raw(raw_row)

    if is_insert:
        derived_from_json = json.dumps(sorted(set(new_ids)), sort_keys=True)
        conn.execute(
            """
            INSERT INTO accepted_recovery_state_daily (
                resting_hr, hrv_ms,
                acute_load, chronic_load, acwr_ratio,
                training_readiness_component_mean_pct,
                derived_from, source, ingest_actor,
                projected_at, corrected_at,
                as_of_date, user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                raw_row.get("resting_hr"),
                raw_row.get("health_hrv_value"),
                raw_row.get("acute_load"),
                raw_row.get("chronic_load"),
                acwr,
                readiness_mean,
                derived_from_json,
                source,
                ingest_actor,
                now_iso,
                None,  # corrected_at NULL on first insert
                as_of_date.isoformat(),
                user_id,
            ),
        )
    else:
        # derived_from: per-dimension slot replacement. The Garmin clean
        # owns the "non-intake" dimension — replace its prior contributor
        # IDs with the new ones, preserve any intake-sourced slots that
        # may appear here in future co-ownership flows.
        merged_derived = _replace_dimension_in_derived_from(
            existing["derived_from"],
            new_ids=new_ids,
            owns=lambda rid: not _is_intake_submission_id(rid),
        )
        conn.execute(
            """
            UPDATE accepted_recovery_state_daily SET
                resting_hr = ?, hrv_ms = ?,
                acute_load = ?, chronic_load = ?,
                acwr_ratio = ?, training_readiness_component_mean_pct = ?,
                derived_from = ?, source = ?, ingest_actor = ?,
                projected_at = ?, corrected_at = ?
            WHERE as_of_date = ? AND user_id = ?
            """,
            (
                raw_row.get("resting_hr"),
                raw_row.get("health_hrv_value"),
                raw_row.get("acute_load"),
                raw_row.get("chronic_load"),
                acwr,
                readiness_mean,
                merged_derived,
                source,
                ingest_actor,
                now_iso,
                now_iso,  # corrected_at on update
                as_of_date.isoformat(),
                user_id,
            ),
        )
    if commit_after:
        conn.commit()
    return is_insert
