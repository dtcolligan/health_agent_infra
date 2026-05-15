# Deterministic Software Contracts as Trusted Monitors in AI Control Protocols

This repository exists to ship one artifact: an arXiv preprint by
2026-09-30, with GovernedAgentBench v1.0 released as a companion
GitHub tag. Single objective. After 2026-10-01 the maintainer pivots
to mechanistic interpretability and the preprint is closed.

[![PyPI](https://img.shields.io/pypi/v/health-agent-infra)](https://pypi.org/project/health-agent-infra/)
[![Tests](https://img.shields.io/badge/tests-2943_passing-green)](hai/verification/tests/)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](pyproject.toml)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)

## Current State

- Preprint scope locked 2026-05-15. Title, mechanism inventory, threat
  model, hypotheses, calendar, and active decisions all live in
  [`PAPER.md`](PAPER.md).
- GovernedAgentBench has the measurement-ready substrate: schemas,
  offline scorer, harness, six synthetic fixtures, ten pilot tasks,
  fourteen hand-authored trajectories, rule baseline. No model-backed
  runs yet.
- HAI is frozen as a product at v0.2.0 PyPI. It is the pinned
  reference runtime; not a product roadmap.

## Read in This Order

| Doc | Lines | Why |
|---|---|---|
| [`PAPER.md`](PAPER.md) | ~350 | What we're shipping. Scope, calendar, decisions, mechanism inventory, hypotheses, threat model, model roster, engineering plan. |
| [`AGENTS.md`](AGENTS.md) | ~150 | Operating contract for AI coding tools. Governance invariants, CLI boundaries, do-not-do list. |
| [`CLAUDE.md`](CLAUDE.md) | ~30 | Claude-Code session-start pointer and common commands. |

Cold-start to productive in 20 minutes from these three files. Lane-
specific docs live under their owner directories.

## Repo Tree

```
README.md / PAPER.md / AGENTS.md / CLAUDE.md     # cold-start surface
CHANGELOG.md / LICENSE / SECURITY.md / CITATION.cff
pyproject.toml / uv.lock

benchmark/governed_agent_bench/                  # benchmark code, schemas, scorer, harness, tasks
hai/src/ + hai/docs/ + hai/verification/         # frozen reference runtime + operator docs + tests
research/paper/                                  # paper draft (LaTeX)
research/prior_art/                              # citation notes only

ARCHIVE/                                         # frozen historical provenance, not in cold-start
  framing_v2/                                    # 27 D-FRAME decisions, 3 rounds, 6 batches
  hai_release_history/                           # v0.1.X release cycles, audit chains
  paper_drafts/                                  # CLAIM_LADDER, DRAFT_PAPER, PAPER_OUTLINE_MERGED
  pre_reframe_plans/                             # superseded HAI strategy
  decisions_log.md                               # full D-PROJ / D-FRAME / D-PREPRINT chain
  hai_paper_readiness_execution.md               # the 779-line phase plan
```

## Research Thesis

Large language models are useful operators, but weak sources of
durable truth. In sensitive workflows, the model should not also be
the database, validator, policy engine, migration layer, and auditor.

This repo tests a different division of labor:

- the **model** proposes, routes, clarifies, and explains;
- the **runtime** owns truth, validation, mutation, policy, and audit.

The preprint's conservative claim is measurement-first: holding the
deployment prompt constant, toggling individual runtime mechanisms
(M4 validation, M5 `agent_safe`, M6 W57 proposal/commit gate, M7
clinical-boundary refusal, M8 audit evidence emission) produces
measurable per-mechanism contributions to safe bounded operation on
a single model class. Full mechanism inventory, model roster, and
threshold package in [`PAPER.md`](PAPER.md).

## HAI Smoke Loop

```bash
pipx install health-agent-infra
hai init --non-interactive
hai capabilities --human
hai doctor
hai daily
hai today
```

Full HAI operator documentation:
[`hai/docs/hai_reference_runtime.md`](hai/docs/hai_reference_runtime.md).

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
