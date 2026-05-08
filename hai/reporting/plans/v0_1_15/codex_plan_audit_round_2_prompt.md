# Codex External Audit — v0.1.15 PLAN.md (D14 round 2)

> **Why this round.** D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS
> with 12 findings (F-PLAN-01 through F-PLAN-12). The maintainer
> applied all 12 revisions on 2026-05-03 — 11 verbatim/agreed, 1 with
> shape extension (F-PLAN-04 used an in-PLAN disposition table
> instead of a separate `round_0_draft.md`). Per-finding triage is
> recorded in `reporting/plans/v0_1_15/codex_plan_audit_response_response.md`.
>
> Round 2 audits whether (a) each round-1 revision actually closes
> its target finding, (b) the revisions introduced no new
> contradictions, and (c) the new structural elements added in
> round 2 (W-A predicate split, P-tier definitions, candidate-package
> shape, W-GYM-SETID scope split, v0.1.15-specific candidate-absence
> procedure, AGENTS.md active-repo declaration) are themselves
> coherent. Empirical halving signature predicts 4-7 findings at
> round 2 close.
>
> **D14 is a settled decision** (added at v0.1.11 ship). Substantive
> PLANs settle in 2-4 rounds at the `12 → 6 → 3 → 0` halving
> signature. Round 2 finding count drives the round 3 decision.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit is
> on the *plan document* — coherence of the round-2 revisions, plus
> a sweep for second-order contradictions across the cross-doc
> fan-out (tactical_plan + AGENTS.md + post_v0_1_14 findings doc).
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
# expect: main (or chore/<scope> if pre-cycle authoring branch is in use)
git log --oneline -5
# expect: HEAD is post-v0.1.14.1 (the doc-freshness sweep at
# 5660fd7 introduced the v0.1.15 / v0.1.16 split, OR a later commit
# if the maintainer has authored further v0.1.15 cycle work). The
# v0.1.14.1 hardening ship (856e689) should appear within the last
# 5 commits.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# — that commit is the head of the STALE checkout under
# /Users/domcolligan/Documents/health_agent_infra/, which is months
# behind and must not be audited.
ls reporting/plans/v0_1_15/
# expect: PLAN.md, README.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md, codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md (this file)
ls reporting/plans/v0_1_17/
# expect: README.md
```

The discriminator that matters is dual-repo: the stale checkout's
HEAD is `2811669 Phase H: implement conversational intake` and is
months behind. The active repo's HEAD is post-v0.1.14.1 and ahead by
many cycles. If HEAD is `2811669`, **stop and surface the
discrepancy**. Otherwise the specific commit message at HEAD does
not need to match a fixed string — what matters is that v0.1.14.1
appears in recent log and the v0.1.15 / v0.1.17 plan dirs exist.

**Ignore any tree under `/Users/domcolligan/Documents/`** — same
stale-checkout note as round 1. AGENTS.md "Authoritative orientation"
preamble (added per round-1 F-PLAN-12) now declares the active path
durably; verify the declaration is present as part of round 2 Q-R3.

---

## Step 1 — Read the orientation artifacts

Round-2 reading order is wider than round 1 because the response +
maintainer-response files plus the cross-doc fan-out targets all need
verification.

In order:

1. **`reporting/plans/v0_1_15/codex_plan_audit_response.md`** —
   round-1 findings (12 F-PLAN-NN entries). Treat as the authoritative
   list of round-1 verdicts; round-2 audit verifies each was closed.
2. **`reporting/plans/v0_1_15/codex_plan_audit_response_response.md`**
   — maintainer's per-finding triage. Names which findings were
   applied verbatim, which had shape extensions, and which raised
   open questions. Cross-check each disposition against the actual
   PLAN.md edit.
3. **`reporting/plans/v0_1_15/PLAN.md`** — the round-2 PLAN under
   review. Pay special attention to:
   - Header (lines 3-7) — sizing 16-25 / D14 expectation 2-4.
   - §1.4 — round-0 → round-1 disposition table (F-PLAN-04 close).
   - §2.A — W-GYM-SETID scope split (F-PLAN-07 close).
   - §2.B — W-A predicate split + `target_present` field (F-PLAN-01 close).
   - §2.E — W-D arm-1 corrected predicate + known-incomplete fix note.
   - §2.F — W-E excludes `weigh_in` (F-PLAN-09 close).
   - §2.G — W-2U-GATE acceptance + P0/P1/P2 + "cheap" definitions (F-PLAN-05 close) + candidate-package shape (F-PLAN-06 close).
   - §4 — risks 4.4 (W-D arm-1/2 known-incomplete), 4.5 (F-PV14-02 interim cleanup, F-PLAN-10 close), 4.6 (v0.1.15-specific candidate-absence procedure, F-PLAN-11 close), 4.8 (AGENTS.md active-repo declaration, F-PLAN-12 close).
   - §5 — effort table reconciliation (F-PLAN-08 close).
   - §8 — open questions for round 2 (OQ-1 / OQ-5 / OQ-6 raised; OQ-2 / OQ-3 / OQ-4 closed in round 2).
4. **`AGENTS.md`** — verify two round-2 edits:
   - "Authoritative orientation" preamble now contains the active-repo
     path declaration (F-PLAN-12 close).
   - "Do Not Do" lines 416-420 now say `(v0.1.17 / v0.2.3)` not
     `(v0.1.15 / v0.2.3)` (F-PLAN-03 close).
   - "Settled Decisions" D124-135 W29 entry should already match v0.1.17
     (was edited in round-1 fan-out; round-2 cross-checks consistency
     with the Do Not Do edit).
5. **`reporting/plans/tactical_plan_v0_1_x.md`** — verify round-2 edits:
   - Rows 46-48 (release table) — already updated in round-1 fan-out;
     round-2 verifies they remain consistent with PLAN.md and the
     detail sections.
   - **§5B (v0.1.15) detail** — rewritten round-2 to combined gate
     cycle (was "candidate-package prep" in pre-restructure text).
     F-PLAN-02 close.
   - **§5C (v0.1.16) detail** — rewritten round-2 to empirical
     post-gate fixes (was "first foreign-machine onboarding" in
     pre-restructure text). F-PLAN-02 close.
   - **§5D (v0.1.17) detail** — NEW; mirrors v0_1_17/README.md.
6. **`reporting/plans/v0_1_17/README.md`** — verify the deferral
   register matches PLAN §1.4's disposition table (every cut item
   from v0.1.15 round-0 should appear in v0.1.17 scope; W-D arm-2
   should be present; no orphans).
7. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`**
   — "Recommendation: cycle scoping" was rewritten in round-1 fan-out
   to match the restructure. Round-2 cross-checks the W-A description
   matches the round-2 PLAN's predicate split (the findings doc's
   F-AV-01 example output should be reconcilable with PLAN §2.B's
   `target_present` addition).
