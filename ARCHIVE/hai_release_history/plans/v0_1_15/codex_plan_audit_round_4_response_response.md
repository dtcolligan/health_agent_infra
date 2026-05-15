# Maintainer Response — Codex Plan Audit Round 4

**Round 4 verdict:** PLAN_COHERENT_WITH_REVISIONS, 2 close-in-place findings, **closed in-place** per round-4 prompt Step 4.
**Round 4 close:** 2026-05-03 evening with both findings applied to PLAN final + cross-doc fan-out (v0.1.17 README dependency bullet).
**Status:** **D14 closed at round 4.** Phase 1 implementation opens next per the substantive-cycle pattern.

Halving signature held end-to-end across rounds 1-3 (12 → 7 → 3); round 4 is the post-Phase-0 ratification round (different chain — audits the F-PHASE0-01 Option A revision specifically, not the original PLAN). Round-4 finding count: 2 (within the prompt Step 7 expectation of 0-2 findings for a small-surface revision-ratification round).

---

## F-R4-01 — W-C convenience command contract needs implementation-level tightening

**Verdict:** AGREED, applied verbatim (with one shape extension on the natural-key approach).

**Why this is real.** Verified all four sub-claims against `core/target/store.py`:

1. **Idempotency** — line 195: `target_id=target_id or f"target_{uuid.uuid4().hex[:12]}"`. Random UUID; no PK-collision idempotency path on identical re-invocation. The round-4 §2.D draft said "matches `cmd_target_set` discipline" without specifying the mechanism — the existing surface is annotated `idempotent="no"`, so the discipline isn't there to inherit.
2. **Atomicity** — line 222: `conn.commit()` inside `add_target()`. Calling it 4 times = 4 separate commits, not a single `BEGIN IMMEDIATE` / `COMMIT` transaction. The round-4 §2.D draft asserted atomic insert without naming the helper change required to enable it.
3. **Source/status conflation** — `_VALID_STATUS = {"proposed", "active", "superseded", "archived"}` at line 38; `"user_authored"` is a `source` value (line 39 W57 invariant: `source != "user_authored" requires status='proposed' on insert`). The round-4 §2.D draft put `"user_authored"` in the `status` slot — a typo that would have failed `_validate()` at line 137-140 immediately.
4. **`_VALID_TARGET_TYPE`** — lines 39-43 lack `'carbs_g'` and `'fat_g'`. Migration 024 extends only the SQL CHECK; the Python validator at line 141-144 would reject before SQL fires.

All four are implementation-level mismatches that would have surfaced at first test failure. Codex caught them at PLAN time.

**Action.** PLAN §2.D rewritten:

- **Source/status pairing** explicitly defined for both invocation paths (agent → `proposed`/`agent_proposed`; user → `active`/`user_authored`), citing `core/target/store.py:160-168` W57 invariant.
- **Atomicity contract** named: W-C must introduce `add_targets_atomic(conn, *, records)` helper (preferred) or extend `add_target()` with `commit: bool = True` kwarg. Existing `cmd_target_set` continues to use the per-row commit form; only the new convenience handler hits the atomic path.
- **Idempotency mechanism** named: natural-key duplicate-detection (preferred — survives `--phase` taxonomy renames) at the convenience-handler entry, querying for `(user_id, domain='nutrition', target_type, status, effective_from, reason LIKE '<phase>:%')` with identical `value_json`. Deterministic-`target_id` approach noted as alternative + brittle reason.
- **`_VALID_TARGET_TYPE` extension** required in the same change-set as migration 024.
- **CLI `--target-type` choices extension** noted (`cli.py:8018-8025` per Codex F-R4-01 reference).

PLAN §2.D acceptance tests rewritten 5 → 8 to cover:
- Migration 024 SQL CHECK + Python `_VALID_TARGET_TYPE` test paired (test 1).
- Atomic-insert helper test with rollback assertion via wrapped connection (test 2).
- Source/status pairing for both invocation paths (test 3, replacing the old conflated test).
- W57 gate test for the agent path (test 4).
- Natural-key idempotency test (test 5).
- Idempotency edge: phase change writes new group (test 6).
- Read-side integration with W-A's query (test 7).
- Capabilities-manifest annotation including the new `idempotent="yes"` for an agent-safe writes-state command (test 8 — first command on this surface marked idempotent; verify the manifest schema accepts the combination).

