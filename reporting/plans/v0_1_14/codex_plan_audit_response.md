# Codex Plan Audit Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS (revise the v0.2.0 end-state claim, sizing envelope, W-2U-GATE abort/candidate procedure, capabilities-snapshot gate, W-EXPLAIN-UX carry-forward gate, P13/W-Vb harness boundary, CP application/status surfaces, and the stale tactical/strategic cross-doc deltas before Phase 0 opens)

**Round:** 1

## Findings

### F-PLAN-01. v0.2.0 is still a build release, not merely a wire-up release

**Q-bucket:** Q1  
**Severity:** plan-incoherence  
**Reference:** PLAN.md §1.1, lines 40-44; PLAN.md §2.B, lines 162-179; tactical_plan_v0_1_x.md §6.1-§6.3, lines 499-530  
**Argument:** The PLAN says the v0.1.14 end-state makes v0.2.0 W52/W58D "a wire-up release, not a build-and-ship" (PLAN lines 40-44). But W-PROV-1 only commits one recovery-domain R-rule demo plus locator roundtrip/rendering (lines 162-179). The v0.2.0 tactical scope still builds weekly-review aggregation, deterministic W58D blocking, a known-good/known-bad claim corpus, W-MCP-THREAT, and a +30 test-count target (tactical lines 499-526), with 18-24 days of effort (line 530). That is materially more than wire-up.  
**Recommended response:** Soften the end-state to "v0.2.0 starts with the source-row primitive and judge harness in tree, reducing design risk." Do not claim W52/W58D becomes wire-up unless W-PROV-1 expands beyond the current one-domain demo.

### F-PLAN-02. The 30-40 day envelope rounds down from the PLAN's own arithmetic

**Q-bucket:** Q3  
**Severity:** sizing-mistake  
**Reference:** PLAN.md §1.2, lines 54-69; PLAN.md §5, lines 395-407  
**Argument:** The workstream catalogue claims 30-40 days (line 69). The detailed roll-up says P0 additions are 11-14 days, tactical baseline 11-16, inherited work 7.5-10.5, and overhead 2-4 (lines 397-405), which totals 31.5-44.5 days. The PLAN then says "round to 30-40 days with contingency" (line 407), but that rounds the upper bound down and consumes contingency before any W-2U coordination slip, W-29 split friction, or W-Vb-3 scaling issue.  
**Recommended response:** Revise the headline to 32-45 days, or keep 30-40 only by naming a pre-authorized scope cut that brings the arithmetic under 40 before contingency. If the maintainer believes the real envelope is 35-50, say that explicitly and move one lower-priority W-id out before Phase 0.

### F-PLAN-03. W-2U-GATE has no candidate-absence or re-authoring procedure

**Q-bucket:** Q7  
**Severity:** absence  
**Reference:** PLAN.md §1.3, lines 73-83; PLAN.md §2.A, lines 127-129; PLAN.md §4, lines 383 and 389; PLAN.md §7, lines 481-483; reconciliation.md §5, lines 153-158  
**Argument:** W-2U-GATE blocks every later workstream (PLAN lines 73-83), but its candidate is still "TBD" and only promised before W-2U-GATE opens (lines 127-129, 481). Reconciliation still lists OQ-I as an open maintainer decision (reconciliation lines 153-154). The risks table handles a failed session, but not "no candidate materializes" (PLAN line 383), and the D14 rescope row points to "§1.3 acceptance criterion" even though §1.3 has sequencing text, not an acceptance procedure (line 389).  
**Recommended response:** Add an explicit pre-open rule: candidate named by D14 close or by Phase 0 gate; if absent, either hold the cycle, defer W-2U-GATE with a named destination, or re-author PLAN.md and re-run D14. Also fix the D14 rescope references to the actual section that owns the gate.

### F-PLAN-04. The capabilities snapshot gate omits W-AN and treats W-29 as allowed drift

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.K, lines 316-318; PLAN.md §2.L, lines 330-333; PLAN.md §3, line 366; src/health_agent_infra/evals/cli.py, lines 97-112  
**Argument:** The ship gate allows "documented surface changes (W-29 split, W-BACKUP commands, W-PROV-1 surface)" (PLAN line 366). But W-29's own acceptance requires byte-stability through the split (lines 330-333), so W-29 should produce zero manifest drift. Conversely, W-AN explicitly changes the eval CLI surface to `hai eval run --scenario-set <set>` (lines 316-318). The current eval parser has `--domain`, `--synthesis`, and `--json`, but no `--scenario-set` (evals/cli.py lines 97-112), so W-AN is a real documented CLI change that the ship gate omits.  
**Recommended response:** Split the gate into expected-diff classes: W-29 must be byte-identical; W-BACKUP and W-AN may change parser/capabilities snapshots; W-PROV-1 may change explain/rendering or capabilities only if the PLAN names the exact surface. The regression test should fail any other diff.

