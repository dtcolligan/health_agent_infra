# Codex External Audit — v0.1.10 Pre-PLAN Bug Hunt

> **Why this round.** v0.1.10 is a pre-PLAN bug hunt, not a feature
> cycle. The maintainer is investing 3-5 days in a structured audit
> *before* opening a formal PLAN.md. Internal sweep + persona
> dogfood matrix have completed and surfaced ~25-30 candidate
> findings. **Your job is to find what the internal sweep missed.**
>
> This is parallel to Claude's internal sweep, not sequential —
> your findings merge into the same `audit_findings.md` file.
> Independent reads catch different things.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -3
# expect: most recent should mention v0.1.9 ship + this v0.1.10 prep work
ls reporting/plans/v0_1_10/
# expect: PRE_AUDIT_PLAN.md, audit_findings.md (in progress), codex_audit_prompt.md (this file)
ls verification/dogfood/
# expect: README.md, runner.py, synthetic_skill.py, personas/, fixtures/
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md`** — the cycle's
   pre-PLAN scope, hunt phases, persona matrix, harness shape, and
   open questions.
2. **`reporting/plans/v0_1_10/audit_findings.md`** — the internal
   sweep's findings so far. **Don't regurgitate these — your goal
   is to find what they missed.**
3. **`AGENTS.md`** — operating contract. Pay special attention to:
   - "Governance Invariants" (W57, three-state audit chain,
     review-summary bool-as-int hardening)
   - "Settled Decisions" (cli.py split deferred, capabilities manifest
     not yet frozen, Garmin Connect not the default live source,
     nutrition v1 macros-only)
   - "Do Not Do" (no skill→runtime imports, no autonomous plan
     generation, no clinical claims)
4. **`reporting/plans/multi_release_roadmap.md`** § 4 v0.1.9 +
   § 4 post-v0.1.9 — what's coming, and what definitionally is
   *not* in v0.1.10's scope ceiling (W52 weekly review, W53
   insight ledger, W58 LLM-judge factuality gate all defer past
   v0.1.10).

---

## Step 2 — The bug-hunt question

> *"Identify correctness, idempotency, and data-flow bugs across
> synthesis, projection, CLI mutation paths, and audit-chain
> integrity. Bonus: find places where the runtime makes assumptions
> that wouldn't hold across the user matrix in
> `verification/dogfood/personas/`. Out of scope: features,
> performance, doc nits, anything in `multi_release_roadmap.md`
> § 4 post-v0.1.10."*

Findings must be specific enough to triage. Each finding should
include:

- **File:line** (one specific location, even if the issue spans
  multiple files — pick the central one).
- **Severity:** crash | validator-reject | action-mismatch |
  band-miscalibration | rationale-incoherence | audit-chain-break |
  correctness | idempotency | type-safety | nit.
- **Blast radius:** which user shapes / which domains affected.
  Reference persona IDs from
  `verification/dogfood/personas/` where applicable.
- **Reproduction:** minimal CLI sequence or test invocation.
- **Triage suggestion:** fix-now | defer-to-v0.2 | won't-fix |
  needs-design-discussion.

---

## Step 3 — Where to look hard

Internal sweep covered:

- ruff (24 findings, most unused imports)
- mypy default (35 errors, 15 files)
- bandit -ll (17 issues, 16 false-positive-shaped B608)
- threshold-consumer audit (≥22 sites)
- `hai explain` audit-chain walk over recent days
- 8-persona dogfood matrix

**It did not cover:**

- **Hypothesis-style property tests.** Are there invariants in
  `core/synthesis.py` or `core/synthesis_policy.py` that a
  property-based test would falsify quickly? E.g., "after
  applying Phase A then Phase B, the action is in the domain's
  valid action set" — does that hold under all inputs?
- **State-machine cracks.** Does `hai target archive` →
  `hai target set` (proposing the same target_type again) →
  `hai target commit` produce a clean state, or can it leave
  duplicate active rows?
- **Migration round-trip.** If a v0.1.9 DB is opened with v0.1.10
  code, does every read path tolerate the older schema? What about
  the reverse — is the migration forward-only as documented?
- **Concurrent same-day mutation race.** If two `hai intake
  nutrition` commands run nearly simultaneously, what happens at
  the supersede step?
- **Skill drift.** Markdown protocols under
  `src/health_agent_infra/skills/` may have specifications that no
  longer match runtime behaviour. Spot-check one or two skills
  against their backing domain code.
- **CLI surface coherence.** Does `hai capabilities --json`
  accurately describe every command? Are mutation classes
  correctly labelled? Are `agent_safe` flags consistent with what
  the implementation actually mutates?
- **Audit-chain integrity at the boundary.** When a plan is
  superseded, does the predecessor's `superseded_by_plan_id`
  always pair with the successor's `supersedes_plan_id`? Is there
  a path where one is set and the other isn't?
- **`hai today` rendering.** What can produce a state-vs-render
  divergence (the F-B-02 finding)? Is it the only case, or are
  there others?

---

## Step 4 — What's already known (don't re-find these)

Internal sweep already documented:

- F-A-01 through F-A-15 in `audit_findings.md` (Phase A: type
  safety, threshold-consumer audit, ruff/mypy findings).
- F-B-01 through F-B-04 in `audit_findings.md` (Phase B: audit
  chain integrity).
- All B1–B7 from the morning-briefing user-facing dogfood
  (project memory).

Anything in those lists, you can ignore — but feel free to add
additional context if you spot a related issue.

---

## Step 5 — Output format

Write your findings to a new file:

```
reporting/plans/v0_1_10/codex_audit_response.md
```

Schema per finding (mirror `audit_findings.md`):

```markdown
### F-CDX-NN. <one-line title>

**Source:** Codex external audit.
**Severity:** ...
**Blast radius:** ...
**File:** path:line
**Description:** ...
**Reproduction:** ...
**Triage:** ...
```

End the response with:

```markdown
## Summary

- Total findings: N
- Crash candidates: N
- Audit-chain integrity: N
- Recommended fix-now scope additions: N
- Recommended defers: N

## What I did NOT find but expected to

- ...
```

That last section matters: an absence of findings in an area where
we expected them is itself a signal — either the area is genuinely
clean, or the audit didn't reach it.

---

## Step 6 — Verdict

End your response with one of:

- **HUNT_COMPLETE** — you reached every area named in Step 3,
  produced findings or explicit "did not find" notes for each.
- **HUNT_PARTIAL** — you ran out of time or scope; name what's
  uncovered.
- **HUNT_BLOCKED** — something prevented the audit; describe.

The maintainer reads your response, merges findings into
`audit_findings.md`, then writes `PLAN.md` based on the
consolidated finding set + triage. The four-round audit cycle
opens after PLAN.md.

---

## Step 7 — Constraints

- **Read-only.** Do not modify `src/health_agent_infra/` or
  `verification/tests/`. Findings are written; fixes are deferred
  to PLAN.md.
- **No new files outside `reporting/plans/v0_1_10/`** unless they
  are obvious test scaffolding.
- **No CHANGELOG.md edits.** v0.1.10 has not opened.
- **No git operations.** The maintainer commits.
- **Honour governance invariants.** Anything that violates W57,
  the three-state audit chain, or no-clinical-claims is itself a
  finding — flag it rather than working around it.

Begin.
