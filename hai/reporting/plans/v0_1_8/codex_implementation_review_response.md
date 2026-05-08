# Codex Implementation Review - v0.1.8

## Step 0 confirmation

- `pwd`: `/Users/domcolligan/health_agent_infra`
- `git branch --show-current`: `v0.1.4-release`
- `git log --oneline -1`: `1579357 v0.1.7: finalize release prep and v0.1.8 plan`
- `git status --short`: 47 modified/new paths, matching the claimed uncommitted v0.1.8 implementation.
- `hai --version`: `hai 0.1.8`
- `python3 -m pytest safety/tests/ -q`: `2038 passed, 4 skipped in 53.12s`
- `python3 scripts/check_skill_cli_drift.py`: `OK: no skill <-> CLI drift detected.`

## Executive verdict

**REVISE_BEFORE_SHIP.** The core W48/W49/W50 snapshot and ledger shape is mostly sound, and the suite is green, but two governance contracts are violated in shipped CLI surfaces: `hai stats --data-quality` mutates the DB despite the read-only capability contract, and agent-proposed intent/target rows can become active through agent-safe commands without an explicit commit path. Those are release-blocking because they contradict the v0.1.8 plan's safety framing, not just docs polish.

## Findings

### Priority 1 - invariant / governance violations

**P1-1 - must-fix - `hai stats --data-quality` writes state while advertised as read-only.**

Evidence:
- PLAN.md says `data_quality_daily` rows are populated by a projector "alongside `hai clean`" and the stats surface is agent-safe + read-only (`reporting/plans/v0_1_8/PLAN.md:410`, `reporting/plans/v0_1_8/PLAN.md:411`, `reporting/plans/v0_1_8/PLAN.md:416`).
- The generated contract marks `hai stats` as `read-only` (`reporting/docs/agent_cli_contract.md:106`).
- `cmd_stats` dispatches `--data-quality` into `_emit_data_quality_stats` (`src/health_agent_infra/cli.py:4928`).
- `_emit_data_quality_stats` lazy-projects rows when the window is empty (`src/health_agent_infra/cli.py:5462`, `src/health_agent_infra/cli.py:5471`).
- `project_data_quality_for_date` performs `INSERT OR REPLACE` and commits (`src/health_agent_infra/core/data_quality/projector.py:102`, `src/health_agent_infra/core/data_quality/projector.py:122`).
- The `hai clean` projection path imports and writes accepted-state projectors only; no data-quality projector is wired there (`src/health_agent_infra/cli.py:688`, `src/health_agent_infra/cli.py:764`).

Why it matters: agents rely on capability metadata for mutation planning. A "read-only" stats command that writes SQLite breaks the agent-safety contract and makes audit logs misleading.

Suggested remediation: either move data-quality projection into the write path (`hai clean` / relevant intake projectors) and make stats purely read, or reclassify this mode as writes-state. Given PLAN.md, the right fix is to remove lazy writes from stats and populate rows on projection.

Likely counter-argument: data-quality rows are a queryable projection, not source-of-truth state. Response: the contract defines `read-only` as "No persistent writes of any kind" (`reporting/docs/agent_cli_contract.md:27`), and `INSERT OR REPLACE` into SQLite is a persistent write.

**P1-2 - must-fix - agent-proposed intent/target rows can be inserted as active.**

Evidence:
- W57 says agent-proposed intent/targets are allowed only when marked `source=agent_proposed` and gated behind explicit user commit before becoming active (`reporting/docs/non_goals.md:114`, `reporting/docs/non_goals.md:116`, `reporting/docs/non_goals.md:117`).
- Intent add flags expose `--source` and default `--status active`; the help says agent-proposed rows "MUST" be proposed, but this is not enforced (`src/health_agent_infra/cli.py:6430`, `src/health_agent_infra/cli.py:6436`).
- The handler passes `status` and `source` straight through to `add_intent` (`src/health_agent_infra/cli.py:2065`, `src/health_agent_infra/cli.py:2070`).
- Target has the same shape: default `--status active`, user-selectable `--source agent_proposed`, direct pass-through (`src/health_agent_infra/cli.py:6611`, `src/health_agent_infra/cli.py:6615`, `src/health_agent_infra/cli.py:2253`, `src/health_agent_infra/cli.py:2255`).
- Both insert commands are marked agent-safe (`src/health_agent_infra/cli.py:6469`, `src/health_agent_infra/cli.py:6626`).

