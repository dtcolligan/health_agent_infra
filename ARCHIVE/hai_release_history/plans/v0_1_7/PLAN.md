# v0.1.7 Plan — first-class agent flow + calibrated correctness

> **Provenance.** Drafted at the close of v0.1.6. Backing report is
> `REPORT.md` in this directory; companion external-audit brief is
> `codex_audit_prompt.md`. Same workstream sequencing template as
> v0.1.6.
>
> **Status.** Draft, awaiting Codex audit response.

---

## 0. Goals & non-goals

### Goals (v0.1.7)

1. **Make the agent's job easier.** Collapse the orchestration
   overhead: an agent should be able to plan a day with one
   "what's next?" call, not 10 sequential reads.
2. **Distribute v0.1.6.** Real PyPI release so anyone can
   `pipx install health-agent-infra` and get the v0.1.6 surface.
3. **Close the v0.1.6 deferred items** the audit cycle flagged as
   structurally important: cold-start matrix decision, synthesis
   allowed-tools order, schema-migrate gap gating, `cmd_propose`
   race-path test.
4. **Add evaluation surfaces** the project currently lacks:
   property-based tests for projectors, determinism eval for
   synthesis, agent-funnel surface in `hai stats`.
5. **Land structural maintainability investments** now that the
   architecture has stabilised: split `cli.py`, declare `__all__`
   discipline + a stability test.

### Non-goals (v0.1.7)

- Multi-user / cloud sync (per `reporting/docs/non_goals.md`).
- Per-meal nutrition (re-evaluate in v0.2 once v0.1.7 closes).
- MCP server implementation (scaffold only if room).
- Redesigning the determinism boundaries — they work; tighten
  what's around them.
- Performance optimisation.

---

## 1. Workstream catalogue

### W21 — `hai daily --auto` next-action manifest (P0)

**Problem.** A Claude Code agent has to compose ~10 commands to
plan one day: `hai daily` → 6 per-domain skill calls → 6
`hai propose` → `hai daily` again → narrate. Each step is correct
but the orchestration burden is on the agent host.

**Fix.** Add `hai daily --auto` mode that, instead of stopping at
the proposal gate, emits a denser `next_actions[]` payload the
agent reads and routes on. Each action is a typed instruction:

```json
{
  "next_actions": [
    {
      "kind": "intake_required",
      "command": "hai intake readiness",
      "reason": "manual_checkin_missing",
      "domain": "recovery",
      "priority": 1
    },
    {
      "kind": "skill_invocation_required",
      "skill": "recovery-readiness",
      "reads": ["snapshot.recovery"],
      "produces": "DomainProposal[domain=recovery]",
      "writes_via": "hai propose --domain recovery"
    },
    {
      "kind": "synthesis_ready",
      "command": "hai synthesize --as-of <date> --user-id <u>"
    }
  ]
}
```

**Acceptance:** an agent reading `next_actions` in order can plan
a day end-to-end without consulting `intent-router` or
`agent_integration.md` for the orchestration logic.

### W22 — PyPI release of 0.1.6 (P0)

**Problem.** v0.1.6 isn't published. Everything we shipped lives
in one checkout.

**Fix.** Build wheel + sdist; verify the `safety/tests/test_packaging.py`
checks pass against the wheel, not just the editable install;
publish to PyPI. Add a `RELEASE.md` checklist to make the next
release reproducible.

**Acceptance:** `pipx install health-agent-infra` from a fresh
machine produces a working `hai 0.1.6`.

### W23 — Migration gap gating in `cmd_state_migrate` (P1)

**Problem.** v0.1.6 W20 added gap detection in `hai doctor`, but
`cmd_state_migrate` still runs `apply_pending_migrations` directly
on a gappy DB. Operators get an OK no-op instead of the warning.

**Fix.** `cmd_state_migrate` calls `detect_schema_version_gaps`
before `apply_pending_migrations`; refuses with `USER_INPUT` and
the same hint `hai doctor` emits.

**Acceptance:** `hai state migrate` against a DB with gaps refuses
with the same diagnostic shape as `hai doctor`.

### W24 — Cold-start matrix decision (P1, deferred from v0.1.6 W14 deep)

**Problem.** Three of six domains have `cold_start_relaxation`;
three don't. v0.1.6 documented the asymmetry as
"intentional" (citing the nutrition non-relaxation test) but
didn't formalise the per-domain decision.

