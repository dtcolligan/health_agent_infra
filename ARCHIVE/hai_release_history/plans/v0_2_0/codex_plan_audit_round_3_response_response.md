# D14 Round 3 Maintainer + Claude Response — v0.2.0 PLAN.md

**Source.** `reporting/plans/v0_2_0/codex_plan_audit_round_3_response.md`
(Codex verdict `PLAN_COHERENT_WITH_REVISIONS`; 3 R3 findings; **0 OQs**).

**Round 3 outcome.** Round 3 caught 3 substantive findings. Settling
shape now `10 → 5 → 3` matches the v0.1.x retro empirical norm
exactly (v0.1.11 + v0.1.12 + v0.1.17 thrice-validated). All 3
verified against codebase + revised PLAN.md; all 3 stand. **No
disagreement.** Codex returned **zero open questions** — the
narrowing scope is itself an indicator the PLAN is approaching
coherent.

**Round 3 settling.** 3 findings is centre-of-norm for R3. The
empirical pattern: stale propagation (R3-01), incomplete propagation
to all command/output surfaces (R3-02), and unallocated math
(R3-03). All three are localised + auditable.

**Verdict accepted: PLAN_COHERENT_WITH_REVISIONS.** PLAN.md revised
in place; round 4 prompt authored. **Round 4 verdict expected to be
`PLAN_COHERENT` with 0-1 nits.**

---

## Finding-by-finding dispositions

All 3 findings: **accept; revise PLAN.md as recommended.**

### F-PLAN-R3-01 — accepted (stale propagation; comparative-claim scope)

**Disposition.** Accept fully. F-PLAN-R2-01 fixed the "every atomic
claim" → "quantitative or comparative" wording in §1.1 + §1.2, but
several narrower surfaces still said "quantitative claim(s)" only.
The cycle scope is quantitative + comparative (per W-FACT-ATOM
gating); deferred-domain suppression must therefore suppress
comparative claims too, not only numeric ones.

**This is a textbook R3 catch** — narrower stale wording surviving
the R2 broader-scope fix. v0.1.x retro Lesson 1 thrice-validated:
each round catches what the previous fix introduced.

**PLAN.md revisions:**
- §0 Theme (line 13): "quoted quantitative claim" → "quoted
  quantitative or comparative factual claim."
- §2.A ship-claim gate prose (line ~201): "every quoted quantitative
  claim" → "every quoted quantitative or comparative factual claim."
- §2.A partial-closure path (line ~203): "W52 must then suppress
  quantitative claims for deferred-domain prose" → "W52 must then
  suppress quantitative AND comparative factual claims for deferred-
  domain prose"; suppression disposition prose updated to "quantitative
  and comparative claims suppressed pending v0.2.1 W-PROV-3."
- §3.4 abort table R-V0.2.0-01 row (line ~676): "W52 suppresses
  quantitative claims for deferred domains" → "W52 suppresses
  quantitative and comparative factual claims for deferred domains."
- §6 closed Codex Q3 disposition note (line ~785): same scope
  correction.

### F-PLAN-R3-02 — accepted (stale propagation; canonical-latest + --include-history)

**Disposition.** Accept fully. F-PLAN-R2-03 added canonical-latest
as default + `--include-history` flag in §2.D acceptance #9 + #11
but didn't propagate to (a) §2.C acceptance #5 (W-EVCARD-WEEKLY's
own JSON output description) or (b) §2.D CLI surface block listing
the flags.

**PLAN.md revisions:**
- §2.C acceptance #5 (line ~313): rewritten to "canonical-latest
  view — one entry per `(iso_week, user_id, claim_id)` tuple, the
  row with maximum `computed_at`. Superseded (historical) cards
  remain in `weekly_claim_card` but are NOT in default JSON output.
  `--include-history` flag exposes full append-only history."
- §2.D CLI surface block (line ~341-348): added
  `[--include-history]` to the flag list; added explanatory line
  describing the flag's behaviour + JSON-only validity.

### F-PLAN-R3-03 — accepted (math; unallocated +3 tests in G2)

