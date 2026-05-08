# Codex External Audit — v0.1.17 PLAN.md (D14 round 3)

> **Why this round.** D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS
> with 11 findings (all AGREED + applied 2026-05-04). D14 round 2
> closed PLAN_COHERENT_WITH_REVISIONS with **5 findings**
> (F-PLAN-R2-01..05; halving signature **11 → 5** matches AGENTS.md
> empirical norm). All 5 round-2 findings AGREED; revisions applied
> 2026-05-04. Round-2 triage in
> `reporting/plans/v0_1_17/codex_plan_audit_round_2_response_response.md`.
>
> **Round 3 is narrow** per Codex round-2 closure recommendation
> (0.5 session budget). Audit only:
> 1. The 5 F-PLAN-R2-NN closures (whether each round-2 revision
>    actually does what it claims).
> 2. A quick stale-status / citation sweep across PLAN + tactical
>    + README (third-order drift introduced by round-2 edits).
>
> **D14 is a settled decision** (added at v0.1.11 ship). Substantive
> PLANs settle in 2-4 rounds at the `10 → 5 → 3 → 0` halving
> signature. v0.1.17 is on track:
> - Round 1: 11 findings (norm 10-12). ✓
> - Round 2: 5 findings (norm 5-6). ✓
> - **Round 3 prediction: 2-3 findings** (close-in-place if ≤3;
>   schedule round 4 if >3 with smaller surface).
> - **Round 4 prediction: 0 findings → PLAN_COHERENT.**
>
> If round 3 returns >3 findings, the round-2 revisions over-
> corrected; re-read the round-2 response_response diff.
>
> **Cycle position.** Pre-PLAN-open. Phase 0 (D11) bug-hunt has
> not started. No code has changed against this PLAN. The audit
> remains on the *plan document* — third-order coherence after
> round-2 revisions, plus a stale-status sweep.
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
# v0.1.17 cycle-open commits.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# (stale checkout under /Users/domcolligan/Documents/health_agent_infra/).
ls reporting/plans/v0_1_17/
# expect: README.md, PLAN.md, codex_plan_audit_prompt.md,
#         codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md,
#         codex_plan_audit_round_2_response_response.md,
#         codex_plan_audit_round_3_prompt.md (this file),
#         cycle_open_session_prompt.md
```

If any don't match, **stop and surface to the maintainer**. AGENTS.md
"Active repo path" preamble is durable for the dual-repo hazard.

---

## Step 1 — Read the round-3 inputs (in order)

Round-3 read surface is small — only what's needed to verify the 5
F-PLAN-R2-NN closures + sweep cross-doc consistency.

1. **`reporting/plans/v0_1_17/codex_plan_audit_round_2_response.md`**
   — your round-2 findings + closure recommendation. The 5 F-PLAN-R2-NN
   define what round 3 is checking against.
2. **`reporting/plans/v0_1_17/codex_plan_audit_round_2_response_response.md`**
   — Claude's per-finding triage. Every finding marked AGREED with
   action taken + line refs. Round 3 audits whether the actions
   actually do what they claim.
3. **`reporting/plans/v0_1_17/PLAN.md`** — the revised artifact.
   Read **only** §2.A (lines 100-160 for items 1-3 + pre-flight
   prose), §2.C (line 192 — eval-corpus gate), §2.D (lines 231-235
   for item 7 snapshot lockstep), §2.G (line 319 for item 5
   expansion), §2.H (line 379 for item 7 snapshot lockstep), §2.I
   (lines 388-450 — the largest revision; full read), §3 (lines
   479-490), §4 risk 1 (line 495 — single-halt branch), §6 (lines
   555-585 — eval-corpus gate + per-WS gates), §8 (lines 630-650
   — OQ list), §9 (lines 654-665 — round-2 close entry).
4. **`reporting/plans/v0_1_17/README.md`** — refreshed at round 1
   per F-PLAN-08; verify nothing in the round-2 edits drifted it.
5. **`reporting/plans/tactical_plan_v0_1_x.md`** — §5D row 703 +
   line 49 top-row updated at round 2 per F-PLAN-R2-05; verify.
6. **Source-code spot-checks** for F-PLAN-R2-01:
   - `src/health_agent_infra/core/state/snapshot.py` — line ~895-909
     (the `classify_nutrition_state` call site PLAN §2.I now names).
   - `src/health_agent_infra/domains/nutrition/classify.py:309-330` —
     threshold seam (`t = thresholds if thresholds is not None else
     load_thresholds()`).
   - `src/health_agent_infra/core/config.py:321-360` —
     `DEFAULT_THRESHOLDS["classify"]["nutrition"]` shape (PLAN now
     names `projection_mode = "target_anchored"` as a new default
     leaf).
7. **Source-code spot-checks** for F-PLAN-R2-02:
   - `src/health_agent_infra/evals/cli.py:68-97, 141-158` —
     `cmd_eval_run` exit-code contract (`failed == 0` returns OK).

Cross-check that everything PLAN.md cites at `core/state/snapshot.py`,
`core/config.py`, and `evals/cli.py` actually exists. **Citation
drift introduced during round-2 revisions is the canonical round-3
finding**.

---

## Step 2 — The round-3 audit questions

Round 3 has the smallest surface yet. Five F-PLAN-R2 closures + one
sweep. **Out of scope:** every CLOSED round-1 finding (F-PLAN-02,
F-PLAN-04, F-PLAN-06, F-PLAN-09, F-PLAN-10, F-PLAN-11), every
section not touched by round-1 or round-2 revisions.

### QR3-1 — F-PLAN-R2-01 close-out (W-D arm-2 plumbing, deeper)

§2.I rewritten at round 2: production call site corrected to
`core/state/snapshot.py`; `cmd_state_snapshot` reattributed from
`recommend.py` to `state.py`; threshold-merge specified as
`build_snapshot()` internal step; `DEFAULT_THRESHOLDS` extension
named (`projection_mode = "target_anchored"`); acceptance item 5
rewritten to use a deep-merged full thresholds tree.

- **QR3-1.1.** Does §2.I's "internal merge inside `build_snapshot()`"
  shape actually flow target values to the classifier without a
  public API change to `build_snapshot()`? Trace the read path:
  presence-block computation (already in tree at `:897-902`) → arm-2
  condition check → `get_active_macro_targets()` call → deep-merge
  into `load_thresholds()` tree → `classify_nutrition_state(thresholds=merged_tree)`
  call. Is the merge step at the right line range, or does §2.I
  hand-wave the merge location?
- **QR3-1.2.** PLAN §2.I claims `DEFAULT_THRESHOLDS["classify"]["nutrition"]`
  gains a new `projection_mode = "target_anchored"` leaf. Verify
  the classifier code path consuming this leaf — does
  `domains/nutrition/classify.py` need a new branch reading
  `t["classify"]["nutrition"]["projection_mode"]`, or is the
  projection-mode dispatch contained inside `build_snapshot()`'s
  merge step? PLAN §2.I "Files of record" lists both — verify the
  split is honest.
- **QR3-1.3.** Acceptance item 5 (linear-extrapolation reachability)
  now passes a deep-merged full thresholds tree via `load_thresholds()`
  + an override of `projection_mode`. Does this actually exercise
  the classifier's projection-mode branch, or does the merge happen
  earlier (in `build_snapshot()`) and bypass the test override?
  If the merge is in `build_snapshot()` but the test calls
  `classify_nutrition_state` directly (per item 5's "Pass... to
  `classify_nutrition_state`"), what triggers the projection branch
  inside `classify_nutrition_state`?
- **QR3-1.4.** PLAN §2.I says carbs/fat are emitted as "informational
  fields" (no band classification). Acceptance item 2 asserts
  `projected_eod_carbs_g=350` + `projected_eod_fat_g=90` get emitted.
  Where in the classified-state shape do these fields live? PLAN
  doesn't name the field path inside `ClassifiedNutritionState`. Is
  this fixable at implementation time, or does PLAN need to specify?
- **QR3-1.5.** Hydration: PLAN says it's held observed (no hydration
  target in W-C 4-row group). But `DEFAULT_THRESHOLDS["classify"]["nutrition"]["targets"]`
  has `hydration_target_l = 2.5` (defaults). When the merge step
  runs, does it **replace** the entire `targets` block (deleting
  hydration), or **merge into** it (preserving hydration default +
  injecting carbs/fat)? PLAN §2.I doesn't specify deep-merge vs
  replace — implementer ambiguity.

### QR3-2 — F-PLAN-R2-02 close-out (eval-corpus gate 100%)

§2.C item 5 + §6 ship gates tightened from ≥95% to 100% pass.

- **QR3-2.1.** Does the 100% gate match the existing `cmd_eval_run`
  contract (`failed == 0` returns OK)? Verify by reading
  `evals/cli.py:68-97, 141-158`.
- **QR3-2.2.** PLAN cites "v0.1.14 baseline: 35-fixture corpus
  passed at 100% at v0.1.14 ship." Is that verifiable from
  `reporting/plans/v0_1_14/RELEASE_PROOF.md` or the v0.1.14 IR
  response? Or is it just an assumption?
- **QR3-2.3.** Per-fixture validation discipline (acceptance item
  2 — fixtures that fail are dropped + logged). Is the 100% gate
  consistent with that discipline, or is there a gap where a
  partially-validated fixture sneaks past?

### QR3-3 — F-PLAN-R2-03 close-out (W-29 single-halt branch)

§2.A acceptance item 2 collapsed to a single halt-and-re-author
branch. §4 risk 1 (a) reduced to "halts the cycle" only.

- **QR3-3.1.** Does §2.A item 2's halt branch enumerate every
  downstream surface that needs reconsideration? Specifically:
  W-29 release-blocker status, §3 governance edits, §6 W-29 gates,
  §7 v0.1.18 dependency, README, tactical §5D + §5E rows, W-29-3
  destination. Is there anything missing?
- **QR3-3.2.** §4 risk 1 was rewritten to drop the round-1
  fork-defer branch. Are there other §4 entries that still
  reference the retired branch? Check risks 2-11 quickly.
- **QR3-3.3.** §7 (out-of-scope) names v0.1.18 dependency. Does
  the wording anticipate the halt branch firing, or does it
  silently assume W-29 closes?

### QR3-4 — F-PLAN-R2-04 close-out (per-WS snapshot lockstep)

§2.D item 7 (W-AI-2), §2.G item 5 expansion (F-PV14-02), §2.H
item 7 (W-B) all gain a snapshot-regeneration acceptance item.

- **QR3-4.1.** Are the three new acceptance items consistent in
  wording — JSON manifest snapshot + parser-tree snapshot +
  markdown contract regeneration in the same commit?
- **QR3-4.2.** Does §6 ship-gate wording about per-W-id snapshot
  regeneration match the per-WS acceptance items, or is there a
  contradiction?
- **QR3-4.3.** F-PV14-02 §2.G item 5 was originally markdown-only;
  expanded at round 2 to all three. Is the "JSON + parser-tree"
  expansion consistent with the rule that the regeneration
  happens in the same commit (not at end of cycle)?

### QR3-5 — F-PLAN-R2-05 close-out (LOC baseline correction)

Tactical §5D row 703 + line 49 top-row updated; PLAN §2.A
pre-flight gains a dual-baseline note.

- **QR3-5.1.** Does the tactical §5D row 703 wording correctly
  attribute 9217 to "v0.1.14 RELEASE_PROOF deferred-W-29
  baseline" (not v0.1.13 W-29-prep)? Verify.
- **QR3-5.2.** Does tactical line 49 (top cycle row) say "9927-line"
  now? Verify.
- **QR3-5.3.** Does PLAN §2.A's dual-baseline note explicitly cite
  both source docs (`cli_boundary_table.md:55` for 8891 and
  `v0_1_14/RELEASE_PROOF.md:25` for 9217)? Are the citations
  verbatim and on disk?

### QR3-6 — Stale-status / citation sweep (the canonical round-3 finding)

Sweep PLAN + tactical + README for third-order drift introduced
by the round-2 revisions:

- **QR3-6.1. §9 provenance entry.** The 2026-05-04 round-2 close
  entry is long. Are the F-PLAN-R2-NN labels + closure verdicts
  consistent with what `codex_plan_audit_round_2_response.md`
  actually said? (E.g., the response_response had a counting bug
  about CLOSED-vs-CLOSED_WITH_RESIDUAL — verify §9 has the
  corrected count: 6 CLOSED + 5 CLOSED_WITH_RESIDUAL.)
- **QR3-6.2. Acceptance-item renumbering.** §2.I expanded 7 → 7
  but item 5 was rewritten end-to-end. §2.D commit-gate expanded
  6 → 7 (added item 7 snapshot lockstep). §2.H expanded 6 → 7
  (added item 7). Are §6 ship gates referring to old item numbers?
- **QR3-6.3. §8 OQ list.** Round-2 left OQ-1, OQ-5, OQ-6, OQ-8
  open. Did round-2 PLAN edits actually update the OQ-1 / OQ-5 /
  OQ-6 / OQ-8 prose in §8 to reflect the round-2 corrections? Or
  is the §8 prose still describing the round-1 provisional state?
- **QR3-6.4. §9 round number consistency.** §9 says "this round-3
  edit pass" but the section header still says "Open questions
  for D14 round 3" — verify the round numbers reconcile across
  the doc.
- **QR3-6.5. Tier sentence audit-trail.** PLAN line 3 has a
  closing sentence "Round-1 PLAN claimed ... F-PLAN-11 corrected".
  Is similar audit-trail text added or needed for the round-2
  corrections (F-PLAN-R2-01..05)?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_17/codex_plan_audit_round_3_response.md`
