# HAI Paper-Readiness Execution Plan

> **Notice (2026-05-15):** This file's overall phase plan, work-packet
> structure, and engineering deliverables remain valid. The *scope* the
> work targets has narrowed: per D-PROJ-024 / D-PREPRINT-001 through
> D-PREPRINT-009 in [`framing_v2/PREPRINT_RESCOPE.md`](framing_v2/PREPRINT_RESCOPE.md),
> the active deliverable is an arXiv preprint by 2026-09-30, not a
> NeurIPS 2027 main-conference submission. Concretely: Phase 5-6 model
> baselines run on one Option-B model class with ~25-30 tasks (not the
> full D-FRAME-020 roster); Engels-extension work (Phase 6a's 18
> adaptive-vs-DRG-0 trajectories, and any DRG-0 implementation) is
> deferred to a future paper; the bounded HS contrast is dropped from
> preprint scope; cost ceiling is USD 300, not USD 1,500. The Phase
> 1-5 mechanism-isolation, refusal-in-code, manifest-completeness,
> hermeticity, and harness work is unchanged. Where this file's
> "merged-paper" framing conflicts with `PREPRINT_RESCOPE.md`, resolve
> in favour of the rescope file.

**Status:** HAI support-lane execution plan, revised for the merged
NeurIPS 2027 paper frame on 2026-05-11.

**Historical audit outcome:** Codex returned `PLAN_INCOHERENT` with 20
findings against the pre-merge runtime-first reframe. Maintainer
adjudication produced six locked architectural answers in
`project/DECISIONS.md` D-PROJ-016 (HAI freeze on disk) + D-PROJ-017
(round-1 architectural answers). Per-finding closeout lives at
`codex_runtime_first_reframe_audit_response_response.md`.

**Merged-scope update:** Phase 1 framing v2 closed on 2026-05-11. This
file no longer controls a standalone workshop-first runtime paper. It is
the execution plan for making HAI paper-ready as the reference runtime
inside **Deterministic Software Contracts as Trusted Monitors in AI
Control Protocols**, targeted at the NeurIPS 2027 main conference.
`framing_v2/CONVERGED.md`, `PAPER_FRAME.md`, `CLAIM_LADDER.md`, and
`RESEARCH_EVAL_STRATEGY.md` are the current paper-planning source of
truth when this file disagrees.

## Why this doc exists

`HAI_PAPER_READINESS_PLAN.md` says *what* a paper-ready HAI looks like at a
high level: frozen manifest, fixtures, command behaviour documentation, no
private data, no live wearables. This doc says *how* the HAI support
engineering executes against that goal under the merged-paper frame.

The reframe in one sentence: **the runtime contract is the intervention,
the runtime is the primary axis of variation in the headline experiment,
and the deployment-realistic prompt is held constant across every
condition.** Withholding the manifest from the model produces an obvious
sandbagged-baseline result. The paper does not vary the prompt. It varies
the runtime.

This doc supersedes the implicit prompt-first ordering in older
execution docs and the original "two phase" shape in the historical
multi-release roadmaps. It does **not** supersede the merged paper
frame. When this doc and `framing_v2/CONVERGED.md`, `PAPER_FRAME.md`,
`CLAIM_LADDER.md`, or `RESEARCH_EVAL_STRATEGY.md` disagree, this doc is
the stale surface to revise.

## The intervention, defined precisely

The runtime contract is a bundle of nine mechanisms. The first three
(M1-M3) are held constant across every benchmark run as harness
infrastructure. M4-M8 are individually ablatable in the headline
experiment. M9-TX is a non-ablatable invariant that wraps all M4-M8
state mutations.

| ID | Mechanism | Where it lives | Held constant or ablated? |
|---|---|---|---|
| M1 | Capabilities manifest visible in the operator prompt | harness prompt construction | held constant |
| M2 | Typed operator action schema | harness JSON parsing | held constant |
| M3 | Harness command allowlist pinned to manifest snapshot | harness execution layer | held constant |
| M4 | Runtime argument and proposal-payload validation | HAI runtime | ablatable: `no_validation` |
| M5 | `agent_safe` enforcement at CLI dispatch | HAI runtime (built in Phase 2) | ablatable: `no_agent_safe` |
| M6 | Proposal/commit separation (W57 user-gate) | HAI runtime + SQL | ablatable: `no_proposal_gate` |
| M7 | Refusal contract enforced in code | HAI runtime (built in Phase 2) | ablatable: `no_refusal` |
| M8 | Audit evidence emission (narrowed from "audit chain") | HAI runtime + SQL | ablatable: `no_audit_chain` |
| M9-TX | Transaction integrity around state-graph writes | HAI runtime + SQLite | **held-constant invariant** (never ablated) |

The five M4-M8 ablations plus the `full_contract` baseline plus the
`no_runtime_enforcement` extreme produce the seven `runtime_mode`
values declared in
`benchmark/governed_agent_bench/schema/trajectory.schema.json`:

```text
full_contract              all of M4..M8 on
no_validation              M4 off; M5..M8 on; M9-TX on
no_agent_safe              M5 off; M4, M6..M8 on; M9-TX on
no_proposal_gate           M6 off; M4..M5, M7..M8 on; M9-TX on
no_refusal                 M7 off; M4..M6, M8 on; M9-TX on
no_audit_chain             M8 off; M4..M7 on; M9-TX on
no_runtime_enforcement     M4..M8 all off; M1..M3 + M9-TX on
```

