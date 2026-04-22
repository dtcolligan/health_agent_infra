# Agent CLI contract

**This file is generated. Do not edit by hand.** Source of truth is
the annotations on each ``add_parser`` call in
``src/health_agent_infra/cli.py``; regenerate with
``python -m health_agent_infra.core.capabilities.render --write`` or
by invoking ``hai capabilities --json`` and piping through the same
renderer.

Schema: see ``core/capabilities/walker.py``. Exit codes follow
``reporting/docs/cli_exit_codes.md``. Every handler is on the stable
taxonomy; the ``LEGACY_0_2`` sentinel is retained in the schema for
forward-compatibility but is not currently emitted.

## Mutation classes

| Value | Meaning |
|---|---|
| ``read-only`` | No persistent writes of any kind. |
| ``writes-sync-log`` | Writes only ``sync_run_log`` rows. |
| ``writes-audit-log`` | Appends to JSONL audit logs (no main-DB writes). |
| ``writes-state`` | Writes to the primary state DB tables. |
| ``writes-memory`` | Writes to the ``user_memory`` table. |
| ``writes-skills-dir`` | Copies the packaged skills tree to ``~/.claude/skills/``. |
| ``writes-config`` | Writes a config / thresholds file on disk. |
| ``writes-credentials`` | Writes to the OS keyring. |
| ``interactive`` | Requires live human input; not agent-invocable. |

## Idempotency

| Value | Meaning |
|---|---|
| ``yes`` | Same inputs produce the same persisted state after every call. |
| ``yes-with-supersede`` | Idempotent via an explicit ``--supersede`` flag that versions. |
| ``no`` | Append-only, order-sensitive, or interactive. |
| ``n/a`` | Read-only; idempotency doesn't apply. |

## JSON output modes

| Value | Meaning |
|---|---|
| ``default`` | Emits JSON on stdout unconditionally. |
| ``opt-in`` | Emits JSON only when ``--json`` is passed. |
| ``opt-out`` | Emits JSON by default; ``--text`` suppresses. |
| ``none`` | Text output only. |
| ``dual`` | Supports both ``--json`` and ``--text`` explicitly. |

## Commands

*37 commands; hai 0.1.1; schema agent_cli_contract.v1*

| Command | Mutation | Idempotent | JSON | Agent-safe | Exit codes | Description |
|---|---|---|---|---|---|---|
| ``hai auth garmin`` | ``writes-credentials`` | ``yes`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Store Garmin credentials in the OS keyring. Interactive by default; operator-only (requires a live password). |
| ``hai auth status`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK`` | Report whether Garmin credentials are configured. Presence only — never emits the secret itself. |
| ``hai capabilities`` | ``read-only`` | ``n/a`` | ``opt-out`` | yes | ``OK`` | Emit the agent-CLI-contract manifest describing every subcommand's mutation class, idempotency, JSON output, and exit codes. The authoritative surface the routing skill consumes. |
| ``hai classify`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Debug helper: run the per-domain classifier on a cleaned evidence JSON. |
| ``hai clean`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Normalize pulled evidence into CleanedEvidence + RawSummary JSON and project accepted state rows. Best-effort projection when --db-path is absent. |
| ``hai config init`` | ``writes-config`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Scaffold a default thresholds.toml at the user-config path. |
| ``hai config show`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Print the effective merged threshold configuration (defaults + overrides). |
| ``hai daily`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Morning orchestrator: pull → clean → reproject → propose → synthesize → daily_plan in one invocation. |
| ``hai doctor`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT`` | Report runtime health: DB present, migrations up to date, per-source freshness, today's accepted counts. |
| ``hai eval run`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT``, ``INTERNAL`` | Execute frozen deterministic eval scenarios for a domain (--domain) or the synthesis layer (--synthesis). Read-only — scores scenarios, never writes state. USER_INPUT when a scenario fails its rubric; INTERNAL if the runner itself crashes. |
| ``hai exercise search`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Rank top exercise-taxonomy matches for a free-text query. |
| ``hai explain`` | ``read-only`` | ``n/a`` | ``opt-out`` | yes | ``OK``, ``USER_INPUT``, ``NOT_FOUND`` | Reconstruct the full audit chain (planned / adapted / firings / performed) for a committed plan. Strictly read-only — never recomputes runtime state. |
| ``hai init`` | ``interactive`` | ``no`` | ``none`` | no | ``OK``, ``USER_INPUT`` | First-run wizard: state init, config scaffolding, auth setup. |
| ``hai intake exercise`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Upsert an exercise taxonomy entry. |
| ``hai intake gym`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a gym session (sets + exercises) as typed human-input. |
| ``hai intake note`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Attach a free-text context note to a day. |
| ``hai intake nutrition`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a macros-only nutrition intake entry. |
| ``hai intake readiness`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a manual readiness self-report entry. |
| ``hai intake stress`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a manual stress observation (used when Garmin stress is absent). |
| ``hai memory archive`` | ``writes-memory`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Mark a user_memory entry archived (soft delete). The row itself stays for audit; read surfaces filter it out. |
| ``hai memory list`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | List user_memory entries active at a given date, grouped by category. |
| ``hai memory set`` | ``writes-memory`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Append a user_memory entry (goal / preference / constraint / context). Append-only — replace by archiving the old row and setting a new one. |
| ``hai policy`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Debug helper: evaluate R-rules on a cleaned evidence JSON. |
| ``hai propose`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Validate a DomainProposal and append it to proposal_log. One of the three determinism boundaries the runtime enforces. |
| ``hai pull`` | ``writes-sync-log`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT``, ``TRANSIENT`` | Acquire Garmin evidence (CSV fixture by default, live via --live) for a date and emit cleaned evidence JSON. Writes a sync_run_log row; does not touch the main state tables. |
| ``hai review record`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a review_outcome against a review_event. Carries the migration-010 enrichment columns (completed, intensity_delta, pre/post_energy, disagreed_firing_ids). |
| ``hai review schedule`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Persist a pending review_event for a recommendation (used to schedule the next-day review question). |
| ``hai review summary`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Summarize review_outcome counts (followed / not-followed, per-domain tallies). |
| ``hai setup-skills`` | ``writes-skills-dir`` | ``yes`` | ``default`` | yes | ``OK`` | Copy the packaged skills/ tree to ~/.claude/skills/ so Claude Code discovers them. |
| ``hai state init`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK`` | Create the local SQLite state DB and apply all pending migrations. Idempotent — safe to call repeatedly. |
| ``hai state migrate`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Apply any pending schema migrations to an already-initialized state DB. |
| ``hai state read`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Read a per-domain accepted-state row for a given date. |
| ``hai state reproject`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Rebuild the accepted_*_state_daily tables from the raw evidence JSONL. Deterministic projection — safe to re-run. |
| ``hai state snapshot`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Emit the cross-domain state snapshot the synthesis / skills layer consumes for a (for_date, user_id) pair. |
| ``hai stats`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT`` | Summarise sync_run_log (last pull per source) + runtime_event_log (recent commands, daily streak) from the user's local DB. No telemetry leaves the device. |
| ``hai synthesize`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | yes | ``OK``, ``USER_INPUT``, ``INTERNAL`` | Run synthesis end-to-end inside one atomic SQLite transaction: daily_plan + x_rule_firings + planned_recommendation + recommendation_log. --supersede versions the plan instead of replacing it. |
| ``hai writeback`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Legacy recovery-only direct writeback path. Validates a TrainingRecommendation against the bounded schema and appends to the recovery audit log. Non-recovery domains go through hai synthesize instead. |
