# Work Packets

**Status:** Agent-executable backlog, 2026-05-08.

Future coding agents should be assigned one packet at a time. Do not ask
an agent to "build GovernedAgentBench" or "finish the paper." Use these
bounded packets with explicit file scopes and acceptance criteria.

## Packet Template

```markdown
## WP-AREA-000 — Title

Goal:
Inputs:
Outputs:
Allowed files:
Forbidden files:
Dependencies:
Acceptance criteria:
Tests:
Manual review needed:
Non-goals:
```

## WP-PRIOR-001 — Prior-Art Matrix

Goal: Produce the first prior-art matrix for the paper's contribution
delta.

Inputs:

- `PRIOR_ART_POSITIONING.md`
- `PAPER_FRAME.md`
- `RESEARCH_EVAL_STRATEGY.md`

Outputs:

- `research/runtime_contracts_paper/prior_art_matrix.md`
- short memo naming the top 5 closest works and the delta against each

Allowed files:

- `research/runtime_contracts_paper/prior_art_matrix.md`
- `research/runtime_contracts_paper/PRIOR_ART_POSITIONING.md`

Forbidden files:

- runtime source;
- benchmark schemas;
- paper claims beyond a "needs citation" note.

Dependencies: none after planning gate.

Acceptance criteria:

- At least 20 works/frameworks/benchmarks categorized.
- Each row answers task setting, interface, safety mechanism, state
  ownership, mutation model, scoring, and difference from this paper.
- No invented citations; uncertain bibliographic details are marked
  `VERIFY`.

Tests: markdown link/check scan if available; otherwise manual review.

Manual review needed: yes, for citation quality.

Non-goals: writing the related-work section.

## WP-CONTRACT-001 — Freeze HAI Manifest Snapshot

Goal: Commit the first frozen manifest used by GovernedAgentBench.

Inputs:

- `RUNTIME_CONTRACT_FREEZE_PLAN.md`
- source-tree `hai capabilities --json`

Outputs:

- `benchmarks/governed_agent_bench/manifests/hai_0_2_0.json` as a
  manifest snapshot envelope, not a raw manifest dump
- provenance note in `benchmarks/governed_agent_bench/manifests/README.md`
- `verification/tests/test_benchmark_manifest_snapshot.py`

Allowed files:

- `benchmarks/governed_agent_bench/manifests/`
- `verification/tests/test_benchmark_manifest_snapshot.py`
- docs that reference the manifest count/current state

Forbidden files:

- runtime behavior changes unless a blocker is discovered and separately
  scoped.

Dependencies: planning gate complete.

Acceptance criteria:

- Snapshot is generated from the current source tree.
- Envelope records `schema_version`, `manifest_version`, `generated_at`,
  `generated_by`, `source_commit`, `hai_version`,
  `contract_schema_version`, and embedded `manifest`.
- Provenance command is documented.
- Embedded manifest is stable under repeated generation, ignoring
  `generated_at`.
- Existing capabilities tests still pass.

Tests:

- `uv run pytest verification/tests/test_capabilities.py -q`
- `uv run pytest verification/tests/test_benchmark_manifest_snapshot.py -q`
- `uv run pytest verification/tests/test_project_reframe_docs_alignment.py -q`

Manual review needed: yes, confirm snapshot is appropriate for paper
contract freeze.

Non-goals: MCP, model adapters, scorer.

## WP-RUNTIME-FIX-NNN — Runtime Defect Packet Template

Use this template only when a contract-freeze or benchmark packet finds
a real runtime defect that blocks the packet.

Goal: Fix one runtime defect required by a named research packet.

Inputs:

- parent packet ID;
- failing command, test, or fixture setup;
- relevant HAI operator docs.

Outputs:

- minimal runtime patch;
- targeted regression test;
- note in parent packet or docs explaining why the runtime fix was
  research-critical.

Allowed files:

- the smallest affected runtime module(s);
- `verification/tests/`;
- docs that describe the corrected contract behavior.

Forbidden files:

- unrelated runtime refactors;
- new product surfaces;
- MCP unless the parent packet is explicitly MCP-scoped.

Dependencies: parent packet is blocked on this fix.

Acceptance criteria:

- Parent packet can resume without changing its scope.
- Existing HAI runtime tests still pass.
- The fix does not broaden the benchmark beyond the approved subset.

Tests: targeted regression plus the parent packet's listed tests.

Manual review needed: yes.

Non-goals: opportunistic cleanup.

## WP-CONTRACT-002 — Fixture-State Plan

Goal: Define synthetic fixture-state requirements before implementation.

Inputs:

- `RUNTIME_CONTRACT_FREEZE_PLAN.md`
- HAI state docs and migrations

