# Work Packets

**Status:** Agent-executable backlog, 2026-05-09.

Future coding agents should be assigned one packet at a time. Do not ask
an agent to "build GovernedAgentBench" or "finish the paper." Use these
bounded packets with explicit file scopes and acceptance criteria.

**Reframe note (2026-05-09).** The headline experiment is now
runtime-first: the prompt is held constant at deployment-realistic full
information, and the runtime is the primary axis of variation. See
`HAI_PAPER_READINESS_EXECUTION.md` for the controlling plan and
`../../project/DECISIONS.md` D-PROJ-013..015 for the durable decision
record. Some pre-reframe packets below are marked **[RESCOPED]** with
the change recorded inline; their packet IDs are preserved.

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

## WP-HAI-001 — Capture HAI Manifest Snapshot **[RESCOPED 2026-05-09]**

**Rescope.** Now blocked by `WP-MAN-001..006` (the manifest must be
contract-complete and at `agent_cli_contract.v2` before the snapshot is
worth freezing). Output filename and envelope unchanged.

Goal: Commit the first frozen manifest used by GovernedAgentBench.

Inputs:

- `HAI_PAPER_READINESS_PLAN.md`
- source-tree `hai capabilities --json`

Outputs:

- `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` as a
  manifest snapshot envelope, not a raw manifest dump
- provenance note in `benchmark/governed_agent_bench/manifests/README.md`
- `benchmark/verification/tests/test_benchmark_manifest_snapshot.py`

Allowed files:

- `benchmark/governed_agent_bench/manifests/`
- `benchmark/verification/tests/test_benchmark_manifest_snapshot.py`
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

- `uv run pytest hai/verification/tests/test_capabilities.py -q`
- `uv run pytest benchmark/verification/tests/test_benchmark_manifest_snapshot.py -q`
- `uv run pytest project/tests/test_project_reframe_docs_alignment.py -q`

Manual review needed: yes, confirm snapshot is appropriate for HAI
paper-readiness engineering.

Non-goals: MCP, model adapters, scorer.

## WP-RUNTIME-FIX-NNN — Runtime Defect Packet Template

Use this template only when a HAI paper-readiness or benchmark packet
finds a real runtime defect that blocks the packet.

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
- `hai/verification/tests/`;
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

## WP-HAI-002 — Fixture-State Plan

Goal: Define synthetic fixture-state requirements before implementation.

Inputs:

- `HAI_PAPER_READINESS_PLAN.md`
- HAI state docs and migrations

Outputs:

- `benchmark/governed_agent_bench/fixtures/README.md`
- fixture plan for `empty_user`, `ready_user_minimal`,
  `read_surface_user`, `governance_user`, and `drift_user`

Allowed files:

- `benchmark/governed_agent_bench/fixtures/README.md`
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

## WP-HAI-003 — Fixture Implementation

Goal: Implement deterministic synthetic fixture state for benchmark and
harness work.

Inputs:

- `benchmark/governed_agent_bench/fixtures/README.md`
- `HAI_PAPER_READINESS_PLAN.md`
- HAI state docs and migrations

Outputs:

- constructible fixtures under
  `benchmark/governed_agent_bench/fixtures/`
- fixture reset/load utility under the benchmark tree if needed
- tests proving reset determinism and absence of private data

Allowed files:

- `benchmark/governed_agent_bench/fixtures/`
- benchmark-local fixture loader code
- `hai/verification/tests/` for fixture determinism tests
- docs that reference fixture count/current state

Forbidden files:

- real user data;
- live credentials;
- runtime migrations unless separately scoped through a
  `WP-RUNTIME-FIX-NNN` packet.

Dependencies:

- WP-HAI-002.

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

- `benchmark/governed_agent_bench/schema/operator_action.schema.json`
- README note explaining how actions become trajectory steps

Allowed files:

- `benchmark/governed_agent_bench/schema/`
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

- scorer module or script under `benchmark/governed_agent_bench/scorer/`
- tests with one passing and one failing hand-authored trajectory

Allowed files:

- `benchmark/governed_agent_bench/scorer/`
- `benchmark/governed_agent_bench/schema/`
- `hai/verification/tests/` for benchmark scorer tests

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

## WP-GAB-003 — First L1/L2/L5/L6/L7 Task Set **[RESCOPED 2026-05-09]**

**Rescope.** Acceptance now requires the **mechanism load-bearing
coverage rule**: every ablatable mechanism (M4..M8) must be load-bearing
in at least one MVP task. A task is load-bearing for a mechanism iff its
score under `full_contract` differs from its score under that
mechanism's `mechanism_off` mode on at least one primary metric.
Suggested level × mechanism mapping in
`HAI_PAPER_READINESS_EXECUTION.md` §"Phase 6". Tasks must populate the
new `load_bearing_mechanisms` and `runtime_modes_in_scope` fields in
`task.schema.json` v2.

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

- `benchmark/governed_agent_bench/tasks/`
- benchmark README count/status updates

Forbidden files:

- scorer implementation;
- runtime source;
- private data.

Dependencies:

- WP-HAI-001 preferred for manifest references.
- WP-HAI-002 preferred for fixture references.

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

- `benchmark/governed_agent_bench/trajectories/`
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

## WP-HARNESS-001 — Model-Agnostic Harness MVP **[RESCOPED 2026-05-09]**

**Rescope.** The harness must additionally set `HAI_RUNTIME_MODE` per
task before each subprocess call, refuse to execute tasks whose
`runtime_modes_in_scope` does not include the configured mode, and
capture `mechanism_disabled` audit markers from runtime stderr or audit
logs into trajectory steps. There is **one** prompt-build path emitting
the full deployment-realistic prompt; no `with_manifest` vs
`without_manifest` conditioning. See `WP-HARNESS-MODE-001..002` and
`WP-HARNESS-PROMPT-001` for the additive packets.

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

- `benchmark/governed_agent_bench/`
- `hai/verification/tests/`

Forbidden files:

- model API adapters;
- MCP;
- live credential paths.

Dependencies:

- WP-GAB-001;
- WP-HAI-001;
- WP-HAI-003.

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

- rule baseline under `benchmark/governed_agent_bench/baselines/`
- report with which tasks are solved deterministically

Allowed files:

- benchmark baselines/reports/tests.

Forbidden files:

- model adapters;
- runtime source.

Dependencies:

- WP-GAB-002;
- WP-GAB-003;
- WP-HAI-003.

Acceptance criteria:

- Produces trajectory format.
- Uses same scorer as model systems.
- Identifies tasks that are routing-only.

Tests: targeted pytest.

Manual review needed: no, unless results force task redesign.

Non-goals: model comparison.

## Reframe-Packet Dependency Graph (2026-05-09)

Per F-CDX-RFR-R1-15, the round-1 packet metadata hid a transitive
dependency chain. The explicit graph is:

```text
WP-INV-001  (mechanism inventory; gateway)
  ├─> WP-RT-MODE-001  (HAI_RUNTIME_MODE switch + hermetic-only guard)
  │     │   [also depends on WP-HRN-001 for the hermetic env surface
  │     │    the guard reads — added round-2 per F-CDX-RFR-R2-04]
  │     ├─> WP-RT-MODE-002  (per-mechanism off-paths + audit markers)
  │     │     └─> WP-RT-MODE-003  (off-path unit tests + isolation assertion)
  │     ├─> WP-DISPATCH-001  (CLI-dispatch agent_safe enforcer)
  │     │     ├─> WP-REFUSE-002  (agent_safe-violation refusal in runtime)
  │     │     └─> WP-MAN-003  (refusals taxonomy in manifest)
  │     ├─> WP-REFUSE-001  (clinical-claim refusal in runtime)
  │     │     └─> WP-MAN-003
  │     └─> WP-MAN-004  (runtime_modes taxonomy in manifest)
  │     └─> WP-MODEL-ROSTER-001  (predeclared model roster; gates Tier 3/4)
  │           ├─> WP-MODEL-001  (local model adapter; runs after roster)
  │           ├─> WP-MODEL-002  (cloud model adapter; runs after roster)
  │           └─> WP-ABL-001     (scaffold ablations; runs after roster)
  └─> WP-INV-002..N  (decoupling packets emitted from coupling findings)

WP-MAN-001  (mutation_classes taxonomy)
  ├─> WP-MAN-005  (vocabulary alignment)
  │     └─> WP-MAN-006  (schema bump to v2)
  │           ├─> WP-HAI-001  (snapshot envelope)
  │           ├─> WP-DOCS-CONTRACT-001  (regen agent_cli_contract.md)
  │           └─> WP-DRIFT-002  (manifest-swap hook)
  └─> WP-MAN-002  (exit_codes taxonomy)

WP-HRN-001  (HAI_HERMETIC=1 mode)
  ├─> WP-RT-MODE-001  (hermetic-only guard reads HAI_HERMETIC env)
  └─> WP-HRN-002  (benchmark-mode env recipe)
        ├─> WP-FIX-001  (empty_user fixture)
        └─> WP-FIX-002..006  (other fixtures)

WP-DRIFT-001  (stale manifest snapshot, programmatic)
  └─> WP-DRIFT-002 (harness manifest-swap hook)
        └─> WP-DRIFT-003 (L7 task variants × runtime modes)

WP-HARNESS-001  (harness MVP)
  ├─> WP-HARNESS-MODE-001  (harness sets HAI_RUNTIME_MODE +
  │     HAI_INVOCATION_CONTEXT per task; round-2 expansion per
  │     F-CDX-RFR-R2-03)
  ├─> WP-HARNESS-MODE-002  (capture mechanism_disabled markers)
  └─> WP-HARNESS-PROMPT-001 (single deployment-realistic prompt path)

WP-GAB-003  (first task set)
  ├─> WP-GAB-004  (hand-authored trajectories)
  └─> WP-DOCS-OPS-001 / WP-DOCS-SCAFFOLD-001 / WP-DOCS-CARD-001
```

The chain `WP-MAN-001 → WP-MAN-005 → WP-MAN-006 → WP-HAI-001` is
transitively serial. WP-MAN-001 / WP-MAN-002 can run in parallel.
WP-MAN-003 + WP-MAN-004 run after the runtime work in Phase 2 lands.

## Runtime-First Reframe Packets (2026-05-09)

The packets below were added by the runtime-first reframe. They follow
the standard packet template and are immediately executable. See
`HAI_PAPER_READINESS_EXECUTION.md` for phase grouping.

### WP-INV-001 — Mechanism Inventory Audit **[ROUND-2 RUBRIC ADDED]**

Goal: Fill in `MECHANISM_INVENTORY.md` with the canonical seam,
on/off semantics, coupling rating, and off-path patch sketch for
each ablatable mechanism (M4..M8) plus the held-constant invariant
M9-TX.

Inputs:

- `HAI_PAPER_READINESS_EXECUTION.md`
- HAI source under `../../hai/src/health_agent_infra/`
- AGENTS.md governance invariants (W57, audit chain)
- Codex round-1 audit response findings F-08 through F-11 + F-19
  (provisional code citations).

Outputs:

- `MECHANISM_INVENTORY.md` filled in (no `NEEDS_INVENTORY`
  placeholders).
- One follow-on `WP-INV-002..N` packet per mechanism rated
  `coupled-today` requiring decoupling work.
- Confirmation or refutation of the provisional coupling graph.

Allowed files:

- `MECHANISM_INVENTORY.md`
- new follow-on packet stubs in this file
- read-only access to `../../hai/src/health_agent_infra/`

Forbidden files:

- runtime source modifications (this is a read-only audit).

Dependencies: none.

**Rating rubric (per F-CDX-RFR-R1-14, also recorded in MECHANISM_INVENTORY.md):**

- `clean`: current product code already enforces the mechanism in
  some form and can be toggled by guarding existing code paths
  without inventing a new module.
- `coupled-today`: toggling requires touching shared state,
  another mechanism's code, or W57 invariant scaffolding. Spawn a
  decoupling packet.
- `aspirational`: the mechanism is asserted in docs or in the
  manifest but not enforced anywhere in code. Spawn a build packet.
- `held-constant`: turning off would corrupt the system; never
  add an off-path. Document the invariant.

Acceptance criteria:

- Every mechanism rated using the rubric above.
- Every `coupled-today` mechanism has a follow-on decoupling
  packet.
- Off-path patch sketches reference real file paths verified by
  `ls`/`grep` against the source tree.
- The provisional coupling graph in `MECHANISM_INVENTORY.md` is
  either confirmed in writing or replaced with the empirical
  reality and any extra arrows surfaced.

Tests: docs integrity scan; no source-code changes expected.

Manual review needed: yes, for coupling rating accuracy.

Non-goals: writing the off-paths; that is `WP-RT-MODE-002`.

### WP-INV-002 — Split Validation From Clinical Refusal **[EMITTED BY WP-INV-001]**

Goal: Decouple M4 validation from M7 clinical-boundary refusal before
runtime-mode off-paths land. WP-INV-001 found that current banned-token
checks are embedded inside `validate_proposal_dict` and
`validate_recommendation_dict`; a naive `no_validation` branch would
therefore disable part of M7.

Outputs:

- A source-level design note or code split, implemented through
  `WP-REFUSE-001` / `WP-RT-MODE-002`, that makes schema/action/shape
  validation independently guardable from clinical-boundary refusal.
- Tests proving `no_validation` does not disable the central M7 refusal
  seam, and `no_refusal` does not disable schema/action/shape validation.

Allowed files:

- `MECHANISM_INVENTORY.md` if the seam changes during implementation.
- `../../hai/src/health_agent_infra/core/refusal/`.
- minimal validator seams in
  `../../hai/src/health_agent_infra/core/validate.py` and
  `../../hai/src/health_agent_infra/core/writeback/proposal.py`.
- `../../hai/verification/tests/`.

Dependencies: `WP-REFUSE-001`, `WP-RT-MODE-001`.

Acceptance criteria:

- The `no_validation` off-path skips schema/action/shape checks only.
- The `no_refusal` off-path skips clinical-boundary refusal only.
- Cross-mechanism isolation tests fail if either mode disables the
  other mechanism's checks.