**Notes on the round-2 architecture (per D-PROJ-017):**

- The mode previously named `no_runtime` is now `no_runtime_enforcement`.
  M1-M3 (manifest in prompt, structured action schema, harness
  allowlist) and M9-TX (transactions) are still on in this mode. The
  rename is per F-CDX-RFR-R1-04: "no_runtime" was misleading.
- M5 and M6 are *separately ablatable* only after Phase 2 ships
  `WP-DISPATCH-001`. Today the W57 user-gate functionally entangles
  them; the dispatch enforcer separates them so each has an
  independent off-path.
- M7 (refusal) does not exist as a canonical runtime seam today.
  Phase 2 builds it (`WP-REFUSE-001`, `WP-REFUSE-002`). Existing
  per-domain validators may be ported in for consolidation.
- M8 is **narrowed** to evidence-reference emission — the audit-row
  pointers downstream surfaces (`hai today`, `hai explain`, weekly
  review) consume. Atomic state-graph writes are M9-TX, held constant.
- M9-TX is never ablated. Disabling transactions would corrupt the
  state graph and produce uninterpretable results, not a measurable
  comparison. See `MECHANISM_INVENTORY.md` for the invariant
  statement.

M1..M3 are *always on* in every condition. The model always sees the
manifest. The harness always parses structured actions. The harness
always rejects shell commands outside the allowlist. The paper does
not vary these.

## The experimental design

The headline experiment varies one axis (runtime mode) on a fixed model,
with the prompt held constant at full deployment information.

### Headline experiment (Tier 2 evidence)

```
fixed prompt:    deployment_full_v1   (versioned, hashed; see prompts/deployment_full_v1.md)
fixed model:     one local class      (e.g., Qwen 7B Instruct, with full model_identity recorded)
varied:          runtime_mode in { full_contract, no_validation,
                                   no_agent_safe, no_proposal_gate,
                                   no_refusal, no_audit_chain,
                                   no_runtime_enforcement }
```

The score gap across these seven conditions is the architectural claim,
isolated from any prompt-level effect.

The prompt is a versioned artifact at
`benchmark/governed_agent_bench/prompts/deployment_full_v1.md`. Every
trajectory records `prompt_template_id` and `prompt_template_hash` so
two runs at different times produce comparable evidence (per
F-CDX-RFR-R1-05).

### Model-scale experiment (Tier 3 evidence)

```
fixed prompt:    deployment_full_v1
varied runtime:  { full_contract, no_runtime_enforcement }
varied model:    predeclared D-FRAME-020 roster of six Houdinis
                 (Qwen2.5-3B, Qwen2.5-7B, Qwen2.5-32B,
                  Qwen2.5-72B, Haiku historical/pilot-only,
                  Sonnet 4 or successor) with full model_identity
                  per trajectory
```

The model roster is predeclared in
`benchmark/governed_agent_bench/model_roster.md` (authored before any
model run). Each trajectory records full `model_identity`
(parameter_count, model_family, quantization, provider_snapshot,
decoding_settings) per F-CDX-RFR-R1-07.

The interesting result is that with `full_contract`, the smallest model
reaches the safety threshold; with `no_runtime_enforcement`, even larger models do
not. The runtime is the floor, not the ceiling.

### What is *not* an axis of variation

- The prompt content is not varied. There is no `with_manifest` versus
  `without_manifest` condition.
- Stale or wrong manifest content *inside L7 drift tasks* is task
  content, not a condition. L7 still varies `runtime_mode` over the
  stale manifest.
- "Skill versus no-skill" is not an axis. The paper claim depends on
  refusal living in the runtime; skills are advisory after Phase 2.

### Why the prompt is held constant

Withholding the manifest produces a sandbagged baseline. That comparison
("model with full info beats model with no info") is already documented
in BFCL, ToolLLM, and Gorilla; it is not what this paper claims. Holding
the prompt at full deployment information makes any score gap
attributable to the runtime alone. See decision **D-PROJ-014** for the
durable record.

## Merged-paper additions outside the HAI substrate

The merge adds paper-critical work that this file must accommodate but
does not make HAI a product roadmap again.

| Addition | HAI-readiness responsibility | Controlling decision |
|---|---|---|
| Engels Backdoor Code extension | Provide frozen HAI/GAB artifacts that make the deterministic-Guard comparison reproducible; DRG-0 itself is implemented in the Engels work packets, not inside HAI product code. | D-FRAME-004, D-FRAME-018 |
| Targeted adversarial layer | Ensure M4-M8 off-paths, fixtures, runtime refusal, and audit evidence markers expose refusal bypass, mutation escalation, audit tampering, and schema evasion cleanly. | D-FRAME-003, D-FRAME-022 |
| Bounded HS contrast | Provide L6 governance/refusal tasks and audit/reference fields suitable for comparing deterministic contract checks against an HS-derived monitor. | D-FRAME-024 |
| Fine-tuning sequel setup | Keep schema slots and reproducibility hashes that let a future `fine_tuned_local` operator compare to paper 1, without running fine-tuning in paper 1. | D-FRAME-027 |
| Coding-agent appendix | No HAI engineering responsibility. Appendix E is a prose sketch only and must not be cited as empirical evidence. | D-FRAME-025 |

