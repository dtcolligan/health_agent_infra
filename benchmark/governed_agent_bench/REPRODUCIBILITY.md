# Offline Reproducibility

The offline reproducibility path rebuilds synthetic fixtures and runs
the deterministic `rule_baseline` ablation, static oracle-pair
isolation matrix, local hermetic HAI live-isolation probes, evidence
tables, figures, error taxonomy, and targeted adversarial summary
tables. It does not call local models, cloud models, paid APIs, live
wearable sources, or private health data.

Run:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro
```

The command writes:

- `rule_baseline_ablation/` trajectories, observations, scores, and
  `rule_baseline_ablation_summary.json`;
- `evidence_tables/evidence_table.json`;
- `evidence_tables/evidence_table.csv`;
- `figures/*.svg`;
- `figures/figures_manifest.json`;
- `error_taxonomy/error_taxonomy.json`;
- `isolation_matrix/isolation_matrix.json`;
- `live_isolation/live_isolation_matrix.json`;
- `adversarial_summary/adversarial_summary_aggregated.json`;
- `adversarial_summary/adversarial_summary_aggregated.csv`;
- `adversarial_summary/adversarial_summary_per_trajectory.json`;
- `adversarial_summary/adversarial_summary_per_trajectory.csv`;
- `offline_repro_manifest.json`, including top-level
  `isolation_matrix`, `live_isolation`, and `adversarial_summary`
  metadata plus path-only artifact entries.

Without `--task-id`, the command runs the full committed 28-task
preprint inventory across each task's declared runtime modes.
Repeating `--task-id` narrows the rule-baseline portion only; the
static isolation matrix still runs its full hand-authored oracle-pair
set, and the live isolation matrix still runs its full M4-M8 probe set.

## Prerequisites

- `uv` (minimum version observed working: `uv 0.11.2`).
- Python >=3.11 (observed `python3` version: Python 3.14.0).
- Approximate output-dir size: 11M for a full offline run.
- macOS or Linux. No Windows support claim.
- No network access required. No private health data required. No
  paid APIs.

## Expected runtime

Observed 76 seconds on Apple M2 (Darwin 23.4.0, arm64). This is
descriptive, not a portability guarantee. Expect 2-3x variance on
other hardware and a 1.5-2x first-run cache penalty while uv builds
its cache.

## Reproducibility scope

The offline reproducer's outputs split into two classes:

**Pinned by golden-fingerprint test** (scoring pipeline):
- evidence_tables/evidence_table.{json,csv}
- error_taxonomy/error_taxonomy.json
- figures/figures_manifest.json
- isolation_matrix/isolation_matrix.json
- adversarial_summary/adversarial_summary_{aggregated,per_trajectory}.{json,csv}

These artifacts are byte-stable across runs (after absolute-path
normalization). They are the load-bearing outputs paper §§5-7 cite.
Drift on any one of them is a research-integrity signal.

**Not pinned** (transient artifacts):
- fixtures/*/state.db -- native SQLite non-determinism (page
  allocation, free-list ordering).
- fixtures/*/fixture_metadata.json, fixtures/*/base/*.jsonl --
  fixture builders embed submission_id and submitted_at.
- rule_baseline_ablation/trajectories/** -- trajectory filenames
  embed random hashes; observation stdouts contain HAI runtime
  timestamps.
- live_isolation/** -- live trajectory IDs and observation refs are
  run-specific by construction. Live tier is mechanism evidence per
  PAPER.md D-22, not byte-reproducible artifact.
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
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro_smoke \
  --task-id gab_l1_doctor_status_route \
  --task-id gab_l2_empty_today_user_input
```

Use `--skip-live-isolation` for a fast path or CI job that should omit
the local hermetic HAI probes. Static isolation still runs; the manifest
sets `live_isolation` to `{"skipped": true, "reason": "skip_flag"}` and
omits `artifacts.live_isolation_matrix`.

The CLI writes `offline_repro_manifest.json` even when an isolation tier
reports non-isolation, then exits 1.

Model-backed reproducibility is intentionally absent until Dom approves
`WP-MODEL-ROSTER-001`.
