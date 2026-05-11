# Orchestrator Working Memory

**Status:** Active
**Last updated:** 2026-05-11 (seeded; not yet updated by any round)
**Current phase:** Phase 1 — Research convergence
**Current round:** Round 3 (prompt drafted, not yet dispatched to worker)

## How to use this file

This is the orchestrator's durable memory. Every round, the
orchestrator updates this file in place. Fresh orchestrator sessions
read this file to know where things stand.

Update sequence after each round:
1. Move closed decisions from "Open decisions" to "Locked decisions".
2. Update "Current round" and "Last updated".
3. Append to "Audit verdicts log".
4. Update "Stop-test status".
5. Append to "Decisions journal" for chronology.

---

## Current state snapshot

- **Phase:** Phase 1
- **Round in progress:** Round 3
- **Sub-state:** Worker prompt drafted at `round_3/PROMPT.md`. Awaiting
  Dom to paste into Codex and return RESPONSE.md.
- **Blockers:** None.
- **Calendar:** May 2026; Phase 1 target completion end of June 2026;
  pilot July 2026; NeurIPS 2027 submission May 2027.

---

## Locked decisions

Locked = ratified by Phase 1 round + audit + synthesis, OR seeded
from prior conversation work (rounds 1+2 before this orchestration
file structure existed; provenance is CONTEXT_DOSSIER.md §3 and the
PAPER_OUTLINE_MERGED.md file).

| ID | Decision | Locked value | Provenance |
|---|---|---|---|
| D-FRAME-001 | Headline framing | "Deterministic software contract that operationalizes a safety spec as the trusted monitor in an AI control protocol for bounded agent operation" | CONTEXT_DOSSIER §3 (round 2 synthesis) |
| D-FRAME-002 | Lineage anchor | Triple-anchor: AI control protocols (Greenblatt) + safety specs (OpenAI Model Spec, Anthropic MSM, Deliberative Alignment) + LLM-monitor baselines (Constitutional Classifiers, Hierarchical Summarization) | Round 2 R2 agent |
| D-FRAME-003 | Threat model | Capability-failure + targeted adversarial layer (50 trajectories, 4 attack types) | Round 2 R1 agent |
| D-FRAME-004 | Headline empirical | Engels Backdoor Code extension; deterministic runtime as Guard at general Elo = 0 | Round 2 R4 agent + merge decision |
| D-FRAME-005 | Direct competitor | Hierarchical Summarization (Anthropic Feb 2025) — explicit contrast required | Round 2 R2 agent |
| D-FRAME-006 | Closest published prior | ST-WebAgentBench (Levy et al., ICML 2025, arXiv:2410.06703) | Round 2 R3 agent |
| D-FRAME-007 | Benchmark framing | Framing D: contract-as-intervention with measured model-scale substitution | Round 2 R3 agent |
| D-FRAME-008 | Target venue | NeurIPS 2027 main conference (May 2027 deadline) | Merge decision |
| D-FRAME-009 | Trajectory | Merge paper 1 + paper 2 into single main-conference submission | Dom 2026-05-11 |
| D-FRAME-010 | Paper 2 redirect | S1 fine-tuning (RBR + Deliberative Alignment lineage) at ICML 2028 or NeurIPS 2028 | Merge decision |
| D-FRAME-011 | Decision gate | Engels pilot July 2026; revert to Trajectory A (separate workshop + conference papers) if pilot fails | Merge decision |
| D-FRAME-012 | Drop from title | "User-owned structured data" framing | Round 2 R2 agent |
| D-FRAME-013 | Personal wellness role | Instantiation, not framing | Round 2 R2 agent |
| D-FRAME-014 | A2 reframe | Closed (do not reopen) — overclaimed, term-collided, Burns misread | Round 2 R1 agent |
| D-FRAME-015 | B1 (no red-team) | Closed (do not reopen) — fatal for control venue legibility | Round 2 R1 agent |

---

## Open decisions

Priorities: **high** = must close in Phase 1; **medium** = should close;
**low** = optional, may defer.

