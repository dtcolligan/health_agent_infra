# Personal Health Agent Positioning

This document names what Health Agent Infra is, how it relates to the
broader "personal health agent" idea as framed by Google Research, and
why its shape is deliberately local-first and governed.

It is a framing document, not an architecture rewrite. The shipped
architecture is described in
[`architecture.md`](architecture.md); the cross-domain rule catalogue
in [`x_rules.md`](x_rules.md); the scope discipline in
[`non_goals.md`](non_goals.md).

## 1. The one-sentence frame

Health Agent Infra is a **governed local runtime** that lets one Claude
agent reason across six health domains with deterministic tools, typed
contracts, and auditable persisted state, so that the agent's
recommendations are bounded, explainable, and resumable across days.

"Governed" means:

- every action the agent can recommend is drawn from a fixed,
  schema-validated enum per domain;
- every cross-domain mediation (X-rules) runs in code, not in the
  agent's head;
- every firing, mutation, and final recommendation is persisted to a
  local SQLite database inside a single atomic transaction;
- every determinism boundary (`hai propose`, `hai synthesize`)
  rejects invalid payloads with a named `invariant` id rather than
  silently coercing them.

"Local" means:

- the source of truth is a SQLite database on the user's machine;
- wearable credentials live in the OS keyring;
- nothing is synced to a hosted service in v1;
- a single local `user_id` is the entire tenant model.

## 2. Role map

The shipped system is usefully described as four cooperating roles, not
as one monolith. This map is a framing tool — the roles are not separate
processes, and only the first two have runtime surface today.

| Role | What it owns | Where it lives |
|---|---|---|
| **Runtime analyst** | Pull, clean, project, classify, policy, synthesis mutation, persistence. All deterministic. | Python code under `src/health_agent_infra/core/` + `domains/<d>/` |
| **Coach** | Composing rationale for an already-fixed action, surfacing uncertainty, asking clarifying questions during narration. Judgment only. | Markdown skills under `src/health_agent_infra/skills/` |
| **Memory** | Raw evidence, accepted per-domain state, proposals, plans, firings, recommendations, reviews. | Local SQLite + per-domain JSONL audits |
| **Grounded expert** | Read-only topic explanation with citations (e.g. "what does sleep debt mean in this system?"). | **Not shipped in v0.1.0.** Planned under post-v0.1 Phase F. |

Two rules hold across the map:

1. **The runtime analyst is the only role that mutates state.** Coach
   skills never change an action and never run arithmetic the runtime
   already ran. Memory is written by the runtime as a side effect of
   `propose` / `synthesize` / `writeback` / `review`.
2. **Memory is inspectable.** Everything the memory role holds is a
   SQLite row or an append-only JSONL line on the user's disk. Nothing
   important lives only in an agent chat transcript.

The memory role is documented in detail in
[`memory_model.md`](memory_model.md); the coach/runtime split is
documented in [`architecture.md`](architecture.md) under "Code-vs-skill
boundary".

## 3. Relation to the Google PHA framing

Google Research's *The anatomy of a personal health agent*
(research.google/blog, September 30 2025) proposes a multi-agent
architecture for personal health assistance: a data-science agent, a
domain-expert agent, and a health-coach agent, orchestrated together.

Health Agent Infra uses that paper as a **lens for role separation and
evaluation maturity**, not as an architecture to copy. Concretely:

| Google PHA | Health Agent Infra v0.1.x |
|---|---|
| Multi-agent (data-science / domain-expert / coach) | Single Claude agent with typed tools + markdown skills + governed state |
| Role specialization inside the agent system | Role specialization inside the **typed-tool + skill + state** system |
| Coaching is a peer agent | Coaching is a skill the one agent loads, constrained by the runtime's already-fixed action set |
| Expert grounding is a first-class agent | Grounded expert is read-only, not shipped in v0.1.0, planned as Phase F |
| Evaluation is multi-level across agents | Evaluation is deterministic today; skill-harness eval is Phase E |

Two lessons we take forward from the PHA framing:

- **Clearer role separation.** Even without multi-agent orchestration,
  the runtime/coach/memory/expert distinction is a sharper vocabulary
  than "the agent."
- **Multi-level evaluation.** Deterministic runtime scoring is not the
  same as skill-mediated behavior scoring. Phase E (skill-harness pilot)
  exists because the PHA framing makes that gap hard to ignore.

Three lessons we explicitly do **not** take:

- We do not split the agent into multiple coordinating agents. A single
  Claude agent reads skills and calls typed CLI tools. The "multi-agent"
  surface is replaced by `hai propose` + `hai synthesize` +
  `x_rule_firing`.
- We do not let a grounded expert mutate recommendations. Any Phase F
  expert layer is read-only; recommendation mutation remains a
  runtime/synthesis responsibility.
- We do not adopt "agent memory" as a hidden retrieval surface. Memory
  here is explicit local SQLite, not opaque embeddings or unbounded
  chat history.

## 4. Why local-first and governed

The architecture is shaped by three things a personal health agent
must survive in the wild:

1. **The user should be able to inspect anything the agent remembers
   about them.** If the agent's durable memory is a SQLite database on
   the user's disk and a small set of JSONL audit files, then `sqlite3`
   and `cat` are enough to audit it. There is no opaque vector store
   and no hidden server-side user profile.
2. **Recommendations must be resumable across days without depending on
   chat state.** Morning `N+1` should be able to plan from yesterday's
   accepted state, proposals, plan, firings, and review outcomes —
   entirely from the local database — even if the agent has no memory
   of the previous conversation. This is why accepted state,
   `proposal_log`, `daily_plan`, `x_rule_firing`, and
   `recommendation_log` exist as first-class tables.
3. **Judgment must stay bounded.** The runtime owns the decision
   *space* (which actions are possible for a given domain given the
   state). Skills own judgment *within* that space (why this one,
   worded this way, with what uncertainty). This is what "governed"
   means in practice: the coach can be wrong about rationale, but it
   cannot invent an action the runtime did not already permit.

Local-first and governed are mutually reinforcing:

- Local state makes the audit chain cheap, which makes governance
  credible.
- Governance makes local state honest, because every row has a
  well-defined author (projector, synthesis, review) and every
  determinism boundary refuses to corrupt it.

The scope cost is explicit. Because the runtime is local-first:

- it does not have a hosted control plane, so multi-user features are
  out of scope;
- it does not have cloud retrieval, so grounded explanations have to
  come from a bounded allowlist when Phase F ships;
- it does not have a fleet-telemetry surface, so learning-loop work
  (if ever scoped) would have to be a per-user local loop, not an
  aggregate one.

See [`non_goals.md`](non_goals.md) for the full scope discipline.

## 5. Where this framing belongs in the docs

For a new reader, this document's job is to prevent three specific
misreadings:

- Reading the repo as a "general AI health coach" or chatbot. It is
  not. It is a governed runtime that a coaching agent drives.
- Reading memory as chat memory. It is not. Memory here is explicit
  local tables documented in [`memory_model.md`](memory_model.md).
- Reading the Google PHA paper as a template the repo implements. It
  is not. The paper is used as a lens for roles and evaluation, not as
  an architecture.

If a later doc, skill, or commit message drifts away from these framings,
this doc is the anchor to pull back to.
