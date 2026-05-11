# Orchestrator Working Memory

**Status:** Complete.
**Last updated:** 2026-05-11 (orchestration closed end-to-end)
**Current phase:** Phase 1 + Phase 2 BOTH CLOSED
**Closure artifacts:** `framing_v2/CONVERGED.md` (Phase 1) +
`framing_v2/phase_2_doc_alignment/COMPLETE.md` (Phase 2) +
`framing_v2/ORCHESTRATION_COMPLETE.md` (whole orchestration)

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

- **Phase:** ORCHESTRATION COMPLETE
- **Closure:** Phase 1 + Phase 2 both closed 2026-05-11. Phase 1
  closed by yield exhaustion (3 consecutive SHIP_WITH_NOTES rounds
  with 0 paper-§-level findings in R5); Phase 2 closed
  SHIP_WITH_NOTES with 5 minor/nit findings (3 fixed inline at
  closure, 2 deferred to a post-Phase-2 polish pass).
- **Final artifacts:** `CONVERGED.md`, `phase_2_doc_alignment/COMPLETE.md`,
  `ORCHESTRATION_COMPLETE.md` (entry-point for fresh sessions).
- **Sub-state:** Batch 6 closed clean (+48/-0); audit-findings-
  closure annotated F-CDX-RFR-R1-01..20 on the original audit-
  response file; final repo-wide audit SHIP_WITH_NOTES with 0
  paper-§-level findings; 3 of 5 final-audit findings fixed inline
  (README phrasing / SCAFFOLD_VIEW.md M8 rename + M9-TX bullet /
  project/FRAME.md cold-start reorder). 27 D-FRAME decisions
  locked. Total Phase 1+2 doc-alignment delta: ~2,827 insertions,
  ~1,282 deletions across ~33 files.
- **Carry-over (not blocking):** documented in
  `phase_2_doc_alignment/COMPLETE.md` — workshop-as-current sweep
  across 5 paper-lane files, "sensitive user-owned data" sweep
  across 4 prior-art docs, pre-pilot artifact commits (prompt
  template + scorer config + model roster), hermetic-mode E2E
  validation, 2 stale test assertions, work-packet template
  completeness pass.
- **Blockers:** None. Next substantive step is the Engels pilot
  (July 2026), which lives outside this orchestration.

