# State Model v1

Status: **authoritative** as of the Phase 6 checkpoint (2026-04-18).
Migrations 001–006 are live. The DDL under
``src/health_agent_infra/core/state/migrations/`` is the source of
truth; this doc reflects it and is updated when migrations land.

This document governs the interpretation of state in Health Agent
Infra. Per the v1 rebuild, classification and mechanical policy
live in Python (``domains/<d>/classify.py`` + ``policy.py``), so
sections describing "skill markdown owns classification" below are
historical framing — the current boundary is tighter (see
[``architecture.md``](architecture.md) §code-vs-skill).

**Phase 2.5 retrieval-gate compression (2026-04-17):** The
nutrition scope was compressed to macros-only — no ``meal_log``, no
``food_taxonomy``, no micronutrient columns, and
``accepted_nutrition_state_daily.derivation_path`` is
``'daily_macros'`` only in v1. Any prior-session references to
meal-level columns or a USDA food database in this doc are
superseded; see [``non_goals.md``](non_goals.md).

---

## 0. Decisions locked by founder

Recorded for downstream phases. Each is closed; the sections below reflect the resolution.

| Decision | Resolution |
|---|---|
| Correction grammar (§3) | Hybrid: raw evidence append-only with `supersedes_<id>`; accepted state UPSERT + `corrected_at`; recommendations append-only; reviews append-only. |
| Goal model (§7) | Option A: multiple concurrent goals with optional `domain` scope. |
| `recovery_daily` split (§8) | Option A: split `source_daily_garmin` (raw vendor) + `accepted_recovery_state_daily` (committed canonical) + derived summaries computed on demand. |
| Missingness taxonomy (§5) | Four states: `absent`, `partial`, `unavailable_at_source`, `pending_user_input`. |
| Mutation allowlist (§6) | Admin commands disallowed. `--use-default-manual-readiness` moved to demo/scratch-only (not normal agent doctrine). `hai state snapshot` is the primary agent read surface; `hai state read` is introspection/debug. |
| Running as first-class domain (§1, §8) | Running is a first-class domain in the state model. Raw `running_session` is declared but **empty in v1** — it lives strictly at the raw-evidence layer and is only populated when per-activity source data arrives. V1 populates `accepted_running_state_daily` directly from `source_daily_garmin` with `derivation_path='garmin_daily'`; when per-activity data lands, derivation flips to `'running_sessions'`. Sleep and acute/chronic load remain as fields within accepted recovery state. |
| Source vs ingest actor (§4) | Two distinct provenance fields: `source` = where the fact originated (`garmin`, `user_manual`, etc.); `ingest_actor` = what transported it into the system (`garmin_csv_adapter`, `hai_cli_direct`, `claude_agent_v1`). |

---

## 1. Canonical entities

The system represents exactly these entities. Anything outside the list is either out of scope (see the non-goals doc) or a subcomponent of one of these.

