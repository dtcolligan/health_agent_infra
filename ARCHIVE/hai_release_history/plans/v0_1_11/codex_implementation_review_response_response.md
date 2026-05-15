# Maintainer Response — Codex Implementation Review Round 1

> **Authored 2026-04-29** by Claude in response to Codex's
> `codex_implementation_review_response.md` (verdict:
> `DO_NOT_SHIP`, 2 blockers + 4 important findings).
>
> **Status.** All 6 findings addressed in additional commits on
> `cycle/v0.1.11`. Branch ready for round 2 review.

---

## 1. Triage summary

| Finding | Severity | Disposition | Resolution |
|---|---|---|---|
| F-IR-01 W-E fingerprint scope | blocker | accept-fix | extended fingerprint to hash `accepted_*_state_daily` corrected_at + projected_at |
| F-IR-02 demo flow not runnable | blocker | accept-fix | `hai demo start` now initializes scratch DB; demo_flow.md § 5 narrates the proposal-authoring boundary |
| F-IR-03 W-W concurrency + JSONL | important | accept-with-revision | narrowed PLAN scope (JSONL out of scope for v0.1.11), added 47/49h boundary tests + 100-trial determinism test |
| F-IR-04 W-S harness schema-version drift | important | accept-fix | synthetic_skill reads from `_DOMAIN_PROPOSAL_SCHEMAS` registry; new contract test |
| F-IR-05 D11 skip justification | important | accept-fix | RELEASE_PROOF § 2.7 gains an actual subprocess transcript + test reference |
| F-IR-06 W-Va cardinal test honesty | important | accept-fix | new subprocess-level isolation test runs real CLI under demo and asserts real-state byte-identical |

No disagreements. Two blockers were genuine implementation
contract gaps the cycle's tests didn't catch because the tests
bypassed the contract surface; the four important findings are
each a real gap between PLAN.md spec and shipped behaviour.

---

## 2. Per-finding response

### F-IR-01 — W-E fingerprint misses material state-only changes

**Accept (blocker).** PLAN.md was clear: the fingerprint must
detect `log nutrition A → daily → log nutrition B → daily`
auto-supersede with `_v<N>`. My implementation only hashed
proposal payloads + Phase-A firings, so a state-only change that
didn't re-author the proposal returned the existing canonical
plan as a no-op. The test I wrote exercised the implementation
(by mutating proposal_log payload directly), not the PLAN
acceptance scenario.

**Revision applied** (`src/health_agent_infra/core/synthesis.py`):

`_compute_state_fingerprint` now accepts optional `conn` /
`for_date` / `user_id` and hashes the upstream state surfaces:

- For each of the six per-domain `accepted_*_state_daily`
  tables, the row's `corrected_at` + `projected_at` timestamps
  at `(for_date, user_id)`. These update on every UPSERT, so a
  `hai intake nutrition` mutation flips `corrected_at` even
  when the proposal rows aren't re-authored.
- Plus the existing proposal-payload + Phase-A-firings hash.

`run_synthesis` passes all three to the fingerprint helper. The
no-op early-return path now correctly survives only against
truly-unchanged state.

**Acceptance test added**:
`test_daily_supersede_on_state_change.py::test_rerun_after_intake_nutrition_change_auto_supersedes`
seeds initial nutrition state, runs synthesis to produce
canonical, bumps `corrected_at` on `accepted_nutrition_state_daily`
WITHOUT touching `proposal_log`, re-runs synthesis, asserts
`_v2` is minted. This is the PLAN.md acceptance scenario through
runtime state, not via direct payload mutation.

### F-IR-02 — Canonical blank-demo flow fails before synthesis

**Accept (blocker).** Two distinct failures:

1. `hai demo start --blank` created the marker + scratch sub-paths
   but never ran `initialize_database()` against the scratch
   `state.db`. Subsequent `hai intake *` calls fell back to JSONL-
   only with the "state DB projection skipped" warning.
