# D1 — Re-author and supersede semantics

- Author: Claude (Opus 4.7)
- Ratified by: Dom Colligan, 2026-04-23
- Decision: **Revise, not append.** Proposals support in-place revision with a linked version chain. Plans already use supersede; the decision is to align proposal-level and plan-level mutation around the same mental model.
- Gates: Workstream A.

---

## Problem

The 2026-04-23 end-to-end session surfaced five distinct bugs sharing one root cause: the system's mutation model is underspecified. Concretely:

1. **`project_proposal` silently skips on duplicate `proposal_id`** (`src/health_agent_infra/core/state/projector.py:1501-1541`), returns False, does not update. Agents re-running skills with new content get the old content persisted.
2. **`hai explain --for-date` returns the oldest plan** in a supersede chain instead of the canonical leaf.
3. **Supersede relinks `proposal_log.daily_plan_id`** to the new plan, orphaning the old plan's proposals — the explain query uses the FK instead of the plan's `proposal_ids_json` array.
4. **Supersede lineage is ambiguous** for chains longer than 2: v1 → v2 → v3 produces `v3.superseded_prior = v1`, not v2.
5. **Orphaned review outcomes**: `review_outcome` rows recorded against a superseded recommendation become silent orphans when the plan supersedes.

Each fix individually is small. Shipping them piecemeal without a unified model invites new bugs in the same class.

---

## Decision

**Every mutable entity in the audit chain supports revision semantics:**

- A **revision chain** is a linked list of rows with the same logical key (for proposals: `(for_date, user_id, domain)`; for plans: `(for_date, user_id)`).
- Exactly one row per chain is the **canonical leaf** — the row agents and users should treat as "current."
- Every non-leaf row carries a `superseded_by_<entity>_id` pointer to the next link in the chain, plus a `superseded_at` timestamp.
- Re-authoring is a two-step atomic operation: insert new leaf, update prior leaf's `superseded_by_*` pointer + `superseded_at`.
- Queries for "today's state" filter on `superseded_by_* IS NULL`; queries for "audit history" traverse the chain explicitly.

This replaces the current `project_proposal` silent-skip behavior with an explicit, auditable revision.

---

## Schema changes

### `proposal_log` — migration 013

```sql
ALTER TABLE proposal_log ADD COLUMN revision INTEGER NOT NULL DEFAULT 1;
ALTER TABLE proposal_log ADD COLUMN superseded_by_proposal_id TEXT
    REFERENCES proposal_log(proposal_id);
ALTER TABLE proposal_log ADD COLUMN superseded_at TEXT;

CREATE INDEX idx_proposal_log_canonical
    ON proposal_log(for_date, user_id, domain, superseded_by_proposal_id);
```

### `daily_plan` — migration 014 (reconciliation)

```sql
ALTER TABLE daily_plan ADD COLUMN superseded_by_plan_id TEXT;
ALTER TABLE daily_plan ADD COLUMN superseded_at TEXT;
-- superseded_prior is renamed superseded_plan_id for symmetry and kept
-- as the back-pointer (leaf → chain toward origin). superseded_by_plan_id
-- is the forward pointer (non-leaf → leaf).

CREATE INDEX idx_daily_plan_canonical
    ON daily_plan(for_date, user_id, superseded_by_plan_id);
```

### `recommendation_log` — migration 015

