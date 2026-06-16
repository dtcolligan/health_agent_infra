# Pre-Lock Work Inventory

**Lock target:** 2026-06-22 (PAPER.md calendar; PILOT_PROTOCOL.md §14).
**Status:** Final after 3 audit rounds (Claude implementer / Codex auditor) plus 6 Dom design decisions on 2026-06-01.
**Source decision row:** PAPER.md D-24.

This document is the engineering execution plan for the pre-lock work the July pilot needs. Each item lists source, gap, and pre-lock acceptance criterion. PAPER.md D-24 records the design decisions; the operational details live here.

Scope OUT (lock-day-only, intentionally absent):
- D-O-01 model-class selection.
- `scorer_config.paper_v1.json` status flip draft -> frozen.
- §14 Locked Hashes SHA-256 table population (`scripts/collect_lock_hashes.py` mechanically produces this).
- Any model-backed API call.

## Dom's 2026-06-01 design decisions

1. **DR-9 stays active.** A6 (Fireworks adapter) + A10 (switch evaluator) are in scope.
2. **§8 amendment authorized.** After `full_contract` completes, evaluate gate A; if it passes, run n=1 gate-B prelude across the 5 no-X modes on the 14 safety-constrained tasks (~70 calls, ~$0.05 at 7B Together pricing); evaluate gate B; switch iff both pass. Implemented by item A12.
3. **Multi-turn history format: standard chat-completion messages.** The model's emitted action is recorded as the `assistant` turn verbatim; each observation is returned as a `user` message. No provider-native `tool_calls` are synthesized (the operator contract is content-JSON; fabricating tool calls would misrepresent the evaluated transcript). Native to Together / Fireworks / Anthropic. Affects A1 + A6. Amended 2026-06-02 in WP-A1, reversing the original `assistant` + `tool` framing.
4. **Fresh fixture per rep.** A2 hermeticity criterion locks fresh-per-rep policy.
5. **Malformed-output trajectory representation: new `invalid_output` step_type.** Affects A1 + trajectory schema.
6. **Cost / wall-time enforcement granularity: between turns.** Affects A2 + A4.

---

## Tier A. Blocks lock or blocks the July pilot

### A1. Multi-turn agent loop, observation-feedback contract, and invalid-output handling

**Status:** shipped 2026-06-02 (commit `2310245`, WP-A1), with
wire-format doc reconciliation in `7a63a1f`.

**Source:** PILOT_PROTOCOL.md §4 multi-turn shape; §5 row "Malformed JSON action ... No retry. Record turn as `invalid_command` violation."

**Gap:** `harness/core.py::run_operator_actions` executes a pre-supplied action list. `harness/together.py::run_together_model_action` calls the model once and runs one action. No loop. No representation for malformed model output.

**Pre-lock criterion:**
- Loop exists; max_turns=7 enforced.
- Multi-turn history sent to the model as standard chat-completion messages: the model's emitted action is the `assistant` turn verbatim, each observation is returned as a `user` message, no synthesized `tool_calls` (Dom decision 3, amended 2026-06-02). Affects Together / Fireworks / Anthropic adapter wire format identically.
- Unit test: turn N+1 prompt contains the previous observation record verbatim, including `exit_code`, `stdout_ref`, and any `mechanism_disabled` markers.
- Unit test: turn N+1 prompt contains the previous turn's `invalid_output` step when the model emitted malformed JSON on turn N.
- Trajectory schema gets a new `invalid_output` step_type (Dom decision 5) carrying raw model output text and parse-error reason. Migration: existing trajectories have no `invalid_output` steps; backward-compat is free.

### A2. Pilot orchestrator with full §11 triage and §12 layout

**Status:** shipped 2026-06-10 (commit `be52fcc`, WP-A2), with
protocol-artifact reconciliation pushed in `96ad77c`. A3 contamination
abort behavior folded into the A2 orchestrator packet.

**Source:** §10 outer-loop ordering; §12 `runs/pilot/<UTC_iso_minute>_lock-<short_sha>/` layout, latest-symlink semantics; §3 per-condition cost cap and wall-time ceiling; §11 disposition tree; SPEC.md hermetic recipe.

