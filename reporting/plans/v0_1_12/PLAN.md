# v0.1.12 — Carry-over closure + trust repair

> **Status.** Authored 2026-04-29 by Claude. **D14 plan-audit chain
> closed: `PLAN_COHERENT` at round 4 (2026-04-29).** Rounds 1-3
> verdicts `PLAN_COHERENT_WITH_REVISIONS` (10 + 5 + 3 = 18
> findings, all closed); round 4 verdict `PLAN_COHERENT`, no
> findings. All six cycle proposals (CP1-CP6) accepted by Codex
> in round-3 audit; round-4 confirmed no second-order regression.
> Cycle tier (per CP3 four-tier classification): **substantive**.
>
> **Audit-chain artifacts in this folder:**
> `codex_plan_audit_prompt.md`,
> `codex_plan_audit_response.md` (round 1),
> `codex_plan_audit_response_round_1_response.md`,
> `codex_plan_audit_round_2_response.md`,
> `codex_plan_audit_round_2_response_response.md`,
> `codex_plan_audit_round_3_response.md`,
> `codex_plan_audit_round_3_response_response.md`,
> `codex_plan_audit_round_4_response.md`,
> `codex_plan_audit_round_4_response_response.md`.
>
> **Empirical settling pattern (matches v0.1.11):** 10 → 5 → 3 → 0
> findings across 4 rounds. v0.1.11 settled at the same shape.
>
> **Next gate: Phase 0 (D11) pre-PLAN bug-hunt.** Authored as
> `PRE_AUDIT_PLAN.md` in this folder when the cycle opens.
> Findings consolidate to `audit_findings.md` with
> `cycle_impact` tags; pre-implementation gate fires after
> consolidation per §6.
>
> **Source.**
> - `reporting/plans/future_strategy_2026-04-29/reconciliation.md` §6
>   action list (items #1-6 + cross-cutting).
> - `reporting/plans/v0_1_11/RELEASE_PROOF.md` §5 carry-overs.
> - Maintainer adjudication 2026-04-29 of disagreements
>   D1 (v0.2.0 shape: substantial + LLM-judge-shadow-by-default),
>   D2 (cli.py: split when convenient), D3 (four-tier classification),
>   D4 (MCP: gated, ship when ready).
>
> **Cycle pattern (D11 + D14 active).**
> 1. PLAN.md draft (this file).
> 2. Codex plan-audit → revise until `PLAN_COHERENT`. Empirical norm
>    for substantive cycles is 2-4 rounds.
> 3. Phase 0 (D11) pre-PLAN bug-hunt → `audit_findings.md`.
> 4. Pre-implementation gate. `revises-scope` findings may revise
>    PLAN.md (loop back to step 2 if large). `aborts-cycle` findings
>    may end the cycle.
> 5. Implementation rounds with Codex review until verdict is SHIP /
>    SHIP_WITH_NOTES.
> 6. `RELEASE_PROOF.md` + `REPORT.md`.

---

## 1. What this release ships

### 1.1 Theme

**Trust repair, not feature push.** Three things this cycle is for:

1. Close-or-honestly-partial-close every named-deferred item from
   v0.1.11 (W-Vb, W-H2, W-N broader gate, F-A-04, F-A-05,
   F-B-04 *design+prototype only — multi-domain closure deferred
   to v0.1.13 W-FBC-2*, F-C-05). Where a deferred item cannot
   close fully in this cycle, the residual is named explicitly
   in §1.3 with a destination cycle (per Codex F-PLAN-R2-04).
2. Repair trust surfaces — public docs that no longer match the
   shipped product, a packaging bug that breaks the demo on a clean
   wheel install, and an asymmetry in the D13 threshold-injection
   seam (four of six domains read raw `t["policy"][...]` without
   `coerce_*` helpers).
3. Document six cycle proposals (CP1-CP6) that the v0.1.13+
   roadmap depends on — lifting the cli.py split deferral, lifting
   the capabilities-manifest schema-freeze deferral, adopting the
   four-tier cycle-weight classification, adopting the staged MCP
   exposure plan, adopting the v0.2.0 substantial-with-shadow shape,
   and a §6.3 strategic-plan framing edit.

Substantive in tier (multiple cycle-proposal docs, demo packaging
contract change, broader test gate) but light in code volume — the
heaviest single workstream is the W-N broader resource-warning
sweep (~3-4 days).

### 1.2 Workstream catalogue

| W-id | Title | Severity | Files (primary) | Source | Effort |
|---|---|---|---|---|---|
| **W-AC** | Public-doc freshness sweep + ship-checklist | trust | `README.md`, `ROADMAP.md`, `HYPOTHESES.md`, `AUDIT.md`, `reporting/plans/README.md`, `success_framework_v1.md`, `AGENTS.md` | C1 + A8 + C9 | 0.5d |
| **W-CARRY** | Carry-over register | audit-chain | `reporting/plans/v0_1_12/CARRY_OVER.md` (new) | F-FS-02 | 0.5d |
| **W-Vb** | `hai demo` polish — persona fixture loading + packaging path | demo polish + packaging | `src/health_agent_infra/core/demo/fixtures.py` (new), `src/health_agent_infra/demo/fixtures/` (packaged tree, new), `verification/dogfood/personas/__init__.py` | v0.1.11 named-defer + C3 | 3-4d |
| **W-H2** | Mypy stylistic class | correctness | `cli.py`, `core/synthesis.py`, scenario-result paths, others per F-A-04 / F-A-05 | v0.1.11 named-defer | 2-3d |
| **W-N-broader** | `-W error::Warning` gate (47 ResourceWarning sites) | correctness | `core/state/store.py` + every raw `sqlite3.Connection` site | v0.1.11 named-defer | 3-4d |
| **W-D13-SYM** | D13-symmetry contract test + fix | trusted-seam | `domains/{recovery,running,sleep,stress}/policy.py`, `verification/tests/test_d13_symmetry_contract.py` (new) | L1 | 0.5-1d |
| **W-PRIV** | Privacy doc updates + `hai auth remove` subcommand | trust | `reporting/docs/privacy.md`, `cli.py`, `core/capabilities/walker.py` | C4 | 0.5-1d |
| **W-FBC** | F-B-04 design + recovery prototype (multi-domain closure deferred to v0.1.13 W-FBC-2 per Codex F-PLAN-R2-04) | audit-chain | `core/synthesis.py`, `cli.py` (`--re-propose-all`), `core/capabilities/walker.py`, `reporting/docs/supersede_domain_coverage.md` (new), `verification/tests/test_supersede_domain_coverage.py` (new) | v0.1.11 named-defer | 1-2d |
| **W-FCC** | F-C-05 — `strength_status` enum surfaceability | UX | `core/capabilities/walker.py`, `cli.py` today handler | v0.1.11 named-defer | 1d |
| **W-CP** | Cycle proposals CP1-CP6 (governance docs) | governance | `reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md` (new) | D1-D4 + L3 | 1d |

**Approximate effort:** 13-20 days, single-contributor. No
release-blocker workstream — every item could in principle defer
again to v0.1.13 — but the cycle's *theme* (carry-over closure)
fails if more than two named-defers slip a second time.

### 1.3 Out of scope (named-deferred to later cycles)

| Item | Defer to | Reason |
|---|---|---|
| A1 trusted-first-value rename + C7 acceptance matrix | v0.1.13 | onboarding cycle owns the gate language |
| A5 declarative persona expected-actions (W-AK pulled forward) | v0.1.13 | precondition for v0.1.14 W58 prep |
| C2 / W-LINT regulated-claim lint | v0.1.13 | first surface; lands before v0.2.0 weekly review |
| W-29-prep cli.py boundary audit (half-day) | v0.1.13 | per CP1 |
| W-29 cli.py mechanical split (1 main + 1 shared + 11 handler-group, <2500 each) | v0.1.14 | per CP1, conditional on prep verdict |
| L2 W-DOMAIN-SYNC scoped contract test (single truth table + expected-subset assertions; not all 8 named tables are six-domain registries — `_DOMAIN_ACTION_REGISTRY` is intentionally Phase-A-only) | v0.1.14 | per reconciliation action 12 (re-scoped per Codex F-PLAN-09) |
| **W-FBC-2** — F-B-04 multi-domain closure (full supersede policy implementation across all six domains; per-domain fingerprint primitive if option B/C chosen at v0.1.12 design) | v0.1.13 | per Codex F-PLAN-R2-04 — v0.1.12 W-FBC delivers design + recovery prototype only |
| A12 judge-adversarial fixtures | v0.1.14 | folds into W-AI per reconciliation action 14 |
| A2 / W-AL calibration scaffold (schema/report shape only) | v0.1.14 | real correlation work to v0.5+ |
| W52 weekly review + W53 insight ledger + C8 evidence-card schema + C5 deterministic claim-block + W58 LLM-judge **shadow-by-default** with `HAI_W58_JUDGE_MODE` feature flag (memory-poisoning fixtures land alongside) | v0.2.0 | per CP5 — single substantial release; flag flip to blocking happens within v0.2.0 (or v0.2.0.x patch) once shadow-mode evidence supports it. Not a release boundary. |
| W-30 capabilities-manifest schema freeze | v0.2.0 | per CP2 (after W52/W58 schema additions land) |
| MCP server *plan* (read surface only; threat-model + provenance prereqs) | v0.3 | per CP4 |
| MCP read surface ship | v0.4 or v0.5 | per CP4 (gated by prereqs) |
| L3 §6.3 strategic-plan framing edit | v0.1.13 strategic-plan rev | per CP6 |

---

## 2. Per-workstream contracts

### 2.1 W-AC — Public-doc freshness sweep + ship-checklist

**Note (Codex F-PLAN-02 round 1).** Two of the three "confirmed on
disk 2026-04-29" reconciliation-C1 instances were already fixed
during the same-day reorg (`HYPOTHESES.md` now points to
`strategic_plan_v1.md` directly; `reporting/plans/README.md` was
rewritten as a cold-session reading index post-v0.1.11 ship).
v0.1.12 W-AC scope rebaselined here.

Concrete remaining instances:

- `ROADMAP.md:13` says "v0.1.8 current" and points to the
  superseded multi-release roadmap → update to v0.1.11 shipped,
  v0.1.12 in flight; point to `tactical_plan_v0_1_x.md`. (Verified
  stale on disk by Codex F-PLAN-02.)
- `README.md`, `AUDIT.md`: spot-check at workstream start for
  version references that lag; absorb into scope only if drift
  found.
- `HYPOTHESES.md`, `reporting/plans/README.md`: spot-check at
  workstream start to confirm Codex-verified post-reorg state still
  holds; remove from W-AC scope if so.

Plus reconciliation A8 (ship-time freshness checklist) + C9
(defer-rate anti-gaming):

- Append a "freshness checklist" subsection to AGENTS.md "Release
  Cycle Expectation" listing the docs that must reflect the
  shipped state at ship time. (Replaces the manual sweep with a
  permanent process artifact.)
- One-line edit to `success_framework_v1.md`: "lower defer rate is
  *not* better if it comes from false confidence."

**Acceptance.**

- Every public doc named above reflects v0.1.11-shipped state.
- AGENTS.md "Release Cycle Expectation" gains the freshness
  checklist.
- `success_framework_v1.md` has the anti-gaming line.
- A new test (`verification/tests/test_doc_freshness_assertions.py`)
  scans docs for version-tag drift against the package version
  string (`importlib.metadata.version("health-agent-infra")`) and
  fails on any doc that names an older version as "current."

### 2.2 W-CARRY — Carry-over register

New doc: `reporting/plans/v0_1_12/CARRY_OVER.md`. Every v0.1.11
named-defer with disposition row.

Items (from v0.1.11 RELEASE_PROOF §5):

| Item | Disposition |
|---|---|
| W-Vb | in-cycle (W-Vb here) |
| W-H2 | in-cycle (W-H2 here) |
| W-N broader gate | in-cycle (W-N-broader here) |
| F-A-04 | in-cycle (W-H2 covers) |
| F-A-05 | in-cycle (W-H2 covers) |
| F-B-04 | partial-closure in v0.1.12 (W-FBC: design doc + recovery prototype + `--re-propose-all` override flag) → multi-domain closure deferred to v0.1.13 W-FBC-2 (per Codex F-PLAN-R2-04) |
| F-C-05 | in-cycle (W-FCC here) |
| W52 / W53 / W58 | defer-with-reason → v0.2.0+ per CP5 |

Plus implicit carry-overs from the reconciliation:

| Item | Disposition |
|---|---|
| C3 fixture-packaging | in-cycle (W-Vb here) |
| C4 privacy doc | in-cycle (W-PRIV here) |
| L1 D13-symmetry | in-cycle (W-D13-SYM here) |
| C1 doc-freshness | in-cycle (W-AC here) |
| A8 freshness checklist | in-cycle (W-AC here) |
| C9 anti-gaming note | in-cycle (W-AC here) |

**Acceptance.** Every line in `v0_1_11/RELEASE_PROOF.md` §5 has a
disposition row in the register. Every reconciliation §6 item
flagged as v0.1.12 has a row.

### 2.3 W-Vb — `hai demo` persona-replay + fixture-packaging path

**Current state (verified by Codex F-PLAN-06 against
`cli.py:8530-8537`, `core/demo/session.py:226-230`,
`pyproject.toml:53-62`).**

The `--persona` flag on `hai demo start` is accepted for
forward-compatibility, but `open_session()` only records the
persona slug; **no fixture is loaded.** No runtime import from
`verification.dogfood` exists in `src/health_agent_infra`. The
`pyproject.toml` package-data list has no `demo/fixtures/**`
entry, so the future packaged-fixture path will need packaging
metadata once added.

**Demo flow today** stops at the runtime/skill boundary (see
`v0_1_11/RELEASE_PROOF.md` §2.7) — `hai daily --skip-pull --source
csv` returns `overall_status: "awaiting_proposals"` because no
`hai propose` has run. The prior PLAN claim that a clean wheel
install fails with `ModuleNotFoundError` was inferred, not
reproduced; corrected.

**Two coupled deliveries (order matters: (a) before (b)).**

**(a) Packaged-fixture path + loader.** Add
`src/health_agent_infra/demo/fixtures/` packaged module tree with
persona-state fixtures (one JSON per persona slug). Update
`pyproject.toml` package-data to include the fixture tree. Build
a runtime fixture loader at
`src/health_agent_infra/core/demo/fixtures.py` with
packaged-resource path resolution (`importlib.resources` or
equivalent).

**(b) Persona fixture loading wired into `open_session()`.**
Extend `open_session()` to load fixtures and pre-populate
proposals so the demo reaches synthesis. After W-Vb:
`hai demo start --persona p1` opens the demo session AND seeds
proposals; `hai daily` reaches `synthesized`; `hai today`
renders a populated plan.

**Note (Codex F-PLAN-R2-01).** Current CLI semantics
(`cli.py:6346-6350`) set `persona = None` whenever `--blank` is
true — the prior PLAN incorrectly combined `--persona p1
--blank`. v0.1.12 W-Vb keeps `--blank` as the explicit
empty-session mode (boundary-stop demo) and uses
`--persona p1` *without* `--blank` for persona-replay. Two
modes, two spellings, no overload of `--blank` semantics.

**Files.**

- `src/health_agent_infra/demo/fixtures/p1.json` etc. (new) —
  serialised persona-state fixtures.
- `src/health_agent_infra/core/demo/fixtures.py` (new) — loader.
- `src/health_agent_infra/core/demo/session.py` — extend
  `open_session()` to call the loader.
- `pyproject.toml` — package-data list extended with
  `demo/fixtures/**`.
- `verification/dogfood/personas/__init__.py` — kept; harness
  fixtures stay separate from packaged fixtures (sync risk
  surfaced by Codex F-PLAN audit Q4 — see §4 risks).

**Tests.**

- `verification/tests/test_demo_fixtures_packaging.py` (new) —
  builds wheel via `python -m build` in tmpdir, installs into
  clean venv, runs `hai demo start --persona p1` as subprocess,
  asserts `overall_status == "synthesized"` after `hai daily`,
  and `hai today` returns 0. **Proves both that package data is
  included and that persona-replay works.** Separate test
  invocation under `--blank` (no persona) confirms boundary-stop
  semantics are preserved (regression guard against
  F-PLAN-R2-01).
- `verification/tests/test_demo_persona_replay.py` (new) —
  exercises persona-replay flow against scratch state with
  isolation contract preserved (real `~/.health_agent` and real
  `state.db` byte-identical before / after).

**Acceptance.**

- `pip install dist/*.whl && hai demo start --persona p1 &&
  hai daily ... && hai today` reaches synthesis on a clean
  venv.
- Separate invocation `hai demo start --blank` retains current
  empty-session boundary-stop semantics (regression guard for
  F-PLAN-R2-01).
- `pyproject.toml` package-data lists the fixture tree.
- Persona-replay flow byte-identical-isolation contract preserved
  (subprocess test).
- W-Z § A becomes canonical when this lands; v0.1.11 boundary-stop
  transcript stays in `v0_1_11/RELEASE_PROOF.md` as historical
  proof for the v0.1.11 surface.

### 2.4 W-H2 — Mypy stylistic class

Reduce the 21 mypy errors at v0.1.11 ship to ≤ 5. Class: Literal
abuse, redefinition warnings, scenario-result type confusion,
`pandas-import-untyped`. Per v0.1.11 PLAN scope declaration.

**Files.** Per F-A-04 / F-A-05 spread across `cli.py`,
`core/synthesis.py`, `evals/runner.py`, plus pandas-import sites.

**Acceptance.** `uv run mypy src/health_agent_infra` returns ≤ 5
errors. Surviving errors documented in PLAN with deferral reason.

### 2.5 W-N-broader — `-W error::Warning` gate

47 ResourceWarning failures from unclosed `sqlite3.Connection`
patterns at v0.1.11 ship (RELEASE_PROOF §2.2). Systemic refactor;
touches every site that opens raw connections without a context
manager.

**Pattern.** Every connection site uses context-manager or
explicit close. The ship gate is a CI command run **outside the
test suite** to avoid in-suite recursion (Codex F-PLAN-08 caught
that the prior in-suite test would have run pytest from inside
pytest).

**Files.** `core/state/store.py` + every raw `sqlite3.Connection`
site (TBD by audit at workstream start).

**Two named commands — audit vs ship (Codex F-PLAN-R3-01).** The
v0.1.11-deferred target is the catch-all `-W error::Warning`
gate. W-N owns:

- **Audit command** (run at workstream start to count failures
  and pick the fallback branch):
  `uv run pytest verification/tests -W error::Warning -q`.
  This is the broader v0.1.11-deferred target, not the
  ResourceWarning-only narrowing.
- **Ship command(s)** — per fallback branch (matches §3 ship
  gate row):

| Audit count | Ship command | Cycle outcome |
|---|---|---|
| ≤ 80 | `uv run pytest verification/tests -W error::Warning -q` | full broader gate ships in v0.1.12 |
| 80-150 | `uv run pytest verification/tests -W error::ResourceWarning::sqlite3 -q` | v0.1.12 ships sqlite3-only ResourceWarning gate; W-N-broader-2 (v0.1.13) carries the residual `Warning` categories; named-defer in `v0_1_12/RELEASE_PROOF.md` §5 |
| > 150 | `uv run pytest verification/tests -W error::pytest.PytestUnraisableExceptionWarning -q` | v0.1.12 keeps v0.1.11 narrow gate; entire broader-gate work carries to v0.1.13 W-N-broader; named-defer recorded |

**Tests.**

- `verification/tests/test_warning_gate_smoke.py` (new) —
  exercises one canonical state-DB workflow under
  `warnings.simplefilter("error", ResourceWarning)` to catch
  regression on the cleanest path. **Not** a recursive full-suite
  invocation.
- The audit and ship commands above run as CI workflow / Makefile
  targets (separate from in-suite tests) at top level. Lives in
  `.github/workflows/` or `Makefile` (TBD at workstream start).

**Acceptance.**

- Audit command run at workstream start; site count recorded in
  PLAN at fork point.
- Selected ship command exits 0.
- Fallback decision documented in PLAN; named-defer recorded in
  RELEASE_PROOF §5 if scope narrowed.

### 2.6 W-D13-SYM — D13-symmetry contract test + fix

Closes L1 from reconciliation.

**Today.** Six domain `policy.py` files. Strength + nutrition use
`core.config.coerce_*` helpers correctly; recovery + running +
sleep + stress read raw `t["policy"][...]` values without going
through the helpers. The threshold-injection seam is defended at
load time by `_validate_threshold_types`, but a future caller that
constructs threshold dicts in-memory and bypasses `load_thresholds`
silently coerces bool-as-int in those four domains.

**Two parts.**

(a) Add `coerce_int / coerce_float / coerce_bool` to recovery,
running, sleep, stress `policy.py` at every threshold-read site.
Mechanical change — already correct in the other two domains.

(b) Add a contract test that scans `domains/*/policy.py` for raw
`t["policy"][...]` reads and fails on new ones. Future PR adding a
raw read gets caught.

**Files.** `domains/{recovery,running,sleep,stress}/policy.py`,
`verification/tests/test_d13_symmetry_contract.py` (new).

**Acceptance.** Contract test green; AST-level scan covers all six
domains; `_validate_threshold_types` defence + consumer-site
defence are both in place.

### 2.7 W-PRIV — Privacy doc updates + `hai auth remove` subcommand

Per reconciliation C4 + Codex F-PLAN-02 / F-PLAN-R2-03 spot-
verify against `reporting/docs/privacy.md`:

- `privacy.md:59-60` says no credential-removal command exists.
  **Decision (Q3 resolution, locked at PLAN authoring + revised
  per F-PLAN-R2-03): ship `hai auth remove` as a subcommand.**
  The `clear_garmin()` and `clear_intervals_icu()` helpers
  already exist at `core/pull/auth.py:171` and
  `core/pull/auth.py:261` respectively (verified on disk
  2026-04-29 — *not* `core/credentials.py` as the prior PLAN
  said). The missing piece is a CLI surface + a capabilities row.
  ~half-day delivery.
- **CLI grammar (Codex F-PLAN-R2-03):** `hai auth remove
  [--source garmin|intervals-icu|all]` as a *subcommand*, not
  a flag. The current `auth` parser
  (`cli.py:6505-6506`) already requires subcommands and exposes
  `auth garmin`, `auth intervals-icu`, `auth status`. `auth
  remove` fits the existing pattern; `auth --remove` would
  fight the parser.
- `privacy.md:116-120` says no first-class "forget one day"
  exists. Reword to point to existing per-row delete path; defer
  the dedicated command to v0.1.13 onboarding cycle.
- ~~chmod failure semantics on shared filesystems~~ — out of
  scope. Codex F-PLAN-02 confirmed behaviour is already documented
  at `privacy.md:44-46`.

**Files.**

- `reporting/docs/privacy.md` — line 59-60 + line 116-120 edits.
- `cli.py` — new `hai auth remove [--source garmin|intervals-icu|all]`
  subcommand handler routed to `core/pull/auth.py`'s existing
  `clear_garmin()` / `clear_intervals_icu()` methods.
- `core/capabilities/walker.py` — capabilities row for the new
  subcommand.

**Acceptance.**

- `hai auth remove --source garmin` / `--source intervals-icu` /
  `--source all` removes credentials cleanly via
  `core/pull/auth.py` helpers.
- `hai capabilities --json | jq '.commands[] | select(.command == "hai auth remove")'`
  returns a non-empty row (Codex F-PLAN-R3-02: manifest
  `commands` is an array of rows keyed by `command` field, not
  a dict keyed by command string — `core/capabilities/walker.py:1-27`).
- Privacy doc accurately describes the shipping CLI surface; no
  doc-says-X-but-X-doesn't-exist mismatches.

### 2.8 W-FBC — F-B-04 domain-coverage drift across supersession

From v0.1.11 PLAN.md §1.2 deferral. Semantic question: when a
`_v2` plan supersedes `_v1`, which domains carry over their
proposals vs re-emit?

**Current state (Codex F-PLAN-07 verified against
`core/synthesis.py:423-455`).** State fingerprinting is global
over upstream state surfaces, proposal payloads, and Phase A
firings. **There is no per-domain fingerprint primitive shipped.**
Without that primitive, "only changed-input domains re-propose"
cannot be implemented across all six domains in this cycle —
v0.1.12's prior option-B framing was over-committed.

**Reframe to design-first (Codex F-PLAN-07 round 1 + F-PLAN-R2-04
round 2).** v0.1.12 W-FBC delivers a *partial closure* of F-B-04:
the policy decision, a one-domain prototype, and an override flag.
**Multi-domain closure is named-deferred to v0.1.13 W-FBC-2** (see
§1.3) — v0.1.12 does not claim to close F-B-04 fully. v0.1.12
W-FBC delivers:

(a) **Policy decision documented.** A new
`reporting/docs/supersede_domain_coverage.md` names the chosen
policy (option A "all domains re-propose" / option B "changed-
input only" with per-domain fingerprint primitive / option C
"hybrid with staleness signal") with rationale.

**Default heading-into-design: option A.** Clean, no new
primitive needed, slightly more compute. Option B's per-domain
fingerprint primitive is treated as v0.1.13 W-FBC-2 work if
chosen.

(b) **One-domain prototype.** Implement the policy for one
domain (recovery — smallest surface) end-to-end through
`hai daily --supersede`. Validates the approach without
committing all six.

(c) **`--re-propose-all` override flag.** Add to `hai daily`
regardless of policy choice — escape hatch for the maintainer.
This *is* a CLI/capabilities change.

(d) **Named persona scenarios.** P1 (morning fresh-state), P5
(thin-history with state delta), P9 (supersede after intake
change).

**Files.**

- `core/synthesis.py` — supersede-policy implementation for the
  chosen option; recovery as the prototype domain.
- `cli.py` — `--re-propose-all` flag on `hai daily`.
- `core/capabilities/walker.py` — new flag in capabilities.
- `reporting/docs/supersede_domain_coverage.md` (new) — policy
  decision doc.
- `verification/tests/test_supersede_domain_coverage.py` (new) —
  exercises P1, P5, P9 against the prototype domain.

**Acceptance.**

- Policy decision doc exists with rationale.
- One-domain prototype (recovery) passes
  `test_supersede_domain_coverage.py` against P1, P5, P9.
- `--re-propose-all` override surfaced in capabilities;
  documented behaviour.
- **Full multi-domain rollout is deferred to v0.1.13 W-FBC-2 for
  the chosen policy** (Codex F-PLAN-R3-03 — unconditional
  regardless of A/B/C). v0.1.12 only proves the design and the
  one-domain prototype. If option B/C is selected, W-FBC-2 also
  owns the per-domain fingerprint primitive (the additional
  B/C-specific surface).

### 2.9 W-FCC — F-C-05 `strength_status` enum surfaceability

From v0.1.11 PLAN.md §1.2. Strength status enum
(`deload_recommended`, `volume_spike`, `coverage_insufficient`,
etc.) is internal; `hai today` does not surface them as user-
facing labels. Either expose via capabilities + `hai today
--verbose`, or annotate as internal-only.

**Decision.** Expose via capabilities + `hai today --verbose`.
`hai capabilities --json | jq '.commands[] | select(.command == "hai today")'`
returns a row that includes the enum surface (Codex F-PLAN-R3-02:
manifest `commands` is an array of rows, not a dict keyed by
command string — `core/capabilities/walker.py:1-27`). The
surfacing is read-only and does not change synthesis behaviour.

**Files.** `core/capabilities/walker.py`, `cli.py` today handler.

**Acceptance.** Capabilities manifest lists the enum surface;
`hai today --verbose` prints status alongside recommendation;
contract test ensures every enum value appears in the manifest.

### 2.10 W-CP — Cycle proposals (CP1-CP6)

Six short proposal documents under
`reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md`. Each
follows the AGENTS.md cycle-proposal pattern: rationale, **current
text quoted verbatim**, proposed delta (exact replacement),
affected files, dependent cycles, per-CP verdict gate.

**Replaces prior implicit-approval framing (Codex F-PLAN-04).**
Each CP carries an explicit `accepted | accepted-with-revisions |
rejected` gate with named fallback if rejected.

#### CP1 — Lift cli.py-split deferral

**Current AGENTS.md "Settled Decisions" text (verbatim):**

> **W-29 / W-30 deferred.** Do not split `cli.py`. Do not freeze
> the capabilities manifest schema yet.

**Plus current "Do Not Do" entry (verbatim):**

> Do not split `cli.py` or freeze the capabilities manifest
> schema in this cycle.

**Paired with CP2 — these two CPs jointly replace the W-29/W-30
settled-decision bullet and the Do Not Do bullet.** Either CP
alone leaves a partially-replaced bullet; the maintainer applies
the fragment that matches the accepted half.

**Proposed delta (CP1 + CP2 jointly accepted) — replace
"Settled Decisions" entry with:**

> **W-29 / W-30 scheduled.** cli.py split scheduled for v0.1.14
> conditional on v0.1.13 boundary-audit verdict
> (parser/capabilities regression test mandatory regardless).
> Capabilities-manifest schema freeze scheduled for v0.2.0 after
> W52/W58 schema additions land.

**Replace "Do Not Do" entry with:**

> Do not split `cli.py` or freeze the capabilities manifest
> schema before their scheduled cycles (v0.1.14 / v0.2.0).

**Acceptance gate (per-CP).**

- `accepted`: revised PLAN.md ships with proposal doc + AGENTS.md
  edit applied at v0.1.12 ship.
- `accepted-with-revisions`: revisions applied to proposal;
  AGENTS.md edit deferred to next cycle pending revision-of-
  revisions sign-off.
- `rejected`: AGENTS.md unchanged; v0.1.13 W-29-prep workstream
  removed from tactical plan; CP1 archived in cycle_proposals/.

#### CP2 — Lift capabilities-manifest-freeze deferral

**Paired with CP1.** Same AGENTS.md bullets quoted above. Same
combined delta.

**If CP1 accepted but CP2 rejected (or vice versa),** the
AGENTS.md replacement text is adjusted at ship-time to keep the
rejected half intact. Maintainer applies the fragment.

**Downstream contract implications (Codex F-PLAN-03 Q4 hidden
coupling).** Schema freeze at v0.2.0 means W-FCC's
`strength_status` enum surface added in v0.1.12 must be back-
compat with whatever shape ships at the v0.2.0 freeze. Any
v0.1.12 manifest additive must be designed not to break at the
freeze.

**Acceptance gate (per-CP).** Same `accepted /
accepted-with-revisions / rejected` shape as CP1.

#### CP3 — Adopt 4-tier cycle-weight classification

**Current AGENTS.md text:** no tier classification exists.

**Proposed delta — add to "Settled Decisions":**

> **(D15, v0.1.12) Cycle-weight tiering.** Substantive /
> hardening / doc-only / hotfix. RELEASE_PROOF.md declares
> chosen tier. D11 + D14 audit weight scales: substantive cycles
> run full Phase 0 + multi-round D14; hardening cycles may run
> abbreviated Phase 0; doc-only and hotfix may skip both.

**Self-application (Codex F-PLAN Q4 paradox-flag).** v0.1.12
declares `tier: substantive`. Resolution per Q2:

- If CP3 `accepted`: v0.1.12 RELEASE_PROOF declares `tier:
  substantive`.
- If CP3 `accepted-with-revisions`: v0.1.12 RELEASE_PROOF declares
  per the revised D15 wording.
- If CP3 `rejected`: v0.1.12 RELEASE_PROOF omits the tier line;
  D11/D14 audit weight follows pre-v0.1.12 norm.

**Acceptance gate (per-CP).** Same 3-state shape.

#### CP4 — Stage and gate the existing MCP-exposure plan

**Current strategic plan text (verified on disk 2026-04-29 per
Codex F-PLAN-R2-05).** Strategic plan §10 *does* have an MCP
row at `strategic_plan_v1.md:444`:

> ### Wave 3 — MCP surface + extension contract (v0.3–v0.4,
> ~3-4 months)

