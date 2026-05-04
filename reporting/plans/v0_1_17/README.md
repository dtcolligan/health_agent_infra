# v0.1.17 cycle — workspace

**Status:** scoped, not yet open. PLAN.md authored when the cycle opens after v0.1.16 closes. v0.1.15 is already published; v0.1.16 must first absorb or defer the post-publish foreign-user findings.

**Tier (anticipated):** substantive (multiple inherited workstreams + new schema/migration + persona-replay residual). Full Phase 0 D11 bug-hunt + multi-round D14 plan-audit.

**Provenance.** Created 2026-05-02 evening as part of the v0.1.15 scope-restructure. The original v0.1.15 round-0 plan combined mechanical refactor + daily-loop hardening + eval substrate + foreign-user gate into a **16-catalogued-slot** 39-60-day cycle (W-D counted as two arms). Round-0 self-audit identified ~50% over-scoping vs the v0.1.15 objective ("foreign user reaches `synthesized`"). The maintainability + eval substrate work was reassigned to this cycle (9 of the 16 slots) so v0.1.15 stays focused on the user-facing gate. v0.1.16 stays reserved exclusively for empirical post-gate bug fixes per the maintainer's framing.

## Scope (provisional, to be finalised in PLAN.md)

| W-id | Title | Effort | Source |
|---|---|---|---|
| **W-29** | cli.py 9217-line mechanical split (byte-stable manifest) | 4-6 d | v0.1.14 RELEASE_PROOF §carry-overs; AGENTS.md D124-135 |
| **W-30** | Capabilities-manifest schema freeze prep (regression test only; freeze itself is v0.2.3) | 0.5 d | AGENTS.md D124-135 |
| **F-PV14-02** | `hai sync purge` surgical-cleanup CLI | 1.5 d | `post_v0_1_14/carry_over_findings.md` F-PV14-02 |
| **W-AH-2** | Scenario fixture expansion 35 → 120+ | 4-6 d | v0.1.14 RELEASE_PROOF §carry-overs |
| **W-AI-2** | `hai eval review` CLI surface | 3-4 d | v0.1.14 RELEASE_PROOF §carry-overs |
| **W-AM-2** | 4 fork-deferred escalate-tagged scenarios (sleep / strength / stress / nutrition) | 2-3 d | v0.1.14 RELEASE_PROOF §carry-overs |
| **W-Vb-4** | Persona-replay residual P7..P12 (6 personas) | 5-7 d | v0.1.14 RELEASE_PROOF §carry-overs |
| **W-B** | `hai intake weight` body-comp surface + `body_comp` table + migration | 3-4 d | `agent_state_visibility_findings.md` F-AV-02 (deferred from v0.1.15 round-0) |
| **W-D arm-2** | Partial-day nutrition end-of-day projection (gated on W-C shipped in v0.1.15) | 2-3 d | `agent_state_visibility_findings.md` F-AV-04 arm 2 |
| **W-C-EQP** *(small)* | EXPLAIN QUERY PLAN stability assertions for the W-A active-window query against the `target` table post-migration 025. Index-name existence is asserted at v0.1.15 W-C ship; the query-plan-stability check is the stronger assertion Codex round-1 IR F-IR-04 named-deferred from v0.1.15. Deferral target landed here per F-IR-R2-02 disposition. | 0.5 d | v0.1.15 IR round 1 F-IR-04 named-defer |

**Total (estimated):** ~10 W-ids, **25-40 days**, substantive tier.

## Sequencing (provisional)

**Phase 1 — Mechanical foundation:**
1. W-29 cli.py split (lands first; no other v0.1.17 WS depends on it but it would create merge friction with W-AH-2 / W-AI-2 if they touched cli.py late).
2. W-30 regression test.

**Phase 2 — Eval substrate (parallelizable):**
3. W-AH-2 + W-AI-2 + W-AM-2 + W-Vb-4. Mostly independent of each other; persona-runner reads the post-v0.1.15 schema (W-A presence + W-C target).

**Phase 3 — Carry-overs + nice-to-haves:**
4. F-PV14-02 (`hai sync purge` — independent, small).
5. W-B (intake weight + body-comp table + migration; independent of eval substrate).
6. W-D arm-2 (end-of-day projection; depends on W-C shipped in v0.1.15).

## Dependency on v0.1.15 + v0.1.16

- **v0.1.15 must close** so that:
  - W-A presence surface is in tree (persona-runner consumes it).
  - W-C `target` table macro extension (migration 025 — `'carbs_g'` + `'fat_g'` added to `target_type` CHECK + `_VALID_TARGET_TYPE`) is in tree; W-D arm-2 reads the existing `target` table filtered by `domain='nutrition' AND target_type IN ('calories_kcal','protein_g','carbs_g','fat_g')`. (Updated post-v0.1.15 round-4 F-PHASE0-01 Option A revision; the original v0.1.15 round-3 PLAN proposed a separate `nutrition_target` table that was cut. Migration number bumped from "024" to "025" at W-C-implementation time because v0.1.15 W-GYM-SETID claimed 024 first.)
  - The repo is post-restructure-stable.
- **(Former v0.1.16 precondition retired 2026-05-04.)** The original
  v0.1.16 → v0.1.17 dependency was that the foreign-user gate would
  have fired and any P0/P1 bugs landed before W-AH-2's eval-substrate
  work, so scenarios wouldn't encode the wrong runtime contract.
  v0.1.16 was cancelled 2026-05-04 (named foreign-user candidate
  unavailable; see `reporting/plans/v0_1_16/README.md`). The
  empirical work renumbered to **v0.1.19**, sequenced after **v0.1.18
  (onboarding)**. v0.1.17 now runs without that precondition: W-AH-2
  consolidates against the existing synthetic persona matrix +
  dogfood evidence, and ships honestly as "synthetic-coverage
  expansion" rather than "foreign-user-validated coverage."

## Out of scope (deferred further)

- v0.2.0 schema work (W52 + W58D) — depends on v0.1.19 close (post-
  cancellation renumber from v0.1.16), runs parallel to or after
  v0.1.17.
- Capabilities-manifest schema freeze (W-30 final destination is v0.2.3, not v0.1.17).
- Apple Health / Whoop adapters (post-v0.2.x).

## First actions for the cycle session (when it opens)

1. Confirm v0.1.15 published (RELEASE_PROOF.md present). v0.1.16
   close is no longer a precondition (cancelled 2026-05-04).
2. Re-read this README + the source carry-over docs.
3. Author `PLAN.md`. First line: tier annotation.
4. Copy `_templates/codex_plan_audit_prompt.template.md` and customise.
5. Hand to maintainer for D14 round-1.

## Cross-references

- AGENTS.md "Settled Decisions" — W-29 destination redirected v0.1.15 → v0.1.17 (2026-05-02 evening; see `v0_1_15/PLAN.md` §1.4).
- `reporting/plans/v0_1_15/PLAN.md` §7 (this cycle's deferred-work register).
- `reporting/plans/post_v0_1_14/carry_over_findings.md` — F-PV14-02 detail.
- `reporting/plans/post_v0_1_14/agent_state_visibility_findings.md` — F-AV-02 (W-B) + F-AV-04 arm-2 (W-D arm-2) detail.
- `reporting/plans/v0_1_14/RELEASE_PROOF.md` §carry-overs — W-29 / W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4 inheritance chain.