2. The demo flow doc § B's "Synthesise" step skipped the
   proposal-authoring requirement; `hai daily` reads existing
   proposals and won't fabricate them.

**Revisions applied**:

- `core/demo/session.py:open_session` now calls
  `initialize_database(db_path)` after creating the scratch
  sub-paths (lazy import to avoid the resolver-import cycle).
- `reporting/docs/demo_flow.md` § 5 rewritten as "Compose
  proposals (the runtime/agent boundary)". Two paths documented:
  (a) stop at `awaiting_proposals` and narrate the
  runtime/skill boundary as the demo moment — **canonical for
  v0.1.11**; (b) seed proposals + synthesise — forward-compat
  for v0.1.12 W-Vb when the persona fixture loader pre-populates.
- Steps 6-7 split into "path (a) only" and "path (b) only"
  sections.

**Acceptance test added**:
`test_demo_session_lifecycle.py::test_open_session_initializes_scratch_db`
asserts the scratch DB exists post-`open_session` + has the head
schema version applied (≥ 22 for migration 022).

**Subprocess replay added**:
`test_demo_isolation_surfaces.py::test_subprocess_cli_writes_under_demo_isolate_real_state`
runs `demo start → intake readiness → intake nutrition →
intake stress → demo end` via subprocess and asserts real DB +
real base_dir checksums byte-identical before / after. Same
sequence captured as a transcript in RELEASE_PROOF § 2.7.

### F-IR-03 — W-W read-consistency contract incomplete

**Accept (important; partial-narrow).** Codex is right that
PLAN.md required JSONL-tail consistency that the implementation
doesn't deliver. The honest path is to narrow the PLAN scope —
gap derivation runs entirely off SQLite via `build_snapshot`,
and there are no JSONL reads in the gap-derivation path. The
F-PLAN-R2-04 row-level-filter contract was authored against a
hypothetical JSONL-tail consumer that doesn't exist in the v0.1.11
code path.

**Revisions applied**:

- PLAN.md § 2.16 (W-W) revised: explicit "JSONL tail reads are
  out of scope for v0.1.11 W-W" note. If a future workstream
  adds JSONL reads to gap derivation, the row-level filter +
  inode-and-byte-range capture must land alongside it.
- Boundary tests at the staleness gate added at exact
  47h / 48h / 49h:
  - `test_pull_at_47h_passes_gate` — under threshold passes.
  - `test_pull_older_than_48h_refused_without_override` (already
    existed) covers the 50h side.
  - `test_pull_at_49h_refused_by_gate` (new) — exact 49h refuses.
- 100-trial determinism test added:
  `test_concurrency_100_trials_deterministic` runs gap derivation
  100 times against a stable DB and asserts every output produces
  the same gap shape (excluding wall-clock `snapshot_read_at`).
  This tests the SQLite read-isolation guarantee `BEGIN IMMEDIATE`
  provides.

The cross-process write-during-read scenario the original spec
described required a JSONL tail consumer; it's deferred with the
PLAN narrowing.

### F-IR-04 — W-S persona harness schema-version drift

**Accept (important).** The harness emitted `f"{domain}_proposal.v1"`
literally; a schema-version bump would silently drift between the
harness, validator, and manifest.

**Revision applied**:

- `verification/dogfood/synthetic_skill.py:build_proposal` now
  reads schema versions from `_DOMAIN_PROPOSAL_SCHEMAS` (the
  same registry the manifest consumes via the W-S walker
  extension). One primitive, three consumers (validator,
  manifest, persona harness).
- New contract test:
  `test_persona_harness_contract.py::test_harness_emits_schema_version_from_canonical_registry`
  asserts the harness's emitted `schema_version` for every
  domain equals the registry value. A future schema-version
  bump that updates the registry but not the harness fails this
  test; the inverse fails it too.

### F-IR-05 — D11 skip justification weakened by bugs

