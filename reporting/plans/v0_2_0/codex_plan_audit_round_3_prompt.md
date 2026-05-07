# Codex External Audit — v0.2.0 PLAN.md (D14 round 3)

> **Why this round.** D14 round 2 closed `PLAN_COHERENT_WITH_REVISIONS`
> with 5 findings — clean halving from R1's 10 findings, matching
> the v0.1.x empirical norm `10 → 5 → 3 → 0`. **All 5 findings
> accepted; PLAN.md revised in place.** Round 3 verifies (a) round-2
> fixes propagated cleanly through the 827-LOC document and (b) no
> third-order incoherence introduced by round-2 revisions.
>
> **Empirical norm per v0.1.x retro Lesson 1:** R3 settles at
> 2-3 findings; round 4 verdict `PLAN_COHERENT`. Round 3 is
> typically the last substantive round; round 4 is verdict-only
> with 0-1 nits.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 closed; D14 R1 + R2
> closed; PLAN.md revised twice. The audit is on the
> *round-2-revised PLAN document*.
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
# expect: most recent should mention v0.2.0 D14 R2 close + PLAN
#         revisions
ls reporting/plans/v0_2_0/
# expect: README.md, PLAN.md, audit_findings.md,
#         codex_audit_findings_prompt.md, codex_audit_findings_response.md,
#         codex_plan_audit_prompt.md, codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md,
#         codex_plan_audit_round_2_response_response.md (R2 closure),
#         codex_plan_audit_round_3_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read the round-3 orientation artifacts

In order:

1. **`reporting/plans/v0_2_0/codex_plan_audit_round_2_response.md`**
   — your round-2 findings (5 items + 2 OQs).

2. **`reporting/plans/v0_2_0/codex_plan_audit_round_2_response_response.md`**
   — Claude's round-2 dispositions. **All 5 findings accepted; 2
   OQs adjudicated; PLAN.md revised in place.**

3. **`reporting/plans/v0_2_0/PLAN.md`** — the **round-2 revised**
   artifact (827 LOC; was 821 LOC pre-R2). Round-2 corrections are
   inline-marked with "**(Round-2 correction per F-PLAN-R2-N: ...)**"
   notes (in addition to the round-1 notes from R1 fixes).

4. **`AGENTS.md`** "Patterns the cycles have validated" — provenance
   discipline + summary-surface sweep + honest partial-closure
   naming + audit-chain settling shape.

5. **`reporting/plans/post_v0_1_18/v0_1_x_retro.md`** §3 Lesson 1.

Cross-check that every PLAN.md citation post-round-2-revision actually
exists in the tree at the cited line. **Broken cross-references
introduced by R2 fixes are the canonical R3 finding.**

---

## Step 2 — The audit questions (round 3)

### Q1. R2 fixes — did each propagate cleanly?

Verify each F-PLAN-R2-01 through F-PLAN-R2-05 fix per the dispositions
in `codex_plan_audit_round_2_response_response.md`:

- **F-PLAN-R2-01 propagation.** §1.1 W58D bullet (line ~48) +
  §1.2 catalogue row 2.F (line ~70) reworded to
  "quantitative or comparative factual atom." Does any other
  summary surface still say "every atomic claim" outside the
  round-N correction notes? Spot-check: §1.4 thesis (round-1
  corrected); §2.E W-FACT-ATOM (correctly says quant/comp validatable
  + qualitative passed-through); §2.F gate logic (correctly says
  `atom_type ∈ {quantitative, comparative}`). Any other site
  unaccounted for?
- **F-PLAN-R2-02 propagation.** §2.D acceptance #8 (deferred-domain
  suppression release-blocker) added; new test
  `test_review_weekly_deferred_domain_suppression.py` in Files of
  record. §4 R-V0.2.0-01 references the suppression behaviour. Did
  the §3.1 G2 test count update absorb the new test? Does the
  §3.4 abort table still cite the W-PROV-2 partial-closure path
  consistently?
- **F-PLAN-R2-03 propagation.** §2.D acceptance #9 (canonical-latest
  output semantics release-blocker) added; rerun fixture defined.
  §2.D acceptance #11 mentions 4 flags including new
  `--include-history`. Does the parser-tree contract (§2.D Files of
  record `cli/__init__.py` mention) absorb the new flag? Does
  §1.3 Cross-phase merge friction list reflect any change? Does
  the §2.C migration 028 schema need a column to track canonical-vs-
  superseded, or is `MAX(computed_at)` sufficient as PLAN-author
  claims in R2 response_response?
- **F-PLAN-R2-04 propagation.** §3.4 abort table R-V0.2.0-03 +
  R-V0.2.0-05 rows rewrite mitigation to abort-and-D14-re-author.
  §4 R-V0.2.0-03 Mitigation rewritten with DAG-conflict argument.
  §4 R-V0.2.0-05 Mitigation: option (a) "fork-defer ONE carrier"
  replaced with abort-and-re-author per round-2 (was caught
  proactively in R2 fix-applying). **Does §1.3 sequencing DAG (Phase
  1 → Phase 2) still implicitly assume fork-defer is possible?**
  **Does §1.4 cycle thesis still mention fork-defer as a
  contingency?** **Any other site that survived the round-1
  fork-defer wording without round-2 revision?**