- **Phase 2 carry-over (test alignment):** 2 stale tests in
  `project/tests/test_project_reframe_docs_alignment.py` assert
  pre-reframe strings ("HAI Paper-Readiness Engineering",
  pre-framing-v2 title) that the merged-paper framing intentionally
  retired. Not blocking batches 5-6. Will be addressed in a dedicated
  test-alignment sub-batch OR rolled into the audit-findings-closure
  batch.
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
| D-FRAME-016 | Title | "Deterministic Software Contracts as Trusted Monitors in AI Control Protocols" (10 words; full anchor set retained — Dom picked 2026-05-11) | Round 3 SYNTHESIS + AUDIT F-AUDIT-3-02; Dom pick 2026-05-11 |
| D-FRAME-017 | Mechanism inventory (revised) | M4-M8 separately ablatable; M5/M6 separable with invocation-context discipline; M7 scoped to clinical-boundary surfaces (JSON exempt); M8 renamed "audit evidence emission"; M9-TX held constant | Round 3 SYNTHESIS + on-disk audit confirmation |
| D-FRAME-018 | Engels pilot protocol | 60 APPS competition samples + 3 Houdinis (Qwen2.5-7B / Haiku 3.5 / Sonnet 4) + DRG-0 with 6-module pipeline + Haiku LLM Guard (5-vote) + 6-clause commit rule + 6-clause revert rule + ~$18.60 cost; "five attempts/sample" Engels claim needs Dom PDF verification | Round 3 SYNTHESIS Q3 |
| D-FRAME-019 | Two paper-killer critiques | (a) framing-overclaim (rhetorical preempt via "trusted-monitor substrate" reframe + arXiv:2510.09462 citation); (b) Greenblatt DRG-artifacts (empirical preempt via pre-registered DRG-0 information boundaries + ablations + FP rates + adaptive attack vs DRG) | Round 3 SYNTHESIS Q4 + AUDIT F-AUDIT-3-07 escalation |
| D-FRAME-020 | Predeclared model roster | 6 Houdinis (Qwen2.5-3B local HF / Qwen2.5-7B-Instruct-Turbo Together / Qwen2.5-32B & 72B Fireworks / Haiku 3.5 retired pilot-only / Sonnet 4 with 2026-06-15 retirement) + 3 Guards (DRG-0 deterministic / Haiku 3.5 retired pilot-only / gpt-4o-mini-2024-07-18). Haiku successor `claude-haiku-4-5-20251001` named for new cells; Sonnet 4 re-anchor to claude-sonnet-4-6 if §7.5 slips past 2026-06-15 | Round 4 RESPONSE Q1 + AUDIT F-AUDIT-4-02/03 |
| D-FRAME-021 | Predeclared thresholds | AND-pass rule + 7 zero-tolerance critical violations + per-metric thresholds (command_validity ≥1.00 + hallucinated=0; mutation-boundary =0; schema_validity ≥0.95; refusal_accuracy ≥0.95; unsupported_narration ≤0.02 + audit_faithfulness ≥0.98; clinical_claim =0; drift_robustness ≥0.90). Sensitivity test per-metric ±5pp. Schema work: claim_tier required at score level + T3/T4 conditional propagated to trajectory.schema.json | Round 4 RESPONSE Q2 + AUDIT F-AUDIT-4-04 |
| D-FRAME-022 | Adversarial attack policy | 50 trajectories: refusal-bypass 8 / mutation-escalation 8 / audit-tampering 8 / schema-evasion 8 / adaptive-vs-DRG-0 18. Per-attack protocols + deterministic adjudication + scope statement (not full control safety case). ControlArena URL canonicalized to `control-arena.aisi.org.uk`; SHADE-Arena added to §8 prior-art | Round 4 RESPONSE Q3 + AUDIT F-AUDIT-4-01/06/07 |
| D-FRAME-023 | Cost ceiling | USD 1,500 hard ceiling for all model API calls across the roster + attack-policy + §7.5 Engels + §7.6 HS runs (Dom picked 2026-05-11). Absorbs one full retry cycle; covers provider-substitution reruns triggered by Sonnet 4 retirement, schema-tightening reruns, attack-policy iteration. Excludes local GPU opportunity cost and human adjudication time | Round 4 AUDIT F-AUDIT-4-05 + Dom pick 2026-05-11 |
| D-FRAME-024 | Bounded HS empirical contrast | §7.6 renamed "Bounded Hierarchical Summarization contrast." Scope: L6 governance/refusal only (optional L5 if early). Caps: 2 weeks Dom-time + $200 API spend. Pre-register hs_monitor_v1 + prompt hashes + verdict schema. Demote to §2.3 prose only if cap missed (no scope expansion allowed) | Round 5 RESPONSE Q1a + AUDIT verified |
| D-FRAME-025 | Coding-agent slice = Appendix E sketch | Appendix sketch only; no second runtime build before this paper. 215-word draft in `round_5/RESPONSE.md` §Q2 is canonical Appendix E body. Anti-overclaim required: "this paper does not demonstrate cross-domain generalization." Must NOT be cited as evidence in abstract / contributions / results | Round 5 RESPONSE Q2 + D-PROJ-016 consistency |
| D-FRAME-026 | ST-WebAgentBench differentiation | 6-row table locked in `round_5/RESPONSE.md` §Q1b. Load-bearing axis: "runtime-mode intervention with mechanism-isolable ablation under a held-constant prompt." §2.3 + §2.4 prose draft ready for Phase 2 import | Round 5 RESPONSE Q1b + AUDIT verified |
| D-FRAME-027 | Paper 2 = S1 fine-tuning of bounded operators | Headline: "Trained operators reach contract-compliance at smaller scales than untrained operators." Frame as scale-substitution-after-runtime-floor. Six paper-1-setup requirements: §11 future-work paragraph; keep `fine_tuned_local` schema slot; freeze paper 1 roster/prompt/scorer/manifests/modes/thresholds; reserve GAB v2 train/val/test split with L7 drift + L6 refusal coverage; pre-register no-private-data recipe; Appendix D recipe description (future-work only, no performance claims) | Round 5 RESPONSE Q3 + AUDIT verified |

---

## Open decisions

Priorities: **high** = must close in Phase 1; **medium** = should close;
**low** = optional, may defer.

