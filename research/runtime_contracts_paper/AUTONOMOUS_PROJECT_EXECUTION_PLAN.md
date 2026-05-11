# Autonomous Project Execution Plan

> **Superseded as current planning:** This file was authored 2026-05-10
> as the autonomous-execution plan targeting a workshop-floor paper.
> The active framing as of 2026-05-11 is
> `research/runtime_contracts_paper/framing_v2/CONVERGED.md` —
> "Deterministic Software Contracts as Trusted Monitors in AI Control
> Protocols" (NeurIPS 2027 main conference, May 2027 deadline). The
> workshop-floor target survives only as the Trajectory A fallback path
> per D-FRAME-009 / D-FRAME-011 if the July 2026 Engels pilot fails.
> Body is preserved as **historical provenance only**, not current
> planning truth. For current planning, read `framing_v2/CONVERGED.md`,
> `framing_v2/ORCHESTRATOR_STATE.md`, and `PROJECT_EXECUTION_PLAN.md`.

---

**Status:** authoritative end-to-end execution plan for autonomous Codex
execution, created 2026-05-10.

**Authority.** This file is the active queue for moving from HAI as the
implementation substrate to a workshop-ready runtime-contract paper. It
consolidates the phase order in `PROJECT_EXECUTION_PLAN.md`, the
runtime-first engineering plan in `HAI_PAPER_READINESS_EXECUTION.md`,
and the packet backlog in `WORK_PACKETS.md`. When packet sequencing in
older docs disagrees with this file, execute this file first and file
the disagreement as a docs-alignment packet.

**Verified checkout.** Before reading or writing planning/source files,
the session verified:

- `pwd` -> `/Users/domcolligan/health_agent_infra`
- `git log -1 --oneline` -> `76d2600 feat(benchmark): add first task seed set`

**Latest continuation verification.** The gate-scaffolding continuation
on 2026-05-10 verified:

- `pwd` -> `/Users/domcolligan/health_agent_infra`
- `git log -1 --oneline` -> `7b692f5 test(benchmark): define model roster gate schema`

The worktree was already dirty before this file was authored. Existing
modified/untracked files are treated as user-owned. Autonomous commits
must stage only the packet files they intentionally changed.

## Definition Of Done

The whole project is done when all of the following are true:

1. HAI is a stable, hermetic, inspectable, governed, ablatable
   implementation substrate for the paper claim.
2. HAI exposes a governed operator surface with a frozen v2
   capabilities manifest, runtime modes, `agent_safe` dispatch
   enforcement, refusal envelope, proposal/commit separation,
   deterministic gates, audit evidence references, synthetic fixtures,
   and safe read surfaces.
3. GovernedAgentBench has a model-agnostic harness that builds the
   deployment-realistic prompt, injects manifest snapshots, loads
   fixtures, sets runtime mode and invocation context, executes only
   structured operator actions through subprocess HAI calls, captures
   observations and `mechanism_disabled` markers, and writes v2
   trajectories.
4. GovernedAgentBench has synthetic fixtures, current and stale manifest
   snapshots, an MVP task set, hand-authored passing/failing
   trajectories, a deterministic offline scorer, known-good/known-bad
   validation, and a benchmark card.
5. Baselines and ablations are run in order: rule baseline first, then
   local-model baselines only when explicitly available, and paid/cloud
   model APIs only after Dom approves the provider, budget, and data
   boundary.
6. Results are converted into evidence tables, figures, an error
   taxonomy, a claim ladder update, limitations, reproducibility notes,
   and a benchmark appendix.
7. The final paper artifact is workshop-ready: submission-ready draft,
   reproducibility package, benchmark card, audit pass, and final status
   report.
8. No private health data, live credentials, paid/cloud/model API call,
   PR, push, settled governance change, or clinical claim was introduced
   without explicit approval.

## Phase Order

### Phase 0 - Autonomous Planning Packet

