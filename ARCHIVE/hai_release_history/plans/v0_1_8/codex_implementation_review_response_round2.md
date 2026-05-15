# Maintainer response to Codex implementation review (round 2)

> **Audit reviewed:** `codex_implementation_review_response.md`
> (Codex round 1, REVISE_BEFORE_SHIP).
> **Response by:** Claude (maintainer-implementer), 2026-04-25.
> **Verdict on the audit:** Both P1 findings accepted as must-fix
> and shipped. All three P2 findings accepted as should-fix and
> shipped same release. P3-1 accepted and shipped. No findings
> refuted.

---

## Executive summary

All six findings from Codex round 1 have been addressed in the same
v0.1.8 cycle. The two P1 governance violations (`hai stats
--data-quality` writing state, agent-proposed rows landing as
active) are fixed at both the CLI surface and the store boundary,
with regression tests pinning the invariants. The three P2
should-fixes and the P3 doc-miss are all closed. Suite grew **2038
→ 2058 passed** (+20 new regression tests). Drift validator OK.
Capability contract regenerated.

---

## Per-finding response

### P1-1 — `hai stats --data-quality` writes state — **ACCEPTED, FIXED**

**Codex finding.** Capability manifest annotates `hai stats` as
`read-only`. `_emit_data_quality_stats` lazy-projected via
`project_data_quality_for_date` which `INSERT OR REPLACE`-d into
`data_quality_daily`. Read-only contract violation.

**Fix shipped.**
- Removed lazy-projection from `_emit_data_quality_stats`
  (`src/health_agent_infra/cli.py:5481-5497`). The read-only stats
  surface now honestly returns empty rows on a fresh DB.
- Wired `project_data_quality_for_date` into the `hai clean` write
  path inside the existing atomic transaction
  (`src/health_agent_infra/cli.py:759-784`). Per PLAN.md § 2 W51:
  "rows populated by a code-owned projector that runs alongside
  `hai clean`."
- Added `commit_after` parameter to `project_data_quality_for_date`
  (`src/health_agent_infra/core/data_quality/projector.py:60-71`)
  so the projector can compose into an outer transaction without
  double-committing.

**Regression tests added.**
- `test_cli_data_quality_is_read_only_on_fresh_db` — explicitly
  verifies the row count in `data_quality_daily` stays 0 after a
  `hai stats --data-quality --json` call against a fresh DB. Pins
  the contract at the SQL layer, not just the CLI exit code.
- `test_cli_data_quality_returns_rows_after_projection` — verifies
  the read-only stats surface returns rows correctly when the
  projector has run via the canonical write path.

**Why accepted without challenge.** The capability contract
explicitly defines `read-only` as "No persistent writes of any
kind"; `INSERT OR REPLACE` is a persistent write. No defence
available; the lazy-projection convenience violated the contract
the project itself defined. PLAN.md § 2 W51 also explicitly named
`hai clean` as the right home for the projector.

### P1-2 — agent-proposed intent/target rows can be inserted as active — **ACCEPTED, FIXED**

**Codex finding.** W57 says agent-proposed intent/targets MUST be
gated behind explicit user commit before becoming active. Help text
asserted this but the runtime did not enforce it. Both `add_intent`
and `add_target` accepted `--source agent_proposed --status active`
through agent-safe CLI commands.

**Fix shipped.** Defence-in-depth at two layers:

- **Store-level invariant** in both validators
  (`src/health_agent_infra/core/intent/store.py:181-191`,
  `src/health_agent_infra/core/target/store.py:175-186`). When
  `record.source != "user_authored"` AND `record.status == "active"`,
  raise `IntentValidationError` / `TargetValidationError` with an
  explicit message naming `commit_intent` / `commit_target` as the
  required path.
- **CLI-level rejection** flows naturally through the existing
  exception handlers (`cli.py:2101`, `cli.py:2317`); USER_INPUT
  exit + stderr message.
- **User-gated commit path added.** New `commit_intent` and
  `commit_target` functions
  (`src/health_agent_infra/core/intent/store.py:282-297`,
  `src/health_agent_infra/core/target/store.py:265-279`) flip a
  `proposed` row to `active` only when it currently *is*
  `proposed`. New CLI subcommands `hai intent commit
  --intent-id ID` and `hai target commit --target-id ID`
  (`cli.py:2218-2245`, `cli.py:2389-2414`).