matching the existing convention:

```markdown
# Codex Plan Audit Response — v0.1.17 PLAN.md

**Verdict:** PLAN_COHERENT | PLAN_COHERENT_WITH_REVISIONS |
PLAN_INCOHERENT

**Round:** 3

## Round-2 closure verdicts (per F-PLAN-R2-NN)

| Round-2 finding | Round-3 verdict | Note |
|---|---|---|
| F-PLAN-R2-01 (W-D arm-2 plumbing) | CLOSED / CLOSED_WITH_RESIDUAL / NOT_CLOSED | ... |
| F-PLAN-R2-02 (eval-corpus gate 100%) | ... | ... |
| F-PLAN-R2-03 (W-29 single-halt branch) | ... | ... |
| F-PLAN-R2-04 (per-WS snapshot lockstep) | ... | ... |
| F-PLAN-R2-05 (LOC baseline) | ... | ... |

## Round-3 findings (new — third-order)

### F-PLAN-R3-01. <short title>

**Q-bucket:** QR3-N
**Severity:** plan-incoherence | sizing-mistake | dependency-error |
acceptance-criterion-weak | hidden-coupling | settled-decision-conflict |
absence | provenance-gap | nit
**Reference:** PLAN.md § X.Y, line N
**Argument:** <why this is a finding, with citations>
**Recommended response:** <revise PLAN.md as follows / accept and
note as known limitation / disagree with reason>

### F-PLAN-R3-02. ...

## Open-question dispositions (round 3)

(For OQ-1, OQ-5, OQ-6, OQ-8 — agree with the resolved-shape revisions
from round 2, or do they still need re-shaping? OQ-5/6/8 are expected
to close at round 3.)

## Closure recommendation

(Verdict + named must-fix revisions list. Empirical signature: ≤3
findings → close in place at round 3 (PLAN_COHERENT or
PLAN_COHERENT_WITH_REVISIONS close-in-place); 4-6 findings →
schedule round 4 with smaller surface; >6 findings → re-read the
round-2 response_response diff and consider whether revisions
over-corrected.)
```