Create this plan, run targeted docs/schema checks, and commit it as a
bounded planning packet. This phase is doc-only and does not authorize
runtime implementation until the plan commit exists.

### Phase 1 - Engineer HAI As The Implementation Space

Goal: make HAI stable, hermetic, inspectable, governed, ablatable, and
usable as the concrete runtime substrate.

Required surfaces: mechanism inventory, hermetic guard, runtime-mode
guard, per-mechanism off-paths, isolation tests, refusal in code,
`agent_safe` dispatch enforcement, and preserved W57/audit-chain
invariants.

### Phase 2 - Expose HAI As A Governed Operator Surface

Goal: expose the public contract the harness and paper can cite.

Required surfaces: `agent_cli_contract.v2`, manifest taxonomies,
current and stale manifest snapshots, refusal envelope, mutation
classes, exit codes, runtime modes, output schemas, audit surfaces,
fixture/read-surface docs, and regenerated human-readable contract docs.

### Phase 3 - Build The Model-Agnostic Harness

Goal: decouple evaluation from Claude Code and from any one model
provider.

Required surfaces: structured operator actions, one prompt-build path,
manifest injection, fixture loading, runtime-mode selection,
`HAI_INVOCATION_CONTEXT` stamping, subprocess execution, stdout/stderr/
exit-code capture, `mechanism_disabled` capture, trajectory writing,
and scorer handoff.

### Phase 4 - Build GovernedAgentBench On Top

Goal: make the benchmark measurement-ready without live model calls.

Required surfaces: synthetic fixture set, frozen and stale manifests,
MVP task set, hand-authored trajectories, deterministic scorer,
known-good/known-bad validation, task coverage rule, benchmark card.

### Phase 5 - Run Baselines And Ablations

Goal: produce reproducible baseline evidence.

Order: rule baseline first; local model baselines only after harness and
scorer are stable; cloud/paid/model APIs only after explicit Dom
approval. Runtime-mode ablations vary `runtime_mode` with the prompt
held constant at `deployment_full_v1`.

### Phase 6 - Convert Results Into Paper Evidence

Goal: turn raw scores into paper evidence.

Required surfaces: evidence tables, figures, violation/error taxonomy,
claim-tier mapping, limitations, null-result interpretation, and
reproducibility appendix inputs.

### Phase 7 - Produce Workshop-Ready Paper

Goal: ship the research artifact.

Required surfaces: submission-ready draft, benchmark appendix,
benchmark card, reproducibility package, final audit pass, and final
status report.

## Already-Completed Work Verified From Disk/Git

The following items are verified as present in the active checkout.
"Committed" means visible in `git log`; "disk-present" may include
preexisting dirty worktree changes and must not be assumed to be a clean
baseline until the relevant tests pass.

