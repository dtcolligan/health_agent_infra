# Batch 4 Edits Summary

## Files touched

| File | Edit type | Lines changed (rough) | Notes |
|---|---|---:|---|
| `hai/docs/hai_reference_runtime.md` | light paper-framing update | ~9 | Added `CONVERGED.md` pointer, replaced dropped "sensitive user-owned structured data" broad-claim wording, and added `CONVERGED.md` to the research-reader row. |
| `hai/docs/runtime_contract_overview.md` | light paper-framing update | ~5 | Added `CONVERGED.md` as the source for active title, venue, and mechanism inventory; fixed the adjacent project-doc links while editing the same paragraph. |
| `hai/docs/current_system_state.md` | light paper-framing update | ~14 | Added `CONVERGED.md` to canonical sources, updated the paper-frame row from "working title" to locked title + NeurIPS 2027 main target, and aligned next-cycle rows to Phase 2 doc alignment plus the D-PROJ-016 freeze. |
| `hai/docs/architecture.md` | light paper-framing update | ~5 | Added `CONVERGED.md` paper-framing pointer and updated the eval row from pre-reframe future-eval wording to paper/benchmark scoring where explicitly scoped. |
| `hai/docs/non_goals.md` | light paper-framing update | ~3 | Added a `CONVERGED.md` pointer to the non-clinical boundary / limitations note. |

## Paper-framing references updated

- `hai/docs/hai_reference_runtime.md`:
  - Found the dropped "sensitive user-owned structured data" broad-claim wording near the opening "What HAI Is" section -> updated to the locked trusted-monitor / AI-control-protocol framing.
  - Added the requested HAI-reference-runtime header note pointing paper readers to `framing_v2/CONVERGED.md`.
  - Added `CONVERGED.md` to the research / benchmark reviewer source list.
- `hai/docs/runtime_contract_overview.md`:
  - Found the top-level repo-wide research-frame pointer without the locked paper-framing authority -> added `CONVERGED.md` for title, venue, and mechanism inventory.
- `hai/docs/current_system_state.md`:
  - Found "Working title" in the research-lane paper-frame row -> updated to locked title + NeurIPS 2027 main-conference target.
  - Found canonical-source ordering without `framing_v2/CONVERGED.md` -> added it.
  - Found next-cycle rows still naming future HAI product work -> added the current Phase 2 doc-alignment cycle and marked the old v0.2.1 insight-ledger row as superseded by D-PROJ-016.
- `hai/docs/architecture.md`:
  - Found no title or venue string, but the file lacked a paper-framing authority pointer -> added `CONVERGED.md`.
  - Found pre-reframe "future personal-guidance / skill harness scoring" wording -> updated to paper/benchmark trajectory scoring and explicitly scoped skill-harness scoring.
- `hai/docs/non_goals.md`:
  - Found the non-clinical boundary note, which is paper-relevant -> added `CONVERGED.md` pointer for active paper framing and limitations scope.

## HAI runtime architecture content touched?

No. The edits did not change installation steps, operator workflow, domain definitions, CLI surface, schema head, command counts, migration discipline, or HAI runtime architecture claims.

## Mechanism inventory consistency

The five target files do not name the M4-M8/M9-TX mechanism inventory directly after this batch. The new pointers direct readers to `framing_v2/CONVERGED.md`, where D-FRAME-017 states M4 validation, M5 `agent_safe` dispatch refusal, M6 W57 proposal/commit gate, M7 clinical-boundary refusal with JSON output exempt, M8 audit evidence emission, and M9-TX transaction integrity held constant.

## Cold-start pointer to framing_v2/CONVERGED.md

- `hai/docs/hai_reference_runtime.md`
- `hai/docs/runtime_contract_overview.md`
- `hai/docs/current_system_state.md`
- `hai/docs/architecture.md`
- `hai/docs/non_goals.md`

## Carry-over for batch 5+

- Batch 5 should update operating contracts (`AGENTS.md`, `CLAUDE.md`, `README.md`) so cold-start agents read `framing_v2/CONVERGED.md` before older paper-planning files.

## Open issues

- None.
