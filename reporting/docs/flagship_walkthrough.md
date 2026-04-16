# Flagship Walkthrough — recovery_readiness_v1

Status: Phase 3 public-proof artifact. First landed 2026-04-16.

This is the outsider-legible walkthrough of Health Lab's flagship loop. It
shows, end to end, how one day's worth of user-owned health evidence becomes
one bounded, typed recommendation with a follow-up review. It is the fastest
way to see what Health Lab actually does today.

If you want the doctrine behind the walkthrough, read
[canonical_doctrine.md](canonical_doctrine.md) and
[flagship_loop_spec.md](flagship_loop_spec.md). This doc is the concrete
equivalent of those specs.

## The shape in one line

```
PULL -> CLEAN -> STATE -> POLICY -> RECOMMEND -> ACTION -> REVIEW
```

Each layer does one job, emits typed output, and is inspectable. The
captured proof artifact lives at
[reporting/artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/](../artifacts/flagship_loop_proof/2026-04-16-recovery-readiness-v1/).

## Run it locally in one command

From repo root:

```bash
PYTHONPATH=clean:safety python -m health_model.recovery_readiness_v1.cli run \
  --scenario mildly_impaired_with_hard_plan \
  --base-dir /tmp/recovery_readiness_v1 \
  --date 2026-04-16 \
  --now 2026-04-16T07:15:00+00:00 \
  --record-review-outcome followed_and_improved
```

Output:

```
scenario:          mildly_impaired_with_hard_plan
as_of_date:        2026-04-16
recovery_status:   mildly_impaired
readiness_score:   0.55
coverage:          full
uncertainties:     (none)
action:            downgrade_hard_session_to_zone_2
confidence:        high
policy_decisions:
  - require_min_coverage: allow — coverage=full, required inputs present
review_at:         2026-04-17T07:00:00+00:00
writeback:         /tmp/recovery_readiness_v1/recommendation_log.jsonl
```

## Walking the layers

### PULL (synthetic in this phase)

The user's recent Garmin sleep, resting HR, HRV, and training-load records,
plus a typed manual readiness check-in submitted today. In this phase the
PULL layer is a synthetic fixture matching the real Garmin export shape.
Wiring a live pull in is a follow-on slice; the CLEAN layer's contract
does not change.

### CLEAN

Turns raw records into one typed `CleanedEvidence` object: today's values,
14-day baselines for resting HR and HRV, a trailing 7-day training load,
and a count of consecutive days where resting HR has been well above
baseline. No interpretation. Missing values are kept as `None` so the
STATE layer can decide what they mean.

### STATE

Produces a typed `recovery_state.v1` object. The scenario above yields
(abridged):

```json
{
  "schema_version": "recovery_state.v1",
  "recovery_status": "mildly_impaired",
  "readiness_score": 0.55,
  "sleep_debt": "mild",
  "soreness_signal": "moderate",
  "resting_hr_vs_baseline": "above",
  "hrv_vs_baseline": "below",
  "training_load_trailing_7d": "high",
  "signal_quality": {
    "coverage": "full",
    "required_inputs_present": true,
    "notes": []
  },
  "uncertainties": []
}
```

State is first-class. The RECOMMEND layer reads only from this object, not
from the raw evidence. That constraint is what lets the system be
inspectable.

### POLICY

Seven executable rules run in order before a recommendation is emitted:

1. `require_min_coverage` — block if coverage is `insufficient`
2. `no_diagnosis` — block if rationale contains diagnosis-shaped tokens
3. `bounded_action_envelope` — block if the action is outside the v1 enum
4. `review_required` — block if there is no review event in the next 24h
5. `no_high_confidence_on_sparse_signal` — soften `high` to `moderate`
6. `resting_hr_spike_escalation` — escalate on persistent 3-day RHR spike
7. `writeback_locality` — block at the ACTION boundary if writeback
   targets anything other than a local recommendation log

See [minimal_policy_rules.md](minimal_policy_rules.md) for full definitions.

### RECOMMEND

Produces a typed `training_recommendation.v1`. For the scenario above:

```json
{
  "schema_version": "training_recommendation.v1",
  "action": "downgrade_hard_session_to_zone_2",
  "action_detail": {
    "target_intensity": "zone_2",
    "target_duration_minutes": 45
  },
  "rationale": [
    "sleep_debt=mild",
    "soreness_signal=moderate",
    "resting_hr_vs_baseline=above",
    "training_load_trailing_7d=high",
    "hrv_vs_baseline=below"
  ],
  "confidence": "high",
  "uncertainty": [],
  "follow_up": {
    "review_at": "2026-04-17T07:00:00+00:00",
    "review_question": "Did yesterday's downgrade to Zone 2 improve how today feels?"
  },
  "policy_decisions": [
    { "rule_id": "require_min_coverage", "decision": "allow", "note": "coverage=full, required inputs present" }
  ],
  "bounded": true
}
```

### ACTION

Appends the recommendation to a local `recommendation_log.jsonl` and a
daily plan markdown note. Idempotent on `recommendation_id`. The function
refuses to write outside the configured local writeback root. There are no
external side effects in this phase.

### REVIEW

Schedules a `ReviewEvent` for the next morning, and records a
`ReviewOutcome` once the user answers the follow-up question. Outcomes are
linked to the originating recommendation via `recommendation_id` so the
loop is closable. Without this layer, the system would be a one-shot
response, not an agentic loop.

## Other scenarios in the captured proof

The proof artifact captures eight scenarios. Each one demonstrates a
different facet of the runtime:

| scenario | shows |
|---|---|
| `recovered_with_easy_plan` | green path: proceed as planned |
| `mildly_impaired_with_hard_plan` | bounded intensity downgrade |
| `impaired_with_hard_plan` | stronger downgrade to mobility only |
| `rhr_spike_three_days` | R4 escalation for persistent resting-HR spike |
| `insufficient_signal` | R1 policy block; system defers rather than guesses |
| `sparse_signal` | confidence downgrade when coverage is thin |
| `tailoring_recovered_strength_block` | goal-conditioned action-parameter variance on identical evidence (paired) |
| `tailoring_recovered_endurance_taper` | paired alternate goal produces different session-detail caps |

All eight are reproducible by swapping the `--scenario` argument in the
command above. A ninth capture, `--source real`, runs the same loop
against the committed Garmin CSV export — see
[reporting/artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/](../artifacts/flagship_loop_proof/2026-04-16-garmin-real-slice/).

## What this proves

- There is one narrow flagship loop, end-to-end, with real code.
- State is typed, versioned, and visible.
- Policy runs as executable rules and leaves an audit trail.
- Recommendations are bounded, structured, and carry explicit confidence
  and uncertainty.
- Writebacks are local, reversible, and idempotent.
- The review layer exists and closes the loop.

## What this does not claim

- PULL is not yet wired to a live Garmin account in this artifact.
- The readiness score is a deterministic heuristic, not a calibrated
  output.
- Nothing here is medical, clinical, or a diagnosis.

See [explicit_non_goals.md](explicit_non_goals.md) for the full deferred
list.