Plus `strategic_plan_v1.md:632` references "at v0.4 (when MCP
surface ships)." The MCP exposure direction is already documented.

**The real gap (Codex F-PLAN-R2-05).** The existing Wave 3 row
lacks: (a) staged exposure design (read surface only, no write
surface), (b) provenance import contract, (c) least-privilege
read-scope model, (d) threat-model gate. CP4 extends the existing
row with these gates rather than adding a new row.

**Proposed delta — extend strategic plan §10 Wave 3 with:**

> **Staging within Wave 3.**
>
> - **v0.3** — *plans* MCP server (read-surface design,
>   threat-model artifact, provenance import contract).
> - **v0.4** — *prereqs* land (least-privilege read-scope model,
>   threat-model doc at `reporting/docs/mcp_threat_model.md`,
>   provenance contract enforced through one full domain).
> - **v0.4-or-v0.5** — *ships* MCP read surface. **No write
>   surface ever.**

**Security gate (Codex Q4 + MCP-spec).** No MCP read surface
ships before:

- Least-privilege read-scope model documented.
- Threat-model artifact at
  `reporting/docs/mcp_threat_model.md` names: resource audience
  validation, confused-deputy risk, token-passthrough risk, SSRF
  risk, with stated mitigations for each.
- Provenance contract verified through one full domain end-to-
  end.

