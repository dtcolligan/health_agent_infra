# How to add a pull adapter

This is a contributor guide for adding a second source adapter under
[`src/health_agent_infra/core/pull/`](../../src/health_agent_infra/core/pull/).
It describes the stabilized post-v0.1.x runtime, not a future
multi-source design. The two reference implementations are the
committed-CSV adapter
([`garmin.py`](../../src/health_agent_infra/core/pull/garmin.py)) and
the live-API adapter
([`garmin_live.py`](../../src/health_agent_infra/core/pull/garmin_live.py)).
Keep both open while you work — every contract below is visible in one
of them.

## When this doc applies

Use this guide when you want to add a new data source to the runtime:
a second wearable (Apple Health, Oura, Whoop…), a different ingest
path into Garmin (e.g. FIT files), or any other deterministic loader
that turns external state into evidence the runtime consumes. It does
**not** apply to user-authored intake surfaces — those live under
[`src/health_agent_infra/core/intake/`](../../src/health_agent_infra/core/intake/)
and are wired through `hai intake …` subcommands, not `hai pull`.

The post-v0.1.x roadmap intentionally defers a second live adapter
(see [`reporting/plans/post_v0_1_roadmap.md`](../plans/post_v0_1_roadmap.md)
§2.3 and locked decision 3.1.8). Land the seam doc before the
implementation; don't grow this doc by shipping the adapter at the
same time.

## The adapter contract (required)

`hai pull` looks up one adapter, calls `adapter.load(as_of)`, and
emits the returned dict on stdout with `source: adapter.source_name`
and `user_id` / `manual_readiness` metadata. See
[`cli.py :: cmd_pull`](../../src/health_agent_infra/cli.py) (around
line 120) for the dispatch.

Conformers are checked structurally against
[`core/pull/protocol.py :: FlagshipPullAdapter`](../../src/health_agent_infra/core/pull/protocol.py):

```python
@runtime_checkable
class FlagshipPullAdapter(Protocol):
    source_name: str
    def load(self, as_of: date) -> dict: ...
```

No inheritance is required. The Protocol is deliberately thin: the
binding contract is the **shape of the dict** `load()` returns, not a
second type declaration. Both Garmin adapters conform structurally
and are exercised against the Protocol in
[`safety/tests/test_pull_garmin_live.py`](../../safety/tests/test_pull_garmin_live.py).

Name: `source_name` must be stable across runs and identify the
source in provenance. `"garmin"` and `"garmin_live"` are taken;
pick a distinct namespace (e.g. `"apple_health"`, `"oura"`).

## Evidence shape (required)

`load(as_of)` must return a dict with the five keys
[`clean_inputs()`](../../src/health_agent_infra/core/clean/recovery_prep.py)
and the raw-row projectors read. The shape is the canonical contract
between pull and clean/state; the exact same layout is emitted by
both reference adapters:

```python
{
    "sleep":            {"record_id": str, "duration_hours": float} | None,
    "resting_hr":       [{"date": str, "bpm":       float, "record_id": str}, ...],
    "hrv":              [{"date": str, "rmssd_ms":  float, "record_id": str}, ...],
    "training_load":    [{"date": str, "load":      float, "record_id": str}, ...],
    "raw_daily_row":    {...full per-day row keyed by source column names...} | None,
    "activities":       [IntervalsIcuActivity.as_dict(), ...],  # optional, v0.1.4+
}
```

The sixth key, `activities`, is optional but recommended when the source
exposes per-session data. `intervals.icu` is the reference example: its
`/wellness.json` endpoint feeds `raw_daily_row` (HRV, RHR, sleep, load —
daily rollups); its `/activities` endpoint feeds the per-session list
(distance, HR zone times, interval structure, TRIMP). The adapter fetches
both, emits both; `cmd_clean` aggregates today's activities into the
daily rollup via `aggregate_activities_to_daily_rollup` so the existing
per-domain classifiers see real numbers instead of nulls. When the source
has no activity-level granularity, omit the key (or emit `[]`) — the
clean pipeline treats its absence as "rollup is authoritative."

Notes a new adapter must honour:

- **`sleep` is the as-of night.** `None` is legal; downstream
  `clean_inputs` treats it as an unavailable signal, not an error.
- **Series are trailing windows.** The Garmin adapters use
  `history_days=14` — match it unless you have a reason not to, since
  downstream baselines assume roughly two weeks of context.
- **Series entries must be JSON-round-trippable.** Date values are
  ISO strings; numeric values are plain floats; `record_id` is stable
  per `(date, signal)` so downstream deduping works.
