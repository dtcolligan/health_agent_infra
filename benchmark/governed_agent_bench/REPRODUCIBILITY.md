# Offline Reproducibility

The offline reproducibility path rebuilds only synthetic fixtures and
runs only the deterministic `rule_baseline` pipeline. It does not call
local models, cloud models, paid APIs, live wearable sources, or private
health data.

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
- `offline_repro_manifest.json`.

Without `--task-id`, the command runs the full committed 28-task
preprint inventory across each task's declared runtime modes.

For a small smoke run, repeat `--task-id`:

```bash
uv run python benchmark/governed_agent_bench/reproduce_offline.py \
  --output-dir /tmp/gab_offline_repro_smoke \
  --task-id gab_l1_doctor_status_route \
  --task-id gab_l2_empty_today_user_input
```

Model-backed reproducibility is intentionally absent until Dom approves
`WP-MODEL-ROSTER-001`.
