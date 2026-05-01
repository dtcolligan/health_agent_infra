# v0.1.14 PLAN — Eval expansion + LLM-judge prep + second-user gate

**Status:** draft (pre-D14 plan-audit).
**Authored:** 2026-05-01.
**Cycle tier (D15):** substantive (14 W-ids; ≥1 release-blocker
workstream W-2U-GATE; ≥3 governance-or-audit-chain edits;
≥10 days estimated).
**Estimated effort:** 30-40 days (1 maintainer).
**D14 expectation:** 4-5 rounds; if it exceeds 5 rounds, maintainer
re-scopes before implementation. (Empirical norm at 17 W-ids
v0.1.13 was 5 rounds; 14 W-ids should fall in the 4-5 range.)
**Source inputs:**
- `reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`
  (post-v0.1.13 strategic research, Codex-audited 2 rounds, closed
  REPORT_SOUND_WITH_REVISIONS).
- `reporting/plans/post_v0_1_13/reconciliation.md`.
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-2U-GATE-FIRST.md`
  (W-2U-GATE sequenced first).
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-MCP-THREAT-FORWARD.md`
  (W-MCP-THREAT scheduled v0.2.0; informs v0.1.14 W-AJ harness
  scope).
- `reporting/plans/post_v0_1_13/cycle_proposals/CP-DO-NOT-DO-ADDITIONS.md`
  (applied to AGENTS.md 2026-05-01).
- `reporting/plans/v0_1_13/RELEASE_PROOF.md` §5 (named deferrals
  inherited).
- `reporting/plans/v0_1_13/CARRY_OVER.md`.

---

## 1. What this release ships

### 1.1 Theme

Build the eval substrate for v0.2.0's W58 factuality gate; land the
source-row provenance type that v0.2.0 W52 will require; empirically
prove the v0.1.13 onboarding test surface against a foreign user;
and close the v0.1.13-deferred mechanical workstreams (W-29 cli.py
split, W-Vb-3 9-persona residual, W-DOMAIN-SYNC contract test).

End-state: **v0.2.0 starts with the source-row primitive + judge
harness in tree, reducing design risk** (v0.2.0 W52/W58D still ships
weekly-review aggregation + deterministic claim-block + claim corpus
in 18-24 days — *not* a wire-up release; F-PLAN-01 corrected). The
runtime has been validated by a non-maintainer; `hai backup` /
`hai restore` / `hai export` give second users a recovery path;
cli.py is split per the v0.1.13 W-29-prep boundary table without
breaking byte-stability of the capabilities snapshot.

### 1.2 Workstream catalogue (14 W-ids)

**Sequencing.** §1.3 below names the strict sequencing constraint:
W-2U-GATE runs first; if it surfaces a P0 remediation, the cycle
reshapes around the fix.

| Section | W-id | Title | Effort | Tier | Source |
|---|---|---|---|---|---|
| §2.A | W-2U-GATE | Foreign-machine onboarding empirical proof | 2-3 d | P0 | post-v0.1.13 §5 P0-1 + CP-2U-GATE-FIRST |
| §2.B | W-PROV-1 | Source-row locator type + 1-domain demo | 3-4 d | P0 | post-v0.1.13 §5 P0-2 |
| §2.C | W-EXPLAIN-UX | `hai explain` confusion-vs-clarity review + P13 persona | 2 d | P0 | post-v0.1.13 §5 P0-3 |
| §2.D | W-BACKUP | `hai backup` / `hai restore` / `hai export` | 3-4 d | P0 | post-v0.1.13 §5 P0-5 |
| §2.E | W-FRESH-EXT | Doc-freshness test extension (catches stale W-id refs) | 1 d | P1 | post-v0.1.13 §6 P1-5 |
| §2.F | W-AH | Scenario fixture expansion (30+ new) | 3-4 d | tactical-plan | tactical_plan §5.1 |
| §2.G | W-AI | Ground-truth labelling methodology + maintainer review tool | 2-3 d | tactical-plan | tactical_plan §5.1 |
| §2.H | W-AJ | LLM-judge harness scaffold (no model invocation yet) | 2-3 d | tactical-plan | tactical_plan §5.1 |
| §2.I | W-AL | Calibration eval — schema/report shape only (FActScore-aware) | 2 d | tactical-plan | tactical_plan §5.1 + reconciliation A2 |
| §2.J | W-AM | Adversarial scenario fixtures (judge-adversarial corpus) | 1-2 d | tactical-plan | tactical_plan §5.1 |
| §2.K | W-AN | `hai eval run --scenario-set <set>` CLI surface | 1-2 d | tactical-plan | tactical_plan §5.1 |
| §2.L | W-29 | cli.py mechanical split (1 main + 1 shared + 11 handler-group) | 3-4 d | inherited | v0.1.13 RELEASE_PROOF §5 + CP1 |
| §2.M | W-Vb-3 | Persona-replay extension (9 non-ship-set personas) | 4-6 d | inherited | v0.1.13 RELEASE_PROOF §5 + F-PLAN-06/R2-02/R3-02 |
| §2.N | W-DOMAIN-SYNC | Scoped contract test (single truth table) | 0.5 d | inherited | reconciliation L2 + Codex F-PLAN-09 |

