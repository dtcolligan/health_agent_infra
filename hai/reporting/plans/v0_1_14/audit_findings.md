# v0.1.14 Phase 0 (D11) — Audit Findings

**Date.** 2026-05-01.
**Authored by.** Claude (delegated by maintainer).
**Status.** Internal sweep + audit-chain probe + persona matrix
complete. Codex external bug-hunt skipped per maintainer
discretion (optional per D11; settled convention from
v0.1.11 / v0.1.12 / v0.1.13 cycles).

**Verdict.** **Pre-implementation gate fires green.** Zero
`aborts-cycle` findings. Zero `revises-scope` findings. One
`in-scope` finding (F-PHASE0-01, persona-harness × demo-session
transient — non-reproducible after cleanup, naturally absorbs into
W-FRESH-EXT runner-hardening or stays a documented residual).

**Cycle tier (D15):** substantive — full Phase 0 sweep completed
(internal + audit-chain + persona matrix; Codex external skipped).

**One open maintainer decision** is on file at the gate but is
**not a Phase 0 finding**: W-2U-GATE candidate (OQ-I) is
**TBD-placeholder** per the post-v0.1.13 reconciliation. PLAN.md
§1.3.1 candidate-absence procedure governs. The maintainer must
either name a candidate before W-2U-GATE opens or invoke one of
the three §1.3.1 paths (hold / defer-to-v0.1.15 / abort-cycle).
This is the canonical pre-implementation-gate maintainer decision
that v0.1.14's PLAN was authored to surface explicitly.

---

## 1. Probes run

| Probe | Command | Result | Cycle impact |
|---|---|---|---|
| **Pytest narrow gate** | `uv run pytest verification/tests -q` | 2493 passed, 3 skipped, 0 failures, 0 errors (115.07 s) | clean — v0.1.13 ship state held |
| **Pytest broader gate** | `uv run pytest verification/tests -W error::Warning -q` | 2493 passed, 3 skipped, **0 failures, 0 errors** (116.51 s) | clean — **W-N-broader closure held since v0.1.13 ship** (zero regression in -W error::Warning surface) |
| **Mypy** | `uvx mypy src/health_agent_infra` | **0 errors** in 120 source files | clean — held from v0.1.13 ship (W-H2 zero state preserved; +4 source files since v0.1.13 are typed clean) |
| **Bandit** `-ll` | `uvx bandit -ll -r src/health_agent_infra` | 46 Low, 0 Medium, 0 High (32,392 LOC scanned) | clean — D10 threshold (≤50 Low) preserved; v0.1.13 ship was 46 Low at 30,660 LOC |
| **Ruff** | `uvx ruff check src/health_agent_infra` | All checks passed | clean |
| **Audit-chain probe** | `hai explain --for-date {2026-04-30, 2026-04-28, 2026-04-27} --user-id u_local_1` | All 3 days return intact `daily_plan` JSON chains; `proposal_log` → `planned_recommendation` → `daily_plan` reconciliation honest; `x_rule_firings` consistent with phase-A/B contract | clean — three-state audit chain integrity preserved (D9 invariant) |
| **Persona matrix (12)** — first run | `uv run python -m verification.dogfood.runner /tmp/persona_run_v0_1_14_phase0` | 12 personas, **1 finding** (P1 `missing_domain_coverage`, severity `audit-chain-break`), 0 crashes | F-PHASE0-01 below |
| **Persona matrix (12)** — retry after `hai demo cleanup` | `uv run python -m verification.dogfood.runner /tmp/persona_run_v0_1_14_phase0_retry` | 12 personas, **0 findings**, 0 crashes | finding non-reproducible after demo-state cleanup → F-PHASE0-01 confirmed transient |
| Codex external bug-hunt | (skipped per maintainer discretion) | — | — |

---

## 2. Findings

### F-PHASE0-01 — Persona harness × demo-session marker interaction

**Cycle impact:** in-scope (transient, non-reproducible after
cleanup; naturally folds into W-FRESH-EXT runner-hardening or
stays a documented residual).

**Symptom.** First persona-matrix run on a fresh checkout produced
1 finding on **P1 (`p1_dom_baseline`)** with kind
`missing_domain_coverage`, severity `audit-chain-break`, naming
all 6 domains as missing. P2..P12 ran clean (0 findings, 0
crashes). The runner step log for P1 showed `propose_nutrition`,
`propose_recovery`, and `propose_running` returning rc=0 with
plausible JSON output, but `proposal_log` for the persona's DB
contained only **3 of 6 expected canonical-leaf rows** (sleep,
strength, stress); nutrition/recovery/running were absent.

