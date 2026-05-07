# HAI Planning Tree — Reading Order Index

> **Last updated:** 2026-05-07 (v0.2.0 source tree shipped; D15 IR
> round 3 verdict `SHIP`; repo reframed around runtime-contract
> research + GovernedAgentBench). Earlier 2026-05-06
> entry: v0.1.18 shipped + post-v0.1.18 strategic refresh: v0.1.19
> cancelled per CP-2U-GATE-SPLIT + D16 [foreign-user gate split into
> install/wearable/dogfood]; `post_v0_1_18/strategic_plan_v2.md`
> supersedes v1 as HAI reference-runtime strategic reference; companion
> `post_v0_1_18/v0_1_x_retro.md` documents v0.1.x track close.
> Project-wide priority now lives in `../../PROJECT_FRAME.md` and
> `../../research/runtime_contracts_paper/PAPER_FRAME.md`.

This is the orientation guide to the `reporting/plans/` tree. Read this
when you need HAI runtime release history, audit records, or backlog
provenance. For current project priority, start at
[`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md).

## Tree at a glance

```
reporting/plans/
├── README.md                          (this file)
├── post_v0_1_18/strategic_plan_v2.md  ← active strategic vision (supersedes v1 2026-05-06)
├── post_v0_1_18/v0_1_x_retro.md       ← v0.1.x track close retro (companion to v2)
├── strategic_plan_v1.md               ← SUPERSEDED 2026-05-06 (preserved as v2 source)
├── tactical_plan_v0_1_x.md            ← active release plan
├── eval_strategy/v1.md                ← active eval methodology
├── success_framework_v1.md            ← active value-measurement (post-v0.2.0 wave-boundary refresh due)
├── risks_and_open_questions.md        ← active risk + decision register (R-T-03 cli.py rot RESOLVED v0.1.17)
├── v0_1_4/ … v0_1_13/                 ← per-cycle artifacts (frozen post-ship)
├── v0_1_14/                           ← shipped 2026-05-01 (eval substrate + provenance + recovery path)
├── v0_1_14_1/                         ← shipped 2026-05-02 (hardening: garmin_live structured signal)
├── v0_1_15/                           ← shipped 2026-05-03 (publish-first package cycle)
├── v0_1_15_1/                         ← hotfix 2026-05-03 (Linux keyring fall-through)
├── v0_1_16/                           ← CANCELLED 2026-05-04 (foreign-user candidate unavailable; scope renumbered to v0.1.19)
├── v0_1_17/                           ← shipped 2026-05-05 (maintainability + eval consolidation; W-29 cli.py split + W-B body-comp + W-D arm-2)
├── v0_1_18/                           ← shipped 2026-05-06 (onboarding-quality + intake-handler migration parity; 7 W-ids closed + W-OB-6 unfired)
├── v0_1_19/                           ← CANCELLED 2026-05-06 per CP-2U-GATE-SPLIT (foreign-user empirical re-tiered to opportunistic; W-2U-INSTALL closed verbal-only, W-2U-WEARABLE + W-2U-DOGFOOD deferred to v0.4 review)
├── v0_2_0/                            ← source-tree shipped 2026-05-07 (Wave 2: weekly review W52 + factuality W58D + W-PROV-2 + evidence cards + atomic claims + Path A doc adjuncts; D15 IR R3 SHIP)
├── post_v0_1_10/                      ← historical between-cycle handoff (demo, Phase 4 audit)
├── post_v0_1_13/                      ← post-v0.1.13 strategic research + audit chain + CPs
├── post_v0_1_14/                      ← post-v0.1.14 carry-over findings + research notes
├── post_v0_1_15/                      ← post-v0.1.15 internal-docs audit + between-cycle notes
├── post_v0_1_18/                      ← post-v0.1.18 strategic refresh: CP-2U-GATE-SPLIT + strategic_plan_v2 + v0_1_x_retro
├── future_strategy_2026-04-29/        ← Claude/Codex deep strategy review
├── historical/                        ← 9 superseded planning docs
└── docs_overhaul/                     ← docs-overhaul review record
```

---

## I want to understand HAI runtime strategy.

For project-wide strategy under the research reframe, read
`../../PROJECT_FRAME.md` and
`../../research/runtime_contracts_paper/PAPER_FRAME.md` first.

**Read in order:**

1. `post_v0_1_18/strategic_plan_v2.md` — 12-24 month vision, settled
   decisions D1–D16, five hypotheses with v0.1.x evidence
   accumulation, scope-expansion exploration. **Supersedes v1 as of
   2026-05-06.**
2. `post_v0_1_18/v0_1_x_retro.md` — companion retro: what 18 cycles
   taught us. Five generalisable lessons + the patterns now load-
   bearing.
3. `tactical_plan_v0_1_x.md` — concrete next 6-8 releases.
4. `risks_and_open_questions.md` — what could derail this + what
   decisions remain.

If you only have time for one HAI strategy doc:
`post_v0_1_18/strategic_plan_v2.md`.

`strategic_plan_v1.md` is preserved as v2's primary source; read v1
only when you need the snapshot of project posture at v0.1.10.

## I want to scope the next HAI runtime release.

**Read in order:**

1. `reporting/docs/current_system_state.md` — latest shipped truth.
2. `tactical_plan_v0_1_x.md` — current release-in-flight rows
   (v0.2.0 source-tree shipped; v0.2.1 insight ledger is HAI backlog).
3. The next cycle's `PLAN.md` once authored.

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
5. `PROJECT_FRAME.md` — current research frame.
6. `research/runtime_contracts_paper/PAPER_FRAME.md` — paper frame.
7. `reporting/plans/post_v0_1_18/strategic_plan_v2.md` — HAI runtime
   strategy before the research reframe.

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
  empirical validation. Migration head 25. Test surface: 2630 passed,
  3 skipped. D14 settled 12 → 7 → 3 → 2; D15 IR settled 6 → 2 → 1 nit.
- `v0_1_15_1/` — Linux keyring fall-through hotfix (shipped 2026-05-03).
  Adds `keyrings.alt` and defensive `_default_backend()` probe so
  Linux installs without a registered desktop secret store degrade
  gracefully. Hotfix tier; no D14 or external IR.
- `v0_1_16/` — **CANCELLED 2026-05-04.** Empirical scope renumbered
  to v0.1.19 after the named candidate became unavailable. Cancellation
  note in `v0_1_16/README.md`.
- `v0_1_17/` — maintainability + eval consolidation (shipped
  2026-05-05). 10 W-ids closed at 100% acceptance: W-29 cli.py
  9,927 LOC mechanical split into 1 main + 1 shared + 11 handler-group
  modules (manifest byte-stable); W-30 schema regression test;
  W-AH-2 corpus 35 → 135; W-AI-2 `hai eval review`; W-AM-2
  4 escalate-tagged scenarios; W-Vb-4 12-of-12 persona closure;
  W-B `hai intake weight` + `body_comp` + migration 026; W-D arm-2
  partial-day projection; W-C-EQP query-plan stability; F-PV14-02
  `hai sync purge`. Schema head 26. Test surface: 2683 passed,
  4 skipped. D14 11 → 5 → 3 → CLOSE; D15 IR 6 → 1-nit.
- `v0_1_18/` — onboarding-quality + intake-handler migration parity
  (shipped 2026-05-06). 7 W-ids closed: W-OB-1 README pivot ratified;
  W-OB-2 `hai init` interactive default with `--non-interactive` +
  `HAI_INIT_NON_INTERACTIVE=1` opt-outs (release-blocker); W-OB-3
  `--guided` post-prompt `next_action_hint` + skip-input affordance
  tests; W-OB-4a Phase 1 upgrade dogfood; W-OB-4b Phase 2 local-wheel
  smoke; W-OB-5 `hai doctor next_action` across hint-emitting checks
  with manifest-consistency invariant; W-OB-7 intake-handler migration
  parity via additive `open_connection_with_migrations` helper —
  closes F-OB-PRE-01. W-OB-6 conditional did NOT fire. Schema head
  unchanged at 26. Test surface: 2756 passed, 4 skipped at close after
  follow-on release-surface fixes. D14 7 → 3 close-in-place; D15 IR
  closed at R3 SHIP_WITH_NOTES.
- `v0_2_0/` — Wave 2 substantive cycle (source-tree shipped 2026-05-07;
  D15 IR R3 verdict `SHIP`). W52 weekly
  review + W58D deterministic factuality gate + W-PROV-2 dormant-
  domain locator emission + W-EVCARD-DAILY (migration 027) +
  W-EVCARD-WEEKLY (migration 028) + W-FACT-ATOM atomic-claim corpus +
  Path A doc adjuncts (W-MCP-THREAT, W-COMP-LANDSCAPE, W-NOF1-METHOD)
  + W-EXPLAIN-UX-CARRY disposition tracker. Schema head 28
  (W-EVCARD migrations 027 + 028). Test surface: 2943 passed, 4
  skipped (broader warning gate, +187 vs v0.1.18 baseline; the +3
  over the Phase-3 close 2940 are IR R1 regression tests landed for
  F-IR-01 + F-IR-05). Persona matrix 13/13 with 0 findings + 0
  crashes. Factuality corpus 100/100 vs 97/99 thresholds. CLI
  surface: 68 commands. D14 10 → 5 → 3 → 1nit close. D15 IR settled
  R1 `SHIP_WITH_FIXES` → R2 `SHIP_WITH_FIXES` → R3 `SHIP`. Honesty
  boundary gates G15-G17 reserve
  foreign-user empirical (W-2U-WEARABLE/DOGFOOD), LLM-judge
  factuality (W58J → v0.2.2), and insight-ledger persistence
  (W53 → v0.2.1) for downstream cycles.

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

## post_v0_1_18/

Post-v0.1.18 strategic refresh + v0.1.x track close. Current contents:

- `CP-2U-GATE-SPLIT.md` — cycle proposal authorising the
  three-way split of W-2U-GATE (install closed verbal-only,
  wearable + dogfood deferred to v0.4 review). AGENTS.md D16
  applied.
- `strategic_plan_v2.md` — fresh-authored strategic plan
  (2026-05-06). Supersedes `strategic_plan_v1.md` as the HAI
  reference-runtime forward reference. Cites v1 as primary source.
  The repo-wide research frame now lives at `../../PROJECT_FRAME.md`.
- `v0_1_x_retro.md` — companion retro on what 18 cycles taught
  us. External-readable; intended for portfolio / careers
  context as well as project continuity.

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
