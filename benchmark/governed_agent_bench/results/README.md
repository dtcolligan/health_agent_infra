# Results

Result utilities convert generated trajectory and score artifacts into
paper-facing evidence tables. They do not run models and do not interpret
claims; they normalize committed or regenerated benchmark outputs so later
paper packets can cite reproducible rows.

`run_layout.py` is the shared run-directory reader (readiness SF-1). It
detects and loads BOTH scored-run layouts:

- flat (rule baseline / offline repro): `scores/*.score.json` +
  `trajectories/<trajectory_id>.json`, observation artifacts relative to
  `trajectories/`;
- nested (paid pilot): `conditions/<system_id>/runtime_mode_<mode>/tasks/
  <task_id>/rep_XX.{trajectory,score,ledger}.json` + `rep_XX.done`
  completion sentinels, observation artifacts relative to each rep's task
  directory.

Every rep record carries its own `observation_root`, because first-attempt
re-scoring against the wrong root silently scores against zero observations.

`evidence_tables.py` consumes either layout via the shared reader and
writes:

- `evidence_table.json`
- `evidence_table.csv`

Each row carries `contract_arm` (`told` default | `untold`) and a `cell`
label (`A`/`B`/`C`/`D`/`sanity_floor`) derived from `contract_arm` x
`runtime_mode`, so a row can be placed in the specify-vs-enforce 2x2
(PAPER.md "Experimental Design").

`cell_contrasts.py` consumes either layout and writes `cell_contrasts.json`
(schema v2). Reps are grouped PER SYSTEM (`systems.<system_id>`; a pooled
`pooled_all_systems` block is reference-only) so a below-floor control model
cannot contaminate the capable-model cells. Per mechanism (M4-M8) a `base`
2x2 gives pooled pass counts per cell -- `{"passes", "n", "rate_pct",
"values", "median"}`, where a rep passes iff its metric value meets the
frozen scorer threshold in the metric's direction -- and the informative
contrasts `B - D` (effect of telling), `C - D` (effect of enforcing), and
`A - B` (marginal value of enforcement given told -- the redundancy
headline) as percentage-point differences of pass rates; medians and
`median_contrasts` are clearly-secondary fields. The base 2x2 uses ONLY the
canonical `<mechanism>_told/untold` pair, holding moderators fixed; variant
tasks are broken out (same cell/contrast structure) so the headline is not
averaged over them: `moderators.goal_conflict` (benign completion pressure,
told-arm A/B), `moderators.blind` (constraint-verifiability manipulation,
told-arm A/B), and `conditions.drift` (stale-manifest, told-arm A/B).
Classification is by task tag (`goal_conflict`, `blind_observation`,
`drift`/`stale_manifest`).

Every contrast is reported for two windows: `first_attempt` and `converged`
(the full trajectory). The first-attempt window ends at (and includes) the
first GENUINE enforcement contact: the first non-`OK` observation whose
immediately preceding command is one of the task's
`expected_behavior.must_not_call` commands. The model's own unrelated errors
do not close the window, and tasks without `must_not_call` never close it
(their USER_INPUT observations are the task stimulus, not enforcement).
First-attempt scoring is required for axis attribution because a runtime
block informs the untold agent late, so cell C converges toward cell B after
first contact. `no_runtime_enforcement` reps are tracked as the sanity
floor, outside the 2x2.

`figures.py` consumes `evidence_table.json` and writes deterministic SVG
summary figures plus `figures_manifest.json`.

`error_taxonomy.py` consumes `evidence_table.json` and writes violation
counts by task level, runtime mode, model class, task mechanism, and
runtime mechanism.

`pilot_evidence.py` consumes an A2 pilot run directory under
`runs/pilot/<run>/` (nested layout, via the shared reader) and writes:

- `pilot_evidence_table.json`
- `pilot_evidence_table.csv`
- `pilot_mechanism_coverage.json`

The coverage summary is bookkeeping only (eligible row counts, pooled pass
counts, pass-rate deltas, full-contract critical-violation surfacing, sanity
floor). The former pre-registered 5pp H1 verdict machinery was deleted
(locked decision 3); the paper's quantities are the cell contrasts above.
