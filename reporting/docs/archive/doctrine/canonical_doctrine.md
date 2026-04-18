# Canonical Doctrine

Status: Phase 1 doctrine. Adopted 2026-04-16 per the Chief Operational Brief.

This document is the controlling explanation of what Health Lab is, what it is trying to prove right now, and how the runtime is shaped. It supersedes prior improvised descriptions. If another doc conflicts with this one, this one wins until explicitly retired by a later dated doctrine update.

## Thesis

Health Lab is the governed runtime that turns user-owned health evidence into structured state, making safe, personally tailored agent action possible.

The emphasis is intentional:

- **governed** — the runtime is constrained by an explicit, inspectable policy layer, not by vibes
- **user-owned health evidence** — inputs are the user's own data, pulled from sources the user already controls
- **structured state** — the system exposes a typed, inspectable state object, not prose
- **safe, personally tailored agent action** — outputs are bounded, confidence-expressed, and reversible

Health Lab is not a clinical product, not a hosted multi-user service, not a broad AI health app, and not a medical-grade decision system. It is a governed runtime, proved through one narrow loop.

## Controlling rule: proof before breadth

Near-term project quality will be determined far more by one convincing end-to-end loop than by many connectors, many ideas, or many folders.

Operationally:

- one flagship loop before platform expansion
- one strong connector slice before connector sprawl
- one explicit state model before broad recommendation logic
- one bounded action pathway before richer automation
- one public proof before ambitious narrative inflation

Every proposed change is evaluated against one question:

**Does this make the flagship proof more real, more inspectable, or more legible?**

If not, it is a distraction and should be deferred.

## Runtime architecture

The canonical runtime model is:

```
PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
```

This is the conceptual operating shape of the system. The eight-bucket repo model is preserved as a workstream organisation layer, not as the deepest runtime architecture.

### Layer definitions

#### PULL
Acquires raw evidence from external sources and manual inputs. Outputs raw, source-shaped records. Does not interpret, normalize, or judge.

#### CLEAN
Normalizes, validates, deduplicates, and aligns evidence into canonical, typed objects. Outputs cleaned evidence ready for state construction. Does not recommend.

#### STATE
Constructs the live user state from cleaned evidence, recent history, profile context, and explicit uncertainty accounting. Outputs a typed state object that downstream layers read. State is first-class and visible.

#### POLICY
Constrains what the system may conclude, recommend, or do. Enforces: no diagnosis, no overconfident claims on noisy proxy data, no recommendation when missingness is too high, explicit escalation / no-escalation. Policy is executable, not prose.

#### RECOMMEND
Produces bounded, structured, state-conditioned recommendations. Each recommendation carries action, rationale, confidence, uncertainty, follow-up. No free-form paragraphs as the primary output.

#### ACTION
Executes low-risk approved actions or writebacks under policy. Examples: write a recommendation log entry, append to a daily plan note. ACTION is reversible and auditable. High-risk actions are not in scope.

#### REVIEW
Evaluates outcomes and updates memory / pattern understanding. A loop without review is not agentic; it is only a one-shot response.

### Layer -> bucket mapping

The eight-bucket model is the project's organising frame. After the 2026-04-17 reshape, the Python implementation lives at `src/health_agent_infra/` with subpackages (`pull/`, `clean/`, `writeback/`, `review/`) mirroring the runtime layers; top-level directories (`safety/tests/`, `reporting/`, `merge_human_inputs/`) hold tests, artifacts, docs, and examples.

Runtime layer -> surface:

- PULL -> `src/health_agent_infra/pull/` (Garmin adapter) + `hai pull` CLI
- CLEAN -> `src/health_agent_infra/clean/` (CleanedEvidence + RawSummary) + `hai clean`
- STATE / POLICY / RECOMMEND -> `skills/recovery-readiness/SKILL.md` (agent-owned judgment, not Python)
- ACTION -> `src/health_agent_infra/writeback/` + `src/health_agent_infra/validate.py` (code-enforced boundary) + `hai writeback`
- REVIEW -> `src/health_agent_infra/review/` + `hai review`
- Human input -> `skills/merge-human-inputs/SKILL.md` (agent partitions raw input into typed slots) + `merge_human_inputs/examples/`
- Safety -> `skills/safety/SKILL.md` (fail-closed rules the agent obeys) + `src/health_agent_infra/validate.py` (R2 banned tokens, action/confidence enums, R4 review window) + `safety/tests/`
- Reporting -> `skills/reporting/SKILL.md` (narration voice) + `reporting/docs/` (doctrine) + `reporting/artifacts/` (proof bundles)

The bucket model is a conceptual category system, not a package-find directive. The installable package's physical layout is `src/health_agent_infra/`.

## Scope doctrine

### In scope for this phase

- the flagship recovery and training-readiness loop
- Garmin as the passive-data anchor
- typed manual readiness intake as the human-input anchor
- one explicit state object
- one minimal executable policy layer
- one bounded recommendation object
- one low-risk writeback
- one next-day review event
- public proof surfaces documenting the above

### Out of scope for this phase

See [explicit_non_goals.md](explicit_non_goals.md) for the enforced list. Summary: no second connector before flagship proof, no broad AI health coaching, no medical-style outputs, no rich UI, no deep nutrition system, no speculative MCP expansion.

## Doctrine on abstraction

The language of the project must not run ahead of the implementation. Every major claim in repo-facing language must be backed by a concrete, inspectable artifact. If a claim cannot be traced to code, a schema, or a checked-in proof artifact, the claim is removed or softened until it can be.

## Doctrine on state

State is first-class. The system does not rely on implicit state buried in prose, logs, or chain-of-thought. The state object is typed, versioned, inspectable, and the single input to the recommendation layer.

## Doctrine on policy

Policy has two faces: **reasoning** and **enforcement**. Reasoning is how an agent decides when to block, soften, or escalate given evidence — that lives in `skills/recovery-readiness/SKILL.md` where it can be read, revised, and argued with. Enforcement is the invariant check that the runtime code must hold regardless of how the agent reasoned — that lives in `src/health_agent_infra/validate.py` with one test per invariant id. Prose-only safety claims are not enough; every invariant the doctrine promises must have a code gate backing it.

## Doctrine on review

The flagship loop is not complete without a review event. A system that recommends but never asks whether the recommendation helped is not yet an agentic loop.

## Doctrine on legibility

Explanation is product work, not marketing garnish. A smart outsider should be able to understand the project and see why it matters in under two minutes of reading. If the repo cannot be read quickly by a stranger, the work is not yet done.

## Five operating directives

When tradeoffs arise, these dominate in this order:

1. **Conceptual discipline** — words match implementation
2. **Narrowness** — one loop, not many
3. **Inspectability** — state and policy are visible
4. **Boundedness** — actions are low-risk and reversible
5. **Legibility** — an outsider gets it fast

## Links

- [chief_operational_brief_2026-04-16.md](chief_operational_brief_2026-04-16.md) — founder brief, captured 2026-04-16
- [flagship_loop_spec.md](flagship_loop_spec.md) — loop shape + inputs + outputs
- [tour.md](tour.md) — 10-minute guided walkthrough
- [phase_timeline.md](phase_timeline.md) — how the repo got here
- [agent_integration.md](agent_integration.md) — how a Claude agent installs + consumes
- [explicit_non_goals.md](explicit_non_goals.md) — what the project refuses to build
- `skills/recovery-readiness/SKILL.md` — classify state, apply policy, shape recommendation (agent-owned judgment)
- `src/health_agent_infra/validate.py` — code-enforced invariants the runtime guarantees
- `src/health_agent_infra/schemas.py` — typed dataclasses at the tool boundary
- [explicit_non_goals.md](explicit_non_goals.md)
