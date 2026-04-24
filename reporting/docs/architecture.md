# Architecture

Health Agent Infra is a governed runtime for a multi-domain personal
health agent. One Claude agent (or open equivalent) reads a
cross-domain state snapshot, emits per-domain proposals via
domain-specific skills, and a synthesis skill reconciles them into
bounded per-domain recommendations validated at the ``hai
writeback`` boundary. Every deterministic guarantee lives in code;
every judgment call lives in a skill; the contract between them is
typed.

This doc covers *how* the runtime is wired. For the framing layer
(what this project is, how roles split across runtime / coach / memory
/ grounded expert, and why it is local-first) see
[``personal_health_agent_positioning.md``](personal_health_agent_positioning.md).
For the layered view of what lives on disk see
[``memory_model.md``](memory_model.md). For the classes of user
question the runtime is built to answer see
[``query_taxonomy.md``](query_taxonomy.md).

## Six domains in v1

| Domain | What it reasons about |
|---|---|
| recovery | Is the body recovered enough for today's planned training? |
| running | Is today's planned run appropriate given recent form? |
| sleep | Is sleep adequate to proceed; is chronic deprivation building? |
| stress | Is stress state eroding readiness; is it sustained? |
| strength | Is recent strength volume aligned with the training block? |
| nutrition | Are today's macros aligned with training demand? (macros-only in v1 — see non_goals.md) |

The ordering reflects historical build order (recovery was first; nutrition
was last) and increasing effort per phase, not a reasoning
precedence. Synthesis does not privilege one domain over another.

## Data flow

```
┌─────────────────────────────────────────────────────────────────────┐
│              INTAKE — source + user-authored                        │
│                                                                     │
│  hai pull [--live]      hai intake gym         hai intake nutrition │
│                         hai intake stress      hai intake note      │
│                         hai intake exercise    hai intake readiness │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼ (raw evidence, append-only JSONL + raw tables)
┌─────────────────────────────────────────────────────────────────────┐
│              PROJECTORS — per-domain, deterministic                 │
│                                                                     │
│  core/state/projectors/{recovery, running, sleep,                   │
│                          stress, strength, nutrition,               │
│                          running_activity}.py                       │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼ (canonical accepted_*_state_daily tables
                                 + running_activity per-session rows)
┌─────────────────────────────────────────────────────────────────────┐
│                     STATE SNAPSHOT                                  │
│              hai state snapshot --as-of <date>                      │
│                                                                     │
│  Returns per-domain block:                                          │
│    - evidence       (the raw accepted row)                          │
│    - raw_summary    (deltas, ratios, coverage)                      │
│    - classified_state   (bands, scores — from domains/<d>/classify) │
│    - policy_result      (R-rule firings — from domains/<d>/policy)  │
│    - missingness        (absent | partial | unavailable | pending)  │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│            DOMAIN SKILLS — judgment, per domain                     │
│                                                                     │
│  skills/recovery-readiness     running-readiness                    │
│         sleep-quality          stress-regulation                    │
│         strength-readiness     nutrition-alignment                  │
│                                                                     │
│  Each reads its snapshot block + the already-computed               │
│  classified_state + policy_result. Honours forced_action and        │
│  capped_confidence from policy; composes rationale; emits a         │
│  DomainProposal validated + appended via `hai propose`.             │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼ (proposal_log, persisted)
┌─────────────────────────────────────────────────────────────────────┐
│        SYNTHESIS PHASE A — cross-domain X-rules (pre-skill)         │
│                                                                     │
│  Runtime: evaluates X1-X7 against snapshot + proposals; emits       │
│           firings; applies mutations mechanically to drafts.        │
│  Skill  : daily-plan-synthesis reads bundle + firings, composes     │
│           rationale overlay on top of already-fixed actions.        │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼ (N draft recommendations, actions now fixed)
┌─────────────────────────────────────────────────────────────────────┐
│       SYNTHESIS PHASE B — post_adjust (action_detail only)          │
│                                                                     │
│  Runtime: evaluates post_adjust-tier rules (X9) against finalised   │
│           drafts. MAY mutate only action_detail on specific target  │
│           domains; a write-surface guard rejects any firing that    │
│           would change action or touch a non-target domain.         │
│                                                                     │
│  Output: N final per-domain recommendations linked by daily_plan_id │
│          All writes commit in one SQLite transaction (daily_plan    │
│          + x_rule_firing rows + recommendation_log rows). Canonical │
│          plan is idempotent on (for_date, user_id).                 │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        REVIEW — per-domain                          │
│    hai review schedule / record / summary [--domain <d>]            │
└─────────────────────────────────────────────────────────────────────┘
```

