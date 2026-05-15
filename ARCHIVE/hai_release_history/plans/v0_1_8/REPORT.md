# v0.1.8 — Report: from "agent-driven contract" to "agent-driven feedback loop"

> **Provenance.** Authored at the close of v0.1.7. Backing context:
> v0.1.6 fixed structural correctness; v0.1.7 made the agent flow
> first-class with a typed `next_actions[]` manifest. The product is
> now ergonomic for an agent — but it still has no feedback loop. A
> day commits, the agent narrates, the user logs an outcome, and...
> nothing happens. Outcomes don't tune confidence; reviews don't
> shift thresholds; multi-day patterns aren't surfaced; the agent
> can't say "your last 14 days suggest your sleep_debt threshold is
> too tight." That's the v0.1.8 thesis.
>
> Companion: `PLAN.md` (the implementation plan) and
> `codex_audit_prompt.md` (the brief for Codex review).

---

## 1. Where the project is right now (post v0.1.7)

### Strong, working surface

- **Three real determinism boundaries** (`hai propose`,
  `hai synthesize`, `hai review record`) with named invariants and
  defence-in-depth at every entry point.
- **Honest agent contract** — `hai daily --auto` emits a typed
  `next_actions[]` manifest; an agent can plan a fixture day
  end-to-end without intent-router prose lookup
  (`safety/tests/test_daily_auto_manifest_fixture.py`).
- **No silent data forks** — review-outcome validator runs at both
  CLI and library entry points; cmd_propose dual-write contract
  surfaces projection failures loudly; reproject orphan-prevents.
- **Cold-start asymmetry documented + pinned** (W24 +
  `cold_start_policy_matrix.md`).
- **Skill ↔ CLI drift caught in CI** including allowed-tools
  frontmatter consistency (W25). Five skills already cleaned of
  documented drift.
- **Local-first, governed, auditable** — every state mutation goes
  through a typed CLI surface; JSONL is the durability boundary.
- **1943 tests passing** — zero locked broken behaviours.

### What v0.1.7 didn't close

The audit cycle surfaced specific items deferred to v0.1.8:

- **W22 actual PyPI publish** — version is at `0.1.7` in
  `pyproject.toml`; the `twine upload dist/*` step is operator-only.
- **W27** property-based projector tests (Codex scoped down: start
  with deterministic-replay fixtures + Hypothesis around small
  factories).
- **W28** `hai stats --funnel --since N` user-facing surface — the
  telemetry inputs landed (`runtime_event_log.context_json` carries
  proposal-gate outcomes per W21), but the funnel command itself
  didn't ship.
- **W29** `cli.py` split (Codex deferred — too noisy alongside
  agent-contract changes).
- **W30** Public Python API stability (Codex deferred — needs
  supported-API definition first).

### What the project still doesn't do (the structural gaps)

This is the v0.1.8 opportunity space. Each gap is something a user
who's been running the agent for 30+ days can articulate but the
runtime can't action.

**A. No feedback loop from outcomes.** Review outcomes (W12) are
typed, validated, and persisted. They are **not** consumed
anywhere. The runtime never reads `review_outcome` rows when
generating a future plan. A user who consistently reports "I
followed the recommendation but felt worse" gets the same
recommendation pattern day after day. The `non_goals.md` doc is
explicit that "review outcomes do not yet feed confidence
calibration" — but that's where the value is.

**B. No multi-day pattern surface.** `hai stats` reports last-sync
+ recent events. There's no "your last 14 days" view. No
"recommendations followed vs ignored, by domain." No "days where
sleep_quality_band=fair correlated with stress_state=elevated."
The data is there; the surface isn't.

**C. No confidence calibration.** The runtime emits `low /
moderate / high` confidence on every proposal. Those values are
fixed by the per-domain skill matrix; they never adjust based on
how often the user actually followed the recommendation or
whether the outcome matched the prediction. A v0.2 story might
introduce learned weights; a v0.1.8 story should at least surface
calibration data so the maintainer can see whether the static
weights are sane.

**D. No threshold authoring / audit surface.** The runtime already
loads user threshold overrides via the platformdirs TOML path and
`hai config show` can print the merged effective config. The missing
surface is discoverable editing, validation, diffing, and auditability:
a user can technically override numbers, but there is no safe CLI path
for understanding or changing them.

**E. No agent-side memory of "what worked."** The user_memory
table (migration 007) holds explicit context (goals, preferences,
constraints) but no implicit learnings. An agent reading the
snapshot has no "your last week's pattern was X" handle.

**F. No multi-day plan surface.** Recommendations are per-day,
per-domain. There's no concept of "this week's training plan" or
"recovery week." A user planning a hard week + an easy week has
to communicate that intent through readiness intake every morning
instead of stating it once.

**G. No agent self-evaluation.** The agent makes choices (which
skill to invoke, which intake to request, how to narrate). Those
choices are not evaluated end-to-end against any fixture, so
regression in agent behaviour can't be caught the way runtime
regression can. The skill-harness blocker
(`safety/evals/skill_harness_blocker.md`) covers part of this but
remains operator-driven.

