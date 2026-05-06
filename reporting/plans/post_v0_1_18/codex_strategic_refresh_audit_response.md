# Codex Strategic-Refresh Audit Response - v2 + retro

**Verdict:** REFRESH_COHERENT_WITH_REVISIONS

**Round:** 1

**Date:** 2026-05-06

## Summary

v2 and the retro are directionally coherent as post-v0.1.18 strategy
substrates, but they need a close-in-place revision pass before v0.2.0
PLAN authoring cites them as canonical. The main issues are factual
provenance errors: overcounted "shipped/closed" work, misdated eval
corpus growth, a wrong D14 round number in the retro, and stale current-doc
freshness surfaces that make v2's "README accurate" claim false.

## Findings

### F-REFRESH-01 - v2 intro overstates new settled decisions since v1

**Severity:** revises-doc

**Q-bucket:** Q2 | Q8

**Claim under audit:** `strategic_plan_v2.md:8-10` says that since v1,
"7 new settled decisions have been added (D10-D16)".

**Verification:** v2 later says the opposite at `strategic_plan_v2.md:352-353`:
"v1 had D1-D12; v2 adds D13-D16." The preserved v1 header also says
"4 new settled decisions added (D13-D16)" at `strategic_plan_v1.md:6-8`,
and v1 already contains D10, D11, and D12 at `strategic_plan_v1.md:330-332`.

**Finding:** The intro count is stale/wrong. D10-D12 were new in v1, not
new since v1. The refresh integrates 4 new decisions since v1: D13-D16.

**Recommended fix:** Change `7 new settled decisions ... (D10-D16)` to
`4 new settled decisions ... (D13-D16)`.

### F-REFRESH-02 - H5 overcounts shipped cycles and fully closed v0.1.13 W-ids

**Severity:** revises-doc

**Q-bucket:** Q1 | Q5

**Claim under audit:** `strategic_plan_v2.md:328-329` says: "18 cycles
shipped by a single maintainer. v0.1.13 alone closed 17 W-ids - largest
cycle in the track."

**Verification:** The retro's own numbers table says `16` release cycles
shipped and `2` cycles cancelled at `v0_1_x_retro.md:61-62`. AUDIT says
v0.1.13 was the largest cycle at 17 workstreams (`AUDIT.md:187-190`),
but the outcome was "16 of 17 W-ids closed-this-cycle; 1 partial-closure"
at `AUDIT.md:205-207`. The v0.1.13 release proof says the same:
`RELEASE_PROOF.md:58-59` records 16 closed and one W-Vb partial closure.

**Finding:** The evidence point is directionally right but overclaims.
The track had 18 cycle outcomes if cancelled cycles are counted, not 18
shipped cycles. v0.1.13 had the largest 17-workstream scope, but did not
close all 17; W-Vb partial-closed with a named v0.1.14 residual.

**Recommended fix:** Rewrite the bullet to: `16 shipped releases plus 2
cancelled empirical cycles disposed by a single maintainer. v0.1.13 was
the largest cycle in the track at 17 workstreams, with 16 closed and one
honest partial-closure.`

### F-REFRESH-03 - Eval corpus growth is misdated in v2

**Severity:** revises-doc

**Q-bucket:** Q1 | Q5

**Claim under audit:** `strategic_plan_v2.md:461-463` says:
"v0.1.10 had ~35 scenario fixtures. v0.1.17 W-AH-2 expanded to 135...
v0.1.18 added 30 judge-adversarial fixtures."

**Verification:** v0.1.14 RELEASE_PROOF records W-AH as `28 -> 35`
scenarios at `v0_1_14/RELEASE_PROOF.md:19`, and W-AI as the 30
judge-adversarial fixtures at `v0_1_14/RELEASE_PROOF.md:20`. v0.1.17's
PLAN states the 35-fixture baseline came from v0.1.14 carry-over
provenance and was the current baseline at v0.1.17 open
(`v0_1_17/PLAN.md:163-167`). v0.1.17 RELEASE_PROOF then records W-AH-2
closing at 135 fixtures and 100% pass-rate at `v0_1_17/RELEASE_PROOF.md:17`
and `:45`. I also checked the v0.1.10 tag on disk: it has 28 scenario JSON
fixtures under `src/health_agent_infra/evals/scenarios/`, not ~35.

