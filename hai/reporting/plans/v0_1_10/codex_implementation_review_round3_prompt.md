# Codex Implementation Review — v0.1.10 Round 3

> **Why this round.** Round 2 returned `DO_NOT_SHIP` with one blocker
> (`codex_implementation_review_round2_response.md`):
>
> - **F-CDX-IR-R2-01** — D12 grep guard catches raw-cast survivors
>   but misses direct numeric leaf consumers. Because Python bools
>   are numeric, a TOML override of e.g. `low_max_ratio = true`
>   would still flow through `protein_ratio < cfg["low_max_ratio"]`
>   as `1`, regardless of the W-A coercer sweep.
>
> Plus two doc concerns:
>
> - **F-CDX-IR-R2-02** — `v0_1_10/PLAN.md` retained pre-rescope
>   stale text (W-C end-of-day = 18:00, W-E/W-F still listed as
>   in-scope, acceptance criteria still naming F-B-02).
> - **F-CDX-IR-R2-03** — `v0_1_11/BACKLOG.md` labelled F-CDX-IR-05
>   as W-S and F-CDX-IR-06 as W-T; PLAN.md correctly maps them
>   to W-R and W-S.
>
> **Round 3 closes all three architecturally.** The blocker is
> closed by **load-time threshold-type validation** in
> `core/config.load_thresholds`, so consumers never see a bool-
> shaped numeric value regardless of how they read the leaf. The
> doc concerns are closed by direct edits.
>
> **Your job.** Verify load-time validation is sound and complete.
> Verify the doc cleanups land. Return a fresh verdict.
>
> **Scope fence — strictly v0.1.10.** Same as round 2: the
> strategic + tactical planning files
> (`reporting/plans/strategic_plan_v1.md`,
> `tactical_plan_v0_1_x.md`, `eval_strategy/`,
> `success_framework_v1.md`, `risks_and_open_questions.md`,
> `README.md`) are **not part of v0.1.10**. `v0_1_11/PLAN.md` and
> `v0_1_11/BACKLOG.md` are in-scope only as receivers of deferred
> items.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git status --short | head -25
# expect: ~24 modified, several untracked under reporting/plans/v0_1_10/,
#         v0_1_11/, verification/dogfood/, verification/tests/
cat pyproject.toml | grep '^version'
# expect: version = "0.1.10"
```

---

## Step 1 — Read the round-3 artifacts

In order:

1. `reporting/plans/v0_1_10/codex_implementation_review_round2_response.md`
   — round-2 verdict + the blocker + the two doc concerns.
2. `reporting/plans/v0_1_10/RELEASE_PROOF.md` — round-3 status
   header, the Round-1→Round-2→Round-3 delta table, the
   workstream catalogue with new W-A-validate row.
3. `reporting/plans/v0_1_10/PLAN.md` — verify § 1.1 catalogue is
   annotated with rescope status, § 2.3 W-C section reflects
   actual implementation (21:00 not 18:00), § 3 acceptance
   criteria match the ship state.
4. `CHANGELOG.md` v0.1.10 entry — verify it captures three
   audit rounds and explains the architectural close.
5. `reporting/plans/v0_1_11/BACKLOG.md` — verify F-CDX-IR-05 →
   W-R and F-CDX-IR-06 → W-S labels match `v0_1_11/PLAN.md`.

---

## Step 2 — The audit questions

### Q1 — F-CDX-IR-R2-01 closed at the right level?

The architectural fix is in `core/config.py`:

- New `_is_strict_bool(value)` — distinguishes bool from int.
- New `_validate_threshold_types(merged, default, path)` —
  recursively walks the merged tree, rejects type-changing
  overrides at each leaf.
- `load_thresholds(path)` calls `_validate_threshold_types` after
  `_deep_merge`.

Audit:

- **Read `core/config.py`.** Find `_is_strict_bool`,
  `_validate_threshold_types`, and the new call site in
  `load_thresholds`.
- **Bool-as-int rejection — the headline class.** Verify
  `_validate_threshold_types` actually catches:
  - `merged={"x": True}, default={"x": 5}` → raises
  - `merged={"x": False}, default={"x": 5}` → raises
  - `merged={"x": True}, default={"x": 1.5}` → raises
  - `merged={"x": 1}, default={"x": True}` → raises (numeric on bool)
  Spot-check the test cases in
  `verification/tests/test_load_time_threshold_validation.py`.
- **End-to-end TOML test.** Try the regression Codex round 2
  named: write a temp TOML with
  `low_max_ratio = true` and call `load_thresholds`. Verify it
  raises `ConfigCoerceError` rather than silently merging.
- **Are there leaves the validator misses?**
  - `DEFAULT_THRESHOLDS` is the reference for types. Are there
    leaves that legitimately have `None` defaults but expect a
    type when populated? (The validator allows any override
    against `None` defaults — is that desired?)
  - Are there leaves that are `dict` defaults where a user might
    legitimately add new keys? (The validator only checks keys
    present in BOTH default and merged — so user-added keys are
    silently allowed; is that desired?)
  - Lists are not type-checked element-by-element. Is that a
    problem in practice?
- **Consumer-side sweep coverage.** Round 3 also coerced the
  named direct-leaf consumers in `domains/nutrition/classify.py`:
  - `_classify_protein_sufficiency` — `very_low_max_ratio`,
    `low_max_ratio`.
  - `_classify_hydration` — `low_max_ratio`.
  - `classify_nutrition_state` — `calorie_target_kcal`,
    `protein_target_g`, `hydration_target_l`.
  - `_nutrition_score` — 9 penalty leaves coerced once into a
    typed dict.
  Verify these match Codex round-2 line numbers (~125-141,
  278-280, 222-239).
- **Architectural soundness vs consumer-side coverage.** The
  load-time validator catches ALL silent bool-on-numeric coercion.
  The consumer-side sweep is now stylistic/self-documenting, not
  load-bearing. Is that the right framing? (Or do you think the
  consumer-side sweep should also extend to recovery, running,
  sleep, stress, strength classifiers — even though load-time
  validation already protects them?)

Verdict: `CLOSED` | `CLOSED_WITH_CONCERNS` | `STILL_OPEN`.

### Q2 — F-CDX-IR-R2-02 (PLAN.md stale text) closed?

The round-3 fix:

- § 1.1 workstream catalogue gained a "Round-2 status" column +
  a banner explaining this is the original pre-rescope plan and
  `RELEASE_PROOF.md` is the actual ship-state record.
- § 2.3 W-C — the 18:00 line replaced with the actual threshold
  (`r_extreme_deficiency_end_of_day_local_hour`, default 21);
  added the round-2 wire note.
- § 3 acceptance criteria rewritten to match the ship state;
  out-of-scope items explicitly named.

Audit:

- Read § 1.1 — does each workstream have an honest round-2
  status?
- Read § 2.3 — is the threshold name + default correct?
- Read § 3 — do the criteria match `RELEASE_PROOF.md` § 1
  workstream catalogue + § 2 test surface?
- Are there other stale references (e.g. § 4 sequencing, § 5
  provenance) that didn't get updated?

Verdict: `CLOSED` | `CLOSED_WITH_CONCERNS` | `STILL_OPEN`.

### Q3 — F-CDX-IR-R2-03 (BACKLOG.md label mismatch) closed?

The round-3 fix:

- F-CDX-IR-05 entry now says "Proposed cycle: v0.1.11 W-R" with
  cross-reference to `v0_1_11/PLAN.md` § 2.11.
- F-CDX-IR-06 entry now says "Proposed cycle: v0.1.11 W-S" with
  cross-reference to `v0_1_11/PLAN.md` § 2.12.

Audit:

- Read both entries in `v0_1_11/BACKLOG.md`.
- Cross-check against `v0_1_11/PLAN.md` § 2.11 (W-R) and § 2.12
  (W-S).

Verdict: same scale.

### Q4 — Round-2 closed blockers still closed?

Sanity check that round 3 didn't regress round 2's fixes.

- F-CDX-IR-01 (W-C wire) — verify `core/state/snapshot.py` still
  passes `meals_count` + `is_end_of_day` into
  `evaluate_nutrition_policy`. Re-run
  `test_partial_day_nutrition_snapshot_wire.py`.
- F-CDX-IR-02 (W-A coercer named survivors) — re-grep:

  ```bash
  rg -n '\b(?:int|float|bool)\(cfg\b' src/health_agent_infra/
  rg -n '\b(?:int|float|bool)\(thresholds\b' src/health_agent_infra/
  ```
  Expect zero matches.
- F-CDX-IR-03 (test hermeticity) — pytest under env-set vs
  env-clean:

  ```bash
  uv run pytest verification/tests -q
  HAI_INTERVALS_ATHLETE_ID=fake \
    HAI_INTERVALS_API_KEY=fake \
    uv run pytest verification/tests -q
  ```
  Expect identical `2202 passed, 2 skipped`.
- F-CDX-IR-04 (rescope honesty) — does the round-3 catalogue +
  delta table preserve the "audit-chain integrity → v0.1.11
  thesis" framing? Spot-check `CHANGELOG.md`,
  `v0_1_10/RELEASE_PROOF.md`, and `v0_1_11/PLAN.md` § 3.

Verdict: `STILL_CLOSED` | `REGRESSED` (name what regressed).

---

## Step 3 — Reproduce the round-3 proof

```bash
uv run pytest verification/tests -q
# expect: 2202 passed, 2 skipped

