# D4 — Cold-start coverage policy

- Author: Claude (Opus 4.7)
- Status: **Draft pending Dom's review**
- Gates: Workstream D.

---

## Problem

A user who installs v0.1.2, runs `hai init --with-auth --with-first-pull`, and then `hai daily` on their first day gets a plan with structure:

| domain | action | why |
|---|---|---|
| recovery | proceed OR defer | depends on whether intervals.icu / Garmin has HRV + RHR + sleep |
| sleep | prescription | wearable gives score + hours |
| running | **defer (forced)** | classifier requires `weekly_mileage_baseline` + `hard_session_history` — neither exists on day one |
| strength | **defer (forced)** | classifier requires `gym_session` history — empty |
| stress | **defer (forced)** | classifier requires `garmin_all_day_stress` or manual — neither on day one without intake |
| nutrition | **defer (forced)** | classifier requires a `nutrition_intake_raw` row — empty |

Four forced defers. Today's session (2026-04-23) confirmed this: even after Dom explicitly logged a planned intervals session via `hai intake readiness`, the running classifier still forced-defers because it wants a mileage baseline. That's semantically wrong — the recovery domain said "you're recovered, go intervals," and the running skill is the one that can't produce a useful recommendation for this user's first run.

The system ships optimized for the steady-state user (4+ weeks of history) and falls off a cliff on day one.

---

## Decision

**Introduce a cold-start mode** that relaxes coverage requirements in running and strength domains when:

1. The user has fewer than 14 days of history in the relevant domain, AND
2. Recovery is not red (i.e. `recovery_status ∈ {recovered, mildly_impaired}`), AND
3. A structured signal for today's intent is present (planned_session_type from manual_readiness, or a logged session).

Under cold-start, the forced-defer rule is replaced with a capped-confidence rule: the skill can produce a non-defer recommendation, but confidence is capped at `moderate`, and a `cold_start_<domain>_history_limited` token is added to the proposal's `uncertainty` array.

**Nutrition does not get cold-start relaxation.** Macro targets genuinely require a macros row; fabricating a recommendation without knowing what someone ate is medically and behaviorally wrong. Instead, nutrition's defer rationale explicitly prompts the user to log.

**Stress does not get automatic cold-start relaxation** but does get a loud signpost: if the user's readiness intake reports `energy=high` or `energy=low` with no other stress signal, the stress skill surfaces "ran on readiness subjective alone" in uncertainty and can produce a `maintain_routine` recommendation at `low` confidence.

---

## Cold-start detection

A user is in cold-start mode for a domain when:

```python
history_days = conn.execute(
    "SELECT COUNT(DISTINCT as_of_date) FROM accepted_<domain>_state_daily "
    "WHERE user_id = ? AND has_meaningful_signal(<domain>, row)",
    (user_id,),
).fetchone()[0]

is_cold_start = history_days < 14
```

Where `has_meaningful_signal(domain, row)` is a domain-specific predicate (not a `MAX(as_of_date) - MIN(as_of_date)` span — we want to count days that actually carry signal, not days with a metadata-only row):

- **running:** non-null `total_distance_m OR total_duration_s OR session_count`
- **strength:** row exists in `accepted_resistance_training_state_daily` at all (the projector only creates rows when a gym_session exists)
- **sleep:** `sleep_hours OR sleep_score_overall` non-null
- **stress:** `garmin_all_day_stress OR manual_stress_score OR body_battery_end_of_day` non-null
- **nutrition:** `calories` non-null
- **recovery:** `resting_hr OR hrv_ms` non-null

Cold-start detection happens once per synthesis, in the snapshot-builder; the result is attached to each domain block as `snapshot.<domain>.cold_start = bool`.

**Graduation:** the user leaves cold-start for a domain once `history_days >= 14`. No manual toggle, no per-user configuration — the relaxation is keyed purely on data presence.

---

## Per-domain cold-start rules

### Running

Current rule (simplified):

```python
if coverage_band == 'insufficient':
    forced_action = 'defer_decision_insufficient_signal'
```

Cold-start replacement:

```python
if coverage_band == 'insufficient':
    if not cold_start:
        forced_action = 'defer_decision_insufficient_signal'
    elif recovery_status in {'impaired'}:
        forced_action = 'defer_decision_insufficient_signal'
    elif planned_session_type is None:
        forced_action = 'defer_decision_insufficient_signal'
    else:
        # Cold-start relaxation: allow skill to produce a non-defer
        # recommendation, but cap confidence at moderate and tag
        # the uncertainty.
        forced_action = None
        capped_confidence = 'moderate'
        classified_state['uncertainty'].append(
            'cold_start_running_history_limited'
        )
```

