# v0.1.14 PLAN — Eval expansion + LLM-judge prep + provenance substrate

**Status:** D14 PLAN_COHERENT (round 4 close); **Phase 0 (D11)
gate fired 2026-05-01**; **W-2U-GATE deferred to v0.1.15** at
pre-implementation gate per `pre_implementation_gate_decision.md`
(§1.3.1 path 2; cycle scope reshaped to 13 W-ids).
**Authored:** 2026-05-01.
**Cycle tier (D15):** substantive (13 W-ids; ≥3 governance-or-audit-chain
edits; ≥10 days estimated; the v0.1.14-original "≥1 release-blocker
workstream W-2U-GATE" trigger fired before W-2U-GATE moved to
v0.1.15, so the substantive tier still holds on the remaining
two triggers).
**Estimated effort:** 30-43 days (1 maintainer; was 32-45 pre-defer;
W-2U-GATE 2-3 d removed). Matches §5 arithmetic 29.5-42.5;
F-PLAN-R2-01 corrected the metadata-surface miss from D14 round 1.
**D14 expectation:** **CLOSED at round 4** (PLAN_COHERENT_WITH_REVISIONS
with 1 nit, applied; settling shape 12 → 7 → 3 → 1-nit → CLOSE
mirrors v0.1.13 exactly).
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
source-row provenance type that v0.2.0 W52 will require; ship the
second-user recovery path (`hai backup` / `hai restore` /
`hai export`); and close the v0.1.13-deferred mechanical workstreams
(W-29 cli.py split, W-Vb-3 9-persona residual, W-DOMAIN-SYNC
contract test). Foreign-machine onboarding empirical proof
(W-2U-GATE) **is deferred to v0.1.15** per the pre-implementation
gate decision (no candidate on file; §1.3.1 path 2; see
`pre_implementation_gate_decision.md`).

End-state: **v0.2.0 starts with the source-row primitive + judge
harness in tree, reducing design risk** (v0.2.0 W52/W58D still ships
weekly-review aggregation + deterministic claim-block + claim corpus
in 18-24 days — *not* a wire-up release; F-PLAN-01 corrected).
`hai backup` / `hai restore` / `hai export` give second users a
recovery path; cli.py is split per the v0.1.13 W-29-prep boundary
table without breaking byte-stability of the capabilities snapshot.
Foreign-user empirical validation lands in v0.1.15 once a
candidate is on file.

### 1.2 Workstream catalogue (13 W-ids)

**Sequencing.** §1.3 below names the post-defer order: **W-PROV-1
runs first** (was second under CP-2U-GATE-FIRST; W-2U-GATE moved to
v0.1.15 at the pre-implementation gate).

| Section | W-id | Title | Effort | Tier | Source |
|---|---|---|---|---|---|
| §2.A | ~~W-2U-GATE~~ | **Deferred to v0.1.15** (no candidate on file at gate; §1.3.1 path 2) | 2-3 d → v0.1.15 | P0 → next-cycle | post-v0.1.13 §5 P0-1 + CP-2U-GATE-FIRST + `pre_implementation_gate_decision.md` |
| §2.B | W-PROV-1 | Source-row locator type + 1-domain demo | 3-4 d | P0 | post-v0.1.13 §5 P0-2 |
| §2.C | W-EXPLAIN-UX | `hai explain` confusion-vs-clarity review + P13 persona (foreign-user review uses maintainer-substitute reader per §1.3.1 path 2) | 2 d | P0 | post-v0.1.13 §5 P0-3 |
| §2.D | W-BACKUP | `hai backup` / `hai restore` / `hai export` | 3-4 d | P0 | post-v0.1.13 §5 P0-5 |
| §2.E | W-FRESH-EXT | Doc-freshness test extension + persona-runner demo-session pre-flight (F-PHASE0-01 absorption) | 1.5 d | P1 | post-v0.1.13 §6 P1-5 + audit_findings F-PHASE0-01 |
| §2.F | W-AH | Scenario fixture expansion (30+ new) | 3-4 d | tactical-plan | tactical_plan §5.1 |
| §2.G | W-AI | Ground-truth labelling methodology + maintainer review tool | 2-3 d | tactical-plan | tactical_plan §5.1 |
| §2.H | W-AJ | LLM-judge harness scaffold (no model invocation yet) | 2-3 d | tactical-plan | tactical_plan §5.1 |
| §2.I | W-AL | Calibration eval — schema/report shape only (FActScore-aware) | 2 d | tactical-plan | tactical_plan §5.1 + reconciliation A2 |
| §2.J | W-AM | Adversarial scenario fixtures (judge-adversarial corpus) | 1-2 d | tactical-plan | tactical_plan §5.1 |
| §2.K | W-AN | `hai eval run --scenario-set <set>` CLI surface | 1-2 d | tactical-plan | tactical_plan §5.1 |
| §2.L | W-29 | cli.py mechanical split (1 main + 1 shared + 11 handler-group) | 3-4 d | inherited | v0.1.13 RELEASE_PROOF §5 + CP1 |
| §2.M | W-Vb-3 | Persona-replay extension (9 non-ship-set personas) | 4-6 d | inherited | v0.1.13 RELEASE_PROOF §5 + F-PLAN-06/R2-02/R3-02 |
| §2.N | W-DOMAIN-SYNC | Scoped contract test (single truth table) | 0.5 d | inherited | reconciliation L2 + Codex F-PLAN-09 |