**Fix.** Write `reporting/docs/cold_start_policy_matrix.md`: per
domain, state whether relaxation applies and why (with a code
citation). For domains where the team decides relaxation SHOULD
apply but currently doesn't (recovery? sleep?), implement it under
the same `cold_start_relaxation` rule_id.

**Acceptance:** the doc exists, code matches the doc, a test pins
the per-domain decision matrix.

### W25 — Synthesis-skill `allowed-tools` order test (P1, deferred from v0.1.6 W16)

**Problem.** Codex r2 flagged that `daily-plan-synthesis` skill's
`allowed-tools` says `Bash(hai synthesize --bundle-only *)` but
its body example puts `--bundle-only` last after `--as-of` /
`--user-id`. If Claude Code's matcher is order-sensitive the
skill blocks itself.

**Fix.** Add a test that the skill's body examples match the
skill's `allowed-tools` patterns (extending the W3 drift validator
to inspect this). If the matcher IS order-sensitive: rewrite the
skill examples to put `--bundle-only` / `--drafts-json` first, OR
broaden `allowed-tools` to `Bash(hai synthesize *)`.

**Acceptance:** the validator covers `allowed-tools` ↔ body
example consistency; either the skill examples or the
allowed-tools match.

### W26 — `cmd_propose` race-path test (P1, gap from v0.1.6 W15)

**Problem.** v0.1.6 W15 made `ProposalReplaceRequired` fatal when
raised by `project_proposal` (the thin race window past the
pre-flight check). But the rare race path is not directly tested.

**Fix.** Add a regression test that monkey-patches the pre-flight
check to pass while `project_proposal` raises
`ProposalReplaceRequired`; assert `USER_INPUT` exit + helpful
stderr.

**Acceptance:** the race-path test runs green.

### W27 — Property-based tests for projectors (P1)

**Problem.** Reproject is "deterministic modulo projection
timestamps" but no test asserts two runs against identical JSONL
produce the same SQLite content (excluding the named volatile
columns).

**Fix.** Add `safety/tests/test_projector_determinism.py` using
`hypothesis` (or hand-rolled property tests if hypothesis is too
heavy a dep): generate valid JSONL, run reproject twice, assert
identical SQLite state on every table excluding `projected_at` /
`corrected_at`.

**Acceptance:** the property test passes; a deliberate
non-determinism injection (e.g. hashing iteration order) makes it
fail.

### W28 — `hai stats` agent funnel (P1)

**Problem.** `hai stats` reports last-sync timestamps and a basic
streak. Operators tuning the runtime can't see what's working.

**Fix.** Extend `hai stats` with a `--funnel` flag that reports:

- proposal_gate status histogram over the last 30 days
  (awaiting/incomplete/complete counts)
- per-domain proposal-emit latency (time from `hai daily` start to
  `hai propose --domain X` write)
- review-outcome rate by domain (followed_recommendation true /
  false / not-yet-reviewed)
- `incomplete` causes — which domains were missing most often

**Acceptance:** `hai stats --funnel --since 30` emits a structured
JSON report and a markdown summary.

### W29 — `cli.py` split into per-command modules (P2 maintainability)

**Problem.** `cli.py` is 6300+ lines. Future audits and refactors
pay a higher tax than they should.

**Fix.** Move each `cmd_*` handler into `src/health_agent_infra/cli/
<command>.py` (or a similar layout); keep `cli.py` as the argparse
wiring + entry point. Helpers split into `cli/_helpers.py`.

**Acceptance:** every test still passes; `cli.py` shrinks to <500
lines; `pyproject.toml` console-script entry still resolves.

### W30 — Public API stability test (P2)

**Problem.** `__all__` is disciplined in some modules; nothing
tests the exported surface doesn't change unintentionally between
releases.

**Fix.** Declare `__all__` in every public module; add a test that
asserts the union of `__all__` lists matches a checked-in snapshot
(`safety/snapshots/public_api.txt`). Failures point at the snapshot
file with a diff so the maintainer can decide intentional vs
regression.

**Acceptance:** the test fails when a public symbol is added /
removed without updating the snapshot.

### W31 — README + changelog discipline (P2)

**Problem.** v0.1.6 release docs (release_notes.md) are still on
v0.1.5. `CHANGELOG.md` doesn't exist.

