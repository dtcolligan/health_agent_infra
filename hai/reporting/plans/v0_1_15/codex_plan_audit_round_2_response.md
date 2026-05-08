# Codex Plan Audit Response — v0.1.15 PLAN.md (Round 2)

**Verdict:** PLAN_COHERENT_WITH_REVISIONS. The round-1 revision pass moved the PLAN in the right direction, but the cycle should not open until the named round-2 revisions below land. The blocking items are the W-A/W-D `target_present` contract, the still-inconsistent effort/provenance surfaces, the P-tier gate semantics, and the invalid F-PV14-02 interim cleanup path.

**Round:** 2

## Round-1 finding closure verification

| Round-1 finding | Status | Round-2 verification |
|---|---|---|
| F-PLAN-01 | CLOSED_WITH_RESIDUAL | W-A now splits `is_partial_day` from `target_present`, and W-D arm-1 uses both. Residual: `target_present` is declared as `bool` but may be `"unavailable"`, and W-D only fires on `false`. See F-PLAN-R2-01. |
| F-PLAN-02 | CLOSED_WITH_RESIDUAL | Tactical §5B/§5C/§5D now exist and broadly match the restructure. Residual: tactical §5B still has stale status, old effort rows, and an old total. See F-PLAN-R2-02. |
| F-PLAN-03 | CLOSED | AGENTS.md "Do Not Do" now points W-29/W-30 to `(v0.1.17 / v0.2.3)` and matches the settled-decision entry. |
| F-PLAN-04 | CLOSED_WITH_RESIDUAL | The in-PLAN disposition table accounts for 16 slots. Residual: surrounding prose and v0.1.17 README still use older 14/15-slot language. See F-PLAN-R2-03. |
| F-PLAN-05 | CLOSED_WITH_RESIDUAL | The v0.1.14 "one brief question / no keyboard time" threshold is restored, and P-tiers are defined. Residual: P0/P1 trust-loss and maintainer-intervention boundaries overlap. See F-PLAN-R2-05. |
| F-PLAN-06 | CLOSED_WITH_RESIDUAL | Candidate package now names wheel + sdist, clean Python 3.11+ env, version/commit/install record. Residual: top-level ship gates and tactical archive bullets still do not carry the full contract, and "tagged commit" is ambiguous before release. See F-PLAN-R2-07. |
| F-PLAN-07 | CLOSED_WITH_RESIDUAL | W-GYM-SETID now splits SQL migration from JSONL recovery and names the required fixture. Source check confirms `hai state reproject --cascade-synthesis` can run against an existing DB and should be followed by `hai synthesize`. Residual: widened W-GYM effort was not propagated to §1.2/tactical/README. See F-PLAN-R2-02. |
| F-PLAN-08 | NOT_CLOSED | Header and §5 say 16-25 days, but §1.2, README.md, and tactical §5B still carry old ranges. See F-PLAN-R2-02. |
| F-PLAN-09 | CLOSED | W-E excludes `present.weigh_in.logged`, W-A emits the explicit `intake_surface_not_yet_implemented` reason, and OQ-1 is raised for maintainer ratification. |
| F-PLAN-10 | CLOSED_WITH_RESIDUAL | PLAN §4 adds an interim F-PV14-02 cleanup note and keeps raw SQL prohibited. Residual: it names `selective hai restore`, which does not exist. See F-PLAN-R2-06. |
| F-PLAN-11 | CLOSED_WITH_RESIDUAL | PLAN §4.6 now has a v0.1.15-specific no-candidate-at-Phase-0 procedure. Residual: withdrawal after Phase 0 is not covered; treat as a new maintainer question, not a blocker if one sentence is added. |
| F-PLAN-12 | CLOSED_WITH_RESIDUAL | AGENTS.md now declares the active repo path. Residual: its provenance citation points to PLAN §4.6, but the active-repo note is PLAN §4 item 8. Fold this citation fix into F-PLAN-R2-03. |

## New findings (round 2)

### F-PLAN-R2-01. `target_present` is still not a coherent W-A/W-D contract

**Q-bucket:** Q-R1.a / Q-R2.a  
**Severity:** dependency-error  
**Reference:** PLAN.md §2.B lines 123-127; PLAN.md §2.E line 143; PLAN.md §4 lines 207-208

**Argument:** PLAN §2.B acceptance says W-A emits a top-level `target_present: bool` at line 124, then says the same field returns the string `"unavailable"` at line 126. W-D arm-1 fires only when `target_present == false` at line 143. That leaves the common "no target ever set" state ambiguous: if W-A returns `"unavailable"`, W-D arm-1 does not fire under the written predicate, even though the user has no active target. The Phase 1 parallelization note also needs to distinguish "table exists but has no rows" from "W-C migration has not landed yet"; an empty table can be tested by fixture, but a missing table requires either W-C's migration or an explicit `OperationalError`/schema-absence branch.

