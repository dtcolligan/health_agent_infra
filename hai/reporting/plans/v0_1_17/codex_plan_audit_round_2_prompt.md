# Codex External Audit — v0.1.17 PLAN.md (D14 round 2)

> **Why this round.** D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS
> with **11 findings** (F-PLAN-01 through F-PLAN-11). All 11 AGREED;
> revisions applied 2026-05-04. Per-finding triage in
> `reporting/plans/v0_1_17/codex_plan_audit_response_response.md`.
>
> Round 2 audits whether (a) each round-1 revision actually closes
> its target finding, (b) the revisions introduced no new
> contradictions (the canonical v0.1.11/v0.1.12/v0.1.14/v0.1.15
> pattern at round 2 — round-1 revisions introduce second-order
> issues), and (c) the new structural elements added in round 2
> (W-D arm-2 plumbing helper + corrected formula + 7-item
> acceptance, W-29 expanded 8 → 10 acceptance items including the
> refreshed-boundary-note pre-flight gate + do-not-split abort
> path + handler-dispatch-smoke test, W-AI-2 commit-gate-vs-
> ship-gate split, W-B agent_safe=False user-authored-only
> schema, AGENTS.md provenance-preserving append/clause-removal
> instructions) are themselves coherent.
>
> **D14 is a settled decision** (added at v0.1.11 ship). Substantive
> PLANs settle in 2-4 rounds at the `10 → 5 → 3 → 0` halving
> signature (twice-validated v0.1.11 + v0.1.12; v0.1.14 + v0.1.15
> confirmed at the same shape). v0.1.17 round 1 returned 11 findings
> — within norm. **Round 2 finding count drives the round 3
> decision:** ≤3 findings → close in place at round 2; 4-6
> findings → schedule round 3 with a smaller surface; >6 findings
> → re-read the response_response.md diff and consider whether
> the round-1 revisions over-corrected.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit is
> on the *plan document* — coherence of the round-1 revisions, plus
> a sweep for second-order contradictions across the cross-doc
> fan-out (PLAN + README + tactical §5D + AGENTS.md governance-edit
> instructions).
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
# expect: main (or cycle/v0.1.17 if branched)
git log --oneline -5
# expect: HEAD includes the 2026-05-04 v0.1.16-cancellation +
# v0.1.17 cycle-open commits. The v0.1.15.1 hardening ship should
# appear within the last 10 commits.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# — that commit is the head of the STALE checkout under
# /Users/domcolligan/Documents/health_agent_infra/, months behind
# and must not be audited.
ls reporting/plans/v0_1_17/
# expect: README.md, PLAN.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md (this file),
#         cycle_open_session_prompt.md
```

The discriminator that matters is dual-repo: the stale checkout's
HEAD is `2811669` (months behind). AGENTS.md "Active repo path"
preamble names this constraint durably; v0.1.15 W-PLAN-12 settled
the discrimination. If `pwd` resolves to `/Users/domcolligan/Documents/health_agent_infra/`,
**stop and surface to the maintainer**.

---

## Step 1 — Read the round-2 inputs (in order)

1. **`reporting/plans/v0_1_17/codex_plan_audit_response.md`** — your
   round-1 findings. The verdicts in the per-W-id table + the
   closure recommendation define what round 2 is checking against.
2. **`reporting/plans/v0_1_17/codex_plan_audit_response_response.md`**
   — Claude's per-finding triage. Every finding marked AGREED with
   action taken + line refs. Round 2 audits whether the actions
   actually do what they claim.
3. **`reporting/plans/v0_1_17/PLAN.md`** — the revised artifact.
   Read end-to-end; round-2 surface is small enough that a full
   read is faster than skimming for diffs.
4. **`reporting/plans/v0_1_17/README.md`** — refreshed per F-PLAN-08
   (line 3: precondition retirement; line 13: 9217 → 9927 LOC; line
   24: total scope reaffirmed).
5. **`reporting/plans/tactical_plan_v0_1_x.md` §5D row 703** —
   refreshed per F-PLAN-08 (W-29 row LOC update with provenance
   chain `9217 → 9927, +710 across v0.1.14/v0.1.15/v0.1.15.1`).
6. **`AGENTS.md`** — for F-PLAN-10 verification (the §3 governance-
   edit instructions claim provenance preservation; verify the
   current AGENTS.md text against what §3 quotes).
7. **`src/health_agent_infra/core/intake/presence.py:163-213`** —
   for F-PLAN-01 verification (the "compute_target_status returns
   enum string only, not values" claim that drives W-D arm-2's
   plumbing-path requirement).
8. **`src/health_agent_infra/domains/nutrition/classify.py:355-395`** —
   for F-PLAN-01 verification (the "classifier reads from thresholds
   config, not from target rows" claim that makes the threshold-
   override seam load-bearing).
9. **`src/health_agent_infra/evals/runner.py:71-86, 300-380`** —
   for F-PLAN-02 verification (the existing scoring contract
   `expected.classified` + `expected.policy.forced_action` that
   the revised §2.C + §2.E now align to).
10. **`verification/tests/test_cli_parser_capabilities_regression.py`** —
    for F-PLAN-06 verification (the existing snapshot scope, which
    drives the new dispatch-smoke-test requirement).

Cross-check that everything PLAN.md cites actually exists at the
cited path/line. **Citation drift introduced during round-1 revisions
is the canonical round-2 finding** per AGENTS.md "Patterns the cycles
have validated" + provenance discipline.

---

## Step 2 — The round-2 audit questions

Round 2 has a smaller surface than round 1 — only the revised
sections need re-checking, plus a sweep for cross-doc consistency.
**Out of scope for round 2:** any section not touched by round-1
revisions. PLAN §1.2 catalogue rows + §1.3 Phase 1/2/3 sequencing +
§1.4 source provenance chains were not flagged in round 1 and do
not need re-auditing.

### QR2-1 — F-PLAN-01 close-out (W-D arm-2 plumbing + formula)

§2.I was the largest revision: target-value plumbing path now
specified (new helper `core/target/store.py::get_active_macro_targets`),
formula corrected (`projected_eod_kcal = target_kcal` directly;
round-1's broken `remaining_day_fraction_at_target_pace` retired),
acceptance items expanded 6 → 7.

- **QR2-1.1.** Does the plumbing path actually flow target values
  to the classifier? Trace: `target` row insert (W-C migration 025
  in tree) → `get_active_macro_targets()` helper (new in this WS) →
  `cmd_synthesize` / `cmd_state_snapshot` call site → thresholds
  override → `classify_nutrition_state(...thresholds=overridden)` →
  band evaluation. Does this path actually exercise the existing
  D13 seam without a code path that bypasses it?
- **QR2-1.2.** Is the corrected formula `projected_eod_kcal =
  target_kcal` consistent with the macro projection scope (calories
  + protein + carbs + fat)? Specifically: is hydration honestly
  excluded (no hydration target in W-C 4-row group), or does the
  classifier need a special-case branch for hydration that the PLAN
  hasn't named?
- **QR2-1.3.** Acceptance item 5 (linear-extrapolation reachability)
  asserts a threshold override `{"projection_mode": "linear_extrapolation"}`.
  Is this naming consistent with how D13 thresholds are structured
  in the existing `core/config.py`? Does the override actually
  reach the classifier's projection branch, or is "projection_mode"
  a hand-wave?
- **QR2-1.4.** Does §2.I retain any vestigial round-1 wording?
  Specifically: search for `remaining_day_fraction` or
  `remaining_day_fraction_at_target_pace` strings — both should be
  retired except in the historical reference paragraph.

### QR2-2 — F-PLAN-02/03 close-out (scenario-runner harness alignment)

§2.C + §2.E rewritten to use `expected.classified` + `expected.policy.forced_action`
+ singular `tag` field. §2.C item 5 replaced with eval-corpus gate.

- **QR2-2.1.** Does the revised §2.C + §2.E actually align to the
  existing harness contract at `evals/runner.py:71-86, 300-380`?
  Spot-check the field names verbatim.
- **QR2-2.2.** Are there any remaining round-1 references to
  `expected_*_token`, `expected_escalate_token`, or `tags[]` in
  PLAN.md that should have been retired? Grep.
- **QR2-2.3.** §2.C item 5's eval-corpus gate (`hai eval run
  --scenario-set all` ≥95% pass-rate). Is 95% load-bearing or
  arbitrary? What's the v0.1.14 baseline? If the v0.1.14 baseline
  was already <95%, the gate fails on day 1 of v0.1.17 implementation
  for reasons unrelated to W-AH-2.
- **QR2-2.4.** §6 ship gates added an eval-corpus gate alongside
  the persona-matrix gate. Is this consistent with §4 risk 7's
  rewritten "eval-corpus runtime expansion" framing?

### QR2-3 — F-PLAN-04 close-out (W-AI-2 commit-gate vs ship-gate split)

§2.D acceptance now split into commit-gate (dynamic over at-commit
corpus) + ship-gate (verifies post-W-AH-2/W-AM-2 visibility).

- **QR2-3.1.** Does the commit-gate test logic actually work without
  knowing whether W-AH-2 or W-AM-2 has committed yet? Specifically:
  if W-AI-2 commits first, the commit-gate test runs against 31
  judge_adversarial fixtures only; if W-AI-2 commits last, it runs
  against 132+ + 6 + 31. Does the test infrastructure handle both?
- **QR2-3.2.** Is the ship-gate ratification at end-of-cycle clearly
  separated from the commit-gate, or do they overlap in §6 ship-
  gates wording?

### QR2-4 — F-PLAN-05/06 close-out (W-29 acceptance expanded 8 → 10)

New items: refreshed-boundary-note (item 1), do-not-split abort
(item 2), handler-dispatch-smoke (extension to item 5).

- **QR2-4.1.** Item 1 names a new artifact at
  `reporting/plans/v0_1_17/w29_boundary_refresh.md`. Does the
  acceptance item specify enough about that artifact for the
  Phase 1 implementer to actually produce it? Or is "refreshed
  boundary note" still vague?
- **QR2-4.2.** Item 2 (do-not-split abort path) specifies cycle-
  halt + PLAN re-shape OR convert-to-fork-deferred. Are both
  branches operational? Specifically: who authors the
  fork-deferred destination W-29-3 catalogue row in v0.1.18+
  if the cycle proceeds without W-29?
- **QR2-4.3.** Item 5's handler-dispatch-smoke test (`test_cli_handler_dispatch_smoke.py`).
  Does "one non-default flag per moved handler group" specify
  enough to write the test? Should the PLAN name which flag for
  each group, or is it implementer's choice?
- **QR2-4.4.** §4 risk 1 rewritten with three abort branches (a/b/c).
  Are they internally consistent with §2.A acceptance items 1 + 2?

### QR2-5 — F-PLAN-07 close-out (snapshot regeneration lockstep)

§3 + §6 reconciled: each intentional CLI-surface commit regenerates
snapshots in the same commit. W-29 byte-stability is the pre-add
comparison.

- **QR2-5.1.** Is the per-W-id snapshot regeneration cadence
  consistent across §2.D (W-AI-2), §2.G (F-PV14-02), §2.H (W-B)?
  Each WS should mention the snapshot update in its acceptance
  or files-of-record.
- **QR2-5.2.** §6 says "final cycle state: snapshot matches the
  post-W-29 + post-Phase-2/3-additions cli.py exactly." If a
  Phase 2/3 commit lands without its co-committed snapshot
  regeneration (implementer error), the test gate is red until
  the next commit. Is this acceptable, or should the PLAN
  mandate a pre-commit check?

### QR2-6 — F-PLAN-08 close-out (source-doc refresh)

README + tactical §5D updated.

- **QR2-6.1.** README.md line 3 now says v0.1.16 cancelled,
  precondition retired. Verify against `v0_1_16/README.md` —
  cancellation note matches.
- **QR2-6.2.** README.md line 13 now cites 9927 LOC. Verify by
  `wc -l src/health_agent_infra/cli.py`.
- **QR2-6.3.** Tactical §5D row 703 cites "9927 LOC at v0.1.17
  cycle-open HEAD `df6a13c`; was 9217 LOC at v0.1.13 W-29-prep
  — +710 LOC across v0.1.13/v0.1.14/v0.1.15/v0.1.15.1 surface
  adds." **Verify:** is 9217 the correct v0.1.13 W-29-prep number?
  PLAN §2.A uses 8891 (the v0.1.13 cycle-open number per the
  boundary-table doc). Tactical uses 9217 (the v0.1.13-ship /
  v0.1.14-cycle-open number per v0.1.14 RELEASE_PROOF). Both
  citations are internally consistent against their stated
  baselines, but **does the PLAN explain the dual-baseline
  difference**, or does it look like a contradiction?

### QR2-7 — F-PLAN-09 close-out (W-B agent_safe=False)

§2.H schema simplified: `source` enum is single-valued
(`'user_authored'`); `agent_safe=False` in manifest.

- **QR2-7.1.** Does the simplified `source` enum still need a
  CHECK constraint, or is the column-default sufficient? PLAN
  §2.H schema includes `CHECK(source = 'user_authored')` — is
  this load-bearing or belt-and-braces?
- **QR2-7.2.** §2.H acceptance item 2 asserts `source='user_authored'`
  regardless of `--ingest-actor` value. Does this match the
  schema (always sets `source='user_authored'` at insert)?
  What happens if a future cycle extends the source enum — does
  the CHECK constraint need a migration?
- **QR2-7.3.** "What this WS does NOT do" gains an "agent-proposal
  path" entry. Is the wording explicit enough that a future
  v0.2.x cycle author wouldn't accidentally extend the enum
  without re-opening the W57 question?

### QR2-8 — F-PLAN-10 close-out (AGENTS.md provenance preservation)

§3 governance-edit bullets rewritten with explicit "append" /
"clause-removal" instructions.

- **QR2-8.1.** Does the proposed AGENTS.md "Settled Decisions"
  edit (append `W-29 closed at v0.1.17 ...` to the existing entry)
  actually preserve the multi-cycle redestination chain? Verify
  by reading the current AGENTS.md entry text and checking that
  the proposed append doesn't replace any existing wording.
- **QR2-8.2.** Does the "Do Not Do" clause-removal preserve the
  W-30 freeze provenance tail? Verify the current AGENTS.md text
  + check that §3's proposed replacement-lead-sentence drops
  ONLY the cli.py clause, not the trailing provenance.
- **QR2-8.3.** Are the §3 instructions specific enough for the
  ship-time editor to execute correctly, or are they still
  ambiguous about which sentences/lines to touch?

### QR2-9 — F-PLAN-11 close-out (D15 tier sentence)

PLAN line 3 rewritten.

- **QR2-9.1.** Does the new tier sentence accurately quote AGENTS.md
  D15? Verify the verbatim text "≥1 release-blocker workstream"
  and "≥10 days estimated."
- **QR2-9.2.** Is the residual "Round-1 PLAN claimed ... F-PLAN-11
  corrected; state-model is not a D15 tier trigger" sentence
  helpful audit-trail wording or distracting?

### QR2-10 — Second-order contradictions (the canonical round-2 finding)

Sweep PLAN.md for second-order issues introduced by round-1
revisions:

- **QR2-10.1. OQ list shrink (8 → 4).** §8 now lists 4 OQs (OQ-1,
  OQ-5, OQ-6, OQ-8) and a "closed at round 1" prefix. Are any of
  the closed OQs referenced elsewhere in PLAN.md as if still
  open?
- **QR2-10.2. Acceptance-item renumber sweep.** §2.A expanded
  8 → 10; §2.I expanded 6 → 7. Are §4 risks or §6 ship gates
  citing old item numbers? E.g., §4 risk 8 used to say
  "acceptance items 6-8 catch import-shape" — is that still
  pointing at the right items post-renumber? (PLAN §4 risk 8
  was already updated; verify it matches the new W-29 item
  numbering.)
- **QR2-10.3. F-PLAN-08 dual-baseline LOC narrative.** PLAN §2.A
  uses 8891 baseline; tactical uses 9217 baseline. Is one of
  them stale, or are both correctly attributed? See QR2-6.3.
- **QR2-10.4. §9 provenance entry.** The 2026-05-04 round-1
  close entry is long and lists every F-PLAN-NN. Is there
  anything in the prose that contradicts what's in §1.4 chains
  A/B/C or §3 governance edits?
- **QR2-10.5. F-PLAN-02 fan-out.** §2.C + §2.E both touch
  the fixture contract. Is the wording consistent across both
  (singular `tag` field, no `tags[]`, no `expected_*_token`
  field)?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_17/codex_plan_audit_round_2_response.md`
