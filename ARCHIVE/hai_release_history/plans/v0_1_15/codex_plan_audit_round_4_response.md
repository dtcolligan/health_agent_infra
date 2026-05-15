# Codex External Audit Response - v0.1.15 PLAN.md D14 round 4

**Verdict:** PLAN_COHERENT_WITH_REVISIONS

Round-4 ratifies the F-PHASE0-01 Option A direction. Reusing the
existing `target` table is coherent, simpler than the duplicate-table
shape, and aligns with migration 020 plus the existing W57 target
commit surface. I found **2 findings**: one acceptance-criterion-weak
W-C command-contract issue and one nit-class stale-prose/fan-out
cluster. Both are closeable in place. No round 5 required if these are
applied directly.

## Finding Closure Verification

| Finding | Status | Rationale |
|---|---|---|
| F-PHASE0-01 | CLOSED_WITH_RESIDUAL | Option A is correctly applied at the architecture level: PLAN §2.B reads `target`, §2.D extends `target`, §2.E narrows the fixture set, §4 removes the table-missing branch, and effort drops by 1 day. Residual: §2.D's convenience-command implementation contract is internally too loose; see F-R4-01. |
| F-PHASE0-02 | CLOSED | PLAN §2.A now cites `cmd_state_reproject` at `cli.py:4111` and `--cascade-synthesis` at `cli.py:8526`; both match the live source. |
| F-PHASE0-03 | CLOSED | PLAN §2.A now cites `_norm` at `core/state/projectors/strength.py:66`; the function exists at that path. |
| F-PHASE0-04 | CLOSED | `agent_state_visibility_findings.md` has a clear F-AV-03 SUPERSEDED header and preserves the original F-AV-03 prose as provenance. |

## New Round-4 Findings

### F-R4-01 - W-C convenience command contract needs implementation-level tightening

**Q-bucket:** Q-R4.1.b, Q-R4.4.a, Q-R4.6.a, Q-R4.6.b  
**Severity:** acceptance-criterion-weak  
**Reference:** `reporting/plans/v0_1_15/PLAN.md:160-178`; `src/health_agent_infra/core/target/store.py:171-223`; `src/health_agent_infra/core/target/store.py:136-168`; `src/health_agent_infra/cli.py:2668-2731`; `src/health_agent_infra/cli.py:8018-8025`

**Argument.** The W-C direction is right, but the detailed command
contract has three implementation mismatches against the existing
target store:

1. PLAN §2.D says identical re-invocation is idempotent and "matches
   `cmd_target_set` discipline." The live command is annotated
   `idempotent="no"` and `add_target()` generates random UUID-backed
   target IDs, so no identical-call PK collision can occur unless W-C
   defines a new deterministic ID or natural-key duplicate-detection
   rule.
2. PLAN §2.D requires all four rows to insert in one `BEGIN IMMEDIATE`
   / `COMMIT` transaction with rollback on any single-row failure.
   The existing `add_target()` helper commits inside each call, so a
   handler that simply calls `add_target()` four times cannot satisfy
   the atomicity acceptance test.
3. PLAN §2.D line 166 appears to put `"user_authored"` in the `status`
   slot for non-agent calls. `status` must be one of `proposed`,
   `active`, `superseded`, `archived`; `user_authored` is a `source`
   value. The implementation also needs to extend the Python
   `_VALID_TARGET_TYPE` set for `carbs_g` and `fat_g`, not only the SQL
   CHECK constraint.

**Recommended response.** Keep Option A, but tighten §2.D before Phase
1 opens:

- Define the source/status pairing explicitly:
  `ingest_actor == claude_agent_v1` or another named agent actor yields
  `source='agent_proposed', status='proposed'`; direct user/CLI calls
  yield `source='user_authored', status='active'`.
- Add an implementation note that W-C must introduce an atomic store
  helper, for example `add_targets_atomic()` or an internal
  `add_target(..., commit=False)` path, because current `add_target()`
  commits each row.
- Define idempotency concretely: either deterministic target IDs for
  `(user_id, effective_from, phase, target_type)` or a natural-key
  duplicate check that returns existing rows on identical args.
- State that W-C updates `_VALID_TARGET_TYPE` and relevant CLI choices
  to admit `carbs_g` and `fat_g`.

### F-R4-02 - Round-4 stale-prose/fan-out cleanup cluster

**Q-bucket:** Q-R4.2.b, Q-R4.2.d, Q-R4.5.a, Q-R4.5.b  
**Severity:** nit  
**Reference:** `reporting/plans/v0_1_15/PLAN.md:252`; `reporting/plans/v0_1_15/PLAN.md:275-277`; `reporting/plans/v0_1_17/README.md:41-44`

**Argument.** The main round-4 contract is coherent, but three stale
prose fragments survived the revision:

