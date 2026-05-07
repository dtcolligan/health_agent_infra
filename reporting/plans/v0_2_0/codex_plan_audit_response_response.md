# D14 Round 1 Maintainer + Claude Response — v0.2.0 PLAN.md

**Source.** `reporting/plans/v0_2_0/codex_plan_audit_response.md` (Codex
verdict `PLAN_COHERENT_WITH_REVISIONS`; 10 findings; 3 OQs).

**Round 1 outcome.** Round 1 caught 10 substantive findings, matching
the empirical norm settling shape. Verifying every citation against
the codebase + PLAN.md, all 10 stand. **No disagreement** — round 1
was unusually clean and all findings are accepted.

**Round 1 settling.** 10 findings is consistent with the v0.1.11 +
v0.1.12 + v0.1.17 substantive-PLAN R1 baseline (10 / 10 / 11
findings). Per v0.1.x retro Lesson 1, expect round 2 to surface
3-5 second-order issues from the round-1 fixes; round 3 0-2;
empirical settling shape `10 → 5 → 3 → 0`.

**Verdict accepted: PLAN_COHERENT_WITH_REVISIONS.** PLAN.md revised
in place; round 2 prompt authored.

---

## Finding-by-finding dispositions

All 10 findings: **accept; revise PLAN.md as recommended.**

### F-PLAN-01 — accepted

**Disposition.** Accept fully. The strength-domain accepted-state
table is `accepted_resistance_training_state_daily` per
`core/state/migrations/001_initial.sql:281` and
`core/synthesis.py:471`. My PLAN named a non-existent
`accepted_strength_state_daily`. **Embarrassing miss; classic Q8
provenance-discipline failure.** v0.1.x retro Lesson 1 explicitly
names this as the round-2-finds-it pattern; Codex caught it round 1.

**PLAN.md revisions:**
- §2.A whitelist code block: replace `accepted_strength_state_daily`
  with `accepted_resistance_training_state_daily`.
- §2.A acceptance #5 (new): introspection check against
  `core/synthesis.py:_ACCEPTED_STATE_TABLES` to prevent future
  drift.
- §2.A added explicit round-1 correction note citing migrations
  + synthesis paths.

### F-PLAN-02 — accepted

**Disposition.** Accept fully. Acceptance #4's `≥4 of 6 domains`
denominator conflated already-wired recovery (W-PROV-1, v0.1.14)
with W-PROV-2's 5-dormant scope. Acceptance #2 (per-domain emission
≥1 path) was incorrectly NOT in the release-blocker list.

**PLAN.md revisions:**
- §2.A acceptance #4: metric changed to "5 of 5 dormant domains
  produce ≥1 row with non-null `evidence_locators_json`."
- §2.A ship-claim gate: item 2 (per-domain emission) added to
  release-blocker list.
- §2.A added explicit partial-closure path (per F-PLAN-02 +
  Codex Q3 disposition): if W-PROV-2 cannot land all 5
  dormant domains within 6d budget, fork-defer late-domain(s)
  to v0.2.1 W-PROV-3; W52 must suppress quantitative claims for
  deferred-domain prose.

### F-PLAN-03 — accepted

