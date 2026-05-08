"""Phase 0.5 synthesis prototype: X-rule evaluators.

Disposable. Not integrated with the main package. Purpose is to generate
mechanical XRuleFiring records that the synthesis skill consumes as
pre-computed context.

Three rules covering soften + block tiers from three distinct signal sources:
  X1a  (soften) sleep_debt_band=moderate + hard run proposed -> zone_2
  X3b  (block)  acwr_ratio >= 1.5 + any hard session        -> escalate
  X6a  (soften) body_battery_end_of_day < 30                -> moderate-cap all
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


HARD_ACTIONS = {"intervals", "tempo", "long_run", "race", "hard", "heavy_lift"}


@dataclass
class XRuleFiring:
    rule_id: str
    tier: str                   # "soften" | "block" | "cap_confidence" | "adjust" | "restructure"
    affected_domains: list[str]
    trigger: str
    recommended_mutation: dict[str, Any]
    source_signals: dict[str, Any]


def _hard_session_proposals(proposals: list[dict]) -> list[dict]:
    return [p for p in proposals if p.get("planned_intensity") in HARD_ACTIONS
            or p.get("planned_action") in HARD_ACTIONS]


def evaluate_x1a(snapshot: dict, proposals: list[dict]) -> list[XRuleFiring]:
    """sleep_debt_band=moderate AND hard running session proposed -> soften to zone 2."""
    sleep_debt = (snapshot.get("recovery", {}).get("classified", {})
                  .get("sleep_debt_band"))
    if sleep_debt != "moderate":
        return []
    firings: list[XRuleFiring] = []
    for p in proposals:
        if p.get("domain") != "running":
            continue
        intensity = p.get("planned_intensity")
        if intensity not in {"intervals", "tempo", "long_run", "race"}:
            continue
        firings.append(XRuleFiring(
            rule_id="X1a",
            tier="soften",
            affected_domains=["running"],
            trigger=f"sleep_debt_band=moderate with planned_intensity={intensity}",
            recommended_mutation={
                "action": "downgrade_hard_session_to_zone_2",
                "target_intensity": "zone_2",
                "target_duration_minutes": 45,
            },
            source_signals={
                "sleep_debt_band": "moderate",
                "proposed_intensity": intensity,
            },
        ))
    return firings


def evaluate_x3b(snapshot: dict, proposals: list[dict]) -> list[XRuleFiring]:
    """acwr_ratio >= 1.5 AND any hard session across any domain -> escalate."""
    acwr = (snapshot.get("recovery", {}).get("today", {}) or {}).get("acwr_ratio")
    if acwr is None or acwr < 1.5:
        return []
    firings: list[XRuleFiring] = []
    for p in proposals:
        intensity = p.get("planned_intensity") or p.get("planned_action")
        if intensity in HARD_ACTIONS:
            firings.append(XRuleFiring(
                rule_id="X3b",
                tier="block",
                affected_domains=[p["domain"]],
                trigger=f"acwr_ratio={acwr:.2f} >= 1.5 with hard {p['domain']} session proposed",
                recommended_mutation={
                    "action": "escalate_for_user_review",
                    "reason_token": "acwr_elevated_hard_session",
                    "consecutive_check_required": True,
                },
                source_signals={
                    "acwr_ratio": acwr,
                    "proposed_intensity": intensity,
                    "domain": p["domain"],
                },
            ))
    return firings


def evaluate_x6a(snapshot: dict, proposals: list[dict]) -> list[XRuleFiring]:
    """body_battery_end_of_day < 30 -> soften all proposals to moderate intensity."""
    today = snapshot.get("recovery", {}).get("today") or {}
    bb = today.get("body_battery_end_of_day")
    if bb is None or bb >= 30:
        return []
    affected = [p["domain"] for p in proposals]
    return [XRuleFiring(
        rule_id="X6a",
        tier="soften",
        affected_domains=affected,
        trigger=f"body_battery_end_of_day={bb} < 30 (depleted reserve)",
        recommended_mutation={
            "target_intensity": "moderate",
            "reason_token": "depleted_reserve_soften_all",
        },
        source_signals={"body_battery_end_of_day": bb},
    )]


def evaluate_all(snapshot: dict, proposals: list[dict]) -> list[XRuleFiring]:
    firings: list[XRuleFiring] = []
    firings.extend(evaluate_x1a(snapshot, proposals))
    firings.extend(evaluate_x3b(snapshot, proposals))
    firings.extend(evaluate_x6a(snapshot, proposals))
    return firings


def _main() -> int:
    if len(sys.argv) != 2:
        print("usage: python xrules.py <scenario.json>", file=sys.stderr)
        return 2
    scenario = json.loads(Path(sys.argv[1]).read_text())
    firings = evaluate_all(scenario["snapshot"], scenario["proposals"])
    print(json.dumps([asdict(f) for f in firings], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