| ID | Decision | Priority | Current state |
|---|---|---|---|
| ~~O-FRAME-001~~ | ~~Title finalization~~ | ~~high~~ | **CLOSED → D-FRAME-016** (Round 3) |
| ~~O-FRAME-002~~ | ~~Mechanism inventory truth audit~~ | ~~high~~ | **CLOSED → D-FRAME-017** (Round 3) |
| ~~O-FRAME-003~~ | ~~Engels pilot protocol design~~ | ~~high~~ | **CLOSED → D-FRAME-018** (Round 3) |
| ~~O-FRAME-004~~ | ~~Anthropic adversarial reviewer simulation~~ | ~~high~~ | **CLOSED → D-FRAME-019** (Round 3) |
| ~~O-FRAME-005~~ | ~~Hierarchical Summarization empirical contrast~~ | ~~medium~~ | **CLOSED → D-FRAME-024** (Round 5) |
| ~~O-FRAME-006~~ | ~~Coding-agent slice~~ | ~~medium~~ | **CLOSED → D-FRAME-025** (Round 5) |
| ~~O-FRAME-007~~ | ~~Predeclared model roster~~ | ~~medium~~ | **CLOSED → D-FRAME-020** (Round 4) |
| ~~O-FRAME-008~~ | ~~Predeclared thresholds~~ | ~~medium~~ | **CLOSED → D-FRAME-021** (Round 4) |
| ~~O-FRAME-009~~ | ~~Adversarial attack policy~~ | ~~medium~~ | **CLOSED → D-FRAME-022** (Round 4) |
| ~~O-FRAME-010~~ | ~~ST-WebAgentBench detailed positioning~~ | ~~medium~~ | **CLOSED → D-FRAME-026** (Round 5) |
| ~~O-FRAME-011~~ | ~~Paper 2 sketch precision~~ | ~~medium~~ | **CLOSED → D-FRAME-027** (Round 5) |
| O-FRAME-012 | Constitutional Classifiers head-to-head | low | Additional baseline or skip |
| O-FRAME-013 | Reproducibility surface | low | What makes the paper replicable for external team |
| O-FRAME-014 | Cross-domain extension appendix | low | Coding-agent sketch exact content |
| O-FRAME-015 | Scope-cut decisions pre-committed | low | If pilot returns 0.3 Elo, what gets dropped |
| O-FRAME-016 | Threat model formalization | low | Precise §3.1/§3.2/§3.3 scope language |
| ~~O-FRAME-017~~ | ~~Cost ceiling~~ | ~~medium~~ | **CLOSED → D-FRAME-023** (Dom pick 2026-05-11, raised to $1,500) |

Round 5 closed all four remaining medium opens. **Phase 1 closed by yield exhaustion 2026-05-11.** 5 low-priority opens (O-FRAME-012/013/014/015/016) carry into Phase 2 as doc-alignment work, not new research.

---

## Stop-test status

| Signal | State |
|---|---|
| Decisions list signal (zero high/medium open) | **FIRED** — 0 high + 0 medium open after Round 5 closure |
| Yield signal (round N+1 has <3 substantive questions) | **FIRED** — zero substantive opens remain; round 6 would have nothing paper-§-level to ask |
| Adversarial-review signal (no paper-killer critique uncovered) | **FIRED** — Round 3 identified 2 paper-killers with pre-committed structural rebuttals (D-FRAME-019); rounds 4 + 5 surfaced no new paper-killers |

**Convergence: YES.** All three stop-test signals fired.

**Phase 1 escape valve also triggered:** Three consecutive
SHIP_WITH_NOTES rounds (R3 + R4 + R5) with 0 paper-§-level findings
in R5. Either path independently closes Phase 1.

**Phase 1 CLOSED 2026-05-11.** See `framing_v2/CONVERGED.md`.

---

## Audit verdicts log

| Round | Verdict | Findings | Paper-§-level | Provenance |
|---|---|---|---|---|
| Round 3 | SHIP_WITH_NOTES | 7 (0 critical, 0 major, 5 minor, 2 nit) | 0 | `round_3/AUDIT_RESPONSE.md` |
| Round 4 | SHIP_WITH_NOTES | 7 (0 critical, 0 major, 4 minor, 3 nit) | 0 | `round_4/AUDIT_RESPONSE.md` |
| Round 5 (terminal) | SHIP_WITH_NOTES | 6 (0 critical, 0 major, 2 minor, 4 nit) | 0 | `round_5/AUDIT_RESPONSE.md` |

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

### 2026-05-11 — Round 3 prompt pre-dispatch revision

- Fresh orchestrator session verified the four required-reading HAI
  source paths and line ranges in Q2 exist on disk (validate.py 548L,
  writeback/proposal.py 377L, handlers/intent.py 306L, handlers/
  target.py 405L, handlers/intake.py 1265L, cli/__init__.py 3264L —
  all cited ranges within bounds).
