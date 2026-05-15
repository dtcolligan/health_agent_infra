# v0.1.14 Cycle Report — Eval substrate + provenance + recovery path

**Cycle tier (D15):** substantive (13 W-ids at PLAN open; closed
8, partial-closed 3, deferred 2).
**Branch.** `cycle/v0.1.14` at `16d2cd0`, 8 commits ahead of `main`.
**Date.** 2026-05-01.

## 1. Theme

> Build the eval substrate for v0.2.0's W58 factuality gate; land
> the source-row provenance type that v0.2.0 W52 will require;
> ship the second-user recovery path (`hai backup` /
> `hai restore` / `hai export`); close v0.1.13-deferred mechanical
> workstreams. Foreign-machine onboarding empirical proof
> (W-2U-GATE) deferred to v0.1.15 at the pre-implementation gate
> per §1.3.1 path 2 (no candidate on file).

The v0.2.0 design risk reduction is the load-bearing motivation:
v0.2.0 W52 weekly review consumes W-PROV-1 source-row locators +
W-AL `CalibrationReport` schema; v0.2.2 W58J consumes W-AJ
`JudgeHarness` ABC. Building those primitives in v0.1.14 means
v0.2.0's PLAN can be authored without "what shape do we land
provenance in?" reserving design risk.

## 2. What shipped

### 2.1 Highlights

- **W-PROV-1 source-row locator type** — typed pointer back to
  evidence rows (`{table, pk, column, row_version}`); whitelist-
  validated; recovery R6 demo end-to-end (proposal → recommendation
  → `hai explain` JSON + markdown → resolve). The type is
  pre-staged for v0.2.0 W52 + W58D to consume without re-design.
- **W-BACKUP recovery path** — `hai backup` / `hai restore` /
  `hai export` close the second-user blind-spot identified in
  the post-v0.1.13 strategic research. Schema-mismatch refusal
  is the load-bearing safety check; `reporting/docs/recovery.md`
  documents 5 disaster scenarios.
- **W-EXPLAIN-UX maintainer-substitute review** — 8 findings
  filed in `explain_ux_review_2026_05.md`, including 6 v0.2.0 W52
  prose obligations and an explicit
  `carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass`
  section. P13 (low-domain-knowledge) persona registered in the
  matrix.
- **W-AJ + W-AL eval substrate scaffold** — judge harness
  invocation interface + calibration eval schema (FActScore-aware)
  with stub decomposer. v0.2.2 W58J's real model invocation and
  v0.2.0 W-FACT-ATOM's semantic decomposer plug into this
  surface without breaking callers.
- **W-AI judge-adversarial fixture corpus** — 30 fixtures (10
  each: prompt_injection / source_conflict / bias_probe). Pinned
  shape; v0.2.2 W58J consumes for the bias-aware judge.
- **W-DOMAIN-SYNC contract test** — pins canonical six across
  the runtime; documents the legitimate `gym↔strength` snapshot-
  read alias and `_DOMAIN_ACTION_REGISTRY` Phase-A-only exemption.
- **W-FRESH-EXT runner pre-flight (F-PHASE0-01 absorption)** — the
  persona harness now refuses to run with an active demo-session
  marker, preventing the v0.1.14 Phase 0 transient from
  recurring.

### 2.2 Test surface delta

`2493 → 2552 passed (+59)`. Net additions:

- `test_source_row_locator_recovery.py` (21 tests)
- `test_judge_harness.py` (13 tests)
- `test_judge_adversarial_fixtures.py` (7 tests)
- `test_backup_restore_roundtrip.py` (8 tests)
- `test_domain_sync_contract.py` (8 tests)

All ship gates green: pytest narrow (2552/3/0), pytest broader
(0 fail / 0 error since v0.1.13 ship), mypy 0 @ 127 files,
bandit 46 Low / 0 Med / 0 High, ruff clean, capabilities byte-
stable post-snapshot regen, agent_cli_contract.md regenerated.

## 3. What partial-closed honestly

Per AGENTS.md "Honest partial-closure naming" pattern:

- **W-29 cli.py mechanical split → v0.1.15 W-29.** 9217-line
  refactor with byte-stable manifest preservation deemed too
  high-risk for single-session execution alongside the 12 other
  W-ids. v0.1.13 W-29-prep boundary table preserved.
- **W-AH scenario expansion → v0.1.15 W-AH-2.** 28 → 35 (+7 new).
  Original 120+ target deferred. Scenario authoring is bottlenecked
  on hand-tracing per-domain classify+policy signal requirements;
  partial-closing lets v0.1.15 do scenario-by-scenario validation
  rather than write-then-validate-en-masse.
