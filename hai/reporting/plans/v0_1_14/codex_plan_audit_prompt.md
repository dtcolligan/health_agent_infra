# Codex External Audit — v0.1.14 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.14 is the first cycle authored from the
> post-v0.1.13 strategic research (`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`),
> which itself went through Codex audit-chain rounds 1+2 (closed
> REPORT_SOUND_WITH_REVISIONS, 17 cumulative findings). The cycle is
> 14 W-ids (9 tactical-plan baseline + 5 P0/P1 additions from the
> research). It applies five CPs (CP-2U-GATE-FIRST,
> CP-MCP-THREAT-FORWARD, CP-DO-NOT-DO-ADDITIONS, CP-PATH-A, CP-W30-SPLIT)
> — three already applied to AGENTS.md / strategic_plan /
> tactical_plan pre-cycle 2026-05-01; two implemented inside PLAN.md.
> The cycle sequences W-2U-GATE first per CP-2U-GATE-FIRST (foreign-
> machine onboarding empirical proof gates the rest of the cycle).
>
> **D14 is a settled decision** (added at v0.1.11 ship). Empirical
> norm: 2-4 rounds for a substantive PLAN, settling at the
> `10 → 5 → 3 → 0` halving signature. v0.1.13 settled at 5 rounds
> for 17 W-ids; v0.1.14 at 14 W-ids should expect **4-5 rounds**
> per the PLAN's own §1.4 / §3 acceptance criterion. PLAN's §10
> ship-gate accepts ≤5 rounds; if it exceeds 5, the maintainer
> re-scopes before implementation.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit is
> on the *plan document itself* — its coherence, sequencing, sizing
> honesty, hidden coupling, and whether the 5 CPs land correctly.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: cycle/v0.1.14 (or chore/<scope> if pre-cycle authoring)
git log --oneline -5
# expect: most recent should mention v0.1.13 ship + post-v0.1.13 work
ls reporting/plans/v0_1_14/
# expect: PLAN.md, codex_plan_audit_prompt.md (this file)
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants"
   - "Settled Decisions" D1-D15 — note that D4 was updated 2026-05-01
     by CP-W30-SPLIT (W-30 destination v0.2.0 → v0.2.3); verify the
     update reads coherently.
   - "Do Not Do" — note three new bullets added 2026-05-01 by
     CP-DO-NOT-DO-ADDITIONS (Strava-anchored data path / MCP
     autoload from project files / threshold mutation without
     explicit user commit). Verify each is coherent against
     existing invariants and not redundant.
   - **"Patterns the cycles have validated"** — provenance
     discipline, summary-surface sweep, honest partial-closure
     naming, audit-chain empirical shape. Apply these as you audit.
2. **`reporting/plans/strategic_plan_v1.md`** — Wave 2 expanded
   2026-05-01 to Path A 4-release shape (v0.2.0/v0.2.1/v0.2.2/
   v0.2.3); Wave 3 staging updated to add v0.2.0 W-MCP-THREAT step
   per CP-MCP-THREAT-FORWARD. Verify deltas read coherently against
   each Wave's existing theme + evidence anchor.
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release table
   (§1) updated 2026-05-01; §5 v0.1.14 expanded to 14 W-ids with
   §1.3-style sequencing; §6/§7/§8/§9 split per Path A; §10/§11/
   §12/§13 cross-cutting renumbered. Verify all section
   cross-references hold.
4. **`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`**
   — the source artifact (Codex-audited rounds 1+2; closed
   REPORT_SOUND_WITH_REVISIONS). PLAN.md cites this as primary
   source for the 5 P0/P1 additions; verify each addition's
   citation is accurate.
5. **`reporting/plans/post_v0_1_13/reconciliation.md`** — audit-chain
   settling shape + §6 next-step punch list. Verify PLAN.md's
   sequencing matches the punch list.
6. **`reporting/plans/post_v0_1_13/cycle_proposals/`:**
   - `CP-2U-GATE-FIRST.md` — implemented inside PLAN.md §1.3 + §2.A.
   - `CP-MCP-THREAT-FORWARD.md` — applied to strategic_plan Wave 3.
   - `CP-DO-NOT-DO-ADDITIONS.md` — applied to AGENTS.md "Do Not Do".
   - `CP-PATH-A.md` — applied to tactical_plan §6/§7/§8/§9.
   - `CP-W30-SPLIT.md` — applied to AGENTS.md D4 + "Do Not Do" line.
7. **`reporting/plans/v0_1_13/RELEASE_PROOF.md`** — prior-cycle
   carry-overs (§5 named-defers). PLAN.md §1.2 inherited W-29 /
   W-Vb-3 / W-DOMAIN-SYNC; verify PLAN's CARRY-OVER inheritance is
   accurate.
