# Flagship loop proof audit bundle

Frozen command:

```bash
python3 scripts/run_flagship_loop_proof_audit.py
```

This bounded proof bundle is the approved context-to-recommendation audit slice.

Inputs:
- frozen context fixture: `tests/fixtures/agent_readable_daily_context/generated_fixture_day_context.json`
- positive payload: `artifacts/flagship_loop_proof/payloads/recommendation_positive_payload_2026-04-09.json`
- negative payload: `artifacts/flagship_loop_proof/payloads/recommendation_negative_payload_2026-04-09.json`

Outputs are regenerated under `artifacts/flagship_loop_proof/2026-04-09/` and include:
- copied frozen context artifact
- successful dated and latest recommendation artifacts
- successful CLI envelope
- fail-closed negative CLI envelope
- byte-preservation proof for preexisting recommendation artifacts

README/demo truth corrections live in `docs/flagship_loop_readme_demo_corrections.md`.
