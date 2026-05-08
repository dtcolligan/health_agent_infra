# D2 — Intake write-path contract

- Author: Claude (Opus 4.7)
- Status: **Draft pending Dom's review**
- Gates: Workstream A (intake fixes and recovery-readiness SKILL.md correction).

---

## Problem

No user can predict, from `hai --help` alone, whether a given `hai intake <X>` call will move tomorrow's plan. Six commands have six different behaviors:

| Command | Lands where today | Read by classifier? |
|---|---|---|
| `hai intake readiness` | **stdout only** — emits JSON for agent composition with `hai pull --manual-readiness-json` | Indirectly, if piped through pull |
| `hai intake note` | `context_note` table | **No** |
| `hai intake gym` | `gym_session` + `gym_set` | Yes (strength domain) |
| `hai intake nutrition` | `nutrition_intake_raw` | Yes (nutrition domain) |
| `hai intake stress` | `stress_manual_raw` | Yes (stress domain) |
| `hai intake exercise` | `exercise_taxonomy` (metadata, not a session) | No (taxonomy is ref data) |

Additionally:

- `hai intake readiness` lacks `--user-id`, `--db-path`, `--base-dir` flags that every other intake command has. Interface asymmetry.
- Recovery-readiness SKILL.md instructs `hai writeback` (legacy recovery-only direct path) while every other domain skill instructs `hai propose`. Skills are out of sync with the agent-operable contract.
- Notes are write-only from the classifier's perspective, but they share the `hai intake …` namespace with commands that do feed classifiers. A user logging "trained legs yesterday" as a note reasonably expects the strength classifier to pick up the recency signal. It doesn't.

These aren't bugs in isolation. They're a missing contract.

---

## Decision

**Every `hai intake <X>` command persists to a named state table.** No stdout-composer exceptions.

