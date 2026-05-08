# Codex External Audit — v0.1.14 PLAN.md Round 2

> **Why this round.** D14 round 1 returned PLAN_COHERENT_WITH_REVISIONS
> with 12 findings. All 12 accepted; revisions applied 2026-05-01 in
> lockstep across PLAN.md + tactical_plan + strategic_plan + AGENTS.md
> + 5 CP files (175 insertions / 74 deletions across 9 files). This is
> the standard D14 "round 2 catches what round 1 introduced" pass.
>
> **Scope is narrower than round 1.** Do not re-audit the full PLAN.
> Audit:
>   1. Did each named round-1 revision land correctly?
>   2. Did the larger revisions (PLAN §1.3.1 new candidate-absence
>      procedure; tactical_plan §11 renumber; strategic_plan §8.2
>      Strava rewrite) introduce second-order issues?
>   3. Spot-check 5+ citations not covered in round 1.
>   4. Are AGENTS.md D4 / tactical §6 / tactical §9 / PLAN §6 / 5 CP
>      files all internally consistent on the v0.2.0 schema-group +
>      Path A application-status story?
>
> **Empirical context.** D14 prior at v0.1.13: 11 → 7 → 3 → 1-nit → 0
> (5 rounds for 17 W-ids). v0.1.14 round 1: 12 findings. Expected
> round 2: ~5-7. PLAN's §3 ship-gate accepts ≤5 rounds; if round 3
> would push beyond 5, maintainer re-scopes per the §1.3.1 procedure.
>
> **Cycle position.** Pre-PLAN-open. Round 1 revisions are committed
> intent; Phase 0 has not started. Audit is on the *plan document
> after revisions*, not on Phase 0 work.
>
> **You are starting fresh.** This prompt and the artifacts it cites
> are everything you need; do not assume context from a prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.14
git log --oneline -5
# expect: 900092e v0.1.14 pre-cycle ... is the most recent;
#   round-1 revisions may or may not be committed yet
ls reporting/plans/v0_1_14/
# expect: PLAN.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md (round 1 Codex),
#         codex_plan_audit_round_1_response.md (round 1 maintainer),
#         codex_plan_audit_round_2_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read in this order

1. **`reporting/plans/v0_1_14/codex_plan_audit_response.md`** — your
   round-1 findings (F-PLAN-01..F-PLAN-12).
2. **`reporting/plans/v0_1_14/codex_plan_audit_round_1_response.md`**
   — maintainer disposition + named revisions per finding.
3. **`reporting/plans/v0_1_14/PLAN.md`** — the artifact post-revision.
   Read fully. Note revisions are in place; PLAN now references
   F-PLAN-NN throughout for traceability.
4. **`reporting/plans/tactical_plan_v0_1_x.md`** — verify §11
   renumber (was 8.x → 11.x), §12 risk-cuts updated for Path A
   per-release scope, §13 boundary "v0.1.11 → v0.2.3", §6.1
   W-EXPLAIN-UX carry-forward consumption hook, §6.1 schema-group
   "weekly-review tables + W58D claim-block", §9.1 W-30 schema-
   group list "W52 + W58D claim-block (v0.2.0), W53 (v0.2.1),
   W58J (v0.2.2)".
5. **`AGENTS.md`** — verify D4 line now reads "W52 + W58D claim-
   block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)".
6. **`reporting/plans/strategic_plan_v1.md`** — verify Wave 3 source-
   list note ("v0.2.0 authoring; refresh at v0.4 prereq completion")
   and §8.2 row (Strava removed; Hevy/MyFitnessPal only).
7. **`reporting/plans/post_v0_1_13/cycle_proposals/`:** verify each
   of 5 CP files has the updated `Codex verdict:` field reflecting
   v0.1.14 D14 round 1 application status.
8. **Spot-read 1 source file you choose at random from §21 of
   `strategic_research_2026-05-01.md`** for citation-pass continuity
   with research-audit round 2.