8. **`reporting/plans/v0_1_14/PLAN.md`** — the artifact under
   review.

Cross-check that everything PLAN.md cites actually exists in the
tree at the cited line ranges. Broken cross-references count as
findings.

---

## Step 2 — The audit questions

### Q1. Cycle thesis coherence

PLAN.md §1.1 names the theme as "build the eval substrate for
v0.2.0's W58 factuality gate; land the source-row provenance type
that v0.2.0 W52 will require; empirically prove the v0.1.13
onboarding test surface against a foreign user; and close the
v0.1.13-deferred mechanical workstreams."

- Do the 14 W-ids in §1.2 add up to that theme, or has scope
  drifted to include items the theme doesn't justify?
- Does the §1.3 sequencing (W-2U-GATE first) make sense with
  the theme, or does it create a hidden dependency that's not
  acknowledged?
- The PLAN's "End-state" claim ("v0.2.0 W52/W58D becomes a wire-up
  release, not a build-and-ship") — is it actually achievable
  given W-PROV-1's scope (1-domain demo, not full plumbing)?

### Q2. Sequencing honesty

§1.3 names a strict sequencing constraint: W-2U-GATE first; if it
surfaces a P0 remediation, the cycle reshapes. Then §1.3 lists 8
order-of-operations steps for after W-2U-GATE closes.

- Are there hidden ordering dependencies inside the post-W-2U-GATE
  group that §1.3 doesn't surface? E.g., does W-EXPLAIN-UX (adds
  P13 persona) create a new D11 persona-matrix obligation that
  W-Vb-3 (closes 9 personas) needs to know about?
- W-29 mechanical split is sequenced second after W-PROV-1. Is this
  honest, or should W-29 land first to give the rest of the cycle
  a stable cli.py target?
- W-FRESH-EXT is sequenced last "doc-fix sweep aware of all
  changes." Does that include sweeping the §21 mechanical citation
  pass on `strategic_research_2026-05-01.md` per Codex F-RES-R2-06
  deferral? PLAN's §1.4 and §2.E say yes — verify the wiring is
  consistent.

### Q3. Effort estimate honesty

§1.2 + §5 estimate 30-40 days for 14 W-ids. The breakdown:

- P0 additions: 11-14 days (W-2U-GATE 2-3 + W-PROV-1 3-4 +
  W-EXPLAIN-UX 2 + W-BACKUP 3-4 + W-FRESH-EXT 1).
- Tactical-plan baseline: 11-16 days.
- Inherited from v0.1.13: 7.5-10.5 days.
- Cycle overhead: 2-4 days.

Per-WS sizing checks:

- **W-2U-GATE 2-3 days:** is this realistic for "coordinate a
  foreign user, capture the session, file the artifact"? The work
  is mostly coordination; if the foreign user's first attempt
  fails (a likely outcome the §1.3 sequencing actually expects),
  does the 2-3 day estimate hold or should it be 3-5?
- **W-PROV-1 3-4 days:** schema design + migration 023 + 1-domain
  demo + roundtrip test. Is 3-4 days realistic for new-schema
  work with capability-manifest snapshot regen?
- **W-29 3-4 days mechanical refactor:** is this realistic for
  splitting 9217 lines across 13 files while maintaining byte-
  stable capabilities snapshot? v0.1.13 W-29-prep was 1 day for
  authoring the boundary table only.
- **W-Vb-3 4-6 days:** v0.1.13 W-Vb closed 3 personas in similar
  effort; 4-6 days for 9 personas (3x the work) — is the scaling
  honest, or should this be larger?

Total: does the cycle fit in the 30-40 day envelope, or is the
real estimate 35-50 days and PLAN is anchoring optimistically?

### Q4. Hidden coupling

PLAN.md §4 risks register names some couplings. Audit for missing
ones:

- **W-PROV-1 schema ↔ W-29 cli.py split.** W-PROV-1 changes the
  capabilities-manifest surface (new locator type appears in
  proposal/recommendation rendering). W-29 mechanical split must
  preserve byte-stable capabilities snapshot. PLAN §3 ship-gate
  says "snapshot accepts only documented surface changes (W-29
  split, W-BACKUP commands, W-PROV-1 surface)." Is this gate
  enforceable, or does it punt the conflict to IR-time?
- **W-EXPLAIN-UX P13 persona ↔ W-Vb-3 9 personas.** PLAN §3 says
  "13 personas (P1..P12 + P13), 0 findings." But W-Vb-3 closes
  the 9-persona residual *via demo-replay*; W-EXPLAIN-UX adds
  P13 *for matrix coverage*. Are these the same harness or
  different harnesses? If different, are the acceptance criteria
  stacked correctly?