- **`raw_daily_row` is the source-of-truth row.** This is what gets
  projected into `source_daily_garmin` (or your source's equivalent
  raw table) — it carries the full column set for the as-of date, not
  the trimmed series. Garmin's canonical key set is the `RAW_DAILY_ROW_COLUMNS`
  tuple in
  [`core/pull/garmin_live.py`](../../src/health_agent_infra/core/pull/garmin_live.py);
  a new source will need its own equivalent.
- **Degrade per-field, not per-pull.** Upstream gaps become `None`
  on the relevant key; the overall pull still returns. This matches
  the live adapter's documented contract — a single missing column
  shouldn't drop the whole day.

The JSON envelope `hai pull` prints is a wrapper with `as_of_date`,
`user_id`, `source`, `pull`, `manual_readiness`. **Only `pull` is the
adapter's output**; the rest is `cli.py`'s job. Reference CSV inputs
for the offline adapter live under
[`src/health_agent_infra/data/garmin/export/`](../../src/health_agent_infra/data/garmin/export/).

## Projection expectations (required)

`hai clean` calls
[`clean_inputs()`](../../src/health_agent_infra/core/clean/recovery_prep.py)
and then projects `raw_daily_row` into the state database via
[`project_source_daily_garmin()`](../../src/health_agent_infra/core/state/projector.py).
A new adapter has three choices here, roughly in order of effort:

1. **Same evidence shape, reuse Garmin projectors.** If the new
   source can be coerced into the Garmin `raw_daily_row` column set
   without loss, reuse
   [`project_source_daily_garmin`](../../src/health_agent_infra/core/state/projector.py)
   and the per-domain accepted-state projectors
   ([`recovery`](../../src/health_agent_infra/core/state/projectors/recovery.py),
   [`sleep`](../../src/health_agent_infra/core/state/projectors/sleep.py),
   [`stress`](../../src/health_agent_infra/core/state/projectors/stress.py),
   [`strength`](../../src/health_agent_infra/core/state/projectors/strength.py)).
   This is the shape the live Garmin adapter takes today.

2. **New raw table, reuse accepted-state tables.** If the source's
   raw shape diverges enough that you don't want to pretend it's
   Garmin, add a `source_daily_<name>` table via a new migration and
   a projector module parallel to `projectors/recovery.py`. Feed the
   per-domain accepted-state tables from that projector. The
   `derived_from` column on each accepted row is how the state model
   keeps mixed-source provenance honest — see
   [`state_model_v1.md`](state_model_v1.md) §3 and §4.

3. **New accepted-state tables.** Reserved for sources that can't be
   reduced to the current per-domain tables at all. This is a
   migration-heavy path and intersects the domain-extension surface
   (see [`how_to_add_a_domain.md`](how_to_add_a_domain.md)) — do it
   only if (1) and (2) are genuinely wrong.

Path (1) is the intended default for the next adapter; the other two
are escape hatches.

Whichever path you pick, preserve these invariants:

- **`source` and `ingest_actor` are distinct.** `source` is the
  upstream identity (`"garmin"`, `"apple_health"`); `ingest_actor`
  is the code path that wrote the row (`"garmin_csv_adapter"`,
  `"apple_health_connector"`). Both are required columns on every
  accepted table — see `state_model_v1.md` §4.
- **Projectors stay idempotent.** First write stamps
  `projected_at`; a correcting rewrite stamps `corrected_at`. The
  existing per-domain projectors all follow this "hybrid correction
  grammar" (see `state_model_v1.md` §3); match it.
- **`derivation_path` distinguishes aggregate origins.** Garmin
  daily rows use `'garmin_daily'`; nutrition uses `'daily_macros'`.
  Pick a stable string per source and document it in
  `state_model_v1.md`.

## Optional refinement points

- **Live-path auth.** If the adapter needs credentials, model them
  on
  [`core/pull/auth.py`](../../src/health_agent_infra/core/pull/auth.py) —
  `CredentialStore` uses the OS keyring; `hai auth garmin` is the
  reference CLI surface.
- **Library-agnostic client split.** `garmin_live.py` depends on a
  `GarminLiveClient` Protocol and only imports the upstream SDK
  inside `build_default_client`. That split makes the adapter
  testable without the SDK installed. Copy the pattern if the new
  source has a heavy SDK dependency.
- **`history_days` configurability.** Expose it as a constructor
  argument and thread it through the `hai pull --history-days` flag
  only if the trailing-window size is genuinely tunable for this
  source. Otherwise leave it fixed.
- **Manual readiness default.** `core/pull/garmin.py ::
  default_manual_readiness` exists so offline runs can exercise the
  whole pipeline without fabricating user answers. A new adapter can
  add an analogous helper if it ships with a neutral offline mode.

## What not to change casually

