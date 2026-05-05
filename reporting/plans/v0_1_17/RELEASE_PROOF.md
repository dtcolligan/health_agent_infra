**Tier: substantive** (per AGENTS.md D15 first-line declaration —
≥1 release-blocker workstream AND ≥10 days estimated effort.)

# v0.1.17 Release Proof — Maintainability + eval substrate consolidation

**Cycle close:** 2026-05-05.
**HEAD at ship:** to be stamped at the version-bump commit.
**Author:** Claude Opus 4.7 (1M context) — autonomous Phase 0 → ship
implementation under maintainer ratification.

## §1 Workstream completion

| W-id | Title | Status | Acceptance |
|---|---|---|---|
| **W-29** | cli.py 9927-LOC mechanical split | **closed** | All 10 acceptance items pass (PLAN §2.A 1-10). Refreshed boundary note at `w29_boundary_refresh.md`; verdict `split`. 11 handler-group modules each <2500 LOC; manifest byte-stable; new `test_cli_handler_dispatch_smoke.py` (12 smokes) + `test_cli_handler_group_loc_ceiling.py` ship. |
| **W-30** | Capabilities-manifest schema-freeze regression test (test-only) | **closed** | `test_capabilities_manifest_schema.py` ships, pins field names + types (top-level + per-command + per-flag) without value pinning (delegated to `test_cli_parser_capabilities_regression.py`). Schema freeze itself remains scheduled for v0.2.3. |
| **W-AH-2** | Synthetic scenario fixture expansion 35 → 132+ | **closed** | 135 fixtures (135 = 6×20 + 15 synthesis). 100% pass-rate via `hai eval run --scenario-set all`. New `test_scenario_corpus_coverage.py` enforces per-domain ≥20 + synthesis ≥12. Per-fixture interactive author-then-validate per v0.1.14 REPORT.md §5.3 — fixtures that initially failed live validation were iterated to pass, never silently shipped. |
| **W-AI-2** | `hai eval review` CLI surface | **closed** | 5 subcommands (list/show/tag/dismiss/export). Per-user persistence at `~/.local/share/health_agent_infra/eval_review.json` per OQ-2. Snapshot lockstep regenerated in this commit per F-PLAN-R2-04. |
| **W-AM-2** | 4 fork-deferred escalate-tagged scenarios | **closed** | sleep_004 + strength_004 + stress_004 + nutrition_004; cumulative `w-am-adversarial-escalate` count 6 of 6 (recovery + running + sleep + strength + stress + nutrition). Per-scenario interactive validation per v0.1.14 §5.3 — every fixture fires its expected forced_action against live runtime. |
| **W-Vb-4** | Persona-replay residual P7..P12 | **closed** | F-PHASE0-07 (Phase 0 finding) verified that all 13 personas close cleanly at HEAD with 0 findings + 0 crashes; effort budget refined from 5-7d → ~0.5d (documentation + opt-in regression test). New `test_w_vb_4_persona_matrix_baseline.py` pins 12-of-12 closure (opt-in via `HAI_RUN_PERSONA_MATRIX=1`; not a CI gate per AGENTS.md D10). |
| **F-PV14-02** | `hai sync purge` surgical sync_run_log cleanup | **closed** | `core/sync/purge.py` + `cmd_sync_purge` ship. 5-row safety cap; `runtime_event_log` audit row on commit; `--dry-run` is read-only. `agent_safe=False`. 6 acceptance tests pass. |
| **W-B** | `hai intake weight` + `body_comp` table + migration 026 | **closed** | Migration 026 lands; table + 2 indexes + `CHECK(source = 'user_authored')` constraint. Multi-measurement-per-day append semantics (OQ-4). Weight (20-250 kg) + body-fat-percent (0-75) validation. JSONL audit at `<base_dir>/body_comp_intake.jsonl`. 10 acceptance tests pass. |
| **W-D arm-2** | Partial-day nutrition end-of-day macro projection | **closed** | New `core/target/store.py::get_active_macro_targets()`. Internal merge inside `build_snapshot()` at lines ~895-952. `ClassifiedNutritionState` extends with 4 optional `projected_eod_*` fields. `_nutrition_classified_to_dict()` serializes them. `DEFAULT_THRESHOLDS["classify"]["nutrition"]["projection_mode"] = "target_anchored"` default leaf. Linear-extrapolation reachable via threshold override. 6 acceptance tests pass. |
| **W-C-EQP** | EXPLAIN QUERY PLAN stability assertion | **closed** | `test_w_c_target_nutrition.py::test_migration_025_preserves_pre_existing_target_rows_byte_stable` extended with EXPLAIN QUERY PLAN check. Asserts the W-A active-window query uses one of the migration-020 indexes (planner picks `idx_target_domain_type` for the IN-filter predicate, which is correct selectivity behaviour). |

