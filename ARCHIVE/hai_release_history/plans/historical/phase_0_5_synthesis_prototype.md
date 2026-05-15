# Phase 0.5 — Synthesis Feasibility Prototype Findings

- Date: 2026-04-17
- Agent: Claude Code (Opus 4.7, this session)
- Branch: `rebuild`
- Artifacts: `reporting/experiments/synthesis_prototype/`
- Status: **GO. Commit to Phase 1 as planned.**

## The decision up front

Plan §Phase 0.5 decision rule:

| Pass rate | Prompt size | Verdict |
|---|---|---|
| ≥75% score 2/3+ | <300 lines | Commit to Phase 1 |
| 50–75% | — | Commit with synthesis-redesign risk |
| <50% OR prompt >500 lines | — | Stop the rebuild |

Observed: **8/8 scenarios scored 3/3 on action correctness (100%). Skill markdown is 117 lines.** Both gates comfortably cleared.

**Verdict: GO.** Proceed to Phase 1 per the plan.

## What was built

- `xrules.py` — 138 lines of Python. Implements X1a (soften, sleep_debt → zone_2), X3b (block, acwr ≥ 1.5 → escalate), X6a (soften, body_battery < 30 → moderate cap). Plus an `XRuleFiring` dataclass and a CLI (`python xrules.py scenarios/<file>.json`) that emits JSON firings.
- `skill_synthesis.md` — 117 lines. Frontmatter + protocol (apply firings mechanically → reconcile via judgment → emit N recommendations) + invariants + conflict-resolution rules. Target was <300; delivered well under.
- 8 scenarios under `scenarios/`, covering: baseline no-firings, each rule solo, two soft×soft interaction, soft×block interaction, sparse-coverage edge, and an unmapped-context discipline test.
- 8 result JSONs under `outputs/`, one per scenario, with inline `_self_score` block.

## Results

| # | Scenario | Firings | Action | Rationale | Uncertainty | Total |
|---|---|---|---|---|---|---|
| 01 | baseline_no_rules | 0 | 3 | 3 | 3 | **9/9** |
| 02 | x1a_sleep_debt_moderate | 1 (soften) | 3 | 3 | 3 | **9/9** |
| 03 | x3b_acwr_spike | 1 (block) | 3 | 3 | 3 | **9/9** |
| 04 | x6a_body_battery_low | 1 (soften, multi-domain) | 3 | 3 | 3 | **9/9** |
| 05 | x1a_x6a_interaction | 2 (soften+soften on running) | 3 | 3 | 3 | **9/9** |
| 06 | x3b_x6a_interaction | 2 (block+soften, same domain) | 3 | 3 | 3 | **9/9** |
| 07 | sparse_coverage_degrade | 0 (intentional) | 3 | 3 | 3 | **9/9** |
| 08 | yesterday_heavy_legs_context | 0 (unmapped) | 3 | 3 | 3 | **9/9** |

All 8 action-correctness scores ≥ 2: **100% pass rate.** Aggregate score: **72/72.**

## Caveats — read before trusting these numbers

This was a tight, single-agent feedback loop. The biases are real:

1. **Single author throughout.** I wrote the skill, wrote the scenarios, reasoned as the agent, and scored the outputs. A real eval needs at least one of those four roles held by a different reasoner. The prototype answers "can the synthesis approach be executed at all?", not "does it generalize."
2. **Small scenario surface.** 8 scenarios sample a tiny fraction of the 3-rule × 2-domain × interaction × coverage × goal space. The Phase 6 eval harness needs 15–25 scenarios with random-seed diversity.
3. **Orphan firings not tested.** Invariant #1 ("no firing dropped") was never exercised — none of my scenarios produce a firing with no affected domain. Add at least one orphan-firing scenario in Phase 1 evals.
4. **`restructure` tier stubbed.** The skill handles it by emitting `escalate_for_user_review` with `restructure_tier_not_implemented`. Fine for the prototype; non-trivial to generalize. X8 was correctly demoted in the revised plan; this confirms it.
5. **Banned-token invariant (R2 analogue) not tested.** No scenario tried to inject `diagnosis` or `illness` into a rationale. Add negative-path scenarios in Phase 1.
6. **The agent reasoner had author context.** I wrote the skill 30 minutes before reasoning through it. A fresh agent encountering the skill for the first time might struggle with the "joint:" vs "synthesis:" prefix convention or the block>soften precedence. Mitigate by re-testing at Phase 1 boundary with a different session.