Each finding must be triageable. "PLAN.md §2.I item 2 cites
`build_snapshot(conn, as_of_date=today, user_id=...)` but
`build_snapshot()` signature at `core/state/snapshot.py:372` takes
positional args" is a finding. "PLAN seems verbose" is not.

---

## Step 4 — Verdict scale

- **PLAN_COHERENT** — open the cycle as written.
- **PLAN_COHERENT_WITH_REVISIONS** — open the cycle after named
  revisions land. Revisions list every must-fix finding.
- **PLAN_INCOHERENT** — do not open. Re-author the named sections
  before re-running this audit. (Unlikely at round 3; would
  indicate round-2 over-correction.)

**Close-in-place option:** if revisions are nit-class (single-line
edits, no new test surface, no new acceptance items), the verdict
is PLAN_COHERENT_WITH_REVISIONS but the recommendation is "apply
+ close at this round, no round 4 needed."

---

## Step 5 — Out of scope

Round 3 explicitly does **not** re-audit:

- Any round-1 finding marked CLOSED at round 2 (F-PLAN-02 / -04 /
  -06 / -09 / -10 / -11). Settled.
- PLAN §1.1, §1.2 catalogue, §1.3 sequencing, §1.4 source
  provenance — never flagged.
- PLAN §2.B (W-30), §2.F (W-Vb-4), §2.J (W-C-EQP) — PASS
  verdicts at round 1.
