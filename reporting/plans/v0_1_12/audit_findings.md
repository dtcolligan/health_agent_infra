# v0.1.12 Phase 0 (D11) — Audit Findings

**Date.** 2026-04-29.
**Authored by.** Claude (delegated by maintainer).
**Status.** Internal sweep + audit-chain probe + persona matrix
complete. Codex external bug-hunt pending maintainer decision
(optional per D11 — informal demo-run probes are sometimes
substituted; v0.1.11 settled at this convention).

**Verdict.** **Pre-implementation gate fires green.** Zero
`aborts-cycle` findings. Two `in-scope` findings absorbed by
existing W-ids. Zero `revises-scope` findings.

---

## 1. Probes run

| Probe | Command | Result | Cycle impact |
|---|---|---|---|
| **Bandit** `-ll` baseline | `uvx bandit -ll -r src/health_agent_infra` | 0 Medium / 0 High; 44 Low (unchanged from v0.1.11 ship) | clean |
| **Mypy** delta vs v0.1.11 | `uvx mypy src/health_agent_infra` | 22 errors in 12 files (v0.1.11 ship: 21 in 11) | **in-scope** of W-H2 (target ≤ 5); +1 error / +1 file drift documented below |
| **Capabilities** byte-stability | `hai capabilities --markdown` x2 + diff | byte-identical | clean |
| **W-N audit command** | `uv run pytest verification/tests -W error::Warning -q` | **49 failed + 1 error** of 2358 tests, 72.84s | **in-scope** of W-N-broader; **≤ 80 branch** confirmed → full broader gate ships per §2.5 fallback ladder |
| **Audit-chain probe** | `uv run pytest verification/tests/test_demo_isolation_surfaces.py -v` | 7/7 PASSED including `test_subprocess_cli_writes_under_demo_isolate_real_state` | clean — v0.1.11 boundary-stop isolation contract holds against current main |
| **Persona matrix** (12) | `uv run python -m verification.dogfood.runner /tmp/v0_1_12_phase0_personas` | 12 personas, 0 findings, 0 crashes | clean — no regression vs v0.1.11 |
| Codex external bug-hunt | (optional — pending maintainer decision) | — | — |

---

## 2. Findings

### F-PHASE0-01 — Mypy +1 / +1 drift since v0.1.11 ship

**Cycle impact:** in-scope (absorbed by W-H2).

v0.1.11 RELEASE_PROOF §2.3 reported 21 errors in 11 files. Phase 0
sweep reports **22 errors in 12 files**. The +1 error / +1 file
delta is small and W-H2 already targets ≤ 5 errors at v0.1.12
ship, so the drift is absorbed.

Sampling of categories observed (not exhaustive):

- `cli.py:374` — `Argument "status" to "complete_sync" has
  incompatible type "str"; expected "Literal['ok', 'partial',
  'failed']"` (Literal-class — F-A-04 territory)
- `cli.py:2054-2055` — Literal vs `dict[str, int]` index/return
  mismatch
- `cli.py:4223` — None-safety on inequality operators
  (`Unsupported operand types for <= ("int" and "None")`)

W-H2 implementation should run a fresh mypy at workstream start
to enumerate the full 22 against the 21-baseline; new error is
not load-bearing for cycle scope.

### F-PHASE0-02 — W-N audit count 49 + 1 error vs 47 baseline

**Cycle impact:** in-scope (absorbed by W-N-broader; branch
decision confirmed).

v0.1.11 RELEASE_PROOF §2.2 noted 47 ResourceWarning failures
under the broader gate. Phase 0 sweep reports **49 failures + 1
error** (2 of which may include non-ResourceWarning Warning
categories under the catch-all `-W error::Warning` audit
command). All counts are well within the §2.5 **≤ 80
fallback-ladder branch**:

- ≤ 80 → full broader gate ships in v0.1.12. **Confirmed.**
- 80-150 → would split. **Not triggered.**
- > 150 → would defer entire broader gate. **Not triggered.**

W-N-broader scope is unchanged: full broader gate as ship target.
Workstream should record 49 + 1 as the audit-time count in
RELEASE_PROOF.

### F-PHASE0-03 — Codex external bug-hunt status

**Cycle impact:** procedural — maintainer decision required.

PLAN.md §6 names a Codex external bug-hunt as the fourth
parallel Phase 0 probe. v0.1.11 settled at the convention that
informal demo-run probes can substitute (RELEASE_PROOF §2.6).
v0.1.12 has no analogous demo-run; if a Codex bug-hunt is
desired, the maintainer signals and a prompt is authored. If
not, the three local probes above are sufficient to fire the
pre-implementation gate.

**Default (consistent with v0.1.11):** proceed without a
separate Codex bug-hunt round; D14 plan-audit chain (4 rounds,
18 findings) already exercised independent external review
against the planned cycle scope.

---

## 3. Pre-implementation gate decision

Three local Phase 0 probes complete. Two findings, both
`in-scope` (W-H2 absorbs F-PHASE0-01; W-N-broader absorbs
F-PHASE0-02). Zero `revises-scope`. Zero `aborts-cycle`.

**Gate fires green.** Cycle opens for implementation.

---

## 4. Workstream sequencing

PLAN.md §1.2 catalogue does not prescribe a sequence; the cycle
pattern is one-contributor-many-workstreams. Recommended
ordering by dependency:

1. **W-CP** (1d) — author 6 cycle-proposal docs first; downstream
   W-AC depends on the CP1-CP5 AGENTS.md / strategic-plan deltas
   being defined.
2. **W-CARRY** (0.5d) — carry-over register; references W-CP
   dispositions but doesn't depend on application.
3. **W-AC** (0.5d) — apply AGENTS.md + strategic-plan deltas
   from CP1-CP5; freshness sweep; anti-gaming line. CP6
   application deferred per its acceptance gate.
4. **W-D13-SYM** (0.5-1d) — domain policy.py coercer fix +
   contract test. Independent of CP work.
5. **W-PRIV** (0.5-1d) — privacy doc + `hai auth remove`
   subcommand.
6. **W-FCC** (1d) — strength_status enum surface in capabilities
   + `hai today --verbose`.
7. **W-FBC** (1-2d) — F-B-04 design doc + recovery prototype +
   `--re-propose-all` flag.
8. **W-H2** (2-3d) — mypy stylistic class.
9. **W-N-broader** (3-4d) — resource-warning sweep across all
   sqlite3 sites; CI gate command.
10. **W-Vb** (3-4d) — demo persona-replay + fixture-packaging
    path. Heaviest single workstream.

W-CARRY can be partially-authored at cycle open with placeholders
filled in as work lands.

Total budget: 13-20 days single-contributor per PLAN.md §1.2.
