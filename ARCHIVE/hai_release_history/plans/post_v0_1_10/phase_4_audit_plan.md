# Phase 4 Codex Audit Plan — Strategic + Tactical Planning Tree

> **Status.** Plan authored 2026-04-28. Not yet executed. Phase 4
> work (the strategic + tactical planning files) is on `main` as of
> v0.1.10 commit; this doc scaffolds the Codex audit round that
> validates that planning work as a coherent set.
>
> **When to run.** When Dom is ready to harden the planning tree
> against external review. Not blocking the demo or v0.1.11 — those
> can run in parallel.

---

## 1. What's in scope

The six Phase 4 documents authored alongside v0.1.10:

- `reporting/plans/strategic_plan_v1.md` (722 lines) — 12-24 month
  vision, category claim, H1-H5 hypotheses, settled decisions
  D1-D12, scope-expansion exploration, five waves to v1.0.
- `reporting/plans/tactical_plan_v0_1_x.md` (545 lines) — release
  timeline v0.1.11 → v0.2.0, per-release workstreams, release
  pattern playbook, risk-driven scope cuts.
- `reporting/plans/eval_strategy/v1.md` (537 lines) — five eval
  classes, current coverage, ground-truth methodology, LLM-as-judge
  approach, calibration eval shape.
- `reporting/plans/success_framework_v1.md` (538 lines) —
  north-star, Tier 1-3 metrics, anti-metrics, targets per wave.
- `reporting/plans/risks_and_open_questions.md` (754 lines) — 19
  risks + 10 open questions, anti-risks, register table.
- `reporting/plans/README.md` (140 lines) — reading-order index.

Plus the AGENTS.md / REPO_MAP.md / multi_release_roadmap.md edits
that made room for Phase 4 (SUPERSEDED banners, new pointers, D10/
D11/D12 settled decisions).

## 2. What's explicitly out of scope

- **v0.1.10 ship artifacts.** Already audited across three rounds;
  shipped to PyPI. The Phase 4 audit doesn't reopen v0.1.10
  decisions.
- **v0.1.11 PLAN / BACKLOG.** They contain v0.1.10 deferred items;
  the Phase 4 audit reviews them only as receivers of those items,
  not as standalone plans. The v0.1.11 cycle will get its own
  audit round.
- **Code.** No code changes are in Phase 4 scope — this is a
  documentation + strategy audit only.

## 3. The audit questions

### Q1 — Strategic plan coherence

- Are the five hypotheses (H1-H5) genuinely falsifiable? Each one
  should have a "if we observe X we abandon this hypothesis"
  clause.
- Does the category claim (what hai *is* and is *not*) match the
  scope-expansion exploration? Or do the speculative scope items
  contradict the category boundaries?
- Are the settled decisions D1-D12 internally consistent? E.g.,
  "no autonomous plan generation" + "scope-expansion to weekly
  review" — is the boundary preserved?