Sources cited in the proposal doc (verify current at v0.4
authoring):

- <https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization>
- <https://modelcontextprotocol.io/specification/2025-06-18/basic/security_best_practices>

**Acceptance gate (per-CP).** Same 3-state shape; security-gate
language is non-negotiable in any `accepted-with-revisions` path.

#### CP5 — Adopt v0.2.0 substantial-with-shadow shape (D1)

**Maintainer adjudication (chat 2026-04-29).**

- "I would like v0.2.0 to be pretty substantial, we can always
  fix bugs in future is they appear."
- On the LLM judge specifically: "we should be more cautious on
  the LLM judge in blocking mode."

**Synthesis (single-release shape).** v0.2.0 = W52 weekly review
+ W53 insight ledger + W58 deterministic claim-block (blocking
from day 1) + W58 LLM judge **shadow-by-default** with feature
flag (`HAI_W58_JUDGE_MODE = shadow | blocking`) to flip to
blocking. The shadow-to-blocking flip is a feature flag in
v0.2.0 (or a v0.2.0.x patch), **not a separate release
boundary.**

**Proposed delta — strategic plan §6 + tactical plan §6**
(replaces 3-release split with single-release shape):

> **v0.2.0** — Weekly review (W52) + insight ledger (W53) +
> factuality gate (W58). Deterministic claim-block enforced from
> day 1; LLM judge ships shadow-by-default with feature flag
> (`HAI_W58_JUDGE_MODE = shadow | blocking`); flag flip to
> blocking happens within v0.2.0 (or via v0.2.0.x patch) once
> shadow-mode evidence supports it. Memory-poisoning fixtures
> land alongside shadow mode.

