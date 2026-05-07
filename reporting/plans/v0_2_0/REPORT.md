# v0.2.0 Cycle Report

**Cycle close:** 2026-05-07 (Phase 3 + Phase 5 prep complete; D15
IR + maintainer manual TTY ship gate pending).

**Tier:** substantive (per AGENTS.md D15) — 11 W-ids, 3 release-
blocker workstreams (W52 + W-FACT-ATOM + W58D), 2 schema migrations
(027 + 028), 2 new CLI surfaces (`hai review weekly` +
`--scenario-set factuality`), 1 architectural addition (deterministic
factuality gate as the cycle thesis surface).

## §1 What v0.2.0 is

The Wave 2 gateway. Three propositions land together:

1. **Provenance is end-to-end populated.** v0.1.14 shipped
   W-PROV-1 (recovery). v0.2.0 W-PROV-2 fills the 5 dormant
   domains (running, sleep, stress, strength, nutrition) using
   the maintainer-chosen "option C" hybrid emission — always-emit
   row-level baseline + column-level citations on spike-shaped
   R-rule firings. Every recommendation now carries a source-row
   locator on its `evidence_locators` field.

2. **Daily and weekly evidence carry per-claim provenance.** Two
   new schema migrations: `recommendation_evidence_card` (027)
   writes one card per recommendation inside `BEGIN EXCLUSIVE` (so
   rollback proves no card survives a failed synth);
   `weekly_claim_card` (028) writes one card per quantitative or
   comparative atomic claim emitted by the weekly review. The
   weekly carrier is append-only (Codex Q1 disposition): re-running
   a weekly review with corrected data appends a new card with a
   new UUID-suffixed `card_id`; the canonical-latest view returns
   the most-recent card per `claim_id`. The full append-only
   history is exposed by `--include-history`.

3. **Factuality is enforced by a deterministic gate, not a model.**
   The cycle's thesis. `hai review weekly` invokes W58D before
   rendering. Every quantitative or comparative atom is validated
   against four lanes: ① locator validates per W-PROV-1 + resolves
   to a row at the cited `row_version` (drift detection), ②
   locator-cited `column` is non-NULL on the row (source-signal-
   conflict), ③ each audit-chain primary key resolves in its cited
   table (audit-ref-orphan), ④ `x_rule_firing` audit_refs are not
   in the user's `review_outcome.disagreed_firing_ids` history
   (x-rule-conflict). Qualitative atoms pass through. Threshold
   acceptance: block ≥97% known-bad / pass ≥99% known-good over a
   ≥150-fixture deterministic corpus. **Empirical this cycle:
   100% / 100% over 160 fixtures (85 known-bad + 75 known-good).**

## §2 Highlights

- **Audit-chain shape twice-validated.** D14 plan-audit settled at
  the canonical 10 → 5 → 3 → 1-nit shape over 4 rounds — same shape
  as v0.1.11 + v0.1.12 + v0.1.18, now four-times-empirically-validated.
- **F-PLAN-10 alignment fix discovered by W-FACT-ATOM.** The
  parser's structural classifier surfaced four hidden alignment
  holes in W52's qualitative atoms (deferred-domain disposition,
  goal-abstain shell example, goal-abstain "below" positional,
  footer conditional count). All 4 fixed in `bfc8722` with a new
  regression test exercising F-PLAN-10's mechanical assertion
  against deferred bundles. The original W52 test only ran against
  non-deferred bundles, hiding the holes; the new test closes the
  gap.
- **W58D deterministic gate ships at 100/100.** Both threshold
  buckets exceed the 97/99 floor by 3 / 1 percentage points. The
  parser-corpus (atomic_claims) is at 100% precision + 100% recall
  on 243 ground-truth atoms.
- **Persona matrix release gate clean.** 13/13 personas, 0 findings,
  0 crashes — same baseline as v0.1.17 + v0.1.18.

## §3 Scope discipline + named deferrals

