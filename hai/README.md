# HAI Reference Runtime

HAI is the pinned reference runtime for the preprint *Measuring
Deterministic Governance Mechanisms in Agent Harnesses*.

The paper does not study HAI as a product. It uses HAI because the
benchmark needs a concrete agent harness whose deterministic governance
mechanisms can be turned on and off under a fixed model and prompt.
HAI v0.2.0 is frozen as the runtime snapshot the paper and
GovernedAgentBench cite against.

Project-wide scope: [`/PAPER.md`](../PAPER.md). Operating contract for
AI tools: [`/AGENTS.md`](../AGENTS.md).

## Role In The Paper

HAI instantiates the software contract that GovernedAgentBench measures:

| Mechanism | HAI surface |
|---|---|
| M4 validation | Typed CLI commands and proposal payload validation |
| M5 `agent_safe` | Dispatch middleware that refuses unsafe agent-context commands |
| M6 proposal gate | W57 proposal/commit semantics for user-authored state |
| M7 refusal | Non-clinical and forbidden-request refusal paths |
| M8 audit evidence | Read surfaces and audit artifacts used by scored narration |
| M9-TX transaction integrity | Held constant across all benchmark runtime modes |

The reference domain is non-clinical personal wellness because it
contains natural contract boundaries. Passing benchmark tasks is
evidence of boundary obedience and runtime-contract behavior, not
evidence of medical quality.

## Layout

| Path | Purpose |
|---|---|
| [`src/health_agent_infra/`](src/health_agent_infra/) | Runtime code (frozen at v0.2.0). Do not modify outside `WP-RUNTIME-FIX-NNN` packets. |
| [`docs/architecture.md`](docs/architecture.md) | Pipeline + code-vs-skill boundary; paper §3 grounding |
| [`docs/agent_cli_contract.md`](docs/agent_cli_contract.md) | Auto-generated CLI surface (regenerate from `hai capabilities --markdown`) |
| [`docs/hai_reference_runtime.md`](docs/hai_reference_runtime.md) | Operator workflow, install, domains, daily-loop |
| [`docs/privacy.md`](docs/privacy.md) | Non-clinical health boundary as part of the contract |
| [`docs/grounded_expert_scope.md`](docs/grounded_expert_scope.md) | Bounded research-retrieval contract (referenced by `core/research/`) |
| [`docs/cold_start_policy_matrix.md`](docs/cold_start_policy_matrix.md) | Cold-start policy table per domain |
| [`docs/x_rules.md`](docs/x_rules.md) | X-rule reference (referenced as `origin_path` by research sources) |
| [`docs/domains/README.md`](docs/domains/README.md) | Six-domain map |
| [`verification/`](verification/) | Test suite |

Historical product-era documentation (competitive landscape, marketing
positioning, standards mapping, query taxonomy, x_rules, tour,
host-agent integration guides, and others) is archived at
[`/ARCHIVE/hai_docs/`](../ARCHIVE/hai_docs/). HAI release history (the
v0.1.X cycles, audit chains, work packets) is at
[`/ARCHIVE/hai_release_history/`](../ARCHIVE/hai_release_history/).

## Smoke Loop

```bash
pipx install health-agent-infra
hai init --non-interactive
hai capabilities --human
hai doctor
hai daily
hai today
```

## Freeze Status

HAI is frozen as a product per D-11 in `/PAPER.md`. Runtime defects
discovered during preprint or benchmark work fix via
`WP-RUNTIME-FIX-NNN` packets; they do not become release work. No
v0.2.1+ cycles, no new tactical-plan rows, no PyPI uploads.

## Non-Goals

- No consumer-product roadmap.
- No clinical or medical-decision claims.
- No new wearable-source expansion for the preprint.
- No private health rows in public benchmark fixtures.
- No runtime changes unless they directly support the paper,
  benchmark, or reproducibility contract.