8. **`reporting/plans/post_v0_1_14/carry_over_findings.md`** — verify
   F-PV14-02's deferral aligns with PLAN §4.5's interim-cleanup risk
   note (F-PLAN-10 close); the carry-over doc itself is unchanged.
9. **`reporting/plans/v0_1_14/PLAN.md` §2.A** — verify the W-2U-GATE
   acceptance threshold restored in PLAN §2.G matches the v0.1.14
   verbatim (lines 200-204 of v0.1.14 PLAN). F-PLAN-05 close.
10. **`reporting/plans/v0_1_15/codex_plan_audit_prompt.md`** —
    round-1 prompt (for context only; not under audit).

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions (round 2)

### Q-R1. Did each round-1 revision close its target finding?

For each F-PLAN-01 through F-PLAN-12, verify the round-2 PLAN edit
actually addresses what round-1 cited. Specifically:

**Q-R1.a F-PLAN-01 (W-D arm-1 unreachable).** PLAN §2.B now defines
`is_partial_day` as time-only and `target_present` as a separate
field. PLAN §2.E now fires arm-1 on `is_partial_day && !target_present`.
Verify the predicates are now logically reachable in both states.
Verify the W-A acceptance test 2 ("`is_partial_day` derives from time
+ meal-count alone, target-independent") matches the corrected
predicate verbatim.

**Q-R1.b F-PLAN-02 (tactical detail rewrite).** Tactical §5B now
describes the combined gate cycle; §5C describes empirical post-gate
fixes; §5D is new for v0.1.17. Verify each section is internally
self-consistent and cross-consistent with PLAN.md + v0_1_17/README.md.

**Q-R1.c F-PLAN-03 (AGENTS.md Do Not Do).** Verify lines 416-420 now
read `(v0.1.17 / v0.2.3)` and provenance chain matches the Settled
Decisions D124-135 entry.

**Q-R1.d F-PLAN-04 (provenance arithmetic).** PLAN §1.4 now contains a
16-row disposition table. Verify the table reconciles: 16 slots = 7
kept (v0.1.15) + 9 deferred (v0.1.17, including W-D arm-2). The
maintainer disagreed with Codex's "14 W-ids" claim, attributing it to
the round-0 PLAN's mis-count; verify by re-counting the round-0
catalogue. The table's "Reason" column should justify each cut
against the second-user objective.

**Q-R1.e F-PLAN-05 (W-2U-GATE acceptance).** Verify PLAN §2.G now
restores the v0.1.14 PLAN §2.A "one brief in-session question;
multiple interventions or any maintainer keyboard time = failure"
threshold verbatim. Verify the new P0/P1/P2 + "cheap" (≤0.5
maintainer-day, no D14 re-run, no state-model schema touch)
definitions are concrete enough to fail an audit on.

**Q-R1.f F-PLAN-06 (candidate package).** Verify PLAN §2.G specifies
wheel + sdist from final v0.1.15 branch + clean Python 3.11+ env +
recorded version/commit/install-command. Verify the install record
path is consistent with the transcript path.

**Q-R1.g F-PLAN-07 (W-GYM-SETID scope split).** Verify PLAN §2.A now
splits SQL migration (in-scope) from JSONL recovery (operator path).
Verify the required fixture is named explicitly (no "if any"). Verify
the maintainer's pre-gate procedure is documented (PLAN §4.3).
Sizing impact: §5 should show W-GYM-SETID widened from 1-2d to
1.5-3d; verify.

**Q-R1.h F-PLAN-08 (effort reconciliation).** Verify a single
headline range (16-25 days) appears in PLAN header + §1.2 catalogue
total + §5 arithmetic + README.md + tactical §5B.3. D14 expectation
should be 2-4 rounds, not 2-3.

**Q-R1.i F-PLAN-09 (W-E weigh_in exclusion).** Verify PLAN §2.F W-E
acceptance excludes `weigh_in` from required `present.*.logged`
checks. Verify W-A's `present` block emits `weigh_in: {logged: false,
reason: "intake_surface_not_yet_implemented"}` consistently. Verify
the maintainer raised OQ-1 about pulling W-B forward.

**Q-R1.j F-PLAN-10 (F-PV14-02 known-limitation).** Verify PLAN §4.5
adds the interim cleanup procedure note; raw SQL DELETE remains
prohibited.

**Q-R1.k F-PLAN-11 (candidate-absence procedure).** Verify PLAN §4.6
adds v0.1.15-specific procedure with three named options if no
candidate at Phase 0 close. Verify the procedure is more aggressive
than v0.1.14 path 2 (the cycle's purpose IS the gate, so "open
implementation without it" doesn't apply).

**Q-R1.l F-PLAN-12 (active-repo declaration).** Verify AGENTS.md
"Authoritative orientation" preamble declares the active path
explicitly. Verify the declaration cites PLAN §4.8 + the round-1
finding for provenance.

### Q-R2. Did the round-2 revisions introduce new contradictions?

Round-1 findings were largely cross-doc consistency issues. Round-2
revisions touched many files in fan-out; verify no second-order
contradictions surfaced.

**Q-R2.a.** The W-A predicate split (F-PLAN-01) added `target_present`
to W-A's output. PLAN §1.3 sequencing puts W-A and W-C in Phase 1
parallel. Can W-A actually be implemented in parallel with W-C if W-A
queries `nutrition_target` (W-C's table)? PLAN §4.2 claims yes via
"W-A's read-side query handles the empty-table case (`target_present:
"unavailable"`)." Verify the claim — is the empty-table case actually
testable before W-C's table exists? (E.g., does the test require a
schema migration as a prerequisite?)

**Q-R2.b.** The W-2U-GATE P-tier definitions (F-PLAN-05) introduced
"P0 = … OR causes the agent to give a recommendation that triggers
user-visible loss of trust mid-session" and "P1 = causes incorrect or
repeated agent prompt, OR silent trust loss the user notices."
"Silent trust loss" appears in both tiers (P0: "user-visible," P1:
"user notices"). Verify the boundary is sharp — what's the
distinction between "user-visible loss of trust" and "silent trust
loss the user notices"?

**Q-R2.c.** PLAN §4.6 says path (a) "hold the cycle open" if no
candidate. Tactical §5B doesn't reference this procedure. Verify
tactical §5B doesn't need a hold-procedure note for cross-doc
consistency.

**Q-R2.d.** The 16-slot provenance table in PLAN §1.4 counts W-D as
two slots (arm-1 kept, arm-2 deferred). PLAN §1.2 catalogue counts
W-D arm-1 as one of the 7 kept W-ids. v0.1.17/README.md scope counts
W-D arm-2 as one of the deferred W-ids. Verify the count is
consistent: 7 v0.1.15 W-ids includes W-D arm-1 as its own row; 9
v0.1.17 W-ids includes W-D arm-2 as its own row; total = 16 catalogued
slots. Or is W-D one W-id with two arms (then 15 W-ids)? The PLAN
should pick one accounting and apply consistently.

### Q-R3. Are the new structural elements internally coherent?

The round-2 revisions added several new structural elements; audit
them on their own merits.

**Q-R3.a.** P0/P1/P2/cheap definitions (PLAN §2.G). Per Q-R2.b above,
the P0/P1 boundary on trust-loss may be unclear. Beyond that: is
"cheap = ≤0.5 maintainer-day, no D14 re-run, no state-model schema
touch" specific enough? What about: a fix that touches the
capabilities manifest (not state-model but agent-contract)?

**Q-R3.b.** Candidate-package shape (PLAN §2.G). "Wheel + sdist from
final v0.1.15 branch (post-merge to main, tagged commit)" — does
"tagged commit" mean a release tag (v0.1.15) or just a ref tag for
the gate session? PyPI publish typically requires a release tag; the
PLAN says "no PyPI pre-release," so what's the tag for?

**Q-R3.c.** W-GYM-SETID maintainer pre-gate procedure (PLAN §4.3).
Three steps: backup → reproject --cascade-synthesis → re-synthesize.
Is the order correct? Specifically, does `hai state reproject
--cascade-synthesis` require a clean state (i.e., needs to follow a
fresh `hai state init`), or can it run against existing state?
Cite the relevant cli.py / projector source if needed.

**Q-R3.d.** v0.1.15-specific candidate-absence procedure (PLAN §4.6).
Three options if no candidate. Are they exhaustive? E.g., what if a
candidate signs up but withdraws mid-Phase-1? Currently the procedure
covers Phase 0 close only.

**Q-R3.e.** AGENTS.md active-repo declaration. The text says "ignore
unless explicitly working on historical provenance." What counts as
"explicitly"? (I.e., is this a magic-words requirement, or a
maintainer judgment call?)

### Q-R4. Round-1 findings the round-2 PLAN didn't address

Verify by re-reading the round-1 findings list against the round-2
PLAN section-by-section. If any round-1 finding isn't addressed,
surface it. (Round-2 maintainer response claims 12/12 applied; verify
the claim.)

### Q-R5. Open questions raised by the maintainer

The maintainer raised OQ-1 / OQ-5 / OQ-6 in PLAN §8. Codex's role:
provide an opinion before maintainer ratifies, so the ratification
isn't unilateral.

**Q-R5.a OQ-1 (W-B pull-forward).** The current shape has W-A's
`weigh_in: {logged: false, reason: "intake_surface_not_yet_implemented"}`
and the morning-ritual skill verbalizing without state-write. If the
foreign user logs a verbal weigh-in, does the absence of a state row
break any downstream classification or recommendation? If yes, W-B
must pull forward. If no, the verbalize-without-state-write shape is
acceptable.

**Q-R5.b OQ-5 (round-0 self-audit pattern → AGENTS.md D-entry).**
Should the pattern be codified? Argument for: prevents future
scope-bloat in cycle openings. Argument against: pattern is too
specific to this restructure to generalize. Codex's verdict.

**Q-R5.c OQ-6 (foreign-device OS).** Mac / Windows / Linux / matrix?
Strategic question — is the gate test meaningful on one OS, or does
the maintainer need a multi-OS sweep before the gate counts? Codex's
verdict on whether single-OS is enough for v0.1.15.

### Q-R6. Sizing honesty under the revised scope

Round-2 widened sizing from 14-20 to 16-25 days. Is the widening
sufficient given the round-1 findings (especially F-PLAN-07's JSONL
recovery + F-PLAN-05's session rigor)? Or should the headline widen
further?

**Q-R6.a.** Per-WS sizing per the §5 table — sanity-check each WS
estimate against historical comparable work (cite v0.1.10-v0.1.14
RELEASE_PROOF actuals where applicable).

**Q-R6.b.** D14 round count expectation (2-4 rounds). Round 1 closed
at 12 findings; round 2 at the halving signature should drop to 4-7.
If round 2 surfaces ≥10 findings, what's the implication for the
cycle? Is "round 5" feasible, or does cycle-too-large fire?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_plan_audit_round_2_response.md` matching
the existing convention:

```markdown
# Codex Plan Audit Response — v0.1.15 PLAN.md (Round 2)

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 2

## Round-1 finding closure verification

For each F-PLAN-01..12: state CLOSED / NOT_CLOSED / CLOSED_WITH_RESIDUAL.

## New findings (round 2)

### F-PLAN-R2-01. <short title>

**Q-bucket:** Q-R1.x / Q-R2.x / Q-R3.x / Q-R4 / Q-R5.x / Q-R6.x
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-R2-02. ...

## Open questions answered (Codex opinions on OQ-1, OQ-5, OQ-6)

## Open questions for maintainer (new from round 2)
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.X claims `core/foo.py:171` but `foo.py` is at
`core/bar/foo.py:171`" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding. If
  finding count is ≤ 3 and severity ≤ acceptance-criterion-weak,
  the maintainer may close in-place without round 3.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

For round 2 specifically, **PLAN_INCOHERENT is unlikely** unless a
round-1 revision introduced a structural contradiction (Q-R2). If
finding count ≥ 8, surface as cycle-too-large signal — the
maintainer may want to consider whether the v0.1.15 + v0.1.17
restructure is itself the problem.

---

## Step 5 — Out of scope

- Prior-cycle implementation (already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started).
- v0.1.16 PLAN scope (post-gate empirical work; PLAN.md authored
  after v0.1.15 ships).
- v0.1.17 PLAN scope (only the README is in tree at this audit).
- v0.2.x scope.
- Round-1 findings already verified CLOSED in Step 1 / Q-R1 — only
  surface as new round-2 findings if a CLOSED status is reversed by
  cross-doc consistency check.

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit round 1 ← CLOSED 2026-05-03
                                    PLAN_COHERENT_WITH_REVISIONS
  Maintainer response             ← CLOSED 2026-05-03
                                    12/12 findings applied
  PLAN.md round 2                 ← CLOSED 2026-05-03
  [D14] Codex plan audit round 2  ← you are here
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs, halving signature 12 → 6 → 3 → 0)

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix
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

- `reporting/plans/v0_1_15/codex_plan_audit_round_2_response.md` (new)
  — your findings.
- `reporting/plans/v0_1_15/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_15/codex_plan_audit_round_3_prompt.md`
  (subsequent round, if revisions warrant another pass).
- Cross-doc revisions (if Q-R2 surfaces second-order contradictions):
  the maintainer will fan out fixes to `tactical_plan_v0_1_x.md`,
  `agent_state_visibility_findings.md`, `AGENTS.md`, and/or
  `v0_1_17/README.md` as appropriate. Audit response should name
  *which* docs need editing for each cross-doc finding.

**No code changes.** No test runs. No state mutations.