**Acceptance gate (per-CP).**

- `accepted`: strategic + tactical plan §6 reshaped at ship; PLAN
  §1.3 deferral table reflects single v0.2.0 row.
- `accepted-with-revisions`: revised shape applied.
- `rejected`: strategic + tactical plans unchanged; v0.2.0 PLAN
  re-scopes when authored next cycle; PLAN §1.3 reverts to 3-
  release-split shape.

#### CP6 — Strategic plan §6.3 framing edit (L3)

**Current strategic plan §6.3 text.** Verify verbatim at
proposal-doc authoring (CP6 dirfile must include the verbatim
quote). The reconciliation L3 finding noted §6.3 frames the moat
as a "publishable rule DSL."

**Proposed delta — rephrase §6.3 to:**

> The defensible substrate is the audit chain (three-state
> `proposal_log → planned_recommendation → daily_plan`
> reconciliation), the skill-overlay invariant
> (`_overlay_skill_drafts` whitelists 3 keys, raises on anything
> else, no skill imports in runtime code), and the Phase B write-
> surface guard (`guard_phase_b_mutation`). The R-rule + X-rule
> DSL is competent engineering, not novel theory.

**Application timing (Codex F-PLAN-05 resolution).** CP6 is
**authored** in v0.1.12 as a proposal doc with the target text-
delta recorded. The actual strategic plan §6.3 edit is **applied
at the v0.1.13 strategic-plan revision** alongside other tactical
adjustments. v0.1.12 ship does *not* require the §6.3 edit to
land.

