# v0.2.0 PLAN — Weekly review + deterministic factuality (Wave 2 gateway)

**Tier (D15):** **substantive** — W52 + W58D both release-blocker workstreams; ≥10 days estimated effort threshold easily met (post-adjudication estimate 25-37d); v0.2 is a major version bump because the schema changes (new tables) are ledger-shape mutations, not pure additions.

**Status:** **authored 2026-05-06, pre-D14 round 1.** PLAN.md is the artifact under audit; no code has changed against it. Phase 0 (D11) bug-hunt closed 2026-05-06 with verdict `PROCEED_WITH_REVISIONS` (Codex round 1; 13 F-PHASE0-* findings consolidated; persona matrix 13/13 with 0 findings + 0 crashes). Pre-implementation gate fired 2026-05-06 with maintainer adjudication of 3 Codex open questions. Cycle workspace at `reporting/plans/v0_2_0/`.

**Authored:** 2026-05-06 against HEAD `b2cf074` (Phase 0 sweep close). v0.1.18 closed cleanly 2026-05-06 (D15 IR R3 SHIP_WITH_NOTES; PyPI publish gated only on maintainer manual TTY ship gate per RELEASE_PROOF). v0.1.19 cancelled 2026-05-06 per CP-2U-GATE-SPLIT (AGENTS.md D16); v0.2.0 promoted to next-active per the cancellation chain.

**Estimated effort:** **25-37 days** (1 maintainer). See §5 arithmetic. Substantively larger than v0.1.18's 5-9-day cycle because v0.2.0 ships the Wave-2 gateway: full evidence-card family (daily + weekly carriers per maintainer Q1 adjudication "always make it more rigourous") + W52 weekly aggregation + W58D deterministic factuality gate + 4 doc-only adjuncts. Single-cycle scope is justified by the design coupling (W52 ↔ W58D per CP5; carriers ↔ W52 per F-PHASE0-09); splitting across two cycles would force schema-group churn.

**D14 expectation:** budget **2-4 rounds** per AGENTS.md empirical norm (twice-or-thrice-validated 10 → 5 → 3 → 0 settling at v0.1.11 + v0.1.12 + v0.1.17). v0.2.0's catalogue is large (11 W-ids) and the schema-bearing surface introduces hidden-coupling risks D14 will pressure-test. Realistic round expectation 3-4. **Don't bet on settling at round 1.**

**Theme.** v0.1.x produced a runtime trustworthy enough to point at on a single-day surface. v0.2.0 extends that trust across calendar time: weekly review aggregation with source-row provenance, paired with a deterministic factuality gate that blocks any quoted quantitative claim that doesn't resolve to evidence. The cycle ships against v0.1.14 substrate (W-PROV-1 locator dataclass + W-AJ judge harness), already shipped. **Foreign-user empirical evidence re-tiered to opportunistic-not-blocking per AGENTS.md D16** (CP-2U-GATE-SPLIT post-v0.1.18); v0.2.0's only remaining hard dep is v0.1.14 substrate.

**Honesty boundary.** v0.2.0 ships W58D **deterministic-only** (W58J judge ships v0.2.2 shadow-by-default per CP-PATH-A). v0.2.0's claim is **"every quoted quantitative or comparative factual claim in W52 prose resolves to a source-row locator OR a write-side audit-chain reference"** — a deterministic claim, not a factuality-judgment claim. **Qualitative atoms are constrained to non-factual narration only** (per F-PLAN-10 round-1 alignment); the W52 prose-builder is structurally prevented from emitting factual qualitative claims about the past week. The deterministic corpus + percentage thresholds (per maintainer Q2 adjudication) are honest about false-negative tolerance.