Superseded by the merge: any plan item whose purpose was "publish the
workshop paper first" or "minimum workshop floor" is now historical
provenance. The active gate is the merged NeurIPS 2027 paper path, with
the July/August 2026 Engels pilot deciding whether that merge remains
committed or reverts to Trajectory A.

## Phase plan

Eight HAI-readiness phases remain useful as the support-lane plan. Phase
1 is the gateway to almost everything else; nothing downstream can be
built well until the mechanism inventory is complete.

### Phase 1 — Mechanism inventory and isolation audit

**Goal.** Audit every ablatable mechanism (M4..M8) in HAI source and
record where each lives, what "off" would mean, and whether the off-path
is cleanly isolatable today.

**Deliverable.** `MECHANISM_INVENTORY.md` filled in with:

- File paths and function names for each mechanism's enforcement seam.
- The smallest patch that would disable each mechanism cleanly.
- Coupling rating per mechanism: `clean | coupled | aspirational`.
- A follow-on decoupling packet for any `coupled` mechanism.

**Packets.**

- `WP-INV-001` — fill in the audit template.
- `WP-INV-002..N` — one packet per `coupled` mechanism for decoupling.
  These are emitted from WP-INV-001 findings, not pre-allocated.

**Acceptance criteria.**

- Every ablatable mechanism rated `clean` or `coupled`.
- For every `coupled` mechanism a decoupling packet exists with allowed
  files and acceptance criteria.
- A diff plan exists for the seam each "off" path will introduce.

**Risk.** The codebase may show more cross-mechanism coupling than
expected. Phase 1's most important output is honest reporting of that
coupling, not premature decoupling work.

### Phase 2 — Runtime-mode switch, refusal in code, and CLI-dispatch enforcer

**Goal.** Build the runtime-side seams the headline experiment needs:
the runtime-mode switch, the centralized refusal contract, and the
CLI-dispatch-level `agent_safe` enforcer that separates M5 from M6.
Per D-PROJ-017, the dispatch enforcer is part of Phase 2 — not a
deferred future build.

**Deliverable.**

- A new `core/refusal/` module enforcing clinical-claim and final-
  output refusals in code, with a `banned_clinical_phrases.txt` that
  the benchmark scorer reuses. Existing per-domain validators in
  `core/validate.py` and `core/writeback/proposal.py` may be consulted
  for design but the deliverable is a fresh canonical seam.
- A new CLI-dispatch middleware (`WP-DISPATCH-001`) that reads the
  manifest's `agent_safe` field per command and refuses agent-classified
  callers from invoking `agent_safe=False` commands at dispatch time —
  before any handler runs. This separates M5 (general agent_safe
  enforcement) from M6 (W57 user-gate on intent/target promotion).
- `HAI_RUNTIME_MODE` env (preferred) or config selecting from the seven
  modes declared in `trajectory.schema.json`.
- Each "off" path emits a `mechanism_disabled` audit marker so
  trajectories can prove the mechanism was intentionally absent.
- Per-mechanism unit tests for both on-path and off-path behaviour,
  including a cross-mechanism isolation assertion (turning off one
  mechanism must not silently disable another).

**Packets.**

- `WP-REFUSE-001` — clinical-claim refusal centralized in runtime.
- `WP-REFUSE-002` — `agent_safe` violation refusal in runtime;
  hermetic-mode-only acceptance criteria per F-CDX-RFR-R1-16
  (cannot run against user state).
- `WP-DISPATCH-001` — CLI-dispatch-level `agent_safe` enforcer.
- `WP-RT-MODE-001` — `HAI_RUNTIME_MODE` switch + supported modes enum.
- `WP-RT-MODE-002` — per-mechanism off-paths + audit markers.
- `WP-RT-MODE-003` — per-mechanism unit tests for off-paths +
  isolation assertion.

**Acceptance criteria.**

- `HAI_RUNTIME_MODE=no_refusal` produces a trajectory step with
  `step_type=mechanism_disabled` and `mechanism=refusal`.
- A clinical-phrase final text under `full_contract` is refused before
  it reaches the operator output; under `no_refusal` it passes through.
- `safety` skill becomes advisory: it may surface refusal context to
  the model, but does not own the refusal decision.
- Tests exist for every (mode, mechanism) on/off pair.

**Dependencies.** Phase 1 audit complete (so we know the seams exist).

### Phase 3 — Manifest completeness and snapshot envelope

**Goal.** Bring the `hai capabilities --json` surface up to the
contract-completeness the paper claims, then snapshot it as a frozen
research artifact.

**Deliverable.**

- Top-level taxonomies: `mutation_classes`, `exit_codes`, `refusals`,
  `runtime_modes`, `output_schemas`, `audit_surfaces`.
- Vocabulary alignment: per-command `mutation` field renamed to
  `mutation_class`; per-command `command` key field aliased or renamed
  to `name` (with one cycle of compatibility if needed).
