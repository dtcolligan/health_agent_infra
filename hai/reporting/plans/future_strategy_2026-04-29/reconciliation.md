# Future Strategy Review — Claude/Codex Reconciliation

**Date:** 2026-04-29
**Scope:** Synthesises `future_strategy_review.md` (Claude, 1200 lines, two
research passes) and `future_strategy_review_codex.md` (Codex, 2005 lines,
three research passes) into a single decision-ready document. Both originals
are preserved as independent reads.
**Posture:** Independent-arrival agreements are high signal. Genuine
disagreements name themselves clearly so Dom can decide.

---

## 1. Combined verdict

Both reports independently land on the same family: **PLAN_STRONG_WITH_REVISIONS**.

The strategic foundation (`strategic_plan_v1.md` + `tactical_plan_v0_1_x.md`
+ `eval_strategy/v1.md` + `success_framework_v1.md`
+ `risks_and_open_questions.md`) does not need reshaping. The deltas are
release-sequence and planning-system corrections, plus a small set of
code/doc concerns. The audit-cycle pattern (D11/D14) is exercised, not
ritualised — v0.1.11's 10 → 5 → 3 → 0 plan-audit halving is a healthy
signature.

---

## 2. Independent-arrival agreements (high signal — both reports caught these)

These were arrived at separately by both passes. Treat as committed
direction unless Dom objects.

| # | Finding | Claude ref | Codex ref |
|---|---|---|---|
| A1 | v0.1.13 "first recommendation in 5 min" gate is too ambiguous; rename to "trusted first value" / "second developer-user" | §1, §10 | F-FS-03, J |
| A2 | W-AL calibration eval is premature in v0.1.14; push the real correlation work to v0.5+; only schema/report shape lands sooner | §10 row v0.5, §12 #2 | F-FS-06, F |
| A3 | H5 should be narrowed away from broad anti-multi-agent claims toward auditability + reproducibility per unit complexity | §3.5 | F-FS-08, D-H5 |
| A4 | H4 PHIA evidence wording is over-specific ("3-agent equal-token-budget"); refresh before next strategic plan rev | §5 | F-FS-07, D-H4 |
| A5 | Persona expected-actions need to become declarative *before* W58 judge work; scenario count mismatch (28 vs ~50) needs normalising | §10 row v0.1.13 (W-AK pulled forward) | F-FS-13 |
| A6 | Open Wearables / MCP servers / Nori / Apple Health MCP commoditise data-access; data-source breadth is not the moat | §6 | F-FS-09, G |
| A7 | `cli.py` is approaching D4 trip-wire during high-risk feature work; act before forced split during onboarding | §3.1, §7.2-7.3, §12 #1 | F-FS-12, I |
| A8 | Public/default docs (`README.md`, `ROADMAP.md`, `HYPOTHESES.md`, `reporting/plans/README.md`, `AUDIT.md`) need a freshness sweep | §9.5 (general) | F-FS-10 (specific instances) |
| A9 | The plans need explicit cycle-weight tiering (substantive vs hardening vs doc-only) so D11/D14 effort matches scope | §9.4 | Planning recs §4 |
| A10 | Move 7+ historical root planning docs to `reporting/plans/historical/` | §12 surgical edits | Planning recs §2, F-FS-11 |
| A11 | Strategic positioning: "local-first governed runtime for personal-health agents" — *not* "AI health coach" | §6 (round 2) | F-FS-01 |
| A12 | The judge in W58 needs adversarial fixtures + shadow mode before blocking; prompt-injection / source-conflict / judge-bias robustness | §10 row v0.1.14, §12 surgical edits | F-FS-05, E |

---

## 3. Genuine disagreements (Dom decides)

These are the points where the reports actually diverge. Each names the
disagreement, both arguments, my recommendation, and what's at stake.

### D1. v0.2.0 — split into four releases or keep atomic?

- **Codex (F-FS-04, J):** Split v0.2.0 / v0.2.1 / v0.2.2 / v0.2.3 = weekly
  review only / insight ledger / factuality gate shadow / factuality gate
  blocking. Argument: too much schema, CLI, eval, and model-risk surface
  in one cycle; a judge false-positive can block the whole milestone.