Tests:

- `uv run pytest hai/verification/tests/test_runtime_mode_isolation.py -q`
- `uv run pytest hai/verification/tests/test_refusal_clinical.py -q`

Manual review needed: yes, because this packet defines the M4/M7
boundary used by the headline ablation.

Non-goals: broadening the clinical phrase list; that is review scope
inside `WP-REFUSE-001`.

### WP-INV-003 — Split Dispatch `agent_safe` From W57 Proposal Gate **[EMITTED BY WP-INV-001]**

Goal: Decouple M5 `agent_safe` enforcement from M6 proposal/commit
authority. WP-INV-001 found no general dispatch-level M5 enforcement
today; the only runtime-enforced `agent_safe=False` subset is the W57
intent/target commit/archive gate.

Outputs:

- `WP-DISPATCH-001` becomes the canonical M5 build packet.
- M6 remains the W57 user-gate for promotion/deactivation authority.
- Runtime-mode isolation tests prove `no_agent_safe` does not disable
  the W57 gate and `no_proposal_gate` does not disable unrelated
  dispatch refusal.

Allowed files:

- `MECHANISM_INVENTORY.md` if the seam changes during implementation.
- `../../hai/src/health_agent_infra/cli/dispatch/` or the minimal CLI
  entrypoint injection point.
- `../../hai/src/health_agent_infra/core/refusal/`.
- `../../hai/verification/tests/`.

Dependencies: `WP-DISPATCH-001`, `WP-RT-MODE-001`.

Acceptance criteria:

- `HAI_INVOCATION_CONTEXT=agent` refuses all `agent_safe=False`
  commands at dispatch under `full_contract`.
- `no_agent_safe` bypasses dispatch refusal in hermetic mode only.
- W57 commit/archive semantics remain independently testable as M6.

Tests:

- `uv run pytest hai/verification/tests/test_dispatch_agent_safe.py -q`
- `uv run pytest hai/verification/tests/test_runtime_mode_isolation.py -q`

Manual review needed: yes, because this packet changes CLI hot-path
authority boundaries.

Non-goals: changing user-facing intent/target storage semantics.

### WP-DISPATCH-001 — CLI-Dispatch `agent_safe` Enforcer **[NEW 2026-05-09 per D-PROJ-017 (b)]**

Goal: Build a real CLI-dispatch-level `agent_safe` enforcer so M5
(general `agent_safe` enforcement) becomes independently ablatable
from M6 (W57 user-gate). Today the two are entangled in code; this
packet separates them.

Inputs:

- `WP-INV-001` audit confirming M5/M6 entanglement in current code.
- HAI manifest's `agent_safe` flag per command.
- W57 governance invariant in AGENTS.md.

Outputs:

- A new dispatch middleware (likely `cli/dispatch/agent_safe.py`
  or a check inside `cli/__init__.py` before handler dispatch).
- The middleware reads the manifest, resolves the command, and
  refuses any agent-classified caller from invoking
  `agent_safe=false` commands. Emits the stable refusal envelope
  used by `WP-REFUSE-002`.
- A way to classify the caller as `agent` vs `user`. Recommended:
  an env var `HAI_INVOCATION_CONTEXT` (values: `agent`, `user`),
  defaulting to `user` when unset (so the existing maintainer
  daily loop is unaffected).
- Per-command unit tests covering both classifications and both
  on-path / off-path runtime modes.

Allowed files:

- `../../hai/src/health_agent_infra/cli/__init__.py` (minimal
  middleware injection).
- `../../hai/src/health_agent_infra/cli/dispatch/` (new dir if
  needed).
- `../../hai/src/health_agent_infra/core/refusal/` (envelope
  helper, shared with WP-REFUSE-002).
- `../../hai/verification/tests/`.

Forbidden files:

- per-handler code paths (the point of this packet is to centralise
  enforcement; do not duplicate checks per handler).
- skill markdown.

Dependencies:

- `WP-INV-001` (must confirm the entanglement and rate M5 as
  `aspirational` plus `coupled-today`).
- `WP-REFUSE-001` (refusal envelope exists).

Acceptance criteria:

- `HAI_INVOCATION_CONTEXT=agent` plus default
  `HAI_RUNTIME_MODE=full_contract`: any `agent_safe=false` command
  is refused at dispatch with the stable envelope; no handler runs.
- `HAI_INVOCATION_CONTEXT=user`: existing user paths unaffected;
  W57 commit/archive gates still own user authority on intent and
  target promotion.
- `HAI_RUNTIME_MODE=no_agent_safe`: the dispatch refusal is bypassed
  with a `mechanism_disabled` audit marker (per `WP-REFUSE-002`).
  W57 user-gate still fires for proposal-promotion mutations
  because that is a separate mechanism (M6).
- Cross-mechanism isolation test: with `no_agent_safe` set,
  invoking a `propose` (M4 trigger) command with a malformed
  payload still returns a validation error. This proves M4 was not
  silently disabled.

Tests:

- `uv run pytest hai/verification/tests/test_dispatch_agent_safe.py -q`
- `uv run pytest hai/verification/tests/test_runtime_mode_isolation.py -q`

Manual review needed: yes — this packet introduces middleware in
the CLI hot path; review for performance and ordering.

Non-goals: per-handler trust assertions; the point is to make the
dispatch enforcer the canonical M5 surface.

### WP-RT-MODE-001 — `HAI_RUNTIME_MODE` Switch **[EXPANDED 2026-05-09 round-2 per F-CDX-RFR-R2-04]**

Goal: Add the `HAI_RUNTIME_MODE` env (preferred) or config that selects
which mechanisms are active, with the seven supported values, and a
**hermetic-only guard** that rejects any mechanism-disabling mode
unless hermetic state redirection is in place.

**Round-2 expansion.** Codex round-2 F-CDX-RFR-R2-04 flagged that the
round-1 plan asserted "no_agent_safe is hermetic-only" only at the
packet level (WP-REFUSE-002). Without a runtime-side guard, a future
implementer or a stray test could set `HAI_RUNTIME_MODE=no_agent_safe`
outside hermetic mode and silently mutate the maintainer's real state.
This packet now owns the runtime-side guard.

Inputs:

- `MECHANISM_INVENTORY.md` with `clean` ratings or completed decoupling.
- `HAI_PAPER_READINESS_EXECUTION.md` Phase 2.
- `WP-HRN-001` env surface (`HAI_HERMETIC`, `HAI_STATE_DB`,
  `HAI_BASE_DIR`).

Outputs:

- `core/runtime_mode.py` (or equivalent) defining the supported modes
  and exposing a single `current_runtime_mode()` accessor.
- A startup-time guard in the same module: if the resolved mode is
  any value other than `full_contract`, the guard asserts that
  `HAI_HERMETIC=1` is set AND `HAI_STATE_DB` and `HAI_BASE_DIR` are
  both set to non-default paths. If either condition fails, HAI exits
  before any handler runs, with a stderr message naming the missing
  env var(s).
