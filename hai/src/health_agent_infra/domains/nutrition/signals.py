"""Nutrition-domain signal derivation — snapshot-row → classifier input.

Phase 5 step 2, under the Phase 2.5 retrieval-gate outcome (macros-only).
Mirrors the structure of ``domains.strength.signals`` and
``domains.sleep.signals``: a single entry point
:func:`derive_nutrition_signals` that packages the snapshot's
``nutrition.today`` row (plus an optional goal_domain) into the dict
that :func:`classify_nutrition_state` consumes.

Macros-only scope — no meal-log aggregation, no cross-derivation
blending. The signal bundle is therefore intentionally small; the
separation from ``classify`` exists so future meal-level work adds new
derived signals here without churning the classifier contract.
"""

from __future__ import annotations

from typing import Any, Optional


def derive_nutrition_signals(
    *,
    nutrition_today: Optional[dict[str, Any]],
    goal_domain: Optional[str] = None,
    is_partial_day: Optional[bool] = None,
    target_status: Optional[str] = None,
) -> dict[str, Any]:
    """Package the snapshot's nutrition.today row into a classifier-ready dict.

    Args:
        nutrition_today: the accepted_nutrition_state_daily row dict for
            ``(as_of_date, user_id)`` as returned under
            ``snapshot.nutrition.today``, or ``None`` when no row exists.
        goal_domain: the user's active goal domain (reserved for post-v1
            goal-aware targets; ignored in v1 classify).
        is_partial_day: v0.1.15 W-A signal — True iff the call is for
            today AND the local time is before the W-A cutoff AND fewer
            than the expected number of meals have been logged. Used by
            W-D arm-1 in classify to suppress when paired with no target.
            ``None`` is the backwards-compat shape: existing call sites
            that haven't been wired to W-A yet pass ``None`` and the
            classifier behaves as it did pre-W-D.
        target_status: v0.1.15 W-A signal — three-valued enum
            ``"present" | "absent" | "unavailable"`` reading the
            existing `target` table for nutrition macros. W-D arm-1
            fires when ``is_partial_day=True`` AND ``target_status in
            ("absent", "unavailable")``. ``None`` is backwards-compat.

    Returns:
        dict with keys ``today_row`` + ``goal_domain`` (+ optional
        ``is_partial_day`` + ``target_status``). Passing extra keys
        through preserves the invariant that the skill reads the same
        bundle the classifier consumed.
    """

    bundle: dict[str, Any] = {
        "today_row": dict(nutrition_today) if nutrition_today is not None else None,
        "goal_domain": goal_domain,
    }
    if is_partial_day is not None:
        bundle["is_partial_day"] = bool(is_partial_day)
    if target_status is not None:
        bundle["target_status"] = target_status
    return bundle
