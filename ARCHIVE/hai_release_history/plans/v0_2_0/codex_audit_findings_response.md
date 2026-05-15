# Codex Phase 0 Audit Response - v0.2.0 Pre-PLAN

**Verdict:** PROCEED_WITH_REVISIONS

**Round:** 1 / 1 (no second round recommended)

## Findings (new - Codex sweep)

### F-PHASE0-09. Weekly-review claims need weekly claim cards, not only daily recommendation evidence cards

**Q-bucket:** Q2 / Q4
**Severity:** revises-scope
**Reference:** `reporting/plans/v0_2_0/README.md:33-35`; `reporting/plans/future_strategy_2026-04-29/review_codex.md:1484-1501`, `:1551-1566`, `:1614-1628`
**Argument:** W52/W58D require every weekly quantitative claim to resolve to evidence (`README.md:33-35`). The cited `recommendation_evidence_card.v1` sketch is daily-recommendation scoped: it has `scope="daily_recommendation"` and keys through `daily_plan_id`, `recommendation_id`, and `for_date` (`review_codex.md:1484-1501`, `:1551-1566`). The same source later says: "Future `hai review weekly`: use weekly claim cards, not daily recommendation cards, for quantitative/comparative weekly claims" and names a weekly fixture gate (`review_codex.md:1614-1628`). Treating the daily card table as W52's only carrier would under-specify aggregate claims like "4 of 7 days had plans" or "average resting HR for the week".
**Recommended response:** PLAN.md should explicitly scope a weekly claim-card / W58D claim-block carrier keyed by week, user, claim_id, prose span, derivation, and locator set. If daily `recommendation_evidence_card` lands too, name it as a related daily carrier inside the same conceptual schema group; do not imply it alone satisfies W52.

### F-PHASE0-10. Existing judge-adversarial fixtures are shape-only; W58D needs a deterministic scoring corpus

**Q-bucket:** Q1 / Q5
**Severity:** revises-scope
**Reference:** `reporting/plans/tactical_plan_v0_1_x.md:893-904`; `src/health_agent_infra/evals/cli.py:26-33`, `:100-102`; `verification/tests/test_judge_adversarial_fixtures.py:1-5`, `:49-72`
**Argument:** v0.2.0 acceptance says "W58D blocks unsupported claims" against known-good / known-bad examples (`tactical_plan_v0_1_x.md:897-898`). The existing `judge_adversarial` corpus cannot satisfy that as-is: `hai eval run --scenario-set judge_adversarial` is fixture-only and explicitly has "no scoring path until v0.2.2 W58J" (`evals/cli.py:26-33`, `:100-102`). The test surface only pins fixture shape and counts (`test_judge_adversarial_fixtures.py:1-5`, `:49-72`).
**Recommended response:** Add a W58D acceptance line for a deterministic factuality corpus and runner, with explicit counts and thresholds. Existing source-conflict fixtures can seed it, but PLAN.md should not count the W-AI/W58J shape-only corpus as the W58D blocking gate.

### F-PHASE0-11. W-2U-GATE-2 carry-forward wording drifts from D16's destination

**Q-bucket:** Q6
**Severity:** informational
**Reference:** `reporting/plans/v0_2_0/README.md:39`; `AGENTS.md:258-276`; `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md:64-72`; `reporting/plans/tactical_plan_v0_1_x.md:880-882`
**Argument:** D16 says W-2U-WEARABLE and W-2U-DOGFOOD are opportunistic-not-blocking from v0.2.0 forward and re-evaluated as hard gates at the v0.4 review (`AGENTS.md:258-276`; CP lines `64-72`). The v0.2.0 README says W-2U-GATE-2 "otherwise carries forward to v0.2.1" (`README.md:39`), and the tactical row still references sequencing after v0.1.16 empirical-fix consolidation even though v0.1.16/v0.1.19 were cancelled by D16 (`tactical_plan_v0_1_x.md:880-882`).
**Recommended response:** PLAN.md should use the D16 destination: opportunistic window in v0.2.0; if no candidate appears, record "did not fire" and leave the formal re-evaluation at v0.4 unless the maintainer deliberately creates a new v0.2.1 workstream.

### F-PHASE0-12. W-PROV-2 guidance currently mixes source-row locators with audit-chain references