**Gap:** no entry-point drives n=3 x 28 x 7. `runs/pilot/` does not exist. No writers for `pilot_manifest.json`, `condition_summary.json`, `condition_index.json`. No cumulative wall-time tracker. No latest-symlink handling. No hermeticity-across-turns assertion. No fixture-reset-between-reps.

**Pre-lock criterion:**
- Orchestrator runs end-to-end against a mock transport; produces the §12 directory layout; no live API calls in tests.
- Per-condition cost meter tracks running spend; halt **between turns** when cumulative >= USD 100 (Dom decision 6). At most one overshoot turn per condition.
- Per-condition wall-time meter tracks elapsed; halt **between turns** when >= 240 min (Option B) / 120 min (Option C).
- §11 disposition tree implemented and tested for each row: cost halt, wall-time halt, contamination abort (delegated to A3), provider-outage pause (delegated to A5), direct-state-write breach abort under M5/M6-active mode, clinical-claim-under-full-contract abort, adapter-error halt, single retry-exhausted turn (continue), >=3 retry-exhausted turns (task fail + advance).
- Latest-symlink advances only on `run_outcome=completed`; aborted / contaminated runs preserve their dir but symlink does not point to them.
- `condition_summary.json` writes `abort_reason` per §11.
- **Hermeticity across turns:** every turn within a single task runs against the same redirected fixture state (`HAI_HERMETIC=1`, `HAI_STATE_DB`, `HAI_BASE_DIR`, `HOME`, `XDG_CONFIG_HOME`, `HAI_RUNTIME_MODE`, `HAI_INVOCATION_CONTEXT` all preserved per SPEC.md hermetic recipe). No turn leaks state outside the fixture. Tested by asserting all subprocess env vars are present and identical across turns of a single task.
- **Fixture lifecycle between reps: fresh fixture per rep** (Dom decision 4). Fixture rebuilt from scratch before each rep. Test injects a stateful side-effect on rep_01 and asserts the state is absent on rep_02. Preserves §9 median independence.
- **Fixture lifecycle between conditions:** every condition starts from a fresh fixture root; no leakage between `runtime_mode_<X>` directories. Tested.

### A3. Real-time contamination abort

**Status:** shipped 2026-06-10 as part of WP-A2 (commit `be52fcc`);
covered by the orchestrator's post-rep disposition tests.

**Source:** §6 post-task hook reads score JSON; aborts condition on `mechanism_disabled_unexpected` or `full_contract` emitting any `mechanism_disabled` marker.

**Gap:** scorer records `mechanism_disabled_unexpected` (D-15), but no orchestrator-side hook reads scores and aborts.

**Pre-lock criterion:** abort triggered on injected contamination; clean conditions continue; `abort_reason` of `contamination_detected` or `full_contract_unexpected_marker` recorded with the offending mechanism in `condition_summary.json`. Tested via synthetic scores fed into the orchestrator under fake transport.

### A4. Per-step trajectory metadata

**Source:** §4 ratified row: "Record `wall_time_ms`, `prompt_tokens`, `completion_tokens`, `cost_usd_estimate` as trajectory step metadata."

**Gap:** Together adapter writes token usage and cost to `provider_reports/<call>.json`, not to trajectory step metadata. A2's between-turns cost / wall-time enforcement and B2's per-mechanism cost rollup depend on these fields living on the trajectory.

**Pre-lock criterion:** model-driven trajectory steps carry these four keys; missing-value semantics defined (None vs absent); existing Together-adapter tests updated to assert presence; A2's cost / wall-time meters consume from trajectory step metadata.

**Status:** shipped 2026-06-02 (commit `ccc90dd`, WP-A4). Codex-audited: plan PASS_WITH_CHANGES (3 corrections folded) → implementation PASS. Option A (fields nested under step `metadata`, no schema change); `elapsed_ms`→`wall_time_ms` rename; provider-neutral `ModelTurnResult` threading seam; numeric-or-None runtime guard. Missing-value rule: rule_baseline + `run_model_response_action` (no provider call) omit the keys; model-loop action steps carry them present, value-or-None.

### A5. Retry / rate-limit middleware and outage detection

**Status:** shipped 2026-06-03 (commit `31bfe4c`, WP-A5).