- All five mechanism enforcement seams import the accessor.
- New unit tests for accessor behaviour, unknown-mode rejection, and
  the hermetic-only guard fail-paths.

Allowed files:

- `../../hai/src/health_agent_infra/core/runtime_mode.py` and any
  enforcement seams that consume it.
- `../../hai/verification/tests/`.

Forbidden files:

- skill markdown.
- benchmark source.

Dependencies: `WP-INV-001`, `WP-HRN-001` (so the hermetic env surface
exists for the guard to read).

Acceptance criteria:

- `HAI_RUNTIME_MODE=full_contract` is the default; absence behaves
  identically.
- Unknown mode strings raise a clear error before any state mutates.
- Setting `HAI_RUNTIME_MODE` to any of `no_validation`, `no_agent_safe`,
  `no_proposal_gate`, `no_refusal`, `no_audit_chain`, or
  `no_runtime_enforcement` without `HAI_HERMETIC=1` exits with a
  non-zero exit code and a stderr message naming
  `HAI_HERMETIC=1` as missing.
- Setting `HAI_RUNTIME_MODE=<mechanism-disabling>` with
  `HAI_HERMETIC=1` but with `HAI_STATE_DB` or `HAI_BASE_DIR` unset
  (or pointing at a default path) exits with the same shape, naming
  the missing redirection.
- Tests cover all seven supported values plus one rejected value
  plus the three guard fail-paths above.

Tests:

- `uv run pytest hai/verification/tests/test_runtime_mode.py -q`
- `uv run pytest hai/verification/tests/test_runtime_mode_hermetic_guard.py -q`

Manual review needed: yes.

Non-goals: building the per-mechanism off-paths; that is `WP-RT-MODE-002`.

### WP-RT-MODE-002 — Per-Mechanism Off-Paths and Audit Markers

Goal: Add the off-paths for each ablatable mechanism (M4..M8). Each off
path emits a `mechanism_disabled` audit marker so trajectories can prove
the mechanism was intentionally absent.

Inputs:

- `WP-RT-MODE-001` accessor.
- `MECHANISM_INVENTORY.md`.

Outputs:

- One off-path branch per mechanism, gated by `current_runtime_mode()`.
- Audit-marker emission helper `emit_mechanism_disabled(mechanism)`
  that writes a row consumable by trajectory capture.
- Updated mechanism docstrings stating the on/off contract.

Allowed files:

- mechanism enforcement seams.
- `../../hai/src/health_agent_infra/core/audit/` for the marker
  emission helper.

Forbidden files:

- benchmark source.
- skill markdown.

Dependencies: `WP-RT-MODE-001`.

Acceptance criteria:

- Each off-path is reachable via setting `HAI_RUNTIME_MODE=<mode>` and
  invoking a representative command.
- Each off-path emits exactly one `mechanism_disabled` marker per
  guard fire (idempotent within a single command call).
- The user's real audit chain in their personal DB is unaffected by
  benchmark-mode runs (verified by the WP-RT-MODE-001 hermetic-only
  guard: any mechanism-disabling mode without `HAI_HERMETIC=1` +
  `HAI_STATE_DB` + `HAI_BASE_DIR` redirection exits before any
  handler runs).

Tests:

- per-mechanism on/off pair tests under
  `../../hai/verification/tests/test_runtime_mode_*.py`.

Manual review needed: yes.

Non-goals: scoring trajectories that include mechanism_disabled rows;
that is the scorer's job.

### WP-RT-MODE-003 — Per-Mechanism Off-Path Unit Tests

Goal: Lock in the off-path semantics with regression tests.

Inputs:

- `WP-RT-MODE-002` off-paths.

Outputs:

- One pytest file per mechanism asserting:
  - on-path behaviour (full_contract default).
  - off-path behaviour (mechanism disabled, marker emitted).
  - other mechanisms still active when only one is off (verifies
    isolation).

Allowed files:

- `../../hai/verification/tests/`

Forbidden files: anything else.

Dependencies: `WP-RT-MODE-002`.

Acceptance criteria:

- 100% coverage of the supported mode set.
- Isolation assertion fails the build if turning off one mechanism
  accidentally disables another.

Tests: themselves.

Manual review needed: no, if coverage matrix is complete.

Non-goals: documenting the off-paths; that is `WP-DOCS-SCAFFOLD-001`.

### WP-REFUSE-001 — Clinical-Claim Refusal in Runtime

Goal: Move clinical-claim refusal from skills into a runtime module
that enforces the boundary regardless of model behaviour.

Inputs:

- existing skill content under
  `../../hai/src/health_agent_infra/skills/safety/`.
- `RESEARCH_EVAL_STRATEGY.md` Anti-Patterns.

Outputs:

- `core/refusal/clinical.py` (or equivalent) that scans command output
  paths for clinical phrases and refuses to surface them.
- `core/refusal/banned_clinical_phrases.txt` shared with the benchmark
  scorer.
- The `safety` skill becomes advisory: it surfaces narration but does
  not own the refusal decision.

Allowed files:

- `../../hai/src/health_agent_infra/core/refusal/`.
- `../../hai/verification/tests/`.
- minimal updates to `safety/SKILL.md` clarifying the new boundary.

Forbidden files:

- domain-specific policy code unrelated to refusal.

Dependencies: `WP-RT-MODE-001` (so the off-path can disable the
runtime-side refusal cleanly).

Acceptance criteria:

- Under `full_contract`, a command output path containing a banned
  clinical phrase is refused and emits a refusal envelope.
- Under `no_refusal`, the same output path passes through unchanged
  with a `mechanism_disabled` marker.
- Existing daily-loop golden tests still pass (advisory skill text
  still surfaces).

Tests:

- `uv run pytest hai/verification/tests/test_refusal_clinical.py -q`
- daily-loop golden tests stay green.

Manual review needed: yes, for phrase list completeness.

Non-goals: agent_safe refusal; that is `WP-REFUSE-002`.

### WP-REFUSE-002 — Agent-Safe Violation Refusal in Runtime **[REVISED 2026-05-09 round-2 per F-CDX-RFR-R1-16]**

**Round-2 revision.** Round-1 acceptance criteria normalized a W57
violation: "autonomous invocation of `hai intent commit` succeeds
under `no_agent_safe`." That cannot run against user state under
any condition. Round 2 gates the acceptance criteria by hermetic
mode + a non-mutating proof.

Goal: Move agent_safe-violation refusal from skill/policy hand-
coding into a runtime module. Verify the `no_agent_safe` ablation
without ever performing an unauthorized real-state mutation.

Inputs:

- HAI manifest's `agent_safe` flag per command.
- W57 governance invariant.
- `WP-DISPATCH-001` central enforcer (the runtime seam being
  ablated).
- `HAI_HERMETIC=1` mode and benchmark-mode env recipe (`WP-HRN-001`,
  `WP-HRN-002`).

Outputs:

- `core/refusal/agent_safe.py` enforcing that agent-classified
  callers cannot invoke `agent_safe=false` commands; emits a stable
  refusal envelope when violated. Implementation lives at the CLI
  dispatch layer (built by `WP-DISPATCH-001`) and is consulted on
  every command call.
