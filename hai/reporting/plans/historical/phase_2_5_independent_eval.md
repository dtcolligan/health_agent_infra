# Phase 2.5 — Track B gate: independent synthesis eval pack

- Date: 2026-04-17
- Author: Claude Opus 4.7 (Phase 2.5 session on branch `rebuild`)
- Branch: `rebuild @ 8ca2ca2` (Phase 2 complete)
- Experiment: `reporting/experiments/synthesis_eval_pack/`

## Gate outcome

**4 of 4 scenarios at action_correctness ≥ 2/3 → Phase 3 authorised
unconditionally per rubric.**

Two of the four passes are **scope-gap passes** (scenarios describe
4-domain invariants; v1 supports 2 domains); authorisation is
therefore conditioned on three follow-ups (see below).

| Scenario | Action correctness | Verdict |
|---|---|---|
| s1 orphan_firing | 3/3 | pass |
| s2 cap_adjust_stacking | 2/3 | pass_with_scope_gap |
| s3 mixed_missingness | 2/3 | pass_with_scope_gap |
| s4 stale_proposal | 3/3 | pass |

See `reporting/experiments/synthesis_eval_pack/findings.md` for the
full write-up.

## Independence claim (as recorded)

> approximated independence: fresh session, not original skill
> author, scenarios authored before reading skill body; still
> single-agent, so not fully independent.

Scenarios were locked on disk before reading `skills/daily-plan-
synthesis/SKILL.md` or `core/synthesis_policy.py`. The author,
implementer, and scorer are the same agent session — a fully
independent eval would split those roles.

## What the eval does NOT cover

The runner tests the **runtime layer**
(`core/synthesis.py` + `core/synthesis_policy.py` +
`core/writeback/proposal.py`). It does not invoke the
daily-plan-synthesis skill, so skill-layer narration quality
(`rationale_quality` in the rubric) is `skipped` for every scenario.
The plan's Invariant that "missingness tags accurately propagate to
final rationale" is therefore **unverified**. This is the single most
important gap in the evidence.

## Conditions on the Phase 3 authorisation

Phase 3 proceeds with these three corrections baked in:

1. **Defensive orphan-firing flag.** Add an `orphan=true` column (or
   JSON tag) on `x_rule_firing` rows whose `affected_domain` is not
   in the committing plan's proposal domains. The current runtime
   prevents orphans by construction for the rules we have today
   (X1/X3/X6/X7 all iterate the proposal set); future rules that emit
   from snapshot-only signals could reintroduce the case, and the
   invariant should be monitored rather than relying on current code
   paths.

2. **Phase B end-to-end test coverage.** `guard_phase_b_mutation`
   correctly rejects illegal Phase B mutations at the unit-test level,
   but no test exercises the full Phase A cap + Phase B adjust cycle
   because nutrition is not submittable in v1. Add a test shim that
   allows a synthetic nutrition proposal through a test-only surface,
   so the cap+adjust stacking case (s2) has real coverage before
   Phase 5.

3. **Skill-harness eval as a Phase 3 exit criterion.** Run s1, s3,
   and s4 again at the end of Phase 3 with the skill actually invoked
   (via Claude Code subprocess or equivalent). Score the full
   `rationale_quality` axis. If any scenario scores below 2/3 on the
   full rubric, synthesis-skill-prompt redesign moves into Phase 3's
   late-phase scope as a visible correction.

4. **Re-run s2 at end of Phase 5.** Once nutrition and X9 are wired,
   the cap+adjust stacking case becomes exercisable end-to-end. Re-run
   and score; if it fails, that's a Phase 5 blocker, not a Phase 3
   one.

## What the eval DID verify

- Input validation (s4): named-invariant rejection, clean stderr,
  no silent synthesis consumption. Strongest result in the pack.
- Cap-confidence tier precedence (s1, s2): confidence correctly
  capped from `high` to `moderate` on each targeted proposal;
  independence from soften/block tiers confirmed.
- Deferred-proposal preservation (s3): runtime does NOT mutate a
  proposal that was already `defer_decision_insufficient_signal` at
  proposal time. No spurious "helpful" X-rule firings.
- Orphan prevention by construction (s1): current X-rule evaluators
  iterate proposals to emit firings; no firing can target a domain
  not in the proposal set. Verified by reading both the code and the
  persisted firings.
- Phase B write-surface guard (s2, code review):
  `guard_phase_b_mutation` structurally enforces the "adjust may only
  mutate action_detail" invariant. Code-correct; awaits end-to-end
  exercise when nutrition lands.

## Comparison to Phase 0.5

Phase 0.5 confirmed the synthesis **architecture** was viable. Phase
2.5 confirms the synthesis **runtime** implements the architecture
correctly for recovery + running, and enforces input validation
cleanly. The skill-layer narration invariant is the next risk line;
it remains unverified and is the condition attached to this
authorisation.

Treat the Phase 0.5 + Phase 2.5 evidence together as "GO for Phase 3";
not as "GO for production."