**Source:** §5 ratified table.

**Gap:** Together adapter catches TimeoutError and returns `OUTCOME_TIMEOUT` immediately. No retry loop. No 429 handling. No outage detector.

**Pre-lock criterion:**
- Wrapper around adapter implements §5: 3 retries on timeout / 503 / 504 (exponential, 1s start, 30s cap); 3 retries on 429 (Retry-After if present, else exponential 5s start, 60s cap); no retry on malformed JSON or subprocess crash.
- Retry counter recorded in trajectory step metadata.
- Outage detector: pauses condition when >50% of last 10 calls failed; passes pause signal to A2 disposition tree.
- Unit tests cover each §5 row using an injected fake transport.

### A6. Fireworks adapter (D-O-01 fallback substrate)

**Status:** shipped 2026-06-03 (commit `379d358`, WP-A6).

**Source:** `model_roster.md` condition `option_b_fallback_qwen25_32b_fireworks`; PAPER.md D-21 (DR-9); PILOT_PROTOCOL.md §8 numerical trigger. DR-9 active per Dom decision 1.

**Gap:** only Together adapter exists.

**Pre-lock criterion:** Fireworks adapter mirrors `together.py` (transport Protocol, mocked-only tests, A5 retry integration, A4 step-metadata threading, standard chat-message multi-turn format per Dom decision 3). No live calls.

### A7. pilot_manifest.json schema and writer

**Status:** shipped 2026-06-07 (commit `b61834b`, WP-A7).

**Source:** §12 ratified schema `governed_agent_bench.pilot_manifest.v1`; §14 hash-recording rows.

**Gap:** no schema file under `schema/`. No writer. No schema regression test.

**Pre-lock criterion:**
- `schema/pilot_manifest.schema.json` exists.
- Schema covers every §12 field AND every §14 hash row: `PILOT_PROTOCOL.md` SHA, `scorer_config.paper_v1.json` SHA (post-flip), `model_roster.md` SHA, `prompts/deployment_full_v1.md` SHA, `manifests/hai_0_2_0.json` SHA, `safety_constrained_subset.json` SHA, per-task SHAs (28 entries), lock date, lock commit SHA, plus §12 runtime fields (run-start UTC, git_sha, D-O-01 selection, replication n, modes executed, `run_outcome`).
- Orchestrator writes a valid manifest.
- Schema-contract test added.
- `scripts/collect_lock_hashes.py` feeds the hash table into the manifest writer.

### A8. L7 hand-authored pass trajectories (2 of 3 missing)

**Source:** §14 row "Hand-authored L7 pass trajectories verified to complete in ≤7 turns under the locked harness."

**Gap:** plural "trajectories" implied; only one exists today (`gab_l7_stale_missing_weekly_command_pass.json`, 3 turns by §4's one-action-per-turn rule). Missing pass trajectories for `gab_l7_stale_capabilities_drift` and `gab_l7_stale_v1_manifest_shape`.

**Pre-lock criterion:** all 3 L7 tasks have hand-authored pass trajectories.

**Risk:** verify the 2 missing tasks have authorable ≤7-turn pass paths before authoring. If a legitimate pass needs >7 turns, §4 max_turns=7 must be amended pre-lock, not silently violated.

**Status:** shipped 2026-06-07 (commit `86bcd68`, WP-A8). Codex-audited: plan PASS (3 corrections folded) → implementation PASS. Q1 ratified to full pass+fail pairs (not pass-only), preserving the pair invariant; counts 14→18. Both pass paths measured at 3 turns against the real scorer, so §4 max_turns=7 stands un-amended (the risk did not fire). Doc reconcile (PAPER.md + benchmark README 14→18) bundled in.

### A9. L7 ≤7-turn replay test

**Source:** §14 row "Captured as a trajectory-replay test artifact in the lock commit."

**Gap:** no test asserts turn count of hand-authored L7 pass trajectories under the locked harness.

**Pre-lock criterion:** test under `benchmark/verification/tests/` replays each L7 pass trajectory through the harness and asserts `turn_count <= 7`. Definition of "turn" matches A1's loop counter (one model action = one turn; `final` and `refusal` count). Lands after A1 + A8.

**Status:** shipped 2026-06-07 (commit `86bcd68`, WP-A9). Codex-audited: plan PASS → implementation PASS. `test_l7_turn_budget.py`: `_TURN_STEP_TYPES = {command, refusal, final, invalid_output}` pinned to A1's action set (observations don't count). Discovery is task-derived from `tasks/l7/*.json` with a coverage guard asserting exactly one pass trajectory per L7 task id (stronger than a glob), then asserts each ≤7 turns; measured 3.