**Net effect**: the 100% pass rate overstates prototype quality. The honest claim is: **the synthesis approach is tractable enough that an agent can execute it without visible confusion.** That's the floor the decision rule asks about, not the ceiling.

## What the prototype exposed that's useful for Phase 1

1. **Tier precedence (block > soften > cap_confidence > adjust) is cleanly expressible** in the skill. The rule was unambiguous in all 6 scenarios that had firings.
2. **Conservative-mutation resolution for same-tier conflicts** (scenario 05: X1a zone_2 vs X6a moderate both on running) was straightforward. The skill's "apply the more conservative mutation" rule worked as-specified.
3. **Joint-rationale criterion is subtle** — the skill says "if two proposals *both got softened by the same firing*, add a shared line." Scenario 06 stressed this: X6a softens recovery AND targets running, but running is blocked by X3b first, so X6a's soften on running is superseded. Result: running is NOT in the softened cohort → no joint line. This is correct under the skill's definition but requires careful reading. **Phase 1 recommendation: move joint-rationale detection to the runtime (X-rule engine) rather than the skill.** Computing "which domains were actually softened by firing X" is mechanical and should not occupy skill attention budget.
4. **Rule-vs-judgment discipline held** on scenario 08. Heavy-legs-yesterday was present in the snapshot but not covered by any X-rule. The skill refused to invent a rule-shaped mutation and surfaced the context as `unmapped_context_observed` in meta.notes. This is the behavior the plan wants; X10-style deferrals to judgment have a home.
5. **The `x_rule_firings_applied[]` per-recommendation field is load-bearing for auditability.** Scenario 06's running rec has both X3b and X6a listed there, even though only X3b's mutation applied. This preserves the "nothing is silently dropped" invariant.
6. **Skill size is not the binding constraint.** 117 lines was comfortable. Phase 1's "<100 lines" aspiration for domain skills looks achievable when the skill's job is reconciliation rather than classification-plus-policy-plus-recommendation.

## What this tells us about Phase 1 and beyond

- **Proceed.** The architectural bet (code-vs-skill split with synthesis reconciling pre-computed firings) is viable. No evidence that the approach is fundamentally broken.
- **Move joint-rationale detection to runtime** (see point 3 above). Reduces skill surface, avoids subtle misreads.
- **In Phase 6 evals, require independent scenario authorship.** Budget at least 5 scenarios written by a reader who hasn't read the skill. This is how you'd catch the bias that this Phase 0.5 could not.
- **Add orphan-firing, banned-token, and `restructure`-tier scenarios** in Phase 1 or early Phase 2. They're edge cases this prototype did not exercise.
- **The `synthesis_meta` block is worth keeping as-is.** `firings_total`, `firings_by_tier`, `domains_blocked`, `domains_softened`, `notes` — all queryable, all cheap to compute, all useful for the `daily_plan` audit row.

## Prompt size note

- `skill_synthesis.md`: 117 lines. Under the 300-line aspiration.
- `xrules.py`: 138 lines. For reference only; it's code, not prompt.
- Scenario JSONs: ~30–50 lines each. At invocation time, the skill sees: skill markdown (117) + one scenario bundle (~50) + firings JSON (~30). Well under 500 lines of total prompt context per invocation. This is the ceiling that matters for model context budget at scale.

## Next action

Per plan dependency graph: **Phase 1 — Core reshape (3 weeks).** No gating issues from Phase 0 or Phase 0.5. Codex review of the rebuild plan can run asynchronously; no blocker.

---

**Reference artifacts:**
- Prototype: `reporting/experiments/synthesis_prototype/`
- Scenarios: `reporting/experiments/synthesis_prototype/scenarios/`
- Outputs: `reporting/experiments/synthesis_prototype/outputs/`
- Phase 0 findings (prior): `reporting/plans/historical/phase_0_findings.md`
- Revised plan: `.claude/worktrees/hardcore-kare-a92e25/reporting/plans/comprehensive_rebuild_plan.md` (commit 3ecd95e)