- **F-PLAN-R2-05 propagation.** §2.D Files of record updated with
  abstain-metadata + deferred-domain test files. §2.D acceptance
  #10 test count raised to ≥23. §2.F acceptance #6 (`--scenario-set
  all` semantics) added. §1.3 Cross-phase merge friction W58D entry
  adds `evals/cli.py`. §3.1 G2 test count target raised to ≥ v0.1.18
  + 86. Math on §3.1 G2 projection: W-PROV-2 +6, W-EVCARD-DAILY +12,
  W-EVCARD-WEEKLY +8, W52 +23, W-FACT-ATOM +8, W58D +26. Sum: 83.
  "+86" target — does the +3 gap account for "others minor" overhead?

### Q2. New incoherence introduced by R2 fixes

The R3 high-risk patterns:

- **§2.D acceptance renumbering.** §2.D went from 10 items to 12
  items (added #8 deferred-domain + #9 canonical-latest). Items
  renumbered downstream. Does any other doc reference §2.D acceptance
  by item number? §3 ship gates? §4 risks register? §1.3 sequencing?
- **§2.F acceptance renumbering.** §2.F went from 7 items to 8 items
  (added #6 `--scenario-set all`). Same renumbering question.
- **F-PLAN-R2-03 canonical-latest interaction with §2.C migration
  schema.** PLAN-author claim: `MAX(computed_at)` aggregation is
  sufficient; no schema delta. Verify this against the §2.C migration
  028 column list — does the schema permit efficient canonical-latest
  query (index on `(iso_week, user_id, claim_id, computed_at DESC)`)?
- **F-PLAN-R2-04 abort-and-re-author interaction with R-V0.2.0-01
  W-PROV-2 mitigation.** R-V0.2.0-01 still says "fork-defer
  late-domain(s) to v0.2.1 W-PROV-3" — that's per-domain fork-defer,
  NOT per-carrier fork-defer (different from F-PLAN-R2-04's
  W-EVCARD-* fork-defer, which IS unsound). Are these two correctly
  distinguished? F-PLAN-R2-04 only addresses W-EVCARD carrier
  fork-defer; W-PROV-2 per-domain fork-defer is still valid because
  W52 suppresses deferred-domain claims (per §2.D acceptance #8).

### Q3. Test count + math reconciliation

§3.1 G2 target: ≥ v0.1.18 + 86. Per-WS projection sum: 83. Discrepancy
of +3 is "others minor" overhead. Is this honest, or should the
projection be tightened?

§2.D acceptance #10: ≥23 tests (was ≥18 in round-1; raised by +5 for
abstain-metadata, deferred-domain, canonical-latest-rerun + others).
Math: 5 (aggregation) + 3 (abstain) + 2 (supersession) + 4
(data-quality) + 2 (claim-card) + 2 (W-EXPLAIN-UX) + 2 (abstain-
metadata) + 2 (deferred-domain) + 1 (canonical-latest-rerun) = 23.
Holds.

§2.F acceptance #7: ≥26 tests. Math: 8 (gate logic) + 12 (corpus
coverage) + 3 (threshold) + 2 (bypass-flag) + 1 (scenario-set-all-
semantics) = 26. Holds.

### Q4. Provenance spot-verify (Q5 from R2, re-applied to R2-revised PLAN)

Spot-verify the load-bearing external citations in R2-revised PLAN.md:

- `core/synthesis.py:466-473` — `_ACCEPTED_STATE_TABLES` mapping
  current.
- `core/state/migrations/008_sync_run_log.sql:41` — `mode` column
  current.
- `evals/cli.py:26-29` + `:100-138` — shape-only summary current.
- `review_codex.md:1597-1602` — 3 conflict categories.

Any drift between cited line and actual content is a Q4 finding.

### Q5. Closeout posture

If R3 returns 0-1 findings, the verdict is `PLAN_COHERENT` and the
cycle opens. If R3 returns 2-3 findings, R4 follows for verdict-only
closure. If R3 returns ≥4 findings, R2 fixes introduced more than
they closed; PLAN-author re-reads R2 fix diff before R4.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_2_0/codex_plan_audit_round_3_response.md` matching
R1 + R2 conventions:

```markdown
# Codex Plan Audit Response — v0.2.0 PLAN.md (R3)

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS

**Round:** 3 / 4

## Findings (R3)

### F-PLAN-R3-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4
**Severity:** stale-propagation | new-incoherence | math-error |
provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N
**Argument:** <why this is a finding>
**Recommended response:** <revise PLAN.md as follows>

### F-PLAN-R3-02. ...

## Open questions for maintainer
```

If R3 finds 0-1 findings, the verdict is `PLAN_COHERENT` and the
cycle opens after any nit absorbed.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle. 0-1 nits typical at R3.
- **PLAN_COHERENT_WITH_REVISIONS** — 2-3 findings; R4 verdict-only
  follows.
- **PLAN_INCOHERENT** — ≥4 findings; PLAN-author re-reads R2 diff
  before R4.

---

## Step 5 — Out of scope

Same as R1 + R2: no R1 + R2 disposition re-litigation; no code
changes; no v0.2.1+ scope; no Phase 0 findings; no foreign-user
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

D14 R3 (this round):
  Round 3 ← you are here
  Empirical norm: 2-3 findings; R4 verdict-only follows

(Round 4 verdict-only on R3 absorption)

Phase 2 — Implementation (after PLAN_COHERENT)
Phase 3 — D15 IR + ship
```

Estimated review duration: 1 session (R3 is propagation check; R2
PLAN diff is smaller than R1's).

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_2_0/codex_plan_audit_round_3_response.md`
  (new) — your findings.
- `reporting/plans/v0_2_0/PLAN.md` (revisions, if warranted).
- `reporting/plans/v0_2_0/codex_plan_audit_round_4_prompt.md`
  (conditional; only if R3 returns ≥2 findings).

**No code changes.** No test runs. No state mutations.

---

*D14 round 3 plan-audit prompt authored 2026-05-07 by Claude.
Ready for Codex.*
