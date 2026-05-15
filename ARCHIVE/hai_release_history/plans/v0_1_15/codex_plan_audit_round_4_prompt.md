# Codex External Audit — v0.1.15 PLAN.md (D14 round 4)

> **Why this round.** D14 round 1 closed PLAN_COHERENT_WITH_REVISIONS
> with 12 findings; round 2 with 7; round 3 with 3 nit-class findings
> closed in-place. Halving signature held end-to-end (12 → 7 → 3),
> recommended close-in-place at round 3.
>
> **Phase 0 (D11) bug-hunt then ran on 2026-05-03 evening** —
> internal sweep + audit-chain probe + persona matrix (13/13
> personas, 0 findings, 0 crashes). Phase 0 surfaced **one
> revises-scope finding (F-PHASE0-01)** plus three nit-class
> findings. The maintainer chose F-PHASE0-01 **Option A** and the
> Phase-0-revision was applied to PLAN.md the same evening.
>
> Per AGENTS.md D11 + D14 patterns, a revises-scope Phase 0 finding
> requires PLAN revision + a fresh D14 round before Phase 1 opens.
> Round 4 is that ratification round. The revision surface is small
> — 5 PLAN sections + 3 cross-doc fan-out targets — and the
> maintainer's expectation is a single-round PLAN_COHERENT close
> (or 1-2 nit-class findings closeable in-place).
>
> **F-PHASE0-01 in one sentence.** The original §2.D W-C contract
> proposed a NEW `nutrition_target` table; the Phase 0 internal
> sweep showed the existing `target` table (migration 020, in tree
> since v0.1.8 W50, already W57-gated, already in production use
> for the maintainer's nutrition rows) is the cleaner home. Option
> A: extend `target_type` CHECK with `'carbs_g'` + `'fat_g'`
> (migration 024); ship `hai target nutrition` as a 4-atomic-row
> convenience over the existing table; W-A reads the existing table
> not a new one; pre-W-C parallelization escape hatch removed.
> Effort delta: −1d on W-C; total 16-25 → 15-24 days.
>
> **Round 4 audits whether** (a) the F-PHASE0-01 Option A revision
> is internally coherent (§2.B query reads the existing table; §2.E
> acceptance test 4 was correctly narrowed; §4 risks correctly
> collapsed; §5 effort table correctly delta'd; OQ-7 redefinition
> correctly tracks the new `unavailable` semantics); (b) the
> cross-doc fan-out caught everything (README.md status; tactical
> §5B effort + main release-table row; agent_state_visibility_findings.md
> SUPERSEDED header for F-AV-03); (c) the three nit fixes
> (F-PHASE0-02 / F-PHASE0-03 / F-PHASE0-04) landed correctly; (d)
> no second-order contradictions surfaced (e.g., did anything in
> §1.2 / §1.3 / §1.4 / §3 / §8 / §9 keep a stale reference to the
> "new `nutrition_target` table" framing); (e) OQ-10 is well-formed
> (per-row vs commit-group W57 default); (f) the PLAN is shippable
> as-written for Phase 1 implementation open.
>
> **D14 is a settled decision** (added at v0.1.11 ship). Substantive
> PLANs settle in 2-4 rounds at the `12 → 7 → 3 → ?` halving
> signature; round 4 is unusual because it is post-Phase-0, not
> pre-Phase-0 (the round-1/2/3 chain closed pre-Phase-0; round 4
> audits the Phase-0-revision specifically). If round 4 surfaces
> > 3 findings or any plan-incoherence severity, signal that the
> revision surface is wider than expected and a round 5 may be
> needed. If ≤ 2 nits, recommend close in-place.
>
> **Cycle position.** Pre-Phase-1-implementation. No code has changed
> against the round-4 PLAN. The audit is on the *plan document* —
> coherence of the F-PHASE0-01 Option A revision, verification that
> the OQ-10 default is sound, and a final cross-doc sweep before
> implementation opens.
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
# expect: main (or chore/<scope> if cycle-work branch is in use)
git log --oneline -5
# expect: HEAD is the round-4 revision commit (containing PLAN §2.B/§2.D/§2.E/§4/§5
# updates + audit_findings.md + pre_implementation_gate_decision.md +
# codex_plan_audit_round_4_prompt.md authoring); within the last 5 commits the
# v0.1.15 D14 close commit (38d4cb3) and the cycle-open prompt commit (0bd534e)
# should both appear.
# REJECT if HEAD is "2811669 Phase H: implement conversational intake"
# — that commit is the head of the STALE checkout under
# /Users/domcolligan/Documents/health_agent_infra/, which is months
# behind and must not be audited.
ls reporting/plans/v0_1_15/
# expect: PLAN.md, README.md, audit_findings.md,
#         pre_implementation_gate_decision.md, cycle_open_session_prompt.md,
#         codex_plan_audit_prompt.md, codex_plan_audit_response.md,
#         codex_plan_audit_response_response.md,
#         codex_plan_audit_round_2_prompt.md,
#         codex_plan_audit_round_2_response.md,
#         codex_plan_audit_round_2_response_response.md,
#         codex_plan_audit_round_3_prompt.md,
#         codex_plan_audit_round_3_response.md,
#         codex_plan_audit_round_3_response_response.md,
#         codex_plan_audit_round_4_prompt.md (this file)
```

The dual-repo discriminator: the stale checkout's HEAD is `2811669`
and is months behind. The active repo's HEAD is post-v0.1.14.1 and
ahead by many cycles. If HEAD is `2811669`, **stop and surface the
discrepancy**. AGENTS.md "Authoritative orientation" preamble (added
per round-1 F-PLAN-12, citation fixed per round-2 F-PLAN-R2-03)
declares the active path durably.

**Ignore any tree under `/Users/domcolligan/Documents/`** — same
stale-checkout note as rounds 1 + 2 + 3.

---

## Step 1 — Read the orientation artifacts

Round-4 reading is **narrower than rounds 1-3** because the
revision surface is bounded. Read in order:

1. **`reporting/plans/v0_1_15/audit_findings.md`** — full Phase 0
   finding catalog. **§1 F-PHASE0-01 is the centerpiece**; §6 records
   the maintainer's Option A choice + the disposition table for all
   4 findings. This is the source of round-4's audit surface.

2. **`reporting/plans/v0_1_15/pre_implementation_gate_decision.md`** —
   gate-decision record showing why the cycle held + how it conditionally
   opened post-revision. §6 ratifies F-PHASE0-01 Option A as the maintainer
   choice.

3. **`reporting/plans/v0_1_15/PLAN.md`** — the round-4 PLAN. The
   round-4-revised sections are explicitly tagged in the section
   bodies; read these closely:
   - **Header status block** (top): "D14 round 4 ready" + revised
     effort/scope.
   - **§1.2 catalogue** — W-C row updated.
   - **§1.3 sequencing** — W-C bullet updated.
   - **§1.4 disposition table** — W-C row reason text updated.
   - **§2.A** — F-PHASE0-02 (cli.py:3041-3049 → cmd_state_reproject
     citation correction) + F-PHASE0-03 (`_norm` path-shorthand fix)
     applied.
   - **§2.B W-A** — query rewritten to read existing `target` table;
     pre-W-C parallelization escape hatch removed; `target_status`
     enum semantics narrowed.
   - **§2.D W-C** — full rewrite. Extends existing `target` table
     (migration 024 CHECK extension); 4-atomic-row convenience
     handler; 6 acceptance tests; OQ-10 raised.
   - **§2.E W-D arm-1** — acceptance test 4 narrowed; `unavailable`
     redefined.
   - **§3 cross-cutting** — `state_model_v1.md` reference updated.
   - **§4 risks 1 + 2** — collapsed (no `OperationalError` catch-and-
     emit branch needed; table is in tree).
   - **§5 effort table** — W-C −1/−1/−1 d; total 16-25 → 15-24.
   - **§8 OQ list** — OQ-7 redefinition note + new OQ-10.
   - **§9 provenance** — Phase 0 close + round 4 entry.

4. **`reporting/plans/post_v0_1_14/agent_state_visibility_findings.md`**
   — the SUPERSEDED-for-F-AV-03 header note added (mirrors F-AV-01
   supersede shape from round-2). Verify the supersede chain reads
   coherently (header → original prose preserved).

5. **`src/health_agent_infra/core/state/migrations/020_target.sql`** —
   the existing `target` table that W-C now extends. Verify it has
   the `target_type` CHECK constraint, `status` enum, supersession
   columns, and indexes that the round-4 §2.D contract claims.

6. **`src/health_agent_infra/cli.py`** — spot-check that
   `cmd_target_set` (line ~2668), `cmd_target_list` (~2745),
   `cmd_target_commit` (~2790), `cmd_target_archive` (~2825) exist
   as cited; `_w57_user_gate` is wired through `cmd_target_commit`.
   Spot-check `cmd_state_reproject` at line 4111 (F-PHASE0-02 fix
   citation) and `--cascade-synthesis` flag at line 8526.

7. **`src/health_agent_infra/core/intake/gaps.py`** —
   `compute_intake_gaps` exists; the file is the W-A target.

8. **Cross-doc fan-out targets:**
   - `reporting/plans/v0_1_15/README.md` — status updated; Phase 0
     close entry added.
   - `reporting/plans/tactical_plan_v0_1_x.md` §5B — W-C effort row
     + cycle-arithmetic effort line + main release-table v0.1.15 row
     all updated.
   - `reporting/plans/v0_1_16/README.md` + `reporting/plans/v0_1_17/README.md`
     — verify NO updates were needed (these are downstream cycles;
     the F-PHASE0-01 Option A revision does not bleed into them
     since v0.1.16 is empirical-by-design and v0.1.17's W-D arm-2
     reads `target` not `nutrition_target`, so the round-4 revision
     IMPROVES v0.1.17's coupling story rather than touching it).

9. **`AGENTS.md`** — verify no governance edit needed for the
   F-PHASE0-01 Option A revision. The "Settled Decisions" / "Do Not
   Do" / governance invariants are unchanged (no new state-model
   discipline, no W57 variant, no clinical-claim shift). Confirm or
   surface a governance gap as a finding.

---

## Step 2 — Audit questions

Each question has a Q-bucket key for response cross-reference.
Answer **yes / no / partial** for each, with one-paragraph rationale
+ recommended response if non-yes.

### Q-R4.1 — F-PHASE0-01 Option A revision internal coherence

**Q-R4.1.a** Does §2.D's migration 024 shape (recreate-and-copy of
`target`; CHECK extension; copy via `INSERT INTO target SELECT * FROM
target_old`; rebuild three indexes) preserve every existing row
byte-stable, including the maintainer's three live nutrition rows?

**Q-R4.1.b** Does §2.D's 4-atomic-row convenience command shape
(single `BEGIN IMMEDIATE` / `COMMIT`; idempotent on re-invocation;
`reason` field carries `<phase>:<free-text-or-default>`) match the
existing `cmd_target_set` discipline at `cli.py:2715-2731`? Or is
there a friction point — e.g., `add_target` doesn't accept a
multi-row payload, so the convenience handler needs to call it 4
times within a single transaction managed at the handler level?

**Q-R4.1.c** Does §2.B's revised W-A `target_status` query (`SELECT 1
FROM target WHERE user_id=? AND domain='nutrition' AND target_type
IN ('calories_kcal','protein_g','carbs_g','fat_g') AND status='active'
AND superseded_by_target_id IS NULL AND date(effective_from) <=
date(?) AND (effective_to IS NULL OR date(effective_to) >= date(?))
LIMIT 1`) correctly use the existing `idx_target_active_window`
index? Does the `(effective_to IS NULL OR effective_to >= ?)` clause
match the active-window semantics per migration 020?

**Q-R4.1.d** Does §2.B's three-valued `target_status` enum
(`present` / `absent` / `unavailable`) map cleanly to the new
"active row covers today" / "rows exist but none cover today" /
"no nutrition rows at all" semantics? Specifically, does the
`absent` derivation (the "broader query: any nutrition target row,
any status") correctly distinguish from `unavailable` without
re-introducing the old `OperationalError`-catch path?

**Q-R4.1.e** Does §2.E W-D arm-1 acceptance test 4 (the narrowed
fixture set: present / absent / unavailable, no table-missing case)
exhaust the suppression contract? Are there any edge cases the
removed table-missing case used to cover that the narrowed set now
misses (e.g., a row exists but has `status='archived'` only — does
that map to `absent` or `unavailable`)?

**Q-R4.1.f** Do §4 risks 1 + 2 correctly collapse the
`OperationalError` catch-and-emit branch? Is there any residual
prose in §4 that still implies pre-W-C table-missing handling?

**Q-R4.1.g** Does §5's effort table correctly delta W-C from 3-4 d
to 2-3 d (−1/−1/−1)? Is the −0.5d to −1d delta the maintainer
estimated in `audit_findings.md` F-PHASE0-01 consistent with the
table's −1/−1/−1?

### Q-R4.2 — Cross-doc fan-out completeness

**Q-R4.2.a** Does `reporting/plans/v0_1_15/README.md`'s status block
match PLAN.md's header? Both should say "D14 round 4 ready" with
the halving signature `12 → 7 → 3 → ?` and the Phase 0 close note.

**Q-R4.2.b** Does `reporting/plans/tactical_plan_v0_1_x.md` §5B's
W-C row + effort estimate + main release-table v0.1.15 row all
reflect the round-4 revision? Or did one of the three update sites
keep stale "new `nutrition_target` table" prose?

**Q-R4.2.c** Does `agent_state_visibility_findings.md`'s
SUPERSEDED-for-F-AV-03 header read coherently against the existing
SUPERSEDED-for-cycle-scoping + SUPERSEDED-W-A-predicate headers? Is
the chain of supersedes legible to a reader landing cold?

**Q-R4.2.d** Are there OTHER docs that should have been touched but
weren't? Specifically: does any line in `AGENTS.md`,
`reporting/docs/architecture.md`, `reporting/docs/state_model_v1.md`,
or `reporting/plans/strategic_plan_v1.md` reference the
"`nutrition_target` table" by name in a way that's now stale? (The
PLAN §3 cross-cutting bullet was updated; verify no other surface
silently kept the old name.)

### Q-R4.3 — Nit-class fix verification

**Q-R4.3.a** F-PHASE0-02: PLAN §2.A line 108 should now cite
`cmd_state_reproject` at `cli.py:4111` and the `--cascade-synthesis`
flag at `cli.py:8526`, with the `cli.py:3041-3049` (the wrong-
function `_project_gym_submission_into_state` range) noted as the
prior incorrect citation. Verify the corrected citations match the
actual source positions.

**Q-R4.3.b** F-PHASE0-03: PLAN §2.A fix-shape paragraph should now
cite `_norm` at `core/state/projectors/strength.py:66` (with the
`core/state/` path prefix). Verify the function exists at that line
and the path is the actively-imported one (not a stale alias).

**Q-R4.3.c** F-PHASE0-04: `agent_state_visibility_findings.md` should
now have a third SUPERSEDED-class header note covering F-AV-03,
mirroring the F-AV-01 supersede shape from round-2. Verify the
existing F-AV-03 prose (lines 196-223) is preserved as
original-finding provenance and not silently rewritten.

### Q-R4.4 — OQ-10 well-formedness

**Q-R4.4.a** Is the round-4 PLAN default (per-row commit, no
`hai target commit-group --reason-prefix`) the right v0.1.15
default? Specifically: does the existing `cmd_target_commit` UX
already require N invocations for N rows (matching the W57 per-row
gate convention), or does it support batched commit-by-reason that
the convenience command would inherit transparently?

**Q-R4.4.b** If the foreign-user gate session surfaces friction
with 4 sequential commit prompts, what's the cleanest reversal
path? The OQ-10 note says "v0.1.16 / v0.1.17"; is that the right
destination given v0.1.16 is empirical-by-design and v0.1.17 is
maintainability + eval?

### Q-R4.5 — Second-order contradictions

**Q-R4.5.a** Did the F-PHASE0-01 Option A revision introduce any
predicate that contradicts an existing PLAN section unchanged
elsewhere? E.g., does any §1.x / §3 / §6 / §7 line still claim a
new table is shipped? Does any acceptance test in §2 reference a
test fixture that the round-4 narrowing removed?

**Q-R4.5.b** Did the round-4 effort retotal (−1/−1/−1 on W-C; total
16-25 → 15-24) propagate to every effort surface? Header status
block, §1.2 total, §5 table, tactical §5B effort line — any of
these still reading "16-25"?

**Q-R4.5.c** Does the OQ-7 redefinition (`unavailable` semantics
narrowed from "no target ever set OR table-missing" to "no
nutrition rows at all") leave any acceptance test in §2.B / §2.E
referring to the old wider definition? Specifically, the §2.B
acceptance test that mentions "table-missing" was supposed to be
removed; verify it was.

### Q-R4.6 — Shippability

**Q-R4.6.a** Is the round-4 PLAN shippable as-written for Phase 1
implementation open? If a contributor opens W-A + W-C + W-D arm-1
as parallel branches today, is there enough specification to
implement each independently against the round-4 contract?

**Q-R4.6.b** Are there any acceptance criteria in §2.B / §2.D / §2.E
that are unfalsifiable, ambiguous, or missing a fixture spec the
contributor would have to invent? Round-3 tightened the
falsifiability surface; round-4's job is to verify the new prose
didn't loosen it.

---

## Step 3 — Verdict format

Return one of:

- **PLAN_COHERENT** — round-4 revision is internally coherent,
  cross-doc fan-out caught everything, no nit-class findings.
  Cycle proceeds to Phase 1.
- **PLAN_COHERENT_WITH_REVISIONS** — round-4 revision is coherent
  modulo N nit-class findings (acceptance-criterion-weak or
  documentation-accuracy severity). Recommend close in-place if
  N ≤ 2; recommend round 5 if N ≥ 3 or any finding is
  scope-revising.
- **PLAN_INCOHERENT** — round-4 revision introduces a contradiction
  the maintainer should rewrite materially. Provide the contradiction
  + recommended rewrite shape.

If any Q-bucket question's answer is "no" or "partial," surface as a
finding with severity (`nit` / `acceptance-criterion-weak` /
`scope-revising` / `plan-incoherent`).

---

## Step 4 — Close-in-place option

If round-4 verdict is PLAN_COHERENT_WITH_REVISIONS with ≤ 2 findings
and all severity ≤ acceptance-criterion-weak, recommend close in
place: maintainer applies findings to PLAN.md without re-firing a
round 5. The cycle then opens for Phase 1 implementation directly.
This matches the round-3 close-in-place pattern.

If verdict is PLAN_COHERENT, the cycle opens for Phase 1
implementation directly with no further revision. Phase 3 (foreign-
user gate) still requires the maintainer-side Q2 candidate decision
per `pre_implementation_gate_decision.md` §6 + PLAN §4 risk 6 —
that question is reserved for the maintainer, not for round-4 audit.

---

## Step 5 — Open questions for the maintainer

If round-4 audit surfaces a question the maintainer should answer
before round 5 (or before Phase 1 opens, if close-in-place), list
it here. Format: one OQ per line with `[OQ-R4-NN]` prefix.

If no new OQs surface, write "None."

---

## Step 6 — Response file

Write the response to
`reporting/plans/v0_1_15/codex_plan_audit_round_4_response.md` with:

1. Verdict line (one of the three).
2. Round-3 finding closure verification (table: each F-PHASE0-NN +
   CLOSED / CLOSED_WITH_RESIDUAL / OPEN + rationale).
3. New round-4 findings (if any) with Q-bucket key + severity +
   reference + argument + recommended response.
4. OQ list (if any).
5. Closure recommendation (close-in-place vs round 5).

The maintainer responds in
`reporting/plans/v0_1_15/codex_plan_audit_round_4_response_response.md`
with per-finding triage (AGREED / DISAGREED / SHAPE-EXTENDED) and
applies the agreed revisions.

---

## Step 7 — Empirical settling-shape expectation

Round-1 12 → round-2 7 → round-3 3 was the halving signature for
the rounds-1-through-3 chain. Round 4 is unusual because it audits
a Phase-0-revision (smaller surface than the rounds-1-3 audits of
the original PLAN). **Empirical expectation: 0-2 findings.** A
round-4 finding count > 2 signals the F-PHASE0-01 Option A revision
surface was wider than the maintainer estimated; in that case
recommend round 5 explicitly.

The cycle has now spent 4 D14 rounds + 1 Phase 0 + 1 gate-decision
on a 7-W-id substantive cycle. That is within the AGENTS.md
empirical norm for substantive PLANs (2-4 D14 rounds + Phase 0 + gate);
exceeding it would signal cycle-too-large risk, which is worth
flagging if round 4 surfaces > 2 findings.
