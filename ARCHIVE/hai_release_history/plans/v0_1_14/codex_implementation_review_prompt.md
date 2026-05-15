# Codex Implementation Review — v0.1.14 cycle

> **Why this round.** v0.1.14 implementation is complete on the
> `cycle/v0.1.14` branch (8 commits since main). The D14 pre-cycle
> plan-audit chain settled at `PLAN_COHERENT` at round 4 (settling
> shape `12 → 7 → 3 → 1-nit → CLOSE`; mirrors v0.1.13 exactly).
> Phase 0 (D11) bug-hunt cleared with 1 in-scope finding
> (F-PHASE0-01) absorbed into W-FRESH-EXT. Pre-implementation
> gate fired with three load-bearing decisions documented in
> `pre_implementation_gate_decision.md`: W-2U-GATE deferred to
> v0.1.15 (no candidate; §1.3.1 path 2), F-PHASE0-01 absorbed
> into W-FRESH-EXT, OQ-J AgentSpec README framing applied.
> RELEASE_PROOF + REPORT authored. **The branch has not been
> merged or pushed.**
>
> **What you're auditing.** The cycle's *implementation* — that
> the code that landed actually delivers what PLAN.md promised,
> that the ship gates pass, and that no defect is hiding in the
> diff. **Not** the plan itself (D14 already settled that),
> **not** the prior-cycle surface (already shipped to PyPI as
> v0.1.13).
>
> **Empirical norm:** 2-3 rounds, settling at `5 → 2 → 1-nit`.
>
> **You are starting fresh.** This prompt and the artifacts it
> cites are everything you need; do not assume context from a
> prior session.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd                                          # /Users/domcolligan/health_agent_infra
git branch --show-current                    # cycle/v0.1.14
git log --oneline cycle/v0.1.14 ^main        # 8 commits, top-down
git status                                   # clean
ls reporting/plans/v0_1_14/                  # PLAN + 12 audit-chain + RELEASE_PROOF + REPORT + this prompt
```

Expected file count under `reporting/plans/v0_1_14/`:
- `PLAN.md`
- `pre_implementation_gate_decision.md`
- `audit_findings.md`
- 4× D14 round prompts (rounds 1-4)
- 4× Codex round responses + 4× maintainer round responses (12 D14 chain files total)
- `RELEASE_PROOF.md`
- `REPORT.md`
- `codex_implementation_review_prompt.md` (this file)

**Total: 16 files** (1 PLAN + 1 gate-decision + 1 findings + 12 D14 chain + 1 RELEASE_PROOF + 1 REPORT + 1 IR-prompt).

If anything mismatches, stop and surface. Ignore
`/Users/domcolligan/Documents/`.

---

## Step 1 — Read orientation artifacts (in order)

1. **`AGENTS.md`** — operating contract. v0.1.14 added no new
   D-entries. Read **"Patterns the cycles have validated"** —
   provenance discipline, summary-surface sweep, honest partial-
   closure naming. Apply these as you audit.
2. **`reporting/plans/v0_1_14/PLAN.md`** — cycle contract.
3. **`reporting/plans/v0_1_14/pre_implementation_gate_decision.md`** —
   the three gate-decisions (W-2U-GATE defer, F-PHASE0-01 →
   W-FRESH-EXT, OQ-J applied).
4. **`reporting/plans/v0_1_14/RELEASE_PROOF.md`** — what shipped,
   with named-defers in §5.
5. **`reporting/plans/v0_1_14/REPORT.md`** — narrative summary.
6. **`reporting/plans/v0_1_14/audit_findings.md`** — Phase 0
   findings.
7. **`reporting/docs/source_row_provenance.md`** — W-PROV-1 design
   (load-bearing for v0.2.0 W52).
8. **`reporting/docs/recovery.md`** — W-BACKUP user contract.
9. **`reporting/docs/explain_ux_review_2026_05.md`** —
   W-EXPLAIN-UX maintainer-substitute findings.
10. **`reporting/docs/calibration_eval_design.md`** — W-AL design
    (load-bearing for v0.2.0 W58D + v0.2.2 W58J).
11. **`reporting/plans/post_v0_1_13/cycle_proposals/CP-2U-GATE-FIRST.md`**
    — applied-but-deferred status header.

Then open the diff:

```bash
git diff main...cycle/v0.1.14 -- src/ verification/ reporting/docs/
git diff main...cycle/v0.1.14 -- AGENTS.md ROADMAP.md AUDIT.md \
    CHANGELOG.md pyproject.toml README.md \
    reporting/plans/strategic_plan_v1.md \
    reporting/plans/tactical_plan_v0_1_x.md \
    reporting/plans/post_v0_1_13/reconciliation.md
