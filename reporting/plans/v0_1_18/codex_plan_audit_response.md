# Codex Plan Audit Response — v0.1.18 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS — open after the must-fix revisions below land, mainly W-OB-7 scope/provenance, W-OB-5 `next_action` contract, W-OB-4 ship-gate shape, and the v0.2.0 dependency claim.

**Round:** 1

## Findings

### F-PLAN-01. W-OB-7 handler inventory and migration-seam map are stale

**Q-bucket:** Q3 / Q5 / Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.1 line 38; §1.2 line 54; §2.G lines 279-302

**Argument:** PLAN §2.G scopes "six `cmd_intake_*` functions" and tests "all six intake commands." Disk check does not match: `rg -n "^def cmd_intake_" src/health_agent_infra/cli/handlers/intake.py` returns eight handlers: `gym` line 62, `exercise` line 300, `nutrition` line 420, `stress` line 643, `note` line 790, `readiness` line 903, `gaps` line 980, and `weight` line 1184. The two omitted handlers are not irrelevant by name: `cmd_intake_exercise` writes state via `open_connection`, and `cmd_intake_gaps` reads the canonical DB through `open_connection`.

The seam description is also stale. PLAN §2.G says handlers currently call raw `sqlite3.connect(...)`, but current intake handlers call `core.state.open_connection`; raw SQLite lives inside `core/state/store.py:64`. PLAN also says `hai state init` uses `apply_pending_migrations` at `cli/handlers/state.py:239,273`; those lines are `cmd_state_migrate`, while `cmd_state_init` is at `cli/handlers/state.py:46-52` and reaches migrations through `initialize_database`, which calls `apply_pending_migrations` at `core/state/store.py:335`.

**Recommended response:** Revise W-OB-7 to enumerate all eight `cmd_intake_*` handlers, then explicitly classify which must migrate before write/read. If any handler is excluded, name why and add a test proving the exclusion cannot hit schema-behind failure. Update the seam description from "replace raw sqlite3.connect" to the current `open_connection`-based shape, and update the `hai state init` provenance to `cmd_state_init` + `initialize_database`.

### F-PLAN-02. W-OB-5 `next_action` example contradicts the post-W-OB-2 command shape and manifest safety

**Q-bucket:** Q2 / Q4 / Q5  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.E lines 228-254

**Argument:** The `next_action` proposal example says `"command": "hai init --guided"` and `"agent_safe": true` at lines 238-241. Acceptance item 2 then says post-W-OB-2 values should reference `hai init`, not `hai init --guided`, when W-OB-2 makes the guided path implicit. Current manifest evidence also conflicts with `agent_safe: true`: `hai init` is `agent_safe: false` in `verification/tests/snapshots/cli_capabilities_v0_1_13.json` and in `reporting/docs/agent_cli_contract.md`.

This is not only stale prose. It creates the exact sequencing hazard PLAN §4 risk 7 names: an implementer could copy the example, ship `hai init --guided`, and miss the post-default-flip contract. It also muddies W57 because `next_action.agent_safe` would disagree with the command's own capabilities entry.

**Recommended response:** Revise the example to the post-W-OB-2 shape: `command: "hai init"`, `interactive: true`, and either `agent_safe: false` or a differently named field whose semantics do not conflict with command manifest `agent_safe`. Add an explicit W-OB-5 test asserting the missing-intent `next_action.command == "hai init"` and that `next_action` safety fields are consistent with the live capabilities manifest for that command.

### F-PLAN-03. W-OB-5 migration-behind acceptance silently changes `onboarding_readiness`

**Q-bucket:** Q4 / Q5 / Q6  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.E lines 249, 254, 257

**Argument:** W-OB-5 acceptance item 1 requires `next_action` for "FAIL with no DB or migration-behind," and item 6 requires a FAIL-with-next-action test. But the current `check_onboarding_readiness` function at `core/doctor/checks.py:470` returns `warn` for missing DB and does not perform a pending-migration check. Pending migrations are currently detected by `check_state_db`, not by onboarding readiness. PLAN line 257 then says W-OB-5 does not change `check_onboarding_readiness` decision logic.

