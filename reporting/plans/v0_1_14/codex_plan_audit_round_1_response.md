# v0.1.14 D14 Plan Audit — Round 1 Maintainer Response

**Round:** 1
**Codex verdict:** PLAN_COHERENT_WITH_REVISIONS
**Maintainer disposition:** ACCEPT 12 / PARTIAL-ACCEPT 0 / DISAGREE 0
**Action:** apply revisions in place across PLAN.md + tactical_plan +
strategic_plan + AGENTS.md + 5 CP files; close D14 round 1; await
round-2 audit.

---

## Summary

12 findings, all accepted as-stated. None challenge the strategic
posture (sequence W-2U-GATE first, 14-W-id substantive cycle, Path A
v0.2.x split). All are mechanical / honesty / cross-doc-propagation
fixes from the same family that surfaced in the post-v0.1.13
research-audit chain (round 2 there caught 7 propagation issues from
round 1 revisions). Empirical-settling shape on track: 12 → expect
~5-7 round 2 → 0-2 round 3.

The most material changes:

- **F-PLAN-01:** v0.2.0 wire-up claim softened (W-PROV-1 ships
  one-domain demo, not full plumbing; v0.2.0 still builds W52/W58D).
- **F-PLAN-02:** sizing envelope honest at 32-45 days (was 30-40,
  rounding down from arithmetic 31.5-44.5).
- **F-PLAN-04:** capabilities-snapshot gate split into expected-diff
  classes (W-29 byte-identical; W-AN/W-BACKUP/W-PROV-1 may diff
  with named surface).
- **F-PLAN-09:** Strava contradiction between AGENTS.md "Do Not Do"
  and strategic_plan §8.2 resolved (Strava removed from importer
  candidates).
- **F-PLAN-10:** AGENTS.md D4 + tactical §6/§9 corrected to include
  W58D claim-block in v0.2.0 schema group.
- **F-PLAN-11:** PLAN §6 gains application-status table; 5 CP files
  status-updated.

---

## Per-finding disposition

### F-PLAN-01 — v0.2.0 wire-up claim overstated

**Disposition:** ACCEPT.

**Verification:** PLAN §1.1 (lines 40-44) claims "v0.2.0 W52/W58D
becomes a wire-up release, not a build-and-ship." But W-PROV-1 ships
one recovery-domain demo only (PLAN §2.B). v0.2.0 W52 still builds
weekly-review aggregation, deterministic W58D blocking, claim
corpus, W-MCP-THREAT — 18-24 days estimated effort
(tactical_plan_v0_1_x.md §6.3). Codex is right; "wire-up" overstated.

**Action:**
- §1.1 end-state: replace "v0.2.0 W52/W58D becomes a wire-up
  release" with "v0.2.0 starts with the source-row primitive +
  judge harness in tree, reducing design risk."

### F-PLAN-02 — 30-40 day envelope rounds down

**Disposition:** ACCEPT.

**Verification:** §5 arithmetic: 11-14 + 11-16 + 7.5-10.5 + 2-4 =
31.5-44.5 days. PLAN's "round to 30-40 with contingency" lops 4.5
days off the upper bound and consumes contingency before any
W-2U-GATE coordination slip / W-29 friction / W-Vb-3 scaling issue.

**Action:**
- §1.2 + §5: revise headline to **32-45 days** (matches arithmetic).
- §10 ship gate already says "≤5 D14 rounds; if exceeds 5, maintainer
  re-scopes" — preserve as the contingency lever.
- ROADMAP.md / tactical_plan_v0_1_x.md §1 timeline retain "Q3 mid"
  ship target but caveat that 35-50 day shapes warrant deferring one
  of W-AM / W-AN / W-FRESH-EXT pre-Phase-0.

### F-PLAN-03 — W-2U-GATE candidate-absence + rescope procedure missing

**Disposition:** ACCEPT.

**Verification:** PLAN §1.3 / §2.A / §7 say candidate is "TBD —
placeholder per OQ-I; maintainer surfaces the candidate before
W-2U-GATE opens." Reconciliation §5 still lists OQ-I as open. Risks
table covers a failed session but not a no-candidate scenario.
§4 risks register row "D14 exceeds 5 rounds" points at "§1.3
acceptance criterion" but §1.3 is sequencing text, not an acceptance
section.

**Action:**
- Add new §1.3.1 "Candidate-absence procedure":
  - **Hard rule:** named candidate by Phase 0 gate (not D14 close —
    D14 audits the PLAN, not coordination state).
  - **If no candidate by Phase 0 gate:** three options, maintainer
    chooses:
      1. Hold the cycle (defer Phase 0 until a candidate surfaces).
      2. Defer W-2U-GATE to v0.1.15 with named destination; v0.1.14
         opens without it; W-EXPLAIN-UX foreign-user review uses a
         maintainer-substitute or also defers.
      3. Re-author PLAN.md (rescope around the absence) and re-run
         D14.