HAI_INTERVALS_ATHLETE_ID=fake \
HAI_INTERVALS_API_KEY=fake \
uv run pytest verification/tests -q
# expect: 2202 passed, 2 skipped (identical)

uvx ruff check src/health_agent_infra/
# expect: All checks passed!

uv run hai capabilities --json | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['hai_version'])"
# expect: 0.1.10

uv run hai capabilities --markdown > /tmp/cap_round3.md
diff /tmp/cap_round3.md reporting/docs/agent_cli_contract.md
# expect: zero drift

rm -rf /tmp/hai_dogfood_run_round3_codex
uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run_round3_codex
# expect: 8 personas, 0 crashes, 3 findings (F-C-04 residuals)

# Bonus reproduction — the exact silent-coercion class from round 2:
uv run python -c '
from pathlib import Path
import tempfile
from health_agent_infra.core.config import load_thresholds, ConfigCoerceError
with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
    f.write("[classify.nutrition.protein_sufficiency_band]\n")
    f.write("low_max_ratio = true\n")
    p = Path(f.name)
try:
    load_thresholds(p)
    print("REGRESSION: silent coercion still passes")
except ConfigCoerceError as e:
    print(f"OK: rejected at load time -- {e}")
'
# expect: OK: rejected at load time -- threshold
#         'classify.nutrition.protein_sufficiency_band.low_max_ratio'
#         got bool True; expected float
```

---

## Step 4 — What's deliberately NOT changed in round 3

- Round-1 and round-2 fixes for F-CDX-IR-01 / 02 / 03 / 04 — see
  Q4 sanity check.
- Persona harness, W-D activity validator, W-D-ext aggregator
  wire, W-G gym alias, W-I/W-J ruff cleanup — unchanged from
  round 2.
- The audit-chain integrity workstreams (W-E + W-F) remain
  deferred to v0.1.11 as release-blocker-class.

---

## Step 5 — What's NOT v0.1.10 (do not audit)

- `reporting/plans/strategic_plan_v1.md`
- `reporting/plans/tactical_plan_v0_1_x.md`
- `reporting/plans/eval_strategy/v1.md`
- `reporting/plans/success_framework_v1.md`
- `reporting/plans/risks_and_open_questions.md`
- `reporting/plans/README.md`

`v0_1_11/PLAN.md` is in-scope only as receiver for W-E / W-F /
W-R / W-S. Audit it for that — not as a standalone plan.

---

## Step 6 — Output format

Write findings (only if blockers remain) to:

```
reporting/plans/v0_1_10/codex_implementation_review_round3_response.md
```

Per-question summary block, then overall verdict:

```markdown
## Overall verdict

- **SHIP** — load-time validation soundly closes the silent-
  coercion class; doc concerns closed; round 1 + 2 fixes intact.
  v0.1.10 is ready to commit, tag, publish.
- **SHIP_WITH_NOTES** — closed but with concerns the maintainer
  should fold into v0.1.11 awareness.
- **DO_NOT_SHIP** — at least one round-2 finding remains, OR a
  new blocker surfaced. Name what must change.
```

---

## Step 7 — Constraints

- **Read-only.** No source edits.
- **No new files outside `reporting/plans/v0_1_10/`** unless
  obvious test scaffolding.
- **No CHANGELOG.md edits.**
- **No git operations.**
- **Phase 4 fence.** If you find yourself reading
  `strategic_plan_v1.md` or any non-v0.1.11 planning doc, stop.

Begin.