- **Capability manifest marks the new commit commands
  `agent_safe=False`** with explicit description: "agents that
  proposed the row must NOT auto-promote it; only an explicit user
  invocation may run this command."

**Regression tests added** (8 new tests across intent + target):
- `test_store_rejects_agent_proposed_active` (×2, intent + target)
- `test_store_allows_user_authored_active` + sanity-check
  variants — pin the legitimate shapes don't regress
- `test_store_allows_agent_proposed_proposed` — pin the
  agent-write path stays open
- `test_commit_intent_promotes_proposed_to_active` (×2)
- `test_commit_intent_no_op_on_already_active` — promotion is
  idempotent
- `test_cli_intent_training_add_session_rejects_agent_proposed_active`
  (×2, intent + target) — the actual CLI surface is rejected
- `test_cli_intent_commit_round_trips` (×2) — the user-gated
  promotion path works end-to-end

**Why accepted without challenge.** Codex correctly identified
that help text is not a runtime invariant. The project treats CLI
validation as the governance boundary, and the boundary was
missing. Worth noting: the store-level enforcement (not just CLI)
means future code paths that bypass the CLI cannot inadvertently
reintroduce the bypass — defence-in-depth is the right shape for a
governance boundary.

### P2-1 — `hai daily --auto --explain` snapshot block is thin — **ACCEPTED, FIXED**

**Codex finding.** The snapshot stage stored only `domains_in_bundle`
and `full_bundle`. `_build_daily_explain_block` looked for
`domains_present`, `missingness_per_domain`, and no classified
bands or review-summary tokens. Result: `explain.snapshot.domains_present`
was always None and the W48 tokens were not surfaced.

**Fix shipped.**
- Enriched the snapshot stage write
  (`src/health_agent_infra/cli.py:4336-4374`) to populate
  `domains_present`, `missingness_per_domain`,
  `classified_bands_per_domain`, `review_summary_tokens_per_domain`.
  Reads already-built snapshot data; no recomputation.
- Kept `domains_in_bundle` as a backward-compatible alias.
- Extended the explain-block builder
  (`src/health_agent_infra/cli.py:5168-5180`) to surface the new
  fields under `explain.snapshot`.

**Regression test added.**
- `test_auto_explain_snapshot_block_carries_w48_signals` —
  asserts `domains_present` is populated, missingness is a dict,
  classified bands and review_summary_tokens dicts exist, and on
  an empty DB the recovery review_summary tokens contain
  `outcome_pattern_insufficient_denominator`. Pins values, not
  just keys.

### P2-2 — W41 live capture wired to recovery skill — **ACCEPTED, FIXED**

**Codex finding.** `invoke_live` always loaded
`recovery-readiness/SKILL.md`; running scenarios would invoke the
wrong skill. Replay was safe; live mode was broken for the new
domain.

**Fix shipped.**
- Added `_LIVE_SKILL_BY_DOMAIN` dispatch table + helper
  (`safety/evals/skill_harness/runner.py:55-75`) mapping
  `"recovery"→"recovery-readiness"` and
  `"running"→"running-readiness"`. Helper raises `HarnessError` for
  unknown domains rather than silently falling back.
- Updated `invoke_live`
  (`safety/evals/skill_harness/runner.py:316-345`) to dispatch
  skill path + prompt on `scenario["domain"]`.

**Regression tests added.**
- `test_live_mode_dispatches_skill_on_scenario_domain` — verifies
  the dispatch table maps recovery and running correctly without
  launching live mode.
- `test_live_mode_refuses_unknown_domain` — verifies unknown
  domains raise rather than silently fall back.

### P2-3 — `hai config validate` does not validate numeric ranges — **ACCEPTED, FIXED**

**Codex finding.** PLAN.md § 2 W39 promised "numeric values satisfy
local range checks where possible." The validator only emitted
`unknown_key` and `type_mismatch`. A user could land
`window_days = -7` or invert mixed-token bounds silently.

**Fix shipped.**
- Added `_review_summary_range_issues` helper
  (`src/health_agent_infra/cli.py:3787-3852`) covering the obvious
  bounds for `[policy.review_summary]`: `window_days >= 1`,
  non-negative `min_denominator` + thresholds, mixed-token bounds in
  `[0, 1]` and `lower <= upper`.
