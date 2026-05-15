# Codex Implementation Review — v0.1.10

> **Why this round.** v0.1.10 implementation has landed in the
> working tree. This is the formal code-review audit before commit
> + ship. The pre-PLAN bug hunt (Phase 0) and implementation
> (Phase 1) are complete; you are auditing the diff that produced
> the current `RELEASE_PROOF.md`.
>
> **This is NOT the pre-PLAN bug hunt.** That separate audit has its
> own prompt (`codex_audit_prompt.md`) and its own input
> (`audit_findings.md`). You are reviewing the **fixes**, not hunting
> for new bugs.
>
> **Scope fence — strictly v0.1.10.** A separate strategic +
> tactical planning effort (`reporting/plans/strategic_plan_v1.md`,
> `tactical_plan_v0_1_x.md`, `eval_strategy/`,
> `success_framework_v1.md`, `risks_and_open_questions.md`,
> `v0_1_11/`, `README.md` index) is in the working tree as untracked
> files. **Ignore that work.** It is post-v0.1.10 and will receive
> its own audit round. If you wander into those files and use them
> as input, your verdict will be wrong.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -3
# expect: 8c1ef8a release: v0.1.9 hardening (and earlier)
git status --short
# expect: ~21 modified + several untracked under reporting/plans/ and verification/dogfood/
cat pyproject.toml | grep '^version'
# expect: version = "0.1.10"
```

If any don't match, **stop and surface the discrepancy**. Ignore
any tree under `/Users/domcolligan/Documents/`.

---

## Step 1 — Read the orientation artifacts in this order

1. **`AGENTS.md`** — operating contract. Pay special attention to
   "Governance Invariants" (W57, three-state audit chain,
   review-summary bool-as-int hardening) and "Settled Decisions"
   (D1-D12). The D10/D11/D12 entries are NEW in this cycle.
2. **`reporting/plans/v0_1_10/PRE_AUDIT_PLAN.md`** — what the
   pre-PLAN hunt set out to do.
3. **`reporting/plans/v0_1_10/audit_findings.md`** — the 27
   findings the hunt produced (Phase A internal sweep + Phase B
   audit-chain probe + Phase C persona matrix).
4. **`reporting/plans/v0_1_10/PLAN.md`** — the workstream catalogue
   built from the findings, including the in-scope/deferred split.
5. **`reporting/plans/v0_1_10/RELEASE_PROOF.md`** — the
   ship-readiness proof. This is the claim you are validating.
6. **`CHANGELOG.md`** v0.1.10 entry — the public-facing summary.

---

## Step 2 — The review questions

You are answering five questions. Each must produce a verdict.

### Q1 — Triage soundness

Given the 27 findings in `audit_findings.md`, is the in-scope vs
deferred split in `PLAN.md § 1.1` and `RELEASE_PROOF.md § 1`
defensible?

- Was anything classified as deferred that should have been
  fix-now (correctness or audit-chain risk)?
- Was anything classified as fix-now that should have been
  deferred (out-of-cycle architectural risk)?
- Are the deferral reasons in `RELEASE_PROOF.md` "Workstreams
  partially closed" honest about *why* the work didn't land
  (genuine investigation needed) vs. cycle exhaustion?

Findings to scrutinise:
- **F-B-01** (audit-chain version-counter `_v0 → _v3` jump) —
  deferred to v0.1.11. Is this safe to defer, or is it shipping
  a known audit-chain integrity hole?
- **F-B-02** (state-change re-synth) — deferred. Same question.
- **F-C-04** (R-volume-spike on regular training pattern) —
  deferred to v0.1.11. Affects 6 of 8 personas. Defensible?
- **F-A-13** (bandit B608, 16 sites) and **F-A-14** (B310) —
  deferred. Security review left open.

### Q2 — W-A correctness (threshold coercer)

The `coerce_int` / `coerce_float` / `coerce_bool` helpers are the
load-bearing change in the cycle.

Audit:
- **`src/health_agent_infra/core/config.py`** — read the helper
  bodies. Do they actually reject bool-as-int? `True` and `False`
  are instances of `int` in Python — does the helper short-circuit
  on `isinstance(value, bool)` *before* `isinstance(value, int)`?
- **`src/health_agent_infra/core/synthesis_policy.py`** — verify
  the W-A coercer was applied at x7, x2, x3a, x3b. The `RELEASE_PROOF`
  claims 4 sites; count them. Were any threshold-consumer sites
  missed?
- **`src/health_agent_infra/domains/nutrition/policy.py`** and
  **`classify.py`** — same check. Claim is 8 sites total.
- **`verification/tests/test_config_coerce.py`** — 24 tests. Do
  they cover: bool rejection, string rejection, None rejection,
  numeric strings, numeric floats, the `name=` kwarg propagating
  to error messages?
- **Coverage gap.** Are there `int(cfg...)` / `float(cfg...)` /
  `bool(cfg...)` calls *outside* the listed sites that should
  have used the coercer? Grep:

  ```bash
  rg -n 'int\(cfg' src/health_agent_infra/
  rg -n 'float\(cfg' src/health_agent_infra/
  rg -n 'bool\(cfg' src/health_agent_infra/
  rg -n 'int\(.*\.get\(' src/health_agent_infra/
  ```
  
  Any survivors are D12 violations (per AGENTS.md "Settled
  Decisions").

### Q3 — W-C partial-day gate correctness

The `_r_extreme_deficiency` rule now takes `meals_count` and
`is_end_of_day` parameters with `r_extreme_deficiency_min_meals_count: 2`
default.

Audit:
- **`src/health_agent_infra/domains/nutrition/policy.py`** — read
  the rule body. Does the gate prevent firing when `meals_count <
  threshold` AND `not is_end_of_day`? What about the boundary
  cases:
  - `meals_count = 2`, `is_end_of_day = False`, time = 17:59 — should
    fire if criteria met. Does it?
  - `meals_count = 1`, `is_end_of_day = True` — should fire (full day,
    one meal logged is genuinely deficient). Does it?
  - `meals_count = None` (backward compatibility) — what happens?
- **`verification/tests/test_partial_day_nutrition_gate.py`** —
  5 tests. Do they cover the boundary above? Is the breakfast-only
  reproduction (B1 from project memory) explicitly tested?
- **Caller wiring.** Where is `meals_count` plumbed in from? Is
  `is_end_of_day` derived from a clock at evaluation time, or
  passed in from the caller? Trace one call path end-to-end.

### Q4 — W-D / W-D-ext correctness (activity projector + aggregator wire)

Two changes touch the running domain.

**W-D — activity projector validation.**
- **`src/health_agent_infra/core/state/projectors/running_activity.py`**
  — read `_validate_activity_payload`. What fields does it require?
  Match against the actual payload shape produced by
  `core/pull/intervals_icu.py` activity rows.
- Does the validator raise `ActivityProjectorInputError` cleanly,
  or is there a path where it raises a `KeyError` the validator
  was meant to catch?
- **`verification/tests/test_running_activity_projector.py`** —
  7 tests. Do they cover each missing-field case + the happy path?

**W-D-ext — running aggregation wire.**
- **`src/health_agent_infra/cli.py`** `cmd_clean` — find the new
  `aggregate_activities_to_daily_rollup` call site. Trace:
  - What dates does it run for (today only, or backfill)?
  - The `_ROLLUP_TO_RAW` field-name mapping — is it complete?
    `aggregate_activities_to_daily_rollup` returns `total_distance_m`,
    `total_moving_time_s`, `total_elevation_m`, etc.; the projector
    expects `distance_m`, `moving_time_s`, `elevation_m`. Spot-check
    each mapped field.
  - Does this introduce a write path that bypasses the three-state
    audit chain? It shouldn't (it's a projection layer above the
    audit chain), but verify.
- **Persona regression evidence.** `RELEASE_PROOF § 3` claims P2 +
  P7 went from `defer` to a useful action on running. Is the
  harness actually exercising the rollup path, or is the synthetic
  CSV bypassing it? Trace the harness call.

### Q5 — Persona harness load-bearing-ness

`verification/dogfood/` is permanent regression infrastructure
per D10. Audit:

- **`verification/dogfood/runner.py`** — does each persona run
  in true isolation? `HAI_STATE_DB` and `HAI_BASE_DIR` are set
  per-persona; verify they actually scope SQLite writes and
  XDG state.
- **`verification/dogfood/synthetic_skill.py`** — this stands in
  for the skill layer. Does the `_DOMAIN_DEFAULT_ACTION` and
  `_STATUS_TO_ACTION` mapping use action tokens from
  `core/validate.ALLOWED_ACTIONS_BY_DOMAIN`? A drift here would
  silently invalidate every persona run.
- **Persona coverage.** Are P1-P8 representative of the
  recreational + technical athlete user shape (per D10's audience
  scope)? What's NOT covered, and is the gap honest in
  `verification/dogfood/README.md`?
- **Schema versions in proposals.** The synthetic skill posts
  `<domain>_proposal.v1` schema versions. If the runtime ever
  bumps these, will the harness silently fall behind? How is drift
  detected?

### Q6 — Cross-cutting integrity

- **Three-state audit chain (Governance Invariant 5).** Does any
  v0.1.10 change introduce a write path that bypasses
  `proposal_log → planned_recommendation → daily_plan +
  recommendation_log → review_outcome`? Spot-check `cmd_clean`'s
  rollup wire.
- **W57 governance.** Did anything in v0.1.10 add a code path
  where the agent can deactivate user-authored intent/target
  state without `--confirm`? Should be no (no intent/target code
  changed in this cycle), but verify.
- **No clinical claims.** Did anything in the partial-day gate
  rationale or the W-A coercer error messages introduce
  diagnosis-shaped language? Read the error strings.
- **Skill drift.** No skill changes in this cycle. Confirm by
  diffing `src/health_agent_infra/skills/`.
- **CLI surface coherence.** `reporting/docs/agent_cli_contract.md`
  was regenerated post-version-bump. Re-run `uv run hai
  capabilities --markdown` and diff. Should be zero drift unless
  W-G's gym intake alias added a documented parameter.

---

## Step 3 — Reproduce the proof

```bash
# Test surface
uv run pytest verification/tests -q
# Expect: 2169 passed, 2 skipped

