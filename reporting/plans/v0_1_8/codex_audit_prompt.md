# Codex Audit — v0.1.8 Plan Review

> **Why this round.** v0.1.7 is materially complete (your r3 must-fix
> items shipped + 11 workstreams against the consolidated punch
> list). v0.1.8 begins the next cycle. The maintainer drafted a
> report (`REPORT.md`) + plan (`PLAN.md`) and wants your review
> before implementation begins.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: v0.1.4-release  (continuation; v0.1.7 ships from here)
git log --oneline -1
# expect: ff77aff (or later, if v0.1.7 has been committed)
ls reporting/plans/v0_1_8/
# expect: REPORT.md, PLAN.md, codex_audit_prompt.md
```

If any don't match, **stop and surface the discrepancy**. Ignore
`/Users/domcolligan/Documents/health_agent_infra/`.

## Step 1 — Read the artifacts

In order:

1. **`reporting/plans/v0_1_8/REPORT.md`** — the maintainer's read
   of where the project actually is post-v0.1.7: what works, what
   v0.1.7 didn't close, and the structural gaps (A–I) the
   maintainer thinks v0.1.8 should address.
2. **`reporting/plans/v0_1_8/PLAN.md`** — workstream catalogue
   (W37–W47), proposed sequencing, acceptance criteria.
3. **`reporting/plans/v0_1_7/PLAN.md`** § 6 — implementation log
   for what just shipped in v0.1.7.
4. **`reporting/plans/v0_1_7/codex_audit_response.md`** — your
   v0.1.7 audit. Particularly the deferred-with-changes items
   (W27, W28, W29, W30) — v0.1.8 PLAN explicitly addresses W28
   (W46) and W27 (W45); leaves W29+W30 deferred again. Push back
   if you think those should ship in v0.1.8.
5. **`reporting/plans/v0_1_7/codex_implementation_review_response.md`**
   — your r3 implementation review of v0.1.6 (the must-fix items
   that drove the start of v0.1.7).
6. **`reporting/docs/non_goals.md`** — anchors v0.1.8's explicit
   non-goals.

## Project context recap

`health-agent-infra` (CLI: `hai`) — local-first governed agent
runtime for personal health data. Three determinism boundaries
(`hai propose`, `hai synthesize`, `hai review record`). Six
domains: recovery, running, sleep, stress, strength, nutrition.
v0.1.7 made the agent contract first-class (typed
`next_actions[]` manifest). v0.1.8 wants to close the **outcome
feedback loop** without introducing ML.

## Your scope this round

Three explicit jobs:

### Job A — Validate the maintainer's read of where v0.1.8 should aim

`REPORT.md` § 1 enumerates 9 structural gaps (A–I) and § 2 refines
the success criteria. For each:

- Are the gaps real on the v0.1.7-shipped surface? Cite file:line
  for any disagreement.
- Are the success criteria reasonable, or is the maintainer
  flattering the project / overstating where it is?
- Specifically: gap **A** (no feedback loop from outcomes) is the
  v0.1.8 thesis. Is consuming `review_outcome` rows in per-domain
  skills (W37) the right shape, or should it land elsewhere
  (e.g. inside the policy gate, inside synthesis)?

### Job B — Audit the workstream plan

For each of W37–W47:

- **Validate the framing.** Does the problem statement match the
  codebase? Cite file:line for any disagreement.
- **Validate the fix.** Will the proposed fix deliver what the
  acceptance criterion claims? Are there better approaches?
- **Validate the effort.** Mark anything materially mis-sized.
- **Find what's missing.** Workstreams the plan should have
  included.
- **Find what should be cut.** Workstreams that aren't worth the
  v0.1.8 budget.

Specific questions:

- **W37 (outcome consumption)** is the flagship. Is the
  "uncertainty token, no action mutation" boundary the right
  contract, or should outcomes also influence policy decisions
  (e.g. cap confidence)? Per `non_goals.md`, "review outcomes do
  not yet feed confidence calibration" — does W37's uncertainty-
  token-only design respect that, or does it cross a line?
- **W39 (per-user thresholds)** — TOML overlay is the simplest
  implementation. But should v0.1.8 also surface a `hai config
  override --threshold <key> --value <v>` CLI to make the override
  discoverable, or is that v0.1.9 scope?
- **W43 (`hai daily --explain`)** — is per-stage explanation the
  right granularity, or should this be `hai explain --for-stage
  <name>` (parallel to the existing `hai explain
  --for-recommendation`)?
- **W41 / W42 (skill-harness)** — Codex r2 said "the blocker
  doc's bounded next steps are recovery live transcript capture
  and maybe one second domain." W41 picks recovery + strength.
  Is that the right second domain, or would running be higher
  leverage given v0.1.7's W21 manifest already exercises running
  in the fixture-day test?
- **W44 (PyPI publish)** is operator-only. Is there CI / release
  automation that should land in v0.1.8 to make this less manual
  (e.g. a tagged-release GitHub Action that runs `twine upload`)?

### Job C — Propose the revised plan

- Reconciliation table: for each of W37–W47, agree-as-is /
  agree-with-changes / cut / defer. New workstreams get fresh ids
  (W48+).
- Re-sequenced punch list for v0.1.8.
- Ship verdict criteria: what would the v0.1.8 implementation
  review need to see for SHIP?

### Non-goals

- Don't re-audit v0.1.6 / v0.1.7 shipped work.
- Don't propose v0.2 redesign.
- Don't suggest cosmetic refactors.

## Output format

Save your response to:

**`reporting/plans/v0_1_8/codex_audit_response.md`**

Structure:

```markdown
# Codex Audit — v0.1.8 Plan Response

## Step 0 confirmation
<branch + commit + files seen>

## Validation of the maintainer's read (Job A)

### §1 Structural gaps A–I
For each: CONFIRMED / NOT_REPRODUCED / PARTIALLY_CONFIRMED /
DISAGREE, with file:line evidence. Add gaps the report missed.

### §2 Refined success criteria
Agree / disagree / push back.

### §3 Investment framing (X / Y / Z / W)
Agree / disagree / re-rank.

## Audit of the workstream plan (Job B)

### W37–W47, one section each
For each: framing, fix, effort, anything missing, anything to cut.

### Workstreams the plan missed
New workstreams (W48+) you'd add.

### Workstreams the plan should cut
Items not worth v0.1.8's budget.

## Revised plan (Job C)

### Reconciliation table
| WS | Maintainer's call | Codex's call | Reason |

### Re-sequenced v0.1.8 punch list
Flat priority-ordered list.

### Ship verdict criteria
What v0.1.8's implementation review would need to vote SHIP.
```

## Tone

Same as prior rounds: direct, file:line cited, "uncertain" or
"DEFERRED — DIDN'T INVESTIGATE" when you can't verify, no
hedging. The maintainer commits + iterates from your output.

## Closing

After this round, the maintainer integrates your findings, then
implements. The cycle continues toward the project's success
criteria.
