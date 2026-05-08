# Codex External Audit — v0.1.15 PLAN.md (D14 round 3)

> **Why this round.** D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS
> with 12 findings (F-PLAN-01..12); round 2 closed
> PLAN_COHERENT_WITH_REVISIONS with 7 findings (F-PLAN-R2-01..07).
> Halving signature held: 12 → 7. Round 3 is the projected
> closing round — the maintainer expects 2-4 nit-class findings,
> closable in-place per the round-2 prompt's Step 4 if severity
> stays ≤ acceptance-criterion-weak.
>
> The maintainer applied all 7 round-2 findings on 2026-05-03 —
> 6 verbatim/agreed, 1 with shape extension (F-PLAN-R2-04 added a
> "SUPERSEDED" header note to `agent_state_visibility_findings.md`
> instead of rewriting the in-doc F-AV-01 example, preserving
> original-finding audit trail). Per-finding triage in
> `reporting/plans/v0_1_15/codex_plan_audit_round_2_response_response.md`.
>
> Round 3 audits whether (a) each round-2 revision actually closes
> its target finding, (b) the round-3 PLAN's three new OQs
> (OQ-7 / OQ-8 / OQ-9) are coherent and the chosen defaults are
> right, (c) no third-order contradictions surfaced from the
> typed-contract / propagation / supersede edits, and (d) the
> PLAN is shippable as-written for Phase 0 open.
>
> **D14 is a settled decision** (added at v0.1.11 ship).
> Substantive PLANs settle in 2-4 rounds at the
> `12 → 7 → 3 → 0` halving signature. If round 3 surfaces > 4
> findings or any plan-incoherence severity, signal that the
> cycle may need a fourth round; if ≤ 3 nits, recommend close
> in-place.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit
> is on the *plan document* — coherence of the round-3 revisions,
> verification that the OQ-7/8/9 defaults are sound, and a final
> cross-doc sweep before the cycle opens.
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
# 5660fd7 introduced the v0.1.15 / v0.1.16 split, OR a later
# commit if the maintainer has authored further v0.1.15 cycle
# work). The v0.1.14.1 hardening ship (856e689) should appear
# within the last 5 commits.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# — that commit is the head of the STALE checkout under
# /Users/domcolligan/Documents/health_agent_infra/, which is months
# behind and must not be audited.
ls reporting/plans/v0_1_15/
# expect: PLAN.md, README.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md,
#         codex_plan_audit_round_2_response_response.md,
#         codex_plan_audit_round_3_prompt.md (this file)
ls reporting/plans/v0_1_17/
# expect: README.md
```

The discriminator that matters is dual-repo: the stale checkout's
HEAD is `2811669 Phase H: implement conversational intake` and is
months behind. The active repo's HEAD is post-v0.1.14.1 and ahead
by many cycles. If HEAD is `2811669`, **stop and surface the
discrepancy**. Otherwise the specific commit message at HEAD does
not need to match a fixed string — what matters is that v0.1.14.1
appears in recent log and the v0.1.15 / v0.1.17 plan dirs exist.

**Ignore any tree under `/Users/domcolligan/Documents/`** — same
stale-checkout note as rounds 1 + 2. AGENTS.md "Authoritative
orientation" preamble (added per round-1 F-PLAN-12, citation fixed
per round-2 F-PLAN-R2-03) declares the active path durably.

---

## Step 1 — Read the orientation artifacts

Round-3 reading order is wider than rounds 1 + 2 because the
chain of audit responses + maintainer responses + revised PLANs is
the audit context.

In order:

1. **`reporting/plans/v0_1_15/codex_plan_audit_response.md`** —
   round-1 findings (F-PLAN-01..12). Already verified CLOSED or
   CLOSED_WITH_RESIDUAL by round 2; round 3 only re-checks if a
   round-3 revision could plausibly have re-opened a round-1
   finding.
2. **`reporting/plans/v0_1_15/codex_plan_audit_response_response.md`**
   — maintainer's round-1 triage. Context only.
3. **`reporting/plans/v0_1_15/codex_plan_audit_round_2_response.md`**
   — round-2 findings (F-PLAN-R2-01..07). **Authoritative for
   round-3 closure verification (Q-R3.1).**
4. **`reporting/plans/v0_1_15/codex_plan_audit_round_2_response_response.md`**
   — maintainer's round-2 triage. Names which findings were applied
   verbatim, which had shape extensions, and which raised new OQs.
   Cross-check each disposition against the actual PLAN.md edit.
5. **`reporting/plans/v0_1_15/PLAN.md`** — the round-3 PLAN under
   review. Pay special attention to:
   - Header (lines 3-7) — sizing 16-25 / D14 expectation 2-4 /
     round-2 verdict noted.
   - §1.2 catalogue — per-WS effort matches §5 arithmetic
     (W-GYM-SETID 1.5-3d, W-2U-GATE 4-7d, total 16-25d).
   - §1.4 — "16 catalogued slots = 7 kept + 9 deferred" accounting.
   - §2.B — W-A typed `target_status: "present" | "absent" |
     "unavailable"` enum + `is_partial_day` target-independent.
   - §2.E — W-D arm-1 fires on `is_partial_day && target_status
     in ("absent", "unavailable")`.
   - §2.G — P-tier definitions (threshold breach = P0;
     capabilities-manifest changes excluded from "cheap").
   - §4 risk 5 — F-PV14-02 truthful interim cleanup options
     (full restore OR leave cosmetic rows; selective restore
     does NOT exist; cites `cli.py:8588-8599`).
   - §4 risk 6 — candidate-withdrawal-mid-cycle reentry sentence.
   - §6 — ship gates restate full §2.G contract.
   - §8 — OQ-1..6 closed with disposition; OQ-7/8/9 raised as
     round-3 ratifications.
6. **`AGENTS.md`** — verify round-2 fan-out:
   - "Authoritative orientation" preamble citation now reads
     `PLAN.md §4 item 8` (was incorrectly §4.6 in round-1 fan-out;
     fixed in round-2 per F-PLAN-R2-03).
   - "Do Not Do" lines 416-420 still say `(v0.1.17 / v0.2.3)`
     (round-1 fix; round-3 cross-checks no regression).
7. **`reporting/plans/tactical_plan_v0_1_x.md`** §5B — verify:
   - Per-WS effort table matches PLAN §1.2 + §5 (W-GYM-SETID
     1.5-3d, W-2U-GATE 4-7d).
   - §5B.3 effort says 16-25 days + halving signature 12 → 7 →
     projected 2-4.
   - Archive bullet now includes install record path.
8. **`reporting/plans/v0_1_17/README.md`** — verify "16-catalogued-
   slot" framing (was 14-W-id in round-1 draft).
9. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`**
   — verify the SUPERSEDED + W-A predicate-supersede header note
   is present at the top of the doc; the F-AV-01 in-doc example is
   intentionally NOT rewritten (preserves original-finding audit
   trail per F-PLAN-R2-04 maintainer disposition).