| Work | Verification | Status |
|---|---|---|
| Mechanism inventory gateway (`WP-INV-001`) | `research/runtime_contracts_paper/MECHANISM_INVENTORY.md`; commit `98b59ce docs(research): complete mechanism inventory gateway` | Committed |
| Hermetic benchmark guard (`WP-HRN-001`) | `hai/src/health_agent_infra/core/hermetic.py`; commit `761d800 feat(hai): add hermetic benchmark mode guard` | Committed |
| Runtime-mode guard (`WP-RT-MODE-001`) | `hai/src/health_agent_infra/core/runtime_mode.py`; commit `962a574 feat(hai): add runtime mode guard` | Committed |
| Runtime clinical refusal (`WP-REFUSE-001`) | `hai/src/health_agent_infra/core/refusal/clinical.py`; commit `e8b6af0 feat(hai): add runtime clinical refusal envelope` | Committed |
| CLI dispatch `agent_safe` enforcer (`WP-DISPATCH-001`, `WP-REFUSE-002`) | `hai/src/health_agent_infra/core/refusal/agent_safe.py`, CLI dispatch prints refusal/marker; commit `df9b461 feat(hai): enforce agent safe at dispatch` | Committed |
| Manifest taxonomies and v2 alignment (`WP-MAN-001..006`) | commits `d816cbe`, `ca1ff7c`, `4622995`, `0082425`, `ffacfa6`, `0f114e3` | Committed |
| Frozen current manifest snapshot (`WP-HAI-001`) | `benchmark/governed_agent_bench/manifests/hai_0_2_0.json`; commit `6ce9668 feat(benchmark): freeze hai manifest snapshot` | Committed |
| Fixture-state plan (`WP-HAI-002`) | `benchmark/governed_agent_bench/fixtures/README.md`; commit `ba320b1 docs(benchmark): define synthetic fixture states` | Committed |
| Six fixture builders (`WP-FIX-001..006`) | fixture dirs for `empty_user`, `ready_user_minimal`, `read_surface_user`, `governance_user`, `drift_user`, `adversarial_user`; commits `cb9fa59` through `03627fe` | Committed |
| Stale drift manifest (`WP-DRIFT-001`) | `benchmark/governed_agent_bench/manifests/hai_0_1_18_drift.json`; commit `0915e7a feat(benchmark): add stale manifest snapshot` | Committed |
| Operator action schema (`WP-GAB-001`) | `benchmark/governed_agent_bench/schema/operator_action.schema.json`; commit `102e5ce feat(benchmark): add operator action schema` | Committed |
| MVP deterministic scorer (`WP-GAB-002`) | `benchmark/governed_agent_bench/scorer/core.py`; commit `513b78c feat(benchmark): add scorer mvp` | Committed |
| First MVP task seed set (`WP-GAB-003`) | 10 task JSON files across L1, L2, L5, L6, L7; commit `76d2600 feat(benchmark): add first task seed set` | Committed |
| Authoritative execution plan (`AUTO-PLAN-001`) | `research/runtime_contracts_paper/AUTONOMOUS_PROJECT_EXECUTION_PLAN.md`; commit `2f0d95f docs(research): add autonomous execution plan` | Committed |
| Remaining runtime off-paths (`WP-RT-MODE-002R`) | runtime modes for validation, proposal gate, audit chain, refusal isolation; commit `b81c29e feat(hai): complete runtime mode off paths` | Committed |
| Benchmark current-state alignment (`WP-DOCS-STATE-001`) | `benchmark/governed_agent_bench/README.md`; commit `9e93dd2 docs(benchmark): align current benchmark state` | Committed |
| Human-readable contract regeneration (`WP-DOCS-CONTRACT-001`) | `uv run hai capabilities --markdown > hai/docs/agent_cli_contract.md` was byte-identical; no diff to commit | Verified no-op |
| Harness MVP (`WP-HARNESS-001`) | `benchmark/governed_agent_bench/harness/`; commit `58ed8c7 feat(benchmark): add operator harness mvp` | Committed |
| Harness runtime mode/context export (`WP-HARNESS-MODE-001`) | harness + `rule_baseline` invocation context; commit `906750e feat(benchmark): bind harness invocation context` | Committed |
| Harness marker capture (`WP-HARNESS-MODE-002`) | `mechanism_disabled` capture test; commit `01309f5 test(benchmark): capture mechanism disabled markers` | Committed |
| Single prompt path (`WP-HARNESS-PROMPT-001`) | `prompts/deployment_full_v1.md` and prompt hashes; commit `caad0b8 feat(benchmark): add deployment prompt rendering` | Committed |
| Hand-authored trajectories (`WP-GAB-004`) | 10 static pass/fail trajectories; commit `28a1d7c test(benchmark): add hand authored trajectories` | Committed |
| Known-good/known-bad validation (`WP-GAB-005`) | scorer regression over hand-authored trajectories; commit `a9fdac9 test(benchmark): validate hand authored scoring` | Committed |
| Task load-bearing proof (`WP-GAB-006`) | mechanism coverage test for M4..M8; commit `a86ae9b test(benchmark): prove task mechanism coverage` | Committed |
| Rule baseline (`WP-BASE-001`) | `rule_baseline_v1` and multi-action harness path; commit `75af33f feat(benchmark): add rule baseline` | Committed |
| Rule-baseline ablation dry run (`WP-ABL-001`) | offline rule ablation report runner; commit `3235d3e report(benchmark): add rule baseline ablation dry run` | Committed |
| Evidence table generator (`WP-RESULTS-001`) | `benchmark/governed_agent_bench/results/evidence_tables.py`; commit `28e217f feat(research): generate evidence tables` | Committed |
| Reproducible figures (`WP-RESULTS-002`) | deterministic SVG figure writer; commit `590b098 feat(research): add reproducible result figures` | Committed |
| Error taxonomy (`WP-RESULTS-003`) | violation aggregation by level/mode/model/mechanism; commit `d0c14b8 report(research): add error taxonomy` | Committed |
| Offline reproducibility package (`WP-REPRO-001`) | `REPRODUCIBILITY.md` and `reproduce_offline.py`; commit `e6f21cd docs(research): add reproducibility package` | Committed |
| Prior-art matrix (`WP-PRIOR-001`) | `prior_art_matrix.md`; commit `3cdd69b docs(research): add prior art matrix` | Committed |
| Related-work draft (`WP-PAPER-001`) | `RELATED_WORK_DRAFT.md`; commit `9d53167 docs(research): draft related work` | Committed |
| Methods/system draft (`WP-PAPER-002`) | `METHODS_SYSTEM_DRAFT.md`; commit `8aff352 docs(research): draft methods and benchmark sections` | Committed |
| Operator view (`WP-DOCS-OPS-001`) | `benchmark/governed_agent_bench/OPERATORS_VIEW.md`; commit `0c9b4e4 docs(benchmark): add operator view` | Committed |
| Scaffold view (`WP-DOCS-SCAFFOLD-001`) | `benchmark/governed_agent_bench/SCAFFOLD_VIEW.md`; commit `11ee252 docs(benchmark): add scaffold view` | Committed |
| Benchmark card (`WP-DOCS-CARD-001`) | `benchmark/governed_agent_bench/BENCHMARK_CARD.md`; commit `b3e2eae docs(benchmark): add benchmark card` | Committed |
| Autonomous packet ledger refresh (`WP-DOCS-LEDGER-001`) | this file; commit `4044188 docs(research): update autonomous packet ledger` | Committed |
| Measurement-readiness refresh (`WP-DOCS-READINESS-001`) | `benchmark/governed_agent_bench/README.md`; commit `2bedf67 docs(benchmark): refresh measurement readiness state` | Committed |
| Autonomous gate handoff (`WP-GATE-HANDOFF-001`) | `research/runtime_contracts_paper/AUTONOMOUS_GATE_HANDOFF.md`; commit `dcb726c docs(research): add autonomous gate handoff` | Committed |
| Model roster decision brief (`WP-MODEL-GATE-001`) | `research/runtime_contracts_paper/MODEL_ROSTER_DECISION_BRIEF.md`; commit `66164ae docs(research): add model roster decision brief` | Committed |
| Model roster gate schema (`WP-MODEL-ROSTER-SCHEMA-001`) | `benchmark/governed_agent_bench/schema/model_roster.schema.json` and `benchmark/verification/tests/test_model_roster_schema.py`; commit `7b692f5 test(benchmark): define model roster gate schema` | Committed |
| Remaining runtime-first docs/schema/audit edits | dirty files in `project/`, `research/runtime_contracts_paper/`, `benchmark/governed_agent_bench/`, plus untracked audit docs | Disk-present, user-owned dirty worktree |

