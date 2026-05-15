# Synthesis Feasibility Prototype (Phase 0.5)

**Disposable.** Not part of the production package. Lives under `reporting/experiments/` so it doesn't contaminate `src/`.

## Purpose

De-risk the central architectural bet of the rebuild plan: that a single synthesis skill can reason coherently across multiple per-domain proposals, applying mechanical X-rules while still exercising judgment where rules don't cover. If this prototype's results are marginal, the rebuild stops here.

## What's in scope

- **2 domains**: recovery + running. Stress/sleep/strength/nutrition live only as stub fields where needed.
- **3 X-rules**: X1a (soften), X3b (block), X6a (soften). Chosen to cover soften + block tiers and to trigger from three different signal sources (sleep debt band, ACWR ratio, body battery).
- **8 scenarios**: baseline, single-rule fires (×3), interactions (×2), partial-coverage edge, yesterday-context case.
- **1 skill markdown**: `skill_synthesis.md`. Target <300 lines.

## How a scenario runs

```
scenario_NN.json
   │
   ▼
xrules.py evaluate(snapshot, proposals)  →  x_rule_firings[]
   │
   ▼
(agent reads skill_synthesis.md + bundle)  →  N final recommendations
   │
   ▼
outputs/scenario_NN_result.json
   │
   ▼
manual rubric score (3-point: action / rationale / uncertainty)
```

## Decision rule (from plan §Phase 0.5)

| Scenario pass rate | Prompt size | Verdict |
|---|---|---|
| ≥75% score 2/3+ | <300 lines | Commit to Phase 1 as planned |
| 50–75% | — | Commit to Phase 1 with synthesis-redesign risk |
| <50% OR prompt >500 lines | — | **Stop the rebuild.** Rethink architecture. |

## Layout

```
synthesis_prototype/
├── README.md                # this file
├── xrules.py                # X-rule evaluators + XRuleFiring dataclass
├── skill_synthesis.md       # the synthesis skill (prototype)
├── scenarios/
│   ├── 01_baseline_no_rules.json
│   ├── 02_x1a_sleep_debt_moderate.json
│   ├── 03_x3b_acwr_spike.json
│   ├── 04_x6a_body_battery_low.json
│   ├── 05_x1a_x6a_interaction.json
│   ├── 06_x3b_x6a_interaction.json
│   ├── 07_sparse_coverage_degrade.json
│   └── 08_yesterday_heavy_legs_context.json
├── outputs/
│   └── scenario_NN_result.json   # one per scenario after skill invocation
└── findings.md              # written at Phase 0.5 completion with verdict
```

Scenario JSON shape:

```json
{
  "scenario_id": "01_baseline_no_rules",
  "description": "...",
  "snapshot": { ... stubbed per-domain state ... },
  "proposals": [
    {"domain": "recovery", ...},
    {"domain": "running", ...}
  ],
  "expected_firings": [ ... list of XRuleFiring dicts ... ],
  "expected_behavior": {
    "recovery": {"action": "...", "notes": "..."},
    "running": {"action": "...", "notes": "..."}
  },
  "rubric_targets": {
    "action_correctness": "exact | functional_equivalent | drift | wrong",
    "rationale_quality": "cites firings explicitly | implicit | missing",
    "uncertainty_calibration": "all tokens present | partial | over-confident"
  }
}
```