Those cannot all be true. Either W-OB-5 is adding doctor-level `next_action` to multiple checks, including `state_db`, or it is changing onboarding-readiness logic. The current wording hides that coupling.

**Recommended response:** Pick one contract. Preferred: keep `check_onboarding_readiness` focused on intent/target/wellness readiness, and state that W-OB-5 adds `next_action` to doctor checks where relevant, including `state_db` pending-migration warnings. If the field remains limited to `onboarding_readiness`, remove the migration-behind acceptance claim.

### F-PLAN-04. W-OB-4 cannot validate the final default-flipped path as sequenced

**Q-bucket:** Q1 / Q2 / Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §1.1 lines 40, 42; §1.3 lines 64, 69; §1.4 line 86; §2.D lines 195-205; §6 lines 386-388

**Argument:** W-OB-4 is sequenced before W-OB-2. That is coherent if W-OB-4 is an exploratory dogfood pass whose findings inform W-OB-3, but it cannot validate the post-W-OB-2 default-flipped `hai init` behavior. Scenario 1 also says to install `health-agent-infra==<v0.1.18-build>` from PyPI before ship; a pre-ship gate cannot depend on the final PyPI artifact already existing.

The PLAN's ship claim is stronger than the gate: it says the maintainer dogfoods the full install/upgrade path, while the actual W-OB-4 run occurs before the release-blocker behavior change and uses a not-yet-published package form.

**Recommended response:** Split W-OB-4 into two gates or narrow the claim. Keep Phase 1 W-OB-4 as "evidence dogfood against W-OB-1 + W-OB-7." Add a post-W-OB-2 pre-ship smoke using a locally built wheel installed through `pipx install <wheel-path>` (or equivalent), including bare `hai init` on an interactive TTY proving the default flip fires. Reserve post-publish PyPI smoke for RELEASE_PROOF or ship-time verification.

### F-PLAN-05. v0.2.0 parallelization claim contradicts the tactical dependency chain

**Q-bucket:** Q1 / Q8  
**Severity:** dependency-error  
**Reference:** PLAN.md top theme line 13; §7 line 416; tactical_plan_v0_1_x.md lines 50-52; v0_1_16/README.md line 33; v0_1_19/README.md lines 44-47

**Argument:** PLAN line 13 says v0.1.18 is "Parallelizable with v0.2.0 since v0.2.0's hard dependencies do not include this cycle." The tactical table says v0.2.0 starts post-v0.1.19 and has v0.1.19 as a hard dependency; v0.1.19 in turn requires v0.1.18 shipped to PyPI. The v0.1.16 cancellation note also says v0.2.0 moved to post-v0.1.19.

**Recommended response:** Replace the parallelization claim with a narrower one: v0.1.18 does not add new v0.2.0 scope or schema dependencies, and v0.2.0 remains tactically sequenced after v0.1.19 unless the maintainer explicitly authorizes implementation-only parallel work.

### F-PLAN-06. W-OB-3 cites a non-existent test file

**Q-bucket:** Q5 / Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.C line 165

**Argument:** PLAN §2.C names `verification/tests/test_guided_onboarding.py` as the existing W-AA prompt-flow test. That file does not exist. The actual W-AA deterministic gate is `verification/tests/test_init_onboarding_flow.py`; v0.1.13 RELEASE_PROOF lines 166-172 also names that file and its nine cases.

**Recommended response:** Replace the file citation with `verification/tests/test_init_onboarding_flow.py`. While editing, clarify whether the refusal-path test means literal user input `"skip"` or the existing "press Enter / `None` means skip" behavior; the current orchestrator treats unrecognized focus text as skipped, which is not the same as a documented `skip` affordance.

### F-PLAN-07. §6 ship gates do not list two load-bearing acceptance checks

**Q-bucket:** Q2 / Q4 / Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.D lines 207-211; §2.E lines 249-254; §6 lines 386-397