10. **`reporting/plans/post_v0_1_14/carry_over_findings.md`** —
    unchanged round-3; verify F-PV14-02 deferral aligns with PLAN
    §4.5's truthful interim path.
11. **`reporting/plans/v0_1_14/PLAN.md` §2.A** — verify the
    W-2U-GATE acceptance threshold restored in PLAN §2.G matches
    the v0.1.14 verbatim (lines 200-204 of v0.1.14 PLAN). Round-2
    F-PLAN-R2-05 sharpened the P0/P1 boundary; the threshold
    itself is still v0.1.14 verbatim.
12. **`src/health_agent_infra/cli.py:8588-8599`** + **`src/health_agent_infra/core/backup/bundle.py:170-175, 285-307`**
    — verify the F-PV14-02 selective-restore correction in PLAN
    §4.5 is sourced correctly (line ranges should still resolve
    to the `cmd_restore` handler + restore-bundle internals).

Cross-check that everything PLAN.md cites actually exists in the
tree. Broken cross-references count as findings.

---

## Step 2 — The audit questions (round 3)

### Q-R3.1. Did each round-2 revision close its target finding?

For each F-PLAN-R2-01 through F-PLAN-R2-07, verify the round-3
PLAN edit actually addresses what round 2 cited.

**Q-R3.1.a F-PLAN-R2-01 (target_present contract).** PLAN §2.B now
defines `target_status` as a three-valued enum and W-A's output
contract is typed. PLAN §2.E W-D arm-1 fires on `is_partial_day
&& target_status in ("absent", "unavailable")`. Verify:
- The enum values are mutually exclusive and collectively exhaust
  the state space (target row exists / table populated but no row
  / table empty / table missing pre-W-C).