- **Claude (round 2 §3.2):** Keep atomic. W52 (weekly review) and W58
  (factuality gate) are *design-coupled* — the judge exists because the
  weekly review needs source-grounded prose. Splitting them means a
  weekly-review v0.2.0 ships ungated. Tactical plan §9 lists both as
  DO-NOT-CUT.

**My read after seeing both:** Codex wins on the W58 split, Claude wins on
the W52↔W58 coupling. The synthesis is **3 releases, not 4 and not 1**:

- **v0.2.0** — W52 weekly review + W58 *deterministic* unsupported-claim
  block (no LLM judge yet). Source-row locators required. Byte-stable
  weekly output over fixtures. This *is* gated, just deterministically.
- **v0.2.1** — W53 insight ledger + W58 LLM-judge **shadow mode**
  (logs only, never blocks). Memory-poisoning fixtures.
- **v0.2.2** — W58 LLM-judge **blocking** mode after one release of
  shadow-mode evidence.

This preserves Claude's coupling argument (weekly review is gated from
day 1) while accepting Codex's correct point that an LLM judge in
blocking mode without shadow evidence is a release-risk vector. **This is
the most important disagreement to resolve.**

### D2. cli.py — schedule the split or schedule the re-evaluation?

- **Codex (F-FS-12, I):** Add a D4 *re-evaluation workstream* before
  v0.2.0. Measure command groups, identify low-risk extraction
  boundaries, define manifest-preserving parser-registration tests.
  *Decide* whether to split. If no split, at minimum add
  parser/capabilities regression test.