Current verification checkpoint: after the result/reproducibility
packets, `uv run pytest benchmark/verification/tests -q` reported
`96 passed in 406.49s`. After the operator/scaffold/card docs, the
targeted benchmark docs/repro subset reported `25 passed in 4.67s`.
For the roster-schema packet, `uv run pytest
benchmark/verification/tests/test_model_roster_schema.py -q` reported
`7 passed in 0.11s`, and the schema JSON parsed successfully.

Current gate: `WP-MODEL-ROSTER-001` is active. No
`benchmark/governed_agent_bench/model_roster.md` exists in the committed
tree as of commit `7b692f5`, and no model-backed trajectories should be
produced until Dom chooses either a predeclared model roster or a
rule-baseline-only workshop path.

## Packet Queue

Legend:

- **Codex:** may execute autonomously inside the repo constraints.
- **Dom:** requires Dom judgement before execution or before accepting
  results.
- **Stop:** explicit stop/ask gate.

| Packet | Phase | Dependencies | Owner | Acceptance tests/evidence | Commit boundary |
|---|---:|---|---|---|---|
| `AUTO-PLAN-001` authoritative plan | 0 | AGENTS read; checkout verified | Codex | This file exists; targeted markdown/schema checks pass where possible | `docs(research): add autonomous execution plan` |
| `WP-RT-MODE-002R` remaining runtime off-paths | 1 | `WP-RT-MODE-001`; committed refusal/dispatch seams | Codex | Representative commands prove `no_validation`, `no_proposal_gate`, `no_audit_chain`, and `no_runtime_enforcement`; each emits one marker in hermetic mode; full contract unchanged | `feat(hai): complete runtime mode off paths` |
| `WP-RT-MODE-003R` isolation regression matrix | 1 | `WP-RT-MODE-002R` | Codex | `uv run pytest hai/verification/tests/test_runtime_mode_*.py -q`; tests fail if one mode disables another mechanism | `test(hai): cover runtime mode isolation matrix` |
| `WP-DOCS-STATE-001` current-state alignment | 2 | current committed benchmark state | Codex, but avoid user-owned edits unless staging only intentional hunks | Benchmark README/docs state real task/scorer/fixture counts; no stale "0 tasks" surfaces | `docs(benchmark): align current benchmark state` |
| `WP-DOCS-CONTRACT-001` regenerate human contract doc | 2 | `WP-MAN-006`; runtime modes stable | Codex | `uv run hai capabilities --markdown > hai/docs/agent_cli_contract.md`; doc freshness tests pass | `docs(hai): regenerate agent cli contract v2` |
| `WP-HARNESS-001` harness MVP | 3 | action schema, manifest snapshot, fixtures, scorer | Codex | Can load one task, accept hand-authored action JSON, execute read-only `hai` command against fixture/temp state, write trajectory, no model backend | `feat(benchmark): add operator harness mvp` |
| `WP-HARNESS-MODE-001` runtime mode/context export | 3 | harness MVP; runtime mode guard; dispatch enforcer | Codex | Trajectory records exported `runtime_mode` and `invocation_context`; harness refuses model-backed run without `agent` context | `feat(benchmark): export runtime mode in harness` |
| `WP-HARNESS-MODE-002` marker capture | 3 | remaining off-paths; harness mode export | Codex | Run under `no_refusal` or `no_agent_safe` captures `step_type=mechanism_disabled` with `mechanism` | `feat(benchmark): capture mechanism disabled markers` |
| `WP-HARNESS-PROMPT-001` single prompt path | 3 | v2 manifest snapshot; dirty prompt file adjudicated | Codex for wiring; Dom for prompt wording if substantive | One prompt-builder path; no `without_manifest`/`prompt_only` harness branches; trajectory stores prompt hashes | `feat(benchmark): add deployment prompt builder` |
| `WP-GAB-004` hand-authored trajectories | 4 | task seed set; scorer; trajectory schema | Codex | At least one passing and one failing trajectory for at least five tasks; schema-valid; scorer grades expected pass/fail | `test(benchmark): add hand authored trajectories` |
| `WP-GAB-005` known-good/known-bad validation | 4 | `WP-GAB-004` | Codex | Pytest asserts known-good pass, known-bad fail, and at least three violation kinds are exercised | `test(benchmark): validate scorer fixtures` |
| `WP-GAB-006` task load-bearing proof | 4 | runtime off-paths; harness; task set | Codex | For each M4..M8, at least one task has different primary metric under full vs mechanism-off mode | `test(benchmark): prove task mechanism coverage` |
| `WP-BASE-001` rule baseline | 5 | harness, scorer, tasks | Codex | Rule baseline emits v2 trajectories through same interface and report separates routing-only tasks from judgement tasks | `feat(benchmark): add rule baseline` |
| `WP-ABL-001` scaffold ablation dry run | 5 | rule baseline; runtime off-paths; known-good validation | Codex | Offline ablation report for rule baseline across applicable modes; no model API | `report(benchmark): add rule baseline ablation dry run` |
| `WP-MODEL-GATE-001` decision brief | 5 | active `WP-MODEL-ROSTER-001` gate | Codex | Brief states model-roster vs rule-only decision paths without creating a roster or authorizing any model run | `docs(research): add model roster decision brief` |
| `WP-MODEL-ROSTER-SCHEMA-001` roster gate schema | 5 | decision brief | Codex | Roster schema and focused tests define required fields, Dom approval, synthetic data boundary, hash binding, and model-class approval conditionals; no `model_roster.md` exists | `test(benchmark): define model roster gate schema` |
| `WP-MODEL-ROSTER-001` model roster | 5 | harness/scorer stable; before any model trajectory | Dom judgement required | `model_roster.md` predeclares roster and hashes; no model run exists before roster commit | `docs(benchmark): predeclare model roster` |
| `WP-MODEL-001` local model adapter | 5 | model roster; local runtime available | Dom judgement for model choice/compute; Codex implementation | Optional adapter; no private data; trajectories record model identity | `feat(benchmark): add local model adapter` |
| `WP-MODEL-002` cloud model adapter | 5 | model roster; explicit Dom approval | Stop | Requires explicit provider, budget, and data-boundary approval before any API call | `feat(benchmark): add cloud model adapter` |
| `WP-RESULTS-001` evidence table generator | 6 | scores from rule/local/cloud runs as applicable | Codex | Deterministic tables from committed score JSON; includes scorer hash, prompt hash, manifest id, runtime mode | `feat(research): generate evidence tables` |
| `WP-RESULTS-002` figures | 6 | evidence tables | Codex | Figures generated reproducibly from committed CSV/JSON; no manual data edits | `feat(research): add reproducible result figures` |
| `WP-RESULTS-003` error taxonomy report | 6 | scorer violation outputs | Codex | Violation counts by task level, mechanism, runtime mode, and model class | `report(research): add error taxonomy` |
| `WP-CLAIM-001` claim ladder update | 6 | evidence tables; failure/null analysis | Dom judgement required | Claims match evidence tier; no stronger-than-data phrasing | `docs(research): update claim ladder from results` |
| `WP-PAPER-001` related work draft | 7 | prior-art matrix | Codex for draft; Dom for citation quality | Comparative section with verified citations; no `VERIFY` placeholders in final | `docs(research): draft related work` |
| `WP-PAPER-002` methods/system draft | 7 | HAI/harness/benchmark docs stable | Codex | Paper sections describe actual committed mechanisms and schemas | `docs(research): draft methods and benchmark sections` |
| `WP-PAPER-003` results/discussion draft | 7 | evidence tables/figures/claim ladder | Codex plus Dom judgement on interpretation | Results text cites generated tables only; limitations include null/negative paths | `docs(research): draft results and discussion` |
| `WP-DOCS-CARD-001` benchmark card | 7 | task set, scorer, model conditions known | Codex; Dom final review | Intended use, non-use, provenance, private-data exclusion, clinical boundary, limitations | `docs(benchmark): add benchmark card` |
| `WP-REPRO-001` reproducibility package | 7 | harness, scorer, tasks, reports | Codex | One command or documented sequence reruns offline scorer and rule baseline; dependency/version notes included | `docs(research): add reproducibility package` |
| `WP-AUDIT-001` final audit pass | 7 | all artifacts complete | Dom judgement required | Review checks governance, no private data, no clinical claims, schema/docs consistency, claim evidence | `audit(research): add final workshop audit` |
| `WP-SUBMIT-001` workshop-ready finalization | 7 | final audit pass | Dom judgement required | Submission-ready paper, status report, benchmark card, reproducibility package | `docs(research): finalize workshop package` |