```

---

## Step 2 — Audit questions

### Q-PROV-1. W-PROV-1 source-row locator implementation matches design

PLAN §2.B ships:
- Schema design at `reporting/docs/source_row_provenance.md`.
- Migration 023 (new column on recommendation_log).
- Recovery R6 firing emits locators.
- `hai explain` renders in JSON + markdown.
- Roundtrip test asserts locator → DB-row resolution.

Verify:
- `core/state/migrations/023_source_row_locator.sql:17` adds
  `evidence_locators_json TEXT` to recommendation_log.
- `core/provenance/locator.py` whitelists `accepted_recovery_state_daily`
  + `source_daily_garmin` (and only those).
- `core/provenance/locator.py::resolve_locator` actually resolves
  back to the row (test_source_row_locator_recovery.py
  test_resolve_locator_returns_row_when_present).
- `core/state/projector.py::project_bounded_recommendation`
  now writes `evidence_locators_json`; the JSONL replay path also
  carries the column.
- `core/synthesis.py:208` (or thereabouts; spot-check) copies
  `evidence_locators` from proposal to recommendation.
- `core/explain/render.py` renders locators in `_format_proposal`
  and `_format_recommendation`.
- `domains/recovery/policy.py::evaluate_recovery_policy` accepts
  the new optional `for_date_iso` / `user_id` /
  `accepted_state_versions` kwargs and emits
  `evidence_locators` only when R6 fires with the spike reason
  token.

Spot-check with the design doc's contract: do the source code
choices match? Any drift between the design doc and the code?

### Q-EXPLAIN-UX. W-EXPLAIN-UX P13 + maintainer-substitute review

PLAN §2.C ships:
- P13 persona registered.
- Maintainer-substitute review (per §1.3.1 path 2) filed.
- Carries-forward-to-v0.1.15 section.

Verify:
- `verification/dogfood/personas/p13_low_domain_knowledge.py`
  exists, registered in `__init__.py::ALL_PERSONAS`,
  `expected_actions` declared inline (W-AK pattern).
- `reporting/docs/explain_ux_review_2026_05.md` contains a
  "v0.2.0 W52 prose obligations" section (per F-PLAN-05) AND a
  "carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass"
  section (per §1.3.1 path 2).
- The 6 prose obligations are concrete (issue / proposed
  prose change / acceptance hook triplets per F-PLAN-05).

### Q-BACKUP. W-BACKUP roundtrip + schema-mismatch refusal

PLAN §2.D ships:
- `hai backup` / `hai restore` / `hai export` CLI subcommands.
- Schema-mismatch case tested.
- `reporting/docs/recovery.md`.
- Capabilities snapshot accepts the new entries (named-change-
  accepted per F-PLAN-04).

Verify:
- `core/backup/bundle.py` writes a versioned tarball with
  `manifest.json` + `state.db` + `jsonl/`.
- `restore_backup` raises `SchemaMismatchError` with explicit
  recovery hint when bundle's schema_version != installed wheel's
  head.
- `hai capabilities --json` shows 59 commands (was 56 pre-cycle).
- `verification/tests/test_backup_restore_roundtrip.py` asserts
  the roundtrip + schema-mismatch refusal.
- `reporting/docs/recovery.md` documents 5 disaster scenarios.

### Q-FRESH-EXT. W-FRESH-EXT extension + F-PHASE0-01 absorption

PLAN §2.E + the gate-decision absorb F-PHASE0-01 into W-FRESH-EXT.
Verify:
- `verification/dogfood/runner.py` has a `_preflight_demo_session_check`
  hook called from `run_all_personas` that raises `SystemExit(2)`
  if `cleanup_orphans()` returns a non-empty list.
- `verification/tests/test_doc_freshness_assertions.py` extends
  to W-id refs across `ROADMAP.md` /
  `reporting/plans/tactical_plan_v0_1_x.md` /
  `reporting/plans/strategic_plan_v1.md` with an honest-deferral
  exempt-keyword set.

### Q-AJ + Q-AL. W-AJ judge harness + W-AL calibration schema

PLAN §2.H + §2.I ship:
- `core/eval/judge_harness.py` with stable invocation interface;
  `NoOpJudge` reference impl.
- `core/eval/calibration_schema.py` FActScore-aware schema with
  stub decomposer.
- `reporting/docs/calibration_eval_design.md` cites FActScore +
  MedHallu.

Verify:
- `JudgeResponse.bias_panel_results` is pre-allocated for v0.2.2
  W-JUDGE-BIAS (empty in v0.1.14).
- `JudgeHarness.judge_batch` provides serial-default fan-out so
  v0.2.2 W58J can override for batched model invocation.
- `decompose_into_atomic_claims` is honestly stubby (sentence-
  boundary split; no semantic decomposition); design doc names
  v0.2.0 W-FACT-ATOM as the replacement.

### Q-AI. W-AI judge-adversarial fixture corpus

PLAN §2.G partially closes — 30 fixtures shipped (10 each:
prompt_injection / source_conflict / bias_probe). `hai eval review`
CLI deferred to v0.1.15 W-AI-2. Verify:
- 10 fixtures per category in
  `src/health_agent_infra/evals/scenarios/judge_adversarial/<cat>/`.
- `index.json` lists all 30 fixture IDs.
- `verification/tests/test_judge_adversarial_fixtures.py` enforces
  the contract.
- `RELEASE_PROOF.md §1` row for W-AI names "partial-closure →
  v0.1.15 W-AI-2" honestly.

### Q-AN. W-AN `hai eval run --scenario-set` CLI

PLAN §2.K ships the `--scenario-set` flag. Verify:
- `evals/cli.py` registers `--scenario-set` choices including
  `judge_adversarial` and `all`.
- `--scenario-set judge_adversarial` emits a shape-only summary
  (no scoring) per the v0.1.14 + v0.2.2 split.
- `--scenario-set all` fan-outs `domain` + `synthesis`.

### Q-DOMAIN-SYNC. W-DOMAIN-SYNC contract test

PLAN §2.N ships a single-truth-table contract test. Verify:
- `verification/tests/test_domain_sync_contract.py` pins the
  canonical six across the runtime.
- The `gym↔strength` snapshot-read alias is documented inline
  with a pin to `core/state/snapshot.py:522`.
- `_DOMAIN_ACTION_REGISTRY` Phase-A-only exemption is explicit
  per F-PLAN-09.

### Q-Vb-3. W-Vb-3 partial closure — 3 of 9 personas (P2/P3/P6)

PLAN §2.M permits further partial closure ("3-at-a-time"). Verify:
- 3 new fixtures at `src/health_agent_infra/demo/fixtures/`:
  `p2_female_marathoner.json`, `p3_older_recreational.json`,
  `p6_sporadic_recomp.json`.
- Each fixture has 6 domain proposals matching `domain_proposal.v1`
  schema.
- RELEASE_PROOF.md §1 names the partial-closure with v0.1.15
  W-Vb-4 destination per AGENTS.md "Honest partial-closure naming".
- Cumulative state across v0.1.13 + v0.1.14: 6 of 12 personas
  closed (P1+P4+P5 from v0.1.13; P2+P3+P6 added v0.1.14).

### Q-29. W-29 deferral honesty

PLAN §2.L promised the cli.py mechanical split. RELEASE_PROOF
deferred it to v0.1.15. Verify:
- `cli.py` is **not** split in this cycle (still a single file).
- v0.1.13 W-29-prep boundary table at
  `reporting/docs/cli_boundary_table.md` is preserved.
- `test_cli_parser_capabilities_regression.py` snapshots are
  regenerated only for the named-change-accepted W-AN + W-BACKUP +
  W-PROV-1 surfaces (per F-PLAN-04 expected-diff classes), not
  for any W-29 split.
- RELEASE_PROOF.md §1 + §5 name v0.1.15 W-29 as the destination.

### Q-AH + Q-AM. W-AH + W-AM partial closure honesty

W-AH grew 28 → 35 (+7); W-AM absorbed into W-AI corpus + 6
escalate-tagged scenarios. Verify:
- 35 scenarios under `src/health_agent_infra/evals/scenarios/`
  (excluding judge_adversarial).
- `uv run hai eval run --scenario-set all` returns OK.
- Six scenarios tagged `w-am-adversarial-escalate` (escalate
  cases) — find them via `grep -rl "w-am-adversarial-escalate"
  src/health_agent_infra/evals/scenarios/`.
- RELEASE_PROOF.md §1 names W-AH partial → v0.1.15 W-AH-2 with
  120+ destination preserved.

### Q-ship-gates. Re-run the gates the PLAN promised

Run from a clean tree:

```bash
uv run pytest verification/tests -q                       # ≥ 2540 expected
uv run pytest verification/tests -W error::Warning -q     # 0 fail / 0 error
uvx mypy src/health_agent_infra                           # 0 errors
uvx bandit -ll -r src/health_agent_infra                  # 0 Med/High; ≤ 50 Low
uvx ruff check src/health_agent_infra                     # clean
uv run hai capabilities --markdown | diff - reporting/docs/agent_cli_contract.md  # empty diff
```

If any gate diverges from the RELEASE_PROOF §2 numbers, that's a
finding.

### Q-pre-implementation-gate. Gate-decision integrity

`pre_implementation_gate_decision.md` records three decisions:

1. W-2U-GATE → v0.1.15 (§1.3.1 path 2).
2. F-PHASE0-01 → W-FRESH-EXT.
3. OQ-J AgentSpec README framing applied.

Verify each landed correctly:
- W-2U-GATE: PLAN §2.A names "deferred"; tactical_plan +
  ROADMAP + reconciliation §5 reflect v0.1.15 destination;
  CP-2U-GATE-FIRST status updated.
- F-PHASE0-01: W-FRESH-EXT contract in PLAN §2.E names the
  absorption; runner pre-flight implemented.
- OQ-J: README opener uses "domain-pinned AgentSpec" framing.

### Q-summary-surface-sweep

Per AGENTS.md "Summary-surface sweep on partial closure", every
partial-closure must move every summary surface in lockstep.
Spot-check W-Vb-3 (the canonical residual):
- PLAN §1.2 catalogue (§2.M row).
- PLAN §2.M contract section.
- PLAN §3 ship gates row (no W-Vb-3 ship gate; matrix-clean
  covers it).
- PLAN §4 risks (W-Vb-3 partial-closes again row).
- RELEASE_PROOF.md §1.
- REPORT.md §3.
- Tactical plan v0.1.15 row.

If any surface is stale, that's a finding.

### Q-provenance discipline

Spot-verify on-disk claims (file paths, line numbers, function
names, exact strings cited in PLAN/RELEASE_PROOF/REPORT). v0.1.12
+ v0.1.13 IR rounds caught multiple provenance errors — be the
independent skeptical pass.

### Q-cross-cutting code quality

- Unused new imports? (`uvx ruff check` clean already, but
  spot-check the new files.)
- Lazy imports in hot paths? `core/writeback/proposal.py`
  imports `core.provenance.locator` lazily inside the
  validator — correct or wrong?
- New error paths fail open vs fail closed? E.g.,
  `_preflight_demo_session_check` raises `SystemExit(2)` —
  correct stop-the-run shape.
- `evidence_locators_json` column is read with a `dict.keys()
  in row.keys()` guard in `core/explain/queries.py` — correct,
  but verify the fallback path (older DBs without the column)
  works.

### Q-absences

Anything the cycle didn't say it shipped that the diff actually
changed? Any deferral that should be named but isn't?

---

## Step 3 — Output shape

Write findings to
`reporting/plans/v0_1_14/codex_implementation_review_response.md`:

```markdown
# Codex Implementation Review — v0.1.14