Outputs:

- `benchmarks/governed_agent_bench/fixtures/README.md`
- fixture plan for `empty_user`, `ready_user_minimal`,
  `read_surface_user`, `governance_user`, and `drift_user`

Allowed files:

- `benchmarks/governed_agent_bench/fixtures/README.md`
- benchmark docs

Forbidden files:

- fixture data generation code;
- private health rows;
- runtime migrations.

Dependencies: none.

Acceptance criteria:

- Each fixture states purpose, required tables, prohibited data, reset
  expectation, and task levels served.
- No real user data.

Tests: docs integrity only.

Manual review needed: yes.

Non-goals: creating fixture databases.

## WP-CONTRACT-003 — Fixture Implementation

Goal: Implement deterministic synthetic fixture state for benchmark and
harness work.

Inputs:

- `benchmarks/governed_agent_bench/fixtures/README.md`
- `RUNTIME_CONTRACT_FREEZE_PLAN.md`
- HAI state docs and migrations

Outputs:

- constructible fixtures under
  `benchmarks/governed_agent_bench/fixtures/`
- fixture reset/load utility under the benchmark tree if needed
- tests proving reset determinism and absence of private data

Allowed files:

- `benchmarks/governed_agent_bench/fixtures/`
- benchmark-local fixture loader code
- `verification/tests/` for fixture determinism tests
- docs that reference fixture count/current state

Forbidden files:

- real user data;
- live credentials;
- runtime migrations unless separately scoped through a
  `WP-RUNTIME-FIX-NNN` packet.

Dependencies:

- WP-CONTRACT-002.

Acceptance criteria:

- Each planned fixture is constructible from committed synthetic inputs.
- Repeated resets produce equivalent state.
- Harness can receive a fixture path through the documented environment
  or config surface.
- No fixture contains private health rows, credentials, or clinical
  records.

Tests:

- targeted fixture determinism tests;
- docs integrity.

Manual review needed: yes.

Non-goals: model execution, scorer implementation, live integrations.

## WP-GAB-001 — Operator Action Schema

Goal: Add the model-output action schema used by the operator harness.

Inputs:

- `OPERATOR_HARNESS_SPEC.md`
- existing trajectory schema

Outputs:

- `benchmarks/governed_agent_bench/schema/operator_action.schema.json`
- README note explaining how actions become trajectory steps

Allowed files:

- `benchmarks/governed_agent_bench/schema/`
- benchmark docs

Forbidden files:

- harness implementation;
- model adapters.

Dependencies: planning gate complete.

Acceptance criteria:

- Schema distinguishes `command`, `refusal`, and `final`.
- Command action uses structured `command` + `args`, not arbitrary shell.
- Schema rejects unknown top-level fields.

Tests:

- schema validation tests to be added in a bounded follow-up packet.

Manual review needed: no if schema is narrow and docs updated.

Non-goals: running HAI commands.

## WP-GAB-002 — Scorer MVP Skeleton

Goal: Implement an offline scorer that can score hand-authored
trajectories.

Inputs:

- `SCORING_SPEC.md`
- existing task/trajectory/score schemas

Outputs:

- scorer module or script under `benchmarks/governed_agent_bench/scorer/`
- tests with one passing and one failing hand-authored trajectory

Allowed files:

- `benchmarks/governed_agent_bench/scorer/`
- `benchmarks/governed_agent_bench/schema/`
- `verification/tests/` for benchmark scorer tests

Forbidden files:

- HAI runtime source;
- model adapters;
- network calls.

Dependencies:

- WP-GAB-001 preferred but not strictly required if trajectory schema is
  sufficient.

Acceptance criteria:

- Scores run offline.
- Output validates against `score.schema.json`.
- Critical violations fail overall pass.
- No LLM judge is used.

Tests:

- targeted pytest for scorer;
- `git diff --check`.

Manual review needed: yes, for metric semantics.

Non-goals: model execution.

## WP-GAB-003 — First L1/L2/L5/L6/L7 Task Set

Goal: Author the first 10 benchmark tasks.

Inputs:

- `BENCHMARK_SPEC.md`
- `TASK_AUTHORING_GUIDE.md`
- frozen manifest if available

Outputs:

- 2 L1 tasks
- 2 L2 tasks
- 2 L5 tasks
- 2 L6 tasks
- 2 L7 tasks

Allowed files:

- `benchmarks/governed_agent_bench/tasks/`
- benchmark README count/status updates

Forbidden files:

- scorer implementation;
- runtime source;
- private data.

Dependencies:

- WP-CONTRACT-001 preferred for manifest references.
- WP-CONTRACT-002 preferred for fixture references.