- Fix §4 risks register references: "§1.3 acceptance criterion" →
  "§1.3 sequencing constraint + §1.3.1 candidate-absence procedure";
  "D14 exceeds 5 rounds → maintainer re-scopes" gains a cross-ref to
  the new §1.3.1.

### F-PLAN-04 — Capabilities snapshot gate omits W-AN, treats W-29 as allowed drift

**Disposition:** ACCEPT.

**Verification:** PLAN §3 ship-gate row: "snapshot accepts only
documented surface changes (W-29 split, W-BACKUP commands, W-PROV-1
surface)." But:
- §2.L W-29 acceptance is byte-stable through the split (zero diff);
  treating W-29 as "allowed drift" is wrong.
- §2.K W-AN ships `hai eval run --scenario-set <set>` CLI — a real
  parser/capabilities surface change. Current
  `src/health_agent_infra/evals/cli.py:97-112` has `--domain` /
  `--synthesis` / `--json` only, no `--scenario-set`. W-AN was
  omitted from the gate's allowed-diff list.

**Action:**
- §3 capabilities-snapshot gate: split into expected-diff classes:
  - **byte-identical (zero diff):** W-29 mechanical split.
  - **named parser/capabilities surface change accepted:** W-AN
    (`--scenario-set`), W-BACKUP (`backup` / `restore` / `export`
    subparsers), W-PROV-1 (locator type in proposal/recommendation
    rendering only — not a parser change).
  - **regression test must fail any other diff.**
- `test_cli_parser_capabilities_regression.py` updated per the new
  gate at IR time (not D14 — this PLAN names the gate, IR enforces
  it).

### F-PLAN-05 — W-EXPLAIN-UX v0.2.0 carry-forward unenforceable

**Disposition:** ACCEPT.

**Verification:** §2.C acceptance: "remediation recommendations
folded into v0.2.0 W52 weekly-review prose design (carried forward,
not implemented in v0.1.14)." Ship gate (§3) only checks the
findings doc exists. Tactical plan §6.1-§6.2 (v0.2.0) has no
W-EXPLAIN-UX carry-forward hook. So a findings doc could ship
without any v0.2.0 obligation.

**Action:**
- §2.C acceptance: add concrete artifact requirement —
  `explain_ux_review_2026-XX.md` must contain a section titled
  **"v0.2.0 W52 prose obligations"** with each remediation listed as
  a structured item (issue / proposed prose change / acceptance
  hook).
- tactical_plan §6.1 v0.2.0 in-scope: add bullet
  **"W-EXPLAIN-UX carry-forward consumption"** — v0.2.0 W52 PLAN
  authoring must reference the v0.1.14 explain-UX-review obligations
  doc and either implement each item or explicitly defer with named
  cycle destination.

### F-PLAN-06 — P13 vs W-Vb-3 demo-replay scope

**Disposition:** ACCEPT.

**Verification:** §2.C adds P13 to `ALL_PERSONAS`, requires
13-persona matrix. §2.M W-Vb-3 closes 9 non-ship-set personas
(P2/P3/P6/P7/P8/P9/P10/P11/P12) via demo-replay. PLAN never says
whether P13 needs demo-replay coverage. Phase 0 (§6) runs 12-persona
matrix pre-W-EXPLAIN-UX P13 addition.

**Decision per OQ #2 in Codex's open questions:** P13 is
**matrix-only for v0.1.14**. W-Vb-3 owns the 9-persona residual; P13
demo-replay coverage is deferred to a future cycle.

**Action:**
- §2.C W-EXPLAIN-UX scope: explicit "P13 is matrix-only for v0.1.14;
  demo-replay coverage deferred (no ship gate for P13 demo-replay)."
- §2.M W-Vb-3 scope: explicit "owns the 9-persona residual
  (P2/P3/P6/P7/P8/P9/P10/P11/P12); P13 is out of scope for W-Vb-3."
- §3 ship gate "13 personas (P1..P12 + P13), 0 findings": clarified
  to "matrix-clean" (no demo-replay assertion for P13).
- §6 Phase 0 scope: 12-persona matrix run pre-Phase-0 is correct;
  P13 added in v0.1.14 implementation; 13-persona matrix runs
  pre-IR.

### F-PLAN-07 — CP-PATH-A left stale tactical-plan elements

**Disposition:** ACCEPT.

**Verification:**
- tactical_plan_v0_1_x.md:1 — title still "v0.1.11 through v0.2.0".
- tactical_plan §11 (was §8) — subheads still labeled `8.1`-`8.5`
  after the §7 → §10 / §8 → §11 / §9 → §12 / §10 → §13 renumber.
