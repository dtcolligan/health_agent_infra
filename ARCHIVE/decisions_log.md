# Decisions Log (Historical)

Full supersession chain across all numbering systems used during the
repo's life. **Not active state.** Active decisions live in
[`/PAPER.md`](../PAPER.md) §"Active Decisions" as D-01..D-13.

This file exists so a future-Y3 sequel paper or a maintainer-handoff
can recover the reasoning behind any historical decision without
archeology.

Four numbering systems lived in this repo and have been collapsed:

| System | Range | Origin |
|---|---|---|
| `D-PROJ-NNN` | 001..024 | `project/DECISIONS.md` post-reframe project log |
| `D-FRAME-NNN` | 001..027 | `framing_v2/CONVERGED.md` Phase 1 framing |
| `D-PREPRINT-NNN` | 001..009 | `framing_v2/PREPRINT_RESCOPE.md` preprint scope |
| `D1..D28` (AGENTS) | D1..D28 | AGENTS.md "Settled Decisions" (HAI-release-cycle + framing imports) |
| `D-NN` (current) | D-01..D-13 | `/PAPER.md` collapsed active state |

## Major Transitions

| Date | Event |
|---|---|
| 2026-05-07 | Research reframe (D-PROJ-017): repo is research-engineering, not HAI product |
| 2026-05-08 | HAI frozen as product (D-PROJ-016): v0.2.0 PyPI is the pinned reference snapshot |
| 2026-05-09 | Runtime-first reframe (D-PROJ-013/014/015): headline experiment varies runtime, not prompt; schemas v2 split condition into runtime_mode × model_class |
| 2026-05-11 | Framing-v2 Phase 1 closed: D-FRAME-001..027 locked; merged NeurIPS 2027 main-conference trajectory |
| 2026-05-11 | Framing-v2 Phase 2 closed: 33 docs aligned across paper/benchmark/project/HAI/operating lanes |
| 2026-05-15 | Preprint rescope (D-PROJ-024 / D-PREPRINT-001..009): arXiv preprint by Sept 30, Engels deferred, Option B floor, USD 300 ceiling |
| 2026-05-15 | Repo consolidation: cold-start surface collapsed to 4 root docs + lane READMEs; provenance moved to `/ARCHIVE/` |

## D-PROJ Series (Project-Level)

Originally in `project/DECISIONS.md`. The decision file itself is at
[`project_decisions/DECISIONS.md`](project_decisions/DECISIONS.md) for
full historical detail.

| ID | Decision | Current state |
|---|---|---|
| D-PROJ-001 | Repo is runtime-contract research, not HAI product | Active (D-01 distillate) |
| D-PROJ-002 | North star: governed local operation over sensitive user-owned data | Active (preserved as framing in PAPER.md research thesis) |
| D-PROJ-003 | HAI is reference runtime, not paper topic | Active (D-11) |
| D-PROJ-004 | Benchmark name: GovernedAgentBench (not HACO-Bench) | Active (unchanged) |
| D-PROJ-005 | Working title leads with claim, not benchmark | Superseded by D-PROJ-018 (which is itself superseded by D-02) |
| D-PROJ-006 | Conservative measurement-first paper posture | Active (preserved as `/PAPER.md` operational discipline) |
| D-PROJ-007 | Non-clinical health boundary is part of the contract | Active (D-12) |
| D-PROJ-008 | Experimental scope: rule + local + cloud + fine-tuned + scaffold ablation conditions | Partially superseded by D-PROJ-013 (no `with_manifest` vs `without_manifest`); preprint scope narrows further to Option B + optional Option C |
| D-PROJ-009 | Benchmark path does not require all six HAI domains | Active |
| D-PROJ-010 | Documentation alignment is the gate before new implementation | Active (current discipline pass executed this) |
| D-PROJ-011 | Current docs and historical provenance must stay separated | Active (D-13: provenance goes to ARCHIVE/) |
| D-PROJ-012 | Owner-based repo shape: project/, hai/, benchmark/, research/ | Partially superseded: project/ and research/ collapsed; hai/ and benchmark/ remain |
| D-PROJ-013 | Runtime is the primary axis of variation; prompt held constant | Active (D-10) |
| D-PROJ-014 | Deployment-realistic prompt held constant; no with/without manifest condition | Active (D-10) |
| D-PROJ-015 | Schemas v2 split `condition` into `runtime_mode` × `model_class` | Active (built into trajectory.schema.json v2) |
| D-PROJ-016 | HAI frozen as a product at v0.2.0 PyPI | Active (D-11) |
| D-PROJ-017 | Six architectural answers from round-1 audit: manifest schema v2; M5+M6 stay separate; M7 canonical seam; M9-TX held constant; Tier 5 future-work appendix; `no_runtime` → `no_runtime_enforcement` | Active (built into mechanism inventory D-09 and runtime mode list) |
| D-PROJ-018 | Merged paper trajectory: Paper 1 + Engels into NeurIPS 2027 main | Superseded by D-PROJ-024 (D-01 + D-03) |
| D-PROJ-019 | Engels pilot is merge-decision gate | Superseded by D-PROJ-024 (D-03: Engels deferred) |
| D-PROJ-020 | Predeclared 6 Houdinis + 3 Guards roster + USD 1,500 ceiling | Superseded by D-PROJ-024 (D-04 + D-05 + D-06: narrow roster, USD 300 ceiling) |
| D-PROJ-021 | Adversarial layer is constitutive (50 trajectories) | Partially superseded by D-PROJ-024 (D-07: 16 trajectories; threat-model class unchanged) |
| D-PROJ-022 | Paper 2 = S1 fine-tuning sequel | Active (preserved as future-work in PAPER.md) |
| D-PROJ-023 | Phase 2 documentation alignment is the current cycle | Superseded: Phase 2 closed 2026-05-11, preprint rescope replaces with `/PAPER.md` discipline |
| D-PROJ-024 | Preprint rescope locked 2026-05-15 | Active; imports D-PREPRINT-001..009; distilled into D-01..D-13 |

