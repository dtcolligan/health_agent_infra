# REPORT — v0.1.15

**Tier:** substantive.
**Theme:** Foreign-user-ready package + empirical-validation framework.
**Released:** 2026-05-03 evening (publish-first pivot).

---

## What this cycle did

v0.1.15 took the runtime from "the maintainer's daily-driver loop works" to "a non-maintainer can install `health-agent-infra` from PyPI on a clean Python 3.11+ machine and run the full daily flow without re-asking the user for state already in the DB or misclassifying partial-day intake against an unset target."

Six W-ids landed:

- **W-GYM-SETID** fixed a silent-drop bug in multi-exercise gym sessions (the maintainer's actual leg+back session had 8 sets silently dropped because `deterministic_set_id(session_id, set_number)` collided across exercises sharing set numbers). New format includes the exercise slug; migration 024 rewrites OLD-format rows in place; correction-row custom IDs preserved.
- **F-PV14-01** closed a CSV-fixture-into-canonical-state contamination class. The carry-over evidence (post-v0.1.14 dogfood session) found three fixture-shaped `sync_run_log` rows in the maintainer's canonical DB — written by the CSV adapter through the same path live pulls use, with no demo-marker check. Now both `hai pull` and `hai daily` (post-IR-r1) refuse the canonical-DB write unless an explicit opt-in (demo session, `--allow-fixture-into-real-state`, or non-canonical `--db-path` / `HAI_STATE_DB`).
- **W-A** added the `present` block + `is_partial_day` + `target_status` enum to `hai intake gaps`. Round-4 F-PHASE0-01 Option A revision discovered the existing `target` table already supports nutrition rows (calories_kcal + protein_g were in production use); W-A reads that table directly rather than a new parallel `nutrition_target`.
- **W-C** extended the existing `target` table with `carbs_g` + `fat_g` (migration 025) and shipped `hai target nutrition` as a 4-row macro convenience. Codex round-1 F-IR-01 caught implementation gaps in the round-4 contract draft (idempotency mechanism, atomicity helper, source/status pairing, Python `_VALID_TARGET_TYPE` extension); all addressed.
- **W-D arm-1** suppresses nutrition classification when partial-day + no target, returning `nutrition_status='insufficient_data'` instead of misclassifying breakfast-only intake against the config baseline (the 2026-05-02 morning bug that triggered the original F-AV-04 finding). Snapshot wires W-A signals through `derive_nutrition_signals` so production daily pipelines hit the suppression.
- **W-E** updated the `merge-human-inputs` skill to read the W-A presence block and choose recap-vs-forward-march framing across the 4 in-scope domains. Explicitly does NOT branch on `weigh_in.logged` because W-B (intake weight) is deferred to v0.1.17.

The audit chain ran longer than usual (4 D14 rounds + Phase 0 + 3 D15 IR rounds), driven by the round-4 Phase-0 revises-scope finding (F-PHASE0-01) that recovered `−1d` of W-C scope by reusing the existing `target` table. The IR chain caught real implementation bugs (`add_target` not being atomic, the bandit B608 false positives, the daily-orchestrator F-PV14 bypass, the vacuous test helper, citation drift in source comments). All 9 IR findings (6 round-1 + 2 round-2 + 1 round-3 nit) AGREED + applied.

---

## What didn't ship in v0.1.15 (named-deferrals)

Per the cycle's strategic architecture:

**v0.1.16 (empirical-fix cycle, post-candidate-session):**
- W-2U-FIX-P1 / W-2U-FIX-P2 — whatever the named foreign-user candidate's session surfaces.
- W-EXPLAIN-UX-2 — empirical foreign-user pass over `hai explain`.
- W-FPV14-SYM (conditional) — broader symmetric `--db-path` / `--base-dir` rule, only if the named foreign-user candidate's session surfaces friction.

**v0.1.17 (maintainability + eval consolidation, finishes off v0.1):**
- W-29 cli.py mechanical split (10K-line file → 1 main + 1 shared + 11 handler-group, byte-stable manifest).
- W-30 capabilities-manifest schema-freeze regression test.
- F-PV14-02 (`hai sync purge` surgical-cleanup CLI).
- W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4 (eval substrate from v0.1.14 carry-overs).
- W-B (`hai intake weight` body-comp surface + table + migration).
- W-D arm-2 (partial-day nutrition end-of-day projection, gated on W-C).
- W-C-EQP (small) — EXPLAIN QUERY PLAN stability assertions.

After v0.1.17, v0.1 is structurally complete; v0.2+ moves on to weekly-review (W52) + deterministic-factuality (W58D) + hosted-agent (W57) + the schema-freeze (W-30 final, v0.2.3).

---

## Pivot: publish-first sequencing

The PLAN's pre-pivot Phase 3 W-2U-GATE was a ship-gate (the named foreign-user candidate's session pass = ship to PyPI; fail = hold v0.1.15). Post-IR-close maintainer call: publish v0.1.15 to PyPI as soon as IR closes; the named foreign-user candidate's session is empirical-validation feeding v0.1.16.