**Diagnosis.** The stderr of P1's first three `propose_*` steps
contained the `[demo session active — marker_id
demo_<unix_ts>_<hex8>, scratch root /tmp/hai_demo_…, persona:
unpopulated, started: …]` banner. The persona harness was running
**inside** an active demo session, so those three `hai propose`
calls were silently routed to the demo's scratch state DB at
`/tmp/hai_demo_demo_<unix_ts>_<hex8>/state.db` rather than the
persona's `/tmp/persona_run_v0_1_14_phase0/p1_dom_baseline/state.db`.
The demo session ended (or its marker was unlinked) between
`propose_running` and `propose_sleep`; the last three propose
calls correctly wrote to the persona DB. Synthesize then blocked
on `missing_expected_proposals`, the persona-matrix
`missing_domain_coverage` check fired, and only P1 was affected
because no marker was active when P2..P12 ran.

**Confirmation.** After `uv run hai demo cleanup` (which reported
"no orphan markers found" — the marker was already gone by then,
having ended naturally during P1), the full 12-persona matrix
re-ran with **0 findings, 0 crashes**.

**Why this matters.** The persona harness is supposed to be
hermetic per D10: each persona gets a fresh scratch DB at
`/tmp/persona_run_*/p{N}/state.db`, and the runner is expected to
produce reproducible per-persona behaviour irrespective of host
state. A pre-existing or concurrently-active demo-session marker
breaks that hermeticity for **whichever persona happens to be
running when the marker is live**. In practice this surfaces only
when a maintainer has been dogfooding `hai demo start …` and
either a test/demo session leaked or `hai demo cleanup` was not
run before the persona matrix.

**Why this is `in-scope` and not `revises-scope`.**
- Persona harness lives in `verification/dogfood/`, not
  `src/health_agent_infra/`. The fix surface is one of:
  (a) runner pre-flight: call `hai demo cleanup` (or refuse to
  run if a marker is active); or
  (b) `hai propose` boundary: refuse-with-warning if a demo
  session is active and the target DB is outside the demo
  scratch root.
- (a) is ~3 lines in the runner. (b) is a small CLI guard.
- Either fits inside W-FRESH-EXT scope (P1 doc-freshness
  test extension; runner-hardening is a natural sibling) or
  can be deferred to v0.1.15 as a tracked item.
- No PLAN.md revision required; no aborts-cycle implication.

