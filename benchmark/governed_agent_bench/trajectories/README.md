# Hand-Authored Trajectories

This directory contains deterministic seed trajectories used to validate the
GovernedAgentBench scorer before any model-backed baseline is run.

`hand_authored/*_pass.json` records the intended operator behavior for a task.
`hand_authored/*_fail.json` records a nearby failure shape that should score
as non-passing. These artifacts are not model results and must not be reported
as baseline performance.

`adversarial/*.json` records targeted attack-shape canaries for the
pilot-phase adversarial layer. These are static scorer fixtures, not live
runtime probes and not model-backed trajectories.
