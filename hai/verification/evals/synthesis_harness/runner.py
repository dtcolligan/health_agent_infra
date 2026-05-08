"""W42 synthesis-skill scoring runner.

Scores a candidate synthesis-skill output (produced by
``daily-plan-synthesis``) against a fixture scenario. The scoring is
deterministic — no LLM judge — and answers four invariants:

  1. **Every Phase A firing is cited or intentionally summarised.**
     For every ``rule_id`` in ``phase_a_firings``, either the rule_id
     itself appears verbatim in the synthesis output, OR the
     ``expected.firing_summaries[rule_id]`` token appears (lets a
     scenario allow grouped narration like "two soften firings" rather
     than enumerated rule ids).
  2. **No invented X-rule.** Every rule_id-shaped token in the
     synthesis output must correspond to a firing that exists in the
     bundle.
  3. **No invented band.** Every band token (e.g. ``sleep_debt_band``)
     used in the synthesis output must correspond to a band actually
     present in the bundle's snapshot.<domain>.classified_state.
  4. **No action mutation claimed by prose.** The synthesis output may
     not assert an action different from what the runtime committed.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


HARNESS_ROOT = Path(__file__).resolve().parent
SCENARIOS_ROOT = HARNESS_ROOT / "scenarios"
RUBRICS_ROOT = HARNESS_ROOT / "rubrics"


@dataclass
class AxisResult:
    verdict: str   # "pass" | "fail" | "skipped"
    detail: str = ""


@dataclass
class SynthesisScore:
    scenario_id: str
    correctness: dict[str, AxisResult]

    @property
    def correctness_passed(self) -> bool:
        return all(r.verdict != "fail" for r in self.correctness.values())


def load_scenarios() -> list[dict[str, Any]]:
    if not SCENARIOS_ROOT.exists():
        return []
    out = []
    for path in sorted(SCENARIOS_ROOT.glob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


_RULE_ID_PATTERN = re.compile(r"\b[Xx](\d+[ab]?)\b")
_BAND_PATTERN = re.compile(r"\b(\w+_band)\b")


def _cited_rule_ids(text: str) -> set[str]:
    return {m.group(0).upper() for m in _RULE_ID_PATTERN.finditer(text)}


def _cited_bands(text: str) -> set[str]:
    return {m.group(1) for m in _BAND_PATTERN.finditer(text)}


def score_synthesis_output(
    scenario: dict[str, Any],
    synthesis_output: dict[str, Any],
) -> SynthesisScore:
    """Apply the W42 rubric to ``synthesis_output``.

    ``synthesis_output`` is the dict the synthesis skill returns —
    typically containing ``per_domain_rationale``,
    ``joint_narration``, and ``per_domain_uncertainty``. The scorer
    treats every string field as candidate prose and checks the four
    invariants against the scenario's bundle.
    """

    bundle = scenario["bundle"]
    expected = scenario.get("expected") or {}
    phase_a_firings = bundle.get("phase_a_firings") or []
    proposals = bundle.get("proposals") or []
    snapshot = bundle.get("snapshot") or {}

    # Concatenate every prose field into one text blob for token checks.
    prose_blobs: list[str] = []
    for value in synthesis_output.values():
        if isinstance(value, str):
            prose_blobs.append(value)
        elif isinstance(value, dict):
            for v in value.values():
                if isinstance(v, str):
                    prose_blobs.append(v)
        elif isinstance(value, list):
            for v in value:
                if isinstance(v, str):
                    prose_blobs.append(v)
    prose = "\n".join(prose_blobs)

    correctness: dict[str, AxisResult] = {}

    # 1. Every Phase A firing cited or summarised.
    expected_firings = {f["rule_id"] for f in phase_a_firings}
    summary_tokens = (expected.get("firing_summaries") or {})
    missing_firings: list[str] = []
    for rule_id in expected_firings:
        if rule_id.upper() in prose.upper():
            continue
        token = summary_tokens.get(rule_id)
        if token and token in prose:
            continue
        missing_firings.append(rule_id)
    correctness["all_firings_cited_or_summarised"] = AxisResult(
        verdict="pass" if not missing_firings else "fail",
        detail=(
            "" if not missing_firings
            else f"missing in prose: {sorted(missing_firings)}"
        ),
    )

    # 2. No invented X-rule.
    cited_rules = _cited_rule_ids(prose)
    invented_rules = sorted(
        rid for rid in cited_rules
        if rid.upper() not in {f.upper() for f in expected_firings}
    )
    correctness["no_invented_xrule"] = AxisResult(
        verdict="pass" if not invented_rules else "fail",
        detail=(
            "" if not invented_rules
            else f"prose references rule(s) not in bundle: {invented_rules}"
        ),
    )

    # 3. No invented band.
    bundle_bands: set[str] = set()
    for domain_name, domain_block in snapshot.items():
        if not isinstance(domain_block, dict):
            continue
        classified = domain_block.get("classified_state") or {}
        for k in classified.keys():
            if k.endswith("_band"):
                bundle_bands.add(k)
    cited_bands = _cited_bands(prose)
    invented_bands = sorted(b for b in cited_bands if b not in bundle_bands)
    correctness["no_invented_band"] = AxisResult(
        verdict="pass" if not invented_bands else "fail",
        detail=(
            "" if not invented_bands
            else f"prose references band(s) not in snapshot: {invented_bands}"
        ),
    )

    # 4. No action mutation claimed by prose.
    proposal_actions = {
        p["domain"]: p.get("draft_action") or p.get("action")
        for p in proposals
    }
    output_actions = (synthesis_output.get("per_domain_action") or {})
    mismatched: list[str] = []
    for domain_name, expected_action in proposal_actions.items():
        if domain_name in output_actions:
            if output_actions[domain_name] != expected_action:
                mismatched.append(
                    f"{domain_name}: expected {expected_action!r}, "
                    f"got {output_actions[domain_name]!r}"
                )
    correctness["no_action_mutation_by_prose"] = AxisResult(
        verdict="pass" if not mismatched else "fail",
        detail="" if not mismatched else "; ".join(mismatched),
    )

    return SynthesisScore(
        scenario_id=scenario["scenario_id"],
        correctness=correctness,
    )
