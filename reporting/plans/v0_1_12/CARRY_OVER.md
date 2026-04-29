# v0.1.12 Carry-Over Register

**Date.** 2026-04-29 (authored at cycle open).
**Authored by.** Claude (delegated by maintainer).
**Source.** `reporting/plans/v0_1_11/RELEASE_PROOF.md` §5
("Out-of-scope items deferred with documented reason") +
reconciliation §6 v0.1.12 action set.

This register is the W-CARRY workstream deliverable per PLAN.md
§2.2. Every named-defer from v0.1.11 + every reconciliation §6
item flagged for v0.1.12 has a row with disposition.

---

## 1. v0.1.11 RELEASE_PROOF §5 named-defers

| Item | Disposition | W-id / cycle | Notes |
|---|---|---|---|
| **W-Vb** (`hai demo` polish — persona fixture loading + packaging path) | in-cycle | W-Vb (v0.1.12) | Demo persona-replay flow + fixture-packaging fix. PLAN §2.3. |
| **W-H2** (mypy stylistic class) | in-cycle | W-H2 (v0.1.12) | 21 (v0.1.11 ship) → 22 (Phase 0 audit) → ≤ 5 (v0.1.12 target). PLAN §2.4. |
| **W-N broader gate** (`-W error::Warning` catch-all) | in-cycle | W-N-broader (v0.1.12) | Phase 0 audit count: 49 + 1 error → ≤ 80 branch → full broader gate ships. PLAN §2.5. |
| **F-A-04** (mypy class — Literal abuse class) | in-cycle | W-H2 covers | Subset of W-H2 mypy work. |
| **F-A-05** (mypy class — pandas-import-untyped) | in-cycle | W-H2 covers | Subset of W-H2 mypy work. |
| **F-B-04** (domain-coverage drift across supersession) | **partial-closure** | W-FBC (v0.1.12) → W-FBC-2 (v0.1.13) | v0.1.12 delivers design doc + recovery prototype + `--re-propose-all` override. **Full multi-domain closure deferred to v0.1.13 W-FBC-2** (per Codex F-PLAN-R2-04 + R3-03). PLAN §2.8. |
| **F-C-05** (`strength_status` enum surfaceability) | in-cycle | W-FCC (v0.1.12) | Expose enum via capabilities + `hai today --verbose`. PLAN §2.9. |
| **W52 / W53 / W58** (weekly review + insight ledger + factuality gate) | defer-with-reason | v0.2.0 | Strategic plan Wave 2. CP5 reshapes to single-substantial v0.2.0 with shadow-by-default LLM judge flag. |

## 2. Reconciliation §6 v0.1.12 actions

| Item | Disposition | W-id / cycle | Notes |
|---|---|---|---|
| **C1** (public-doc freshness sweep — `ROADMAP.md`, `HYPOTHESES.md`, `README.md`, `AUDIT.md`, `reporting/plans/README.md`) | in-cycle (rebaselined) | W-AC (v0.1.12) | Codex F-PLAN-02 round 1 caught: 2 of 3 instances already fixed in 2026-04-29 reorg. Remaining: `ROADMAP.md:13` confirmed stale; `README.md` + `AUDIT.md` spot-check. PLAN §2.1. |
| **A8** (ship-time freshness checklist) | in-cycle | W-AC (v0.1.12) | Append checklist subsection to AGENTS.md "Release Cycle Expectation." PLAN §2.1. |
| **C9** (defer-rate anti-gaming note) | in-cycle | W-AC (v0.1.12) | One-line edit to `success_framework_v1.md`. PLAN §2.1. |
| **F-FS-02** (carry-over register — this doc) | in-cycle | W-CARRY (v0.1.12) | This document. |
| **C3** (W-Vb fixture-packaging fix) | in-cycle | W-Vb (v0.1.12) | Packaged fixture path under `src/health_agent_infra/demo/fixtures/`. PLAN §2.3. |
| **L1** (D13 consumer-site symmetry) | in-cycle | W-D13-SYM (v0.1.12) | Add `coerce_*` to recovery + running + sleep + stress `policy.py`; AST contract test. PLAN §2.6. |
| **C4** (privacy doc gaps + `hai auth remove`) | in-cycle | W-PRIV (v0.1.12) | Subcommand `hai auth remove [--source ...]` (Codex F-PLAN-R2-03 grammar fix). Path: `core/pull/auth.py:171` + `:261`. PLAN §2.7. |

