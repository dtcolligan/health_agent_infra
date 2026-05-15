# post-v0.1.14 carry-over findings

Surfaced 2026-05-01 during a maintainer-as-user session that opened with
the question "what does my agent say tonight?" and uncovered three
fixture-shaped rows in `sync_run_log` written ~17:54-17:55 UTC the same
day, while the maintainer had only been doing v0.1.14 release work
(build, smoke, push, PyPI upload). No `hai daily` was invoked
(`runtime_event_log` confirms last `daily` event was 2026-04-30T19:26 UTC).

Status: documented for v0.1.15 scope. State DB pollution was confirmed
**bounded to the freshness-telemetry table** (`sync_run_log`); all six
canonical-domain projected tables read empty across the three suspect
dates. No reasoning surface (proposals / planned_recommendations /
daily_plan / recommendation_log / review_outcome) was affected. A
backup at `/tmp/hai-backup-pre-cleanup-2026-05-01.tar.gz` was taken
before further state changes; no DB mutations were made.

---

## F-PV14-01: CSV-fixture pull writes to canonical state DB without isolation marker

**Severity:** ship-impact (silently misrepresents user state).

**Shape.** `core/pull/garmin.py:43` (`load_recovery_readiness_inputs`)
reads from a packaged CSV fixture
(`src/health_agent_infra/data/garmin/export/daily_summary_export.csv`)
and writes through the same `_open_sync_row` /
`_close_sync_row_ok` codepath that real intervals.icu pulls use
(`cli.py:183` / `cli.py:267`). The CSV adapter has no
`hai demo`-marker check — invoking `hai pull --source garmin` against
the canonical user DB succeeds silently and stamps `sync_run_log`
with `last=<now>`, `for=<as_of arg>`, `status=ok`.

**Evidence (2026-05-01).** Three rows in the maintainer's real
`~/.local/share/health_agent_infra/state.db`:

| source | last (UTC) | for_date | matches |
|---|---|---|---|
| `garmin` | 17:54:30 | 2026-02-10 | first row of `daily_summary_export.csv` |
| `garmin_live` | 17:54:30 | 2026-04-17 | `as_of_date` of `evals/scenarios/recovery/rec_001/002/003.json` |
| `readiness_manual` | 17:55:43 | 2026-04-08 | last row of `daily_summary_export.csv`; `default_manual_readiness(as_of)` shape |

JSONL audit logs at `~/.health_agent/` were **not** touched today
(latest mtime is 2026-04-30T20:25), so whatever wrote those rows
either bypassed the JSONL path or set `--base-dir` (HAI_BASE_DIR) to
a temp location while leaving `--db-path` (HAI_STATE_DB) on the
canonical resolver. The asymmetric-override shape is a real isolation
bug regardless of which command surfaced it.

**Same-family precedent.** F-DEMO-01 (v0.1.12 cycle): `hai doctor`
greens intervals.icu auth on credential presence, not API acceptance.
Same false-positive shape — adapter or doctor renders "ok" while the
underlying state is wrong.

**Proposed v0.1.15 fix:**

1. CSV adapter (`core/pull/garmin.py`) refuses to project into the
   canonical state DB unless either (a) a valid `hai demo` marker is
   active OR (b) an explicit `--allow-fixture-into-real-state` flag is
   passed. Default-deny.
2. `hai stats` and `hai doctor` compare `sync_run_log.last` vs
   `sync_run_log.for_date` per source and raise WARN when they diverge
   by >48h. Catches silent fixture-load patterns generally, not just
   this one.
3. `hai capabilities` manifest marks each source as `live` vs
   `fixture` so an agent driving the CLI knows the CSV path is
   fixture-only.
4. Symmetry rule: every CLI command that consumes both
   `--db-path` and `--base-dir` must refuse if exactly one is
   resolved to a non-default location. Asymmetric override is an
   isolation bug, not a feature.

**Acceptance:** repro test that invokes `hai pull --source garmin`
against the canonical DB without a demo marker and asserts USER_INPUT
exit + zero rows written to `sync_run_log`. Plus a regression test
on `hai stats` / `hai doctor` that asserts WARN when `last` and
`for_date` diverge.

---

## F-PV14-02: no `hai sync purge` surface for surgical sync_run_log cleanup

**Severity:** doctrine-gap (forces raw-SQL or full-DB-wipe choice when
contamination is bounded).

**Shape.** `hai state` exposes `init / migrate / read / snapshot /
reproject` — none mutate `sync_run_log`. AGENTS.md "Do Not Do" forbids
bypassing the `hai` CLI for mutations. Result: when contamination
is confined to `sync_run_log` (as F-PV14-01 produced), the maintainer's
options are (a) raw SQL DELETE (doctrine break), (b) wipe and reseed
the entire DB (over-aggressive), or (c) leave the cosmetic pollution
in place (the call we made tonight).

**Proposed v0.1.15 fix:**

Add `hai sync purge --source <s> --for-date <d> [--started-after <ts>]`.
Refuses unless all selectors resolve to ≤5 rows (prevents bulk-delete
footgun). Writes a single `runtime_event_log` row tagged
`sync_purge` with the deleted-row payloads as JSON, so the audit
chain remains queryable. Standard `hai backup` recommendation in
the help text.

**Acceptance:** unit test that creates 3 fixture rows and removes
exactly the targeted set; integration test that the runtime_event_log
row contains the deleted payloads; refusal test for selectors that
would match >5 rows.

---

## Recommended v0.1.15 cycle disposition

Pair F-PV14-01 + F-PV14-02 as a single workstream ("**isolation +
surgical-cleanup**"). F-PV14-01 alone leaves users with an unfixable
state if a fixture leak reoccurs before F-PV14-02 lands; F-PV14-02
alone is a footgun-by-omission with no preventive backstop.

Tier (per D15): **hardening** — no governance change, no audit-chain
change, scoped to two adapter/CLI surfaces. Single-round D14
plan-audit target.
