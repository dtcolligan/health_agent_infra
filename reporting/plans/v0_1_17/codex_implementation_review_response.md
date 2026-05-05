# Codex Implementation Review — v0.1.17

**Verdict:** SHIP_WITH_FIXES
**Round:** 1

## Verification summary
- Tree state: `/Users/domcolligan/health_agent_infra`, branch `main`, `df6a13c..HEAD` = 27 commits. Pre-review tracked state was not clean: `uv.lock` was already modified; I did not touch it.
- Test surface: `uv run pytest verification/tests -q` passed (`2683 passed, 4 skipped`); `uv run hai eval run --scenario-set all` passed (`135/135`); explicit W-Vb-4 persona matrix passed with `HAI_RUN_PERSONA_MATRIX=1` (`1 passed in 172.64s`); `uvx mypy src/health_agent_infra` passed.
- Ship gates: capabilities markdown is byte-stable against `reporting/docs/agent_cli_contract.md`; wheel/sdist build completed with setuptools license warnings. `uvx bandit -ll -r src/health_agent_infra` failed with 3 Medium B608 findings, so the release gate is red.
- Governance/provenance: no new D-entry was introduced. AGENTS.md appends W-29 closure and retires only the cli.py-split Do-Not-Do clause while retaining W-30 freeze provenance. `CARRY_OVER.md` and `cycle_proposals/` are absent for this cycle.

## Findings

### F-IR-01. Bandit release gate is red on three Medium SQL findings
**Q-bucket:** ship-gates / cross-cutting code quality
**Severity:** security
**Reference:** `src/health_agent_infra/core/body_comp/store.py:174`; `src/health_agent_infra/core/sync/purge.py:110`; `src/health_agent_infra/core/target/store.py:469`
**Argument:** PLAN §6 requires `uvx bandit -ll -r src/health_agent_infra` clean, and RELEASE_PROOF §2 claims `0 medium / 0 high severity`. Re-running the exact gate fails with 3 Medium B608 findings: W-B `list_body_comp()` string-builds the WHERE clause, F-PV14-02 `resolve_purge_selectors()` does the same, and W-D/W-C target lookup still trips B608 on the f-string SQL. The target-store site has a `# nosec B608` rationale above the flagged line, but Bandit still reports the issue, so the ship gate is objectively red even if the query is judged safe by review.
**Recommended response:** fix-and-reland. Either reshape these queries so Bandit no longer flags them or place targeted, same-line `# nosec B608` suppressions with the existing rationale style, then rerun the Bandit gate.

### F-IR-02. `hai eval review show/tag/dismiss` cannot resolve judge_adversarial rows
**Q-bucket:** W-AI-2
**Severity:** correctness-bug
**Reference:** `src/health_agent_infra/evals/review.py:287`; `src/health_agent_infra/evals/review.py:308`; `src/health_agent_infra/evals/scenarios/judge_adversarial/bias_probe/ja_bp_001.json:12`
**Argument:** W-AI-2 promises the review surface over both the expanded scenario corpus and the v0.1.14 judge_adversarial fixtures. `_walk_corpus()` lists judge_adversarial fixtures by `fixture.get("scenario_id") or fixture_path.stem`, so `list --corpus judge_adversarial` exposes `ja_bp_001`. `_find_in_corpus()` only matches `fixture.get("scenario_id") == scenario_id`; judge_adversarial fixtures carry `fixture_id`, not `scenario_id`. Repro: `hai eval review list --corpus judge_adversarial` returns `ja_bp_001`; `hai eval review show --scenario-id ja_bp_001` exits `3` with `scenario_id='ja_bp_001' not found in fixture tree`. `tag` and `dismiss` call the same lookup path, so they are broken for that corpus.
**Recommended response:** fix-and-reland. Normalize `_find_in_corpus()` to the same id contract as `_walk_corpus()` (`scenario_id` or `fixture_id` or stem), and add judge_adversarial coverage for `show`, `tag`, and `dismiss`.

### F-IR-03. W-D arm-2 missed the promised `hai explain` projection rendering test/surface
**Q-bucket:** W-D arm-2
**Severity:** scope-mismatch
**Reference:** `reporting/plans/v0_1_17/PLAN.md:462`; `verification/tests/test_w_d_arm2_target_plumbing.py:21`; `verification/tests/test_w_d_arm2_target_plumbing.py:325`; `src/health_agent_infra/core/explain/render.py:48`
**Argument:** PLAN §2.I acceptance item 6 requires an explain rendering test proving `hai explain --as-of <today>` surfaces both observed calories and `projected_eod_kcal`. The W-D test file repeats item 6 in its module docstring, but implemented tests jump from item 5 to item 7; there is no explain snapshot/test. The explain serializer still emits plan/proposals/firings/recommendations/reviews/user_memory only, with no nutrition classified-state block or projected_eod fields. The core classifier and `build_snapshot()` plumbing otherwise look correctly implemented, but the operator-facing audit-chain surface promised by PLAN is absent.
**Recommended response:** fix-and-reland. Add the explain rendering path and a snapshot or CLI test that proves observed and projected nutrition values are visible after arm-2 fires.