- Do the five waves to v1.0 make geometric sense (each wave moves
  the project forward in a way the previous wave couldn't)?

### Q2 — Tactical plan execution feasibility

- Per release v0.1.11 → v0.2.0, do the workstreams add up to a
  coherent release theme?
- Are the dependencies between cycles right (e.g., does v0.1.11's
  audit-chain work actually unlock v0.1.12's planned work)?
- Does the release pattern playbook (Phase 0 pre-PLAN through
  Phase 5 post-ship retro) match what v0.1.10 actually did?
- Risk-driven scope cuts — are they specific enough that future
  Dom can apply them, or are they vague aspirations?

### Q3 — Eval strategy load-bearing-ness

- Five eval classes (unit, scenario, persona, outcome/calibration,
  adversarial) — is each one actually distinct, or do some
  collapse together in practice?
- Current coverage snapshot (2169 unit tests, 28 scenarios, 8
  personas) — is the gap analysis honest?
- LLM-as-judge approach (Prometheus-2-7B local, 2-shot
  negotiation) — is this load-bearing for the success-framework
  metrics, or aspirational?
- Calibration eval shape — does it match what the audit chain can
  actually produce?

### Q4 — Success framework anti-metric discipline

- North-star sentence — does it have falsifiable claims, or is it
  marketing prose?
- Tier 1 metrics — daily-use frequency, audit-chain
  reconcilability, persona matrix pass rate, confidence
  calibration, defer rate per domain. Each one — is it measurable
  today, measurable in the next release, or never measurable?
- Anti-metrics (skill arithmetic, clinical claims, direct DB
  writes, confidence inflation, doc rot, audit-cycle compression)
  — are they specific enough to detect violations? Or too vague
  to be load-bearing?
- Targets per wave — too aggressive, too soft, or right-sized?

### Q5 — Risk register completeness

- 19 risks — what's missing? Likely gaps to probe:
  - **Maintainer single-point-of-failure** — what happens if Dom
    pauses for 6 months?
  - **Anthropic / OpenAI API discontinuity** — model deprecation,
    pricing changes, rate-limit shifts.
  - **Privacy / DPA risk** if hai is ever deployed beyond
    single-user local.
  - **Health-claim drift** — could the codebase accumulate
    diagnosis-shaped language without anyone noticing?
- 10 open questions — are they actually open, or has Dom already
  decided and just hasn't documented?
- Risk format (trigger/impact/likelihood/mitigation/trip-wire) —
  does each risk have all five fields populated, or are some thin?

### Q6 — Cross-document consistency

- Does AGENTS.md "Settled Decisions" match the strategic plan's
  settled decisions section?
- Does REPO_MAP.md classify the new docs honestly?
- Are cross-references between docs accurate? (E.g., when
  strategic_plan_v1.md says "see eval_strategy/v1.md § 4," does
  that section exist?)
- Does the planning README index disambiguate which doc to read
  for which intent?

## 4. The audit prompt template

Drafted skeleton (Codex round 1):

```
You are reviewing the Phase 4 strategic + tactical planning tree
for the health_agent_infra project. The planning files landed on
main alongside v0.1.10 (already shipped). Your job is to identify
where the planning is internally inconsistent, where claims aren't
falsifiable, where scope decisions contradict each other, or where
the docs don't match the codebase reality.

Out of scope: v0.1.10 implementation review (done across 3 prior
rounds), code changes, v0.1.11 PLAN execution.

Read in order:
1. AGENTS.md (settled decisions D1-D12)
2. REPO_MAP.md
3. reporting/plans/README.md (planning-tree index)
4. reporting/plans/strategic_plan_v1.md
5. reporting/plans/tactical_plan_v0_1_x.md
6. reporting/plans/eval_strategy/v1.md
7. reporting/plans/success_framework_v1.md
8. reporting/plans/risks_and_open_questions.md

Address Q1-Q6 (see this file's § 3). Output to
reporting/plans/post_v0_1_10/codex_phase_4_audit_response.md.

Verdict scale: PLANS_COHERENT | PLANS_COHERENT_WITH_REVISIONS |
PLANS_INCOHERENT (name what to revise).
```

Refine the prompt before sending — the Q3 (eval) section in
particular is technical and needs careful framing.

## 5. Cycle pattern

Same as v0.1.8 / v0.1.9 / v0.1.10 audits, scaled down because this
is docs-only:

1. **Round 1.** Codex reviews against Q1-Q6, produces findings.
2. **Maintainer response.** Dom + Claude triage findings:
   accept-with-revision, document-and-defer, disagree-with-reason.
3. **Round 2.** Codex reviews the revisions.
4. **SHIP / SHIP_WITH_NOTES** when verdict is positive.

Estimated duration: 1-2 sessions. Smaller than a code audit
because there's no implementation to verify, no test surface to
re-run.

## 6. Acceptance gate (Phase 4 docs are "audited" when…)

- [ ] All six Phase 4 docs reviewed by Codex against Q1-Q6.
- [ ] Each finding either addressed in revision or explicitly
      deferred with reason.
- [ ] Cross-references verified (no broken links between docs).
- [ ] Final Codex verdict: PLANS_COHERENT or
      PLANS_COHERENT_WITH_REVISIONS.
- [ ] `reporting/plans/post_v0_1_10/codex_phase_4_audit_response.md`
      committed alongside any revisions.

## 7. Why this is post-v0.1.10, not pre

The planning tree was authored under one continuous session. It
needs an external read to catch consistency drift, blind spots,
and category-claim weakness. But it doesn't gate v0.1.10 (which
shipped the runtime, not the plans) or the demo (which uses
v0.1.10's runtime).

Run when: Dom has bandwidth and wants to harden the plans before
investing further cycles in them. Not urgent.
