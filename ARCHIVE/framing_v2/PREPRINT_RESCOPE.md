# Preprint Rescope

**Status:** Active source of truth for preprint scope.
**Locked:** 2026-05-15
**Supersedes (for preprint scope only):** D-FRAME-008, D-FRAME-009,
D-FRAME-010, D-FRAME-011, D-FRAME-018, D-FRAME-019 (clause 2),
D-FRAME-020, D-FRAME-022, D-FRAME-023, D-FRAME-024, D-FRAME-027.
**Preserves intact:** D-FRAME-001 (headline framing), D-FRAME-002
(lineage anchor), D-FRAME-003 (threat model, with adversarial layer
scoped down), D-FRAME-005 / D-FRAME-006 / D-FRAME-007 (prior-art
relationships), D-FRAME-012 / D-FRAME-013 / D-FRAME-014 / D-FRAME-015
(closed reframes), D-FRAME-016 (title), D-FRAME-017 (mechanism
inventory), D-FRAME-019 (clause 1: framing-overclaim preempt),
D-FRAME-021 (predeclared thresholds; applied to smaller experiment),
D-FRAME-025 (Appendix E sketch), D-FRAME-026 (ST-WAB differentiation).
**Reading order note:** `CONVERGED.md` is preserved as the
NeurIPS 2027 main-conference framing record. For all questions about
current paper scope, calendar, roster, cost, and empirical contribution,
this file overrides CONVERGED.md.

---

## One-paragraph summary

The merged NeurIPS 2027 main-conference trajectory is rescoped to an
arXiv preprint deliverable by 2026-09-30. The Engels Backdoor Code
extension is unmerged and deferred to a future paper. Sonnet 4 cells
re-anchor to `claude-sonnet-4-6`. The empirical contribution becomes
mechanism ablations (M4-M8 toggled individually) on one model class
against ~25-30 GovernedAgentBench tasks in the HAI reference domain,
with an optional model-scale stretch if the July substrate holds. Cost
ceiling drops from USD 1,500 to ~USD 300. The Greenblatt
DRG-artifacts paper-killer preempt disappears with Engels; the
framing-overclaim preempt remains active. Title, mechanism inventory,
threat-model class, and lineage anchor are unchanged.

---

## Why we are rescoping

Three drivers, all maintainer-side:

1. **Bandwidth.** Year-2 Imperial coursework, summer-2026 paid roles
   (Cyber Mangrove + Lettingweb + IDEA Lab), and the autumn-2026
   application window (MATS / DeepMind Student Researcher / SPAR) leave
   no honest path to the NeurIPS 2027 main-conference scope at single-
   maintainer cadence.
2. **Sub-specialty shift.** The maintainer is preparing a handoff from
   agent safety / evals / runtime governance toward mechanistic
   interpretability. The preprint is the clean exit artifact for this
   subspace, not the continuing investment.
3. **Pre-committed floor.** The user's career strategy in
   `~/.claude/CLAUDE.md` explicitly named "workshop preprint with
   benchmark released and reproducible baselines" as the pre-committed
   floor outcome before May 2026. This rescope executes that floor with
   discipline rather than retreating from a ceiling.

External framing does not soften. This remains an AI control paper
under the AI safety umbrella: deterministic software contracts as the
trusted monitor in an AI control protocol for bounded agent operation.

---

## Locked preprint-scope decisions

### D-PREPRINT-001: Target deliverable

**Locked.** arXiv preprint, 8-12 pages NeurIPS or ICML LaTeX format,
public and citable, not peer-reviewed. Submission 2026-09-30. Permanent
ID e.g. `arXiv:2609.XXXXX`. Sponsor required (any cs.LG-prior-submission
researcher endorses).

### D-PREPRINT-002: Engels deferral

**Locked.** The Engels Backdoor Code extension is unmerged and deferred
to a future paper. Removed from preprint:

- §7.5 Engels-pilot section.
- DRG-0 and Houdini/Guard scaling-laws-for-oversight curve placement.
- D-FRAME-018 pilot protocol (60 APPS + 10 smoke + 3 Houdinis + DRG-0
  + Haiku Guard + USD 18.60 + 6-clause commit rule).
