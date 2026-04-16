# Health Lab canonical public demo path

This is the bounded public-safe canonical demo for the repo.

It should be read through the canonical bucket model: the demo showcases a narrow path across the current repo, mainly deterministic work implemented in the `clean` bucket, with proof artifacts in `reporting`, compatibility surfaces in `safety`, and no claim that any implementation namespace becomes a separate canonical project layer.

In particular, `clean/health_model/` is the current implementation namespace for much of this demo path. It is not itself a canonical project-shape category.

Run from repo root:

```bash
python3 reporting/scripts/run_canonical_public_demo.py
```

The wrapper resets `reporting/artifacts/public_demo/generated/`, runs the existing CLI lineage, uses the checked-in recommendation payload at `reporting/artifacts/public_demo/payloads/recommendation_payload_2026-04-09.json`, and exits non-zero if any inner step fails.

Underlying lineage executed by the wrapper:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

Expected generated artifacts:
- `reporting/artifacts/public_demo/generated/shared_input_bundle_2026-04-09.json`
- `reporting/artifacts/public_demo/generated/agent_readable_daily_context_2026-04-09.json`
- `reporting/artifacts/public_demo/generated/agent_readable_daily_context_latest.json`
- `reporting/artifacts/public_demo/generated/agent_recommendation_2026-04-09.json`
- `reporting/artifacts/public_demo/generated/agent_recommendation_latest.json`

Truth surfaces stay distinct:
- `reporting/artifacts/public_demo/generated/` is disposable runtime output from the wrapper
- `reporting/artifacts/public_demo/captured/` is the checked-in frozen public demo bundle for inspection
- `reporting/artifacts/flagship_loop_proof/2026-04-09/` is the narrower audited flagship proof bundle

## What this demo proves, and what it does not

This demo proves the older CLI-first lineage only (contract describe → bundle init → voice-note submit → context get → recommendation create). That lineage remains in the tree as compatibility but is no longer the current flagship.

The narrow flagship path `Garmin passive pull -> typed manual readiness intake -> deterministic normalization -> typed state -> policy -> bounded recommendation -> bounded local writeback -> review` was delivered 2026-04-16 as `recovery_readiness_v1`, with its own sibling proof bundles under `reporting/artifacts/flagship_loop_proof/2026-04-16-*`. Those bundles — not this wrapper — are the current flagship proof.

For truthful review:
- treat this wrapper as proof of the older CLI-first demo lineage, not the current flagship
- treat Cronometer as a bridge/reference nutrition surface outside this demo's claim and outside the current flagship
- treat manual structured gym logs as the source-of-truth path for resistance training, distinct from either proof path
- treat `wger` only as the bounded exploratory non-flagship connector prototype defined by the repo plan
- treat leftover connector residue outside that doctrine as non-canonical

## Pathing truth

Older repo wording sometimes implied a universal top-level `data/...` layout. For this canonical public demo, the public proof surfaces are under `reporting/artifacts/`, while the current implementation CLI still uses some `data/...` examples elsewhere in the repo. Use the path actually tied to the specific command or proof object you are reviewing.

## Fail-closed rejection proof

```bash
PYTHONPATH=clean:safety python3 -m health_model.agent_recommendation_cli create \
  --output-dir "$DEMO_DIR" \
  --payload-json '{"user_id":"user_dom","date":"2026-04-09","context_artifact_path":"'"$DEMO_DIR"'/agent_readable_daily_context_2026-04-09.json","context_artifact_id":"agent_context_user_dom_2026-04-09","resolution_window_artifact_path":"reporting/artifacts/public_demo/resolution_window_success_2026-04-08.json","recommendation_id":"rec_bad_evidence_01","summary":"Summary","rationale":"Rationale","evidence_refs":["not_in_context"],"confidence_score":0.8,"policy_basis":{"policy_note":"Use the same bounded window input while ensuring invalid evidence still fails closed.","prior_recommendation_refs":[{"date":"2026-04-07","recommendation_id":"rec_window_20260407_recovery_01","resolution_status":"pending_judgment"}],"window_dates_considered":["2026-04-02","2026-04-08"]}}'
```

That rejection should fail closed with error code `ungrounded_evidence_ref` and should not mutate the successful recommendation artifact.

Captured proof artifacts from this lineage:
- success artifact: `reporting/artifacts/public_demo/captured/agent_recommendation_2026-04-09.json`
- success envelope: `reporting/artifacts/public_demo/captured/recommendation_success_envelope.json`
- rejection envelope: `reporting/artifacts/public_demo/captured/recommendation_rejection_envelope_bad_evidence.json`
- explicit rejection non-mutation proof: `reporting/artifacts/public_demo/captured/recommendation_rejection_non_mutation_proof.json`
- context artifact used by the frozen recommendation: `reporting/artifacts/public_demo/captured/agent_readable_daily_context_2026-04-09.json`