### A10. DR-9 7B->32B switch evaluator

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit). WP-A11/B3 exposes `dr9_ready_inputs` in
`pilot_h1_mechanism_summary.json`; this packet adds
`results/dr9_switch.py`, wires `write_pilot_evidence_tables()` to emit
`dr9_switch_decision.json` adjacent to
`pilot_h1_mechanism_summary.json`, and intentionally does not implement
live model switching.

**Source:** PAPER.md D-21 (DR-9); PILOT_PROTOCOL.md §8 ratified numerical trigger; §8 amendment authorized via Dom decision 2.

**Gap:** no code computes and records this decision.

**Pre-lock criterion:**
- Evaluator reads gate-A evidence (from `full_contract`'s 14 safety-constrained pass rate) and gate-B evidence (from the n=1 prelude that A12's amendment inserts).
- Emits a structured `dr9_switch_decision.json` adjacent to `pilot_h1_mechanism_summary.json`.
- Verdict carries both gate evaluations (subset saturation count, per-mechanism delta count under §7 thresholds) and the overall switch flag.
- Unit tests: synthetic evidence that should trigger switch triggers it; evidence that fails either gate does not.
- Depends on A6 (Fireworks substrate), A11 (§7 verdict logic for gate B), A12 (§8 / §10 amendment defining when the evaluator fires).

### A11. §7 falsification verdict generator

**Status:** shipped 2026-06-15 (commit `dbc6656`, WP-A11/B3).
Implemented by `results/pilot_evidence.py` and
`test_pilot_evidence.py` over synthetic A2 run artifacts.

**Source:** PILOT_PROTOCOL.md §7 ratified per-mechanism falsification rules; §12 names `pilot_h1_mechanism_summary.json` as a required pilot artifact.

**Gap:** no code applies the §7 rules to evidence. §7 is pre-registered; should be mechanically executable before model evidence exists.

**Pre-lock criterion:**
- Generator reads the pilot evidence table (or, pre-lock, the static oracle-pair isolation matrix as smoke-test substrate), applies §7 rules, emits `pilot_h1_mechanism_summary.json` matching the §12 schema.
- Per-mechanism output reports both binary-leg result (where applicable) and 5pp-delta result (where applicable), separate for static / live / model-backed tiers per D-22.
- Tests: synthetic "all clean" evidence yields zero falsifications; synthetic "M7 leaks under full_contract" yields the right falsification flag.

### A12. PILOT_PROTOCOL.md §8 / §10 amendment for DR-9 timing

**Status:** shipped 2026-06-01 (commit `b1863de`, WP-A12).

**Source:** Dom decision 2 (2026-06-01). Resolves the structural defect where §8 says "evaluate switch after full_contract" but the switch criterion requires no-X deltas that §10 ordering makes unavailable at that point.

**Gap:** ratified §8 contradicts itself. Cannot implement A10 against an inconsistent spec.

**Pre-lock criterion:**
- §8 rewritten: after `full_contract` completes, evaluate gate A; if gate A passes, insert a gate-B prelude (n=1 across the 5 no-X modes on the 14 safety-constrained tasks, ~70 calls, ~$0.05 at 7B pricing); evaluate gate B; switch iff both pass; if gate A fails, DR-9 does not fire and pilot proceeds with 7B per §10.
- §10 amended to document the prelude insertion conditional on gate A.
- §3 cost-budget table updated to acknowledge the ~$0.05 prelude overhead.
- PAPER.md D-21 wording reconciled with the amended §8.
- Plan-mode trigger: PILOT_PROTOCOL.md active-content edit. Surface to Dom before commit.

**Doc-only packet (no code). Lands before A10.**

---

## Tier B. Defends lock under audit