- D-FRAME-019 clause 2 (Greenblatt DRG-artifacts paper-killer preempt).
- D-FRAME-022's 18 adaptive-vs-DRG-0 trajectories.
- Hypothesis H3 in `project/HYPOTHESES.md`.
- D-FRAME-011 merge-decision gate (no merge to gate).
- "Merged paper 1 + paper 2" framing (D-FRAME-009); D-FRAME-010's S1
  fine-tuning sequel framing remains valid as future-work, alongside
  Engels.

Engels remains a legitimate future paper using GovernedAgentBench's
deterministic-Guard slot. The "five Houdini attempts per sample"
verification item against arXiv:2504.18530 §4 carries forward to that
future paper, not this preprint.

### D-PREPRINT-003: Sonnet 4 re-anchor

**Locked.** All `claude-sonnet-4-20250514` cells in the predeclared
roster re-anchor to `claude-sonnet-4-6` immediately. The 2026-06-15
Sonnet 4 retirement binding (CONVERGED.md calendar) is dissolved.

### D-PREPRINT-004: Empirical contribution scope

**Locked floor (Option B).** Mechanism-ablation paper:

- One model class run across all six runtime modes: `full_contract`,
  `no_validation`, `no_agent_safe`, `no_proposal_gate`, `no_refusal`,
  `no_audit_chain`. (`no_runtime_enforcement` joins as the all-off
  control.)
- ~25-30 GovernedAgentBench tasks selected from existing L1, L2, L5,
  L6, L7 pilot tasks to ensure each of M4-M8 is load-bearing in at
  least one task.
- Headline empirical claim: per-mechanism pass/fail deltas isolate
  the contribution of each runtime mechanism under a held-constant
  deployment prompt. Tests H1 in `project/HYPOTHESES.md`.
- ~5,000-6,000 API calls; well under the new cost ceiling.

**Optional stretch (Option C), only if the July substrate holds.**
Add a small model-scale cross-product:

- 2-3 model classes total: rule baseline + the Option-B model +
  optionally one cloud cell (`claude-sonnet-4-6`).
- Two runtime modes only: `full_contract` and
  `no_runtime_enforcement`.
- Same ~25-30 task set.
- Tests H2 weakly; framed as preliminary evidence, not headline.

**Single model class for Option B.** Default candidate:
`Qwen/Qwen2.5-7B-Instruct-Turbo` (Together AI) for cost predictability
and prior research familiarity. Final selection ratified at the
mid-June pilot-protocol-lock gate.

### D-PREPRINT-005: Cost ceiling

**Locked.** USD 300 hard ceiling across all model API calls for the
preprint. Option B alone is well under USD 100; the remaining headroom
covers Option C stretch and one full retry cycle. Excludes local GPU
opportunity cost and human time.

### D-PREPRINT-006: Adversarial layer scope

**Locked.** Threat-model class remains capability failure plus a
targeted adversarial layer (D-FRAME-003 unchanged). The 50-trajectory
breakdown in D-FRAME-022 reduces to **16 trajectories** for the
preprint:

| Attack type | Preprint count | Target mechanism |
|---|---:|---|
| Refusal bypass | 4 | M7 |
| Mutation escalation | 4 | M5 + M6 |
| Audit tampering | 4 | M8 |
| Schema evasion | 4 | M4 |
| Adaptive-vs-DRG-0 | 0 (deferred) | Future paper |

Reported as §7 (or §8 depending on final outline) characterization
result. Not a headline contribution. Honest scope statement: "bounded
stress test of whether deterministic runtime mechanisms remain
observable and load-bearing under known attack classes." No claim of a
full control safety case.

### D-PREPRINT-007: Bounded Hierarchical Summarization contrast dropped

**Locked.** D-FRAME-024's L6-only bounded empirical contrast against
Hierarchical Summarization is dropped from the preprint. Hierarchical
Summarization remains in §2 related work as the direct LLM-monitor
comparator (D-FRAME-005), prose only. The 2-week + USD 200 cap
recovers as future work.

### D-PREPRINT-008: Title, mechanism inventory, and lineage unchanged

**Locked.** The preprint retains:

- Title: *Deterministic Software Contracts as Trusted Monitors in AI
  Control Protocols* (D-FRAME-016).
- Mechanism inventory: M4 / M5 / M6 / M7 / M8 + held-constant M9-TX
  (D-FRAME-017).
- Lineage triple: AI control protocols + safety specs + LLM-monitor
  baselines (D-FRAME-002).
- Headline framing: "deterministic software contract operationalizes a
  safety spec as the trusted monitor in an AI control protocol for
  bounded agent operation" (D-FRAME-001).
