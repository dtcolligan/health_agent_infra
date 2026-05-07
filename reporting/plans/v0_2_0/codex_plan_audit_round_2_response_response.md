# D14 Round 2 Maintainer + Claude Response — v0.2.0 PLAN.md

**Source.** `reporting/plans/v0_2_0/codex_plan_audit_round_2_response.md`
(Codex verdict `PLAN_COHERENT_WITH_REVISIONS`; 5 R2 findings; 2 OQs).

**Round 2 outcome.** Round 2 caught 5 substantive findings. Settling
shape **10 → 5** matches the empirical norm midpoint exactly (v0.1.11
+ v0.1.12 + v0.1.17 substantive-PLAN R1 → R2 transitions: 10 → 5,
10 → 5, 11 → 5). All 5 verified against codebase + revised PLAN.md;
all 5 stand. **No disagreement.**

**Round 2 settling.** 5 findings is exactly half of round 1's 10 —
the canonical halving signature. Round 3 expected at 2-3 findings;
round 4 verdict `PLAN_COHERENT`.

**Verdict accepted: PLAN_COHERENT_WITH_REVISIONS.** PLAN.md revised
in place; round 3 prompt authored.

---

## Finding-by-finding dispositions

All 5 findings: **accept; revise PLAN.md as recommended.**

### F-PLAN-R2-01 — accepted (stale propagation)

**Disposition.** Accept fully. F-PLAN-10 round-1 fixed §1.4 cycle
thesis but didn't propagate to §1.1 line 48 (Thread 2 W58D bullet)
or §1.2 line 70 (workstream catalogue row title). Both still said
"Every atomic claim resolves..." while the gate logic and W-FACT-ATOM
contract are explicitly quantitative + comparative only.

**This is the canonical R2 catch** per v0.1.x retro Lesson 1: round-2
catches second-order issues round-1 fixes introduced. The §1.4 fix
treated the thesis as the authoritative summary; it didn't note that
§1.1 + §1.2 are *also* summary surfaces that needed the same
rewording.

**PLAN.md revisions:**
- §1.1 W58D bullet (line 48): rewritten to "Every quantitative or
  comparative factual atom resolves to a locator OR audit-chain
  reference; otherwise the gate blocks. Qualitative atoms are
  constrained to non-factual narration and are not gated."
- §1.2 workstream catalogue row 2.F (line 70): same rewording in
  compressed form for the catalogue cell.

### F-PLAN-R2-02 — accepted (missing test)

**Disposition.** Accept fully. The deferred-domain suppression
behaviour was named in §2.A partial-closure path + §3.4 abort table
but had no W52 acceptance test. Round-1 added the behaviour as a
mitigation contract; round-2 catches the absence of the verification
gate.

**PLAN.md revisions:**
- §2.D Files of record: new test added —
  `verification/tests/test_review_weekly_deferred_domain_suppression.py`.
- §2.D acceptance new item #8: deferred-domain suppression
  release-blocker. Fixture: state DB with one dormant domain marked
  W-PROV-3-deferred. Asserts (a) no claim cards for that domain in
  `weekly_claim_card`, (b) JSON output includes
  `deferred_domains: [...]`, (c) markdown output renders the
  "insufficient provenance" disposition prose.
- §4 R-V0.2.0-01 mitigation: explicitly references the §2.D
  acceptance #8 suppression behaviour rather than the looser "ships
  against partial substrate" wording.

### F-PLAN-R2-03 — accepted (new incoherence; append-only output)

**Disposition.** Accept fully. The round-1 append-only schema change
(per Codex Q1 disposition) introduced new incoherence with §2.C
acceptance #5 (one entry per card) + §2.D acceptance #6 (count cards
= count atoms). Both assertions read like latest-only semantics; both
break under append-only on rerun.

**Resolution per Codex Q1 (round-2):** `claim_cards` JSON output =
**canonical-latest view** (one row per `(iso_week, user_id, claim_id)`
tuple, max `computed_at`). Historical (superseded) rows remain in
`weekly_claim_card` but are not in default JSON. New
`--include-history` flag exposes full append-only history (latest +
superseded) when needed.

This preserves the cycle thesis (claims resolve deterministically;
canonical-latest is the canonical view) while making append-only
audit history available for diagnosis. Per maintainer rigor preference,
canonical-latest-as-default + history-on-demand is cleaner than
either-or.

**PLAN.md revisions:**
- §2.D acceptance new item #9: canonical-latest output semantics
  release-blocker. Rerun fixture asserts (a) `weekly_claim_card`
  has 2 rows after rerun-with-mutation (append-only), (b) default
  `--json` returns 1 row per `claim_id`, (c) `--json --include-history`
  returns both rows.
- §2.D acceptance #11 (was #9): `hai capabilities --json` regenerates
  with **4 flags** on `hai review weekly` — added `--include-history`.
- §2.D Files of record: implicit (test surface absorbed into
  `test_review_weekly.py` rerun fixture; no new file).

### F-PLAN-R2-04 — accepted (new incoherence; carrier fork-defer DAG conflict)

**Disposition.** Accept fully. The R1 fork-defer mitigation (replacing
stub-then-fill per F-PLAN-09) was internally unsound: §1.3 sequencing
explicitly says W-EVCARD-WEEKLY aggregates over W-EVCARD-DAILY, so
the carriers are NOT interchangeable. Deferring weekly removes
W52/W58D's claim-card surface entirely. Deferring daily contradicts
the weekly-aggregates-over-daily dependency unless W52 is reauthored
with a non-daily-card evidence path — and that reauthor IS the
cycle-abort + D14-re-author path.

**This is a stronger correction than F-PLAN-09's round-1 fix.** Round 1
removed stub-then-fill in favor of fork-defer; round 2 removes
fork-defer in favor of abort-and-D14-re-author. The carriers are
load-bearing for the cycle thesis; if either can't ship, the cycle
needs to redesign rather than ship a partial system.

