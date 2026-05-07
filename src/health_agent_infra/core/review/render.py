"""Weekly-review render layer — W52 step 5 (v0.2.0 §2.D).

Translates the structured :class:`WeeklyProseBundle` from
``core/review/prose_builder.py`` into either:

  * **Markdown** — human-readable surface for ``hai review weekly
    --markdown`` (the default). Single-pass concatenation of section
    headers + atoms; the F-EXPLAIN-UX obligation hooks fire against
    the rendered string.

  * **JSON** — machine-readable surface for ``hai review weekly
    --json``. Carries every prose-builder lane plus the optional
    ``claim_cards`` list. Default: canonical-latest view (one row
    per ``(iso_week, user_id, claim_id)``). With
    ``include_history=True``: full append-only history (latest +
    superseded) per PLAN §2.D acceptance #9 + F-PLAN-R2-03.

Determinism contract (PLAN §2.D acceptance #1): same fixture week
→ byte-identical output across consecutive runs. Achieved by:

  * stable section order (header → per-domain → data_quality →
    cadence → footer)
  * stable atom ordering within sections (built deterministically
    by the prose builder)
  * sorted JSON keys in ``json.dumps``
  * no ``datetime.now()`` in this module — the prose builder
    already chose the rendering moment

Abstain-branch render: when ``coverage.weekly_status ==
'insufficient_data'`` the sections list is empty; the markdown
output uses the PLAN §2.D abstain template directly (counts +
threshold + date lists are deterministic substitutions from
``coverage`` per the F-PLAN-03 round-1 correction).
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any, Optional

from health_agent_infra.core.review.prose_builder import (
    WeeklyAtom,
    WeeklyProseBundle,
    WeeklyProseSection,
)
from health_agent_infra.core.review.weekly_card import (
    load_canonical_latest_for_week,
    load_full_history_for_week,
)


# ---------------------------------------------------------------------------
# Markdown render
# ---------------------------------------------------------------------------


def render_markdown(bundle: WeeklyProseBundle) -> str:
    """Render the bundle as a human-readable markdown string.

    On the abstain branch (``coverage.weekly_status ==
    'insufficient_data'``) emits the PLAN §2.D abstain template:

      # Weekly review — 2026-W18

      **Insufficient data for this week.**

      Plans found: 3 of 7 days (threshold: ≥5).
      Days with plans: 2026-04-30, 2026-05-02, 2026-05-04.
      Days without plans: 2026-04-27, 2026-04-28, 2026-04-29, ...

      Run `hai daily` on past days where you have data, then
      re-run this command.

    Counts + threshold + date lists are deterministic
    substitutions from ``coverage`` — no prose authoring on the
    abstain path. F-EXPLAIN-03: ``synthesis_meta`` never surfaces
    in markdown.
    """

    coverage = bundle.coverage
    if coverage.weekly_status == "insufficient_data":
        return _render_abstain_markdown(bundle)

    return _render_full_markdown(bundle)


def _render_abstain_markdown(bundle: WeeklyProseBundle) -> str:
    coverage = bundle.coverage
    populated = ", ".join(coverage.populated_dates) or "(none)"
    missing = ", ".join(coverage.missing_dates) or "(none)"
    week_size = len(bundle.coverage.populated_dates) + len(
        bundle.coverage.missing_dates
    )
    lines = [
        f"# Weekly review — {coverage.iso_week}",
        "",
        "**Insufficient data for this week.**",
        "",
        (
            f"Plans found: {coverage.days_with_plans} of {week_size} "
            f"days (threshold: ≥{coverage.coverage_threshold})."
        ),
        f"Days with plans: {populated}.",
        f"Days without plans: {missing}.",
        "",
        (
            "Run `hai daily` on past days where you have data, then "
            "re-run this command."
        ),
    ]
    return "\n".join(lines) + "\n"


def _render_full_markdown(bundle: WeeklyProseBundle) -> str:
    parts: list[str] = []
    for idx, section in enumerate(bundle.sections):
        # Header section uses h1; all others use h2.
        prefix = "# " if section.section_id == "header" else "## "
        parts.append(f"{prefix}{section.title}")
        parts.append("")
        for atom in section.atoms:
            parts.append(_format_atom_markdown(atom))
        parts.append("")
        # Multi-canonical-day disposition (F-PHASE0-07): if a
        # canonical_plan day has 2+ non-superseded plans, surface
        # the disposition prose at the end of the corresponding
        # domain section. The disposition is a footer note here so
        # the section atoms stay clean for W58D fact-gate review.
        if (
            section.section_id == "header"
            and _multi_canonical_day_count(bundle.coverage) > 0
        ):
            parts.append(
                "> Multiple plans on this day: surfaced as separate "
                "rows in the per-domain sections below per the "
                "F-PHASE0-07 reconciliation contract."
            )
            parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def _format_atom_markdown(atom: WeeklyAtom) -> str:
    """Render one atom as a markdown bullet line.

    Atoms render as `- <atom_text>` so the markdown is uniform.
    No atom_id, atom_type, or audit_refs leak into markdown — those
    surface only in JSON. F-EXPLAIN-03 invariant: ``synthesis_meta``
    must never appear in this string (asserted by the prose builder
    test suite).
    """

    return f"- {atom.atom_text}"


def _multi_canonical_day_count(coverage: Any) -> int:
    """Number of dates within the rendered week that have 2+ non-
    superseded canonical plans (F-PHASE0-07). Drives the markdown
    "multiple plans on this day" disposition footer per PLAN §409.
    Reads ``coverage.multi_canonical_dates`` (added v0.2.0 IR R1
    F-IR-05); legacy/test instances without the field default to 0.
    """
    return len(getattr(coverage, "multi_canonical_dates", ()) or ())


# ---------------------------------------------------------------------------
# JSON render
# ---------------------------------------------------------------------------


def render_json(
    bundle: WeeklyProseBundle,
    *,
    conn: Optional[sqlite3.Connection] = None,
    include_history: bool = False,
) -> str:
    """Render the bundle as a JSON string.

    On the abstain branch carries ``weekly_status='insufficient_data'``,
    populated_dates, missing_dates, threshold, and the empty
    ``claim_cards`` array. No section content (the prose-builder's
    sections list is empty on abstain).

    On the full-render branch carries every section + the
    ``claim_cards`` array. ``include_history`` controls which view
    of weekly_claim_card is emitted:

      * False (default) — canonical-latest view (max ``computed_at``
        per ``(iso_week, user_id, claim_id)``); superseded cards
        excluded.
      * True — full append-only history including superseded cards
        (PLAN §2.D acceptance #9 + F-PLAN-R2-03).

    Cards are loaded via ``weekly_card.load_canonical_latest_for_week``
    or ``weekly_card.load_full_history_for_week`` from the connection.
    If ``conn`` is None or the table is missing the array is empty.
    """

    payload: dict[str, Any] = {
        "iso_week": bundle.iso_week,
        "user_id": bundle.user_id,
        "weekly_status": bundle.coverage.weekly_status,
        "primary_goal": bundle.primary_goal,
        "coverage": {
            "days_with_plans": bundle.coverage.days_with_plans,
            "coverage_threshold": bundle.coverage.coverage_threshold,
            "populated_dates": list(bundle.coverage.populated_dates),
            "missing_dates": list(bundle.coverage.missing_dates),
            "multi_canonical_dates": list(
                getattr(bundle.coverage, "multi_canonical_dates", []) or []
            ),
        },
        "data_quality_rollup": {
            "threshold_hours": bundle.data_quality_rollup.threshold_hours,
            "fresh_count": bundle.data_quality_rollup.fresh_count,
            "stale_pull_count": bundle.data_quality_rollup.stale_pull_count,
            "retrospective_manual_count":
                bundle.data_quality_rollup.retrospective_manual_count,
            "unclassifiable_count":
                bundle.data_quality_rollup.unclassifiable_count,
        },
        "deferred_domains": list(bundle.deferred_domains),
        "sections": [_section_to_json(s) for s in bundle.sections],
        "claim_cards": _load_claim_cards(
            conn,
            iso_week=bundle.iso_week,
            user_id=bundle.user_id,
            include_history=include_history,
        ),
        "include_history": include_history,
    }
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def _section_to_json(section: WeeklyProseSection) -> dict[str, Any]:
    return {
        "section_id": section.section_id,
        "title": section.title,
        "atoms": [_atom_to_json(a) for a in section.atoms],
    }


def _atom_to_json(atom: WeeklyAtom) -> dict[str, Any]:
    return {
        "atom_id": atom.atom_id,
        "atom_text": atom.atom_text,
        "atom_type": atom.atom_type,
        "derivation_path": atom.derivation_path,
        "domain": atom.domain,
        "locator_set": list(atom.locator_set),
        "audit_refs": dict(atom.audit_refs),
    }


def _load_claim_cards(
    conn: Optional[sqlite3.Connection],
    *,
    iso_week: str,
    user_id: str,
    include_history: bool,
) -> list[dict[str, Any]]:
    """Load weekly_claim_card rows for the JSON output."""

    if conn is None:
        return []
    try:
        if include_history:
            return load_full_history_for_week(
                conn, user_id=user_id, iso_week=iso_week,
            )
        return load_canonical_latest_for_week(
            conn, user_id=user_id, iso_week=iso_week,
        )
    except sqlite3.OperationalError:
        return []