**Acceptance gate (per-CP).**

- `accepted`: proposal doc authored at v0.1.12 ship; v0.1.13
  strategic-plan rev applies the §6.3 edit per recorded delta.
- `accepted-with-revisions`: revised wording applied at v0.1.13.
- `rejected`: proposal doc archived in cycle_proposals/;
  strategic plan §6.3 unchanged.

---

**Definition of done for W-CP** (replaces prior
implicit-approval framing per Codex F-PLAN-04).

- All six proposal docs authored at
  `reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md`.
- Each proposal doc contains: rationale, **current text quoted
  verbatim**, proposed delta (verbatim replacement), affected
  files, dependent cycles, per-CP verdict gate.
- Codex round-N D14 audit returns per-CP verdict (`accepted /
  accepted-with-revisions / rejected`) for each. Verdicts captured
  in audit-response file.
- v0.1.12 ship applies AGENTS.md / strategic plan / tactical plan
  deltas only for CPs with `accepted` verdict (or
  `accepted-with-revisions` after revisions land). **CP6
  application deferred to v0.1.13 strategic-plan rev** per its
  acceptance gate.
- `RELEASE_PROOF.md` records per-CP final verdict +
  applied-vs-deferred status.

---

## 3. Ship gates

| Gate | Threshold |
|---|---|
| Tests | ≥ 2347 + 15 new = **≥ 2362** |
| Mypy | **≤ 5 errors** (W-H2) |
| Bandit | 0 unsuppressed Medium/High at `bandit -ll` (unchanged from v0.1.11) |
| Pytest warning gate (W-N-broader) | **Command chosen by W-N fork decision exits 0** (per §2.5 fallback ladder, Codex F-PLAN-R2-02): full `-W error::Warning -q` only on the ≤80-sites branch; `-W error::ResourceWarning::sqlite3 -q` on the 80-150 branch with named residuals deferred; v0.1.11 narrow `-W error::pytest.PytestUnraisableExceptionWarning -q` on the >150 branch with broader gate deferred to v0.1.13 W-N-broader. RELEASE_PROOF declares the chosen branch + records the named-defer if narrowed. |
| Capabilities | byte-identical across runs (unchanged); `hai capabilities --markdown` reflects strength_status surface (W-FCC) and `hai auth remove` subcommand (W-PRIV) |
| Demo regression | **`hai demo start --persona p1` reaches synthesis end-to-end on a clean wheel install** (Codex F-PLAN-R2-01: `--blank` removed — current CLI semantics make `--blank` mutually exclusive with persona); `hai today` renders populated plan; isolation contract byte-identical preserved; separate `hai demo start --blank` invocation regression-tested for empty-session boundary-stop semantics (W-Vb) |
| D13 symmetry | contract test green; all six domain `policy.py` files use `coerce_*` helpers (W-D13-SYM) |
| Doc freshness | every public-facing doc reflects v0.1.11-shipped state; freshness-assertion test green (W-AC) |
| Carry-over register | every line in `v0_1_11/RELEASE_PROOF.md` §5 has disposition row; every reconciliation §6 v0.1.12 item has a row (W-CARRY) |
| Cycle proposals | CP1-CP6 authored at `reporting/plans/v0_1_12/cycle_proposals/CP{1..6}.md` per W-CP DoD; per-CP verdicts captured in audit-response files; **CP1-CP5 deltas applied at v0.1.12 ship for `accepted` verdicts** (CP6 application deferred to v0.1.13 strategic-plan rev) (W-CP) |
| Tier classification | RELEASE_PROOF.md declares `tier: substantive` (CP3) — falls back to no tier line if CP3 rejected, per CP3 acceptance gate |