## D-FRAME Series (Framing-v2)

Originally in `framing_v2/CONVERGED.md`. Full Phase 1 + Phase 2 history
at [`framing_v2/`](framing_v2/).

| ID | Topic | Current state |
|---|---|---|
| D-FRAME-001 | Headline framing | Active (transferred to D-09 mechanism inventory + PAPER.md frame) |
| D-FRAME-002 | Lineage anchor (AI control + safety specs + LLM-monitor baselines) | Active (PAPER.md §"Lineage Anchor") |
| D-FRAME-003 | Threat model = capability failure + targeted adversarial | Active (D-07 modulo trajectory count) |
| D-FRAME-004 | Headline empirical = Engels Backdoor Code | Superseded by D-03 |
| D-FRAME-005 | Direct competitor = Hierarchical Summarization | Active (prose only; D-08 dropped empirical contrast) |
| D-FRAME-006 | Closest benchmark prior = ST-WebAgentBench | Active |
| D-FRAME-007 | Benchmark framing = contract-as-intervention with model-scale substitution | Active (preprint scope narrows model-scale to Option C stretch) |
| D-FRAME-008 | Target venue = NeurIPS 2027 main, May 2027 deadline | Superseded by D-01 (arXiv preprint, Sept 30 2026) |
| D-FRAME-009 | Merged paper 1 + paper 2 | Superseded by D-03 (Engels deferred, unmerged) |
| D-FRAME-010 | Paper 2 = S1 fine-tuning sequel | Active (future work) |
| D-FRAME-011 | Engels pilot July 2026 = decision gate | Superseded by D-03 |
| D-FRAME-012 | Drop "user-owned structured data" from title | Active |
| D-FRAME-013 | Personal wellness = instantiation, not framing | Active (D-12 boundary + PAPER.md frame) |
| D-FRAME-014 | A2 capability-elicitation reframe closed | Active (do not reopen) |
| D-FRAME-015 | B1 no-red-team option closed | Active (D-07 keeps a small adversarial layer) |
| D-FRAME-016 | Title locked | Active (D-02) |
| D-FRAME-017 | Mechanism inventory M4-M8 + held-constant M9-TX | Active (D-09) |
| D-FRAME-018 | Engels pilot protocol (60 APPS + 3 Houdinis + DRG-0 + Haiku Guard + 6-clause commit rule) | Superseded by D-03 (carried to future Engels paper) |
| D-FRAME-019 | Two paper-killer preempts (framing-overclaim + DRG-artifacts) | Partially superseded: framing-overclaim preempt remains active and more load-bearing post-rescope; DRG-artifacts preempt carries to future Engels paper |
| D-FRAME-020 | Predeclared 6 Houdinis + 3 Guards roster | Superseded by D-04 + D-05 (narrow preprint roster) |
| D-FRAME-021 | AND-pass thresholds + 7 zero-tolerance critical violations | Active (applied at smaller preprint scale) |
| D-FRAME-022 | 50-trajectory attack policy | Superseded by D-07 (16 trajectories) |
| D-FRAME-023 | USD 1,500 cost ceiling | Superseded by D-06 (USD 300) |
| D-FRAME-024 | Bounded HS empirical contrast (L6, 2-week + USD 200 caps) | Superseded by D-08 (HS prose only) |
| D-FRAME-025 | Coding-agent slice = Appendix E sketch only | Active (subject to keep/drop O-PREPRINT-002 / D-O-02) |
| D-FRAME-026 | ST-WAB differentiation table + axis | Active |
| D-FRAME-027 | Paper 2 = S1 fine-tuning of bounded operators | Active (future work) |

