# Synthesis eval pack — findings

- Phase: 2.5, Track B
- Session: Claude Opus 4.7, 2026-04-17, branch `rebuild @ 8ca2ca2`
- Scenarios: 4 (orphan firing, cap+adjust stacking, mixed missingness,
  stale proposal)
- Rubric: 3-point per rubric.md

## Independence stance

Per Dom's call in the planning exchange, the recorded independence
claim is:

> **approximated independence: fresh session, not original skill
> author, scenarios authored before reading skill body; still
> single-agent, so not fully independent.**

Concretely:

- I am Claude Opus 4.7 in a new session. I did not author
  `skills/daily-plan-synthesis/SKILL.md` — that shipped in commit
  `6c93c9d` from a prior session.
- The four scenario JSONs were written before I read the skill's body
  or `core/synthesis_policy.py`. My input surface during scenario
  authoring was limited to the rebuild plan's X-rule table (§2.2) and
  Phase 2.5 scenario spec (§Phase 2.5 Track B).
- After locking the scenarios, I read the skill + synthesis code to
  build the runner that exercises them.
- This session also built the runner and scored the outputs — so the
  author, implementer, and scorer are a single agent. A fully
  independent eval would split those roles across at least two
  sessions.

## Headline

**4 of 4 scenarios pass at action_correctness ≥ 2/3 → per rubric,
Phase 3 authorised unconditionally.**

But two of the four passes are **scope-gap passes**: the scenarios
describe 4-domain invariants that are not testable against v1, which
only supports recovery + running proposals. Reading those passes as
"full invariant verified" would be dishonest. I record them instead as
"the testable subset passes; the untestable subset is structurally
guarded at the code level."

Concretely:

| Scenario | Action correctness | Verdict | Note |
|---|---|---|---|
| s1 orphan_firing | 3/3 | pass | Runtime prevents orphans by construction; invariant holds via a different mechanism than the plan's scenario assumed |
| s2 cap+adjust stacking | 2/3 | pass_with_scope_gap | Phase A cap verified; Phase B adjust guarded at code level but not exercisable (nutrition not in v1) |
| s3 mixed missingness | 2/3 | pass_with_scope_gap | Deferred proposals correctly preserved; sleep + strength domains not in v1 |
| s4 stale_proposal | 3/3 | pass | Named-invariant rejection; clean stderr; no silent synthesis consumption |

## Scoring method caveat

The runner tests the **runtime layer** (`core/synthesis.py`,
`core/synthesis_policy.py`, `core/writeback/proposal.py`) — it does NOT
invoke the daily-plan-synthesis skill. Running the skill requires
spawning Claude Code as a subprocess per scenario, which was out of
scope for this eval. The consequence:

- `action_correctness` and `uncertainty_calibration` *can* be scored
  from runtime state (firings persisted, confidence applied, actions
  preserved or mutated as expected).
- `rationale_quality` *cannot* be scored without running the skill.
  Marked `skipped` for all four scenarios.

This is the most important limitation of the eval pack as delivered. A
follow-up session with a Claude Code harness that drives the
daily-plan-synthesis skill per-scenario would close this gap. Given
that this is a gate, not production, I judged runtime-layer evidence
sufficient for the go/no-go call — but the plan's invariant #1 ("no
firing is dropped, including in rationale prose") is only partially
verified.

## Per-scenario findings

### s1 — Orphan firing

The runtime generates X7 firings by iterating the proposal set
(`core/synthesis_policy.py:526`). This means it is **impossible** for
the runtime to emit a firing whose `affected_domain` is not present in
the proposal set. The plan's scenario envisions a skill-layer handler
that catches such firings and tags them as `orphan_firing_<rule_id>` —
but the runtime never emits one.

This is a good finding: the invariant is preserved by construction, not
by fragile skill handling. It is also a test-design finding: the
scenario as written cannot exercise the skill's orphan path because the
runtime filters such firings out before the skill ever sees them.

Both recommendations correctly capped from `high` to `moderate`
confidence. Two X7 firings persisted (one per domain) — no firings
dropped.

### s2 — cap_confidence + adjust stacking

Phase A cap (X7) works correctly. Confidence went from `high` to
`moderate` on both recovery and running proposals. X7 firings are
independent per the tier-precedence table (`TIER_PRECEDENCE` in
`synthesis_policy.py`) and do not interact with soften/block.

Phase B adjust (X9) **cannot fire** in the current system:

1. `PROPOSAL_SCHEMA_VERSIONS` / `SUPPORTED_DOMAINS` is
   `{recovery, running}` — nutrition proposals cannot be submitted.
2. `evaluate_x9` in `synthesis_policy.py` early-exits when no nutrition
   drafts exist.
3. The `PHASE_B_TARGETS` registry only permits X9 to touch
   `nutrition` — so even if X9 fired, it couldn't touch recovery or
   running.

