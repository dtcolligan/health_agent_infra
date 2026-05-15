# Round-2 Audit Response — Maintainer Closeout

**Date:** 2026-05-09 (round-2 closeout, same session as the round-1
closeout).

**Codex verdict:** `PLAN_COHERENT_WITH_REVISIONS`.

**Findings:** 6 major, 0 critical, 0 minor. All 6 accepted; 0 disputed.

**Empirical settling shape.** Round 1 produced 20 findings (2
critical, 17 major, 1 minor). Round 2 produced 6 findings (6 major).
Continued descent matches the empirical 10→5→3→0 settling shape
recorded in AGENTS.md "Patterns the cycles have validated". A round
3 should be a ≤2-finding nit pass at most; if round 3 produces ≥4
findings, this closeout introduced second-order issues that need a
re-read.

**Closeout artifacts.**

- This file: per-finding maintainer adjudication.
- `project/DECISIONS.md` D-PROJ-018: durable architectural record.
- `benchmark/verification/tests/test_runtime_first_alignment.py`:
  mechanical regression guard for F-CDX-RFR-R2-01 + F-CDX-RFR-R2-02.
- `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`:
  expanded from 13 to 15 tests covering the round-2 schema additions.

---

## F-CDX-RFR-R2-01 — Runtime-mode naming drift reintroduced the old confusion [REGRESSION]

**Severity:** major.

**Disposition:** **accept (regression by maintainer).**

**Action.**

- `HAI_PAPER_READINESS_EXECUTION.md`: replaced 7 occurrences of
  `no_runtime_enforcement_enforcement` with `no_runtime_enforcement`.
  The typo originated from a global replace that double-applied
  during the round-1 closeout. Lines 56, 67, 72 (also fixed the
  "previously named" direction), 109, 125, 549 (D-PROJ-017 (f) row
  fixed: now `no_runtime` → `no_runtime_enforcement`), 576.
- `benchmark/governed_agent_bench/BENCHMARK_SPEC.md` line 160:
  replaced bare `no_runtime` enum entry with
  `no_runtime_enforcement`. Lines 164-165 corrected: v2 task fields
  `load_bearing_mechanisms` and `runtime_modes_in_scope` are
  **required** (the schema already required them; the doc had
  drifted to "optional").
- `WORK_PACKETS.md` line 1163 (`WP-MAN-004` outputs): replaced bare
  `no_runtime` with `no_runtime_enforcement`.
- New regression test: `benchmark/verification/tests/test_runtime_first_alignment.py::test_no_double_enforcement_typo`
  fails on any markdown line containing the doubled-enforcement typo.
- New regression test: `test_no_bare_no_runtime_in_active_docs`
  fails on bare `no_runtime` outside rename callouts, retired blocks,
  audit prose, and historical plans.
- The schema-contract test
  `test_runtime_modes_cover_mechanism_ablations` already asserts
  `"no_runtime" not in modes` for the v2 enum; that test still
  passes.

**Closeout note.** The typo was caught only because Codex sample-
verified the closeout actions on disk. The lesson reinforces the
provenance-discipline pattern in AGENTS.md: do not trust a global
replace's claim of correctness without a post-replace grep.

---

## F-CDX-RFR-R2-02 — Supersession notes sit on top of still-active prompt-first bodies [ROUND-1 RESIDUAL]

**Severity:** major.

**Disposition:** **accept (round-1 closeout did not push deep
enough).**

**Action.** Body sections of all nine cited docs rewritten to drop
prompt-axis comparison language and reframe around the canonical
`runtime_mode` × `model_class` design:

| Doc | Section(s) rewritten |
|---|---|
| `PAPER_FRAME.md` | §Contributions item 4 (no longer "manifest-grounded prompting"/"prompt-only baselines"); §Empirical Result Tiers (now points at `CLAIM_LADDER.md` T0..T4 + Future-A; lists forbidden phrasings explicitly). |
| `RESEARCH_EVAL_STRATEGY.md` | §Scaffold Ablations (now lists the seven canonical `runtime_mode` values and explicitly retires "no manifest" / "stale manifest" / "no exit-code semantics" etc as conditions); §Result Interpretation (now points at `CLAIM_LADDER.md`); §Fine-Tuning Scope (now Future-A appendix, prompt held constant). |
| `PROJECT_EXECUTION_PLAN.md` | §M3 Baseline Harness (single deployment-realistic prompt path, all v2 trajectory fields recorded); §M4 Experiment Set (`runtime_mode` × `model_class`, no prompt variants); §M5 Fine-Tuning (Future-A appendix). |
| `IMPLEMENTATION_PLAN.md` | §Phase 4 Baselines (predeclared-roster `model_class` × `runtime_mode`, no "prompt-only" entries); §Phase 5 (Future-A appendix); §Phase 6 (per-mechanism off-paths along the seven-mode `runtime_mode` enum); §Scientific Success Criteria (Tier-tagged claims). |
| `OPERATING_MODEL.md` | §Evaluation Scope (rewritten as `runtime_mode` × `model_class`; the seven canonical modes enumerated). |
| `ROADMAP.md` | §Next "Model baselines" (predeclared roster, prompt held constant); §Next "Fine-tuned local operator" (Future-A appendix); §Next "Scaffold ablations" (per-mechanism off-paths only); §Research Milestones table; §Support-lane row v0.2.3 freeze tombstoned. |
| `HYPOTHESES.md` | §H2 (component list replaced with M4..M8 mechanism enum; "manifest access" / "drift-aware manifest retrieval" removed); §H4 (rewritten to keep prompt held constant; "with vs without live manifest retrieval" removed). |
| `OPERATOR_HARNESS_SPEC.md` | §Trajectory Encoding (records `runtime_mode`, `model_class`, `manifest_snapshot_id`, `prompt_template_id`, `prompt_template_hash`, `invocation_context`; old `condition`/`model_id` retired). |
| `DRAFT_PAPER.md` | Round-2 reframe note added (was missing in round 1); §Contributions item 4-5 rewritten; §5.1 Models, §5.2 Conditions, §5.3 Scaffold Ablations rewritten as predeclared-roster × `runtime_mode`; §6.1 main-result table re-keyed by `model_class` × `runtime_mode`. |

**Mechanical regression guard.**
`benchmark/verification/tests/test_runtime_first_alignment.py::test_no_prompt_axis_strings_in_active_docs`
parametrises six forbidden phrases (`local_prompt_only`,
`cloud_prompt_only`, `with_manifest`, `without_manifest`,
`prompt-only baseline`, `manifest-grounded prompting`) and fails on
any active markdown line containing them outside retired/forbidden
callout blocks, audit prose, or historical plans. The test passes;
adding a regressing prompt-axis sentence to any active doc would
fail the suite.

**Closeout note.** Round-1 closeout claimed these docs were
"tombstoned with supersession notes". Codex correctly flagged that
header notes are not enough — a cold agent reading the body could
still execute the old design. Rewriting the body sections is the
honest fix.

---

## F-CDX-RFR-R2-03 — Agent/user invocation classification has no harness owner

**Severity:** major.

**Disposition:** **accept (deferred deliverable that was load-bearing).**

**Action.**

- `WP-HARNESS-MODE-001` expanded with the round-2 contract: harness
  exports `HAI_INVOCATION_CONTEXT=agent` for every model-backed
  subprocess; `HAI_INVOCATION_CONTEXT=rule_baseline` for rule-
  baseline subprocesses; never sets it for the maintainer's daily-
  driver loop (which inherits the dispatch default `user`).
  Acceptance now includes:
  - trajectory's `invocation_context` field matches the exported
    value;
  - a unit test fails the harness contract if a model-backed
    subprocess omits `HAI_INVOCATION_CONTEXT=agent`;
  - a grep test asserts no benchmark code path exports
    `HAI_INVOCATION_CONTEXT=user` for a model-backed run.
- The Claude-Code daily-driver classification is documented
  explicitly: it stays `user`. A research-only opt-in for the daily
  loop to operate as `agent` is named but not the default.
- Trajectory schema gains `invocation_context` field with the enum
  `["agent", "user", "rule_baseline"]`. New schema-contract test
  `test_trajectory_records_round_2_closeout_fields` asserts this.

**Closeout note.** The round-1 closeout introduced
`WP-DISPATCH-001` with a `user` default to protect the daily loop,
but did not specify the harness export side. Without the harness
export, the dispatch enforcer would silently default to `user` for
every benchmark call, which is exactly the failure mode Codex
described.

---

## F-CDX-RFR-R2-04 — Dangerous ablation modes are not runtime-gated to hermetic state [ROUND-1 RESIDUAL]

**Severity:** major.

**Disposition:** **accept (packet-level assertions are not a runtime
guard).**