- Framing-overclaim paper-killer preempt: arXiv:2510.09462 citation
  in §1 and §2 plus the "trusted-monitor substrate" reframe
  (D-FRAME-019 clause 1).

The connection to AI control becomes a framing claim defended in
prose, not an empirical claim defended by the (now-deferred) Engels
extension. The framing-overclaim preempt is therefore more
load-bearing in the preprint than it was in the merged paper.

### D-PREPRINT-009: Future-work expansion

**Locked.** The preprint's future-work section commits the following
threads, in order of likely sequel priority:

1. **Engels Backdoor Code extension.** DRG-0 added to the Engels
   scaling-laws-for-oversight curve as a Guard with general Elo = 0.
   Carries the deferred D-FRAME-018 pilot protocol.
2. **Full model-scale cross-product.** The predeclared D-FRAME-020
   roster of 6 Houdinis + 3 Guards under the AND-pass threshold
   package (D-FRAME-021).
3. **S1 fine-tuning of bounded operators.** Trained operators reach
   contract-compliance at smaller scales than untrained operators
   (D-FRAME-010 + D-FRAME-027). Future-work appendix in CLAIM_LADDER.md
   already reflects this.
4. **Bounded Hierarchical Summarization contrast.** L6 governance /
   refusal with the original 2-week + USD 200 cap (D-FRAME-024).
5. **Full adaptive red-team.** Beyond the 16 trajectories shipped in
   the preprint.

The preprint must not imply these are in-paper results.

---

## Paper outline (preprint)

| § | Section | Pages |
|---|---|---|
| 1 | Introduction (motivation, trusted/untrusted decomposition, contribution) | 1.5 |
| 2 | Background and related work (AI control, software contracts, capability-based security, agent runtimes, LLM monitors incl. HS prose contrast) | 1 |
| 3 | The runtime contract (formal definition, M4-M8 + M9-TX, guarantees) | 2-3 |
| 4 | GovernedAgentBench methodology (tasks, scorer, runtime modes, held-constant prompt design) | 2 |
| 5 | Mechanism ablation results (Option B headline) | 1.5-2 |
| 6 | Model-scale extension (Option C stretch; demote to §5.3 if absent) | 0-1 |
| 7 | Targeted adversarial characterization (16 trajectories) | 0.5-1 |
| 8 | Discussion (limitations, personal-health-as-domain defense paragraph) | 1 |
| 9 | Future work + conclusion | 1 |
| - | Appendix: tasks, prompts, seeds, reproducibility, additional results | - |

Total 8-12 pages, NeurIPS or ICML LaTeX format.

---

## Calendar binding

Today: 2026-05-15.

| Window | Block | Notes |
|---|---|---|
| 2026-05-15 to 2026-05-31 | Framing rewrite | Propagate this file's deltas to README.md, project/FRAME.md, project/DECISIONS.md, project/ROADMAP.md, project/HYPOTHESES.md, research/runtime_contracts_paper/PAPER_FRAME.md, AGENTS.md, hai/docs/current_system_state.md. CONVERGED.md gets a banner; body preserved. |
| 2026-05-15 to 2026-06-30 | Benchmark measurement-readiness | Freeze schemas, scorer, harness, fixtures, rule baseline, runtime-mode toggling. Scoped to what Option B + (optionally) Option C needs, not the full year-long version. |
| 2026-06-15 to 2026-06-22 | Pilot-protocol-lock gate | Write down exactly what experiments run, which model, success criteria, pre-committed falsification. Single Dom decision point. |
| 2026-07 | Pilot execution | Option B run end-to-end. Option C stretch only if Option B is clean by mid-July. No scope expansion mid-flight. |
| 2026-07-28 to 2026-08-15 | SPAR application window | Cite "preprint in late-stage drafting; GovernedAgentBench v1.0 tagged." |
| 2026-07-25 to 2026-09-15 | Paper writing | Start outline + related-work in late July before pilot finalises; do not start from blank page in August. |
| 2026-08 to 2026-09-15 | Benchmark release polish | README, install, reproducibility script, v1.0 tag. Acid test: external researcher runs it in October and reproduces preprint numbers. |
| 2026-09-15 to 2026-09-30 | arXiv submission | Sponsor confirmation, LaTeX polish, moderation 1-3 days. |
| 2026-10-01 | Mech interp handoff | Subspace pivot begins. No paper work bleeds into October. |