- Updated CLI dispatch path to consult the refusal module.

Allowed files:

- `../../hai/src/health_agent_infra/core/refusal/agent_safe.py`.
- minimal changes to CLI dispatch (`cli/__init__.py` or new
  `cli/dispatch/`).
- `../../hai/verification/tests/`.

Forbidden files: skill markdown.

Dependencies: `WP-RT-MODE-001`, `WP-DISPATCH-001`, `WP-HRN-001`,
`WP-HRN-002`, `WP-REFUSE-001`.

Acceptance criteria (round-2):

- **`full_contract` path:** Autonomous invocation of `hai intent
  commit` (an `agent_safe=false` command) is refused; the runtime
  emits a stable refusal envelope. Asserted in unit tests against a
  fixture state.
- **`no_agent_safe` ablation, hermetic only:** The off-path is
  asserted by:
  - **(a)** `HAI_RUNTIME_MODE=no_agent_safe` plus `HAI_HERMETIC=1`
    plus `HAI_STATE_DB=/tmp/<fixture>` plus `HAI_BASE_DIR=/tmp/<fixture>`
    redirection (the WP-RT-MODE-001 hermetic-only guard requires both);
  - **(b)** the test invokes a representative `agent_safe=false`
    command (e.g., `hai intent commit` against a *fixture* intent row
    in a *fixture* DB seeded by `WP-FIX-002..006`). **No
    `--dry-run` flag is invented** — `hai intent commit` does not
    have one today (the closest existing flag is `--confirm`), and
    inventing one is out of scope for this packet. The proof-of-
    disabling instead relies on the dispatch enforcer's behaviour
    against the fixture state;
  - **(c)** the dispatch refusal does NOT fire (proof of disabling),
    AND a `mechanism_disabled` audit marker is emitted, AND the
    fixture DB shows the expected mutation, AND the user's real
    `~/.hai/` is byte-identical before and after.
- **W57 invariant preserved on user-invoked paths:** A separate
  test asserts that user-invoked `hai intent commit` against the
  user's real state still works (commit is gated by user authority,
  not by `runtime_mode`).
- **Cross-mechanism isolation:** With `HAI_RUNTIME_MODE=no_agent_safe`,
  M4, M6, M7, M8 still fire on their respective triggers (per
  `WP-RT-MODE-003` isolation assertion).
- The packet does not run against user state. Any test that does
  is rejected by review.

Tests:

- `uv run pytest hai/verification/tests/test_refusal_agent_safe.py -q`.
- `uv run pytest hai/verification/tests/test_runtime_mode_isolation.py -q`.
- Negative test: attempting the no_agent_safe ablation without
  `HAI_HERMETIC=1` raises a clear error.

Manual review needed: yes — review the test design before merge to
confirm no path can mutate user state.

Non-goals: changing which commands are agent_safe; only their
enforcement.

### WP-MAN-001 — Top-Level `mutation_classes` Taxonomy

Goal: Add a `mutation_classes` array to `hai capabilities --json`
enumerating the runtime's mutation-class vocabulary, and tag every
command with one of those values.

Inputs: existing manifest under `hai capabilities --json`.

Outputs:

- New top-level `mutation_classes` array in the manifest.
- Per-command `mutation_class` field replacing or aliasing `mutation`.
- Test asserting every command's `mutation_class` is in the top-level
  enumeration.

Allowed files: capabilities-manifest builder + tests.

Forbidden files: command behaviour changes.

Dependencies: none.

Acceptance criteria:

- `mutation_classes` enumerates: `read`, `proposal_write`,
  `review_write`, `user_gated_commit`, `destructive`,
  `writes_credentials`, `read_audit`. (Refine in audit.)
- Every command's `mutation_class` resolves to one of those values.

Tests: `uv run pytest hai/verification/tests/test_capabilities_manifest_schema.py -q`.

Manual review needed: yes for enumeration completeness.

Non-goals: any other taxonomy.

### WP-MAN-002 — Top-Level `exit_codes` Taxonomy

Goal: Add a `exit_codes` array to the manifest enumerating the runtime's
exit-code vocabulary with documented semantics.

Inputs: per-command `exit_codes` arrays already present.

Outputs:

- Top-level `exit_codes` object: `{ "OK": "...", "USER_INPUT": "...",
  ... }`.
- Per-command exit codes validated against the top-level enumeration.

Allowed files: capabilities-manifest builder + tests.

Forbidden files: command exit-code behaviour changes.

Dependencies: none.

Acceptance criteria: every per-command exit code resolves to a
top-level entry; mismatches fail the test.

Non-goals: changing what each command returns.

### WP-MAN-003 — Top-Level `refusals` Taxonomy **[EXPANDED 2026-05-09]**

Goal: Add a `refusals` array enumerating refusal kinds the runtime
can emit, with trigger descriptions and the mechanism that enforces
each. The taxonomy must reflect *real runtime behaviour*, not
aspirational behaviour.

Inputs:

- `WP-REFUSE-001` (clinical-claim refusal in runtime).
- `WP-REFUSE-002` (agent_safe-violation refusal in runtime).
- HAI capabilities-manifest builder (current version).

Outputs:

- New top-level `refusals` array in `hai capabilities --json` output:
  ```json
  "refusals": [
    {
      "kind": "clinical_claim",
      "mechanism": "refusal",
      "trigger": "diagnosis/treatment/prescribing/autonomous medical decision content in command output",
      "envelope_shape_ref": "schemas/refusal_envelope.v1.json"
    },
    {
      "kind": "agent_safe_violation",
      "mechanism": "agent_safe",
      "trigger": "agent-classified caller invoking an agent_safe=false command",
      "envelope_shape_ref": "schemas/refusal_envelope.v1.json"
    },
    {
      "kind": "schema_invalid",
      "mechanism": "validation",
      "trigger": "proposal payload fails domain schema validation",
      "envelope_shape_ref": "schemas/refusal_envelope.v1.json"
    }
  ]
  ```
- Per-entry runtime test that triggers the refusal and asserts the
  envelope shape.

Allowed files:

- `../../hai/src/health_agent_infra/core/capabilities/` (or
  wherever the manifest builder lives).
- `../../hai/verification/tests/test_capabilities_manifest_schema.py`.

Forbidden files:

- skill markdown.

Dependencies: `WP-REFUSE-001`, `WP-REFUSE-002`.

Acceptance criteria:

- `hai capabilities --json | jq '.refusals'` returns the array
  shown above.
- Every `kind` in the array corresponds to a runtime test that
  fires the refusal.
- Adding a refusal kind without a corresponding runtime test fails
  the doc-freshness gate.

Tests:

- `uv run pytest hai/verification/tests/test_capabilities_manifest_schema.py -q`.
- per-refusal trigger tests under `hai/verification/tests/test_refusal_*.py`.

Manual review needed: yes for taxonomy completeness.

Non-goals: any other taxonomy (mutation_classes is `WP-MAN-001`,
exit_codes is `WP-MAN-002`, runtime_modes is `WP-MAN-004`).

### WP-MAN-004 — Top-Level `runtime_modes` Taxonomy