### B1. M7 detector negative-control corpus (size 84 stratified)

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit). Corpus:
`refusal_negative_controls/m7_benign_negative_controls.jsonl`; test:
`test_m7_negative_controls.py`.

**Source:** PILOT_PROTOCOL.md §7 "M7 binary-leg sensitivity (acknowledged)" — single detector false-positive on benign output falsifies M7 attribution. Protocol names lock-day verification against a curated negative-control set.

**Gap:** the set does not exist.

**Pre-lock criterion:**
- Corpus size at least 84 (matches the 84 model-backed `full_contract` trajectories the §7 binary rule is sensitive to).
- Stratified across: task families (L1 / L2 / L5 / L6 / L7), `final` / `refusal` narration styles, clinical-adjacent wellness language, JSON-exempt surfaces.
- Test asserts the M7 detector (`hai/src/health_agent_infra/core/refusal/clinical.py` + `banned_clinical_phrases.txt`) emits zero clinical-claim signals over the corpus.

### B2. condition_summary.json schema + writer with even-split cost reconciliation

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit). `condition_summary.schema.json` now uses
`governed_agent_bench.condition_summary.v1` and requires
per-mechanism cost, diagnostic cost, and reconciliation fields.

**Source:** §12 ratified "per-mode aggregate cost (incl. per-mechanism rollup of cost_usd_estimate from §4), wall-time, abort_reason if any."

**Gap:** no schema, no writer. §12 does not specify the per-mechanism aggregation rule.

**Pre-lock criterion:**
- Schema file + writer.
- Per-mechanism cost allocation: for each trajectory step with `cost_usd_estimate`, split equally across the task's declared `load_bearing_mechanisms`; track non-load-bearing diagnostic cost separately.
- Reconciliation invariant: sum of per-mechanism costs + diagnostic bucket = sum of per-step `cost_usd_estimate` for the condition.
- Tests verify the reconciliation invariant on synthetic data and zero double-counting across multi-mechanism tasks.

### B3. pilot_evidence_table.{json,csv} generator

**Status:** shipped 2026-06-15 (commit `dbc6656`, WP-A11/B3). Emits
`pilot_evidence_table.json`, `pilot_evidence_table.csv`, and
`pilot_h1_mechanism_summary.json` from A2 run directories.

**Source:** §12 ratified per-row `task × mode × rep × scored metrics + evidence_tier`; §11 ratified `diagnostic_only` tagging for aborted-condition tasks.

**Gap:** no generator.

**Pre-lock criterion:** generator reads `runs/pilot/<dated>/conditions/.../tasks/.../rep_NN.score.json` tree, emits both serializations, applies §11 evidence_tier tagging. Tested with synthetic per-rep score files.

### B4. PAPER.md and PILOT_PROTOCOL.md cross-reference staleness reconciliation

**Status:** shipped 2026-06-02 (commit `8198ec0`, WP-B4). Codex-audited rounds 1–3; substantive PASS at round 2.

**Source:** PAPER.md Engineering Plan row "Pilot protocol document | Not started." contradicts PILOT_PROTOCOL.md §1-§13 ratified 2026-05-27. PAPER.md is the cold-start single source of truth; a contradiction at the top of the cold-start chain is an audit-defensibility hazard.

**Gap:** row content rot.

**Pre-lock criterion:**
- PAPER.md row updated to reflect content ratification (2026-05-27) and lock target (2026-06-22 per §14).
- Any other PAPER.md ↔ PILOT_PROTOCOL.md ↔ SPEC.md ↔ scorer_config drift folds in here.
- Plan-mode trigger: PAPER.md active-decisions / engineering-plan edit; surface to Dom before commit.

---

## Tier C. Risk reduction pre-lock

### C1. Provider-IDs / pricing dry-run probe

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit). `provider_probe.py` emits JSON/Markdown,
defaults to no live network, supports `--live` read-only metadata/docs
checks, and guards against chat/completions/messages/generation
endpoints.

**Source:** §14 row "Provider IDs and pricing verified against live vendor docs as of the lock date."

**Gap:** no script. Manual lookup under lock-day pressure.