---

## Step 2 — Round-2 audit questions

### R2-Q1. Did each round-1 revision land correctly?

For each F-PLAN-01..F-PLAN-12, verify the revision is present in the
artifact and reads as intended:

- **F-PLAN-01 (wire-up claim softened):** PLAN §1.1 should NOT say
  "wire-up release"; should say "starts with the source-row primitive
  + judge harness in tree, reducing design risk."
- **F-PLAN-02 (sizing 32-45):** PLAN §1.2 + §5 should both say
  32-45 days (not 30-40); §4 risks "Cycle exceeds 45-day budget"
  (not 40-day).
- **F-PLAN-03 (§1.3.1 candidate-absence procedure):** PLAN should
  have a new §1.3.1 with three options (hold / defer / re-author);
  §4 risks should reference §1.3 + §1.3.1; §2.A should reference
  §1.3.1 in candidate-absence path.
- **F-PLAN-04 (snapshot gate diff classes):** PLAN §3 should split
  the gate row into byte-identical (W-29) vs named-diff-allowed
  (W-AN, W-BACKUP, W-PROV-1).
- **F-PLAN-05 (W-EXPLAIN-UX carry-forward):** PLAN §2.C acceptance
  should require a "v0.2.0 W52 prose obligations" section in the
  findings doc; tactical_plan §6.1 should have a carry-forward
  consumption bullet + §6.2 acceptance row.
- **F-PLAN-06 (P13 matrix-only):** PLAN §2.C should say P13 is
  matrix-only for v0.1.14; §2.M should say W-Vb-3 owns P2-P12 only;
  §3 ship-gate should clarify "matrix-clean (no demo-replay
  assertion for P13)."
- **F-PLAN-07 (tactical_plan stale propagation):** title should be
  "v0.1.11 through v0.2.3"; §11 subheads should be 11.1-11.6; §12
  risk-cuts should not say "W53 from v0.2.0"; §13 boundary should
  be "v0.1.11 → v0.2.3".
- **F-PLAN-08 (Wave 3 source timing):** strategic_plan should say
  "verify current at v0.2.0 authoring; refresh at v0.4 prereq
  completion" (not "verify current at v0.4").
- **F-PLAN-09 (Strava §8.2 removal):** strategic_plan §8.2 row
  should NOT list Strava; should say "Hevy / MyFitnessPal only;
  Strava prohibited."
- **F-PLAN-10 (W58D claim-block in v0.2.0):** AGENTS.md D4 +
  tactical §6.1 schema-group + tactical §9.1 W-30 list should all
  include "W58D claim-block" as part of the v0.2.0 schema group.
- **F-PLAN-11 (CP application status):** PLAN §6 should have an
  application-status table; 5 CP files should have updated
  `Codex verdict:` fields.
- **F-PLAN-12 (90-day claim softened):** PLAN §2.D "Why P0" should
  NOT say "will corrupt their state.db within 90 days"; should say
  "is likely to need a recovery path."

For any revision that didn't land or landed incorrectly, file as a
finding with severity `unfinished-revision`.

### R2-Q2. Did the larger revisions introduce second-order issues?

Three revisions are large enough to warrant focused second-order
review:

**§1.3.1 candidate-absence procedure** is new. Audit:
- Does the "hard rule: candidate by Phase 0 gate" actually fit the
  cycle pattern? Phase 0 (D11) bug-hunt happens *after* D14 closes
  per AGENTS.md cycle pattern. Is "Phase 0 gate" the right gate, or
  should it be "before Phase 0 opens" / "before W-2U-GATE opens"?
- The three fallback options (hold / defer / re-author + re-D14) —
  is each one an actually-achievable maintainer move, or are any of
  them theoretical?
- Does the §4 risks register "D14 exceeds 5 rounds" row's reference
  to §1.3.1 actually make sense? §1.3.1 is about candidate absence,
  not about D14 round count.