**Total:** 13 W-ids (down from 14 at D14 close); **30-43 days**
(matches §5 arithmetic 29.5-42.5; was 32-45 pre-defer);
substantive tier.

### 1.3 Sequencing (post-defer)

CP-2U-GATE-FIRST sequenced W-2U-GATE first; W-2U-GATE has been
deferred to v0.1.15 at the pre-implementation gate (§1.3.1 path 2;
see `pre_implementation_gate_decision.md`). The
post-W-2U-GATE order from the original §1.3 now applies directly,
with **W-PROV-1 as the first implementation workstream**:

1. **W-PROV-1** (foundation for v0.2.0 W52; needs to land before W-AH/W-AI scenario work that may reference source-row provenance).
2. W-29 mechanical cli.py split (mechanical refactor; lands early to avoid merge friction with later substantive edits).
3. W-DOMAIN-SYNC (small contract test; trivial after W-29).
4. W-EXPLAIN-UX (P13 persona + foreign-user review uses maintainer-substitute reader per §1.3.1 path 2; folds W-AK declarative-actions contract).
5. W-BACKUP (independent of eval substrate).
6. Eval substrate W-AH/W-AI/W-AJ/W-AL/W-AM/W-AN (parallelizable).
7. W-Vb-3 (parallelizable with eval substrate).
8. W-FRESH-EXT (last; doc-fix sweep + persona-runner demo-session pre-flight aware of all changes).

**If a foreign-user candidate surfaces during the cycle**, a
mid-cycle CP under
`reporting/plans/v0_1_14/cycle_proposals/CP-2U-GATE-PULL-FORWARD.md`
may pull W-2U-GATE back into v0.1.14. The workstream is already
PLAN-audited; the original §2.A contract (preserved below) still
applies. No re-D14 is required.

### 1.3.1 Candidate-absence procedure (per F-PLAN-03 + R2-04 timing fix) — **path 2 invoked 2026-05-01**

W-2U-GATE has a hard external dependency on a non-maintainer
candidate. The OQ-I placeholder ("TBD") had to resolve before
W-2U-GATE could open. Phase 0 (D11 bug-hunt: internal sweep, audit-
chain probe, 12-persona matrix) did *not* depend on the foreign
user and proceeded regardless (see `audit_findings.md`). Procedure:

- **Hard rule:** named candidate must be on file by the
  **pre-implementation gate** (after Phase 0 closes, before
  W-2U-GATE — the first implementation workstream — opens).
  D14 audits the PLAN, not coordination state; Phase 0 audits the
  pre-cycle code/audit-chain state, not the candidate. "On file"
  means: maintainer has identified the candidate, contacted them,
  and confirmed availability for the recorded session.
