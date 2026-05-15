# CP-PATH-A — Split v0.2.0 into four releases (strict-C6 honoring)

**Cycle:** v0.2.0 PLAN authoring upcoming.
**Author:** Claude (delegated by maintainer; OQ-B 2026-05-01).
**Codex verdict:** applied at v0.1.14 D14 round 1
(PLAN_COHERENT_WITH_REVISIONS); tactical_plan §6/§7/§8/§9 split
applied 2026-05-01 pre-cycle. F-PLAN-07 surfaced stale propagation
gaps from the application: title still "v0.1.11 through v0.2.0",
§11 subheads still 8.x, §12 risk-cut text still claimed "W53 from
v0.2.0", §13 boundary still "v0.1.11 → v0.2.0" — all corrected at
v0.1.14 D14 round 1.
**Application timing:** at v0.2.0 PLAN.md authoring — replaces
tactical_plan_v0_1_x.md §6 v0.2.0 single-release shape with a
4-release sequence (v0.2.0 / v0.2.1 / v0.2.2 / v0.2.3); revisits
CP5 (v0.1.12) with named reasoning.
**Source:** Strategic-research report 2026-05-01 §11 Path A; Codex
research-audit round-1 F-RES-03; Codex round-2 F-RES-R2-01;
reconciliation §3.B; reconciliation.md C6 (one schema group per
release). Maintainer OQ-B answered Path A 2026-05-01.

---

## Rationale

CP5 (v0.1.12) settled v0.2.0 as a "single substantial release with
shadow-by-default LLM judge." The argument was W52↔W58 design
coupling: claims surface (W52) + claim-checker (W58) should not
ship apart. That argument is correct.

CP5 did *not* engage with reconciliation C6
(`reporting/plans/future_strategy_2026-04-29/reconciliation.md:147`):

> **Migration cadence:** the store has strict gap detection. v0.2.0
> should not add weekly review tables + insight ledger tables +
> judge log tables in one migration burst. **One conceptual schema
> group per release.**

C6 is a correctness-flavored constraint (the gap detector *will*
trip on a 3-schema-group migration), not a sequencing preference.
CP5 and C6 are in tension. The strategic-research report Codex
round-2 audit (F-RES-R2-01) corrected an initial 3-release Path A
to 4 releases for strict-C6 honoring — the 3-release shape still
left v0.2.1 carrying two schema groups (insight ledger + judge log)
and therefore did not actually honor C6.

**The 4-release Path A preserves CP5's W52↔W58 coupling argument
in v0.2.0 (W52 + W58D ship together) while honoring C6 strictly
across the cycle sequence.** Each downstream release ships exactly
one schema group, or no schema group.

This is a deliberate revisit of CP5, not a violation. CP5's
substance (preserve W52↔W58 coupling) is honored; its scope
(everything in one cycle) is rescoped.

## Current tactical_plan_v0_1_x.md text (verbatim, verified on disk 2026-05-01)

`reporting/plans/tactical_plan_v0_1_x.md:441-503`:

```
## 6. v0.2.0 — Weekly review + insight ledger + factuality gate

> **Theme.** Make the runtime useful beyond one day. Original v0.1.9
> scope (cut to hardening); now lands as v0.2.0. Detail in strategic
> plan § 7 Wave 2.

### 6.1 In scope

Lifted from `historical/multi_release_roadmap.md` § 4 v0.1.9 (cut),
now v0.2.0. **Reshaped at v0.1.12 per CP5 (single substantial
release with shadow-by-default LLM judge):**

- **W52: `hai review weekly --week YYYY-Www [--json|--markdown]`.**
  ...
- **W53: Insight proposal ledger** (`insight_proposal` + `insight`
  tables).
- **W58D: Deterministic factuality gate.** ... Blocking from day 1.
  No LLM in this layer.
- **W58J: LLM judge layer.** ... Ships **shadow-by-default** ...
  Flag flip to blocking happens within v0.2.0 (or v0.2.0.x patch)
  ...
- **W-30: capabilities-manifest schema freeze** as the last act
  of the cycle, after W52/W58D/W58J schema additions land
  (per CP2).

### 6.2 Acceptance

- Weekly review runs deterministically ...
- Insight proposal ledger has migration + CLI + snapshot ...
- Factuality judge: deterministic claim-block (W58D) enforces
  from day 1. LLM judge (W58J) ships shadow-by-default ...
- Capabilities-manifest schema frozen as last cycle act
  (W-30 / per CP2).
- Test count grows ≥ 30 vs v0.1.14.

### 6.3 Effort estimate

15-20 days. Last v0.1.x-style release ...
```