## §2 Standard substantive-cycle ship gates

```
✓ Full pytest suite (narrow gate): 2683 passed, 4 skipped (~2 min)
✓ uvx mypy src/health_agent_infra: Success — 147 source files, 0 errors
✓ uvx bandit -ll -r src/health_agent_infra: 0 medium / 0 high severity
✓ hai capabilities --json: byte-stable against snapshot
✓ hai capabilities --markdown: byte-stable against agent_cli_contract.md
✓ Persona matrix: 13/13 personas, 0 findings, 0 crashes (~5 min, opt-in)
✓ hai eval run --scenario-set all: 135/135 PASS (100% per W-AH-2 §2.C item 5)
```

## §3 W-29-specific ship gates (release-blocker)

```
✓ Refreshed boundary note authored: w29_boundary_refresh.md (verdict: split)
✓ test_cli_handler_group_loc_ceiling.py: 11 modules all <2500 LOC
✓ test_cli_handler_dispatch_smoke.py: 12 smokes (1 per handler-group + coverage)
✓ Manifest byte-stable across the 3-commit W-29.1/.2/.3 series + each
  W-29.2.N per-group split (auth → review → target → state → intent →
  tools → config_init → inspect → pull_clean → intake → recommend)
```

## §4 W-AH-2-specific ship gates

```
✓ test_scenario_corpus_coverage.py: per-domain ≥20 + synthesis ≥12 ✓
✓ hai eval run --scenario-set all returns OK exit code (100% pass-rate)
✓ Fixtures align to existing scenario-runner contract (singular `tag` field;
  expected.classified + expected.policy.forced_action / fired_rule_ids;
  no new harness extension)
```

## §5 Out-of-scope items (explicit deferrals)

None. All 10 W-ids in PLAN §1.2 closed cleanly. No partial-closure or
fork-deferral.

## §6 Cross-cutting work (per PLAN §3)

```
✓ AGENTS.md "Settled Decisions" — W-29 closure appended (provenance-
  preserving per F-PLAN-10); W-30 schema-freeze destination retained.
✓ AGENTS.md "Do Not Do" — cli.py-split clause retired (provenance tail
  preserved per F-PLAN-10); W-30 schema-freeze clause retained.
✓ pyproject.toml: 0.1.15.1 → 0.1.17
✓ AUDIT.md: new v0.1.17 row + round table + outcome verdict
✓ CHANGELOG.md: v0.1.17 entry summarising all 10 W-ids
✓ reporting/docs/agent_cli_contract.md: regenerated (snapshot lockstep)
✓ verification/tests/snapshots/cli_capabilities_v0_1_13.json: regenerated
✓ verification/tests/snapshots/cli_help_tree_v0_1_13.txt: regenerated
```

## §7 Notes for the maintainer

- **D15 IR pending.** The Codex implementation review is the next
  audit step. Per AGENTS.md substantive-cycle pattern, the IR prompt
  is authored at ship-time + handed to the maintainer to launch.
  This release proof reflects ship-readiness up to but not through
  IR; the IR may surface further nits to close-in-place before PyPI
  publish.
- **Test-infra change at W-29.2.9 / W-29.2.11.** Tests that monkeypatch
  cli-private *module attributes* (e.g. `_build_live_adapter`) now target
  `cli.handlers.pull_clean.X` / `cli.handlers.recommend.X` directly —
  the `cli` re-export binding doesn't propagate to source-module local
  bindings. Class-attribute patches (e.g.
  `monkeypatch.setattr(cli_mod.CredentialStore, "default", ...)`) continue
  to work because the class object is identity-shared.
- **F-PHASE0-01 nit closed** at W-AI-2 commit time (judge_adversarial
  count was cited as 31 in PLAN §2.C/§2.D/§6; actual is 30). The
  W-AI-2 implementation reads dynamic at-commit corpus via
  `_walk_corpus`; no hard-coded count.
- **F-PHASE0-08 nit closed** at W-Vb-4 — runner produces `result.json`
  + `today.txt`, not `recommendation.json` (PLAN §2.F item 3 cite was
  imprecise).

## §8 Persona run-time + eval-corpus run-time

- Persona matrix: ~5 min for 13 personas (matches v0.1.14 baseline; W-AH-2
  expansion did not impact persona runtime — separate code paths per
  F-PLAN-03).
- `hai eval run --scenario-set all`: ~6-8 sec for 135 fixtures + 30
  judge_adversarial enumeration (judge_adversarial is shape-only per
  v0.1.14 W-AI; v0.2.2 W58J wires real judge calls).