## Code-vs-skill boundary

The line is tight and the plan documents it in detail
(``reporting/plans/comprehensive_rebuild_plan.md §2.1``). Short form:

**Code owns:**
- Deterministic arithmetic (band classification, scoring, signal
  counting).
- Mechanical policy rules (R-rules per domain; X-rules cross-
  domain).
- Parsing of user narration into structured rows (gym sets,
  nutrition macros, stress score).
- Taxonomy lookup ranking (exercise taxonomy today; food taxonomy
  deferred per Phase 2.5 retrieval-gate outcome).
- X-rule mutation application, tier precedence, Phase B write-
  surface guard.
- Atomic transaction around daily_plan + firings + recommendations.
- Schema validation at the writeback boundaries.

**Skills own:**
- Composing rationale prose for an already-fixed action.
- Deciding when to ask the user a clarifying question (e.g.
  strength-intake disambiguating "squats" → back vs front).
- Surfacing uncertainty the runtime cannot itself resolve (data-
  gaps, ambiguous narration).
- Joint-rationale reconciliation during synthesis when multiple
  domains' firings share a signal.

Skills never change an action. Skills never run arithmetic the
runtime already ran. A skill that tries to compute a band has
regressed into code's territory and should be rewritten.

## R-rules (per-domain mechanical policy)

Each domain's ``policy.py`` implements a small R-rule set that the
classifier + snapshot bundle feeds into. Common ids:

- ``require_min_coverage`` — missing required inputs forces
  ``defer_decision_insufficient_signal``.
- ``no_high_confidence_on_sparse_signal`` — sparse coverage caps
  confidence at ``moderate``.
- Domain-specific escalation rules (recovery RHR-spike, running
  ACWR-spike, sleep chronic-deprivation, stress sustained-high,
  strength volume-spike, strength unmatched-taxonomy, nutrition
  extreme-deficiency).

See the domain classifiers under
``src/health_agent_infra/domains/<d>/classify.py`` and policies at
``domains/<d>/policy.py`` for the authoritative list of bands and
rule firings.

## X-rules (synthesis-layer cross-domain)

See [``x_rules.md``](x_rules.md) for the full catalogue.

## State model

See [``state_model_v1.md``](state_model_v1.md) for the authoritative
table-by-table schema. Each accepted_*_state_daily table is
deterministically derived from one or more raw + source tables by
the projector. Migrations 001–011 are live:

- 001 initial schema
- 002 training-readiness column rename
- 003 synthesis scaffolding (proposal_log, daily_plan, x_rule_firing)
- 004 sleep + stress tables
- 005 strength expansion + exercise_taxonomy
- 006 nutrition macros-only (derivation_path='daily_macros';
  micronutrient columns + food_taxonomy deferred per Phase 2.5
  retrieval gate)
- 007 explicit user memory (goals / preferences / constraints /
  context notes)
- 008 sync_run_log (per-source freshness observability)
- 009 recommendation_log.daily_plan_id column + index
- 010 review_outcome enrichment (completed, intensity_delta,
  pre/post_energy_score, disagreed_firing_ids, …)
- 011 planned_recommendation ledger (pre-X-rule aggregate, M8
  Phase 1) — closes the audit chain at the aggregate level so
  `planned ⊕ firings = adapted` is verifiable from rows alone
- 012 runtime_event_log — per-invocation telemetry for `hai stats`
- 013 proposal_log revision columns (D1 re-author semantics)
- 014 daily_plan.superseded_by_plan_id forward-link
- 015 manual_readiness_raw (D2 per-domain intake landing)
- 016 review_outcome.re_linked_from_recommendation_id (D1 auto-re-link)
- 017 running_activity — per-session structural data from the
  intervals.icu `/activities` stream (HR zone times, interval
  summaries, TRIMP, warmup/cooldown). Distinct from the daily rollup
  in `accepted_running_state_daily`: activities are the source of
  truth for session structure; the rollup is an aggregation over
  today's activities (populated by `aggregate_activities_to_daily_rollup`
  in `cmd_clean`)

