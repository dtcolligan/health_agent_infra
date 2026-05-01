# Calibration eval design (v0.1.14 W-AL)

**Status.** v0.1.14 W-AL — schema/report shape only. Correlation
work is **deferred to v0.5+** per
`reporting/plans/future_strategy_2026-04-29/reconciliation.md` A2.
**Origin.** FActScore (Min et al. 2023) atomic-claim decomposition
for factuality scoring; MedHallu (Pandit et al. 2024) clinical-text
adaptation. v0.2.0 W58D consumes this schema for the deterministic
claim block; v0.2.2 W58J consumes it for the LLM-judge harness.

## What v0.1.14 ships

- `core/eval/calibration_schema.py` — `AtomicClaim`,
  `CalibrationReport`, `decompose_into_atomic_claims` stub,
  `validate_calibration_report`.
- `core/eval/judge_harness.py` — `JudgeHarness` ABC, `JudgeRequest`,
  `JudgeResponse`, `NoOpJudge` reference impl (W-AJ scaffold).
- Test pin (`test_judge_harness.py`) for the invocation interface
  and the schema contract.

## What v0.1.14 does NOT ship

- Semantic decomposition (handles compound sentences, anaphora,
  unit-bearing numerics). v0.2.0 **W-FACT-ATOM** owns this; folds
  into W58D.
- Live LLM-judge model invocation. v0.2.2 **W58J** plugs in the
  model.
- Bias panel (CALM-style). v0.2.2 **W-JUDGE-BIAS** owns this;
  folds into W58J.
- Correlation between calibrated factuality scores and outcomes.
  Deferred to **v0.5+** (the calibration substrate proper).
- Coverage metrics, agreement-with-human-annotator scoring,
  Brier/log-loss tooling. Out of scope until v0.5+.

## Schema

`CalibrationReport`:

```jsonc
{
    "schema_version": "calibration_report.v1",
    "prose_id":       "weekly_2026-W17_user_local_1",
    "source_prose":   "<verbatim source text>",
    "atomic_claims": [
        {
            "claim_id":          "weekly_2026-W17_user_local_1_atom_000",
            "text":              "Resting HR was 67 bpm on 2026-04-30.",
            "span":              [0, 36],
            "evidence_locators": [
                {"table": "accepted_recovery_state_daily", ...}
            ]
        }
    ],
    "judge_verdicts":   [],
    "aggregate_score":  0.0
}
```

## FActScore + MedHallu vocabulary

Both papers landed in 2023-2024 as atomic-claim factuality scoring
benchmarks. Vocabulary HAI inherits:

- **Atomic claim** — a self-contained assertion that can be true or
  false independently. Every quantitative claim in weekly-review
  prose decomposes into one or more atomic claims.
- **Evidence retrieval** — the process of finding support rows for
  a claim. HAI's W-PROV-1 source-row locators are pre-computed
  evidence retrieval (the prose authors specify which rows
  support which claims at write time, not at score time).
- **Verdict** — one of `supported / unsupported / ambiguous /
  skipped`. v0.2.2 W58J's judge produces these per claim.
- **Aggregate score** — a single [0.0, 1.0] number summarising
  per-claim verdicts. v0.2.2 W58J shadow-mode logs aggregates;
  v0.2.3 promotes to a blocking gate at a configured threshold.

MedHallu's contribution: clinical-text-specific atomic-claim
patterns (e.g., "diagnosis", "dose", "test result") that extend
the general FActScore decomposition. HAI's local "no clinical
claims" invariant means MedHallu's exact patterns don't apply
verbatim, but the atomic-claim discipline is the same.

## How v0.1.14 stub decomposition works

`decompose_into_atomic_claims` splits prose on sentence boundaries
(`.`, `?`, `!`). Each sentence becomes one `AtomicClaim` with the
character span into the source prose. Locators are not attached
in v0.1.14 — that requires the smarter v0.2.0 W-FACT-ATOM extractor
that knows which numerics/dates anchor a claim to specific
evidence rows.

The stub is deterministic, dependency-free, and good enough for
the surrounding code to be written in v0.2.0 W52 (weekly-review
prose generation): the v0.2.0 PLAN can author callers against this
shape, and v0.2.0 W-FACT-ATOM swaps the decomposer without
breaking callers.

## Test surface

`verification/tests/test_judge_harness.py` pins:

1. `NoOpJudge` invocation interface (request → response shape).
2. `judge_batch` returns one response per request, preserving
   `claim_id`.
3. `JudgeResponse.bias_panel_results` exists (pre-allocated for
   v0.2.2 W-JUDGE-BIAS).
4. `decompose_into_atomic_claims` handles single, multiple,
   question-mark/exclamation, and empty inputs.
5. `validate_calibration_report` rejects unknown schema version /
   missing fields / malformed atomic claims.

## v0.2.0 W52 + W-FACT-ATOM consumption

When v0.2.0 W52 (weekly review) ships:

1. The weekly-review aggregator emits prose via
   `core/review/weekly.py` (v0.2.0).
2. Each prose passage is decomposed via
   `decompose_into_atomic_claims` (or v0.2.0 W-FACT-ATOM's
   replacement).
3. Each atomic claim gets evidence locators attached (the
   aggregator knows which rows fed which prose).
4. The deterministic claim block (W58D) verifies every
   quantitative claim has at least one locator; blocks on
   absence.
5. The claim list is stored as a `CalibrationReport`.

When v0.2.2 W58J ships:

1. The weekly-review pipeline invokes the LLM judge over the
   `CalibrationReport`.
2. The judge returns one `JudgeResponse` per atomic claim.
3. Verdicts populate `judge_verdicts` on the report.
4. `aggregate_score` is computed (v0.2.2 W58J defines the
   aggregation formula; CALM-style bias panel adjusts).
5. Shadow mode: log everything; don't block.
6. v0.2.3 promotes to blocking at a configured threshold.

## Why a stub instead of a real decomposer

The v0.1.14 cycle's effort budget (1.5 d on W-AL) doesn't admit a
proper FActScore-style decomposer. Pre-staging the schema is the
cheap way to unblock v0.2.0 PLAN authoring without committing to
implementation choices that v0.2.0 will need to revisit. Per
reconciliation A2, the right home for the calibration substrate
proper is v0.5+ when correlation work has a real outcome record
to correlate against.

## Why pre-staged in v0.1.14

W52 (v0.2.0) and W58 family (v0.2.0-v0.2.3) all reference this
shape. Designing the schema in v0.1.14 means v0.2.0's PLAN can be
written without reserving design risk for "what shape do we land
the calibration report in?". The cycles after v0.2.3 (which lands
W58J as a blocking gate) inherit a stable substrate.