**Per Codex Q2 (round-2):** "If a carrier must fork-defer, is the
intended fallback weekly-only, daily-only, or 'do not proceed without
D14 re-authoring'?" Answer: **D14 re-authoring is the only sound
fallback.** Per maintainer rigor preference, the destination cycle for
"if effort tightens" is "v0.2.0 PLAN re-author + re-D14," not "v0.2.1
W-EVCARD-{DAILY,WEEKLY}-2."

**PLAN.md revisions:**
- §3.4 abort table R-V0.2.0-03 row: rewrites mitigation to "Cycle
  aborts at G1; D14 re-author required before re-opening."
- §3.4 abort table R-V0.2.0-05 row: same correction (single-carrier
  fork-defer is unsound).
- §4 R-V0.2.0-03 Mitigation: rewrites round-1 fork-defer mitigation
  to abort-and-re-author with the DAG-conflict argument named
  explicitly.
- §4 R-V0.2.0-05 Mitigation: round-2 correction; option (a)
  fork-defer is replaced with abort-and-re-author.

### F-PLAN-R2-05 — accepted (stale propagation; R1 verification work)

**Disposition.** Accept fully. Round 1 added verification work in two
places that didn't propagate to summary surfaces:

1. F-PLAN-03 added `test_review_weekly_abstain_metadata.py` — but the
   §2.D Files of record didn't list it; W52 test count target wasn't
   updated; §3.1 G2 test count target wasn't updated.
2. F-PLAN-07 said `--scenario-set all` semantics extension goes in
   W58D acceptance — but §2.F acceptance had no item for it; §1.3
   Cross-phase merge friction didn't list `evals/cli.py` as a W58D
   touched file.

**PLAN.md revisions:**
- §2.D Files of record: new entries —
  `test_review_weekly_abstain_metadata.py` (round-1 add per F-PLAN-03)
  + `test_review_weekly_deferred_domain_suppression.py` (round-2 add
  per F-PLAN-R2-02).
- §2.D acceptance #10 (was #8): test count raised from ≥18 to ≥23
  to absorb round-1 + round-2 added tests.
- §2.F acceptance new item #6: `--scenario-set all` semantics
  extension is a release-blocker W58D acceptance line; corresponds to
  §3.1 G4a.
- §2.F acceptance #7 (was #6): test count raised from ≥25 to ≥26 to
  absorb item #6's CLI-semantics test.
- §2.F ship-claim gate: item #6 added to release-blocker list.
- §1.3 Cross-phase merge friction W58D entry: `evals/cli.py` added
  as a touched file.
- §3.1 G2 test count target: raised from `≥ v0.1.18 + 80` to
  `≥ v0.1.18 + 86` to absorb round-1 + round-2 W52 + W58D growth.

### Codex Q1 — folded into F-PLAN-R2-03 (canonical-latest)

**Disposition.** Canonical-latest as default; `--include-history` for
full audit history. Already addressed in F-PLAN-R2-03 disposition.

### Codex Q2 — folded into F-PLAN-R2-04 (D14 re-author fallback)

**Disposition.** D14 re-authoring is the only sound fallback. Already
addressed in F-PLAN-R2-04 disposition.

---

## Round 2 → Round 3 transition

**Empirical expectation per v0.1.x retro Lesson 1:** round 3 catches
2-3 third-order issues introduced by round-2 fixes. The most common
patterns at round 3:

- **Stale clauses post-round-2 wording.** F-PLAN-R2-04 turned
  fork-defer into abort-and-re-author. Does the §1.3 sequencing DAG
  still imply fork-defer is possible? Does any other doc reference
  fork-defer as an active option?
- **New acceptance items create test-count drift.** §2.D went from
  10 acceptance items to 12; §2.F went from 7 to 8. Test counts
  computed from per-item projections: did the math hold?
- **Append-only schema interactions.** F-PLAN-R2-03 added
  `--include-history` flag. Does §2.C migration 028 schema need
  to change to support it? (PLAN-author claim: no — `--include-history`
  is a query-time filter, not a schema feature; canonical-latest
  view is computed via `MAX(computed_at) GROUP BY (iso_week, user_id,
  claim_id)` aggregation.)

**Round 3 prompt** authored at
`reporting/plans/v0_2_0/codex_plan_audit_round_3_prompt.md`. Cycle
pattern unchanged; round 3 reads the round-2-revised PLAN against the
R2 dispositions.

---

## Cross-cutting observations

**The two-LLM disagreement-without-consensus-collapse posture earns
its keep again.** F-PLAN-R2-04 (carrier fork-defer DAG conflict) is
exactly the kind of catch v0.1.x retro Lesson 2 names — Codex
correctly observed that my R1 fix to F-PLAN-09 (replacing stub-then-fill
with fork-defer) introduced a new contradiction with the §1.3 DAG.
Without adversarial review, this would have surfaced at IR or
implementation time when "we can't fork-defer the daily carrier
because the weekly card needs daily evidence" became apparent during
W52 work.

**Round 2 settling shape matches empirical norm precisely.** 10 → 5
is the canonical halving. Round 3 expected at 2-3 findings; round 4
expected `PLAN_COHERENT` verdict.

**One self-caught propagation issue.** While applying R2 fixes, I
noticed §4 R-V0.2.0-05 Mitigation option (a) still said "fork-defer
ONE carrier" — the round-1 wording stale post-F-PLAN-R2-04. Fixed
pre-commit. Round 3 may catch additional similar items.

---

*D14 round 2 response_response authored 2026-05-07 by Claude.
PLAN.md revised in place. Round 3 prompt authored. Ready for Codex.*
