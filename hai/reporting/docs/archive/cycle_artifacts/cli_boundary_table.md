# cli.py boundary table

**Cycle.** v0.1.13 W-29-prep (CP1 prerequisite for v0.1.14 W-29).

**Purpose.** Name the proposed handler-group split for `cli.py`'s
mechanical division at v0.1.14. Every leaf command is assigned to
exactly one group. This is a *plan*, not a contract — v0.1.14 W-29's
audit may revise it.

**Coupled regression contract.** The companion test at
`verification/tests/test_cli_parser_capabilities_regression.py` pins
the JSON manifest + parser-tree shape against
`verification/tests/snapshots/cli_capabilities_v0_1_13.json` and
`verification/tests/snapshots/cli_help_tree_v0_1_13.txt`. The
snapshots were frozen at v0.1.13 batch 1 (`45319da`) AFTER W-AB
`--human` + W-AE `--deep` intentional surface changes per F-PLAN-11
sequencing, and have been legitimately regenerated twice since:

| Commit | Workstream | Reason |
|---|---|---|
| `45319da` | batch 1 (initial freeze) | post-W-AB / post-W-AE F-PLAN-11 baseline |
| `03fab4f` | W-AA | adds `hai init --guided` flag + onboarding subsurface |
| `bd11be3` | W-FBC-2 | updates `--re-propose-all` help text from v0.1.12 partial-closure language to v0.1.13 full-closure semantics |

Each regeneration was an intentional v0.1.13 public-surface change
that the W-29-prep contract allows before the v0.1.14 W-29
mechanical-split freeze. v0.1.14 W-29's split must not produce any
further snapshot drift; that is the actual purpose of the
regression test. (Provenance correction added per v0.1.13 IR
round 1 finding F-IR-05.)

**Live derivation.** The leaf-command list below was generated from
`hai capabilities --json` against `cycle/v0.1.13` HEAD on 2026-04-30,
post-W-AB and post-W-AE. To regenerate after future surface changes:

```bash
uv run hai capabilities --json | python3 -c '
import json, sys
m = json.load(sys.stdin)
print(f"# {len(m[\"commands\"])} leaf commands at hai {m[\"hai_version\"]}")
for c in m["commands"]:
    print(c["command"])
'
```

The `verification/tests/test_doc_freshness_assertions.py` doc-freshness
test asserts the leaf-command count below matches the live manifest.

---

## Source-file metrics (informational)

| Metric | v0.1.13 cycle-open | Notes |
|---|---|---|
| `cli.py` total LOC | 8891 | Up from ~10k cited in CP1 — mechanical line counting differs from reported "~10k handler-group split target" |
| Top-level `sub.add_parser(...)` calls | 24 in `cli.py` + 1 in `evals/cli.py` | Per CP1 enumeration; verified at v0.1.13 cycle-open via grep |
| Leaf commands in manifest | 56 | From `hai capabilities --json`, post-W-AB / post-W-AE |
| Handler functions (`def cmd_*`) | ~58 | Includes nested-subcommand handlers |

---

## Proposed handler-group split (11 groups)

Groups are named by the proposed module path under
`src/health_agent_infra/cli/handlers/`. The split target per CP1 is
"1 main + 1 shared + 11 handler-group, <2500 each" — every group
below is well below 2500 LOC at v0.1.13 cycle-open.

### 1. `cli/handlers/auth.py` — credential surface

Approx 230 LOC.

| Leaf command | Handler |
|---|---|
| `hai auth garmin` | `cmd_auth_garmin` |
| `hai auth intervals-icu` | `cmd_auth_intervals_icu` |
| `hai auth status` | `cmd_auth_status` |
| `hai auth remove` | `cmd_auth_remove` |

### 2. `cli/handlers/pull_clean.py` — evidence acquisition

Approx 600 LOC. `cmd_clean` is large (~470 LOC) because it owns
multi-source normalization; v0.1.14 W-29 may further split this.

| Leaf command | Handler |
|---|---|
| `hai pull` | `cmd_pull` |
| `hai clean` | `cmd_clean` |

### 3. `cli/handlers/state.py` — DB lifecycle + projection

Approx 240 LOC.

| Leaf command | Handler |
|---|---|
| `hai state init` | `cmd_state_init` |
| `hai state migrate` | `cmd_state_migrate` |
| `hai state read` | `cmd_state_read` |
| `hai state snapshot` | `cmd_state_snapshot` |
| `hai state reproject` | `cmd_state_reproject` |

### 4. `cli/handlers/config_init.py` — config + setup

Approx 360 LOC. Includes `init` + `setup-skills` because they're the
"first-run" surface and share scaffolding helpers.

| Leaf command | Handler |
|---|---|
| `hai init` | `cmd_init` |
| `hai setup-skills` | `cmd_setup_skills` |
| `hai config init` | `cmd_config_init` |
| `hai config show` | `cmd_config_show` |
| `hai config validate` | `cmd_config_validate` |
| `hai config diff` | `cmd_config_diff` |

### 5. `cli/handlers/intake.py` — typed user inputs

Approx 1080 LOC. Largest group. v0.1.14 W-29 may split this further
(e.g. `intake_food.py` for nutrition + exercise; `intake_subjective.py`
for stress + readiness + note; `intake_sessions.py` for gym).

