# Health Lab canonical public demo path

This is the bounded public-safe flagship loop for the repo.

Run from repo root:

```bash
DEMO_DIR="$PWD/artifacts/public_demo/generated"
FIXTURE_PATH="$PWD/tests/fixtures/voice_note_intake/daily_voice_note_input.json"

rm -rf "$DEMO_DIR"
mkdir -p "$DEMO_DIR"

python3 -m health_model.agent_contract_cli describe

python3 -m health_model.agent_bundle_cli init \
  --bundle-path "$DEMO_DIR/shared_input_bundle_2026-04-09.json" \
  --user-id user_dom \
  --date 2026-04-09

python3 -m health_model.agent_voice_note_cli submit \
  --bundle-path "$DEMO_DIR/shared_input_bundle_2026-04-09.json" \
  --output-dir "$DEMO_DIR" \
  --user-id user_dom \
  --date 2026-04-09 \
  --payload-path "$FIXTURE_PATH"

python3 -m health_model.agent_context_cli get \
  --artifact-path "$DEMO_DIR/agent_readable_daily_context_2026-04-09.json" \
  --user-id user_dom \
  --date 2026-04-09

python3 -m health_model.agent_recommendation_cli create \
  --output-dir "$DEMO_DIR" \
  --payload-json '{"user_id":"user_dom","date":"2026-04-09","context_artifact_path":"'"$DEMO_DIR"'/agent_readable_daily_context_2026-04-09.json","context_artifact_id":"agent_context_user_dom_2026-04-09","recommendation_id":"rec_20260409_recovery_01","summary":"Keep training easy and prioritize recovery inputs today.","rationale":"The submitted voice note grounds low energy, soreness, and same-day training load, so the safe next step is a lighter day.","evidence_refs":["subjective_01JQVOICESUBJ01","event_01JQVOICELEGS1"],"confidence_score":0.82}'
```

Expected generated artifacts:
- `artifacts/public_demo/generated/shared_input_bundle_2026-04-09.json`
- `artifacts/public_demo/generated/agent_readable_daily_context_2026-04-09.json`
- `artifacts/public_demo/generated/agent_readable_daily_context_latest.json`
- `artifacts/public_demo/generated/agent_recommendation_2026-04-09.json`
- `artifacts/public_demo/generated/agent_recommendation_latest.json`

Fail-closed rejection proof:

```bash
python3 -m health_model.agent_recommendation_cli create \
  --output-dir "$DEMO_DIR" \
  --payload-json '{"user_id":"user_dom","date":"2026-04-09","context_artifact_path":"'"$DEMO_DIR"'/agent_readable_daily_context_2026-04-09.json","context_artifact_id":"agent_context_user_dom_2026-04-09","recommendation_id":"rec_bad_evidence_01","summary":"Summary","rationale":"Rationale","evidence_refs":["not_in_context"],"confidence_score":0.8}'
```

That rejection should fail closed with error code `ungrounded_evidence_ref` and should not mutate the successful recommendation artifact.

Captured proof artifacts from this exact lineage:
- success artifact: `artifacts/public_demo/captured/agent_recommendation_2026-04-09.json`
- success envelope: `artifacts/public_demo/captured/recommendation_success_envelope.json`
- rejection envelope: `artifacts/public_demo/captured/recommendation_rejection_envelope_bad_evidence.json`
- context artifact used by the frozen recommendation: `artifacts/public_demo/captured/agent_readable_daily_context_2026-04-09.json`