**Verdict:** SHIP | SHIP_WITH_NOTES | SHIP_WITH_FIXES
**Round:** 1 / 2 / 3 / ...

## Verification summary
- Tree state: …
- Test surface: …
- Ship gates: …

## Findings

### F-IR-01. <short title>
**Q-bucket:** Q-PROV-1 / Q-EXPLAIN-UX / Q-BACKUP / ...
**Severity:** correctness-bug | security | scope-mismatch | provenance-gap | acceptance-weak | nit
**Reference:** <commit SHA / file:line> or "absent"
**Argument:** <what + citations>
**Recommended response:** <fix-and-reland | accept-as-known | ...>

## Per-W-id verdicts

| W-id | Verdict | Note |
|---|---|---|
| W-PROV-1 | clean | … |
| W-EXPLAIN-UX | clean | … |
| ... | ... | ... |

## Open questions for maintainer
```

Each finding triageable. Vague feedback is not a finding;
"PLAN §1.2 W-X catalogue row says 'recovery prototype' but commit
SHA shipped only the flag plumbing per `cli.py:8125`" is.

---

## Step 4 — Verdict scale

- **SHIP** — merge + publish, no further work.
- **SHIP_WITH_NOTES** — merge + publish; named follow-ups carry
  to next cycle. Notes enumerate every non-blocking finding.
- **SHIP_WITH_FIXES** — fix-and-reland. Notes enumerate every
  blocking finding. Round-2 review after maintainer addresses.
- **DO_NOT_SHIP** — only on correctness/security bug warranting
  commit reverts.

For most substantive cycles, `SHIP_WITH_NOTES` with a small
next-cycle follow-up set is the natural shape.

---

## Step 5 — Out of scope

- Prior-cycle implementation (v0.1.13 already shipped to PyPI).
- D14 plan-audit chain itself (closed at PLAN_COHERENT round 4).
- Strategic-plan / tactical-plan content beyond the deltas this
  cycle applied.
- The named-deferrals themselves (W-2U-GATE → v0.1.15, W-29 →
  v0.1.15, etc.) — they have destination cycles. Findings only
  about deferrals that should NOT be deferred.
- Next-cycle scope (v0.1.15 catalogue is in tactical_plan_v0_1_x.md).

---

## Step 6 — Cycle pattern

```
D14 plan-audit ✓ (round 4 PLAN_COHERENT, settling 12→7→3→1-nit→CLOSE)
Phase 0 (D11) ✓ (1 in-scope finding F-PHASE0-01 absorbed)
Pre-implementation gate ✓ (W-2U-GATE→v0.1.15 + F-PHASE0-01→W-FRESH-EXT + OQ-J applied)
Implementation ✓ 8 commits since main; 8 W-ids closed + 3 partial + 2 deferred + 1 absorbed
Codex implementation review ← you are here
  → SHIP_WITH_FIXES → maintainer + new commits
  → SHIP / SHIP_WITH_NOTES → merge to main
RELEASE_PROOF.md ✓ + REPORT.md ✓
PyPI publish (per ~/.claude/projects/.../memory/reference_release_toolchain.md)
```

Estimated: 1-2 sessions per round.

---

## Step 7 — Files this audit may modify

- `reporting/plans/v0_1_14/codex_implementation_review_response.md`
  (new) — your findings.
- `reporting/plans/v0_1_14/codex_implementation_review_round_N_response.md`
  (subsequent rounds).

**No code changes.** No source commits. No state mutations.
Maintainer applies fixes; you do not edit source directly.

If you find a correctness/security bug warranting `DO_NOT_SHIP`,
name it explicitly and stop the review for maintainer
adjudication.
