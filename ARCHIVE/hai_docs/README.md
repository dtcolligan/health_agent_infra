# HAI Docs — Index

Current documentation for the HAI reference runtime. Start with
`hai_reference_runtime.md` if you want the operator manual,
`current_system_state.md` if you need the latest HAI runtime truth, and
`architecture.md` if this is your first architecture read.

This directory is owned by the HAI reference-runtime lane. HAI-specific
tests/evals live under `hai/verification/`, HAI assets live under
`hai/assets/`, and HAI release proof/provenance lives under
`hai/reporting/`.

Project-wide research framing lives at
[`../../project/FRAME.md`](../../project/FRAME.md),
[`../../project/DECISIONS.md`](../../project/DECISIONS.md),
[`../../project/OPERATING_MODEL.md`](../../project/OPERATING_MODEL.md), and
[`../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../research/runtime_contracts_paper/PAPER_FRAME.md).
GovernedAgentBench lives at
[`../../benchmark/governed_agent_bench/`](../../benchmark/governed_agent_bench/).

Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent. It is not a health chatbot, and the
runtime is not the agent. It gives the agent durable local state,
deterministic interpretation, bounded write paths, review memory,
backup/recovery tooling, and auditable explanations for personal-health
decisions.

For a one-page orientation of the top-level repo layout (what each
top-level directory is, what is active vs historical), see
[`../../project/REPO_MAP.md`](../../project/REPO_MAP.md). For a map of `hai/reporting/`
itself (docs / artifacts / plans / experiments), see
[`../../hai/reporting/README.md`](../../hai/reporting/README.md).

## Controlling docs

- [`current_system_state.md`](current_system_state.md) — current package
  version, schema head, command count, release posture, and next-cycle
  roles. This is the shortest "what is true now?" document.
- [`hai_reference_runtime.md`](hai_reference_runtime.md) — HAI-specific
  operator manual: install, daily workflow, domains, data paths,
  boundaries, and command groups.
- [`architecture.md`](architecture.md) — pipeline diagram,
  code-vs-skill boundary, R-rule / X-rule intro, package layout.
- [`host_agent_contract.md`](host_agent_contract.md) — compact
  operating contract for a shell-capable host agent.
- [`non_goals.md`](non_goals.md) — what v1 refuses to build and
  why (macros-only nutrition, no ML loop, no hosted, etc).
- [`x_rules.md`](x_rules.md) — full X-rule catalogue with
  triggers, tiers, effects, and config keys.
- [`glossary.md`](glossary.md) — shared vocabulary for agent-safe,
  R-rule, X-rule, forced_action, target_status, W57, and related terms.
- [`state_model_v1.md`](state_model_v1.md) — table-by-table state
  schema. The migrations themselves at
  `hai/src/health_agent_infra/core/state/migrations/` are the source of
  truth; this doc may lag the latest migration when a release adds
  schema (currently 028 live in the v0.2.0 source tree).

## Read by role

| Reader | Read |
|---|---|
| Research / benchmark contributor | [`../../project/FRAME.md`](../../project/FRAME.md), [`../../project/DECISIONS.md`](../../project/DECISIONS.md), [`../../project/OPERATING_MODEL.md`](../../project/OPERATING_MODEL.md), [`../../project/HYPOTHESES.md`](../../project/HYPOTHESES.md), [`../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../research/runtime_contracts_paper/PAPER_FRAME.md), [`../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`](../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md), [`../../benchmark/governed_agent_bench/README.md`](../../benchmark/governed_agent_bench/README.md) |
| User | [`hai_reference_runtime.md`](hai_reference_runtime.md), [`current_system_state.md`](current_system_state.md), [`privacy.md`](privacy.md), [`non_goals.md`](non_goals.md), [`backup_and_recovery.md`](backup_and_recovery.md) |
| Host-agent integrator | [`host_agent_contract.md`](host_agent_contract.md), [`agent_integration.md`](agent_integration.md), [`agent_cli_contract.md`](agent_cli_contract.md), [`cli_exit_codes.md`](cli_exit_codes.md), [`glossary.md`](glossary.md) |
| Runtime contributor | [`architecture.md`](architecture.md), [`state_model_v1.md`](state_model_v1.md), [`domains/README.md`](domains/README.md), [`how_to_add_a_domain.md`](how_to_add_a_domain.md), [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md) |
| Release auditor / maintainer | [`current_system_state.md`](current_system_state.md), [`../../hai/reporting/AUDIT.md`](../../hai/reporting/AUDIT.md), [`../../project/ROADMAP.md`](../../project/ROADMAP.md), [`../../hai/reporting/plans/README.md`](../../hai/reporting/plans/README.md) |
| Explanation reviewer | [`explainability.md`](explainability.md), [`x_rules.md`](x_rules.md), [`memory_model.md`](memory_model.md) |

## Current-vs-provenance rule

Docs directly under this directory are intended as current operating
docs unless their header says otherwise. Cycle docs under
`hai/reporting/plans/v0_*/`, launch drafts under `hai/reporting/docs/launch/`,
and dated review artifacts are provenance: useful for why a decision
happened, not automatically current product truth. When they disagree, prefer
`current_system_state.md`, generated CLI capabilities, migrations,
and tests.

## Onboarding

- [`tour.md`](tour.md) — 10-minute guided reading tour.
- [`agent_integration.md`](agent_integration.md) — how Claude
  Code / Agent SDK / open equivalents install and drive the
  package.
- [`domains/README.md`](domains/README.md) — "how to add a new
  domain" checklist plus links to the six v1 domain references.
- [`how_to_add_a_domain.md`](how_to_add_a_domain.md) — conceptual
  walk-through for the domain-extension surface; pairs with the
  `domains/README.md` checklist.
- [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md) —
  contract + evidence shape + DoD for adding a second source
  adapter under `core/pull/`.

## Archived

[`../../hai/reporting/docs/archive/doctrine/`](../../hai/reporting/docs/archive/doctrine/) holds pre-rebuild
doctrine docs (canonical_doctrine.md, chief_operational_brief,
founder_doctrine, phase_timeline). [`../../hai/reporting/docs/archive/cycle_artifacts/`](../../hai/reporting/docs/archive/cycle_artifacts/)
holds v0.1.x cycle-specific design/review docs that were previously mixed
into the current docs directory. Both archives are retained for historical
context only — do not cite them as current truth.

## Where proof lives

- Eval runner captures:
  ``hai/reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/``
- Plans (rebuild + Phase 2.5 gates):
  ``hai/reporting/plans/``
- Throwaway prototypes (Phase 0.5, Phase 2.5 Track A/B):
  ``hai/reporting/experiments/``
