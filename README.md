# Measuring Deterministic Governance Mechanisms in Agent Harnesses

This project treats the **agent harness, not the model, as the
experimental intervention surface**.

GovernedAgentBench measures deterministic governance mechanisms in
agent harnesses by holding the model and prompt fixed, varying only the
runtime contract, and scoring whether specific software-enforced
mechanisms are load-bearing for constraint-respecting agent behavior.

The repository exists to ship one artifact: the arXiv preprint
*Measuring Deterministic Governance Mechanisms in Agent Harnesses* by
2026-09-30, with GovernedAgentBench v1.0 released as a companion
GitHub tag. HAI is the pinned reference runtime used to instantiate the
contract; it is not an active product roadmap.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2999_passing-green)](hai/verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## The Experiment

Most agent evaluations collapse model, prompt, tools, and runtime into
one performance number. This project separates one layer: the
deterministic software contract around the model.

The primary experiment holds constant:

- the model class;
- the deployment-realistic prompt;
- the manifest snapshot;
- the task suite;
- the deterministic scorer.

It varies only `runtime_mode`. In `full_contract`, all deterministic
governance mechanisms are active. In the ablation modes, one mechanism
is disabled at a time:

| ID | Mechanism | Off mode |
|---|---|---|
| M4 | Typed-command and proposal validation | `no_validation` |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` |
| M7 | Clinical-boundary and forbidden-request refusal | `no_refusal` |
| M8 | Audit evidence emission | `no_audit_chain` |

`no_runtime_enforcement` disables M4-M8 together and is reported only
as a sanity floor. M9-TX transaction integrity is held constant.

The bounded claim is not that these mechanisms prove agent safety in
general. It is that, in this fixed harness, task suite, prompt, model,
and evidence tier, individual deterministic runtime mechanisms can be
measured as load-bearing for reliable, constraint-respecting operation.

## What This Is And Is Not

| This repo is | This repo is not |
|---|---|
| An AI-engineering study of agent-harness governance | A new model or prompting method |
| A mechanism-level ablation of deterministic runtime contract code | A broad AI safety benchmark |
| A reproducible benchmark with synthetic fixtures and offline scoring | A consumer health product evaluation |
| A non-clinical reference runtime used to instantiate concrete mechanisms | Evidence of diagnosis, treatment, prescribing, or clinical quality |
| A bounded empirical claim with separated evidence tiers | A universal causal claim about all agents or domains |

## Evidence Discipline

GovernedAgentBench keeps evidence tiers separate:

- **Static oracle pairs** show that hand-authored full/off transcripts
  isolate the intended scored consequence.
- **Live runtime probes** show that the HAI runtime changes behavior
  under targeted hermetic M4-M8 disable paths.
- **Model-backed trajectories** show how the locked model condition
  behaves through the governed harness.

These tiers are not merged into one oversized causal claim. Model
transcripts only count as benchmark evidence after conversion into
trajectory JSON and deterministic offline scores.

## Current State

- Preprint scope, title, mechanism inventory, threat model, hypotheses,
  calendar, and active decisions live in [`PAPER.md`](PAPER.md).
- GovernedAgentBench has schemas, an offline scorer, harness code,
  six synthetic fixtures, 28 pilot tasks, seed trajectories, static
  isolation oracle pairs, targeted live isolation probes for M4-M8, and
  a deterministic rule baseline.
- Model-backed paper claims are pending the locked pilot workflow and
  must preserve the static/live/model-backed evidence split.
- HAI is frozen as a product at v0.2.0 PyPI and serves only as the
  pinned reference runtime for the benchmark and preprint.

## Read in This Order

| Doc | Lines | Why |
|---|---|---|
| [`PAPER.md`](PAPER.md) | ~400 | Active research control plane: scope, calendar, decisions, hypotheses, roster, mechanism inventory, and talk track. |
| [`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md) | ~100 | Benchmark overview, directory map, measurement-readiness, and current gates. |
| [`benchmark/governed_agent_bench/BENCHMARK_CARD.md`](benchmark/governed_agent_bench/BENCHMARK_CARD.md) | ~150 | Intended use, non-use, data provenance, runtime modes, scorer, and limitations. |
| [`AGENTS.md`](AGENTS.md) | ~220 | Operating contract for AI coding tools working in this multi-agent tree. |
| [`CLAUDE.md`](CLAUDE.md) | ~40 | Claude-Code session-start pointer and common commands. |

Lane-specific docs live under their owner directories. Historical
decision provenance lives in [`ARCHIVE/`](ARCHIVE/) and is not part of
the cold-start path.

## Repo Tree

```
README.md / PAPER.md / AGENTS.md / CLAUDE.md     # cold-start surface
CHANGELOG.md / LICENSE / SECURITY.md / CITATION.cff
pyproject.toml / uv.lock

benchmark/governed_agent_bench/                  # benchmark code, schemas, scorer, harness, tasks, results
hai/src/ + hai/docs/ + hai/verification/         # frozen HAI reference runtime + operator docs + tests
paper/DRAFT.md                                   # paper draft scaffold
paper/prior_art_notes.md                         # citation notes only

ARCHIVE/                                         # frozen historical provenance, not in cold-start
  framing_v2/                                    # 27 D-FRAME decisions, 3 rounds, 6 batches
  hai_release_history/                           # v0.1.X release cycles, audit chains
  paper_drafts/                                  # CLAIM_LADDER, DRAFT_PAPER, PAPER_OUTLINE_MERGED
  pre_reframe_plans/                             # superseded HAI strategy
  decisions_log.md                               # full D-PROJ / D-FRAME / D-PREPRINT chain
  hai_paper_readiness_execution.md               # the 779-line phase plan
```

## Reproduce Offline Evidence

The offline path does not call local models, cloud models, paid APIs,
live wearable sources, or private health data:

```bash
PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

It regenerates synthetic fixtures, deterministic rule-baseline
trajectories, scores, evidence tables, SVG figures, the static
isolation matrix, targeted live-isolation probes, adversarial summary
tables, and an offline reproducibility manifest.

## HAI Smoke Loop

HAI is included because the benchmark needs a concrete runtime contract
to instantiate and ablate. For operator documentation, see
[`hai/docs/hai_reference_runtime.md`](hai/docs/hai_reference_runtime.md).

```bash
pipx install health-agent-infra
hai init --non-interactive
hai capabilities --human
hai doctor
hai daily
hai today
```

## Health Boundary

The reference runtime is explicitly non-clinical:

- no diagnosis;
- no treatment;
- no prescribing;
- no autonomous medical decisions;
- no private health rows in public benchmark fixtures.

This is part of the evaluated runtime contract, not a disclaimer.

## License

MIT. See [LICENSE](LICENSE).
