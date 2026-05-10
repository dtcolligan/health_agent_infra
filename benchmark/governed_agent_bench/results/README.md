# Results

Result utilities convert generated trajectory and score artifacts into
paper-facing evidence tables. They do not run models and do not interpret
claims; they normalize committed or regenerated benchmark outputs so later
paper packets can cite reproducible rows.

`evidence_tables.py` expects a run directory with:

- `scores/*.score.json`
- `trajectories/*.json`

It writes:

- `evidence_table.json`
- `evidence_table.csv`

`figures.py` consumes `evidence_table.json` and writes deterministic SVG
summary figures plus `figures_manifest.json`.
