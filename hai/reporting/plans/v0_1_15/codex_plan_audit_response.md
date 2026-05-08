# Codex Plan Audit Response — v0.1.15 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS (revise W-A/W-C/W-D trigger contracts, W-2U-GATE acceptance, W-GYM-SETID migration acceptance, stale tactical/AGENTS surfaces, sizing, and provenance before Phase 0 opens)

**Round:** 1

## Findings

### F-PLAN-01. W-D arm-1 is unreachable under W-A's predicate

**Q-bucket:** Q2 / Q5  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.B lines 87-91; PLAN.md §2.D lines 99-103; PLAN.md §2.E lines 105-111; PLAN.md §4 lines 146-147  
**Argument:** W-A defines `is_partial_day` as `(timestamp.hour < cutoff) AND (meals_count < expected_for_day_complete) AND target_present` (line 91). W-D arm-1 is supposed to fire when `is_partial_day == true && no active nutrition_target row` (line 107). Those conditions cannot both be true. W-C then adds "classifier reads the active target row when classifying" (line 103), but target-present classification is W-D arm-2's projection path, which PLAN defers to v0.1.17 (line 107). The acceptance line "same intake with a target rolling forward classifies normally" (line 111) also sounds like deferred arm-2 behaviour.  
**Recommended response:** Split the signals: W-A should expose an observed partial-day signal independent of target presence, plus a separate `target_present`/active-target locator. W-C should own table, commit gate, and read APIs only. W-D arm-1 should test only the no-target suppression path. Any target-present projection/classification belongs to W-D arm-2 in v0.1.17 unless explicitly pulled forward.

### F-PLAN-02. Tactical detailed sections still describe the rejected split

**Q-bucket:** Q4 / Q9  
**Severity:** hidden-coupling  
**Reference:** tactical_plan_v0_1_x.md rows 46-48 lines 46-48; tactical_plan_v0_1_x.md §5B lines 576-633; tactical_plan_v0_1_x.md §5C lines 636-682; PLAN.md §1.4 lines 57-63  
**Argument:** The release table has the new split: v0.1.15 includes W-GYM-SETID/W-A/F-PV14-01/W-C/W-D arm-1/W-E/W-2U-GATE, v0.1.16 is post-gate bugs, and v0.1.17 gets maintainability/eval (lines 46-48). But the detailed v0.1.15 section still says v0.1.15 is "Second-user candidate-package prep," with W-29/W-AH-2/W-AI-2/W-AM-2/W-Vb-4/W-PV14-ISO in scope and the empirical gate in v0.1.16 (lines 576-633). The detailed v0.1.16 section still scopes W-2U-GATE itself (lines 636-682). This directly contradicts PLAN.md's restructure claim.  
**Recommended response:** Rewrite tactical §5B and §5C, not only rows 46-48 and the horizon paragraph. §5B should summarize the current v0.1.15 PLAN. §5C should become empirical post-gate fixes only. Add a new §5D for v0.1.17 or explicitly point the detail to `v0_1_17/README.md`.

### F-PLAN-03. AGENTS.md Do Not Do still schedules the cli.py split for v0.1.15

**Q-bucket:** Q4 / Q6  
**Severity:** settled-decision-conflict  
**Reference:** AGENTS.md "Settled Decisions" lines 124-141; AGENTS.md "Do Not Do" lines 416-420; PLAN.md §3 line 135  
**Argument:** The settled-decision entry now says the cli.py split is scheduled for v0.1.17 and records the v0.1.15 -> v0.1.17 redestination (lines 124-141). The Do Not Do bullet still says not to split `cli.py` before "their scheduled cycles (v0.1.15 / v0.2.3)" and cites only the v0.1.14 -> v0.1.15 update (lines 416-420). That leaves AGENTS.md with two active W-29 destinations.  
**Recommended response:** Update the Do Not Do bullet to `(v0.1.17 / v0.2.3)` and add the same 2026-05-02 evening redestination provenance. This is a required cross-doc fix before open.

### F-PLAN-04. Round-0 provenance arithmetic is not audit-stable

**Q-bucket:** Q1 / Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md header lines 3-5; PLAN.md §1.4 lines 57-63; README.md lines 20-26; v0_1_17/README.md lines 7-23  
**Argument:** PLAN.md says the superseded round-0 draft was a 14-W-id cycle (line 4), the self-audit found "6 of 14 W-ids" did not affect the second-user objective (line 60), and then says "the eight non-objective W-ids" were deferred (line 61). The current scope is 7 W-ids (line 38). Depending on whether W-D arm-2 and W-30 are counted as W-ids, these numbers do not reconcile. The central evidence for the cut is a chat transcript, not a tracked artifact, so an auditor cannot verify the rejected 14-W list or the per-WS classifier.  
**Recommended response:** Add a small provenance table to PLAN.md §1.4, or preserve `round_0_draft.md`, listing every round-0 item, whether it was kept/deferred/split, the destination, and the reason. Make the count reconcile explicitly: e.g. "14 workstream slots, 7 kept, 7 deferred; W-D arm-2 is a deferred arm, not a W-id" if that is the intended accounting.