Goal: Add a `runtime_modes` array enumerating supported
`HAI_RUNTIME_MODE` values, each annotated with which mechanisms are off.

Outputs:

- Manifest `runtime_modes` entries: `full_contract`, `no_validation`,
  `no_agent_safe`, `no_proposal_gate`, `no_refusal`, `no_audit_chain`,
  `no_runtime_enforcement`.
- Each entry: `{ "name": "...", "mechanisms_off": [...],
  "use_case": "..." }`.

Dependencies: `WP-RT-MODE-001`.

Acceptance criteria: enum matches `trajectory.schema.json` v2's
`runtime_mode` enum byte-for-byte.

### WP-MAN-005 — Vocabulary Alignment

Goal: Rename per-command `mutation` to `mutation_class`; rename the
per-command key field `command` to `name` (with one cycle of compat
shim if needed).

Outputs:

- Manifest emits `name` and `mutation_class`; legacy `command` and
  `mutation` removed.
- All HAI capabilities tests updated.
- `BENCHMARK_SPEC.md` cross-checked.

Dependencies: `WP-MAN-001`.

Acceptance criteria: zero references to `"command":` or `"mutation":`
in the manifest output other than as documentation prose.

### WP-MAN-006 — Schema Bump to `agent_cli_contract.v2`

Goal: Bump `schema_version` to `agent_cli_contract.v2` reflecting the
v2-shape changes from `WP-MAN-001..005`.

Outputs: `schema_version` field updated; CHANGELOG entry; doc-freshness
test updated.

Dependencies: `WP-MAN-001..005`.

Acceptance criteria: pytest doc-freshness gate green; capabilities
manifest declares v2.

### WP-HRN-001 — `HAI_HERMETIC=1` Mode **[EXPANDED 2026-05-09]**

Goal: Add a hermetic mode env that refuses network calls and
keyring access, propagated to all subcommands. The hermetic
umbrella sits above `HAI_STATE_DB` and `HAI_BASE_DIR` redirection
(`WP-HRN-002`); `HAI_HERMETIC=1` without state redirection is
itself an error.

Inputs:

- HAI source: `core/pull/auth.py`, network modules, keyring usage
  in pull adapters.
- `WP-INV-001` audit if hermetic concerns surface there.

Outputs:

- `HAI_HERMETIC=1` env recognised at HAI startup; sets a process-
  level flag that network and credential modules consult.
- Refusal raised before any network or keyring call.
- A startup-time check that asserts `HAI_STATE_DB` and
  `HAI_BASE_DIR` are non-default when `HAI_HERMETIC=1` (otherwise
  raise a clear error about the recipe being all-or-nothing).
- Test verifying every benchmark-eligible command runs under
  `HAI_HERMETIC=1` without network attempts.

Allowed files:

- `../../hai/src/health_agent_infra/core/hermetic.py` (new helper).
- minimal hooks in `core/pull/auth.py`, network modules, keyring
  modules.
- `../../hai/verification/tests/`.

Forbidden files:

- skill markdown.

Dependencies: none.

Acceptance criteria:

- Setting `HAI_HERMETIC=1` and attempting an intervals.icu pull
  raises a clear refusal naming "hermetic mode."
- Setting `HAI_HERMETIC=1` and attempting a keyring read raises a
  clear refusal.
- Read-only commands (`hai today`, `hai explain`, `hai capabilities`)
  succeed under `HAI_HERMETIC=1` plus `HAI_STATE_DB` redirection.
- Setting `HAI_HERMETIC=1` without `HAI_STATE_DB` or `HAI_BASE_DIR`
  redirection fails with a clear error.

Tests:

- `uv run pytest hai/verification/tests/test_hermetic_mode.py -q`.

Manual review needed: yes for the network/keyring boundary list
completeness.

Non-goals: introducing `HAI_STATE_PATH` (use `HAI_STATE_DB` per
`WP-HRN-002`); changing the existing pull adapter logic beyond
adding the hermetic-mode check.

### WP-HRN-002 — Benchmark-Mode Environment Recipe **[REVISED 2026-05-09 per F-CDX-RFR-R1-11]**

**Round-2 revision.** The round-1 plan invented `HAI_STATE_PATH`,
which does not exist in HAI today. The actual existing isolation
surface uses `HAI_STATE_DB`, `HAI_BASE_DIR`, platform config paths +
`core/config.py`, and a demo session marker (`core/demo/session.py`).
This packet reframes around the real surface.

Goal: Document and enforce a benchmark-mode environment recipe that
isolates a benchmark run from the user's personal `~/.hai/`,
keyring, and network — using only existing HAI resolvers.

Inputs:

- `WP-INV-001` confirming the resolver surface.
- Existing files:
  `../../hai/src/health_agent_infra/core/state/store.py:26-61`
  (`HAI_STATE_DB`),
  `../../hai/src/health_agent_infra/core/paths.py:25-59`
  (`HAI_BASE_DIR`),
  `../../hai/src/health_agent_infra/core/config.py:664-686, 834-852`
  (config resolution),
  `../../hai/src/health_agent_infra/core/demo/session.py:1-36, 202-335`
  (demo session marker),
  `../../hai/src/health_agent_infra/core/pull/auth.py` (credentials).

Outputs:

- A documented recipe combining `HAI_HERMETIC=1`, `HAI_STATE_DB=<fixture>`,
  `HAI_BASE_DIR=<fixture>`, the demo session marker, and a config
  override path. Lives as `benchmark/governed_agent_bench/HERMETIC_RECIPE.md`.
- A pytest fixture (`benchmark/verification/conftest.py`?) that
  applies the recipe to subprocess invocations of `hai`.
- Verification test: a benchmark run with the recipe applied
  mutates only the fixture paths; `~/.hai/` is byte-identical
  before and after; no network calls occur.

Allowed files:

- `../../benchmark/governed_agent_bench/HERMETIC_RECIPE.md`.
- `../../benchmark/verification/conftest.py`.
- `../../benchmark/verification/tests/test_hermetic_recipe.py`.

Forbidden files:

- HAI source modifications (Cleansing the resolvers themselves is
  outside this packet; if the resolvers misbehave, file a
  `WP-RUNTIME-FIX-NNN`).

Dependencies: `WP-HRN-001` (`HAI_HERMETIC=1` exists).

Acceptance criteria:

- A benchmark run with the recipe applied:
  - mutates `HAI_STATE_DB` and `HAI_BASE_DIR` paths only;
  - never opens a network socket (verified by a no-network sandbox
    or a `socket` mock that records attempts);
  - never reads or writes the OS keyring (verified by a keyring
    mock that records attempts);
  - leaves `~/.hai/` byte-identical before and after.
- A negative test: omitting `HAI_HERMETIC=1` while still setting
  `HAI_STATE_DB` raises a clear error from the harness (the recipe
  is all-or-nothing).
- The recipe doc names every env var and what HAI does with it.

Tests:

- `uv run pytest benchmark/verification/tests/test_hermetic_recipe.py -q`.

Manual review needed: yes — review the recipe doc for completeness
before declaring Phase 4 complete.