---

## 4. Risks

- **W-N-broader scope creep.** 47 ResourceWarning sites is a *lower
  bound* — sqlite3 patterns may surface more under stricter gate.
  If audit at workstream start reveals > 80 sites, split as
  W-N-broader-2 → v0.1.13.
- **W-Vb fixture-packaging coupling.** Pre-populating proposals
  depends on the packaged-resource path being reliable; the
  fix-then-extend ordering matters. Land C3 packaging fix *first*,
  then the persona-loading work. The wheel-install test catches
  the order if it inverts.
- **W-CP / D14 timing.** Six cycle proposals are documents, but
  CP1, CP2, CP4, CP5 reverse or extend AGENTS.md "Settled
  Decisions" — substantive enough that the D14 plan-audit may
  surface revisions to one or more. **Budget 2-4 D14 rounds for
  this PLAN.md** per the v0.1.11 empirical norm.
- **Demo-flow contract change.** W-Vb changes the demo contract
  from "stops at boundary" (v0.1.11 isolation-replay) to "reaches
  synthesis" (v0.1.12 persona-replay). The v0.1.11 boundary-stop
  transcript stays in v0_1_11/RELEASE_PROOF as historical proof;
  v0.1.12's RELEASE_PROOF documents the new transcript.
- **F-B-04 partial-closure scope** (revised post-Codex F-PLAN-07
  round 1 + F-PLAN-R2-04 round 2). Per-domain fingerprint
  primitive does not exist today. v0.1.12 W-FBC delivers
  *partial closure* — design doc + recovery prototype + override
  flag. **Full multi-domain F-B-04 closure is named-deferred to
  v0.1.13 W-FBC-2** (see §1.3 and §2.2 W-CARRY). Risk: claiming
  full closure here would overstate what the cycle delivers;
  Codex round 2 caught this. Risk on the partial closure: the
  one-domain prototype may not surface compute-cost issues that
  emerge only in multi-domain production state — budget revisit
  at v0.1.13 W-FBC-2 design.
