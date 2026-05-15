# Codex External Audit — v0.1.X PLAN.md (pre-cycle plan review)

<!--
TEMPLATE — copy to reporting/plans/v0_1_X/codex_plan_audit_prompt.md
and customise the per-cycle sections marked {{TEMPLATE}}. Do not
modify Step 0, Step 3, Step 4, Step 5, Step 6, Step 7 — they are
the stable contract surface across cycles. See
reporting/plans/_templates/README.md for the workflow.
-->

> **Why this round.** {{TEMPLATE: 2-4 sentences naming the cycle's
> theme, the scope-shaping inputs (reconciliation? maintainer
> adjudication? prior-cycle deferrals?), and any settled-decision
> reversals the cycle proposes. Reference the round number if this
> is round 2+.}}
>
> **D14 is a settled decision** (added at v0.1.11 ship). Empirical
> norm: 2-4 rounds for a substantive PLAN, settling at the
> `10 → 5 → 3 → 0` halving signature.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit is
> on the *plan document itself* — its coherence, sequencing, sizing
> honesty, hidden coupling.
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
# expect: cycle/v0.1.X (or chore/<scope> if pre-cycle authoring)
git log --oneline -5
# expect: most recent should mention the prior release ship
ls reporting/plans/v0_1_X/
# expect: PLAN.md, codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants"
   - "Settled Decisions" D1-DN — note any new D-entries this cycle
     proposes via cycle proposals.
   - "Do Not Do" — note any reversals this cycle proposes.
   - **"Patterns the cycles have validated"** — provenance
     discipline, summary-surface sweep, honest partial-closure
     naming, audit-chain empirical shape. Apply these as you audit.
2. **`reporting/plans/strategic_plan_v1.md`** — vision; note the
   sections this cycle proposes editing (if any).
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release-by-
   release plan. {{TEMPLATE: name the section this cycle's PLAN.md
   represents.}}
4. {{TEMPLATE: any cycle-specific input — reconciliation doc,
   prior-cycle RELEASE_PROOF for carry-overs, demo-run findings,
   etc.}}
5. **`reporting/plans/v0_1_X-1/RELEASE_PROOF.md`** — prior-cycle
   carry-overs (§5 named-defers). The cycle's W-CARRY register
   should account for every line.
6. **`reporting/plans/v0_1_X/PLAN.md`** — the artifact under review.

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions

{{TEMPLATE: per-cycle audit questions, organised by Q-bucket. Use
the v0.1.11 + v0.1.12 prompts as the canonical examples — see
reporting/plans/v0_1_11/codex_plan_audit_prompt.md and
reporting/plans/v0_1_12/codex_plan_audit_prompt.md.

Standard Q-buckets that recur:

- **Q1. Cycle thesis coherence.** Do the workstreams add up to the
  stated theme, or has scope drifted?
- **Q2. Sequencing honesty.** Hidden ordering dependencies?
- **Q3. Effort estimate honesty.** Per-WS sizing realistic?
- **Q4. Hidden coupling.** Workstream-to-workstream interactions
  not documented in PLAN.md §4 risks.
- **Q5. Acceptance criterion bite.** Is each acceptance criterion
  specific enough to fail on?
- **Q6. Settled-decision integrity.** Do CP deltas quote AGENTS.md
  current text verbatim? Are the proposed replacements honest?
- **Q7. What the plan doesn't say.** Absences — abort path,
  rollback, conditional scope.
- **Q8. Provenance / external-source skepticism.** Spot-verify
  claims that lean on external docs (reconciliation, prior cycle,
  third-party docs).

Add cycle-specific Q-buckets as needed — e.g., v0.1.12 had a
governance-edit-density question because CP1-CP6 reversed multiple
settled decisions.}}

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_X/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.X PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 / 4

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Open questions for maintainer
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.X claims `core/foo.py:171` but `foo.py` is at
`core/bar/foo.py:171`" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- Prior-cycle implementation (already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started).
- v0.1.X+1+ scope (named in tactical_plan_v0_1_x.md but not in
  this PLAN's commitments).
- The strategic + tactical + eval + success + risks docs beyond
  the deltas this cycle proposes.

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here
  Maintainer response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md → ship to PyPI
```

Estimated review duration: 1-2 sessions per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_X/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_X/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_X/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations.
