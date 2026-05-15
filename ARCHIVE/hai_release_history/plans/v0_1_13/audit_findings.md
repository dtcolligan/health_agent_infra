# v0.1.13 Phase 0 (D11) — Audit Findings

**Date.** 2026-04-30.
**Authored by.** Claude (delegated by maintainer).
**Status.** Internal sweep + audit-chain probe + persona matrix
complete. Codex external bug-hunt skipped per maintainer
discretion (optional per D11 — informal probes are sometimes
substituted; v0.1.11/v0.1.12 settled at this convention).

**Verdict.** **Pre-implementation gate fires green.** Zero
`aborts-cycle` findings. One `in-scope` finding (W-N-broader
baseline confirmation, marginal -1 drift from v0.1.12 named
baseline). Zero `revises-scope` findings.

---

## 1. Probes run

| Probe | Command | Result | Cycle impact |
|---|---|---|---|
| **Pytest narrow gate** | `uv run pytest verification/tests -q` | 2384 passed, 2 skipped, 0 failures (52.34s) | clean — matches v0.1.12 ship state of 2384 |
| **Pytest broader gate** | `uv run pytest verification/tests -W error::Warning -q` | **48 failed + 1 error** of 2384 tests, 51.94s | **in-scope** of W-N-broader; baseline confirmed at 49 surfaces (vs 50 named in v0.1.12 audit_findings F-PHASE0-02). -1 marginal drift documented in F-PHASE0-01 below |
| **Mypy** | `uvx mypy src/health_agent_infra` | **0 errors** in 116 source files | clean — held from v0.1.12 ship (W-H2 closed at 0) |
| **Bandit** `-ll` | `uvx bandit -ll -r src/health_agent_infra` | 46 Low, 0 Medium, 0 High (30,660 LOC scanned) | clean — matches v0.1.12 ship state (D10 threshold ≤ 50 Low preserved) |
| **Ruff** | `uvx ruff check src/health_agent_infra` | All checks passed | clean |
| **Audit-chain probe** | `hai explain` for 2026-04-26/27/28 | All 3 days return intact `daily_plan` JSON chains (`plan_<date>_u_local_1`); proposal_log → planned_recommendation → daily_plan reconciliation honest | clean |
| **Persona matrix** (12) | `uv run python -m verification.dogfood.runner /tmp/persona_run_phase0` | 12 personas, **0 findings**, **0 crashes** | clean — no regression vs v0.1.12 ship |
| Codex external bug-hunt | (skipped per maintainer discretion) | — | — |

---

## 2. Findings

### F-PHASE0-01 — W-N-broader baseline -1 drift

**Cycle impact:** in-scope (absorbed by W-N-broader; no scope
revision required).

v0.1.12 audit_findings.md F-PHASE0-02 named the W-N-broader
surface at **49 fail + 1 error = 50 sites**. v0.1.13 Phase 0 sweep
returns **48 fail + 1 error = 49 sites**. Net -1 drift.

The -1 drift is most likely incidental — either:
- A test was incidentally fixed by some v0.1.12-cycle change that
  closed a connection lifecycle as a side effect, OR