**Q-bucket:** Q8
**Severity:** informational
**Reference:** `reporting/plans/v0_2_0/audit_findings.md:103-107`; `reporting/docs/archive/cycle_artifacts/source_row_provenance.md:42-46`; `src/health_agent_infra/core/state/migrations/019_intent_item.sql:19`; `src/health_agent_infra/core/state/migrations/020_target.sql:15`; `src/health_agent_infra/core/state/migrations/003_synthesis_scaffolding.sql:72`; `src/health_agent_infra/core/state/migrations/021_data_quality.sql:20`
**Argument:** F-PHASE0-01's likely fix says to add `intent_log`, `target_log`, `recommendation_log`, `x_rule_firing_log`, `review_outcome`, and `data_quality_log` to `_ALLOWED_TABLES_PK` (`audit_findings.md:103-107`). That conflicts with the W-PROV-1 contract, which says source-row locators must name evidence / accepted-state tables and "never a write-side table" (`source_row_provenance.md:42-46`). Several names also do not exist as written: current tables are `intent_item`, `target`, `x_rule_firing`, and `data_quality_daily` (`019_intent_item.sql:19`, `020_target.sql:15`, `003_synthesis_scaffolding.sql:72`, `021_data_quality.sql:20`).
**Recommended response:** Keep `_ALLOWED_TABLES_PK` for source/evidence locators. Put write-side audit-chain references in the weekly claim-card / evidence-card provenance payload, not in `SourceRowLocator`.

### F-PHASE0-13. Abort, rollback, and conditional absorption criteria are not yet cycle-specific

**Q-bucket:** Q7
**Severity:** informational
**Reference:** `reporting/plans/v0_2_0/README.md:59-62`, `:83-91`; `reporting/plans/tactical_plan_v0_1_x.md:906-910`; `reporting/plans/v0_2_0/audit_findings.md:427-442`
**Argument:** The README names the generic `aborts-cycle` tag and ship sequence, but not v0.2.0-specific abort triggers or rollback shape (`README.md:59-62`, `:83-91`). This matters because v0.2.0 is schema-bearing (`tactical_plan_v0_1_x.md:906-910`). F-PHASE0-08 also leaves absorb-vs-defer for runtime-event observability to PLAN author choice without a criterion (`audit_findings.md:427-442`).
**Recommended response:** PLAN.md should add a small risk/decision section: abort if W-PROV-2 cannot produce locators inside the agreed budget or W58D cannot hit its corpus threshold; rollback is forward-only migration / hotfix, not `git revert`; F-PHASE0-08 absorbs only if missing failed-run errors affect W52 fixture weeks or exceed a named threshold.

## Findings (review of Claude's 8)

- **F-PHASE0-01 agree-with-additions** - The finding stands. Add that recovery R6 is not totally dormant (`domains/recovery/policy.py:180-188`, `:215-230`), but it is one rule-specific path, not a general per-domain quantitative provenance system. Also revise the proposed W-PROV-2 whitelist per F-PHASE0-12.
- **F-PHASE0-02 agree** - Weekly coverage / partial-week semantics must be explicit.
- **F-PHASE0-03 agree-with-additions** - The data-quality surface is narrower than the finding implies. `data_quality_daily` stores freshness hours, coverage, missingness, and flags, but not `last_successful_sync_at`, `for_date`, entry mode, or runtime failure cause (`core/data_quality/projector.py:90-123`; `021_data_quality.sql:20-40`). W52 will need joins to `sync_run_log` / `runtime_event_log` or a schema extension.
- **F-PHASE0-04 agree-with-additions** - The schema-group count can remain one, but the carrier must resolve the daily-card vs weekly-claim-card distinction in F-PHASE0-09 before PLAN.md claims the schema shape.
- **F-PHASE0-05 agree** - Existing `hai review` is `schedule` / `record` / `summary`; weekly is greenfield (`cli/__init__.py:1141-1253`).
- **F-PHASE0-06 agree** - W48 is outcome-token aggregation, not the W52 weekly aggregation base (`core/review/summary.py:1-23`).
- **F-PHASE0-07 agree** - The multi-canonical supersession day is good fixture material.
- **F-PHASE0-08 agree-with-additions** - The defer path is viable only if W52 explicitly surfaces "failure cause unknown" and the PLAN names when that is acceptable versus when observability must be fixed in v0.2.0.

## Open questions for maintainer

1. Should v0.2.0 land daily `recommendation_evidence_card` plus weekly claim cards, or only the weekly claim-block carrier needed for W52/W58D?
2. What W58D corpus threshold is acceptable for PLAN.md: exact 100% over a smaller deterministic corpus, or a larger corpus with explicit block/pass percentages?
3. Does W-2U-GATE-2 remain a v0.2.0-only opportunistic window with v0.4 re-evaluation, or do you want a deliberate v0.2.1 carry-forward row despite D16?
