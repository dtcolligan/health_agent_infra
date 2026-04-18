# Reading Tour

A 10-minute guided read of the v1 multi-domain runtime, for someone
(including future-you) coming back cold.

## 1. What you're looking at

Health Agent Infra is **agent infrastructure**, not a health app. It
ships two things to an agent like Claude Code:

- **A CLI called ``hai``** with deterministic subcommands for
  pulling evidence, running intake, projecting state, classifying
  per-domain bands, applying R-rules, emitting proposals, running
  synthesis, persisting recommendations, and running evals.
- **A ``skills/`` directory** with twelve markdown skills — one per
  domain plus a synthesis skill and a handful of cross-cutting
  skills (merge-human-inputs, writeback-protocol, reporting,
  safety).

The runtime owns deterministic work (arithmetic, mechanical
policy, X-rule mutation application, atomic transactions). Skills
own judgment (picking from an already-constrained action set,
composing rationale, surfacing uncertainty). The code-vs-skill line
is tight — see [``architecture.md``](architecture.md) §code-vs-skill.

## 2. How to orient the repo

```
src/health_agent_infra/
    cli.py                   # `hai` dispatcher
    core/                    # schemas, validate, config, synthesis, state
    domains/                 # per-domain schemas + classify + policy + intake
        recovery/  running/  sleep/  stress/  strength/  nutrition/
    skills/                  # markdown packaged with the wheel
reporting/
    docs/                    # this tour + architecture + x_rules + ...
    artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/
    plans/                   # rebuild plan + Phase 2.5 gates
    experiments/             # Phase 0.5 / 2.5 throwaway prototypes
safety/
    tests/                   # unit + contract + integration (1200+)
    evals/                   # Phase 6 eval framework (28 scenarios)
```

Rule of thumb: if the file is ``.py``, it's code; if it's
``SKILL.md``, it's judgment; if it's under ``safety/tests/``, it
locks an invariant; if it's under ``safety/evals/``, it scores
deterministic runtime behaviour on frozen scenarios.

## 3. Where the thesis lives

- [`architecture.md`](architecture.md) — pipeline diagram,
  code-vs-skill boundary, R-rules + X-rules intro, package layout.
- [`non_goals.md`](non_goals.md) — what this project refuses to
  build (no medical device, no hosted product, no ML loop, no
  meal-level nutrition in v1, etc).
- [`x_rules.md`](x_rules.md) — the full cross-domain X-rule
  catalogue.
- [`state_model_v1.md`](state_model_v1.md) — table-by-table state
  schema.
- [`domains/README.md`](domains/README.md) — "how to add a domain"
  recipe.

## 4. Where the runtime lives

Six domains, each in ``src/health_agent_infra/domains/<d>/``:

- ``recovery/``, ``running/``, ``sleep/``, ``stress/``,
  ``strength/``, ``nutrition/``

Each ships ``schemas.py`` + ``classify.py`` + ``policy.py`` plus
optional ``signals.py`` / ``intake.py`` / ``taxonomy_match.py``.

Core orchestration in ``src/health_agent_infra/core/``:

- ``synthesis.py`` — ``run_synthesis`` atomic-commit orchestrator.
- ``synthesis_policy.py`` — ten X-rule evaluators across Phase A
  and Phase B.