## Proposed delta — replace tactical_plan_v0_1_x.md §6 with §6, §7, §8, §9

The current §6 single-release shape is replaced by four sections,
one per release. The §7 cross-cutting section that follows is
renumbered to §10.

### New §6 — v0.2.0 — Weekly review + deterministic factuality

> **Theme.** Make claims about the past week deterministically
> checkable. Lifts W52 + W58D from CP5; W53 / W58J / W-30 split
> across v0.2.1-v0.2.3 per CP-PATH-A (post-v0.1.13 strategic
> research; reconciliation C6).

**In scope:**
- **W52: `hai review weekly --week YYYY-Www [--json|--markdown]`.**
  Source-row locators required for every quantitative claim
  (carrier: `recommendation_evidence_card.v1` schema per
  reconciliation C8). Builds on v0.1.14 W-PROV-1.
- **W58D: Deterministic factuality gate.** Every quoted quantitative
  claim in weekly-review prose must resolve to a source-row
  locator. Blocking from day 1. No LLM in this layer.
- **W-FACT-ATOM:** FActScore-shaped atomic-claim decomposition
  (folds into W58D).
- **Doc-only adjuncts:** W-MCP-THREAT (per CP-MCP-THREAT-FORWARD),
  W-COMP-LANDSCAPE, W-NOF1-METHOD, W-2U-GATE-2 (second foreign
  user).

**Schema group:** weekly-review tables + claim-block (one group;
honors C6).

**Acceptance:**
- Weekly review runs deterministically over fixture weeks,
  output byte-stable.
- W58D blocks unsupported claims; tested against a corpus of
  known-good and known-bad examples.
- Test count grows ≥ 30 vs v0.1.14.
- W-MCP-THREAT artifact filed; OWASP MCP Top 10 mapping verified
  against primary source per CP-MCP-THREAT-FORWARD.

**Effort estimate:** 18-24 days. Cycle tier: substantive.

### New §7 — v0.2.1 — Insight ledger

> **Theme.** Persist multi-week insights with provenance. One
> schema group only.

**In scope:**
- **W53: Insight proposal ledger** (`insight_proposal` + `insight`
  tables). Insight rows persist with provenance; `hai insights`
  lists; user commit gates promotion to durable insight.

**Schema group:** insight ledger (one group; honors C6).

**Acceptance:**
- Insight proposal ledger has migration + CLI + snapshot integration
  + capability manifest entry.
- User-commit gating tested (agent-proposed insight cannot promote
  without explicit user step).
- Test count grows ≥ 15 vs v0.2.0.

**Effort estimate:** 8-12 days. Cycle tier: hardening (single
substantive workstream).

### New §8 — v0.2.2 — LLM judge shadow-by-default

> **Theme.** Add LLM judgment as a shadow layer over W58D's
> deterministic gate.

**In scope:**
- **W58J: LLM judge layer.** Residual judgment on causal framing,
  missing uncertainty, overconfident tone. Local Prometheus-2-7B
  (or comparable) pinned by SHA. Builds on v0.1.14's W-AJ harness.
  Ships **shadow-by-default** with `HAI_W58_JUDGE_MODE = shadow |
  blocking` env flag. Logs every shadow-mode judgement to
  `judge_decision_log` table for evidence accumulation.
- **W-JUDGE-BIAS:** bias test panel covering position bias,
  verbosity bias, score-rubric-order bias, reference-answer bias,
  self-consistency. Thresholds proposed per HAI strategic-research
  §13 E-3; validated locally per shadow-mode runs.

**Schema group:** judge log (`judge_decision_log` table; one group;
honors C6).

**Acceptance:**
- W58J runs shadow-by-default; logs every shadow decision.
- W-JUDGE-BIAS test panel runs against shadow-mode output;
  thresholds proposed per E-3.
