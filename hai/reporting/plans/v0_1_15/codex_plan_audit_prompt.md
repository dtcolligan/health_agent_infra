# Codex External Audit — v0.1.15 PLAN.md (pre-cycle plan review)

> **Why this round.** v0.1.15 PLAN.md was authored 2026-05-02 evening
> after a maintainer-as-user session surfaced a class of agent-state-
> visibility bugs (matching the morning session findings already
> catalogued in `post_v0_1_14/agent_state_visibility_findings.md`)
> plus one new runtime bug (W-GYM-SETID — gym set-id PK collision).
> The PLAN went through **two scope rounds in one evening**: an
> initial 14-W-id "everything queued" maintainer override (round 0),
> followed by a Claude-led self-audit that cut to 7 W-ids optimised
> for the second-user objective (round 1, the version under review).
> The audit must verify both the cuts and the cross-document
> consistency of the six-file restructure that followed.
>
> **D14 is a settled decision** (added at v0.1.11 ship). Empirical
> norm: 2-4 rounds for a substantive PLAN, settling at the
> `10 → 5 → 3 → 0` halving signature.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit is
> on the *plan document itself* — its coherence, sequencing, sizing
> honesty, hidden coupling — and on the cross-doc consistency of
> the restructure.
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
# 5660fd7 introduced the v0.1.15 / v0.1.16 split this audit reviews,
# OR a later commit if the maintainer has authored further v0.1.15
# cycle work). The v0.1.14.1 hardening ship (856e689) should appear
# within the last 5 commits.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# — that commit is the head of the STALE checkout under
# /Users/domcolligan/Documents/health_agent_infra/, which is months
# behind and must not be audited.
ls reporting/plans/v0_1_15/
# expect: PLAN.md, README.md, codex_plan_audit_prompt.md (this file)
ls reporting/plans/v0_1_17/
# expect: README.md
```

The discriminator that matters is dual-repo: the stale checkout's
HEAD is `2811669 Phase H: implement conversational intake` and is
months behind. The active repo's HEAD is post-v0.1.14.1 and ahead by
many cycles. If HEAD is `2811669`, **stop and surface the
discrepancy**. Otherwise, the specific commit message at HEAD does
not need to match a fixed string — what matters is that v0.1.14.1
appears in recent log and the v0.1.15 / v0.1.17 plan dirs exist.

**Ignore any tree under `/Users/domcolligan/Documents/`** — a stale
checkout exists there and was the source of the round-0 over-scoping
(memory entry `feedback_verify_active_repo_at_session_start.md`
records the incident; one of the audit questions below probes
whether the PLAN adequately mitigates the recurrence risk).

---

## Step 1 — Read the orientation artifacts

In order:

1. **`AGENTS.md`** — operating contract. Pay attention to:
   - "Governance Invariants" (W57 in particular — W-C is W57-gated).
   - **"Settled Decisions" D124-135** — the W-29 destination entry
     was edited as part of this restructure (v0.1.15 → v0.1.17).
     Verify the provenance chain reads honestly.
   - "Do Not Do" — note any reversals this cycle proposes (none
     intended).
   - **"Patterns the cycles have validated"** — provenance
     discipline, summary-surface sweep, honest partial-closure
     naming, audit-chain empirical shape. Apply these as you audit.
2. **`reporting/plans/strategic_plan_v1.md`** — vision; note the
   sections this cycle proposes editing (none intended; restructure
   is purely tactical).
3. **`reporting/plans/tactical_plan_v0_1_x.md`** — release-by-
   release plan. **Rows 46-48 (v0.1.15 / v0.1.16 / v0.1.17) were
   rewritten as part of this restructure.** The "Total v0.1.x →
   v0.2.3 horizon" paragraph below the table was also rewritten.
4. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`**
   — F-AV-01..05 are the source for W-A through W-E. The
   "Recommendation: cycle scoping" section was rewritten as part
   of this restructure (the original recommendation argued for a
   v0.1.15-mechanical / v0.1.16-hardening split that this cycle's
   restructure rejects in favour of v0.1.15-gate / v0.1.17-
   maintainability).