Why it matters: this allows the exact W57-forbidden shape: an agent-proposed plan/target becoming active without a separate user-confirmed commit path.

Suggested remediation: reject `--source agent_proposed --status active` at the CLI and store validation boundary, or add an explicit confirm/promote command that is clearly user-gated.

Likely counter-argument: help text instructs agents to use `--status proposed`. Response: help text is not a runtime invariant, and this project treats CLI validation as the governance boundary.

### Priority 2 - workstream-specific spot checks

**P2-1 - should-fix - `hai daily --auto --explain` omits the promised snapshot details.**

Evidence:
- PLAN.md requires the explain snapshot block to include per-domain classified bands, missingness, and `review_summary` tokens (`reporting/plans/v0_1_8/PLAN.md:538`, `reporting/plans/v0_1_8/PLAN.md:542`, `reporting/plans/v0_1_8/PLAN.md:543`).
- The daily snapshot stage stores only `domains_in_bundle` and `full_bundle` (`src/health_agent_infra/cli.py:4246`, `src/health_agent_infra/cli.py:4251`).
- `_build_daily_explain_block` looks for `domains_present`, `missingness_per_domain`, and no classified bands or review-summary tokens (`src/health_agent_infra/cli.py:5067`, `src/health_agent_infra/cli.py:5070`).

Why it matters: `explain.snapshot.domains_present` is currently always `None`, and the feature does not expose the W48 tokens that motivated the explain addition.

Suggested remediation: populate the snapshot stage from the already-built `snapshot` dict with domain bands, missingness, and `review_summary.tokens`; align key names (`domains_in_bundle` vs `domains_present`) and extend the W43 test to assert values, not just keys.

**P2-2 - should-fix - W41 running live capture is wired to the recovery skill.**

Evidence:
- The harness now declares `SUPPORTED_DOMAINS = ("recovery", "running")` (`safety/evals/skill_harness/runner.py:55`).
- `invoke_live()` always loads `recovery-readiness/SKILL.md` (`safety/evals/skill_harness/runner.py:312`, `safety/evals/skill_harness/runner.py:314`).
- Its live prompt always says "You are running as the recovery-readiness skill" (`safety/evals/skill_harness/runner.py:321`, `safety/evals/skill_harness/runner.py:322`).

Why it matters: CI replay is safe, but operator live capture for the new running domain would invoke the wrong skill, so the "second domain live capture" path is not actually usable for running.

Suggested remediation: select the skill path and prompt from `scenario["domain"]`, and add a tiny test that a running live invocation would target `running-readiness/SKILL.md` without actually launching live mode.

**P2-3 - should-fix - `hai config validate` does not validate numeric ranges.**

Evidence:
- PLAN.md includes range validation in W39: "numeric values satisfy local range checks where possible" (`reporting/plans/v0_1_8/PLAN.md:484`, `reporting/plans/v0_1_8/PLAN.md:489`).
- The validator only emits `unknown_key` and scalar `type_mismatch` issues (`src/health_agent_infra/cli.py:3785`, `src/health_agent_infra/cli.py:3823`).
- Review-summary numeric knobs include values where local ranges are obvious: `window_days`, `min_denominator`, and mixed lower/upper bounds (`src/health_agent_infra/core/config.py:367`, `src/health_agent_infra/core/config.py:386`).

Why it matters: a file with `window_days = -7` or `mixed_token_lower_bound > mixed_token_upper_bound` can pass validation, then fail or produce misleading W48 token behavior at use time.

