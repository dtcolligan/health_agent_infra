# Batch 3 Edits Summary

## Files touched

| File | Edit type | Lines changed (rough) | Notes |
|---|---|---:|---|
| `project/FRAME.md` | rewrite | ~187 diff lines | Reframed cold-start project identity around the merged NeurIPS 2027 paper, title, triple lineage, load-bearing claims, threat model, mechanism inventory, priority order, and source-of-truth ordering. |
| `project/DECISIONS.md` | append + targeted supersession notes | ~325 diff lines | Appended D-PROJ-018..023 for framing-v2 locked decisions; marked the old title package as superseded by D-PROJ-018; removed obsolete open venue/title rows. |
| `project/OPERATING_MODEL.md` | rewrite | ~210 diff lines | Updated current objective, PARTIALLY MET documentation gate, artifact hierarchy, evaluation scope, threat model, mechanisms, and alignment questions. |
| `project/HYPOTHESES.md` | refactor | ~150 diff lines | Refactored H1 around contract-as-trusted-monitor; added H2/H3 exact merged-paper hypotheses; preserved prior hypotheses as mapped/future-work surfaces. |
| `project/ROADMAP.md` | rewrite | ~148 diff lines | Replaced old planning-gate roadmap with May/June/July-August/post-August merged-paper roadmap and explicit out-of-scope list. |
| `project/REPO_MAP.md` | reclassification | ~43 diff lines | Classified `framing_v2/` as active research lane and `framing_v2/round_*/` as active framing provenance. |

## Cross-file invariant check

- Title: `project/FRAME.md`, `project/DECISIONS.md`,
  `project/OPERATING_MODEL.md`, and `project/HYPOTHESES.md` all use
  "Deterministic Software Contracts as Trusted Monitors in AI Control
  Protocols."
- Active objective: `FRAME.md`, `OPERATING_MODEL.md`, and `ROADMAP.md`
  all state the runtime-contract paper + GovernedAgentBench objective,
  with HAI as the reference runtime and HAI polish subordinate unless
  paper-critical.
- Closed reframes: `DECISIONS.md` D-PROJ-023 marks the
  capability-elicitation reframe and no-red-team threat model as closed
  by D-FRAME-014/015 and not current claims.
- Threat model: `FRAME.md`, `OPERATING_MODEL.md`, `ROADMAP.md`, and
  `DECISIONS.md` all use capability failure plus targeted adversarial
  testing; no pure capability-failure/no-red-team threat model is stated
  as current.
- Mechanism inventory: `FRAME.md` and `OPERATING_MODEL.md` both state
  M4 validation, M5 `agent_safe`, M6 proposal/commit gate, M7
  clinical-boundary refusal with JSON exempt, M8 audit evidence
  emission, and M9-TX transaction integrity held constant.
- Source-of-truth ordering: `FRAME.md`, `OPERATING_MODEL.md`, and
  `REPO_MAP.md` name `framing_v2/CONVERGED.md` first,
  `framing_v2/ORCHESTRATOR_STATE.md` second, and
  `PAPER_OUTLINE_MERGED.md` / batch-1 / batch-2 derivatives beneath
  them.

## New D-PROJ records appended

- D-PROJ-018: merged paper trajectory locked; title + NeurIPS 2027 main
  target supersede the earlier working-title package.
- D-PROJ-019: Engels pilot July 2026 is the merge-decision gate.
- D-PROJ-020: predeclared model roster and USD 1,500 cost ceiling are
  locked.
- D-PROJ-021: targeted adversarial layer is constitutive, not optional.
- D-PROJ-022: Paper 2 redirects to S1 fine-tuning of bounded operators
  at ICML 2028 / NeurIPS 2028.
- D-PROJ-023: Phase 2 documentation alignment cycle and
  `framing_v2/CONVERGED.md` as top source of truth.

## H1 refactor confirmation

- H1 previous wording: "Runtime contracts improve safety-constrained
  operation."
- H1 new wording: "Deterministic software contracts can serve as the
  trusted monitor in an AI control protocol for bounded agent operation,
  with measurable per-mechanism contributions to safety-constrained
  operation under a held-constant deployment prompt."
- H2/H3 status: added/refactored to the exact runtime-as-floor and
  deterministic-Guard hypotheses from the batch prompt.
- Out-of-scope hypotheses section: present.

## REPO_MAP.md changes

- Reclassifications performed: `research/runtime_contracts_paper/framing_v2/`
  is active research lane; `research/runtime_contracts_paper/framing_v2/round_*/`
  subdirectories are active framing provenance.

## A2 / B1 residual sweep

- Files searched: `project/*.md`.
- Residual A2 mentions outside historical-marker context: none.
- Residual B1 mentions outside historical-marker context: none.
- Notes: current `red-team` wording appears only for the locked targeted
  adversarial layer, not for the rejected no-red-team threat model.

## Carry-over for batch 4+

- Batch 4 should update HAI runtime docs to reference the merged-paper
  frame lightly without turning HAI docs into paper-planning docs.
- Batch 5 should update `AGENTS.md`, `CLAUDE.md`, and `README.md` so
  operating contracts point cold agents at `framing_v2/CONVERGED.md`
  before older paper-planning files.
- The existing project doc-alignment test still has two out-of-batch
  failures: one expects the pre-framing-v2 title string in
  `research/runtime_contracts_paper/PAPER_FRAME.md`, and one expects
  `HAI Paper-Readiness Engineering` in
  `research/runtime_contracts_paper/PROJECT_EXECUTION_PLAN.md`. Batch 3
  did not edit those non-target files.

## Open issues

- None requiring a new framing decision in batch 3. The only failed
  verification is the out-of-batch project test described above.
