# Phase 4 manual-gym prototype proof

This bundle makes the first contract-aligned manual-first Phase 4 resistance-training object layer obvious to a repo reviewer.

Current canonical set-level truth here is `gym_set_record`. Any retained `gym_exercise_set` surface in the snapshot artifact is legacy compatibility only.

Claim boundary:
- manual structured gym logs are the source-of-truth path
- `wger` stays exploratory and non-flagship
- resistance training is surfaced as a `prototype`, not `proof_complete`
- `program_block` stays explicitly deferred until real manual program metadata exists and is proved

Checked-in contents:
- `manual_gym_session_input.json`
- `training_sessions.json`
- `exercise_catalog.json`
- `exercise_alias.json`
- `gym_set_record.json`
- `daily_health_snapshot.json`
- `stable_id_evidence.json`
- `proof_manifest.json`

Smoke check:
```bash
PYTHONPATH=clean:safety python3 -m unittest safety.tests.test_manual_logging
```
