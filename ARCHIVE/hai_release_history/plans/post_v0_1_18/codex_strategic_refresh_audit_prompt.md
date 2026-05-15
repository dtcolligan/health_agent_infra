# Codex External Audit — post-v0.1.18 strategic refresh

> **Why this round.** Claude authored a fresh strategic plan v2
> (`reporting/plans/post_v0_1_18/strategic_plan_v2.md`) supersding
> `strategic_plan_v1.md` (2026-04-27), plus a companion v0.1.x
> retro doc. The refresh integrates 4 settled decisions added since
> v1 (D13–D16), 10 cycles shipped + 2 cancelled, the post-v0.1.15
> docs overhaul, and the v0.1.17 cli.py split. Both docs ship as
> commit `d8115ac` on main. v0.2.0 PLAN.md will cite v2 as
> strategic substrate; this audit catches drift between v2's
> claims and current state **before** v0.2.0 D14 round 1 has to.
>
> **This is NOT a D14 plan-audit.** Strategic-plan refresh is
> doc-only and does not gate a release. The audit is a single
> targeted round — *do v2's claims about current state hold against
> what the codebase + AGENTS.md + AUDIT.md actually say?* — not
> a multi-round PLAN_COHERENT settling exercise.
>
> **Empirical norm.** Refresh audits are 1 round. If you find
> contradictions warranting a second round, surface them in your
> response and propose the second-round shape; the maintainer
> decides whether to spin one up.
>
> **Cycle position.** Post-v0.1.18 ship + post-CP-2U-GATE-SPLIT
> (D16) + pre-v0.2.0 PLAN authoring. v0.1.x track is closing;
> v0.2.x has not opened.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -5
# expect: most recent two commits are the strategic refresh:
#   d8115ac docs(post-v0.1.18): strategic refresh — strategic_plan_v2 + v0_1_x_retro + freshness sweep
#   498ded3 docs(governance): adopt CP-2U-GATE-SPLIT (D16) — split W-2U-GATE; cancel v0.1.19
ls reporting/plans/post_v0_1_18/
# expect: CP-2U-GATE-SPLIT.md, strategic_plan_v2.md, v0_1_x_retro.md,
#         codex_strategic_refresh_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay specific attention to:
   - "Settled Decisions" D1–D16 (D13–D16 are new since v1).
   - "Patterns the cycles have validated" — provenance discipline,
     summary-surface sweep, honest partial-closure naming.
   - "Ship-time freshness checklist."
2. **`reporting/docs/current_system_state.md`** — current shipped
   truth (v0.1.18; schema 26; 2,733 tests; 67 commands; 13
   personas; 135 eval scenarios).
3. **`AUDIT.md`** — release-cycle audit index. Verify settling-shape
   claims in v2 §3 + retro §3 against actual round-counts cited.
4. **`reporting/plans/strategic_plan_v1.md`** — preserved as v2's
   primary source. Read for what v1 claimed at v0.1.10.
5. **`reporting/plans/post_v0_1_18/strategic_plan_v2.md`** — the
   primary artifact under audit.
6. **`reporting/plans/post_v0_1_18/v0_1_x_retro.md`** — companion
   retro doc; secondary artifact under audit.
7. **`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`** — the CP
   that authorised D16, applied at commit `498ded3`.
8. **`reporting/plans/tactical_plan_v0_1_x.md`** — sanity-check
   v2 §7 timeline claims against current row state.

Cross-check that everything v2 + retro cite actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions

### Q1. Provenance discipline

Both docs cite specific files, line numbers, function names,
W-ids, settled decisions, and cycle dates. Per AGENTS.md "Patterns
the cycles have validated":

> Before citing a file path, line number, function name, or fact in
> a PLAN, RELEASE_PROOF, audit response, or reply to the maintainer,
> **verify on disk**.

Spot-check a meaningful sample (≥10 citations) of v2's and retro's
factual claims. Specifically verify:

- **v2 §3 H1 evidence.** "v0.1.10 W-A's bool-as-int silent-coercion
  closure (D12)" — does W-A actually live in v0.1.10? Was the closure
  bool-as-int? AGENTS.md D12 cites the helper paths.
- **v2 §3 H4 evidence.** "v0.1.17 W-29 cli.py 9,927-LOC mechanical
  split into 11 handler modules" — verify against
  `current_system_state.md` and `src/health_agent_infra/cli/`.
- **v2 §3 H5 evidence.** "v0.1.13 alone closed 17 W-ids — largest
  cycle in the track." Verify against AUDIT.md or v0.1.13
  RELEASE_PROOF.
- **v2 §5.5 settling shapes.** "10 → 5 → 3 → 0 (v0.1.11), 10 → 5 →
  3 → 0 (v0.1.12), 11 → 5 → 3 (v0.1.17), 7 → 3 (v0.1.18)" — verify
  against AUDIT.md round tables.