## Agent-operable surfaces (M8)

The M8 cycle added three surfaces that make the runtime directly
agent-operable without changing the governance model:

- **Three-state audit chain.** `planned_recommendation` (migration
  011) persists the aggregate pre-X-rule bundle alongside the
  existing `daily_plan` + `recommendation_log`. `hai explain` renders
  `planned → adapted → performed` side-by-side.
- **Agent CLI contract.** Every `hai` subcommand carries contract
  metadata (mutation class, idempotency, JSON output, exit codes,
  agent-safe flag). `hai capabilities --json` emits a manifest walked
  from the argparse tree; the markdown mirror lives at
  [``agent_cli_contract.md``](agent_cli_contract.md). All handlers
  return from the stable `OK / USER_INPUT / TRANSIENT / NOT_FOUND /
  INTERNAL` taxonomy.
- **Sentence-form X-rule explanations.** Every firing carries both a
  stable slug (`sleep-debt-softens-hard`) and a one-sentence
  `human_explanation` the agent narrates verbatim.
- **Authoritative intent-router skill.** Maps NL intent to CLI
  workflow sequences by reading the capabilities manifest as its
  source of truth. Teaches the agent `hai` the way Claude already
  knows `gh`. See [``agent_operable_runtime_plan.md``](../plans/agent_operable_runtime_plan.md)
  for the full cycle context.

## Package layout

```
src/health_agent_infra/
    cli.py                          # unified hai dispatcher
    core/
        schemas.py                  # BoundedRecommendation[ActionT] base
        validate.py                 # shared invariants
        config.py                   # DEFAULT_THRESHOLDS + loader
        synthesis.py                # Phase A + Phase B orchestration
        synthesis_policy.py         # X-rule evaluators
        writeback/
            proposal.py             # DomainProposal validation + JSONL
            recommendation.py       # BoundedRecommendation validation
        state/
            snapshot.py             # cross-domain bundle builder
            store.py                # SQLite connection + migrations
            projector.py            # orchestrator
            projectors/{recovery,running,sleep,stress,strength,nutrition}.py
            migrations/001…006.sql
        clean/                      # hai clean deterministic prep
        pull/                       # Garmin CSV + live adapters + auth
        review/                     # schedule / record / summarize
        intake/                     # shared intake helpers
    domains/
        recovery/   {schemas, classify, policy}.py
        running/    {schemas, classify, policy, signals}.py
        sleep/      {schemas, classify, policy, signals}.py
        stress/     {schemas, classify, policy, signals, intake}.py
        strength/   {schemas, classify, policy, signals, intake,
                     taxonomy_match}.py + taxonomy_seed.csv
        nutrition/  {schemas, classify, policy, signals, intake}.py
    skills/                         # packaged with the wheel
        recovery-readiness/SKILL.md
        running-readiness/SKILL.md
        sleep-quality/SKILL.md
        stress-regulation/SKILL.md
        strength-readiness/SKILL.md
        nutrition-alignment/SKILL.md
        daily-plan-synthesis/SKILL.md
        strength-intake/SKILL.md
        merge-human-inputs/SKILL.md
        review-protocol/SKILL.md
        safety/SKILL.md
        reporting/SKILL.md
reporting/
    docs/                           # this doc + friends
    artifacts/flagship_loop_proof/  # eval runner captures
    plans/                          # rebuild plan + Phase 2.5 gates
    experiments/                    # Phase 0.5 / 2.5 throwaway prototypes
safety/
    tests/                          # unit + contract + integration tests
    evals/                          # Phase 6 eval framework
        scenarios/{domain,synthesis}/
        rubrics/
        runner.py  cli.py  README.md
```

## CLI surface (v1)