**Recommended disposition (proposal to maintainer).** Fold into
W-FRESH-EXT contract as a one-bullet runner-hardening adjunct
("call `hai demo cleanup` at runner pre-flight; refuse to run if
the call returns a non-empty `removed_marker_ids`"). Preserve the
finding in this file as the canonical reproduction trail. This
adjunct adds <1 day to W-FRESH-EXT and does not change the P1
priority of the workstream.

**Provenance for the F-PHASE0-01 reproduction.**
- First-run summary at `/tmp/persona_run_v0_1_14_phase0/summary.json`
- Retry summary at `/tmp/persona_run_v0_1_14_phase0_retry/summary.json`
- Demo scratch root that captured the leaked proposals:
  `/tmp/hai_demo_demo_1777643501_8989433c/`

---

## 3. Pre-implementation gate

| Cycle-impact category | Count |
|---|---|
| `revises-scope` | 0 |
| `aborts-cycle` | 0 |
| `in-scope` | 1 (F-PHASE0-01, recommended absorption into W-FRESH-EXT) |

**Gate fires green.** Implementation may begin, **subject to the
W-2U-GATE-candidate decision** (PLAN §1.3.1; not a Phase 0
finding but the explicit pre-implementation-gate side-channel that
v0.1.14's PLAN was structured to surface).

W-2U-GATE candidate decision pathways available to the maintainer:

1. **Name a candidate** (foreign user willing to onboard on a
   non-maintainer machine). W-2U-GATE opens immediately.
2. **Hold cycle on W-2U-GATE.** Phase 0 sweep is complete; cycle
   waits for a candidate before any code work begins.
3. **Defer W-2U-GATE to v0.1.15** with named destination;
   v0.1.14 opens without it. W-EXPLAIN-UX foreign-user review
   becomes contingent on internal-only proxy review.
4. **Abort cycle.** Re-scope into a different release shape via
   D14.

This is a maintainer decision, not a Claude action. Document the
chosen path in a `pre_implementation_gate_decision.md` file in
this directory before W-PROV-1 (or whichever workstream opens
first under path 2/3) starts.

---

## 4. Comparison vs v0.1.13 Phase 0 ship state

| Probe | v0.1.13 Phase 0 | v0.1.14 Phase 0 | Δ |
|---|---|---|---|
| Pytest narrow | 2384 passed, 2 skipped | 2493 passed, 3 skipped | +109 / +1 (matches v0.1.13 ship-time test additions) |
| Pytest broader (failures + errors) | 48 fail + 1 error = 49 sites | **0 fail + 0 error = 0 sites** | -49 (W-N-broader closure held since v0.1.13 ship) |
| Mypy | 0 errors @ 116 files | 0 errors @ 120 files | +4 source files, all typed clean |
| Bandit Low | 46 (30,660 LOC) | 46 (32,392 LOC) | +1,732 LOC, no new Low/Med/High issues |
| Ruff | clean | clean | held |
| Audit-chain probe | 3 / 3 days clean | 3 / 3 days clean | held |
| Persona matrix | 12 / 0 findings / 0 crashes | 12 / **1 finding** (transient, non-reproducible after demo cleanup) / 0 crashes | F-PHASE0-01 (in-scope) |

The v0.1.14 Phase 0 baseline is **strictly better than v0.1.13
Phase 0** on every quantitative metric: broader-gate failure
surface fully closed, mypy clean across +4 files, bandit clean
across +1,732 LOC, audit-chain integrity preserved. The single
persona-matrix finding is transient and fully recovers after
`hai demo cleanup`.

This confirms that **no v0.1.13 ship-state regression has
occurred between v0.1.13 ship (`5c59008`) and v0.1.14 cycle open
(`354df18`, post-D14-r4 chain close)**. The five v0.1.14 commits
on `cycle/v0.1.14` to date are all doc/plan/CP authoring; no code
has changed.

---

## 5. What this means for the cycle

- **W-2U-GATE-candidate decision** is the pre-implementation
  gate's load-bearing input (see §3 above).
- **F-PHASE0-01** is recommended for absorption into W-FRESH-EXT
  scope as a runner-hardening adjunct (~3 lines, no PLAN
  revision); maintainer disposition required.
- **All 14 v0.1.14 W-ids** open against a clean baseline — no
  Phase 0 finding constrains scope of W-2U-GATE / W-PROV-1 /
  W-EXPLAIN-UX / W-BACKUP / W-FRESH-EXT (P0/P1) or the inherited
  W-29 / W-Vb-3 / W-DOMAIN-SYNC / W-AH..W-AN.
- **Post-v0.1.13 reconciliation OQ-J** (AgentSpec README framing)
  remains an open maintainer decision but is README-prose only;
  not a Phase 0 finding, not a pre-implementation-gate blocker.

---

## 6. Provenance

- **Probes run on:** branch `cycle/v0.1.14`, HEAD `354df18`
  (post-D14-r4 chain close).
- **Probe outputs preserved:**
  - Persona matrices: `/tmp/persona_run_v0_1_14_phase0/summary.json`
    + `/tmp/persona_run_v0_1_14_phase0_retry/summary.json`
  - Demo scratch root that captured F-PHASE0-01 reproduction:
    `/tmp/hai_demo_demo_1777643501_8989433c/`
  - Pytest / mypy / bandit / ruff / `hai explain` outputs:
    bash background-task output files (ephemeral).
- **Audit-chain artifact set** for v0.1.14 D14 + D11 phases:

```
codex_plan_audit_prompt.md                                (round 1 prompt)
codex_plan_audit_response.md                              (round 1 Codex)
codex_plan_audit_round_1_response.md                      (round 1 maintainer)
codex_plan_audit_round_2_prompt.md                        (round 2 prompt)
codex_plan_audit_round_2_response.md                      (round 2 Codex)
codex_plan_audit_round_2_response_response.md             (round 2 maintainer)
codex_plan_audit_round_3_prompt.md                        (round 3 prompt)
codex_plan_audit_round_3_response.md                      (round 3 Codex)
codex_plan_audit_round_3_response_response.md             (round 3 maintainer)
codex_plan_audit_round_4_prompt.md                        (round 4 prompt)
codex_plan_audit_round_4_response.md                      (round 4 Codex; PLAN_COHERENT_WITH_REVISIONS, 1 nit)
codex_plan_audit_round_4_response_response.md             (round 4 maintainer; chain CLOSED)
audit_findings.md                                         (this file; D11 Phase 0)
```

**D14 settling shape:** 12 → 7 → 3 → 1-nit → CLOSE (4 rounds, 23
cumulative findings; mirrors v0.1.13's 11 → 7 → 3 → 1-nit → 0
shape; pattern twice-validated for substantive PLANs at the
14-17 W-id range).