**Pre-lock criterion:** script probes Together / Fireworks / Anthropic `/v1/models` (read-only, no chat-completion); confirms each `condition.model_id` resolves; cross-checks public pricing against `together.py::TOGETHER_QWEN25_7B_PRICING` (and any analogous Fireworks / Anthropic constants once A6 lands). No model invocation. Markdown summary for the lock commit.

### C2. PILOT_PROTOCOL.md §13 phrasing reconciliation

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit).

**Source:** §13 conditional "If §7 §reproduce_offline.py emits an aggregated adversarial summary artifact ..." is stale; the generator (`results/adversarial_summary.py`) exists and `reproduce_offline.py` records the artifact in the offline manifest.

**Gap:** stale conditional phrasing. The artifact itself is runtime output, NOT a committed CSV, and NOT part of the §14 hashed surface.

**Pre-lock criterion:** §13 rewritten in indicative with a one-line clarification that the artifact is generated output and not part of the §14 hashed surface.

### C3. SPEC.md ↔ PILOT_PROTOCOL.md ↔ scorer_config drift audit

**Status:** implemented in the current Codex working tree (pending
Claude audit + Dom commit). Reconciled active docs in place:
`SPEC.md`, `PILOT_PROTOCOL.md`, `schema/README.md`, and
`results/README.md`; no `PAPER.md` edit was needed.

**Source:** SPEC.md predates the recent ratification rounds; PILOT_PROTOCOL.md §12 specifies new directory layout, schemas, manifest keys.

**Gap:** SPEC.md may name file paths or schema versions that disagree with PILOT_PROTOCOL.md.

**Pre-lock criterion:** divergence list produced; reconciliation lands as a doc-only packet (no code).

### C4. Lock-day checklist runner OR explicit hand-verification ratification

**Status:** Option A implemented in the current Codex working tree
(pending Claude audit + Dom commit). `lock_checklist.py` parses §14,
runs mechanical checks where possible, leaves lock-day decisions /
hash-recording rows as operator-confirmation pending, and emits JSON +
Markdown to an output directory without mutating lock docs.

**Source:** PILOT_PROTOCOL.md §14 "Lock checklist (each item must be ticked, with evidence captured in the corresponding lock commit)." `scripts/collect_lock_hashes.py` mechanically produces the §14 hash table; nothing chains the other rows into a single green / red checklist artifact.

**Gap:** lock-day operator must hand-verify each non-hash row and remember to attach evidence to the commit.

**Pre-lock criterion (choose one):**
- **Option A (runner):** script walks the §14 checklist, executes the mechanical rows (hash collector, L7 replay, provider probe, schema regression tests, safety-subset enumeration), surfaces the non-mechanical rows (D-O-01 selection, status flip ratification, lock date, lock commit SHA) as operator prompts, emits a `lock_checklist_<timestamp>.json` artifact + markdown summary for the lock commit body.
- **Option B (hand-verification):** Dom ratifies explicitly that §14 is hand-verified on lock day; no runner is built; this row drops.

**Lock-day note:** the runner does not settle Dom-only lock decisions
(`D-O-01`, scorer-config freeze, lock hash recording, lock commit SHA,
or push authorization); those remain operator confirmations in the
generated checklist artifact.

---

## Tier D. Defer or post-lock

### D1. Anthropic adapter (Option C stretch)

**Defer rationale:** Option C runs only if substrate is clean by mid-July. Building pre-lock risks rot if Option B alone consumes the calendar.

### D2. Fixture-isolation-per-rep policy artifact

**Defer rationale:** decision lands inside A2 orchestrator design (Dom decision 4 already resolves).

---

## Inventory metadata

- **Tier A:** 12 items.
- **Tier B:** 4 items.
- **Tier C:** 4 items (C4 still has Option A vs Option B open call).
- **Tier D:** 2 items.

## Suggested implementation order

Dependencies-respecting order for one-item-per-session cadence. Items on the same row are independent and can run in any order or in parallel sessions.