- Applied two pre-dispatch nits to `round_3/PROMPT.md`:
  - Q3: pinned token-spend estimate to May 2026 API pricing for
    Claude 3.5 Haiku, Claude Sonnet 4, Qwen2.5-7B-Instruct on
    Together AI, with a named-substitute fallback clause.
  - Q4: neutralized "Mrinank Sharma (until Feb 2026)" to "verify
    current affiliation first — do not assume Anthropic" to avoid
    locking in an unverified claim.
- Did not split the round on topical-clustering grounds; four
  high-priority opens against an end-of-June Phase 1 target
  justifies the breadth and Codex `/goal` handles it.

### 2026-05-11 — Round 3 closed (SHIP_WITH_NOTES)

- Codex returned `round_3/RESPONSE.md` (485 lines) covering all four
  questions. Goal time: 729 seconds.
- Orchestrator drafted `round_3/AUDIT_PROMPT.md` flagging five
  critical risk surfaces (arXiv:2601.19062 oddity, 20+ new HAI source
  citations outside the original required-reading set, Engels paper
  "225 APPS / four games / five attempts" claims, API pricing claims,
  Sharma resignation press claim) and dispatched audit via Agent
  tool (general-purpose subagent, 40 tool uses, 232s runtime).
- Audit returned SHIP_WITH_NOTES with 7 findings: 0 critical, 0
  major, 5 minor, 2 nit. All 20+ HAI source citations verified on
  disk. All 7 mandatory arXiv IDs resolved. Q3 cost arithmetic clean
  to the penny. Sharma resignation has primary-source confirmation
  (his own X post, 2026-02-09) that Codex missed but audit located.
- Locked D-FRAME-016 (title editorial fork — 9w vs 10w), D-FRAME-017
  (revised mechanism inventory; M8 renamed "audit evidence
  emission"; M7 narrowed; M9-TX held constant), D-FRAME-018 (full
  Engels pilot spec — 60 APPS samples, 3 Houdinis, DRG-0 module
  breakdown, 6-clause commit rule), D-FRAME-019 (two paper-killer
  critiques, not one).
- Stop-test: 1 partial + 2 not-fired. Convergence: No. Round 4
  recommended target cluster: predeclared-design
  (O-FRAME-007/008/009).
- Outstanding for Dom: pick title form (9w vs 10w); approve Round 4
  cluster.

### 2026-05-11 — Round 4 prompt drafted

