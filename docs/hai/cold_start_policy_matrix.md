# Cold-Start Policy Matrix

> **Status.** Authored 2026-04-25 as v0.1.7 W24. Documents the
> per-domain cold-start decisions; preserves the running/strength/stress
> vs recovery/sleep/nutrition asymmetry per the Codex r3 verdict.
> Ships alongside `verification/tests/test_cold_start_policy_matrix.py`
> which pins each domain's decision against this doc.

---

## What "cold-start" means in this runtime

A user's first 14 days produce noisy signals. The runtime computes a
``cold_start`` flag per domain in the snapshot
(`core/state/snapshot.py:35` — `COLD_START_THRESHOLD_DAYS = 14`),
distributed to every domain's policy evaluator via the snapshot's
per-domain block.

**Three of six domains** (running, strength, stress) honour the
``cold_start_relaxation`` rule: when the ``cold_start`` flag is set
AND the per-domain coverage check would otherwise force a defer, the
relaxation rule allows a non-defer recommendation at moderate
confidence. The rule's sole purpose is to give the system something
useful to say in the first 14 days when baselines are still forming.

**The other three** (recovery, sleep, nutrition) explicitly DO NOT
relax. This is intentional — see the per-domain rationale below.

## Per-domain decisions

### Running — RELAXES (`domains/running/policy.py:233-273`)

- **Trigger.** ``cold_start`` set AND running coverage forced defer.
- **Effect.** Allows ``proceed_with_planned_run`` at moderate
  confidence with ``cold_start_running_history_limited`` added to
  uncertainty.
- **Why this is safe.** Running readiness leans heavily on
  trailing-7d activity counts + ACWR. In the first 14 days, neither
  baseline is full, so the coverage gate would defer ~indefinitely.
  Relaxation produces useful guidance from the cleaned evidence the
  user *does* have (today's HRV / RHR / sleep / planned session) and
  honestly flags the missing baseline.
- **Why not unsafe.** A blocking recovery status (`impaired`) AND a
  blocking planned session both override the relaxation —
  ``_running_cold_start_relax`` checks for these before allowing the
  non-defer recommendation.

### Strength — RELAXES (`domains/strength/policy.py:269-302`)

- **Trigger.** ``cold_start`` set AND strength coverage forced defer
  AND planned session contains "strength" substring.
- **Effect.** Allows ``proceed_with_planned_session`` at moderate
  confidence with ``cold_start_strength_history_limited`` added to
  uncertainty.
- **Why this is safe.** Strength v1 history is opt-in (`hai intake
  gym`). Until the user logs sessions, the system has no volume
  baseline. Relaxation gives the user something to act on for their
  first session; the volume-spike R-rule still fires loudly on the
  cold-start "1 session in 28 days = 4× ratio" artifact (which is
  documented in the README's calibration timeline).

### Stress — RELAXES (`domains/stress/policy.py:255-285`)

- **Trigger.** ``cold_start`` set AND stress coverage forced defer
  AND readiness energy self-report present.
- **Effect.** Allows ``maintain_routine`` at low confidence (note:
  one tier lower than running/strength) with
  ``cold_start_stress_history_limited`` added to uncertainty.
- **Why this is safe.** Manual stress baseline only forms after ~7
  days of self-report; intervals.icu doesn't expose Garmin's all-day
  stress / body battery. Relaxation lets the system say "no signal
  yet — keep doing what you're doing" instead of indefinitely
  deferring.

### Recovery — DOES NOT RELAX (`domains/recovery/classify.py:152-166`)

- **Why no relaxation.** Recovery's ``insufficient`` coverage means
  one of the headline signals (sleep_hours, soreness self-report) is
  missing. The right response is to ASK for the signal (an
  ``intake_required`` action — closeable via `hai intake readiness`),
  not to invent a recommendation from nothing.
- **What happens at cold-start.** The same coverage check fires; the
  agent surfaces the gap-fill prompt. Once the user provides the
  signal, classification proceeds normally even on day 1.

### Sleep — DOES NOT RELAX (`domains/sleep/classify.py:158-178`)

- **Why no relaxation.** Sleep's ``insufficient`` coverage means
  ``sleep_hours`` is missing — there's literally no data to
  recommend from. Relaxation here would manufacture a sleep
  recommendation from no sleep evidence, which contradicts the
  cite-or-defer principle.
- **What happens at cold-start.** Defer with the missing-sleep
  uncertainty token. Once a wearable populates ``sleep_hours``,
  classification proceeds.

### Nutrition — DOES NOT RELAX (`domains/nutrition/classify.py:162-188`; `verification/tests/test_nutrition_cold_start_non_relaxation.py`)

- **Why no relaxation.** Nutrition is macros-only and entirely
  manual-intake-driven. ``insufficient`` means the day has no
  ``hai intake nutrition`` row at all. Without macros, there's
  nothing to align to a target — relaxation would emit an arbitrary
  number.
- **What happens at cold-start.** Defer with
  ``no_nutrition_row_for_day`` uncertainty. The agent's
  W21 next-action manifest emits an ``intake_required`` action
  for the user to log their daily total.

## Decision summary

| Domain | Relaxes? | If not, what gates the defer? | Source |
|---|---|---|---|
| Recovery | No | Missing sleep_hours OR soreness self-report | `domains/recovery/classify.py:152-166` |
| Running | Yes | (coverage forced defer & not impaired) | `domains/running/policy.py:233-273` |
| Sleep | No | Missing sleep_hours | `domains/sleep/classify.py:158-178` |
| Strength | Yes | (coverage forced defer & planned session is strength) | `domains/strength/policy.py:269-302` |
| Stress | Yes | (coverage forced defer & energy self-report present) | `domains/stress/policy.py:255-285` |
| Nutrition | No | Missing daily macros row | `domains/nutrition/classify.py:162-188` |

## How this interacts with W21

The v0.1.7 W21 next-action manifest emits ``intake_required`` actions
for the recovery/sleep/nutrition deferral cases — the manifest's
typed fields make the gap-fill discoverable to the agent without
prose lookup. For running/strength/stress, when relaxation fires the
manifest emits the normal ``skill_invocation_required`` flow at
moderate (or low, for stress) confidence.

## When to revisit this matrix

- **A new domain is added.** Decide explicitly whether it relaxes;
  add a row above + a test pin.
- **A non-relaxation domain gets a manual-intake fallback.** E.g. if
  sleep adds a `hai intake sleep --hours <n>` surface, the right
  next step is more likely "extend the intake gap detector" than
  "add cold-start relaxation."
- **A relaxation domain proves to recommend poorly during the
  cold-start window.** Tighten the relaxation guard
  conditions (the `_*_cold_start_relax` helpers each check pre-conditions
  beyond just `cold_start=True`); don't disable relaxation outright
  unless the helper's evidence shows the recommendations are
  net-harmful.

## Testing contract

`verification/tests/test_cold_start_policy_matrix.py` pins each row of
the table above. Changing a domain's decision requires updating both
this doc and the test in the same commit.
