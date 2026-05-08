"""Sleep-domain mechanical policy gates.

Phase 3 step 3. Mirrors the recovery / running R-rule contract: a
single entry point ``evaluate_sleep_policy`` returns a frozen
``SleepPolicyResult`` carrying every decision (allow / soften / block /
escalate) along with any ``forced_action`` or ``capped_confidence`` the
sleep-quality skill must honour.

Three rules in v1:

  - ``require_min_coverage`` (block + forced
    ``defer_decision_insufficient_signal``) when
    ``coverage_band == 'insufficient'``.
  - ``no_high_confidence_on_sparse_signal`` (soften + cap to
    ``moderate``) when ``coverage_band == 'sparse'``.
  - ``chronic_deprivation_escalation`` (escalate + forced
    ``sleep_debt_repayment_day``) when the trailing 7-night window has
    >= r_chronic_deprivation_nights nights under
    r_chronic_deprivation_hours. Sleep's v1 action enum has no
    ``escalate_for_user_review`` — the remedial action
    ``sleep_debt_repayment_day`` is forced, and the severity is
    recorded in the ``escalate`` decision tier on the audit record.

R-rules are domain-internal and fire deterministically off the sleep
classifier output + the sleep signals dict. Cross-domain X-rules (X1
sleep → training) live in the synthesis layer and are evaluated
separately; an R-rule that overlaps with an X-rule (e.g. chronic
deprivation + X1b elevated debt) is intentional — the R-rule gives the
domain its own forced action even if synthesis is not run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from health_agent_infra.core.config import load_thresholds
from health_agent_infra.domains.sleep.classify import ClassifiedSleepState


DecisionTier = str  # "allow" | "soften" | "block" | "escalate"


@dataclass(frozen=True)
class PolicyDecision:
    rule_id: str
    decision: DecisionTier
    note: str


@dataclass(frozen=True)
class SleepPolicyResult:
    policy_decisions: tuple[PolicyDecision, ...]
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None
    # v0.2.0 W-PROV-2: source-row locator(s) for this policy result.
    # Always-emit baseline → 1 locator on today's
    # accepted_sleep_state_daily row. Chronic-deprivation firing adds
    # one column-level locator (column="sleep_hours") per night in the
    # trailing window, mirroring recovery R6's spike-window emission.
    evidence_locators: Optional[tuple[dict[str, Any], ...]] = None


# ---------------------------------------------------------------------------
# Rule evaluators
# ---------------------------------------------------------------------------

def _r_coverage_gate(
    classified: ClassifiedSleepState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "insufficient":
        return (
            PolicyDecision(
                rule_id="require_min_coverage",
                decision="block",
                note="coverage=insufficient; required sleep inputs missing",
            ),
            "defer_decision_insufficient_signal",
        )
    return (
        PolicyDecision(
            rule_id="require_min_coverage",
            decision="allow",
            note=f"coverage={classified.coverage_band}; required inputs present",
        ),
        None,
    )


def _r_sparse_confidence_cap(
    classified: ClassifiedSleepState,
) -> tuple[PolicyDecision, Optional[str]]:
    if classified.coverage_band == "sparse":
        tokens_str = ",".join(classified.uncertainty) if classified.uncertainty else ""
        return (
            PolicyDecision(
                rule_id="no_high_confidence_on_sparse_signal",
                decision="soften",
                note=f"capped confidence to moderate on sparse signal ({tokens_str})",
            ),
            "moderate",
        )
    return (
        PolicyDecision(
            rule_id="no_high_confidence_on_sparse_signal",
            decision="allow",
            note=f"coverage={classified.coverage_band}; no cap required",
        ),
        None,
    )


def _r_chronic_deprivation(
    sleep_signals: dict[str, Any],
    t: dict[str, Any],
) -> tuple[PolicyDecision, Optional[str], Optional[dict[str, Any]]]:
    """Count nights in the trailing 7-night window under the deprivation
    threshold. Fires when >= ``r_chronic_deprivation_nights``.

    The caller supplies ``sleep_history_hours_last_7`` as a list of
    floats (most-recent 7 nights of ``sleep_hours``, including today
    if available). Absent / None entries are treated as non-deprivation
    nights — the R1 coverage gate is the authoritative signal for
    missing-data escalation; this rule only counts explicit shortfalls.
    """

    from health_agent_infra.core.config import coerce_float, coerce_int  # noqa: PLC0415

    history = sleep_signals.get("sleep_history_hours_last_7") or []
    threshold_hours = coerce_float(
        t["policy"]["sleep"]["r_chronic_deprivation_hours"],
        name="policy.sleep.r_chronic_deprivation_hours",
    )
    threshold_nights = coerce_int(
        t["policy"]["sleep"]["r_chronic_deprivation_nights"],
        name="policy.sleep.r_chronic_deprivation_nights",
    )

    short_nights = sum(
        1 for h in history if h is not None and h < threshold_hours
    )

    if short_nights >= threshold_nights:
        detail = {
            "reason_token": "chronic_deprivation_detected",
            "short_nights": short_nights,
            "window_nights": len(history),
            "threshold_hours": threshold_hours,
            "threshold_nights": threshold_nights,
        }
        return (
            PolicyDecision(
                rule_id="chronic_deprivation_escalation",
                decision="escalate",
                note=(
                    f"short_nights={short_nights} >= threshold={threshold_nights} "
                    f"(< {threshold_hours}h in last {len(history)} nights)"
                ),
            ),
            "sleep_debt_repayment_day",
            detail,
        )

    return (
        PolicyDecision(
            rule_id="chronic_deprivation_escalation",
            decision="allow",
            note=(
                f"short_nights={short_nights} below threshold={threshold_nights} "
                f"(history_len={len(history)})"
            ),
        ),
        None,
        None,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def evaluate_sleep_policy(
    classified: ClassifiedSleepState,
    sleep_signals: dict[str, Any],
    thresholds: Optional[dict[str, Any]] = None,
    *,
    for_date_iso: Optional[str] = None,
    user_id: Optional[str] = None,
    sleep_state_versions: Optional[dict[str, str]] = None,
) -> SleepPolicyResult:
    """Apply sleep R-rules to a classified sleep state.

    Returns every decision along with any forced_action or
    capped_confidence the skill must honour. Rule ordering:
    R-coverage short-circuits action selection; R-chronic-deprivation
    overrides even if R-coverage allows; R-sparse caps confidence
    independently of action.

    v0.2.0 W-PROV-2: when ``for_date_iso`` / ``user_id`` /
    ``sleep_state_versions`` are provided, the result carries an
    always-emit row-level locator citing today's
    ``accepted_sleep_state_daily``. When R-chronic-deprivation
    fires, additional column-level locators citing
    ``accepted_sleep_state_daily.sleep_hours`` are appended for each
    night in the trailing window present in the version map (mirrors
    recovery R6's spike-window emission). ``sleep_state_versions`` is
    ``{as_of_date_iso: row_version_iso}``; the trailing window length
    matches the ``sleep_history_hours_last_7`` signal length. Args are
    optional to preserve the legacy 3-arg signature.
    """

    t = thresholds if thresholds is not None else load_thresholds()
    decisions: list[PolicyDecision] = []
    forced_action: Optional[str] = None
    forced_action_detail: Optional[dict[str, Any]] = None
    capped_confidence: Optional[str] = None

    cov_dec, cov_forced = _r_coverage_gate(classified)
    decisions.append(cov_dec)
    if cov_forced is not None:
        forced_action = cov_forced

    cap_dec, cap_value = _r_sparse_confidence_cap(classified)
    decisions.append(cap_dec)
    if cap_value is not None:
        capped_confidence = cap_value

    chron_dec, chron_forced, chron_detail = _r_chronic_deprivation(
        sleep_signals, t,
    )
    decisions.append(chron_dec)
    if chron_forced is not None:
        # Chronic deprivation is the louder signal — mirrors recovery
        # R6 and running R-acwr-spike precedence — so it overrides any
        # R-coverage defer that may have fired earlier.
        forced_action = chron_forced
        forced_action_detail = chron_detail

    evidence_locators = _build_sleep_locators(
        for_date_iso=for_date_iso,
        user_id=user_id,
        sleep_state_versions=sleep_state_versions,
        chronic_deprivation_fired=(
            forced_action_detail is not None
            and forced_action_detail.get("reason_token")
            == "chronic_deprivation_detected"
        ),
        window_nights=(
            forced_action_detail.get("window_nights")
            if forced_action_detail is not None
            else None
        ),
    )

    return SleepPolicyResult(
        policy_decisions=tuple(decisions),
        forced_action=forced_action,
        forced_action_detail=forced_action_detail,
        capped_confidence=capped_confidence,
        evidence_locators=evidence_locators,
    )


def _build_sleep_locators(
    *,
    for_date_iso: Optional[str],
    user_id: Optional[str],
    sleep_state_versions: Optional[dict[str, str]],
    chronic_deprivation_fired: bool,
    window_nights: Optional[int],
) -> Optional[tuple[dict[str, Any], ...]]:
    """v0.2.0 W-PROV-2 hybrid emission for sleep.

    Always-emit: 1 row-level locator on today's
    ``accepted_sleep_state_daily`` when the trio of identity args is
    present. Spike-emit (additional): on chronic-deprivation firing,
    append one column-level locator per night in the trailing window
    present in ``sleep_state_versions`` (column=``sleep_hours``).
    Days missing from the map are silently skipped (the safe-default
    that mirrors ``_r6_spike_locators``).
    """

    if for_date_iso is None or user_id is None:
        return None
    if not sleep_state_versions:
        return None

    today_version = sleep_state_versions.get(for_date_iso)
    out: list[dict[str, Any]] = []
    if today_version is not None:
        out.append({
            "table": "accepted_sleep_state_daily",
            "pk": {"as_of_date": for_date_iso, "user_id": user_id},
            "row_version": today_version,
        })

    if chronic_deprivation_fired and window_nights:
        from datetime import date, timedelta
        end_date = date.fromisoformat(for_date_iso)
        for offset in range(int(window_nights)):
            day = end_date - timedelta(days=offset)
            day_iso = day.isoformat()
            version = sleep_state_versions.get(day_iso)
            if version is None:
                continue
            out.append({
                "table": "accepted_sleep_state_daily",
                "pk": {"as_of_date": day_iso, "user_id": user_id},
                "column": "sleep_hours",
                "row_version": version,
            })

    return tuple(out) if out else None