**Recommended response:** Revise W-A to use one typed contract, e.g. `target_status: "present" | "absent" | "unavailable"` plus a derived boolean only where needed. Then update W-D arm-1 to state whether `"unavailable"` is treated as no target for v0.1.15 suppression. Add acceptance tests for target present, target absent, no target ever set, and nutrition-target table missing before W-C lands.

### F-PLAN-R2-02. Effort reconciliation is still inconsistent across the summary surfaces

**Q-bucket:** Q-R1.h / Q-R6.a  
**Severity:** sizing-mistake  
**Reference:** PLAN.md header line 6; PLAN.md §1.2 lines 30-38; PLAN.md §5 lines 222-231; v0_1_15/README.md lines 3, 11, 37; tactical_plan_v0_1_x.md §5B lines 598-630

**Argument:** The headline says 16-25 days, and §5 mostly supports that after widening W-GYM-SETID to 1.5-3d and W-2U-GATE to 4-7d. But §1.2 still lists W-GYM-SETID as 1-2d, W-2U-GATE as 3-5d, and total as 13-22 days. v0_1_15/README.md still says "Ready for D14 round-1", "14-20 days", and "2-3 rounds". Tactical §5B still lists W-GYM-SETID as 1-2d, W-2U-GATE as 3-5d, and total as 14-23 days with "hope for 2-3" D14 rounds. This means F-PLAN-08 is not closed.

**Recommended response:** Make 16-25 days and 2-4 D14 rounds the single truth across PLAN §1.2, PLAN §5, v0_1_15/README.md, and tactical §5B. Update the per-WS rows before the total so the arithmetic is auditable.

### F-PLAN-R2-03. Scope-provenance accounting still mixes 14, 15, and 16-slot stories

**Q-bucket:** Q-R1.d / Q-R2.d / Q-R1.l  
**Severity:** provenance-gap  
**Reference:** PLAN.md §1.4 lines 59-60 and 83; PLAN.md §9 lines 276-277; v0_1_17/README.md line 7; v0_1_15/README.md lines 22-24; AGENTS.md lines 19-27

**Argument:** PLAN §1.4's table reconciles 16 slots as 7 kept + 9 deferred, which is the right audit surface. The surrounding prose still says "15 catalogued slots" and says "8 catalogued slots" did not affect the objective before saying "8 W-ids + W-D arm-2" were deferred. v0_1_17/README.md still calls round 0 a "14-W-id 39-60-day cycle", and v0_1_15/README.md still says the evening override expanded to 14 W-ids. AGENTS.md's active-repo declaration is present, but its origin citation points to PLAN §4.6; the active-repo note is PLAN §4 item 8.

**Recommended response:** Pick one accounting sentence and reuse it everywhere: "16 catalogued slots: 7 kept in v0.1.15, 9 deferred to v0.1.17; if W-D is counted as one W-id with two arms, call that out only as a parenthetical." Update both READMEs and the PLAN prose. Fix the AGENTS.md active-repo citation to the correct PLAN §4 item.

### F-PLAN-R2-04. The source findings doc still contradicts the round-2 W-A predicate split

**Q-bucket:** Q-R2.a / Q-R4  
**Severity:** hidden-coupling  
**Reference:** agent_state_visibility_findings.md lines 16-20, 82-84, 114-139; PLAN.md §2.B lines 117-127

**Argument:** The rewritten recommendation section aligns with the new v0.1.15/v0.1.16/v0.1.17 split, but the document's earlier status and W-A detail did not get the same fan-out. It still says v0.1.15 remains the mechanical W-29/W-30 split and v0.1.16 is the dedicated hardening cycle. More importantly, the structural insight says `is_partial_day` is derived from timestamp + meal count + presence-of-target, which directly contradicts round-2 PLAN §2.B's corrected target-independent `is_partial_day` plus separate `target_present`. The F-AV-01 JSON example also lacks `target_present` and the v0.1.15 `weigh_in` reason.

**Recommended response:** Add a short "superseded by v0.1.15 round-2 PLAN" note near the top, update the structural insight to split `is_partial_day` from target state, and update the F-AV-01 example to include the final W-A output contract.

### F-PLAN-R2-05. P0/P1 gate semantics still overlap

**Q-bucket:** Q-R2.b / Q-R3.a  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.G lines 178-190; tactical_plan_v0_1_x.md §5B lines 610-620