- **v2 §5.6 eval corpus.** "v0.1.10 had ~35 scenario fixtures.
  v0.1.17 W-AH-2 expanded to 135." Verify against
  `current_system_state.md` and v0.1.17 RELEASE_PROOF.
- **Retro §2 numbers table.** Spot-check `cli.py` original line
  count (9,927), schema head (26), test count (2,733), persona
  count (13), command count (67), settled-decision count (16),
  cycles-cancelled count (2).
- **Retro §3.2 two-LLM disagreement examples.** "v0.1.12 D14 round
  1 — Codex caught Claude citing `core/credentials.py:171` for a
  helper that actually lived at `core/pull/auth.py:171`." Verify
  against the v0.1.12 D14 round-1 response.

Any miscitation is a finding.

### Q2. Settled-decision integrity

v2 §4 claims D1–D16 in a table. Compare against AGENTS.md "Settled
Decisions" current text. Specifically:

- **D4 status.** v2 says: *"v0.1.8 / v0.1.17"* with note that the
  W29 split closed at v0.1.17. AGENTS.md D4 text — does v2's
  summary match?
- **D16 wording.** v2's D16 entry is a one-line summary. Compare
  to AGENTS.md's full D16 text (added at commit `498ded3`). Are
  they consistent? Does the summary preserve the load-bearing
  claims (verbal-only closure, v0.4 review re-evaluation, v0.2.0
  hard-dep dropped)?

### Q3. Hypothesis evidence updates

v2 §3 claims fresh evidence per hypothesis. Specifically:

- **H1 father-session evidence.** v2 says: *"the maintainer's
  father installed v0.1.18 on a foreign machine without a wearable
  and reported 'it worked for him.'"* Source: maintainer chat
  2026-05-06 (CP-2U-GATE-SPLIT names this verbal-only). Is v2's
  framing of this evidence consistent with the closure provenance
  named in CP-2U-GATE-SPLIT and v0_1_19/README.md?
- **H4 manifest-byte-stable claim.** v2: *"manifest byte-stable
  through the [v0.1.17 cli.py] split."* Verify via v0.1.17
  RELEASE_PROOF or `test_cli_parser_capabilities_regression.py`.

### Q4. Wave timeline coherence

v2 §7 re-baselines from 2026-05-06. Compare against
`tactical_plan_v0_1_x.md` §1 row state — do v2's wave summaries
match the tactical plan's hard-deps column post-D16?

Specifically:
- v2 §7 Wave 2: "v0.2.0 hard deps post-D16: v0.1.14 substrate,
  already shipped." Match tactical plan?
- v2 §7 Wave 3: "v0.4 — W-2U-WEARABLE + W-2U-DOGFOOD re-evaluated
  as hard gates here (D16)." Match AGENTS.md D16 + CP-2U-GATE-SPLIT
  destination claim?
- v2 §7 horizon: "Wave 1 shipped ~3 weeks ahead of v1's estimate."
  v1 §7 said "14-18 months optimistic from v0.1.10 (April 2026) to
  v1.0 ship — late 2027." v0.1.18 shipped 2026-05-06. Is the
  "3 weeks ahead" claim defensible?

### Q5. Hidden coupling between v2 and retro

v2 cites retro §2 for numbers. Retro cites v2 §3 for hypothesis
evidence. Are there contradictions between the two docs? Specific
sub-questions:

- v2 §1 calls the agent-wrapper framing "load-bearing across
  README.md, ARCHITECTURE.md, AGENTS.md, and the six per-domain
  reference docs." Retro §1 echoes "the contract is one line: the
  agent proposes and explains; the runtime validates and commits."
  Verify that wording is current in README.md.
- v2 §5.7 + retro §6 both reference v0.1.18 W-OB-2 interactive
  default. Do the two summaries agree on what shipped?

### Q6. Stale claims that should have been retired

v1 contained claims that became false during v0.1.x. v2 §5
explicitly retires several. Are there others v2 missed?

Spot-check candidates:
- Is anything in v2 §6 (strategic posture) still future-tense that
  should be present-tense post-v0.1.18?
- Is anything in v2 §8 (scope-expansion) under-updated relative
  to current empirical evidence?
- Is anything in v2 §10 (decision branches) stale per the v0.1.x
  evidence accumulation?

### Q7. What the docs don't say

Absences worth surfacing:

- **v2's risk register cross-reference.** v2 §11 names companion
  docs but doesn't explicitly cite `risks_and_open_questions.md`
  R-T-03 RESOLVED status. Should it? (R-T-03 cli.py rot is now
  closed per the v0.1.17 W-29 split.)
