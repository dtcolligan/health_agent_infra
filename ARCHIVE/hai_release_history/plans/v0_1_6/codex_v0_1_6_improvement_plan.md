# Codex v0.1.6 Improvement Plan

## Purpose

This report answers a narrower question than the round-3 ship review:

> How can v0.1.6 become a substantial improvement over v0.1.5 before tag?

The recommendation is to make v0.1.6 an **agent-operable runtime quality
release**, not merely a bug-fix release. That means the release should improve
the user's lived loop, the agent contract, the safety boundary, and the proof
artifacts all at once.

The project definition of success is already explicit: it must work end to end
for the founder, maintain trustworthy inspectable multi-domain state, be better
than generic chat-layer coaching, track outcomes into future tailoring, enforce
safety in code, install for an outside builder, and be legible to outsiders
(`reporting/docs/archive/doctrine/founder_doctrine_2026-04-17.md:114-123`).

v0.1.6 can materially move toward that standard without opening the wrong
surface area.

## Current Baseline

The round-3 review found that the implementation is close but not yet ready to
tag. The current verdict is:

```
SHIP_WITH_FIXES - must-fix before tag: [P0] bump release metadata/contract
version to 0.1.6; [P1] add `hai capabilities --json` alias or remove all
docs/skill references; [P1] fix `hai daily` capabilities output
schema/description for `incomplete`; [P1] update README cheat sheet +
`agent_integration.md` stale daily/review-record protocol; [P1] add validation
inside `record_review_outcome` or explicitly document direct Python writers as
unsupported.
```

Source: `reporting/plans/v0_1_6/codex_implementation_review_response.md:247-249`.

The v0.1.6 plan also already defines release acceptance:

- Codex r2's 19-item punch list is triaged into fixed or explicitly deferred.
- W3 drift validator runs in CI and reports zero drifts.
- B1's broken daily behavior test is flipped to lock the fixed invariant.
- No `cmd_*` handler can produce an uncaught Python traceback for any CLI args.

Source: `reporting/plans/v0_1_6/PLAN.md:499-510`.

Those are necessary but not sufficient for the user's stated goal. They make
v0.1.6 shippable. They do not yet make it a *massive* improvement.

## Scope Rule

Aggressive v0.1.6 improvement should stay inside these boundaries:

- Improve the existing six-domain local-first loop.
- Improve the CLI/skill contract and agent-operability.
- Improve review/outcome capture.
- Improve install, doctoring, documentation, and proof artifacts.
- Improve tests and eval evidence.

Do not use v0.1.6 to start MCP server work, hosted/multi-user work, UI-first
productization, meal-level nutrition, or connector sprawl. MCP remains roadmap
or later-phase work (`README.md:300-322`; `reporting/docs/agent_integration.md:145-148`).
New domains and adapters have deliberately heavy definitions of done
(`reporting/docs/how_to_add_a_domain.md:470-492`;
`reporting/docs/how_to_add_a_pull_adapter.md:263-285`).

## Proposed v0.1.6 Outcome

By the tag, v0.1.6 should honestly be described as:

> The first release where a local agent can discover the CLI contract, run the
> governed daily loop, capture review outcomes, inspect state, and recover from
> common operator mistakes without relying on maintainer memory.

That is a meaningful improvement over v0.1.5 and still fits the repo's current
identity.

## Workstream A: Close The Current Ship Fixes

Priority: P0.

Goal: remove every known blocker from the round-3 review.

Tasks:

1. Bump release metadata and generated contract version to v0.1.6.
2. Implement `hai capabilities --json` if the repo intends manifest-first
   agent operation. Removing references would be smaller, but it would weaken
   the release. The stronger v0.1.6 move is to ship JSON.
3. Fix `hai daily` capability description and output schema so `incomplete` is
   a first-class state.
4. Update README, `agent_integration.md`, and relevant skills for current
   daily, pull, capabilities, and review-record reality.
5. Validate review outcome payloads at the core writer boundary, not only the
   CLI boundary.

Acceptance:

- `hai capabilities --json` exists and is covered by tests.
- `hai capabilities --markdown` and `reporting/docs/agent_cli_contract.md`
  match after regeneration.
- No stale references to impossible review-record flags remain.
- Bad direct review outcome calls fail before JSONL/SQLite divergence.
- Full suite passes.

