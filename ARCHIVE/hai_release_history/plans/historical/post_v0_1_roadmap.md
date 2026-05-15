# Post-v0.1.0 Execution Plan

- Author: Codex
- Date: 2026-04-19
- Status: **superseded by [`agent_operable_runtime_plan.md`](agent_operable_runtime_plan.md) (M8 cycle).** Phases A–E complete, F/G deferrable (statuses updated inline below).
- Starting point: `main @ f220c5d`
- Prior checkpoint: `v0.1.0` shipped; Phase A truth-alignment complete

> **M8 update (2026-04-22):** Phases A, B, C, D shipped as originally
> scoped. Phase E (skill-harness pilot) was substantially resolved
> by the work described in
> [`safety/evals/skill_harness_blocker.md`](../../safety/evals/skill_harness_blocker.md);
> M8 Phase 4 expanded reference-transcript coverage from 3 to 6 of 7
> recovery branches. Phases F (grounded expert prototype) and G
> (extension-path docs) remain deferrable; their deliverables are
> unchanged and can be picked up in a future cycle if prioritised.
> The M8 cycle itself added new phases not contemplated here:
> planned-recommendation ledger (three-state audit), agent CLI
> contract manifest + full exit-code migration, sentence-form X-rule
> explanations, and the authoritative `intent-router` skill. See
> [`agent_operable_runtime_plan.md`](agent_operable_runtime_plan.md)
> for the full cycle.

This document is the next-cycle master plan after the rebuild and
`v0.1.0` release. It keeps the same execution discipline as the
comprehensive rebuild plan, but it is intentionally smaller in scope.

The architecture is now fundamentally sound. The next cycle is not
another rebuild. It is a focused extension cycle over the shipped
local-first, governed runtime.

---

## 1. Executive summary

Health Agent Infra has already shipped the hard part:

- six-domain governed runtime
- deterministic classify / policy / synthesis logic in code
- judgment surfaces in skills
- atomic SQLite persistence
- review loop
- packaged CLI
- deterministic eval harness

The immediate post-release audit found surface-truth gaps, and **Phase A**
closed them at `main @ f220c5d`:

- `hai eval` is now a real packaged surface
- `hai synthesize --bundle-only` is real and documented
- `hai writeback` is honestly framed as the recovery-only legacy direct
  path
- the docs now distinguish `hai daily` from the two-pass synthesis flow
- deterministic eval claims are phrased honestly

So the next cycle should not ask "what is broken?" It should ask
"what should this runtime become next?"

The answer is:

1. Make the shipped system easier to explain.
2. Turn the existing audit chain into a first-class explainability
   surface.
3. Add explicit user memory as inspectable local state.
4. Close the biggest remaining evaluation gap: real skill-harness
   evaluation.
5. Only then add a read-only grounded expert layer.
6. Document the extension seams once the post-v0.1 shape is stable.