## D-PREPRINT Series

From `framing_v2/PREPRINT_RESCOPE.md` (now archived under
`framing_v2/`). All distilled into D-01..D-13 in `/PAPER.md`.

| ID | Decision | Distilled to |
|---|---|---|
| D-PREPRINT-001 | arXiv preprint by 2026-09-30 | D-01 |
| D-PREPRINT-002 | Engels deferred to future paper | D-03 |
| D-PREPRINT-003 | Sonnet 4 re-anchor to claude-sonnet-4-6 | D-04 |
| D-PREPRINT-004 | Empirical = Option B floor + Option C stretch | D-05 |
| D-PREPRINT-005 | Cost ceiling USD 300 | D-06 |
| D-PREPRINT-006 | Adversarial layer = 16 trajectories | D-07 |
| D-PREPRINT-007 | Bounded HS contrast dropped | D-08 |
| D-PREPRINT-008 | Title / mechanism inventory / lineage unchanged | D-02 + D-09 |
| D-PREPRINT-009 | Future-work bucket expansion (Engels, full roster, S1 FT, HS, full red-team) | PAPER.md §"Out (deferred to future work)" |

## D1-D28 (AGENTS.md Settled Decisions)

Many of D1-D28 in the prior AGENTS.md were HAI release-cycle workflow
patterns (D10-D15: persona harness location, bug-hunt phase, threshold
coercer discipline, threshold-injection seam, plan-audit pattern,
cycle-weight tiering) and D16 (W-2U-GATE foreign-user split).

The HAI-release-cycle decisions (D10-D16) are historical because HAI
is frozen as a product (D-11). They remain useful provenance if HAI
release work ever reopens. Specifically:

- **D10:** Persona harness lives in `hai/verification/dogfood/`, not in
  CI. Still true.
- **D11:** Pre-PLAN bug-hunt phase pattern. Dormant.
- **D12:** Bool-as-int coercion discipline using `core.config.coerce_*`.
  Active (preserved in `/AGENTS.md` governance invariants).
- **D13:** Threshold-injection seam trusted-by-design. Active.
- **D14:** Pre-cycle Codex plan-audit pattern for substantive PLANs.
  Dormant.
- **D15:** Cycle-weight tiering (substantive / hardening / doc-only /
  hotfix). Dormant.
- **D16:** W-2U-GATE split (W-2U-INSTALL closed verbal-only; W-2U-WEARABLE
  and W-2U-DOGFOOD deferred to v0.4 review). Dormant (HAI is frozen).

D17-D27 in the prior AGENTS.md were imports of D-PROJ-016/017 and
D-FRAME-001..027 already enumerated above.

D28 (preprint rescope) collapsed into D-01..D-13 in `/PAPER.md`.

## How to Recover a Decision

To understand a specific historical decision:

1. Find the ID prefix (D-PROJ / D-FRAME / D-PREPRINT / D-NN-AGENTS).
2. For D-PROJ: read [`project_decisions/DECISIONS.md`](project_decisions/DECISIONS.md).
3. For D-FRAME: read [`framing_v2/CONVERGED.md`](framing_v2/CONVERGED.md)
   and [`framing_v2/ORCHESTRATOR_STATE.md`](framing_v2/ORCHESTRATOR_STATE.md).
4. For D-PREPRINT: read [`framing_v2/PREPRINT_RESCOPE.md`](framing_v2/PREPRINT_RESCOPE.md).
5. For D1-D28 (AGENTS.md): read the git history of `/AGENTS.md` at
   commit `~consolidate: collapse repo to preprint-only navigable surface`.

The full Phase 1 + Phase 2 framing-v2 orchestration record (3 rounds +
6 batches + final audit + closure) is preserved unchanged at
[`framing_v2/`](framing_v2/).