- Memory-poisoning fixtures present (per reconciliation A12).
- Test count grows ≥ 20 vs v0.2.1.

**Effort estimate:** 8-12 days. Cycle tier: substantive.

### New §9 — v0.2.3 — Judge promotion + capabilities freeze

> **Theme.** Flip the judge from shadow to blocking + freeze the
> capabilities manifest schema.

**In scope:**
- **W58J flip from shadow to blocking.** Conditional on
  W-JUDGE-BIAS panel passing (HAI-proposed thresholds met across
  ≥ 50 shadow-mode weekly reviews per CP5's original criterion).
  Maintainer cannot manually override (the bias panel is the
  override criterion).
- **W-30: capabilities-manifest schema freeze** as the last act
  of the v0.2.x sequence, after W52/W58D/W53/W58J schema
  additions have all landed (per CP2 + CP-W30-SPLIT).

**Schema group:** none (flag flip + manifest pin).

**Acceptance:**
- W-JUDGE-BIAS panel passing for ≥ 50 shadow-mode runs.
- W58J flag flips; existing tests pass under blocking mode.
- Capabilities-manifest schema frozen; new fields require migration
  + version bump + explicit override.

**Effort estimate:** 5-8 days. Cycle tier: hardening.

### Total Path A v0.2.x effort

39-56 days across four cycles. Larger than CP5's 15-20 day single-
release estimate but distributes audit surface across four D14
plan-audits (each smaller than a single 5-6 round D14 on a
3-schema-group cycle). Estimated D14 rounds per cycle: 3-4 each.

## Affected files

- `reporting/plans/tactical_plan_v0_1_x.md` §6 (replaced with §6/§7/§8/§9; existing §7 cross-cutting renumbered to §10).
- `reporting/plans/strategic_plan_v1.md` Wave 2 row updated to
  reflect 4-release shape.
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-W30-SPLIT.md`
  (separate CP) — places W-30 in v0.2.3.
- `ROADMAP.md` Now/Next sections updated.
- `reporting/plans/v0_2_0/PLAN.md` (new at v0.2.0 PLAN authoring) —
  scope per new §6.
- `reporting/plans/v0_2_1/PLAN.md` etc. as cycles open.

## Dependent cycles

- **v0.2.0**: ships W52 + W58D + adjuncts. Schema group: weekly-
  review + claim-block.
- **v0.2.1**: ships W53. Schema group: insight ledger.
- **v0.2.2**: ships W58J shadow + W-JUDGE-BIAS. Schema group:
  judge log.
- **v0.2.3**: W58J promotion + W-30 freeze. No new schema.
- **v0.3+ MCP cycles**: unchanged from CP4 + CP-MCP-THREAT-FORWARD.

## Acceptance gate

- `accepted`: tactical_plan §6 split into §6/§7/§8/§9 per the
  delta above. CP5 marked as superseded for the cycle-shape
  question (W52↔W58 coupling preservation is the surviving
  substance).
- `accepted-with-revisions`: 4-release shape preserved; per-release
  scope or sizing revised. The "one schema group per release"
  property is load-bearing — any revision that recombines schema
  groups defeats CP-PATH-A's purpose and falls back to CP5
  single-release shape.
- `rejected`: CP5 stands; v0.2.0 ships single-release with 3 schema
  groups + W-30; reconciliation C6 is treated as advisory rather
  than load-bearing. Requires authoring a separate CP that
  explicitly overrides C6.

## Round-N codex verdict

**Applied at v0.1.14 D14 round 1 (PLAN_COHERENT_WITH_REVISIONS,
2026-05-01).** tactical_plan §6/§7/§8/§9 split applied 2026-05-01
pre-cycle. F-PLAN-07 surfaced stale propagation gaps from the
application: title still "v0.1.11 through v0.2.0", §11 subheads
still 8.x, §12 risk-cut text still claimed "W53 from v0.2.0", §13
boundary still "v0.1.11 → v0.2.0" — all corrected at v0.1.14 D14
round 1. F-PLAN-R2-07 (round 2) corrected §11.3 verdict-scale
mixing (D14 vs IR phases now described separately).