Suggested remediation: add local range checks for `[policy.review_summary]` at minimum: positive `window_days`, non-negative denominators/thresholds, and `0 <= lower <= upper <= 1`.

### Priority 3 - release prep / docs

**P3-1 - should-fix - snapshot v2 transition is not documented where the code says it is.**

Evidence:
- `build_snapshot` says v1 consumers should see `reporting/docs/agent_integration.md` for the v2 transition note (`src/health_agent_infra/core/state/snapshot.py:938`, `src/health_agent_infra/core/state/snapshot.py:943`).
- RELEASE_PROOF documents the v2 fields (`reporting/plans/v0_1_8/RELEASE_PROOF.md:70`, `reporting/plans/v0_1_8/RELEASE_PROOF.md:78`).
- `agent_integration.md` still describes the agent wire contract and determinism boundaries without any `state_snapshot.v2`, `review_summary`, `data_quality`, `snapshot.intent`, or `snapshot.target` references (`reporting/docs/agent_integration.md:113`, `reporting/docs/agent_integration.md:116`). `rg -n "state_snapshot\\.v2|review_summary|data_quality|snapshot\\.intent|snapshot\\.target" reporting/docs/agent_integration.md` returned no matches.

Why it matters: the code and proof pack point consumers to a transition note that does not exist. This is not a code break, but it is a release-contract miss.

Suggested remediation: add a short "Snapshot schema v2" section to `agent_integration.md` listing the additive fields and telling v1 consumers to ignore unknown keys or pin versions.

## What's clean

- Code-vs-skill boundary held in the readiness skills: W49/W50 added read-only `hai intent list` / `hai target list` tools, and the skills still explicitly forbid band/score/R-rule/X-rule computation (`src/health_agent_infra/skills/running-readiness/SKILL.md:4`, `src/health_agent_infra/skills/running-readiness/SKILL.md:85`, `src/health_agent_infra/skills/running-readiness/SKILL.md:87`).
- W48 review-summary tokens are code-owned and visibility-only in the implementation I traced: `build_review_summary` computes them (`src/health_agent_infra/core/review/summary.py:197`, `src/health_agent_infra/core/review/summary.py:234`), and production callers only attach/read them in snapshot/stats (`src/health_agent_infra/core/state/snapshot.py:869`, `src/health_agent_infra/cli.py:5119`).
- Snapshot v1 -> v2 is additive in code: old top-level v1 keys remain present and new `intent` / `target` siblings are appended (`src/health_agent_infra/core/state/snapshot.py:944`, `src/health_agent_infra/core/state/snapshot.py:975`).
- Migrations 019/020/021 are forward and idempotent, with the requested SQL CHECK constraints present (`src/health_agent_infra/core/state/migrations/019_intent_item.sql:24`, `src/health_agent_infra/core/state/migrations/020_target.sql:20`, `src/health_agent_infra/core/state/migrations/021_data_quality.sql:30`, `safety/tests/test_state_store.py:169`).
- Active-at-date semantics are inclusive and handle open-ended targets correctly (`src/health_agent_infra/core/intent/store.py:273`, `src/health_agent_infra/core/target/store.py:251`).
- W51 cold-start state is consistent between in-memory snapshot and projector: both derive `in_window` from the same `cold_start` boolean (`src/health_agent_infra/core/state/snapshot.py:895`, `src/health_agent_infra/core/state/snapshot.py:907`, `src/health_agent_infra/core/data_quality/projector.py:83`, `src/health_agent_infra/core/data_quality/projector.py:100`).
- W43 additive gating is correct even though the block content is thin: explain attaches only when both `--auto` and `--explain` are set (`src/health_agent_infra/cli.py:4345`, `src/health_agent_infra/cli.py:4410`).
- W41/W42 CI paths are replay/deterministic; live skill invocation is env-gated and not triggered by pytest (`safety/evals/skill_harness/runner.py:306`, `safety/tests/test_skill_harness.py:152`, `safety/evals/synthesis_harness/runner.py:5`).