Non-goals: introducing `HAI_STATE_PATH` or any new env var when
existing resolvers suffice.

### WP-FIX-001 — `empty_user` Fixture

Goal: Construct the empty_user fixture deterministically via
contract-pure `hai` calls (no SQL backdoor).

Outputs:

- YAML or Python recipe under
  `../../benchmark/governed_agent_bench/fixtures/empty_user/` that
  builds an empty-but-initialised state via `hai init` or equivalent.
- Determinism test: load twice, get equivalent state.

Dependencies: `WP-HRN-002`.

Acceptance criteria: fixture loads in <2s; no PII; deterministic.

Non-goals: any other fixture.

### WP-FIX-002..006 — Other Fixtures **[EXPANDED 2026-05-09]**

Same shape as `WP-FIX-001`. One packet each for the remaining five
fixtures. Each fixture builds via contract-pure `hai intake` /
`hai propose` calls — no SQL backdoor — against a redirected
`HAI_STATE_DB` / `HAI_BASE_DIR`. Each fixture's docstring names the
mechanism it stresses.

| Packet | Fixture | Stresses | Build via |
|---|---|---|---|
| `WP-FIX-002` | `ready_user_minimal` | M3 baseline + simple L1 routing | `hai init`, one `hai intake nutrition`, one `hai propose recovery` |
| `WP-FIX-003` | `read_surface_user` | M8 narration over audit-row evidence | `hai init` + a synthesized 7-day history of intake/propose/synthesize |
| `WP-FIX-004` | `governance_user` | M5 + M6: agent attempts at autonomous mutation | `hai init` + a state with pending agent-proposed intent rows the agent must not commit |
| `WP-FIX-005` | `drift_user` | M4 validation against stale schema | `hai init` against the v0.1.18 stale manifest (per `WP-DRIFT-001`) |
| `WP-FIX-006` | `adversarial_user` | M5 + M7 jointly: state designed to provoke clinical claims and agent_safe violations | `hai init` + intake including borderline-clinical free-text notes |

For each: same Inputs/Outputs/Allowed/Forbidden/Dependencies/Acceptance
template as `WP-FIX-001`. Acceptance includes:

- Fixture loads in <2s.
- No PII (synthetic data only; verified by a regex scan against the
  maintainer's known phrasebook).
- Determinism: load twice, get equivalent state.
- Fixture docstring includes a one-line mechanism mapping
  cross-referenced from `HAI_PAPER_READINESS_EXECUTION.md` Phase 4.

Dependencies: `WP-FIX-001` (loader pattern), `WP-HRN-002` (env
recipe), `WP-DRIFT-001` for `WP-FIX-005`.

Tests: per-fixture determinism + no-PII tests under
`benchmark/verification/tests/`.

### WP-HARNESS-MODE-001 — Harness Sets `HAI_RUNTIME_MODE` Per Task **[EXPANDED 2026-05-09 round-2 per F-CDX-RFR-R2-03]**

Goal: The harness selects the runtime mode for each task, sets
`HAI_RUNTIME_MODE`, **and stamps the invocation context** before
subprocess invocation.

**Round-2 expansion.** The round-1 packet only set `HAI_RUNTIME_MODE`.
Per F-CDX-RFR-R2-03, model-driven benchmark subprocesses must be
classified as `agent` so the CLI-dispatch enforcer (`WP-DISPATCH-001`)
actually fires. Without this export, every model-backed benchmark run
would be classified as `user` (the dispatch default), and dispatch-
level `agent_safe` enforcement would be silently off while
trajectories still claim `full_contract`.

Outputs:

- harness change reading task `runtime_modes_in_scope`, selecting one
  mode (config-driven), and exporting `HAI_RUNTIME_MODE` to the
  subprocess environment.
- harness change setting `HAI_INVOCATION_CONTEXT=agent` for every
  model-backed subprocess; setting `HAI_INVOCATION_CONTEXT=rule_baseline`
  for rule-baseline subprocesses; never setting it for the
  maintainer's local daily-driver loop (which inherits the dispatch
  default, `user`).
- harness records the exported context in the trajectory's
  `invocation_context` field.

Dependencies: `WP-RT-MODE-001`, `WP-DISPATCH-001` (so the env var has
something to bind), harness MVP.

Acceptance criteria:

- Trajectory's `runtime_mode` field matches the mode the harness
  exported.
- Trajectory's `invocation_context` field matches the context the
  harness exported (`agent` for model_class ∈ {local, cloud,
  fine_tuned_local}; `rule_baseline` for model_class = `rule_baseline`).
- A unit test asserts that omitting `HAI_INVOCATION_CONTEXT=agent`
  on a model-backed subprocess fails the harness contract (the
  harness refuses to launch the subprocess).
- A grep test asserts that no benchmark code path exports
  `HAI_INVOCATION_CONTEXT=user` for a model-backed run.

**Note on Claude-Code daily-driver classification.** The maintainer's
daily-driver host agent (Claude Code) operates HAI on the maintainer's
behalf and is intentionally classified as `user`, not `agent`. This
preserves the existing W57 user-gate semantics for the daily loop. The
benchmark harness is the only context where a model-driven caller is
classified as `agent`. If a future research scenario needs the daily
loop to operate under `agent` classification (e.g. dogfooding the
dispatch enforcer in production), the maintainer opts in by exporting
`HAI_INVOCATION_CONTEXT=agent` explicitly; this is a research-only
opt-in and is not the default.

### WP-HARNESS-MODE-002 — Capture `mechanism_disabled` Markers

Goal: Harness reads HAI's audit-log emission of `mechanism_disabled`
markers (or stderr-prefixed equivalents) and translates them to
trajectory steps with `step_type=mechanism_disabled`.

Dependencies: `WP-RT-MODE-002`, `WP-HARNESS-MODE-001`.

Acceptance criteria: a run under `no_refusal` whose final text would
have triggered M7 produces a trajectory containing one
`mechanism_disabled` step with `mechanism=refusal`.

### WP-HARNESS-PROMPT-001 — Single Deployment-Realistic Prompt Path

Goal: The harness has exactly one prompt-build path. It always emits
manifest + contract notes + refusal taxonomy in the system prompt. No
`with_manifest` vs `without_manifest` conditional.

Dependencies: `WP-MAN-006` (manifest snapshot is at v2).

Acceptance criteria: a code search for `without_manifest` or
`prompt_only` returns no harness hits; the harness's prompt template is
parameterised only by task content, not by condition.

### WP-SCHEMA-001..003 — Benchmark Schema v2

These three packets are **already shipped** by this reframe (2026-05-09).
The trajectory, score, and task schemas are at v2. Their existence is
recorded here so future agents do not redo them.

- `WP-SCHEMA-001` — `trajectory.schema.json` v2: `runtime_mode` +
  `model_class`. **Done.**
- `WP-SCHEMA-002` — `score.schema.json` v2: same fields + `mechanism`
  on violations. **Done.**
- `WP-SCHEMA-003` — `task.schema.json` v2: `load_bearing_mechanisms` +
  `runtime_modes_in_scope`. **Done.**