matching the existing convention:

```markdown
# Codex Plan Audit Response — v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT (state which workstreams need rework)

**Round:** 2

## Round-1 closure verdicts (per F-PLAN-NN)

| Round-1 finding | Round-2 verdict | Note |
|---|---|---|
| F-PLAN-01 (W-D arm-2 plumbing+formula) | CLOSED / CLOSED_WITH_RESIDUAL / NOT_CLOSED | ... |
| F-PLAN-02 (scenario contract) | ... | ... |
| F-PLAN-03 (persona vs eval-corpus gate) | ... | ... |
| F-PLAN-04 (W-AI-2 sequencing) | ... | ... |
| F-PLAN-05 (W-29 pre-flight gate) | ... | ... |
| F-PLAN-06 (W-29 dest coverage) | ... | ... |
| F-PLAN-07 (snapshot lockstep) | ... | ... |
| F-PLAN-08 (source-doc refresh) | ... | ... |
| F-PLAN-09 (W-B agent_safe) | ... | ... |
| F-PLAN-10 (AGENTS.md provenance) | ... | ... |
| F-PLAN-11 (D15 tier sentence) | ... | ... |

## Round-2 findings (new — second-order)

### F-PLAN-R2-01. <short title>

**Q-bucket:** QR2-N
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-R2-02. ...

## Open-question dispositions

(For OQ-1, OQ-5, OQ-6, OQ-8 — agree with revised provisional?
Suggest alternative? Or is the default still wrong-shaped after
the round-1 revisions?)

## Closure recommendation

(Verdict + named must-fix revisions list + recommended round 3
budget. Empirical signature: ≤3 findings → close in place at
round 2; 4-6 → round 3 with smaller surface; >6 → re-read the
response_response diff and consider whether revisions over-
corrected.)
```