## Workstream B: Make The Agent Contract Executable

Priority: P0/P1.

Goal: the agent-facing contract should be generated, testable, and hard to
silently drift.

Rationale: the current implementation review found the generated contract file
matches the CLI, but the content inside the annotations is still stale for
`hai daily`, `hai pull`, and `hai capabilities --json`
(`reporting/plans/v0_1_6/codex_implementation_review_response.md:238-245`).

Tasks:

1. Treat `hai capabilities --json` as the source of truth.
2. Add a JSON-schema-like test for the manifest shape.
3. Extend `scripts/check_skill_cli_drift.py` to inspect:
   - fenced commands,
   - inline/prose command mentions,
   - `allowed-tools` command patterns,
   - choice values,
   - deleted/deprecated flags.
4. Add an allowlist file for intentional references, so the validator can be
   strict without becoming noisy.
5. Add CI tests that fail when README, skills, or generated docs mention
   unsupported CLI flags.

Acceptance:

- The validator catches the current class of `hai capabilities --json` drift.
- The validator catches `allowed-tools` patterns that cannot match examples.
- Adding a new subcommand without annotation fails tests.
- Adding or removing an argparse flag without updating agent-facing docs fails
  tests unless explicitly allowlisted.

## Workstream C: Make `hai daily` Operationally Excellent

Priority: P1.

Goal: `hai daily` should be the best proof that the runtime is governed rather
than chatty.

The v0.1.6 fixes already move daily from "any proposals means complete" to an
honest proposal gate. The next improvement is to make blocked, incomplete, and
complete states easy for both humans and agents to act on.

Tasks:

1. Ensure daily JSON always includes:
   - status,
   - expected domains,
   - present proposal domains,
   - missing proposal domains,
   - next recommended command,
   - whether synthesis was attempted,
   - whether any state mutation occurred.
2. Add tests for zero, partial, complete, and filtered-domain cases.
3. Add one "operator recovery" path to docs: what to do when daily returns
   `awaiting_proposals` or `incomplete`.
4. Add a small transcript/demo artifact for a successful daily loop and a
   blocked partial-domain loop.

Acceptance:

- No daily state requires reading Python code to understand what happened.
- Agents can recover from partial proposal sets using the JSON response alone.
- Docs show the honest two-pass loop, not the old one-shot story.

## Workstream D: Make Review Outcomes Product-Grade

Priority: P1.

Goal: review outcomes should be visibly part of the loop, not a side table.

The doctrine says the flagship loop is not complete without review events
(`reporting/docs/archive/doctrine/canonical_doctrine.md:118-120`). v0.1.6
should prove that.

Tasks:

1. Validate review outcome payloads in the core writer.
2. Add tests that direct Python writer calls cannot create JSONL/SQLite truth
   forks.
3. Improve `hai review summary` output so it clearly surfaces:
   - reviewed recommendations,
   - missed/unreviewed recommendations,
   - followed vs not followed,
   - completion status,
   - disagreement flags,
   - per-domain counts.
4. Add at least one test or fixture showing an outcome is available to a later
   state snapshot or planning surface.

Acceptance:

- The release can truthfully say review outcomes are governed data.
- Outcome capture is covered at CLI and core API layers.
- A maintainer can inspect whether recommendations were actually useful.

## Workstream E: Improve First-Run And Recovery UX

Priority: P1/P2.

Goal: an outside builder should not need maintainer context to run the project.

Tasks:

1. Ensure `hai doctor` catches:
   - missing credentials,
   - missing or gappy migrations,
   - stale/unsupported schema state,
   - unwritable base dir,
   - missing expected docs/contract generation.
2. Add a "clean local dry run" checklist to README or release notes.
3. Add one command transcript from fresh base-dir to first governed daily JSON.
4. Make error messages point to the next concrete command, not just the failing
   condition.

Acceptance:

- A clean checkout can run the documented loop without hidden local state.
- Common setup failures have named doctor checks.
- Release QA includes a fresh-base-dir smoke run.

## Workstream F: Convert Dogfood Findings Into Fixtures

Priority: P1.

Goal: the user-session findings that motivated v0.1.6 should become permanent
tests, not just a one-time audit.

Tasks:

1. Turn the empirical session failures into small fixtures:
   - malformed JSON args,
   - missing evidence bundle,
   - partial proposals,
   - stale review-record docs,
   - projection/reproject mismatch,
   - missing capability annotations.
2. Add one "golden day" fixture representing a realistic complete day.
3. Add one "messy day" fixture representing incomplete proposals plus recovery.

Acceptance:

- Each major v0.1.6 user-session failure has a regression test.
- The test names read like user stories, not only implementation details.
- Future audits do not need to rediscover the same failures manually.

## Workstream G: Expand Skill Evidence, But Keep It Bounded

Priority: P2 for v0.1.6, P1 if time remains.

Goal: improve confidence that packaged skills behave under live agent use.

The skill harness status note says live transcript capture is still manual,
only recovery is covered, synthesis is unscored, and cross-run stability is not
measured (`safety/evals/skill_harness_blocker.md:79-111`). It gives two
bounded next steps: capture first live recovery transcripts, or clone the
harness into a second domain (`safety/evals/skill_harness_blocker.md:127-142`).

Tasks:

1. Capture live recovery transcripts for the existing frozen scenarios.
2. Commit the transcripts with source labels that distinguish live output from
   hand-authored references.
3. Clone the harness to one second domain only if recovery live capture is
   clean.
4. Do not block normal CI on live LLM invocation.

Acceptance:

- At least recovery has live skill-behavior evidence.
- The release notes are honest about what remains unscored.
- The project can claim progress on skill evals without overclaiming coverage.

## Workstream H: Release Proof Pack

Priority: P1.

Goal: make v0.1.6 easy to trust.

Tasks:

1. Add a short release proof document under `reporting/plans/v0_1_6/` with:
   - version/branch/HEAD,
   - full test command and result,
   - targeted workstream test command and result,
   - generated contract check,
   - drift validator result,
   - fresh-base-dir smoke result,
   - known deferrals.
2. Update release notes with "what got materially better" instead of only
   listing files changed.
3. Explicitly list what is still not claimed: MCP server, hosted mode, meal
   planning, medical advice, full skill-harness coverage.

Acceptance:

- A reviewer can understand release quality without rerunning the whole audit.
- Known deferrals are named, not buried.
- The release artifact supports the repo's legibility doctrine
  (`reporting/docs/archive/doctrine/canonical_doctrine.md:122-124`).

## Recommended Sequence

1. **A. Close ship fixes.** Nothing else matters if the current review blockers
   remain open.
2. **B. Executable agent contract.** This prevents the next wave of docs/skill
   drift while other work lands.
3. **C. Daily operational excellence.** This is the center of the user loop.
4. **D. Review outcomes.** This makes the loop visibly outcome-aware.
5. **E. First-run and recovery UX.** This makes the release usable by someone
   outside the maintainer's machine.
6. **F. Dogfood fixtures.** This turns session pain into permanent coverage.
7. **H. Release proof pack.** This makes the release auditable.
8. **G. Skill evidence.** Do recovery live transcripts if time remains; do not
   derail the release for broad skill-harness expansion.

## Definition Of Success For v0.1.6

v0.1.6 should not tag until these are true:

1. `SHIP_WITH_FIXES` is cleared.
2. `hai capabilities --json` exists or every reference is removed; preferred:
   it exists.
3. CLI contract, README, integration docs, and packaged skills agree.
4. `hai daily` has honest, actionable states for zero, partial, and complete
   proposal sets.
5. Review outcomes are validated at every write boundary.
6. Full suite and targeted v0.1.6 suite pass.
7. Fresh-base-dir smoke test passes.
8. Drift validator covers the kinds of drift that actually reached round 3.
9. Release proof pack exists.
10. Deferrals are explicit and do not contradict shipped claims.

## What Would Make This A Massive Improvement

v0.1.6 becomes a major release if the user can say:

- "The CLI tells agents the truth about what exists."
- "The daily loop fails honestly and tells me what to do next."
- "Review outcomes cannot corrupt or fork state."
- "Docs and skills no longer drift silently from argparse."
- "A clean local checkout can prove the core loop."
- "The release has a proof pack, not just a tag."

That is the right ambition for this version. It is more valuable than starting
MCP, adding another wearable, or adding another domain before the core loop is
boringly reliable.
