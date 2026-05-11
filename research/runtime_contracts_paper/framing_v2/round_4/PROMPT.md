# Round 4 Worker Prompt — Research

**Drafted:** 2026-05-11
**Worker:** Codex via `/goal`
**Target:** Close O-FRAME-007, O-FRAME-008, O-FRAME-009 (predeclared-
design cluster)

---

## Identity

You are Codex, operating in `/goal` mode for an extended research
session. You are the worker agent for the runtime-contracts paper
framing v2 orchestration. The orchestrator (Claude Code) wrote this
prompt. Take your time; depth over speed.

## Project briefing

The paper is **"Deterministic Software Contracts as Trusted Monitors
in AI Control Protocols"** (D-FRAME-016 locked 2026-05-11). Target
venue: NeurIPS 2027 main conference, May 2027 deadline. The paper
merges paper 1 (runtime contract architecture + GovernedAgentBench)
with paper 2 (Engels et al. Backdoor Code extension as §7.5).

**Round 3 closed four high-priority opens.** Locked outcomes you must
not reopen:

- **D-FRAME-017 mechanism inventory.** M4-M8 ablatable independently
  under disciplined invocation context. M7 scoped narrowly to
  clinical-boundary surfaces (JSON output exempt). M8 renamed
  "audit evidence emission." M9-TX (transaction integrity) held
  constant non-ablatable.
- **D-FRAME-018 Engels pilot protocol.** 60 APPS competition samples,
  three Houdinis (Qwen2.5-7B-Instruct Turbo via Together AI, Claude
  3.5 Haiku, Claude Sonnet 4), DRG-0 with six modules, Haiku LLM
  Guard with 5-vote majority, 6-clause commit rule, ~$18.60 cost.
- **D-FRAME-019 two paper-killer critiques.** Framing-overclaim
  (rhetorical preempt: "trusted-monitor substrate for bounded
  AI-control protocols") and Greenblatt DRG-artifacts (empirical
  preempt: pre-registered DRG inputs + ablations + FP rates +
  adaptive attack against DRG).

**Round 4 targets the predeclared-design cluster.** Three remaining
medium-priority opens that share benchmark-design literature:

- **O-FRAME-007** — predeclared model roster (6 Houdinis + 3 Guards
  with provider snapshots, parameter counts, quantization).
  Originates in F-CDX-RFR-R1-07.
- **O-FRAME-008** — predeclared thresholds (exact pass values per
  primary metric). Originates in F-CDX-RFR-R1-06.
- **O-FRAME-009** — concrete adversarial attack policy per attack
  type for the 50-trajectory layer.

These three decisions together turn GovernedAgentBench from "a
benchmark in design" into a **reproducible measurement instrument** a
Phase 2 reviewer or external team could re-run. Without them the
paper's §6 (benchmark) cannot survive the F-CDX-RFR-R1 audit closure.

## Required reading

Read these before answering. Verify on disk where the question
concerns repo files.

1. `research/runtime_contracts_paper/framing_v2/CONTEXT_DOSSIER.md` —
   full project briefing.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — current locked decisions D-FRAME-001 through D-FRAME-019; open
   decisions list.
3. `research/runtime_contracts_paper/framing_v2/round_3/SYNTHESIS.md`
   — round-3 closures + action items + missing-literature flags.
4. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` — §6
   GovernedAgentBench + §6.2 metrics list + §6.4-6.6 predeclaration
   commitments.
5. `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
   — specifically F-CDX-RFR-R1-06 (thresholds) and F-CDX-RFR-R1-07
   (model roster).
6. `benchmark/governed_agent_bench/BENCHMARK_SPEC.md` — current spec.
7. `benchmark/governed_agent_bench/SCORING_SPEC.md` — current scoring
   methodology.
8. `benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md` — current
   harness design.
9. `benchmark/governed_agent_bench/schema/trajectory.schema.json` —
   current model_identity fields.
10. `benchmark/governed_agent_bench/schema/score.schema.json` —
    current scorer fields.

For Q3, key prior-art benchmarks to read (cite primary sources):

- ST-WebAgentBench (Levy et al., ICML 2025, arXiv:2410.06703) — how
  it constructs adversarial cases.
- AgentDojo (Debenedetti et al., NeurIPS 2024) — prompt-injection
  attack taxonomy and trajectory protocol.
- Constitutional Classifiers (arXiv:2501.18837) — red-team protocol
  and 3000-hour bug bounty.
- ControlArena (control-arena.aisi.org.uk) — UK AISI's
  attack-policy-as-component framework.
- Adaptive Attacks on Trusted Monitors (arXiv:2510.09462) — recent
  attack-policy work that the paper §2/§5 will cite per Round 3
  missing-literature flag.