**Total:** 14 W-ids; **32-45 days** (matches §5 arithmetic
31.5-44.5; F-PLAN-02 corrected the original 30-40 round-down);
substantive tier.

### 1.3 Sequencing constraint (per CP-2U-GATE-FIRST)

W-2U-GATE precedes all other workstreams. If it surfaces a P0
remediation:

- **P0 remediation (e.g., foreign user cannot reach `synthesized`):**
  v0.1.14 reshapes around the fix; non-blocking workstreams move to
  v0.1.15 without prejudice.
- **P1 remediation (e.g., onboarding works but UX is rough):** fold
  the P1 work into v0.1.14 W-EXPLAIN-UX scope; downstream W-ids
  proceed.
- **P2 / cosmetic remediation:** file as v0.2.0+ doc-fix-sweep
  candidates; downstream W-ids proceed.

**Order-of-operations after W-2U-GATE closes:**

1. W-PROV-1 (foundation for v0.2.0 W52; needs to land before W-AH/W-AI scenario work that may reference source-row provenance).
2. W-29 mechanical cli.py split (mechanical refactor; lands early to avoid merge friction with later substantive edits).
3. W-DOMAIN-SYNC (small contract test; trivial after W-29).
4. W-EXPLAIN-UX (P13 persona + foreign-user review; folds W-AK declarative-actions contract).
5. W-BACKUP (independent of eval substrate).
6. Eval substrate W-AH/W-AI/W-AJ/W-AL/W-AM/W-AN (parallelizable).
7. W-Vb-3 (parallelizable with eval substrate).
8. W-FRESH-EXT (last; doc-fix sweep aware of all changes).

### 1.3.1 Candidate-absence procedure (per F-PLAN-03)

W-2U-GATE has a hard external dependency on a non-maintainer
candidate. The OQ-I placeholder ("TBD") must resolve before Phase 0
can open. Procedure:

- **Hard rule:** named candidate must be on file by **Phase 0 gate**
  (not D14 close — D14 audits the PLAN, not coordination state).
  "On file" means: maintainer has identified the candidate, contacted
  them, and confirmed availability for the recorded session.
- **If no candidate by Phase 0 gate**, three options — maintainer
  chooses:
  1. **Hold the cycle.** Defer Phase 0 until a candidate surfaces;
     v0.1.14 holds at PLAN-authored / D14-passed state.
  2. **Defer W-2U-GATE to v0.1.15** with named destination; v0.1.14
     opens without it. W-EXPLAIN-UX foreign-user review uses a
     maintainer-substitute reader (or also defers to v0.1.15
     without prejudice). Cycle reshapes around the absence.
  3. **Re-author PLAN.md** (rescope around the absence) and re-run
     D14. Use this path if the maintainer believes W-2U-GATE
     should not be sequenced first under the absence (e.g., if
     candidate availability is a long horizon and v0.1.14 should
     proceed on substrate work first).