**Fix.** Create `CHANGELOG.md` with v0.1.6 entry summarising the
13-workstream pass; include in `RELEASE.md` checklist for v0.1.7.

**Acceptance:** changelog exists; v0.1.6 + v0.1.7 entries land
together at v0.1.7 release.

---

## 2. Proposed sequencing

| # | Workstream | Why this order |
|---|---|---|
| 1 | W22 (PyPI release of 0.1.6) | Precondition for everything downstream that wants real distribution. |
| 2 | W21 (`hai daily --auto`) | Highest-leverage UX win; flagship feature of v0.1.7. |
| 3 | W23 (migrate gap gate) | Smallest fix; closes a v0.1.6 deferred item with no risk. |
| 4 | W26 (cmd_propose race test) | Pin the v0.1.6 W15 race path. |
| 5 | W25 (synthesis-skill allowed-tools) | Drift validator extension; might block-itself bug. |
| 6 | W27 (projector property tests) | Tightens the W19 determinism claim. |
| 7 | W24 (cold-start matrix) | Deeper design work; needs maintainer decision before code. |
| 8 | W28 (hai stats funnel) | Quality-of-life; useful once W21 is shipped + observed. |
| 9 | W30 (public API stability test) | Maintenance discipline; lands before W29. |
| 10 | W29 (cli.py split) | Big refactor; do last so prior changes are smaller diffs. |
| 11 | W31 (changelog discipline) | Bundle with the v0.1.7 release tag. |

---

## 3. Acceptance for the v0.1.7 release

The release is shippable when:

- v0.1.6 is on PyPI (W22 prerequisite verified).
- `hai daily --auto` (W21) emits a `next_actions` manifest the
  intent-router skill can consume; an end-to-end test using the
  manifest plans a fixture day with no inter-step orchestration.
- All P1 items (W23–W28) have committed fixes + regression tests.
- `cli.py` either remains intact OR (W29 lands) is split with
  zero behavioural delta.
- `CHANGELOG.md` exists with v0.1.6 + v0.1.7 entries.
- Codex audit's P0 + P1 findings on the v0.1.7 plan have been
  triaged into "fixed in this release" or "deferred with rationale."

---

## 4. Codex audit integration

Same protocol as v0.1.6: Codex audits this plan, returns findings,
maintainer folds them into a "Codex audit findings" section here.

---

## 5. Codex audit integration (2026-04-25)

Codex's audit response is at `codex_audit_response.md`. Reconciliation:

- **Cuts/defers to v0.1.8:** W29 (`cli.py` split — too noisy alongside agent-contract work), W30 (public API stability — needs supported-API definition first).
- **Adds (P1):** W32 (source-default drift sweep), W33 (planned-session vocabulary CLI/manifest, revives W8), W34 (nutrition supersede guard, revives W6), W35 (manifest-only fixture-day agent test for W21), W36 (release proof pack).
- **Major scope changes:**
  - **W21** `next_actions[]` shape needs significant strengthening — versioned schema, concrete `command_argv`, `input_schema` references, `blocking`, `safe_to_retry`, `after_success` routing, stable `reason_code`, idempotency hints. The `synthesis_ready` action should normally be `hai daily --skip-pull` (so review scheduling runs) unless explicit two-pass overlay. Also: persist `overall_status` + `expected/present/missing domains` + action count into `runtime_event_log.context_json` so W28 has truthful inputs. Re-sized M/L.
  - **W24** preserve cold-start asymmetry — recovery/sleep/nutrition correctly defer rather than relax (their `insufficient` coverage means missing headline evidence; relaxation would invent recommendations from nothing). Ship the matrix doc + tests pinning the per-domain decisions, NOT relaxation rules.
  - **W22** wheel smoke must be stronger than current CI: `twine check`, README render, fresh `pipx install`, `hai capabilities`, `hai eval run --domain recovery --json`, `hai doctor --json`, no-secret wheel listing.
  - **W23** also guard the lower-level `apply_pending_migrations` (or add a strict variant), not only the CLI.
  - **W25** validator must parse `allowed-tools` frontmatter, not just code blocks.
  - **W27** start with deterministic-replay fixtures; add Hypothesis only around small object factories. Don't generate arbitrary full JSONL.
  - **W31** changelog/release docs are a W22 precondition, not tag cleanup. Update or retire stale `PUBLISH_CHECKLIST.md` rather than adding a competing `RELEASE.md`.