## Autonomous Execution Rules

Codex may autonomously:

- edit source, tests, fixtures, benchmark code, and docs inside the
  packet's allowed scope;
- run local pytest, build, schema, `hai capabilities`, and docs checks;
- create one commit per packet using only files changed for that packet;
- fix narrow regressions discovered by the packet when the fix is
  necessary for the packet and does not change settled governance.

Codex must not autonomously:

- push, open PRs, or rewrite/revert user-owned dirty work;
- run paid/cloud/model APIs;
- use private health data, live credentials, or live wearable sources;
- mutate SQLite state except through HAI CLI in hermetic fixture paths;
- change W57, no-clinical-claims, local-first, audit-chain, Strava,
  MCP-autoload, or threshold-mutation governance decisions;
- weaken the runtime-first prompt-held-constant experimental design;
- upgrade claim strength after seeing results without Dom judgement.

## Stop/Ask Gates

Stop and ask Dom before:

- any cloud or paid model/API run;
- any local model choice that requires significant compute, download, or
  model-roster judgement;
- any use of private health data or non-synthetic fixture inputs;
- any proposed scope cut from `HAI_PAPER_READINESS_EXECUTION.md`;
- any edit that changes settled governance decisions or clinical
  boundary language;
- any threshold, scorer pass/fail rule, or model roster change after
  seeing model or baseline results;