- New issue kind `range_violation` is always blocking (not gated
  on `--strict`) — these errors produce misbehaving W48 token
  output, not just unknown-key noise.

**Regression tests added** (4 tests):
- `test_config_validate_window_days_negative_blocks`
- `test_config_validate_mixed_lower_above_upper_blocks`
- `test_config_validate_mixed_bound_outside_unit_interval_blocks`
- `test_config_validate_negative_threshold_blocks`

### P3-1 — snapshot v2 transition undocumented in agent_integration.md — **ACCEPTED, FIXED**

**Codex finding.** Code comment + RELEASE_PROOF reference a v2
transition note in `agent_integration.md` that did not exist. Not
a code break; release-contract miss.

**Fix shipped.**
- Added "Snapshot schema v2 (v0.1.8 transition note)" section to
  `reporting/docs/agent_integration.md` (between "What an agent
  should NOT do" and "MCP" sections). Lists the four additive
  fields (`review_summary`, `data_quality`, `intent`, `target`),
  pins the additive guarantee ("no v1 field was removed or had its
  shape changed"), and gives v1 consumers explicit pin-or-ignore
  guidance.

---

## Maintainer findings beyond Codex's audit

None this round. Every finding Codex surfaced was correct and
actionable.

---

## Suite + verification deltas

| Metric | Before round-1 fixes | After round-1 fixes |
|---|---:|---:|
| Tests passed | 2038 | 2058 |
| Tests skipped | 4 | 4 |
| Tests added (this round) | — | +20 |
| Drift validator | OK | OK |
| Capability contract regenerated | n/a | yes |
| `hai --version` | hai 0.1.8 | hai 0.1.8 |

New tests are concentrated on pinning the governance invariants
Codex identified, not on adding new feature surface. Every P1 fix
has at least one test that would have caught the original
violation.

---

## What changed by file

```
src/health_agent_infra/cli.py
  - cmd_clean: data-quality projection wired into clean transaction
  - _emit_data_quality_stats: lazy-write removed, surface read-only
  - cmd_intent_commit + parser: new user-gated promotion command
  - cmd_target_commit + parser: new user-gated promotion command
  - daily snapshot stage: enriched with W48 tokens + bands + missingness
  - _build_daily_explain_block: surface new snapshot fields
  - cmd_config_validate: range_violation issue kind + helper

src/health_agent_infra/core/intent/store.py
  - _validate: agent-proposed-active rejected at insert
  - commit_intent: new function for user-gated promotion

src/health_agent_infra/core/intent/__init__.py
  - export commit_intent

src/health_agent_infra/core/target/store.py
  - _validate: same invariant for targets
  - commit_target: parallel to commit_intent

src/health_agent_infra/core/target/__init__.py
  - export commit_target

src/health_agent_infra/core/data_quality/projector.py
  - project_data_quality_for_date: commit_after parameter

safety/evals/skill_harness/runner.py
  - _LIVE_SKILL_BY_DOMAIN dispatch table + helper
  - invoke_live: dispatch on scenario["domain"]

safety/tests/test_data_quality_ledger.py
  - read-only contract test + post-projection test

safety/tests/test_intent_ledger.py
  - 8 new tests for W57 enforcement + commit path

safety/tests/test_target_ledger.py
  - 4 new tests for the same invariants on targets

safety/tests/test_cli_daily_auto_explain.py
  - W48-signal-on-snapshot-block test

safety/tests/test_skill_harness.py
  - dispatch table tests for invoke_live

safety/tests/test_cli_config_validate_diff.py
  - 4 range-violation tests

reporting/docs/agent_integration.md
  - Snapshot schema v2 transition section
```

---

## Re-verdict request

Round 1 verdict: REVISE_BEFORE_SHIP. With the fixes above shipped
and regression-tested, the two P1 blockers are resolved, all three
P2 should-fixes are resolved, and the P3 doc miss is closed. The
maintainer requests a round-2 audit confirming the fixes match the
findings; if confirmed, ship verdict on v0.1.8 should move to
SHIP.

If round 2 finds residual issues with any of the fixes (e.g. the
`commit_intent` semantics are wrong, or the `_review_summary_range_issues`
ranges are too narrow), surface them with the same severity model
(must-fix / should-fix / nit) and the maintainer will respond
under the same protocol.