5. **`reporting/plans/post_v0_1_14/carry_over_findings.md`** —
   F-PV14-01 (in v0.1.15 scope) + F-PV14-02 (deferred to v0.1.17).
6. **`reporting/plans/v0_1_14/RELEASE_PROOF.md`** §carry-overs —
   prior-cycle carry-overs. v0.1.15 inherits W-2U-GATE; the rest
   (W-29, W-AH-2, W-AI-2, W-AM-2, W-Vb-4) were originally inherited
   into v0.1.15 round-0 and reassigned to v0.1.17 by the restructure.
7. **`reporting/plans/v0_1_14_1/RELEASE_PROOF.md`** + REPORT.md —
   most-recent shipped state (Garmin-live structured signal).
8. **`reporting/plans/v0_1_15/README.md`** — entry point + reading
   order for the cycle session. Rewritten as part of the
   restructure.
9. **`reporting/plans/v0_1_15/PLAN.md`** — the artifact under
   review.
10. **`reporting/plans/v0_1_17/README.md`** — workspace for the
    deferred maintainability + eval work. Confirm the deferral
    register is complete (every W-id cut from v0.1.15 round-0
    appears in v0.1.17, with no orphans and no double-counts).

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions

### Q1. Cycle thesis coherence — did round-0 self-audit cut the right things?

The round-0 self-audit (PLAN §1.4) cut 8 W-ids from a 14-W-id
maintainer override down to 7 W-ids by classifying each WS as
"affects second-user end-to-end flow" vs "doesn't." The classifier
was: does this WS make the difference between the foreign user
reaching `synthesized` or not?

**Q1.a.** Per-WS, do you agree with the cut/keep classification?
Specifically:
- W-29 (cli.py mechanical split) — cut. Mechanical refactor with
  byte-stable manifest. Does the foreign user benefit from it
  during the gate session?
- W-AH-2 / W-AI-2 / W-AM-2 (eval substrate) — cut. Validates
  runtime against fixtures, not against a real user. Does the
  gate session need expanded eval scenarios to be meaningful?
- W-Vb-4 (persona-replay residual P7..P12) — cut. Internal
  correctness. Does the foreign user need P7..P12 covered before
  their session is meaningful?
- W-B (`hai intake weight`) — cut. The maintainer planned weigh-ins
  starting 2026-05-03. Does the foreign user need weight intake
  on day 1?
- F-PV14-02 (`hai sync purge`) — cut. Surgical-cleanup tool.
  Would the foreign user hit a contamination scenario in their
  first session?
- W-D arm-2 (end-of-day projection) — cut. Enhancement over arm-1.
  Does arm-1 (suppress) close the user-trust bug, or does the
  foreign user need projection?

**Q1.b.** Symmetric check — anything *kept* in v0.1.15 that
wouldn't actually affect the foreign user? In particular, is
F-PV14-01 (CSV-fixture isolation marker) really needed for the
gate session, or could it defer to v0.1.17 as well?

**Q1.c.** The "second-user objective" is operationalized as
"reaches `synthesized`" — is that the right operationalization?
Could the foreign user reach `synthesized` while still hitting a
user-trust bug we'd want to catch? E.g., gym set drops mid-session
but they don't notice until later. Should the acceptance criterion
be sharper than "reaches `synthesized`"?

### Q2. Sequencing honesty

PLAN §1.3 specifies a DAG with Phase 1 (W-GYM-SETID + W-A +
F-PV14-01 + W-C parallelizable) → Phase 2 (W-D arm-1 + W-E,
both depend on W-A) → Phase 3 (W-2U-GATE).

**Q2.a.** Is W-A sufficient to unblock W-D arm-1, or does W-D
arm-1 need W-C as well? PLAN §2.E says arm-1 fires when
"`is_partial_day == true && no active nutrition_target row`" —
which means it reads the absence of a W-C row. Does that count
as a dependency on W-C, or is "absence of W-C row" satisfiable
even before W-C ships?

