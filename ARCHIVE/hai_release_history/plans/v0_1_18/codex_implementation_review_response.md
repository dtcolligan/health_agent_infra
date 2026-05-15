# Codex Implementation Review — v0.1.18

**Verdict:** SHIP_WITH_FIXES  
**Round:** 1

## Verification summary

- Tree state: active repo confirmed at `/Users/domcolligan/health_agent_infra` on `main`; HEAD `aa418d5` (`release(v0.1.18): ship-prep ...`). `git log 9c651da..HEAD` shows 10 commits, not the prompt's "9", because both D14 settlement and Phase 0 closure are in range before the 7 W-id/ship-prep commits. `git status --short` shows only pre-existing `M uv.lock`.
- Diff surface: `AGENTS.md` unchanged across `9c651da..HEAD`; no CP-shape governance edit landed.
- W-OB targeted tests: `uv run pytest verification/tests/test_cli_init_default_flip.py verification/tests/test_init_onboarding_w_ob_3.py verification/tests/test_doctor_next_action.py verification/tests/test_intake_migration_parity.py -q` → **34 passed**.
- Full pytest gate: `uv run pytest verification/tests -q` → **1 failed, 2721 passed, 5 skipped**. Failure: `verification/tests/test_capabilities.py::test_committed_contract_doc_matches_generated`.
- Broader warning gate: `uv run pytest verification/tests -W error::Warning -q` → **1 failed, 2721 passed, 5 skipped**. Same failure.
- Static gates: `uvx mypy src/health_agent_infra` → **Success: no issues found in 147 source files**. `uvx bandit -ll -r src/health_agent_infra` → **0 medium / 0 high severity**; 46 low-severity findings reported.
- Capabilities: generated `hai capabilities --json` reports `hai_version: "0.1.18"` and schema `agent_cli_contract.v1`; committed `reporting/docs/agent_cli_contract.md` still says `hai 0.1.17`.
- Eval corpus: `uv run hai eval run --scenario-set all` → **135/135 PASS**.
- Persona matrix: `uv run python -m verification.dogfood.runner /tmp/hai_ir_v0_1_18_persona_matrix` → **13 personas, 0 findings, 0 crashes**.
- W-OB-7 mutation probe: non-persistent in-memory replacement of `open_connection_with_migrations` with `open_connection` makes `hai intake weight` on schema-25 DB fail with `sqlite3.OperationalError: no such table: body_comp`; the reproducer is meaningful.

## Findings

### F-IR-01. Ship gate fails because `agent_cli_contract.md` was not regenerated after the version bump

**Q-bucket:** Q-G  
**Severity:** provenance-gap  
**Reference:** `verification/tests/test_capabilities.py:305`; `verification/tests/test_capabilities.py:320`; `reporting/docs/agent_cli_contract.md:66`; `pyproject.toml:7`

**Argument:** The standard full-suite gate fails at `test_committed_contract_doc_matches_generated`. Generated markdown now renders `hai 0.1.18`, while the committed contract doc still says `hai 0.1.17` at `reporting/docs/agent_cli_contract.md:66`. `pyproject.toml` is already bumped to `0.1.18`, so the committed contract doc is stale. This also makes the broader warning gate fail with the same assertion. RELEASE_PROOF §2 currently claims both pytest gates are green, but HEAD does not satisfy that claim.

**Recommended response:** Regenerate `reporting/docs/agent_cli_contract.md` from the current manifest and commit it with the fix set, then rerun both pytest gates. This is blocking because it is an explicit ship gate failure.

### F-IR-02. README quickstart still describes the pre-W-OB-2 `hai init` behavior

**Q-bucket:** Q-W-OB-1  
**Severity:** scope-mismatch  
**Reference:** `README.md:214`; `README.md:221`; `README.md:222`; `README.md:225`; `src/health_agent_infra/cli/handlers/config_init.py:586`

**Argument:** W-OB-2 changed bare `hai init` on an interactive TTY with incomplete onboarding state to auto-promote into the guided flow. The README still instructs new users to run `hai init --guided` and states that bare `hai init` "does the non-interactive scaffold only" and that "New users on an interactive terminal should always pass `--guided`." That is now false for the shipped behavior: `cmd_init`'s W-OB-2 block auto-promotes bare `hai init` on TTY unless `--non-interactive`, `HAI_INIT_NON_INTERACTIVE=1`, or no-TTY opt-out applies.

Keeping `hai init --guided` as an explicit power-user spelling is fine, but the current README contradicts the core cycle claim that the easy path is the default path.

**Recommended response:** Update README quickstart to the post-W-OB-2 shape. Recommended user-facing wording: show bare `hai init` as the interactive first-run command, mention that it auto-promotes to guided onboarding on TTY when setup is incomplete, and document `--non-interactive` / `HAI_INIT_NON_INTERACTIVE=1` for CI and agent harnesses. Keep `hai init --guided` as the explicit-force variant, not as the only correct new-user path.

### F-IR-03. W-OB-5 did not cover every concrete hint-emitting doctor check

**Q-bucket:** Q-W-OB-5  
**Severity:** scope-mismatch  
**Reference:** `src/health_agent_infra/core/doctor/checks.py:60`; `src/health_agent_infra/core/doctor/checks.py:70`; `src/health_agent_infra/core/doctor/checks.py:79`; `src/health_agent_infra/core/doctor/checks.py:364`; `src/health_agent_infra/core/doctor/checks.py:383`; `src/health_agent_infra/core/doctor/checks.py:489`; `src/health_agent_infra/core/doctor/checks.py:507`; `src/health_agent_infra/core/doctor/checks.py:673`; `src/health_agent_infra/core/doctor/checks.py:692`; `verification/tests/test_doctor_next_action.py:5`

