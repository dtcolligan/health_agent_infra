# reporting/experiments/

**Frozen historical prototypes.** Each subdirectory captures one
throwaway experiment that was used to decide whether to commit to a
specific architectural bet during the v1 rebuild. They are preserved
as proof of those decisions; they are **not** living code, and the
runtime does not import from here.

If you are looking for current runtime behaviour, this is the wrong
directory — see
[`../../src/health_agent_infra/`](../../src/health_agent_infra/) and
[`../docs/architecture.md`](../docs/architecture.md).

## What lives here

| Subdir | Phase | What it decided |
|---|---|---|
| [`synthesis_prototype/`](synthesis_prototype/) | Phase 0.5 (feasibility) | Whether a single synthesis skill could reconcile per-domain proposals via mechanical X-rules without devolving into prose. Eight scenarios, three X-rules, two domains. Verdict: GO for Phase 1. Gate doc: [`../plans/historical/phase_0_findings.md`](../plans/historical/phase_0_findings.md). |
| [`nutrition_retrieval_prototype/`](nutrition_retrieval_prototype/) | Phase 2.5 Track A (retrieval gate) | Whether food-string → USDA candidate retrieval was good enough to support meal-level nutrition in v1. 20 queries against a real USDA SR Legacy slice. Verdict: NO — nutrition shipped macros-only. Gate doc: [`../plans/historical/phase_2_5_retrieval_gate.md`](../plans/historical/phase_2_5_retrieval_gate.md). |
| [`synthesis_eval_pack/`](synthesis_eval_pack/) | Phase 2.5 Track B (independent eval) | An independently-authored stress test of the synthesis runtime, written before reading the synthesis skill body. Four scenarios covering orphan firings, cap+adjust stacking, mixed missingness, and stale proposals. Verdict: GO for Phase 3. Gate doc: [`../plans/historical/phase_2_5_independent_eval.md`](../plans/historical/phase_2_5_independent_eval.md). |

Each subdirectory has its own `README.md` describing its scope and
its own `findings.md` with the verdict.

## Why these are kept

Three reasons:

1. **Decision history.** Future contributors asking "why is nutrition
   macros-only?" or "why is synthesis a single skill?" can read the
   experiment that closed those questions.
2. **Reproducibility.** Each prototype is self-contained — the
   scenarios, the runner, and the captured outputs are all here. The
   verdict can be re-checked.
3. **Honesty about scope.** The retrieval prototype in particular
   is a record that meal-level nutrition was tested and rejected,
   not silently dropped.

## Why these are not promoted

The runtime equivalents now live elsewhere:

- The synthesis prototype's `xrules.py` was superseded by
  [`../../src/health_agent_infra/core/synthesis_policy.py`](../../src/health_agent_infra/core/synthesis_policy.py)
  with ten X-rules across two phases.
- The synthesis prototype's `skill_synthesis.md` was superseded by
  the packaged
  [`../../src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md`](../../src/health_agent_infra/skills/daily-plan-synthesis/SKILL.md).
- The independent eval pack's `runner.py` was superseded by the
  packaged eval runner at
  [`../../src/health_agent_infra/evals/`](../../src/health_agent_infra/evals/),
  invoked via `hai eval run`.

Do not extend or modify these prototypes. If a question they
addressed needs to be reopened, write a new experiment under a new
subdirectory, do not edit these.