### 1.4 Deferrals (named, with destination)

The post-v0.1.13 strategic research surfaced items that do NOT
ship in v0.1.14:

| Item | Deferred to | Reason |
|---|---|---|
| W-MCP-THREAT (MCP threat-model artifact) | v0.2.0 doc-only adjunct | Per CP-MCP-THREAT-FORWARD; precedes v0.3 PLAN-audit |
| W-COMP-LANDSCAPE (`competitive_landscape.md`) | v0.2.0 doc-only adjunct | Per OQ-E |
| W-NOF1-METHOD (`n_of_1_methodology.md`) | v0.2.0 doc-only adjunct | Per OQ-E |
| W-2U-GATE-2 (second foreign user) | v0.2.0 doc-only adjunct | Sequenced after v0.1.14 remediation lands |
| W-FACT-ATOM (FActScore atomic decomposition) | v0.2.0 (folds into W58D) | Lands when W58D ships |
| W-JUDGE-BIAS (CALM bias panel) | v0.2.2 (folds into W58J) | Lands when W58J ships per Path A |
| `hai support` redacted bundle | v0.2.0 (per OQ-M default) | v0.1.14 already at 14 W-ids |
| AgentSpec README framing (per OQ-J option 2) | maintainer review pending | Draft surfaced; not yet applied |
| §21 mechanical citation pass on strategic-research report | bundled with W-FRESH-EXT | Codex round-2 deferred per F-RES-R2-06 |
| privacy.md hosted-agent-exposure tightening (P2-5) | v0.1.14 W-EXPLAIN-UX-adjacent doc | Symmetry with README:34-38 |

---

## 2. Per-workstream contracts

### §2.A — W-2U-GATE: foreign-machine onboarding empirical proof (P0; sequenced first)

**Why first.** v0.1.13 shipped the test surface for "trusted first
value" (W-AA, W-AF, W-A1C7). This workstream produces the empirical
proof that the test surface holds against a non-maintainer user.
Every later v0.1.14 workstream inherits the foreign-machine-onboarding
risk; if W-2U-GATE surfaces a structural blocker, the cycle reshapes.

**Workstream:**
- One recorded foreign-machine onboarding session by a non-
  maintainer (candidate: TBD — placeholder per OQ-I; maintainer
  surfaces the candidate by Phase 0 gate per §1.3.1; if no
  candidate by Phase 0 gate, §1.3.1 procedure fires).
- Capture: terminal recording, time-to-`synthesized`, every place
  the user paused, every place they had to ask the maintainer.
- Output artifact: `reporting/docs/second_user_onboarding_2026-XX.md`
  with verbatim feedback + remediation plan (each item triaged
  P0/P1/P2 per §1.3).

