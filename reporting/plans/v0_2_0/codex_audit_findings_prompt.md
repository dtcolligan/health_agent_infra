# Codex External Audit — v0.2.0 Pre-PLAN Bug Hunt

> **Why this round.** v0.2.0 is the gateway to Wave 2 (weekly review +
> deterministic factuality + insight ledger + LLM judge progression).
> Cycle theme: **make claims about the past week deterministically
> checkable.** Substantive tier; 18-24d estimate; one schema group.
> Maintainer's father (post-v0.1.18) closed W-2U-INSTALL verbal-only;
> AGENTS.md D16 (CP-2U-GATE-SPLIT) dropped the foreign-user empirical
> hard dep on v0.2.0. v0.2.0 opens against v0.1.14 substrate
> (W-PROV-1 + W-AJ judge harness), already shipped.
>
> **Phase 0 sweep status (Claude).**
> - Step 1 internal sweep — DONE; 4 findings.
> - Step 2 audit-chain probe — DONE; 4 findings.
> - Step 3 persona matrix — DONE; **13/13 with 0 findings + 0 crashes**.
>   Baseline holds.
> - Step 4 — **this round (you).**
>
> Eight `F-PHASE0-*` findings are written up at
> `reporting/plans/v0_2_0/audit_findings.md`. Three are tagged
> `revises-scope`; five are `informational`; **none are `aborts-cycle`**.
> The Claude internal sweep concludes the v0.2.0 thesis holds.
>
> **Your job is to find what the internal sweep missed.** Independent
> reads catch different things — your findings merge into the same
> `audit_findings.md` file (you write to a separate response file;
> maintainer + Claude consolidate). The two-LLM-disagreement-without-
> consensus-collapse posture is load-bearing per v0.1.x retro Lesson 2.
>
> **D14 plan-audit will run after PLAN.md authoring.** This audit is
> *pre-PLAN*. The PLAN.md does not yet exist — audit the cycle's
> scope shape, the 8 surfaced findings, and the dependency surface
> against the cycle thesis. Empirical Phase 0 norm: 1 round; if you
> surface ≥3 `revises-scope` findings, a second round may be warranted.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main (or chore/v0_2_0_phase0 if pre-cycle authoring)
git log --oneline -5
# expect: most recent should mention v0.2.0 cycle workspace seed +
#         post-v0.1.18 strategic refresh + v0.1.18 ship
ls reporting/plans/v0_2_0/
# expect: README.md, audit_findings.md, codex_audit_findings_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay special attention to:
   - "Governance Invariants" — W57 user-commit gate, three-state
     audit chain, review-summary bool-as-int hardening (D6 / D12 / D13).
   - "Settled Decisions" D1-D16 — note D16 (CP-2U-GATE-SPLIT;
     dropped v0.2.0's foreign-user empirical hard dep), D14
     (D14 plan-audit pattern), D15 (cycle-weight tiering), D11
     (Phase 0 D11 bug-hunt pattern).
   - "Do Not Do" — note that v0.2.0 ships W58D **deterministic
     only**; W58J ships shadow-by-default at v0.2.2. No autonomous
     threshold mutation. No clinical claims. No mechanism that
     auto-loads MCP servers from project files.
   - **"Patterns the cycles have validated"** — provenance
     discipline (verify file:line on disk before citing), summary-
     surface sweep on partial closure, honest partial-closure
     naming, audit-chain empirical settling shape. Apply these as
     you audit.

2. **`reporting/plans/post_v0_1_18/strategic_plan_v2.md`** §7 Wave 2
   — strategic context for v0.2.0–v0.2.3. Note that v0.2.0 is
   release 1 of 4 in Path A (post-v0.1.13 CP-PATH-A); reconciliation
   C6 caps each release at one schema group. v0.2.0's group is
   "weekly-review tables + W58D claim-block + recommendation_evidence_card
   carrier."

3. **`reporting/plans/tactical_plan_v0_1_x.md`** §6 v0.2.0 — release-
   by-release detail. Note 6.1 in-scope list, 6.2 acceptance, 6.3
   effort line (18-24d), 6.4 strategic context (gateway to v0.2.1-3
   then Wave 3).

4. **`reporting/plans/v0_2_0/README.md`** — workspace stub. The
   provisional scope table (lines 31-40) names the 7 W-ids; the
   sequencing block (lines 47-91) names the Phase 0 → Phase 1 →
   Phase 2 → Phase 3 ordering.

5. **`reporting/plans/post_v0_1_18/v0_1_x_retro.md`** §3 — five
   lessons. **Especially Lesson 4** (empirical-by-design cycles
   can't be built on synthetic evidence) and **Lesson 5** (honest
   partial-closure naming saves audit rounds). Apply these to your
   audit of the 8 findings.

6. **`reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md`** — the CP
   that produced D16. Note the named residual: W-2U-INSTALL closure
   is verbal-only (no transcript). Note the v0.2.0 hard-dep delta.

7. **`reporting/docs/current_system_state.md`** — v0.1.18 baseline.
   Note schema head 26, CLI command count 67, test gate
   2733p/5s, persona matrix 13/13, eval corpus 135+30.

8. **`reporting/plans/v0_2_0/audit_findings.md`** — Claude's 8
   `F-PHASE0-*` findings. **Read these carefully. Don't regurgitate
   them — your goal is to find what they missed.**

9. **The W-PROV-1 substrate the cycle will lean on:**
   - `src/health_agent_infra/core/provenance/locator.py` (199 LOC)
     — locator dataclass, validate, dedupe, serialize.
   - `src/health_agent_infra/core/state/projector.py` (1,600+ LOC)
     — projector path; locator emission edge.
   - `src/health_agent_infra/core/writeback/proposal.py:273-300`
     — proposal-acceptance path that reads `evidence_locators`.
   - `src/health_agent_infra/core/eval/judge_harness.py` (151 LOC)
     — W-AJ harness W58D shadows (W58J ships v0.2.2 shadow).
   - `src/health_agent_infra/core/review/summary.py` (515 LOC) —
     W48 outcome-token builder; W52 boundary surface (F-PHASE0-06).

10. **The v0.2.0 schema-group target:**
    - `reporting/plans/future_strategy_2026-04-29/review_codex.md:1551`
      — `recommendation_evidence_card` table sketch.
    - `src/health_agent_infra/core/state/migrations/` — current head
      `026_body_comp.sql`. v0.2.0 migrations land at 027+.

Cross-check that everything `audit_findings.md` cites actually
exists in the tree at the cited line. **Broken cross-references
count as findings.** The v0.1.x retro names this as the canonical
provenance-discipline failure mode.

---

## Step 2 — The audit questions

### Q1. Did Claude's internal sweep miss any `revises-scope` finding?

The 4 findings from step 1 (internal sweep) are F-PHASE0-01,
F-PHASE0-04, F-PHASE0-05, F-PHASE0-06. The 4 findings from step 2
(audit-chain probe) are F-PHASE0-02, F-PHASE0-03, F-PHASE0-07,
F-PHASE0-08.

**Adversarial sweep targets** — independent reads of:

- The 6 per-domain `domains/*/classify.py` files (~5,500 LOC total).
  Locator emission feasibility, F-PHASE0-01's "is locator derivation
  mechanical?" question, any per-domain partial-day or abstain
  path that W52 must handle.
- `src/health_agent_infra/cli/handlers/review.py` — does the existing
  `hai review` handler have any structural pattern that constrains
  W52's command shape?
- `src/health_agent_infra/core/synthesis.py` (1,213 LOC) +
  `synthesis_policy.py` (1,362 LOC) — does the synthesis layer carry
  any state that W52 should aggregate over but isn't named in §6.1?
- `src/health_agent_infra/core/data_quality/` — what does the data-
  quality surface look like today? F-PHASE0-03 names a constraint;
  is the actual surface narrower or broader than the finding assumes?
- `src/health_agent_infra/evals/` — eval scenario corpus structure;
  W58D fixture-corpus scope.

### Q2. Is v0.2.0's effort estimate honest given F-PHASE0-01?

README §6.1 names W52 as 6-8d. F-PHASE0-01 names locator emission
across 5 dormant domains as ~2-4d additional (or a separate
W-PROV-2 workstream). Total cycle estimate moves from 18-24d
toward 20-28d.

- Are there *other* hidden-scope items the F-PHASE0 findings
  imply but don't name?
- Is the schema-group claim (one group per reconciliation C6)
  intact? Or does F-PHASE0-04 (`recommendation_evidence_card`
  carrier) imply a *second* schema group separate from W52's
  weekly-review tables + W58D's claim-block?

### Q3. Is the Phase 1 → Phase 2 → Phase 3 sequencing honest?

README §-Sequencing names W52 first, W58D + W-FACT-ATOM second,
doc-only adjuncts in parallel, W-EXPLAIN-UX consumed during W52
prose authoring.

- Does W58D actually depend on W52's output schema, or could they
  proceed in parallel with a smaller mock?
- Does W-PROV-2 (if separated) need to land *before* W52 starts,
  or can the two co-evolve?
- W-MCP-THREAT is named as load-bearing for v0.3 PLAN-audit. Does
  it need to land in v0.2.0 specifically, or is a v0.2.1 carry-
  forward acceptable?

### Q4. Hidden coupling between v0.2.0 and other waves

README out-of-scope §-Out-of-scope lists what v0.2.0 will *not*
ship. Cross-check:

- W58J judge (v0.2.2) — W58D's claim-block schema must not
  preempt W58J's needs. Is the schema design forward-compatible?
- W53 insight ledger (v0.2.1) — does W52's weekly-review surface
  presume insight-ledger rows that v0.2.1 will create? Coupling
  risk.
- W-30 capabilities-manifest schema freeze (v0.2.3) — v0.2.0 adds
  `hai review weekly` to the manifest; the freeze cycle inherits
  the addition. Is the addition shape-stable enough?
- N-of-1 substrate (v0.5+) — does W52's weekly-review row schema
  set up the (recommendation, compliance, outcome, classified_state)
  triple ledger v0.5 will read? Or does v0.2.0 paint v0.5 into a
  corner?

### Q5. Acceptance criterion bite

README §6.2 acceptance is currently 5 bullets. **None of the 5 has
a quantitative threshold.** Compare to v0.1.18 PLAN.md acceptance,
which named explicit "3 of 4 onboarding flow steps testably
covered" / "test count grows ≥ 11" thresholds.

- Should each W-id in v0.2.0 have a quantitative acceptance line?
  (E.g., "W58D blocks ≥95% of corpus-of-known-bad claims,
  passes ≥98% of corpus-of-known-good claims.")
- Is "W-MCP-THREAT artifact filed" enough, or does it need
  "OWASP MCP Top 10 mapping verified against primary source per
  CP-MCP-THREAT-FORWARD" (which §6.2 already says) plus a count
  of mitigations documented?

### Q6. Settled-decision integrity

D16 (CP-2U-GATE-SPLIT, post-v0.1.18) is the newest settled
decision. Claude's audit_findings.md respects it (no foreign-user
empirical claim). Cross-check:

- Does any F-PHASE0-* finding implicitly reopen a settled decision?
- Does the cycle's W-2U-GATE-2 row (opportunistic-not-blocking)
  align with D16's "W-2U-WEARABLE / W-2U-DOGFOOD deferred to v0.4
  review"? Or does it conflate the new gate with the old?

### Q7. What the cycle doesn't say

Conventional Phase 0 absence sweeps:
- Abort path — what triggers cycle abort? (Should the v0.2.0 cycle
  abort if W-PROV-2 reveals locator emission is >4d?)
- Rollback — if W52 ships then a v0.2.0.1 hotfix is needed, what's
  the rollback shape? (Schema-group rollback is harder than CLI-
  flag rollback.)
- Conditional scope — F-PHASE0-08 (failed daily-runs observability
  hole) named "absorb into v0.2.0 vs defer to v0.2.1" as
  PLAN-author choice. Is the criterion for choice documented?

### Q8. Provenance / external-source skepticism

Spot-verify the load-bearing external citations in
`audit_findings.md`:
- `core/provenance/locator.py:23` whitelist — confirm the 2-table
  list is current.
- `core/state/projector.py:1466` — confirm the cited line carries
  the JSONL-projection import.
- `core/writeback/proposal.py:278-287` — confirm the cited
  `evidence_locators` opt-in shape.
- `future_strategy_2026-04-29/review_codex.md:1551` — confirm the
  `recommendation_evidence_card` table sketch is at this line.
- `core/review/summary.py:1-23` — confirm the W48 docstring
  describes the W48 contract as Claude's finding asserts.

Any drift between cited line and actual content is a Q8 finding.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_audit_findings_response.md` matching
the convention from prior cycles' Codex audit responses:

```markdown
# Codex Phase 0 Audit Response — v0.2.0 Pre-PLAN

**Verdict:** PROCEED_TO_PLAN | PROCEED_WITH_REVISIONS | RECONSIDER_SCOPE

**Round:** 1 / 2 (rare)

## Findings (new — Codex sweep)

### F-PHASE0-09 (or next available index). <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8
**Severity:** revises-scope | aborts-cycle | informational
**Reference:** file:line citation OR audit_findings.md F-PHASE0-N
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise scope as follows / accept and
note as known limitation / disagree with reason>

### F-PHASE0-10. ...

## Findings (review of Claude's 8)

For each F-PHASE0-01 through F-PHASE0-08:

- **F-PHASE0-N agree** — Claude's finding stands; nothing to add.
- **F-PHASE0-N agree-with-additions** — finding stands; add the
  following <evidence / recommendation>.
- **F-PHASE0-N disagree** — finding does not stand because
  <evidence>.
- **F-PHASE0-N reframe** — finding is real but the disposition
  (`revises-scope` vs `informational`) should change because
  <evidence>.

## Open questions for maintainer
```

Each finding must be triageable. Vague feedback is not a finding;
"`audit_findings.md` F-PHASE0-01 cites
`core/provenance/locator.py:23` for the whitelist; the actual
whitelist is at line 27 because of imports added 2026-05-04" is
a finding.

---

## Step 4 — Verdict scale

Phase 0 is not a PLAN_COHERENT-shape audit (no PLAN.md exists yet).
The verdict scale:

- **PROCEED_TO_PLAN** — Claude's 8 findings are sufficient + your
  sweep adds no new `revises-scope` items. PLAN.md authoring may
  open against the F-PHASE0-01..08 scope-shape impact list.
- **PROCEED_WITH_REVISIONS** — Phase 0 disposition holds, but
  Codex surfaces additional `informational` findings that PLAN.md
  must address explicitly. Cycle proceeds.
- **RECONSIDER_SCOPE** — Codex surfaces ≥1 `aborts-cycle` finding
  OR ≥3 new `revises-scope` findings. The maintainer should pause
  before authoring PLAN.md and either restructure scope or run a
  second Phase 0 round.

---

## Step 5 — Out of scope

- **Prior-cycle implementation** (already audited and shipped at
  v0.1.18; no v0.2.0 PLAN exists yet).
- **Code changes** (Phase 0 has not started implementation).
- **v0.2.1 / v0.2.2 / v0.2.3 / v0.3+ scope** — named in tactical
  plan §7-§9 but not in v0.2.0's commitments. F-PHASE0-08's
  "defer to v0.2.1" path is in scope to evaluate as a sequencing
  question; the v0.2.1 design itself is not.
- **Strategic + tactical + eval + success + risks docs beyond the
  v0.2.0 deltas** — the v0.1.x retro is a snapshot; do not audit
  the retro itself.
- **Non-maintainer foreign-user empirical evidence** — D16 settled
  this; W-2U-WEARABLE + W-2U-DOGFOOD are deferred to v0.4 review.

---

## Step 6 — Cycle pattern (this audit's place)

```
v0.1.18 ship → 2026-05-06 ✓
post-v0.1.18 strategic refresh → 2026-05-06 ✓
  (strategic_plan_v2 + v0_1_x_retro + CP-2U-GATE-SPLIT D16)
v0.2.0 cycle workspace seeded → 2026-05-06 ✓

Phase 0 (D11):
  1. Internal sweep ✓ (Claude, F-PHASE0-01..04..05..06)
  2. Audit-chain probe ✓ (Claude, F-PHASE0-02..03..07..08)
  3. Persona matrix ✓ (13/13, 0 findings, 0 crashes)
  4. Codex external Phase 0 audit ← you are here
  5. audit_findings.md consolidates → maintainer reads

Pre-implementation gate:
  revises-scope findings shape PLAN.md
  aborts-cycle findings end the cycle (none expected)

Phase 1 (PLAN authoring + D14 plan-audit):
  PLAN.md authored
  D14 plan-audit rounds (empirical 2-4 rounds, 10 → 5 → 3 → 0)

Phase 2 (Implementation):
  W52 (foundational; W58D consumes its output schema)
  W58D + W-FACT-ATOM (deterministic factuality gate)
  Doc-only adjuncts in parallel
  W-EXPLAIN-UX carry-forward consumed during W52 prose authoring

Phase 3 (D15 IR + ship):
  D15 IR rounds (empirical 2-3 rounds, 5 → 2 → 1-nit)
  RELEASE_PROOF.md + REPORT.md + CHANGELOG + AUDIT.md
  Manual TTY ship gate → git push origin main → uvx twine upload
```

Estimated review duration: 1-2 sessions for this audit round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_audit_findings_response.md` (new)
  — your findings.
- `reporting/plans/v0_2_0/audit_findings.md` (append) — maintainer
  + Claude consolidate Codex findings into the same file after
  this audit closes.
- `reporting/plans/v0_2_0/codex_audit_findings_round_2_prompt.md`
  (rare; only if your verdict is RECONSIDER_SCOPE).

**No code changes.** No test runs. No state mutations. No PLAN.md
authoring (PLAN.md does not yet exist; it authors after the
pre-implementation gate fires).

---

*Phase 0 Codex audit prompt authored 2026-05-06 by Claude. Ready
for Codex round 1.*
