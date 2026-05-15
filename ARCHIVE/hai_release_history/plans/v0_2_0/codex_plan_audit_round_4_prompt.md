# Codex External Audit — v0.2.0 PLAN.md (D14 round 4 — verdict-only-likely)

> **Why this round.** D14 round 3 closed `PLAN_COHERENT_WITH_REVISIONS`
> with 3 findings — clean settling at the empirical norm
> `10 → 5 → 3 → 0` thrice-validated across v0.1.11 + v0.1.12 +
> v0.1.17. **All 3 findings accepted; PLAN.md revised in place.**
> Codex returned **zero open questions** in R3, a settling signal.
>
> **R4 expected verdict: `PLAN_COHERENT` with 0-1 nits.** Round 4 is
> the canonical verdict-only round per v0.1.x empirical norm. The
> R3 fixes were localised wording substitutions + a math
> reconciliation; no new architectural decisions introduced.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 closed; D14 R1 + R2 + R3
> closed; PLAN.md revised three times. The audit is on the
> *round-3-revised PLAN document*. If R4 returns `PLAN_COHERENT`,
> the cycle opens.
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
# expect: most recent should mention v0.2.0 D14 R3 close + PLAN
#         revisions
ls reporting/plans/v0_2_0/
# expect: README.md, PLAN.md, audit_findings.md,
#         codex_audit_findings_prompt.md, codex_audit_findings_response.md,
#         codex_plan_audit_prompt.md, codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md,
#         codex_plan_audit_round_2_response_response.md,
#         codex_plan_audit_round_3_prompt.md,
#         codex_plan_audit_round_3_response.md,
#         codex_plan_audit_round_3_response_response.md (R3 closure),
#         codex_plan_audit_round_4_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read the round-4 orientation artifacts

In order:

1. **`reporting/plans/v0_2_0/codex_plan_audit_round_3_response.md`**
   — your round-3 findings (3 items + 0 OQs).

2. **`reporting/plans/v0_2_0/codex_plan_audit_round_3_response_response.md`**
   — Claude's round-3 dispositions. **All 3 findings accepted;
   PLAN.md revised in place.**

3. **`reporting/plans/v0_2_0/PLAN.md`** — the **round-3 revised**
   artifact (851 LOC; was 833 LOC pre-R3). Round-3 corrections are
   inline-marked with "**(Round-3 correction per F-PLAN-R3-N: ...)**"
   notes.

4. **`AGENTS.md`** "Patterns the cycles have validated" — provenance
   discipline + summary-surface sweep + audit-chain settling shape.

Cross-check that every PLAN.md citation post-round-3-revision actually
exists in the tree at the cited line.

---

## Step 2 — The audit questions (round 4)

**Round 4 is verdict-only-likely.** The thrice-validated empirical
settling shape `10 → 5 → 3 → 0` predicts 0-1 findings. Apply
discipline: **don't search for findings that aren't there.** Frame
findings only when there is a concrete, citable, triageable issue.
A nit (acceptance-item wording polish, etc.) is a finding; a
preference is not.

### Q1. R3 fixes — did each propagate cleanly?

Verify each F-PLAN-R3-01 through F-PLAN-R3-03 fix per the
dispositions in `codex_plan_audit_round_3_response_response.md`:

- **F-PLAN-R3-01 propagation.** §0 Theme (line ~13), §2.A
  ship-claim gate prose (line ~201), §2.A partial-closure path
  (line ~203), §3.4 abort table R-V0.2.0-01 row (line ~676), §6
  closed Codex Q3 disposition note (line ~785) — all reworded to
  "quantitative or comparative factual claim(s)" or equivalent.
  **Are there any remaining "quantitative claim" surfaces that
  should be in the broader scope?** Spot-check via grep against
  the full PLAN.
- **F-PLAN-R3-02 propagation.** §2.C acceptance #5 (line ~313)
  rewrites canonical-latest disposition. §2.D CLI surface block
  (line ~341-348) lists `[--include-history]`. Anything missed?
  Does any other doc cite the W-EVCARD-WEEKLY JSON output shape?