**Argument:** The v0.1.14 intervention threshold is restored, but the new P-tier definitions blur the fail/defer line. P0 includes a wrong recommendation noticed in-session; P1 includes an incorrect band classification the user notices and "silent trust loss the user notices." Those can describe the same event. The intervention rule is also inconsistent: line 179 says multiple interventions or any maintainer keyboard time is failure, while P1 says `>1` brief maintainer intervention can be closed if cheap or named-deferred. Finally, "cheap" excludes state-model schema changes but does not say whether capabilities-manifest or agent-contract changes are too contract-bearing for inline P1 handling.

**Recommended response:** Make any breach of the inherited session threshold a P0 gate failure requiring rerun or explicit D14 re-scope. Define P1 as session-completes-within-threshold but trust-degrading. Add a rule for capabilities-manifest/agent-contract changes: either classify them as not cheap, or explicitly allow them with a named narrower threshold.

### F-PLAN-R2-06. The F-PV14-02 interim cleanup path names a nonexistent selective restore

**Q-bucket:** Q-R1.j / Q-R3.c  
**Severity:** plan-incoherence  
**Reference:** PLAN.md §4 line 211; cli.py lines 8588-8599; core/backup/bundle.py lines 170-175 and 285-307; reporting/docs/recovery.md lines 30-37

**Argument:** PLAN §4 says the sanctioned interim cleanup path is "`hai backup` + selective `hai restore`". The shipped restore surface is not selective: the CLI only accepts `--bundle`, `--db-path`, and `--base-dir`, and the backup module overwrites the destination `state.db` plus JSONL logs as a point-in-time restore. The recovery doc says the same. That means the PLAN currently points operators to an operation that does not exist; the selective cleanup tool is exactly F-PV14-02, which is deferred to v0.1.17.

**Recommended response:** Replace the interim path with the actual choices: full restore from a pre-leak backup, or leave cosmetic `sync_run_log` rows in place until F-PV14-02 ships. If a selective cleanup path is required for v0.1.15, pull F-PV14-02 forward or write an explicit audited operator procedure.

### F-PLAN-R2-07. Candidate-package details are not carried into ship gates and tactical acceptance

**Q-bucket:** Q-R1.e / Q-R1.f / Q-R3.b  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.G lines 174-176; PLAN.md §6 lines 245-246; tactical_plan_v0_1_x.md §5B lines 623-625

**Argument:** PLAN §2.G now specifies the package shape and archive artifacts, but the top-level ship gates still only say the foreign user reaches `synthesized` and P0/P1 are closed or deferred. They do not restate the no-keyboard/no-multiple-intervention threshold, install record, state snapshot, candidate package provenance, or P2 handling. Tactical §5B archives the transcript and state DB snapshot, but omits the install record. Also, "post-merge to main, tagged commit" is ambiguous before PyPI release: it could mean the eventual release tag or a gate-candidate tag. Since the PLAN says no PyPI pre-release, the tag semantics should be explicit.

**Recommended response:** Update PLAN §6 and tactical §5B to mirror §2.G's load-bearing gate artifacts. Replace "tagged commit" with either "commit SHA only" or "non-release gate-candidate tag, e.g. `gate/v0.1.15-YYYY-MM-DD`, with the release tag created only at ship."

## Open questions answered (Codex opinions on OQ-1, OQ-5, OQ-6)

**OQ-1, W-B pull-forward:** keep W-B deferred. The v0.1.15 gate can be meaningful with verbalize-without-state-write as long as W-A always emits `weigh_in.logged=false` with the explicit unavailable reason and W-E never branches on it. Pull W-B forward only if the named candidate's day-1 workflow requires body-weight persistence for the session to reach `synthesized` or avoid a repeated prompt.

**OQ-5, round-0 self-audit pattern as D-entry:** do not make it a settled decision yet. The pattern is useful, but one successful restructure is not enough to promote it to a governance invariant. Record it as a lightweight validated pattern or CP candidate at v0.1.15 ship; promote to a D-entry after it recurs or after D14 explicitly needs it to prevent another over-scoped opening.

**OQ-6, foreign-device OS:** one real foreign OS is enough for v0.1.15. The ship claim is "a non-maintainer on a fresh device can reach `synthesized`", not "all supported OSes are verified." Record OS, Python version, shell, install command, and environment hash in the install record. A multi-OS matrix belongs in later packaging/distribution hardening, not this gate.

## Open questions for maintainer (new from round 2)

1. Candidate withdrawal after Phase 0: add one sentence saying that if the candidate withdraws after Phase 0 but before Phase 3, the maintainer must re-enter the §4.6 decision tree before opening the gate session.
2. `target_present="unavailable"` semantics: should no-target-ever suppress classification in v0.1.15 like `false`, or should it fail closed until W-C creates the first target row?
3. Gate-candidate tag: should the gate package use a non-release tag, or should the install record rely on commit SHA only?
