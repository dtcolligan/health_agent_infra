# Scorer

The scorer should first support offline grading of recorded
trajectories. It should not require model calls, network access, or
private health rows.

Planned stages:

1. Validate task / trajectory / score JSON against schemas.
2. Score command validity and hallucinated-command rate against the
   frozen manifest.
3. Score command-sequence correctness against each task's expected
   behavior.
4. Score violation classes: unsafe mutation, direct state write,
   clinical claim, unsupported narration, refusal error, and drift
   failure.
