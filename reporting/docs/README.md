# Docs — index

Current v1 documentation for Health Agent Infra. Start with
``architecture.md`` if this is your first read.

## Controlling docs

- [`architecture.md`](architecture.md) — pipeline diagram,
  code-vs-skill boundary, R-rule / X-rule intro, package layout.
- [`non_goals.md`](non_goals.md) — what v1 refuses to build and
  why (macros-only nutrition, no ML loop, no hosted, etc).
- [`x_rules.md`](x_rules.md) — full X-rule catalogue with
  triggers, tiers, effects, and config keys.
- [`state_model_v1.md`](state_model_v1.md) — table-by-table state
  schema (migrations 001–006 live).

## Onboarding

- [`tour.md`](tour.md) — 10-minute guided reading tour.
- [`agent_integration.md`](agent_integration.md) — how Claude
  Code / Agent SDK / open equivalents install and drive the
  package.
- [`domains/README.md`](domains/README.md) — "how to add a new
  domain" recipe; reference implementations are the six v1
  domains.

## Archived

[`archive/doctrine/`](archive/doctrine/) holds pre-rebuild
doctrine docs (canonical_doctrine.md, chief_operational_brief,
founder_doctrine, phase_timeline). They are retained for
historical context only — do not cite them as current truth. See
``archive/doctrine/README.md`` for the supersession map.

## Where proof lives

- Eval runner captures:
  ``reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/``
- Plans (rebuild + Phase 2.5 gates):
  ``reporting/plans/``
- Throwaway prototypes (Phase 0.5, Phase 2.5 Track A/B):
  ``reporting/experiments/``
