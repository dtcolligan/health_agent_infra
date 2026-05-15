# Batch 5 Edits Summary

## Files touched

| File | Edit type | Lines changed (rough) | Notes |
|---|---|---:|---|
| `AGENTS.md` | revise + append | ~207 diff lines | Added framing-v2 cold-start source ordering, merged-paper identity, D19-D27 settled decisions, mechanism inventory, active framing-v2 cycle pattern, dormant HAI release-cycle note, and Do Not Do updates. |
| `CLAUDE.md` | light revise | ~49 diff lines | Added `framing_v2/CONVERGED.md` first in session-start orientation, updated AGENTS decision range to D1-D27, and distinguished dormant HAI release cycles from active framing-v2 orchestration. |
| `README.md` | revise | ~106 diff lines | Replaced top-level title and pitch with the locked paper title and conservative pre-pilot framing; added status, source-of-truth, NeurIPS 2027, and current-priority updates. |

## AGENTS.md additions

- New "Settled Decisions" entries: D19-D27.
- D19 imports D-FRAME-001..027 through `framing_v2/CONVERGED.md` and points to D-PROJ-018..023 as project-level imports.
- D20 locks the D-FRAME-016 title, D-FRAME-008 NeurIPS 2027 main-conference venue, and D-FRAME-009 merged trajectory.
- D21-D27 carry forward the headline framing, closed A2/B1 reframes, mechanism inventory, Engels pilot gate, adversarial layer, model/threshold/cost package, bounded prior-art contrasts, and future-work/scope boundaries.
- Updated "What This Project Is" pitch to the merged-paper/control-protocol framing with HAI as frozen reference runtime.
- "Patterns the cycles have validated" now includes the framing-v2 orchestration pattern.
- Cycle-pattern signposts now name the `framing_v2/` shape: `CONVERGED.md`, `ORCHESTRATOR_STATE.md`, `PHASE_PLAN.md`, `ORCHESTRATOR_PROTOCOL.md`, `round_*/`, and `phase_2_doc_alignment/`.
- "Do Not Do" now explicitly blocks reopening D-FRAME-001..027, A2, B1, the NeurIPS 2027 main-conference target, the merged trajectory, and the HAI product freeze without the required decision path.
- Title + venue + mechanism inventory consistency checked against D-FRAME-016, D-FRAME-008, and D-FRAME-017.

## CLAUDE.md updates

- Session-start orientation now starts with `research/runtime_contracts_paper/framing_v2/CONVERGED.md`.
- `framing_v2/ORCHESTRATOR_STATE.md` is second in the cold-start list.
- AGENTS.md cross-reference now names settled decisions D1-D27.
- Cycle-pattern signposts distinguish the dormant HAI release-cycle pattern from the active framing-v2 research-lane pattern.

## README.md updates

- Title replaced with "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols."
- Headline framing now names deterministic software contracts as trusted monitors in AI control protocols, with HAI as reference runtime and GovernedAgentBench as benchmark.
- Status section reflects Phase 1 closed 2026-05-11, Phase 2 in progress, July 2026 Engels pilot gate, and NeurIPS 2027 main-conference target.
- Pitch language is conservative: implemented reference runtime + benchmark scaffold + locked pilot protocol, not model-result claims.
- Repo orientation names `framing_v2/CONVERGED.md` as canonical paper-framing source-of-truth and `ORCHESTRATOR_STATE.md` as the full decisions table.

## Cycle-pattern vocabulary

- HAI release cycle pattern: named as historical/dormant while HAI is frozen as a product per D-PROJ-016.
- Framing-v2 pattern: named as active research-lane pattern with Phase 1 research convergence, Phase 2 doc alignment, worker-auditor-orchestrator triad, `round_N` artifacts, `batch_N` artifacts, escape valve after three consecutive `SHIP_WITH_NOTES` rounds with zero paper-section-level findings, and end-of-phase-only audit in Phase 2.

## Cold-start file ordering check

AGENTS.md authoritative orientation starts:

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md`
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
3. `project/FRAME.md`
4. `project/DECISIONS.md`
5. `project/OPERATING_MODEL.md`

CLAUDE.md session-start orientation starts:

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md`
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
3. `project/FRAME.md`
4. `project/DECISIONS.md`
5. `project/OPERATING_MODEL.md`

## Carry-over for batch 6 + audit-findings-closure

- Batch 6 can proceed to historical-provenance supersession headers; no operating-contract blocker found.
- Audit-findings-closure should verify that A2 capability-elicitation and B1 no-red-team language now appears only as closed historical markers in the operating contracts.

## Open issues

- None.
