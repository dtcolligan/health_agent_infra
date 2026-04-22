# Memory Model

What Health Agent Infra remembers on disk, who writes each layer, what
it is used for, and what is deliberately NOT remembered.

This doc pairs with
[`personal_health_agent_positioning.md`](personal_health_agent_positioning.md)
(role map) and [`query_taxonomy.md`](query_taxonomy.md) (the questions
the runtime is built to answer). The one-line frame:

> *Memory here is explicit, local, and projector-authored. Nothing
> important lives only in a chat transcript, and nothing quietly retunes
> the runtime behind the user's back.*

[`state_model_v1.md`](state_model_v1.md) is the authoritative
table-by-table schema. This doc is the layered view.

## 1. The four shipped memory layers

The runtime writes four distinct kinds of memory, each with a different
author, a different idempotency contract, and a different consumer.

```
┌──────────────────────────────────────────────────────────────────────┐
│  1. Raw evidence memory    — append-only; verbatim inputs            │
│  2. Accepted state memory  — projector-authored; idempotent per day  │
│  3. Decision memory        — proposal / planned / plan / firing /     │
│                              recommendation (three-state audit)       │
│  4. Outcome memory         — scheduled + captured review records     │
└──────────────────────────────────────────────────────────────────────┘
```

Plus two kinds of memory that are explicitly *not* shipped yet, covered
in §2:

- explicit user memory (planned, roadmap Phase D);
- adaptive memory (deliberately absent).

### 1.1 Raw evidence memory

**What it holds.** Verbatim inputs to the system, before any
interpretation. Two forms:

- **Raw tables in SQLite.** Per-domain raw and source tables populated
  by pull + intake:
  - `source_daily_garmin` — one row per Garmin pull day.
  - `running_session` — Garmin-derived running sessions.
  - `gym_session`, `gym_set` — user-authored strength sessions and
    per-set detail (via `hai intake gym`).
  - `nutrition_intake_raw` — daily macros entries (via
    `hai intake nutrition`; macros-only in v1).
  - `stress_manual_raw` — user-authored stress scores (via
    `hai intake stress`).
  - `context_note` — user-authored notes (via `hai intake note`).
  - `exercise_taxonomy` — canonical lift taxonomy (seeded from
    `taxonomy_seed.csv`; extendable via `hai intake exercise`).
- **Per-domain JSONL audit files.** Append-only logs under
  `<base_dir>/<domain>_proposals.jsonl` (default
  `~/.local/share/hai/`), plus the recovery-only writeback audit at
  the same base. These carry the full validated payload that passed
  each determinism boundary.

**Who writes it.** `hai pull`, each `hai intake *` subcommand, and the
JSONL writers inside `core/writeback/*.py`. A writer never edits a prior
row — raw evidence is append-only; corrections happen by writing a
later row that the projector then supersedes.

**Who reads it.** The projectors read the SQLite raw tables to derive
accepted state; `hai clean` reads pull output to produce
`CleanedEvidence + RawSummary`. Audit JSONL is not read by the runtime
during normal operation — it exists for human / agent audit.

**Why it stays separate from accepted state.** Raw evidence can be
noisy, late-arriving, or contradictory. Keeping it separate lets the
projector decide deterministically which raw inputs to trust and lets
`hai state reproject` rebuild accepted state from raw evidence without
losing history.

### 1.2 Accepted state memory

**What it holds.** The canonical, projector-derived, day-keyed state
the runtime reasons over. One table per domain:

- `accepted_recovery_state_daily`
- `accepted_running_state_daily`
- `accepted_sleep_state_daily`
- `accepted_stress_state_daily`
- `accepted_resistance_training_state_daily` (the strength domain)
- `accepted_nutrition_state_daily`
  (`derivation_path = 'daily_macros'` in v1;
  `micronutrient_coverage = 'unavailable_at_source'`).

Each row is keyed on `(for_date, user_id)` plus domain-specific
context and is idempotent per day: running the projector twice over the
same raw evidence produces the same row.

**Who writes it.** The per-domain projectors under
`core/state/projectors/<domain>.py`, orchestrated by
`core/state/projector.py` and triggered via
`hai state reproject`.

**Who reads it.** `hai state snapshot` reads every accepted table into
a cross-domain bundle. `domains/<d>/classify.py` and
`domains/<d>/policy.py` operate over snapshot blocks (evidence +
raw_summary). The synthesis layer reads the full bundle.

**Why it exists.** This is what makes the agent resumable across days
without depending on chat state. The morning of day `N+1`, the runtime
can compose a full snapshot — and therefore reproduce its reasoning —
from local tables alone.

