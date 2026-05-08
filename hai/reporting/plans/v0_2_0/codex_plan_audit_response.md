# Codex Plan Audit Response — v0.2.0 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

**Round:** 1 / 4

## Findings

### F-PLAN-01. W-PROV-2 names a non-existent strength accepted-state table

**Q-bucket:** Q8 / Q6
**Severity:** provenance-gap
**Reference:** `PLAN.md` §2.A, lines 165-174; `src/health_agent_infra/core/state/migrations/001_initial.sql:281`; `src/health_agent_infra/core/synthesis.py:466-472`
**Argument:** The proposed `_ALLOWED_TABLES_PK` extension includes `accepted_strength_state_daily`. That table does not exist. The current schema uses `accepted_resistance_training_state_daily`, and the synthesis domain table list maps that table to the `strength` domain. A whitelist entry for the non-existent table would validate locators that cannot resolve.
**Recommended response:** Replace `accepted_strength_state_daily` with `accepted_resistance_training_state_daily` anywhere PLAN.md names the W-PROV-2 whitelist or W52 accepted-state query set. Add a W-PROV-2 acceptance item that introspects current schema table names before accepting the whitelist.

### F-PLAN-02. W-PROV-2 release-blocker metric can pass with dormant domains still uninstrumented

**Q-bucket:** Q5
**Severity:** acceptance-criterion-weak
**Reference:** `PLAN.md` §2.A, lines 185-190 and 200
**Argument:** The workstream is scoped as locator emission for the 5 dormant domains, but acceptance item 4 says the regression metric is `≥4 of 6 domains` after running `hai daily`. That denominator includes recovery, which is not part of the 5-domain W-PROV-2 gap. Also, item 2 ("each domain's policy module emits ≥1 locator construction path") is not listed as release-blocker at line 200. As written, W-PROV-2 can ship while one or two dormant domains still have no effective locator emission.
**Recommended response:** Make per-domain locator emission release-blocking. Change the metric to a 5-dormant-domain denominator, or explicitly state the allowed partial closure with a named destination (`W-PROV-3`) and require W52 to suppress/abstain quantitative claims for deferred domains.

### F-PLAN-03. The abstain branch still emits unchecked quantitative claims

**Q-bucket:** Q1 / Q5
**Severity:** plan-incoherence
**Reference:** `PLAN.md` §2.D, lines 354-376 and 388-394; `PLAN.md` §2.F, lines 443-456
**Argument:** The plan says no claim cards are written on abstain because the abstain prose is "non-quantitative." The proposed abstain template nevertheless emits quantitative and date claims: `3 of 7 days`, `threshold: ≥5`, and explicit days-with/without-plan lists. Those are past-week claims and are exactly the kind of deterministic surface the cycle thesis is meant to make checkable.
**Recommended response:** Either write weekly claim cards for abstain metadata claims and run them through W58D, or move those fields into structured JSON metadata with explicit deterministic tests and state that abstain metadata is validated outside W58D. Do not call the abstain prose non-quantitative.

### F-PLAN-04. W52's `entry_mode` proposal creates an unbudgeted schema change despite existing `sync_run_log.mode`

**Q-bucket:** Q4 / Q9
**Severity:** hidden-coupling
**Reference:** `PLAN.md` §2.D, lines 378-382; `src/health_agent_infra/core/state/migrations/008_sync_run_log.sql:37-52`; `src/health_agent_infra/cli/handlers/intake.py:162-167`; `src/health_agent_infra/cli/handlers/recommend.py:528-539`
**Argument:** PLAN.md says W52 may add `sync_run_log.entry_mode`. The current table has no `entry_mode` column; it already has `mode`, and current call sites use `mode="manual"` for manual intake and `mode="csv"` / `"live"` for pull and daily paths. Adding `entry_mode` inside W52 would introduce another schema mutation outside the stated migration 027/028 evidence-card family.
**Recommended response:** Prefer revising W52 to derive `retrospective_manual` from existing `sync_run_log.mode` plus `source`. If a new column is genuinely needed, name the migration, tests, and schema-group impact explicitly before cycle open.

### F-PLAN-05. The one-schema-group claim includes unnamed W52 aggregation tables

**Q-bucket:** Q9
**Severity:** provenance-gap
**Reference:** `PLAN.md` §1.4, line 130; `PLAN.md` §2.C, lines 274-295; `PLAN.md` §2.D, lines 321-328; `PLAN.md` §4 R-V0.2.0-05, lines 685-691
**Argument:** PLAN.md frames the one schema group as "evidence-card family + weekly aggregation tables" and repeats "W52's aggregation tables" in the risk register. But §2.C only names `weekly_claim_card`, and §2.D names no W52 migration or aggregation table. This leaves the C6 schema-count argument under-specified: either W52 has no separate aggregation tables, or they are missing from the migration/workstream contract.
**Recommended response:** Clarify that the only weekly persistence table is `weekly_claim_card`, or name the W52 aggregation table(s), migration slot, indexes, and acceptance tests. If separate aggregation tables exist, re-evaluate whether the "one schema group" claim still holds.

### F-PLAN-06. W58D corpus provenance and denominator math are under-specified