Acceptance criteria:

- All tasks validate against task schema.
- No task requires clinical interpretation.
- Expected behavior is deterministic and scoreable.

Tests:

- task schema validation test.

Manual review needed: yes, especially L6 clinical boundary.

Non-goals: model runs.

## WP-GAB-004 — Hand-Authored Trajectories

Goal: Add passing and failing trajectories for the first task set.

Inputs:

- first task set;
- `OPERATOR_HARNESS_SPEC.md`;
- `SCORING_SPEC.md`.

Outputs:

- one passing and one failing trajectory for at least five tasks.

Allowed files:

- `benchmarks/governed_agent_bench/trajectories/`
- benchmark docs

Forbidden files:

- model adapters;
- runtime source.

Dependencies:

- WP-GAB-003.

Acceptance criteria:

- Trajectories validate against trajectory schema.
- Failures exercise at least three violation kinds.
- Scorer can grade them.

Tests:

- trajectory schema validation;
- scorer tests once WP-GAB-002 exists.

Manual review needed: yes.

Non-goals: real model output.

## WP-HARNESS-001 — Model-Agnostic Harness MVP

Goal: Build a harness that can load a task, accept a structured action,
execute allowed HAI CLI commands against fixture state, and record a
trajectory.

Inputs:

- `OPERATOR_HARNESS_SPEC.md`
- frozen manifest
- fixture-state plan

Outputs:

- harness implementation under benchmark tree;
- tests for hand-authored actions.

Allowed files:

- `benchmarks/governed_agent_bench/`
- `verification/tests/`

Forbidden files:

- model API adapters;
- MCP;
- live credential paths.

Dependencies:

- WP-GAB-001;
- WP-CONTRACT-001;
- WP-CONTRACT-003.

Acceptance criteria:

- Blocks non-`hai` shell commands.
- Runs only against fixture/temp state.
- Records stdout/stderr/exit code into trajectory.
- Requires no model backend.

Tests:

- targeted pytest;
- docs integrity.

Manual review needed: yes, for safety.

Non-goals: local/cloud model invocation.

## WP-BASE-001 — Rule Baseline

Goal: Implement deterministic baseline actions for simple tasks.

Inputs:

- first task set;
- operator action schema;
- scorer.

Outputs:

- rule baseline under `benchmarks/governed_agent_bench/baselines/`
- report with which tasks are solved deterministically

Allowed files:

- benchmark baselines/reports/tests.

Forbidden files:

- model adapters;
- runtime source.

Dependencies:

- WP-GAB-002;
- WP-GAB-003;
- WP-CONTRACT-003.

Acceptance criteria:

- Produces trajectory format.
- Uses same scorer as model systems.
- Identifies tasks that are routing-only.

Tests: targeted pytest.

Manual review needed: no, unless results force task redesign.

Non-goals: model comparison.

## Future Packets — Expand Before Assignment

The packets below are strategic placeholders. They must be expanded to
the full packet template before any coding agent is assigned to them:
Inputs, Outputs, Allowed files, Forbidden files, Dependencies,
Acceptance criteria, Tests, Manual review needed, and Non-goals.

## WP-MODEL-001 — Local Model Adapter

Goal: Add a local-model adapter that consumes task prompts and emits
operator actions.

Dependencies:

- scorer MVP;
- operator action schema;
- task set;
- harness MVP.

Acceptance criteria:

- Adapter is optional and can be skipped when local model runtime is not
  installed.
- Run logs record model id, decoding settings, prompt condition, and
  manifest version.
- No private data leaves local machine.

Non-goals: fine-tuning.

## WP-MODEL-002 — Cloud Model Adapter

Goal: Add a cloud-model adapter with the same action interface.

Dependencies:

- same as WP-MODEL-001.

Acceptance criteria:

- Adapter requires explicit env vars.
- No private health rows are sent.
- Prompt-only and contract conditions share comparable wording.

Non-goals: product integration.

## WP-ABL-001 — First Scaffold Ablations

Goal: Run a small ablation set once baseline harness is stable.

Dependencies:

- first model adapter;
- scorer;
- task set.

Acceptance criteria:

- At least `full_contract`, `no_manifest`, `stale_manifest`, and
  `no_agent_safe` conditions are represented.
- Results report violation taxonomy counts.

Non-goals: full ablation suite before workshop floor.

## WP-PAPER-001 — Related Work Draft

Goal: Convert the prior-art matrix into a paper section.

Dependencies:

- WP-PRIOR-001.

Acceptance criteria:

- Claims are comparative, not dismissive.
- Contribution delta is stated against closest works.
- Unknown citations are not left as placeholders.

Non-goals: results writing.
