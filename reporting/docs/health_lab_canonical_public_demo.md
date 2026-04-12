# Health Lab canonical public demo path

This is the bounded public-safe canonical demo for the repo.

It should be read as a narrow proof of the current deterministic infrastructure lane, mainly PULL/CLEAN plus one model handoff point, not as a claim that interpretation and reporting belong inside `health_model`.

For the current reset slice, `health_model/` is the truthful implementation namespace and `health_agent_infra/` remains compatibility-only.

Run from repo root:

```bash
python3 scripts/run_canonical_public_demo.py
```

The wrapper resets `artifacts/public_demo/generated/`, runs the existing CLI lineage, uses the checked-in recommendation payload at `artifacts/public_demo/payloads/recommendation_payload_2026-04-09.json`, and exits non-zero if any inner step fails.

Underlying lineage executed by the wrapper:

`contract describe -> bundle init -> voice-note submit -> context get -> recommendation create`

Expected generated artifacts:
- `artifacts/public_demo/generated/shared_input_bundle_2026-04-09.json`
- `artifacts/public_demo/generated/agent_readable_daily_context_2026-04-09.json`
- `artifacts/public_demo/generated/agent_readable_daily_context_latest.json`
- `artifacts/public_demo/generated/agent_recommendation_2026-04-09.json`
- `artifacts/public_demo/generated/agent_recommendation_latest.json`

Truth surfaces stay distinct:
- `artifacts/public_demo/generated/` is the disposable runtime output from the one-command wrapper
- `artifacts/public_demo/captured/` is the checked-in frozen public demo bundle for inspection
- `artifacts/flagship_loop_proof/2026-04-09/` is the narrower audited flagship proof bundle

Fail-closed rejection proof:

```bash
python3 -m health_model.agent_recommendation_cli create \
  --output-dir "$DEMO_DIR" \
  --payload-json '{"user_id":"user_dom","date":"2026-04-09","context_artifact_path":"'"$DEMO_DIR"'/agent_readable_daily_context_2026-04-09.json","context_artifact_id":"agent_context_user_dom_2026-04-09","resolution_window_artifact_path":"artifacts/public_demo/resolution_window_success_2026-04-08.json","recommendation_id":"rec_bad_evidence_01","summary":"Summary","rationale":"Rationale","evidence_refs":["not_in_context"],"confidence_score":0.8,"policy_basis":{"policy_note":"Use the same bounded window input while ensuring invalid evidence still fails closed.","prior_recommendation_refs":[{"date":"2026-04-07","recommendation_id":"rec_window_20260407_recovery_01","resolution_status":"pending_judgment"}],"window_dates_considered":["2026-04-02","2026-04-08"]}}'
```

That rejection should fail closed with error code `ungrounded_evidence_ref` and should not mutate the successful recommendation artifact. The payload now also needs `resolution_window_artifact_path` plus `policy_basis`, matching the current recommendation contract. If you still need the legacy compatibility lane for an older proof surface, `health_agent_infra.agent_recommendation_cli` remains available, but it is no longer the taught default for this public demo path.

Captured proof artifacts from this exact lineage:
- success artifact: `artifacts/public_demo/captured/agent_recommendation_2026-04-09.json`
- success envelope: `artifacts/public_demo/captured/recommendation_success_envelope.json`
- rejection envelope: `artifacts/public_demo/captured/recommendation_rejection_envelope_bad_evidence.json`
- explicit rejection non-mutation proof: `artifacts/public_demo/captured/recommendation_rejection_non_mutation_proof.json`
- context artifact used by the frozen recommendation: `artifacts/public_demo/captured/agent_readable_daily_context_2026-04-09.json`