| Entity | Definition | Abstraction layer |
|---|---|---|
| **Garmin daily record** | One row of `daily_summary_export.csv` for one civil date, as emitted by Garmin Connect. Wearable-side vendor truth — carries sleep components, resting HR/HRV, training readiness, acute/chronic load, stress, intensity minutes, distance, etc. | Raw evidence |
| **Gym session** | A completed resistance-training session: a set of lifts performed in one block of time. | Raw evidence (user-reported) |
| **Gym set** | A single set within a gym session: exercise, weight, reps, RPE. | Raw evidence (user-reported) |
| **Running session** | A completed running activity as reported by a source (per-activity row). Raw evidence by definition — only exists when we have true source-shaped per-activity data. **Empty in v1**: the `running_session` table is declared by the schema but not populated until Garmin `activities_export.csv` is re-synced. V1 does not synthesise "sessions" from daily aggregates — that would blur the layer boundary. Daily-grain running is represented only in `accepted_running_state_daily` below (a derived artifact), not as a fake raw session. | Raw evidence |
| **Nutrition intake** | User-reported calories/macros/hydration for one civil date. | Raw evidence (user-reported) |
| **Manual stress score** | User-reported subjective stress score (1–5) for one civil date. | Raw evidence (user-reported) |
| **Context note** | Free-text user note with optional tags and a recorded timestamp. No schema on the body. | Raw evidence (user-reported) |
| **Accepted recovery state** | The runtime's committed view of one civil date's recovery-relevant facts, drawing from Garmin daily record + manual stress + any corrections. **Includes sleep-hours fields and acute/chronic load fields** — those stay as fields inside this entity rather than being promoted to their own entities in v1. | Accepted canonical state |
| **Accepted running state (daily)** | The runtime's committed view of one civil date's running activity. In v1, derived directly from `source_daily_garmin`'s `distance_m` + `moderate_intensity_min` + `vigorous_intensity_min` + `total_kcal` (daily-grain only — one row per date). When per-activity `running_session` raw rows become available, derivation flips to aggregating those, and the earlier Garmin-daily-derived rows are superseded. | Accepted canonical state |
| **Accepted resistance-training state (daily)** | The runtime's committed view of one civil date's gym work: total sets, total volume kg-reps, session count. Derived from `gym_session` + `gym_set` rows. | Accepted canonical state |
| **Accepted nutrition state** | The runtime's committed view of one civil date's nutrition. Normally a pass-through of nutrition intake; distinct so corrections can be superseded without mutating raw. | Accepted canonical state |
| **Goal** | A named training or health objective active over a date range, optionally scoped to a domain (`resistance_training`, `running`, `nutrition`, `recovery`, etc.). Multiple goals may be concurrently active; see §7. | Accepted canonical state |
| **Recovery summary** | Deltas, ratios, counts, coverage fractions computed from accepted state. Agent reads these; agent does not persist them. | Derived summary |
| **State snapshot** | The cross-domain object emitted by `hai state snapshot --as-of <date>`. Built on demand from accepted state + raw evidence + derived summaries. | Derived summary |
| **Agent proposal** | A structured dict the agent hands to a `hai intake <kind>` call *before* validation. Becomes raw evidence once validated. | Agent proposal |
| **Training recommendation** | A schema-validated bounded agent output for a `(user_id, for_date)` pair. Multiple recommendations for the same day are retained append-only (suffix `_01`, `_02`, …) — see §3. Read surfaces operationally prefer the latest row per `(user_id, for_date)` but history is never discarded. Written via `hai writeback`. | Recommendation |
| **Review event** | A scheduled future-dated prompt asking "did yesterday's recommendation help?" linked to one recommendation. | Review |
| **Review outcome** | The user's response to a review event: followed/not-followed, improved/no-change/unknown, optional free text. | Review |

---

## 2. Abstraction-layer taxonomy

Six layers. Each row of every table belongs to exactly one layer. Layer membership determines what's allowed to mutate it, how provenance attaches, and how corrections flow.

### Raw evidence
Source-shaped data as acquired. **Immutable after ingest.** If the source corrects (e.g. Garmin restates an overnight sleep value), the new value is a new raw evidence row, not an UPDATE to the old.

- Ingested by: Garmin CSV adapter (`hai pull`); user via `hai intake <kind>`.
- Never mutated by: the agent, the runtime, or any derived process.
- Provenance: every raw row carries `source` (fact origin — `garmin`, `user_manual`, etc.), `ingest_actor` (transport — `garmin_csv_adapter`, `hai_cli_direct`, `claude_agent_v1`), `submission_id` (for user-reported) or `export_batch_id` + `csv_row_index` (for vendor-reported), and `ingested_at` timestamp. See §4 for the source / ingest-actor distinction.

### Accepted canonical state
The runtime's committed view — "this is what happened on this day." Derived from one or more raw evidence rows plus any corrections. Queried by the agent via `hai state snapshot`.

- Mutated by: the runtime only, in response to raw evidence ingestion or explicit correction events.
- Never mutated by: the agent directly.
- Provenance: every accepted-state row links back to the raw evidence row(s) it was derived from, plus the `projected_at` timestamp when that projection ran.