- **W-AI `hai eval review` CLI → v0.1.15 W-AI-2.** Substrate work
  for maintainer-side scenario flagging; not blocking v0.2.2
  W58J (which only needs the judge harness, not the review CLI).
- **W-Vb-3 persona-replay → v0.1.15 W-Vb-4.** 3 of 9 (P2/P3/P6).
  Cumulative 6 of 12 across v0.1.13+v0.1.14. The contract from
  PLAN.md §2.M ("may further partial-close, 3-at-a-time") was
  pre-anticipated.

## 4. Pre-implementation gate decisions (recap)

Documented in `pre_implementation_gate_decision.md`:

- **W-2U-GATE → v0.1.15** (§1.3.1 path 2, no candidate on file).
- **F-PHASE0-01 → W-FRESH-EXT** (runner-hardening adjunct,
  ~3 lines + 1 test).
- **OQ-J AgentSpec README framing** applied (option 2).

The W-2U-GATE deferral is the load-bearing scope change of the
cycle. Path 2 is the canonical "no candidate by gate" handler
explicitly anticipated by the audited PLAN; no re-D14 was
required. Cycle scope went `14 → 13` W-ids; effort `32-45 → 30-43`
days.

## 5. Lessons / patterns observed

### 5.1 Substrate-first sequencing reduced design risk

Pre-staging W-PROV-1 + W-AJ + W-AL ahead of v0.2.0 W52 + W58D +
W58J means v0.2.0's PLAN can be authored without reserving
design risk for "what shape do we land the locator type / judge
harness / calibration report in?". Worth the 5-7 days spent.

### 5.2 Honest partial-closure scaled the cycle

The cycle started at 14 W-ids; closed 13 (after the W-2U-GATE
defer); partial-closed 3 of those with named v0.1.15 destinations.
Trying to ship full closure on every W-id in one session would
have produced silent "looks done but actually broken" surfaces
(see W-AH initial scenario writes that failed to match the real
classify+policy paths). Naming partial closure honestly per
AGENTS.md preserves trust with the next-cycle author.

### 5.3 Fixture scenario authoring is bottlenecked on classify-policy tracing

The 28 → 35 W-AH increase reveals that bulk scenario authoring
without per-scenario validation against the live classify+policy
stack produces fixtures that fail their stated expectations. The
right fix is interactive: write one fixture, run `hai eval run
--domain X`, fix the expected if needed, repeat. This is a
v0.1.15 W-AH-2 affordance — author scenarios in batches of 5,
validate after each batch, not 30+ at a time.

### 5.4 Pre-flight hermeticity matters

F-PHASE0-01 (persona-harness × demo-session interaction) was a
real bug masked by environmental-state coincidence. Catching it
required Phase 0 running in a maintainer environment with prior
demo activity. The W-FRESH-EXT runner pre-flight prevents
recurrence; future test-substrate harnesses should consider the
same "refuse-on-stale-state" pattern.

### 5.5 Maintainer-substitute review has limits

The W-EXPLAIN-UX maintainer-substitute pass per §1.3.1 path 2
surfaces 8 findings, but the maintainer cannot fully simulate
foreign-user confusion. The
`carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass` section
explicitly names 4 items that need empirical foreign-user
testing — precisely the items most likely to surface
expectation drift.

## 6. Ship-readiness state

| Gate | Status |
|---|---|
| D14 plan-audit | ✓ closed at round 4 (PLAN_COHERENT) |
| Phase 0 (D11) | ✓ gate fired green |
| Pre-implementation gate | ✓ decisions documented |
| Implementation | ✓ 8 closed + 3 partial + 2 deferred + 1 absorbed |
| Codex IR | ⏳ prompt authored; awaiting Codex |
| Ship-freshness checklist | ⏳ pending pre-publish sweep |
| PyPI publish | ⏳ maintainer-handoff |

## 7. Audit-chain settling shape

D14: **12 → 7 → 3 → 1-nit → CLOSE** (4 rounds, 23 cumulative
findings, all ACCEPT, zero DISAGREE). Mirrors v0.1.13 exactly;
twice-validated for substantive PLANs at the 14-17 W-id range.

Phase 0 (D11): **0 revises-scope, 0 aborts-cycle, 1 in-scope**
(F-PHASE0-01 absorbed into W-FRESH-EXT).

Codex IR: pending.

## 8. Cycle position

Substantive-cycle implementation closed. Awaiting Codex IR
verdict before merge to `main` + PyPI publish.

## 9. Provenance

Authored 2026-05-01 by Claude Opus 4.7 (1M context) at HEAD
`16d2cd0`, on branch `cycle/v0.1.14`. Inputs: PLAN.md (D14 r4),
pre_implementation_gate_decision.md, audit_findings.md, RELEASE_PROOF.md.