- **F-PLAN-R3-03 propagation.** §3.1 G2 has explicit per-WS table
  with cross-cutting subtotal +3. Math: 6+12+8+23+8+26+1+1+1 = 86.
  Holds. Does the R3 cross-cutting allocation (doc-freshness +
  capabilities + ship-gate-freshness) match the actual test surfaces
  v0.2.0 will deliver?

### Q2. New incoherence introduced by R3 fixes (low probability)

R3 fixes were localised wording substitutions + a math
reconciliation. New incoherence is unlikely. Spot-check:

- The §3.1 G2 cross-cutting subtotal (+3) names test surfaces
  outside per-WS scope. Are these surfaces named consistently
  elsewhere in PLAN.md? E.g., does the §3.2 ship-time freshness
  sweep (G8) reference the doc-freshness test? Does §6 OQs reference
  the capabilities-manifest regression?
- Round-3 correction notes are now stacked (some sites have
  round-1 + round-2 + round-3 notes). Is the correction-note
  density readable, or has it become noise?

### Q3. Provenance spot-verify (re-applied; minimal)

Quick spot-verify on R3 citations:
- `core/synthesis.py:466-473` `_ACCEPTED_STATE_TABLES`.
- `core/state/migrations/008_sync_run_log.sql:41` `mode` column.
- `evals/cli.py:26-29` shape-only summary.
- `review_codex.md:1597-1602` 3 conflict categories.

If R3 didn't change any external citations, this should be a
no-finding spot-check.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_plan_audit_round_4_response.md`.

If R4 returns 0 findings:

```markdown
# Codex Plan Audit Response — v0.2.0 PLAN.md (R4)

**Verdict:** PLAN_COHERENT

**Round:** 4 / 4

## Findings (R4)

None. PLAN.md is coherent and ready for cycle open.

## Open questions for maintainer

None.
```

If R4 returns 1 nit:

```markdown
# Codex Plan Audit Response — v0.2.0 PLAN.md (R4)

**Verdict:** PLAN_COHERENT (with 1 nit absorbed in cycle-open commit)

**Round:** 4 / 4

## Findings (R4)

### F-PLAN-R4-01. <short title>

**Severity:** nit
**Reference:** PLAN.md § X.Y, line N
**Argument:** <concise>
**Recommended response:** <inline fix>
```

If R4 returns ≥2 findings, R5 follows (uncommon at this stage but
preserves the empirical-settling discipline).

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle. Most likely outcome at R4.
- **PLAN_COHERENT_WITH_REVISIONS** — ≥2 findings; R5 verdict-only
  follows.
- **PLAN_INCOHERENT** — ≥4 findings; PLAN-author re-reads R3 diff.
  Very unlikely at R4 given thrice-validated settling shape.

---

## Step 5 — Out of scope

Same as R1 + R2 + R3: no prior-round disposition re-litigation; no
code changes; no v0.2.1+ scope; no Phase 0 findings; no foreign-user
empirical re-tier.

---

## Step 6 — Cycle pattern (this audit's place)

```
v0.1.18 ship → 2026-05-06 ✓
post-v0.1.18 strategic refresh → 2026-05-06 ✓
v0.2.0 cycle workspace seeded → 2026-05-06 ✓
Phase 0 (D11) closed → 2026-05-06 ✓
PLAN.md authored → 2026-05-06 ✓
D14 R1 closed PLAN_COHERENT_WITH_REVISIONS → 2026-05-07 ✓ (10 findings)
D14 R2 closed PLAN_COHERENT_WITH_REVISIONS → 2026-05-07 ✓ (5 findings)
D14 R3 closed PLAN_COHERENT_WITH_REVISIONS → 2026-05-07 ✓ (3 findings)

D14 R4 (this round) — verdict-only-likely:
  Round 4 ← you are here
  Empirical norm: 0-1 findings
  PLAN_COHERENT verdict opens the cycle

Phase 2 — Implementation (after PLAN_COHERENT)
Phase 3 — D15 IR + ship
```

Estimated review duration: <1 session (R4 is verdict-only).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_plan_audit_round_4_response.md`
  (new) — your verdict.
- `reporting/plans/v0_2_0/PLAN.md` (revisions if R4 finds 1 nit;
  none if 0).

**No code changes.** No test runs. No state mutations.

---

*D14 round 4 plan-audit prompt authored 2026-05-07 by Claude.
Ready for Codex.*