**Argument:** PLAN §2.E acceptance item 1 says `next_action` is added to every doctor check that emits a hint where the hint maps to a concrete command. The implementation covers `state_db`, `onboarding_readiness`, both auth checks, and `skills`, but several concrete command hints still omit `next_action`:

- `check_config` missing-thresholds path: hint is `run `hai init` or `hai config init``.
- `check_config` malformed-TOML path: hint is `repair the TOML or regenerate with `hai config init --force``.
- `check_sources` no-DB path: hint is `run `hai state init``.
- `check_today` no-DB path: hint is `run `hai state init``.
- `check_today` schema-read-failed path: hint is `run `hai state migrate``.
- `check_intake_gaps` no-DB path: hint is `run `hai init``.
- `check_intake_gaps` schema-read-failed path: hint is `re-run `hai doctor` after `hai state migrate``.

I verified the no-DB paths directly: `check_config`, `check_sources`, `check_today`, and `check_intake_gaps` all returned a concrete `hint` and `has_next_action: false`. The W-OB-5 tests encode the broader acceptance text in their docstring, but the assertions only cover the five implemented checks, so this acceptance gap is not test-enforced.

**Recommended response:** Either implement `next_action` for all concrete command hints above, or explicitly narrow the contract and document why these checks are prose-only. Given the PLAN wording, the better fix is to expand `_NEXT_ACTION_REGISTRY` and add tests for at least `check_config`, `check_today`, `check_sources`, and `check_intake_gaps`. If any of these go through special-case renderers, update those renderers to display the `next:` line too.

### F-IR-04. `next_action_hint` can incorrectly say to run `hai daily` when targets were skipped

**Q-bucket:** Q-W-OB-3  
**Severity:** correctness-bug  
**Reference:** `src/health_agent_infra/core/init/onboarding.py:535`; `src/health_agent_infra/core/init/onboarding.py:541`; `src/health_agent_infra/core/init/onboarding.py:544`; `verification/tests/test_init_onboarding_w_ob_3.py:182`

**Argument:** W-OB-3's post-prompt hint is based on `auth_status` and `intent_target["status"]` only. `_step_intent_target` returns `status: "authored"` if the user authors an intent even when all target prompts are skipped. The post-prompt branch then treats onboarding as ready and emits: `Run `hai daily` to compute today's recommendation, or ask your agent.`

I verified this path without editing source: scripted guided onboarding with credentials + focus answer + all three target prompts skipped produced one active intent, zero active targets, `intent_target_status: "authored"`, `overall_status: "ok"`, and `next_action_hint: "Run `hai daily`..."`. That contradicts the cycle's onboarding-readiness model: `check_onboarding_readiness` requires intent, target, and wellness pull. It also weakens W-OB-3's acceptance that the post-prompt summary surfaces what was authored and what was deferred.

**Recommended response:** Compute `next_action_hint` from actual authored/present prerequisites, not from the coarse `intent_target.status` alone. At minimum, distinguish intent readiness from target readiness using `intent_ids` / `target_ids` and pre-existing row checks, then add a regression test for "credentials + focus answered + all targets skipped" asserting the hint names `hai target set` or rerun guided onboarding instead of `hai daily`.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-OB-1 | FIX | README install/quickstart is stale relative to W-OB-2's shipped default behavior. |
| W-OB-2 | PASS | Predicate ordering matches PLAN: explicit `--guided`, flag opt-out, env opt-out, no-TTY, then `check_onboarding_readiness`; six W-OB-2 tests pass. Manual TTY UX gate still required pre-publish. |
| W-OB-3 | FIX | Core additive field and tests landed, but `next_action_hint` can direct users to `hai daily` while targets are still missing. |
| W-OB-4a | PASS | Upgrade dogfood evidence is honest; W-OB-7 was verified end-to-end against schema-25. Synthetic DB fidelity is acceptable for this cycle. |
| W-OB-4b | PASS_WITH_NOTE | I ratify the autonomous substitution shape: unit-test predicate + isolated wheel opt-out smoke + maintainer manual TTY gate is honest. The manual gate remains mandatory before PyPI publish. |
| W-OB-5 | FIX | Runtime-only manifest invariant is good, but concrete doctor hints remain without `next_action`, so PLAN §2.E acceptance is not fully met. |
| W-OB-7 | PASS | Additive seam is scoped to intake handlers; all intake call sites use `open_connection_with_migrations`; reproducer and in-memory mutation probe both validate the bug closure. |

## Open questions for maintainer

1. **Manual TTY gate ratification:** I recommend accepting the W-OB-4b substitution shape as honest, but only if RELEASE_PROOF §3 is run before PyPI publish and the outcome is recorded.
2. **README wording preference:** Should the README show bare `hai init` as the primary first-run command, or show both `hai init` and `hai init --guided` with bare `hai init` first? The implementation makes bare `hai init` the actual easy path.
3. **W-OB-5 scope:** I recommend treating the uncovered concrete doctor hints as in-cycle W-OB-5 fixes, not v0.1.19 notes, because the PLAN acceptance already promised this broader scope.

## Closure recommendation

Do not push or publish this HEAD. Fix and reland:

1. Regenerate `reporting/docs/agent_cli_contract.md` and rerun both pytest gates.
2. Update README quickstart to the post-W-OB-2 default behavior.
3. Complete W-OB-5 `next_action` coverage for concrete command hints, with tests.
4. Fix W-OB-3 `next_action_hint` prerequisite logic, with a target-skipped regression test.

Recommended next-round budget: one focused fix pass plus D15 IR round 2. The likely settling shape is `4 -> 1/0`; the remaining work is small and localized, but current HEAD is not shippable because a standard ship gate fails.