**Action.**

- `WP-RT-MODE-001` rewritten with a runtime-side hermetic-only
  guard. The accessor's startup-time check rejects any non-
  `full_contract` `HAI_RUNTIME_MODE` value unless `HAI_HERMETIC=1`
  AND `HAI_STATE_DB` AND `HAI_BASE_DIR` are all set to non-default
  paths. The guard fires before any handler runs and exits with a
  stderr message naming the missing env var. New acceptance
  criteria + new test file
  `hai/verification/tests/test_runtime_mode_hermetic_guard.py`.
- `WP-RT-MODE-001` now depends on `WP-HRN-001` (so the hermetic env
  surface exists before the guard reads it).
- `WP-RT-MODE-002` acceptance criterion 3 rewritten: "user's real
  audit chain unaffected by benchmark-mode runs (verified by the
  WP-RT-MODE-001 hermetic-only guard)" — replaces the previous
  "verified via `HAI_STATE_PATH` redirection" language (and
  `HAI_STATE_PATH` doesn't exist; the round-1 closeout already
  caught that name in `WP-HRN-002` but missed this echo).
- `WP-REFUSE-002` acceptance: `hai intent commit --dry-run`
  reference removed (the flag does not exist; closest existing flag
  is `--confirm`). Replaced with: dispatch enforcer's behaviour
  against fixture state (the proof-of-disabling is the dispatch
  refusal not firing, which requires no flag).
- Dependency graph updated: `WP-HRN-001 → WP-RT-MODE-001` is now an
  explicit edge.

**Closeout note.** This is the single biggest correctness improvement
of the round-2 closeout. The previous "hermetic-only by convention"
posture left a real path where a stray test or future implementer
could mutate user state under `HAI_RUNTIME_MODE=no_agent_safe`
outside hermetic mode. The runtime-side guard makes that
structurally impossible.

---

## F-CDX-RFR-R2-05 — `deployment_full_v1` cannot render against v1 or stale manifest snapshots

**Severity:** major.

**Disposition:** **accept (template was forward-only; v1/stale paths
ignored).**

**Action.**

- `prompts/deployment_full_v1.md` now contains an explicit
  **Manifest-shape promotion rule (v1 → v2 envelope)** section. Any
  pre-Phase-3 manifest snapshot or any explicitly stale L7 drift
  snapshot is promoted to a v2-shaped envelope at task-build time
  by adding empty `refusals`, `mutation_classes`, and `exit_codes`
  fields. Promotion is purely additive; the snapshot's behaviour
  (missing/stale `commands`) is preserved. The promoted envelope is
  recorded as `manifests/<snapshot_id>.promoted_v2.json` for
  reproducibility.
- L7 drift specifically: the v0.1.18-era drift snapshot is
  generated by `WP-DRIFT-001`, then promoted to a v2 envelope
  before rendering. The model still sees the v0.1.18-era command
  surface inside `commands`; it sees empty taxonomies in the
  envelope. This is part of the realistic drift signal, not a
  template bug.
- Placeholder count corrected: "Exactly five placeholders" (was
  "Exactly four"; the round-1 file listed five but said four).
- New section **Hashes — file vs rendered** distinguishes
  `prompt_template_file_hash` (sha256 of the template file's bytes,
  stable across all trajectories sharing the template version) from
  `prompt_template_hash` (sha256 of the rendered system+user prompt
  for a specific task and snapshot, varies per task/snapshot).
  Trajectory schema gains optional `prompt_template_file_hash`
  field.
- Reproducibility section rewritten to use both hashes: a
  `prompt_template_id` + `file_hash` mismatch indicates mid-
  experiment template edits; a `task_id` + `file_hash` match with
  rendered-hash mismatch indicates substitution drift. Both are
  flagged by the score gate.
- New schema-contract test
  `test_trajectory_records_round_2_closeout_fields` asserts the
  field exists.

**Closeout note.** The round-1 template was authored assuming Phase
3 would land before any model run. Codex correctly observed that
L7 drift specifically requires a v1-snapshot path, and the
template-vs-rendered hash conflation made byte-stability claims
ambiguous. Both gaps closed.

---

## F-CDX-RFR-R2-06 — Model-roster predeclaration still has no enforceable gate

**Severity:** major.

**Disposition:** **accept (predeclared-roster discipline was
procedural, not structural).**

**Action.**

