# Synthetic recommendation stress harness

Command: `python3 scripts/run_synthetic_recommendation_stress_harness.py`

Passed 5 of 5 scenarios.

| Scenario | Stage | Result | Key actual |
| --- | --- | --- | --- |
| grounded-evidence-success | canonical_cli_path | PASS | `{"bundle_ok": true, "context_ok": true, "contract_ok": true, "dated_latest_bytes_match": true, "recommendation_artifact_path": "/var/folders/0x/nzg00zm516l2nzfq2z18gm4c0000gn/T/tmpbvz4wsh7/generated/agent_recommendation_2026-04-09.json", "recommendation_ok": true, "voice_note_ok": true}` |
| ungrounded-evidence-rejection-non-mutation | recommendation_create | PASS | `{"artifact_path": null, "error_code": "ungrounded_evidence_ref", "exit_code": 1, "latest_artifact_path": null, "ok": false, "preexisting_artifacts_preserved": true}` |
| wrong-user-rejection | recommendation_create | PASS | `{"artifact_path": null, "error_code": "artifact_user_mismatch", "exit_code": 1, "latest_artifact_path": null, "ok": false, "preexisting_artifacts_preserved": true}` |
| missing-context-rejection | recommendation_create | PASS | `{"artifact_path": null, "error_code": "context_artifact_not_found", "exit_code": 1, "latest_artifact_path": null, "ok": false, "preexisting_artifacts_preserved": true}` |
| voice-note-scope-mismatch-rejection | voice_note_submit | PASS | `{"accepted_ok": true, "bootstrap_ok": true, "bundle_and_context_preserved": true, "error_code": "bundle_fragment_scope_mismatch", "exit_code": 1, "ok": false}` |

Scenario definitions: `artifacts/synthetic_stress_harness/scenarios.json`
Detailed outputs: `artifacts/synthetic_stress_harness/latest/scenario_outputs`