### Derived summary
Deterministically recomputable from accepted state + raw evidence. `RawSummary` in `schemas.py` is an example. Computed on demand, may be cached (e.g. materialised as a view), but the canonical truth is always the accepted state.

- Mutated by: nothing (ephemeral).
- Read by: the agent (via `hai state snapshot` / `hai clean` output), humans (via `hai state read`).

### Agent proposal
A dict the agent constructs and hands to a validating CLI (`hai intake <kind>` for structured, `hai intake note` for free-text, `hai writeback` for recommendations). Lives only in memory or on disk as a temp file before validation. After validation, it becomes raw evidence (for intake) or a recommendation (for writeback).

- Mutated by: the agent, until it's submitted.
- Post-submission: validated at the CLI boundary; accepted proposals land in raw evidence or the recommendation log.

### Recommendation
A schema-validated `TrainingRecommendation` produced by the agent. Validation is code-enforced at `hai writeback` (see `src/health_agent_infra/validate.py`). Once written, **immutable and append-only**. The log may contain multiple recommendations for the same `(for_date, user_id)` — each with a bumped suffix (`rec_<date>_<user>_01`, `_02`, …) — and all are retained. Read surfaces (reporting skill, agent read via `hai state snapshot`) operationally prefer the latest row per day, but the history is never discarded.

- Mutated by: nothing.
- Append-only: yes. Same-day re-emission adds a new row; nothing is deleted or overwritten.

### Review
Event + outcome. Event is scheduled by the runtime when a recommendation is written; outcome is recorded by the user (via the agent) next day. Append-only.

- Mutated by: nothing.

---

## 3. Correction semantics

Founder decision gate. Two grammars on the table; picking one uniformly applies across the whole schema. Proposed: **hybrid**, applied per layer.

### Proposed grammar

- **Raw evidence: append-only.** New raw rows never overwrite old ones. If a user corrects "I logged 2200 kcal but meant 2400," the correction is a new raw row with `supersedes_submission_id = <old>` set. The old row stays for audit.
- **Accepted canonical state: UPSERT + `corrected_at`.** A fresh projection run overwrites the existing accepted state row for a given `(as_of_date, user_id, source)` key and sets `corrected_at = now()`. The audit trail lives one layer down in raw evidence.
- **Recommendations: append-only.** Same-day re-runs produce new recommendations with bumped suffixes (`rec_<date>_<user>_01`, `_02`); all are retained.
- **Reviews: append-only.** An outcome can only ever be added, never rewritten.

### Why hybrid

- **Raw evidence is user-authored or vendor-authored truth.** Overwriting it loses the audit trail the doctrine values.
- **Accepted state is the runtime's synthesis.** It's legitimately re-synthesisable from the raw layer below it; overwriting keeps the query layer simple without losing audit (the audit lives in raw).
- **Recommendations are bounded agent outputs.** Keeping them append-only means the review loop can reference any historical recommendation.

### Alternative (rejected in this draft)

Pure append-only everywhere with a computed "active row" projection. Cleaner conceptually; more query complexity. Rejected unless founder prefers.

**Founder: pick one. Hybrid or pure-append. Plan proceeds from there.**

---

## 4. Provenance rules

Every row in every table carries provenance sufficient to trace it back to its origin **and** the actor that moved it into the system. These are two distinct dimensions; conflating them loses information.

### Two provenance dimensions

- **`source`** — where the fact *originated*. Answers "whose truth is this?" Values: `garmin`, `user_manual`, `oura` (future), `whoop` (future), etc.
- **`ingest_actor`** — what *transported* the fact into the system. Answers "who put this row here?" Values: `garmin_csv_adapter` (the `hai pull` path), `hai_cli_direct` (user typed flags to `hai intake` themselves), `claude_agent_v1` (an agent mediated: user narrated, agent translated to structured args, agent invoked `hai intake`).

A user-reported nutrition row entered by an agent on behalf of the user has `source='user_manual'` **and** `ingest_actor='claude_agent_v1'`. The fact originates with the user; the agent was the conduit. Both are recorded.