### F-PLAN-05. W-2U-GATE claims verbatim inheritance but drops the hard failure threshold

**Q-bucket:** Q1 / Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §1.3 line 53; PLAN.md §2.G lines 123-129; v0_1_14/PLAN.md §2.A lines 189-204  
**Argument:** PLAN.md says W-2U-GATE is inherited verbatim from v0.1.14 (line 125), but the current acceptance only requires reaching `synthesized`, a transcript, and P0/P1/P2 disposition (line 129). The v0.1.14 acceptance was sharper: one full session reaches `synthesized` with at most one brief in-session question; multiple interventions or any maintainer keyboard time is failure (v0.1.14 lines 200-204). The current PLAN also uses P0/P1/P2 and "closed if cheap" without definitions (lines 53 and 129). A user could reach `synthesized` while still hitting the user-trust bug class this cycle is meant to catch.  
**Recommended response:** Restore the v0.1.14 intervention threshold, define P0/P1/P2 and "cheap" in PLAN.md, and make user-trust blockers fail the gate even if `synthesized` is reached. At minimum: P0 blocks install/intake/synthesis or corrupts/drops user state; P1 causes incorrect/repeated prompt, silent trust loss, or maintainer intervention beyond the one allowed brief question; P2 is cosmetic.

### F-PLAN-06. "Candidate package" is not defined as a package artifact

**Q-bucket:** Q2 / Q5  
**Severity:** absence  
**Reference:** PLAN.md §1.3 lines 52-53; PLAN.md §2.G lines 123-129; PLAN.md §6 lines 174-180  
**Argument:** Phase 3 runs against "the candidate package built from Phases 1-2" (line 53), but PLAN.md never says whether that means a wheel/sdist built from the final branch, a local editable checkout, a PyPI pre-release, or main with all commits landed. The ship gates require capabilities regeneration and a recorded session (lines 174-180), but not a build/install smoke for the exact artifact used by the foreign user.  
**Recommended response:** Define the artifact and install path. Example: build wheel+sdist from the final v0.1.15 branch, install the wheel into a clean environment on the foreign device, record the exact version/commit, and archive the transcript plus state DB snapshot under a named path.

### F-PLAN-07. W-GYM-SETID migration acceptance assumes a fixture and a non-SQL recovery path

**Q-bucket:** Q3 / Q5 / Q7  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.A lines 73-85; PLAN.md §4 line 148; PLAN.md §8 line 200; core/state/store.py lines 142-160 and 243-299; cli.py lines 3041-3049; core/backup/bundle.py lines 81-82  
**Argument:** W-GYM-SETID says the migration regenerates set IDs and preserves supersession chains (lines 73-80), then acceptance says existing multi-exercise days recover dropped sets from JSONL via reproject path "if any in test fixtures" (line 85). The migration runner discovers packaged `.sql` files and executes SQL statements only (store.py lines 142-160, 243-299); it cannot read JSONL audit logs. The CLI projection comment says JSONL can rebuild through `hai state reproject` after a DB failure (cli.py lines 3041-3049), which is a separate operational path, not a schema migration. The backup assumption is otherwise valid because `hai backup` includes `state.db` and JSONL logs (backup bundle lines 81-82), but the PLAN conflates backup/reproject/migrate.  
**Recommended response:** Author an explicit multi-exercise fixture; do not gate on "if any." Split the contract into: schema/data migration for rows that exist in `gym_set`, explicit post-migrate reproject/backfill procedure for rows recoverable only from JSONL, and backup/restore rehearsal before touching user state. Increase W-GYM-SETID sizing if the JSONL recovery path remains in scope.

### F-PLAN-08. Effort headline contradicts the PLAN's own arithmetic

**Q-bucket:** Q3  
**Severity:** sizing-mistake  
**Reference:** PLAN.md header lines 5-7; PLAN.md §1.2 line 38; PLAN.md §5 lines 157-168; README.md lines 11 and 37; AGENTS.md lines 201-208 and 351-357  
**Argument:** The header and README say 14-20 days (PLAN line 6; README line 11), the catalogue says 13-22 days (PLAN line 38), and the arithmetic table adjusts to 14-18-23 days (line 168). The D14 expectation is also narrowed to 2-3 rounds (PLAN line 7; README line 37) even though AGENTS.md says substantive PLANs should budget 2-4 rounds and twice-validated the 4-round settling shape (AGENTS lines 201-208, 351-357). W-2U-GATE also has external coordination and inline P0/P1 fix risk, so treating 5 days as the hard upper bound is optimistic.  
**Recommended response:** Make the headline match the arithmetic, e.g. 14-23 days before D14/IR overhead or 16-25 days if W-GYM recovery and W-2U coordination remain in scope. Change D14 expectation to "budget 2-4 rounds; hope for 2-3 if round 1 is low-density."

