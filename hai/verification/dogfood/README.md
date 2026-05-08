# Dogfood persona harness

Permanent regression infrastructure introduced in v0.1.10. Each
persona under `personas/` is a synthetic user shape; the runner
drives every persona through the full `hai pull → clean → daily →
today → explain` pipeline against an isolated state DB and captures
structured findings.

## Why this exists

The maintainer's daily-driver flow is one user shape. Single-user
dogfood cannot find bugs that depend on different age, sex, body
composition, training pattern, history length, or data source. The
persona matrix probes those axes deliberately.

See `reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md` § 4 for the matrix
and § 5 for the harness design.

## How to run

```bash
# Run the full matrix into a temp directory
uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run

# Result files
ls /tmp/hai_dogfood_run/
# → p1_dom_baseline/result.json, p2_female_marathoner/result.json, ...
# → summary.json (cross-persona aggregation)
```

## Isolation discipline

- Each persona uses `/tmp/hai_dogfood_run/<persona_id>/state.db`
  for state and `/tmp/hai_dogfood_run/<persona_id>/intake_root/`
  for intake JSONL files.
- Every subprocess invocation of `hai` sets `HAI_STATE_DB` and
  `HAI_BASE_DIR` explicitly. The harness never reads or writes the
  maintainer's real state DB.
- `pytest` integration is deliberately limited — the full matrix
  takes ~minutes to run and is not part of `verification/tests/`
  CI. Smoke tests that import the runner without invoking it can
  live there if desired.

## Adding a persona

1. Create `personas/p<N>_<slug>.py` exporting a single
   `SPEC: PersonaSpec` constant.
2. Import it in `personas/__init__.py` and add to `ALL_PERSONAS`.
3. Re-run `python -m verification.dogfood.runner` and inspect the
   new persona's `result.json`.

A new persona should stress an axis the existing matrix does not
cover — e.g., a different sport mix, an extreme training-load
regime, a specific data-source combination.

## What "findings" means

The runner compares actual pipeline output against expectations
encoded in the persona spec. A finding is a deviation — a setup
failure, a pipeline crash, a missing domain, a band miscalibration,
or an action-mismatch (e.g., day-1 fresh install producing a
high-confidence "proceed").

Findings are not fixes. They are inputs to the v0.1.10 audit
findings doc + PLAN.md cycle.

## Exclusions

This harness does not cover:

- Clinical edge cases (out of scope per project invariants).
- Adolescent (<18) or elderly (>55) users.
- Pregnancy, chronic disease, rehab.
- Multi-tenant or concurrent-user scenarios.

Expanding the user-set above is a v0.2-class scope change and
requires new persona archetypes plus reviewer judgement.