- **At the 2026-05-01 pre-implementation gate, no candidate was on
  file.** The maintainer's three options were:
  1. **Hold W-2U-GATE / implementation.** Phase 0 bug-hunt complete;
     pre-implementation gate withholds implementation start until
     candidate surfaces OR option 2/3 fires.
  2. **Defer W-2U-GATE to v0.1.15** with named destination; v0.1.14
     opens implementation without it. W-EXPLAIN-UX foreign-user
     review uses a maintainer-substitute reader (or also defers to
     v0.1.15 without prejudice). Cycle reshapes around the absence.
  3. **Re-author PLAN.md** (rescope around the absence) and re-run
     D14. Use this path if the maintainer believes W-2U-GATE
     should not be sequenced first under the absence (e.g., if
     candidate availability is a long horizon and v0.1.14 should
     proceed on substrate work first).
- **Path 2 chosen** (see `pre_implementation_gate_decision.md`).
  W-2U-GATE deferred to v0.1.15. W-EXPLAIN-UX foreign-user review
  uses a maintainer-substitute reader (the maintainer reading
  `hai explain` output with a foreign-user lens) per §2.C below.
  v0.1.14 opens implementation with W-PROV-1 first.

### 1.4 Deferrals (named, with destination)

The post-v0.1.13 strategic research surfaced items that do NOT
ship in v0.1.14:

| Item | Deferred to | Reason |
|---|---|---|
| **W-2U-GATE (foreign-machine onboarding empirical proof)** | **v0.1.15** (per `pre_implementation_gate_decision.md`; §1.3.1 path 2) | No candidate on file at 2026-05-01 pre-implementation gate; W-EXPLAIN-UX foreign-user review uses maintainer-substitute reader in v0.1.14 |
| W-2U-GATE-2 (second foreign user) | v0.2.0 doc-only adjunct (was scheduled after v0.1.14 W-2U-GATE; v0.2.0 destination preserved — sequenced after v0.1.15 W-2U-GATE first-foreign-user lands) | Sequenced after v0.1.15 remediation |
| W-MCP-THREAT (MCP threat-model artifact) | v0.2.0 doc-only adjunct | Per CP-MCP-THREAT-FORWARD; precedes v0.3 PLAN-audit |
| W-COMP-LANDSCAPE (`competitive_landscape.md`) | v0.2.0 doc-only adjunct | Per OQ-E |
| W-NOF1-METHOD (`n_of_1_methodology.md`) | v0.2.0 doc-only adjunct | Per OQ-E |
| W-FACT-ATOM (FActScore atomic decomposition) | v0.2.0 (folds into W58D) | Lands when W58D ships |
| W-JUDGE-BIAS (CALM bias panel) | v0.2.2 (folds into W58J) | Lands when W58J ships per Path A |
| `hai support` redacted bundle | v0.2.0 (per OQ-M default) | v0.1.14 still at 13 W-ids |
| AgentSpec README framing (per OQ-J option 2) | **applied 2026-05-01** at pre-implementation gate (per `pre_implementation_gate_decision.md`) | README opener now positions HAI as a domain-pinned AgentSpec implementation for personal health |
| §21 mechanical citation pass on strategic-research report | bundled with W-FRESH-EXT | Codex round-2 deferred per F-RES-R2-06 |
| privacy.md hosted-agent-exposure tightening (P2-5) | v0.1.14 W-EXPLAIN-UX-adjacent doc | Symmetry with README:34-38 |

---

## 2. Per-workstream contracts

### §2.A — W-2U-GATE: foreign-machine onboarding empirical proof (**deferred to v0.1.15**)

**Status (2026-05-01).** **Deferred to v0.1.15** at the
pre-implementation gate per §1.3.1 path 2 (no foreign-user
candidate on file at gate; OQ-I unresolved). See
`pre_implementation_gate_decision.md`. Original contract preserved
below for v0.1.15 carry-forward and as the contract that applies
if a mid-cycle candidate surfaces and the workstream is pulled
back into v0.1.14 via `cycle_proposals/CP-2U-GATE-PULL-FORWARD.md`.

**Original contract (preserved for v0.1.15 / mid-cycle pull-forward):**

**Why first** *(in the original PLAN — now decoupled)*. v0.1.13
shipped the test surface for "trusted first value" (W-AA, W-AF,
W-A1C7). This workstream produces the empirical proof that the
test surface holds against a non-maintainer user. Every later
workstream inherits the foreign-machine-onboarding risk; if
W-2U-GATE surfaces a structural blocker, the cycle reshapes.

**Workstream:**
- One recorded foreign-machine onboarding session by a non-
  maintainer (candidate: TBD — surfaced by maintainer at v0.1.15
  D14 / pre-implementation gate per §1.3.1).