**Why this slipped at round 4.** The round-4 §2.D rewrite focused on the table-reuse architecture decision (the F-PHASE0-01 Option A direction) and didn't drill into the helper-level implementation contract. The Phase 0 internal sweep verified the `target` table existed with the right schema (migration 020) but didn't verify the Python helper paths would compose into a 4-row atomic + idempotent macro. Round 4's audit caught the gap before any code was written — exactly the audit-chain function. **Pattern note for future cycles:** when a PLAN section names "atomic" or "idempotent" against an existing helper, verify the helper's commit boundary + key-generation behavior in the same provenance pass, not after.

---

## F-R4-02 — Round-4 stale-prose/fan-out cleanup cluster

**Verdict:** AGREED, applied verbatim. Three independent stale fragments.

**Action.**

1. **PLAN §4 risk 4 test number:** "§2.E acceptance test 3 explicitly asserts the fallback behavior" → "§2.E acceptance test 4 explicitly asserts the fallback behavior (10am breakfast-only with `target_status='present'` falls through to existing classifier)." Test 3 is the 19:00 day-closed normal-classification case; test 4 is the partial-day-with-target fallback. The number was correct in the round-3 PLAN but the round-4 §2.E narrowing renumbered the table-missing case out, leaving §4 referencing a stale anchor.
2. **PLAN §5 effort retotal:** "**15 - 19 - 25 days**" → "**15 - 19 - 24 days**" (matches the per-WS arithmetic ceiling of 24 from the §5 table). The `25` was carried over from the round-3 worst-case; the round-4 −1d on W-C should have dropped it. Same paragraph: D14 expectation sentence rewritten to describe round 4 honestly as "fired post-Phase-0 to ratify the F-PHASE0-01 Option A revision," not "only fires if round 3 surfaces structural issues" (which is now backwards-looking and misleading — round 4 fired for a different reason than the rounds-1-3 chain anticipated).
3. **v0.1.17 README dependency bullet:** "W-C `nutrition_target` table is in tree (W-D arm-2 reads it)" → "W-C `target` table macro extension (migration 024 — `'carbs_g'` + `'fat_g'` added to `target_type` CHECK + `_VALID_TARGET_TYPE`) is in tree; W-D arm-2 reads the existing `target` table filtered by `domain='nutrition' AND target_type IN (...)`." The original v0.1.17 README was authored before the round-4 F-PHASE0-01 Option A revision and silently kept the old name; this is exactly the cross-doc fan-out failure the "Summary-surface sweep on partial closure" pattern warns about — every time a state-model decision moves, every reader-facing reference must move with it.

**Cross-doc fan-out audit.** Codex Q-R4.2.d confirmed no other surface (`AGENTS.md`, `reporting/docs/architecture.md`, `reporting/docs/state_model_v1.md`, `reporting/plans/strategic_plan_v1.md`) carried a stale `nutrition_target` reference. v0.1.17 README was the only cross-doc miss.

**Why this slipped.** I ran a `grep -rn nutrition_target` sweep at round-4 close but bounded it to v0_1_15/, README.md, and tactical_plan_v0_1_x.md — exactly the surfaces I was actively editing. v0.1.17 README was outside the sweep box. Should have widened to `reporting/plans/` whole-tree. **Pattern note for future cycles:** scope sweep queries by what's affected, not by what I'm editing.

---

## OQ-10 default ratified per Codex Q-R4.4

**Codex opinion (Q-R4.4.a + Q-R4.4.b):** per-row commit is the right v0.1.15 default. The existing `cmd_target_commit` UX is per-row only; no batched commit-by-reason exists, so the OQ-10 per-row default matches W57 surface convention. Commit-group is reversible to v0.1.16 (if the foreign-user gate surfaces friction) or v0.1.17 (if treated as maintainability/UX consolidation).

