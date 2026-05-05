# Planning Tree — Reading Order Index

> **Last updated:** 2026-05-05 (v0.1.17 shipped — maintainability +
> eval substrate consolidation; 10 W-ids closed at 100% acceptance.
> v0.1.16 was cancelled 2026-05-04; foreign-user empirical work is
> now v0.1.19, sequenced after v0.1.18 onboarding).

This is the orientation guide to the `reporting/plans/` tree.
Read this when you're returning cold and need to find the right
doc by intent.

## Tree at a glance

```
reporting/plans/
├── README.md                          (this file)
├── strategic_plan_v1.md               ← active strategic vision
├── tactical_plan_v0_1_x.md            ← active release plan
├── eval_strategy/v1.md                ← active eval methodology
├── success_framework_v1.md            ← active value-measurement
├── risks_and_open_questions.md        ← active risk + decision register
├── v0_1_4/ … v0_1_13/                 ← per-cycle artifacts (frozen post-ship)
├── v0_1_14/                           ← shipped 2026-05-01 (eval substrate + provenance + recovery path)
├── v0_1_14_1/                         ← shipped 2026-05-02 (hardening: garmin_live structured signal)
├── v0_1_15/                           ← shipped 2026-05-03 (publish-first package cycle)
├── v0_1_15_1/                         ← hotfix 2026-05-03 (Linux keyring fall-through)
├── v0_1_16/                           ← next empirical-fix workspace (authors after foreign-user candidate transcript)
├── v0_1_17/                           ← maintainability + eval consolidation workspace
├── post_v0_1_10/                      ← historical between-cycle handoff (demo, Phase 4 audit)
├── post_v0_1_13/                      ← post-v0.1.13 strategic research + audit chain + CPs
├── post_v0_1_14/                      ← post-v0.1.14 carry-over findings + research notes
├── post_v0_1_15/                      ← post-v0.1.15 internal-docs audit + between-cycle notes
├── future_strategy_2026-04-29/        ← Claude/Codex deep strategy review
├── historical/                        ← 9 superseded planning docs
└── docs_overhaul/                     ← docs-overhaul review record
```

---

## I want to understand the project's strategic direction.

**Read in order:**

1. `strategic_plan_v1.md` — 12-24 month vision, settled decisions,
   five hypotheses, scope-expansion exploration.
2. `tactical_plan_v0_1_x.md` — concrete next 6-8 releases.
3. `risks_and_open_questions.md` — what could derail this + what
   decisions remain.

If you only have time for one: `strategic_plan_v1.md`.

## I want to scope the next release.

**Read in order:**

1. `reporting/docs/current_system_state.md` — latest shipped truth.
2. `tactical_plan_v0_1_x.md` — current release-in-flight rows
   (v0.1.16 empirical fixes, v0.1.17 maintainability/eval).
3. `v0_1_16/README.md` — next-cycle workspace. PLAN.md is intentionally
   absent until the named foreign-user candidate's transcript exists.
4. The opening cycle's `PLAN.md` once authored.

If you only have time for one: the open cycle's `PLAN.md` (or, when
no cycle is open, `tactical_plan_v0_1_x.md` for the next two
release rows).

## I want to know how we evaluate correctness.

**Read in order:**

1. `eval_strategy/v1.md` — five eval classes, current coverage,
   ground-truth methodology.
2. `verification/dogfood/README.md` — persona harness operating
   guide.
3. `src/health_agent_infra/evals/rubrics/domain.md` — per-scenario
   rubric mechanics.

If you only have time for one: `eval_strategy/v1.md`.

## I want to know if the project is succeeding.

**Read in order:**

1. `success_framework_v1.md` — north-star, Tier 1-3 metrics,
   anti-metrics.
2. CHANGELOG.md (top entry) — what just shipped.

If you only have time for one: `success_framework_v1.md`.

## I want to understand what could go wrong.

**Read in order:**

1. `risks_and_open_questions.md` § 2-7 — strategic, technical,
   operational, external risks.

## I need to make a decision and don't want to commit.

**Read:**

1. `risks_and_open_questions.md` § 8 — open questions for
   maintainer judgement.
2. AGENTS.md "Settled Decisions" — what's already been decided.

## I'm a new agent session opening cold.

**Read in order:**

1. `AGENTS.md` (project root) — operating contract.
2. `README.md` (project root) — product story + quickstart.
3. `ARCHITECTURE.md` (project root) — runtime shape.
4. `REPO_MAP.md` (project root) — every directory classified.
5. `reporting/plans/strategic_plan_v1.md` — strategic frame.
6. `reporting/plans/tactical_plan_v0_1_x.md` — execution frame.

## I'm reviewing a specific past release.

Cycle directories preserve their own history:

- `v0_1_4/` — running activity pull (per memory).
- `v0_1_6/` — intervals.icu integration.
- `v0_1_7/` — auto manifest + W21 next-actions.
- `v0_1_8/` — plan-aware feedback visibility (W43, W48, W51).
- `v0_1_9/` — hardening + governance closure (B1-B8).
- `v0_1_10/` — pre-PLAN audit pattern + persona harness.
- `v0_1_11/` — audit-cycle deferred items + persona expansion (shipped 2026-04-28).
- `v0_1_12/` — carry-over closure + trust repair (shipped 2026-04-29).
- `v0_1_12_1/` — Cloudflare User-Agent hotfix (shipped 2026-04-29).
- `v0_1_13/` — onboarding + W-Vb/W-N-broader/W-FBC-2 closure +
  governance prerequisites (shipped 2026-04-30, **largest cycle in
  the v0.1.x track at 17 W-ids**).