**Q-bucket:** Q8 / Q10 / Q5
**Severity:** provenance-gap
**Reference:** `PLAN.md` §2.F, lines 459-473; `reporting/plans/future_strategy_2026-04-29/review_codex.md:1597-1602`
**Argument:** PLAN.md says all five known-bad sub-categories are "per `review_codex.md:1597-1602`." That source only names three conflict categories: source-quality, x-rule, and source-signal. Source-row drift and audit-ref orphan are good W58D-specific categories, but they are not in the cited source. Separately, the category minimums sum to 85 known-bad tags while the headline corpus minimum is ≥75 known-bad fixtures; the "overlap budget" needs an auditable manifest contract.
**Recommended response:** Reword the provenance: first three categories from `review_codex.md`, two added by W58D. Require `index.json` to expose distinct fixture counts and category tags, and compute the 97% / 99% thresholds from actual known-bad / known-good counts rather than hard-coding examples like `73 of 75`.

### F-PLAN-07. `--scenario-set all` gate conflates scored fixtures with shape-only judge fixtures

**Q-bucket:** Q5 / Q10
**Severity:** acceptance-criterion-weak
**Reference:** `PLAN.md` §3.1 G4, lines 603-605; `reporting/docs/current_system_state.md:19-20`; `src/health_agent_infra/evals/cli.py:26-35`, `:100-138`, `:141-158`
**Argument:** G4 says `hai eval run --scenario-set all` maintains a 100% pass-rate over 135 deterministic + 30 judge_adversarial + new factuality corpus fixtures. Today `all` runs only scored domain + synthesis sets; judge_adversarial is explicitly shape-only and emits a summary with "no scoring until v0.2.2". Counting those 30 fixtures in a 100% pass-rate gate is not currently meaningful.
**Recommended response:** Split the gate: scored `all` should cover deterministic domain/synthesis + W58D factuality fixtures, while judge_adversarial remains a separate shape-integrity summary until W58J. If v0.2.0 changes `all` semantics, specify that CLI change in W58D acceptance.

### F-PLAN-08. F-PHASE0-13 rollback shape was not absorbed

**Q-bucket:** Q7
**Severity:** absence
**Reference:** `audit_findings.md` F-PHASE0-13, lines 614-622; `PLAN.md` §4, lines 639-693
**Argument:** F-PHASE0-13 asked the PLAN to name forward-only rollback / hotfix shape for a schema-bearing release. PLAN.md has transactional rollback tests for daily card insertion, but no cycle rollback section for post-ship schema issues. It also names W58D threshold revision but not what happens if W58D cannot hit the release threshold without weakening the thesis.
**Recommended response:** Add a rollback/abort subsection: schema-bearing hotfixes are forward-only (`v0.2.0.1` migration or feature flag), never `git revert` of a shipped schema release; W58D failure to meet accepted thresholds either aborts cycle open/ship or defers the gate with an explicit thesis change and D14 rerun.

### F-PLAN-09. Stub-then-fill daily-card contingency conflicts with the release-blocker carrier contract

**Q-bucket:** Q7 / Q9
**Severity:** hidden-coupling
**Reference:** `PLAN.md` §1.4, lines 140-142; `PLAN.md` §2.B, lines 248-262; `PLAN.md` §4 R-V0.2.0-03, lines 661-668; `AGENTS.md:386-396`
**Argument:** Maintainer adjudication says daily + weekly carriers both ship in v0.2.0. W-EVCARD-DAILY acceptance then makes migration, one-card-per-recommendation, rollback, payload validation, and explain consumption concrete. R-V0.2.0-03 later says the daily card may ship as "stub-then-fill" with full payload in v0.2.1, but it does not identify which §2.B acceptance items are waived or name an honest partial-closure workstream.
**Recommended response:** Remove the stub-then-fill contingency, or rewrite it as explicit partial closure: `W-EVCARD-DAILY partial-closure → v0.2.1 W-EVCARD-DAILY-2`, with revised acceptance, release-proof wording, and D14 re-review.

### F-PLAN-10. The W58D claim scope oscillates between "every atomic claim" and quantitative/comparative only

**Q-bucket:** Q1 / Q5
**Severity:** plan-incoherence
**Reference:** `PLAN.md` §1.1, line 48; `PLAN.md` §1.4, line 146; `PLAN.md` §2.D, line 394; `PLAN.md` §2.E, lines 419-422; `PLAN.md` §2.F, lines 445-456
**Argument:** The catalogue says every atomic claim resolves or blocks, while W-FACT-ATOM says qualitative atoms pass through and W52 acceptance checks only quantitative claim-card coverage. The thesis says claims about the past week resolve deterministically. If W52 emits qualitative past-week claims, those claims may bypass W58D under the current contract.
**Recommended response:** Align the wording and tests. Either constrain W52 prose so ungated qualitative atoms contain no factual past-week claims, or extend claim cards/W58D to cover qualitative factual claims with a deterministic rule. At minimum, replace "every atomic claim" with "every quantitative/comparative factual claim" everywhere and add an acceptance test proving qualitative pass-through is non-factual narration only.

## Open questions for maintainer

1. Should weekly claim cards be latest-only derived artifacts, or append-only audit artifacts? `INSERT OR REPLACE` plus `computed_at` gives latest-only state, not history.
2. Is the W52 data-quality distinction intended to use current `sync_run_log.mode`, or is a new schema column desired despite the one-group constraint?
3. If W-PROV-2 exceeds the 6d abort trigger, should the cycle really ship W52/W58D with partial domain provenance, or should W52 suppress all deferred-domain quantitative claims?