### F-IR-04. Most new domain fixtures pass classification vacuously
**Q-bucket:** W-AH-2
**Severity:** acceptance-weak
**Reference:** `reporting/plans/v0_1_17/PLAN.md:189`; `reporting/plans/v0_1_17/PLAN.md:193`; `src/health_agent_infra/evals/runner.py:312`; `src/health_agent_infra/evals/scenarios/stress/stress_005_low_stress_with_high_battery.json:23`
**Argument:** The fixture contract says every new domain fixture has `expected.classified` plus `expected.policy`. In the 100 added non-judge fixtures, 5 are synthesis fixtures and 95 are domain fixtures; 94 of those 95 domain fixtures omit `expected.classified`. The runner treats a missing block as `{}` and marks the `classified_bands` axis pass without checking any band. Example: `stress_005_low_stress_with_high_battery.json` asserts only empty policy firings. This preserves `135/135 PASS`, but it does not validate the classifier paths the expanded corpus was meant to cover.
**Recommended response:** fix-and-reland or explicitly narrow the contract. If W-AH-2 is intended to validate classifier coverage, add meaningful `expected.classified` assertions to the new domain fixtures.

### F-IR-05. Locally built wheel includes deleted `health_agent_infra/cli.py`
**Q-bucket:** ship-gates / W-29 packaging
**Severity:** provenance-gap
**Reference:** `dist/health_agent_infra-0.1.17-py3-none-any.whl`; `build/lib/health_agent_infra/cli.py`; absent from `src/health_agent_infra/cli.py`
**Argument:** The built wheel contains both `health_agent_infra/cli.py` (385904 bytes, stale deleted source) and the new `health_agent_infra/cli/__init__.py`. Python resolves `health_agent_infra.cli` to the package in an installed probe, so this did not break import resolution, but the artifact still ships a deleted pre-split file. That weakens the W-29 packaging/provenance gate and could confuse artifact inspection.
**Recommended response:** fix-and-reland if this reproduces from the maintained release toolchain; otherwise clean `build/`, `dist/`, and egg-info before publish and add a wheel-content smoke check that refuses deleted source paths.

### F-IR-06. Unnamed runtime-contract paper planning docs landed inside the cycle diff
**Q-bucket:** absences / provenance discipline
**Severity:** nit
**Reference:** `d06d694`; `reporting/plans/hai_runtime_contract_paper/DRAFT_PAPER.md`; `reporting/plans/hai_runtime_contract_paper/IMPLEMENTATION_PLAN.md`
**Argument:** The F-PV14-02 commit adds a 606-line `reporting/plans/hai_runtime_contract_paper/` subtree, but PLAN, RELEASE_PROOF, and REPORT do not name this as shipped scope or a deferred artifact. The files are future-facing HACO-Bench/runtime-contract paper planning material, not part of any v0.1.17 W-id.
**Recommended response:** accept-as-known only if the maintainer deliberately wants these planning docs in-tree now; otherwise move them to the intended future cycle or name them in release notes/proof as an out-of-band planning addition.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-29 | PASS_WITH_NOTE | Handler split holds: 11 handler modules, no `cmd_*` in `cli/__init__.py`, every handler module <2500 LOC, W-29 split range did not regenerate snapshots. Packaging note in F-IR-05. |
| W-30 | PASS | `test_capabilities_manifest_schema.py` pins field names and types, not values; schema freeze remains v0.2.3. |
| W-AH-2 | FIX | `hai eval run --scenario-set all` passes 135/135, singular `tag` is used, no invented expected-token fields found; classifier assertions are missing for 94/95 added domain fixtures. |
| W-AI-2 | FIX | Five subcommands exist and persistence path is implemented, but `show/tag/dismiss` cannot operate on judge_adversarial fixtures listed by the same surface. |
| W-AM-2 | PASS | Cumulative `w-am-adversarial-escalate` count is 6/6; each uses existing runner policy assertions with no harness extension. |
| W-Vb-4 | PASS | Opt-in persona matrix pin passed explicitly with `HAI_RUN_PERSONA_MATRIX=1`. |
| F-PV14-02 | FIX | Functional purge behavior passes tests: 5-row cap, 6-row refusal, audit payload, `agent_safe=False`; Bandit still flags the new purge selector SQL. |
| W-B | FIX | Migration 026, enum/source contract, append semantics, and `agent_safe=False` coverage look correct; Bandit flags the new body_comp list query. |
| W-D arm-2 | FIX | Core projection/state shape is mostly correct: build_snapshot internal merge, optional `projected_eod_*` dataclass fields, omit-when-None serializer, full-tree linear override, and `protein_sufficiency_band="met"` all pass. The `hai explain` rendering acceptance item is missing, and target-store SQL trips Bandit. |
| W-C-EQP | PASS | The migration-025 query-plan test now asserts indexed access and permits the planner's `idx_target_domain_type` choice. |

## Open questions for maintainer
- Should `reporting/plans/hai_runtime_contract_paper/` remain in the v0.1.17 diff and be named in the release artifacts, or should it move to the cycle that owns that paper/benchmark work?