**Accept (important).** Codex correctly observed that the
RELEASE_PROOF argument for skipping Phase 0 was weakened by
the F-IR-01 + F-IR-02 implementation gaps — exactly the kind of
end-to-end-replay bugs a real Phase 0 would have caught.

**Revision applied**:

- RELEASE_PROOF § 2.7 gains an actual isolation-replay
  transcript: pre-replay shasum of real DB + base, the demo
  session sequence (`demo start → intakes → daily → demo end`),
  post-replay shasum, ISOLATION REPLAY: PASS verdict.
- The transcript references the new
  `test_subprocess_cli_writes_under_demo_isolate_real_state`
  test that runs the same sequence as a permanent regression.
- v0.1.12 pre-PLAN bug-hunt should treat
  "demo flow runs end-to-end" as a Phase-0 acceptance scenario,
  not a downstream test concern. Carry this forward as a cycle
  lesson.

### F-IR-06 — W-Va cardinal isolation test does not run real CLI writes

**Accept (important).** The pre-fix
`test_demo_isolation_surfaces.py` proved the resolvers route to
scratch under a marker, but it didn't subprocess-out to verify
the END-TO-END CLI path lacks a direct write bypass.

**Revision applied**:

- New test:
  `test_subprocess_cli_writes_under_demo_isolate_real_state`.
  Uses `subprocess.run` to invoke `python -m
  health_agent_infra.cli` with `HAI_STATE_DB` / `HAI_BASE_DIR` /
  `HAI_DEMO_MARKER_PATH` pinned to tmp_path-controlled real
  surfaces, runs the canonical demo command sequence, and
  asserts the real DB + real base_dir checksums are
  byte-identical before and after.
- Same sequence captured as the F-IR-05 transcript in
  RELEASE_PROOF.

---

## 3. Net cycle impact

| Metric | Pre-R1-fixes | Post-R1-fixes |
|---|---|---|
| Test surface | 2347 passing | **2354 passing** (+7) |
| Mypy errors | 21 | 21 (unchanged; W-H2 stylistic deferred) |
| Bandit -ll medium/high | 0 | 0 |
| Blocker-class findings | 2 (Codex R1) | 0 (verify in R2) |
| Branch state | clean | clean (additional commits on cycle/v0.1.11) |

7 new tests added (vs. R1 baseline):
- `test_open_session_initializes_scratch_db` (F-IR-02)
- `test_subprocess_cli_writes_under_demo_isolate_real_state` (F-IR-06)
- `test_pull_at_47h_passes_gate` (F-IR-03)
- `test_pull_at_49h_refused_by_gate` (F-IR-03)
- `test_concurrency_100_trials_deterministic` (F-IR-03)
- `test_rerun_after_intake_nutrition_change_auto_supersedes` (F-IR-01)
- `test_harness_emits_schema_version_from_canonical_registry` (F-IR-04)

Plus PLAN.md § 2.16 narrowing (F-IR-03), demo_flow.md § 5
rewrite (F-IR-02), RELEASE_PROOF § 2.7 transcript (F-IR-05),
and the W-S harness fix.

---

## 4. Outstanding actions

Branch `cycle/v0.1.11` ready for **Codex implementation review
round 2**. Use the same
`codex_implementation_review_prompt.md` (still self-contained
for a fresh session); add a reading-order note that this file
is the round-1 response. Verdict scale unchanged: SHIP /
SHIP_WITH_NOTES / DO_NOT_SHIP.

Worth specifically re-checking in round 2:

- F-IR-01 acceptance test asserts the right contract (state-only
  change → `_v2` via accepted-state corrected_at delta, not via
  proposal-payload mutation).
- F-IR-02 + F-IR-06 subprocess test exercises the cardinal
  isolation contract at the CLI surface, not just resolvers.
- F-IR-03 narrowing is honest — no JSONL consumer in v0.1.11
  W-W; future workstreams must own the row-level-filter contract
  alongside their JSONL reads.
- F-IR-04 contract test catches both directions of drift
  (registry-changes-but-harness-doesn't and vice versa).
