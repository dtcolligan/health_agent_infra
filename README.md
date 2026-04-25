# Health Agent Infra

**A governed local agent runtime for personal health data.**
Claude Code + Garmin today; MCP-portable and multi-source on the roadmap.

A Claude Code agent reads your own health data, emits per-domain proposals
bounded by codified rules, and commits auditable recommendations you review
the next day. Every decision is logged to a local SQLite database on your
machine; nothing leaves your device.

**For** technical users comfortable with a CLI who use Claude Code and want
agent recommendations they can audit, reproduce, and keep local.

- **Local-first.** State lives in a SQLite file under your home directory. No
  cloud, no account, no remote telemetry.
- **Governed, not generative.** Python owns mechanical decisions
  (classification bands, policy rules, transactional commits); markdown
  skills own rationale and uncertainty. Skills never change an action; code
  never writes prose.
- **Agent-operable by contract.** Every CLI subcommand carries
  machine-readable contract metadata (mutation class, idempotency, exit
  codes) that an agent reads via `hai capabilities --json`. An authoritative
  `intent-router` skill maps natural-language intent to deterministic
  workflows; every X-rule firing carries a stable slug plus a sentence-form
  explanation the agent can narrate verbatim.
- **Auditable by construction.** Pulls, proposals, rule firings, synthesis,
  and final recommendations all land in typed tables. Inspect anytime with
  `hai today` (end-user prose), `hai explain --operator` (dense audit
  report), `hai doctor`, `hai stats`. Prefer these over reading the
  SQLite file directly — they reconcile supersede chains and hide
  schema churn, which plain SQL won't.

## Install

```bash
pipx install health-agent-infra                # or: pip install -e .
hai init --with-auth --with-first-pull         # scaffolds state + config + skills,
                                                # prompts for credentials,
                                                # backfills the last 7 days
hai daily                                       # tomorrow morning: orchestrates the
                                                # deterministic stages (pull → clean
                                                # → snapshot → gaps); the agent then
                                                # invokes the 6 per-domain skills,
                                                # posts proposals, and re-runs to
                                                # synthesize. See "How `hai daily`
                                                # actually completes" below.
hai today                                       # read today's plan in plain language
hai stats                                       # local funnel: syncs, recent runs, daily streak
```

**`--source` defaults (v0.1.6).** When neither `--source` nor `--live`
is passed, `hai pull` and `hai daily` resolve to **`intervals_icu`**
when intervals.icu credentials are configured (the supported live
source as of v0.1.6), else fall back to `csv` (the committed fixture,
useful offline). Garmin Connect's login surface is rate-limited and
unreliable for live scraping; pass `--source garmin_live` only if you
explicitly want it. Set up intervals.icu auth with `hai auth
intervals-icu`.