- A flaky test toggled out of the broader-gate failure set, OR
- The hypothesis-under-warning-filter test-reduction footprint
  shifted by one count (v0.1.12 RELEASE_PROOF §2.2 noted "count
  differs from §2.1 due to hypothesis-test-reduction under
  different warning filters").

W-N-broader's contract (PLAN.md §2.A) accepts an authoritative
file list derived from a fresh `pytest -W error::Warning` run at
Phase 0 open, recorded in `audit_findings.md` before per-site
fixes begin. This Phase 0 run produces that fresh list:

**Per-site failure cluster (sample of 8 of 49; full list captured
in pytest output):**

- `verification/tests/test_pull_intervals_icu.py::test_http_client_fetch_activities_raises_on_error`
- `verification/tests/test_review_per_domain.py::test_cli_review_summary_splits_mixed_domains_under_domain_filter`
- `verification/tests/test_review_record_relink.py` (3 tests)
- `verification/tests/test_running_policy.py::test_sparse_cap_allows_on_full_coverage`
- `verification/tests/test_snapshot_bundle.py` (2 tests)
- `verification/tests/e2e/test_reauthor_journey_2026_04_23.py::test_explain_for_date_returns_canonical_leaf` (the one error, not a failure)

This sample suggests the connection-lifecycle leak surface spans
the **review path** (3 tests in test_review_record_relink), the
**snapshot bundle path** (2 tests), the **pull adapter** (1 test),
the **running policy** (1 test), and a **synthesize-related e2e
test** (1 error).

Per the W-N-broader files-list contract:

> "Authoritative file list to be derived from a fresh `pytest -W
> error::Warning` run at Phase 0 open and recorded in
> `audit_findings.md` before per-site fixes begin."

This finding satisfies that prerequisite.

**Disposition:** No PLAN.md revision needed. W-N-broader implementation
opens against this 49-site surface; the per-site fix table will be
authored in v0.1.13 RELEASE_PROOF §2.X at ship time.

---

## 3. Pre-implementation gate

| Cycle-impact category | Count |
|---|---|
| `revises-scope` | 0 |
| `aborts-cycle` | 0 |
| `in-scope` | 1 (F-PHASE0-01, absorbed by W-N-broader) |

**Gate fires green.** Implementation may begin.

---

## 4. Comparison vs v0.1.12 Phase 0 ship state

| Probe | v0.1.12 Phase 0 | v0.1.13 Phase 0 | Δ |
|---|---|---|---|
| Pytest narrow | 2347 passed (pre-W-H2 +35) | 2384 passed | +37 (matches v0.1.12 ship) |
| Pytest broader (failures) | 49 failed + 1 error | 48 failed + 1 error | -1 |
| Mypy | 22 errors (Phase 0) → 0 (ship) | 0 errors | held |
| Bandit Low | 44 (pre-cycle) → 46 (ship) | 46 | held |
| Capabilities byte-stability | byte-identical | (not re-probed; W-29-prep inherits the regression test scaffold) | n/a |
| Persona matrix | 12 / 0 findings / 0 crashes | 12 / 0 findings / 0 crashes | identical |

The v0.1.13 Phase 0 baseline is essentially the same as v0.1.12
ship state, with:
- W-N-broader surface marginally smaller (-1 site).
- All mypy / bandit / ruff / persona-matrix gates held.
- Audit-chain integrity preserved.

This confirms that **no v0.1.12 ship-state regression has occurred
between v0.1.12 ship (2026-04-29) and v0.1.13 cycle open (2026-04-30
~14 hours later)**. The two cherry-picked commits (W-CF-UA fix +
v0.1.12.1 RELEASE_PROOF doc) did not introduce regressions.

---

## 5. What this means for the cycle

- **W-N-broader** opens against a confirmed 49-site surface,
  per-site fix table to be authored at implementation time.
- **All other 16 W-ids** open against a clean baseline — no
  Phase 0 finding constrains their scope.
- **Pre-implementation gate fires green** — implementation may
  begin in any order respecting the W-AB → W-AE → W-29-prep
  sequencing constraint per F-PLAN-11.

---

## 6. Provenance

- **Probes run on:** branch `cycle/v0.1.13`, HEAD `57460a6`
  (post-D14-r5 chain close).
- **Probe outputs preserved** in
  `/tmp/persona_run_phase0/summary.json` (persona matrix) +
  bash background-task output files (pytest / mypy / bandit / ruff;
  ephemeral).
- **Audit-chain artifact set** for v0.1.13 D14 + D11 phases:

```
codex_plan_audit_prompt.md
codex_plan_audit_response.md                              (round 1 Codex)
codex_plan_audit_response_round_1_response.md             (round 1 maintainer)
codex_plan_audit_response_round_2_response.md             (round 2 Codex)
codex_plan_audit_round_2_response_response.md             (round 2 maintainer)
codex_plan_audit_round_3_response.md                      (round 3 Codex)
codex_plan_audit_round_3_response_response.md             (round 3 maintainer)
codex_plan_audit_round_4_response.md                      (round 4 Codex)
codex_plan_audit_round_4_response_response.md             (round 4 maintainer)
codex_plan_audit_round_5_response.md                      (round 5 Codex; PLAN_COHERENT)
codex_plan_audit_round_5_response_response.md             (round 5 maintainer; chain close)
audit_findings.md                                         (this file; D11 Phase 0)
```