- **W-2U-GATE foreign user ↔ W-EXPLAIN-UX foreign-user review.**
  PLAN §2.C says W-EXPLAIN-UX uses "the W-2U-GATE foreign user
  (or a separate candidate)." Is the same person doing both
  sessions, or two people? If same, does the W-2U-GATE artifact
  inform the W-EXPLAIN-UX review and vice versa, or are they
  independent?
- **W-AL FActScore-aware schema ↔ v0.2.0 W58D.** PLAN §1.4 says
  "W-FACT-ATOM (FActScore atomic decomposition) folds into v0.2.0
  W58D." If W-AL's schema in v0.1.14 doesn't anticipate atomic
  claims, v0.2.0 W58D needs a migration. Is W-AL's "FActScore-
  aware schema" specification tight enough to prevent that
  migration?

### Q5. Acceptance criterion bite

For each P0 W-id, is the acceptance criterion specific enough to
fail on?

- **W-2U-GATE:** "one full session reaches `synthesized` without
  maintainer intervention." Specific. But what if the maintainer
  intervenes once, briefly? Is that a failure? Acceptance is
  silent on the threshold.
- **W-PROV-1:** "design doc + 1-domain demo + roundtrip test." The
  roundtrip-test acceptance is testable; "design doc" and "1-domain
  demo" are softer. What's the explicit pass/fail?
- **W-EXPLAIN-UX:** "structured findings list + remediation
  recommendations folded into v0.2.0 W52 weekly-review prose
  design (carried forward, not implemented in v0.1.14)." How is
  "carried forward" enforced — a v0.1.14 artifact, or a v0.2.0
  PLAN obligation?
- **W-BACKUP:** roundtrip test in CI. Specific.
- **W-FRESH-EXT:** "Test rejects W-id references in informal-
  section sites that don't match active workstreams." Specific.

### Q6. Settled-decision integrity

Five CPs apply at this cycle. For each, verify:

- **CP-2U-GATE-FIRST** (PLAN §1.3 + §2.A): does the PLAN actually
  enforce "first" sequencing, or is W-2U-GATE just listed first in
  §1.2 without a real gate?
