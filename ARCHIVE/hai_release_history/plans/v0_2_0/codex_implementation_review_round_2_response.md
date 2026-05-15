# Codex Implementation Review — v0.2.0 (round 2)

**Verdict:** SHIP_WITH_FIXES
**Round:** 2

## Verification summary

- Round-1 -> round-2 delta: expected fix subjects are present:
  5 `fix(v0.2.0): IR R1 F-IR-{01,02,03,04,05}` commits and 1
  subject-level `docs(v0.2.0): D15 IR round 1 response` commit.
  Note: the raw `git log --grep='IR round 1 response'` command
  also matches the body of `22eb6d5` because the Step-0 tolerance
  meta-commit quotes that command. The subject-level check has the
  required count.
- Tree state: `/Users/domcolligan/health_agent_infra`, branch `main`.
  Tracked tree was clean before this response file; existing untracked
  artifact remains `reporting/plans/v0_2_0/next_session_prompt_w_fact_atom.md`.
- Test surface: both full warning gates passed at `2943 passed, 4 skipped`:
  `uv run pytest verification/tests -W error::Warning -q` and
  `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q`.
- Ship gates: `uvx mypy src/health_agent_infra` passed with no issues
  in 158 source files. `uvx bandit -ll -r src/health_agent_infra`
  exited 0 with 0 Medium / 0 High issues and 37 potential issues
  skipped via explicit `# nosec BXXX`. `hai capabilities --json`
  reports 68 commands.
- Eval gates: `hai eval run --scenario-set factuality` reports
  known-bad `85/85 blocked (100.00%)` and known-good `75/75 passed
  (100.00%)`. `hai eval run --scenario-set all` passed all six
  domains, synthesis, and factuality fan-out at 100%.
- Persona matrix: `HAI_RUN_PERSONA_MATRIX=1 uv run python -m
  verification.dogfood.runner /tmp/v0_2_0_ir_r2_persona_run` completed
  13/13 personas with 0 findings and 0 crashes; summary written to
  `/tmp/v0_2_0_ir_r2_persona_run/summary.json`.
- Round-1 finding closures: F-IR-01 closed; F-IR-02 closed; F-IR-03
  closed; F-IR-04 partial due second-order freshness drift; F-IR-05
  closed.

## Findings (this round only)

### F-IR-R2-01. Round-1 fixes moved the test surface to 2943 but summary surfaces still claim 2940

**Q-bucket:** Q-second-order / Q-summary-surface / Q-IR-R1-fixes  
**Severity:** provenance-gap  
**Reference:** `README.md:20`, `README.md:27`,
`reporting/docs/current_system_state.md:21`,
`reporting/plans/README.md:205`, `ROADMAP.md:27`,
`reporting/plans/v0_2_0/RELEASE_PROOF.md:43`,
`reporting/plans/v0_2_0/RELEASE_PROOF.md:50`,
`reporting/plans/v0_2_0/REPORT.md:96`, `CHANGELOG.md:14`  
**Argument:** The round-1 fixes added three regression tests:
one real-schema W58D drift test and two W52 multi-canonical
disposition tests. The actual ship gates now pass at `2943 passed,
4 skipped`, not 2940. Multiple summary surfaces still publish the
old count: README badge and status prose say `2940` / `2,940`;
`current_system_state.md` says `2940 passed`; `reporting/plans/README.md`
says `Test surface: 2940 passed`; ROADMAP says `2,940 passed`;
RELEASE_PROOF and REPORT still say `2940`. This is exactly the
second-order freshness gap the round-2 prompt called out. In the
same sweep, `CHANGELOG.md`'s v0.2.0 `[Unreleased]` section covers
W52, W-FACT-ATOM, and W58D, but does not record the round-1 IR
fixes the prompt required: real-schema row-version drift closure,
multi-canonical disposition surfacing, mypy clean, bandit clean,
and freshness repair.  
**Recommended response:** fix-and-reland. Update every release-summary
surface that publishes the v0.2.0 test count from 2940 to 2943 and
adjust the deltas where shown. Add a v0.2.0 changelog bug-fix entry
covering the round-1 IR fixes. Re-run the two full pytest gates after
the doc edits so the final count in docs matches the final count on
disk.

## Round-1 finding disposition

| F-IR | Closure | Notes |
|---|---|---|
| F-IR-01 | closed | `_ROW_VERSION_COLUMN` maps accepted-state tables to `projected_at`; `_resolve_locator_with_drift` compares via that mapping and coerces actual values with `str()`. Synthetic factuality seed now uses `projected_at`, and `test_gate_claim_drift_runs_against_real_accepted_state_schema` proves stale real-schema locator -> BLOCK / `LOCATOR_ROW_VERSION_DRIFT` while matching locator -> PASS. |
| F-IR-02 | closed | Mypy is clean. Spot checks match the requested fixes: `bad_locators` annotation, synthesis lookup locals, `_make_row_getter`, `Sequence[T]` defaults, `_NullConn()` scoped ignore, and `first is not None` type-narrowing assertion. The assertion is acceptable here: it protects an internal invariant already implied by `all_passed=False`; under `-O`, an impossible invariant break would still fail at the subsequent `first.claim_id` access rather than silently passing the gate. |
| F-IR-03 | closed | Bandit exits 0 with 0 Medium / 0 High findings. The B608 suppressions are on the f-string lines in `factuality_gate.py` and `snapshot.py`, and the disabled-issue count is 37. |
| F-IR-04 | partial | The original 2733/67/v0.2.0-next-active stale surfaces were updated, but the same freshness sweep did not propagate the three tests added by the round-1 fixes and did not add the required changelog coverage for the IR fixes. Tracked as F-IR-R2-01. |
| F-IR-05 | closed | `WeeklyCoverage.multi_canonical_dates` is populated from non-superseded plans per date; markdown disposition now renders when present; JSON coverage includes `multi_canonical_dates`. Positive and negative regression tests pass, and byte-stable weekly JSON tests pass. |

## Open questions for maintainer

None. The remaining issue is a bounded freshness fix-and-reland.
