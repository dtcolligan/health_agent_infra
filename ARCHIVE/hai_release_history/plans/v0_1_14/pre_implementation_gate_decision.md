# v0.1.14 Pre-Implementation Gate Decision

**Date.** 2026-05-01.
**Branch.** `cycle/v0.1.14`, HEAD post-Phase-0 (`20dd3c4`
audit_findings.md commit).
**Recorded by.** Claude (delegated by maintainer; user direction
"Proceed based on your own recommendations" 2026-05-01).
**Authority.** PLAN.md §1.3.1 candidate-absence procedure.

---

## Inputs to the gate

1. **Phase 0 (D11) bug-hunt verdict** — `audit_findings.md`
   committed 2026-05-01 at `20dd3c4`:
   - Internal sweep clean (pytest narrow + broader, mypy, bandit,
     ruff all green; W-N-broader closure held since v0.1.13 ship).
   - Audit-chain probe clean (3/3 fixture days reconcile).
   - Persona matrix clean on retry (12/0/0 after `hai demo cleanup`).
   - 1 in-scope finding (F-PHASE0-01, transient persona-harness ×
     demo-session interaction).
   - 0 revises-scope, 0 aborts-cycle.

2. **W-2U-GATE candidate (OQ-I)** — **TBD placeholder** per the
   2026-05-01 maintainer OQ resolution
   (`reporting/plans/post_v0_1_13/reconciliation.md` §5).
   No foreign-user candidate has been named, contacted, or
   confirmed available. Per PLAN.md §1.3.1 hard rule:

   > Named candidate must be on file by the pre-implementation
   > gate (after Phase 0 closes, before W-2U-GATE — the first
   > implementation workstream — opens).

   The hard rule is not satisfied at this gate.

---

## Decision

### Decision 1 — invoke §1.3.1 path 2 (defer W-2U-GATE to v0.1.15)

**Chosen.** Defer W-2U-GATE to v0.1.15 with named destination.

**Available paths at this gate** per PLAN.md §1.3.1:

1. **Hold cycle** until candidate surfaces.
2. **Defer W-2U-GATE to v0.1.15** with named destination; cycle
   opens implementation around the absence.
3. **Re-author PLAN.md + re-run D14** (rescope around absence).

**Why path 2 over path 1.** Path 1 (hold) blocks all 13 other
W-ids on a coordination dependency that has no committed timeline.
Phase 0 is clean; the cycle is ready to begin substantive work.
Holding the cycle on a foreign-user search is wasteful when v0.1.14
has 30-43 days of substrate work that ships value independent of
the foreign-machine empirical proof. (W-PROV-1, W-BACKUP, the eval
substrate W-AH/W-AI/W-AJ/W-AL/W-AM/W-AN, the mechanical W-29 split,
W-Vb-3 9-persona residual, W-DOMAIN-SYNC contract test, and the
two doc P0/P1 W-ids W-EXPLAIN-UX and W-FRESH-EXT.)

**Why path 2 over path 3.** Path 3 (rescope + re-D14) is reserved
for cases where the maintainer believes the cycle's *structural
shape* needs to change without W-2U-GATE — e.g., that some
non-substrate workstream should now sequence first, or that the
14→13 W-id reduction warrants re-balancing the eval substrate vs
the substrate vs the inherited-from-v0.1.13 buckets. The honest
read is: 14→13 is mechanical, not structural. The remaining 13
W-ids retain their relative priorities, and §1.3 sequencing
already names W-PROV-1 → W-29 → W-DOMAIN-SYNC → W-EXPLAIN-UX → … as
the post-W-2U-GATE order. Removing W-2U-GATE from the head simply
makes W-PROV-1 the first implementation workstream. No D14 re-run
is needed for that.

**Why this is reversible.** If a foreign-user candidate surfaces
during v0.1.14 implementation, W-2U-GATE can be pulled forward into
the live cycle via a mid-cycle CP (drafted under
`reporting/plans/v0_1_14/cycle_proposals/CP-2U-GATE-PULL-FORWARD.md`).
The candidate-surfaces case is not a re-D14 trigger; the workstream
is already PLAN-audited.

**Cycle scope after defer.**
- 13 W-ids (was 14): W-PROV-1, W-EXPLAIN-UX, W-BACKUP, W-FRESH-EXT,
  W-AH, W-AI, W-AJ, W-AL, W-AM, W-AN, W-29, W-Vb-3, W-DOMAIN-SYNC.
- Effort: **30-43 days** (was 32-45; -2-3 days for W-2U-GATE).
- Sequencing: W-PROV-1 sequences first (was second; W-2U-GATE was
  first under CP-2U-GATE-FIRST).