This plan uses Google Research's
[*The anatomy of a personal health agent*](https://research.google/blog/the-anatomy-of-a-personal-health-agent/)
as a lens for role separation, memory, and evaluation maturity. It does
not replace the current architecture with a new multi-agent design.

---

## 2. Current state and closed debt

### 2.1 What is already done

The following items are **closed** and should not be reopened as if they
are still active defects:

1. Packaged `hai eval` truth gap
2. Phantom `--bundle-only` skill instruction
3. `hai writeback` scope ambiguity
4. `hai daily` vs `hai synthesize --drafts-json` docs confusion
5. Deterministic eval headline phrasing drift
6. The concrete CLI/docs drift fixed in Phase A

### 2.2 What remains genuinely open

The next-cycle open work is now:

1. Positioning / role-map / query-taxonomy / memory-model docs
2. Explainability as a supported CLI surface
3. Explicit user memory tables and write surfaces
4. Skill-harness eval pilot
5. Grounded expert prototype under explicit source/privacy rules
6. Extension-path docs for adapters and domains

### 2.3 What is still opinionated future work

These are plausible later bets, but they are not next-cycle essentials:

1. Adaptive learning loop from review outcomes
2. Apple Health or a second wearable adapter
3. MCP wrapper
4. Meal-level nutrition re-gate
5. Hosted / multi-user surfaces

---

## 3. Locked decisions

### 3.1 Architecture

| # | Decision |
|---|---|
| 1 | **Keep the current code-vs-skill boundary.** Runtime code owns projection, classification, policy, synthesis, validation, and persistence. Skills own rationale, uncertainty surfacing, and clarifying questions only. |
| 2 | **Keep SQLite as the primary memory system.** New memory work extends explicit local state, not hidden chat memory or an opaque retrieval store. |
| 3 | **Keep nutrition macros-only.** No meal-level retrieval, USDA import, or food taxonomy work in this cycle. |
| 4 | **Do not add a learning loop yet.** User memory may inform context, but it must not silently retune thresholds or policy behavior in this cycle. |
| 5 | **Grounded explanation is read-only first.** A grounded expert may explain and cite, but it may not mutate recommendations in this cycle. |
| 6 | **Do not replace the current orchestration model.** `hai daily`, `hai synthesize`, and the current audit chain remain the spine of the system. |
| 7 | **Evaluation stays first-class.** New agent-facing surfaces should not outrun the project’s ability to evaluate them honestly. |
| 8 | **No second adapter implementation yet.** Document the seam first; do not broaden product scope before the seam is clear. |
| 9 | **MCP remains optional.** It may be revisited later, but it is not required for this cycle to succeed. |

### 3.2 Product framing

The system should now be described as four cooperating layers:

1. **Runtime analyst**
   Pull, clean, project, classify, policy, synthesis, persistence.
2. **Coach**
   Domain readiness skills, synthesis skill, human-facing judgment.
3. **Memory**
   Accepted state, proposals, plans, reviews, and future explicit user
   memory.
4. **Grounded expert**
   Future read-only explainer / research layer.

This is a framing improvement, not a runtime rewrite.

### 3.3 Source and privacy policy for future grounding

Any grounded-expert work in this cycle must obey:

1. read-only only; never inside recommendation mutation
2. explicit allowlist of source classes
3. claim must cite or abstain
4. no silent retrieval inside `hai daily`, `hai synthesize`, or policy
5. any off-device context send must be explicit and operator-initiated

---

## 4. Target architecture for the next cycle

The current shipped runtime remains the base:

```text
pull / intake
    ↓
projectors
    ↓
accepted_*_state_daily
    ↓
hai state snapshot
    ↓
domain proposals
    ↓
synthesis
    ↓
daily_plan + x_rule_firing + recommendation_log
    ↓
review_event + review_outcome
```

The next-cycle additions should be:

```text
accepted state ───────┐
                      ├── hai explain
proposal_log ─────────┤
x_rule_firing ────────┤
recommendation_log ───┘

user writes ──> hai memory ... ──> explicit user memory tables
                                      │
                                      ├── visible in snapshot
                                      ├── visible in explain
                                      └── available as bounded context

deterministic evals ──> remain default, packaged, CI-friendly
skill-harness evals ──> small opt-in pilot over a real skill path

grounded expert ──> read-only explanation layer with citations
```

Expected new top-level additions:

1. `hai explain`
2. explicit user-memory tables and CLI
3. first real skill-harness pilot
4. read-only grounded expert prototype
5. better positioning and extension docs

---

## 5. Phases

### Phase A — Truth alignment (complete)

**Status**: complete at `main @ f220c5d`

This phase is closed. It fixed the audit’s first-contact surface-truth
issues and established the new starting point for the cycle.

---

### Phase B — Positioning, query taxonomy, and memory-model docs

**Goal**: make the shipped system legible without changing runtime
behavior.

**Why now**:

The repo is stronger than its conceptual docs. Before adding new
surfaces, the project needs crisp vocabulary for:

- what the runtime does
- what “memory” means here
- what kinds of user questions the system is actually built to answer

**Deliverables**:

1. `reporting/docs/personal_health_agent_positioning.md`
   - role map: runtime analyst / coach / memory / grounded expert
   - relation to the Google PHA framing
   - why this project is local-first and governed

2. `reporting/docs/query_taxonomy.md`
   - current state understanding
   - action planning
   - explanation / audit
   - longitudinal review
   - grounded topic explanation
   - human-input routing

3. `reporting/docs/memory_model.md`
   - raw evidence memory
   - accepted state memory
   - decision memory
   - outcome memory
   - explicit user memory (future in this plan)
   - absent adaptive memory

4. Tight alignment updates only where needed:
   - [README.md](/Users/domcolligan/Documents/health_agent_infra/README.md)
   - [reporting/docs/architecture.md](/Users/domcolligan/Documents/health_agent_infra/reporting/docs/architecture.md)
   - [reporting/docs/agent_integration.md](/Users/domcolligan/Documents/health_agent_infra/reporting/docs/agent_integration.md)

**Acceptance criteria**:

1. A new reader can explain the system without inventing:
   - chat-memory assumptions
   - voice-note product assumptions
   - “general AI coach” assumptions
2. The local-first memory story is explicit and consistent.
3. The role split is described consistently across active docs.
4. The docs are good enough to serve as reference material for later
   phases.

**Effort estimate**: 2–3 days

**Dependencies / sequencing**:

- none
- this phase should happen first

---

### Phase C — Explainability as a first-class surface

**Goal**: expose the existing audit chain as a supported, read-only CLI
surface for users and agents.

**Why now**:

The project’s strongest differentiator is not just “it stores state.” It
stores an auditable chain:

- accepted state
- proposals
- X-rule firings
- final recommendations
- supersession links
- review records

Right now that value is real but too hidden. This phase turns it into a
product surface.

**Deliverables**:

1. `hai explain`
   - likely forms:
     - `hai explain --for-date <d> --user-id <u>`
     - `hai explain --daily-plan-id <id>`
   - JSON and human-readable output

2. Explainability support code
   - `src/health_agent_infra/core/explain/queries.py`
   - `src/health_agent_infra/core/explain/render.py`
   - or similarly bounded modules

3. Explainability docs
   - `reporting/docs/explainability.md`

4. Focused tests
   - `safety/tests/test_cli_explain.py`
   - end-to-end explain test over a synthesized plan

**Acceptance criteria**:

1. `hai explain` is read-only.
2. It can reconstruct, from persisted state only:
   - proposals used
   - X-rule firings
   - final recommendations
   - supersession linkage
   - review linkage if present
3. At least one canonical six-domain plan can be explained end to end.
4. The output is good enough for both a human operator and a future agent
   to inspect why the plan exists.

**Effort estimate**: 4–6 days

**Dependencies / sequencing**:

- Phase B first
- should land before explicit user memory, so memory can plug into an
  existing explain surface

---

### Phase D — Explicit user memory (shipped)

**Status**: shipped. Migration 007 creates the `user_memory` table;
`src/health_agent_infra/core/memory/` owns the schemas / store /
projector; `hai memory set|list|archive` is the canonical CLI;
`hai state snapshot` and `hai explain` each expose a new top-level
`user_memory` key. Tests live at `safety/tests/test_user_memory.py`
and `safety/tests/test_cli_memory.py`.

**Goal**: persist goals, preferences, constraints, and durable context as
explicit local state instead of implicit prompt context.

**Why now**:

This is the right next form of “memory” for the project:

- local
- inspectable
- scriptable
- auditable

It deepens the product without sliding into opaque adaptation.

**Deliverables**:

1. Migration 007
   - add user-memory tables for:
     - goals
     - preferences
     - constraints
     - durable context notes

2. Core memory module
   - `src/health_agent_infra/core/memory/schemas.py`
   - `src/health_agent_infra/core/memory/store.py`
   - `src/health_agent_infra/core/memory/projector.py`

3. Memory CLI
   - choose one canonical surface
   - recommended:
     - `hai memory set`
     - `hai memory list`
     - `hai memory archive`
   - include JSON output where appropriate

4. Snapshot / explain exposure
   - bounded user-memory state appears in:
     - `hai state snapshot`
     - `hai explain`

5. Focused tests
   - `safety/tests/test_user_memory.py`
   - `safety/tests/test_cli_memory.py`

**Acceptance criteria**:

1. User memory is stored locally in SQLite.
2. Memory can be created, listed, and archived without manual SQL.
3. Memory is visible in snapshot and explain output.
4. No hidden policy/X-rule adaptation is introduced.
5. No write-surface bypass is introduced.

**Effort estimate**: 1–1.5 weeks

**Dependencies / sequencing**:

- Phase C first
- memory in this phase is **read-only context**, not adaptive behavior

---

### Phase E — Skill-harness eval pilot

**Goal**: build a small but real harness that invokes an actual skill path
and scores more than deterministic runtime outputs.

**Why now**:

This is the biggest remaining credibility gap. Deterministic evals are
real and useful, but they do not yet score:

- real skill invocation
- narration quality
- skill-mediated adherence to the written boundary

That gap should be narrowed before more agent-facing capability is added.

**Deliverables**:

1. Pilot harness
   - `safety/evals/skill_harness/runner.py`

2. Pilot scenarios
   - `safety/evals/skill_harness/scenarios/recovery/...`

3. Pilot rubric
   - `safety/evals/skill_harness/rubrics/recovery.md`

4. Execution note / RFC
   - `reporting/plans/historical/skill_harness_rfc.md`

5. Update blocker doc
   - refine [skill_harness_blocker.md](/Users/domcolligan/Documents/health_agent_infra/safety/evals/skill_harness_blocker.md)
     into what is resolved vs what remains blocked

**Recommended initial scope**:

1. one domain: recovery
2. one skill: `recovery-readiness`
3. 5–10 frozen scenarios
4. score:
   - bounded action correctness
   - rationale quality

**Acceptance criteria**:

1. At least one real skill path is exercised end to end.
2. Rationale quality is scored by an explicit rubric.
3. Pilot reporting separates:
   - deterministic correctness
   - narration/rationale quality
4. The pilot is opt-in and does not destabilize normal CI yet.

**Effort estimate**: 1–2 weeks

**Dependencies / sequencing**:

- Phase B first for framing
- Phase D preferred before this phase if user memory will soon be part of
  skill context
- must land before grounded expert work becomes more than a doc

---

### Phase F — Grounded expert prototype

**Goal**: add a read-only explanation/research layer that can answer
bounded health-topic or recommendation-context questions with citations.

**Why now**:

This is where the Google PHA framing is genuinely useful, but it should
come only after the project has:

- better language for what it is
- a stronger explainability surface
- a first skill-harness eval foothold

**Deliverables**:

1. Scope / policy doc
   - `reporting/docs/grounded_expert_scope.md`
   - source classes
   - privacy rules
   - citation policy
   - explicit out-of-scope list

2. Research / retrieval module
   - `src/health_agent_infra/core/research/sources.py`
   - `src/health_agent_infra/core/research/retrieval.py`

3. Read-only skill
   - `src/health_agent_infra/skills/expert-explainer/SKILL.md`

4. Initial eval scenarios
   - `safety/evals/scenarios/expert/...`

**Questions in scope**:

1. “What does elevated sleep debt mean in this system?”
2. “Why would low protein soften strength?”
3. “What does body battery measure?”

**Out of scope**:

1. symptom triage
2. diagnosis
3. recommendation mutation
4. hidden retrieval inside synthesis or `hai daily`

**Acceptance criteria**:

1. The prototype answers bounded explainer questions with citations.
2. Every substantive claim either cites or abstains.
3. Retrieval behavior follows the explicit allowlist and privacy rules.
4. No action mutation enters the runtime through this layer.

**Effort estimate**: 1–1.5 weeks

**Dependencies / sequencing**:

- Phase E first
- should remain read-only through the full phase

---

### Phase G — Extension-path documentation

**Goal**: make the next contributor path clearer than the last one was.

**Why now**:

Once the post-v0.1.x shape is stable, the most useful thing the project
can do for future contributors is document one or two clean extension
paths.

**Deliverables**:

1. Pull-adapter extension doc
   - `reporting/docs/how_to_add_a_pull_adapter.md`
   - adapter contract
   - evidence shape
   - projection expectations
   - required tests
   - definition of done

2. Domain-extension doc
   - `reporting/docs/how_to_add_a_domain.md`

**Acceptance criteria**:

1. A contributor can understand how to add a second wearable adapter
   without reverse-engineering the repo.
2. A contributor can understand the minimum contract for adding a new
   domain.

**Effort estimate**: 2–4 days

**Dependencies / sequencing**:

- last in the main cycle
- should describe the stabilized post-v0.1.x system, not a moving target

---

## 6. Must-fix, deferrable, and later

### 6.1 Next-cycle essentials

These should define the cycle:

1. Phase B — positioning / taxonomy / memory docs
2. Phase C — explainability CLI
3. Phase D — explicit user memory
4. Phase E — skill-harness eval pilot

### 6.2 Important but deferrable

These are valuable, but the cycle can still succeed if they slip:

1. Phase F — grounded expert prototype
2. Phase G — extension-path docs
3. dedicated scenario-pack expansion for X4 / X5 / X6b

### 6.3 Later bets / optional work

These should not quietly enter the next cycle:

1. adaptive learning loop
2. Apple Health or another live second adapter
3. MCP wrapper
4. meal-level nutrition re-gate
5. hosted / multi-user product surfaces

---

## 7. Why this order

1. **Docs before new surfaces**
   The project now needs shared vocabulary more than it needs another
   capability spike. Phase B prevents future work from being described
   sloppily.

2. **Explainability before deeper memory**
   The audit chain is already the strongest latent product asset. Making
   it explorable is lower risk and higher trust than jumping straight to
   new agent capability.

3. **Explicit user memory before adaptive behavior**
   Goals, preferences, and constraints should exist as inspectable local
   data before they influence anything more ambitious.

4. **Skill-harness eval before grounded expert**
   The project’s main remaining proof gap is still skill-mediated
   behavior. A grounded expert increases agent-facing surface area, so it
   should come after the first real harness exists.

5. **Extension docs after the shape stabilizes**
   Contributors should learn the post-v0.1.x architecture, not an
   in-between version.

---

## 8. Definition of success for the next cycle

This cycle is successful if the following become true:

1. The project has a clear positioning doc, query taxonomy, and memory
   model.
2. `hai explain` exists and can reconstruct a plan from persisted state.
3. Explicit user memory exists as local SQLite state with a real CLI.
4. At least one real skill path is evaluated by a pilot harness.
5. A grounded expert prototype exists only if it stays read-only,
   cited, and policy-bounded.
6. Extension seams are documented well enough that a new adapter or
   domain can be added without another repo-wide archaeology pass.

---

## 9. Explicit non-goals for this cycle

Do not broaden this cycle into:

1. another rebuild-scale architecture rewrite
2. meal-level nutrition / USDA / food taxonomy productization
3. symptom triage or diagnosis
4. hidden adaptive learning from chat or review outcomes
5. grounded retrieval that mutates recommendations
6. a second live wearable adapter implementation
7. hosted or multi-user surfaces
8. MCP as a required deliverable

---

## 10. Recommended first execution prompt

Start with **Phase B only**.

Reason:

- Phase A is done
- the architecture is stable
- Phase B gives the repo the language it needs before new runtime surface
  work lands

The next Claude Code session should therefore:

1. verify `main @ f220c5d`
2. read this plan plus the active architecture docs
3. execute Phase B only
4. stop at a clean checkpoint and summarize what Phase C should start
   from