The Sonnet 4 retirement on 2026-06-15 is dissolved by D-PREPRINT-003.

---

## Downstream doc-alignment work

The following active docs need to reflect the preprint rescope. Order
is rough priority; nothing here is blocking the next substantive step
(benchmark measurement-readiness).

1. `CONVERGED.md` — banner at top pointing to this file as current
   scope; body preserved as NeurIPS-2027-main historical record.
2. `project/FRAME.md` — Active Objective section, priority order,
   paper source-of-truth order.
3. `project/DECISIONS.md` — new D-PROJ-024 importing this rescope.
4. `project/ROADMAP.md` — Now / Next / Then windows replaced with the
   2026-05-15 to 2026-09-30 calendar.
5. `project/HYPOTHESES.md` — H2 demoted to weak-evidence / future
   work, H3 moved to future-work-only section.
6. `research/runtime_contracts_paper/PAPER_FRAME.md` — venue, abstract
   shape, contributions list, empirical design, Engels-pilot section
   removed.
7. `research/runtime_contracts_paper/PAPER_OUTLINE_MERGED.md` —
   rename or supersede; outline replaced by §1-9 above.
8. `research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md` —
   evaluation scope reduced to Option B floor + Option C stretch.
9. `research/runtime_contracts_paper/HAI_PAPER_READINESS_EXECUTION.md`
   — preserve, but tag Phase 3+ as preprint-floor scope rather than
   main-conference scope.
10. `AGENTS.md` — "Settled Decisions" updated to import
    D-PREPRINT-001..009; "What This Project Is" paragraph rewrites
    the four-artifact list.
11. `README.md` — Active Objective, calendar, scope.
12. `benchmark/governed_agent_bench/README.md` — current-gate row,
    measurement-readiness exit criteria, "model_roster.md required" gate.
13. `hai/docs/current_system_state.md` — Research-lane status table,
    Next cycles row.

CONVERGED.md banner is the minimum required for cold-start
correctness; everything else is alignment work.

---

## What stays unchanged

- The repo's owner model (`project/`, `hai/`, `benchmark/`, `research/`).
- HAI's frozen-as-product posture (D-PROJ-016). No HAI v0.2.1+ work
  re-opens.
- The non-clinical health boundary (D-PROJ-007, D-FRAME-013).
- The six health domains as the reference instantiation.
- The W57 governance invariant, agent-safe dispatch boundary, and
  three-state audit chain.
- The "framing v2 orchestration" pattern as a validated cycle shape
  (AGENTS.md "Patterns the cycles have validated").
- The closed reframes A2 (capability elicitation, D-FRAME-014) and B1
  (no red-team, D-FRAME-015). The preprint keeps a small adversarial
  layer; it does not reopen the no-red-team option.

---

## Open decisions

Three small ones remain, all resolvable at the mid-June pilot-protocol-
lock gate or earlier:

| ID | Decision | Recommended resolution window |
|---|---|---|
| O-PREPRINT-001 | Final Option-B model class. Default `Qwen/Qwen2.5-7B-Instruct-Turbo`; alternative is `Qwen/Qwen2.5-32B-Instruct` Fireworks if 7B is too capable to surface mechanism deltas. | Mid-June pilot lock. |
| O-PREPRINT-002 | Whether to keep the Appendix E coding-agent sketch (D-FRAME-025) in the preprint or drop it. Anti-overclaim header still required if kept. | Mid-August during paper writing. |
| O-PREPRINT-003 | Whether arXiv sponsor is already in-network (Imperial UROP supervisor, IDEA Lab contact, or external researcher) or needs cold-outreach. | Lock by 2026-08-15 to leave 6 weeks of margin. |

---

## Provenance

This rescope was decided by the maintainer on 2026-05-15 in a Claude
Code session, four days after Phase 1 + Phase 2 of the framing-v2
orchestration closed (`ORCHESTRATION_COMPLETE.md` dated 2026-05-11).
The three locked decisions in this file were named explicitly:

- "I think I want to defer Engels to a future paper" (→ D-PREPRINT-002)
- "I am happy to reanchor to Claude-Sonnet-4-6 now" (→ D-PREPRINT-003)
- Empirical scope = Option B floor + Option C stretch (→ D-PREPRINT-004)

The remaining D-PREPRINT decisions (001, 005, 006, 007, 008, 009) are
implications the assistant locked in, consistent with the three
maintainer calls and the pre-existing framing-v2 decisions.