**tactical_plan §11 renumber.** Verify:
- All 6 subheads are now 11.x (not 8.x).
- No remaining 8.x references anywhere in the document body
  (e.g., in §13 provenance text or other narrative).
- §11 still reads coherently after the renumber (no orphan refs
  to "the §8.x phase 0 step" elsewhere).

**strategic_plan §8.2 Strava rewrite.** Verify:
- The new wording does not weaken D5 ("Garmin Connect is not the
  default live source") — D5 is about rate-limiting + reliability,
  not about ToS prohibition. Verify the new §8.2 row is in addition
  to D5, not in conflict.
- Does not contradict D6 (nutrition v1 macros-only) — the row
  mentions MyFitnessPal totals; verify "totals" doesn't open a
  micronutrient or food-taxonomy door.
- The new wording flags the v0.1.14 D14 round-1 F-PLAN-09 lineage —
  is that propagation honest, or does it bury the strava-banned
  fact under audit-chain noise?

### R2-Q3. Spot-check 5+ citations not covered in round 1

Round 1 spot-checked some PLAN.md citations. Round 2 widens:

- PLAN.md §6 references AGENTS.md D11 + D14 — verify current AGENTS.md
  text matches.
- PLAN.md §7 references `reporting/plans/v0_1_13/RELEASE_PROOF.md §5`
  for inherited carry-overs — verify §5 actually contains those
  W-ids (W-29, W-Vb-3, W-DOMAIN-SYNC).
- tactical_plan §6.1 references `reconciliation C8` for
  `recommendation_evidence_card.v1` schema — verify reconciliation
  actually contains C8 evidence-card text.
- strategic_plan Wave 3 source-list URLs — verify they resolve to
  the actual MCP spec pages (no link rot caught at round-1 sweep).
- AGENTS.md "Do Not Do" Strava bullet cites Strava Nov 2024 ToS —
  verify the bullet's wording is internally consistent with
  strategic_plan §8.2's revised row.

If any citation fails verification, file as `provenance-failure`.

### R2-Q4. Cross-doc consistency on v0.2.0 schema-group + Path A application

After F-PLAN-10 + F-PLAN-11 revisions, multiple surfaces describe
the v0.2.0 schema group and Path A CP application status. Verify:

| Surface | What it should say |
|---|---|
| AGENTS.md D4 | "W52 + W58D claim-block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)" |
| tactical_plan §6.1 schema-group | "weekly-review tables + W58D claim-block (one group)" |
| tactical_plan §9.1 W-30 list | "W52 + W58D claim-block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)" |
| PLAN.md §6 application status | CP-W30-SPLIT applied-pre-cycle to AGENTS.md D4 + "Do Not Do" |
| CP-W30-SPLIT.md status | applied at v0.1.14 D14 round 1; W58D claim-block addition noted |
| CP-PATH-A.md status | applied-pre-cycle; F-PLAN-07 propagation gaps closed |

Any inconsistency between these surfaces is a `settled-decision-conflict`.

### R2-Q5. Empirical-settling shape

Note your round-2 finding count.

- **0-2 findings:** PLAN can close at round 2; standard mechanical
  fix-and-accept-revisions path.
- **3-5 findings:** round 3 likely; PLAN still on track for the ≤5
  round acceptance gate.
- **6+ findings:** signal that round-1 revisions introduced more
  drift than they fixed; recommend maintainer re-scope per §1.3.1
  rather than continuing rounds.

Round 1 was 12 findings; if round 2 is 12+, the audit chain is
under-converging.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_14/codex_plan_audit_round_2_response.md`:

```markdown
# Codex Plan Audit Round 2 Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS | PLAN_INCOHERENT

**Round:** 2

**Round-1 follow-through summary:** <of the 12 round-1 findings, how
many revisions landed cleanly, how many partial, how many didn't land>

## Findings

### F-PLAN-R2-01. <short title>

**Q-bucket:** R2-Q1 / R2-Q2 / R2-Q3 / R2-Q4 / R2-Q5
**Severity:** unfinished-revision | second-order-issue | provenance-failure |
settled-decision-conflict | sizing-mistake | acceptance-criterion-weak |
absence | nit
**Reference:** PLAN.md / tactical_plan / strategic_plan / AGENTS.md /
CP-* § X, line N
**Argument:** <citation-grounded; what's wrong + what source it should match>
**Recommended response:** <revise as follows / accept / disagree with reason>

### F-PLAN-R2-02. ...

## Empirical-settling note (per R2-Q5)

<one paragraph: round-2 finding count, expected round-3 yield,
recommendation on whether to close at round 2 or continue>
```

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle; PLAN is ready for Phase 0
  (D11) bug-hunt.
- **PLAN_COHERENT_WITH_REVISIONS** — name must-fix findings;
  maintainer applies; round 3 verifies (or closes at round 2 if
  findings are trivial).
- **PLAN_INCOHERENT** — do not open. Re-author named sections;
  re-run audit. **Unlikely at round 2** given round-1 verdict was
  PLAN_COHERENT_WITH_REVISIONS.

---

## Step 5 — Out of scope

- Re-auditing PLAN's strategic posture (settled at round 1).
- Re-auditing the 14-W-id catalogue + scope (settled at round 1).
- Re-auditing Path A vs Path B (settled at OQ-B 2026-05-01).
- The strategic-research audit chain
  (`post_v0_1_13/strategic_research_2026-05-01.md`) — already
  Codex-audited rounds 1+2 and closed.
- Code changes against this PLAN (Phase 0 hasn't started).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14 r1] Codex plan audit ← done 2026-05-01
  [D14 r1 response] Maintainer round-1 response ← done 2026-05-01
  [D14 r1 revisions] Applied to PLAN + tactical + strategic + AGENTS
                     + 5 CP files ← done 2026-05-01
  [D14 r2] Codex plan audit ← you are here
  Maintainer round-2 response
  Round-2 revisions if warranted (or close at r2)
  ...continue until PLAN_COHERENT (≤5 rounds per §3 ship-gate)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (12 personas pre-W-EXPLAIN-UX P13)
  Optional Codex external bug-hunt
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds (IR):
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md → ship to PyPI
```

Estimated round-2 review duration: 1 session. Round 2 is
verification, not re-analysis.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_14/codex_plan_audit_round_2_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_14/PLAN.md` (revisions, if warranted) —
  maintainer applies in response.
- `reporting/plans/tactical_plan_v0_1_x.md`,
  `reporting/plans/strategic_plan_v1.md`, `AGENTS.md`,
  `reporting/plans/post_v0_1_13/cycle_proposals/CP-*.md` (revisions
  to round-1 revisions, if warranted).
- `reporting/plans/v0_1_14/codex_plan_audit_round_3_prompt.md`
  (only if round 3 is warranted).

**No code changes.** No test runs. No state mutations.

---

## Reference: pre-conceded falsifiers (from round 1)

Round 1 conceded these; they remain pre-conceded in round 2:

- W-2U-GATE structural P0 blocker → cycle reshapes around fix per §1.3.
- W-2U-GATE candidate doesn't materialize → §1.3.1 procedure fires.
- W-PROV-1 schema design needs major change → v0.1.14 splits
  substrate + features.
- W-29 split breaks capabilities snapshot → rollback.
- W-Vb-3 partial-closes again → honest naming with v0.1.15
  destination.
- W-EXPLAIN-UX foreign user unavailable → §1.3.1 fallback.
- Cycle exceeds 45-day budget → defer one of W-AM/W-AN/W-FRESH-EXT.
- D14 exceeds 5 rounds → maintainer re-scopes.

If round 2 finds evidence supporting any of these *as currently
manifesting*, the corresponding workstream / acceptance criterion
adjusts automatically. Surface things round-1 *didn't* concede AND
that the round-1 revisions *introduced*.