- Capture: terminal recording, time-to-`synthesized`, every place
  the user paused, every place they had to ask the maintainer.
- Output artifact:
  `reporting/docs/second_user_onboarding_2026-XX.md` with verbatim
  feedback + remediation plan (each item triaged P0/P1/P2 per
  §1.3 of the v0.1.15 PLAN).

**Acceptance:**
- One full session reaches `synthesized` **with at most one brief
  in-session question to the maintainer** (load-bearing acceptance
  criterion). Multiple interventions or any maintainer keyboard
  time = failure.
- Remediation list filed and triaged.
- If P0 items surface in v0.1.15, they are addressed before any
  v0.1.15 substrate W-id ships.

**Risk:** structural blocker (P0 remediation surfaces) reshapes
the v0.1.15 cycle. Treat as a *good outcome* — better to surface
in v0.1.15 than after v0.1.15 ships unproven. Candidate-absence
path: §1.3.1 (which carries forward to v0.1.15 PLAN authoring).

### §2.B — W-PROV-1: source-row locator type + 1-domain demo (P0)

**Why P0.** v0.2.0 W52 weekly review depends on source-row locators
being a first-class type.
`reporting/plans/future_strategy_2026-04-29/reconciliation.md` §4
C10 named this as non-deferrable for W52 (per F-PLAN-R2-06: the
unqualified "reconciliation §4 C10" was ambiguous after the
post-v0.1.13 reconciliation file was added; full path now cited).
Building W52 on the assumption that provenance can be retrofitted
is the most expensive sequencing error available.

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
  trajectories. **Per §1.3.1 path 2 (W-2U-GATE deferred to
  v0.1.15), the v0.1.14 review uses a maintainer-substitute
  reader** — the maintainer reading `hai explain` output with a
  foreign-user lens (a deliberate "what would a low-domain-knowledge
  user not understand here?" pass), captured against the P13
  persona's expected confusion modes. Foreign-user review of the
  same trajectories carries forward to v0.1.15 W-2U-GATE; this
  v0.1.14 pass is the maintainer-confidence baseline before the
  empirical foreign-user pass lands.
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
- **Maintainer-substitute review** session captured (per §1.3.1
  path 2; foreign-user review carries forward to v0.1.15 W-2U-GATE);
  structured findings filed in `explain_ux_review_2026-XX.md` with
  an explicit "carries-forward-to-v0.1.15-W-2U-GATE-foreign-user-pass"
  section listing items that must re-test against an actual
  foreign user once W-2U-GATE opens.
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

### §2.E — W-FRESH-EXT: doc-freshness test extension + persona-runner demo-session pre-flight (P1)

**Why P1.** `test_doc_freshness_assertions.py` (added v0.1.12 W-AC)
catches version-tag drift mechanically. The C-DRIFT-02/03/04 class
of contradictions caught in the post-v0.1.13 strategic research
were stale *content* references (v0.1.9 weekly review, v0.2 BCTO,
v0.3 first-run UX) — the mechanical test cannot catch these without
expansion. Plus: F-PHASE0-01 (Phase 0 audit_findings.md) surfaced a
hermeticity bug in the persona harness where a stale demo-session
marker silently sandboxes the first persona's first proposes; the
pre-flight cleanup is a sibling hardening adjunct that fits this
workstream's mechanical-test-coverage scope.

Also catches: stale W-id references in informal doc sections (e.g.,
any W52 reference outside v0.2.0+ contexts is suspect after this
extension).

**Workstream:**
- Extend `test_doc_freshness_assertions.py` to grep ROADMAP.md /
  strategic_plan / tactical_plan for W-id references; cross-check
  against current cycle's PLAN.md scope.
- Cover the §21 mechanical citation pass on
  `strategic_research_2026-05-01.md` (per Codex F-RES-R2-06 deferral).
- **F-PHASE0-01 absorption (runner-hardening adjunct).** Add a
  pre-flight step to `verification/dogfood/runner.py` that calls
  `hai demo cleanup` before the first persona runs; refuse to run
  if cleanup returns a non-empty `removed_marker_ids` list (a stale
  marker existed when the harness started — emits a clear error
  rather than silently sandboxing the first persona's proposes).
  This prevents the F-PHASE0-01 transient from re-occurring on
  any future Phase 0 sweep that runs in a maintainer environment
  with prior `hai demo` activity. Effort: ~3 lines + 1 test.

**Acceptance:**
- Test rejects W-id references in informal-section sites that
  don't match active workstreams.
- Test catches the 2 unsampled citation errors from §21 mechanical
  pass (or confirms they are absent).
- Persona runner pre-flight refuses to run with an active demo
  marker; test asserts the refusal path emits a `hai demo cleanup`
  remediation hint.

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
| ~~W-2U-GATE artifact~~ | **deferred to v0.1.15** (per pre-implementation gate decision; gate carries forward to v0.1.15 ship-gate row) | — |
| W-EXPLAIN-UX artifact | `reporting/docs/explain_ux_review_2026-XX.md` exists with maintainer-substitute review (per §1.3.1 path 2) + carries-forward-to-v0.1.15 section | manual review |
| W-BACKUP roundtrip | backup → wipe → restore → identical state | CI |
| W-FRESH-EXT | doc-freshness test rejects stale W-id refs in informal sections; persona-runner pre-flight refuses with active demo marker | CI |
| Codex IR verdict | SHIP or SHIP_WITH_NOTES | review chain |
| D14 plan-audit | **CLOSED at round 4 (PLAN_COHERENT)**; pre-implementation defer per §1.3.1 path 2 does not require re-D14 | review chain |
| Phase 0 (D11) gate | **fired green 2026-05-01** (audit_findings.md committed `20dd3c4`) | maintainer review |
| Cycle tier | substantive declared at top of RELEASE_PROOF | per CP3 D15 |

---

## 4. Risks register

| Risk | Trigger | Mitigation |
|---|---|---|
| ~~W-2U-GATE surfaces structural P0 blocker~~ | (W-2U-GATE deferred to v0.1.15; risk migrates to v0.1.15 PLAN) | Carries to v0.1.15 risks register |
| ~~W-2U-GATE candidate doesn't materialize~~ | **Triggered 2026-05-01.** OQ-I unresolved at pre-implementation gate; §1.3.1 path 2 invoked (defer to v0.1.15) per `pre_implementation_gate_decision.md` | Closed for v0.1.14; v0.1.15 D14 re-surfaces OQ-I with same §1.3.1 paths available |
| Mid-cycle candidate surfaces but pull-forward CP introduces second-order issues | Maintainer drafts `CP-2U-GATE-PULL-FORWARD.md` mid-cycle | CP must include a summary-surface sweep (per AGENTS.md pattern); if the maintainer is uncertain about second-order impact, re-D14 instead |
| W-PROV-1 schema design needs major change | Recovery R-rule demo reveals locator type insufficient (e.g., needs to span multiple tables) | v0.1.14 splits into substrate (W-PROV-1 only) + features (rest); v0.2.0 W52 absorbs the redesign |
| W-29 split breaks capabilities snapshot | Byte-stability regression test fails post-split | W-29-prep boundary table + green verdict already cleared this; rollback the split if regression appears at IR. Note §3 ship-gate diff classes: W-29 must be **byte-identical** (zero diff allowed) |
| W-Vb-3 partial-closes again | Same shape as v0.1.13 (3-at-a-time) | Honest partial-closure naming with v0.1.15 destination per AGENTS.md "Honest partial-closure naming" pattern; W-Vb-3 owns P2-P12 only (per F-PLAN-06) |
| W-EXPLAIN-UX maintainer-substitute review surfaces a confusion mode the maintainer cannot judge from inside | Maintainer cannot honestly evaluate "would a low-domain-knowledge user understand this?" from inside | Carries-forward-to-v0.1.15 section in `explain_ux_review_2026-XX.md` lists items that must re-test against the v0.1.15 W-2U-GATE foreign user; v0.1.14 ships the maintainer-confidence baseline, v0.1.15 confirms or remediates against the empirical foreign-user pass |
| Cycle exceeds 43-day budget | Cumulative effort overruns 30-43 envelope (post-defer) | Re-scope: defer one of W-AM / W-AN / W-FRESH-EXT to v0.1.15; substrate W-ids (W-PROV-1 / W-BACKUP / W-29) are non-negotiable. Pulling W-2U-GATE forward via mid-cycle CP raises the budget by 2-3 d; account for the increase before pulling |
| D14 exceeds 5 rounds | New finding-density at round N > N-1 | Per §3 ship gate + §5 D14 expectation: maintainer re-scopes before implementation; surface to Codex why the cycle is settling slower than the empirical norm. (R2-05 corrected the original §1.3 / §1.3.1 cross-refs — §1.3.1 governs candidate absence, not round-count rescope.) |

---

## 5. Effort estimate

**30-43 days, 1 maintainer, substantive cycle tier** (post-defer
of W-2U-GATE; was 32-45 days at D14 close).

Breakdown:
- P0 additions: 9.5-11.5 days (W-PROV-1 3-4 + W-EXPLAIN-UX 2 +
  W-BACKUP 3-4 + W-FRESH-EXT 1.5; **W-2U-GATE 2-3 d removed**;
  W-FRESH-EXT +0.5 d for F-PHASE0-01 absorption).
- Tactical-plan baseline: 11-16 days (W-AH 3-4 + W-AI 2-3 + W-AJ 2-3
  + W-AL 2 + W-AM 1-2 + W-AN 1-2).
- Inherited from v0.1.13: 7.5-10.5 days (W-29 3-4 + W-Vb-3 4-6 +
  W-DOMAIN-SYNC 0.5).
- Cycle overhead (D14 plan-audit closed at round 4, Phase 0
  bug-hunt closed 2026-05-01, IR rounds, RELEASE_PROOF authoring,
  ship-time freshness sweep): 2-4 days.

Total: **29.5-42.5 days**; reported as **30-43 days** to match
the arithmetic honestly. If the cycle trends past 43 days, the
§4 risks register "Cycle exceeds 43-day budget" mitigation fires:
defer one of W-AM / W-AN / W-FRESH-EXT to v0.1.15.

D14 status: **CLOSED at round 4** (PLAN_COHERENT_WITH_REVISIONS
with 1 nit; nit applied; mirrors v0.1.13's 4-round
12 → 7 → 3 → 1-nit → CLOSE settling shape on 14-W-id substantive
PLANs). The pre-implementation defer of W-2U-GATE per §1.3.1
path 2 does not require re-D14 (the path is the canonical
candidate-absence handler explicitly anticipated by the audited
PLAN).

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
  4-5 rounds per §3 ship gate (R2-05 corrected the original
  "§1.4 acceptance" reference — §1.4 is the deferrals table).

### Pre-implementation gate

Maintainer reads `audit_findings.md`. Findings tagged
`revises-scope` may revise PLAN.md (loop back to D14). Findings
tagged `aborts-cycle` may end the cycle. Implementation does not
start until this gate fires.

### CP application status (per F-PLAN-11)

| CP | Status | Application target |
|---|---|---|
| **CP-2U-GATE-FIRST** | implemented-in-PLAN at D14 close; **W-2U-GATE deferred to v0.1.15 at pre-implementation gate** per §1.3.1 path 2 (CP-2U-GATE-FIRST status: applied-but-deferred; original sequencing intent carries forward to v0.1.15) | PLAN §1.3 + §1.3.1 + §2.A + `pre_implementation_gate_decision.md` |
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

> **Reconciliation row-label citation convention (per F-PLAN-R3-03):**
> Throughout this PLAN and tactical_plan_v0_1_x.md, citations to
> reconciliation row labels (A1..A12, L1..L6, C1..C10, D1..D4) refer
> to `reporting/plans/future_strategy_2026-04-29/reconciliation.md`
> (the 2026-04-29 Claude/Codex deep-strategy review) unless
> otherwise stated with a full path. The 2026-05-01
> `reporting/plans/post_v0_1_13/reconciliation.md` file (which
> consolidates the post-v0.1.13 strategic-research audit chain) does
> not use these row labels.

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
   - OQ-I: TBD placeholder for W-2U-GATE candidate **at D14 close;
     resolved at pre-implementation gate 2026-05-01 via §1.3.1
     path 2 (defer W-2U-GATE to v0.1.15)** per
     `pre_implementation_gate_decision.md`.
   - OQ-J: option 2 (draft AgentSpec README framing) **applied
     2026-05-01 at pre-implementation gate** per
     `pre_implementation_gate_decision.md`.
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