1. PLAN §4 risk 4 says "§2.E acceptance test 3 explicitly asserts the
   fallback behavior." The fallback is acceptance test 4; test 3 is the
   19:00 day-closed normal-classification case.
2. PLAN §5 says adjusted effort is `15 - 19 - 25 days`, then says the
   headline is `15-24`. Header, §1.2, README, and tactical all use
   `15-24`; §5 should not retain a `25` worst-case after the round-4
   retotal. The same paragraph still says round 4 only fires if round
   3 surfaces structural issues, but this round 4 fired because Phase 0
   found F-PHASE0-01 after round 3 closed.
3. v0.1.17 README says "W-C `nutrition_target` table is in tree
   (W-D arm-2 reads it)." Under Option A, v0.1.17 depends on the
   `target` table macro extension from v0.1.15, not a
   `nutrition_target` table.

**Recommended response.** Apply a small prose-only patch:

- PLAN §4 risk 4: change "acceptance test 3" to "acceptance test 4."
- PLAN §5: align the adjusted effort sentence to `15 - 19 - 24` or
  equivalent `15-24` prose, and rewrite the D14 expectation sentence
  to say round 4 is the post-Phase-0 F-PHASE0-01 ratification round.
- v0.1.17 README: replace the dependency bullet with "W-C target-table
  macro extension is in tree; W-D arm-2 reads the existing `target`
  table."

## Q-Bucket Summary

| Q-bucket | Answer | Note |
|---|---|---|
| Q-R4.1.a | yes | Migration 024 recreate-and-copy shape preserves existing columns and rows, assuming identical column order. |
| Q-R4.1.b | partial | See F-R4-01. |
| Q-R4.1.c | yes | The query shape can use `idx_target_active_window` for `user_id`, `status`, and window predicates; domain/type filtering happens after the active-window narrowing. |
| Q-R4.1.d | yes | `present` / `absent` / `unavailable` now map cleanly to active-covering row / historical nutrition row but none covering today / no nutrition target rows. Archived-only rows correctly map to `absent`. |
| Q-R4.1.e | yes | The narrowed three-fixture set covers the suppression contract; archived-only is covered by the "rows exist but none cover today" absent fixture. |
| Q-R4.1.f | yes | §4 no longer requires an OperationalError catch-and-emit branch. |
| Q-R4.1.g | partial | W-C delta is correctly -1/-1/-1, but §5 still has a stale `15 - 19 - 25` sentence; see F-R4-02. |
| Q-R4.2.a | yes | v0.1.15 README matches the D14 round-4-ready status and halving signature. |
| Q-R4.2.b | yes | Tactical v0.1.15 row, §5B W-C row, and §5B effort estimate reflect Option A. |
| Q-R4.2.c | yes | `agent_state_visibility_findings.md` supersede chain is legible and preserves original provenance. |
| Q-R4.2.d | partial | No AGENTS/architecture/state_model/strategic stale `nutrition_target` reference found, but v0.1.17 README still has one; see F-R4-02. |
| Q-R4.3.a | yes | F-PHASE0-02 citations match live source. |
| Q-R4.3.b | yes | F-PHASE0-03 citation matches live source. |
| Q-R4.3.c | yes | F-PHASE0-04 header note exists and original F-AV-03 prose is preserved. |
| Q-R4.4.a | yes with F-R4-01 caveat | Existing target commit UX is per-row only; no batched commit-by-reason exists. OQ-10's per-row default matches current W57. |
| Q-R4.4.b | yes | Reversal can be v0.1.16 if the foreign-user gate surfaces P1 friction and the maintainer scopes it there, or v0.1.17 if treated as maintainability/UX consolidation. |
| Q-R4.5.a | partial | No stale new-table predicate in PLAN core sections, but the §4 test-number prose needs correction; see F-R4-02. |
| Q-R4.5.b | partial | Most surfaces read `15-24`; PLAN §5 retains `15 - 19 - 25`; see F-R4-02. |
| Q-R4.5.c | yes | The table-missing fixture state was removed from §2.B / §2.E and OQ-7 was narrowed correctly. |
| Q-R4.6.a | partial | Phase 1 is shippable once F-R4-01 tightens the W-C implementation contract. W-A and W-D arm-1 are sufficiently specified. |
| Q-R4.6.b | partial | W-C idempotency/atomicity is under-specified against current helpers; see F-R4-01. |

## Open Questions

None.

## Closure Recommendation

Close in place. The finding count is 2 and severities are at or below
acceptance-criterion-weak. Apply F-R4-01 and F-R4-02 directly to the
PLAN/cross-doc surfaces, then open Phase 1 implementation. No D14
round 5 is needed unless the maintainer chooses to change OQ-10's
default from per-row commit to commit-group in v0.1.15.
