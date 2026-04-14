# Phase 4 manual-gym prototype proof

This bundle makes the first bounded Phase 4 manual-gym deliverable obvious to a repo reviewer.

Claim boundary:
- manual structured gym logs are the source-of-truth path
- `wger` stays exploratory and non-flagship
- resistance training is surfaced as a `prototype`, not `proof_complete`

Checked-in contents:
- `manual_gym_session_input.json`
- `training_sessions.json`
- `gym_exercise_sets.json`
- `daily_health_snapshot.json`
- `stable_id_evidence.json`
- `proof_manifest.json`

Smoke check:
```bash
PYTHONPATH=clean:safety python3 -m unittest safety.tests.test_manual_logging
```