- Dom picked 10-word title form (D-FRAME-016 locked: "Deterministic
  Software Contracts as Trusted Monitors in AI Control Protocols")
  and approved predeclared-design cluster (O-FRAME-007/008/009) for
  round 4.
- Drafted `round_4/PROMPT.md` with three questions: predeclared model
  roster (Q1, 6 Houdinis + 3 Guards with provider/snapshot/quant),
  predeclared thresholds (Q2, pass values + calibration defense +
  sensitivity test + multi-metric rule + hash), adversarial attack
  policy (Q3, five trajectory protocols including adaptive-vs-DRG-0
  as Greenblatt-critique structural preempt).
- Required-reading list extended to benchmark/governed_agent_bench/*
  files (verified on disk: BENCHMARK_SPEC.md 188L, SCORING_SPEC.md
  134L, schema files present).
- Awaiting Codex dispatch.

### 2026-05-11 — Round 4 closed (SHIP_WITH_NOTES)

- Codex returned `round_4/RESPONSE.md` (180 lines, tighter than
  round 3's 485). Goal time: 627 seconds.
- Orchestrator drafted `round_4/AUDIT_PROMPT.md` flagging six
  critical risk surfaces (Anthropic deprecation claims, model
  identifier strings including Fireworks IDs not audited before,
  scorer surface claims including 10 field names, ControlArena URL
  discrepancy, $1,000 cost ceiling, arXiv:2406.13352 AgentDojo).
- Dispatched audit via in-session Agent tool (general-purpose
  subagent, 33 tool uses, 194s runtime).
- Audit returned SHIP_WITH_NOTES with 7 findings: 0 critical, 0
  major, 4 minor, 3 nit. All load-bearing claims verified: Anthropic
  deprecation directions right (Haiku 3.5 retired 2026-02-19; Sonnet
  4 retirement 2026-06-15), all 10 scorer fields on disk in
  `benchmark/governed_agent_bench/scorer/core.py`, all model
  identifiers resolve.
- Locked D-FRAME-020 (model roster, 9 rows, Haiku-retired and
  Sonnet-retirement-window annotations), D-FRAME-021 (AND-pass rule +
  per-metric thresholds + critical-violation list + schema
  tightening for trajectory.schema.json T3/T4 conditional),
  D-FRAME-022 (50-trajectory attack policy with adaptive-vs-DRG-0
  18 trajectories + canonical ControlArena URL + SHADE-Arena added
  to prior art).
- New medium open: O-FRAME-017 cost ceiling ($1,000 has zero
  margin; audit recommends $1,500 raise or drop-not-rerun commit).
  Surface for Dom decision.
- Stop-test: 1 not-fired + 1 marginal + 1 partial. Convergence: No.
  Escape valve status: 2 consecutive SHIP_WITH_NOTES; one more
  triggers yield exhaustion.
- Round 5 recommended cluster: paper-positioning + scope-cleanup
  (O-FRAME-005+010 merged, O-FRAME-006, O-FRAME-011) — 3 questions.
- Outstanding for Dom: resolve O-FRAME-017 cost ceiling; approve
  round 5 cluster.

### 2026-05-11 — Round 5 prompt drafted (likely terminal)

- Dom picked $1,500 cost ceiling (D-FRAME-023 locked) and approved
  3-question paper-positioning + scope-cleanup cluster.
- Drafted `round_5/PROMPT.md` with three questions: Q1 merges
  O-FRAME-005 (HS empirical contrast — cut / appendix / bounded /
  full options) with O-FRAME-010 (ST-WebAgentBench differentiation
  table); Q2 O-FRAME-006 coding-agent slice (cut / appendix-sketch /
  full domain); Q3 O-FRAME-011 paper 2 sketch precision (S1
  fine-tuning concrete / spec-at-inference / pivot).
- Round explicitly framed as terminal candidate. Prompt's orchestrator
  notes flag the Phase 1 escape valve trigger: if this round returns
  SHIP_WITH_NOTES with no new paper-§-level findings, write
  CONVERGED.md and move to Phase 2.
- Awaiting Codex dispatch.

### 2026-05-11 — Round 5 closed; Phase 1 closed by yield exhaustion

- Codex returned `round_5/RESPONSE.md` (398 lines, ~3,452 words).
  Goal time: 561 seconds. External sources cited: HS Anthropic, RBR
  arXiv:2411.01111, Deliberative Alignment arXiv:2412.16339, MSM
  page, ST-WebAgentBench arXiv:2410.06703.
- Orchestrator drafted `round_5/AUDIT_PROMPT.md` flagging six
  critical risk surfaces (RBR arXiv ID, HS methodology accuracy,
  Haiku 4.5 pricing, ST-WebAgentBench 222 tasks + metrics, HAI v2
  manifest size ambiguity, cost arithmetic). Dispatched audit via
  Agent tool (28 tool uses, 210s runtime).
- Audit returned **SHIP_WITH_NOTES with 0 paper-§-level findings**.
  All primary-source claims verified. Six minor/nit findings: HS
  optional-classifier overgloss, v2 manifest path ambiguity (means
  `hai_0_2_0.json`), Deliberative Alignment gloss slight imprecision,
  L2 task family omitted from family-fit lists, Constitutional
  Classifiers Pareto-precedent un-cited, 16-24h bounded reimpl
  estimate optimistic. None change a § in the paper outline or
  re-open a locked Phase 1 decision.
- Locked D-FRAME-024 (bounded HS empirical contrast, L6-only with
  2w+$200 caps), D-FRAME-025 (coding-agent slice = Appendix E sketch),
  D-FRAME-026 (ST-WAB differentiation 6-row table + load-bearing
  axis "runtime-mode intervention with mechanism-isolable ablation
  under a held-constant prompt"), D-FRAME-027 (paper 2 = S1
  fine-tuning of bounded operators, "trained operators reach
  contract-compliance at smaller scales than untrained").
- Stop-test: ALL THREE signals fired. Decisions list (0 high + 0
  medium open), yield (zero substantive opens remain), adversarial-
  review (no new paper-killer in R4 or R5). Convergence: YES.
- Phase 1 escape valve also triggered: three consecutive SHIP_WITH_
  NOTES rounds with 0 paper-§-level findings in R5.
- **`framing_v2/CONVERGED.md` written 2026-05-11.** One-page summary
  of locked framing + 27 decisions table + 3-round audit log + Phase
  2 batch roadmap + Engels pilot pre-checks + calendar binding.
- Phase 1 CLOSED. Phase 2 documentation alignment is the next step.

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
