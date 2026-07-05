# Offline Reproducibility

The offline reproducibility path rebuilds synthetic fixtures and runs
the deterministic sharp pipeline: `rule_baseline` ablation -> evidence
tables -> figures -> error taxonomy. It does not call local models,
cloud models, paid APIs, live wearable sources, or private health data,
and it requires no network access.

Run:

```bash
PYTHONPATH=benchmark uv run python \
  benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

The command writes:

- `rule_baseline_ablation/` trajectories, scores, and
  `rule_baseline_ablation_summary.json`;
- `evidence_tables/evidence_table.json`;
- `evidence_tables/evidence_table.csv`;
- `figures/*.svg`;
- `figures/figures_manifest.json`;
- `error_taxonomy/error_taxonomy.json`;
- `offline_repro_manifest.json`, whose `artifacts` block carries
  path-only entries keyed `rule_baseline_ablation_summary`,
  `evidence_table_json`, `evidence_table_csv`, `figures_manifest`, and
  `error_taxonomy`, plus top-level `row_count`, `figure_count`,
  `violation_count`, and `runtime_modes`.

Without `--task-id`, the command runs the full committed 16-task
preprint inventory (operate floor + per-mechanism told/untold +
goal-conflict + blind + drift) across each task's declared runtime
modes, producing 72 cells (offline rule baseline runs each cell once). Repeating `--task-id`
narrows the ablation to the named subset.

## Prerequisites

- `uv` (minimum version observed working: `uv 0.11.2`).
- Python >=3.11 (observed `python3` version: Python 3.14.0).
- Approximate output-dir size: 4.1M for a full offline run.
- macOS or Linux. No Windows support claim.
- No network access required. No private health data required. No
  paid APIs.

## Expected runtime

Observed 43 seconds on Apple M2 (Darwin 23.4.0, arm64). This is
descriptive, not a portability guarantee. Expect 2-3x variance on
other hardware and a 1.5-2x first-run cache penalty while uv builds
its cache.

## Reproducibility scope

The offline reproducer's outputs split into two classes:

**Pinned by golden-fingerprint test** (scoring pipeline):
- evidence_tables/evidence_table.{json,csv}
- error_taxonomy/error_taxonomy.json
- figures/figures_manifest.json

These artifacts are byte-stable across runs (after absolute-path
normalization). They are the load-bearing outputs the paper cites.
Drift on any one of them is a research-integrity signal.

**Not pinned** (transient artifacts):
- fixtures/*/state.db -- native SQLite non-determinism (page
  allocation, free-list ordering).
- fixtures/*/fixture_metadata.json, fixtures/*/base/*.jsonl --
  fixture builders embed submission_id and submitted_at.
- rule_baseline_ablation/trajectories/** -- trajectory filenames
  embed random hashes; observation stdouts contain HAI runtime
  timestamps.
- figures/*.svg -- rendered plots; the pinned surface is
  figures/figures_manifest.json, not the SVG bytes.
- offline_repro_manifest.json -- contains absolute output_dir; the
  load-bearing contents are also captured in scoring artifacts.

The test does not validate these. They vary across runs by design.

## Golden fingerprint check

`REPRODUCIBILITY_GOLDEN.json` carries SHA-256 fingerprints of the
pinned files. `test_reproducibility_golden.py` strict-fails on
mismatch. A legitimate refresh is: re-run the reproducer, copy new
fingerprints from the test failure output into the golden file, and
commit the refresh alongside the change that justified it.

For a small smoke run, repeat `--task-id`:

```bash
PYTHONPATH=benchmark uv run python \
  benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro_smoke \
  --task-id gab_l1_operate_read \
  --task-id gab_l2_validation_told
```

The command exits 0 when the ablation produced scored rows and
figures (`row_count >= 1` and `figure_count >= 1`); it writes
`offline_repro_manifest.json` and exits 1 otherwise.

Model-backed reproducibility is intentionally absent until Dom approves
`WP-MODEL-ROSTER-001`.