Effect on today's session: with recovery=recovered and planned_session_type=intervals_4x4_z4_z2, the running skill would have produced `action=proceed_with_planned_run, confidence=moderate, uncertainty=[cold_start_running_history_limited, ...]` instead of defer.

### Strength

Current rule: forced-defer when no gym_session rows exist in recent window.

Cold-start replacement:

```python
if coverage_band == 'insufficient':
    if not cold_start:
        forced_action = 'defer_decision_insufficient_signal'
    elif recovery_status == 'impaired':
        forced_action = 'defer_decision_insufficient_signal'
    elif planned_session_type and 'strength' in planned_session_type.lower() or has_recent_gym_note_recency_signal:
        forced_action = None
        capped_confidence = 'moderate'
        classified_state['uncertainty'].append(
            'cold_start_strength_history_limited'
        )
    else:
        # No planned strength, no recent signal — honest defer
        forced_action = 'defer_decision_insufficient_signal'
```

Note: `has_recent_gym_note_recency_signal` is a **rejected design**: per D2, notes don't feed classifiers. The check is purely on `planned_session_type` from readiness. Users who want strength recommendations must explicitly indicate strength in their readiness intake ("planned_session_type=strength_legs") or log a gym session.

### Nutrition

**No cold-start relaxation.** Nutrition genuinely needs today's macros. Cold-start users see:

```
## ⚪ Nutrition — not enough information to recommend

You haven't logged any nutrition for today, and I don't have a
history of your typical macros. My recommendation would be made up.

**What would unblock me:** `hai intake nutrition --calories N --protein-g N
--carbs-g N --fat-g N` with today's totals. Even rough estimates help —
I'll get better as you log more days.
```

The `hai today` renderer detects `cold_start_nutrition=true` and uses this explicit "make up" language instead of the generic defer message.

### Stress

