# v0.2.0 cycle — workspace

**Status:** scoped, not yet open. PLAN.md authored when the cycle
opens after Phase 0 (D11) bug-hunt completes.

**Tier (anticipated):** substantive (W52 + W58D both release-blockers
per tactical plan §6.1; new schema group; major version bump
per §6.3). Full Phase 0 D11 bug-hunt + multi-round D14 plan-audit +
multi-round D15 IR.

**Provenance.** Created 2026-05-06 at the close of the v0.1.x track:
v0.1.18 shipped to PyPI (2026-05-06), strategic_plan_v2 + v0_1_x_retro
authored, AGENTS.md D16 (CP-2U-GATE-SPLIT) settled.
v0.1.19 cancelled per D16; v0.2.0 hard-dep on foreign-user empirical
evidence dropped — v0.2.0 opens against v0.1.14 substrate (W-PROV-1
+ W-AJ judge harness), already shipped.

The thesis: **make claims about the past week deterministically
checkable.** v0.1.x produced a runtime trustworthy enough to point at
on a single-day surface. v0.2.0 extends that trust across calendar
time — weekly review aggregation with source-row provenance, paired
with a deterministic factuality gate that blocks any quoted
quantitative claim that doesn't resolve to evidence.

This is the gateway to Wave 2 (v0.2.0–v0.2.3 Path A 4-release split
per CP-PATH-A) and ultimately to Wave 3 (MCP read-surface + extension
contracts per strategic plan §7).

## Scope (provisional, finalised in PLAN.md after Phase 0 gate)

| W-id | Title | Effort | Source |
|---|---|---|---|
| **W52** | `hai review weekly --week YYYY-Www [--json\|--markdown]` — code-owned aggregation across accepted state, intent, target, recommendation, X-rule firing, review outcome, data quality. Source-row locators required for every quantitative claim. Builds on v0.1.14 W-PROV-1. | 6-8d | tactical plan §6.1 + CP5 (W52↔W58 design coupling) |
| **W58D** | Deterministic factuality gate. Every quoted quantitative claim in weekly-review prose must resolve to a source-row locator. Blocking from day 1. No LLM in this layer. | 4-6d | tactical plan §6.1 + reconciliation C6 |
| **W-FACT-ATOM** | FActScore-shaped atomic-claim decomposition (folds into W58D). | 2-3d | tactical plan §6.1 |
| **W-MCP-THREAT** | Threat-model artifact at `reporting/docs/mcp_threat_model.md`. OWASP MCP Top 10 mapping; pre-requisite for v0.3 PLAN-audit. Doc-only adjunct. | 2-3d | CP-MCP-THREAT-FORWARD (post-v0.1.13) |
| **W-COMP-LANDSCAPE** | `reporting/docs/competitive_landscape.md` doc. Refreshes the comparable-OSS survey with 2026-Q2 evidence. Doc-only adjunct. | 1-2d | tactical plan §6.1 |
| **W-NOF1-METHOD** | `reporting/docs/n_of_1_methodology.md` doc. Methodology for the substrate-then-estimator chain. Doc-only adjunct. | 1-2d | tactical plan §6.1 |
| **W-2U-GATE-2** *(opportunistic)* | Second foreign-machine onboarding session. **Opportunistic-not-blocking per AGENTS.md D16.** Fires if a candidate surfaces during the cycle window; otherwise carries forward to v0.2.1. | 1-2d if fires; 0d otherwise | D16 + tactical plan §6.1 |
| **W-EXPLAIN-UX carry-forward** | Consume v0.1.14 `reporting/docs/explain_ux_review_2026-XX.md` "v0.2.0 W52 prose obligations" section. Each remediation item: implement OR explicitly defer with named destination (per v0.1.14 PLAN F-PLAN-05). | folds into W52 | v0.1.14 carry-forward |

**Total (estimated):** 6-7 W-ids in scope, **18-24 days**, substantive
tier.

## Sequencing (provisional)

**Phase 0 (D11) — pre-PLAN bug-hunt:**

1. Internal sweep — review code surface since v0.1.18 close for any
   bugs introduced or surfaced by the v0.1.18 onboarding work.
2. Audit-chain probe — verify `proposal_log → planned_recommendation
   → daily_plan + recommendation_log → review_outcome` reconciliation
   across recent days via `hai explain --plan-version all`.
3. Persona matrix run — `HAI_RUN_PERSONA_MATRIX=1 uv run python -m
   verification.dogfood.runner /tmp/v0_2_0_baseline`. Current baseline:
   13/13 with 0 findings + 0 crashes (v0.1.18 ship). Should hold.
4. Codex external Phase 0 audit — author `codex_audit_findings_prompt.md`,
   run, consolidate to `audit_findings.md` with `cycle_impact` tags.
5. **Pre-implementation gate** fires when `audit_findings.md`
   consolidates. Findings tagged `revises-scope` may revise this
   workspace stub or PLAN.md; findings tagged `aborts-cycle` may end
   the cycle.

**Phase 1 — PLAN.md authoring + D14:**

6. Author `PLAN.md`. First line: `**Tier: substantive**` per D15.
7. Copy `_templates/codex_plan_audit_prompt.template.md` and customise
   per-cycle Step 1 (reading list) + Step 2 (audit questions).
