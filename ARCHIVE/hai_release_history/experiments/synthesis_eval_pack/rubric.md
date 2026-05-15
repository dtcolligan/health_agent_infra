# Synthesis eval pack — rubric

Same 3-point rubric as Phase 0.5, sharpened for these scenarios.

## Per-scenario scoring

Each scenario gets three scores (0 / 1 / 2 / 3), plus a pass/fail
summary. The acceptance bar for the eval pack is **action_correctness
≥ 2/3 on at least 3 of the 4 scenarios**.

### 1. Action correctness (0–3)

- **3**: All `pass_criteria` for the scenario are met. Invariant held.
- **2**: Most pass_criteria met; one non-critical slip (e.g., tag
  present but phrased differently than expected).
- **1**: Partial — invariant is materially breached on one key
  pass_criterion (e.g., firing silently dropped, or cap not applied).
- **0**: Invariant fully breached or the path crashes.

### 2. Rationale quality (0–3)

- **3**: Rationale is concise, names the X-rule firings and
  missingness tags that drove the decision, and reads like a human
  coach.
- **2**: Rationale is correct but verbose or fails to name one of
  the drivers.
- **1**: Rationale is generic ("based on your data") and does not
  reference the specific signals at play.
- **0**: Rationale is missing, incoherent, or contradicts the action.

### 3. Uncertainty calibration (0–3)

- **3**: Confidence value correctly reflects the combined effect
  of cap_confidence rules, missingness tags, and proposal confidence.
- **2**: Confidence is in the right zone but off by one level.
- **1**: Confidence ignores a known signal (e.g., cap not applied,
  or overly-low confidence with no reason).
- **0**: Confidence contradicts the pass_criteria.

## Gate decision

| Count of scenarios with action_correctness ≥ 2/3 | Outcome |
|---|---|
| 4 of 4 | Phase 3 authorised unconditionally |
| 3 of 4 | Phase 3 authorised; single miss recorded as a known-risk |
| ≤ 2 of 4 | Synthesis-skill-prompt redesign moves into Phase 3 scope as a visible correction (not a stop-rebuild trigger, per plan) |

## Note on scoring honesty

All four scenarios were authored before reading the skill body. The
scorer (same session as author) applies the rubric against the actual
current-system behaviour, not against imagined behaviour. Where the
current system partially satisfies a criterion, the score reflects
that; where invariants are breached, the score does too.