Prefer the non-interactive path? Run `hai init` on its own, then `hai
auth intervals-icu` (or `hai auth garmin`) separately. `hai init` is
idempotent and safe to re-run. Full CLI surface in
[`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).

**macOS Keychain note.** `hai auth garmin` and `hai auth intervals-icu`
store credentials in the OS keyring. On macOS, the first time `hai
pull` reads those credentials the system prompts you to allow access.
Click **Always Allow** — otherwise every subsequent pull re-prompts
and scripted runs (including `hai daily`) will hang waiting for a
keyboard.

## Where your data lives

Everything stays on your machine. Three locations matter:

| What | Default path | Override |
|---|---|---|
| **State DB** (the SQLite file with all accepted state, proposals, plans, recommendations, reviews) | `~/.local/share/health_agent_infra/state.db` | `$HAI_STATE_DB` env var, or `--db-path` on any subcommand |
| **Writeback / intake JSONL** (raw intakes, per-domain proposals, review events — append-only audit trail) | `~/.health_agent/` | `$HAI_BASE_DIR` env var, or `--base-dir` on any subcommand that writes (optional in v0.1.6) |
| **Config** (thresholds.toml — bands, R-rule thresholds, X-rule parameters) | platform-specific user config dir (macOS: `~/Library/Application Support/hai/thresholds.toml`; Linux: `~/.config/hai/thresholds.toml`) | scaffold a fresh one with `hai config init --path <p>` |

The state DB path is hardcoded to the XDG-style
`~/.local/share/health_agent_infra/state.db` on every platform (see
`core/state/store.py:DEFAULT_DB_PATH`). The base-dir default is
`~/.health_agent/` (see `core/paths.py:DEFAULT_BASE_DIR`). Confirm
your resolved paths with `hai doctor` — it prints state DB, schema
version, sources, and skill installation status in one shot.

`hai doctor` also catches a class of subtle drift the v0.1.6 release
hardened against: a DB that looks "current" by `MAX(version)` but
has gaps in the applied migration set (e.g. after a manual edit or
partial restore). The check warns when the applied set is not the
contiguous range `[1..head]`.

## How `hai daily` actually completes

`hai daily` is the orchestrator the agent drives, **not** a single
end-to-end command that finishes on its own. Run from a fresh state,
the deterministic stages run to completion and then stop at the
proposal gate:

1. **`pull`** — fetch evidence from the configured source.
2. **`clean`** — normalize into typed evidence + raw summary.
3. **`snapshot`** — build the per-domain bundle the skills consume.
4. **`gaps`** — enumerate user-closeable intake gaps (only when
   `--evidence-json` made it through; the structured response carries
   `"computed": true` so an agent can pattern-match without guessing).
5. **`proposal_gate`** — three statuses: `awaiting_proposals` (zero
   proposals), `incomplete` (some proposals, missing ≥1 expected
   domain), `complete` (every expected domain present).

The first time you hit `awaiting_proposals` or `incomplete`, the
agent must invoke the per-domain readiness skills, post a
`DomainProposal` per domain via `hai propose --domain <d>`, then
re-run `hai daily`. The `proposal_gate.status` is the documented
contract field the agent watches for; the accompanying `hint` names
exactly what's missing.

`--domains <csv>` narrows the gate's expected set so an agent
planning a partial day (e.g. "today's sleep + recovery only") can
unblock without posting unused proposals. Synthesis still runs over
every proposal present in `proposal_log`.

The skill-driven completion is documented in
[`reporting/docs/agent_integration.md`](reporting/docs/agent_integration.md).

## Reading your plan

`hai today` is the non-agent-mediated user surface — it reads the
canonical plan for a date (resolving supersede chains automatically)
and renders prose in the voice the `reporting` skill specifies:
top-matter → 2–4 sentence summary → six per-domain sections → footer
pointing at the next review.

```bash
hai today                         # today, markdown on TTY / plain elsewhere
hai today --as-of 2026-04-23      # specific date
hai today --domain recovery       # narrow to one domain
hai today --format json           # machine-readable (same shape, no prose)
```

Defer domains (insufficient signal) surface a domain-specific
follow-up question and an **unblock hint** naming the `hai intake …`
command that would give tomorrow's plan the signal it needs — see
[`reporting/plans/v0_1_4/D3_user_surface.md`](reporting/plans/v0_1_4/D3_user_surface.md)
for the voice contract.

For debug-level audit dumps, use `hai explain --operator` (dense
field-by-field text) or `hai explain` (JSON). Both consume the same
explain bundle `hai today` reads — they just render it differently.

## Recording your day

After tomorrow's `hai daily` schedules a review event for each rec,
log how yesterday went:

```bash
hai review record --outcome-json <path>           # --base-dir + --db-path
                                                   # default to $HAI_BASE_DIR /
                                                   # $HAI_STATE_DB

hai review summary [--domain recovery]            # same defaults
```

Outcomes are append-only and **auto-re-link** when a plan has been
superseded — if you recorded an outcome against the morning plan but
re-authored the day after lunch, `hai review record` routes the
outcome to the canonical leaf's matching-domain rec. See the
`review-protocol` skill for the full payload shape.

`followed_recommendation` and `self_reported_improvement` MUST be
strict booleans (`true` / `false`), not `"yes"` / `1` / truthy
strings. The v0.1.6 review-outcome validator rejects non-boolean
values with a named invariant (`followed_recommendation_must_be_bool`)
to prevent the JSONL-vs-SQLite truth fork that earlier releases were
silent about.

Manual intake surfaces (stress score, gym sessions, nutrition macros,
readiness self-reports) all live under `hai intake <domain>`; they
persist to their per-domain raw tables so the next `hai daily` picks
them up automatically. `--base-dir` is optional on every intake
command (defaults to `$HAI_BASE_DIR` or `~/.health_agent/`).

**Nutrition is a daily total, not per-meal.** `hai intake nutrition`
records one row per `(as_of_date, user_id)`. Re-calling within the
same day creates a supersede chain — log it once at end of day. If
you want to keep notes between meals, use `hai intake note --tags
nutrition,lunch` as a scratchpad and sum at the end.

**Planned-session vocabulary.** The `--planned-session-type` field on
`hai intake readiness` is free text, but the per-domain classifiers
match against a canonical vocabulary: `easy_z2`, `intervals_4x4`,
`tempo`, `long`, `race`, `strength_sbd`, `strength_*` (back_biceps /
push / pull / etc.), `rest`. Strings outside this set classify as
"other" with reduced specificity.

## Six domains in v1

**recovery · running · sleep · stress · strength · nutrition**

Each domain ships its own schemas, classification bands, policy rules, and a
readiness skill, and is wired into the synthesis X-rule catalogue that
reconciles across domains. Nutrition is macros-only in v1 — see
[`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

## Calibration timeline

The system needs history to do its job. A fresh install produces
recommendations on day one, but several rules can't fire meaningfully
until baselines have formed. The day numbers below are not arbitrary —
each one corresponds to a specific window length the runtime depends
on. Code-derived markers cite the file; the rest are reasoned.

| Window | What works | Why this number |
|---|---|---|
| **Days 1–14** | Cold-start mode for running / strength / stress (`cold_start_relaxation` rule softens R-coverage blocks). The volume-spike-on-first-strength-session escalation is the canonical artifact — review it but expect to consciously override several flags. | Code-derived: `COLD_START_THRESHOLD_DAYS = 14` in `core/state/snapshot.py:35`, gating `cold_start_relaxation` in `domains/{running,strength,stress}/policy.py`. |
| **Day 14** | Cold-start window closes — recommendations stop being softened by `cold_start_relaxation`. HRV + RHR rolling baselines stabilize. Sleep's chronic-deprivation rule has enough nights to fire on real signal. | Code-derived: same constant; chosen so a 7-day trailing window has at least one full validated week plus a buffer. |
| **Days 14–28** | Recovery, sleep, and stress recommendations become genuinely calibrated against your trailing-7d trend. Manual stress baseline forms; the `sustained_very_high_stress_escalation` rule's 5-day window is reliably full. | Reasoned: per-domain trailing-7d signals require ~2 windows of overlap before "your normal" is stable enough to compare against. |
| **Day 28** | ACWR's chronic-load denominator is full (`domains/running/signals.py:167` slices a 28-day window). Strength `volume_ratio` (7d ÷ 28d week-mean, `domains/strength/signals.py:51,80`) stops mechanically reading as 4× on every session. Running freshness detection works for real. | Code-derived: 28-day windows appear literally in the running + strength signal layers. |
| **Day 60+** | Trend bands (`sleep_timing_consistency`, `weekly_mileage_trend`) start carrying real signal. | Reasoned: a trend band compares two consecutive ~28-day windows; you need ~60 days before the second window has enough days *outside* the first to differ meaningfully. |
| **~Day 90** | Steady state. Remaining uncertainty is structural, not history-bounded. | Reasoned: ~3 months covers enough variance across training cycles, recovery patterns, and life events that the trailing distributions characterize "your normal" rather than "your last fortnight." |

**Cold-start asymmetry across domains.** Only running, strength, and
stress have a `cold_start_relaxation` rule; recovery, sleep, and
nutrition do not. Nutrition non-relaxation is intentional and tested
(`safety/tests/test_nutrition_cold_start_non_relaxation.py`):
nutrition keeps deferring on insufficient evidence rather than
relaxing into a low-confidence guess.

**Permanent caveats — not fixable by accumulating history:**

- `sleep_efficiency_unavailable`, `body_battery_unavailable`,
  `garmin_all_day_stress_unavailable` — intervals.icu doesn't expose
  these signals, and intervals.icu is the supported pull source for
  the foreseeable future (Garmin Connect's login surface is
  rate-limited and unreliable for live scraping).
- `micronutrients_unavailable_at_source` — v1 nutrition is
  macros-only by design; see
  [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).

If you hit a cold-start escalation in your first week (e.g.
`volume_spike_detected` after your first logged strength session),
that's expected: the rule is comparing 7-day load to a 28-day
baseline of zero. Review the escalation, judge whether the underlying
signal is real, and override consciously rather than ignoring.
Cold-start escalations are usually logging artifacts, not real
warnings.

## Local-first runtime at a glance

```
pull / intake  →  projectors  →  accepted_*_state_daily tables
                                        │
                                        ▼
                         hai state snapshot --as-of <date>
                                        │
                                        ▼
                 domain skills emit DomainProposal × 6
                                        │ hai propose
                                        ▼
                              proposal_log
                                        │
                                        ▼
   Phase A X-rules (X1–X7) → runtime applies mutations to drafts
                                        │
                                        ▼
             daily-plan-synthesis skill overlays rationale
                                        │
                                        ▼
         Phase B X-rules (X9) → action_detail adjustments
                                        │
                                        ▼
  ATOMIC COMMIT: daily_plan + x_rule_firings
               + planned_recommendation (pre-X-rule aggregate)
               + N recommendation_log (adapted)
                                        │
                                        ▼
             hai today (read) / hai review record (write)
```

- **Local state memory** — ``accepted_*_state_daily`` tables store the
  canonical per-domain day-level state the runtime reasons over.
- **Decision memory** — ``proposal_log`` (per-domain planned intent),
  ``planned_recommendation`` (aggregate pre-X-rule plan), ``daily_plan`` +
  ``x_rule_firing`` + ``recommendation_log`` (aggregate adapted plan)
  preserve the full audit chain: what was originally planned, how X-rules
  mutated it, and what was finally committed.
- **Outcome memory** — ``review_event`` and ``review_outcome`` record how
  the plan went, so the history of decisions and outcomes stays on-device.
- **Agent contract surface** — ``hai capabilities --json`` emits a
  machine-readable manifest of every subcommand; the markdown mirror lives
  at
  [``reporting/docs/agent_cli_contract.md``](reporting/docs/agent_cli_contract.md).
  The ``intent-router`` skill is authoritative for NL → CLI mapping against
  that contract.

See [`reporting/docs/architecture.md`](reporting/docs/architecture.md) for
the full pipeline and the code-vs-skill boundary.

## Roadmap

- **Runtime portability via MCP.** Expose the agent-safe CLI surface as an
  MCP server so any agentic runtime (Claude Code, Codex, others) can drive
  it. Today the project is Claude Code–native; the CLI contract is already
  annotated agent-safe vs. interactive, which maps cleanly onto MCP tool
  schemas.
- **Multi-source wearables.** Apple Health, Oura, Whoop. The adapter
  protocol (`core/pull/protocol.py`) is already source-agnostic; the
  per-domain evidence contract needs to broaden before additional sources
  land. Community adapters welcome — see
  [`reporting/docs/how_to_add_a_pull_adapter.md`](reporting/docs/how_to_add_a_pull_adapter.md).
- **Skill-narration eval harness.** Live-mode pilot shipped (Phase E +
  M8 Phase 4); broader scenario coverage still to come. See
  `safety/evals/skill_harness_blocker.md`.

## What this is not

- Not a medical device, not hosted, not multi-user, not an ML loop. See
  [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md).
- Not meal-level nutrition in v1 — macros only.
- Not an MCP server yet (see Roadmap).
- Not an MCP-wrapper-integrated or skill-harness-eval-complete release yet.

## Dig deeper

1. **Positioning & role map** — [`reporting/docs/personal_health_agent_positioning.md`](reporting/docs/personal_health_agent_positioning.md)
2. **Query taxonomy** — [`reporting/docs/query_taxonomy.md`](reporting/docs/query_taxonomy.md)
3. **Memory model** — [`reporting/docs/memory_model.md`](reporting/docs/memory_model.md)
4. **Architecture overview** — [`reporting/docs/architecture.md`](reporting/docs/architecture.md)
5. **Explainability surface (three-state audit)** — [`reporting/docs/explainability.md`](reporting/docs/explainability.md)
6. **Agent CLI contract (generated manifest)** — [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md)
7. **X-rule catalogue + sentence explanations** — [`reporting/docs/x_rules.md`](reporting/docs/x_rules.md)
8. **Non-goals (scope discipline)** — [`reporting/docs/non_goals.md`](reporting/docs/non_goals.md)
9. **State schema** — [`reporting/docs/state_model_v1.md`](reporting/docs/state_model_v1.md)
10. **10-minute reading tour** — [`reporting/docs/tour.md`](reporting/docs/tour.md)
11. **Extension path — pull adapter** — [`reporting/docs/how_to_add_a_pull_adapter.md`](reporting/docs/how_to_add_a_pull_adapter.md)
12. **Extension path — new domain** — [`reporting/docs/how_to_add_a_domain.md`](reporting/docs/how_to_add_a_domain.md)
13. **Agent-operable runtime plan (M8 cycle)** — [`reporting/plans/agent_operable_runtime_plan.md`](reporting/plans/agent_operable_runtime_plan.md)
14. **Eval capture** — [`reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/`](reporting/artifacts/flagship_loop_proof/2026-04-18-multi-domain-evals/)

## CLI surface

```
# Evidence + intake
hai pull [--source intervals_icu|garmin_live|csv] --date <d>
                                                # default: intervals.icu when configured, else csv
hai clean --evidence-json <p>                   # raw → CleanedEvidence + RawSummary
hai intake gym|exercise|nutrition|stress|note|readiness ...
                                                # --base-dir optional in v0.1.6
                                                # ($HAI_BASE_DIR or ~/.health_agent/)

# State
hai state init | migrate | read | snapshot | reproject [--cascade-synthesis]

# Per-domain debug: use `hai state snapshot --evidence-json <p>` —
# emits classified_state + policy_result for every domain in one call.

# Agent flow — `hai daily` is the orchestrator the agent drives, not a one-shot.
# It runs pull → clean → snapshot → gaps → proposal_gate. The gate emits
# `awaiting_proposals` / `incomplete` / `complete`; the agent posts the
# missing DomainProposal rows and re-runs to advance the gate. See
# "How `hai daily` actually completes" above and reporting/docs/agent_integration.md.
hai daily [--domains <csv>]                     # narrows the gate's expected set
hai propose  --domain <d> --proposal-json <p>   # determinism boundary #1
hai synthesize --as-of <d> --user-id <u>        # determinism boundary #2
hai synthesize --bundle-only                    # post-proposal skill-overlay seam

# Persistence + review
hai review schedule --recommendation-json <p>
hai review record --outcome-json <p>            # determinism boundary #3
                                                # followed_recommendation MUST be strict bool
hai review summary [--domain <d>] [--user-id <u>]

# Agent contract + audit
hai capabilities [--json | --markdown]          # JSON manifest (default), markdown for the doc
hai explain --for-date <d> --user-id <u>        # three-state audit: planned → adapted → performed
hai memory set | list | archive                 # explicit user memory (goals, preferences, constraints)
hai research topics                             # bounded local-only retrieval (no network)
hai research search --topic <t>

# Ops
hai init [--with-auth] [--with-first-pull]      # first-run wizard (idempotent)
hai doctor [--json]                             # runtime health + per-source freshness
hai stats [--json]                              # local funnel (sync + command history, daily streak)

# Auth + config + helpers
hai auth garmin | status
hai config init | show
hai exercise search --query <free-text>

# Evals
hai eval run --domain <d> | --synthesis [--json]

hai setup-skills                                # copy packaged skills into ~/.claude/skills/
```

## Repo layout

For a one-page orientation of every top-level entry (active vs historical vs
generated) see [`REPO_MAP.md`](REPO_MAP.md). The package itself:

```
src/health_agent_infra/
├── cli.py                          # hai dispatcher
├── core/
│   ├── schemas.py  validate.py  config.py
│   ├── synthesis.py  synthesis_policy.py
│   ├── writeback/  state/  clean/  pull/  review/
│   ├── memory/  explain/  research/
│   └── intake/
├── domains/
│   ├── recovery/  running/  sleep/  stress/  strength/  nutrition/
│   └── each: schemas.py classify.py policy.py [+ signals/intake]
├── skills/
│   ├── recovery-readiness/  running-readiness/  sleep-quality/
│   ├── stress-regulation/  strength-readiness/  nutrition-alignment/
│   ├── daily-plan-synthesis/  intent-router/  expert-explainer/
│   └── strength-intake/  merge-human-inputs/  review-protocol/
│       reporting/  safety/
├── evals/                          # packaged eval runner + scenarios
└── data/garmin/export/              # committed CSV fixture
reporting/                          # see reporting/README.md
├── docs/                            # architecture, x_rules, non_goals, ...
├── artifacts/flagship_loop_proof/   # eval runner captures
├── plans/                           # post-v0.1 roadmap + historical phase docs
└── experiments/                     # frozen Phase 0.5 / 2.5 prototypes
safety/                             # see safety/README.md
├── tests/                           # 1489 unit + contract + integration
├── evals/                           # eval-doc reference + skill-harness pilot
└── scripts/                         # legacy pre-rebuild demo shim
```

## What's proven

- Six domains end-to-end: classify → policy → skill proposal → synthesis →
  review.
- Ten X-rule evaluators across two phases with atomic transactional commits,
  each firing carrying a stable slug and a one-sentence `human_explanation`
  agents can narrate verbatim.
- Three-state audit chain: `proposal_log` → `planned_recommendation`
  (aggregate pre-X-rule intent, migration 011) → `daily_plan` +
  `recommendation_log` → `review_outcome`. `hai explain` renders all three
  states from persisted rows alone.
- Agent CLI contract: every subcommand annotated with mutation class,
  idempotency, JSON output, exit codes, agent-safe flag; machine-readable
  manifest at `hai capabilities --json`; markdown mirror at
  [`reporting/docs/agent_cli_contract.md`](reporting/docs/agent_cli_contract.md).
  Every handler on the stable exit-code taxonomy.
- Authoritative `intent-router` skill consumes the manifest as the NL → CLI
  mapping surface; deliberately scoped so mutation commands are previewed
  before they run.
- Skill-harness pilot: 7 frozen recovery scenarios, 6 with hand-authored
  reference transcripts scoring 2.0/2.0 on the token-presence rubric;
  live-mode backend opt-in via `HAI_SKILL_HARNESS_LIVE=1`.
- Local onboarding + engagement telemetry (migration 012 `runtime_event_log`)
  surfaced via `hai stats`. No data leaves the device.
- Garmin live pull via OS keyring (`hai auth garmin` + `hai pull --live`).
- Idempotent synthesis with optional `--supersede` versioning.
- 28 eval scenarios (18 domain + 10 synthesis) — all deterministic axes green.
- **1489 tests** covering every band, every R-rule, every X-rule, atomic
  transaction semantics, proposal/synthesis invariants, skill-boundary contracts,
  capabilities-manifest coverage + determinism, planned-ledger round-trip,
  three-state explain render, and the new runtime_event_log + hai stats
  paths.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).
