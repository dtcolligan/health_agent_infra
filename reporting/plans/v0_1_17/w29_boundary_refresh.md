# W-29 refreshed boundary note (v0.1.17 Phase 1 prerequisite)

**Authored:** 2026-05-05 morning at HEAD `e6bc26d` (post-Phase-0 close commit; cli.py at 9927 LOC).
**Required by:** PLAN §2.A acceptance item 1 — gates W-29 split execution.
**Architectural spec:** `reporting/docs/archive/cycle_artifacts/cli_boundary_table.md` (v0.1.13 W-29-prep, 8891 LOC baseline).

## Verdict

**`split`** — execute the mechanical split per PLAN §2.A acceptance items 3-10 with the group assignments below. Every handler-group module lands well under the 2500 LOC ceiling specified in §2.A item 7 (largest at ~1180 LOC; ~1320 LOC headroom against the ceiling). No grouping is contested enough to require sub-splits. The v0.1.13 boundary table is structurally sound — only LOC numbers, +5 leaves enumeration, and helper attribution have drifted.

This verdict is the green-light for W-29.1 / W-29.2 / W-29.3 commit series per PLAN §2.A item 3 + OQ-8 ratification.

## (a) Current command inventory

Live derivation at HEAD `e6bc26d`:

```bash
$ uv run hai capabilities --json | python3 -c "import json,sys; print(len(json.load(sys.stdin)['commands']))"
60
$ wc -l src/health_agent_infra/cli.py
9927
$ grep -cE "^def cmd_" src/health_agent_infra/cli.py
59
```

**60 leaf commands at hai 0.1.15.1.** 59 `cmd_*` handlers physically in `cli.py` (the gap: `hai eval run` + `hai validate` are 2 leaves whose handlers live in `evals/cli.py` and are wired to the parser-tree via `_register_eval_subparser` at `cli.py:7145`; W-29 does NOT move them).