- **CP-MCP-THREAT-FORWARD** (strategic_plan Wave 3): the v0.2.0
  W-MCP-THREAT step was inserted between v0.3 and v0.4 staging.
  Verify the Wave 3 v0.3 line still reads coherently after the
  insertion (no orphan references to "v0.3 threat-model
  authoring").
- **CP-DO-NOT-DO-ADDITIONS** (AGENTS.md "Do Not Do"): three new
  bullets added. Verify each is non-redundant against existing
  bullets and that the Strava bullet does not contradict D5
  ("Garmin Connect is not the default live source").
- **CP-PATH-A** (tactical_plan §6/§7/§8/§9): the section split.
  Verify §1 release table matches §6-§9 release shape; verify
  §10 cross-cutting renumbering didn't break any cross-references.
- **CP-W30-SPLIT** (AGENTS.md D4 + "Do Not Do" line): W-30
  destination updated v0.2.0 → v0.2.3. Verify both lines updated
  consistently.

Specifically: do the CP deltas quote AGENTS.md / strategic_plan /
tactical_plan current text *verbatim*? If a CP's "current text"
section is paraphrased rather than verbatim, the application
risks mis-applying the delta.

### Q7. What the plan doesn't say

- **Abort path for W-2U-GATE.** PLAN §1.3 says P0 remediation
  reshapes the cycle, but doesn't say what reshaping looks like
  in practice — does the cycle re-author PLAN.md and re-run D14,
  or does it patch in place? AGENTS.md plan-mode triggers say
  PLAN-authoring requires plan mode, but post-D14 PLAN reshapes
  do not have a settled procedure.
- **Concurrency.** Can W-2U-GATE run in parallel with W-AH (3-4 day
  scenario expansion) once W-2U-GATE's session is scheduled but
  not yet complete? PLAN doesn't say.
- **What if W-2U-GATE candidate doesn't materialize.** PLAN §2.A
  says "candidate: TBD — placeholder per OQ-I; maintainer surfaces
  the candidate before W-2U-GATE opens." But what if no candidate
  surfaces by D14 close? Does the cycle hold, or does W-2U-GATE
  defer to v0.1.15 and v0.1.14 ship without it?
- **D14 acceptance ≤5 rounds.** §3 ship-gate is the only gate
  that names "if exceeds 5 rounds, maintainer re-scopes." Is the
  re-scope path documented anywhere, or is it left to maintainer
  judgement?
- **AgentSpec README framing (OQ-J option 2).** PLAN §1.4 lists
  "AgentSpec README framing — maintainer review pending." Is this
  blocking on cycle ship, or floating? PLAN should name the
  destination.

### Q8. Provenance / external-source skepticism

PLAN.md leans heavily on `strategic_research_2026-05-01.md`
citations. Spot-check:

- §2.B W-PROV-1 cites "Reconciliation §4 C10." Verify
  `reporting/plans/post_v0_1_13/reconciliation.md` actually
  references C10 source-row locators.
- §2.C W-EXPLAIN-UX cites "JMIR AI 2024 systematic review" and
  "Tandfonline 2025." Verify these citations were not flagged in
  the post-v0.1.13 audit-chain rounds 1+2 as needing
  re-verification.
- §2.D W-BACKUP doesn't cite an external source — is the
  90-day-corruption claim ("a second user *will* corrupt their
  state.db within 90 days") a load-bearing claim that needs
  evidence, or is it a hand-wave that should be softened?
- §6 cycle-pattern compliance cites AGENTS.md D11 + D14. Verify
  current AGENTS.md text matches the citation.

### Q9. CP application coherence

Three CPs were applied pre-cycle (2026-05-01):

- CP-DO-NOT-DO-ADDITIONS → AGENTS.md
- CP-PATH-A → tactical_plan + AGENTS.md
- CP-W30-SPLIT → AGENTS.md

Two CPs are implemented inside PLAN.md:

- CP-2U-GATE-FIRST → §1.3 + §2.A
- CP-MCP-THREAT-FORWARD → §1.4 deferral list (W-MCP-THREAT
  scheduled v0.2.0)

For each:

- Does the application match the CP's "Proposed delta" exactly,
  or did the application drift from the CP text?
- Are there any cross-doc inconsistencies introduced by the
  applications? (E.g., AGENTS.md D4 says v0.2.3; does
  tactical_plan §1 release table match?)
- Should the CPs be marked `applied` in their respective files
  (the CPs currently say "Codex verdict: not yet authored"; should
  this audit's verdict update them)?

### Q10. Path A integrity (does v0.1.14 leave v0.2.0 buildable?)

CP-PATH-A locks v0.2.0 to W52 + W58D + 4 doc-only adjuncts. v0.2.0
W52 depends on W-PROV-1 (source-row locator type) shipping in
v0.1.14.

- If W-PROV-1 partial-closes (e.g., schema design lands but the
  1-domain demo doesn't), is v0.2.0 W52 buildable?
- PLAN §4 risks register names the W-PROV-1 partial-closure
  fallback ("v0.1.14 splits into substrate (W-PROV-1 only) +
  features (rest); v0.2.0 W52 absorbs the redesign"). Is this
  fallback compatible with the Path A 4-release shape, or does
  it implicitly fold v0.2.0 back into Path B single-release?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_14/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.14 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1 / 2 / 3 / 4 / 5

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9 / Q10
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-02. ...

## Open questions for maintainer
```

Each finding must be triageable. "PLAN.md §2.A acceptance is silent
on threshold for 'maintainer intervention'" is a finding; "§2.A
feels handwavy" is not.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.13 already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started).
- v0.2.0+ scope (named in tactical_plan_v0_1_x.md §6-§9 but not in
  this PLAN's commitments).
- The strategic + tactical + eval + success + risks docs beyond
  the deltas this cycle proposes.
- The post-v0.1.13 strategic-research artifact itself (already
  Codex-audited rounds 1+2 and closed).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here
  Maintainer response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 4-5 rounds for v0.1.14
   per the 14-W-id substantive shape; ≤5 round acceptance per
   PLAN §3)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (12 personas pre-W-EXPLAIN-UX P13)
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md consolidates

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES

RELEASE_PROOF.md + REPORT.md → ship to PyPI
```

Estimated review duration: 1-2 sessions per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_14/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_14/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_14/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).

**No code changes.** No test runs. No state mutations. No edits to
AGENTS.md, ROADMAP.md, README.md, strategic_plan_v1.md, or
tactical_plan_v0_1_x.md from this audit — those edits are
downstream and are gated by the maintainer's PLAN-revision step.

---

## Reference: pre-conceded falsifiers

PLAN.md §4 risks register and §1.3 sequencing constraint name
specific things that would change the cycle shape:

- W-2U-GATE structural P0 blocker → cycle reshapes around fix.
- W-PROV-1 schema design needs major change → v0.1.14 splits
  substrate + features.
- W-29 split breaks capabilities snapshot → rollback the split.
- W-Vb-3 partial-closes again → honest naming with v0.1.15
  destination.
- W-EXPLAIN-UX foreign user unavailable → use W-2U-GATE candidate
  for both, or defer.
- Cycle exceeds 40-day budget → defer one of W-AM / W-AN /
  W-FRESH-EXT.
- D14 exceeds 5 rounds → maintainer re-scopes before
  implementation.

Treat these as *pre-conceded* — if you find evidence supporting
any of them, the corresponding workstream / acceptance criterion
adjusts automatically. Your job is to surface things PLAN.md
*didn't* concede.