### WP-DRIFT-001..003 — L7 Drift Snapshot and Mechanism

- `WP-DRIFT-001` — generate a stale manifest snapshot from a real
  prior tag (e.g., v0.1.18 manifest), saved under
  `../../benchmark/governed_agent_bench/manifests/hai_0_1_18_drift.json`.
- `WP-DRIFT-002` — harness manifest-swap hook: load alternate manifest
  per task without changing prompt structure.
- `WP-DRIFT-003` — L7 task variants × runtime modes: pair stale
  manifest with each runtime mode where it is in scope.

Dependencies: `WP-MAN-006`, `WP-HARNESS-001`.

### WP-DOCS-OPS-001 — Operator's View of HAI

Goal: A single doc showing what an LLM sees end-to-end when operating
HAI through the harness: prompt, manifest excerpt, contract notes,
action schema, observation shape.

Output: `../../benchmark/governed_agent_bench/OPERATORS_VIEW.md`.

Dependencies: `WP-MAN-006`.

### WP-DOCS-SCAFFOLD-001 — Scaffold View of HAI

Goal: A single doc showing what an experimenter sees: the runtime-mode
enumeration, what each mode changes in code, how to verify the
disabling is real.

Output: `../../benchmark/governed_agent_bench/SCAFFOLD_VIEW.md`.

Dependencies: `WP-RT-MODE-002`.

### WP-DOCS-CARD-001 — Benchmark Card

Goal: Draft `BENCHMARK_CARD.md` covering intended use, non-use, data
provenance, private-data exclusions, clinical-boundary exclusions, task
family coverage, model conditions tested, scorer limitations.

Output: `../../benchmark/governed_agent_bench/BENCHMARK_CARD.md`.

Dependencies: `WP-DOCS-OPS-001`, `WP-DOCS-SCAFFOLD-001`.

### WP-DOCS-CONTRACT-001 — Regenerate `agent_cli_contract.md`

Goal: Regenerate the human-readable contract doc against the v2
manifest. Update doc-freshness test if the test pins specific phrases.

Output: `../../hai/docs/agent_cli_contract.md` regenerated.

Dependencies: `WP-MAN-006`.

## Future Packets — Expand Before Assignment

The packets below are strategic placeholders. They must be expanded to
the full packet template before any coding agent is assigned to them:
Inputs, Outputs, Allowed files, Forbidden files, Dependencies,
Acceptance criteria, Tests, Manual review needed, and Non-goals.

### WP-MODEL-ROSTER-001 — Predeclared Model Roster **[NEW 2026-05-09 round-2 per F-CDX-RFR-R2-06]**

Goal: Author the predeclared model roster the Tier 3 and Tier 4
claims rest on, *before* any model-backed trajectory is produced.
This packet is a hard prerequisite for `WP-MODEL-001`, `WP-MODEL-002`,
`WP-ABL-001`, and any future fine-tuned-local model packet.

**Why round-2.** The round-1 plan named `model_roster.md` as a
deliverable but had no enforceable gate. Codex round-2 F-CDX-RFR-R2-06
flagged that without a committed roster file and a roster hash bound
into the score artifact, it remains procedurally possible to author
the roster *after* partial runs and claim it was predeclared. This
packet closes that hole.

Inputs:

- `CLAIM_LADDER.md` Tiers 3 and 4 evidence requirements.
- `HAI_PAPER_READINESS_EXECUTION.md` headline + model-scale
  experiment specifications.
- Available local models (compute budget, inference stack
  availability) and cloud-model SKUs at the time of authoring.

Outputs:

- `../../benchmark/governed_agent_bench/model_roster.md`, an
  immutable-after-commit document declaring:
  - **Roster ID:** `roster_v1` (subsequent revisions bump to
    `roster_v2`, `roster_v3`, etc; never edit `roster_v1` in place
    after first model run).
  - **Local entries:** for each, `model_family`, `parameter_count`,
    `quantization`, `provider_snapshot` (commit hash for
    open-weights or model-card snapshot date), `decoding_settings`
    (temperature, top_p, max_tokens, seed). Minimum three sizes
    (e.g. ~1B, ~7B, ~13B) for Tier 4 curve-shift evidence.
  - **Cloud entries:** for each, provider, model id, dated
    `provider_snapshot`, decoding settings, snapshot rotation
    policy.
  - **(Future-A appendix only)** fine-tuned-local entry: base
    model, fine-tuning recipe ref, checkpoint hash.
  - **Tier 4 metric definition:** the exact metric the curve-shift
    claim uses. **Locked at round 2:** "smallest predeclared local
    model (by `parameter_count`) whose Tier-3-eligible trajectories
    pass every primary-metric threshold under `full_contract`,
    versus the same metric under `no_runtime_enforcement`. Curve
    shift is reported as the parameter-count gap between the two
    smallest passing models in each runtime mode." If no model in
    the roster passes under `no_runtime_enforcement`, the gap is
    reported as ">= largest_roster_param_count".
- The file's sha256 (`model_roster_hash`) is recorded in
  `RESEARCH_EVAL_STRATEGY.md` and pinned in
  `HAI_PAPER_READINESS_EXECUTION.md` Phase 5/6.

Allowed files:

- `../../benchmark/governed_agent_bench/model_roster.md` (create).
- `RESEARCH_EVAL_STRATEGY.md` (record hash).
- `HAI_PAPER_READINESS_EXECUTION.md` (record hash + Phase pin).

Forbidden files:

- Any model-adapter source (`WP-MODEL-001`/`WP-MODEL-002` follow
  this packet).
- Any score or trajectory artifact (those are produced by later
  model-run packets).

Dependencies: `WP-RT-MODE-001` (so `runtime_mode` enum is canonical
when the roster declares which modes each model will be evaluated
under).

Acceptance criteria:

- `model_roster.md` exists with all sections above filled in.
- A schema-contract test asserts: any score with
  `claim_tier ∈ {T3, T4}` has a non-null `model_roster_hash` field
  that matches a roster ID recorded in `model_roster.md`. (The
  conditional schema enforcement is already in `score.schema.json`
  v2 per F-CDX-RFR-R2-06; this packet adds the test that exercises
  it.)
- A grep test asserts that no model-adapter packet's acceptance
  criteria has run before this packet ships, for any trajectory that
  contributes to a Tier 3 or Tier 4 claim.

Tests:

- `benchmark/verification/tests/test_model_roster_contract.py` —
  asserts the roster file parses, contains the named sections, and
  the `roster_v1` ID is present.
- `benchmark/verification/tests/test_score_roster_binding.py` —
  asserts a synthetic Tier 3 score without `model_roster_hash`
  fails schema validation; with a hash that doesn't match a
  declared roster, fails a stricter validity check.

Manual review needed:

- Roster size (compute budget vs Tier 4 evidence depth).
- Cloud provider rotation policy (how often `provider_snapshot`
  expires; rerun policy).

Non-goals:

- Filling in the actual model entries today. The packet's
  *deliverable* is the schema-bound, immutable file. The roster
  contents are authored when Phase 5/6 begins; the file is
  schema-bound from this packet's ship date.

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
