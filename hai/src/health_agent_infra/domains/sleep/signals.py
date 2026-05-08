"""Sleep-domain signal derivation.

Phase 3 step 5. Mirrors the Phase 2 ``domains.running.signals`` module:
a single pure function that builds the ``sleep_signals`` dict
``classify_sleep_state`` + ``evaluate_sleep_policy`` consume from
existing snapshot inputs.

Keeping derivation here — not in ``snapshot.py`` — preserves the
boundary that ``core/state/snapshot.py`` is a thin assembler that
dispatches to per-domain logic, rather than holding domain-specific
aggregation rules of its own.

Inputs come from the snapshot bundle:

  - ``sleep_today``: today's ``accepted_sleep_state_daily`` row, or
    ``None`` if no row.
  - ``sleep_history``: trailing rows from ``accepted_sleep_state_daily``
    excluding today, ordered by ``as_of_date``.
  - ``evidence``: the ``hai clean`` ``cleaned_evidence`` dict. Used as a
    fall-through for ``sleep_hours`` when the accepted-sleep row is
    missing but the raw pull surfaced it — keeps classify lit when
    migration 004's reproject hasn't run yet.

Output is the dict shape ``classify_sleep_state`` +
``evaluate_sleep_policy`` already accept. Absent inputs become ``None``
entries; the classifier + policy translate those into ``unknown`` bands
and uncertainty tokens.
"""

from __future__ import annotations

from typing import Any, Optional


def derive_sleep_signals(
    *,
    sleep_today: Optional[dict[str, Any]],
    sleep_history: list[dict[str, Any]],
    evidence: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Build a ``sleep_signals`` dict for sleep classify + policy.

    Keys emitted:

      - ``sleep_hours`` — headline duration. Prefer today's accepted-sleep
        row; fall back to ``evidence['sleep_hours']`` (the ``hai clean``
        bundle) so the classifier stays lit when the sleep projector
        hasn't been run yet on a freshly-pulled day.
      - ``sleep_score_overall`` / ``sleep_awake_min`` — enrichment
        signals from the accepted-sleep row. None when absent.
      - ``sleep_start_variance_minutes`` — v1 is always None because
        ``sleep_start_ts`` is a v1.1 column; carried as a key so the
        classifier's contract is exercised end-to-end.
      - ``sleep_history_hours_last_7`` — trailing 7 nights of
        ``sleep_hours`` including today when present, most-recent last.
        Consumed by R-chronic-deprivation.
    """

    sleep_hours = _pick(sleep_today, "sleep_hours")
    if sleep_hours is None and evidence is not None:
        sleep_hours = evidence.get("sleep_hours")

    sleep_score_overall = _pick(sleep_today, "sleep_score_overall")
    sleep_awake_min = _pick(sleep_today, "sleep_awake_min")

    history_hours_last_7 = _trailing_sleep_history_hours(
        sleep_today=sleep_today,
        sleep_history=sleep_history,
        window=7,
    )

    return {
        "sleep_hours": sleep_hours,
        "sleep_score_overall": sleep_score_overall,
        "sleep_awake_min": sleep_awake_min,
        # v1.1 enrichment — always None in v1 because sleep_start_ts is
        # never populated on accepted_sleep_state_daily today.
        "sleep_start_variance_minutes": None,
        "sleep_history_hours_last_7": history_hours_last_7,
    }


def _pick(row: Optional[dict[str, Any]], key: str) -> Optional[Any]:
    if row is None:
        return None
    return row.get(key)


def _trailing_sleep_history_hours(
    *,
    sleep_today: Optional[dict[str, Any]],
    sleep_history: list[dict[str, Any]],
    window: int,
) -> list[Optional[float]]:
    """Return the trailing ``window`` nights of sleep_hours, most-recent last.

    History rows are passed oldest-to-newest; the result matches that
    orientation (oldest first, today last). Entries that are missing or
    lack a sleep_hours value become ``None``. When fewer than ``window``
    days are available, the returned list is shorter — the policy layer
    interprets list length as the window actually observed.
    """

    series: list[Optional[float]] = []
    # history rows are oldest-to-newest per build_snapshot.
    for row in sleep_history[-(window - 1):] if window > 1 else []:
        series.append(row.get("sleep_hours"))
    if sleep_today is not None:
        series.append(sleep_today.get("sleep_hours"))
    return series