- **W-Vb harness/packaged fixture sync.** Packaged fixtures live
  at `src/health_agent_infra/demo/fixtures/`; harness fixtures
  live at `verification/dogfood/personas/`. Drift between them
  means demo and persona-test surfaces describe different state.
  Mitigation: `test_demo_persona_replay.py` asserts the demo's
  pre-populated proposals match the harness's expected actions
  for the same persona. Long-term: consolidation is a v0.1.14+
  question.
- **CP6 framing-edit blast radius.** L3 strategic-plan §6.3 is
  publicly read; the rephrasing is honest but visible. Codex
  D14 may push back on wording. Treat the edit as iterable in
  audit response, not fixed at PLAN authoring.

---

## 5. Definition of done

- All ship gates green per §3.
- D14 plan-audit closed at `PLAN_COHERENT`.
- D11 pre-PLAN bug-hunt closed (`audit_findings.md` consolidated;
  pre-implementation gate fired).
- All implementation rounds closed at `SHIP` or `SHIP_WITH_NOTES`.
- `RELEASE_PROOF.md` + `REPORT.md` authored.
- AGENTS.md + strategic plan + tactical plan updated per **CP1-CP5
  `accepted` deltas applied at ship**. CP6 application deferred
  to v0.1.13 strategic-plan rev per its acceptance gate (Codex
  F-PLAN-05).
