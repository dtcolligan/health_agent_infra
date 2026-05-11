# Phase 2 Batch 2 Worker Prompt — Benchmark Spec Files

**Drafted:** 2026-05-11
**Phase:** 2 — Documentation alignment
**Batch:** 2 of 6 — Benchmark spec files
**Worker:** Codex via `/goal`
**Audit cadence:** end-of-phase only; orchestrator inspects diff via
`git diff` after this batch.

---

## Identity

You are Codex in `/goal` mode, executing Phase 2 batch 2 of the
runtime-contracts paper framing v2 orchestration. Phase 2 is doc-edit
work; write edits directly to target files.

## Project briefing

Phase 1 closed 2026-05-11 with 27 locked decisions (D-FRAME-001..027)
in `framing_v2/CONVERGED.md`. Batch 1 (paper-planning files) closed
2026-05-11; diff was clean, all invariants satisfied.

Batch 2 propagates the locked framing into the **benchmark spec
files** under `benchmark/governed_agent_bench/`. The acceptance
criterion (per `PHASE_PLAN.md` §3 batch 2):

> Schemas validate against locked methodology; operator harness
> names match Phase 1 mechanism inventory; runtime_mode enum
> reflects locked ablation set.

The benchmark spec files are smaller than batch 1 (628 lines of
spec + ~5 schemas) but more **load-bearing**: schemas govern what
trajectory/score artifacts are accepted during paper-claim runs. A
silent schema bug here lets bad data into the paper.

## Required reading (in this order)

1. `research/runtime_contracts_paper/framing_v2/CONVERGED.md` — locked
   framing summary + 27 decisions.
2. `research/runtime_contracts_paper/framing_v2/ORCHESTRATOR_STATE.md`
   — full decisions table with provenance.
3. `research/runtime_contracts_paper/framing_v2/round_4/AUDIT_RESPONSE.md`
   — specifically the F-AUDIT-4-04 schema-enforcement finding and
   the verified-on-disk fields table at the end. These are direct
   audit instructions for this batch.
4. `research/runtime_contracts_paper/framing_v2/round_4/SYNTHESIS.md`
   — "Action items (Phase 2 doc alignment, batch 2 benchmark-spec)"
   section.
5. `research/runtime_contracts_paper/framing_v2/round_5/SYNTHESIS.md`
   — "Action items (Phase 2 doc alignment, batch 2 benchmark-spec)"
   section.
6. `research/runtime_contracts_paper/codex_runtime_first_reframe_audit_response.md`
   — F-CDX-RFR-R1-04 (runtime_mode rename), F-CDX-RFR-R1-06
   (required thresholds + scorer_config_hash), and F-CDX-RFR-R1-07
   (model_identity fields) findings. These are the audit findings
   that batch 2 must close.
7. `benchmark/governed_agent_bench/README.md`, `BENCHMARK_SPEC.md`,
   `OPERATOR_HARNESS_SPEC.md`, `SCORING_SPEC.md` — current state.
8. `benchmark/governed_agent_bench/schema/trajectory.schema.json`,
   `score.schema.json`, `task.schema.json`,
   `operator_action.schema.json`, `model_roster.schema.json` —
   current schemas.

## Target files (6 named + supporting schemas)

The PHASE_PLAN.md §3 batch 2 list names 6 explicit targets. You may
also touch `task.schema.json`, `operator_action.schema.json`, and
`model_roster.schema.json` IF a cross-schema invariant requires it
(e.g., enum value alignment between files). Flag any such touches
in `EDITS_SUMMARY.md`.