- **Retro's omissions.** Does the retro mention F-OB-PRE-01 (the
  schema-behind-DB intake crash from 2026-05-05)? If not, is that
  a load-bearing omission?
- **v2's MCP threat-model dependency.** v2 §7 Wave 3 names
  W-MCP-THREAT as a v0.2.0 doc-only adjunct + v0.3 prereq. Is the
  threat-model artifact authoring scope accurately summarised?

### Q8. Provenance discipline applied to v2 itself

v2's §11 Provenance section names primary sources. Are they all
current (not historical-and-stale)?

- `reporting/docs/current_system_state.md` (2026-05-06) — current.
- `reporting/plans/post_v0_1_15/docs_overhaul_report.md` (2026-05-04)
  — current, references commit `c86f80b`.
- `AUDIT.md` (2026-05-06) — current.
- `AGENTS.md` (2026-05-06) — current.
- `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md` — current
  (committed `498ded3`).

Are any other primary sources missing from §11 that should be
cited?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/post_v0_1_18/codex_strategic_refresh_audit_response.md`
matching the existing D14 response convention:

```markdown
# Codex Strategic-Refresh Audit Response — v2 + retro

**Verdict:** REFRESH_COHERENT | REFRESH_COHERENT_WITH_REVISIONS | REFRESH_INCOHERENT

**Round:** 1

**Date:** YYYY-MM-DD

## Summary

[2-3 sentences naming the verdict + the most load-bearing finding(s).]

## Findings

### F-REFRESH-01 — [short title]

**Severity:** revises-doc | nit | informational

**Q-bucket:** Q1 | Q2 | ... | Q8

**Claim under audit:** [direct quote from v2 or retro]

**Verification:** [what you did; file:line]

**Finding:** [what's wrong]

**Recommended fix:** [propose specific edit]

### F-REFRESH-02 — ...

[continue per finding]

## What didn't surface

[Anti-findings — places you spot-checked that did hold. Brief.]

## Recommended next step

- If REFRESH_COHERENT: maintainer applies any nits in-place; v2
  + retro stand as canonical.
- If REFRESH_COHERENT_WITH_REVISIONS: maintainer revises per
  recommended fixes; this can be a single close-in-place pass
  unless findings cascade.
- If REFRESH_INCOHERENT: maintainer reconsiders v2 authorship;
  surface the structural problems that prevent close-in-place
  resolution.
```

---

## Step 4 — Verdict vocabulary

- **REFRESH_COHERENT** — v2 + retro hold against current state. No
  findings or only informational items.
- **REFRESH_COHERENT_WITH_REVISIONS** — v2 + retro need named edits
  (file:line + recommended fix) before being trusted as substrate
  for v0.2.0 PLAN authoring. Close-in-place expected.
- **REFRESH_INCOHERENT** — structural contradictions that
  close-in-place can't resolve. Maintainer reconsiders v2
  authorship.

---

## Step 5 — Single-round expectation + escalation path

This audit is **scoped as 1 round**. The maintainer's expectation
(per CLAUDE.md ship-time freshness checklist + strategic-refresh
shape):

- Strategic-plan refresh is doc-only and does not gate a release.
- v2 + retro have no D14 obligation per AGENTS.md (D14 governs
  PLAN.md authoring, not strategic-plan refresh).
- A round 2 is an **escalation path**, not a default. Surface in
  your round-1 response if you find contradictions warranting one.

If you find sufficient drift to warrant round 2: name the shape
(re-audit-after-revisions vs deeper provenance sweep vs cross-cycle
consistency check) and the maintainer decides.

---

## Step 6 — What this audit explicitly does NOT cover

- Per-cycle code correctness (covered by cycle RELEASE_PROOFs +
  D15 IR rounds).
- v0.2.0 PLAN.md authoring (not yet started; covered by future D14
  round 1).
- Eval methodology (`eval_strategy/v1.md` is unchanged).
- Tactical plan §2-§9 per-cycle detail (covered by per-cycle
  artifacts).

If you find drift in those surfaces during this audit, note as
informational; do not treat as REFRESH_COHERENT_WITH_REVISIONS
findings unless they directly contradict v2 or retro claims.

---

## Step 7 — Provenance for this prompt

This prompt was authored 2026-05-06 by Claude (delegated by
maintainer) at the close of the strategic-refresh session. The
session's full chain:

1. Maintainer asked whether to replan or refresh.
2. Claude recommended refresh; both authored (commit `d8115ac`).
3. Maintainer approved + asked for ship-time freshness sweep
   (commits `498ded3` + `d8115ac`).
4. This audit prompt authored as final step.

The audit's job is to verify that 2-3 actually held — not to
re-derive the strategic case. v1 is the prior strategic-plan
artifact; this audit treats v1 as primary source for what the
project believed pre-v0.1.11, not as a parallel claim against v2.
