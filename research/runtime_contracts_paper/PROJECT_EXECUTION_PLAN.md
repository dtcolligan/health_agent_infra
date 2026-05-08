# Project Execution Plan

**Status:** Master research-engineering execution plan, 2026-05-08.

This is the controlling plan for moving from the post-reframe repository
to a paper + benchmark + reference-runtime release. It does not implement
anything. Its purpose is to make future implementation work decomposable
into bounded slices that coding agents can execute without making
strategic decisions.

For project framing, read `PROJECT_FRAME.md`, `PROJECT_DECISIONS.md`,
and `PROJECT_OPERATING_MODEL.md` first. For the paper frame, read
`PAPER_FRAME.md`. The older `IMPLEMENTATION_PLAN.md` is retained as the
coarse phase plan; this file is the more operational master plan.

## Objective

Produce a conservative research-engineering artifact set:

1. A paper testing runtime contracts for bounded agents over sensitive
   user-owned data.
2. GovernedAgentBench as the benchmark artifact.
3. HAI as the first reference runtime.
4. Reproducible baselines, scaffold ablations, and optional fine-tuned
   local operators.

The project is not trying to build a Google Health competitor. HAI is the
demonstrator used to make the runtime-contract claim testable.

## Non-Negotiables

- No private health rows in benchmark fixtures, training data, reports,
  or public artifacts.
- No diagnosis, treatment, prescribing, or autonomous medical decisions.
- No benchmark dependence on Claude Code as the operator.
- No MCP dependency for the first benchmark/paper slice.
- No model-run experiments before a deterministic offline scorer exists.
- No HAI product polish unless it stabilizes the contract, benchmark, or
  reproducibility.
- No post-hoc safety thresholds chosen after seeing model results.

## Artifact Dependency Graph

```text
PROJECT_FRAME / PROJECT_DECISIONS
        |
        v
PAPER_FRAME + CLAIM_LADDER + PRIOR_ART_POSITIONING
        |
        v
RUNTIME_CONTRACT_FREEZE_PLAN
        |
        v
BENCHMARK_SPEC + OPERATOR_HARNESS_SPEC + SCORING_SPEC
        |
        v
TASK_AUTHORING_GUIDE + frozen manifest + pilot tasks
        |
        v
offline scorer + hand-authored trajectories
        |
        v
rule baseline + model adapters
        |
        v
baselines + scaffold ablations + fine-tuning
        |
        v
paper results + benchmark card + reproducibility appendix
```

## Milestones

### M0 — Planning Gate

**Purpose.** Make the execution plan explicit enough that future agents
can implement bounded work packets.

**Exit criteria.**

- `PROJECT_EXECUTION_PLAN.md` defines phases, gates, and dependencies.
- `CLAIM_LADDER.md` defines minimum, strong, best-case, and null-result
  claims.
- `PRIOR_ART_POSITIONING.md` defines the positioning work to complete
  before paper writing.
- `BENCHMARK_SPEC.md`, `OPERATOR_HARNESS_SPEC.md`, `SCORING_SPEC.md`,
  and `TASK_AUTHORING_GUIDE.md` define GovernedAgentBench.
- `RUNTIME_CONTRACT_FREEZE_PLAN.md` defines the paper-critical HAI
  contract slice.
- `BASELINES_AND_ABLATIONS_PLAN.md` defines systems and ablations.
- `WORK_PACKETS.md` contains agent-executable tasks with file scopes,
  dependencies, acceptance criteria, tests, and non-goals.

**Implementation allowed.** Documentation/specification only.

### M1 — Contract Freeze

**Purpose.** Freeze the HAI contract subset that the benchmark will use.

**Exit criteria.**

- A frozen `hai capabilities --json` snapshot exists under
  `benchmarks/governed_agent_bench/manifests/`.
- The snapshot is generated from the source tree and has a documented
  provenance command.
- The benchmark subset of command behavior is documented:
  command name, args, `agent_safe`, mutation class, expected outputs,
  exit-code semantics, and audit surface.
- Synthetic fixture-state requirements are specified without private
  health data.
- Any HAI runtime gap discovered during freeze is either fixed through a
  separate bounded work packet or explicitly deferred as non-critical.