| ID | Decision | Priority | Current state |
|---|---|---|---|
| O-FRAME-001 | Title finalization | high | 4 candidates in PAPER_OUTLINE_MERGED.md, no convergence |
| O-FRAME-002 | Mechanism inventory truth audit | high | F-CDX-RFR-R1-08/09/10 flag M5/M6/M7 may not be independently ablatable |
| O-FRAME-003 | Engels pilot protocol design | high | Sample sizes, prompts, hashing, decoding settings, Houdini/Guard pairings undefined |
| O-FRAME-004 | Anthropic adversarial reviewer simulation | high | Strongest single critique a Sharma/Perez/Shlegeris reviewer would land — not yet investigated |
| O-FRAME-005 | Hierarchical Summarization empirical contrast | medium | Full reimplementation vs rhetorical-only; cost and feasibility unclear |
| O-FRAME-006 | Coding-agent slice | medium | Appendix sketch / full second domain / cut entirely |
| O-FRAME-007 | Predeclared model roster | medium | Need exact 6 Houdinis + 3 Guards with provider snapshots, parameter counts, quantization (per F-CDX-RFR-R1-07) |
| O-FRAME-008 | Predeclared thresholds | medium | Exact pass values per primary metric (per F-CDX-RFR-R1-06) |
| O-FRAME-009 | Adversarial attack policy | medium | 50 trajectories across 4 attack types → concrete protocol per attack type |
| O-FRAME-010 | ST-WebAgentBench detailed positioning | medium | Concrete differentiation table not drafted |
| O-FRAME-011 | Paper 2 sketch precision | medium | S1 fine-tuning direction concrete or pivot |
| O-FRAME-012 | Constitutional Classifiers head-to-head | low | Additional baseline or skip |
| O-FRAME-013 | Reproducibility surface | low | What makes the paper replicable for external team |
| O-FRAME-014 | Cross-domain extension appendix | low | Coding-agent sketch exact content |
| O-FRAME-015 | Scope-cut decisions pre-committed | low | If pilot returns 0.3 Elo, what gets dropped |
| O-FRAME-016 | Threat model formalization | low | Precise §3.1/§3.2/§3.3 scope language |

Round 3 targets: O-FRAME-001, O-FRAME-002, O-FRAME-003, O-FRAME-004.

---

## Stop-test status

| Signal | State |
|---|---|
| Decisions list signal (zero high/medium open) | Not fired — 4 high + 7 medium open |
| Yield signal (round N+1 has <3 substantive questions) | Not fired — round 3 has 4 substantive |
| Adversarial-review signal (no paper-killer critique uncovered) | Not yet evaluated (round 4 candidate) |

**Convergence:** No.

---

## Audit verdicts log

(Empty — round 3 not yet dispatched.)

---

## Decisions journal (chronological)

### 2026-05-11 — Framing v2 orchestration opened

- Seeded `framing_v2/` directory with README, CONTEXT_DOSSIER,
  PHASE_PLAN, ORCHESTRATOR_PROTOCOL, ORCHESTRATOR_STATE, round_3/.
- Locked decisions D-FRAME-001 through D-FRAME-015 from prior
  conversation work (rounds 1+2, 2026-05-11).
- Identified 16 open decisions; ranked 4 high, 7 medium, 5 low.
- Drafted round 3 prompt targeting 4 high-priority decisions.
- Status: awaiting Dom to dispatch round 3 to Codex.

---

## Calendar markers

| Date | Event |
|---|---|
| 2026-05-11 | Orchestration v2 opened |
| 2026-06-30 (target) | Phase 1 convergence |
| 2026-07-15 (target) | Phase 2 doc alignment complete |
| 2026-07-20 to 2026-08-05 (target) | Engels pilot (de-risks merge) |
| 2026-08-10 (target) | Pilot decision gate: commit or revert |
| 2027-05-15 (approx) | NeurIPS 2027 submission deadline |

---

## Notes for the next orchestrator session

If you are reading this for the first time:

1. Confirm with Dom what state we're actually in. The file should be
   current, but verify.
2. The round 3 prompt is in `framing_v2/round_3/PROMPT.md`. If
   Dom has not dispatched it yet, you may revise the prompt before
   he does. If he has dispatched and a RESPONSE.md exists, proceed to
   audit-prompt drafting.
3. Always update this file after any state change. Stale state is
   the failure mode that breaks orchestrator continuity.