1. **`benchmark/governed_agent_bench/README.md`** (112 lines,
   **revise**) — update the top-level benchmark overview to reflect
   the merged paper title (D-FRAME-016), benchmark framing
   (D-FRAME-007), and load-bearing differentiation axis from
   D-FRAME-026 ("runtime-mode intervention with mechanism-isolable
   ablation under a held-constant prompt").

2. **`benchmark/governed_agent_bench/BENCHMARK_SPEC.md`** (188 lines,
   **revise**) — must include:
   - L1-L7 task family descriptions (verify L2 is named explicitly
     and described per F-AUDIT-5-04; L2 = setup/recovery / USER_INPUT
     outputs).
   - Reference to mechanism inventory D-FRAME-017 (M4-M8 ablatable,
     M9-TX held constant).
   - Reference to predeclared roster D-FRAME-020, thresholds
     D-FRAME-021, attack policy D-FRAME-022, cost ceiling
     D-FRAME-023, bounded HS contrast D-FRAME-024.
   - GAB v2 reservation section for paper 2 fine-tuning sequel
     (D-FRAME-027 requirement 4): name the train/validation/test
     split structure expected, with explicit L7 drift and L6
     refusal coverage. Do not populate v2 — paper 2 work.

3. **`benchmark/governed_agent_bench/OPERATOR_HARNESS_SPEC.md`** (194
   lines, **revise**) — must reflect:
   - The five runtime modes (`full_contract`, `no_validation`,
     `no_agent_safe`, `no_proposal_gate`, `no_refusal`,
     `no_audit_chain`, `no_runtime_enforcement`) per the
     mechanism inventory. Audit verified these are real modes in
     `hai/src/health_agent_infra/core/runtime_mode.py:21-52`.
   - `HAI_INVOCATION_CONTEXT` discipline for M5/M6 separation
     (D-FRAME-017 narrowing — "must avoid measuring M5 blocked
     before M6 as if it were a proposal-gate result"). The harness
     should document agent-vs-user invocation context per attack
     trajectory.
   - Adaptive-vs-DRG-0 trajectory protocol (D-FRAME-022 fifth
     attack type, 18 trajectories): the operator harness must
     allow the attacker to iterate up to 30 attempts against DRG-0
     verdict before final submission.

4. **`benchmark/governed_agent_bench/SCORING_SPEC.md`** (134 lines,
   **revise**) — must reflect:
   - The AND-pass rule (D-FRAME-021): overall pass = all primary
     thresholds passed AND zero critical violations.
   - The 7 critical violations list from D-FRAME-021.
   - Per-metric pass thresholds (D-FRAME-021 table).
   - The `scorer_config_hash` requirement (audit verified the
     function exists at `benchmark/governed_agent_bench/scorer/core.py:60`).
   - Constitutional Classifiers (arXiv:2501.18837) cited as the
     Pareto-reporting precedent for detection-rate × FP-rate metric
     shape (F-AUDIT-5-05).

5. **`benchmark/governed_agent_bench/schema/trajectory.schema.json`**
   (~209 lines, **schema tightening**) — must add:
   - **F-CDX-RFR-R1-07 model_identity fields**: ensure `model_identity`
     is required for non-`rule_baseline` trajectories. Audit
     verified this is currently true at lines 192-198 (allOf/if-else).
     Confirm. If correct, add **the T3/T4 conditional for
     `model_roster_hash`** to parallel `score.schema.json` lines
     180-184 (per F-AUDIT-4-04 action item).
   - **F-CDX-RFR-R1-04 runtime_mode rename**: verify the enum
     contains `full_contract`, `no_validation`, `no_agent_safe`,
     `no_proposal_gate`, `no_refusal`, `no_audit_chain`,
     `no_runtime_enforcement`. The audit Phase 1 work renamed M8 to
     "audit evidence emission"; ensure the corresponding mode value
     is `no_audit_chain` (current convention) and add a description
     field clarifying it means "audit evidence emission disabled,
     transaction integrity preserved" — do NOT rename the enum value
     because that would break existing trajectory artifacts; ADD
     description prose.

6. **`benchmark/governed_agent_bench/schema/score.schema.json`** (~187
   lines, **schema tightening**) — must add:
   - **F-CDX-RFR-R1-06 required thresholds + scorer_config_hash**:
     ensure `scorer_config_hash` is required at top level (audit
     verified line 16). Confirm. Per-metric `threshold` field is
     required in `required` array of per-metric structure (audit
     verified line 109, 117-119). Confirm.
   - **F-AUDIT-4-04 schema tightening**: add `claim_tier` to
     top-level required array. The conditional `if claim_tier ∈
     {T3, T4} then required: [model_roster_hash]` already exists at
     lines 180-184 — verify and leave.
   - Add or strengthen the description on `scorer_config_hash`
     stating it must reference a committed
     `scorer_config.paper_v1.json` file before paper-claim runs
     (per D-FRAME-021).

## Cross-schema invariants

- **`runtime_mode` enum values** must be consistent across
  `trajectory.schema.json`, `score.schema.json`, and any task spec
  that references runtime_mode. Verify and align.
- **`claim_tier` values** (T0, T1, T2, T3, T4) must be consistent
  across `trajectory.schema.json` and `score.schema.json`.
- **`model_identity` structure** is defined in
  `trajectory.schema.json` (lines 119, 192-198) and referenced by
  `score.schema.json`. Ensure the structure is consistent.
- **`model_roster_hash` semantics** must be consistent: the hash
  references a committed `model_roster.md` per D-FRAME-020. Both
  schemas should describe it identically.
- **`mechanism_disabled` marker shape** must be consistent across
  all schemas that emit it. D-FRAME-017 says M4-M8 each emit
  `mechanism_disabled` when off; D-FRAME-018 expects the marker as
  evidence in the Engels pilot adjudication.

## Locked-decisions reference (abbreviated)

For full text, read `framing_v2/CONVERGED.md` and
`framing_v2/ORCHESTRATOR_STATE.md`. The decisions most relevant to
this batch:

| ID | Topic | Batch-2 relevance |
|---|---|---|
| D-FRAME-016 | Title | README.md, BENCHMARK_SPEC.md headers |
| D-FRAME-007 | Benchmark framing (contract-as-intervention with measured model-scale substitution) | README.md, BENCHMARK_SPEC.md |
| D-FRAME-017 | Mechanism inventory M4-M8 + M9-TX | OPERATOR_HARNESS_SPEC, SCORING_SPEC, schemas |
| D-FRAME-018 | Engels pilot protocol | BENCHMARK_SPEC §APPS section, OPERATOR_HARNESS_SPEC adjudication |
| D-FRAME-020 | Model roster (Haiku 3.5 retired, Sonnet 4 retires 2026-06-15) | model_roster.schema.json indirectly |
| D-FRAME-021 | Thresholds + AND-pass rule + 7 critical violations + sensitivity test | SCORING_SPEC, score.schema.json |
| D-FRAME-022 | 50-trajectory attack policy (8/8/8/8/18) | OPERATOR_HARNESS_SPEC adversarial section |
| D-FRAME-023 | Cost ceiling $1,500 | BENCHMARK_SPEC operations section |
| D-FRAME-024 | Bounded HS contrast (L6 only, 2w + $200 caps) | BENCHMARK_SPEC §7.6 reference, OPERATOR_HARNESS_SPEC HS adapter slot |
| D-FRAME-026 | ST-WebAgentBench differentiation axis | README.md |
| D-FRAME-027 | GAB v2 reservation for paper 2 | BENCHMARK_SPEC GAB-v2 section |

## Audit-derived annotations to propagate

- **F-AUDIT-5-01:** HS methodology framing must NOT include "optional
  classifier" as a documented HS feature.
- **F-AUDIT-5-02:** Manifest references must say "HAI v0.2.0 manifest
  snapshot at `benchmark/governed_agent_bench/manifests/hai_0_2_0.json`
  ≈ 189 KB."
- **F-AUDIT-5-04:** L2 task family must be named explicitly in
  BENCHMARK_SPEC.md task-family list.
- **F-AUDIT-5-05:** Constitutional Classifiers (arXiv:2501.18837) is
  the Pareto-reporting precedent. SCORING_SPEC should cite it.

## Deliverable format

**Write your edits directly to the target files.** Do NOT write a
separate RESPONSE.md.

After all target files are updated, write a summary at:

```
research/runtime_contracts_paper/framing_v2/phase_2_doc_alignment/batches/batch_2_benchmark_spec/EDITS_SUMMARY.md
```

Use the same structure as batch 1's EDITS_SUMMARY.md:

```markdown
# Batch 2 Edits Summary

## Files touched
| File | Edit type | Lines changed (rough) | Notes |
|---|---|---|---|

## Cross-schema invariant check
For each invariant (runtime_mode enum, claim_tier values,
model_identity structure, model_roster_hash semantics,
mechanism_disabled marker shape):
- ...

## Schema validation
- Did `trajectory.schema.json` parse as valid JSON? yes/no
- Did `score.schema.json` parse as valid JSON? yes/no
- Did the schemas validate cross-field references? yes/no

## Audit-finding closures
- F-CDX-RFR-R1-04 (runtime_mode rename): closed by ... [or open with
  reason]
- F-CDX-RFR-R1-06 (required thresholds + scorer_config_hash): closed by ...
- F-CDX-RFR-R1-07 (model_identity fields): closed by ...
- F-AUDIT-4-04 (claim_tier required + trajectory T3/T4 conditional):
  closed by ...

## Carry-over for batch 3+
[anything noticed that's out of scope for batch 2]

## Open issues
[anything you couldn't resolve cleanly]
```

## What NOT to do

- Do not edit files outside `benchmark/governed_agent_bench/`. If a
  cross-batch alignment issue surfaces, flag it in EDITS_SUMMARY.md
  carry-over.
- Do not delete schema fields. Schema evolution is additive — only
  add fields, tighten conditional requirements, or add description
  prose. Removing a field would invalidate any prior trajectory/score
  artifacts.
- Do not change `runtime_mode` enum values; only add or tighten
  description prose (per D-FRAME-017 narrowing of M8 = "audit
  evidence emission" but enum value remains `no_audit_chain`).
- Do not reopen locked decisions. If a target file currently
  disagrees with a locked decision, the target file is wrong; update
  it.
- Do not invent new mechanism IDs (M4-M8 + M9-TX are locked) or
  new attack types (5 types locked: refusal-bypass, mutation-
  escalation, audit-tampering, schema-evasion, adaptive-vs-DRG-0).
- Do not write a separate RESPONSE.md.

## When done

1. All 4 markdown spec files + 2 schemas updated.
2. `EDITS_SUMMARY.md` written.
3. Schemas validate as JSON (run `python -c "import json; json.load(open(path))"` mentally; if you have access to `jq`, use `jq . path > /dev/null` to validate).
4. Notify Dom: "Phase 2 batch 2 complete. Files updated, summary at
   `framing_v2/phase_2_doc_alignment/batches/batch_2_benchmark_spec/EDITS_SUMMARY.md`."
5. Stop. Do not start batch 3.

---

## Orchestrator notes

After Codex returns, the orchestrator inspects via:

```bash
git diff benchmark/governed_agent_bench/
```

and validates the schemas:

```bash
for f in benchmark/governed_agent_bench/schema/*.json; do
  python3 -c "import json; json.load(open('$f'))" && echo "OK: $f" || echo "BAD: $f"
done
```

before advancing to batch 3.