This matters because:
- Audits over "what has the agent written?" must filter on `ingest_actor = 'claude_agent_v1'`.
- Audits over "what has the user asserted?" must filter on `source = 'user_manual'` (regardless of which actor transported it).
- If we later add a voice transcript path, `source` stays `user_manual` + a new `ingest_actor = 'hai_voice_note_adapter'` captures the new transport.

### Raw evidence rows

Required fields:

- `source` TEXT NOT NULL — fact origin (see above).
- `ingest_actor` TEXT NOT NULL — transport (see above).
- `ingested_at` TIMESTAMP NOT NULL — when the runtime first accepted this row.
- Source-specific identifiers:
  - Garmin rows: `export_batch_id` + `csv_row_index` (part of `source_daily_garmin`'s PK).
  - User-reported rows: `submission_id` TEXT — globally unique (format `m_<kind>_<date>_<suffix>`).
- `supersedes_<entity>_id` TEXT NULL — pointer to the row this one corrects, if any. NULL = "first assertion of this fact."

### Accepted state rows

- `source` + `ingest_actor` propagated from the primary raw row (or the most recent raw row, if synthesis spans multiple).
- `derived_from` TEXT — JSON array of raw-row identifiers this accepted state was synthesised from.
- `projected_at` TIMESTAMP NOT NULL — when this projection run produced this row.
- `corrected_at` TIMESTAMP NULL — set on re-projection overwrites (hybrid grammar, see §3).

### Agent-authored rows (recommendations, outcomes)

- `source = 'claude_agent_v1'` (or whichever agent identity).
- `ingest_actor = 'claude_agent_v1'` (the agent both originated the recommendation and transported it).
- `agent_version` TEXT NULL — specific model identity (e.g. `claude-opus-4-7`).
- `produced_at` TIMESTAMP NOT NULL — when the agent proposed the row.
- `validated_at` TIMESTAMP NOT NULL — when the CLI validator accepted it.

**Rule:** if a row lacks its required provenance fields, the INSERT fails. Validation is code-enforced, not convention-enforced.

---

## 5. Missingness rules

The state surface distinguishes four cases. The agent reads the tag and must not fabricate.

### `absent` — no data ingested for this domain + date
The runtime has no raw evidence for this `(domain, as_of_date, user_id)` and does not expect any. The snapshot field is `null` with a missingness token:
```json
{"nutrition": {"today": null, "missingness": "absent"}}
```

### `partial` — some but not all expected fields present, day is closed
E.g. user logged calories + protein but not carbs/fat, and the day is over. This is the final state of the row with gaps. The snapshot surfaces what's present and tags missingness:
```json
{"nutrition": {"today": {"calories": 2200, "protein_g": 180, "carbs_g": null, "fat_g": null},
               "missingness": "partial:carbs_g,fat_g"}}
```

### `unavailable_at_source` — source was asked but the field is not available
E.g. Garmin didn't record HRV that night. Distinct from `absent` because we did try; Garmin just didn't have it. The snapshot surfaces the field as null and tags:
```json
{"recovery": {"today": {"hrv_ms": null, ...}, "missingness": "unavailable_at_source:hrv_ms"}}
```

### `pending_user_input` — day in progress, more logging expected
E.g. it's 15:00 local time on an ongoing day; the user has logged breakfast + lunch but dinner hasn't happened yet. The row exists and has partial data, but this is **not** a closed "partial" state — the user is still logging. Distinct from `partial` because the missingness is expected to resolve before end-of-day.
```json
{"nutrition": {"today": {"calories": 1200, "protein_g": 90, ...},
               "missingness": "pending_user_input:dinner_not_logged",
               "last_logged_at": "2026-04-17T14:45:00+00:00"}}
```

The runtime decides `pending_user_input` vs `partial` by a deterministic rule: if `as_of_date == today_local_civil_date` AND `now_local < 23:30`, unsubmitted fields default to `pending_user_input`; otherwise `partial`. The cutover time can be tuned per-user later if needed.

### Rule for the agent

When a field is `null` in the snapshot, the agent **must** read the `missingness` tag to understand which of the four cases applies, and **must not** fabricate a plausible value. The recovery-readiness skill and merge-human-inputs skill both carry this as an invariant. `pending_user_input` specifically signals "ask the user for more" rather than "proceed as if the field were absent."

---

## 6. Agent mutation and read allowlist

The agent is permitted to invoke these commands (and only these). Read vs write is explicit because the agent's routine loop is majority-read.

### Primary read surface (agent's default)

- `hai state snapshot --as-of <date> [--user-id X] [--lookback-days N]` — **this is the command the recovery-readiness skill uses to load context.** Cross-domain, shaped for recommendation-producing reasoning. The agent should reach for this first whenever it needs to know "what is this person's state today?"

### Secondary read surface (introspection / debug / reporting)

- `hai state read --domain <d> --since <date> [--until <date>] [--user-id X]` — for when the agent (or the reporting skill) needs a targeted slice of one domain. Useful when the snapshot would be over-fetching, or when a human-facing narration wants raw rows for a specific window. Not for the normal recovery-readiness classification path.

### Write surface — structured intake

- `hai intake readiness --soreness ... --energy ... --planned-session-type ... [--active-goal ...]`
- `hai intake gym --session-id ... --exercise ... --set-number ... --weight-kg ... --reps ... --rpe ...` (and bulk `--session-json` variant)
- `hai intake stress --score <1-5> [--tags ...]`
- `hai intake note --text "..." [--tags ...]`

### Write surface — data acquisition

- `hai pull [--date X] [--manual-readiness-json P]` — pulls Garmin evidence. Normal form: pairs with `hai intake readiness` upstream (so readiness JSON is real user input, not a default).
- `hai clean --evidence-json P` — normalises pulled evidence into CleanedEvidence + RawSummary.

### Write surface — recommendation + review

- `hai writeback --recommendation-json P --base-dir D`
- `hai review schedule --recommendation-json P --base-dir D`
- `hai review record --outcome-json P --base-dir D`
- `hai review summary --base-dir D [--user-id X]`

### Demo / scratch only — NOT part of normal agent doctrine

- `hai pull --use-default-manual-readiness` — fabricates neutral subjective readiness. **Not** part of routine state-maintenance operation; reserved for demos, CI fixtures, and reproducing captured proof bundles where real intake isn't available. The merge-human-inputs skill explicitly tells the agent to ask the user for readiness rather than defaulting.

### The agent is NOT permitted to invoke

- `hai state init` — one-time user setup
- `hai state migrate` — schema evolution is user-owned
- `hai state reproject` — recovery tool, user-only
- `hai setup-skills` — installation, user-only
- any direct SQLite access (the DB is not in the agent's tool surface at all)
- any filesystem mutation outside the JSON stdin/stdout surface

Skills' `allowed-tools` YAML fronts match this list exactly, except that `--use-default-manual-readiness` appears only in demo/fixture skills, not in normal-operation skills. Mismatches between this doc and skill frontmatter are caught by a future lint pass (not in scope for 7A.0 itself).

---

## 7. Goal model (decision: multi-active, optionally domain-scoped)

Per founder decision in §0.

```sql
goal (goal_id TEXT PK, user_id, label TEXT, domain TEXT NULL,
      started_on DATE, ended_on DATE NULL, created_at TIMESTAMP)
```

- Multiple rows with `ended_on IS NULL` = multiple active goals.
- `domain` is NULL (whole-person goal) or one of `resistance_training`, `running`, `nutrition`, `recovery`, etc.
- Example: `label='strength_block', domain='resistance_training'` + `label='5k_pace_maintain', domain='running'` + `label='bf_pct_reduction', domain='nutrition'` can all be active simultaneously.
- Rationale: matches real training periodization; the recovery-readiness skill can pick the goal relevant to the day's planned session type; extensible without migrations.

The agent reads active goals via `hai state snapshot`'s `goals_active[]` field. The recovery-readiness skill selects the relevant goal(s) based on `planned_session_type` and the domain tag — e.g. a "hard intervals" session prefers the `running` domain goal. Where no domain goal applies, whole-person goals (domain=NULL) are used.

---

## 8. `recovery_daily` layer split (decision: three tables)

Per founder decision in §0.

```sql
source_daily_garmin (as_of_date, user_id, export_batch_id, csv_row_index,
                     source, ingest_actor, ingested_at,
                     -- raw vendor fields: sleep_deep_sec, sleep_light_sec,
                     -- sleep_rem_sec, resting_hr, health_hrv_value,
                     -- acute_load, chronic_load, acwr_status,
                     -- training_readiness_*, all_day_stress, body_battery,
                     -- moderate_intensity_min, vigorous_intensity_min, distance_m,
                     -- [all 60 CSV columns available])
  PRIMARY KEY (as_of_date, user_id, export_batch_id)

accepted_recovery_state_daily (as_of_date, user_id,
                               sleep_hours REAL,      -- derived from sleep_deep + sleep_light + sleep_rem
                               resting_hr REAL,       -- direct from source
                               hrv_ms REAL,           -- direct from source
                               all_day_stress INTEGER, -- direct from source
                               acute_load REAL,       -- direct vendor field, retained as accepted
                               chronic_load REAL,
                               acwr_ratio REAL,
                               training_readiness_pct REAL,
                               body_battery_end_of_day INTEGER,
                               derived_from TEXT,     -- JSON array of raw row refs
                               source, ingest_actor, projected_at, corrected_at)
  PRIMARY KEY (as_of_date, user_id)

-- Derived summaries (RawSummary, coverage fractions, ratios, spike-day counts)
-- are computed on demand from accepted_recovery_state_daily + trailing-window
-- queries; not persisted as a table.
```

Running gets the same layer-split shape, but its v1 population path is different from recovery: v1 derives the accepted daily directly from `source_daily_garmin`, because we have no per-activity source data yet. The raw `running_session` table is declared so the projector and skill can reference a stable shape, but it is only populated when per-activity source data arrives later.

```sql
-- Raw: true per-activity running data from a source. DECLARED BUT EMPTY IN V1.
-- Populated later when Garmin activities_export.csv is re-synced.
running_session (session_id TEXT PK, user_id, as_of_date,
                 started_at TIMESTAMP, duration_s REAL,
                 distance_m REAL, avg_hr INTEGER,
                 source TEXT NOT NULL, ingest_actor TEXT NOT NULL,
                 submission_id TEXT, export_batch_id TEXT,
                 ingested_at TIMESTAMP NOT NULL,
                 supersedes_session_id TEXT NULL)

-- Accepted canonical: one row per date. V1 derives from source_daily_garmin;
-- later flips to aggregating running_session rows once those exist.
accepted_running_state_daily (as_of_date, user_id,
                              total_distance_m REAL, total_duration_s REAL,
                              moderate_intensity_min INTEGER,
                              vigorous_intensity_min INTEGER,
                              session_count INTEGER,
                              derived_from TEXT,      -- JSON: list of source row refs
                              derivation_path TEXT,   -- 'garmin_daily' | 'running_sessions'
                              source, ingest_actor, projected_at, corrected_at)
  PRIMARY KEY (as_of_date, user_id)
```

Rationale:
- Layer boundaries stay honest: raw evidence must be source-shaped acquired facts. A "session" the runtime invents from daily totals is not a raw fact.
- Running is still a first-class *domain* in the state model — the entity exists, the accepted daily row exists, the snapshot surfaces it — even though the *raw layer* for running is empty in v1.
- When real per-activity data lands, the v1 `accepted_running_state_daily` rows flip their `derivation_path` from `'garmin_daily'` to `'running_sessions'` and get re-projected. The API the agent sees via `hai state snapshot` doesn't change.
- `session_count` is NULL when `derivation_path = 'garmin_daily'` (we don't know how many runs made up the daily totals) and a concrete count when `'running_sessions'`. The agent treats NULL session_count as "daily-aggregate only, session-level detail unavailable."
- Adding a second passive connector (Oura, Whoop) later is clean: new `source_daily_oura` table; `accepted_recovery_state_daily` gets a reconciliation strategy per-field.
- The runtime code that projects raw → accepted is explicit and testable.

---

## 9. What happens on a "correction" — worked example

A concrete trace through the grammar to ground it.

### Day 1 evening: user narrates nutrition to the agent; agent calls `hai intake nutrition`

Raw evidence (agent mediated):
```
nutrition_intake_raw(submission_id='m_nut_2026-04-17_abc', user_id='u_1',
                    as_of_date='2026-04-17', calories=2200, protein_g=180,
                    source='user_manual',              -- user is the fact origin
                    ingest_actor='claude_agent_v1',    -- agent was the conduit
                    ingested_at='2026-04-17T19:30+01:00',
                    supersedes_submission_id=NULL)
```

Accepted state (via projection):
```
accepted_nutrition_state_daily(as_of_date='2026-04-17', user_id='u_1',
                               calories=2200, protein_g=180,
                               derived_from='["m_nut_2026-04-17_abc"]',
                               source='user_manual', ingest_actor='claude_agent_v1',
                               projected_at='2026-04-17T19:30+01:00',
                               corrected_at=NULL)
```

### Day 2 morning: user types a correction directly into the CLI

Raw evidence (new append-only row, different ingest actor this time):
```
nutrition_intake_raw(submission_id='m_nut_2026-04-17_def', user_id='u_1',
                    as_of_date='2026-04-17', calories=2400, protein_g=180,
                    source='user_manual',           -- still user's truth
                    ingest_actor='hai_cli_direct',  -- this time typed to the CLI directly
                    ingested_at='2026-04-18T08:00+01:00',
                    supersedes_submission_id='m_nut_2026-04-17_abc')
```

Accepted state (UPSERT + corrected_at):
```
accepted_nutrition_state_daily(as_of_date='2026-04-17', user_id='u_1',
                               calories=2400, protein_g=180,
                               derived_from='["m_nut_2026-04-17_def","m_nut_2026-04-17_abc"]',
                               source='user_manual', ingest_actor='hai_cli_direct',
                               projected_at='2026-04-18T08:00+01:00',
                               corrected_at='2026-04-18T08:00+01:00')
```

Audit query: "what was the user's first recorded calorie count for 2026-04-17?" → `SELECT calories FROM nutrition_intake_raw WHERE submission_id = 'm_nut_2026-04-17_abc'` → 2200. Audit preserved.

Audit query: "which facts on 2026-04-17 were mediated by the agent vs typed directly?" → `SELECT submission_id, ingest_actor FROM nutrition_intake_raw WHERE as_of_date = '2026-04-17'` → answers both. Having `ingest_actor` separate from `source` is why this query works cleanly.

Agent query via snapshot on 2026-04-18: sees 2400. Agent doesn't need to know there was a correction unless it reads the `derived_from` field.

---

## 10. Open questions for founder review

All major decisions are resolved in §0. Three minor items that do **not** block 7A.1 and will only be revisited if concrete pain surfaces during execution:

1. **Entity completeness revisit.** Sleep and acute/chronic load remain fields inside `accepted_recovery_state_daily` per founder decision (§0). If during 7B's Garmin-richness work this feels wrong, promote them then.
2. **Goal labels.** `goal.label` is free-text in v1. If that turns out to cause drift (agent inventing inconsistent labels across days), enumerate later; no enum enforcement in v1.
3. **ingest_actor extensibility.** v1 ingest actors are `garmin_csv_adapter`, `hai_cli_direct`, `claude_agent_v1`. Field is free-text TEXT; future actors (voice-note adapter, external MCP caller, etc.) are added in place as their adapters land. No enum, no pre-allocation.

Nothing remaining blocks 7A.1 DDL.

---

## 11. What this doc is NOT

- Not the SQL. DDL lands in 7A.1 after this doc is approved.
- Not a commitment to SQLite specifically — though it's the proposed backing store and nothing in this doc rules it out.
- Not a contract for the agent's prompt behaviour — that lives in skills.
- Not a product spec — it's the runtime's data contract. What the user sees is a separate concern.
- Not a doctrine replacement. The Founder Doctrine is controlling; this doc translates it.