- `v0_1_14/` — eval substrate + provenance + recovery path
  (W-PROV-1 + W-AJ + W-AL + W-BACKUP + W-EXPLAIN-UX + W-FRESH-EXT +
  W-DOMAIN-SYNC + W-AN closed; W-AH / W-AI / W-Vb-3 partial-closed
  to v0.1.15; W-2U-GATE / W-29 deferred to v0.1.15). Shipped
  2026-05-01. D14 settled at round 4 PLAN_COHERENT; IR settled at
  round 3 SHIP_WITH_NOTES.
- `v0_1_14_1/` — hardening cycle: Garmin-live unreliability surfaced
  as structured capabilities signal (W-GARMIN-MANIFEST-SIGNAL).
  Shipped 2026-05-02 as a hardening tier (D15) with abbreviated
  audit chain (no external Codex IR). Test surface: 2581 passed.
- `v0_1_15/` — package release published 2026-05-03.
  Six W-ids shipped (W-GYM-SETID, F-PV14-01, W-A, W-C, W-D arm-1,
  W-E); W-2U-GATE reframed from pre-publish ship gate to post-publish
  empirical validation feeding v0.1.16. Migration head 25. Test
  surface: 2630 passed, 3 skipped. D14 settled 12 → 7 → 3 → 2;
  D15 IR settled 6 → 2 → 1 nit.

Each cycle directory typically contains:
- `PLAN.md` — cycle scope.
- `audit_findings.md` (v0.1.10+) — pre-PLAN bug hunt findings.
- `BACKLOG.md` — items deferred from this cycle.
- `codex_audit_prompt.md` — external audit prompt.
- `codex_audit_response.md` (and round 2/3/4) — Codex findings.
- `RELEASE_PROOF.md` — ship readiness proof.
- `REPORT.md` — post-ship retro.

## I want to read the current strategy review (Apr 2026).

The 2026-04-29 deep strategy review lives in
`future_strategy_2026-04-29/`:

- `reconciliation.md` — single decision-ready synthesis of the two
  reviews. Start here if you only have time for one.
- `review_claude.md` — Claude's two-pass review (1200 lines).
- `review_codex.md` — Codex's three-pass review (2005 lines).

The reconciliation drives the v0.1.12+ planning refresh.

## I want to read the post-v0.1.13 strategic research (May 2026).

The 2026-05-01 post-v0.1.13 strategic research lives in
`post_v0_1_13/`:

- `strategic_research_2026-05-01.md` — 21-section operational
  research report (Codex-audited 2 rounds, closed
  REPORT_SOUND_WITH_REVISIONS). Start here if you only have time
  for one.
- `reconciliation.md` — consolidates the audit chain + per-finding
  dispositions. Read after the report.
- `cycle_proposals/CP-*.md` — five CPs authored from the report:
  CP-2U-GATE-FIRST, CP-MCP-THREAT-FORWARD, CP-DO-NOT-DO-ADDITIONS,
  CP-PATH-A, CP-W30-SPLIT.
- Audit-chain artifacts: `codex_research_audit_prompt.md` (rounds
  1+2) + `codex_research_audit_response.md` (rounds 1+2) +
  `codex_research_audit_round_N_response.md` (maintainer
  dispositions).

The research drives v0.1.14 PLAN.md scope and the v0.2.0-v0.2.3
Path A 4-release split.

## Historical / superseded docs (preserve provenance, do not act on)

All 9 superseded docs live under `historical/`:

- `historical/multi_release_roadmap.md` — **SUPERSEDED 2026-04-27** by
  `strategic_plan_v1.md` + `tactical_plan_v0_1_x.md`.
- `historical/post_v0_1_roadmap.md` — earlier roadmap; superseded by
  the multi-release roadmap (2026-04-25), now further superseded.
- `historical/agent_operable_runtime_plan.md` — Phase-3 design doc;
  some details lifted into AGENTS.md.
- `historical/phase_0_findings.md`,
  `historical/phase_0_5_synthesis_prototype.md`,
  `historical/phase_2_5_retrieval_gate.md`,
  `historical/phase_2_5_independent_eval.md` — pre-v0.1 design
  exploration.
- `historical/skill_harness_rfc.md` — pre-v0.1 RFC.
- `historical/launch_notes.md` — pre-v0.1 launch checklist.

Do not assume claims in historical docs are still load-bearing.
Cross-check against AGENTS.md "Settled Decisions" if relying on
any of them.

## docs_overhaul/

The `docs_overhaul/` directory contains the historical v0.1.x
documentation restructuring review record (`codex_review.md`). It is
provenance, not the current docs-operating surface.

## post_v0_1_15/

Post-v0.1.15 between-cycle notes. Current contents:

- `internal_docs_audit.md` — internal-docs audit + fix report from
  the 2026-05-03 post-publish cleanup.

---

## How to keep this index current

When a new doc is added or an old doc retired:

1. Add or remove the entry above.
2. Update `reporting/docs/current_system_state.md` if the change affects
   current truth, schema head, command count, or next-cycle role.
3. Update the relevant cycle PLAN.md to reflect the doc relationship.
4. Bump the "Last updated" date at top.

This file is small enough that drift is the maintainer's
responsibility — no automated check today.
