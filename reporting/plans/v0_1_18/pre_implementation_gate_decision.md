# Pre-implementation Gate Decision — v0.1.18

**Date:** 2026-05-06
**Decided by:** Claude (autonomous mode under maintainer ratification)
**HEAD at decision:** `8e762c2` (D14 closure commit)
**Decision:** **OPEN PHASE 1** — implementation proceeds.

---

## §1 Gate inputs

The pre-implementation gate consumes:

1. **D14 plan-audit closure status.** ✅ Settled at round 2, PLAN_COHERENT close-in-place. R1 7 findings + R2 3 findings, all accepted, all revised in lockstep. Settling shape `7 → 3` matches AGENTS.md empirical norm `10 → 5 → 3 → 0`. See `codex_plan_audit_response.md` + `codex_plan_audit_response_response.md` + `codex_plan_audit_round_2_response.md` + `codex_plan_audit_round_2_response_response.md`.
2. **Phase 0 (D11) bug-hunt findings.** See `audit_findings.md`. Three records: F-OB-PRE-01 (the cycle-open absorbed finding → W-OB-7); F-PHASE0-01 (existing init tests don't mock `isatty` — informational, absorbs into W-OB-2 implementation discipline); F-PHASE0-02 (W-OB-5 production code surface broader than test floor — informational, absorbs into W-OB-5 implementation sizing); F-PHASE0-03 (pre-impl baselines clean — not a finding).
3. **Pre-impl baselines.** All clean:
   - `hai capabilities --json`: hai_version 0.1.17, 67 commands, `hai init` 10 flags pre-W-OB-2.
   - 13-persona matrix: 13/13 reach `synthesized` cleanly, 0 findings, 0 crashes.
   - Init/doctor scoped tests: 33/33 passed in 3.56s.
   - Full suite under broader warning gate: 2688 passed, 5 skipped in 80.69s.
   - Schema head: 26 (unchanged from v0.1.17 ship).
4. **Outstanding OQs.** None. All 7 OQs settled at D14 R1.

---

## §2 Gate decision logic

Per AGENTS.md "Pre-implementation gate" (D11):

- **`revises-scope` findings** → loop back to D14. **None present.** F-PHASE0-01 + F-PHASE0-02 are both `informational` — they inform implementation discipline, but the PLAN's contracts already cover them (PLAN §2.B names monkeypatch discipline; PLAN §2.E names "every check that emits hint where the hint maps to a concrete command"). No PLAN revision required.
- **`aborts-cycle` findings** → end cycle. **None present.** No architectural blocker surfaced.
- **All clear** → open Phase 1 implementation.

**Decision:** **OPEN PHASE 1.**

---

## §3 Phase 1 entry conditions

| Condition | Status |
|---|---|
| D14 settled (`PLAN_COHERENT` or close-in-place) | ✅ R2 close-in-place |
| Phase 0 audit_findings consolidated | ✅ F-OB-PRE-01 + F-PHASE0-01..03 |
| No `revises-scope` finding | ✅ |
| No `aborts-cycle` finding | ✅ |
| OQ ratifications complete | ✅ all 7 settled |
| Pre-impl baselines clean (suite + persona matrix + manifest) | ✅ |
| Active repo path verified | ✅ `/Users/domcolligan/health_agent_infra` (per AGENTS.md preamble) |

---

## §4 Phase 1 implementation order

Per PLAN §1.3:

1. **W-OB-1** (README pivot ratification + cross-reference sweep) — independent; lands first.
2. **W-OB-7** (intake-handler migration parity; 8 callers + new `open_connection_with_migrations` helper in `core/state/store.py`) — load-bearing for W-OB-4a's upgrade scenario to validate the no-crash claim.
3. **W-OB-4a** (early-evidence dogfood pass against the W-OB-1 + W-OB-7-shipped tree; upgrade-from-old-DB scenario) — produces `dogfood_findings.md` § "W-OB-4a Phase 1"; informs W-OB-3 prompt content.

Phase 1 closes when W-OB-1 + W-OB-7 commits land + W-OB-4a evidence gate fires (findings file populated).

**Phase 2 entry condition:** Phase 1 closes + W-OB-4a findings absorbed (route to W-OB-3 / W-OB-5 / W-OB-6 as classified).

---

## §5 Risk-acknowledgement at gate-fire

Per PLAN §4 risks register, the following risks remain live going into Phase 1:

- **Risk 1 (W-OB-2 default-flip / pseudo-TTY automation breakage):** mitigated by 5-case test surface + 2 opt-out paths + CHANGELOG callout. F-PHASE0-01 reinforces the conftest.py fixture discipline.
- **Risk 3 (W-OB-4a synthetic-old-DB doesn't mimic real users):** mitigated by OQ-3 priority order (snapshot → install old wheel → targeted rollback last resort with documented mutation).
- **Risk 8 (W-OB-7 scope creep):** F-PHASE0-02 confirms intake.py shape matches PLAN expectation; no exotic connection lifecycle observed at the 8 handler sites.
- **Risk 9 (dogfood reveals architecture-level finding):** unmitigated by design — cycle-abort path reserved per AGENTS.md D11 if it fires.

None of these risks are gating; all have named mitigations.

---

## §6 Implementation discipline reminders

For Phase 1 + Phase 2 commits:

1. **Atomic per-W-id commits** per PLAN §1.3 ("Recommended commit cadence: atomic per-W-id commits").
2. **Provenance discipline** per AGENTS.md "Patterns the cycles have validated" — verify file paths + line numbers + function names + exact strings before citing them in commit messages or RELEASE_PROOF.
3. **Summary-surface sweep** per AGENTS.md — when a W-id ships partial, sweep PLAN §1/§2/§3/§6 + RELEASE_PROOF + REPORT + CARRY_OVER + tactical plan + CHANGELOG in lockstep.
4. **D12 coercer use** for any threshold reads (none expected in v0.1.18 scope, but reflexive discipline).
5. **Run state before asking the user** — applies to W-OB-3 prompt review (informed by W-OB-4a findings, not maintainer guess).
6. **F-PHASE0-01 conftest fixture** — W-OB-2 commit lands the existing-init-test isatty mock alongside the cmd_init logic change.

---

## §7 Files this gate decision references

- `reporting/plans/v0_1_18/PLAN.md` — the artifact being opened for implementation.
- `reporting/plans/v0_1_18/audit_findings.md` — F-OB-PRE-01 + F-PHASE0-01/02/03.
- `reporting/plans/v0_1_18/codex_plan_audit_*.md` — full D14 audit chain.
- `AGENTS.md` "Settled Decisions" D11 + D14 + D15 — gate procedure source.
- `/tmp/persona_v0_1_18_baseline/summary.json` — 13-persona matrix baseline output.

---

## §8 Decision

**OPEN PHASE 1.**

Phase 1 implementation proceeds with W-OB-1 → W-OB-7 → W-OB-4a in order. Maintainer may interrupt at any commit boundary; otherwise, autonomous mode runs the implementation under the discipline reminders in §6.
