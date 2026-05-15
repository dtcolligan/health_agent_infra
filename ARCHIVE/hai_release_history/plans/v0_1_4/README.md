# v0.1.4 — Comprehensive Release Plan

- Author: Claude (Opus 4.7) with Dom Colligan
- Started: 2026-04-23
- Status: **Phase 0 (design) in progress**
- Supersedes planned v0.1.3 tranche; v0.1.3 skipped in favour of rigorous v0.1.4.

---

## The argument in one paragraph

The first real end-to-end intervals.icu loop on 2026-04-23 surfaced 15 bugs and 8 broader consistency issues in a codebase with 1489 passing tests. Individual fixes would produce a lacklustre v0.1.3; six underlying patterns need pattern-level remediation. v0.1.4 is the release where every claim in the README is true when audited end-to-end by a motivated reader — the re-author loop works, the audit chain has no silent holes, the user surface exists as a first-class CLI command, the agent-contract manifest is complete, and the first-run experience produces useful recommendations rather than four defers. Nothing ships to PyPI between now and then; `0.1.3.devN` tags on main mark progress.

---

## Phase 0 — Design decisions (gates all code)

Four design docs must be written, reviewed, merged before the corresponding workstream begins. No code in a workstream lands before its gating D-doc is ratified.

| Doc | Status | Decision gating workstream |
|---|---|---|
| [D1 — Re-author and supersede semantics](D1_re_author_semantics.md) | **ratified 2026-04-23: revise, not append** | Workstream A |
| [D2 — Intake write-path contract](D2_intake_write_paths.md) | **ratified 2026-04-23: persist everything, rename note → journal, remove writeback** | Workstream A |
| [D3 — User-facing narration surface](D3_user_surface.md) | **ratified 2026-04-23: `hai today` first-class, per-domain defer templates** | Workstream B |
| [D4 — Cold-start coverage policy](D4_cold_start.md) | **ratified 2026-04-23: 14-day window, relax running/strength, strict nutrition** | Workstream D |

---

## Workstreams

| Workstream | Gates | Owns |
|---|---|---|
| A — Correctness & audit integrity | D1, D2 | proposal revision model, audit-chain integrity, supersede lineage, X9 precondition |
| B — User surface | D3 | `hai today`, narration voice, defer review_questions, README "Reading your plan" |
| C — Agent contract & MCP readiness | — | `hai capabilities --json` enrichment with `flags[]`, contract tests, intent-router manifest update |
| D — Cold-start & onboarding | D4 | cold-start policy relaxation, optional `hai init --interactive`, keychain ACL, `hai stats` cred-awareness |
| E — Test coverage & release QA | — (runs concurrently) | `safety/tests/e2e/`, `safety/tests/contract/`, snapshot tests, dogfood ritual |

---

## Acceptance criteria inventory

See the 18 items in [`acceptance_criteria.md`](acceptance_criteria.md). Each is either in-flight, blocked (on a D-doc or another item), or complete.

---

## Release criteria

v0.1.4 ships to PyPI when all of:

1. All 18 acceptance criteria met.
2. All four D-docs ratified and merged.
3. Each workstream's artifact list complete.
4. New test categories exist in CI: `safety/tests/e2e/`, `safety/tests/contract/`, `safety/tests/snapshot/`.
5. Dogfood day completed against TestPyPI by a fresh user profile; README walkthrough reproducible end-to-end.
6. New tests measurably catch regressions: spot-check by reverting each fix and confirming CI fails.
7. `hai doctor` reports `overall_status=ok` on a fresh install when all expected sources are credentialed.
8. A reader running `hai init` + `hai daily` + `hai today` on v0.1.4, with no agent mediation, gets a useful 6-domain plan and understands what they're reading.

Any failure → v0.1.4 stays on `0.1.3.devN` and we iterate.

---

## Explicit non-goals for v0.1.4

- No MCP server ship (stretch: prove the scaffold works).
- No new domains.
- No new pull adapters (intervals.icu + Garmin stays the set).
- No ML loop.
- No multi-user concerns.
- No meal-level nutrition.
- No real-time or incremental sync.
