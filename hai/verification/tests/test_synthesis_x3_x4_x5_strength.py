"""Phase 4 step 5 — synthesis X-rules wire to strength data.

Contracts pinned:

  1. X3a/X3b already fired on running; they now fire equivalently on
     hard strength proposals, using the strength registry's default
     downgrade action ``downgrade_to_moderate_load``.
  2. X4 softens hard running proposals when yesterday's
     ``strength.history[-1].volume_by_muscle_group_json`` has any of
     ``{quads, hamstrings, glutes}`` at or above the heavy threshold.
     No firing if the heavy groups are upper-body only.
  3. X5 softens hard strength proposals (action =
     ``downgrade_to_technique_or_accessory``) when yesterday's
     ``running.history[-1]`` had either ``vigorous_intensity_min`` at
     threshold or ``total_duration_s`` at the long-run threshold.
  4. End-to-end: snapshot + proposals go through
     ``evaluate_phase_a`` + ``apply_phase_a`` and the mutated draft
     reflects the expected action + reason_token.
"""

from __future__ import annotations

import json
from copy import deepcopy
from typing import Any

import pytest

from health_agent_infra.core.config import DEFAULT_THRESHOLDS
from health_agent_infra.core.synthesis_policy import (
    apply_phase_a,
    evaluate_phase_a,
    evaluate_x3a,
    evaluate_x3b,
    evaluate_x4,
    evaluate_x5,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _thresholds(**overrides: Any) -> dict[str, Any]:
    cfg = deepcopy(DEFAULT_THRESHOLDS)
    for path, value in overrides.items():
        keys = path.split(".")
        cur = cfg
        for k in keys[:-1]:
            cur = cur.setdefault(k, {})
        cur[keys[-1]] = value
    return cfg


def _snapshot(
    *,
    acwr_ratio: float | None = None,
    yesterday_strength_volume_by_group: dict[str, float] | None = None,
    yesterday_running: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recovery = {"today": {}}
    if acwr_ratio is not None:
        recovery["today"]["acwr_ratio"] = acwr_ratio

    strength = {"history": []}
    if yesterday_strength_volume_by_group is not None:
        strength["history"] = [{
            "as_of_date": "2026-04-17",
            "volume_by_muscle_group_json": json.dumps(
                yesterday_strength_volume_by_group
            ),
        }]

    running = {"history": []}
    if yesterday_running is not None:
        running["history"] = [yesterday_running]

    return {
        "recovery": recovery,
        "strength": strength,
        "running": running,
    }


def _strength_hard_proposal(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": "strength_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_strength_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "strength",
        "action": "proceed_with_planned_session",
        "action_detail": None,
        "rationale": ["recent_volume_band=moderate"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


def _running_hard_proposal(**overrides: Any) -> dict[str, Any]:
    base = {
        "schema_version": "running_proposal.v1",
        "proposal_id": "prop_2026-04-18_u_local_1_running_01",
        "user_id": "u_local_1",
        "for_date": "2026-04-18",
        "domain": "running",
        "action": "proceed_with_planned_run",
        "action_detail": None,
        "rationale": ["weekly_mileage_trend=moderate"],
        "confidence": "high",
        "uncertainty": [],
        "policy_decisions": [{"rule_id": "r1", "decision": "allow", "note": "full"}],
        "bounded": True,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# X3a/X3b now target strength
# ---------------------------------------------------------------------------


def test_x3a_fires_on_hard_strength_proposal():
    firings = evaluate_x3a(
        _snapshot(acwr_ratio=1.35),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X3a"
    assert f.tier == "soften"
    assert f.affected_domain == "strength"
    assert f.recommended_mutation["action"] == "downgrade_to_moderate_load"


def test_x3b_escalates_hard_strength_proposal():
    firings = evaluate_x3b(
        _snapshot(acwr_ratio=1.6),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X3b"
    assert f.tier == "block"
    assert f.affected_domain == "strength"
    assert f.recommended_mutation["action"] == "escalate_for_user_review"


def test_x3a_skips_already_softened_strength_proposal():
    prop = _strength_hard_proposal(action="downgrade_to_moderate_load")
    firings = evaluate_x3a(
        _snapshot(acwr_ratio=1.35),
        [prop],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X4 — yesterday's heavy lower body caps running
# ---------------------------------------------------------------------------


def test_x4_fires_on_heavy_quads_yesterday_with_hard_running():
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"quads": 2500.0, "chest": 500.0},
        ),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X4"
    assert f.tier == "soften"
    assert f.affected_domain == "running"
    assert f.recommended_mutation["action"] == "downgrade_to_easy_aerobic"
    assert f.recommended_mutation["action_detail"]["reason_token"] == "x4_heavy_lower_body_yesterday"
    assert "quads" in f.recommended_mutation["action_detail"]["heavy_groups"]


def test_x4_does_not_fire_on_upper_body_only_yesterday():
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"chest": 3000.0, "back": 2500.0},
        ),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x4_does_not_fire_without_running_proposal():
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"quads": 2500.0},
        ),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x4_does_not_fire_when_no_strength_history():
    firings = evaluate_x4(
        _snapshot(yesterday_strength_volume_by_group=None),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x4_does_not_fire_below_threshold():
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"quads": 1500.0},
        ),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x4_threshold_is_configurable():
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"quads": 1000.0},
        ),
        [_running_hard_proposal()],
        _thresholds(**{
            "synthesis.x_rules.x4": {"heavy_lower_body_min_volume": 500.0},
        }),
    )
    assert len(firings) == 1


