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

Each row carries `contract_arm` (`told` default | `untold`) and a `cell`
label (`A`/`B`/`C`/`D`/`sanity_floor`) derived from `contract_arm` x
`runtime_mode`, so a row can be placed in the specify-vs-enforce 2x2
(PAPER.md "Experimental Design").

`cell_contrasts.py` consumes the same run directory and writes
`cell_contrasts.json`: per mechanism (M4-M8) a `base` 2x2 giving the A/B/C/D
cell medians of that mechanism's load-bearing metric(s) and the informative
contrasts `B - D` (effect of telling), `C - D` (effect of enforcing), and
`A - B` (marginal value of enforcement given told -- the redundancy
headline). The base 2x2 uses ONLY the canonical `<mechanism>_told/untold`
pair, holding moderators fixed; variant tasks are broken out (same
cell/contrast structure) so the headline is not averaged over them:
`moderators.goal_conflict` (benign completion pressure, told-arm A/B),
`moderators.blind` (constraint-verifiability manipulation, told-arm A/B), and
`conditions.drift` (stale-manifest, told-arm A/B). Classification is by task
tag (`goal_conflict`, `blind_observation`, `drift`/`stale_manifest`).
Every contrast is reported for two windows: `first_attempt` (the leading
trajectory window up to and including the first runtime enforcement
contact -- the first non-`OK` observation `exit_code`) and `converged`
(the full trajectory). First-attempt scoring is required for axis
attribution because a runtime block informs the untold agent late, so
cell C converges toward cell B after first contact. `no_runtime_enforcement`
reps are tracked as the sanity floor, outside the 2x2.

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
