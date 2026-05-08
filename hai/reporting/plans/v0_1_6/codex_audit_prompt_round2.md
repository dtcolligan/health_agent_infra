# Codex Audit — Round 2

> **Why round 2.** Round 1 (`codex_audit_response.md`) was conducted
> against the stale `main` branch in a different working tree
> (`/Users/domcolligan/Documents/health_agent_infra/`). The actual
> current branch — `v0.1.4-release` — is **15 commits ahead of `main`**
> and includes the entire v0.1.4 + v0.1.5 release work. Several
> round-1 findings turned out to be already-fixed; others remain real;
> the maintainer's internal cross-validation found additional issues
> Codex never saw because of the branch divergence. This round is the
> reconciliation pass.

---

## Step 0 — Confirm you're in the right tree

Before you do anything else, verify:

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: v0.1.4-release
git log --oneline -1
# expect: ff77aff v0.1.5: sync release QA + handoff docs to v0.1.5 reality
```

If any of those don't match, **stop and surface the discrepancy** —
do not audit the wrong tree. The previous round did exactly that and
half the findings ended up stale. The other working tree at
`/Users/domcolligan/Documents/health_agent_infra/` is on `main` and
~15 commits behind; ignore it.

## Step 1 — Read every prior artifact in this directory

There are four documents in `reporting/plans/v0_1_6/`. Read all of
them before forming opinions:

1. **`codex_audit_prompt.md`** — the original audit brief (round 1).
   Same project context, same scope structure. Read for orientation.
2. **`PLAN.md`** — the maintainer's draft v0.1.6 plan. 9 workstreams
   (W1–W9), drawn from the 2026-04-25 end-to-end user session.
   Treat as draft, not ground truth.
3. **`codex_audit_response.md`** — your round-1 output. **Note: it
   was conducted on the wrong branch.** The maintainer cross-
   validated each finding against `v0.1.4-release` and recorded
   which ones survived; you'll want to re-confirm those judgments
   on the current branch.
4. **`internal_audit_response.md`** — the maintainer's own audit
   response, on `v0.1.4-release`, validating round-1 + adding
   new findings. This is the document round 2 most critically
   needs to react to.

You do not have a separate brief from the maintainer this round.
Your job is to **react to `internal_audit_response.md`** with the
same rigour you applied in round 1 — confirm, refute, expand.

## Project context (recap; same as round 1)

`health-agent-infra` (CLI: `hai`) is a **governed local agent runtime
for personal health data**. A Claude Code agent reads the user's
Garmin / intervals.icu data, emits per-domain proposals bounded by
codified rules, and commits auditable recommendations the user
reviews the next day. Everything stays on-device in a local SQLite
file.

Architectural invariant — code-vs-skill boundary:

- **Python (code-owned)** does the mechanical decisions:
  classification bands, R-rules / X-rules, transactional commits,
  projector logic, contract validation. No prose.
- **Markdown skills (judgment-owned)** do the rationale, uncertainty
  narration, and per-domain action selection inside a bounded enum.
  No arithmetic, no state mutation.
- **Three determinism boundaries** the runtime is documented as
  refusing at: `hai propose` (validates DomainProposal),
  `hai synthesize` (transactional plan commit), `hai review record`
  (typed outcome). The maintainer's audit found that only the first
  is fully invariant-coded; the other two have real gaps.

Six domains in v1: recovery · running · sleep · stress · strength ·
nutrition. Nutrition is macros-only by design (see
`reporting/docs/non_goals.md`).

Current version: v0.1.5 just released. v0.1.6 is the upcoming release
this audit informs.

## Empirical session findings (recap; from `PLAN.md`)

A maintainer used the agent live for a full day on 2026-04-25 (in
user mode, not builder mode). Eight items came out the other side:

1. `hai state reproject` crashes with `sqlite3.IntegrityError:
   FOREIGN KEY constraint failed`.
2. `hai intake gaps` returns misleading `gap_count: 0` without
   `--evidence-json`.
3. `hai daily` doesn't complete the loop on its own.
4. Schema drift between intent-router skill docs and `hai review
   record` CLI.
5. Garmin live pull is unreliable (429s); intervals.icu is the
   maintainer's declared supported source.
6. `hai intake nutrition` is a daily total, not per-meal, not
   idempotent.
7. Every `hai intake *` requires `--base-dir`.
8. `planned_session_type` vocabulary is undocumented.

## Your scope this round

Three explicit jobs:

### Job A — Validate the maintainer's cross-validation

`internal_audit_response.md` claims that on `v0.1.4-release`:

- B1 (`hai daily` partial-domain plans) is **CONFIRMED** at
  `cli.py:3496` — `gate_ok = bool(proposals)` rather than checking
  `not missing_expected`.
- B2 (JSON crash bugs across `cmd_propose` / `cmd_writeback` /
  `cmd_review_record` / `cmd_review_schedule` and `main()` having
  no exception guard) is **CONFIRMED** at `cli.py:914, 1658, 1688,
  5655-5657`.
- B3 (truth-fork: JSONL keeps `"definitely"`, SQLite coerces to `1`)
  is **CONFIRMED** at `cli.py:1787` + `core/state/projectors/_shared.py:20-27`.
- B4 (`--bundle-only` bypasses no-proposals gate) is **CONFIRMED**
  at `cli.py:1107-1123`.
- B5 (reproject FK crash) is **CONFIRMED** — reproduced in the
  session at `core/state/projector.py:1258`.
- B6 (gaps misleading zero) is **CONFIRMED**.
- B7 (intent-router skill drift on `hai review record`) is
  **CONFIRMED**.
- Two round-1 findings are **STALE — already fixed in v0.1.4**:
  recovery skill on legacy writeback path (now allows `hai propose`
  and emits `RecoveryProposal`); `hai classify`/`hai policy`
  hard-limited to recovery (now accepts all 6 domains per
  `cli.py:4644`).

Re-validate each of those claims at the cited file:lines. Status
options: **REPRODUCED**, **NOT REPRODUCED — claim is wrong**,
**PARTIALLY REPRODUCED — narrower than claimed**, **FIXED SINCE
INTERNAL AUDIT** (someone else committed in between). Cite the
file:line you actually looked at.

### Job B — Validate the maintainer's new findings

`internal_audit_response.md` adds findings round 1 missed because
of the branch divergence:

- **Cold-start asymmetry** — `cold_start_relaxation` is implemented
  in `domains/{running,strength,stress}/policy.py` only. Recovery,
  sleep, nutrition do not have an equivalent rule. Days 1–14
  produce inconsistent behaviour across the 6 domains.
- **Date-flag naming inconsistency** — `--as-of` (11 commands),
  `--for-date` (1: `hai explain`), `--date` (1: `hai pull`).
- **Hardcoded threshold duplication** — 14-day cold-start cutoff
  lives in 3 separate files; 28-day chronic-load window lives in 2.
  Not factored to config.
- **Test coverage gaps** — every P0 bug above has zero direct
  regression test. B1 has a test that LOCKS the broken behaviour
  as correct.

Re-validate each. Confirm or refute with file:line evidence.

### Job C — Find what BOTH audits missed

Walk the codebase fresh on `v0.1.4-release`. The maintainer's
`internal_audit_response.md` covered the structural surface — the
boundary integrity, skill-vs-code drift, cold-start correctness,
reproject correctness, migration safety, test coverage. Find
issues that didn't show up in either round 1 (wrong branch) or
internal audit (maintainer was looking at known-bug areas).

Specifically look for:

- **Race conditions / non-determinism** in projectors, snapshots,
  synthesis. The `BEGIN EXCLUSIVE` is the synchronisation surface;
  is it consistent across writers?
- **Privacy / data-leak surfaces.** The repo claims local-first.
  Where does data leave the machine? Vendor calls (Garmin,
  intervals.icu); explain/today JSON outputs; logs; tracebacks.
- **Schema-version compatibility.** Live DB is at
  `schema_version = 18`. What happens when a user with a v17 DB
  upgrades? Are migrations forward-only safe? Backward-incompatible?
- **Skill `allowed-tools` correctness.** Each skill restricts what
  CLI it can call. Are those restrictions actually consistent with
  what the skill body tells the agent to do? Round 1 caught the
  recovery-skill case (which is now fixed); other skills may have
  similar mismatches.
- **What the maintainer's plan over-promises.** The PLAN.md
  acceptance criterion says "a fresh user, running through Install
  → Reading your plan → Recording your day, hits no surprises."
  Is that achievable in v0.1.6 scope, or does it require work the
  plan hasn't named?
- **CI / release machinery.** Is there a packaging test, a
  versioning gate, a changelog discipline? The previous round's
  packaging/version mismatch was a stale-artifact issue, but the
  underlying question — "does the release process catch this kind
  of drift?" — stands.

### Non-goals (explicit)

- Re-validating the round-1 findings the maintainer's audit already
  marked stale (recovery legacy path, classify/policy
  hard-limiting). They're fixed; cite once and move on.
- Cosmetic refactoring suggestions.
- v0.2 redesign work — anything larger than ~2–3 weeks of single-
  maintainer effort goes in "Roadmap recommendations" as a named
  candidate, not as a P0/P1.
- Re-derivation of the 9 PLAN.md workstreams — engage with them as
  drafted; don't re-write them from scratch.

## Output format

Save your response to:

**`reporting/plans/v0_1_6/codex_audit_response_round2.md`**

Structure (sections in this order; "No findings" is acceptable for
any section that genuinely has none — do not pad):

```markdown
# Codex Audit — Round 2 Response

