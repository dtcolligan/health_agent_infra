# HAI Reading Tour

A 10-minute guided read of the HAI reference runtime, for someone
(including future-you) coming back cold. For the repo-wide research
frame, read [`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md) and
[`../../PROJECT_DECISIONS.md`](../../PROJECT_DECISIONS.md), then
[`../../PROJECT_OPERATING_MODEL.md`](../../PROJECT_OPERATING_MODEL.md).
For the HAI operator manual, read
[`hai_reference_runtime.md`](hai_reference_runtime.md).
For exact HAI version, schema head, command count, and release posture, read
[`current_system_state.md`](current_system_state.md) first.

## 1. What you're looking at

Health Agent Infra is the local plugin/runtime wrapper around a
shell-capable personal-health agent, not a health app. The user speaks to
the agent in natural language; the agent operates the local `hai` CLI.
Claude Code is the first compatibility surface, not the architecture
boundary. The package ships two things to the agent:

- **A CLI called ``hai``** with deterministic subcommands for
  pulling evidence, running intake, projecting state, classifying
  per-domain bands, applying R-rules, emitting proposals, running
  synthesis, persisting recommendations, rendering the three-state
  audit chain via `hai explain`, emitting a contract manifest via
  `hai capabilities`, and running evals.
- **A ``skills/`` directory** with fourteen markdown skills — one
  per domain, a synthesis skill, an authoritative `intent-router`
  skill (NL → CLI workflow mapping), an expert-explainer, plus
  cross-cutting (merge-human-inputs, review-protocol, reporting,
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
    plans/                   # roadmap + release/audit plans
    experiments/             # Phase 0.5 / 2.5 throwaway prototypes
verification/
    tests/                   # unit + contract + integration (2943 passed at v0.2.0)
    evals/                   # dev-reference docs + Phase E skill-harness pilot
benchmarks/
    governed_agent_bench/    # benchmark scaffold for contract-governed operation
research/
    runtime_contracts_paper/ # paper frame, draft, execution plan
```

Rule of thumb: if the file is ``.py``, it's code; if it's
``SKILL.md``, it's judgment; if it's under ``verification/tests/``, it
locks an invariant; if it's under ``verification/evals/``, it scores
deterministic runtime behaviour on frozen scenarios.

## 3. Where the thesis lives

- [`architecture.md`](architecture.md) — pipeline diagram,
  code-vs-skill boundary, R-rules + X-rules intro, package layout,
  agent-native surfaces.
- [`non_goals.md`](non_goals.md) — what this project refuses to
  build (no medical device, no hosted product, no ML loop, no
  meal-level nutrition in v1, etc).
- [`x_rules.md`](x_rules.md) — the full cross-domain X-rule
  catalogue, including sentence-form human explanations per rule.
- [`state_model_v1.md`](state_model_v1.md) — table-by-table state
  schema (schema head 028 as of v0.2.0; migrations remain the
  source of truth).
- [`explainability.md`](explainability.md) — `hai explain` and the
  three-state audit bundle (planned → adapted → performed).
- [`agent_cli_contract.md`](agent_cli_contract.md) — generated
  per-command contract manifest the intent-router skill consumes.
- [`../../reporting/plans/tactical_plan_v0_1_x.md`](../../reporting/plans/tactical_plan_v0_1_x.md)
  — HAI runtime backlog and release-history plan. Repo-wide research
  priority lives in [`../../PROJECT_FRAME.md`](../../PROJECT_FRAME.md)
  and [`../../research/runtime_contracts_paper/PAPER_FRAME.md`](../../research/runtime_contracts_paper/PAPER_FRAME.md).
- [`how_to_add_a_domain.md`](how_to_add_a_domain.md) —
  conceptual walk-through for adding a seventh domain; paired with
  the [`domains/README.md`](domains/README.md) checklist.
- [`how_to_add_a_pull_adapter.md`](how_to_add_a_pull_adapter.md) —
  contract for adding a second source adapter under `core/pull/`.

## 4. Where the runtime lives

Six domains, each in ``src/health_agent_infra/domains/<d>/``:

- ``recovery/``, ``running/``, ``sleep/``, ``stress/``,
  ``strength/``, ``nutrition/``

Each ships ``schemas.py`` + ``classify.py`` + ``policy.py`` plus
optional ``signals.py`` / ``intake.py`` / ``taxonomy_match.py``.

Core orchestration in ``src/health_agent_infra/core/``:

- ``synthesis.py`` — ``run_synthesis`` atomic-commit orchestrator.
- ``synthesis_policy.py`` — 11 X-rules: 10 Phase A rules and one
  Phase B adjustment rule.
- ``state/snapshot.py`` — cross-domain bundle the agent reads.
- ``state/projectors/*.py`` — one projector per domain turning raw
  evidence into ``accepted_*_state_daily`` rows.
- ``writeback/proposal.py`` — the `hai propose` determinism
  boundary; `hai synthesize` is the other, inline in
  ``synthesis.py``. (The legacy ``writeback/recommendation.py`` was
  removed in v0.1.4 D2.)

## 5. Where the judgment lives

Fourteen skills in ``skills/``:

- ``recovery-readiness/``  ``running-readiness/``  ``sleep-quality/``
  ``stress-regulation/``  ``strength-readiness/``
  ``nutrition-alignment/`` — one per domain.
- ``daily-plan-synthesis/`` — reconciles proposals via X-rules into
  a coherent daily plan (rationale only; actions are already fixed
  by Phase A before the skill runs).
- ``strength-intake/`` — agent-mediated narration of gym sessions.
- ``merge-human-inputs/`` — hybrid-intake router (shipped in
  Phase 7C.4, retained as-is).
- ``intent-router/`` — maps natural-language user intent to `hai`
  workflows by reading the capabilities manifest.
- ``expert-explainer/`` — read-only explanation over allowlisted local
  sources.
- ``review-protocol/``, ``reporting/``, ``safety/`` — cross-
  cutting.

Skills land in ``~/.claude/skills/`` after ``hai setup-skills``
runs.

## 6. Where the proof lives

``reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/``
captures the original Phase 6 proof pass across all six domains +
synthesis. The packaged eval scenario tree has since grown to 135
deterministic domain/synthesis fixtures plus atomic-claim and factuality
corpora used by v0.2.0.

Pre-rebuild artifacts live under
``reporting/artifacts/archive/`` and no longer reflect the runtime.

The eval framework is **packaged inside the wheel** at
``src/health_agent_infra/evals/``: ``scenarios/<d>/*.json`` are the
authored scenarios, ``runner.py`` executes + scores them, and
``hai eval run`` is the CLI entry point. The dev-reference docs
(``README.md``, ``skill_harness_blocker.md``) still live under
``verification/evals/``.

Deterministic runtime coverage is full. Skill coverage is partial and lives
outside packaged ``hai eval``: ``verification/evals/skill_harness/`` covers
recovery + running readiness replay/live paths, and
``verification/evals/synthesis_harness/`` scores synthesis-skill output
fixtures. See ``verification/evals/skill_harness_blocker.md`` for the
remaining live-capture and LLM-judge gaps.

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
# Evidence — intervals.icu when credentials exist, else the CSV fixture.
hai pull --date 2026-04-18

# Manual inputs (whichever the user reports).
hai intake readiness --soreness low --energy high
hai intake gym --session-json /tmp/session.json
hai intake nutrition --calories 2400 --protein-g 140 --carbs-g 280 --fat-g 75
hai intake stress --score 3
hai intake note --text "new role kicked off; early starts this week"

# Deterministic projection.
hai clean --evidence-json /tmp/evidence.json
hai state reproject

# Snapshot — the cross-domain bundle the agent reads.
hai state snapshot --as-of 2026-04-18 --user-id u_local_1 > /tmp/snapshot.json

# Agent reads snapshot + domain skills, emits one DomainProposal per domain.
hai propose --domain recovery   --proposal-json /tmp/prop_rec.json
hai propose --domain running    --proposal-json /tmp/prop_run.json
# ... one per domain

# Synthesis — Phase A, skill overlay, Phase B, atomic commit.
hai synthesize --as-of 2026-04-18 --user-id u_local_1

# Review scheduled automatically; record outcomes next morning.
hai review record --outcome-json /tmp/outcome_recovery.json
hai review summary --domain recovery
```

## 8. What's intentionally not here

- No ML / learning loop. ``hai review summary`` counts; it does not
  tune.
- No broad wearable marketplace. intervals.icu is the supported live source;
  Garmin Connect live scraping is best-effort and not the default.
- No meal-level nutrition, no food taxonomy, no micronutrient
  inference. See ``non_goals.md`` for why (Phase 2.5 retrieval
  gate).
- No mobile / voice / hosted UI.
- No multi-user (schema has ``user_id`` but always resolves to one
  local user).
- No complete skill-narration eval harness across all domains or live CI.
  Current coverage is the recovery/running pilot plus the synthesis-output
  scorer under ``verification/evals/``.

## 9. Reading paths by question

| Question | Start at |
|---|---|
| "What is this project?" | [architecture.md](architecture.md) |
| "How are X-rules scoped?" | [x_rules.md](x_rules.md) |
| "What's in the state DB?" | [state_model_v1.md](state_model_v1.md) |
| "How do I add a domain?" | [how_to_add_a_domain.md](how_to_add_a_domain.md) |
| "How do I add a pull adapter?" | [how_to_add_a_pull_adapter.md](how_to_add_a_pull_adapter.md) |
| "Why is feature X not included?" | [non_goals.md](non_goals.md) |
| "How does an agent install this?" | [agent_integration.md](agent_integration.md) |
| "Is it tested?" | ``verification/tests/`` plus the latest release gate in [current_system_state.md](current_system_state.md) |
| "Does it have evals?" | ``verification/evals/`` + ``hai eval run --domain <d>`` |
| "Does it run on live wearable data?" | ``hai auth intervals-icu`` then ``hai pull --source intervals_icu`` |
| "How did we get here?" | [AUDIT.md](../../AUDIT.md) + release folders under ``reporting/plans/`` |

## 10. One honest caveat

This is a personal-use runtime. It is published and installable, but
still single-user, local-first, non-clinical, and intentionally narrow.
Its audience is an agent driving one user's health state through a
bounded, auditable pipeline. If a section of the docs stops matching
the code, the likely cause is drift — trust the generated CLI
capabilities, migrations, tests, and current-system-state doc over
older prose, then update the docs.
