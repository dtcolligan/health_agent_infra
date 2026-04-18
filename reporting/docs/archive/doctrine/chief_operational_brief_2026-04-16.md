# Chief Operational Brief — 2026-04-16

This file preserves the source brief that initiated the Phase 1 doctrine pass. It is the controlling input for the artifacts in this directory dated 2026-04-16 onward. It is reference material, not a replacement for the derived doctrine docs.

## Controlling thesis

Health Lab is the governed runtime that turns user-owned health evidence into structured state, making safe, personally tailored agent action possible.

## Controlling rule

Proof before breadth. One narrow, inspectable loop beats many connectors, many ideas, many folders. Every change should answer: does this make the flagship proof more real, more inspectable, or more legible?

## Canonical runtime architecture

`PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW`

This is the conceptual runtime model. It sits on top of the existing eight-bucket repo organisation, it does not replace it.

Mapping to existing buckets:

- `pull/` -> PULL
- `clean/` -> CLEAN
- `merge_human_inputs/` -> PULL and STATE update surface
- `interpretation/` -> RECOMMEND
- `writeback/` -> ACTION and STATE persistence
- `safety/` -> POLICY
- `reporting/` -> proof and output surfaces
- `research/` -> exploratory support, not core runtime

## Flagship loop

Recovery and training-readiness. Inputs: Garmin sleep, resting HR, HRV-or-proxy, prior training load, manual readiness check-in, optional workload context. Outputs: explicit state object, bounded recommendation object, rationale, confidence, uncertainty, low-risk writeback, next-day review event.

## Phase 1 deliverable set

- canonical doctrine memo
- runtime architecture doc
- flagship loop spec
- state object schema
- recommendation object schema
- minimal policy rule set
- explicit non-goals

## Phase 1 exit condition

The project can be explained consistently, precisely, and without improvisation.

## Chief operating directives

Optimize only for: conceptual discipline, narrowness, inspectability, boundedness, legibility.

## Link index

- [canonical_doctrine.md](canonical_doctrine.md)
- [flagship_loop_spec.md](flagship_loop_spec.md)
- [explicit_non_goals.md](explicit_non_goals.md)
- [tour.md](tour.md)
- [phase_timeline.md](phase_timeline.md)
- [agent_integration.md](agent_integration.md)

Note: this brief predates the 2026-04-17 reshape. It references some schema and policy docs (`state_object_schema.md`, `recommendation_object_schema.md`, `minimal_policy_rules.md`) that were retired in commit 4c of the reshape. The current equivalents are:

- classification rules + policy + recommendation shape -> `skills/recovery-readiness/SKILL.md`
- recommendation dataclass -> `src/health_agent_infra/schemas.py`
- code-enforced invariants -> `src/health_agent_infra/validate.py`