**H. No data-quality surface.** When the agent gets confusing
results (e.g. today's strength escalation from a cold-start
volume artifact in the 2026-04-25 user session), the user has no
quick way to ask "is this signal real or a coverage artifact?"
The expert-explainer skill (W17) covers concept questions but
not "explain THIS specific recommendation against THIS specific
data."

**I. No graceful onboarding.** A fresh `hai init` user gets a
cold DB, low-confidence recommendations, the volume-spike
escalation on first strength session, and a calibration timeline
that says "wait 90 days for steady state." The README documents
this but doesn't smooth it. A first-week experience that emits
"you're in cold-start, here's what would help us calibrate
faster" would change the first impression.

### Inferred success criteria (refined since v0.1.7)

Adding to the v0.1.7 read of success:

- **The agent should learn from outcomes.** Not in an ML sense;
  in a "the system surfaces patterns the maintainer can act on"
  sense.
- **The runtime should respect the user's own data over fixed
  defaults.** User overrides already load; the next step is safe
  config validation/diffing plus explicit intent and target state.
- **Multi-day continuity should be a first-class concept.** Days
  aren't independent draws; training cycles, recovery weeks, and
  travel matter.
- **Onboarding should not require reading the calibration
  timeline.** The system should explain itself in week 1.

---

## 2. Where v0.1.8 should aim

Three investment pillars. Maintainer picks the lead; the others
are follow-ons.

### Investment X — "Outcome-aware agent"

Close the feedback loop. Concretely:

- **Code-owned review summaries**: the runtime reads recent
  `review_outcome` rows, computes deterministic summary tokens and
  denominators, and exposes them in the snapshot. Skills narrate the
  tokens; they do not compute them or change actions from them.
- **`hai stats --outcomes [--domain <d>] [--since N]`**: surfaces
  followed/not-followed counts, self-reported-improvement rates,
  intensity-delta distribution. The funnel surface from W28, but
  through the outcomes lens.
- **Outcome-derived uncertainty tokens**: when the last 7 days
  show >50% "followed but felt worse," the next proposal carries
  `outcome_pattern_recent_negative` in its uncertainty list. No
  threshold tuning, just visibility — the agent and the user
  decide what to do with it.

### Investment Y — "Per-user calibration surface"

- **`hai config show` + `hai config validate`**: surface the
  active threshold values so a user can read what they're being
  classified against.
- **Threshold override authoring / diffing**: user overrides already
  load through the config layer; v0.1.8 should add safe validation,
  diffing, and optional set-with-reason authoring so changes are
  inspectable rather than hand-edited silently.
- **`hai stats --baselines`**: shows the user's actual
  trailing-7d / trailing-28d values for every band. So "my HRV
  baseline is 86 not 65" becomes legible without SQL.

### Investment Z — "Agent regression eval"

- **Skill-harness next step** per
  `safety/evals/skill_harness_blocker.md` §127–145: scope to
  recovery + strength live transcripts; score against a fixture
  corpus.
- **Synthesis-skill scoring**: the daily-plan-synthesis skill
  (W25) currently has no eval. Build a tiny rubric: does the
  rationale cite the actual Phase A firings? Does it claim
  things outside the proposal bands?
- **Manifest-shape eval**: extend `test_daily_auto_manifest_fixture.py`
  to cover defer paths, supersede chains, and mid-day re-planning
  (Codex r2 W21 nit).

### Investment W (smaller, name-sized)

- **`hai daily --explain`**: per-stage explainability — `gaps`
  stage names which evidence triggered each gap; `proposal_gate`
  stage names which proposal pinned each band. This is the
  per-day expert-explainer (where W17 was for concepts).
- **PyPI publish + first public install verification**: W22
  carried over, plus a fresh-machine smoke transcript captured
  in the next release proof.
- **CHANGELOG discipline**: every workstream commit references
  the changelog entry it modifies. (Currently the discipline is
  "update at release time." Move to per-commit.)

### Explicitly OUT of scope for v0.1.8

- ML / learned models. Out per `non_goals.md`.
- Multi-user / cloud sync. Out per `non_goals.md`.
- Web UI. Out per `non_goals.md`.
- v0.2 redesign work.
- `cli.py` split (Codex deferred this from v0.1.7; keep deferred
  unless other refactors create the right window).

---

## 3. The proposal

**Lead with X (outcome-aware agent).** It's the highest-leverage
gap — the one a user who's been running the system for a month
articulates as "why doesn't this learn?" The answer is "it can't
without consumption surfaces"; X builds those surfaces.

**Y (per-user calibration) follows X** because outcome-derived
uncertainty is more useful when the user can also see their
actual band cutoffs and adjust them.

**Z (agent regression eval) lands in parallel** — it's
test-suite work that doesn't depend on X/Y, and it's the only
lever for catching agent-side regression as the surface grows.

**W (smaller items) opportunistic** — `hai daily --explain` and
the PyPI publish are short, high-impact, and unblock things.

The full workstream catalogue lives in `PLAN.md`. This report
establishes the WHY.