- Acceptance test 4 actually covers the pre-W-C-table-missing case
  (the parallelization escape hatch claim).
- W-D arm-1's "treat unavailable as suppress" matches the OQ-7
  default the maintainer raised.

**Q-R3.1.b F-PLAN-R2-02 (effort propagation).** Verify a single
sizing range (16-25 days, 2-4 D14 rounds) appears identically in:
- PLAN header (line 6)
- PLAN §1.2 catalogue total
- PLAN §5 arithmetic table + adjusted total
- v0_1_15/README.md
- tactical §5B.3 effort estimate
Per-WS values (W-GYM-SETID 1.5-3d, W-2U-GATE 4-7d) should match
across PLAN §1.2 + PLAN §5 + tactical §5B.

**Q-R3.1.c F-PLAN-R2-03 (16-slot accounting).** Verify the canonical
sentence "16 catalogued slots = 7 kept (v0.1.15) + 9 deferred
(v0.1.17). W-D counted as two slots because the arms ship in
different cycles" appears identically in PLAN §1.4 + v0_1_15/README
+ v0_1_17/README. AGENTS.md citation now reads `PLAN §4 item 8`
(not §4.6).

**Q-R3.1.d F-PLAN-R2-04 (findings doc supersede).** Verify the
supersede header note at the top of `agent_state_visibility_findings.md`
covers both (a) cycle scoping (v0.1.15-mechanical→v0.1.16-hardening
recommendation is dead) and (b) W-A predicate (the
"timestamp + meal count + presence-of-target" structural insight
is dead). Verify the maintainer's deliberate choice to NOT rewrite
the F-AV-01 in-doc example (preserves provenance) is honest — i.e.,
the header note explicitly tells future readers "PLAN is canonical;
this doc is provenance only."

**Q-R3.1.e F-PLAN-R2-05 (P0/P1 overlap).** Verify PLAN §2.G
acceptance restructured so:
- Acceptance-1 threshold breach → P0 (not P1).
- P0 = blocks `synthesized` OR corrupts state OR breaches the
  acceptance-1 threshold.
- P1 = within a threshold-met session, trust-degrading.
- "Cheap" excludes capabilities-manifest changes (per the
  round-2 finding).
Verify these three statements are internally consistent and don't
overlap.