### 1.3 Decision memory

**What it holds.** What the agent proposed, what the runtime's
pre-X-rule aggregate looked like, what synthesis changed, and what
was finally committed. Together these form the **three-state audit
chain** (planned → adapted → performed) that `hai explain` renders
from persisted rows alone.

- `proposal_log` — every `DomainProposal` that passed `hai propose`
  validation. Keyed on `(for_date, user_id, domain)`. This is the
  per-domain **planned** intent.
- `planned_recommendation` — the aggregate pre-X-rule bundle, one row
  per (daily_plan_id, domain), mirroring the `recommendation_log`
  shape. Captured inside the synthesis transaction **before** Phase A
  mutations run, so the bundle can be compared against the adapted
  outcome without reconstruction. FKs to both `daily_plan` and
  `proposal_log` make the audit chain fully walkable. Added in
  migration 011 (M8 Phase 1). Legacy plans committed before 011 have
  no paired row and degrade cleanly to the two-state view.
- `daily_plan` — the synthesis row, keyed on `(for_date, user_id)`,
  with a `superseded_by` pointer for `--supersede` versioning.
- `x_rule_firing` — one row per X-rule firing (Phase A and Phase B),
  carrying rule id, tier, target domain, inputs read, mutation
  applied, and `orphan` flag. Each firing's rule id maps (via
  `X_RULE_PUBLIC_NAMES` + `X_RULE_DESCRIPTIONS`) to a stable slug and
  a one-sentence `human_explanation` surfaced by `hai explain`.
- `recommendation_log` — the final per-domain `BoundedRecommendation`
  rows (the **adapted** aggregate). Linked to the `daily_plan` row
  for the day. Supports `supersedes` / `superseded_by` pointers.

All five are written inside a single SQLite transaction by
`core/synthesis.py :: run_synthesis`. If any step fails, the entire
transaction rolls back; no partial plan reaches state.

**Who writes it.** `hai propose` writes `proposal_log`. `hai
synthesize` writes `daily_plan`, `x_rule_firing`, and (for every domain
except legacy recovery-only writeback) `recommendation_log`. `hai
writeback` writes `recommendation_log` only for the recovery-only
legacy direct path.

**Who reads it.** `hai explain` (shipped in Phase C) reads this layer
to reconstruct why a given plan exists; direct SQLite reads remain
available. See [`explainability.md`](explainability.md) for the
bundle shape and [`query_taxonomy.md`](query_taxonomy.md) §2.3 for
the question class it answers.

**Why it exists.** This is the project's strongest differentiator. The
runtime does not just tell the user what to do — it retains an
auditable chain that any reader can walk: accepted state →
proposal → firing → mutation → final recommendation.

### 1.4 Outcome memory

**What it holds.** What happened after a recommendation went out.

- `review_event` — one row per scheduled review (typically one per
  recommendation), with due date and domain.
- `review_outcome` — one row per captured outcome, carrying the
  review verdict (`completed` / `modified` / `skipped` / etc.) and
  freeform notes.

**Who writes it.** `hai review schedule` writes `review_event`; `hai
review record` writes `review_outcome`.

**Who reads it.** `hai review summary` rolls outcomes up per domain.
`hai explain` (Phase C) includes review linkage when present — see
[`explainability.md`](explainability.md).

**Why it exists.** Outcome memory closes the audit loop: a later
reader can see not only what was recommended and why, but also how it
landed.

**What it deliberately does not do.** Outcome rows never feed back into
thresholds, classifiers, policy, or X-rules. See §2.2.

## 2. Memory that is not shipped yet — and memory that will not be

### 2.1 Explicit user memory (shipped, Phase D)

**What it holds.** Goals, preferences, constraints, and durable
context notes as inspectable local SQLite state. Migration 007
introduces the `user_memory` table keyed on `memory_id`, carrying:

- `category` — one of `goal | preference | constraint | context`;
- `value` — the durable content;
- `key` (optional) — a short handle within the category (e.g.
  `primary_goal`, `injury_left_knee`);
- `domain` (optional) — scoping to one of the six domains, or global;
- `created_at` — when the operator recorded the memory;
- `archived_at` — soft-delete stamp; NULL while active.

**Who writes it.** `hai memory set` writes one row per invocation; no
implicit updates happen. To replace a preference the operator
archives the old row via `hai memory archive --memory-id <id>` and
`hai memory set`s the replacement — every change lands as a distinct
row + archive timestamp, visible to `hai memory list
--include-archived`.

