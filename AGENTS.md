# AGENTS.md

Operating contract for AI coding agents in this repo. The active
research scope, calendar, hypotheses, mechanism inventory, model roster,
and decisions live in `PAPER.md`. Read `PAPER.md` first.

## North Star

This repo exists to ship one artifact: the arXiv preprint
*Deterministic Software Contracts as Trusted Monitors in AI Control
Protocols* by 2026-09-30, with GovernedAgentBench v1.0 released beside
it.

The project is not a HAI product roadmap. HAI is the pinned reference
runtime used to instantiate and test the paper's runtime-contract
mechanisms.

## How We Work

Multiple AI coding agents work this repo in parallel. You are not the
only agent here. Treat this section as binding context for every turn.

**Roles.** Dom drives. Agents are workers, not deciders. Dom authorizes
every commit, push, scope change, and research measurement. Agents
propose; Dom accepts or redirects.

**Implementer / auditor pattern.** Most work moves through two agents:
one implements a packet, then a different agent audits the work before
any commit. The auditing agent re-derives facts rather than echoing the
implementer's summary — re-read the changed files, re-run the
verification the implementer claimed, check that the brief was
followed, and flag any out-of-scope or surprising changes. The audit's
job is to disagree where disagreement is warranted.

**Trust but verify.** A handoff summary describes what the implementer
*intended* to do, not necessarily what they did. Always confirm by
reading the files and re-running tests yourself.

**Shared-tree etiquette.**

- If the working tree contains uncommitted changes you did not make
  this session, treat them as outside your scope. Stage only what you
  authored and flag the rest to Dom before any commit.
- If a file you need to change is also being edited by another agent,
  pause and coordinate via Dom rather than stomping.
- Do not extend scope silently. If you find work that needs doing
  outside your brief, surface it; do not just do it.

**Commits and pushes.** Agents never push autonomously and never commit
without explicit user authorization. When authorized, drive the
terminal — do not print commands for Dom to paste.

## Session Start

1. Confirm you are in `/Users/domcolligan/health_agent_infra/`.
   `~/Documents/health_agent_infra/` is stale.
2. Run `git status --short --branch`. Identify whose work is in the
   tree before editing — uncommitted changes may belong to another
   agent's in-flight packet.
3. Read `PAPER.md` before making scope or prioritization calls.
4. Identify your role this turn: implementer, auditor, or coordinator.
   Dom's prompt will tell you. If unclear, ask.
5. Choose the work lane: paper, benchmark, HAI runtime fix, or archive.

## Active Lanes

Default engineering lane today: **GovernedAgentBench**.

| Lane | Path | Default posture |
|---|---|---|
| Paper control plane | `PAPER.md`, `paper/` | Single source of truth. Update in place only when Dom explicitly changes scope, decisions, hypotheses, roster, calendar, or claims. |
| GovernedAgentBench | `benchmark/governed_agent_bench/`, `benchmark/verification/` | Primary engineering lane. Tasks, schemas, harness, scorer, fixtures, trajectories, reports, and reproducibility live here. |
| HAI reference runtime | `hai/` | Frozen v0.2.0 reference runtime. Modify only via a named `WP-RUNTIME-FIX-NNN`-style fix serving the preprint or benchmark. |
| Historical provenance | `ARCHIVE/` | Read-only by default. Use for decision archaeology; do not treat as current guidance. |

## Research Invariants

- The headline experiment varies the runtime, not the prompt.
- Keep static oracle-pair evidence, live runtime probes, and
  model-backed trajectories clearly separated.
- Mechanism inventory: M4 validation, M5 `agent_safe`, M6 W57
  proposal/commit gate, M7 refusal, M8 audit evidence emission, M9-TX
  transaction integrity held constant.
- `no_runtime_enforcement` is a robustness sanity floor, not
  per-mechanism attribution evidence.
- No model-backed trajectory runs until the pilot protocol and model
  roster are explicitly locked by Dom.
- No private health rows, live wearable exports, credentials, or
  maintainer personal data in benchmark fixtures, prompts, trajectories,
  reports, or reproducibility artifacts.
- The health boundary is part of the evaluated contract: no diagnosis,
  treatment, prescribing, or autonomous medical decisions.

## Benchmark Discipline

- Treat trajectories as benchmark evidence. Model transcripts that are
  not converted into trajectory JSON are not evidence.
- The operator action contract is structured JSON, not arbitrary shell.
- The scorer is deterministic and offline. Do not add model calls to
  the scorer.
- Offline reproducibility must not use network, private state, live
  wearable sources, or paid APIs.
- When changing tasks, trajectories, scorer config, or runtime modes,
  update tests that prove the intended coverage and evidence tier.