The scenario's core invariant (`X7 cap + X9 adjust on same domain; X9
does not escalate tier or change action`) is therefore **structurally
guarded** (via `guard_phase_b_mutation` at
`core/synthesis_policy.py:651`, which rejects any Phase B mutation
that touches `action` or a non-target domain with
`XRuleWriteSurfaceViolation`) but **not exercisable end-to-end**.

Action for Phase 3/5 scope: re-run this scenario once nutrition domain
is wired. The guard is code-correct; the interaction case isn't
covered by tests because the inputs can't exist yet.

### s3 — Mixed missingness

Runtime correctly preserves deferred proposals. Running proposed
`defer_decision_insufficient_signal` with `confidence=low`; the final
recommendation carries exactly those values, with no X-rule firings
attempting to "help". Recovery proposed
`proceed_with_planned_session` with `confidence=high`; no stress
signal triggered X7 (scenario's stress data was not in the snapshot
because sleep/stress tables don't exist in v1), so confidence held.

Two of the four scenario proposals (sleep, strength) are not
submittable against v1. The scenario's richer missingness mix cannot
be exercised. A narrower statement is provable: for the recovery +
running subset, the runtime respects deferred proposals and does not
invent or interpolate data.

The skill-layer invariant ("rationale or synthesis_meta accurately
reflects the underlying missingness tag: partial / unavailable /
pending_user_input") is unverifiable without running the skill. That
is the part that most needs the follow-up skill-harness eval.

### s4 — Stale/invalid proposal

Cleanest result in the pack. Both defects rejected at the writeback
boundary with named invariants:

- Stale `schema_version='0.1'` →
  `ProposalValidationError(invariant='schema_version', message='expected
  schema_version="recovery_proposal.v1" for domain "recovery", got
  "0.1"')`.
- Out-of-enum `action='moonshot_tempo_plus_long_run'` →
  `ProposalValidationError(invariant='action_enum', …)` with the full
  expected enum set enumerated in the message.

`proposal_log` is empty. `run_synthesis` on the empty proposal_log
raises `SynthesisError('no proposals in proposal_log for …')` — no
silent consumption of malformed input, no Python traceback leaking to
stderr.

The input validation path is the strongest layer in the system. It is
the pattern other layers (skill invocation, cross-domain reconciliation)
should aim for: named invariants, structured exceptions, loud refusals.

## Concrete design adjustments flagged before/during Phase 3

1. **Invariant #1 ("no firing dropped") coverage is partial.** The
   runtime prevents orphan firings by construction for the rules we
   have today, but future rules that emit from snapshot-level signals
   (not proposal iteration) could reintroduce the orphan case. Add a
   defensive runtime check at firing-persistence time: any firing with
   `affected_domain` not in `{proposal.domain for proposal in proposals}`
   is explicitly tagged `orphan=true` in the `x_rule_firing` row (new
   column in a tiny follow-up migration), so the invariant is monitored,
   not just currently-true.
2. **Phase B end-to-end coverage pends Phase 5.** X9 is the only Phase
   B rule today and cannot fire in v1. Add a test-only dummy Phase B
   rule (or a test harness that allows submitting a nutrition proposal
   through a test shim) so the Phase A cap + Phase B adjust interaction
   can be exercised in tests before the real nutrition domain lands.
   Without this, `guard_phase_b_mutation` is only exercised by unit
   tests on the guard itself — not by a full synthesis cycle.
3. **Missingness-tag propagation at the skill layer is unverified.**
   The plan's Invariant on missingness surfacing in rationale /
   synthesis_meta needs a skill-harness test. This is the single most
   important gap in this eval pack.
4. **Re-authorisation checkpoint at end of Phase 3.** When sleep +
   stress become first-class domains (Phase 3 per plan), re-run s1
   and s3 with sleep and stress proposals actually in the proposal set.
   Re-run s2 at end of Phase 5 when nutrition + X9 are wired.

## Gate decision

**Phase 3 is authorised.** 4 of 4 scenarios passed at ≥ 2/3
action_correctness per the rubric's unconditional-authorisation rule.

But the authorisation carries a recorded condition: Phase 3 must
include (a) the defensive orphan-firing flag, (b) a skill-harness
follow-up eval that scores rationale_quality on these same four
scenarios once sleep + stress are wired, and (c) re-running s2 at
end of Phase 5. Absent those, Phase 0.5 + 2.5 evidence remains "GO
for Phase 3" but NOT "GO for production" — the narrative-layer
invariants are unverified.

Treat Phase 0.5 and this Phase 2.5 eval as complementary: Phase 0.5
confirmed the synthesis architecture is viable; Phase 2.5 confirms the
runtime layer implements the architecture correctly and enforces the
critical input-validation invariant. The skill-layer narration
invariant is the next risk line.
