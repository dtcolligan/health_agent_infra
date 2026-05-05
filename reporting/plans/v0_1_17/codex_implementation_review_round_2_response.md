# Codex Implementation Review — v0.1.17 Round 2

**Verdict:** SHIP_WITH_NOTES
**Round:** 2

## Verification summary
- Tree state: `/Users/domcolligan/health_agent_infra`, branch `main`; `e04c86f..HEAD` has the expected 7 commits (6 IR-R1 fixes + provenance commit `82c5ed5`). Pre-existing tracked state remains `M uv.lock`; I did not touch it.
- Test surface: `uv run pytest verification/tests -q` passed (`2688 passed, 5 skipped`); `HAI_RUN_PERSONA_MATRIX=1 uv run pytest verification/tests/test_w_vb_4_persona_matrix_baseline.py -q` passed (`1 passed`); `uv run pytest verification/tests/test_w_ai_2_eval_review.py -q` passed (`13 passed`); `uv run pytest verification/tests/test_w_d_arm2_target_plumbing.py -q` passed (`7 passed`).
- Ship gates: `uvx mypy src/health_agent_infra` clean on 147 source files; `uvx bandit -ll -r src/health_agent_infra` clean with 0 Medium / 0 High and 27 B608/B108 suppressions skipped; `uv run hai eval run --scenario-set all` passed 135/135; capabilities markdown is byte-stable against `reporting/docs/agent_cli_contract.md`; parser/capability snapshots passed; wheel-content smoke passed (`2 passed, 1 skipped`) and the v0.1.17 wheel contains `health_agent_infra/cli/__init__.py` but not top-level `health_agent_infra/cli.py`.

## Findings

### F-IR-R2-01. RELEASE_PROOF W-D row still says 6 acceptance tests
**Q-bucket:** ship-gate honesty / F-IR-03 closure
**Severity:** nit
**Reference:** `reporting/plans/v0_1_17/RELEASE_PROOF.md:23`; `verification/tests/test_w_d_arm2_target_plumbing.py:335`
**Argument:** F-IR-03 is functionally closed: the new `test_hai_explain_renders_observed_and_projected_eod_for_arm2` exercises the full `build_snapshot -> project_proposal -> run_synthesis -> load_bundle_for_date -> bundle_to_dict + render_bundle_text` path, and the focused test file now reports `7 passed`. RELEASE_PROOF §1 still says W-D arm-2 has "6 acceptance tests pass." RELEASE_PROOF §2 was restamped accurately, but this workstream row missed the count update after the R1 explain test landed.
**Recommended response:** accept-as-known / close-in-place. Update the W-D row to "7 acceptance tests pass" before final release-proof freeze; no source reland needed.

## Per-finding R1-closure verdicts

| Finding | R2 verdict | Note |
|---|---|---|
| F-IR-01 | CLOSED | Bandit now reports 0 Medium / 0 High. The three B608 annotations are same-line and carry narrow bind-params/literal-predicate rationales. |
| F-IR-02 | CLOSED | `_find_in_corpus()` now accepts `scenario_id`, `fixture_id`, or file stem. Judge-adversarial show/tag/dismiss regression tests pass; corpus identifier spot-check found 0 cross-file collisions. |
| F-IR-03 | CLOSED_WITH_NOTE | Explain rendering is implemented and covered end-to-end. `_format_domain_classified_states_section({})` and with an empty `domain_classified_states` both return `""`; no exact text snapshot drift surfaced. Note is F-IR-R2-01's stale RELEASE_PROOF count. |
| F-IR-04 | CLOSED_PARTIAL | All 120 domain fixtures now carry `expected.classified`; six-domain spot-check matched live classifier output; in-memory band mutation failed as expected. Level-2 intent-versus-computation audit remains appropriate v0.1.18+ scope. |
| F-IR-05 | CLOSED | Wheel smoke parametrizes over `dist/*.whl`, skips pre-W-29 wheels, and passes on the rebuilt v0.1.17 wheel. Dist-empty no-op is documented and acceptable for CI because publish flow supplies the artifact. |
| F-IR-06 | CLOSED_NAMED | REPORT §5.4 names `reporting/plans/hai_runtime_contract_paper/` as out-of-band research planning and deliberately defers destination-cycle naming. |

## Open questions for maintainer

None blocking. The only note is the RELEASE_PROOF W-D test-count restamp.