Recommendations are re-generated on every synthesis, so they do not need full revision chains — but the superseded-plan orphan problem (bug #15) means we need to know which plan they belong to and whether that plan is canonical.

```sql
-- No new columns; we derive canonicality by joining
-- recommendation_log.daily_plan_id → daily_plan.superseded_by_plan_id IS NULL.
-- Contract test asserts this join is always valid.
```

### `review_outcome` — migration 016

On write, if the target recommendation's plan has been superseded, the outcome is **re-linked** to the canonical leaf plan's matching recommendation (same domain, same for_date). If the canonical leaf does not have a matching-domain recommendation (rare — supersede only adds, doesn't subtract), write fails loudly with exit code `USER_INPUT`.

```sql
-- No schema change; behavioral change in core/writeback/review.py
-- + a contract test asserting no outcome points to a superseded rec
-- after supersede.
```

---

## Proposal ID format

Unchanged for the first revision: `prop_<for_date>_<user_id>_<domain>_01`.

Revisions append a revision suffix: `prop_2026-04-23_u_local_1_recovery_02`, `_03`, …

The `_01` suffix is retained as the original-revision marker for backward compatibility with existing test fixtures and audit history. The numeric suffix **is** the revision — there's no ambiguity between "first proposal" and "revision 1."

**Rationale for keeping the suffix human-readable rather than e.g. UUID:** consistent with current IDs, audit trail is grep-able, matches the plan supersede `_v<N>` convention.

---

## `hai propose` behavior changes

New flag: `--replace`. Behavior matrix:

| Existing canonical row for `(for_date, user_id, domain)`? | `--replace` flag? | Action |
|---|---|---|
| No | (any) | INSERT as revision=1, proposal_id = `_01`. |
| Yes | Absent | **Reject**: exit code `USER_INPUT`, stderr: "proposal already exists at revision N for (date, domain); use --replace to revise." |
| Yes | Present | **Two-step atomic transaction:** INSERT new row with revision = leaf.revision + 1, proposal_id = `_<N+1:02d>`, then UPDATE old leaf SET superseded_by_proposal_id = new.proposal_id, superseded_at = now(). Both inside a single BEGIN/COMMIT. |

**Idempotency under identical replay:** if `--replace` is passed but the new payload is byte-identical to the current leaf's payload (after JSON canonicalization), treat as no-op and return the existing leaf. This prevents revision-chain pollution from benign reruns.

---

## `hai explain` behavior changes

- **Default (no flag):** returns the canonical leaf for `(for_date, user_id)`. For proposals, uses canonical leaves per domain. For review outcomes, follows re-link pointers to current.
- **`--plan-version first`:** returns the original (chain-head) plan.
- **`--plan-version all`:** returns the full chain as an ordered list.
- **`--daily-plan-id <explicit>`:** unchanged — returns that specific plan.

All proposal-reading queries switch from `WHERE daily_plan_id = ?` to `WHERE superseded_by_proposal_id IS NULL AND for_date = ?` for "current" and to explicit chain traversal for history.

---

## `hai synthesize --supersede` behavior changes

- `superseded_plan_id` on the new plan points to the **canonical leaf at time of synthesis** (not the chain head). This fixes bug #14.
- Old leaf's `superseded_by_plan_id` is set to the new plan; old leaf's `superseded_at` is set to now.
- Proposals are **not relinked**. The new plan's `proposal_ids_json` and `recommendation_ids_json` store the proposal/rec IDs; the proposal rows' `daily_plan_id` stays pointed at whichever plan first used them. This fixes bug #3.
- `hai explain` on a superseded plan reads proposals via the stored `proposal_ids_json` array, not via the FK. This is the "one plan per proposal is wrong" fix.

---

## `hai review record` behavior changes

On write, before INSERT:

1. Resolve `review_event.recommendation_id` → `recommendation_log` row.
2. Follow `recommendation_log.daily_plan_id` → `daily_plan` row.
3. If the plan has `superseded_by_plan_id IS NOT NULL`:
   - Resolve the canonical-leaf plan.
   - Find a recommendation in the leaf with the same `domain` for the same `for_date`.
   - If found: **re-link** the outcome to the leaf's recommendation_id, log an `ingest_note` field explaining the re-link.
   - If not found: exit `USER_INPUT`, stderr: "recommendation is in a superseded plan and the canonical leaf has no matching domain; refusing to create an orphaned outcome."

Orphans are structurally impossible after this.

---

## Migration plan

- **013** adds `revision`, `superseded_by_proposal_id`, `superseded_at` to `proposal_log`. Backfills existing rows: `revision=1`, both nullable columns NULL (all existing proposals become canonical leaves).
- **014** adds `superseded_by_plan_id`, `superseded_at` to `daily_plan`. Backfills: for each `(for_date, user_id)` group, the row with no other row pointing at it is the leaf (superseded_by NULL); if a chain exists via current `superseded_prior`, walk it forward and set `superseded_by_plan_id` on each non-leaf.
- **015** and **016** are behavioral-only; no SQL.
- **Forward-only migrations.** No reverse paths in code — users on v0.1.2 can't downgrade from v0.1.4 state. Documented in release notes. Backup-before-upgrade instruction prominent.

---

## Code touch-points

- `src/health_agent_infra/core/state/projector.py`:
  - `project_proposal`: rewritten to implement the `--replace` behavior matrix.
  - `read_proposals_for_plan_key`: new signature adds `include_superseded: bool = False` parameter.
  - New helper `resolve_canonical_proposal(conn, for_date, user_id, domain)`.
  - New helper `resolve_canonical_plan(conn, for_date, user_id)`.
- `src/health_agent_infra/cli.py`:
  - `cmd_propose`: wire up `--replace`.
  - `cmd_explain`: default resolves canonical leaf; new `--plan-version` flag.
  - `cmd_synthesize`: `--supersede` targets canonical leaf.
  - `cmd_review_record`: re-link logic.
- `src/health_agent_infra/core/synthesis.py`: supersede targets canonical leaf, fixes lineage bug.
- `src/health_agent_infra/core/writeback/proposal.py`: validator unchanged.
- `src/health_agent_infra/core/writeback/review.py`: re-link logic.
- `src/health_agent_infra/core/state/migrations/013_proposal_revisions.sql`: new.
- `src/health_agent_infra/core/state/migrations/014_plan_supersede_forward_links.sql`: new.

---

## Test coverage (acceptance criteria)

All implemented as part of Workstream A.

1. **Unit: revision insert.** Fresh proposal_log. `hai propose` creates revision=1 leaf. Assert row shape.
2. **Unit: reject without --replace.** Existing leaf. `hai propose` without --replace. Assert exit USER_INPUT, stderr clear.
3. **Unit: replace atomicity.** Existing leaf. `hai propose --replace` with new payload. Assert new leaf at revision=2, old leaf `superseded_by_proposal_id` set, both writes in single transaction (verify via rollback-on-second-write failure injection).
4. **Unit: identical-payload idempotency.** `hai propose --replace` with byte-identical payload to current leaf. Assert no-op, return existing leaf.
5. **Unit: supersede lineage.** v1 synthesized; `daily` rerun with `--supersede` creates v2 with `superseded_plan_id = v1`. Third rerun creates v3 with `superseded_plan_id = v2`. Chain: v1.superseded_by → v2 → v3.superseded_by = NULL.
6. **Unit: explain on canonical leaf.** After v1 → v2 → v3 chain, `hai explain --for-date <d>` returns v3. `--plan-version first` returns v1. `--plan-version all` returns all three.
7. **Unit: explain resolves proposals on superseded plan.** v1 plan has proposals `p1..p6`. Supersede creates v2. `hai explain plan_v1` still shows all 6 proposals (via `proposal_ids_json`, not FK).
8. **Unit: review outcome re-link.** Record outcome on plan v1 rec. Supersede to v2. Record new outcome referencing the v1 rec. Assert outcome is re-linked to v2's matching-domain rec; `ingest_note` explains.
9. **Unit: review outcome refuse.** Same as #8 but v2 is constructed without the relevant domain (synthetic edge case). Assert `hai review record` exits USER_INPUT with clear message.
10. **Contract: audit-chain integrity.** After any synthesis sequence, assert: (a) every `proposal_ids_json` entry resolves in `proposal_log`; (b) every `recommendation_log.daily_plan_id` resolves in `daily_plan`; (c) every `review_outcome.recommendation_id` points to a canonical-leaf recommendation OR to a re-linked one with `ingest_note`.
11. **Migration: 013+014 forward.** Seed v0.1.3-era DB; apply migrations; assert all existing rows are canonical leaves; assert new columns exist.
12. **E2E: re-author journey.** Workstream E reference scenario. Post proposals → synthesize v1 → intake readiness → propose --replace for recovery → synthesize --supersede → v2 committed → `hai today` renders revised recovery rec → review outcome on v2 records correctly.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Migration 013 backfill is wrong for existing chains | The only existing chain-like data is superseded plans (added mid-development). Write a pre-migration audit script that reports the current chain state; validate manually before running in anger. |
| `--replace` footgun: agent accidentally overwrites skill output with a revision that loses information | The `identical-payload idempotency` rule catches benign cases. For true edits, revision history is fully recoverable via `--plan-version all` / chain traversal. Document the pattern prominently. |
| Performance of canonical-leaf queries on long chains | Index `idx_proposal_log_canonical` covers the common path. For audit history, chain depth is naturally bounded (a handful of revisions per domain per day). |
| Forward-only migration blocks user rollback | Documented loudly in release notes. Backup instruction in upgrade path. Acceptable trade-off given audit-integrity gain. |

---

## Explicit non-goals

- **Not implementing revision for every table.** Notes and memory tables stay append-only-with-archive (existing behavior). Revision chains are only for entities in the plan/proposal/recommendation audit triangle.
- **Not implementing a UI for revision history.** `hai explain --plan-version all` is sufficient for now; richer display is v0.1.5+.
- **Not implementing concurrent-writer lock escalation.** Single-user local DB; revision reads/writes are serialized through SQLite's WAL mode; no MVCC needed.
- **Not changing `hai writeback` (legacy recovery-only direct path).** It's being removed in Workstream B as part of the recovery-readiness SKILL.md fix; no revision semantics to add.