### F-PLAN-05. W-EXPLAIN-UX's v0.2.0 carry-forward is not enforceable

**Q-bucket:** Q5  
**Severity:** acceptance-criterion-weak  
**Reference:** PLAN.md §2.C, lines 198-212; PLAN.md §3, line 369; tactical_plan_v0_1_x.md §6.1-§6.2, lines 499-526  
**Argument:** W-EXPLAIN-UX acceptance requires remediation recommendations to be "folded into v0.2.0 W52 weekly-review prose design" while not implementing them in v0.1.14 (PLAN lines 210-212). The ship gate only checks that `explain_ux_review_2026-XX.md` exists (line 369), and tactical v0.2.0 contains no W-EXPLAIN-UX carry-forward row or prose-design acceptance hook (tactical lines 499-526). A filed findings document could ship without any v0.2.0 obligation.  
**Recommended response:** Add a concrete carry-forward artifact, for example a required "v0.2.0 W52 prose obligations" section in `explain_ux_review_2026-XX.md`, plus a tactical_plan §6 bullet or v0.2.0 PLAN seed item that must consume it.

### F-PLAN-06. P13 persona and W-Vb-3 demo-replay scope are not separated cleanly

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md §2.C, lines 190-209; PLAN.md §2.M, lines 335-343; PLAN.md §3, line 367; PLAN.md §6, lines 428-429  
**Argument:** W-EXPLAIN-UX adds P13 to `ALL_PERSONAS` and requires a 13-persona matrix (PLAN lines 190-209, 367). W-Vb-3, however, closes the 9 non-ship-set personas from the original P1-P12 universe and says "v0.1.14 owns the full residual" (lines 335-343). Phase 0 still runs 12 personas before P13 exists (lines 428-429). The PLAN never says whether P13 needs demo-replay fixture coverage, only matrix coverage, or no W-Vb relation at all.  
**Recommended response:** State explicitly that W-Vb-3 owns only the P2/P3/P6/P7/P8/P9/P10/P11/P12 residual and P13 is matrix-only for v0.1.14, or add P13 to the demo-replay acceptance if that is intended.

### F-PLAN-07. CP-PATH-A left stale tactical-plan title, section labels, boundary text, and risk cuts

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** tactical_plan_v0_1_x.md title/table of contents, lines 1 and 23-31; tactical_plan_v0_1_x.md §11, lines 695-731; tactical_plan_v0_1_x.md §12, lines 757-758; tactical_plan_v0_1_x.md §13, lines 777-779  
**Argument:** CP-PATH-A successfully adds v0.2.1-v0.2.3 to the table of contents and release table (tactical lines 23-31, 45-48), but the document title still says "v0.1.11 through v0.2.0" (line 1), the release-pattern playbook under §11 still labels subsections as `8.1` through `8.5` after renumbering (lines 699-731), the risk-cut section still says "W52, W53, W58 from v0.2.0" even though W53 moved to v0.2.1 (lines 757-758), and the boundary still says the doc covers only v0.1.11 -> v0.2.0 (lines 777-779).  
**Recommended response:** Update the title and boundary to v0.2.3, renumber §11 subheads to 11.x, and revise the risk-cut text so W53 is not described as part of v0.2.0.

### F-PLAN-08. CP-MCP-THREAT-FORWARD leaves threat-model source verification timed at v0.4

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** strategic_plan_v1.md Wave 3, lines 493-524  
**Argument:** Strategic Plan Wave 3 now says the MCP threat-model artifact is authored in v0.2.0 and is a prerequisite for v0.3 PLAN-audit (lines 493-502). Immediately after the staging block, the source list is introduced as "Sources for threat-model authoring (verify current at v0.4)" (line 524). That timing matched the older CP4 shape, but it conflicts with CP-MCP-THREAT-FORWARD's point: the threat model is authored before v0.3, not verified for the first time at v0.4.  
**Recommended response:** Change the source note to "verify current at v0.2.0 authoring; refresh at v0.4 prereq completion" or split the v0.2.0 authoring sources from the v0.4 mitigation-refresh sources.

### F-PLAN-09. The new Strava prohibition contradicts the strategic-plan data-source row

