# W-T — In-Memory Threshold Injection Seam Audit

> **Cycle:** v0.1.11 W-T. **Source:** Codex round 3 SHIP_WITH_NOTES
> note 1 (F-CDX-IR-R3-N1) on the v0.1.10 audit.
>
> **Verdict:** documentation-only outcome. Every call site that
> passes `thresholds=` is either production (transitively validated
> via `load_thresholds` at the user-TOML boundary) or test
> (trusted by design). No additional in-runtime validation is
> required. Settled decision **D13** added to AGENTS.md.

---

## Background

`load_thresholds()` is the documented boundary that validates
user-supplied `thresholds.toml` overrides against
`DEFAULT_THRESHOLDS`. v0.1.10's `_validate_threshold_types`
(F-CDX-IR-R2-01 fix) catches bool-as-int silent coercion at TOML
parse time.

But every domain's `evaluate_*_policy` and `classify_*_state` entry
point also accepts a `thresholds: Optional[dict[str, Any]] = None`
argument. When a caller constructs that dict in-memory and passes
it directly, `_validate_threshold_types` is bypassed: a
programmatic `{"policy": {"strength": {"r_volume_spike_min_ratio":
True}}}` would propagate a Python `bool` into the comparison sites
even though the same shape from `thresholds.toml` would reject.

Codex round 3 flagged this as a trusted-seam concern. The
question for W-T: are any non-test, non-production callers
constructing the dict in-memory? If so the seam is genuinely
broken and the validator must extend. If only production +
test callers exist, the seam is trusted by design.

## Survey

`grep -rn "thresholds: Optional\[dict" src/health_agent_infra`
identifies the function signatures (every domain's
classify_*_state and evaluate_*_policy — 12 total entry points
across 6 domains).

Caller survey (`grep -rn "thresholds=" src/health_agent_infra
--include="*.py"`):

### Production callers

The primary production caller is `core/state/snapshot.py`
(`build_snapshot`). It loads the validated thresholds via
`load_thresholds()` once at the snapshot boundary and threads
the dict through every classify+policy call. **Validated
upstream.** No in-memory dict construction.

`core/synthesis.py` and `core/synthesis_policy.py` follow the
same pattern: pass through the validated dict from the snapshot
boundary, or load fresh via `load_thresholds()` when invoked
standalone.

`evals/runner.py` loads via `load_thresholds(scenario_path)`
when running scenario evaluations against a per-scenario
thresholds.toml. **Validated.** A scenario that supplies an
in-memory threshold override would also pass through TOML
serialise + load, hitting `_validate_threshold_types`.

The strength `_r_volume_spike` site added in v0.1.11 W-B (this
cycle) reads from the dict and uses `coerce_int` / `coerce_float`
internally — that's defensive even if the dict bypassed the
boundary, because the coercer rejects bool-as-int regardless of
how the dict was constructed.

### Test callers

`verification/tests/` contains many tests that build threshold
dicts in-memory (typically by `copy.deepcopy(DEFAULT_THRESHOLDS)`
followed by overrides for the bug class under test). These are
trusted by design — the test author intentionally exercises a
specific shape, often one that the validator would reject.

The new `test_xrule_volume_spike_coverage.py` in this cycle uses
that exact pattern to verify the D12 coercer rejects bool
overrides at policy-invocation time. The test path being
validator-bypass is the point of the test.

### Non-production, non-test callers

**None observed.** The persona harness
(`verification/dogfood/synthetic_skill.py`) does not construct
threshold dicts directly; it builds proposals and routes them
through `hai propose`, which uses the full snapshot+policy
pipeline behind the validated boundary.

## Outcome

The threshold-passing seam is **trusted by design**. Every
production caller transitively validates via `load_thresholds`;
every test caller is intentional and trusted. No
non-production-non-test caller exists today.

Documentation:

1. **AGENTS.md gains D13** — explicit settled decision: the
   threshold-injection seam is trusted-by-design; production
   callers must always validate via `load_thresholds`. New code
   that constructs threshold dicts in-memory and passes them to
   `evaluate_*_policy` / `classify_*_state` is a code-review
   concern. (Below.)
2. **Defensive coercion** — the v0.1.11 W-B addition uses
   `coerce_int` / `coerce_float` directly inside `_r_volume_spike`
   so even a hypothetical bypass-the-boundary call still rejects
   bool-as-int at the consumer site. New threshold-consumer code
   should follow this pattern (D12 already requires it; W-T
   reinforces).

No code changes required for the W-T workstream. The audit
itself is the deliverable.

## D13 (proposed addition to AGENTS.md "Settled Decisions")

> **(D13, v0.1.11) Threshold-injection seam is trusted-by-design.**
> Production callers always validate user-supplied thresholds via
> `core.config.load_thresholds`, which runs
> `_validate_threshold_types` at the user-TOML boundary. Every
> `evaluate_*_policy` / `classify_*_state` entry point accepts a
> `thresholds: Optional[dict]` arg, but in-memory construction +
> direct pass-through is reserved for tests (trusted by design)
> and intentional defensive paths. New non-test code that
> constructs threshold dicts and bypasses `load_thresholds` is a
> code-review concern. Defensive D12 coercer use at consumer sites
> is the second line of defence.

## Files inspected (no edits made)

- `src/health_agent_infra/core/config.py` (load_thresholds,
  _validate_threshold_types, coerce_*).
- `src/health_agent_infra/domains/*/classify.py` and
  `src/health_agent_infra/domains/*/policy.py` (12 entry points).
- `src/health_agent_infra/core/state/snapshot.py` (build_snapshot
  threshold pass-through).
- `src/health_agent_infra/core/synthesis.py`,
  `core/synthesis_policy.py`.
- `src/health_agent_infra/evals/runner.py`.
- `verification/dogfood/synthetic_skill.py` and persona authoring
  surface.

## Acceptance gate

- [x] Audit summary documents every call-site category.
- [x] Documentation-only outcome confirmed.
- [x] D13 proposed for AGENTS.md.
- [x] Defensive D12 coercer pattern reinforced in W-B (this cycle).