### F-PLAN-09. W-E requires a weigh-in token while W-B is deferred

**Q-bucket:** Q1 / Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.F lines 117-121; PLAN.md §7 lines 190-191; agent_state_visibility_findings.md F-AV-02 lines 149-170; v0_1_17/README.md line 20  
**Argument:** W-E acceptance requires the skill to check `present.{nutrition,gym,readiness,sleep,weigh_in}.logged` (line 117). But the body-comp/weigh-in intake surface is W-B, explicitly deferred to v0.1.17 (PLAN lines 190-191; v0.1.17 README line 20). F-AV-02 says there is no canonical `hai intake weight` surface today (findings lines 149-170). As written, the v0.1.15 skill is required to branch on a token that cannot be truthy through an in-scope CLI path.  
**Recommended response:** Either pull W-B into v0.1.15, or revise W-E/W-A to state that `weigh_in` is `unavailable`/always false until v0.1.17 and is not part of the gate's acceptance. If the foreign-user morning ritual includes weigh-in, the PLAN should say how it is handled without canonical intake.

### F-PLAN-10. The F-PV14-01/F-PV14-02 split drops the source doc's paired-cleanup warning

**Q-bucket:** Q1 / Q7  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.C lines 93-97; PLAN.md §7 lines 190-191; carry_over_findings.md lines 110-115; v0_1_17/README.md line 15  
**Argument:** The carry-over doc recommends pairing F-PV14-01 and F-PV14-02 because prevention alone can still leave users without a sanctioned cleanup path if a fixture leak recurs before the purge tool lands (carry-over lines 110-115). PLAN.md keeps F-PV14-01 but defers F-PV14-02 to v0.1.17 (PLAN lines 93-97, 190-191; v0.1.17 line 15) without naming the residual risk or the interim operator procedure. The cut is probably right for the foreign-user objective, but the PLAN should not silently erase the coupling argument.  
**Recommended response:** Keep F-PV14-02 deferred if the maintainer accepts the risk, but add an explicit known limitation: until v0.1.17, bounded `sync_run_log` contamination is handled by `hai backup`/`hai restore` or by leaving cosmetic rows in place; raw SQL remains prohibited.

### F-PLAN-11. Candidate-absence procedure no longer maps cleanly to this cycle

**Q-bucket:** Q7  
**Severity:** absence  
**Reference:** PLAN.md §4 line 149; v0_1_14/PLAN.md §1.3.1 lines 120-144; PLAN.md §1.3 lines 52-53  
**Argument:** PLAN.md carries forward v0.1.14 path 2 and says that if no candidate exists at the gate, hold the cycle open and continue Phase 1+2 polish (line 149). In v0.1.14, path 2 meant "defer W-2U-GATE to v0.1.15 and open implementation without it" at the pre-implementation gate (v0.1.14 lines 120-144). In v0.1.15, W-2U-GATE is the Phase 3 ship claim, not the first implementation workstream, so the old procedure only partially applies.  
**Recommended response:** Add a v0.1.15-specific rule: named candidate must be on file by a defined milestone (D14 close, Phase 0 gate, or before Phase 2 closes). If absent at Phase 3, either hold the cycle open without ship, downgrade to a non-shipping candidate-package cycle and re-D14, or defer the gate with a new named destination.

### F-PLAN-12. Dual-repo mitigation is prompt-local, not durable

**Q-bucket:** Q7  
**Severity:** absence  
**Reference:** PLAN.md §4 line 151; AGENTS.md "When In Doubt" lines 444-467; codex_plan_audit_prompt.md Step 0 lines 35-64  
**Argument:** PLAN.md identifies the stale `/Users/domcolligan/Documents/health_agent_infra/` checkout and relies on the D14 prompt Step 0 plus a memory entry (line 151). The prompt correctly guards this audit, but AGENTS.md does not declare the active checkout path in its durable operating contract. The same class of mistake can recur outside D14 prompts.  
**Recommended response:** Add a short AGENTS.md note under "When In Doubt" or "Authoritative orientation": active repo path is `/Users/domcolligan/health_agent_infra`; ignore `/Users/domcolligan/Documents/health_agent_infra/` unless explicitly requested. Keep Step 0 in prompts as the per-session check.

## Open questions for maintainer

1. Should W-B remain deferred if the v0.1.15 gate still exercises a "morning ritual" that includes weigh-in, or should the gate explicitly omit canonical weigh-in logging?
2. Is W-GYM-SETID expected to recover already-dropped sets automatically, or is the v0.1.15 fix allowed to be prospective plus documented reproject from JSONL?
3. Should the round-0 14-W-id draft be preserved as a tracked artifact, or is a PLAN.md §1.4 per-item provenance table enough?