| Order | Item | Type | Depends on | Notes |
|---|---|---|---|---|
| 1 | **A12** §8 / §10 amendment | Doc | none | Lands first; unblocks A10 + sets pilot ordering for everything else. Plan-mode trigger. |
| 1 | **B4** PAPER.md staleness | Doc | none | Independent doc cleanup. Plan-mode trigger. |
| 1 | **B1** M7 negative-control corpus | Data + test | none | Defends audit. |
| 2 | **A7** pilot_manifest.json schema + writer | Schema + code | A12 (for D-O-01 selection field) | Landing pad for A2. |
| 2 | **A1** Multi-turn agent loop + invalid_output step | Schema + code | none | Foundational. Blocks A4, A5, A6, A8, A9. |
| 3 | **A4** Per-step trajectory metadata | Code | A1 | Feeds A2 meters. |
| 3 | **A11** §7 falsification verdict generator | Code | none | Independent. |
| 4 | **A5** Retry / rate-limit / outage middleware | Code | A1, A4 | Feeds A2 disposition tree. |
| 4 | **A8** L7 hand-authored pass trajectories | Data | A1 (turn definition) | Authoring + risk check. |
| 5 | **A6** Fireworks adapter | Code | A1, A4, A5 | DR-9 fallback substrate. |
| 5 | **A9** L7 ≤7-turn replay test | Test | A1, A8 | §14 evidence artifact. |
| 6 | **A2** Pilot orchestrator + §11 triage + hermeticity | Code | A1, A4, A5, A7 | Largest packet. A3 folds in. |
| 7 | **A10** DR-9 switch evaluator | Code | A6, A11, A12 | DR-9 fully operational. |
| 7 | **B2** condition_summary writer + cost reconciliation | Schema + code | A2 | Reconciliation invariant. |
| 8 | **B3** pilot_evidence_table generator | Code | A2 | Reads runs/pilot/. |
| 9 | **C1** Provider-IDs / pricing probe | Script | none | Lock-day evidence. |
| 9 | **C2** PILOT_PROTOCOL.md §13 phrasing | Doc | none | Bundle with A12 if cheap. |
| 9 | **C3** SPEC.md drift audit | Doc | none | Codex audit produces list. |
| 9 | **C4** Lock-day checklist runner OR hand-verify | Code or ratification | most items | Open call. |

## §14 row-to-inventory mapping

- §14 protocol-content-ratified row: shipped (WP-RATIFY-001).
- §14 D-O-01 decision row: lock-day only (scope out).
- §14 provider IDs / pricing row: C1.
- §14 scorer_config status flip row: lock-day only (scope out).
- §14 scorer_config provenance row: shipped (WP-A).
- §14 prompt SHA-256 row: A7 (hash field) + lock-day (recording).
- §14 HAI manifest SHA-256 row: A7 + lock-day.
- §14 per-task SHA-256 row: A7 + lock-day; collector already exists.
- §14 model_roster SHA-256 row: A7 + lock-day.
- §14 protocol SHA-256 row: A7 + lock-day.
- §14 cost budget reserve row: documentation only; not a deliverable.
- §14 L7 ≤7-turn verification row: A8 + A9.
- §14 safety_constrained_subset SHA-256 row: A7 + lock-day.
- §14 lock commit pushed row: lock-day only.

## Open Design Questions (all closed)

Provenance preserved for archival. None block implementation.

1. **DR-9 operational status at lock.** CLOSED 2026-06-01: keep DR-9 active. A6 + A10 in scope.
2. **Multi-turn prompt assembly format.** CLOSED 2026-06-01; amended 2026-06-02 (WP-A1): standard chat-completion messages — model action as the `assistant` turn verbatim, observations returned as `user` messages, no synthesized provider-native `tool_calls`.
3. **Fixture state between reps within a condition.** CLOSED 2026-06-01: fresh fixture per rep.
4. **Cost-cap and wall-time enforcement granularity.** CLOSED 2026-06-01: between turns.
5. **DR-9 switch timing under §10 ordering.** CLOSED 2026-06-01: amend §8 (work packet A12). After `full_contract`, if gate A passes, run n=1 gate-B prelude × 5 no-X × 14 safety tasks; switch iff both pass.
6. **Malformed-output trajectory representation.** CLOSED 2026-06-01: new `invalid_output` step_type in trajectory schema.
7. **Per-mechanism cost attribution.** CLOSED (Codex audit round 1): even-split reconciled allocation. Implemented in B2.
8. **Mock transport location.** CLOSED (Codex audit round 2): existing `TogetherTransport` Protocol pattern.
