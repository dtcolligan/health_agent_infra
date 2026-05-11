# Superseded — HAI Plans

**Status:** Historical provenance for pre-reframe HAI planning artifacts.
**Moved:** 2026-05-11.

Files here are **not current planning truth.** They were authored
before the 2026-05-11 framing-v2 merge and reflect the pre-reframe
HAI strategic / evaluation / risk planning. HAI is now frozen as a
product per D-PROJ-016 (2026-05-08) and the active project objective
is the merged paper *Deterministic Software Contracts as Trusted
Monitors in AI Control Protocols* (NeurIPS 2027 main conference).

For current planning, read:

- `../../../research/runtime_contracts_paper/framing_v2/CONVERGED.md` —
  locked framing summary
- `../../../project/DECISIONS.md` — D-PROJ-016 HAI freeze + D-PROJ-018..023
  framing-v2 imports
- `../tactical_plan_v0_1_x.md` — HAI reference-runtime backlog (active
  support-lane planning)
- `../README.md` — the plans tree reading-order index

## What's in here

| File | Original path | Why superseded |
|---|---|---|
| `risks_and_open_questions.md` | `plans/` | Pre-reframe HAI risk register. Risks against pre-merge framing; replaced by `../../../framing_v2/CONVERGED.md` calendar binding + carry-over lists. |
| `success_framework_v1.md` | `plans/` | Pre-reframe HAI value framework. HAI's project-level value is now subordinate to the paper per D-FRAME-013 (instantiation, not framing). |
| `strategic_plan_v2.md` | `plans/post_v0_1_18/` | Pre-reframe HAI strategic plan. HAI is frozen as a product per D-PROJ-016; the strategic surface for HAI shrinks to runtime-fix packets only. |
| `eval_strategy_v1.md` | `plans/eval_strategy/v1.md` | Pre-reframe HAI correctness strategy. Project-wide research evaluation is now in `../../../research/runtime_contracts_paper/RESEARCH_EVAL_STRATEGY.md`. |

## Do not edit

These files are preserved as-is. The supersession headers (added in
Phase 2 batch 6) disclaim their content explicitly. If you find a
reference to one of these files in an active doc that should point
to a current artifact, fix the active doc.

## Note on `historical/` vs `superseded/`

`hai/reporting/plans/historical/` also exists and serves the same
function for older HAI cycle artifacts (multi_release_roadmap,
post_v0_1_roadmap, phase_0_*, etc.). The `superseded/` directory is
the framing-v2-era variant, holding files that the
2026-05-11 merge specifically retired. Both directories are
provenance-only.