- Per-CP verdicts (`accepted / accepted-with-revisions / rejected`)
  recorded in `RELEASE_PROOF.md` for all six.
- Branch merged to main; PyPI publish per
  `reference_release_toolchain.md`.

---

## 6. Phase 0 outline (D11 pre-PLAN bug-hunt)

Authored as `PRE_AUDIT_PLAN.md` in this folder when the cycle
opens (post round-2-or-later D14 `PLAN_COHERENT`). Phase 0 must
be scoped tightly enough that v0.1.12 doesn't grow the way
v0.1.11 did (Codex F-PLAN-10).

**Probes (parallel).**

- **Internal sweep** — bandit `-ll` baseline, mypy delta vs
  v0.1.11, **W-N audit command** (`uv run pytest
  verification/tests -W error::Warning -q`, per §2.5) to confirm
  the 47-site baseline or surface drift (Codex F-PLAN-R3-01: the
  v0.1.11 narrow gate was `PytestUnraisableExceptionWarning`,
  which cannot confirm the broader-target site count),
  capabilities byte-stability re-confirm.
- **Audit-chain probe** — replay v0.1.11 RELEASE_PROOF §2.7
  isolation transcript against current main; confirm boundary-
  stop demo still passes; surface any drift in the v0.1.11
  surface that v0.1.12 must absorb.
- **Persona matrix re-run** — full 12-persona harness against
  current main; confirm no regression vs v0.1.11 ship. Surface
  any persona that newly trips a v0.1.12-scope workstream.
- **Codex external bug-hunt audit** — Codex round against the
  current tree, scoped to v0.1.12 workstream surfaces
  specifically (W-Vb demo flow, W-D13-SYM domain policies,
  W-N-broader resource-warning sites, W-FBC supersede flow,
  W-CP cycle-proposal surface).

**Expected artifact.** `audit_findings.md` consolidates findings
with `cycle_impact` tags per AGENTS.md D11:

- `in-scope` — the cycle absorbs the finding.
- `revises-scope` — finding warrants a PLAN.md revision (loops
  back to D14 if large).
- `aborts-cycle` — finding warrants ending the cycle.

**Workstream-specific abort/revise triggers.**

- **W-Vb.** If Phase 0 reveals that current `open_session()` has
  hidden coupling to harness fixtures that breaks under
  packaged-fixture isolation, treat as `revises-scope`. If clean
  wheel-install fails for an unrelated packaging reason
  (pyproject.toml metadata corruption, etc.), treat as
  `aborts-cycle` until packaging is investigated separately.
- **W-FBC.** If Phase 0 reveals that the existing global
  fingerprint primitive in `core/synthesis.py:423-455` is itself
  inconsistent across domains (i.e., the "global" framing was
  optimistic), treat as `revises-scope` — option A's correctness
  may depend on the primitive being trustworthy.
- **W-N-broader.** Site-count > 150 fires the fallback ladder
  (§2.5) as `revises-scope`, not abort.
- **W-CP.** If Phase 0 surfaces a contradiction between a CP's
  proposed delta and an AGENTS.md decision NOT in scope of CP1-
  CP6, treat as `revises-scope` — the contradiction must be
  named in the affected CP doc.

**Pre-implementation gate.** Maintainer reads
`audit_findings.md`. `revises-scope` findings may revise PLAN
(loop to D14 if revision is large). `aborts-cycle` findings end
the cycle. Implementation does not start until this gate fires.