Three honesty-boundary gates active per PLAN §3.3:
- **G15** — RELEASE_PROOF does NOT claim foreign-user empirical
  validation (W-2U-WEARABLE + W-2U-DOGFOOD remain v0.4-deferred per
  D16; W-2U-INSTALL closed verbal-only by the post-v0.1.18 session).
- **G16** — RELEASE_PROOF does NOT claim LLM-judge factuality
  (W58J is v0.2.2; W58D ships deterministic-only).
- **G17** — RELEASE_PROOF does NOT claim insight-ledger persistence
  (W53 is v0.2.1; W58D ships claim-cards only).

W-2U-GATE-2 did NOT fire — opportunistic-not-blocking per D16; no
foreign-machine candidate surfaced during the cycle window.

One parser-corpus finding deferred to a future cycle: W-PROV-1's
`pk_value_scalar` validator accepts bool because `isinstance(True,
int)` is True. The corpus fixture `fac_sq_028_pk_value_type`
documents the sneak-through; downstream the gate fail-closes
correctly via `LOCATOR_ROW_MISSING`. A future cycle could tighten
the validator to mirror D13's bool-as-int rejection (small change;
not a v0.2.0 ship blocker).

## §4 Test surface

- v0.1.18 close baseline: 2756.
- v0.2.0 Phase-3 close: 2940 passed, 4 skipped (broader gate).
- v0.2.0 ship-time (post-IR R1 close): 2943 passed, 4 skipped.
- Delta: +187 (Phase-3 close +184 + IR R1 regression +3).
  PLAN G2 floor was +86. Exceeded 2.2×.

Per-W-id growth (rough):
- W-PROV-2: +27 (Phase 1 close memory).
- W-EVCARD-DAILY: +17. W-EVCARD-WEEKLY: +15.
- W52: +54.
- W-FACT-ATOM: +24 (13 step 1 + 11 step 3) + 1 F-PLAN-10 regression.
- W58D: +46 (16 step 1 + 5 step 2 + 8 step 3 + 4 step 4 + 2 step 5
  + 4 step 6 + 3 step 7 + 4 step 8).
- IR R1 closure: +3 (F-IR-01 W58D real-schema drift regression test
  + F-IR-05 W52 multi-canonical disposition positive + negative
  regression tests).

## §5 Lessons from the cycle

1. **The F-PLAN-10 alignment-hole pattern repeats.** A mechanical
   assertion that runs only against the "happy path" misses
   adjacent paths. v0.2.0 W-FACT-ATOM-discovered F-PLAN-10 fix
   exemplifies this: the mechanical assertion was structurally
   correct but only ran against non-deferred bundles, hiding 4
   holes for ≥1 cycle. Future-cycle pattern: when adding a
   mechanical-assertion test, run it against EVERY structurally
   distinct path the assertion targets, not only the happy one.

2. **Run full pytest before every commit, not targeted tests.** The
   W-FACT-ATOM step-2 corpus commit went in with the eval-review
   walk regression — a 30-fixture data-only corpus addition broke
   `_walk_corpus`'s sort because atomic_claims fixtures don't have
   `scenario_id`. The targeted test pass at commit time missed it;
   the full suite caught it at step-3 time. The fix commit
   (`2b46bea`) is documented; the process learning is "run the
   full suite, not a targeted run, before every commit."

3. **Honest partial-closure naming applies even to data-only
   commits.** When a corpus commit changes the eval-review walk's
   environment (more JSON files at scenarios/), the eval-review
   tests reflect that environment — they're not separate concerns.
   The fix happened the same session as the regression; honest
   partial-closure naming was never violated, but the discipline
   matters going forward.

## §6 Next cycle (v0.2.1)

W53 multi-week insight ledger. Hard deps: v0.2.0 W52 surface +
W-EVCARD-WEEKLY substrate, both shipped. One schema group (single
migration). PLAN to be authored post-v0.2.0 ship.
