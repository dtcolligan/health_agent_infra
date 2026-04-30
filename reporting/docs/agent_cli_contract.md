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

**Per-command structured detail lives in the JSON manifest, not
this markdown.** Every row below also carries a ``flags[]`` array
(name / type / required / choices / default / help / aliases), and
selected high-traffic commands opt in to ``output_schema`` (JSON
shape per exit code) and ``preconditions`` (state that must exist
before invocation). Agents should ``hai capabilities`` and read the
JSON; this markdown is an at-a-glance overview for humans.

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

*56 commands; hai 0.1.13; schema agent_cli_contract.v1*

| Command | Mutation | Idempotent | JSON | Agent-safe | Exit codes | Description |
|---|---|---|---|---|---|---|
| ``hai auth garmin`` | ``writes-credentials`` | ``yes`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Store Garmin credentials in the OS keyring. Interactive by default; operator-only (requires a live password). |
| ``hai auth intervals-icu`` | ``writes-credentials`` | ``yes`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Store Intervals.icu credentials in the OS keyring. Interactive by default; operator-only (requires a live API key). |
| ``hai auth remove`` | ``writes-credentials`` | ``yes`` | ``default`` | no | ``OK`` | Remove stored credentials from the OS keyring. Idempotent — removing absent credentials is a no-op. Env-var-supplied credentials are never touched. |
| ``hai auth status`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK`` | Report whether Garmin and Intervals.icu credentials are configured. Presence only — never emits the secret itself. |
| ``hai capabilities`` | ``read-only`` | ``n/a`` | ``opt-out`` | yes | ``OK`` | Emit the agent-CLI-contract manifest describing every subcommand's mutation class, idempotency, JSON output, and exit codes. The authoritative surface the routing skill consumes. |
| ``hai clean`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Normalize pulled evidence into CleanedEvidence + RawSummary JSON and project accepted state rows. Best-effort projection when --db-path is absent. |
| ``hai config diff`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Diff user thresholds.toml against DEFAULT_THRESHOLDS, leaf by leaf. |
| ``hai config init`` | ``writes-config`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Scaffold a default thresholds.toml at the user-config path. |
| ``hai config show`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Print the effective merged threshold configuration (defaults + overrides). |
| ``hai config validate`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Validate user thresholds.toml against DEFAULT_THRESHOLDS shape. |
| ``hai daily`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Morning orchestrator: deterministic stages run end-to-end (pull → clean → snapshot → gaps → proposal_gate). The agent then invokes the 6 per-domain readiness skills, posts DomainProposal rows via `hai propose --domain <d>`, and re-runs `hai daily` to advance the gate to `complete` and trigger synthesis. `--domains <csv>` narrows the expected set for partial-day planning. |
| ``hai demo cleanup`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK`` | Remove an orphan / corrupt demo marker so the CLI can return to normal mode. Allowed even when the marker is invalid (the fail-closed escape hatch). |
| ``hai demo end`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK`` | Close the active demo session. Removes the marker so subsequent CLI invocations route to real persistence. v0.1.11 W-Va leaves the scratch root in place; W-Vb adds archive-on-end behaviour. |
| ``hai demo start`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Open a new demo session. Creates a scratch root at /tmp/hai_demo_<id>/ with state.db, health_agent_root/, and config/thresholds.toml. Writes a marker file at the demo-session location ($XDG_CACHE_HOME/hai/ or ~/.cache/hai/). Refuses with USER_INPUT if a session is already active. |
| ``hai doctor`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT`` | Report runtime health: DB present, migrations up to date, per-source freshness, today's accepted counts. |
| ``hai eval run`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT``, ``INTERNAL`` | Execute frozen deterministic eval scenarios for a domain (--domain) or the synthesis layer (--synthesis). Read-only — scores scenarios, never writes state. USER_INPUT when a scenario fails its rubric; INTERNAL if the runner itself crashes. |
| ``hai exercise search`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Rank top exercise-taxonomy matches for a free-text query. |
| ``hai explain`` | ``read-only`` | ``n/a`` | ``opt-out`` | yes | ``OK``, ``USER_INPUT``, ``NOT_FOUND`` | Reconstruct the full audit chain (planned / adapted / firings / performed) for a committed plan. Strictly read-only — never recomputes runtime state. |
| ``hai init`` | ``interactive`` | ``no`` | ``none`` | no | ``OK``, ``USER_INPUT`` | First-run wizard: state init, config scaffolding, auth setup. |
| ``hai intake exercise`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Upsert an exercise taxonomy entry. |
| ``hai intake gaps`` | ``read-only`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Return the list of user-closeable intake gaps in the snapshot. Read-only; no side effects. |
| ``hai intake gym`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a gym session (sets + exercises) as typed human-input. |
| ``hai intake note`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Attach a free-text context note to a day. |
| ``hai intake nutrition`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a macros-only nutrition intake entry. |
| ``hai intake readiness`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a manual readiness self-report entry. |
| ``hai intake stress`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a manual stress observation (used when Garmin stress is absent). |
| ``hai intent archive`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Archive a W49 intent row (status='archived'). Marked NOT agent-safe: archiving an active or proposed row IS user-state deactivation per AGENTS.md W57. Agents that proposed the row must NOT auto-archive it; only an explicit user invocation may run this command. |
| ``hai intent commit`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Promote a proposed intent row to active. Marked NOT agent-safe: agents that proposed the row must NOT auto-promote it; only an explicit user invocation may run this command. |
| ``hai intent list`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | List intent rows from the W49 ledger; default-active. |
| ``hai intent sleep set-window`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Insert a sleep-window intent into the W49 intent ledger. |
| ``hai intent training add-session`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Insert a user-authored training-session intent into the W49 intent ledger. |
| ``hai intent training list`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | List training intent rows from the W49 ledger. |
| ``hai memory archive`` | ``writes-memory`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Mark a user_memory entry archived (soft delete). The row itself stays for audit; read surfaces filter it out. |
| ``hai memory list`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | List user_memory entries active at a given date, grouped by category. |
| ``hai memory set`` | ``writes-memory`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Append a user_memory entry (goal / preference / constraint / context). Append-only — replace by archiving the old row and setting a new one. |
| ``hai planned-session-types`` | ``read-only`` | ``yes`` | ``default`` | yes | ``OK`` | Emit the canonical planned_session_type vocabulary (token + classifier_substring + description per entry). Source registry: core/intake/planned_session_vocabulary.py. |
| ``hai propose`` | ``writes-state`` | ``yes-with-replace`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Validate a DomainProposal and append it to proposal_log. One of the three determinism boundaries the runtime enforces. |
| ``hai pull`` | ``writes-sync-log`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT``, ``TRANSIENT`` | Acquire evidence for a date and emit cleaned evidence JSON. Source resolution (v0.1.6): explicit `--source` > legacy `--live` (= garmin_live) > intervals.icu when credentials are configured > csv fixture fallback. Garmin live is best-effort (rate-limited); intervals.icu is the supported live source. Writes a sync_run_log row; does not touch the main state tables. |
| ``hai research search`` | ``read-only`` | ``yes`` | ``default`` | yes | ``OK`` | Retrieve sources for one allowlisted research topic. Mirrors core.research.retrieve but exposes only the topic-token interface — the privacy-violation booleans are not configurable. Read-only; no network. |
| ``hai research topics`` | ``read-only`` | ``yes`` | ``default`` | yes | ``OK`` | List the allowlisted topics the bounded retrieval surface recognises. Read-only. |
| ``hai review record`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Record a review_outcome against a review_event. Carries the migration-010 enrichment columns (completed, intensity_delta, pre/post_energy, disagreed_firing_ids). |
| ``hai review schedule`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Persist a pending review_event for a recommendation (used to schedule the next-day review question). |
| ``hai review summary`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Summarize review_outcome counts (followed / not-followed, per-domain tallies). |
| ``hai setup-skills`` | ``writes-skills-dir`` | ``yes`` | ``default`` | yes | ``OK`` | Copy the packaged skills/ tree to ~/.claude/skills/ so Claude Code discovers them. |
| ``hai state init`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK`` | Create the local SQLite state DB and apply all pending migrations. Idempotent — safe to call repeatedly. |
| ``hai state migrate`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Apply any pending schema migrations to an already-initialized state DB. |
| ``hai state read`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Read a per-domain accepted-state row for a given date. |
| ``hai state reproject`` | ``writes-state`` | ``yes`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Rebuild the accepted_*_state_daily tables from the raw evidence JSONL. Deterministic modulo projection timestamps — content/keys/links replay identically across runs, but projected_at / corrected_at columns reflect the wall-clock of the rebuild. Safe to re-run. |
| ``hai state snapshot`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Emit the cross-domain state snapshot the synthesis / skills layer consumes for a (for_date, user_id) pair. |
| ``hai stats`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT`` | Summarise sync_run_log (last pull per source) + runtime_event_log (recent commands, daily streak) from the user's local DB. With --outcomes, emits the code-owned review-outcome summary (W48) instead. No telemetry leaves the device. |
| ``hai synthesize`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | yes | ``OK``, ``USER_INPUT``, ``INTERNAL`` | Run synthesis end-to-end inside one atomic SQLite transaction: daily_plan + x_rule_firings + planned_recommendation + recommendation_log. --supersede versions the plan instead of replacing it. |
| ``hai target archive`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Archive a W50 target row (status='archived'). Marked NOT agent-safe: archiving an active or proposed row IS user-state deactivation per AGENTS.md W57. Agents that proposed the row must NOT auto-archive it; only an explicit user invocation may run this command. |
| ``hai target commit`` | ``writes-state`` | ``yes-with-supersede`` | ``default`` | no | ``OK``, ``USER_INPUT`` | Promote a proposed target row to active. Marked NOT agent-safe: agents that proposed the row must NOT auto-promote it; only an explicit user invocation may run this command. |
| ``hai target list`` | ``read-only`` | ``n/a`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | List target rows from the W50 ledger; default-active. |
| ``hai target set`` | ``writes-state`` | ``no`` | ``default`` | yes | ``OK``, ``USER_INPUT`` | Insert a wellness target into the W50 target ledger. Wellness support, not a medical prescription. |
| ``hai today`` | ``read-only`` | ``n/a`` | ``opt-in`` | yes | ``OK``, ``USER_INPUT`` | Render today's canonical plan in plain language — the non-agent-mediated user surface. Read-only. |