**Implementation allowed.** Contract snapshotting, fixture planning,
doc updates, narrow runtime fixes only if they are required for the
benchmark subset.

### M2 — Benchmark Vertical Slice

**Purpose.** Prove that GovernedAgentBench can score model-agnostic
trajectories without any live model backend.

**Exit criteria.**

- At least one task each exists for L1, L2, L5, L6, and L7.
- Each task validates against `task.schema.json`.
- At least one passing and one failing hand-authored trajectory exist.
- The scorer can grade those trajectories offline.
- The score output validates against `score.schema.json`.
- The benchmark README reports real counts instead of scaffold-only
  state.

**Implementation allowed.** Benchmark tasks, fixtures, scorer, and
trajectory files. No model APIs yet.

### M3 — Baseline Harness

**Purpose.** Run comparable non-learning baselines and establish that the
benchmark measures more than trivial routing.

**Exit criteria.**

- Rule baseline runs through the same trajectory/scoring interface.
- Prompt-only and manifest/contract prompt templates are specified.
- Local and cloud model adapters share the same model-output action
  schema.
- Outputs are recorded as trajectories before scoring.
- The first baseline report distinguishes deterministic routing tasks
  from tasks requiring model judgment.

**Implementation allowed.** Model adapter interfaces, rule baseline,
prompt templates, run logs. Avoid expensive experiments until M2 is
stable.

### M4 — Experiment Set

**Purpose.** Produce the empirical evidence for the paper.

**Exit criteria.**

- Rule, local prompt-only, local+contract, cloud prompt-only,
  cloud+contract, and at least one scaffold ablation are run on the same
  task set.
- Thresholds are fixed before interpreting outcomes.
- Failures are categorized by the agreed violation taxonomy.
- Results can support at least the minimum claim in `CLAIM_LADDER.md`,
  or the paper narrows to a null/negative result.

**Implementation allowed.** Baseline runs, ablation prompt/context
variants, reports.

### M5 — Fine-Tuning

**Purpose.** Test whether a small local operator can learn benchmark
behavior without memorizing stale contract details.

**Exit criteria.**

- Training data contains no private health rows or clinical advice
  corpus.
- Fine-tuned local is evaluated with and without live/frozen manifest
  access.
- Drift robustness is measured against at least one changed contract
  condition.
- Model card documents data provenance and limitations.

**Implementation allowed.** Dataset generation, LoRA/QLoRA recipe, model
card, reproducible evaluation.

### M6 — Paper and Release

**Purpose.** Package the work as a research-engineering artifact.

**Exit criteria.**

- Paper draft includes prior-art positioning, methods, benchmark,
  results, limitations, and reproducibility appendix.
- GovernedAgentBench has a benchmark card.
- Public fixtures, frozen manifests, scorer, and reports are committed.
- Claims match results. Weak or null results are reported without
  inflation.

## Decision Gates

| Gate | Question | Default decision |
|---|---|---|
| G1 | Is the benchmark still HAI-specific after task authoring? | Generalize task schema and language before adding model runs. |
| G2 | Does a task require private health rows? | Redesign the task. |
| G3 | Does a task require clinical interpretation? | Remove or reframe it. |
| G4 | Do rule baselines solve most tasks? | Narrow claim toward which tasks require model judgment. |
| G5 | Does cloud+contract dominate all local conditions? | Focus on safety/privacy/cost tradeoffs, not local parity. |
| G6 | Do ablations fail to explain full-contract gains? | Narrow the architecture claim; do not assert component causality. |
| G7 | Does fine-tuning memorize stale commands? | Require manifest-grounded evaluation and drift tests. |

## Scope Control

Work is in scope when it directly advances one of:

- contract freeze;
- benchmark MVP;
- scorer;
- operator harness;
- baselines;
- scaffold ablations;
- fine-tuning;
- paper/release packaging.

Work is out of scope before M6 when it is primarily:

- HAI consumer-product polish;
- MCP transport work not required by the benchmark;
- extra wearable integrations;
- more health-domain breadth;
- N-of-1 product surfaces;
- hosted app work.

## Agent Execution Rule

Future coding agents should not receive broad prompts like "build the
benchmark." They should receive a single work packet from
`WORK_PACKETS.md`, including allowed files, forbidden files,
dependencies, acceptance criteria, tests, and non-goals.