**Acceptance:**
- One full session reaches `synthesized` **with at most one brief
  in-session question to the maintainer** (the load-bearing
  acceptance criterion; "brief" = a single clarifying question that
  doesn't require the maintainer to operate the keyboard or read
  the user's screen). Multiple interventions or any maintainer
  keyboard time = failure.
- Remediation list filed and triaged.
- If P0 items surface, they are addressed before any §2.F-§2.K
  eval-substrate W-id ships.

**Risk:** structural blocker (P0 remediation surfaces) reshapes the
cycle. Treat as a *good outcome* — better to surface now than after
v0.1.14 ships unproven. Candidate-absence path: §1.3.1.

### §2.B — W-PROV-1: source-row locator type + 1-domain demo (P0)

**Why P0.** v0.2.0 W52 weekly review depends on source-row locators
being a first-class type. Reconciliation §4 C10 named this as
non-deferrable for W52. Building W52 on the assumption that
provenance can be retrofitted is the most expensive sequencing
error available.

**Workstream:**
- Schema design: `source_row_locator` value type (table + pk +
  column + row-version), surfaceable in `recommendation_log` +
  `proposal_log` + future `weekly_review` + `claim_block`.
  Documented at `reporting/docs/source_row_provenance.md`.
- Migration 023 if the schema requires DDL (likely yes; new column
  on `recommendation_log` storing JSON locator).
- One end-to-end demonstration on a single domain (recovery R-rule
  firing) — proposal cites source rows; `hai explain` renders them;
  test asserts roundtrip.

**Files likely touched:**
- `core/state/migrations/023_source_row_locator.sql` (new).
- `core/writeback/proposal.py` (locator emission).
- `core/explain/render.py` (locator rendering).
- `verification/tests/test_source_row_locator_recovery.py` (new).
- `reporting/docs/source_row_provenance.md` (new).

**Acceptance:**
- Design doc filed.
- Recovery domain emits source-row locators on R-rule firing.
- `hai explain` renders locators in markdown + JSON modes.
- Roundtrip test asserts locator → DB-row resolution.
- Capabilities-manifest snapshot updates accepted (W-29-prep
  byte-stability gate accommodates W-PROV-1 surface change).

### §2.C — W-EXPLAIN-UX: `hai explain` confusion-vs-clarity review + P13 persona (P0)

**Why P0.** JMIR AI 2024 systematic review on XAI in clinical decision
support shows explanations can *reduce* trust when confusing.
Tandfonline 2025 shows high-confidence calibrated outputs can also
*reduce* diagnostic accuracy via overreliance. "Refusal IS the demo"
only works if the refusal is legible.

**Workstream:**
- Add P13 persona archetype to `verification/dogfood/personas/`:
  low-domain-knowledge user (no athletics background, basic English,
  smartphone-native but not CLI-native). Includes
  `expected_actions=` declarative contract per W-AK pattern.
- Manual review pass: run `hai explain` on three sample state
  trajectories; have the W-2U-GATE foreign user (or a separate
  candidate) read the output and report what they understood, what
  confused them, what they wanted to know.
- Output artifact: `reporting/docs/explain_ux_review_2026-XX.md`
  with structured findings list + remediation recommendations.

**Files likely touched:**
- `verification/dogfood/personas/p13_low_domain_knowledge.py`
  (new).
- `verification/dogfood/personas/__init__.py` (P13 registration).
- `reporting/docs/explain_ux_review_2026-XX.md` (new).

**Acceptance:**
- P13 persona added to `ALL_PERSONAS`; **matrix-only coverage for
  v0.1.14** (per F-PLAN-06; no demo-replay coverage required —
  W-Vb-3 owns P2-P12 demo-replay residual exclusively).
  Persona matrix re-runs clean (13 personas, 0 findings;
  matrix-clean = each persona reaches a synthesized plan or
  expected-defer state without crashes; no demo-replay assertion
  for P13).
- Foreign-user review session captured; structured findings filed
  in `explain_ux_review_2026-XX.md`.
- The findings doc **must contain a section titled "v0.2.0 W52
  prose obligations"** — each remediation listed as a structured
  item with: issue / proposed prose change / acceptance hook
  (per F-PLAN-05). v0.2.0 W52 PLAN authoring consumes this section
  and either implements or explicitly defers each item.

### §2.D — W-BACKUP: `hai backup` / `hai restore` / `hai export` (P0)

**Why P0.** A second user is likely to need a recovery path; without
one, state corruption or migration mistakes can break the audit
chain. privacy.md currently gives manual file-copy / deletion
guidance but no canonical `hai backup` / `hai restore` / `hai export`
command exists. (F-PLAN-12 corrected the original 90-day claim; the
gap is real even without quantification.)

**Workstream:**
- `hai backup [--dest path]` writes a versioned tarball containing
  state.db + JSONL audit logs + capabilities snapshot + version
  stamp.
- `hai restore <tarball>` reverses, verifies migration version
  compatibility, refuses on schema mismatch with documented
  recovery path.
- `hai export --format jsonl` consolidates existing partial export
  surfaces into a single structured stream (not net-new
  functionality — formalisation).
- `reporting/docs/recovery.md` step-by-step for state.db corruption,
  keyring loss, intervals.icu credential rotation, schema-mismatch.

**Files likely touched:**
- `cli.py` new `backup` / `restore` / `export` subparsers.
- `core/backup/` (new module).
- `verification/tests/test_backup_restore_roundtrip.py` (new).
- `reporting/docs/recovery.md` (new).

**Acceptance:**
- Roundtrip test (backup → wipe state.db → restore → identical
  `hai today` / `hai explain` output) passes in CI.
- Schema-mismatch case tested (older tarball + newer wheel refuses
  cleanly).
- `hai capabilities --human` updated to surface the new commands;
  byte-stability snapshot accepts the new entries.

### §2.E — W-FRESH-EXT: doc-freshness test extension (P1)

**Why P1.** `test_doc_freshness_assertions.py` (added v0.1.12 W-AC)
catches version-tag drift mechanically. The C-DRIFT-02/03/04 class
of contradictions caught in the post-v0.1.13 strategic research
were stale *content* references (v0.1.9 weekly review, v0.2 BCTO,
v0.3 first-run UX) — the mechanical test cannot catch these without
expansion.

Also catches: stale W-id references in informal doc sections (e.g.,
any W52 reference outside v0.2.0+ contexts is suspect after this
extension).

**Workstream:**
- Extend `test_doc_freshness_assertions.py` to grep ROADMAP.md /
  strategic_plan / tactical_plan for W-id references; cross-check
  against current cycle's PLAN.md scope.
- Cover the §21 mechanical citation pass on
  `strategic_research_2026-05-01.md` (per Codex F-RES-R2-06 deferral).

**Acceptance:**
- Test rejects W-id references in informal-section sites that
  don't match active workstreams.
- Test catches the 2 unsampled citation errors from §21 mechanical
  pass (or confirms they are absent).

### §2.F — W-AH: scenario fixture expansion (tactical-plan)

Per tactical_plan_v0_1_x.md §5.1: 30+ new per-domain scenarios.

**Acceptance:** scenario fixtures grow from current ~50 to 120+;
per-persona expected-behaviour table covers all 12 personas across
all 6 domains (W-AK declarative shape from v0.1.13 + W-AH coverage
expansion).

### §2.G — W-AI: ground-truth labelling methodology + maintainer review tool (tactical-plan)

Per tactical_plan §5.1. Includes A12 judge-adversarial fixtures
folded in.

**Acceptance:** `hai eval review` lets maintainer flag scenario
expected output (per eval_strategy/v1.md:233-234); judge-adversarial
fixture corpus covers prompt-injection / source-conflict / bias-
probe categories with ≥10 fixtures per category.

### §2.H — W-AJ: LLM-judge harness scaffold (tactical-plan)

Per tactical_plan §5.1. No model invocation in v0.1.14; clean
invocation interface for v0.2.2 W58J to plug into.

**Acceptance:** harness has stable invocation interface; v0.2.2 W58J
just needs to plug in the model.

### §2.I — W-AL: calibration eval — schema/report shape only (tactical-plan)

Per reconciliation A2: schema/report shape ships in v0.1.14;
correlation work deferred to v0.5+. FActScore-aware schema (per
post-v0.1.13 §13 E-1).

**Acceptance:** `core/eval/calibration_schema.py` (new) supports
FActScore-style atomic-claim decomposition.
`reporting/docs/calibration_eval_design.md` cites FActScore + MedHallu
as prior art.

### §2.J — W-AM: adversarial scenario fixtures (tactical-plan)

Per tactical_plan §5.1. Explicit "should escalate" cases.

### §2.K — W-AN: `hai eval run --scenario-set <set>` CLI (tactical-plan)

Per tactical_plan §5.1. Batch-eval CLI surface.

### §2.L — W-29: cli.py mechanical split (inherited from v0.1.13)

Per CP1 (v0.1.12) + v0.1.13 W-29-prep verdict (green; boundary table
at `reporting/docs/cli_boundary_table.md`).

**Workstream:** Split cli.py (9217 lines at v0.1.13) into:
- `cli/__init__.py` (main; <500 lines, dispatch only).
- `cli/_shared.py` (shared helpers; <2500 lines).
- 11 handler-group files (each <2500 lines per the boundary table).

**Acceptance:**
- `test_cli_parser_capabilities_regression.py` byte-stable through
  the split (the load-bearing gate).
- All existing CLI tests pass without modification.

### §2.M — W-Vb-3: persona-replay extension (inherited)

Per F-PLAN-06 + F-PLAN-R2-02 + F-PLAN-R3-02 (v0.1.13 deferred
items). **Owns the 9-persona residual exclusively
(P2/P3/P6/P7/P8/P9/P10/P11/P12); P13 (added by §2.C W-EXPLAIN-UX)
is matrix-only and out of scope for W-Vb-3 demo-replay coverage.**

**Acceptance:** 9 personas reach `synthesized` via demo replay;
`expected_actions` declarative contract enforced. May further
partial-close (e.g., 3-at-a-time) if the cycle shape requires;
v0.1.14 owns the full residual for the P2-P12 set only.

### §2.N — W-DOMAIN-SYNC: scoped contract test (inherited)

Per reconciliation L2 + Codex F-PLAN-09. Single truth table +
expected-subset assertions.

**Acceptance:** `verification/tests/test_domain_sync_contract.py`
(new) ensures the 8 hardcoded registry enumerations stay in sync;
note that `_DOMAIN_ACTION_REGISTRY` is intentionally Phase-A-only
and exempted explicitly.

---

## 3. Ship gates

| Gate | Target | Enforcement |
|---|---|---|
| Test surface | ≥ 2540 (≥ +47 vs v0.1.13's 2493) | `uv run pytest verification/tests -q` |
| Broader-warning gate | clean | `uv run pytest verification/tests -W error::Warning -q` |
| Mypy | 0 errors | `uvx mypy src/health_agent_infra` |
| Bandit | 0 Medium/High; Low ≤ 50 | `uvx bandit -ll -r src/health_agent_infra` |
| Ruff | All checks pass | `uvx ruff check src/health_agent_infra` |
| Capabilities byte-stability | split into expected-diff classes (per F-PLAN-04): **byte-identical** (zero diff) for W-29 mechanical split; **named parser/capabilities surface change accepted** for W-AN (`hai eval run --scenario-set`), W-BACKUP (`backup` / `restore` / `export` subparsers), and W-PROV-1 (locator type in proposal/recommendation rendering only — not a parser change). Regression test must fail any other diff. | `test_cli_parser_capabilities_regression.py` |
| Persona matrix | 13 personas (P1..P12 + P13), 0 findings, **matrix-clean** (no demo-replay assertion for P13 per F-PLAN-06; W-Vb-3 owns P2-P12 demo-replay) | `verification/dogfood/runner.py` |
| W-2U-GATE artifact | `reporting/docs/second_user_onboarding_2026-XX.md` exists | manual review |
| W-EXPLAIN-UX artifact | `reporting/docs/explain_ux_review_2026-XX.md` exists | manual review |
| W-BACKUP roundtrip | backup → wipe → restore → identical state | CI |
| W-FRESH-EXT | doc-freshness test rejects stale W-id refs in informal sections | CI |
| Codex IR verdict | SHIP or SHIP_WITH_NOTES | review chain |
| D14 plan-audit | PLAN_COHERENT within ≤5 rounds; if exceeds 5, maintainer re-scopes | review chain |
| Phase 0 (D11) gate | Internal sweep + audit-chain probe + persona matrix clean | maintainer review |
| Cycle tier | substantive declared at top of RELEASE_PROOF | per CP3 D15 |

---

## 4. Risks register

| Risk | Trigger | Mitigation |
|---|---|---|
| W-2U-GATE surfaces structural P0 blocker | Foreign user cannot reach `synthesized` | Cycle reshapes around fix per §1.3 sequencing constraint; downstream work moves to v0.1.15 without prejudice; treat as good outcome |
| W-2U-GATE candidate doesn't materialize | OQ-I unresolved by Phase 0 gate | §1.3.1 candidate-absence procedure: hold cycle / defer W-2U-GATE to v0.1.15 / re-author PLAN + re-D14. Maintainer chooses |
| W-PROV-1 schema design needs major change | Recovery R-rule demo reveals locator type insufficient (e.g., needs to span multiple tables) | v0.1.14 splits into substrate (W-PROV-1 only) + features (rest); v0.2.0 W52 absorbs the redesign |
| W-29 split breaks capabilities snapshot | Byte-stability regression test fails post-split | W-29-prep boundary table + green verdict already cleared this; rollback the split if regression appears at IR. Note §3 ship-gate diff classes: W-29 must be **byte-identical** (zero diff allowed) |
| W-Vb-3 partial-closes again | Same shape as v0.1.13 (3-at-a-time) | Honest partial-closure naming with v0.1.15 destination per AGENTS.md "Honest partial-closure naming" pattern; W-Vb-3 owns P2-P12 only (per F-PLAN-06) |
| W-EXPLAIN-UX foreign user unavailable | OQ-I candidate falls through | Use W-2U-GATE candidate for both; or defer W-EXPLAIN-UX to v0.1.15 if neither resolves; covered by §1.3.1 |
| Cycle exceeds 45-day budget | Cumulative effort overruns 32-45 envelope | Re-scope: defer one of W-AM / W-AN / W-FRESH-EXT to v0.1.15; substrate W-ids (W-2U-GATE / W-PROV-1 / W-BACKUP / W-29) are non-negotiable |
| D14 exceeds 5 rounds | New finding-density at round N > N-1 | Per §1.3 sequencing constraint + §1.3.1 candidate-absence procedure: maintainer re-scopes before implementation; surface to Codex why the cycle is settling slower than the empirical norm |

---

## 5. Effort estimate

**32-45 days, 1 maintainer, substantive cycle tier.**

Breakdown:
- P0 additions: 11-14 days (W-2U-GATE 2-3 + W-PROV-1 3-4 +
  W-EXPLAIN-UX 2 + W-BACKUP 3-4 + W-FRESH-EXT 1).
- Tactical-plan baseline: 11-16 days (W-AH 3-4 + W-AI 2-3 + W-AJ 2-3
  + W-AL 2 + W-AM 1-2 + W-AN 1-2).
- Inherited from v0.1.13: 7.5-10.5 days (W-29 3-4 + W-Vb-3 4-6 +
  W-DOMAIN-SYNC 0.5).
- Cycle overhead (D14 plan-audit, Phase 0 bug-hunt, IR rounds,
  RELEASE_PROOF authoring, ship-time freshness sweep): 2-4 days.

Total: **31.5-44.5 days**; reported as **32-45 days** to match the
arithmetic honestly (F-PLAN-02 corrected the original 30-40
round-down). If the cycle trends past 45 days, the §4 risks register
"Cycle exceeds 45-day budget" mitigation fires: defer one of
W-AM / W-AN / W-FRESH-EXT to v0.1.15.

D14 expectation: **4-5 rounds**. Per the cycle's §3 ship-gate
acceptance: if it exceeds 5 rounds, maintainer re-scopes. v0.1.13's
5-round settling on 17 W-ids is the prior; v0.1.14's 14 W-ids should
fall in the 4-5 range.

---

## 6. Cycle pattern compliance (D11 + D14)

### D11 (pre-PLAN bug-hunt) — required for substantive cycle

Per AGENTS.md D11: substantive releases run a structured hunt
before scoping PLAN.md.

- Internal sweep: lint pass on cli.py / core/synthesis.py /
  core/config.py for any v0.1.13-introduced drift not caught at
  ship.
- Audit-chain probe: `hai explain` reconcilability spot-check on
  3 recent fixture days.
- Persona matrix: 12 personas (pre-W-EXPLAIN-UX P13 addition),
  re-run clean.
- Optional Codex external bug-hunt audit (per maintainer
  discretion).

Findings consolidate to
`reporting/plans/v0_1_14/audit_findings.md`.

### D14 (pre-cycle Codex plan-audit) — required for substantive cycle

- `codex_plan_audit_prompt.md` authored from
  `reporting/plans/_templates/codex_plan_audit_prompt.template.md`.
- Codex returns verdict; maintainer responds; PLAN.md revises until
  `PLAN_COHERENT`.
- Empirical norm: 4 rounds, 10→5→3→0 signature; v0.1.14 expectation
  4-5 rounds per §1.4 acceptance.

### Pre-implementation gate

Maintainer reads `audit_findings.md`. Findings tagged
`revises-scope` may revise PLAN.md (loop back to D14). Findings
tagged `aborts-cycle` may end the cycle. Implementation does not
start until this gate fires.

### CP application status (per F-PLAN-11)

| CP | Status | Application target |
|---|---|---|
| **CP-2U-GATE-FIRST** | implemented-in-PLAN | PLAN §1.3 + §1.3.1 + §2.A |
| **CP-MCP-THREAT-FORWARD** | applied-pre-cycle 2026-05-01 | strategic_plan_v1.md Wave 3 staging |
| **CP-DO-NOT-DO-ADDITIONS** | applied-pre-cycle 2026-05-01 | AGENTS.md "Do Not Do" (3 new bullets) |
| **CP-PATH-A** | applied-pre-cycle 2026-05-01 | tactical_plan_v0_1_x.md §6/§7/§8/§9 + ROADMAP.md + strategic_plan_v1.md Wave 2 |
| **CP-W30-SPLIT** | applied-pre-cycle 2026-05-01 | AGENTS.md D4 + "Do Not Do" line |

All five CP files' `Codex verdict:` status fields update post-D14
round 1 to "applied at v0.1.14 D14 round 1
(PLAN_COHERENT_WITH_REVISIONS); revisions per F-PLAN-07/08/09/10
applied to source documents in lockstep."

CP-MCP-THREAT-FORWARD is **already applied** pre-cycle to
strategic_plan_v1.md Wave 3 (F-PLAN-11 corrected the original
"lands at v0.1.14 ship" wording).

---

## 7. Provenance

This PLAN is the direct output of:

1. **Post-v0.1.13 strategic research**
   (`reporting/plans/post_v0_1_13/strategic_research_2026-05-01.md`)
   — synthesised 2026-05-01; Codex-audited 2 rounds (round 1: 10
   findings 9 ACCEPT 1 PARTIAL; round 2: 7 findings all ACCEPT);
   closed REPORT_SOUND_WITH_REVISIONS.
2. **Reconciliation**
   (`reporting/plans/post_v0_1_13/reconciliation.md`) —
   consolidates audit chain + per-finding dispositions.
3. **Maintainer OQ resolution 2026-05-01:**
   - All yes-default OQs (A, C, D, E, F, G, H, K, L, N, O) accepted.
   - OQ-B: Path A (4-release strict-C6).
   - OQ-I: TBD placeholder for W-2U-GATE candidate.
   - OQ-J: option 2 (draft AgentSpec README framing; surface for
     review before applying — pending).
   - OQ-M: default (`hai support` in v0.2.0).
4. **CPs authored under
   `reporting/plans/post_v0_1_13/cycle_proposals/`:**
   - `CP-2U-GATE-FIRST.md`
   - `CP-MCP-THREAT-FORWARD.md`
   - `CP-DO-NOT-DO-ADDITIONS.md` (applied to AGENTS.md 2026-05-01)
   - `CP-PATH-A.md` (applied to tactical_plan + AGENTS.md
     2026-05-01)
   - `CP-W30-SPLIT.md` (applied to AGENTS.md 2026-05-01)
5. **v0.1.13 release artifacts:**
   - `reporting/plans/v0_1_13/RELEASE_PROOF.md` §5 named deferrals.
   - `reporting/plans/v0_1_13/CARRY_OVER.md`.

The empirical-settling shape of the post-v0.1.13 audit chain
(round 1: 10 → round 2: 7 → closed) matches the D14 plan-audit
prior. Per OQ-O, the research-audit pattern itself remains ad-hoc
until a second strategic-research cycle uses it; not a D16
candidate at N=1.