```
hai auth garmin                               # keyring credential storage
hai auth status

hai pull [--live] --date <YYYY-MM-DD>         # Garmin CSV / live pull
hai clean --evidence-json <p>                  # raw → CleanedEvidence + RawSummary

hai intake gym      --session-json <p>         # per-set + bulk modes
hai intake exercise --name <canonical>         # user-defined taxonomy row
hai intake nutrition --calories ... --protein-g ... [macros]
hai intake stress   --score 1..5 [--tags ...]
hai intake note     --text ...
hai intake readiness --soreness low|moderate|high --energy low|moderate|high

hai state init | migrate | read | snapshot | reproject

hai state snapshot --evidence-json <p> --as-of <d> --user-id <u>
# Emits classified_state + policy_result for every domain in one call.
# (The legacy recovery-only `hai classify` / `hai policy` debug CLIs
# were removed in v0.1.4 — see `reporting/plans/v0_1_4/adr_classify_policy_cli.md`.)
# For multi-scenario sweeps use the eval runner: `hai eval run --domain <d>`.

hai propose  --domain <d> --proposal-json <p> --base-dir <root>
hai synthesize --as-of <d> --user-id <u>                        # six-domain atomic commit
hai synthesize --as-of <d> --user-id <u> --bundle-only          # read-only skill seam
hai synthesize --as-of <d> --user-id <u> --drafts-json <p>      # skill overlay pass

hai explain --for-date <d> --user-id <u> [--text]                # read-only audit-chain reconstruction
hai explain --daily-plan-id <id> [--text]                        # exact-plan form (incl. _v<N> variants)

hai review schedule | record | summary [--domain <d>] --base-dir <root>

hai config init | show
hai exercise search --query <free-text>
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills [--dest ~/.claude/skills] [--force]
```

## Determinism boundary

Two places the runtime refuses to proceed without a valid contract:

1. **``hai propose``** — every DomainProposal is validated against
   ``core/writeback/proposal.py:validate_proposal_dict``:
   schema_version per-domain, action in the domain's v1 enum, confidence
   enum, banned fields absent (``follow_up``, ``daily_plan_id``,
   ``recommendation_id``), non-empty policy_decisions.

2. **``hai synthesize``** — refuses when no proposals reached
   proposal_log; rolls back the entire transaction on any failure;
   Phase B firings are guarded against writing anything other than
   ``action_detail`` on a registered target domain. Per-domain
   BoundedRecommendation validation for all six domains happens inside
   ``run_synthesis`` via ``project_bounded_recommendation``. (The
   legacy recovery-only ``hai writeback`` direct path was removed in
   v0.1.4 D2.)

Both points reject-loudly with ``exit=2`` and named ``invariant`` ids
for programmatic recovery.

## How an agent uses this

One Claude agent reads the bundle from ``hai state snapshot`` and
the domain skills from ``~/.claude/skills/``. Per-domain, it emits a
proposal via ``hai propose``. Once all proposals for a (for_date,
user_id) are in, the agent has two paths:

- **Runtime-only path (`hai daily` or a single `hai synthesize`
  call without `--drafts-json`).** The runtime evaluates Phase A,
  applies mutations mechanically to drafts, runs Phase B, and
  atomically commits. Rationale is the per-proposal text the
  domain skills already wrote — the synthesis skill is NOT
  invoked.
- **Skill-overlay path (two-pass `hai synthesize`).** The agent
  first calls `hai synthesize ... --bundle-only` (read-only) to
  emit `(snapshot, proposals, phase_a_firings)`. The
  daily-plan-synthesis skill composes a rationale overlay and the
  agent then calls `hai synthesize ... --drafts-json <path>` to
  finish the commit. The runtime applies the overlay onto the
  mechanical drafts (rationale + uncertainty + review_question
  only), then runs Phase B, then atomically commits.

`hai daily` ships the runtime-only path today: it stops cleanly at
the proposal gate (`overall_status=awaiting_proposals`) when no
proposals are present, but it does not orchestrate the two-pass
skill overlay. The two-pass path is opt-in for an agent that wants
to drive the synthesis skill explicitly.

``hai review`` captures outcomes for the next morning.

See [``agent_integration.md``](agent_integration.md) for the
concrete Claude Code / Agent SDK wiring.
