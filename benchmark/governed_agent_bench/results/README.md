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

`error_taxonomy.py` consumes `evidence_table.json` and writes violation
counts by task level, runtime mode, model class, task mechanism, and
runtime mechanism.

`pilot_evidence.py` consumes an A2 pilot run directory under
`runs/pilot/<run>/` and writes:

- `pilot_evidence_table.json`
- `pilot_evidence_table.csv`
- `pilot_h1_mechanism_summary.json`
- `dr9_switch_decision.json`

`dr9_switch.py` can also be run directly against
`pilot_h1_mechanism_summary.json` plus the optional pilot evidence table. It
is an offline evaluator and never invokes a model provider.

`adversarial_summary.py` writes generated adversarial summary JSON/CSV
artifacts during `reproduce_offline.py`; those generated files are not §14
lock-hash inputs.