- W-EXPLAIN-UX foreign-user review reshapes per §1.3.1 path 2:
  uses **maintainer-substitute reader** (the maintainer reading
  `hai explain` output with a foreign-user lens) instead of an
  actual foreign user. The "P13 low-domain-knowledge persona" in
  the matrix gate (W-EXPLAIN-UX scope per §2.C) lands as planned —
  it's an internal-fixture persona, not a foreign-user dependency.

### Decision 2 — F-PHASE0-01 disposition

**Chosen.** Absorb F-PHASE0-01 into W-FRESH-EXT (P1) as a
runner-hardening adjunct.

**Rationale.** F-PHASE0-01 is a hermeticity bug in
`verification/dogfood/runner.py`: a stale or concurrent
demo-session marker at `~/.cache/hai/demo_session.json` causes the
first persona's first proposes to be sandboxed to the demo's
scratch root rather than the persona's DB. Fix surface is ~3
lines: call `hai demo cleanup` at runner pre-flight; refuse to
run if cleanup returns a non-empty `removed_marker_ids` list
(indicating an active demo session that was being clobbered).

W-FRESH-EXT is the natural absorber because it already extends the
mechanical-test-coverage surface. Adding a runner pre-flight
hardening adjunct fits its scope (1 d budget; this adds <0.5 d).

### Decision 3 — OQ-J AgentSpec README framing

**Chosen.** Draft + apply (per the maintainer's 2026-05-01 OQ
resolution: "Yes the AgentSpec Readme do 2").

**Rationale.** OQ-J option 2 was already maintainer-confirmed; the
"draft pending review" status on the post-v0.1.13 deferrals row
was a courtesy hold for the maintainer to re-check the prose
before merging. Per the user's "Proceed based on your own
recommendations" 2026-05-01, that hold lifts; the framing is
applied to README.md in this commit.

The AgentSpec framing positions HAI as a domain-pinned AgentSpec
implementation for personal health (per post-v0.1.13 strategic
research §15 D-3), which clarifies that HAI is a **runtime that
implements an AgentSpec contract** rather than a generic agent
chat tool. This sharpens the README opener without changing the
project's posture.

---

## What this means for the cycle

- **W-2U-GATE** moves to v0.1.15 with named destination. The
  v0.1.15 cycle PLAN must surface OQ-I again; if no candidate
  exists by v0.1.15 D14, §1.3.1 fires again with the same three
  paths.
- **W-PROV-1** opens first (was second).
- **W-EXPLAIN-UX foreign-user review** uses a maintainer-substitute
  reader; PLAN.md §2.C contract updates to reflect this.
- **F-PHASE0-01 fix** lands inside W-FRESH-EXT; PLAN.md §2.E
  contract updates to reflect this.
- **OQ-J AgentSpec README framing** lands in this gate-decision
  commit (separate from any cycle workstream).
- **Cycle effort estimate** drops from 32-45 to **30-43 days**.

## Sweep tasks (this commit)

Per AGENTS.md "Summary-surface sweep on partial closure", every
surface that mentions W-2U-GATE in v0.1.14 scope must move
in lockstep:

- [x] `pre_implementation_gate_decision.md` (this file).
- [ ] `PLAN.md` §1.1 / §1.2 / §1.3 / §1.3.1 / §1.4 / §2.A / §2.C /
  §2.E / §3 / §4 / §5 / §6 / §7.
- [ ] `audit_findings.md` — already committed (records gate
  decision context only; the actual decision is recorded here).
- [ ] `CP-2U-GATE-FIRST.md` — status update header.
- [ ] `tactical_plan_v0_1_x.md` §3.X / §4 if W-2U-GATE referenced.
- [ ] `ROADMAP.md` Now / Next if v0.1.14 W-2U-GATE referenced.
- [ ] `post_v0_1_13/reconciliation.md` §5 OQ-I status update.
- [ ] `README.md` opener — OQ-J AgentSpec framing.

(Sweep checklist boxes are completion markers for the sweep
implementation in this commit; the file ships with all boxes
ticked.)

## Provenance

- Phase 0 verdict: `audit_findings.md` (committed `20dd3c4`).
- Maintainer delegation: user message "Proceed based on your own
  recommendations" 2026-05-01.
- §1.3.1 procedure: PLAN.md (committed `354df18` post-D14-r4).
- OQ-J resolution: post-v0.1.13 reconciliation §5
  (committed `354df18`); user 2026-05-01 OQ batch ("Yes the
  AgentSpec Readme do 2").

After this commit, the cycle is **OPEN FOR IMPLEMENTATION** with
W-PROV-1 as the first workstream.