- v0.1.18 / v0.1.19 / v0.2.0 scope — out-of-cycle per PLAN §7.
- Strategic + eval + success + risks docs.
- AGENTS.md "Active repo path" preamble.

If round 3 surfaces a finding in an out-of-scope section, that's
itself notable — note it as a finding, but flag that rounds 1 + 2
both missed it (which means the cumulative surface coverage was
incomplete).

---

## Step 6 — Cycle pattern (this audit's place)

```
Pre-PLAN-open:
  [D14 round 1] CLOSED 2026-05-04 PLAN_COHERENT_WITH_REVISIONS (11)
  [D14 round 2] CLOSED 2026-05-04 PLAN_COHERENT_WITH_REVISIONS (5)
  [D14 round 3] ← you are here (predicted 2-3 findings)
  Maintainer + Claude response to plan audit
  PLAN.md revised if warranted
  (loop until PLAN_COHERENT — empirical 2-4 rounds for
   substantive PLANs; v0.1.17 expectation 3-4)

Phase 0 (D11):
  ...
```

Estimated review duration: 0.5 session.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_17/codex_plan_audit_round_3_response.md` (new) —
  your findings.
- `reporting/plans/v0_1_17/PLAN.md` (revisions, if warranted) —
  maintainer + Claude apply revisions in response.
- `reporting/plans/v0_1_17/codex_plan_audit_round_4_prompt.md`
  (only if round 3 returns >3 findings).

**No code changes.** No test runs. No state mutations. No
implementation against the PLAN.