- ``state/snapshot.py`` — cross-domain bundle the agent reads.
- ``state/projectors/*.py`` — one projector per domain turning raw
  evidence into ``accepted_*_state_daily`` rows.
- ``writeback/proposal.py`` + ``writeback/recommendation.py`` —
  the three determinism boundaries.

## 5. Where the judgment lives

Twelve skills in ``skills/``:

- ``recovery-readiness/``  ``running-readiness/``  ``sleep-quality/``
  ``stress-regulation/``  ``strength-readiness/``
  ``nutrition-alignment/`` — one per domain.
- ``daily-plan-synthesis/`` — reconciles proposals via X-rules into
  a coherent daily plan (rationale only; actions are already fixed
  by Phase A before the skill runs).
- ``strength-intake/`` — agent-mediated narration of gym sessions.
- ``merge-human-inputs/`` — hybrid-intake router (shipped in
  Phase 7C.4, retained as-is).
- ``writeback-protocol/``, ``reporting/``, ``safety/`` — cross-
  cutting.

Skills land in ``~/.claude/skills/`` after ``hai setup-skills``
runs.

## 6. Where the proof lives

``reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/``
captures a complete pass of the Phase 6 eval runner across all six
domains + synthesis: 28 scenarios, all green.

Pre-rebuild artifacts live under
``reporting/artifacts/archive/`` and no longer reflect the runtime.

``safety/evals/scenarios/<d>/*.json`` are the authored scenarios;
``safety/evals/runner.py`` executes + scores them; ``hai eval run``
is the CLI entry point.

Deterministic runtime coverage is full. Skill-narration coverage is
explicitly NOT scored — see
``safety/evals/skill_harness_blocker.md`` for the blockers.

## 7. How to use it

Install:

```bash
pip install -e .
hai setup-skills
```

Set up the state DB:

```bash
hai state init
```

A daily run from the agent's perspective:

```bash
# Evidence — pull Garmin (CSV fixture by default; --live uses keyring).
hai pull --date 2026-04-18

# Manual inputs (whichever the user reports).
hai intake readiness --soreness low --energy high
hai intake gym --session-json /tmp/session.json
hai intake nutrition --calories 2400 --protein-g 140 --carbs-g 280 --fat-g 75
hai intake stress --score 3
hai intake note --text "new role kicked off; early starts this week"

# Deterministic projection.
hai clean --evidence-json /tmp/evidence.json
hai state reproject --scope all

# Snapshot — the cross-domain bundle the agent reads.
hai state snapshot --as-of 2026-04-18 --user-id u_local_1 > /tmp/snapshot.json

# Agent reads snapshot + domain skills, emits one DomainProposal per domain.
hai propose --domain recovery   --proposal-json /tmp/prop_rec.json
hai propose --domain running    --proposal-json /tmp/prop_run.json
# ... one per domain

# Synthesis — Phase A, skill overlay, Phase B, atomic commit.
hai synthesize --as-of 2026-04-18 --user-id u_local_1

# Review scheduled automatically; record outcomes next morning.
hai review record --outcome-json /tmp/outcome_recovery.json --domain recovery
hai review summary --domain recovery
```

## 8. What's intentionally not here

- No ML / learning loop. ``hai review summary`` counts; it does not
  tune.
- No second wearable. Garmin only in v1.
- No meal-level nutrition, no food taxonomy, no micronutrient
  inference. See ``non_goals.md`` for why (Phase 2.5 retrieval
  gate).
- No mobile / voice / hosted UI.
- No multi-user (schema has ``user_id`` but always resolves to one
  local user).
- No skill-narration eval harness (Phase 2.5 Track B Condition 3
  remains deferred).

## 9. Reading paths by question

| Question | Start at |
|---|---|
| "What is this project?" | [architecture.md](architecture.md) |
| "How are X-rules scoped?" | [x_rules.md](x_rules.md) |
| "What's in the state DB?" | [state_model_v1.md](state_model_v1.md) |
| "How do I add a domain?" | [domains/README.md](domains/README.md) |
| "Why is feature X not included?" | [non_goals.md](non_goals.md) |
| "How does an agent install this?" | [agent_integration.md](agent_integration.md) |
| "Is it tested?" | ``safety/tests/`` (1200+ tests) |
| "Does it have evals?" | ``safety/evals/`` + ``hai eval run --domain <d>`` |
| "Does it run on real Garmin data?" | ``hai pull --live`` after ``hai auth garmin`` |
| "How did we get here?" | Git log on ``rebuild`` branch |

## 10. One honest caveat

This is a personal-use runtime. Not hosted, not multi-user, not
clinical, not polished for general install. Its audience is a
Claude agent driving a single user's daily health signals through a
bounded, auditable pipeline. If a section of the docs stops matching
the code, the likely cause is drift — trust the code + tests + git
log over the docs, and update the docs.