**Q-bucket:** Q6 / Q9  
**Severity:** settled-decision-conflict  
**Reference:** AGENTS.md "Do Not Do", lines 404-408; strategic_plan_v1.md §8.2, line 580  
**Argument:** AGENTS.md now prohibits anchoring a data path on Strava, directly or through an upstream that proxies Strava data (lines 404-408). Strategic Plan §8.2 still lists "Manual fitness apps (Strava, Hevy, MyFitnessPal)" and says an importer for Strava activities would be "v0.3 — small-scope, high-utility" (line 580). That is a direct cross-doc contradiction introduced by applying CP-DO-NOT-DO-ADDITIONS without sweeping the strategic expansion table.  
**Recommended response:** Remove Strava from the candidate importer row, or rewrite it as "Hevy/MyFitnessPal only; Strava explicitly prohibited unless a future CP reopens the ToS decision."

### F-PLAN-10. The W-30 settled-decision text omits W58D's claim-block schema

**Q-bucket:** Q6  
**Severity:** settled-decision-conflict  
**Reference:** AGENTS.md D4, lines 127-131; tactical_plan_v0_1_x.md §6.1, lines 505-516; tactical_plan_v0_1_x.md §9.1, lines 620-623  
**Argument:** AGENTS.md says W-30 moves to v0.2.3 "after all v0.2.x schema additions land" and lists W52 v0.2.0, W53 v0.2.1, and W58J v0.2.2 (AGENTS lines 127-129). Tactical v0.2.0 also ships W58D's deterministic claim-block, and names "weekly-review tables + claim-block" as the v0.2.0 schema group (tactical lines 505-516). The W-30 v0.2.3 row then says the freeze happens after W52, W53, and W58J schema additions (lines 620-623), again omitting W58D/claim-block.  
**Recommended response:** Update the D4 and tactical wording to list the v0.2.0 W52/W58D weekly-review + claim-block schema group, W53, and W58J before W-30. If claim-block is intentionally considered part of W52, say that explicitly.

### F-PLAN-11. CP application status is inconsistent across PLAN and CP files

**Q-bucket:** Q9  
**Severity:** provenance-gap  
**Reference:** PLAN.md §6, lines 452-462; PLAN.md §7, lines 485-492; CP-2U-GATE-FIRST.md line 5; CP-MCP-THREAT-FORWARD.md line 5; CP-DO-NOT-DO-ADDITIONS.md line 5; CP-PATH-A.md line 5; CP-W30-SPLIT.md line 5  
**Argument:** PLAN §6 is titled "CPs to apply at v0.1.14 ship" (line 452), but then says CP-2U-GATE-FIRST is already implemented in this PLAN, CP-DO-NOT-DO-ADDITIONS was applied pre-cycle, and CP-PATH-A/CP-W30-SPLIT were applied pre-cycle (lines 454-462). The CP files themselves still say "Codex verdict: not yet authored" (all five CPs, line 5 in each file). For CP-MCP-THREAT-FORWARD, PLAN §6 says the strategic_plan Wave 3 update happens at v0.1.14 ship (lines 456-457), while the current strategic_plan already contains the v0.2.0 threat-model staging.  
**Recommended response:** Add an "Application status" table in PLAN §6 with `drafted / applied-pre-cycle / implemented-in-PLAN / pending-downstream` states, and update each CP file's status after maintainer acceptance. Reword CP-MCP-THREAT-FORWARD so it does not describe an already-applied strategic-plan delta as future ship-time work.

### F-PLAN-12. W-BACKUP's 90-day corruption claim is unsupported and unnecessary

**Q-bucket:** Q8  
**Severity:** provenance-gap  
**Reference:** PLAN.md §2.D, lines 216-219; strategic_research_2026-05-01.md §5 P0-5, lines 423-425  
**Argument:** W-BACKUP says "A second user will corrupt their state.db within 90 days" (PLAN lines 216-219), repeating the strategic-research claim (strategic_research lines 423-425). I found no cited evidence for the 90-day probability. The workstream does not need that quantified claim: the source-backed gap is that privacy.md currently gives manual file-copy/deletion guidance while no canonical `hai backup` / `hai restore` / `hai export` command exists.  
**Recommended response:** Soften to "A second user is likely to need a recovery path; without one, state corruption or migration mistakes can break the audit chain." Keep W-BACKUP P0, but remove the unsupported 90-day assertion.

## Open questions for maintainer

1. Should W-2U-GATE require a named candidate before D14 can close, or is "candidate appears before W-2U-GATE opens" sufficient even though W-2U-GATE is first and blocks the cycle?
2. Should P13 receive demo-replay coverage in v0.1.14, or is it intentionally matrix-only until a later cycle?
3. Should CP files themselves be status-updated as part of PLAN revision, or should PLAN §6 alone carry CP application status until ship?