## 5a. Final consolidated v0.1.7 punch list (post-Codex)

Per Codex's re-sequenced list:

1. **[P0] W22 + W31 + W36** — publish v0.1.6 from a reproducible release checklist; update stale release docs; create release proof pack.
2. **[P0] W21 + W35** — versioned next-action manifest + fixture-day test that consumes only `next_actions[]`.
3. **[P0] W21 telemetry prerequisite** — write daily `overall_status` / expected-present-missing / action counts into `runtime_event_log.context_json`.
4. **[P1] W32** — source-default doc/skill drift sweep.
5. **[P1] W23** — migrate gap gating in CLI + lower-level helper.
6. **[P1] W25** — extend drift validator to `allowed-tools`; fix `daily-plan-synthesis`.
7. **[P1] W26** — `cmd_propose` race-path regression.
8. **[P1] W33** — planned-session vocabulary CLI/manifest surface.
9. **[P1] W34** — nutrition same-day supersede guard.
10. **[P1] W24** — cold-start policy matrix doc + per-domain tests (preserving asymmetry).
11. **[P1] W28** — `hai stats --funnel --since N` over persisted telemetry (depends on W21).
12. **[P2] W27** — deterministic projector replay fixtures + Hypothesis around small factories.
13. **[P2] Skill harness** — opportunistic recovery live transcripts; do not claim "completion."
14. **[DEFER] W29** — `cli.py` split → v0.1.8.
15. **[DEFER] W30** — public Python API snapshot → v0.1.8+.

## 5b. New workstream specs (W32–W36)

### W32 — Source-default and agent-doc drift sweep (P1)

**Problem.** Code + README say intervals.icu is the implicit pull
default when configured. But:
- `hai daily --source` parser help still describes csv default
  (`cli.py:5665-5675`)
- `intent-router` skill still routes refresh through `hai pull --live`
  (`intent-router/SKILL.md:85-99`)
- `agent_integration.md` still says CSV is the default
  (`agent_integration.md:184-189`)

**Fix.** Sweep all three locations to match the W5 semantic. Extend
the drift validator (W25) to flag `--source` / `--live` references
that contradict the resolution chain.

**Acceptance.** `hai daily` help, capabilities, README, intent-router,
and agent_integration.md all describe the same source-resolution
order.

### W33 — Planned-session vocabulary CLI surface (P1, W8 revived)

**Problem.** README documents canonical values (`easy_z2`,
`intervals_4x4`, `strength_sbd`, etc.) but parser help on
`hai intake readiness --planned-session-type` still says free text.
Agent has no machine-discoverable way to know which strings are
recognised.

**Fix.** Add `hai planned-session-types --json` (read-only,
agent-safe) that emits the canonical list with per-domain
classifier coverage. W21 `intake_required` actions reference it.

**Acceptance.** `hai planned-session-types --json` returns a
sorted list; `hai capabilities` lists it; W21 next-action manifest
references it for `intake_required` actions.

### W34 — Nutrition same-day supersede guard (P1, W6 revived)

**Problem.** Nutrition intake silently resolves a prior same-day
submission and supersedes it (`cli.py:2464-2512`). README warns
users to log once at end of day, but a public release should make
correction explicit.

**Fix.** When `hai intake nutrition` is called for a day that
already has a row, refuse with USER_INPUT unless `--replace` (or
`--confirm-supersede`) is passed. Stderr names the existing row's
submission_id + recorded_at so the user knows what would be
superseded.

**Acceptance.** Same-day second write without `--replace` refuses
with named USER_INPUT; `--replace` succeeds and the supersede
chain is visible in stdout payload.

### W35 — Manifest-only fixture-day agent test (P0/P1)

**Problem.** W21 acceptance says an agent can plan without
intent-router prose, but no test proves it.

**Fix.** A test harness (`safety/tests/test_daily_auto_manifest_fixture.py`)
that:
1. Initialises a fresh state DB.
2. Runs `hai daily --auto` to get `next_actions[]`.
3. For each action, dispatches to a fake skill / fake intake /
   real `hai propose` based on `kind` + `command_argv`.
4. Re-runs `hai daily --auto` until the manifest reaches
   `synthesis_ready`.
5. Asserts a committed plan exists.

The test must NEVER consult intent-router, agent_integration.md,
or any prose source — only the manifest's typed fields.

