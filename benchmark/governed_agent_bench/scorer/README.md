# Scorer

The scorer should first support offline grading of recorded
trajectories. It should not require model calls, network access, or
private health rows.

Current MVP:

- `core.py` scores hand-authored task/trajectory dictionaries fully
  offline.
- The deterministic score envelope records `scorer_version` and
  `scorer_config_hash`.
- Implemented checks cover command validity/order, hallucinated
  commands, unsafe command attempts, refusal accuracy, direct-state
  write attempts, and banned clinical phrases.

Planned next stages:

1. Validate task / trajectory / score JSON against schemas.
2. Expand command validity and hallucinated-command rate against the
   frozen manifest.
3. Score command-sequence correctness against each task's expected
   behavior.
4. Score violation classes: unsafe mutation, direct state write,
   clinical claim, unsupported narration, refusal error, and drift
   failure.