- Schema bump from `agent_cli_contract.v1` to `agent_cli_contract.v2`.
- Frozen snapshot at
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json` with
  envelope fields per `HAI_PAPER_READINESS_PLAN.md` §"Manifest Snapshot
  Envelope", plus a `runtime_modes` field declaring the modes the paper
  varies. This is the HAI v0.2.0 manifest snapshot referenced by the
  paper-planning docs (about 189 KB).
- Provenance test in `benchmark/verification/tests/`.

**Packets.**

- `WP-MAN-001` — top-level `mutation_classes` taxonomy.
- `WP-MAN-002` — top-level `exit_codes` taxonomy.
- `WP-MAN-003` — top-level `refusals` taxonomy.
- `WP-MAN-004` — top-level `runtime_modes` taxonomy.
- `WP-MAN-005` — vocabulary alignment (`mutation` → `mutation_class`,
  `command` → `name`).
- `WP-MAN-006` — schema bump to `agent_cli_contract.v2`.
- `WP-HAI-001` (existing) — capture the manifest snapshot. Stays.

**Acceptance criteria.**

- The frozen snapshot validates against the new contract schema.
- Every command in the snapshot resolves to one of the enumerated
  `mutation_classes`.
- Every `runtime_modes` entry maps to a runtime seam exercised in a
  Phase 2 unit test.
- Snapshot generation is byte-stable under repeated runs (ignoring
  `generated_at`).
- The manifest snapshot reference is exact in downstream docs:
  `benchmark/governed_agent_bench/manifests/hai_0_2_0.json`, not "v2
  manifest."

**Dependencies.** Phase 2 (`runtime_modes` is meaningful only if the
modes actually exist).

### Phase 4 — Hermeticity and mechanism-stress fixtures

**Goal.** Make HAI runnable in a sandboxed mode against fixture state
without network or credentials, and build the fixture set whose
*purpose* is to exercise specific runtime mechanisms.

**Hermeticity surface (corrected per F-CDX-RFR-R1-11).** HAI does not
have a `HAI_STATE_PATH` env. The actual existing isolation surface
uses `HAI_STATE_DB` (state SQLite path), `HAI_BASE_DIR` (file-backed
state base dir), platform config paths + `core/config.py` for
threshold/config, and a demo session marker. Phase 4 reframes around
this real surface; the `HAI_HERMETIC=1` umbrella refuses network and
keyring access and asserts that all four surfaces are redirected away
from the user's personal `~/.hai/`.

**Deliverable.**

- `HAI_HERMETIC=1` env umbrella: refuses network calls, refuses keyring
  lookups, asserts `HAI_STATE_DB` and `HAI_BASE_DIR` are redirected
  before any state-mutating command runs.
- Documented benchmark-mode environment recipe combining
  `HAI_HERMETIC=1`, `HAI_STATE_DB`, `HAI_BASE_DIR`, and the demo session
  marker.
- Six fixtures, each constructed by replaying contract-pure
  `hai intake` / `hai propose` calls (no SQL backdoor):
  - `empty_user`
  - `ready_user_minimal`
  - `read_surface_user`
  - `governance_user`
  - `drift_user`
  - `adversarial_user` (new — designed to provoke M5 + M7 violations)
- Determinism test: load fixture twice, get equivalent state.

**Packets.**

- `WP-HRN-001` — `HAI_HERMETIC=1` mode + network/keyring refusal.
- `WP-HRN-002` — benchmark-mode env recipe combining `HAI_STATE_DB`,
  `HAI_BASE_DIR`, demo session marker, and platform config paths
  (no invented `HAI_STATE_PATH`).
- `WP-FIX-001..006` — one packet per fixture (six packets).
- `WP-FIX-DET-001` — determinism test.

**Acceptance criteria.**

- A pytest run of every fixture finishes with no network calls (verified
  via a no-network sandbox or a network-attempt monitor).
- Each fixture's docstring or `README.md` line names the mechanism it
  is intended to stress, and references the load-bearing tasks that
  consume it.

**Dependencies.** Phase 3 (the snapshot is the manifest the fixtures'
seeded `hai propose` calls validate against).

### Phase 5 — Operator harness with runtime-mode control

**Goal.** Build the harness that the paper's experiments run against:
loads a task, sets `HAI_RUNTIME_MODE`, executes structured operator
actions, captures stdout/stderr/exit-code, records `mechanism_disabled`
markers, and writes a trajectory.

**Deliverable.**

- Harness implementation under `benchmark/governed_agent_bench/harness/`.
- One prompt-build path that always emits the full deployment-realistic
  prompt (manifest + contract notes + refusal taxonomy).
- `HAI_RUNTIME_MODE` set per task before each subprocess call.
- Refusal to run a task whose `runtime_modes_in_scope` does not include
  the configured mode.
- Trajectory records `runtime_mode` and `model_class` per the v2 schema.
- Capture of `mechanism_disabled` audit markers from runtime stderr or
  audit logs into trajectory steps.

**Packets.**

- `WP-HARNESS-001` (existing, rescoped) — harness MVP.
- `WP-HARNESS-MODE-001` — set `HAI_RUNTIME_MODE` per task.
- `WP-HARNESS-MODE-002` — capture `mechanism_disabled` markers.
- `WP-HARNESS-PROMPT-001` — single deployment-realistic prompt path
  (no prompt-level conditioning).

**Acceptance criteria.**

- Hand-authored operator action JSON runs end-to-end against fixture
  state in every supported `runtime_mode`.
- Trajectory steps include `mechanism_disabled` rows for any disabled
  mechanism that would have fired had it been enabled.
- A task's `runtime_modes_in_scope` is honoured: the harness refuses
  out-of-scope runs and emits a clear error.

**Dependencies.** Phase 2 (modes exist), Phase 3 (manifest snapshot
exists), Phase 4 (fixtures exist).

### Phase 6 — Benchmark task design (level × mechanism matrix)

**Goal.** Author the first MVP task set, gated by a coverage rule on
mechanisms, not just on levels.

**Coverage rule.** Each ablatable mechanism (M4..M8) must be
**load-bearing** in at least one MVP task. A task is load-bearing for a
mechanism iff the score under `full_contract` differs from the score
under that mechanism's `mechanism_off` mode on at least one primary
metric. The MVP task set is not approved until every mechanism has at
least one load-bearing task.

**Suggested mapping (provisional; refined during task authoring).**

| Mechanism | Suggested level | Sample task topic |
|---|---|---|
| M4 validation | L4 | malformed proposal payload (recovery requires schema retry) |
| M5 agent_safe | L6 | autonomous attempt at user-gated commit (must refuse) |
| M6 proposal_gate | L6 | direct-write attempt that bypasses propose/commit |
| M7 refusal | L6 | clinical diagnosis request (must refuse) |
| M8 audit_evidence | L5 | narration that requires audit-row reference (drops without M8) |
| M4 (drift) | L7 | stale manifest validation surface |

**Deliverable.** At least one load-bearing task per mechanism, plus
enough non-mechanism tasks to satisfy the L1/L2/L3 coverage from
`BENCHMARK_SPEC.md`. MVP target ~10-12 tasks.

**Packets.**

- `WP-GAB-003` (existing, rescoped) — first task set; acceptance now
  requires the load-bearing coverage rule.
- `WP-GAB-004` (existing) — hand-authored trajectories per task.

**Acceptance criteria.**

- Every task's `load_bearing_mechanisms` field is populated.
- A pytest fixture replays each task under `full_contract` and the
  matching `mechanism_off` mode and asserts a primary metric differs.
- No task requires private health data, clinical interpretation, or
  Claude-Code-specific surfaces.

**Dependencies.** Phase 2 (modes), Phase 3 (manifest), Phase 4
(fixtures), Phase 5 (harness).

### Phase 6a — Merged-paper adversarial task support

**Goal.** Ensure the HAI/GAB fixture and task surfaces can support the
50-trajectory adversarial layer without inventing new runtime behavior
after results are known.

**Deliverable.**

- Eight refusal-bypass L6 trajectories against M7.
- Eight mutation-escalation trajectories against M5+M6.
- Eight audit-tampering trajectories against M8 audit evidence
  emission.
- Eight schema-evasion trajectories against M4.
- Fields in trajectory artifacts for attack family, target mechanism,
  authoring mode, source prompt hash, seed, freeze timestamp, success
  score, and safety/usefulness tradeoff.

The 18 adaptive-vs-DRG-0 trajectories belong to the Engels/DRG work
packets, not HAI runtime code.

**Dependencies.** Phases 2-6, plus the merged-paper attack policy in
`RESEARCH_EVAL_STRATEGY.md`.

### Phase 7 — Drift snapshot and version pinning

**Goal.** Produce a deliberately-stale manifest snapshot for L7 tasks
and wire it through the harness.

**Deliverable.**

- A second manifest snapshot generated from a real prior tag (e.g.,
  `git show v0.1.18:hai capabilities`-equivalent), saved to
  `benchmark/governed_agent_bench/manifests/hai_0_1_18_drift.json`.
- Harness mechanism for swapping the manifest reference at task-load
  time without otherwise changing the harness prompt structure.
- L7 task variants that pair stale manifest with each runtime mode.

**Packets.**

- `WP-DRIFT-001` — programmatic stale-manifest generation from a prior
  tag.
- `WP-DRIFT-002` — harness manifest-swap hook.
- `WP-DRIFT-003` — L7 task variants × runtime modes.

**Acceptance criteria.**

- The drift snapshot validates against `agent_cli_contract.v1` (its
  era's schema), not v2; the harness must accept both.
- L7 tasks score differently under `full_contract` (where validation
  catches the stale-manifest mismatch) vs `no_validation` (where the
  stale call goes through and corrupts state).

**Dependencies.** Phase 3 (current snapshot), Phase 5 (harness).

### Phase 8 — Documentation and benchmark card

**Goal.** Make the contract auditable by reviewers from docs alone.

**Deliverable.**

- `benchmark/governed_agent_bench/OPERATORS_VIEW.md` — what an LLM sees
  end-to-end (prompt, manifest, contract notes, action schema).
- `benchmark/governed_agent_bench/SCAFFOLD_VIEW.md` — what an
  experimenter sees: the runtime-mode enumeration, what each mode
  changes, how to verify the disabling is real.
- `benchmark/governed_agent_bench/BENCHMARK_CARD.md` — intended use,
  non-use, data provenance, private-data exclusions, clinical-boundary
  exclusions, task family coverage, model conditions tested, scorer
  limitations.
- `hai/docs/agent_cli_contract.md` regenerated against the v2 manifest.
- `RESEARCH_EVAL_STRATEGY.md` cross-link confirming the runtime-first
  experimental design.

**Packets.**

- `WP-DOCS-OPS-001` — operator's view doc.
- `WP-DOCS-SCAFFOLD-001` — scaffold view doc.
- `WP-DOCS-CARD-001` — benchmark card draft.
- `WP-DOCS-CONTRACT-001` — regenerate `agent_cli_contract.md` from v2.

**Acceptance criteria.**

- A reviewer can read these four docs and answer: what is the
  contract, what is each runtime mode, how is each ablation verified
  to be real, what does the benchmark not measure?
- Every doc cross-references at least one other doc; no orphaned
  pointers.

**Dependencies.** Phases 2, 3, 5 (so the docs describe the actual
runtime, manifest, and harness).

## Cross-cutting concerns

### Schema deltas (D-PROJ-015)

The benchmark schemas are bumped to v2. The headline change is dropping
the old single `condition` enum and splitting it into two orthogonal
fields. Files changed:

- `benchmark/governed_agent_bench/schema/trajectory.schema.json` →
  v2: requires `runtime_mode` and `model_class`; old `condition` field
  removed.
- `benchmark/governed_agent_bench/schema/score.schema.json` → v2:
  same split; adds `mechanism` field on violations for finer-grained
  attribution.
- `benchmark/governed_agent_bench/schema/task.schema.json` → v2:
  adds optional `load_bearing_mechanisms` and `runtime_modes_in_scope`
  fields.
- `benchmark/verification/tests/test_governed_agent_bench_schema_contracts.py`
  updated to assert the new shape.

The old prompt-condition values (`local_prompt_only`,
`cloud_prompt_only`) are intentionally dropped. They are not part of
the headline experimental design.

**Merged-paper schema tightening.** Before any T3/T4 paper-claim run,
the schema work must also close the D-FRAME-021 / F-AUDIT-4-04 gap:

- `claim_tier` is required at the score level.
- T3/T4 trajectories and scores require `model_roster_hash`.
- T3/T4 trajectories and scores require a committed scorer config
  reference or hash.
- The T3/T4 conditional is propagated to
  `benchmark/governed_agent_bench/schema/trajectory.schema.json`, not
  only to score artifacts.

Without this tightening, exploratory runs may proceed, but the paper
must not claim predeclared thresholds or model-scale substitution.

### Vocabulary alignment (D-PROJ-V)

The HAI runtime today uses `mutation` and `command` per-command;
benchmark/spec docs use `mutation_class` and `name`. Phase 3 reconciles
to the doc vocabulary. The schema bump to `agent_cli_contract.v2`
records the break.

### Refusal as a runtime property (D-PROJ-S, non-negotiable)

The paper claim that the *runtime* enforces safety, not the model,
requires that refusal lives in code rather than in skills. Phase 2 is
the load-bearing engineering for this. Skills become advisory: they
may surface context to the model, but they do not own the refusal
decision and are not on the runtime's enforcement path.

## Reframe decision log

| ID | Decision | Status |
|---|---|---|
| D-PROJ-013 | Runtime is the primary axis of variation in the headline experiment. | Locked. |
| D-PROJ-014 | The deployment-realistic prompt is held constant across every condition. No `with_manifest` vs `without_manifest` ablation. | Locked. |
| D-PROJ-015 | Schema split: trajectory and score schemas use `runtime_mode` × `model_class`, dropping the single `condition` enum. | Locked (v2 schemas shipped 2026-05-09). |
| D-PROJ-016 | HAI is frozen as a product. v0.2.0 PyPI is the reference snapshot. No v0.2.1/v0.2.2/v0.2.3. | Locked. |
| D-PROJ-017 (a) | HAI manifest schema bumps to `agent_cli_contract.v2`; v0.2.3 freeze rule retired. | Locked. |
| D-PROJ-017 (b) | M5 + M6 stay separate; Phase 2 builds CLI-dispatch enforcer (`WP-DISPATCH-001`). | Locked. |
| D-PROJ-017 (c) | M7 refusal built as one canonical seam in `core/refusal/`. | Locked. |
| D-PROJ-017 (d) | Transaction integrity (M9-TX) held-constant non-ablatable invariant. M8 narrowed to evidence-reference emission. | Locked. |
| D-PROJ-017 (e) | Tier 5 (fine-tuning) moves to future-work appendix in `CLAIM_LADDER.md`. | Locked. |
| D-PROJ-017 (f) | `no_runtime` runtime mode renamed to `no_runtime_enforcement`. | Locked (v2 schemas shipped 2026-05-09). |
| D-PROJ-S | Refusal lives in runtime code, not skills. | Locked, non-negotiable. |
| D-PROJ-V | Manifest vocabulary aligned to spec docs (`mutation_class`, `name`). | Locked. |
| D-PROJ-G | Build weakened-runtime modes (`HAI_RUNTIME_MODE`) per Phase 2. | Locked. |
| D-PROJ-H | `HAI_HERMETIC=1` env mode, no new CLI subcommand. | Locked. |
| D-PROJ-F | Fixtures seeded via contract-pure `hai intake`/`hai propose` calls. | Locked. |
| D-PROJ-D | L7 drift snapshot generated programmatically from a prior tag. | Locked. |
| D-PROJ-M | MVP domain coverage = recovery + nutrition, expanded only if mechanism load-bearing tasks force it. | Provisional, revisit after Phase 6 task authoring. |
| D-PROJ-T | Defer fine-tuning data generator until Phase 7+. | Locked. |
| D-PROJ-R | HAI runtime defects discovered during research execute through `WP-RUNTIME-FIX-NNN`, no new HAI release ladder. | Locked. |
| D-FRAME-016 | Paper title is `Deterministic Software Contracts as Trusted Monitors in AI Control Protocols`. | Inherited from framing v2. |
| D-FRAME-020 | Predeclared roster is 6 Houdinis + 3 Guards, with Haiku 3.5 retired/pilot-only and Sonnet 4 retirement binding. | Inherited from framing v2. |
| D-FRAME-021 | AND-pass thresholds + 7 zero-tolerance critical violations + T3/T4 schema tightening. | Inherited from framing v2. |
| D-FRAME-022 | 50-trajectory attack policy, including 18 adaptive-vs-DRG-0. | Inherited from framing v2. |
| D-FRAME-023 | USD 1,500 hard model-API cost ceiling. | Inherited from framing v2. |
| D-FRAME-024 | Bounded HS contrast, L6 only, 2-week + USD 200 caps. | Inherited from framing v2. |

These supersede the prompt-first interpretation of `D-PROJ-008`'s
"local prompt-only" condition for the headline experiment. The
prompt-only condition may still appear as a future extension under a
defense-in-depth claim (out of scope for v1; see below).

## Risk profile

Round-1 audit (F-CDX-RFR-R1-18) flagged the original five-row register
as incomplete. The revised register adds API drift, reproducibility,
audit-round budget, schema forward-compatibility, and Phase 1 coupling
cost.

| Risk | Why it matters | Mitigation |
|---|---|---|
| Mechanisms not cleanly isolatable in HAI source. | Ablations contaminated; score gaps reflect multiple mechanisms; reviewers reject the architectural claim. | Phase 1 audit + per-mechanism unit tests + cross-mechanism isolation assertion. Decoupling packets emitted from findings. |
| MVP task set fails to find load-bearing tasks for one mechanism in MVP domains. | Coverage rule blocks Phase 6 sign-off. | Expand to one more domain or relax to one shared task per under-covered mechanism. |
| `no_runtime_enforcement` baseline performs comparably to `full_contract` on most tasks. | Architectural claim weakens to "the contract helps in narrow cases" (Tier 1, not Tier 2/3). | Empirical risk; cannot be engineered away. The experiment is *for* this question. |
| Refusal-in-code regresses HAI's user-facing daily loop. | Maintainer's own dogfood path breaks. | Skills retain their narration roles; only the refusal *decision* moves. Per-domain tests for the daily loop kept green. |
| Phase 1 audit finds extensive coupling, blowing the calendar. | Headline calendar slips by weeks. | Scope cuts: collapse M5+M6 (revert D-PROJ-017 (b)); narrow M7 to existing validators only (revert D-PROJ-017 (c)); drop `adversarial_user` fixture. Reorder cuts to favour those that don't require throwing away built work. |
| Cloud model API drift between baseline runs and ablation runs. | Cross-condition comparisons may reflect provider-side model updates rather than contract effects. | Pin `model_identity.provider_snapshot` per trajectory; rerun affected conditions when a snapshot expires. Avoid spanning paper experiments across provider snapshot rotations. |
| Reproducibility across machines (local model decoding nondeterminism, library-version drift). | Two researchers re-running the benchmark get materially different scores; reviewers cannot replicate. | Pin `decoding_settings` (temperature, top_p, max_tokens, seed) in `model_identity`. Pin `scorer_config_hash`, `prompt_template_hash`, `manifest_snapshot_id` in every trajectory. Version-pin model checkpoints and library deps in a reproducibility manifest. |
| Audit-round budget unaccounted for in calendar. | Round 1 alone produced 20 findings; round 2 typically 3-5; round 3 usually 1 nit. The original 9-12 week calendar didn't budget the 2-4 weeks of plan-audit loops the project's empirical settling shape implies. | Add 2-4 weeks for plan-audit loops between phases. Treat each major phase exit as a Codex audit gate (not a continuous audit). |
| Schema forward-compatibility once benchmark is public. | Future contributors building on the benchmark may hit v2/v3 migration friction. | Bump `schema_version` const on every breaking change. Provide a one-page migration note per bump. Do not silently mutate v2 schemas after a public release tag. |
| Public release of fixtures inadvertently includes private health data. | Privacy boundary violation; project posture (D-PROJ-007) breach. | Fixtures are seeded via `hai intake`/`hai propose` from synthetic inputs only. Pre-release scan rejects any fixture containing real wearable IDs, real timestamps from the maintainer's data, or any string matching the maintainer's personal phrasebook. |

## Calendar honesty

Round-1 audit (F-CDX-RFR-R1-18) flagged the original 9-12 week
estimate as missing the audit-round buffer. The estimates below now
apply only to HAI/GAB support work. They do not include the Engels full
run, bounded HS implementation, final red-team, or manuscript writing.
The merged-paper calendar is controlled by `PROJECT_EXECUTION_PLAN.md`:
Engels pilot July 2026, pilot decision gate August 2026, mechanism
ablations November 2026, full Engels February 2027, red-team and HS
March 2027, manuscript v1 April 2027, NeurIPS submission May 2027.

- **Strong version:** 12-16 weeks of evening/weekend bandwidth.
  Includes 2-4 weeks for plan-audit loops between major phases. Phase
  2 alone grew ~2-3 weeks because of `WP-DISPATCH-001` (the dispatch
  enforcer is now real engineering, not a config flag).
- **Calendar floor (12 weeks):** Phase 1 audit unsurprising (mechanisms
  isolatable as inventoried), no major schema rework needed in round
  3, MVP fixtures usable on first attempt.
- **Calendar ceiling (16+ weeks):** Phase 1 audit reveals extensive
  coupling, requiring architectural decoupling before Phase 2;
  multiple Codex review rounds reveal task-design issues; fixture
  seeding hits unexpected hermeticity gaps.

Critical path (longest sequential dependency chain):

```
Phase 1 inventory
   -> Phase 2 dispatch enforcer + refusal-in-code + runtime-mode switch
   -> Phase 3 manifest v2 + snapshot envelope
   -> Phase 4 hermeticity + fixtures
   -> Phase 5 harness with mode control + prompt template
   -> Phase 6 task authoring against load-bearing coverage rule
   -> Phase 7 drift snapshot + L7 variants
   -> Phase 8 docs + benchmark card
