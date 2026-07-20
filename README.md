# Told or Enforced: Measuring When In-Context Contracts Substitute for Runtime Enforcement in Agent Harnesses

### 📄 [Read the paper (PDF)](paper/DRAFT_dom.pdf)

Full draft. Also as the [paper landing page](paper/README.md) (abstract, figures, result) and [Markdown](paper/DRAFT_dom.md).

An agent harness has **two ways to make an agent respect a constraint**:
specify it in the prompt (an in-context contract), or enforce it in the
runtime (a guardrail). Real systems do both, and rarely ask when one
substitutes for the other.

GovernedAgentBench separates the two. It measures how much of an agent's
constraint-respecting behavior comes from being *told* versus being
*enforced*, mechanism by mechanism, with a deterministic offline scorer.

The repository exists to ship one artifact: the preprint
*Told or Enforced: Measuring When In-Context Contracts Substitute for
Runtime Enforcement in Agent Harnesses*, with GovernedAgentBench v1.0 released
as a companion GitHub tag. HAI is the pinned reference runtime used to
instantiate the contract; it is the instrument, not an active product
roadmap.

**The draft is complete and readable now.** arXiv submission is the
remaining step and may be delayed, so the paper is presented on the repo
in the meantime: **[read it in `paper/`](paper/)** (start with the
[landing page](paper/README.md) or the [PDF](paper/DRAFT_dom.pdf)).

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2999_passing-green)](hai/verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## The Experiment

Most agent evaluations collapse model, prompt, tools, and runtime into
one performance number, and guardrail evaluations never check what the
model would have done on its own. This project separates two levers with
a 2x2 applied per mechanism:

- **Contract axis:** is the constraint specified in the in-context
  contract (the manifest in the prompt), or withheld?
- **Enforcement axis:** does the runtime enforce it, or not?

|  | Runtime enforces | Runtime off |
|---|---|---|
| **Contract in prompt** | deployment baseline | told, not enforced (self-enforcement) |
| **Contract withheld** | enforced, not told | neither (violation floor) |

The mechanisms toggled on the enforcement axis:

| ID | Mechanism | Off mode | Context-verifiable? |
|---|---|---|---|
| M4 | Typed-command and proposal validation | `no_validation` | yes |
| M5 | `agent_safe` dispatch refusal | `no_agent_safe` | yes |
| M6 | W57 proposal/commit user gate | `no_proposal_gate` | yes |
| M7 | Boundary and forbidden-request refusal | `no_refusal` | yes |
| M8 | Audit evidence emission / reference faithfulness | `no_audit_chain` | no |

`no_runtime_enforcement` disables M4-M8 together and is reported only
as a sanity floor. M9-TX transaction integrity is held constant.

The question under test is what runtime enforcement adds once the model has
already been told the rule (the A-vs-B contrast). A within-family run
answers it: telling the rule moves behavior in every family (+24 points pooled
with the runtime off), but it does not stand in for enforcement. The marginal
value of enforcement given telling is 41 points pooled, small only for the two
self-enforcing families and most of the barrier for the two weak ones, so
substitution holds only in that narrow corner. Capability does not cleanly
decide it. The runtime's block, meanwhile, is an unconditional guarantee (488
of 488 enforced runs safe). See `PAPER.md` "Evidence Status" for what is
confirmed versus pending.

## What This Is And Is Not

| This repo is | This repo is not |
|---|---|
| An AI-engineering study of agent-harness governance | A new model or prompting method |
| A study separating the in-context contract from runtime enforcement, per mechanism | A broad AI safety benchmark |
| A reproducible benchmark with synthetic fixtures and offline scoring | A consumer health product evaluation |
| A non-clinical reference runtime used to instantiate concrete mechanisms | Evidence of diagnosis, treatment, prescribing, or clinical quality |
| A bounded empirical claim with separated evidence tiers | A universal causal claim about all agents or domains |

The told-not-enforced cell (told, runtime off) isolates what a model does with
a rule it was told but that nothing enforces, a quantity a post-training
evaluation could track; the benchmark measures it and does no training.

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
  six synthetic fixtures, a 39-task suite (16-task paid subset), seed
  trajectories, static isolation oracle pairs, targeted live isolation
  probes for M4-M8, and a deterministic rule baseline.
- The specify-vs-enforce 2x2 ran as a within-family sweep (four
  model families, a strong and a weak sibling each) against the git-pinned
  runtime. The headline: telling moves behavior in every family (+24 points
  pooled with the runtime off) but does not stand in for enforcement, whose
  marginal value given telling is 41 points pooled and small only for the
  self-enforcing families; capability does not cleanly order it (paper §5).
  A four-model capability ladder is the confounded precursor it corrects.
  The goal-conflict and instrumental arms returned nulls; the adversarial
  arm, long-horizon drift, and an external non-HAI replication remain
  future work. See
  [`paper/`](paper/) for the result and `PAPER.md` "Evidence Status" for
  the diagnostic-tier provenance.
- Model-backed paper claims must preserve the static/live/model-backed
  evidence split.
- HAI is frozen as a product and serves only as the pinned reference
  runtime for the benchmark and preprint. The v0.2.0 PyPI wheel is a
  **non-enforcing** snapshot: the dispatch/commit gates landed after it,
  so the runtime measured in the preprint is pinned by git commit
  `6c82cd0` (tag `gab-runtime-1.0.1`). Reproduce the paper's runtime by
  checking out that tag, not by installing the wheel. The paid-run
  trajectories and grades are released as
  [`gab-run-archive-v1.0`](https://github.com/dtcolligan/health_agent_infra/releases/tag/gab-run-archive-v1.0)
  with SHA-256 checksums.

## Read in This Order

| Doc | Lines | Why |
|---|---|---|
| [`PAPER.md`](PAPER.md) | ~900 | Active research control plane: scope, calendar, decisions, hypotheses, roster, mechanism inventory, and talk track. |
| [`benchmark/governed_agent_bench/README.md`](benchmark/governed_agent_bench/README.md) | ~150 | Benchmark overview, directory map, measurement-readiness, and current gates. |
| [`benchmark/governed_agent_bench/BENCHMARK_CARD.md`](benchmark/governed_agent_bench/BENCHMARK_CARD.md) | ~280 | Intended use, non-use, data provenance, runtime modes, scorer, and limitations. |
| [`AGENTS.md`](AGENTS.md) | ~240 | Operating contract for AI coding tools working in this multi-agent tree. |
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
paper/README.md + paper/DRAFT_dom.pdf            # the paper: landing page + full draft
paper/JOURNEY.md                                 # the making-of essay
paper/prior_art_notes.md + paper/refs.bib        # citation notes and bibliography

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
