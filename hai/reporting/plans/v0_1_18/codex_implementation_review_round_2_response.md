# Codex Implementation Review — v0.1.18 (D15 IR round 2)

**Verdict:** SHIP_WITH_FIXES  
**Round:** 2

## Verification summary

- Tree state: `/Users/domcolligan/health_agent_infra` on `main`; `git rev-list --count 9c651da..HEAD` = **11** commits. `git status --short` shows only pre-existing `M uv.lock`.
- Fix-and-reland diff: HEAD `4de4306` changes 15 files across 3 source files, 2 test files, README/contract docs, release docs, and R1/R2 audit artifacts. `AGENTS.md` unchanged.
- Targeted R2 tests: `uv run pytest verification/tests/test_doctor_next_action.py verification/tests/test_init_onboarding_w_ob_3.py verification/tests/test_capabilities.py -q` -> **42 passed**.
- Full pytest gate: `uv run pytest verification/tests -q` -> **2729 passed, 5 skipped** in 126.49s.
- Warning gate: `uv run pytest verification/tests -W error::Warning -q` -> **2729 passed, 5 skipped** in 124.29s.
- Static gates: `uvx mypy src/health_agent_infra` -> success, 147 source files; `uvx bandit -ll -r src/health_agent_infra` -> 0 medium / 0 high severity.

## R1 closure verification

| Finding | Closure status | Note |
|---|---|---|
| F-IR-01 (`agent_cli_contract.md`) | CLOSED | Contract doc now embeds `hai 0.1.18` at `reporting/docs/agent_cli_contract.md:66`, matching `pyproject.toml:7`; the committed-doc test is green under both pytest gates. |
| F-IR-02 (README post-W-OB-2) | CLOSED_WITH_R2_PROVENANCE_GAP | README quickstart now leads with bare `hai init` and documents auto-promotion + opt-outs, but downstream release/docs summaries still describe the old `--guided`-primary shape. See F-IR-R2-02. |
| F-IR-03 (W-OB-5 broader coverage) | PARTIAL | The 7 R1-enumerated missed paths now emit `next_action`, and special renderers were updated. A new round-2 walk found a still-uncovered `check_auth_intervals_icu --deep` concrete-command hint path. See F-IR-R2-01. |
| F-IR-04 (`next_action_hint` correctness) | CLOSED | `run_guided_onboarding` now derives the hint from `intent_ids` + `target_ids` primitives; the two new regression tests pass and would fail under the prior status-string branch. |

## Findings (R2)

### F-IR-R2-01. `hai doctor --deep` credential-failure hints still omit `next_action`

**Q-bucket:** Q-R2-03  
**Severity:** scope-mismatch  
**Reference:** `src/health_agent_infra/core/doctor/checks.py:319`; `src/health_agent_infra/core/doctor/checks.py:334`; `src/health_agent_infra/core/doctor/probe.py:171`; `src/health_agent_infra/core/doctor/probe.py:177`; `verification/tests/test_doctor_next_action.py:139`

**Argument:** W-OB-5's contract is still not complete for "every doctor check that emits `hint` where the hint maps to a concrete command." The fix closes the R1-enumerated static paths, but `check_auth_intervals_icu` has a second hint surface under `--deep`: when credentials exist and the probe fails with an `outcome_class`, it sets `out["hint"] = out["next_step"]` from `OUTCOME_NEXT_STEPS`. At least `CAUSE_2_CREDS` maps to `hai auth intervals-icu`, and `NETWORK` maps to rerunning `hai doctor --deep`. That result has no `next_action`.

I verified the path directly with a credential-present `CredentialStore` plus `ProbeResult(ok=False, outcome_class="CAUSE_2_CREDS")`: the result was `status: "fail"` with a hint telling the user to rerun `hai auth intervals-icu`, and no `next_action` field. The new F-IR-03 tests start at `verification/tests/test_doctor_next_action.py:139`, but they cover the no-credential auth path and the R1-enumerated checks, not this deep-probe branch.

**Recommended response:** Add `next_action` for deep-probe outcomes whose next step maps to a concrete CLI command. Minimum: `CAUSE_2_CREDS` -> `_next_action("hai auth intervals-icu")`; for `NETWORK`, either use `_next_action("hai doctor")` after documenting the flag/prose boundary or explicitly classify it as manual/prose and exclude it from W-OB-5. Add regression tests for the deep-probe failure path and rerun the targeted W-OB-5 tests plus both pytest gates.

### F-IR-R2-02. Fix-and-reland did not propagate to release-summary surfaces

**Q-bucket:** Q-R2-02 / Q-R2-05  
**Severity:** provenance-gap  
**Reference:** `reporting/docs/agent_integration.md:27`; `CHANGELOG.md:61`; `reporting/plans/v0_1_18/RELEASE_PROOF.md:18`; `reporting/plans/v0_1_18/RELEASE_PROOF.md:20`; `reporting/plans/v0_1_18/RELEASE_PROOF.md:23`; `reporting/plans/v0_1_18/REPORT.md:202`; `reporting/docs/current_system_state.md:48`; `reporting/docs/current_system_state.md:64`

**Argument:** The post-fix test counts are consistent at 2729/5 across the primary gate surfaces, but several narrative closure surfaces still describe the pre-R1 state:

- `agent_integration.md:27` still says the root README leads with `hai init --guided`, while README now leads with bare `hai init`.
- `CHANGELOG.md:61-64` still says W-OB-1 pivots `hai init --guided` as the recommended interactive command and says `agent_integration.md:27` was updated to match.
- `RELEASE_PROOF.md:18` says README already shows `hai init --guided` at HEAD `9c651da`; `README.md:214` now shows bare `hai init`.
- `RELEASE_PROOF.md:20` still says W-OB-3 has 6 new tests and hint logic based on auth + intent status; the fix changed this to 8 tests and primitive intent/target readiness logic.
- `RELEASE_PROOF.md:23` still says W-OB-5 has a 9-command registry and 5 doctor checks; code now has 11 registry entries and broader coverage.
- `REPORT.md:202-204` still lists `check_today`, `check_intake_gaps`, and `check_config` as examples that do not yet emit `next_action`, which is false for the fixed R1 paths.
- `current_system_state.md:48` and `current_system_state.md:64` repeat the stale W-OB-1 / W-OB-5 summaries.

This is exactly the round-2 summary-surface failure mode: the code and §2 gate block were updated, but downstream closure summaries were not swept. It is not a runtime bug, but these are ship artifacts and should not publish with false cycle-state claims.

**Recommended response:** Do a text-only provenance sweep before publish. Update `agent_integration.md`, `CHANGELOG.md`, `RELEASE_PROOF.md` §1, `REPORT.md` §6, and `current_system_state.md` to the post-R1-fix state: bare `hai init` is primary; W-OB-3 is 8 tests + primitive readiness; W-OB-5 is 11 registry entries plus the broader check coverage. Keep historical `--guided` mentions only where clearly framed as v0.1.13 provenance or explicit-force spelling.

## Closure recommendation

Do not push/publish this HEAD yet. The gates are green and three of the four R1 findings are fully closed, but W-OB-5 still has a concrete-command doctor hint without `next_action`, and release-summary provenance is stale.

Fix-and-reland-2 should be small:

1. Patch `check_auth_intervals_icu` deep-probe concrete-command outcomes with `next_action`, plus tests.
2. Run the targeted W-OB-5 tests, both full pytest gates, mypy, and bandit.
3. Sweep the stale docs named in F-IR-R2-02.

Recommended next-round budget: one narrow R3 pass focused on the deep-probe branch, docs propagation, and stamped gate counts.