- tactical_plan §12 (was §9) — risk-cut text says "W52, W53, W58
  from v0.2.0" but W53 moved to v0.2.1, W58J/W58D split per Path A.
- tactical_plan §13 (was §10) — boundary still "v0.1.11 → v0.2.0".

**Action:**
- Title: "v0.1.11 through v0.2.0" → "v0.1.11 through v0.2.3".
- §11 subheads: `8.1`-`8.5` → `11.1`-`11.5`.
- §12 risk-cut text: rewrite "W52, W53, W58 from v0.2.0" → name
  per-release scope per Path A.
- §13 boundary: "v0.1.11 → v0.2.0" → "v0.1.11 → v0.2.3".

### F-PLAN-08 — Strategic-plan threat-model verification timed at v0.4

**Disposition:** ACCEPT.

**Verification:** strategic_plan_v1.md Wave 3 staging now puts
threat-model authoring at v0.2.0 (per CP-MCP-THREAT-FORWARD), but
the source list immediately after still says "verify current at
v0.4" (line 524). That timing matched the older CP4 shape.

**Action:**
- Wave 3 source list note: "verify current at v0.4" → "verify
  current at v0.2.0 authoring; refresh at v0.4 prereq completion."

### F-PLAN-09 — Strava AGENTS.md "Do Not Do" contradicts strategic-plan §8.2

**Disposition:** ACCEPT.

**Verification:** AGENTS.md "Do Not Do" (post-CP-DO-NOT-DO-ADDITIONS)
prohibits anchoring data path on Strava (lines 404-408). But
strategic_plan §8.2 still lists "Manual fitness apps (Strava, Hevy,
MyFitnessPal)" with Strava-importer flagged as v0.3 small-scope
high-utility candidate (line 580). Direct cross-doc contradiction
introduced by CP-DO-NOT-DO-ADDITIONS without sweeping the strategic
expansion table.

**Action:**
- strategic_plan §8.2: remove Strava from candidate-importer row;
  rewrite as "Manual fitness apps (Hevy, MyFitnessPal). **Strava is
  explicitly prohibited per AGENTS.md "Do Not Do" — Strava's Nov
  2024 ToS bans AI/ML use of Strava data. Reopening would require a
  formal CP overriding the prohibition.**"
- This is a summary-surface-sweep miss caught by D14; future CP
  applications must include the strategic-plan expansion table in
  the sweep checklist.

### F-PLAN-10 — AGENTS.md D4 + tactical §6/§9 omit W58D claim-block schema

**Disposition:** ACCEPT.

**Verification:** AGENTS.md D4 (post-CP-W30-SPLIT) lists "W52
v0.2.0, W53 v0.2.1, W58J v0.2.2" as the schema additions before
W-30. But tactical §6.1 explicitly says v0.2.0's schema group is
"weekly-review tables + claim-block (one group)" — claim-block is
W58D's, not W52's. The D4 wording understates v0.2.0 by omitting
W58D.

**Action:**
- AGENTS.md D4: revise "W52 v0.2.0, W53 v0.2.1, W58J v0.2.2" to
  "W52/W58D claim-block (v0.2.0), W53 (v0.2.1), W58J (v0.2.2)."
- tactical_plan §9.1 W-30 row: revise "after W52, W53, and W58J
  schema additions" to "after W52/W58D claim-block (v0.2.0), W53
  (v0.2.1), W58J (v0.2.2) schema additions."
- CP-W30-SPLIT.md "Proposed delta — AGENTS.md D4" updated similarly.

### F-PLAN-11 — CP application status inconsistent

**Disposition:** ACCEPT.

**Verification:**
- PLAN §6 says CP-MCP-THREAT-FORWARD strategic_plan delta "lands at
  v0.1.14 ship," but the strategic_plan already has the v0.2.0
  staging applied (CP application 2026-05-01).
- All 5 CP files still say "Codex verdict: not yet authored" in
  their status fields, but D14 round 1 has now reviewed them
  (verdict on the applied deltas is implied by the F-PLAN-07/08/09/
  10 findings).

**Decision per OQ #3 in Codex's open questions:** Yes, both PLAN §6
gains an application-status table AND the CP files' status fields
update.

**Action:**
- PLAN §6: add **Application status table**:
  | CP | Status | Application target |
  |---|---|---|
  | CP-2U-GATE-FIRST | implemented-in-PLAN | PLAN §1.3 + §2.A |
  | CP-MCP-THREAT-FORWARD | applied-pre-cycle | strategic_plan_v1.md Wave 3 |
  | CP-DO-NOT-DO-ADDITIONS | applied-pre-cycle | AGENTS.md "Do Not Do" |
  | CP-PATH-A | applied-pre-cycle | tactical_plan_v0_1_x.md §6/§7/§8/§9 |
  | CP-W30-SPLIT | applied-pre-cycle | AGENTS.md D4 + "Do Not Do" line |