def test_x4_fires_on_hamstrings_or_glutes_too():
    for group in ("hamstrings", "glutes"):
        firings = evaluate_x4(
            _snapshot(
                yesterday_strength_volume_by_group={group: 3000.0},
            ),
            [_running_hard_proposal()],
            _thresholds(),
        )
        assert len(firings) == 1, group


def test_x4_skips_already_softened_running_proposal():
    prop = _running_hard_proposal(action="downgrade_to_easy_aerobic")
    firings = evaluate_x4(
        _snapshot(
            yesterday_strength_volume_by_group={"quads": 3000.0},
        ),
        [prop],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# X5 — yesterday's long run / hard intervals caps lower-body strength
# ---------------------------------------------------------------------------


def test_x5_fires_on_hard_intervals_yesterday_with_hard_strength():
    firings = evaluate_x5(
        _snapshot(
            yesterday_running={
                "vigorous_intensity_min": 25,
                "total_duration_s": 3000,
            },
        ),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.rule_id == "X5"
    assert f.tier == "soften"
    assert f.affected_domain == "strength"
    assert f.recommended_mutation["action"] == "downgrade_to_technique_or_accessory"
    assert f.recommended_mutation["action_detail"]["trigger"] == "hard_intervals"


def test_x5_fires_on_long_run_yesterday():
    firings = evaluate_x5(
        _snapshot(
            yesterday_running={
                "vigorous_intensity_min": 5,
                "total_duration_s": 5400,  # 90 min
            },
        ),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert len(firings) == 1
    f = firings[0]
    assert f.recommended_mutation["action_detail"]["trigger"] == "long_run"


def test_x5_does_not_fire_on_easy_short_run_yesterday():
    firings = evaluate_x5(
        _snapshot(
            yesterday_running={
                "vigorous_intensity_min": 5,
                "total_duration_s": 1800,
            },
        ),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x5_does_not_fire_without_strength_proposal():
    firings = evaluate_x5(
        _snapshot(
            yesterday_running={
                "vigorous_intensity_min": 30,
                "total_duration_s": 6000,
            },
        ),
        [_running_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x5_does_not_fire_when_no_running_history():
    firings = evaluate_x5(
        _snapshot(yesterday_running=None),
        [_strength_hard_proposal()],
        _thresholds(),
    )
    assert firings == []


def test_x5_skips_already_softened_strength_proposal():
    prop = _strength_hard_proposal(action="downgrade_to_moderate_load")
    firings = evaluate_x5(
        _snapshot(
            yesterday_running={
                "vigorous_intensity_min": 30,
                "total_duration_s": 6000,
            },
        ),
        [prop],
        _thresholds(),
    )
    assert firings == []


# ---------------------------------------------------------------------------
# End-to-end: evaluate_phase_a + apply_phase_a on a strength proposal
# ---------------------------------------------------------------------------


def test_phase_a_end_to_end_strength_proposal_downgraded_by_x5():
    """Scenario: user went for a 90-minute long run yesterday and the
    strength proposal is a hard session. Synthesis should flip the
    strength proposal to ``downgrade_to_technique_or_accessory``
    with the X5 reason token and leave a firing on the audit list."""

    snapshot = _snapshot(
        yesterday_running={
            "vigorous_intensity_min": 10,
            "total_duration_s": 5400,
        },
    )
    proposals = [_strength_hard_proposal()]
    firings = evaluate_phase_a(snapshot, proposals, _thresholds())

    x5_firings = [f for f in firings if f.rule_id == "X5"]
    assert len(x5_firings) == 1

    mutated, fired_ids = apply_phase_a(proposals[0], firings)
    assert mutated["action"] == "downgrade_to_technique_or_accessory"
    assert mutated["action_detail"]["reason_token"] == "x5_endurance_fatigue_yesterday"
    assert "X5" in fired_ids


def test_phase_a_end_to_end_strength_proposal_escalated_by_x3b_over_x5():
    """Scenario: X3b (acwr≥1.5, block) + X5 (long run, soften) both
    fire on a hard strength proposal. Tier precedence gives X3b the
    action mutation; X5 is recorded-as-fired on the audit list but
    not applied."""

    snapshot = deepcopy(_snapshot(
        yesterday_running={"vigorous_intensity_min": 30, "total_duration_s": 6000},
    ))
    snapshot["recovery"]["today"]["acwr_ratio"] = 1.6

    proposals = [_strength_hard_proposal()]
    firings = evaluate_phase_a(snapshot, proposals, _thresholds())

    rule_ids = {f.rule_id for f in firings}
    assert {"X3b", "X5"} <= rule_ids

    mutated, fired_ids = apply_phase_a(proposals[0], firings)
    # X3b (block) wins over X5 (soften) for action mutation.
    assert mutated["action"] == "escalate_for_user_review"
    # Both rules are on the audit trail.
    assert "X3b" in fired_ids
    assert "X5" in fired_ids


def test_phase_a_mixed_bundle_running_softened_by_x4_strength_softened_by_x5():
    """Scenario: yesterday was leg day (heavy quads) AND yesterday
    was also a long run. Today's bundle has both a hard running and
    a hard strength proposal. X4 softens the running proposal; X5
    softens the strength proposal. Both independently."""

    snapshot = {
        "recovery": {"today": {}},
        "strength": {
            "history": [{
                "as_of_date": "2026-04-17",
                "volume_by_muscle_group_json": json.dumps({"quads": 3000.0}),
            }],
        },
        "running": {
            "history": [{
                "as_of_date": "2026-04-17",
                "vigorous_intensity_min": 30,
                "total_duration_s": 6000,
            }],
        },
    }
    proposals = [_running_hard_proposal(), _strength_hard_proposal()]
    firings = evaluate_phase_a(snapshot, proposals, _thresholds())

    x4 = [f for f in firings if f.rule_id == "X4"]
    x5 = [f for f in firings if f.rule_id == "X5"]
    assert len(x4) == 1
    assert len(x5) == 1

    running_mutated, _ = apply_phase_a(proposals[0], firings)
    strength_mutated, _ = apply_phase_a(proposals[1], firings)
    assert running_mutated["action"] == "downgrade_to_easy_aerobic"
    assert strength_mutated["action"] == "downgrade_to_technique_or_accessory"