## 3. Reconciliation §6 v0.1.13+ actions (named-deferred)

These are reconciliation actions explicitly scheduled to later
cycles. Not v0.1.12 work; included here for traceability.

| Item | Disposition | Defer to | Notes |
|---|---|---|---|
| A1 trusted-first-value rename + C7 acceptance matrix | named-defer | v0.1.13 | Onboarding cycle owns the gate language. |
| A5 declarative persona expected-actions (W-AK pulled forward) | named-defer | v0.1.13 | Precondition for v0.1.14 W58 prep. |
| C2 / W-LINT regulated-claim lint | named-defer | v0.1.13 | First surface; lands before v0.2.0 weekly review. |
| W-29-prep cli.py boundary audit | named-defer | v0.1.13 | Per CP1. |
| W-29 cli.py mechanical split | named-defer | v0.1.14 | Per CP1, conditional on prep verdict. |
| L2 W-DOMAIN-SYNC scoped contract test | named-defer | v0.1.14 | Re-scoped per Codex F-PLAN-09: single truth table + expected-subset assertions. |
| A12 judge-adversarial fixtures | named-defer | v0.1.14 | Folds into W-AI per reconciliation action 14. |
| A2 / W-AL calibration scaffold | named-defer | v0.1.14 | Schema/report shape only; real correlation work to v0.5+. |
| W-30 capabilities-manifest schema freeze | named-defer | v0.2.0 | Per CP2; after W52/W58 schema additions land. |
| MCP server *plan* (read-surface design + threat-model + provenance prereqs) | named-defer | v0.3 | Per CP4. |
| MCP read-surface ship | named-defer | v0.4 or v0.5 | Per CP4; gated by prereqs. |
| L3 §6.3 strategic-plan framing edit | named-defer | v0.1.13 strategic-plan rev | Per CP6; proposal doc authored at v0.1.12, edit applies at v0.1.13. |
| **W-FBC-2** (full F-B-04 multi-domain closure) | **named-defer** | v0.1.13 | New W-id introduced by Codex F-PLAN-R2-04 in this cycle. |

## 4. Phase 0 (D11) findings absorbed

Phase 0 internal sweep ran 2026-04-29; results in
`audit_findings.md`. Two findings, both `in-scope`:

| Finding | Disposition | W-id |
|---|---|---|
| F-PHASE0-01 (mypy +1 error / +1 file drift) | in-cycle | W-H2 |
| F-PHASE0-02 (W-N audit count 49 + 1 error vs 47 baseline; ≤ 80 branch) | in-cycle | W-N-broader |

No `revises-scope` or `aborts-cycle` findings; pre-implementation
gate fired green.

## 5. Audit-chain integrity

- v0.1.11 demo isolation contract holds (7/7 isolation surface
  tests pass against current main). Audit-chain probe clean.
- 12-persona matrix clean (0 findings, 0 crashes).
- Bandit `-ll` baseline unchanged from v0.1.11 ship (44 Low,
  0 Medium, 0 High).
- Capabilities byte-stability holds.

## 6. Settled-decision deltas at v0.1.12 ship

CPs that mutate AGENTS.md / strategic plan / tactical plan at
v0.1.12 ship (per acceptance gate `accepted`):

| CP | Effect | Verdict |
|---|---|---|
| CP1 | Lift W29/W30 cli.py-split portion of "Settled Decisions" + "Do Not Do" | accepted (round 4) |
| CP2 | Lift W29/W30 manifest-freeze portion (paired with CP1) | accepted (round 4) |
| CP3 | Add D15 four-tier cycle-weight classification | accepted (round 4) |
| CP4 | Extend strategic plan Wave 3 row with MCP staging + security gates | accepted (round 4) |
| CP5 | Reshape strategic + tactical plan v0.2.0 to single-substantial-with-shadow | accepted (round 4) |
| CP6 | Author proposal; **§6.3 edit deferred to v0.1.13 strategic-plan rev** | accepted (round 4); deferred application |

---

## Acceptance check (W-CARRY)

✅ Every line in `v0_1_11/RELEASE_PROOF.md` §5 has a disposition
row in §1 above.

✅ Every reconciliation §6 v0.1.12 item has a row in §2 above.

✅ Reconciliation v0.1.13+ items named-deferred with destination
cycle in §3 (not strictly required but improves traceability).

✅ Phase 0 findings absorbed and tagged in §4.

W-CARRY workstream deliverable complete.
