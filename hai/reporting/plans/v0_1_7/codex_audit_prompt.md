# Codex Audit — v0.1.7 Plan Review

> **Why this round.** v0.1.6 is tag-ready (your round-3 must-fix
> items shipped). v0.1.7 starts the next iteration. The maintainer
> has drafted a report (`REPORT.md`) + plan (`PLAN.md`) and wants
> your review before implementation begins. This is the same
> rhythm as v0.1.6: maintainer drafts → Codex audits → revised plan
> → implementation.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: v0.1.4-release
git log --oneline -1
# expect: ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality
ls reporting/plans/v0_1_7/
# expect: REPORT.md, PLAN.md, codex_audit_prompt.md
```

If any don't match, **stop and surface the discrepancy**. Ignore
`/Users/domcolligan/Documents/health_agent_infra/`.

## Step 1 — Read the artifacts in order

1. **`reporting/plans/v0_1_7/REPORT.md`** — the maintainer's read of
   where the project actually is post-v0.1.6: strong parts, real
   gaps, success criteria inferred from observed behaviour, the
   thesis behind v0.1.7's investments.
2. **`reporting/plans/v0_1_7/PLAN.md`** — the workstream catalogue
   (W21–W31), proposed sequencing, acceptance criteria.
3. **`reporting/plans/v0_1_6/PLAN.md`** § 7 — the consolidated
   v0.1.6 plan + § 6 implementation log. Use as background for
   what just shipped.
4. **`reporting/plans/v0_1_6/codex_implementation_review_response.md`** —
   your round-3 review. Specifically the "Deferred items —
   agree or disagree" section (W6, W8, W14 deeper, W16) — v0.1.7
   PLAN explicitly addresses W14 deeper (W24) and W16 (W25); it
   leaves W6 + W8 deferred again. Push back if you think those
   should ship in v0.1.7.
5. **`reporting/docs/non_goals.md`** — anchors the explicit
   v0.1.7 non-goals.
6. **`reporting/plans/post_v0_1_roadmap.md`** — pre-existing
   roadmap; sanity-check that v0.1.7 doesn't contradict named
   future commitments.

## Project context recap (same as prior rounds)

`health-agent-infra` (CLI: `hai`) — local-first governed agent
runtime for personal health data. Three determinism boundaries
(`hai propose`, `hai synthesize`, `hai review record`). Six domains
in v1: recovery, running, sleep, stress, strength, nutrition.
Code-vs-skill boundary: code owns mechanical decisions; skills own
rationale + bounded action selection. v0.1.6 is tag-ready as of
this audit.

## Your scope this round

Three explicit jobs:

### Job A — Validate the maintainer's read of the project

`REPORT.md` sections 1–3 establish what's strong, what's weak, and
what success criteria look like. For each:

- **§1 "Where the project is right now"**: are the "strong parts"
  actually that strong on the v0.1.4-release branch? Are the "real
  gaps" enumerated correctly? Anything missing or overstated?
- **§2 "Maintainer's success criteria"**: is the inferred read
  reasonable, or is the maintainer flattering the project?
- **§3 "Where v0.1.7 should aim"**: agree with the A/B/C investment
  framing? Push back on the A-leads / B-follows / C-lower
  prioritisation if you'd rank differently.

### Job B — Audit the workstream plan

For each of W21–W31:

- **Validate the framing.** Does the problem statement match what
  the codebase actually shows? Cite file:line for any disagreement.
- **Validate the fix.** Will the proposed fix actually deliver what
  the acceptance criterion claims? Are there better approaches?
- **Validate the effort estimate** (implicit in the sizing). Mark
  any workstream you think is materially S/M/L mis-sized.
- **Find what's missing.** Workstreams the plan should have
  included but doesn't.
- **Find what should be cut.** Workstreams the plan includes that
  aren't worth the v0.1.7 budget — defer or drop.

Specific things to weigh in on:

- **W21 (`hai daily --auto`)** is the flagship. Is the
  `next_actions[]` shape sufficient? Will the agent actually be
  able to consume it without falling back to intent-router prose?
  Are there cases (defer paths, supersede chains, mid-day
  re-planning) the manifest design doesn't cover?
- **W22 (PyPI release)** is the precondition for distribution.
  Anything about the build / packaging / CI pipeline that needs
  attention before a public release that the plan doesn't list?
- **W24 (cold-start matrix)** asks for a per-domain decision. Do
  you think recovery/sleep/nutrition SHOULD have
  `cold_start_relaxation` rules, or is the asymmetry correct?
  Cite the per-domain semantics where you can.
- **W27 (property-based projector tests)** — is `hypothesis` the
  right dep, or is a hand-rolled approach better given the project
  doesn't currently depend on it?
- **W29 (cli.py split)** is the biggest refactor. Worth doing in
  v0.1.7 or defer? If defer, what's the cost of waiting another
  release?

### Job C — Propose the revised plan

Based on Jobs A+B:

- **Reconciliation table** — for each of W21–W31: agree as-is /
  agree-with-changes / cut / defer to v0.1.8. New workstreams you
  add get fresh ids (W32+).
- **Re-sequenced punch list** for v0.1.7 in priority order.
- **Ship verdict criteria** — what would you need to see in the
  v0.1.7 implementation review to vote SHIP?

### Non-goals

- Don't re-audit v0.1.6's shipped work; that's done.
- Don't propose v0.2 redesign work — anything larger than ~3 weeks
  of one maintainer's effort goes in "deferred to v0.1.8+" as a
  named candidate.
- Don't argue for cosmetic changes.

## Output format

Save your response to:

**`reporting/plans/v0_1_7/codex_audit_response.md`**

Structure:

```markdown
# Codex Audit — v0.1.7 Plan Response

## Step 0 confirmation
<branch + commit + files seen>

## Validation of maintainer's read (Job A)

### §1 Strong parts
For each "strong part" listed in REPORT.md §1: VERIFIED /
OVERSTATED / DEFERRED — DIDN'T_INVESTIGATE, with evidence.

### §1 Real gaps
For each "real gap" A–K listed: CONFIRMED / NOT_REPRODUCED /
PARTIALLY_CONFIRMED / DISAGREE. Add gaps you think the report
missed.

### §2 Success criteria
Agree / disagree with the inferred success criteria. Push back
if the maintainer is flattering the project.

### §3 Investment framing
Agree / disagree / re-rank A/B/C.

## Audit of the workstream plan (Job B)

### W21–W31, one section each
For each: framing assessment, fix assessment, effort sizing
review, anything missing, anything to cut.

### Workstreams the plan missed
New workstreams you'd add (W32+).

### Workstreams the plan should cut
Items that aren't worth v0.1.7's budget.

## Revised plan (Job C)

### Reconciliation table
| WS | Maintainer's call | Codex's call | Reason |

### Re-sequenced v0.1.7 punch list
Flat priority-ordered list.

### Ship verdict criteria
What v0.1.7's implementation review would need to vote SHIP.
```

## Tone

Same as prior rounds: direct, file:line cited, "uncertain" or
"DEFERRED — DIDN'T INVESTIGATE" when you can't verify, no hedging.
Maintainer commits + iterates from your output.

## Closing

After this round, the maintainer integrates your findings into
`PLAN.md`, then begins implementation. The cycle continues.
