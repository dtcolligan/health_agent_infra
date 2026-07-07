# Run-ready lock evidence — 2026-07-07

The instrument is at the run-ready lock state (PILOT_PROTOCOL §21).

- PILOT_PROTOCOL.md final SHA-256 (post §21 + §14 refresh):
  `60c26947fa74bad79c04fb13ccb62fced7e9d0548f605937b569bb5f4616ac59`
- §14 Locked Hashes table refreshed over the current committed state,
  now including the run template `deployment_full_v3` (41 hashed
  inputs: 5 fixed files + 36 task files).
- Mechanical lock checklist (`lock_checklist_run_ready_2026-07-07.json`):
  lock_hashes / l7_turn_budget / schema_json_parse / scorer_config
  provenance+frozen (Amendment 9) / untold_leak_scan (rendered under the
  run template v3) all PASS. The 4 run conditions are provider-verified
  live and context-fit pass/disclosed; only the legacy provenance
  conditions are tolerated-pending. Overall:
  pending_operator_confirmation (Dom's lock call is the last gate).
- Verification: three-gate plan + a four-audit convergence loop all
  passed (§20.20 / §21). Blind twin verified (0 leaks, 75–100pp
  separation); runtime-mode blindness verified end-to-end (0 feedback
  leaks over a live off-mode run); self-enforcement holds mode-blind
  (0 unsafe, 8/8 refused).
- Together balance at last check: $40.10; auto-recharge unset; provider
  pauses usage at $0. Aggregate cost cap USD 100 (§20.1).