**Who reads it.** The core module
`src/health_agent_infra/core/memory/` exposes `build_user_memory_bundle`
which `hai state snapshot` and `hai explain` both call to surface an
active-at-as_of bundle under their new top-level `user_memory` key.
Skills may consume the same bundle via the snapshot.

**Time-axis semantics.** The snapshot + explain readers ask for
entries that were active at the snapshot's `as_of_date` or the plan's
`for_date`: `created_at <= as_of` AND (`archived_at IS NULL` OR
`archived_at > as_of`). This is what makes `hai explain` for
yesterday's plan reflect the memory that was active then, not the
current state.

**What it still does not do.** It does not silently retune
thresholds, classifiers, policy, or X-rules. Explicit user memory is
bounded read-only context for snapshot / explain / skills — it is not
an adaptation channel. See §2.2.

See
[`reporting/plans/post_v0_1_roadmap.md`](../plans/post_v0_1_roadmap.md)
§5 Phase D for the acceptance criteria.

### 2.2 Absent adaptive memory (deliberately)

The runtime does not, and in this cycle will not:

- feed `review_outcome` rows back into per-domain confidence
  calibration;
- tune any X-rule threshold or R-rule threshold based on observed
  outcomes;
- learn a user-specific band or score from history;
- infer preferences from conversation turns and silently apply them
  to future recommendations;
- store any embedding, vector, or opaque agent-side profile of the
  user.

This is a locked non-goal (see
[`non_goals.md`](non_goals.md) "Not a learning loop (yet)" and
[`reporting/plans/post_v0_1_roadmap.md`](../plans/post_v0_1_roadmap.md)
§3.1 locked decision 4). The reasoning:

- Adaptive behavior that hides inside a threshold is the opposite of
  auditability. The runtime's credibility rests on a reader being able
  to reproduce a recommendation from persisted inputs.
- Thresholds and classifiers are already config-driven via
  `~/.config/hai/thresholds.toml`. User-specific tuning, if ever
  scoped, belongs in that explicit config surface — not in a silent
  online loop.
- A learning loop makes eval much harder; the roadmap's Phase E
  (skill-harness eval pilot) is the prerequisite any serious
  adaptation work would need to land after, not before.

If adaptive memory is ever added, it would need: an explicit config
surface, an inspectable per-user record of every adaptation, an eval
harness that distinguishes "deterministic runtime correct" from
"adaptation helped or hurt," and a clear user-visible on/off switch.
None of those exist today.

## 3. Where each layer lives on disk

| Layer | SQLite tables | Files |
|---|---|---|
| Raw evidence | `source_daily_garmin`, `running_session`, `gym_session`, `gym_set`, `nutrition_intake_raw`, `stress_manual_raw`, `context_note`, `exercise_taxonomy` | per-domain JSONL audits under `~/.local/share/hai/` (default `base_dir`) |
| Accepted state | `accepted_recovery_state_daily`, `accepted_running_state_daily`, `accepted_sleep_state_daily`, `accepted_stress_state_daily`, `accepted_resistance_training_state_daily`, `accepted_nutrition_state_daily` | none |
| Decision | `proposal_log`, `planned_recommendation`, `daily_plan`, `x_rule_firing`, `recommendation_log` | `<base_dir>/<domain>_proposals.jsonl`; recovery-only writeback audit |
| Outcome | `review_event`, `review_outcome` | none |
| Explicit user memory | `user_memory` (migration 007) | none |
| Adaptive memory | *(intentionally none)* | *(intentionally none)* |

The SQLite database itself lives under `platformdirs` user-data path by
default (overridable via `--db-path`). Migrations 001–007 create the
shipped tables; forward-only migrations are expected for later phases.

## 4. What this buys a new reader

A reader with this doc plus
[`personal_health_agent_positioning.md`](personal_health_agent_positioning.md)
and [`query_taxonomy.md`](query_taxonomy.md) should be able to state,
without reading any source file:

- *where* any piece of information the runtime uses lives on disk
  (which of the four layers, which table);
- *who* wrote it (projector, `hai propose`, `hai synthesize`, `hai
  review`, a raw intake command);
- *whether* a given behavior is shipped, planned, or deliberately out
  of scope (explicit user memory is Phase D; adaptive memory is
  absent-by-design);
- *why* the runtime refuses to turn review outcomes into silent
  learning.

If any later doc, skill, or commit message drifts away from this
layered view — for example by treating chat memory as equivalent to
accepted state, or by quietly assuming an adaptive loop — this doc is
the anchor to pull back to.