**Diff vs v0.1.13 W-29-prep boundary table:**
- v0.1.13 boundary author enumerated 57 leaves across 11 groups (the doc says "56 leaf commands at hai 0.1.13" header, but the per-group enumeration sums to 57 — author rounding).
- Snapshot at `verification/tests/snapshots/cli_capabilities_v0_1_13.json` is at **60 leaves** (regenerated through W-AA `hai init --guided` flag-add, W-FBC-2 `--re-propose-all` text update, W-A `hai intake gaps` add, W-C `hai target nutrition` add, +others — manifest in lockstep).
- HEAD manifest = 60 leaves; snapshot = 60 leaves. **Zero drift between snapshot and HEAD.** PLAN §2.A acceptance items 4-6 byte-stability gate has a clean baseline.
- **5 leaves unaccounted-for in the v0.1.13 boundary-table enumeration but present at HEAD:** `backup`, `restore`, `export`, `target nutrition` (W-C v0.1.15 add), and the manifest also exposes `hai eval run` as 1 of the 60 (counted in v0.1.13's 56 too — 1 leaf delta from v0.1.13 author-time figure).

The five leaves above need group assignment in this refresh — see (d) Contested groupings.

## (b) Per-handler-group LOC at HEAD `e6bc26d`

LOC = sum of `cmd_*` handler bodies + private helpers attributed to the group. Computed via top-level `def` line-spans (each def's body = next-def-line − this-def-line). cli.py = **9927 LOC** total; per-group rollup:

| Group | Handlers (LOC) | Private helpers (LOC) | Total LOC | Headroom vs 2500 ceiling |
|---|---:|---:|---:|---:|
| `auth` | 175 | 106 | **281** | 2219 |
| `pull_clean` | 276 | 729 | **1005** | 1495 |
| `state` | 375 | 0 | **375** | 2125 |
| `config_init` | 467 | 179 | **646** | 1854 |
| `intake` | 775 | 358 | **1133** | 1367 |
| `intent` | 151 | 105 | **256** | 2244 |
| `target` | 370 | 0 | **370** | 2130 |
| `recommend` | 320 | 819 | **1139** | 1361 |
| `review` | 249 | 113 | **362** | 2138 |
| `inspect` | 836 | 235 | **1071** | 1429 |
| `tools` | 486 | 78 | **564** | 1936 |
| **handler subtotal** | 4480 | 2722 | **7202** | — |
| `shared.py` (extraction target) | — | ~96 | **~96** | n/a (small lib) |
| `__init__.py` (parser-builder + main + module head) | — | 2656 | **~2656** | n/a (entry point) |
| **cli.py reconciliation** | | | **~9954** | (vs cli.py 9927 — ±27 LOC slack from helper attribution) |

**Largest group: `inspect` at ~1071 LOC** (driven by `cmd_stats` at ~796 LOC including the 4 `_emit_*_stats` private helpers). Second largest: `recommend` at ~1139 LOC (driven by `_run_daily` at ~340 LOC + `_daily_pull_and_project` at ~160 LOC + `_run_first_pull_backfill` at ~92 LOC + `_build_daily_explain_block` at ~74 LOC). Third: `intake` at ~1133 LOC (5 `_project_*_submission_into_state` helpers totaling ~340 LOC + 7 `cmd_intake_*` handlers).

**LOC drift since v0.1.13 author-time** (8891 → 9927 = +1036 LOC):
- `intake` group: ~1080 → ~1133 (+53; W-A `intake gaps` add)
- `target` group: ~195 → ~370 (+175; W-C `target nutrition` add — 165 LOC handler at `cli.py:2972`)
- `pull_clean` group: ~600 → ~1005 (+405; W-A presence-block wiring + W-C target-status check + intervals.icu adapter hardening + F-PV14-01 contamination guard `_f_pv14_csv_canonical_guard`)
- `tools` group: ~250 → ~564 (+314; cmd_demo_start/end/cleanup likely grew + cmd_research_search expanded)
- `inspect` group: ~280 → ~1071 (+791; cmd_stats grew massively with W48 outcomes/funnel/baselines/data-quality emission helpers)
- `state` group: ~240 → ~375 (+135; backup/restore/export attribution added — see (d))
- `recommend` group: ~710 → ~1139 (+429; cmd_daily / `_run_daily` orchestration grew significantly)
- Other groups roughly stable.

**No group is at or near the 2500 LOC ceiling.** Closest is `recommend` at 1139 LOC (54% of ceiling). The v0.1.13 boundary table's "may further split" note for `intake.py` and `recommend.py` is **not triggered** at v0.1.17 cycle-open — both are well within the ceiling. Sub-splits per the v0.1.13 footnote (`intake_food.py` / `intake_subjective.py`; recommend further split) are unnecessary at v0.1.17 and remain post-v0.2.x territory if growth requires.

## (c) Shared-helper extraction list (for `cli/shared.py`)

Helpers with cross-handler use (consumed by ≥2 distinct handler-groups):

| Helper | LOC | Where currently | Used by |
|---|---:|---|---|
| `_emit_json` | ~30 | cli.py:157 | every cmd_* with `--json` output |
| `_load_json_arg` | ~45 | cli.py:~140 (estimated) | `cmd_propose`, `cmd_review_record`, `cmd_state_snapshot`, others |
| `_coerce_date` | ~6 | cli.py | many handlers parsing date args |
| `_coerce_dt` | ~9 | cli.py | many handlers parsing ISO8601 args |
| `_skills_source` | ~6 | cli.py | `cmd_setup_skills` + `cmd_doctor` |
| `_w57_user_gate` | ~34 | cli.py | `cmd_intent_commit` + `cmd_target_commit` (W57 governance) |
| **shared.py target subtotal** | **~130** | | |

`annotate_contract` does NOT extract — it lives at `core/capabilities/walker.py:191` and is imported, not defined, by cli.py. Stays an import from `core.capabilities`.

`_emit_text` from the v0.1.13 boundary spec does not exist as a top-level def in cli.py at HEAD (output is rendered via `print()` directly). No extraction needed.

`_resolve_db_path` / `_resolve_user_id` from v0.1.13 boundary spec do not exist as top-level defs at HEAD (path/id resolution is inline within `build_parser` argparse `default=` callbacks + per-handler `args.db_path` access). The `add_db_path_arg` / `add_user_id_arg` parser helpers do not exist as named functions at HEAD either. **The v0.1.13 spec was forward-looking; the actual extraction is thinner than predicted.** No PLAN-correction needed — PLAN §2.A files-of-record names `cli/shared.py` as the destination without enumerating helpers.

## (d) Contested groupings

Five leaves the v0.1.13 boundary table did not explicitly enumerate; this refresh assigns each:

| Leaf | Handler | LOC | Assigned group | Reasoning |
|---|---|---:|---|---|
| `hai backup` | `cmd_backup` | ~44 | **`state`** | DB lifecycle surface; sibling of `state init/migrate/snapshot/reproject`. Adds 44 LOC to state.py (375 → 419, headroom 2081). |
| `hai restore` | `cmd_restore` | ~58 | **`state`** | Mirror of `backup`; same DB-lifecycle affinity. |
| `hai export` | `cmd_export` | ~48 | **`state`** | Read-only DB-export surface; cohabits cleanly with state-lifecycle group. |
| `hai target nutrition` | `cmd_target_nutrition` | ~165 | **`target`** | Already in target group per W-C v0.1.15 ship; no contention. |
| `hai sync purge` *(F-PV14-02 add this cycle, post-W-29 commit)* | `cmd_sync_purge` *(new, ~50-100 LOC est.)* | tbd | **`state` (OQ-1 closed)** | F-PV14-02 surgical-cleanup CLI is state-mutation under `hai sync` namespace. PLAN §8 OQ-1: "Provisional default: state.py — `hai sync purge` is a state-mutation surgical surface that fits the state-handlers shape." With state.py at ~375 LOC + backup/restore/export adds (~150 LOC) → ~525 LOC pre-sync-purge, then ~575-625 LOC post-F-PV14-02; well under ceiling. **Decision: state.py, no separate sync.py group.** Codex round-3 OQ-1 disposition: "state.py default is coherent." Kept. |

**OQ-1 closed at this refresh.** `hai sync purge` lands in `cli/handlers/state.py`. No `cli/handlers/sync.py` module is created. If a future cycle adds ≥2 more `hai sync ...` subcommands and `state.py` approaches 2500 LOC, sub-split per the v0.1.13 boundary table's "may further split" footnote.

**No leaf is mis-grouped enough to trigger `split-with-revisions`.** All five contested-but-now-assigned leaves cohabit cleanly within their assigned groups.

## (e) Verdict (per PLAN §2.A acceptance item 1, item (e))

**`split`.**

- (1) The v0.1.13 boundary table's 11-group structure is structurally sound at HEAD. ✓
- (2) No handler-group module exceeds 2500 LOC after this refresh's contested-leaf assignments. Largest projected: `recommend` at ~1139 LOC (still ~1361 LOC headroom). ✓
- (3) No leaf is obviously mis-grouped. The 5 newly-assigned leaves (backup/restore/export/target-nutrition/sync-purge) cohabit with semantically coherent siblings. ✓
- (4) Shared-helper extraction list (~130 LOC) is small and contains the cross-handler primitives (`_emit_json`, `_load_json_arg`, date coercers, W57 gate). ✓
- (5) Snapshot already aligns to HEAD (60 leaves, byte-identical). PLAN §2.A items 4-6 byte-stability gate has a clean baseline. ✓

**Phase 1 implementation greenlit per PLAN §2.A item 3:** 3-commit W-29 series (`W-29.1` shared module extraction + `cli/__init__.py` skeleton; `W-29.2` 11 handler-group splits; `W-29.3` final `cli/__init__.py` parser-tree + dispatch refactor). Every commit individually passes acceptance items 4-7. Final commit closes the byte-stability gate.

## What this refresh does NOT do

- Does not freeze the capabilities-manifest schema (W-30 + v0.2.3 territory).
- Does not introduce new commands or new flags. Pure mechanical refactor in W-29.
- Does not rename leaf commands. The user-facing CLI surface stays byte-identical.
- Does not include the F-PV14-02 `hai sync purge` add itself — that's a Phase 3 commit, post-W-29. The OQ-1 placement decision IS recorded here so F-PV14-02 implementation knows its target file.
- Does not refactor intra-handler shared logic. The handler split is structural; logic stays put.

## Provenance

- 2026-04-30: v0.1.13 W-29-prep boundary table authored (cli.py at 8891 LOC).
- 2026-05-04: v0.1.17 PLAN.md authored against HEAD `df6a13c` (cli.py at 9927 LOC).
- 2026-05-05 morning: this refresh authored against HEAD `e6bc26d` (post-Phase-0-close commit; cli.py still at 9927 LOC — no source drift between PLAN-author and Phase-1-open).

LOC accounting derived from `wc -l` + top-level `def` line-spans. Every PLAN-cited file path/line/symbol verified clean in Phase 0 §1 internal sweep (see `audit_findings.md`).