**Disposition.** Accept fully. G2 target was `≥ v0.1.18 + 86` with
visible per-WS sum of +83 and "others minor" placeholder for the
remaining +3. Codex correctly flagged that "others minor" is not
auditable.

**Choice between Codex's two options.** Codex offered (a) lower G2
to +83 OR (b) keep +86 and allocate the +3 explicitly. Per
maintainer rigor preference (`feedback_pick_rigor_over_velocity.md`)
+ AGENTS.md "honest partial-closure naming" pattern: **explicit
allocation is the rigorous choice.** The +3 cross-cutting tests are
real (doc-freshness, capabilities-manifest regression, ship-gate
freshness); naming them upfront makes the count fail cleanly if
the cross-cutting work doesn't ship.

**PLAN.md revisions:**
- §3.1 G2 (line ~630): rewritten with explicit per-WS table
  including a "Cross-cutting subtotal" row of +3 with three
  named test surfaces:
  - Doc-freshness assertion (+1) — extends
    `test_doc_freshness_assertions.py` with v0.2.0 release-gate
    claims.
  - Capabilities-manifest regression (+1) — new flags shape
    contract pinned by `test_capabilities_manifest_schema.py`
    extension.
  - Ship-gate freshness (+1) — tier annotation first-line
    assertion + AGENTS.md D-entry sweep at RELEASE_PROOF author
    time.
- Removed "others minor" placeholder.

---

## Round 3 → Round 4 transition

**Empirical expectation per v0.1.x retro Lesson 1:** R4 verdict-only
with 0-1 nits. The thrice-validated `10 → 5 → 3 → 0` settling shape
implies R4 returns `PLAN_COHERENT` cleanly.

**Why R4 is likely zero-finding:**
- R3-01 fixes are localised wording substitutions across 5 specific
  sites; verifiable.
- R3-02 fixes are 2 specific edits in §2.C + §2.D; verifiable.
- R3-03 is a math reconciliation; verifiable.
- No new architectural decisions introduced by R3 fixes (unlike R1's
  fork-defer mitigation which created the F-PLAN-R2-04 contradiction).

**Possible R4 catches** (low probability):
- A summary surface I didn't update for F-PLAN-R3-01 (Codex was
  thorough but a non-cited site might exist).
- Math arithmetic disagreement (the +3 cross-cutting allocation may
  have a counter-argument from Codex's perspective).
- A documentation cross-reference to a renumbered acceptance item
  (R3 didn't renumber, so this is unlikely).

**Round 4 prompt** authored at
`reporting/plans/v0_2_0/codex_plan_audit_round_4_prompt.md`. Cycle
pattern unchanged; R4 reads R3-revised PLAN against R3 dispositions.
**R4 prompt explicitly frames the round as verdict-only-likely** so
Codex doesn't over-search for findings.

---

## Cross-cutting observations

**Three rounds of settling, three rounds of canonical R-N catches:**
- R1 (10 findings): first-order architectural issues + provenance
  gaps + missing scope clauses. F-PLAN-01 (wrong table name) +
  F-PLAN-09 (stub-then-fill contradiction) were the most structural.
- R2 (5 findings): second-order issues introduced by R1 fixes.
  F-PLAN-R2-04 (carrier fork-defer DAG conflict) was the canonical
  R2 catch — R1 fix to F-PLAN-09 introduced new contradiction with
  the §1.3 DAG.
- R3 (3 findings): third-order propagation gaps + math. R3-01
  (comparative-claim scope) was the canonical R3 catch — R2's broader
  scope fix didn't reach all summary surfaces.

The audit chain is doing exactly what v0.1.x retro Lesson 1
predicted: each round catches what the previous round's fix
introduced. Pretending it doesn't would mean shipping with R3-class
issues uncaught.

**Codex returned 0 open questions in R3** — first time across the
3 rounds. The narrowing OQ count is itself a settling signal: R1
had 3 OQs (substantive design choices), R2 had 2 OQs (canonical-
latest + fork-defer fallback), R3 had 0 OQs. R4 should return 0
findings + 0 OQs to close the chain.

---

*D14 round 3 response_response authored 2026-05-07 by Claude.
PLAN.md revised in place. Round 4 prompt authored. Ready for Codex
verdict-only round.*