uvx ruff check src/health_agent_infra/
# Expect: All checks passed!

uv run hai capabilities --json | head -5
# Expect: valid JSON; version field reads "0.1.10"

# Persona harness regression
rm -rf /tmp/hai_dogfood_run_codex
uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run_codex
# Expect: 8 personas, 0 crashes, ≤3 findings (all F-C-04 residual)
```

If any of these don't match `RELEASE_PROOF.md` claims, the proof
is invalid — flag it as severity-blocker.

---

## Step 4 — What's already deferred (don't re-find)

These are explicitly out of scope per `PLAN.md § 1.2` and
`RELEASE_PROOF.md § 1`:

- **W-B** R-volume-spike coverage gate (deferred — interacts with
  strength freshness model)
- **W-E** state-change re-synth detection (deferred — needs design)
- **W-F** version-counter integrity investigation (deferred —
  root cause not yet localised)
- **W-H** ~30 remaining mypy errors (deferred — out-of-cycle)
- **W-K** bandit B608 audit (16 sites — deferred)
- **W-L** bandit B310 audit (deferred)
- **W-N** pytest unraisable warning (deferred)
- **F-B-03, F-B-04, F-A-08, F-C-05, F-C-06** (per `PLAN.md § 1.2`)
- **W52, W53, W58** (already deferred per v0.1.9 backlog)

You can flag concerns about *whether* the deferral is safe (Q1),
but don't propose fixes for these in v0.1.10.

---

## Step 5 — What's NOT v0.1.10 (do not audit)

Untracked files in the working tree from a separate strategic
planning effort:

- `reporting/plans/strategic_plan_v1.md`
- `reporting/plans/tactical_plan_v0_1_x.md`
- `reporting/plans/eval_strategy/v1.md`
- `reporting/plans/success_framework_v1.md`
- `reporting/plans/risks_and_open_questions.md`
- `reporting/plans/README.md` (new index)
- `reporting/plans/v0_1_11/` (entire directory)

**Do not read these as inputs. Do not include them in your
review. They will get their own audit round once v0.1.10 is
shipped.** If a v0.1.10 doc cross-links to one of these files,
note the link but do not follow it.

The modified `AGENTS.md` and `REPO_MAP.md` *do* contain
v0.1.10-relevant updates (D10, D11, D12 settled decisions; new
seams) — those parts are in scope. Updates pointing at the
strategic-plan tree are not.

---

## Step 6 — Output format

Write your findings to a new file:

```
reporting/plans/v0_1_10/codex_implementation_review_response.md
```

Schema per finding:

```markdown
### F-CDX-IR-NN. <one-line title>