**Acceptance.** The test runs green with no string parsing of
prose.

### W36 — Release proof pack (P1)

**Problem.** v0.1.6 release docs are scattered across stale
locations (`PUBLISH_CHECKLIST.md` references 0.1.0;
`reporting/plans/v0_1_4/release_qa.md` pins 0.1.5).

**Fix.** Single proof artifact at `reporting/plans/v0_1_7/RELEASE_PROOF.md`
capturing: branch, version, full-suite result (count + duration),
wheel install verification, capability contract regen, drift
validator result, known deferrals. Updated for v0.1.6 release
event; template carries forward to v0.1.7.

**Acceptance.** Proof pack exists, populated for v0.1.6 publish
event, referenced from CHANGELOG.md.

---

## 6. Implementation log

(Append as work lands.)

- 2026-04-25 · plan + report · `reporting/plans/v0_1_7/{REPORT.md, PLAN.md, codex_audit_prompt.md}` · authored at close of v0.1.6 cycle.
- 2026-04-25 · audit · `reporting/plans/v0_1_7/codex_audit_response.md` · Codex audit: validates 11 of 11 v0.1.6-shipped strong-parts, confirms 11 of 11 real gaps, adds W32–W36, defers W29+W30 to v0.1.8.
- 2026-04-25 · W26 · `safety/tests/test_propose_dual_write_contract.py:test_propose_race_path_replace_required_after_preflight` · race-path regression for v0.1.6 W15.
- 2026-04-25 · W23 · `cli.py:cmd_state_migrate` + `core/state/store.py:apply_pending_migrations(strict=True)` + `SchemaVersionGapError` · migrate refuses gappy DB; library callers can opt into strict mode.
- 2026-04-25 · W34 · `cli.py:cmd_intake_nutrition` `--replace` flag + same-day supersede guard. 4 new tests in `test_nutrition_supersede_guard.py`; 5 existing nutrition tests updated.
- 2026-04-25 · W33 · `core/intake/planned_session_vocabulary.py` registry + `hai planned-session-types` CLI surface. 5 tests in `test_planned_session_vocabulary.py`. Capabilities manifest regenerated.
- 2026-04-25 · W32 · `cli.py` `hai daily --source` help + `intent-router/SKILL.md` refresh section + `agent_integration.md` source-resolution paragraphs all rewritten to consistent v0.1.6+ semantics.
- 2026-04-25 · W21 · `core/intake/next_actions.py` (versioned manifest builder) + `cli.py` `hai daily --auto` flag + per-stage `next_actions_manifest` emission + `runtime_event_log.context_json` writes for proposal-gate telemetry. Fixture-day end-to-end agent test ships as W35.
- 2026-04-25 · W35 · `safety/tests/test_daily_auto_manifest_fixture.py` · 3 tests; the manifest-only end-to-end agent flow reaches `narrate_ready` from a fresh DB without any prose lookup.
- 2026-04-25 · W25 · `scripts/check_skill_cli_drift.py` extended with `allowed-tools` frontmatter inspection + `parse_hai_permissions` + `check_allowed_tools_consistency`. `daily-plan-synthesis` skill `allowed-tools` broadened to `Bash(hai synthesize *)` + prose invariant pinning the read-only/overlay-only contract.
- 2026-04-25 · W24 · `reporting/docs/cold_start_policy_matrix.md` + `safety/tests/test_cold_start_policy_matrix.py` (7 tests). Asymmetry preserved per Codex r3 verdict.
- 2026-04-25 · W31 · `CHANGELOG.md` v0.1.6 + v0.1.7 entries prepended to existing v0.1.5 history.
- 2026-04-25 · W36 · `reporting/plans/v0_1_7/RELEASE_PROOF.md` template + populated for v0.1.7 in-progress state.

**v0.1.7 net delta:** 11 workstreams shipped (W21 + W22 prep + W23 + W24 + W25 + W26 + W31 + W32 + W33 + W34 + W35 + W36). Test count 1921 → 1943 (+22 new tests; 4 skipped). Codex r3 must-fix items all closed. Outstanding for v0.1.8: W22 actual PyPI publish (operator-only), W27 (projector property tests, Codex deferred-with-changes), W28 (stats funnel — telemetry shipped, user surface deferred), W29 (`cli.py` split — Codex defer), W30 (public API stability — Codex defer).
