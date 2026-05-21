# Offline Reproducibility

The offline reproducibility path rebuilds synthetic fixtures and runs
the deterministic `rule_baseline` ablation, static oracle-pair
isolation matrix, local hermetic HAI live-isolation probes, evidence
tables, figures, and error taxonomy. It does not call local models,
cloud models, paid APIs, live wearable sources, or private health data.

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
- `offline_repro_manifest.json`, including top-level
  `isolation_matrix` and `live_isolation` metadata plus path-only
  artifact entries.

Without `--task-id`, the command runs the full committed 28-task
preprint inventory across each task's declared runtime modes.
Repeating `--task-id` narrows the rule-baseline portion only; the
static isolation matrix still runs its full hand-authored oracle-pair
set, and the live isolation matrix still runs its full M4-M8 probe set.

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