**Question:** Q1 | Q2 | Q3 | Q4 | Q5 | Q6
**Severity:** blocker | concern | nit
**File:** path:line
**Description:** ...
**Recommendation:** fix-before-ship | document-and-defer |
                   accept-as-is
```

Then a per-question summary block:

```markdown
## Q1 — Triage soundness
Verdict: SOUND | SOUND_WITH_CONCERNS | UNSOUND
Reasoning: ...

## Q2 — W-A correctness
Verdict: ...
...
```

Then an overall verdict:

```markdown
## Overall verdict
- **SHIP** — no blockers, ≤3 nits.
- **SHIP_WITH_NOTES** — concerns documented, none blocking;
  notes captured in v0.1.11 BACKLOG.md.
- **DO_NOT_SHIP** — at least one blocker; name what must change.
```

End with:

```markdown
## What I did NOT review
- ...
## What I expected to find but did not
- ...
```

---

## Step 7 — Constraints

- **Read-only.** Do not modify `src/health_agent_infra/` or
  `verification/tests/`. Findings are written; fixes are
  maintainer's call.
- **No new files outside `reporting/plans/v0_1_10/`** unless
  obvious test scaffolding.
- **No CHANGELOG.md edits.**
- **No git operations.** The maintainer commits.
- **Honour governance invariants.** Anything that violates W57,
  the three-state audit chain, or no-clinical-claims is a
  blocker — flag rather than work around.
- **Phase 4 fence.** If you find yourself reading
  `strategic_plan_v1.md` or anything in `reporting/plans/v0_1_11/`,
  stop. Those are not v0.1.10.

Begin.