**Q2.b.** W-E "consumes W-A presence tokens" — is the contract
between W-A's output shape and W-E's skill input precise enough
that Phase 2 W-E can start as soon as W-A's interface is locked,
or does W-E need W-A's full implementation to test against?

**Q2.c.** W-2U-GATE Phase 3 — what is "the candidate package built
from Phases 1-2"? Is that a packaged release artefact, or just
"main with all Phase 1+2 commits landed"? PLAN doesn't specify.

### Q3. Effort estimate honesty

PLAN §5 sums to 13-22 days mid-band, adjusted to 14-20 with
coordination overhead. v0.1.14's 13-W-id substantive cycle
estimated 30-43 days and closed at 35.

**Q3.a.** Per-WS sizing — particularly the 1-2d for W-GYM-SETID
(includes a state-DB migration with audit-chain preservation) and
the 3-5d for W-2U-GATE (includes coordinating a foreign user,
recording the session, P0 fixes inline, and any P1 fixes). Are
these realistic, or are they understated relative to historical
sizing?

**Q3.b.** The cycle has fewer W-ids than v0.1.14 (7 vs 13) but
proportionally more new schema (W-C `nutrition_target` table +
migration; W-GYM-SETID set_id format change + migration) and a
release-blocker workstream (W-2U-GATE) that depends on an
external coordinator. Is the cycle compressing too much?

**Q3.c.** What multiplier should D14 round count add? PLAN §1
claims "2-3 rounds at the empirical halving signature." For a
substantive cycle with cross-doc consistency stakes, is 2-3
realistic, or should the maintainer plan for 4?

### Q4. Hidden coupling — across the restructure

The restructure edited 6 files: `v0_1_15/PLAN.md`,
`v0_1_15/README.md`, `v0_1_17/README.md` (new),
`tactical_plan_v0_1_x.md`, `post_v0_1_14/agent_state_visibility_findings.md`,
`AGENTS.md`. Cross-doc consistency is a major audit surface here
because the changes to one document could contradict claims in
another.

**Q4.a.** Verify the W-29 destination chain across:
- `AGENTS.md` D124-135 W29/W30 entry text
- `v0_1_15/PLAN.md` §1.4 + §3 W-29 redestination claim
- `v0_1_17/README.md` scope provenance
- `tactical_plan_v0_1_x.md` row 48 (v0.1.17)

**Q4.b.** Verify the v0.2.0 dependency claim:
- `tactical_plan_v0_1_x.md` row v0.2.0: "NOT dependent on v0.1.17"
- `v0_1_17/README.md` "Dependency on v0.1.15 + v0.1.16" + "Out of
  scope": "v0.2.0 schema work depends on v0.1.16 close, runs
  parallel to or after v0.1.17"
- Is "parallel to or after v0.1.17" consistent with "NOT
  dependent on v0.1.17"? Either v0.2.0 needs v0.1.17 closed
  (sequential) or it doesn't (parallel). Pick one.

**Q4.c.** Verify the W-D arm-1 / arm-2 split:
- `v0_1_15/PLAN.md` §2.E: arm-1 only, arm-2 deferred to v0.1.17
- `v0_1_17/README.md` scope: includes W-D arm-2
- `agent_state_visibility_findings.md` F-AV-04: defines both arms
  as a two-arm fix
- Does the deferral split create a partial-closure scenario that
  the AGENTS.md "Honest partial-closure naming" pattern would
  flag?

**Q4.d.** Verify the v0.1.16 scope:
- Maintainer's stated framing: "v0.1.16 cycle should literally
  just be bug fixes from the onboarding tests"
- `tactical_plan_v0_1_x.md` row 47: "Empirical post-gate bug
  fixes from v0.1.15's W-2U-GATE recorded session. P0 closed
  inline during v0.1.15 cycle; v0.1.16 picks up named-deferred
  P1 + any P2 surfaced during the recorded session."
- `v0_1_15/PLAN.md` §6 ship gates: "All P0 findings from the
  foreign-user session closed inline; P1 named-deferred or
  closed."