## Step 0 confirmation
<state which branch + commit you audited; explicitly confirm path>

## Validation of internal audit's reproductions (Job A)

### B1. hai daily partial-domain gate
Status: REPRODUCED / NOT REPRODUCED / PARTIALLY REPRODUCED / FIXED SINCE
Evidence: <file:line you actually looked at>
Disagreement (if any): <what the maintainer got wrong, if anything>

### B2. JSON crash bugs in cmd_propose / cmd_writeback / cmd_review_record / cmd_review_schedule + missing main() guard
### B3. Truth-fork in cmd_review_record
### B4. --bundle-only bypasses no-proposals gate
### B5. hai state reproject FK orphan crash
### B6. hai intake gaps misleading zero without --evidence-json
### B7. intent-router schema drift on hai review record
### Stale findings (recovery legacy path; classify/policy hard-limiting)
<one line confirming each is actually fixed at file:line>

## Validation of internal audit's new findings (Job B)

### Cold-start asymmetry across 6 domains
### Date-flag naming inconsistency (--as-of vs --for-date vs --date)
### Threshold constant duplication
### Test coverage gaps for the P0 bugs

## What both audits missed (Job C)
For each: severity, evidence (file:line), recommended fix, effort,
risk if unfixed. Same shape as round-1 bugs.