8. Run D14 plan-audit rounds. Empirical norm: 2-4 rounds, 10 → 5 → 3
   → 0 settling. Not done until verdict is `PLAN_COHERENT`.

**Phase 2 — Implementation:**

9. **W52 first** (foundational; W58D consumes its output schema).
10. **W58D + W-FACT-ATOM** (deterministic factuality gate over W52
    output).
11. **Doc-only adjuncts** in parallel where staffing allows
    (W-MCP-THREAT is the load-bearing one; v0.3 PLAN-audit depends
    on it).
12. **W-EXPLAIN-UX carry-forward** consumed during W52 prose
    authoring.

**Phase 3 — D15 IR rounds + ship:**

13. Run D15 implementation review. Empirical norm: 2-3 rounds, 5 → 2
    → 1-nit settling.
14. Address findings. Fix-and-reland convention if structural.
15. Ship-time freshness sweep per AGENTS.md checklist.
16. RELEASE_PROOF.md + REPORT.md + CHANGELOG + AUDIT.md updates.
17. Manual TTY ship gate (if any introduced) → `git push origin main`
    → `uvx twine upload`.

## Hard dependencies

- **v0.1.14 substrate (W-PROV-1 + W-AJ judge harness)** — already
  shipped. No additional dependency on v0.1.17/v0.1.18; v0.2.0 is
  parallelizable with both per tactical plan §1.
- **Foreign-user empirical evidence is NOT a hard dep** per AGENTS.md
  D16 (CP-2U-GATE-SPLIT). W-2U-WEARABLE + W-2U-DOGFOOD deferred to
  v0.4 review; W-2U-INSTALL closed verbal-only by post-v0.1.18 father
  session.
- **v0.1.18 published to PyPI** (2026-05-06) — needed only if W-2U-GATE-2
  fires (foreign user installs the post-v0.1.18 build).

## What's explicitly OUT of scope for v0.2.0

- **No LLM judge** — that's W58J in v0.2.2. v0.2.0 ships W58D
  deterministic only.
- **No insight ledger** — that's W53 in v0.2.1.
- **No MCP read-surface** — only the threat-model artifact (doc-only)
  ships; the read-surface itself is v0.3+.
- **No new domain or domain-policy changes.**
- **No new live-data sources.**
- **No capabilities-manifest schema freeze** — that's v0.2.3 W-30.
- **No N-of-1 estimator scaffolding** — that's v0.5+ Wave 4.
- **No autonomous threshold mutation** — explicitly prohibited per
  AGENTS.md "Do Not Do" + W57.
- **No clinical claims** — boundary unchanged.

## First actions for the cycle session (when it opens)

1. Confirm v0.1.18 closed (RELEASE_PROOF.md present, PyPI publish
   verified at 0.1.18, AUDIT.md entry filed).
2. Re-read this README + strategic_plan_v2 §7 Wave 2 + tactical plan §6.
3. Begin Phase 0 (D11) bug-hunt:
   a. Internal sweep against current `src/health_agent_infra/`.
   b. Audit-chain probe via `hai explain` reconciliation.
   c. Persona matrix run (13/13 baseline; opt-in).
   d. Author Codex external Phase 0 audit prompt at
      `codex_audit_findings_prompt.md`.
4. Consolidate findings to `audit_findings.md` with `cycle_impact`
   tags.
5. Pre-implementation gate fires; maintainer reviews findings.
6. Author `PLAN.md`. First line: tier annotation.
7. Copy `_templates/codex_plan_audit_prompt.template.md` and
   customise.
8. Hand to maintainer for D14 round-1.

## Cross-references

- `reporting/plans/post_v0_1_18/strategic_plan_v2.md` §7 Wave 2 —
  strategic context for v0.2.0–v0.2.3.
- `reporting/plans/tactical_plan_v0_1_x.md` §6 — release-by-release
  detail for v0.2.0.
- `reporting/plans/post_v0_1_18/CP-2U-GATE-SPLIT.md` + AGENTS.md D16
  — foreign-user gate split, v0.2.0 hard-dep impact.
- `reporting/plans/post_v0_1_18/v0_1_x_retro.md` — five lessons +
  patterns now load-bearing; informs v0.2.0 audit-cycle expectations.
- `reporting/plans/v0_1_18/RELEASE_PROOF.md` — v0.1.18 ship state
  (W-OB-1..7 + W-OB-6 unfired; D14 7→3, D15 IR 4→2→1-nit).
- `reporting/plans/v0_1_14/RELEASE_PROOF.md` — W-PROV-1 + W-AJ
  substrate v0.2.0 builds on.
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-PATH-A.md` —
  4-release split rationale honoring reconciliation C6.
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-MCP-THREAT-FORWARD.md`
  — W-MCP-THREAT timing.
- `reporting/plans/_templates/codex_plan_audit_prompt.template.md` —
  D14 prompt template.
- `reporting/plans/_templates/codex_implementation_review_prompt.template.md`
  — D15 IR prompt template.
- AGENTS.md "Settled Decisions" D1–D16 + "Patterns the cycles have
  validated" — load-bearing operational context.