**Source inputs:**
- `reporting/plans/v0_2_0/README.md` — workspace stub + provisional W-id catalogue.
- `reporting/plans/v0_2_0/audit_findings.md` — 13 consolidated `F-PHASE0-*` findings (8 Claude internal sweep + audit-chain probe; 5 Codex round 1) with maintainer adjudication of 3 Codex open questions.
- `reporting/plans/v0_2_0/codex_audit_findings_response.md` — Codex round 1 response (verdict `PROCEED_WITH_REVISIONS`).
- `reporting/plans/post_v0_1_18/strategic_plan_v2.md` §7 Wave 2 — strategic context; v0.2.0 is release 1 of 4 in Path A.
- `reporting/plans/tactical_plan_v0_1_x.md` §6 — release-by-release detail; W52 ↔ W58D design coupling per CP5.
- `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md` (D16) — foreign-user empirical hard-dep drop for v0.2.0; W-2U-GATE-2 destination is v0.4 review (NOT v0.2.1).
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-PATH-A.md` — 4-release Wave-2 split honoring reconciliation C6 (one schema group per release).
- `reporting/plans/future_strategy_2026-04-29/review_codex.md:1480-1632` — `recommendation_evidence_card.v1` schema sketch + weekly claim-card distinction at `:1614-1615` ("use weekly claim cards, not daily recommendation cards, for quantitative/comparative weekly claims").
- `reporting/docs/archive/cycle_artifacts/source_row_provenance.md:42-46` — W-PROV-1 contract: locators name evidence/accepted-state tables, **never** write-side tables.
- `reporting/plans/v0_1_18/RELEASE_PROOF.md` — v0.1.18 ship state.
- `reporting/plans/v0_1_14/RELEASE_PROOF.md` — W-PROV-1 + W-AJ substrate v0.2.0 builds on.

---

## 1. What this release ships

### 1.1 Theme

**Make claims about the past week deterministically checkable.** Two threads, one schema group, one ship.

**Thread 1 — Substrate readiness.** Three pre-W52 substrate workstreams that close the gap between v0.1.14's locator *capability* and v0.2.0's locator *consumption*:

- **W-PROV-2** wires locator emission across the 5 dormant domains (running, sleep, stress, strength, nutrition; recovery R6 already partially wired per `domains/recovery/policy.py:215-230`). Whitelist (`core/provenance/locator.py:23`) extends with **accepted-state tables only** per W-PROV-1 contract (F-PHASE0-12); audit-chain references go in claim-card payload, not in `_ALLOWED_TABLES_PK`.
- **W-EVCARD-DAILY** ships the daily `recommendation_evidence_card.v1` carrier per `review_codex.md:1551`. Migration 027. Written inside the synthesis transaction; rolls back with the daily plan if any card insert fails.
- **W-EVCARD-WEEKLY** ships the weekly claim-card carrier (W52 + W58D consumer). Migration 028. Keyed by week + user + claim_id + prose-span + derivation + locator-set; payload carries source-row locators (validated per W-PROV-1) AND audit-chain primary-key references (validated as plain PKs, not as `SourceRowLocator` instances).

**Thread 2 — Aggregation + factuality enforcement.** Three workstreams that consume Thread-1 substrate:

- **W52** ships `hai review weekly --week YYYY-Www [--json|--markdown]`. Aggregates accepted state + intent_item + target + recommendation_log + x_rule_firing + review_outcome + data_quality_daily + sync_run_log + runtime_event_log. Filters on `superseded_by_plan_id IS NULL`. Partial-week abstain branch (`weekly_status='insufficient_data'` if coverage < threshold) per F-PHASE0-02. Data-quality rollup distinguishes `stale_pull` vs `retrospective_manual` per F-PHASE0-03. Consumes v0.1.14 W-EXPLAIN-UX prose obligations as carry-forward.
- **W-FACT-ATOM** is FActScore-shaped atomic-claim decomposition. Folds into W58D as the parsing layer that splits W52 prose into atom-level claims.
- **W58D** is the deterministic factuality gate. Every quantitative or comparative factual atom resolves to a locator OR audit-chain reference; otherwise the gate blocks. **Qualitative atoms are constrained to non-factual narration and are not gated** (per F-PLAN-10 + F-PLAN-R2-01 round-2 alignment). **Own deterministic corpus + scoring runner** (NOT the existing `judge_adversarial` shape-only fixtures per F-PHASE0-10). Acceptance: `block ≥97% known-bad / pass ≥99% known-good` over corpus of ≥150 fixtures (per maintainer Q2 adjudication; D14 pressure-tests the percentages).

**Thread 3 — Doc-only adjuncts (parallel).** Four documentation artifacts that ship alongside Threads 1+2:

- **W-MCP-THREAT** authors `reporting/docs/mcp_threat_model.md` (OWASP MCP Top 10 mapping; pre-req for v0.3 PLAN-audit per CP-MCP-THREAT-FORWARD).
- **W-COMP-LANDSCAPE** authors `reporting/docs/competitive_landscape.md` (2026-Q2 evidence refresh).
- **W-NOF1-METHOD** authors `reporting/docs/n_of_1_methodology.md` (substrate-then-estimator chain methodology).
- **W-2U-GATE-2** *(opportunistic; 0d if doesn't fire)* — second foreign-machine onboarding session if a candidate surfaces during v0.2.0. Per D16: opportunistic-not-blocking; "did not fire" in RELEASE_PROOF if no candidate; formal re-eval at v0.4 review (NOT v0.2.1 — F-PHASE0-11 README drift fix during this PLAN's authoring touch-up).

**Thread 4 — Carry-forward (folds into Thread 2 W52).**

- **W-EXPLAIN-UX-CARRY** consumes v0.1.14's `reporting/docs/explain_ux_review_*.md` "v0.2.0 W52 prose obligations" section. Each remediation item: implement OR explicitly defer with named cycle destination (per v0.1.14 PLAN F-PLAN-05). Effort folds into W52.

### 1.2 Workstream catalogue (11 W-ids)

| § | W-id | Title | Effort | Source | Severity |
|---|---|---|---|---|---|
| 2.A | **W-PROV-2** | Locator emission substrate. Extend `_ALLOWED_TABLES_PK` with accepted-state tables for 5 dormant domains (running, sleep, stress, strength, nutrition); wire emission at classify/projector/writeback paths per recovery R6 reference shape | 2-4d | F-PHASE0-01 + F-PHASE0-12 + maintainer Q1 (rigor default) | release-blocker (W52 + W58D both depend on populated substrate) |
| 2.B | **W-EVCARD-DAILY** | Daily `recommendation_evidence_card.v1` carrier (migration 027). Per-recommendation row written inside synthesis transaction; rolls back with the daily plan if any card insert fails | 3-5d | F-PHASE0-04 + F-PHASE0-09 + maintainer Q1 (daily + weekly) | release-blocker (W52 + v0.2.2 W58J judge both depend on daily-grain audit substrate) |
| 2.C | **W-EVCARD-WEEKLY** | Weekly claim-card carrier (migration 028). Keyed by week + user + claim_id + prose-span + derivation + locator-set; payload carries source-row locators AND audit-chain refs as separate lanes | 2-4d | F-PHASE0-09 + F-PHASE0-12 | release-blocker (W52 + W58D both consume) |
| 2.D | **W52** | `hai review weekly --week YYYY-Www [--json\|--markdown]` aggregation. Filter on `superseded_by_plan_id IS NULL`; partial-week `weekly_status='insufficient_data'` abstain branch with threshold in `thresholds.toml`; data-quality rollup distinguishes `stale_pull` vs `retrospective_manual` | 6-9d | tactical §6.1 + F-PHASE0-02 + F-PHASE0-03 + F-PHASE0-07 + W-EXPLAIN-UX-CARRY consumption | release-blocker (cycle thesis depends) |
| 2.E | **W-FACT-ATOM** | FActScore-shaped atomic-claim decomposition. Parser splits W52 prose into atom-level claims. Folds into W58D | 2-3d | tactical §6.1 + F-PHASE0-10 | release-blocker (W58D depends) |
| 2.F | **W58D** | Deterministic factuality gate. Every quantitative or comparative factual atom resolves to a locator OR audit-chain ref; otherwise gate blocks. Qualitative atoms not gated (per F-PLAN-R2-01). **Own deterministic corpus + scoring runner** (NOT W-AI judge_adversarial shape-only fixtures). Acceptance: `block ≥97% known-bad / pass ≥99% known-good` over corpus of ≥150 fixtures | 5-8d | tactical §6.1 + F-PHASE0-10 + maintainer Q2 (% over larger corpus) | release-blocker (cycle thesis depends; blocking from day 1) |
| 2.G | **W-MCP-THREAT** | `reporting/docs/mcp_threat_model.md`. OWASP MCP Top 10 mapping. Pre-req for v0.3 PLAN-audit per CP-MCP-THREAT-FORWARD | 2-3d | tactical §6.1 + CP-MCP-THREAT-FORWARD | doctrine-gap (load-bearing for v0.3 prereqs) |
| 2.H | **W-COMP-LANDSCAPE** | `reporting/docs/competitive_landscape.md`. 2026-Q2 evidence refresh of comparable-OSS survey | 1-2d | tactical §6.1 | doctrine-gap (positioning artifact) |
| 2.I | **W-NOF1-METHOD** | `reporting/docs/n_of_1_methodology.md`. Substrate-then-estimator chain methodology | 1-2d | tactical §6.1 | doctrine-gap (Wave-4 positioning) |
| 2.J | **W-2U-GATE-2** *(opportunistic)* | Second foreign-machine session if candidate surfaces during v0.2.0. Per D16 + maintainer Q3: opportunistic-not-blocking; v0.4 review re-eval if doesn't fire | 0-2d | D16 + maintainer Q3 | empirical-substitute |
| 2.K | **W-EXPLAIN-UX-CARRY** | v0.1.14 prose-obligations carry-forward. Each item: implement OR defer with named destination | folds into W52 | v0.1.14 PLAN F-PLAN-05 carry-forward | informational |

**Total:** 11 W-ids (10 active + 1 opportunistic), **25-37 days estimated effort** (per-WS arithmetic 24-42d, +inter-WS coordination overhead ~3-5%, -overlap savings ~5-7d; see §5), substantive tier.

### 1.3 Sequencing (DAG)

**Phase 1 — Substrate (parallelisable except where noted):**

1. **W-PROV-2** — locator-emission substrate. Lands first because W-EVCARD-DAILY + W-EVCARD-WEEKLY + W52 all depend on populated substrate. Per-domain emission can land in 5 atomic commits (one per domain) for fine-grained review.
2. **W-MCP-THREAT** — doc-only, parallelisable with W-PROV-2.
3. **W-COMP-LANDSCAPE** — doc-only, parallelisable.
4. **W-NOF1-METHOD** — doc-only, parallelisable.

**Phase 2 — Carriers (Phase 1 W-PROV-2 must be in tree):**

5. **W-EVCARD-DAILY** — migration 027, daily carrier. Lands before W-EVCARD-WEEKLY because the daily card is the per-recommendation atom that the weekly card aggregates over.
6. **W-EVCARD-WEEKLY** — migration 028, weekly carrier. Lands after W-EVCARD-DAILY.

**Phase 3 — Aggregation + factuality (Phase 2 carriers in tree):**

7. **W52** — `hai review weekly` aggregation. Consumes both carriers + reads from accepted-state + audit-chain tables. **W-EXPLAIN-UX-CARRY consumed during W52 prose authoring** as a sub-sequence.
8. **W-FACT-ATOM** — atomic-claim decomposition. Parses W52's prose output into claim atoms. Sequenced after W52 because it consumes W52's prose schema.
9. **W58D** — deterministic factuality gate. Consumes W-FACT-ATOM output + the new deterministic corpus. **Blocking from day 1** per tactical §6.1.

**Phase 4 — Opportunistic (any time during cycle):**

10. **W-2U-GATE-2** — if a candidate surfaces. 0d if doesn't fire.

**Phase 5 — Ship:**

11. D15 IR rounds (empirical 2-3 rounds, 5 → 2 → 1-nit settling).
12. RELEASE_PROOF + REPORT + AUDIT.md + CHANGELOG + ROADMAP.md + tactical_plan + current_system_state.md freshness sweep.
13. Manual TTY ship gate → `git push origin main` → `uvx twine upload`.

**Cross-phase merge friction.** All edits land in distinct files post-W-29 cli.py split:

- W-PROV-2 in `core/provenance/locator.py` (whitelist) + per-domain `domains/*/policy.py` + `core/state/projector.py` + `core/writeback/proposal.py` (emission paths). 5-6 files touched.
- W-EVCARD-DAILY in `core/state/migrations/027_*.sql` + `core/synthesis.py` (transaction-scoped writes) + `core/state/projectors/evidence_card.py` (new).
- W-EVCARD-WEEKLY in `core/state/migrations/028_*.sql` + `core/review/weekly_card.py` (new).
- W52 in `cli/handlers/review.py` + `core/review/weekly.py` (new) + `core/review/render.py` (new) + capabilities manifest extension.
- W-FACT-ATOM in `core/eval/atomic_claims.py` (new).
- W58D in `core/eval/factuality_gate.py` (new) + `evals/scenarios/factuality/` (new corpus dir) + `evals/cli.py` (extend `--scenario-set all` semantics to fan out factuality scenarios per F-PLAN-07 round-1 + F-PLAN-R2-05 round-2 propagation).
- Doc-only: `reporting/docs/{mcp_threat_model,competitive_landscape,n_of_1_methodology}.md`.

Recommended commit cadence: atomic per-W-id commits where possible (W-PROV-2 splits to 1-per-domain; carriers split to schema + emission; W52 may split to aggregation + render; W58D may split to corpus + runner). Total estimated commits: 18-25.

### 1.4 Source provenance + cycle thesis

**Chain A — Wave 2 gateway (CP-PATH-A, post-v0.1.13).** v0.2.0 is release 1 of 4 in Path A:

- v0.2.0 — W52 + W58D + W-FACT-ATOM + 4 doc-only adjuncts (this cycle).
- v0.2.1 — W53 insight ledger only.
- v0.2.2 — W58J LLM judge shadow-by-default + W-JUDGE-BIAS bias panel.
- v0.2.3 — W58J flip to blocking + W-30 capabilities-manifest schema freeze.

Reconciliation C6 (post-v0.1.13 strategic refresh) caps each release at **one schema group**. v0.2.0's group is the **evidence-card family**: migration 027 (`recommendation_evidence_card`, daily) + migration 028 (`weekly_claim_card`, weekly). **There are no separate W52 aggregation tables** — W52 produces in-memory aggregations from existing tables (accepted-state + audit-chain) plus reads/writes to `weekly_claim_card`; W52 itself ships no migration. **(Round-1 correction per F-PLAN-05: original "evidence-card family + weekly aggregation tables" wording implied W52 had its own tables; clarified that the only W52 weekly persistence surface is `weekly_claim_card` from migration 028.)** Conceptually one schema family per C6; F-PHASE0-09 (Codex) + F-PHASE0-12 (Codex) sharpen the architecture.

**Chain B — Phase 0 sweep (2026-05-06).** 13 `F-PHASE0-*` findings consolidated. 5 `revises-scope` shape this PLAN materially:

- **F-PHASE0-01** (Claude) + **F-PHASE0-12** (Codex) drove W-PROV-2's design. Original Claude finding proposed expanding `_ALLOWED_TABLES_PK` with audit-chain tables; Codex caught that this violates the W-PROV-1 contract at `source_row_provenance.md:42-46` ("never a write-side table"). Corrected architecture: locators stay source/evidence-only; audit-chain refs go in claim-card payload as separate lanes.
- **F-PHASE0-02** drove W52's partial-week abstain branch.
- **F-PHASE0-03** drove W52's data-quality rollup `stale_pull` vs `retrospective_manual` distinction.
- **F-PHASE0-09** (Codex) drove the W-EVCARD-DAILY vs W-EVCARD-WEEKLY split.
- **F-PHASE0-10** (Codex) drove W58D's "own corpus, not judge_adversarial" architecture.

**Chain C — Maintainer adjudication (2026-05-06 chat).** 3 Codex open questions adjudicated:

1. **Daily + weekly carrier.** Both ship in v0.2.0. Reasoning: "always make it more rigourous" (saved as feedback memory `feedback_pick_rigor_over_velocity.md`).
2. **Percentage thresholds over larger corpus.** W58D acceptance is `block ≥X% / pass ≥Y%` over ≥M fixtures. PLAN proposes 97% / 99% / 150 fixtures; D14 pressure-tests.
3. **W-2U-GATE-2 honors D16 v0.4 destination.** README:39 + tactical §6.1:880-882 drift per F-PHASE0-11 fixes during this PLAN's authoring; AGENTS.md D16 unchanged.

**Cycle thesis.** **v0.2.0 ships when quantitative and comparative factual claims about the past week resolve to source rows or audit-chain references, deterministically, with no LLM in the gate.** A user can run `hai review weekly --week 2026-W18 --json` and every quoted number AND every comparison ("higher than last week", "below baseline") traces back to a row the user can inspect. Qualitative atoms in the prose are constrained to non-factual narration. The factuality gate enforces this scope; the carriers ship the substrate; the locator emission populates the substrate; the doc-only adjuncts position the cycle for v0.3 prereqs. **(Round-1 alignment per F-PLAN-10: the "every atomic claim" framing was inconsistent with the W-FACT-ATOM scope (quantitative + comparative; qualitative pass-through). The cycle thesis now matches the gate.)**

**Honesty boundary (re-stated for §3 ship gates).** v0.2.0 does NOT ship the LLM judge layer (W58J, v0.2.2). v0.2.0 does NOT freeze the capabilities-manifest schema (v0.2.3 W-30). v0.2.0 does NOT ship the insight ledger (W53, v0.2.1). v0.2.0 does NOT add new domains, new live-data sources, autonomous threshold mutation, or any clinical claims (per AGENTS.md "Do Not Do" + W57 invariant). v0.2.0 ships against W58D's deterministic-only contract; the percentage-threshold framing per Q2 adjudication is honest about false-negative tolerance.

---

## 2. Per-workstream contracts

### §2.A W-PROV-2 — Locator emission substrate

**Source.** F-PHASE0-01 (Claude) + F-PHASE0-12 (Codex correction). v0.1.14 W-PROV-1 shipped the locator dataclass + validate + dedupe + serialize machinery, but no domain currently emits locators at writeback time except recovery R6 (conditional, never fired against maintainer's data; 0 of 86 recommendation_log rows carry locators).

**Files of record:**
- `src/health_agent_infra/core/provenance/locator.py:23` — `_ALLOWED_TABLES_PK` whitelist. Currently 2 tables (`accepted_recovery_state_daily`, `source_daily_garmin`); extend to include accepted-state tables for the 5 dormant domains.
- `src/health_agent_infra/domains/{running,sleep,stress,strength,nutrition}/policy.py` — wire conditional locator emission per the recovery R6 reference shape (`domains/recovery/policy.py:215-230`).
- `src/health_agent_infra/core/state/projector.py` — projector path; per-domain locator construction may live here (or in classify.py per domain's choice).
- `src/health_agent_infra/core/writeback/proposal.py:273-300` — proposal-acceptance path; reads `evidence_locators` if present.
- `verification/tests/test_provenance_locator_emission.py` (new) — pinned regression test covering one R-rule emission per domain (5 new test cases minimum).

**Whitelist extension (corrected per F-PLAN-01 round-1; verified against `core/synthesis.py:466-473` `_ACCEPTED_STATE_TABLES` mapping):**

```python
_ALLOWED_TABLES_PK: dict[str, tuple[str, ...]] = {
    "accepted_recovery_state_daily": ("as_of_date", "user_id"),
    "accepted_running_state_daily": ("as_of_date", "user_id"),
    "accepted_sleep_state_daily": ("as_of_date", "user_id"),
    "accepted_stress_state_daily": ("as_of_date", "user_id"),
    "accepted_resistance_training_state_daily": ("as_of_date", "user_id"),
    "accepted_nutrition_state_daily": ("as_of_date", "user_id"),
    "source_daily_garmin": (
        "as_of_date", "user_id", "export_batch_id", "csv_row_index",
    ),
}
```

**Round-1 correction (F-PLAN-01):** The strength-domain accepted-state table is `accepted_resistance_training_state_daily` (per `core/state/migrations/001_initial.sql:281` + `core/synthesis.py:471`), NOT `accepted_strength_state_daily`. The original PLAN proposal had a non-existent table name; corrected. Acceptance #5 below adds an introspection check against `_ACCEPTED_STATE_TABLES` to prevent recurrence.

**W-PROV-1 contract intact.** The whitelist contains **only evidence + accepted-state tables**. Per `source_row_provenance.md:42-46`: "never a write-side table (no `recommendation_log`, no `proposal_log`, no `daily_plan`). Self-citation is meaningless and a classification bug; the validator rejects it." Audit-chain references (recommendation_id, planned_id, proposal_id, firing_id, outcome_id) go in claim-card payloads (W-EVCARD-DAILY + W-EVCARD-WEEKLY), NOT in `SourceRowLocator` instances.

**Acceptance.**
1. `_ALLOWED_TABLES_PK` extended with 5 accepted-state-table entries (one per dormant domain), table names matching `core/synthesis.py:_ACCEPTED_STATE_TABLES` exactly. Validation roundtrip test passes for each.
2. Each of the 5 dormant domains (running, sleep, stress, strength, nutrition) emits ≥1 locator construction path. Wire shape mirrors `domains/recovery/policy.py:215-230`'s conditional emission. Domain may choose: (a) per-rule conditional (recovery R6 model — emit on specific R-rule firing); (b) always-emit (every classification result carries locators back to its accepted-state row).
3. Conditional vs always-emit choice is documented per domain in a new `reporting/docs/per_domain_locator_emission.md` artifact (~1 page). Documents which classification paths emit, which don't, and why.
4. **All 5 dormant domains emit at least one locator across a fixture state DB run.** Metric: regression test seeds a fixture state DB exercising one R-rule firing or always-emit path per dormant domain; asserts **5 of 5 dormant domains** produce ≥1 row with non-null `evidence_locators_json` in `recommendation_log`. Recovery is NOT in the denominator — its R6 conditional emission already shipped at v0.1.14 and is not under W-PROV-2's scope. **(Round-1 correction per F-PLAN-02: original "≥4 of 6 domains" denominator conflated already-wired recovery with W-PROV-2 scope.)**
5. **Whitelist introspection check** — new test (`test_provenance_whitelist_against_synthesis.py`) asserts `_ALLOWED_TABLES_PK` keys for accepted-state tables match `core/synthesis.py:_ACCEPTED_STATE_TABLES` first-element values. Prevents future drift like F-PLAN-01.
6. No write-side audit-chain table in `_ALLOWED_TABLES_PK`. Validator-roundtrip negative test asserts `recommendation_log`, `proposal_log`, `daily_plan`, `intent_item`, `target`, `x_rule_firing`, `review_outcome`, `data_quality_daily` all reject.
7. Full pytest suite (narrow + broader warning gates) green post-W-PROV-2.
8. `CHANGELOG.md` v0.2.0 entry names W-PROV-2 with user-facing wording "per-domain source-row provenance now populated for recommendations."

**What this WS does NOT do.**
- Does not extend the whitelist with audit-chain tables (F-PHASE0-12 correction; those go in claim-card payloads).
- Does not change locator emission for recovery R6 (already wired at v0.1.14).
- Does not change proposal-acceptance behaviour for proposals that omit `evidence_locators` (still optional per `proposal.py:278`).
- Does not introduce new R-rules or classification paths.

**Ship-claim gate:** acceptance items 1, **2**, 4, 5, 6 are **release-blocker**. **(Round-1 correction per F-PLAN-02: item 2 (per-domain emission ≥1 path) is now release-blocker — without it, dormant-domain claims have no provenance to resolve to.)** The contract claim "every quoted quantitative claim in W52 prose resolves to evidence" depends on populated substrate across all 5 dormant domains.

**Partial-closure path (per F-PLAN-02 + Codex Q3 disposition).** If W-PROV-2 cannot land all 5 dormant domains within the 6d abort budget (R-V0.2.0-01), fork-defer the late-domain(s) to v0.2.1 W-PROV-3 with explicit named-partial-closure in CARRY_OVER.md. **W52 must then suppress quantitative claims for deferred-domain prose** — the weekly review renders qualitative-only sections for any domain without locator emission, with explicit "domain X: insufficient provenance — quantitative claims suppressed pending v0.2.1 W-PROV-3" disposition.

### §2.B W-EVCARD-DAILY — Daily `recommendation_evidence_card.v1` carrier

**Source.** F-PHASE0-04 (Claude) + F-PHASE0-09 (Codex split into daily/weekly) + maintainer Q1 adjudication (daily + weekly).

**Files of record:**
- `src/health_agent_infra/core/state/migrations/027_evidence_card_daily.sql` (new) — table per `review_codex.md:1551-1566` schema sketch.
- `src/health_agent_infra/core/state/projectors/evidence_card.py` (new) — card construction logic.
- `src/health_agent_infra/core/synthesis.py` — write evidence cards inside the synthesis transaction post-recommendation-log + planned-recommendation rows; rollback if any insert fails.
- `src/health_agent_infra/core/explain/queries.py` (extend) + `render.py` (extend) — `hai explain` consumes cards.
- `verification/tests/test_evidence_card_daily.py` (new) — table + transaction + rollback + per-recommendation cardinality.

**Migration 027 shape (PLAN-author proposal per `review_codex.md:1551`):**

```sql
CREATE TABLE recommendation_evidence_card (
    card_id TEXT PRIMARY KEY,
    daily_plan_id TEXT NOT NULL REFERENCES daily_plan(daily_plan_id),
    recommendation_id TEXT NOT NULL REFERENCES recommendation_log(recommendation_id),
    planned_id TEXT REFERENCES planned_recommendation(planned_id),
    proposal_id TEXT REFERENCES proposal_log(proposal_id),
    user_id TEXT NOT NULL,
    for_date TEXT NOT NULL,
    domain TEXT NOT NULL,
    schema_version TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    computed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    ingest_actor TEXT NOT NULL,
    agent_version TEXT
);
CREATE INDEX idx_evidence_card_for_date ON recommendation_evidence_card (for_date, user_id);
CREATE INDEX idx_evidence_card_recommendation ON recommendation_evidence_card (recommendation_id);
```

**Cardinality.** Per maintainer Q1 default (per-recommendation, not per-recommendation-per-revision): one card per row in `recommendation_log` at insert time. Supersession: when a new `planned_recommendation` supersedes an existing one, the new recommendation_log row gets its own card; the old card remains as audit history. **D14 may pressure-test whether the per-revision-too variant is preferable; PLAN defaults to per-recommendation per the verbatim Codex Q1 phrasing + `review_codex.md:1551` schema (no revision column).**

**Payload shape (per `review_codex.md:1480-1545`):** `decision`, `evidence`, `source_quality`, `provenance`, `conflicts`, `review` lanes. Provenance lane carries:

- `accepted_state_rows: SourceRowLocator[]` (validated per W-PROV-1 contract)
- `raw_source_refs: SourceRowLocator[]` (validated per W-PROV-1 contract)
- `proposal_log: string[]` (proposal_id list — plain PK refs)
- `planned_recommendation: string[]` (planned_id list — plain PK refs)
- `recommendation_log: string[]` (recommendation_id list — plain PK refs)
- `x_rule_firing: number[]` (firing_id list — plain PK refs)
- `data_quality_daily: object[]` (composite PK ref shape)

**Acceptance.**
1. Migration 027 lands; `recommendation_evidence_card` table created with the schema above. Migration includes legacy-DB degradation test (synthesis on a schema-26 DB does not crash; the W-OB-7 `open_connection_with_migrations` seam handles auto-application).
2. Synthesis transaction writes exactly one card per committed recommendation. Test fixture: synthesize a 6-domain plan, assert 6 cards created, all cards have non-null `recommendation_id` cross-referenceable to `recommendation_log`.
3. Synthesis rollback proves no card survives a failed synthesis. Test fixture: monkey-patch a card insert to raise, assert daily_plan + recommendation_log + cards all rolled back together.
4. Card payload validates against `recommendation_evidence_card.v1` schema. Locator entries in `accepted_state_rows` + `raw_source_refs` validate per W-PROV-1 (`validate_locator` rejects any non-whitelist table).
5. `hai explain --json` includes top-level `evidence_cards` field with one entry per card for the requested plan.
6. Test count grows ≥ 12 vs v0.1.18 (table tests 3 + transaction tests 3 + rollback tests 2 + payload-schema tests 2 + explain-integration tests 2).
7. `CHANGELOG.md` v0.2.0 entry names W-EVCARD-DAILY with user-facing wording "per-recommendation evidence cards now persist alongside the daily plan."

**What this WS does NOT do.**
- Does not change recommendation_log shape (only adds a sibling table).
- Does not change `hai today` rendering by default (separate `--evidence` flag work is a v0.2.1 candidate; W-EVCARD-DAILY ships the carrier + `hai explain --json` consumption only).
- Does not implement W58D factuality enforcement (W58D's job; W-EVCARD-DAILY ships the substrate the gate reads).

**Ship-claim gate:** acceptance items 1, 2, 3 are **release-blocker**. Atomic transaction + rollback discipline preserves the three-state audit chain invariant.

### §2.C W-EVCARD-WEEKLY — Weekly claim-card carrier

**Source.** F-PHASE0-09 (Codex) + F-PHASE0-12 (Codex architecture correction) + maintainer Q1.

**Files of record:**
- `src/health_agent_infra/core/state/migrations/028_evidence_card_weekly.sql` (new).
- `src/health_agent_infra/core/review/weekly_card.py` (new) — card construction logic.
- `src/health_agent_infra/core/review/weekly.py` (W52 — created at §2.D; uses the carrier).
- `verification/tests/test_evidence_card_weekly.py` (new).

**Migration 028 shape (PLAN-author proposal):**

```sql
CREATE TABLE weekly_claim_card (
    card_id TEXT PRIMARY KEY,                -- UUID — append-only per F-PLAN-OQ1 disposition
    user_id TEXT NOT NULL,
    iso_week TEXT NOT NULL,                  -- YYYY-Www format
    claim_id TEXT NOT NULL,                  -- stable content hash; same content → same claim_id
    claim_atom_text TEXT NOT NULL,           -- the prose claim itself
    atom_type TEXT NOT NULL,                 -- 'quantitative' | 'comparative' (qualitative atoms emit no card per F-PLAN-10)
    derivation_path TEXT NOT NULL,           -- 'aggregate' | 'comparison' | 'literal'
    locator_set_json TEXT NOT NULL,          -- JSON list of SourceRowLocator dicts
    audit_refs_json TEXT NOT NULL,           -- JSON object: {recommendation_log: [], x_rule_firing: [], ...}
    computed_at TEXT NOT NULL,
    source TEXT NOT NULL,
    ingest_actor TEXT NOT NULL,
    agent_version TEXT,
    CHECK (atom_type IN ('quantitative', 'comparative'))
);
CREATE INDEX idx_weekly_card_iso_week ON weekly_claim_card (iso_week, user_id);
CREATE INDEX idx_weekly_card_claim_id ON weekly_claim_card (claim_id, computed_at DESC);
-- No UNIQUE constraint on (iso_week, user_id, claim_id) — append-only per F-PLAN-OQ1.
-- Canonical-view query: latest computed_at per (iso_week, user_id, claim_id).
```

**Cardinality.** One card per *quantitative or comparative atomic claim* in W52's prose output (per F-PLAN-10 round-1 scope alignment). A weekly review with N quoted numbers + M comparisons produces N+M cards; qualitative atoms emit no card. The `claim_id` is a stable hash; re-running W52 for the same week is idempotent at the *content* level — same prose + same data → same `claim_id`.

**Append-only audit history (round-1 per Codex OQ-1 disposition).** Cards persist append-only; re-running W52 for the same week with corrected data produces a new row with a new `computed_at` AND a new `card_id` (UUID-suffixed if `claim_id` already exists). The latest card per `(iso_week, user_id, claim_id)` is the canonical view; superseded cards remain as audit history. **(Round-1 correction: original PLAN proposed `INSERT OR REPLACE` (latest-only) which lost audit history; Codex OQ-1 flagged the trade-off. Per maintainer rigor preference (`feedback_pick_rigor_over_velocity.md`), append-only is the more rigorous choice.)** Migration 028 schema updated below to reflect this — UNIQUE constraint moves from `(iso_week, user_id, claim_id)` to `card_id` only; canonical-view query joins on latest `computed_at` per claim.

**Payload separation per F-PHASE0-12.** `locator_set_json` carries `SourceRowLocator[]` validated per W-PROV-1 contract (evidence + accepted-state tables only). `audit_refs_json` carries write-side primary-key references as a plain JSON object with one key per audit-chain table — these are NOT `SourceRowLocator` instances and bypass the W-PROV-1 whitelist (the validator is intentionally permissive on `audit_refs_json`).

**Acceptance.**
1. Migration 028 lands; `weekly_claim_card` table + indexes created.
2. Card construction validates: `locator_set_json` entries validate per W-PROV-1; `audit_refs_json` matches the schema (object with optional keys for each audit-chain table; values are arrays of plain PK strings or composite-PK objects).
3. `claim_id` hashing is deterministic (same prose content → same `claim_id`). Idempotency test: run W52 twice for same week with same data, assert no card content drift (latest-by-`computed_at` query returns identical content).
4. **Append-only audit history**: re-running W52 for the same week with corrected data produces a new card row (new `card_id`, same `claim_id`, newer `computed_at`); superseded cards remain in the table. Test: run W52, mutate a fixture row, re-run W52, assert two rows for the affected `claim_id` with distinct `computed_at`. **(Round-1 update per F-PLAN-OQ1 — append-only replaces original `INSERT OR REPLACE` shape.)**
5. `hai review weekly --json` output includes top-level `claim_cards` field with one entry per card for the requested week.
6. Test count grows ≥ 8 vs W-EVCARD-DAILY baseline (migration 2 + cardinality 2 + payload-separation 2 + idempotency 2).
7. `CHANGELOG.md` v0.2.0 entry names W-EVCARD-WEEKLY with user-facing wording "weekly review claims now persist with source-row provenance."

**What this WS does NOT do.**
- Does not implement W52 aggregation (W52 ships separately, consumes the carrier).
- Does not change daily evidence-card schema.
- Does not implement factuality enforcement (W58D's job).

**Ship-claim gate:** acceptance items 2, 3, 4 are **release-blocker**. Idempotency + payload separation are load-bearing for W52 + W58D.

### §2.D W52 — `hai review weekly` aggregation

**Source.** tactical §6.1 + F-PHASE0-02 (calendar-coverage gap) + F-PHASE0-03 (data-quality semantics) + F-PHASE0-07 (supersession-reconciliation fixture) + W-EXPLAIN-UX-CARRY consumption.

**Files of record:**
- `src/health_agent_infra/cli/handlers/review.py` (extend) — new `hai review weekly` subcommand.
- `src/health_agent_infra/core/review/weekly.py` (new) — aggregation queries.
- `src/health_agent_infra/core/review/render.py` (new) — markdown / JSON output rendering.
- `src/health_agent_infra/core/review/prose_builder.py` (new) — prose authoring with W-EXPLAIN-UX-CARRY obligations.
- `src/health_agent_infra/cli/__init__.py` parser-tree — new subcommand + flags.
- `verification/tests/test_review_weekly.py` (new) — aggregation correctness + abstain branch + supersession + data-quality semantics.
- `verification/tests/test_review_weekly_byte_stable.py` (new) — fixture-week deterministic output.
- `verification/tests/test_review_weekly_abstain_metadata.py` (new — round-1 add per F-PLAN-03) — deterministic-substitution test for abstain-branch metadata claims (counts, threshold, date lists).
- `verification/tests/test_review_weekly_deferred_domain_suppression.py` (new — round-2 add per F-PLAN-R2-02) — fork-defer fixture asserting deferred-domain prose renders qualitative-only with explicit "insufficient provenance" disposition.

**CLI surface (PLAN-author proposal):**

```
hai review weekly --week YYYY-Www [--json | --markdown]
                  [--user-id <user>] [--coverage-threshold <N>]

  Required: --week is ISO 8601 week shape (e.g., 2026-W18).
  Default --user-id: u_local_1 (per single-user shape).
  Default --coverage-threshold: 5 (of 7 days; from thresholds.toml).
  Default output: markdown.
```

**Aggregation queries (PLAN-author proposal):**

For week `iso_week`, gather (filtered on `superseded_by_plan_id IS NULL` per F-PHASE0-07):
- All `daily_plan` rows where `for_date IN (iso_week_dates)`.
- All `recommendation_log` rows linked to those plans.
- All `x_rule_firing` rows linked to those plans.
- All `review_outcome` rows linked to those recommendations.
- `accepted_*_state_daily` rows for each `for_date` in the week.
- `data_quality_daily` rows + joins to `sync_run_log` + `runtime_event_log` for the data-quality lane (per F-PHASE0-03 disambiguation).
- `intent_item` and `target` rows active during the week.
- All `recommendation_evidence_card` rows for the recommendations (W-EVCARD-DAILY consumer).

**Partial-week abstain branch (per F-PHASE0-02).** If `len(plan_dates) < coverage_threshold`, return `weekly_status='insufficient_data'` and refuse to render quantitative prose. Threshold default in `thresholds.toml`:

```toml
[policy.review_weekly]
coverage_threshold_days = 5
data_quality_stale_pull_hours = 48
```

Abstain output shape (markdown):

```
# Weekly review — 2026-W18

**Insufficient data for this week.**

Plans found: 3 of 7 days (threshold: ≥5).
Days with plans: 2026-04-30, 2026-05-02, 2026-05-04.
Days without plans: 2026-04-27, 2026-04-28, 2026-04-29, 2026-05-01, 2026-05-03.

Run `hai daily` on past days where you have data, then re-run this command.
```

**Abstain metadata IS quantitative and IS validated** (round-1 correction per F-PLAN-03). The numbers `3`, `7`, `5` and the date lists are deterministic claims about the past week. They are validated **outside W58D** via a deterministic-by-construction path:

- Counts (`3 of 7`) derive directly from the SQL query result (`SELECT COUNT(*) FROM daily_plan WHERE for_date IN iso_week_dates AND superseded_by_plan_id IS NULL` for the numerator; `7` is constant). No prose authoring is involved; the integer is a literal substitution from query output.
- Threshold (`5`) is a literal substitution from `thresholds.toml` `policy.review_weekly.coverage_threshold_days`, validated at threshold-injection-seam time per D13.
- Date lists are direct enumerations of the SQL result rows.

W52's abstain-branch render is asserted by a deterministic test (`test_review_weekly_abstain_metadata.py`): the test seeds a fixture state DB with 3 plan-days in a 7-day window, runs `hai review weekly --week`, asserts the rendered prose substitutes the queried counts + the configured threshold + the queried date lists exactly. **No claim cards written on abstain because the validation is structurally simpler (literal substitution from query output)**, not because the prose is non-quantitative. The structural argument: if the substitution is byte-stable AND the query is correct, the prose claim is correct.

**Round-1 framing correction.** The original PLAN said "no claim cards written on abstain (the abstain prose is itself non-quantitative; no atoms to validate)." That framing was incorrect — the abstain prose IS quantitative. The correct framing: claim cards are not written on abstain because abstain metadata uses a stricter deterministic-substitution path that doesn't go through prose authoring at all. The non-abstain (full-render) path uses claim cards because prose authoring introduces the risk W58D blocks.

**Data-quality rollup (per F-PHASE0-03; round-1 corrected per F-PLAN-04).** Distinguish `stale_pull` from `retrospective_manual` using the **existing `sync_run_log.mode` column** (verified at `core/state/migrations/008_sync_run_log.sql:41`; current call sites use `mode="manual"` for manual intake and `mode="csv"` / `mode="live"` for pull paths per `cli/handlers/intake.py:162-167` + `cli/handlers/recommend.py:528-539`):

- `stale_pull`: `for_date < started_at - data_quality_stale_pull_hours` AND `mode IN ('csv', 'live')` (auto-pull paths).
- `retrospective_manual`: `for_date < started_at` AND `mode = 'manual'` (deliberate retrospective entry).

**No new schema column.** The original PLAN proposed a new `entry_mode` column; that conflicted with the schema-group budget AND duplicated the existing `mode` column. **(Round-1 correction per F-PLAN-04: PLAN now derives `retrospective_manual` from existing `mode` + `source` without ALTER.)**

**Supersession-reconciliation (per F-PHASE0-07).** All queries filter `superseded_by_plan_id IS NULL`. Multi-canonical day handling: if two non-superseded plans exist for the same `for_date`, surface BOTH in the weekly prose with explicit "multiple plans on this day" disposition (not silent latest-wins).

**Test fixture: maintainer's own state DB.** F-PHASE0-02 / F-PHASE0-07 evidence directly: 2026-W18 (week of 04-27 → 05-03) has 4 of 7 plan-days; 2026-W17 (week of 04-20 → 04-26) has 5 of 7 plan-days; 2026-04-24 has 5-version supersession chain. PLAN proposes a fixture-week corpus seeded from these days (anonymised to remove maintainer-specific intent prose; structural state preserved).

**Acceptance.**
1. `hai review weekly --week YYYY-Www --json` runs deterministically over a fixture-week corpus. Byte-stable output assertion: same fixture week → same JSON output across 3 consecutive runs.
2. Partial-week abstain branch fires when `< 5 of 7 days` populated; `weekly_status='insufficient_data'` in JSON output; markdown output matches the abstain template above.
3. Coverage threshold reads from `thresholds.toml` per D13 contract; threshold-injection-seam validation exists (negative test: invalid threshold value rejected at `load_thresholds` boundary).
4. Supersession reconciliation correct: fixture week containing the 04-24 5-version chain renders with both `_v3` and `_v5` canonical plans surfaced; mid-chain `_v1`, `_v2`, `_v4` not surfaced.
5. Data-quality rollup distinguishes `stale_pull` vs `retrospective_manual` with ≥4 fixture cases (auto-pull stale, manual-recent fresh, manual-retrospective, auto-pull fresh).
6. Weekly claim cards (W-EVCARD-WEEKLY consumer) populated for every quantitative + comparative atomic claim in non-abstain output. Test: count cards = count of (quantitative + comparative) atoms in prose. **Qualitative atoms emit no card** — but a separate test asserts qualitative atoms contain no factual past-week content (mechanical: no numeric tokens, no date tokens, no comparison operators in qualitative atom_text). **(Round-1 addition per F-PLAN-10: qualitative-non-factual mechanical assertion.)**
7. W-EXPLAIN-UX-CARRY consumed: each prose obligation from v0.1.14 review doc has been implemented OR explicitly deferred with named cycle destination in `reporting/plans/v0_2_0/explain_ux_obligations.md` (new file).
8. **Deferred-domain suppression** (round-2 add per F-PLAN-R2-02): if W-PROV-2 fork-defers any dormant domain to v0.2.1 W-PROV-3, W52 emits no quantitative or comparative atoms (and writes no claim cards) for that domain in the weekly review; the domain section renders with explicit "domain X: insufficient provenance — quantitative claims suppressed pending v0.2.1 W-PROV-3" disposition. **Test:** fixture state DB with one dormant domain marked W-PROV-3-deferred; `hai review weekly` for a populated week asserts (a) no claim cards exist for that domain in `weekly_claim_card`, (b) the JSON output includes `deferred_domains: ["<domain>"]`, (c) the markdown output renders the suppression disposition prose.
9. **Append-only output semantics** (round-2 add per F-PLAN-R2-03): `hai review weekly --json` returns `claim_cards` as the **canonical-latest view** — for each `(iso_week, user_id, claim_id)` tuple in the table, only the row with maximum `computed_at` is emitted. Historical (superseded) rows remain in `weekly_claim_card` but are NOT in the default JSON output. A new `--include-history` flag exposes the full append-only history (latest + superseded). **Test:** rerun fixture — run W52, mutate one fixture row, rerun W52, assert (a) `weekly_claim_card` has 2 rows for the affected `claim_id` (append-only preserved), (b) default `--json` returns 1 row per `claim_id` (canonical-latest), (c) `--json --include-history` returns both rows.
10. Test count grows ≥ 23 vs W-EVCARD-WEEKLY baseline (aggregation 5 + abstain 3 + supersession 2 + data-quality 4 + claim-card 2 + W-EXPLAIN-UX 2 + abstain-metadata 2 + deferred-domain 2 + canonical-latest-rerun 1). **(Round-2 update per F-PLAN-R2-05: count raised from 18 to 23 to absorb the round-1 + round-2 added test surfaces.)**
11. `hai capabilities --json` regenerates with new `hai review weekly` command + 4 flags (round-2: added `--include-history` per acceptance #9). Snapshot regenerates in lockstep.
12. `CHANGELOG.md` v0.2.0 entry names W52 with user-facing wording "weekly review with source-row provenance."

**What this WS does NOT do.**
- Does not run an LLM judge over the prose (W58J, v0.2.2).
- Does not implement insight-ledger persistence (W53, v0.2.1).
- Does not autonomously author intent/target rows from outcomes (per W57 invariant).
- Does not extend `hai today` rendering (separate v0.2.1+ candidate).

**Ship-claim gate:** acceptance items 1, 2, 4, 6, 7, **8**, **9** are **release-blocker** (round-2: items 8 + 9 added per F-PLAN-R2-02 + F-PLAN-R2-03). Cycle thesis depends on byte-stable output + abstain branch + supersession correctness + deferred-domain suppression + canonical-latest output semantics.

### §2.E W-FACT-ATOM — Atomic-claim decomposition

**Source.** tactical §6.1 + F-PHASE0-10 (Codex). FActScore-shaped atomic-claim decomposition; folds into W58D as the parsing layer.

**Files of record:**
- `src/health_agent_infra/core/eval/atomic_claims.py` (new) — atomic-claim parser.
- `src/health_agent_infra/core/eval/__init__.py` — public API.
- `verification/tests/test_atomic_claims.py` (new).

**Approach.** No LLM in the parser (deterministic per W58D contract). Regex + structured-prose-shape recognition. W52's prose follows a known template (per `prose_builder.py` shape); the atomic-claim parser knows that template and extracts atoms by structural rule, not by NLU.

**Acceptance.**
1. Atomic-claim parser splits W52's prose into atoms with ≥98% precision against a 30-fixture parse corpus (manually-annotated ground truth in `evals/scenarios/atomic_claims/`).
2. Each atom carries `(atom_text, atom_type, derivation_path)`. Atom types: `quantitative`, `comparative`, `qualitative`. Quantitative + comparative atoms are W58D-validatable; qualitative atoms are passed through (informational, not gated).
3. Parser is deterministic: same prose → same atoms. Test asserts byte-stable atom output.
4. Test count grows ≥ 8 vs W52 baseline (parse 4 + determinism 2 + atom-type-classification 2).

**What this WS does NOT do.**
- Does not enforce factuality (W58D's job; W-FACT-ATOM provides the input).
- Does not run an LLM (W58J, v0.2.2).

**Ship-claim gate:** acceptance items 1, 3 are **release-blocker** (W58D depends).

### §2.F W58D — Deterministic factuality gate

**Source.** tactical §6.1 + F-PHASE0-10 (Codex; "judge_adversarial corpus is shape-only — W58D needs its own deterministic scoring corpus") + maintainer Q2 adjudication (% over larger corpus).

**Files of record:**
- `src/health_agent_infra/core/eval/factuality_gate.py` (new) — gate logic.
- `src/health_agent_infra/evals/scenarios/factuality/` (new dir) — deterministic corpus.
- `src/health_agent_infra/evals/scenarios/factuality/index.json` (new) — corpus manifest.
- `src/health_agent_infra/evals/cli.py` (extend) — new `--scenario-set factuality` shorthand.
- `verification/tests/test_factuality_gate.py` (new).
- `src/health_agent_infra/cli/__init__.py` parser-tree — new flag on `hai review weekly`: `--bypass-factuality-gate` (developer-only; explicit override; logs WARN; does NOT ship in capabilities-manifest agent_safe surface).

**Gate logic (PLAN-author proposal).** For each atomic claim from W-FACT-ATOM:

```
1. If atom_type ∈ {quantitative, comparative}:
   2. Resolve atom to a (claim_id, derivation_path, locators, audit_refs) tuple.
   3. For each locator: assert locator validates per W-PROV-1 AND
                         the resolved row exists at the cited row_version
                         (re-resolve against current state).
   4. For each audit_ref: assert the referenced primary key exists in
                         the cited table at the cited revision.
   5. If any locator or audit_ref fails to resolve: gate BLOCKS.
   6. If all resolve: gate PASSES the atom.
7. If atom_type == qualitative: pass through (gate does not validate).
8. Aggregate: weekly review render is BLOCKED if any atom is blocked.
```

**Corpus shape (per maintainer Q2; round-1 corrected per F-PLAN-06).** ≥150 fixtures. Composition (PLAN-author proposal):

- ≥85 known-bad fixtures (claim doesn't resolve; gate must block). **(Round-1 correction: was ≥75, raised to ≥85 to match the sub-category sum and remove the under-specified "overlap budget."** Sub-categories below sum to 85 with no overlap; corpus may grow beyond 85 known-bad with overlap explicitly tagged.)
- ≥75 known-good fixtures (claim resolves cleanly).
- Total ≥150.

**Sub-categories** — provenance corrected per F-PLAN-06: 3 categories from `reporting/plans/future_strategy_2026-04-29/review_codex.md:1597-1602` (source-quality, x-rule-conflict, source-signal-conflict); 2 added by W58D (source-row-drift, audit-ref-orphan):

| # | Category | Source | Min count |
|---|---|---|---|
| 1 | Source-quality (stale, partial, absent, unavailable, pending user input) | `review_codex.md:1599-1600` | ≥30 known-bad |
| 2 | X-rule-conflict (user marked `disagreed_firing_ids`) | `review_codex.md:1601` | ≥15 known-bad |
| 3 | Source-signal-conflict (deterministic detector exists) | `review_codex.md:1602` | ≥15 known-bad |
| 4 | Source-row drift (cited row_version no longer matches current; supersession case) | W58D-specific (NOT in `review_codex.md`) | ≥15 known-bad |
| 5 | Audit-ref orphan (cited audit-chain PK doesn't exist) | W58D-specific (NOT in `review_codex.md`) | ≥10 known-bad |
| **Sum** | | | **85 known-bad** |

**Manifest contract.** `evals/scenarios/factuality/index.json` exposes per-fixture `category` + `expected_outcome` (`block` or `pass`) tags + a stable `fixture_id`. The scoring runner reads the manifest and computes pass/block percentages from actual counts. **No hard-coded "73 of 75" examples** — all thresholds compute from manifest cardinality. **(Round-1 correction per F-PLAN-06.)**

**Threshold acceptance (per maintainer Q2 + PLAN proposal; D14 pressure-tests):**
- **Block ≥97% of known-bad** atoms (computed: `block_count / known_bad_count ≥ 0.97`).
- **Pass ≥99% of known-good** atoms (computed: `pass_count / known_good_count ≥ 0.99`).

**False-negative tolerance is named.** The "97% block / 99% pass" framing admits ≤3% false-negatives on bad atoms and ≤1% false-positives on good atoms. The cycle thesis is that this is honest, scalable, and pressure-tested over time as the corpus grows. **D14 round 1 should challenge whether 97% is the right block threshold — could be tighter (99%) or looser (95%) depending on corpus shape.**

**Acceptance.**
1. `core/eval/factuality_gate.py` implements gate logic per the proposal above. No LLM imports.
2. Deterministic corpus at `evals/scenarios/factuality/` has ≥150 fixtures (≥75 known-good, ≥85 known-bad with sub-category coverage per the table above; round-1 raised from ≥75 known-bad to ≥85 per F-PLAN-06 sub-category-sum reconciliation).
3. `hai eval run --scenario-set factuality` runs the gate over the corpus and reports `block ≥97% known-bad / pass ≥99% known-good`.
4. `hai review weekly` invokes the gate by default; if any atom blocks, the command exits with `INTERNAL` exit code and stderr names the blocked atom + reason. `--bypass-factuality-gate` flag exists for developer-only override (logs WARN; not in agent_safe surface; not in capabilities `agent_safe: true` set).
5. Threshold values live in `thresholds.toml`:
   ```toml
   [policy.factuality_gate]
   block_known_bad_min_pct = 97.0
   pass_known_good_min_pct = 99.0
   ```
   Threshold-injection seam validates per D13.
6. **`--scenario-set all` semantics extension** (round-2 add per F-PLAN-R2-05 propagation; corresponds to §3.1 G4a). v0.2.0 modifies `evals/cli.py` so `hai eval run --scenario-set all` fans out to deterministic domain/synthesis fixtures + W58D factuality fixtures (BOTH scored at 100%), while `--scenario-set judge_adversarial` preserves the v0.1.14 W-AI shape-only summary behaviour (no scoring assertion until v0.2.2 W58J). Existing v0.1.18 baseline behaviour for `judge_adversarial` is unchanged; the only `all`-set semantics change is adding factuality to the fan-out.
7. Test count grows ≥ 26 vs W-FACT-ATOM baseline (gate logic 8 + corpus coverage 12 + threshold 3 + bypass-flag 2 + scenario-set-all-semantics 1). **(Round-2: count raised from 25 to 26 to absorb item 6's CLI-semantics change.)**
8. `CHANGELOG.md` v0.2.0 entry names W58D with user-facing wording "deterministic factuality gate over weekly-review prose."

**What this WS does NOT do.**
- Does not run an LLM judge (W58J, v0.2.2).
- Does not auto-correct blocked claims (gate blocks; user reads stderr; W52 is re-run after data is fixed).
- Does not autonomously mutate thresholds (per AGENTS.md "Do Not Do").
- Does not change `--scenario-set judge_adversarial` behaviour — it stays shape-only summary per `evals/cli.py:100-138`.

**Ship-claim gate:** acceptance items 1, 2, 3, 4, **6** are **release-blocker** (round-2: item 6 added per F-PLAN-R2-05). Cycle thesis depends on the gate working blocking from day 1 + the `--scenario-set all` semantics aligning with G4a.

### §2.G W-MCP-THREAT — MCP threat-model artifact

**Source.** CP-MCP-THREAT-FORWARD (post-v0.1.13). Pre-req for v0.3 PLAN-audit.

**Files of record:**
- `reporting/docs/mcp_threat_model.md` (new) — OWASP MCP Top 10 mapping.
- `AGENTS.md` "Do Not Do" — verify the existing MCP autoload prohibition (post-v0.1.13 strategic research §17 Sc-5) is reflected; no change unless drift detected.

**Acceptance.**
1. `reporting/docs/mcp_threat_model.md` exists and maps OWASP MCP Top 10 against this project's planned read-surface (Wave 3, v0.3-v0.4). Each item: (a) categorisation (applies / not applicable), (b) mitigation if applies, (c) gap-named-deferred-to-cycle if mitigation not yet shipped.
2. CVE-2025-59536 / CVE-2026-21852 (Check Point project-file autoload + token-exfiltration chain) explicitly named per AGENTS.md "Do Not Do" provenance.
3. Doc length 4-8 pages; not a stub.
4. Cross-references existing `SECURITY.md` + `reporting/docs/privacy.md` + AGENTS.md "Do Not Do" entries for self-consistency.

**What this WS does NOT do.**
- Does not implement any MCP read-surface (Wave 3 territory).
- Does not change AGENTS.md "Do Not Do" entries (those are settled per post-v0.1.13).

**Ship-claim gate:** acceptance items 1, 2 are **release-blocker for v0.3 PLAN-audit prereq** (not v0.2.0 ship gate, but absent the doc, v0.3 PLAN cannot author).

### §2.H W-COMP-LANDSCAPE — Competitive landscape doc

**Source.** tactical §6.1.

**Files of record:**
- `reporting/docs/competitive_landscape.md` (new) — 2026-Q2 evidence refresh of comparable-OSS survey.

**Acceptance.**
1. Doc exists at `reporting/docs/competitive_landscape.md`. Refreshes the survey from `historical/multi_release_roadmap.md` (2026-04-25) with 2026-Q2 evidence.
2. Five competitor categories covered (per strategic_plan_v2 §2.1): QS trackers, athlete analytics, MCP servers, vendor coaches, multi-agent personal-health frameworks.
3. Each category has ≥3 named competitors with primary-source evidence (URL + date-checked).
4. Doc cites the 5 unique-to-HAI elements per strategic_plan_v2 §2.2 with supporting evidence.

**What this WS does NOT do.**
- Does not change AGENTS.md or strategic-plan-v2.

### §2.I W-NOF1-METHOD — N-of-1 methodology doc

**Source.** tactical §6.1.

**Files of record:**
- `reporting/docs/n_of_1_methodology.md` (new) — substrate-then-estimator chain methodology.

**Acceptance.**
1. Doc exists. Documents the v0.5 substrate (recommendation, compliance, outcome, classified_state) triple ledger + the v0.6 estimator that reads it.
2. Cites academic sources for N-of-1 trial methodology (e.g., Lillie et al. 2011 N-of-1 trial framework; Senn 2007 individualised effect estimation).
3. Names the substrate-maturation gates: ≥90d substrate before v0.6 estimator analyses; ≥90d post-v0.7 zero-incident before v1.0 ship.
4. 4-8 pages; not a stub.

**What this WS does NOT do.**
- Does not implement substrate or estimator (Wave 4, v0.5+).

### §2.J W-2U-GATE-2 — Opportunistic foreign-machine session

**Source.** D16 + maintainer Q3 adjudication.

**Trigger.** A non-maintainer candidate surfaces during the v0.2.0 cycle window AND has a wearable AND can run a recorded session. **Per D16, this is opportunistic-not-blocking.** If no candidate appears, the WS does not fire.

**Files of record (if fires):**
- `reporting/plans/v0_2_0/foreign_machine_session_<YYYY-MM-DD>.md` (new) — session transcript + findings.

**Acceptance (if fires).**
1. Session transcript filed.
2. Findings tagged with `cycle_impact` (`absorbs-into-WS` / `revises-scope` / `aborts-cycle` / `informational`).
3. Any structural finding routes to the appropriate v0.2.0 W-id OR named-deferred to v0.2.1 with explicit destination.

**Acceptance (if doesn't fire).**
1. RELEASE_PROOF.md §-Out-of-scope explicitly names "W-2U-GATE-2 did not fire — no candidate surfaced during v0.2.0 cycle window."
2. Re-evaluation gate stays at v0.4 review per D16. **NOT v0.2.1.** F-PHASE0-11 README drift fix during this PLAN's authoring touch-up addresses any prior wording.

**What this WS does NOT do.**
- Does not block ship (D16).
- Does not re-tier W-2U-WEARABLE or W-2U-DOGFOOD (those stay deferred to v0.4 review per D16).
- Does not require a transcript if doesn't fire (the "did not fire" naming itself is the closure).

### §2.K W-EXPLAIN-UX-CARRY — Carry-forward consumption (folds into W52)

**Source.** v0.1.14 PLAN F-PLAN-05 carry-forward.

**Files of record:**
- `reporting/docs/explain_ux_review_2026-XX.md` (existing — read for obligations).
- `reporting/plans/v0_2_0/explain_ux_obligations.md` (new — track per-item disposition).
- `src/health_agent_infra/core/review/prose_builder.py` (W52 — implement obligations).

**Acceptance.**
1. Each obligation in the v0.1.14 review doc's "v0.2.0 W52 prose obligations" section has a named disposition: `implemented-in-W52` / `deferred-to-v0.2.1` / `deferred-to-v0.3` / `out-of-scope-with-reason`.
2. Implemented obligations have a corresponding test in `test_review_weekly.py` asserting the prose-shape compliance.
3. Deferrals name the destination cycle explicitly.

**Effort:** 0d (folds into W52). Tracked here for accountability per F-PLAN-05.

**What this WS does NOT do.**
- Does not extend obligations beyond the v0.1.14 review doc (no new obligations authored here).

---

## 3. Ship gates

### 3.1 In-cycle gates (must pass before D15 IR opens)

**G1. All 10 active W-ids' release-blocker acceptance items pass.** W-PROV-2, W-EVCARD-DAILY, W-EVCARD-WEEKLY, W52, W-FACT-ATOM, W58D, W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD, W-EXPLAIN-UX-CARRY. W-2U-GATE-2 is opportunistic; "did not fire" is acceptable.

**G2. Full pytest suite green** (broader `-W error::Warning` gate). Test count target ≥ v0.1.18 + 86 (rough projection: W-PROV-2 +6, W-EVCARD-DAILY +12, W-EVCARD-WEEKLY +8, W52 +23 (round-2 raised from +18 per F-PLAN-R2-05 absorbing abstain-metadata + deferred-domain + canonical-latest-rerun tests), W-FACT-ATOM +8, W58D +26 (round-2 raised from +25 per scenario-set-all semantics test), others minor). Maintainer to verify final count.

**G3. `hai eval run --scenario-set factuality` reports `block ≥97% / pass ≥99%`** over the deterministic corpus (≥150 fixtures).

**G4a. `hai eval run --scenario-set all` 100% pass-rate over scored fixtures** (per F-PLAN-07 split). Scope: 135 deterministic domain/synthesis fixtures + the new W58D factuality corpus. **(Round-1 correction: judge_adversarial fixtures NOT counted in this gate — they are shape-only summary per `evals/cli.py:100-138` until v0.2.2 W58J wires real scoring. Counting shape-only fixtures in a 100% pass-rate gate is meaningless.)** **Implementation note:** v0.2.0 extends `--scenario-set all` semantics to fan out to deterministic + factuality scoring; W58D acceptance includes the CLI-semantics change.

**G4b. `hai eval run --scenario-set judge_adversarial` shape-integrity summary** continues to emit `total_fixtures: 30` + per-category counts (existing v0.1.14 W-AI behaviour). No scoring assertion until v0.2.2 W58J. **(Round-1 split per F-PLAN-07.)**

**G5. Persona matrix 13/13 with 0 findings + 0 crashes** (HAI_RUN_PERSONA_MATRIX=1; opt-in). Baseline holds from v0.1.18 close.

**G6. `hai capabilities --json` byte-stable** post-W-29 split contract. New `hai review weekly` command + flags surface in manifest; v0.2.3 W-30 schema freeze remains untouched.

**G7. Migration 027 + 028 land cleanly.** Schema-25 + schema-26 + schema-27 DBs all upgrade-test green; legacy-DB degradation tests cover synthesis + intake paths.

### 3.2 Ship-time gates (RELEASE_PROOF + ship)

**G8. Ship-time freshness sweep** per AGENTS.md checklist. ROADMAP, AUDIT, README "Now/Next", `current_system_state.md`, HYPOTHESES, `reporting/plans/README.md`, `tactical_plan_v0_1_x.md` next-cycle row.

**G9. Doc-freshness assertions test green** (`verification/tests/test_doc_freshness_assertions.py`).

**G10. RELEASE_PROOF.md authored with tier annotation `**Tier: substantive**` first line.**

**G11. CHANGELOG.md v0.2.0 entry includes user-facing wording for each shipped W-id** (W-2U-GATE-2 inclusion conditional on firing).

**G12. AUDIT.md v0.2.0 entry filed.**

**G13. Manual TTY ship gate** — maintainer runs final smoke against locally built wheel before `git push` + `uvx twine upload`.

**G14. PyPI publish verification** — `pipx install --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.2.0'` succeeds; `hai capabilities --json | jq .hai_version` returns `"0.2.0"`.

### 3.3 Honesty boundary gates

**G15. RELEASE_PROOF does NOT claim foreign-user empirical validation** unless W-2U-GATE-2 fires with a transcript. The W-2U-INSTALL closure from v0.1.18 (verbal-only) remains the only foreign-user empirical evidence; v0.2.0's own foreign-user claim is "did not fire" or "1 session, transcript at v0_2_0/foreign_machine_session_*.md."

**G16. RELEASE_PROOF does NOT claim LLM-judge factuality** — v0.2.0 ships W58D deterministic-only; W58J shadow-by-default is v0.2.2.

**G17. RELEASE_PROOF does NOT claim insight-ledger persistence** — v0.2.0 ships claim-cards (per-claim provenance), not insight-ledger (multi-week insights). Insight ledger is v0.2.1 W53.

### 3.4 Abort + rollback shape (per F-PHASE0-13 + F-PLAN-08)

**Schema-bearing release; rollback is forward-only.** v0.2.0 introduces migrations 027 + 028. Once shipped to PyPI, **never `git revert` of the schema-bearing release** — `pipx install` users have already applied 027 + 028 and a revert would leave them on schema-head pointing at deleted migration files. Hotfix shape: `v0.2.0.1` introduces a forward migration 029 that null-defaults columns, drops a flag, or reverses a problematic column-shape via additive change. Same pattern as v0.1.15.1 + v0.1.14.1 hotfixes.

**Cycle abort triggers (in-cycle, pre-ship):**

| Trigger | Action |
|---|---|
| W-PROV-2 cannot land all 5 dormant domains within 6d budget (R-V0.2.0-01) | Fork-defer late-domain(s) to v0.2.1 W-PROV-3 with named-partial-closure; W52 suppresses quantitative claims for deferred domains. Cycle proceeds. |
| W58D cannot meet `block ≥97% / pass ≥99%` thresholds after corpus + threshold revision (R-V0.2.0-02) | **Cycle abort at G3.** Two paths: (a) re-author thresholds with explicit thesis-change CP + D14 rerun before re-opening; (b) defer W58D to v0.2.1 with explicit `partial-closure → v0.2.1 W58D-2` and `aborts-cycle-thesis` finding logged. Cycle does NOT ship if neither path adopts. |
| Effort upper bound (37d) exceeded with W52 not yet at IR (R-V0.2.0-03) | **Cycle aborts at G1; D14 re-author required before re-opening.** **(Round-2 correction per F-PLAN-R2-04: original wording "fork-defer ONE carrier (daily OR weekly)" was unsound — the carriers are NOT interchangeable.** Deferring weekly removes W52/W58D's claim-card surface entirely (cycle thesis breaks). Deferring daily contradicts the §1.3 weekly-aggregates-over-daily dependency unless W52 is reauthored with a non-daily-card evidence path — that reauthor IS the abort-and-D14-re-author path. Stub-then-fill remains NOT an option per F-PLAN-09.) |
| F-PHASE0-08 absorption decision (R-V0.2.0-04) | If failed-run rows missing error_class affect ≥10% of any fixture week's daily plans → absorb into v0.2.0 as new W-RUNTIME-EVENT-OBSERVABILITY (additive, ~0.5d). If <10% → defer to v0.2.1 with named destination. |
| Schema-group count drift (R-V0.2.0-05) | If D14 forces 2-group split despite C6, **cycle aborts; D14 re-author required.** **(Round-2 correction per F-PLAN-R2-04: same DAG-conflict reasoning — single-carrier deferral is unsound; either both carriers ship or D14 re-authors the dependency design.)** |

**Post-ship hotfix shape.** A v0.2.0 critical bug surfaced post-PyPI ships as `v0.2.0.1` (hotfix tier per D15). Forward-only migration if schema fix needed. Lightweight RELEASE_PROOF; abbreviated audit chain. v0.1.14.1 + v0.1.15.1 are the precedents.

---

## 4. Risks register

### R-V0.2.0-01. W-PROV-2 effort under-estimated

**Severity.** Release-blocker (W52 + W58D both depend on populated substrate).

**Trigger.** Per-domain locator emission turns out to be harder than the recovery R6 reference shape implies — e.g., a domain's classify path doesn't have a clean accepted-state-table mapping; or the per-domain accepted-state row needs additional columns added to make locator emission meaningful.

**Mitigation.** PLAN-author estimate is 2-4d; abort trigger is **>6d**. If W-PROV-2 exceeds 6d during Phase 1, fork-defer the late-domain(s) to v0.2.1 W-PROV-3 with explicit named-defer in CARRY_OVER.md. v0.2.0 ships W52 + W58D against partial substrate (whichever domains landed by the 6d budget) with explicit "domains X, Y deferred" disposition in RELEASE_PROOF. **W52 must suppress quantitative and comparative claims for deferred domains** per §2.D acceptance #8 (round-2 add per F-PLAN-R2-02): the deferred-domain section renders qualitative-only with explicit "insufficient provenance" disposition; no claim cards written; `deferred_domains` field surfaced in JSON output.

**Probability.** Moderate (35%). The recovery R6 path is real existing code, not theoretical, but it took the v0.1.14 cycle a non-trivial amount of work and there are 5 dormant domains, not 1.

### R-V0.2.0-02. W58D corpus threshold values incorrect

**Severity.** Release-blocker (cycle thesis depends on gate working).

**Trigger.** D14 round 1 (or IR round 1) finds the proposed `block ≥97% / pass ≥99%` thresholds either too lax (gate misses bad claims) or too strict (gate blocks valid claims). Or the corpus distribution is wrong (e.g., known-bad sub-categories under-represent supersession-row-drift).

**Mitigation.** Threshold proposal is explicit + lives in `thresholds.toml` per D13. If D14 finds the proposal wrong, threshold values revise during the round; corpus reshape happens in W58D scope. **No threshold change post-D15 IR open without a fresh CP** (changes the cycle thesis claim).

**Probability.** Moderate (40%). No published baseline for HAI's specific corpus; PLAN proposes from intuition + comparable-OSS hand-wave.

### R-V0.2.0-03. Effort upper bound (37d) brushes 6-week PR-fatigue threshold

**Severity.** Cycle-shape risk (not a single-WS risk).

**Trigger.** Cumulative effort drift. Cycle approaches 30d wall-clock at W52 IR open with W-FACT-ATOM + W58D not yet at acceptance.

**Mitigation (round-2 corrected per F-PLAN-R2-04).** **Cycle aborts at G1 if either carrier cannot ship within budget; D14 re-author required before re-opening.** The carriers are NOT interchangeable: weekly aggregates over daily per §1.3, so deferring weekly removes the W52/W58D claim-card surface entirely (cycle thesis breaks); deferring daily contradicts the weekly-aggregates-over-daily dependency unless W52 is reauthored with a non-daily-card evidence path — and that reauthor IS the abort-and-D14-re-author path. The original round-1 mitigation (fork-defer ONE carrier) was unsound; round-2 corrects to abort-and-re-author. Stub-then-fill also remains NOT an option per F-PLAN-09. **Maintainer-rigor preference (`feedback_pick_rigor_over_velocity.md`):** "if effort tightens, defer with named destination cycle" — for v0.2.0, that destination is "v0.2.0 PLAN re-author + re-D14" not "v0.2.1 W-EVCARD-{DAILY,WEEKLY}-2" because the dependency design is load-bearing.

**Probability.** Moderate (30%). v0.1.x retro Lesson 1 ("audit chains settle, not converge") implies D14 + IR rounds will surface scope-shape issues that absorb effort.

### R-V0.2.0-04. F-PHASE0-08 absorption decision

**Severity.** Informational (W52 data-quality narrative completeness).

**Trigger.** PLAN absorbs OR defers the runtime_event_log error-class fix (failed `hai daily` runs at 2026-05-06T09:28 emit no error_class / error_message).

**Mitigation.** PLAN proposes **defer** to v0.2.1 W-RUNTIME-EVENT-OBSERVABILITY unless ≥X% of failed runs in past 30 days affect W52 fixture weeks. Threshold proposal:
- If failed-run rows missing error_class affect ≥10% of any fixture week's daily plans → absorb into v0.2.0.
- If <10% → defer to v0.2.1 with named destination.

W52 surfaces "N failures, error_class missing in M of N rows" as honest data-quality narrative regardless.

**Probability.** Low (15%). The 4 failures at 2026-05-06T09:28 affect 1 day; `<<10%` of 7-day window. Default disposition: defer.

### R-V0.2.0-05. Schema-group count drift (one-group claim brittleness)

**Severity.** Plan-coherence risk.

**Trigger.** D14 round 2+ surfaces an argument that migration 027 (daily card) + 028 (weekly card) are conceptually two schema groups, not one — thereby violating reconciliation C6 (one group per release).

**Mitigation (round-1 corrected per F-PLAN-05; round-2 corrected per F-PLAN-R2-04).** PLAN's framing is **"evidence-card family"** = migration 027 + 028 only. **W52 produces no migration of its own** — it reads existing tables (accepted-state, audit-chain) and writes to `weekly_claim_card` (migration 028). The C6 schema-group count is 1, not 2 or 3. F-PHASE0-09 (Codex Phase 0) + F-PLAN-05 + F-PLAN-R2-04 (Codex D14) all support this: "schema-group count can remain one." If D14 round 3+ disagrees, two options: (a) **cycle aborts; D14 re-author required** (per §3.4 abort table + F-PLAN-R2-04 — single-carrier fork-defer is unsound because carriers are not interchangeable); (b) merge 027 + 028 into one migration file (preserves group count, slightly worse rollback granularity); (c) reopen reconciliation C6 with a fresh CP. **Round-2 correction:** original option (a) "fork-defer ONE carrier" was unsound and is replaced with abort-and-re-author per F-PLAN-R2-04's DAG-conflict argument.

**Probability.** Low (15%). The §1.4 round-1 clarification eliminates the original ambiguity; both senior reviewers (Claude Phase 0 sweep + Codex round 1 F-PLAN-05) now hold the one-group framing with W52 = no migration.

---

## 5. Effort arithmetic

| W-id | Effort (d) | Mid-point | Notes |
|---|---|---|---|
| W-PROV-2 | 2-4 | 3 | 5 dormant domains; recovery R6 reference shape |
| W-EVCARD-DAILY | 3-5 | 4 | migration 027 + synthesis txn + rollback discipline |
| W-EVCARD-WEEKLY | 2-4 | 3 | migration 028 + idempotency + payload separation |
| W52 | 6-9 | 7.5 | aggregation + abstain + supersession + W-EXPLAIN-UX-CARRY |
| W-FACT-ATOM | 2-3 | 2.5 | parser + atom-type classification |
| W58D | 5-8 | 6.5 | corpus build + scoring runner + thresholds |
| W-MCP-THREAT | 2-3 | 2.5 | doc-only |
| W-COMP-LANDSCAPE | 1-2 | 1.5 | doc-only |
| W-NOF1-METHOD | 1-2 | 1.5 | doc-only |
| W-2U-GATE-2 | 0-2 | 0 | opportunistic; 0d default |
| W-EXPLAIN-UX-CARRY | 0 | 0 | folds into W52 |
| **Sum (mid)** | | **32d** | sum of mid-points |
| **+ inter-WS coordination overhead (~3-5%)** | | +1-2d | review hand-offs, branch sync |
| **− overlap savings (~10%)** | | -3d | parallel doc-only adjuncts; W-FACT-ATOM ↔ W58D |
| **Net mid-point** | | **30d** | |
| **Range** | **25-37d** | | low: minimal-spec carriers + lean corpus; high: corpus expansion + per-domain emission complexity |

**Calibration check.** v0.1.18 was 5-9d actual. v0.1.17 was the largest cycle in v0.1.x at 25-40d catalogue (W-29 cli.py split); v0.2.0 substantively matches v0.1.17's upper bound but with a denser feature surface (more new tables + new commands vs v0.1.17's mechanical split). 25-37d is realistic; D14 may pressure-test downward.

---

## 6. Open questions for D14 round 2+

**Closed in round 1 (Codex D14 round 1, 2026-05-07):**

- ~~**OQ-1.** Per-domain locator emission shape.~~ **Closed.** Per-domain choice retained; D14 round 1 did not pressure-test this.
- ~~**OQ-2.** W58D threshold values.~~ **Held at 97% / 99%** through D14 round 1; threshold computation now manifest-driven per F-PLAN-06 (no hard-coded examples).
- ~~**OQ-3.** Daily evidence-card revision shape.~~ **Held at per-recommendation** through D14 round 1; superseded cards remain as audit history without a new column.
- ~~**OQ-4.** F-PHASE0-08 absorption.~~ **Defer to v0.2.1** (default); criterion in §3.4 abort table.
- ~~**OQ-5.** Schema-group count.~~ **One group** confirmed; §1.4 + §4 R-V0.2.0-05 + §2.D clarified per F-PLAN-05.
- ~~**OQ-6.** Doc-only adjunct timing.~~ Held: parallelisable through Phase 2; W-MCP-THREAT load-bearing for ship-time.
- ~~**OQ-7.** W52 capabilities-manifest delta.~~ Held: forward-compat handled by parser-tree contract.

**Codex round 1 OQs adjudicated:**

- ~~**Codex Q1.** Append-only vs latest-only weekly cards.~~ **Append-only** per maintainer rigor preference; §2.C migration 028 schema updated.
- ~~**Codex Q2.** W52 data-quality column choice.~~ **Existing `sync_run_log.mode`**; no schema delta per F-PLAN-04.
- ~~**Codex Q3.** W-PROV-2 abort + deferred-domain shape.~~ **W52 suppresses quantitative claims for deferred domains** per §2.A partial-closure path + §3.4 abort table.

**Open for D14 round 2+ (none new from round 1; round 2 prompt may surface fresh items):**

PLAN-author note: the round-1 settling cleanly closed all 7 original OQs + Codex's 3 round-1 OQs. Round 2 will pressure-test whether round-1 fixes propagated everywhere (the canonical second-order issue per v0.1.x retro Lesson 1: round-2 catches what round-1 fixes introduced).

---

## 7. Phase 0 closure cross-reference

This PLAN was authored against the consolidated Phase 0 sweep at `reporting/plans/v0_2_0/audit_findings.md`. Each F-PHASE0-* finding has a named PLAN-side disposition:

| Finding | Severity | PLAN disposition |
|---|---|---|
| F-PHASE0-01 | revises-scope | W-PROV-2 (§2.A); architecture per F-PHASE0-12 |
| F-PHASE0-02 | revises-scope | W52 §2.D abstain branch |
| F-PHASE0-03 | revises-scope | W52 §2.D data-quality rollup |
| F-PHASE0-04 | informational (subsumed by F-PHASE0-09) | W-EVCARD-DAILY (§2.B) |
| F-PHASE0-05 | informational | confirmed in §2.D (greenfield) |
| F-PHASE0-06 | informational | §1.4 boundary clarification (W48 ≠ W52) |
| F-PHASE0-07 | informational | W52 §2.D supersession-reconciliation acceptance |
| F-PHASE0-08 | informational | R-V0.2.0-04 + OQ-4 (defer default) |
| F-PHASE0-09 | revises-scope | W-EVCARD-DAILY + W-EVCARD-WEEKLY split (§2.B + §2.C) |
| F-PHASE0-10 | revises-scope | W-FACT-ATOM (§2.E) + W58D (§2.F) own corpus |
| F-PHASE0-11 | informational | doc-only fix during this PLAN's authoring touch-up |
| F-PHASE0-12 | informational (architectural) | W-PROV-2 §2.A whitelist constraint + W-EVCARD-WEEKLY §2.C payload separation |
| F-PHASE0-13 | informational | §4 risks register + R-V0.2.0-04 absorb criterion |

---

## 8. F-PHASE0-11 doc-only drift fixes (during this PLAN's authoring)

Per F-PHASE0-11 disposition: "doc-only fix on README.md:39 + tactical §6.1:880-882 during PLAN authoring touch-up."

**`reporting/plans/v0_2_0/README.md:39`** — replace "carries forward to v0.2.1" with "v0.4 review per AGENTS.md D16."

**`reporting/plans/tactical_plan_v0_1_x.md:880-882`** — replace "sequenced after the v0.1.15 foreign-user candidate session and v0.1.16 empirical-fix consolidation" with "opportunistic-not-blocking per AGENTS.md D16; formal re-evaluation at v0.4 review."

These edits land in the W52 commit (or a discrete `chore(v0.2.0)` doc-only commit during W52 authoring). **NOT settled-decision changes** — D16 stays as authored; only the cross-reference wording in v0.2.0 README + tactical §6.1 prose is corrected to match D16's destination.

---

*PLAN.md authored 2026-05-06 by Claude. Substantive tier per D15. Ready for D14 round 1.*