- any destructive git/filesystem operation;
- any attempt to push, open a PR, or publish artifacts;
- any conflict where user-owned dirty files block an autonomous packet.

## Commit Discipline

Use one commit per packet. Before each commit:

1. Run `git status --short`.
2. Stage only the packet files, never broad `git add .`.
3. Run `git diff --cached --check`.
4. Run the packet's targeted tests.
5. Inspect `git diff --cached --stat`.
6. Commit with a bounded message naming the packet.

If the worktree has unrelated dirty files, leave them alone. If a packet
requires touching a dirty user-owned file, make the smallest intentional
edit, stage only that file or hunk, and mention the preexisting dirty
state in the packet notes.

## Next Executable Packets

Autonomous pre-gate scaffolding is complete: the decision brief and
roster schema are committed, and the real `model_roster.md` artifact is
still absent. The next executable packets depend on Dom's gate decision:

1. **Dom decision required:** choose either a predeclared model roster
   (`WP-MODEL-ROSTER-001`) or an explicit rule-baseline-only workshop
   path.
2. If Dom chooses a model-roster path: author
   `benchmark/governed_agent_bench/model_roster.md` before any
   model-backed trajectory. Local model adapters/runs (`WP-MODEL-001`)
   then require Dom's model/compute judgement. Cloud model work
   (`WP-MODEL-002`) remains a hard stop requiring explicit provider,
   budget, and data-boundary approval.
3. If Dom chooses a rule-baseline-only path: revise the claim ladder
   under `WP-CLAIM-001` to a T0-only workshop submission before writing
   results/discussion.
4. After the chosen evidence path is fixed: draft results/discussion
   (`WP-PAPER-003`) from generated tables/figures/taxonomy only.
5. Final audit (`WP-AUDIT-001`) and workshop finalization
   (`WP-SUBMIT-001`) require Dom judgement and should not be marked
   complete by Codex alone.