## Reaction to PLAN.md workstreams
For each of W1–W9 (and the proposed W10–W14 from the internal audit):
- Agree / disagree with the workstream's framing
- Agree / disagree with the proposed sequencing
- Anything materially missing

## Reaction to internal_audit_response.md
The maintainer's own audit made specific judgment calls (e.g.
"demote W1 to P1 because workaround exists," "B1 is RELEASE_BLOCKER
because the architecture story depends on it"). React to those
calls explicitly: agree, disagree-with-reason, or "depends on X."

## Final severity-ranked punch list for v0.1.6
A flat numbered list reflecting BOTH audits' findings, sorted by
priority. Each line: `[P0] <one-sentence problem> — <one-sentence
fix> — <S/M/L>`.

If the maintainer's punch list is broadly right, say so and surface
only the deltas. If there's a structural disagreement (e.g. you
think B1 is P1 not P0), say so directly.

## Things both audits got wrong
Be direct. The maintainer prefers terse, evidence-cited prose over
hedged generalities.

## Things both audits didn't ask about but should have
Same.
```

## Tone

- Direct. Cite `file:line` for every claim.
- "Uncertain" is a fine word; "DEFERRED — DIDN'T INVESTIGATE" is
  fine if you can't run the test suite or reproduce a network thing.
  Don't bury uncertainty in soft language.
- No marketing copy. No hedging theatre.
- The maintainer is going to commit P0 fixes off the back of this.
  Be wrong out loud rather than vaguely defensible.

## Scope guardrail

This audit informs v0.1.6, not v0.2. Recommendations should fit
within ~2–3 weeks of one maintainer's work. Anything larger goes in
a separate "Roadmap recommendations" section as a named candidate.

## Closing — what changes after this

The maintainer will:

1. Fold your findings into `PLAN.md` (the same way the internal
   audit reconciliation table does at the bottom of
   `internal_audit_response.md`).
2. Sequence the v0.1.6 workstreams off the merged punch list.
3. Ship; track in the implementation log section of `PLAN.md`.

Your output is the second authoritative read on the v0.1.6 surface.
After this round, the plan moves to execution.