The reversal supersedes the round-3 OQ-8 ratification ("no PyPI pre-release"). Rationale: v0.1.16 is already structured as the empirical-fix cycle — that's the supersession mechanism for any P0/P1 from the named foreign-user candidate's session. The PyPI-pollution risk OQ-8 protected against is exactly what v0.1.16 absorbs in days, not cycles. Choosing publish-first makes the named foreign-user candidate's install path realistic (`pip install` from PyPI, like any second user) which strengthens the gate evidence.

If the named foreign-user candidate hits a small + isolated P0, a v0.1.15.1 hotfix may ship (matches the v0.1.12.1 / v0.1.14.1 hotfix pattern).

---

## Lessons + patterns reinforced

1. **Provenance discipline is symmetric.** AGENTS.md "Patterns the cycles have validated" already names provenance discipline as a recurring audit-finding shape. This cycle reinforced that the citation-drift class hits both response docs AND source code comments equally — F-IR-R2-02 caught it in the response triage doc; F-IR-R3-01 caught it in a source rationale comment 1 round later. Lesson: when correcting citations after revisions, grep the entire repo, not just the named surface.

2. **Phase 0 internal sweep saved a parallel-table.** F-PHASE0-01 caught that the original W-C contract proposed building a `nutrition_target` table when the existing `target` table (migration 020, in tree since v0.1.8 W50) was already domain-agnostic and in production use. The sweep pattern — verify on disk before citing in PLAN — would have prevented the misframing in the original `agent_state_visibility_findings.md` F-AV-03 finding too. Lesson: every "new table" proposal in a future PLAN should mandatorily include a check for existing-table-already-supports.

3. **The 5 → 2 → 1-nit IR norm holds at slightly higher absolute counts when the cycle bundles multiple W-ids.** v0.1.15 IR settled at 6 → 2 → 1; the bundling of 6 W-ids in one Phase 1+2 batch increased round-1 finding density. Future cycles with similar W-id counts should budget round-1 = ~5-6, not = 5.

4. **Strategic-architecture calls trump cycle-scope ratifications.** OQ-8's "no PyPI pre-release" was a defensible local decision; the publish-first pivot was a strategic-arc decision that overrode it. Both are honest. Lesson: cycle-scope ratifications (OQ-1..N) are operational defaults; strategic-arc decisions sit above them and may override them at any point with documented rationale.

---

## Verification (at-publish snapshot)

| Gate | Status |
|---|---|
| pytest | 2630 passed, 3 skipped |
| mypy | clean |
| bandit (-ll) | 0 medium/high |
| capabilities markdown diff | clean |
| migration head | 25 |
| pyproject version | 0.1.15 |

---

## Next: the named foreign-user candidate's session

- The named foreign-user candidate installs `pip install health-agent-infra==0.1.15` on the candidate's laptop.
- He runs through morning ritual + intake + `hai today` + agent conversation.
- I (the maintainer) observe-only.
- Recorded transcript at `reporting/plans/v0_1_15/foreign_machine_session_<YYYY-MM-DD>.md`.
- State DB snapshot at `verification/dogfood/foreign_user/state_snapshot/<YYYY-MM-DD>/`.
- Install record at `verification/dogfood/foreign_user/install_record_<YYYY-MM-DD>.json`.

Findings → v0.1.16 PLAN authoring.