- Preserve manifest and fixture hermeticity: benchmark subprocesses
  must use redirected HAI state/base paths.

## HAI Runtime Discipline

HAI is subordinate to the paper/benchmark. Runtime changes are allowed
only when they support a preprint claim, benchmark mechanism, fixture,
or reproducibility need.

- Mutate HAI state only through `hai` CLI surfaces, never direct SQLite
  writes.
- Read the CLI contract with `uv run hai capabilities --json` rather
  than guessing command shapes.
- Python under `hai/src/health_agent_infra/` owns deterministic
  behavior: validation, policy, R-rules, X-rules, synthesis,
  persistence, and CLI behavior.
- Markdown skills under `hai/src/health_agent_infra/skills/` own
  rationale, uncertainty surfacing, clarification, and free-text
  routing.
- Skills never compute bands, scores, R-rule firings, or X-rule
  mutations; runtime code never improvises coaching prose.
- Do not import from `skills/` inside Python runtime code.
- Threshold-consumer sites must use
  `core.config.coerce_int / coerce_float / coerce_bool`; never silent
  bool-as-int coercion.
- W57: agents cannot deactivate user-authored state without explicit
  user commit. Proposals are agent-safe; activation/deactivation is
  not.

## Audit Protocol

The implementer produces a handoff packet; the auditor uses it as the
entry point for verification, not as the source of truth. The audit
re-derives the facts.

**Implementer's handoff packet:**

- Lane and goal
- Current git state and what files changed
- Tests and commands run, with outcomes
- Evidence tier affected, if benchmark work
- Known failures or skipped checks
- Next concrete action
- Anything the next agent should avoid touching

**Auditor's checklist before recommending commit:**

- Read every changed file end-to-end; do not trust the diff summary
- Re-run the verification the implementer claimed
- Check that the brief was followed and no scope crept silently
- Confirm uncommitted files outside the implementer's reported scope
  are flagged, not bundled into the commit
- Surface any security-sensitive defaults the implementer chose
  (env-only credentials, mocked transports, fixture-only data
  boundaries)
- Report findings to Dom in plain language; Dom decides the commit

## Test Commands

Use the narrowest relevant command first, then broaden before handoff.

```bash
# Benchmark suite
PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests
PYTHONPATH=benchmark uv run pytest -q benchmark/verification/tests/test_<area>.py
PYTHONPATH=benchmark uv run python benchmark/governed_agent_bench/reproduce_offline.py --output-dir /tmp/gab_offline_repro

# HAI suite + CLI
uv run pytest hai/verification/tests -q
uv run pytest hai/verification/tests/test_<area>.py -q
uv run hai capabilities --json
uv run hai doctor

# Type and security checks (project venv lacks these; use uvx)
uvx mypy hai/src/health_agent_infra
MYPYPATH=benchmark:hai/src uvx mypy --explicit-package-bases benchmark/governed_agent_bench
uvx bandit -ll -r hai/src/health_agent_infra benchmark/governed_agent_bench
```

The project venv intentionally omits `mypy`, `bandit`, and `build`.
Use `uvx` for those rather than mutating `uv.lock`.

## Do Not Do

- Do not commit autonomously or push without explicit Dom authorization.
- Do not stage or commit changes you did not make this session. Flag
  unfamiliar working-tree files to Dom before any commit.
- Do not extend scope silently. Surface the work; let Dom decide.
- Do not trust another agent's verification summary without re-running
  tests yourself.
- Do not make HAI product-roadmap changes or v0.2.1+ polish.
- Do not create new planning, phase, batch, or orchestration files in
  the active tree. Decisions update in `PAPER.md`; provenance goes in
  `ARCHIVE/`.
- Do not reopen active D-NN decisions without an explicit Dom call.
- Do not soften the external framing: this is an AI control paper under
  the AI safety umbrella.
- Do not merge static canary evidence with live runtime causality
  claims.
- Do not put private user data in public benchmark artifacts.
- Do not bypass `agent_safe`, W57, refusal, validation, or audit paths
  to make a task pass.
- Do not add wearable sources, micronutrient/food-taxonomy features, or
  clinical/medical decision claims.
- Do not anchor data paths on Strava or an upstream that proxies Strava
  data. Strava's Nov 2024 API agreement prohibits AI/ML use;
  intervals.icu is the supported live source.
- Do not auto-load MCP servers from project files. CVE-2025-59536 /
  CVE-2026-21852 demonstrate the autoload + token-exfiltration chain.
  Manual install + local stdio is the only allowed exposure path.
- Do not open a PR, push, or publish autonomously.

## When In Doubt

Read `PAPER.md`, then this file. If the scope is still unclear, ask
Dom rather than guessing. Asking is preferred over inventing.