**Maintainer ratification:** per-row commit confirmed. No change to PLAN §2.D OQ-10 default. If the W-2U-GATE recorded session shows the named foreign-user candidate hitting friction with 4 sequential commit prompts (P1 trust-degrading-but-threshold-met per PLAN §2.G), defer to v0.1.16 with named `W-2U-FIX-P1` scope per the PLAN §2.G P1 rules.

---

## Q-bucket summary cross-reference

| Q-bucket | Codex answer | Maintainer disposition |
|---|---|---|
| Q-R4.1.a (migration recreate-and-copy preserves rows) | yes | no action |
| Q-R4.1.b (4-row atomic match cmd_target_set discipline) | partial | F-R4-01 applied |
| Q-R4.1.c (target_status query uses idx_target_active_window) | yes | no action |
| Q-R4.1.d (3-valued enum maps cleanly) | yes | no action |
| Q-R4.1.e (3-fixture set exhausts suppression contract) | yes | no action |
| Q-R4.1.f (§4 risks correctly collapse) | yes | no action |
| Q-R4.1.g (W-C effort delta is right) | partial | F-R4-02 applied (§5 25 → 24) |
| Q-R4.2.a (README matches PLAN status) | yes | no action |
| Q-R4.2.b (tactical fan-out caught W-C) | yes | no action |
| Q-R4.2.c (supersede chain legible) | yes | no action |
| Q-R4.2.d (no other docs stale on nutrition_target) | partial | F-R4-02 applied (v0.1.17 README) |
| Q-R4.3.a (F-PHASE0-02 citation correct) | yes | no action |
| Q-R4.3.b (F-PHASE0-03 citation correct) | yes | no action |
| Q-R4.3.c (F-PHASE0-04 SUPERSEDED preserved) | yes | no action |
| Q-R4.4.a (OQ-10 per-row default right) | yes (with F-R4-01 caveat) | ratified per-row |
| Q-R4.4.b (reversal path) | yes | v0.1.16 if gate surfaces P1 friction |
| Q-R4.5.a (no stale new-table predicate in core) | partial | F-R4-02 applied |
| Q-R4.5.b (effort retotal propagated) | partial | F-R4-02 applied |
| Q-R4.5.c (OQ-7 redefinition consistent) | yes | no action |
| Q-R4.6.a (PLAN shippable for Phase 1 open) | partial | F-R4-01 applied — now shippable |
| Q-R4.6.b (acceptance criteria falsifiable) | partial | F-R4-01 applied — acceptance tests rewritten 5 → 8 with concrete falsification surfaces |

---

## Summary

2/2 findings applied. No new OQs raised. No round 5 fired.

**D14 closed at round 4.** The cycle is open for Phase 1 implementation:

- W-GYM-SETID, W-A, F-PV14-01, W-C parallelizable per PLAN §1.3.
- Tests-first per W-id (PLAN §2 contracts are the acceptance criteria; F-R4-01 acceptance tests for W-C are the lock-in surface).
- Atomic commits per W-id.

Phase 3 W-2U-GATE candidate is on file (the named foreign-user candidate, named at the pre-implementation gate). Cycle proceeds path (a) per PLAN §4 risk 6 closure.

**Empirical D14 settling-shape retrospective for v0.1.15:**
- Round 1 (pre-Phase-0 chain): 12 findings.
- Round 2: 7.
- Round 3: 3 — close-in-place.
- Phase 0 (D11): 1 revises-scope (F-PHASE0-01) + 3 nits + persona matrix 13/13 clean.
- Round 4 (post-Phase-0 ratification): 2 close-in-place.

Total D14 surface: 4 rounds + Phase 0 + gate-decision. Within AGENTS.md substantive-cycle norm (2-4 D14 rounds + Phase 0 + gate). The round-4 fire was **not** a "halving signature broke" event — it audited a *different* PLAN (the post-Phase-0 revision) than rounds 1-3 audited, so the 2 round-4 findings don't extend the 3 → ? trajectory; they're a separate small-surface chain. **Pattern lesson worth capturing for future cycles:** when Phase 0 surfaces a revises-scope finding, the post-revision D14 round is its own audit chain — budget 0-2 findings (small surface) regardless of the rounds-1-3 trajectory.