- **The evidence dict shape.** `sleep` / `resting_hr` / `hrv` /
  `training_load` / `raw_daily_row` is the pull→clean contract.
  Widening it invalidates `clean_inputs()` and every downstream
  projector — it is a runtime change, not an adapter change.
- **`_SOURCE_DAILY_GARMIN_COLUMNS`** in
  [`projector.py`](../../src/health_agent_infra/core/state/projector.py).
  Columns outside this tuple are silently dropped — that defensiveness
  is deliberate (state_model drift lands via migrations, not implicit
  writes). Don't mutate it from an adapter.
- **Accepted-table column sets and projector semantics.** A new
  adapter that wants a new column should add a migration, update the
  domain's accepted-state projector, and surface the field through
  `build_snapshot` — not reach into an existing projector.
- **`hai propose` / `hai synthesize`.** These are downstream write
  surfaces. A pull adapter never calls them; pull ends at
  `raw_daily_row` + the clean stage.
- **Skill files.** Skills under
  [`src/health_agent_infra/skills/`](../../src/health_agent_infra/skills/)
  do not reference adapters. Adding a source does not change
  judgment; don't edit skills.

## Required tests

A new adapter ships green when, at minimum:

- `safety/tests/test_pull_<source>.py` (or the CSV/live split if the
  adapter has both) asserts:
  - the adapter conforms to
    `FlagshipPullAdapter` (Protocol `isinstance` check, mirroring
    `test_pull_garmin_live.py`).
  - `load(as_of)` returns a dict with the five canonical keys.
  - per-field degradation: when the upstream omits a field, the
    corresponding key is `None` or an empty series, not an exception.
  - window assembly: the adapter walks the `history_days + 1`
    expected dates exactly once each.
  - `raw_daily_row` is populated for the as-of date and shares its
    column set with whatever projector will consume it.
- At least one test exercises the full `pull → clean → project`
  path against the real projectors the adapter targets. Use
  [`test_state_clean_projection.py`](../../safety/tests/test_state_clean_projection.py)
  as the pattern: seed a fake upstream, run `load`, run
  `clean_inputs`, project, and assert the accepted-state rows look
  right.
- If the adapter introduces credentials, mirror the
  [`test_pull_auth.py`](../../safety/tests/test_pull_auth.py) +
  [`test_cli_pull_live_and_auth.py`](../../safety/tests/test_cli_pull_live_and_auth.py)
  shapes: credential storage, missing-credential error path, live
  error surfacing.

The existing eval runner (`hai eval run --domain <d>`) does not read
adapters; it runs off committed scenarios. A new adapter does not
need to extend evals.

## CLI wiring

`hai pull` is the only surface that calls adapters today. Rather
than introducing a `--source <name>` flag per adapter, the intended
pattern (mirrored by the CSV/live split) is:

- The adapter exports a constructor that `cmd_pull` can dispatch to
  behind a flag. `--live` switched between the CSV and live Garmin
  adapters in
  [`cli.py :: cmd_pull`](../../src/health_agent_infra/cli.py).
- The dispatch logic stays tiny: construct, call `.load(as_of)`,
  emit. If dispatch grows past a second flag, that is a signal to
  refactor `cmd_pull` into a registry — **not** to move the logic
  into the adapter.

Don't add a new top-level CLI subcommand for a source. `hai pull`
is the single documented entry point.

## Definition of done

An adapter is ready to land when **all** of the following are true.
If any are not, finish the missing ones before opening the PR —
don't rely on follow-ups to close the seam.

1. The adapter conforms to `FlagshipPullAdapter` (Protocol check
   passes in tests).
2. `adapter.load(as_of)` returns the five-key evidence dict with the
   documented shapes, and degrades per-field on upstream gaps.
3. `hai pull` dispatches to the adapter with a named flag (no
   subcommand split).
4. `hai clean` of the adapter's output projects into state without
   errors on a fresh migration run.
5. Accepted-state rows carry a correct, distinct `source` and
   `ingest_actor`; `derivation_path` is set if appropriate;
   `derived_from` lists the source row ids.
6. Tests cover Protocol conformance, evidence shape, per-field
   degradation, window assembly, and the pull→clean→project path.
7. Credentials (if any) are handled through `CredentialStore`, not
   environment-variable hacks or inline prompts.
8. `state_model_v1.md` is updated with any new column, table,
   `source` value, or `derivation_path` the adapter introduces.
9. The [architecture diagram](architecture.md) still reflects the
   pipeline. If the adapter added a new projector or a new accepted
   table, update the pipeline ASCII; otherwise leave it alone.
10. No skill files, no synthesis code, no X-rule evaluators, and no
    writeback surfaces were edited. A pull adapter is a seam, not a
    policy change.