**Finding:** Two dates are wrong. The ~35 baseline is post-v0.1.14, not
v0.1.10. The 30 judge-adversarial fixtures shipped in v0.1.14 W-AI, not
v0.1.18.

**Recommended fix:** Replace section 5.6 with: `v0.1.14 moved the deterministic
scenario corpus from 28 -> 35 and shipped 30 judge-adversarial fixtures.
v0.1.17 W-AH-2 expanded the deterministic corpus from 35 -> 135
(6x20 + 15 synthesis) at 100% pass-rate.`

### F-REFRESH-04 - Retro attributes the W-PRIV wrong-path catch to the wrong D14 round

**Severity:** revises-doc

**Q-bucket:** Q1 | Q5

**Claim under audit:** `v0_1_x_retro.md:130-133` says: "v0.1.12 D14
round 1 - Codex caught Claude citing `core/credentials.py:171` for a
helper that actually lived at `core/pull/auth.py:171`."

**Verification:** The actual finding appears in the v0.1.12 D14 round 2
response, not round 1: `codex_plan_audit_round_2_response.md:98-113`
names the nonexistent `core/credentials.py` path and the real
`core/pull/auth.py:171` / `:261` helpers. The round-1 response does not
contain that W-PRIV path finding. AGENTS.md currently repeats the same
round-number phrasing at `AGENTS.md:350-351`.

**Finding:** The example is valid, but the round number is wrong. Keeping
it as round 1 weakens the provenance-discipline example because the point
was a second-order D14 catch after round-1 revisions.

**Recommended fix:** Change the retro bullet to `v0.1.12 D14 round 2`.
Also fix the corresponding AGENTS.md provenance example, or explicitly
leave AGENTS.md for a separate governance-doc freshness pass.

### F-REFRESH-05 - v2 says public docs are accurate, but README/current-state surfaces are stale

**Severity:** revises-doc

**Q-bucket:** Q6 | Q8

**Claim under audit:** `strategic_plan_v2.md:714-716` says public
`README.md`, `ARCHITECTURE.md`, and `AGENTS.md` are accurate to shipped
state and "Currently true as of v0.1.18 + the post-v0.1.15 docs overhaul."
v2 also cites `reporting/docs/current_system_state.md` as the 2026-05-06
source of v0.1.18 shipped baseline at `strategic_plan_v2.md:793-794`.

**Verification:** Root `README.md` still advertises a `2683` test badge
at `README.md:20`, status `0.1.17` at `README.md:24-33`, and a package
version table row of `0.1.17` at `README.md:289-294`. Current release proof
and AUDIT say v0.1.18 settled at `2733 passed, 5 skipped` with D15 IR
closed (`AUDIT.md:24-31`). `current_system_state.md` has the right table
values at `:14-20` and v0.2.0 next-active at `:134-135`, but it still has
a stale header "current truth as of v0.1.17" at `:3`, a stale "D15 IR
pending" published-posture clause at `:15`, and a stale product-claim
paragraph saying v0.1.19 will run the foreign-user session at `:38-44`.

**Finding:** The claim that public docs are currently accurate is too
strong, and one of v2's primary provenance sources is internally mixed
between pre-D16/pre-IR-close and post-D16 state.

**Recommended fix:** Either update README/current_system_state before
retaining the v2 claim, or revise v2 to say the governance/planning docs
are current while README/current_system_state still need a ship-time
freshness sweep. If updating docs, align README to v0.1.18 / 2733 tests /
v0.2.0 next-active, and remove current_system_state's v0.1.19-future and
D15-pending clauses.

### F-REFRESH-06 - Wave 1 "3 weeks ahead" timing claim is not defensible

**Severity:** revises-doc

**Q-bucket:** Q4

**Claim under audit:** `strategic_plan_v2.md:629-631` says v1 had a
14-18 month optimistic horizon from v0.1.10 to v1.0, and "Wave 1 shipped
~3 weeks ahead of v1's estimate."