- Is "P1 named-deferred or closed" inside v0.1.15 consistent
  with v0.1.16 picking up "named-deferred P1"? If P1 is closed
  inline during v0.1.15, what's left for v0.1.16?

**Q4.e.** Verify the agent_state_visibility_findings rewrite
preserved the original coupling argument (W-A through W-D share
architecture). PLAN §1.3 sequences W-A first then W-D arm-1 —
which honors the coupling. But the rewrite also pulled W-B (body-
comp) into v0.1.17 separately from W-A — is that a coupling break?

### Q5. Acceptance criterion bite

**Q5.a.** PLAN §2.G W-2U-GATE acceptance: "Non-maintainer foreign
user reaches `synthesized` end-state on a fresh device.
Maintainer presence: hands-off (observe-only). Session transcript
captured. P0 findings closed inline before ship; P1 closed if
cheap or named-deferred to v0.1.16; P2+ defer to v0.1.16."
- "P0 / P1 / P2" are not defined in the PLAN.
- "Closed if cheap" is not defined.
- The maintainer is responsible for triage, but the contract
  doesn't name a triage threshold.
- Is this acceptance criterion specific enough to fail on, or
  does its ambiguity guarantee a "shippable" verdict regardless
  of session quality?

**Q5.b.** PLAN §2.A W-GYM-SETID acceptance: three test bullets.
The migration test mentions "if any in test fixtures" for the
multi-exercise day case — does the test plan rely on a fixture
that may not exist? If so, does authoring the fixture count as
sub-WS effort?

**Q5.c.** PLAN §2.D W-C acceptance — schema migration test +
W57 gate test + read-side test + integration. Is the integration
test ("classifier reads the active target row when classifying")
actually W-D arm-1's responsibility, not W-C's? The boundary
between "W-C provides the row" and "W-D consumes it" matters for
sequencing.

### Q6. Settled-decision integrity

**Q6.a.** AGENTS.md D124-135 W29 entry — the rewritten text adds
a third "destination updated" timeline entry. Quote the prior
text and the new text and verify:
- Original 2026-05-02 mid-day entry preserved verbatim
- New 2026-05-02 evening redestination provenance honest
- The chain reads: v0.1.13 prep → v0.1.14 deferred → v0.1.15
  scheduled (mid-day) → v0.1.17 redestinated (evening). Is each
  link cited properly?

**Q6.b.** No new D-entries proposed; no settled-decision
reversals. Confirm or surface a D-entry the restructure should
add (e.g., "round-0 self-audit pattern" — if this restructure's
self-audit-then-cut shape is novel, should it become a settled
decision?).

### Q7. What the plan doesn't say

**Q7.a.** Abort path — what triggers an abort? PLAN §4.4 says
"hold the cycle open and continue Phase 1+2 polish, do not ship
without the recorded session" if no candidate. What about other
abort conditions — e.g., W-GYM-SETID migration breaks an existing
user state, or D14 round 1 returns PLAN_INCOHERENT?

**Q7.b.** Rollback for W-GYM-SETID migration — PLAN §4.3 names
`hai backup` as the rollback path. Has v0.1.14 W-BACKUP been
verified against this specific migration shape? "Backed up via
hai backup" assumes the backup format covers the gym_set table;
verify.

**Q7.c.** Foreign-user candidate — PLAN §4.4 says the absence
procedure carries forward from v0.1.14 §1.3.1 path 2. Does that
path 2 actually apply to v0.1.15? The original was "no candidate
on file at pre-implementation gate, defer the WS." For v0.1.15
the gate is Phase 3, not the whole cycle. Confirm the procedure
maps cleanly.

**Q7.d.** Dual-repo confusion mitigation (PLAN §4.6) — Step 0
of this prompt says "Ignore any tree under /Documents/." Is
that sufficient codification, or should AGENTS.md or another
durable doc also declare the active repo path?

### Q8. Provenance / external-source skepticism