**Argument:** §2.D acceptance item 3 says scenario 2's `hai intake weight` success is a no-ship-until-fixed gate. §6 only requires `dogfood_findings.md` to exist with both scenarios documented and separately requires the unit-style W-OB-7 reproducer test. That is not the same as proving the packaged dogfood upgrade scenario succeeded. Similarly, §2.E acceptance item 2 requires post-W-OB-2 `next_action.command` values, but §6 has no gate that would catch a stale `hai init --guided` command string.

**Recommended response:** Add explicit §6 gates for: (1) W-OB-4 scenario 2 packaged/wheel upgrade run includes `hai intake weight` success; (2) W-OB-5 tests assert `next_action.command` uses the post-W-OB-2 command shape; (3) if F-PLAN-04 is accepted, the post-W-OB-2 local-wheel smoke passes.

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-OB-1 | PASS | Scope fits the theme; README quickstart lines 206-244 exist and already show `hai init --guided`. |
| W-OB-2 | PASS | Release-blocker classification is honest. Add the post-W-OB-2 smoke gate through F-PLAN-04/F-PLAN-07, not by expanding W-OB-2 itself. |
| W-OB-3 | FIX | Fix the stale test-file reference and clarify literal `skip` vs existing empty-input skip behavior. |
| W-OB-4 | FIX | Keep the early dogfood pass, but add or rename the pre-ship/local-wheel/post-W-OB-2 validation gate. |
| W-OB-5 | FIX | Align `next_action` example, safety fields, migration-behind scope, and tests. |
| W-OB-6 | PASS | The structural trigger is adequate: "not absorbable into W-OB-3 or W-OB-5" plus examples is sharp enough for this conditional slot. |
| W-OB-7 | FIX | Revise handler count, seam provenance, and test scope before opening. |

## Open questions for maintainer

**OQ-1:** Default should move from `cli/shared.py` to a `core/state/store.py` helper such as `open_connection_with_migrations` unless the maintainer wants the seam explicitly CLI-only. Do not change `open_connection` globally without a broader audit; too many read paths depend on it.

**OQ-2:** Agree with "no" on `HAI_NON_INTERACTIVE` for v0.1.18. But W-OB-2 tests should separately cover `--non-interactive` and `HAI_INIT_NON_INTERACTIVE=1`, both with `isatty() == True`.

**OQ-3:** Agree with the default order: use the maintainer's real pre-v0.1.17 DB snapshot if available; otherwise install the v0.1.16 wheel and run `hai init`. Treat targeted rollback as last resort and document the exact mutation.

**OQ-4:** Current default conflicts with §2.E.5. If capabilities gain `doctor_check_schema`, update `test_capabilities_manifest_schema.py` in the same commit and name it as a manifest schema delta. If the field is runtime-only, remove the §2.E.5 manifest acceptance item.

**OQ-5:** Agree with "yes" for a post-prompt next-action hint, as content only. Do not add a new guided step under W-OB-3.

**OQ-6:** Prefer user-facing CHANGELOG wording: "interactive `hai init` default (with opt-out)" rather than internal "default-flip." The internal term can remain in PLAN.

**OQ-7:** Agree with reserving W-OB-6. If it does not fire, RELEASE_PROOF should explicitly say "no W-OB-6-class findings" and count the shipped workstreams as six base plus W-OB-7, with W-OB-6 unused.

## Tier ratification

Recommend keeping **substantive**. The days leg is below D15's 10-day threshold, but hardening does not fit because this is not correctness/security-only: W-OB-2 changes the most visible first-run command behavior and can break automation if wrong. The release-blocker leg is load-bearing enough, provided F-PLAN-04/F-PLAN-07 add a post-W-OB-2 validation gate.

## Closure recommendation

Verdict remains **PLAN_COHERENT_WITH_REVISIONS**. Must-fix before cycle open: F-PLAN-01, F-PLAN-02, F-PLAN-03, F-PLAN-04, F-PLAN-05, F-PLAN-06, and F-PLAN-07.

Recommended next-round budget: one focused revision pass by Claude/maintainer, then D14 round 2. Expected round 2 should be small: mostly checking that the W-OB-7 inventory, W-OB-5 schema, W-OB-4 gates, and v0.2.0 wording moved in lockstep across §1, §2, §6, and §8.
