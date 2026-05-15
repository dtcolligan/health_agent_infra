# RELEASE_PROOF — v0.1.15

**Tier (D15):** **substantive** — W-2U-GATE foreign-user gate cycle + W-C state-model edit (`target` table CHECK extension via migration 025) + W-GYM-SETID schema-data migration (024) + F-PV14-01 audit-chain edit. Per AGENTS.md "(D15, v0.1.12) Cycle-weight tiering": ≥3 governance/state-model/audit-chain edits → substantive.

**Theme:** Make the package usable for a non-maintainer on a foreign machine. Ship the v0.1.15 wheel to PyPI; the named foreign-user candidate installs `pip install health-agent-infra==0.1.15` and runs the recorded gate session as empirical-validation feeding v0.1.16.

**Released:** 2026-05-03 evening.

---

## §1 — Workstream completion

| W-id | Status | Commit | Test surface |
|---|---|---|---|
| W-GYM-SETID | shipped | `485bae7` | 5 acceptance tests; multi-exercise fixture; migration 024; supersession chains preserved |
| F-PV14-01 | shipped | `df44cb5` (+ `9e113b4` IR-r1 + `48eb3e2` IR-r2) | 11 acceptance tests across `hai pull` + `hai daily` (centralised guard `_f_pv14_csv_canonical_guard` per IR round-1 F-IR-02); capabilities source_type tagging; >48h sync.last vs for_date WARN |
| W-A | shipped | `77ecb3c` (+ `9e113b4` thresholds-config + `ac2d1fe` IR-r3 nit) | 13 acceptance tests; `present` block + `is_partial_day` (thresholds-configurable per IR round-1 F-IR-03) + `target_status` enum reading existing `target` table per round-4 F-PHASE0-01 Option A |
| W-C | shipped | `b47552c` (+ `9e113b4` IR-r1 byte-stable preservation test) | 10 acceptance tests; migration 025 (extends `target_type` CHECK + Python `_VALID_TARGET_TYPE`); `add_targets_atomic` helper; `hai target nutrition` 4-row macro convenience; W57 source/status pairing; natural-key idempotency |
| W-D arm-1 | shipped | `70d4f76` (+ `9e113b4` IR-r1 enum docs) | 6 acceptance tests; nutrition classifier suppresses to `nutrition_status='insufficient_data'` when `is_partial_day=True && target_status in (absent, unavailable)`; snapshot wires W-A signals through `derive_nutrition_signals`; F-IR-06 docstring + skill enum updates |
| W-E | shipped | `0fd5179` | 4 acceptance tests; `merge-human-inputs` skill consumes W-A `present` block (recap-vs-forward-march framing across 4 domains); explicit no-branch-on-`weigh_in.logged` per W-B-deferred-to-v0.1.17 |
| W-2U-GATE | **post-publish empirical-validation** (publish-first pivot) | post-RELEASE_PROOF | The named foreign-user candidate's recorded session against the published v0.1.15; findings feed v0.1.16 |

**6 of 7 W-ids shipped at IR close.** W-2U-GATE was reframed from ship-gate to empirical-validation per the publish-first pivot (PLAN §2.G "Why the reversal"; see §5 below).

---

## §2 — Ship-gate verification

| Gate | Status | Evidence |
|---|---|---|
| Full pytest suite (narrow + broader warning gates) | **2630 passed, 3 skipped** | `uv run pytest verification/tests -q` |
| `uvx mypy src/health_agent_infra` | **clean** | "Success: no issues found in 128 source files" |
| `uvx bandit -ll -r src/health_agent_infra` | **clean** | 0 medium/high (was 2 medium B608 pre-IR-r1; F-IR-01 closed) |
| `uv run hai capabilities --json` round-trip stable | clean | 60 commands; manifest schema unchanged |
| `uv run hai capabilities --markdown` matches `reporting/docs/agent_cli_contract.md` | clean | `diff` empty |
| Persona matrix (P1..P13) | **13/13 clean** | 0 findings, 0 crashes; ran at Phase 0 |
| AGENTS.md D124-135 W-29 destination | **scheduled v0.1.17** | unchanged from D14 close |
| AUDIT.md entry | landed | this cycle |
| CHANGELOG entry | landed | this cycle |

---

## §3 — Migration head

- Pre-cycle: 23 (`023_source_row_locator.sql`, v0.1.14 W-PROV-1).
- Post-cycle: **25**.
  - 024: `024_gym_set_id_with_exercise_slug.sql` (W-GYM-SETID prospective fix; in-place UPDATE preserving custom-id correction rows).
  - 025: `025_target_macros_extension.sql` (W-C `target_type` CHECK extension via recreate-and-copy; preserves existing rows byte-stable).

---

## §4 — Audit-chain provenance

| Chain stage | Rounds | Findings | Settled-at |
|---|---|---|---|
| D14 plan-audit | 4 | 12 → 7 → 3 → 2 (close-in-place at round 4 post-Phase-0 F-PHASE0-01 Option A revision) | round 4, AGENTS.md halving-norm met |
| Phase 0 (D11) bug-hunt | 1 sweep | 1 revises-scope (F-PHASE0-01) + 3 nits + persona matrix 13/13 clean | gate-decision recorded; F-PHASE0-01 Option A applied via D14 round 4 |
| D15 IR | 3 | 6 → 2 → 1 (SHIP_WITH_NOTES at round 3) | AGENTS.md `5 → 2 → 1-nit` empirical norm met |