Each finding must be triageable. "PLAN.md §2.I cites a `target`
table column but the column doesn't exist" is a finding. "PLAN
seems verbose" is not.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit.

---

## Step 5 — Out of scope

Round 2 explicitly does **not** re-audit:

- PLAN §1.2 catalogue rows (not flagged at round 1).
- PLAN §1.3 Phase 1/2/3 sequencing structure (not flagged at round 1).
- PLAN §1.4 source provenance chains A/B/C (not flagged at round 1).
- PLAN §2.B (W-30), §2.F (W-Vb-4), §2.G (F-PV14-02), §2.J (W-C-EQP) —
  PASS verdicts at round 1.
- v0.1.18 / v0.1.19 / v0.2.0 scope — out-of-cycle per PLAN §7.
- Strategic + tactical + eval + success + risks docs beyond the
  closure-side §3 deltas + the F-PLAN-08 source-doc refresh.
- AGENTS.md "Active repo path" preamble (settled v0.1.15 W-PLAN-12).

If round 2 surfaces a finding in an out-of-scope section, that is
itself notable — note it as a finding, but flag that round 1 missed
it (which means round 1's surface coverage was incomplete).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14 round 1] CLOSED 2026-05-04 PLAN_COHERENT_WITH_REVISIONS
  [D14 round 2] ← you are here
  Maintainer + Claude response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs; v0.1.17 expectation 2-3)

Phase 0 (D11):
  ...
```

Estimated review duration: 1 session.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_17/codex_plan_audit_round_2_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_17/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_17/codex_plan_audit_round_3_prompt.md`
  (only if round 2 returns >3 findings).

**No code changes.** No test runs. No state mutations. No
implementation against the PLAN.