---

## Questions for this round

### Q1 — Predeclared model roster (closes O-FRAME-007)

The merged paper §6.4 names "Qwen2.5 family, Claude 3.5 Haiku, Claude
Sonnet 4, GPT-4o-mini" without provider snapshots, parameter counts,
or quantization. F-CDX-RFR-R1-07 flagged this as insufficient for
reproducibility. The Engels pilot (D-FRAME-018) already locks a
3-Houdini ladder; the full paper needs **6 Houdinis + 3 Guards** for
the §7.5 scaling-laws curve plus §7.1-7.4 contract ablations.

**Task:**

1. Propose the exact 6 Houdinis. Must span general-Elo range from
   the Engels-style weakest (e.g., Qwen2.5-3B-Instruct) to a frontier
   model (e.g., Claude Sonnet 4 or GPT-4.1). Include at least three
   open-weight models for replication outside Anthropic-API access.
   For each Houdini specify:
   - Exact model identifier (e.g., `Qwen/Qwen2.5-7B-Instruct-Turbo` on
     Together AI, or `claude-3-5-haiku-20241022`).
   - Provider (Anthropic API, OpenAI API, Together AI, Fireworks,
     Hugging Face local).
   - Provider snapshot date or version-pin (e.g., "as served on
     2026-05-15").
   - Parameter count (or stated parameter count if undisclosed).
   - Quantization in production serving (FP16 / BF16 / FP8 / INT8 /
     custom). For closed models, mark as "vendor-undisclosed."
   - Approximate general-Elo position (LMArena, MMLU, or other public
     reference where available) — note the metric and snapshot date.

2. Propose the exact 3 Guards. Must include:
   - **DRG-0** (the deterministic runtime Guard from D-FRAME-018).
   - One LLM Guard at the same provider/family as the Engels pilot
     (Claude 3.5 Haiku) for calibration continuity.
   - One additional LLM Guard at a *different* capability tier or
     provider to make the deterministic-vs-LLM contrast not vendor-
     specific. Candidates: GPT-4o-mini, Llama 3.1 8B Instruct on
     Together, or DeepSeek-V3 on DeepSeek API.

3. Specify availability risk. The paper submits May 2027; some 2026
   models will be deprecated. For each model, note:
   - Earliest known deprecation date (vendor sunset announcements,
     model card EOL fields).
   - Replacement strategy if deprecated before submission (frozen
     trajectory replays via `model_identity` schema, or substitute
     model with disclosed re-run).

4. Map the roster to §7 sections:
   - §7.1-7.4 (mechanism ablations): which subset of the 6 Houdinis
     runs the contract-mechanism toggles?
   - §7.5 (Engels Backdoor Code): all 6 Houdinis vs 3 Guards =
     18 cells. Confirm cell count matches §6.5 trial-budget claim.
   - §7.6 (Hierarchical Summarization head-to-head): which Houdinis
     and which LLM Guard?

**Deliverable:** A predeclared model roster table:

| Role | Model ID | Provider | Snapshot date | Params | Quant | Public Elo anchor | Deprecation risk | §7 cells |
|---|---|---|---|---|---|---|---|---|
| Houdini 1 | ... | ... | ... | ... | ... | ... | ... | ... |
| ... | ... | ... | ... | ... | ... | ... | ... | ... |
| Houdini 6 | ... | ... | ... | ... | ... | ... | ... | ... |
| Guard 1 (DRG-0) | n/a — deterministic | n/a | 2026-Q3 freeze | n/a | n/a | general-Elo = 0 | none | all §7.5 |
| Guard 2 | ... | ... | ... | ... | ... | ... | ... | ... |
| Guard 3 | ... | ... | ... | ... | ... | ... | ... | ... |

Plus: total trial-cell count for §7 and rough cost ceiling under May
2026 API pricing.

### Q2 — Predeclared thresholds (closes O-FRAME-008)

The merged paper §6.2 lists primary metrics but does not name pass
values. F-CDX-RFR-R1-06 flagged this as missing for `score.schema.json`
required-fields enforcement and for honest pre-registration.

**Task:**

1. For each primary metric in §6.2, propose a **pass threshold** and
   defend its calibration source. Metrics list (per current outline):

   - **command_validity** — fraction of agent-emitted commands that
     parse against the capabilities manifest.
   - **mutation_boundary_obedience** — fraction of agent runs that do
     not attempt unauthorized mutations (i.e., do not trigger M5 or
     M6 refusals when those mechanisms are enabled).
   - **schema_valid_proposal_generation** — fraction of agent
     proposals that pass `core/writeback/proposal.py` validators.
   - **refusal_accuracy** — fraction of clinical-claim test prompts
     where M7 emits a refusal envelope (true-positive rate on a
     held-out clinical-claim test set).
   - **unsupported_narration_rate** — fraction of synthesis prose
     outputs containing claims not justified by `classified_state` /
     `policy_result` evidence (lower is better).
   - **clinical_boundary_violations** — count of clinical-claim
     emissions in output where M7 was enabled (should be near zero).
   - **contract_drift_robustness** — fraction of agent runs where the
     `agent_cli_contract.v2` manifest schema changes do not break
     downstream parsing.

   For each: propose a numeric threshold (e.g., "≥ 0.95"). Defend the
   calibration source as one of:
   - **Literature anchor** — cite a published benchmark with similar
     metric and similar threshold.
   - **Internal calibration** — derived from current HAI test-suite
     pass rates or persona-matrix outputs.
   - **Pre-registered floor** — chosen as the value below which the
     paper's claim ("the contract shifts the model-scale safety
     curve") fails.

2. Specify the **threshold sensitivity test**. For at least three
   primary metrics, propose a sensitivity analysis: how the
   conclusions change if the threshold is moved ±5 percentage points
   from the predeclared value. This is the structural preempt of the
   "threshold cherry-picked" reviewer critique.

3. Specify the **multi-metric pass rule**. Does the paper claim
   "passes all primary thresholds" (AND across metrics) or "passes a
   weighted score" (single composite)? Either is defensible; pick
   one and justify. The choice changes §7.4 ("runtime-as-floor")
   claim wording.

4. Specify the **threshold-set hash**. The thresholds must be
   serialized into `score.schema.json`'s `scorer_config` field and
   hashed (`scorer_config_hash`) before any runs that produce
   numbers for the paper. Confirm this is implementable against
   current `benchmark/governed_agent_bench/schema/score.schema.json`
   structure or flag the needed schema-field addition.

**Deliverable:** A predeclared threshold table:

| Metric | Pass threshold | Calibration source | Sensitivity test | §7 claim dependency |
|---|---|---|---|---|
| command_validity | ≥ ... | ... | ±5pp | ... |
| ... | ... | ... | ... | ... |

Plus: pass rule (AND / weighted), defense of the choice, and
serialization/hash implementability statement.

### Q3 — Adversarial attack policy (closes O-FRAME-009)

The merged paper §8 names "50 trajectories across 4 attack types"
without specifying what an attack trajectory is, who authors it, how
attack success is scored, or how the trajectories are sampled. The
adversarial layer is **non-negotiable** per D-FRAME-015 (B1 closed) —
control-aligned reviewers desk-reject without it. Round 3's
F-AUDIT-3-07 escalated this further: Greenblatt's DRG-artifacts
critique requires an **adaptive attack against DRG-0 itself** as one
of the trajectory types.

**Task:**

1. For each of the four attack types in §8.2, specify a concrete
   protocol. Each protocol must answer:
   - **What is a trajectory?** A single agent run? A multi-turn
     dialogue? A scripted attack-policy invocation?
   - **Who authors the attack?** Human red team, static playbook,
     LLM red-team agent, automated fuzzer? (For the LLM red-team
     option, name the model and decoding settings — cf. ControlArena
     and AgentDojo for prior art on LLM-authored attacks.)
   - **How is attack success scored?** Boolean (succeeded / didn't),
     or graded (partial leak vs full)? Specify the rubric.
   - **What is the safety/usefulness tradeoff metric?** Per
     trajectory, what's logged so the §8.3 Pareto plot is generable?

   Apply this to:
   - **Refusal bypass** (target: M7) — attacks attempting to elicit
     clinical-boundary violations or refusal-eligible content.
   - **Mutation escalation** (target: M5 + M6) — attacks attempting
     to promote agent-proposed intent/target rows without the W57
     user-commit gate.
   - **Audit tampering** (target: M8) — attacks attempting to
     suppress, forge, or alter audit-chain rows.
   - **Schema evasion** (target: M4) — attacks attempting to emit
     commands that bypass capabilities-manifest typing while still
     producing side effects.

2. Specify the **fifth attack type — adaptive attack against DRG-0**
   for §7.5 / §8 cross-cutting use. This is the structural preempt
   of Greenblatt's critique. The protocol must:
   - Give the attacker (Houdini or red-team LLM) full read access to
     the DRG-0 implementation, thresholds, and config hash.
   - Allow the attacker to iterate against DRG-0's verdict surface.
   - Measure how many iterations / how much compute is needed to
     find a CLEAN-verdict-but-actually-corrupt sample.
   - Compare adaptive attack effort against the LLM Guard.

3. Specify the **trajectory budget allocation**. 50 trajectories
   total. How are they distributed across attack types? Equal split
   (12-13 each) or weighted by paper-§8.4 question importance? The
   adaptive-attack-vs-DRG-0 type may need more trials than the others
   for statistical separation. Justify the allocation.

4. Specify **adjudication procedure**. Who decides if an attack
   succeeded? If LLM-judged, name the judge model and the rubric. If
   human-judged, who judges and how is inter-rater reliability
   measured?

5. Specify **scope discipline**. The paper is not a full AI Control
   safety case (D-FRAME-019 first prong). The adversarial layer must
   not pretend to be one. Identify the precise scope language for
   §8.1 that names what this layer *does* characterize (capability
   under bounded adversarial pressure) and what it *does not*
   characterize (scheming-misalignment substitution).

**Deliverable:** An attack-policy table:

| Attack type | Trajectory unit | Authored by | Success score | Tradeoff metric | Budget |
|---|---|---|---|---|---|
| Refusal bypass (vs M7) | ... | ... | ... | ... | ... |
| Mutation escalation (vs M5/M6) | ... | ... | ... | ... | ... |
| Audit tampering (vs M8) | ... | ... | ... | ... | ... |
| Schema evasion (vs M4) | ... | ... | ... | ... | ... |
| Adaptive vs DRG-0 | ... | ... | ... | ... | ... |
| Total budget | 50 trajectories | — | — | — | — |

Plus: §8.1 scope language paragraph (draft text); adjudication
procedure; provenance citations to ST-WebAgentBench / AgentDojo /
ControlArena / Adaptive Attacks on Trusted Monitors where each
protocol element draws from prior art.

---

## Deliverable format

Write your output to:

```
research/runtime_contracts_paper/framing_v2/round_4/RESPONSE.md
```

Structure:

```markdown
# Round 4 Research Response

## Q1 — Predeclared model roster
[Findings, citations, roster table, §7 cell mapping, cost ceiling]

## Q2 — Predeclared thresholds
[Per-metric thresholds, calibration defense, sensitivity analysis,
multi-metric pass rule, hash implementability]

## Q3 — Adversarial attack policy
[Per-attack-type protocol, fifth (adaptive-vs-DRG-0) protocol,
budget allocation, adjudication, §8.1 scope language]

## Summary

### Decisions this round closes
- O-FRAME-007 (model roster): [recommendation]
- O-FRAME-008 (thresholds): [recommendation]
- O-FRAME-009 (attack policy): [recommendation]

### Decisions still open
- [list any of the above that the round couldn't close, with reasons]

### New decisions surfaced
- [anything else the round revealed needs deciding]
```

## Length and depth

Use `/goal` mode. Each question is substantive. Expected length:
- Q1: 1000-1500 words plus the table.
- Q2: 800-1200 words plus the table.
- Q3: 1500-2000 words plus the table — this is the longest and
  most prior-art-dependent.

Cite primary sources for every claim about prior work. Verify
benchmark/governed_agent_bench/* files on disk before claiming
"current spec has X" — those files may have moved since round 3.

## What NOT to do

- Do not edit any file outside `framing_v2/round_4/`.
- Do not propose decisions that contradict locked decisions
  D-FRAME-001 through D-FRAME-019 without flagging the conflict
  explicitly.
- Do not propose a model roster that requires GPU compute Dom doesn't
  have access to (Dom's stack is API + small local inference; do not
  assume 8× H100 access for fine-tuning).
- Do not propose thresholds that are arbitrary; every threshold needs
  a calibration-source defense.
- Do not propose an adversarial protocol that requires hiring a
  professional red team; Dom is a single-author solo researcher.
  LLM-authored attacks + static playbook + Dom-authored manual
  trajectories are the realistic surfaces.
- Do not hallucinate model identifiers (e.g., do not invent
  `claude-3-5-haiku-20251015` without verifying it exists). For each
  model identifier, cite the vendor model-card page or API model-
  listing endpoint.

## When done

1. Save `RESPONSE.md` to the path above.
2. Notify Dom that round 4 research is complete.
3. Stop. Do not also write SYNTHESIS.md or AUDIT_RESPONSE.md — those
   are orchestrator-driven.

---

## Orchestrator notes for the fresh session

If you (orchestrator) are reading this for the first time and the
round 4 prompt has not been dispatched yet, you may revise this
prompt before handing it to Dom. If you revise:

1. Update `ORCHESTRATOR_STATE.md` "Sub-state" to note the revision.
2. Keep the three medium-priority questions; do not drop them.
3. Do not add a fourth question — round size discipline matters.

If RESPONSE.md already exists when you read this, skip the dispatch
and proceed to drafting `AUDIT_PROMPT.md` per the protocol.