**Q8.a.** PLAN §1.4 cites a Claude-led round-0 self-audit. The
artifact is a chat transcript, not a tracked doc. Does the
provenance chain hold up under audit, or is there a missing
artifact (e.g., should the round-0 14-W-id draft be preserved as
a `v0_1_15/round_0_draft.md` for traceability)?

**Q8.b.** The "second-user objective" framing comes from the
2026-05-02 evening session. Where is that objective formally
stated in a tracked doc? `tactical_plan_v0_1_x.md` row 46 says
"non-maintainer foreign user reached `synthesized`" — but is
that derived from the strategic plan or from in-session
maintainer judgment? If the latter, is it durable enough to lock
the cycle around?

### Q9. Restructure-specific — is the v0.1.15 / v0.1.16 / v0.1.17 split optimal?

This is the audit question that distinguishes this round from a
vanilla cycle audit. The maintainer chose to combine v0.1.15-prep
+ v0.1.16-gate into a single v0.1.15 (gate ship-claim moves one
release earlier) and split off maintainability/eval into a new
v0.1.17 (deferred from round-0).

**Q9.a.** Counter-proposal — should the maintainability work
land in v0.1.16 instead of v0.1.17, with v0.1.16 = "post-gate
fixes + maintainability" (combined) and no v0.1.17 needed?
Argument for: keeps cycle count constant. Argument against:
v0.1.16 would mix empirical bug fixes (unknowable scope) with
mechanical refactor (knowable scope), violating the
single-axis ship-claim discipline.

**Q9.b.** Counter-proposal — should W-A through W-E stay in
v0.1.16 (per the original `agent_state_visibility_findings.md`
recommendation) and v0.1.15 ship as mechanical-only? Argument:
the original recommendation's coupling argument (W-A through
W-D share architecture) is preserved; the gate test runs against
maintenance-tier code. Argument against: the gate test would
hit the daily-loop bugs and produce a P0 wave that v0.1.16
absorbs anyway, just with worse signal-to-noise.

**Q9.c.** Sizing — the new v0.1.15 is 14-20 days; v0.1.17 is
25-39 days. Combined: 39-59 days, almost identical to round-0's
39-60 days. Is the split actually buying anything beyond
single-axis ship claims, or is it overhead-for-its-own-sake?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_plan_audit_response.md` matching the
existing convention:

```markdown
# Codex Plan Audit Response — v0.1.15 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 1

## Findings

### F-PLAN-01. <short title>

**Q-bucket:** Q1 / Q2 / Q3 / Q4 / Q5 / Q6 / Q7 / Q8 / Q9
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

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.X claims `core/foo.py:171` but `foo.py` is at
`core/bar/foo.py:171`" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

For this round specifically, **PLAN_INCOHERENT is on the table**
if the round-0 self-audit cut the wrong things (Q1) or the
cross-doc consistency check surfaces direct contradictions (Q4).

---

## Step 5 — Out of scope

- Prior-cycle implementation (already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started).
- v0.1.16 PLAN scope (post-gate empirical work; PLAN.md authored
  after v0.1.15 ships).
- v0.1.17 PLAN scope (only the README is in tree at this audit;
  the PLAN itself authors after v0.1.15 + v0.1.16 close).
- v0.2.x scope (named in tactical_plan_v0_1_x.md but not in this
  PLAN's commitments).
- The strategic + tactical + eval + success + risks docs beyond
  the deltas this cycle proposes (tactical_plan rows 46-48 +
  horizon paragraph; agent_state_visibility_findings recommendation
  section; AGENTS.md D124-135).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit ← you are here
  Maintainer response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs)

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

- `reporting/plans/v0_1_15/codex_plan_audit_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_15/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_15/codex_plan_audit_round_N_response.md`
  (subsequent rounds, if revisions warrant another pass).
- Cross-doc revisions (if Q4 surfaces contradictions): the
  maintainer will fan out fixes to `tactical_plan_v0_1_x.md`,
  `agent_state_visibility_findings.md`, `AGENTS.md`, and/or
  `v0_1_17/README.md` as appropriate. Audit response should name
  *which* docs need editing for each cross-doc finding.

**No code changes.** No test runs. No state mutations.