| Leaf command | Handler |
|---|---|
| `hai intake gym` | `cmd_intake_gym` |
| `hai intake exercise` | `cmd_intake_exercise` |
| `hai intake nutrition` | `cmd_intake_nutrition` |
| `hai intake stress` | `cmd_intake_stress` |
| `hai intake note` | `cmd_intake_note` |
| `hai intake readiness` | `cmd_intake_readiness` |
| `hai intake gaps` | `cmd_intake_gaps` |

### 6. `cli/handlers/intent.py` — W49 intent ledger

Approx 180 LOC.

| Leaf command | Handler |
|---|---|
| `hai intent training add-session` | `cmd_intent_training_add_session` |
| `hai intent training list` | `cmd_intent_training_list` |
| `hai intent sleep set-window` | `cmd_intent_sleep_set_window` |
| `hai intent list` | `cmd_intent_list` |
| `hai intent commit` | `cmd_intent_commit` |
| `hai intent archive` | `cmd_intent_archive` |

### 7. `cli/handlers/target.py` — W50 target ledger

Approx 195 LOC.

| Leaf command | Handler |
|---|---|
| `hai target set` | `cmd_target_set` |
| `hai target list` | `cmd_target_list` |
| `hai target commit` | `cmd_target_commit` |
| `hai target archive` | `cmd_target_archive` |

### 8. `cli/handlers/recommend.py` — propose + synthesize + daily

Approx 710 LOC. The "make a recommendation" pipeline.

| Leaf command | Handler |
|---|---|
| `hai propose` | `cmd_propose` |
| `hai synthesize` | `cmd_synthesize` |
| `hai daily` | `cmd_daily` |

### 9. `cli/handlers/review.py` — review schedule + record + summary

Approx 225 LOC.

| Leaf command | Handler |
|---|---|
| `hai review schedule` | `cmd_review_schedule` |
| `hai review record` | `cmd_review_record` |
| `hai review summary` | `cmd_review_summary` |

### 10. `cli/handlers/inspect.py` — read-only operator surfaces

Approx 280 LOC. The "what does the system know" group.

| Leaf command | Handler |
|---|---|
| `hai today` | `cmd_today` |
| `hai explain` | `cmd_explain` |
| `hai stats` | `cmd_stats` |
| `hai doctor` | `cmd_doctor` |
| `hai capabilities` | `cmd_capabilities` |

### 11. `cli/handlers/tools.py` — admin / demo / research / eval

Approx 250 LOC. Lower-traffic surfaces grouped by "operator-mode tool"
intent rather than feature affinity.

| Leaf command | Handler |
|---|---|
| `hai memory set` | `cmd_memory_set` |
| `hai memory list` | `cmd_memory_list` |
| `hai memory archive` | `cmd_memory_archive` |
| `hai demo start` | `cmd_demo_start` |
| `hai demo end` | `cmd_demo_end` |
| `hai demo cleanup` | `cmd_demo_cleanup` |
| `hai research search` | `cmd_research_search` |
| `hai research topics` | `cmd_research_topics` |
| `hai exercise search` | `cmd_exercise_search` |
| `hai eval run` | `cmd_eval_run` |
| `hai validate` | `cmd_validate` |
| `hai planned-session-types` | `cmd_planned_session_types` |

---

## Shared module proposal

`cli/shared.py` would carry helpers used across handlers:

- `_emit_json` / `_emit_text` (output formatting)
- `_resolve_db_path`, `_resolve_user_id` (path/id helpers)
- `annotate_contract` re-export (capabilities annotation)
- Common arg-parsing helpers (`add_db_path_arg`, `add_user_id_arg`)

`cli/__init__.py` (the new `main`) would:

- Build the parser tree (calling each handler module's `register(...)`)
- Dispatch to the resolved subcommand handler

---

## Verdict to record at v0.1.13 RELEASE_PROOF

CP1's gate: **"v0.1.14 W-29 has a clear go/no-go verdict from the
boundary audit."** Per W-29-prep contract, three outcomes are
acceptable:

| Verdict | When | Action at v0.1.14 |
|---|---|---|
| `split` | Above table is coherent, no group exceeds 2500 LOC, no command obviously mis-grouped. | Execute the mechanical split per this table. |
| `split-with-revisions` | Above table is mostly coherent but ≥1 group exceeds 2500 LOC OR ≥1 grouping is contested. | Revise the table at v0.1.14 plan-audit; execute. |
| `do-not-split` | The split itself is wrong-shaped (e.g. shared state across handlers makes the split synthetic). | Defer split; cli.py keeps growing and v0.2.x revisits. |

**Recommended verdict (preliminary).** `split-with-revisions` —
`cli/handlers/intake.py` at ~1080 LOC and `cli/handlers/recommend.py`
at ~710 LOC are both candidate "further-split" groups, but the
boundaries are clean enough at the leaf-command level that the
mechanical split is safe to execute.

The maintainer records the final verdict in v0.1.13 RELEASE_PROOF
§2.X (W-29-prep section).

---

## Out-of-scope at this cycle

- Implementing the actual split (that's v0.1.14 W-29).
- Refactoring intra-handler shared logic.
- Renaming or reorganising the `core/` modules the handlers call
  into. The handler split is structural; logic stays put.

---

## Provenance

- Authored 2026-04-30 by Claude.
- Source: live `hai capabilities --json` at HEAD `f0ebe65`
  (cycle/v0.1.13 phase-0-gate-fires-green).
- Tactical plan reference: `tactical_plan_v0_1_x.md` v0.1.14 row.
- Cycle proposal reference: `v0_1_12/cycle_proposals/CP1.md`.