**Notes are renamed `hai journal add`** to signal their write-only status. The `context_note` table is kept (it's useful for user free-text history), but it's unambiguous: journal entries are *for the user*, not inputs to the classifier graph. A documentation contract and the command name make this obvious.

**Recovery-readiness SKILL.md is rewritten** to match the other five domain skills — emit a `DomainProposal`, call `hai propose --domain recovery`. The legacy `hai writeback` path is removed from v0.1.4 entirely (see §Removal plan).

**Intake command flag surfaces are unified.** Every `hai intake …` command supports `--user-id`, `--db-path`, `--base-dir`, `--as-of`, `--ingest-actor` with consistent defaults.

---

## The single intake contract

An intake command:

1. Takes structured input via CLI flags (typed) **or** `--<entity>-json` bulk (for scripted/agent use).
2. Validates the payload against a domain-specific schema at `src/health_agent_infra/core/intake/<domain>_schema.py`.
3. Appends a row to `<base_dir>/<entity>.jsonl` (JSONL audit, authoritative).
4. Projects the row into exactly one named state table (best-effort, logs stderr warning if DB absent).
5. Is idempotent on `submission_id` (or the appropriate natural key per domain).
6. Emits the written row as JSON on stdout (exit code OK) or a structured error on stderr (exit code USER_INPUT / TRANSIENT).

Every intake matches this shape. No exceptions.

---

## Per-domain landing tables

| Command | Landing table | Primary classifier consumer |
|---|---|---|
| `hai intake readiness` | **new table `manual_readiness_raw`** (migration 017) | recovery + running |
| `hai intake gym` | `gym_session` + `gym_set` (unchanged) | strength |
| `hai intake nutrition` | `nutrition_intake_raw` (unchanged) | nutrition |
| `hai intake stress` | `stress_manual_raw` (unchanged) | stress |
| `hai intake exercise` | `exercise_taxonomy` (unchanged) | strength (name resolution) |
| `hai journal add` (renamed from `intake note`) | `context_note` (unchanged) | **none** — user-facing history only |

### New table: `manual_readiness_raw`

```sql
CREATE TABLE manual_readiness_raw (
    submission_id       TEXT    PRIMARY KEY,
    user_id             TEXT    NOT NULL,
    as_of_date          TEXT    NOT NULL,
    soreness            TEXT    NOT NULL CHECK (soreness IN ('low','moderate','high')),
    energy              TEXT    NOT NULL CHECK (energy IN ('low','moderate','high')),
    planned_session_type TEXT   NOT NULL,
    active_goal         TEXT,
    source              TEXT    NOT NULL,
    ingest_actor        TEXT    NOT NULL,
    ingested_at         TEXT    NOT NULL,
    supersedes_submission_id TEXT
);

CREATE INDEX idx_manual_readiness_raw_date
    ON manual_readiness_raw(user_id, as_of_date DESC);
```

This parallels the existing `stress_manual_raw` and `nutrition_intake_raw` shapes. On re-submission the same day, the new row supersedes the prior via `supersedes_submission_id`.

### `hai pull` adapter integration

`hai pull` gains an automatic same-day readiness check: if `manual_readiness_raw` has a row for `(user_id, as_of_date)`, it is included in the cleaned-evidence output under the same `manual_readiness` key that `--manual-readiness-json <path>` uses today. The `--manual-readiness-json` flag is retained as an override (explicit-path wins over DB row).

This preserves the agent-composer pattern for non-state-DB flows while removing the "why didn't my intake do anything" footgun for state-DB users.

---

## Flag-surface unification

Every `hai intake …` command (including the renamed `hai journal add`) supports:

- `--as-of <ISO-8601>` — civil date the intake pertains to (default: today UTC).
- `--user-id <id>` — user this intake attaches to (default: `u_local_1`).
- `--db-path <path>` — same semantics as other state-writing commands.
- `--base-dir <path>` — required for commands that append JSONL audit (everything except readiness, which has no JSONL today; readiness gains JSONL in this round to match).
- `--ingest-actor {hai_cli_direct,claude_agent_v1}` — transport identity, default `hai_cli_direct`.

`hai intake readiness` gains all five. A contract test in Workstream E asserts every intake command's argparse declares these flags with identical types and defaults.

---

## Skill-contract reconciliation

Every domain's SKILL.md is rewritten against a single template:

```markdown
## Output

Emit a `<Domain>Proposal` JSON and call:

    hai propose --domain <domain> --proposal-json <path> --base-dir <root>

The propose tool validates the shape and appends to `proposal_log`;
it is your determinism check.

`proposal_id` = `prop_<for_date>_<user_id>_<domain>_01` on first write;
revisions get `_02`, `_03` (see D1). Use `hai propose --replace` when
revising the same day's proposal with new skill output.
```

This replaces the current recovery-readiness §7 and §Output which instruct `hai writeback`. A CI check (part of Workstream E) parses every SKILL.md and asserts its `allowed-tools` and Output section reference only commands currently in the capabilities manifest.

---

## Removal plan: `hai writeback`

`hai writeback` was the recovery-only legacy direct path that predated the agent-operable contract. It duplicates what `hai propose --domain recovery` + `hai synthesize` now does. Keeping it invites future drift.

**Remove `hai writeback` entirely in v0.1.4.** Migration steps:

1. Mark `hai writeback` as deprecated in its `--help` output in `0.1.3.devN` tags on main.
2. Rewrite recovery-readiness SKILL.md to use `hai propose` (part of this workstream).
3. Audit every test in `safety/tests/` that invokes `hai writeback`; migrate to `hai propose` + `hai synthesize`.
4. Remove the command, handler, and writeback module.
5. Release notes: "Removed `hai writeback` (legacy recovery-only direct path); use `hai propose --domain recovery` + `hai synthesize`."

Justification for removal rather than keep-and-deprecate: this is a pre-1.0 project; no external users depend on `hai writeback`; keeping it dilutes the agent-operable-contract story.

---

## Migration plan

- **017** creates `manual_readiness_raw` table. Backfill: none (first-time table).
- **No data migration** for the rename `context_note` → journal. The CLI subcommand is what changes; the table stays `context_note`. The table retains this name because (a) it's widely referenced in code, (b) `context_note` accurately describes the row's role in state, and (c) only the user-facing command is what confuses. The renamed command `hai journal add` writes to `context_note` under the hood.
- **Behavior change** in `hai pull` to read `manual_readiness_raw` for the given date. Implemented in `src/health_agent_infra/core/pull/orchestrator.py` (or equivalent).

---

## Code touch-points

- `src/health_agent_infra/cli.py`:
  - `cmd_intake_readiness`: rewritten to persist to DB, append JSONL, emit stdout as an echo (still composable).
  - `cmd_intake_note` renamed internally to `cmd_journal_add`; the `hai intake note` alias is kept for `0.1.3.devN` and removed in v0.1.4 release; `hai journal add` is the new canonical.
  - Every `intake` subparser's flag set aligned.
- `src/health_agent_infra/core/intake/`:
  - new `readiness_schema.py` + `readiness_projector.py`.
  - existing gym/nutrition/stress/note modules get a uniform `--user-id` / `--db-path` flag handler (likely a shared helper).
- `src/health_agent_infra/core/pull/` (adapter orchestrator):
  - Read `manual_readiness_raw` for `(user_id, as_of_date)`; include in cleaned-evidence output when present.
  - `--manual-readiness-json <path>` override still wins if passed.
- `src/health_agent_infra/skills/recovery-readiness/SKILL.md`: rewritten.
- `src/health_agent_infra/skills/*/SKILL.md`: standardized §Output section template.
- Migration `017_manual_readiness_raw.sql`: new.

---

## Test coverage (acceptance criteria)

1. **Unit: readiness persists and round-trips.** `hai intake readiness --soreness low --energy high …` → DB has a row → next `hai pull` picks it up automatically → cleaned evidence contains the readiness block.
2. **Unit: --manual-readiness-json overrides DB row.** Same as above, but pass `--manual-readiness-json <different-path>`. Assert the file path wins.
3. **Unit: readiness supersedes on same-day re-submission.** Intake twice. Assert latest row has `supersedes_submission_id` pointed at the first.
4. **Unit: journal rename.** `hai journal add --text "…"` works and lands in `context_note`. `hai intake note` in 0.1.3.devN still works (deprecation alias). `hai intake note` in v0.1.4 release is removed.
5. **Contract: every intake has unified flags.** Test walks argparse for every `hai intake <X>` and `hai journal add`, asserts `--user-id`, `--db-path`, `--base-dir`, `--as-of`, `--ingest-actor` are all present with consistent types.
6. **Contract: every SKILL.md's allowed-tools resolves.** Test parses each SKILL.md, asserts every `Bash(hai …)` entry is a command currently in `hai capabilities --json`. Would have caught the recovery-readiness drift.
7. **Contract: recovery-readiness SKILL.md instructs `hai propose`.** Sanity test: grep SKILL.md for `hai writeback`, assert zero matches; grep for `hai propose`, assert non-zero.
8. **Removal: `hai writeback` absent in v0.1.4.** Test asserts the subcommand does not appear in `hai capabilities --json` for the release build.
9. **E2E: readiness → plan.** Part of Workstream E. Intake readiness; run `hai daily`; assert recovery classifier's classified_state reflects the intake (soreness_band=low, planned_session_type present).

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Renaming `hai intake note` breaks existing scripts / muscle memory | Keep the alias through `0.1.3.devN`; remove only at v0.1.4 release. Deprecation warning in help text. Release notes call it out. |
| `manual_readiness_raw` schema choice is wrong and needs migration in v0.1.5 | Keep the columns minimal and tightly matched to the existing `--manual-readiness-json` shape; if we need more fields later, additive migrations are cheap. |
| `hai pull` auto-reading readiness changes the semantics of "what a pull does" | Add a line to `hai pull --help` explaining the auto-read; feature this in release notes. The behavior is strictly additive (no pulls that previously succeeded will fail). |
| Removing `hai writeback` breaks something in the test fixtures | Part of acceptance criterion #8; test migration is part of the workstream. |

---

## Explicit non-goals

- **Not making context_notes classifier-readable.** Notes stay write-only from the classifier graph's perspective. If users want recency signals to affect recommendations, they use the typed intakes. This preserves the "structured input vs. free-text memory" distinction cleanly.
- **Not adding per-domain "partial" intake modes.** `hai intake gym` still requires structured set/rep data; there's no "I trained legs, roughly" shortcut. Partial-structured intake is a separate feature design for v0.1.5+.
- **Not changing `hai intake exercise`'s role.** It remains a taxonomy-writer, not a session-writer. Documented explicitly.
- **Not addressing `hai memory set` / `user_memory`** in this doc. That's a separate surface (user-level goals/preferences, not per-day intake) and its contract is already coherent.
