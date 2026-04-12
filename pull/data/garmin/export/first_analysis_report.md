# First Garmin export analysis

Internal runtime artifact generated from normalized Garmin export outputs.

## Coverage
- date range: 2026-02-05 -> 2026-04-08 (63 days)
- daily rows: 63
- activity rows: 28
- running activities: 26
- hydration rows: 27
- health rows: 59

## Latest day snapshot
- date: 2026-04-08
- steps: 13597
- sleep score: 84
- body battery: 43
- training readiness: LOW
- training status: PRODUCTIVE

## Recent 7-day averages
- steps: 11595
- sleep score: 83
- resting HR: 52
- body battery: 43
- acute load: None

## Week-over-week change
- steps delta vs prior 7 days: 100.86
- sleep score delta vs prior 7 days: 0.55
- resting HR delta vs prior 7 days: -0.14
- body battery delta vs prior 7 days: 9.14

## Activity summary
- total activities: 28
- total running distance: 169.2 km
- average running distance: 6.51 km
- best run: 2026-02-07 | 11.27 km | 77.8 min | avg HR 139 | load 53.8492431640625
- latest run: 2026-04-08 | 7.47 km | 48.6 min

## Interpretation
- label: absorb-and-maintain
- headline: The latest day reads like an absorb-the-work snapshot, where productive fitness can coexist with a short-term signal to keep the next move conservative.
- positives: sleep score is in a solid range, movement stayed at or above the recent weekly baseline, Garmin marks the wider block as productive
- cautions: body battery is still muted, so recovery may be only partial, readiness is low even though the broader block is productive, which usually means fitness may be building but today is not the day to force extra intensity, recovery time is still about 24 hours, so this reads as residual load rather than a green light, the latest day already contains a 7.47 km run with load 49.848052978515625, so low readiness may reflect absorbed work rather than a system failure
- note: Conservative interpretation only. This view describes training signals and recovery context, not medical status or injury risk.

## Signal availability
- sleep-score days present: 59
- training-readiness days present: 63
- HRV days present: 59
- hydration events with estimated sweat loss: 26

## Why this matters
- proves the GDPR export can become a usable analysis surface inside `garmin_lab`
- gives a first bounded runtime artifact without requiring live Garmin login
- creates a clean base for richer readiness, dashboards, and interpretation passes