**Verification:** v1's Wave 1 estimate was "v0.1.10-v0.1.13, ~3 months"
at `strategic_plan_v1.md:456-464`. v2 now defines Wave 1 as
v0.1.10-v0.1.18 and says it took "~10 days actual" at
`strategic_plan_v2.md:547-555`. v1's total horizon line is at
`strategic_plan_v1.md:573-574`.

**Finding:** If the comparison is against v1's Wave 1 estimate, actual
Wave 1 finished roughly 10-11 weeks ahead of the "~3 months" estimate,
not ~3 weeks. If the comparison is against the total v1.0 horizon, the
claim should not be expressed as "Wave 1 shipped 3 weeks ahead" because
v1.0 still remains governed by 90-day substrate gates.

**Recommended fix:** Replace the sentence with either: `Wave 1 shipped
roughly 2-3 months ahead of v1's Wave 1 estimate, but the total v1.0
horizon is unchanged because the back-half calendar gates dominate`, or
remove the ahead-of-estimate clause entirely.

### F-REFRESH-07 - Provenance list omits sources v2 actually depends on

**Severity:** nit

**Q-bucket:** Q7 | Q8

**Claim under audit:** v2 section 11 lists primary provenance sources at
`strategic_plan_v2.md:787-805`.

**Verification:** v2 section 7 hard-dependency claims match the tactical plan
row at `tactical_plan_v0_1_x.md:52`, and v2 section 5.1's R-T-03 resolved claim
matches `risks_and_open_questions.md:8-15` and `:229-231`. Neither
`tactical_plan_v0_1_x.md` nor `risks_and_open_questions.md` appears in
the section 11 provenance list, despite both being named as companion docs at
`strategic_plan_v2.md:21-25`.

**Finding:** This is not a coherence break, but it weakens v2's own
provenance discipline. The doc uses the tactical plan and risk register
as current-state sources, not just companion reads.

**Recommended fix:** Add section 11 bullets for `reporting/plans/tactical_plan_v0_1_x.md`
(source of current v0.2.x row/hard-dep state) and
`reporting/plans/risks_and_open_questions.md` (source of R-T-03 resolved
status and active risk/open-question posture).

## What didn't surface

- D16 substance held: AGENTS.md D16, CP-2U-GATE-SPLIT, tactical plan
section 1, and v0_1_19/README.md agree that W-2U-INSTALL is closed
verbal-only, W-2U-WEARABLE and W-2U-DOGFOOD defer to v0.4 review, and
v0.2.0 drops the foreign-user empirical hard dep.
- W-29 evidence held: pre-split `cli.py` was 9,927 LOC, current CLI
layout is 1 main package module + shared + 11 handler groups, and
v0.1.17 RELEASE_PROOF records manifest byte-stability through the split.
- v2's D4 and D16 settled-decision summaries are semantically consistent
with AGENTS.md, though D16 is necessarily compressed.
- v2 and retro agree on W-OB-2: bare `hai init` auto-promotes to guided
only on TTY + incomplete onboarding state, with `--non-interactive` and
`HAI_INIT_NON_INTERACTIVE=1` opt-outs.
- The eval corpus current count held after excluding
`judge_adversarial/index.json`: 135 deterministic fixtures plus 30
judge-adversarial fixtures.
- The father-session framing is consistent with CP-2U-GATE-SPLIT and
v0_1_19/README.md as verbal-only, transcript-free W-2U-INSTALL evidence.
- F-OB-PRE-01 is not omitted from the retro: it appears in the D11
pattern section as the v0.1.18 Phase 0 finding absorbed as W-OB-7
(`v0_1_x_retro.md:281-283`).
- W-MCP-THREAT is accurately summarized as a v0.2.0 doc-only adjunct and
v0.3 prerequisite; the deeper authoring scope belongs to the future
v0.2.0 PLAN.

## Recommended next step

- Maintainer revises v2 + retro per F-REFRESH-01 through F-REFRESH-07.
  This can be a single close-in-place pass; no round 2 is needed unless
  the freshness-source edits reveal further contradictions.