**Q-R3.1.f F-PLAN-R2-06 (selective restore).** Verify PLAN §4.5
now names the truthful options (full restore from pre-leak backup
OR leave cosmetic rows). Verify the cited line range
`cli.py:8588-8599` resolves to the actual `cmd_restore` handler in
the active repo (Step 1 #12). Verify "selective restore" is not
mentioned anywhere else in PLAN.md or tactical.

**Q-R3.1.g F-PLAN-R2-07 (ship-gate completeness).** Verify PLAN §6
ship gates restate the full §2.G contract: acceptance-1 threshold,
P0/P1/P2 disposition, candidate-package shape, install record path,
transcript path, state DB snapshot path. Verify tactical §5B
archive bullet now lists install record alongside transcript +
state DB snapshot. Verify the "commit SHA only" choice is
unambiguous in §2.G (no residual "tagged commit" ambiguity).

### Q-R3.2. Did the round-3 revisions introduce new contradictions?

The round-3 revisions added typed contracts, propagated effort, and
restated ship gates. Verify no third-order contradictions.

**Q-R3.2.a.** The W-A typed contract (F-PLAN-R2-01) added the
acceptance-test-4 case for "table missing pre-W-C." Does the
read-side query in PLAN §2.B acceptance-3 ("`SELECT 1 FROM
nutrition_target WHERE …`") actually handle the `OperationalError`
from a missing table, or does it raise? PLAN should specify the
catch-and-emit-`unavailable` shape OR explicitly say "W-A's read
handler wraps the query in `try/except OperationalError`."

**Q-R3.2.b.** OQ-7 ratifies "treat unavailable as suppress." This
means the foreign user with no targets ever set will see
`nutrition_status=insufficient_data` for every meal logged before
they set a target. Is this a friction the gate session would
notice? If yes, the v0.1.15 morning-ritual flow may need to prompt
the user to set targets early in the gate session — verify W-E
acceptance covers this (or surface as a gap).

**Q-R3.2.c.** PLAN §6 ship gates now restate the full §2.G
contract. Does the duplication risk drift over time (one updated,
the other not)? Consider recommending DRY: §6 should reference
§2.G as the source of truth and only restate the cycle-specific
gates (full pytest, mypy, etc.). This is a nit, not a blocker.

**Q-R3.2.d.** The capabilities-manifest exclusion from "cheap"
(F-PLAN-R2-05) is right but raises: what about `hai capabilities
--markdown` regeneration? PLAN §6 says regenerated and diffed at
ship; if a P1 fix touches the manifest, the diff is by definition
non-trivial, but the diff regeneration itself is not the fix. Is
the boundary clear?

### Q-R3.3. Are the OQ-7/8/9 defaults right?

The maintainer raised three new OQs in round 2 and picked defaults
in round-3 PLAN. Codex's role: confirm or push back on each.

**Q-R3.3.a OQ-7 (`target_status="unavailable"` semantics).**
Default: treat as suppress (same outcome as `absent`). Argument
for: foreign user shouldn't hit a hard fail before setting targets;
suppress is the "honest unknown" path. Argument against: a user
who never sets a target will get `insufficient_data` forever and
may not know they need to set one. Codex's verdict — is suppress
right, or should W-E (or `hai today`) prompt the user to set
targets when `target_status=="unavailable"` for >N days?

**Q-R3.3.b OQ-8 (gate-candidate tag shape).** Default: commit
SHA only. Argument for: install record carries SHA; tag adds
bookkeeping without verification benefit. Argument against:
human-readability — a tag like `gate/v0.1.15-2026-05-15` is
easier to reference in retrospectives than `5660fd7…`. Codex's
verdict.

**Q-R3.3.c OQ-9 (candidate-withdrawal mid-cycle).** Default:
"must re-enter §4.6 (a)/(b)/(c) decision tree before opening
Phase 3." Argument for: prevents silent ship without recorded
session. Argument against: doesn't cover the "withdrawal during
Phase 3" case (the candidate starts the session and aborts
mid-stream). Codex's verdict — is the procedure complete, or
does it need a Phase-3-mid-stream-abort branch?

### Q-R3.4. Round-2 findings the round-3 PLAN didn't address

Re-read the round-2 findings list (F-PLAN-R2-01..07) against the
round-3 PLAN section-by-section. If any round-2 finding isn't
addressed, surface it. (Round-3 maintainer response claims 7/7
applied; verify the claim.)

### Q-R3.5. Sweep for ship-readiness

Round 3 is the final D14 audit before Phase 0 opens (assuming
verdict closes the cycle). Sweep for any remaining absences:

**Q-R3.5.a.** Phase 0 reading list — is it explicit anywhere what
Phase 0's bug-hunt scope is for this cycle? Substantive cycles
require full Phase 0 per AGENTS.md; PLAN should name what the
internal sweep / audit-chain probe / persona matrix runs should
cover.

**Q-R3.5.b.** Test-effort reality — the cycle adds new fixtures
(W-GYM-SETID multi-exercise), new tests (W-A four target_status
states + is_partial_day transitions, W-C four acceptance bullets,
W-D arm-1 four states, W-GYM-SETID five tests, F-PV14-01 repro
+ regression, W-E skill-tests). Is the test surface budgeted in
the per-WS sizing, or is it treated as overhead? The round-2 PLAN
raised this implicitly via F-PLAN-R2-02 sizing widening; verify
round 3 still has slack.

**Q-R3.5.c.** Cross-doc citation integrity — round 1 missed the
AGENTS.md Do-Not-Do, round 2 missed the §4 item 8 vs §4.6
citation. Sweep for any other cross-doc citations in PLAN.md that
might be stale (line numbers in `agent_state_visibility_findings.md`,
`v0_1_14/PLAN.md` references, etc.).

**Q-R3.5.d.** Verdict-driving — if round 3 surfaces ≤ 3 nit-class
findings (acceptance-criterion-weak severity or below), recommend
the maintainer close in-place per the round-2 prompt's Step 4.
If round 3 surfaces ≥ 5 findings or any plan-incoherence severity,
recommend a round 4. State which signal applies in your verdict.

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_15/codex_plan_audit_round_3_response.md`
matching the existing convention:

```markdown
# Codex Plan Audit Response — v0.1.15 PLAN.md (Round 3)

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework before open)

**Round:** 3

**Closure recommendation:** close in-place / round 4 needed /
re-author named sections (per Step 4).

## Round-2 finding closure verification

For each F-PLAN-R2-01..07: state CLOSED / NOT_CLOSED /
CLOSED_WITH_RESIDUAL. Round-1 findings only re-checked if a
round-3 revision could plausibly have re-opened them.

## New findings (round 3)

### F-PLAN-R3-01. <short title>

**Q-bucket:** Q-R3.1.x / Q-R3.2.x / Q-R3.3.x / Q-R3.4 / Q-R3.5.x
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N (or "absent")
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-R3-02. ...

## Open questions answered (Codex opinions on OQ-7, OQ-8, OQ-9)

## Open questions for maintainer (new from round 3, if any)
```

Each finding must be triageable. Vague feedback is not a finding;
"PLAN.md §2.X claims `core/foo.py:171` but `foo.py` is at
`core/bar/foo.py:171`" is a finding.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written. Phase 0 (D11) can
  fire immediately.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. **If finding count is ≤ 3 and severity ≤
  acceptance-criterion-weak, recommend close in-place** without
  round 4. The maintainer applies the nits in PLAN round 4 and
  opens Phase 0; no further D14 audit fires unless the maintainer
  explicitly requests one.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

For round 3 specifically:
- ≤ 3 nit-class findings → close in-place (recommended path).
- 4-7 findings → round 4 prompt should fire.
- ≥ 8 findings OR any plan-incoherence severity → cycle-too-large
  signal; the maintainer may want to consider re-splitting v0.1.15
  + v0.1.17, or pulling W-2U-GATE back to v0.1.16.

---

## Step 5 — Out of scope

- Prior-cycle implementation (already audited and shipped).
- Code changes against this PLAN (Phase 0 hasn't started).
- v0.1.16 PLAN scope (post-gate empirical work; PLAN.md authored
  after v0.1.15 ships).
- v0.1.17 PLAN scope (only the README is in tree at this audit).
- v0.2.x scope.
- Round-1 + round-2 findings already verified CLOSED — only
  surface as new round-3 findings if a CLOSED status is reversed
  by cross-doc consistency check.

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14] Codex plan audit round 1 ← CLOSED 2026-05-03
                                    PLAN_COHERENT_WITH_REVISIONS
                                    12 findings
  Maintainer response             ← CLOSED 2026-05-03
                                    12/12 findings applied
  PLAN.md round 2                 ← CLOSED 2026-05-03
  [D14] Codex plan audit round 2 ← CLOSED 2026-05-03
                                    PLAN_COHERENT_WITH_REVISIONS
                                    7 findings
  Maintainer response             ← CLOSED 2026-05-03
                                    7/7 findings applied
  PLAN.md round 3                 ← CLOSED 2026-05-03
  [D14] Codex plan audit round 3 ← you are here
  (close in-place if ≤3 nits, OR loop to round 4 if substantial)

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

- `reporting/plans/v0_1_15/codex_plan_audit_round_3_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_15/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_15/codex_plan_audit_round_4_prompt.md`
  (only if round 4 is needed; ≤3-nit close-in-place path skips
  this).
- Cross-doc revisions (if Q-R3.2 surfaces third-order
  contradictions): the maintainer will fan out fixes to
  `tactical_plan_v0_1_x.md`, `agent_state_visibility_findings.md`,
  `AGENTS.md`, and/or `v0_1_17/README.md` as appropriate. Audit
  response should name *which* docs need editing for each
  cross-doc finding.

**No code changes.** No test runs. No state mutations.