- **Claude (§7.2-7.3, §12 #1):** Schedule **W-29 cli.py split at
  v0.1.14** as a 3-4 day mechanical refactor. Concrete shape: 1 main
  + 1 shared + 11 handler-group files, each <2500 lines. Land before
  v0.2.0 W52/W53 commands so they inherit the new layout. Treat 10k
  as abort condition, not trigger.

**My read:** These are compatible if sequenced. Run Codex's
re-evaluation as **W-29-prep at v0.1.13** (half-day audit), run
Claude's mechanical split as **W-29 at v0.1.14** if the prep concludes
the boundaries are clean. **Either way the parser/capabilities
regression test is non-optional** — that's the cheapest insurance
against a future split changing CLI surface silently. Both reports
agree the worst outcome is splitting under pressure during onboarding
or weekly-review work.

### D3. Cycle weight tiers — three classes or four?

- **Codex (Planning §4):** Four tiers — substantive / hardening / doc-only
  / hotfix.
- **Claude (§9.4):** Three tiers — substantive / hardening / doc-only.
  Hotfixes already have an implicit lighter touch.

**My read:** Trivial. Codex's four-tier is more explicit; Claude's
three-tier is closer to current practice. **Pick four**: codifying
"hotfix" prevents the hardening tier from absorbing legitimate hotfix
work and inflating its audit cost.

### D4. v0.3+ surface — read-only UI checkpoint vs MCP-as-distribution

- **Codex (J v0.3+):** Treat v0.3+ as external integration / MCP
  *prerequisites*: weekly review stable, threat model, no raw SQLite
  surface, source provenance contract. **Then** decide MCP exposure.
- **Claude (§10 row v0.3, §12 #6):** Dual-publish health-agent-infra
  as MCP server in v0.3 (~1 cycle, ~1k LOC). Mirrors `hai` capabilities
  boundary; W57 commit path *not* exposed (LLM cannot deactivate user
  state through MCP). Read-only UI stays at v0.5.

**My read:** Codex's prerequisites list is right; Claude's MCP scope
is right. The synthesis: **MCP exposure is an offence move, but
gated by Codex's prerequisites**. v0.3 *plans* the MCP server,
v0.4 *prerequisites* land (provenance, threat model), v0.4 or v0.5
*ships* the MCP read surface. Don't dual-publish before the threat
model exists.

---

## 4. Codex caught these; Claude missed them

These are real findings that did not appear in Claude's report.
Each should land in the next cycle's BACKLOG or v0.1.12 PLAN.

| # | Finding | Action |
|---|---|---|
| C1 | **Specific stale public-doc instances:** `ROADMAP.md` says "v0.1.8 current" and points to superseded roadmap; `HYPOTHESES.md` says superseded roadmap is "the working document"; `reporting/plans/README.md:95` calls v0.1.11 "in flight" though it shipped (verified on disk 2026-04-29). | **v0.1.12 W-AC** — pre-implementation doc-freshness sweep. Required before D14. |
| C2 | **Regulated-claim lint** with concrete taxonomy — "abnormal HRV", "clinical-grade marker", "risk score", "detects overtraining syndrome", "monitor diabetes", "biomarker" must not appear in user-facing prose. Maps to FDA general-wellness boundary. | Add **W-LINT** to v0.1.13 or v0.2.0 PLAN.md. Cover packaged skills, recommendation prose, weekly-review prose, insight labels, and public docs. Land *before* W52 weekly review starts generating user-facing rationale at scale. |
| C3 | **W-Vb fixture-packaging:** demo personas should not import from `verification/dogfood` at runtime; that path is not packaged wheel data. Either move fixtures to a packaged module/resource path or build a runtime fixture loader with wheel-availability tests. | Update v0.1.12 W-Vb or v0.1.13 to specify packaged-resource path. |
| C4 | **Privacy doc gaps:** `reporting/docs/privacy.md:59` says no `hai auth --remove` exists; line 116 says no first-class "forget one day" command; chmod failure semantics on shared filesystems are not explained. | v0.1.12 doc sweep (with C1) + v0.1.13 add credential-revoke UX (or explicitly defer with reason). |
| C5 | **W58 architecture redesign:** deterministic claim-extraction + source-row locators *before* any LLM judgment. Block on unsupported quantitative claims with code, not with the judge. LLM judge becomes residual (causal framing, missing uncertainty, overconfident tone). | Rewrite v0.2.0 W58 acceptance to be deterministic-first. The judge is the second line, not the first. Per D1 above, this aligns with the v0.2.0 deterministic-only / v0.2.1 shadow / v0.2.2 blocking sequence. |
| C6 | **Migration cadence:** the store has strict gap detection. v0.2.0 should not add weekly review tables + insight ledger tables + judge log tables in one migration burst. **One conceptual schema group per release.** | Confirm in v0.2.0/v0.2.1/v0.2.2 PLAN.md that each release introduces one schema group. |
| C7 | **v0.1.13 acceptance matrix:** five explicit paths (blank demo / persona demo / real intervals.icu / host-agent flow / failure path) × explicit required result. Not a single "5 minutes to first recommendation" gate. | Use Codex's matrix verbatim in v0.1.13 PLAN.md acceptance section. |
| C8 | **Evidence-card schema** as concrete deterministic audit artifact (`recommendation_evidence_card.v1`). Specifies schema, CLI, migration, and W-rule integration. | Include in v0.2.0 W52 design — the source-row-locator requirement (D1, C5) needs a concrete carrier. |
| C9 | **Defer-rate anti-gaming note:** lower defer rate is *not* better if it comes from false confidence. Add to `success_framework_v1.md` before v0.5 calibration metrics start being read. | One-line edit. Bundle with A8 doc sweep. |
| C10 | **Source-row locators for every quantitative claim** — the deterministic primitive that makes A12 / C5 implementable. | First class concept in W52 weekly review, not added later. |

---

## 5. Claude caught these; Codex missed them

These are findings that did not appear in Codex's report.

| # | Finding | Action |
|---|---|---|
| L1 | **D13 asymmetric application:** consumer sites in `domains/{recovery,running,sleep,stress}/policy.py` read `t["policy"][...]` directly *without* `coerce_*` helpers; strength + nutrition use coercers correctly. The threshold-injection seam is defended at load time by `_validate_threshold_types`, but consumer-site defence is uneven. If a future caller bypasses `load_thresholds`, four domains silently coerce bool-as-int. | Add **D13-symmetry contract test** in v0.1.12 (~30 min). Scans for raw `t["policy"][...]` reads; fails on new ones. |
| L2 | **Hardcoded 6-domain enumeration tables:** ~8 registries (`_ACCEPTED_STATE_TABLES`, `RECOMMENDATION_SCHEMA_BY_DOMAIN`, `SCHEMA_VERSION_BY_DOMAIN`, `ALLOWED_ACTIONS_BY_DOMAIN`, `_DOMAIN_ACTION_REGISTRY`, `_DEFAULT_REVIEW_QUESTIONS`, `_DOMAIN_REVIEW_QUESTION_OVERRIDES`, `V1_EXPECTED_DOMAINS`) enumerate the six domains by name. None is the source of truth for the others. A forgotten registry entry on a 7th-domain expansion would be silent. | Add **W-DOMAIN-SYNC** in v0.1.14 (~half day). Single contract test introspects all 8 registries against a single truth table. Pays off at 7th-domain expansion (v0.7+). |
| L3 | **The actual moat is narrower than "publishable rule DSL".** R-rule + X-rule code is competent engineering, not novel theory. What's genuinely defensible: (a) the audit chain, (b) the skill-overlay invariant (`_overlay_skill_drafts` whitelists 3 keys, raises on anything else, no skill imports in runtime code), (c) the Phase B write-surface guard (`guard_phase_b_mutation`). Strategic plan §6.3 oversells. | Soften §6.3 framing to "publishable governance contract + audit chain + skill-overlay seam." Cycle proposal under AGENTS.md (substantive plan edit). |
| L4 | **Concrete cli.py split shape:** 1 main + 1 shared + 11 handler-group files, each <2500 lines. Treat 10k as abort condition, not trigger. | Use as input to D2 re-evaluation. |
| L5 | **MCP-as-distribution-offence:** Open Wearables / Pierre / garmy threat is *overstated* (Pierre 404, garmy dormant), but MCP-as-distribution is the durable channel in 2026. Health Agent Infra dual-publishing as an MCP server is offence (reach), not defence. | See D4 above. |
| L6 | **Round-1 mistake corrections (methodology):** explicit "what I got wrong and why" trace for 5 round-1 recommendations that fought straw-men or ignored settled decisions. | Treat as auditable methodology — adversarial review of one's own recommendations is a discipline worth carrying into D14 round-2 culture. |

---

## 6. Combined recommended action set (priority-ordered)

This is the merged punch-list that should drive v0.1.12 PLAN.md and the
forward roadmap. It is what falls out of §2 + §3-resolutions + §4 + §5.

**v0.1.12 — carry-over closure + trust repair (must-include):**

1. C1 doc-freshness sweep (`ROADMAP.md`, `HYPOTHESES.md`, `README.md`,
   `AUDIT.md`, `reporting/plans/README.md`) — before D14.
2. Codex F-FS-02 carry-over register: every v0.1.11 deferral named with
   disposition (W-Vb, W-N broader gate, W-H2, F-A-04/F-A-05, F-B-04,
   F-C-05, W52/W53/W58 explicit).
3. C3 W-Vb fixture-packaging fix.
4. L1 D13-symmetry contract test.
5. C4 privacy doc updates.
6. Per-existing-plan: W-S, W-U, W-V, W-H2.

**v0.1.13 — second-developer-user onboarding:**

7. A1 rename gate to "trusted first value" with C7 acceptance matrix
   (5 paths × required result).
8. A5 declarative persona expected-actions (W-AK pulled forward from
   v0.1.14).
9. C2 regulated-claim lint (W-LINT) — first implementation.
10. D2 W-29-prep cli.py boundary audit (half-day).
11. Per-existing-plan: W-AA, W-AB, W-AD, W-AE, W-AG.

**v0.1.14 — eval substrate (not judge confidence theatre):**

12. L2 W-DOMAIN-SYNC contract test (~half day).
13. D2 W-29 cli.py mechanical split if W-29-prep cleared (3-4 days,
    1 main + 1 shared + 11 handler-group files <2500 each).
14. A12 judge-adversarial fixtures fold into W-AI (not new W-id).
15. A2 W-AL calibration: schema/report-shape only, defer real
    correlation to v0.5.
16. Per-existing-plan: W-AH, W-AJ.

**v0.2.0 — deterministic weekly review + deterministic claim-block:**

17. W52 weekly review with C10 source-row locators required.
18. C8 evidence-card schema (`recommendation_evidence_card.v1`).
19. C5/D1 W58 deterministic unsupported-claim block (no LLM judge yet).
20. Lift D4 (capabilities-manifest schema freeze) here.

**v0.2.1 — insight ledger + judge shadow mode:**

21. W53 insight ledger.
22. W58 LLM-judge shadow mode (logs only).
23. Memory-poisoning fixtures.

**v0.2.2 — judge blocking after shadow evidence:**

24. W58 blocking mode if shadow evidence supports it.
25. Override/review path.

**v0.3 — MCP planning:**

26. Threat model + provenance import contract (Codex prereqs).
27. *Plan* the MCP server design — read surface, not write surface.

**v0.4 — multi-source ingest + MCP read surface:**

28. Garmin and/or Apple Health adapter (gating feature for non-developer
    reach).
29. MCP read surface ships if v0.3 prereqs landed.
30. L3 strategic plan §6.3 framing edit (cycle proposal — moat
    rephrasing).

**v0.5 — calibration substrate:**

31. A2/W-AL calibration scaffold pulled forward — *with* C9 anti-gaming
    note in `success_framework_v1.md`.
32. Read-only UI decision-checkpoint (per existing plan, *not* moved to
    v0.3).

**Cross-cutting (planning-system):**

33. A9/D3 four-tier cycle-weight classification
    (substantive/hardening/doc-only/hotfix). `RELEASE_PROOF.md` declares
    chosen tier.
34. A10 move 7+ historical docs to `reporting/plans/historical/`.
35. A8 ship-time freshness checklist in AGENTS.md "Release Cycle
    Expectation."
36. Codex Planning §3 consolidate audit-round transcripts to
    `plan_audit_log.md` and `implementation_review_log.md` — **but only
    after ship**, preserving per-round granularity until then (Claude
    §9.2 correctly identified the per-round detail as the artifact of
    D14; Codex's consolidation idea works *post-ship* as compression).

---

## 7. Round-1 recommendations definitively rejected

These appeared in Claude's round 1 (and round 2 corrected them); Codex
did not propose them either:

- ~~`hai init --demo` as documented first command~~ — inverts
  refusal-IS-the-demo posture.
- ~~Read-only UI to v0.3~~ — inverts H4.
- ~~Reframe H5 as user-preference claim~~ — fights straw-man H5.
- ~~Consolidate per-cycle audit transcripts pre-ship~~ — per-round
  granularity is the artifact of D14. (See action #36 above for
  the post-ship variant that Codex proposed and is correct.)

---

## 8. Limitations of this reconciliation

- **Codex read 4 root planning docs Claude did not read** (`HYPOTHESES.md`,
  `AUDIT.md`, `ROADMAP.md`, `reporting/docs/privacy.md`, `reporting/docs/demo_flow.md`).
  Codex's findings against those files are taken at face value here;
  spot-verified: F-FS-10 stale instances confirmed on disk 2026-04-29.
- **Claude read code Codex did not (deeply)** — D13 consumer-site
  asymmetry, 8-registry enumeration tables, skill-overlay invariant,
  Phase B write-surface guard. Codex's Addendum II and III treat the
  code as well-engineered without surfacing these specific concerns.
- **Both reports failed to spawn one or more research agents** at peak.
  Claude's round 2: 4 of 8 agents failed. Codex: documented similar
  research-pass scoping. Both reports are best-effort, not exhaustive.
- **Some recommendations cross AGENTS.md settled decisions** (D4 lift,
  W-29 split timing, §6.3 framing edit, MCP exposure). Per AGENTS.md
  these require cycle proposals before action. The action list above
  *names* them but does not pre-empt the cycle process.
- **Neither report independently verified** PHIA-paper specifics (Claude:
  failed agent; Codex: F-FS-07 self-flags this), so action A4 should
  *re-read PHIA before* the next strategic plan rev rather than copying
  either report's wording.
- This reconciliation is itself a synthesis with no independent
  research pass — it adjudicates between two reports rather than
  generating new evidence.

---

## 9. Bottom line

The strategic foundation is sound. The substantive deltas are ten
specific items (§4 C1-C10) that Codex caught in addition to the
twelve agreed (§2 A1-A12), six items (§5 L1-L6) that Claude caught,
and four genuine disagreements (§3 D1-D4) that need maintainer
adjudication. The merged action list (§6) is the artifact to drive the
v0.1.12 PLAN.md and the forward roadmap.

**The single most important decision:** D1 (v0.2.0 split shape).
The recommended synthesis — three releases, with W52 deterministic-
gated from v0.2.0 — preserves the design coupling Claude flagged while
accepting Codex's evidence-of-staging argument for the LLM judge.

**The cheapest high-value action:** the v0.1.12 doc-freshness sweep
(action #1, C1). Verified-stale public docs are explicitly part of how
agents (and second users) read this project. Fixing them is half a
day and removes a real trust-and-onboarding hazard.