**Disposition.** Accept fully. The abstain template ("Plans found:
3 of 7 days, threshold: ≥5") is quantitative; my "no claim cards
on abstain because abstain prose is non-quantitative" framing was
incoherent.

**PLAN.md revisions:**
- §2.D abstain section: rewrite framing. Abstain metadata IS
  quantitative; validated outside W58D via deterministic-by-
  construction substitution from query output + `thresholds.toml`
  literal substitution.
- New test (`test_review_weekly_abstain_metadata.py`) seeds a
  fixture state DB with 3 plan-days in 7-day window; asserts
  rendered prose substitutes queried counts + threshold + date
  lists exactly.
- Explicit framing correction: abstain claims are validated, just
  via a stricter deterministic-substitution path than W58D's
  prose-authored gate.

**Path chosen (Codex offered two).** Path B (validate outside
W58D via deterministic-substitution test). Path A (write claim
cards for abstain metadata) is more rigorous in framing but
adds complexity for a fixed prose template that mechanically
derives from query output. The substitution test is structurally
equivalent at lower cost.

### F-PLAN-04 — accepted

**Disposition.** Accept fully. `sync_run_log.mode` already exists
per `migrations/008_sync_run_log.sql:41`. Adding a duplicate
`entry_mode` column would have introduced an unbudgeted schema
change outside the evidence-card family.

**PLAN.md revisions:**
- §2.D data-quality rollup section: derive `retrospective_manual`
  from existing `mode='manual'` + `for_date < started_at` (no ALTER).
- Removed proposed `entry_mode` ALTER from §2.D.

### F-PLAN-05 — accepted

**Disposition.** Accept fully. The "evidence-card family + weekly
aggregation tables" wording implied W52 had its own aggregation
tables. W52 actually produces in-memory aggregations only;
`weekly_claim_card` (migration 028) is the only weekly persistence
surface.

**PLAN.md revisions:**
- §1.4 schema-group description: clarified to "evidence-card
  family" = migrations 027 + 028 only; W52 ships no migration.
- §4 R-V0.2.0-05 mitigation: aligned with the §1.4 clarification.

### F-PLAN-06 — accepted

**Disposition.** Accept fully. The 5 sub-categories were
incorrectly cited as all-from-`review_codex.md:1597-1602`; actual
source has 3 (source-quality, x-rule, source-signal); 2 are W58D
additions (source-row-drift, audit-ref-orphan). Sub-category
counts (≥85 known-bad) didn't match headline (≥75 known-bad);
the "overlap budget" was hand-wave.

**PLAN.md revisions:**
- §2.F corpus section: provenance reworded; 3 from
  `review_codex.md:1599-1602` named explicitly, 2 added by W58D.
- Sub-category table refactored with explicit Source column.
- Headline ≥75 → ≥85 known-bad to match sub-category sum.
- Manifest contract: `index.json` exposes per-fixture `category` +
  `expected_outcome` + stable `fixture_id`; scoring runner computes
  thresholds from manifest cardinality.
- Removed hard-coded "73 of 75" / "74 of 75" examples; thresholds
  now `block_count / known_bad_count ≥ 0.97` and
  `pass_count / known_good_count ≥ 0.99`.

### F-PLAN-07 — accepted

**Disposition.** Accept fully. `--scenario-set all` runs only
scored domain + synthesis sets today (`evals/cli.py:34-35`);
judge_adversarial is shape-only with no scoring path until v0.2.2
W58J (`evals/cli.py:26-29, :100-138`). My G4's "100% pass-rate over
135 + 30 + factuality" gate counted shape-only fixtures as scored;
meaningless.

**PLAN.md revisions:**
- §3.1 G4 split into G4a (scored: deterministic + factuality at
  100%) + G4b (judge_adversarial shape-integrity summary; no
  scoring assertion).
- §2.F W58D acceptance: implementation note that `--scenario-set
  all` extends to fan out factuality scenarios; the CLI-semantics
  change is in W58D scope.

### F-PLAN-08 — accepted

**Disposition.** Accept fully. F-PHASE0-13 explicitly required PLAN
to name forward-only rollback shape; my §4 risks register named
abort triggers per-WS but had no consolidated rollback subsection.

**PLAN.md revisions:**
- New §3.4 Abort + rollback shape subsection. Schema-bearing
  release; rollback is forward-only; never `git revert` of shipped
  schema. Hotfix shape is `v0.2.0.1` with forward migration 029.
  v0.1.14.1 + v0.1.15.1 named as precedents.
- Cycle-abort triggers table covering all 5 risk register entries
  with explicit action (fork-defer / cycle-abort / absorb / etc).
- W58D corpus-failure abort path: cycle aborts at G3 if thresholds
  not met after corpus + threshold revision.

### F-PLAN-09 — accepted

**Disposition.** Accept fully. The stub-then-fill contingency in
R-V0.2.0-03 contradicted W-EVCARD-DAILY's release-blocker
acceptance items + maintainer Q1's "always more rigorous" + AGENTS.md
"honest partial-closure naming" pattern.

**PLAN.md revisions:**
- §4 R-V0.2.0-03 mitigation: replaced stub-then-fill with
  honest partial-closure (`fork-defer ONE carrier to v0.2.1
  W-EVCARD-{DAILY,WEEKLY}-2` per maintainer call at trigger time).
- §3.4 abort table: stub-then-fill explicitly named as NOT an
  option per F-PLAN-09.

### F-PLAN-10 — accepted

**Disposition.** Accept fully. The cycle thesis used "every atomic
claim" while the gate logic and W-FACT-ATOM scope used
"quantitative + comparative" with qualitative pass-through. PLAN
oscillated between the two framings.

**PLAN.md revisions:**
- §1.1 Honesty boundary: rewrite to "quantitative or comparative
  factual claim"; explicit "qualitative atoms constrained to
  non-factual narration."
- §1.4 cycle thesis: rewrite to match the gate scope.
- §2.D acceptance #6: weekly cards for quantitative + comparative
  atoms; qualitative atoms emit no card. New mechanical assertion:
  qualitative atom_text contains no numeric tokens, no date tokens,
  no comparison operators.

### Codex Q1 (open-question on append-only vs latest-only) — accept append-only

**Disposition.** Per maintainer rigor preference
(`feedback_pick_rigor_over_velocity.md`), append-only is the more
rigorous choice. Audit history preserved across re-runs.

**PLAN.md revisions:**
- §2.C migration 028 schema: drop UNIQUE constraint on
  `(iso_week, user_id, claim_id)`; `card_id` is UUID-suffixed for
  append.
- §2.C cardinality section: append-only audit history explained;
  canonical-view query joins on latest `computed_at`.
- §2.C acceptance #4: re-running W52 with corrected data produces
  new card row, not in-place update.

### Codex Q2 (W52 data-quality column) — folded into F-PLAN-04

**Disposition.** Use existing `sync_run_log.mode`; no schema delta.
Already addressed in F-PLAN-04 disposition.

### Codex Q3 (W-PROV-2 abort + deferred-domain shape) — accept W52 suppression

**Disposition.** If W-PROV-2 fork-defers domain X, W52 must
suppress quantitative claims for domain X's section of the weekly
review. Mirrors v0.1.15 W-D arm-1's per-domain
`nutrition_status='insufficient_data'` shape at weekly grain.

**PLAN.md revisions:**
- §2.A partial-closure path: W52 suppression behaviour named
  explicitly; deferred-domain prose renders qualitative-only with
  "domain X: insufficient provenance — quantitative claims
  suppressed pending v0.2.1 W-PROV-3" disposition.

---

## Round 1 → Round 2 transition

**Empirical expectation per v0.1.x retro Lesson 1:** round 2 catches
3-5 second-order issues introduced by round-1 fixes. The most
common patterns:

- **Stale propagation.** F-PLAN-X's fix at §A doesn't propagate to
  §B which references the same item. (One caught proactively
  during this round-1 fix-applying: §2.F acceptance #2 still said
  "≥75 known-bad" after the §-Corpus-shape update raised it to
  ≥85; corrected pre-round-2.)
- **New incoherence.** F-PLAN-X's fix introduces wording that
  conflicts with elsewhere. The append-only weekly-card change
  (Codex Q1) may interact with the `claim_id` idempotency claim;
  round 2 may find drift.
- **Missing acceptance test.** F-PLAN-X's fix proposes new
  behaviour without naming the test that verifies it. F-PLAN-10's
  qualitative-non-factual mechanical assertion is a new test;
  round 2 may verify it's complete.

**Round 2 prompt** authored at
`reporting/plans/v0_2_0/codex_plan_audit_round_2_prompt.md`.
Cycle pattern unchanged; round 2 reads the revised PLAN against
the round-1 dispositions.

---

## Cross-cutting observations

**The two-LLM disagreement-without-consensus-collapse posture
earned its keep again.** F-PLAN-01 (the strength-table miss) was a
provenance-discipline failure that Claude's own internal sweep had
not caught. Codex caught it because Codex's review process treats
file:line citations as adversarial — verify on disk before accepting.
Same Lesson 2 pattern as v0.1.12 D14 round 2 catch on
`core/credentials.py:171` vs actual `core/pull/auth.py:171`.

**Round 1 settling shape matches empirical norm.** 10 findings is
the centre of the v0.1.11 / v0.1.12 / v0.1.17 substantive-PLAN R1
range. Round 2 expected to settle to 3-5 findings; round 3 to 0-2.

---

*D14 round 1 response_response authored 2026-05-07 by Claude.
PLAN.md revised in place. Round 2 prompt authored. Ready for Codex.*