Relaxation is lighter than running/strength: if any subjective signal is available (readiness's energy band is set), the stress skill can produce `maintain_routine` at `low` confidence with uncertainty tag `cold_start_stress_history_limited`. Without any signal at all, still defer.

### Recovery

Recovery's coverage rules already handle the case where HRV/RHR/sleep are present but training_readiness is missing (degrading coverage from full → partial). No cold-start change needed. A first-time user with HRV + RHR from intervals.icu gets a real recovery recommendation on day one.

### Sleep

Sleep has a similar situation to recovery: Garmin/intervals.icu sleep score + hours is usually enough to produce a recommendation on day one. No cold-start change needed.

---

## Interaction with `hai today`

Each cold-start recommendation's prose includes a one-line footer:

```
_Note: you're in the first 14 days of using the agent. My running
recommendations will get more specific as session history accumulates._
```

This sets expectations honestly — the user knows why confidence is capped and knows the system gets better with use. Only shown once per domain per day (not on every rerun of `hai today`).

---

## Interaction with `hai init --interactive` (optional, stretch goal)

An interactive first-run flow that populates baseline intakes:

```
$ hai init --interactive

Welcome to health-agent-infra. I'll ask a few questions so your first
plan has something real to work with. This takes ~3 minutes.

[1/5] What training goals are you focused on right now?
  (free text, e.g. "improving my 5k time, building SBD strength")

[2/5] Can you describe your typical training week?
  - How many runs? What kinds (easy, threshold, intervals)?
  - How many gym sessions? What split (full body, push/pull/legs, etc.)?
  - Rest days?
  (open-ended; I'll parse and log baseline sessions)

[3/5] Have you trained anything in the last 3 days?
  (I'll log recent sessions as recency signals)

[4/5] Roughly, what are your typical daily macros?
  (calories, protein, carbs, fat — rough is fine)

[5/5] Any injuries, constraints, or things I should remember?
  (goes into user_memory as a constraint)

Seeding state...
  - 2 goals → user_memory
  - 3 baseline runs → running_session (synthetic, tagged `seeded_baseline`)
  - 4 baseline gym sessions → gym_session
  - 1 nutrition target → nutrition_intake_raw (tagged `typical_week`)
  - 1 constraint → user_memory

Ready. Run `hai daily` to get your first plan.
```

**This is a stretch goal for v0.1.4.** If cold-start mode alone gives an acceptable first-day experience (likely), `hai init --interactive` can wait for v0.1.5 with more UX investment. Acceptance criterion in §Test coverage below covers cold-start mode's adequacy.

---

## Code touch-points

- `src/health_agent_infra/core/state/snapshot.py`:
  - `build_snapshot` computes per-domain `history_days` and `cold_start` booleans.
  - Attaches to each domain block.
- `src/health_agent_infra/domains/running/policy.py`:
  - `evaluate_policy` honors cold-start relaxation as specified.
- `src/health_agent_infra/domains/strength/policy.py`:
  - Same shape.
- `src/health_agent_infra/domains/stress/policy.py`:
  - Lighter relaxation as specified.
- `src/health_agent_infra/domains/nutrition/policy.py`:
  - No logic change; renderer change below handles the cold-start-specific message.
- `src/health_agent_infra/skills/running-readiness/SKILL.md`:
  - Skill gains "Cold-start adjustments" section: when `classified_state.uncertainty` contains `cold_start_running_history_limited`, the skill's action matrix still runs but capped_confidence is honored.
- Same addition in strength-readiness, stress-regulation, nutrition-alignment SKILL.md's.
- `src/health_agent_infra/core/narration/templates.py`:
  - Cold-start-specific defer/prescription templates for `hai today` prose.
  - Per-domain one-line cold-start footer.

---

## Test coverage (acceptance criteria)

1. **Unit: cold-start detection.** Seed zero history → `cold_start=true`. Seed 13 days → `cold_start=true`. Seed 14+ days → `cold_start=false`. Assert for each domain independently.
2. **Unit: running cold-start with green recovery + planned session → non-defer.** Seed recovery=recovered, no running history, readiness has planned_session_type=intervals. Run policy. Assert `forced_action is None`, `capped_confidence == 'moderate'`, uncertainty includes `cold_start_running_history_limited`.
3. **Unit: running cold-start with red recovery → still defer.** Same setup but recovery=impaired. Assert `forced_action == 'defer_decision_insufficient_signal'`.
4. **Unit: running cold-start without planned session → still defer.** Setup without planned_session_type. Assert defer.
5. **Unit: strength cold-start only on explicit strength intent.** Seed cold-start, readiness planned_session_type="run_z2" (no strength). Assert strength still defers. Seed planned_session_type="strength_legs". Assert strength allows non-defer with cold-start uncertainty.
6. **Unit: stress cold-start with energy signal.** Seed cold-start, readiness energy=high. Assert stress can produce `maintain_routine` at low confidence with cold-start uncertainty.
7. **Unit: nutrition never gets cold-start relaxation.** Seed cold-start, readiness planned_session_type=whatever. Assert nutrition always defers when no nutrition row exists.
8. **Unit: graduation at 14 days.** Seed exactly 14 days of running history. Assert cold_start=false. Assert normal policy rules apply (no cold-start uncertainty tag added even with sparse coverage).
9. **Integration: `hai today` shows cold-start footer.** Seed a cold-start running recommendation. Run `hai today`. Assert footer line about 14-day window is present. Run again. Assert footer not duplicated (once per domain per day).
10. **E2E: first-run user journey.** Fresh DB, intervals.icu pull, `hai intake readiness` with planned_session_type, `hai daily`. Assert running produces `proceed_with_planned_run` at moderate confidence with cold-start uncertainty. `hai today` renders it with the footer. This is the scenario Workstream E uses to validate cold-start's day-one adequacy.

---

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Cold-start mode produces overconfident recommendations that cause users to train poorly | Confidence is capped at moderate; cold-start uncertainty tag is prominently narrated in `hai today`; footer sets expectations. The recovery domain still gates via recovery_status so cold-start never overrides a red recovery signal. |
| Users misinterpret the 14-day window as a promise of accuracy after 14 days | Narration says "will get more specific as history accumulates," not "will be accurate." Explicit hedging throughout. |
| `history_days` calculation is wrong for users who pause the agent for weeks | The predicate counts days with *meaningful signal*, not elapsed days. A user who skips 30 days then returns stays in cold-start only if their accumulated-signal history is still under 14 days. Reasonable for the use case; documented. |
| Strength cold-start's reliance on planned_session_type substring matching ("strength_legs", "strength_pull") is fragile | Add a structured enum in readiness intake for session category (running / strength / rest / crosstrain) to v0.1.5; for v0.1.4, documented substring-match is acceptable and tested. |
| Cold-start footer bloats `hai today` output | Single-line, per-cold-start-domain. At most 6 lines of footer on a day-one plan; shrinks to zero as the user graduates. |

---

## Explicit non-goals

- **No synthetic historical data generation.** `hai init --interactive` (if shipped) writes baseline intakes from user declarations, not extrapolated history.
- **No cold-start for sleep, recovery.** Those domains have adequate day-one coverage from wearable alone. Adding cold-start machinery to them is over-engineering.
- **No user-tunable cold-start window.** 14 days is hardcoded in v0.1.4. Configurability can come later.
- **No graduation celebration / notification.** When the user leaves cold-start, nothing happens visibly. The uncertainty tag and footer simply stop appearing. Adding "you've graduated!" notifications is product-surface work for v0.1.5+.
- **No ML-style cold-start remediation** (e.g. population-level defaults, collaborative-filtering-style "users like you..."). This is a local, single-user, governed agent; such remediation contradicts the system's design goals.