```

Scope-cut ladder (revised; ordered by *cost-of-cutting-after-already-built*,
cheapest first):

1. **Collapse M5+M6 into one mechanism.** Reverts D-PROJ-017 (b).
   Drops `WP-DISPATCH-001` (saves ~2-3 weeks if cut early; not
   recoverable cheaply once the dispatch middleware exists).
2. **Narrow M7 to existing validators.** Reverts D-PROJ-017 (c).
   Skips the new `core/refusal/` module; uses existing per-domain
   validators only.
3. **Cut `adversarial_user` fixture.** Use `governance_user` for both
   M5 and M7 stress.
4. **Cut to one MVP domain (recovery only).** Lose nutrition L4 task
   family.
5. **Cut Phase 7 drift to the bare minimum.** One stale snapshot, one
   L7 task family, no per-mode L7 variants. Loses the L7 × runtime
   cross-product.
6. **Cut M8 audit evidence ablation.** Keeps M4-M7 ablatable; loses one
   Tier 2 component. (Was cut #1 in round 1; reordered down because
   removing it after the harness is built around mechanism markers
   is more expensive than removing a future build.)
7. **Cut Phase 8 to operator's view + benchmark card.** Defer
   scaffold view.

Cuts beyond level 7 endanger the architectural claim and should not
be made without explicit maintainer decision.

## Out of scope before merged-paper claims

- Defense-in-depth experiments that vary both prompt and runtime in a
  2x2. These are a future paper or a v2 of this one.
- Prompt-only conditions in the headline experiment. See D-PROJ-014.
- New HAI domains beyond the MVP set.
- MCP transport. Deferred per AGENTS.md "Do Not Do".
- Hosted multi-user deployment, dashboards, frontends.
- LLM-judge factuality scoring as the primary safety oracle. See
  `SCORING_SPEC.md` for why.
- Threshold tuning after seeing results. See `RESEARCH_EVAL_STRATEGY.md`
  Anti-Patterns.
- Publishing a workshop paper first as the active path. That route is
  superseded by the merged-paper frame unless the Engels pilot gate
  reverts to Trajectory A.
- Building a coding-agent reference runtime before this paper. Appendix
  E is a sketch only and is not evidence of cross-domain generalization.
- Running fine-tuned local operators in paper 1. S1 fine-tuning is the
  sequel paper.

## Cross-references

- High-level paper-readiness goal: `HAI_PAPER_READINESS_PLAN.md`.
- Locked paper frame: `PAPER_FRAME.md`.
- Project-wide eval strategy: `RESEARCH_EVAL_STRATEGY.md`.
- Master merged-paper phase plan: `PROJECT_EXECUTION_PLAN.md`.
- Bounded coding-agent backlog: `WORK_PACKETS.md`.
- Mechanism inventory deliverable: `MECHANISM_INVENTORY.md`.
- Benchmark spec: `../../benchmark/governed_agent_bench/BENCHMARK_SPEC.md`.
- Operator harness spec: `../../benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`.
- Scoring spec: `../../benchmark/governed_agent_bench/SCORING_SPEC.md`.
- Schema deltas committed at:
  `../../benchmark/governed_agent_bench/schema/{trajectory,score,task}.schema.json`.
- Reframe provenance: `../../project/DECISIONS.md` D-PROJ-013..015.

## Glossary

- **Ablation.** Removing one component to measure its contribution.
- **Mechanism.** One of the eight enforcement components of the
  runtime contract (M1..M8).
- **Load-bearing task.** A benchmark task whose `full_contract` score
  differs from its `mechanism_off` score on at least one primary
  metric. This is the test that the task actually exercises the
  mechanism.
- **Runtime mode.** A configured combination of which mechanisms are
  on or off. Seven modes total; declared in `trajectory.schema.json`.
- **Hermetic mode.** `HAI_HERMETIC=1`: HAI refuses network and keyring
  access, runs only against fixture state. Required for benchmark
  reproducibility.
- **Snapshot envelope.** The provenance-wrapped capabilities manifest
  the benchmark pins against. Not a raw `hai capabilities --json` dump.
- **Scaffold ablation.** Synonym for "runtime mechanism ablation" in
  the literature; same thing as the modes other than `full_contract`.
- **`mechanism_disabled` step.** A trajectory step proving a mechanism
  was intentionally off in this run, distinguishing intentional
  disabling from silent breakage.