- New packet `WP-MODEL-ROSTER-001` added to `WORK_PACKETS.md` as a
  hard prerequisite for `WP-MODEL-001`, `WP-MODEL-002`, and
  `WP-ABL-001`. The packet's deliverable is a schema-bound
  immutable file `benchmark/governed_agent_bench/model_roster.md`
  declaring `roster_v1`, local model entries (≥3 sizes for Tier 4
  evidence), cloud model entries (with `provider_snapshot` rotation
  policy), Future-A fine-tuned-local entries, and the **locked**
  Tier 4 curve-shift metric: "smallest predeclared local model (by
  `parameter_count`) whose Tier-3-eligible trajectories pass every
  primary-metric threshold under `full_contract`, versus the same
  metric under `no_runtime_enforcement`. Curve shift is reported as
  the parameter-count gap between the two smallest passing models
  in each runtime mode." If no model in the roster passes under
  `no_runtime_enforcement`, the gap is reported as
  ">= largest_roster_param_count".
- `score.schema.json` v2 gains `claim_tier` (enum `T0..T4`) and
  `model_roster_hash` fields. New conditional invariant: when
  `claim_tier ∈ {T3, T4}`, `model_roster_hash` is required. New
  schema-contract test `test_score_requires_model_roster_hash_for_t3_t4`
  asserts the conditional structure.
- `trajectory.schema.json` v2 gains optional `model_roster_hash`
  field for trajectories contributing to T3/T4 claims.
- Dependency graph updated: `WP-MODEL-ROSTER-001` is a child of
  `WP-RT-MODE-001` (so `runtime_mode` is canonical when the roster
  is authored) and a parent of `WP-MODEL-001`, `WP-MODEL-002`, and
  `WP-ABL-001`.
- `CLAIM_LADDER.md` Tier 4 metric now references the locked
  definition above (no longer "e.g., parameter count at which the
  safety threshold is first reached").

**Closeout note.** The procedural "author the roster before any
model run" assertion is now structurally enforceable: a Tier 3 or
Tier 4 score without a valid `model_roster_hash` fails schema
validation. The future "Could you have authored the roster after
partial runs?" attack is closed by hash binding.

---

## What did not need a closeout action

**Codex no-finding notes.** Three observations from Codex did not
require closeout actions:

1. **Schema conditional structure.** Codex read the trajectory and
   score schema `allOf` blocks and confirmed they are syntactically
   sound. Codex flagged the schema-contract suite as structural
   (asserting shape, not validating instances). This is a noted
   future-hardening opportunity; instance-validation tests would
   require `jsonschema` in the project venv (currently uvx-only),
   which the maintainer has not bundled. **Status:** accepted as
   future hardening, not blocking the round-2 closeout.
2. **Test count honesty.** Codex confirmed the schema-contract
   suite contains 13 (now 15 after F-CDX-RFR-R2-03/06 additions)
   `def test_*` functions with no `skip`/`xfail` markers. **Status:**
   no action.
3. **MECHANISM_INVENTORY citations.** Codex confirmed the source
   paths cited by the rewritten inventory exist on disk. **Status:**
   no action.

## What the round-3 audit prompt should focus on

If the maintainer authors a round-3 audit prompt, it should ask
Codex to focus on:

1. **Per-finding action verification on disk** for the six closeout
   actions above, especially:
   - that the F-CDX-RFR-R2-04 hermetic guard's acceptance criteria
     name the specific exit codes / stderr messages cleanly enough
     for a coding agent to implement without further prompting;
   - that the F-CDX-RFR-R2-06 Tier 4 metric definition handles edge
     cases (no model passes under either mode; tied smallest models
     in each mode);
   - that the F-CDX-RFR-R2-02 alignment test's exemption logic does
     not accidentally allow a future regressing edit by hiding it
     under one of the negative-context markers.
2. **Round-3 budget calibration:** if Codex finds 0-2 nits, ship
   the runtime-first reframe at this point. If it finds 3-5 fresh
   substantive findings, round-3 plan-audit is justified. If it
   finds ≥6, this closeout introduced second-order issues and
   needs a self-re-read before round 3 fires.
3. **Phase-1 implementation kickoff readiness:** is
   `WP-INV-001` actually executable as written? Does the rating
   rubric handle every M4-M8 mechanism cleanly? Does the
   coupling graph survive contact with HAI source?

Drafting the round-3 prompt is optional; per the empirical
settling shape, this closeout's scope should be the last
substantive audit gate before Phase 1 implementation begins.