- Reword CP-MCP-THREAT-FORWARD reference in §6 to "applied
  2026-05-01" rather than "lands at v0.1.14 ship."
- 5 CP files: "Codex verdict: not yet authored" →
  "Codex verdict: applied at v0.1.14 D14 round 1
  (PLAN_COHERENT_WITH_REVISIONS); revisions per F-PLAN-07/08/09/10
  applied to source documents in lockstep."

### F-PLAN-12 — W-BACKUP 90-day claim unsupported

**Disposition:** ACCEPT.

**Verification:** PLAN §2.D "A second user *will* corrupt their
state.db within 90 days" repeats the strategic-research §5 P0-5
claim. No cited evidence for the 90-day probability. The workstream
doesn't need the quantified claim.

**Action:**
- §2.D "Why P0" rewrite: "A second user is likely to need a recovery
  path; without one, state corruption or migration mistakes can
  break the audit chain. privacy.md currently gives manual file-copy
  / deletion guidance; no canonical `hai backup` / `hai restore` /
  `hai export` command exists."
- strategic_research_2026-05-01.md §5 P0-5 — same softening (separate
  follow-up; documented here, applied during W-FRESH-EXT mechanical
  citation pass).

---

## Summary-surface sweep (per AGENTS.md "Summary-surface sweep on partial closure")

The accepted revisions move multiple summary surfaces in lockstep:

| Surface | Change |
|---|---|
| PLAN.md §1.1 | wire-up claim softened (F-01) |
| PLAN.md §1.2 / §5 | sizing 30-40 → 32-45 days (F-02) |
| PLAN.md §1.3 | new §1.3.1 candidate-absence procedure (F-03) |
| PLAN.md §2.A / §7 | candidate-absence cross-refs (F-03) |
| PLAN.md §2.C | P13 matrix-only; v0.2.0 carry-forward enforceable (F-05, F-06) |
| PLAN.md §2.D | 90-day claim softened (F-12) |
| PLAN.md §2.M | W-Vb-3 owns P2-P12 residual only (F-06) |
| PLAN.md §3 | snapshot gate split into expected-diff classes; P13 matrix-clean clarification (F-04, F-06) |
| PLAN.md §4 risks | F-03 cross-refs |
| PLAN.md §6 | Application status table; CP-MCP-THREAT-FORWARD wording (F-11) |
| tactical_plan title + §11 + §12 + §13 | CP-PATH-A propagation (F-07) |
| tactical_plan §6.1 + §9.1 | W58D claim-block schema (F-10); W-EXPLAIN-UX carry-forward hook (F-05) |
| strategic_plan Wave 3 source list | v0.2.0 verification timing (F-08) |
| strategic_plan §8.2 | Strava removed from importer candidates (F-09) |
| AGENTS.md D4 | W58D claim-block in v0.2.0 schema group (F-10) |
| 5 CP files status fields | applied at v0.1.14 D14 round 1 (F-11) |
| CP-W30-SPLIT.md "Proposed delta" | W58D claim-block addition (F-10) |

---

## Round-2 expectations

Codex round 1 on a 14-W-id substantive PLAN: 12 findings.
Empirical D14 prior (v0.1.13 17 W-ids): 11 → 7 → 3 → 1-nit → 0.

Round 2 should catch:

- Any propagation gap from this round's revisions (e.g.,
  ROADMAP.md not updated to match the 32-45 day sizing; CP file
  status updates introducing new inconsistencies).
- Any second-order issue introduced by §1.3.1 candidate-absence
  procedure (hold/defer/rescope semantics need to be tight).
- The strategic_plan §8.2 Strava rewrite — verify the new wording
  doesn't inadvertently weaken D5 ("Garmin Connect is not the
  default live source") or contradict D-D6 nutrition v1 macros-only.
- The application-status table — verify each CP file's status field
  matches the table.

Expected yield: **5-7 findings**. PLAN's ≤5-round acceptance gate
holds; we are on track for 4-5 rounds total.

---

## Open questions answered

1. **W-2U-GATE candidate-by-D14-close vs by-Phase-0-gate?** Phase 0
   gate (per F-PLAN-03 disposition). D14 audits the PLAN, not
   coordination state.
2. **P13 demo-replay coverage in v0.1.14?** No — matrix-only for
   v0.1.14 per F-PLAN-06 disposition. Demo-replay deferred.
3. **CP files status-updated as part of PLAN revision?** Yes — both
   PLAN §6 application-status table AND CP file status fields
   update per F-PLAN-11 disposition.
