# Architecture

Health Agent Infra is a governed runtime for a multi-domain personal
health agent. One Claude agent (or open equivalent) reads a
cross-domain state snapshot, emits per-domain proposals via
domain-specific skills, and a synthesis skill reconciles them into
bounded per-domain recommendations validated at the ``hai
writeback`` boundary. Every deterministic guarantee lives in code;
every judgment call lives in a skill; the contract between them is
typed.

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
│                          stress, strength, nutrition}.py            │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼ (canonical accepted_*_state_daily tables)
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
the projector. Migrations 001–006 are live:

- 001 initial schema
- 002 training-readiness column rename
- 003 synthesis scaffolding (proposal_log, daily_plan, x_rule_firing)
- 004 sleep + stress tables
- 005 strength expansion + exercise_taxonomy
- 006 nutrition macros-only (derivation_path='daily_macros';
  micronutrient columns + food_taxonomy deferred per Phase 2.5
  retrieval gate)

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
        writeback-protocol/SKILL.md
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

hai classify --domain <d> --evidence-json <p>  # debug: dump classified state
hai policy   --domain <d> --evidence-json <p>  # debug: dump policy result

hai propose  --domain <d> --proposal-json <p> --base-dir <root>
hai synthesize --base-dir <root> --as-of <d> --user-id <u>

hai writeback --recommendation-json <p> --base-dir <root>

hai review schedule | record | summary [--domain <d>] --base-dir <root>

hai config init | show
hai exercise search --query <free-text>
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills [--dest ~/.claude/skills] [--force]
```

## Determinism boundary

Three places the runtime refuses to proceed without a valid contract:

1. **``hai propose``** — every DomainProposal is validated against
   ``core/writeback/proposal.py:validate_proposal_dict``:
   schema_version per-domain, action in the domain's v1 enum, confidence
   enum, banned fields absent (``follow_up``, ``daily_plan_id``,
   ``recommendation_id``), non-empty policy_decisions.

2. **``hai synthesize``** — refuses when no proposals reached
   proposal_log; rolls back the entire transaction on any failure;
   Phase B firings are guarded against writing anything other than
   ``action_detail`` on a registered target domain.

3. **``hai writeback``** — every BoundedRecommendation validated
   against the per-domain schema before it reaches
   recommendation_log.

All three points reject-loudly with ``exit=2`` and named
``invariant`` ids for programmatic recovery.

## How an agent uses this

One Claude agent reads the bundle from ``hai state snapshot`` and
the domain skills from ``~/.claude/skills/``. Per-domain, it emits a
proposal via ``hai propose``. Once all proposals for a (for_date,
user_id) are in, the agent invokes ``hai synthesize`` — the runtime
runs Phase A, then invokes the daily-plan-synthesis skill to overlay
rationale, then runs Phase B, then atomically commits the final
plan. ``hai review`` captures outcomes for the next morning.

See [``agent_integration.md``](agent_integration.md) for the
concrete Claude Code / Agent SDK wiring.