**Total audit surface:** 4 D14 rounds + Phase 0 + 3 D15 IR rounds + pre-implementation gate. Within AGENTS.md substantive-cycle norm.

---

## §5 — Publish-first pivot (post-IR-close)

D15 IR closed SHIP_WITH_NOTES. The pre-pivot sequencing (PLAN §2.G + §6) had Phase 3 W-2U-GATE recorded session firing as a SHIP gate, with PyPI publish gated on the gate session passing.

**Maintainer call (2026-05-03 evening, post-IR-close):** v0.1.15 publishes to PyPI BEFORE Phase 3. The named foreign-user candidate's session reframes from ship-gate to empirical-validation feeding v0.1.16. The "v0.1.15 = ready for second user; v0.1.16 = bug-fix iteration of whatever the run finds; v0.1.17 = hardening leftover" model is the strategic architecture for the v0.1.x arc; PyPI publish is the act that makes v0.1.15 actually accessible to a second user.

**OQ-8 reversal.** D14 round 3's OQ-8 ratification ("commit SHA only, no PyPI pre-release") was overridden post-IR-close. The PyPI-pollution risk OQ-8 protected against (immutable PyPI version with potential P0) is the exact risk v0.1.16 is structured to absorb in days, not cycles. Per the AGENTS.md "Settled Decisions" pattern: this is a maintainer-scope decision, documented here for audit-chain queryability; not a settled-decision reversal because OQ-8 was a cycle-scope ratification, not a D-entry.

**Hotfix path.** If the named foreign-user candidate's session reveals a small + isolated P0, a v0.1.15.1 hotfix may ship (matches the v0.1.12.1 / v0.1.14.1 hotfix pattern). Larger findings feed v0.1.16.

---

## §6 — Out of scope (named-deferrals to future cycles)

Per cycle architecture:

- **v0.1.16 (empirical-by-design):**
  - W-2U-FIX-P1 (any P1 named-deferred from the named foreign-user candidate's recorded session)
  - W-2U-FIX-P2 (any P2 named-deferred)
  - W-EXPLAIN-UX-2 (foreign-user pass over `hai explain`)
  - **W-FPV14-SYM (conditional)** — broader F-PV14-01 symmetry rule for asymmetric `--db-path` / `--base-dir` overrides; lands only if the named foreign-user candidate's session surfaces friction. Per IR round-1 F-IR-02 named-defer + IR round-2 F-IR-R2-02 durable-surface placement.
- **v0.1.17 (maintainability + eval consolidation):**
  - W-29 cli.py mechanical split + W-30 regression test (per AGENTS.md D124-135)
  - W-AH-2 / W-AI-2 / W-AM-2 / W-Vb-4 (eval substrate from v0.1.14 carry-overs)
  - F-PV14-02 (`hai sync purge` surgical-cleanup CLI)
  - W-B (`hai intake weight` body-comp surface + `body_comp` table)
  - W-D arm-2 (partial-day nutrition end-of-day projection, gated on W-C)
  - **W-C-EQP (small)** — EXPLAIN QUERY PLAN stability assertions for the W-A active-window query against `target` post-migration 025. Per IR round-1 F-IR-04 named-defer + IR round-2 F-IR-R2-02 durable-surface placement.

All deferrals carry destination cycles + sources; future cycle authors find them via the v0.1.16 + v0.1.17 README §scope tables.

---

## §7 — Maintainer pre-publish recovery procedure (per PLAN §4 risk 3)

Before the named foreign-user candidate's gate session, the maintainer's local state needs the W-GYM-SETID JSONL recovery (the production leg+back session has 8 dropped sets recoverable only via reproject):

```bash
hai backup --dest ~/hai-backup-pre-w-gym-setid-recovery.tar.gz
hai state migrate                              # apply migrations 024 + 025
hai state reproject --base-dir ~/.health_agent --cascade-synthesis
hai synthesize --as-of $(date -u +%F) --user-id u_local_1
```

Maintainer-only path; the named foreign-user candidate starts from a fresh DB so this does not apply to the candidate.

---

## §8 — Provenance + signatures

- **Cycle dir:** `reporting/plans/v0_1_15/`
- **Final commit before publish:** see git log.
- **D14 close:** `f593b5a` (round 4 closed in-place).
- **Phase 1+2 implementation:** `485bae7..0fd5179` (6 atomic commits).
- **D15 IR fixes:** `9e113b4` (round 1) → `48eb3e2` (round 2) → `ac2d1fe` (round 3 nit).
- **Publish-first pivot:** this commit (PLAN §2.G + §6 + §9 reframing + RELEASE_PROOF + REPORT + version bump).

**Settled decisions touched:** none. F-PHASE0-01 Option A revision was scope-recovery; OQ-8 reversal is cycle-scope, not D-entry-scope.

**Settled decisions deferred (per AGENTS.md D124-135):** W-29 cli.py split → v0.1.17. Capabilities-manifest schema freeze → v0.2.3.
