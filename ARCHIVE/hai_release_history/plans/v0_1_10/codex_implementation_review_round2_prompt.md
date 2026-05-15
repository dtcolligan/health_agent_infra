# Codex Implementation Review — v0.1.10 Round 2

> **Why this round.** Round 1 returned `DO_NOT_SHIP`
> (`codex_implementation_review_response.md`) with four blockers:
>
> - **F-CDX-IR-01** — W-C partial-day gate not wired into
>   `build_snapshot`.
> - **F-CDX-IR-02** — W-A coercer sweep missed live threshold
>   consumers.
> - **F-CDX-IR-03** — `verification/tests` not hermetic (8 tests
>   hit live intervals.icu and 403'd under configured credentials).
> - **F-CDX-IR-04** — F-B-02 / F-B-01 deferral incompatible with
>   the "audit-chain integrity" release framing.
>
> The maintainer chose Path B from the round-1 follow-up:
> **fix all three mechanical blockers + rescope v0.1.10 honestly**
> instead of un-deferring W-E / W-F under release pressure.
> v0.1.11 is now positioned as the audit-chain-integrity release;
> v0.1.10 ships with the correctness + persona-harness scope
> only.
>
> **Your job.** Verify the three mechanical fixes are complete and
> sound. Verify the rescope is honest (CHANGELOG, PLAN, RELEASE_PROOF,
> v0.1.11 BACKLOG, v0.1.11 PLAN). Return a fresh verdict.
>
> **Scope fence — strictly v0.1.10.** A separate strategic +
> tactical planning effort (`reporting/plans/strategic_plan_v1.md`,
> `tactical_plan_v0_1_x.md`, `eval_strategy/`,
> `success_framework_v1.md`, `risks_and_open_questions.md`,
> `v0_1_11/PLAN.md`, `v0_1_11/BACKLOG.md`, `README.md`) is in the
> working tree. v0.1.11 PLAN.md and v0.1.11 BACKLOG.md *are*
> in-scope for round 2 verification (they receive the deferred
> items), but the rest of the strategic-plan tree is **not part
> of v0.1.10**. Do not audit those documents themselves.

---

## Step 0 — Confirm you're in the right tree

```bash
pwd
# expect: /Users/domcolligan/health_agent_infra
git branch --show-current
# expect: main
git log --oneline -3
# expect: 8c1ef8a release: v0.1.9 hardening (and earlier)
git status --short | head -20
# expect: ~22 modified, several untracked under reporting/plans/v0_1_10/,
#         v0_1_11/, and verification/dogfood/
cat pyproject.toml | grep '^version'
# expect: version = "0.1.10"
```

If any don't match, **stop and surface the discrepancy**.

---

## Step 1 — Read the round-2 artifacts

In order:

1. `reporting/plans/v0_1_10/codex_implementation_review_response.md`
   — round-1 verdict + the four blockers + the deferred concerns
   F-CDX-IR-05, F-CDX-IR-06.
2. `reporting/plans/v0_1_10/RELEASE_PROOF.md` — round-2 status
   header, the round-1→round-2 delta table, the workstream
   catalogue (W-A / W-A-extra / W-C / W-C-wire / W-D / W-D-ext /
   W-G / W-hermeticity / W-I / W-J / W-M).
3. `reporting/plans/v0_1_10/PLAN.md` — top-of-file rescope banner
   (2026-04-28); § 1 release framing; § 1.2 release-blocker-class
   vs backlog split.
4. `CHANGELOG.md` v0.1.10 entry — public-facing rescope language.
5. `reporting/plans/v0_1_11/PLAN.md` — verify W-E (§ 2.2), W-F
   (§ 2.3), W-R (§ 2.11), and W-S (§ 2.12) have honest scope
   contracts; verify the ship gate names W-E / W-F as
   release-blocker-class.
6. `reporting/plans/v0_1_11/BACKLOG.md` — verify W-E and W-F land
   in the "Release-blocker-class" section, not buried in generic
   backlog.

---

## Step 2 — Audit the four blockers

### Q1 — F-CDX-IR-01 (W-C wire) closed?

The fix should plumb `meals_count` and `is_end_of_day` from the
nutrition row into `evaluate_nutrition_policy`.

Audit:

- **`src/health_agent_infra/core/state/snapshot.py`** — find the
  `evaluate_nutrition_policy(...)` call site (was at line ~875
  in round 1). Verify it now passes `meals_count` and
  `is_end_of_day`.
- **`meals_count` source.** The fix reads from
  `(nutrition_today or {}).get("meals_count")`. Trace
  `nutrition_today` upstream — is `meals_count` reliably present
  on accepted nutrition rows? When is it `None`?
- **`is_end_of_day` derivation.** The fix uses
  `now_local.hour >= eod_hour` for today, `True` for past dates,
  `False` for future. Verify:
  - Past date with full-day nutrition row → escalates as expected.
  - Today + 06:32 + 1 meal → suppressed.
  - Today + 21:30 + 1 meal → escalates.
  - Today + 06:32 + 4 meals → escalates (gate disengaged).
- **`r_extreme_deficiency_end_of_day_local_hour` threshold.**
  Confirm it's added to `DEFAULT_THRESHOLDS["policy"]["nutrition"]`
  with default 21 and that `coerce_int` is used to read it.
- **Test coverage.**
  `verification/tests/test_partial_day_nutrition_snapshot_wire.py`
  — read the four test cases. Do they actually exercise
  `build_snapshot` (not just the policy boundary)? Are the
  boundary conditions (21:30 fire, 06:32 suppress, past-date
  fire, threshold override) covered?

Verdict: `CLOSED` | `CLOSED_WITH_CONCERNS` | `STILL_OPEN`.

### Q2 — F-CDX-IR-02 (W-A sweep completion) closed?

Round 1 Codex grepped and found survivors:
`heavy_lower_body_min_volume`, `vigorous_intensity_min`,
`long_run_min_duration_s`, `body_battery_max` (twice),
plus `core/pull/garmin_live.py:160` retry config.

Audit:

- Re-grep:

  ```bash
  rg -n '\b(?:int|float|bool)\(cfg\b' src/health_agent_infra/
  rg -n '\b(?:int|float|bool)\(thresholds\b' src/health_agent_infra/
  ```

  Expect zero matches.
- **`src/health_agent_infra/core/synthesis_policy.py`** — verify
  x4 (`heavy_lower_body_min_volume`), x5
  (`vigorous_intensity_min`, `long_run_min_duration_s`), x6a +
  x6b (`body_battery_max`) all use `coerce_int` / `coerce_float`
  with named `name=` args.
- **`src/health_agent_infra/core/pull/garmin_live.py`** —
  `retry_config_from_thresholds` uses all four `coerce_*` helpers
  (int, float×2, bool).
- **`verification/tests/test_d12_no_raw_cfg_coerce.py`** — read
  the test. Does the regex actually catch the patterns Codex
  round 1 named? Spot-check by adding a fake `int(cfg.get("x"))`
  line in your local copy of a runtime file and confirm the test
  fails. (Don't commit the fake line.)
- **Coverage gap.** Are there *other* threshold-consumer patterns
  the grep doesn't catch? E.g., `thresholds["policy"]["x"]["y"]`
  unwrapped without coercion. Spot-check
  `_get(thresholds, ...)` call sites.

Verdict: same scale.

### Q3 — F-CDX-IR-03 (test-suite hermeticity) closed?

Round 1 reproduction:

```bash
HAI_INTERVALS_ATHLETE_ID=fake_id \
HAI_INTERVALS_API_KEY=fake_key \
uv run pytest verification/tests -q
# round 1: 8 failed, 2161 passed, 2 skipped
```

Round 2 should now produce identical results regardless of env
state.

Audit:

- **`verification/tests/conftest.py`** — read the autouse fixture.
  Does it monkeypatch
  `health_agent_infra.cli._intervals_icu_configured` to return
  `False`? Is `raising=True` set so missing target fails loudly
  (rather than silently no-op'ing if the symbol is renamed)?
- **Reproduce the env-set case:**

  ```bash
  HAI_INTERVALS_ATHLETE_ID=fake \
    HAI_INTERVALS_API_KEY=fake \
    uv run pytest verification/tests -q
  ```

  Expect `2174 passed, 2 skipped`.
- **Reproduce the env-clean case:**

  ```bash
  uv run pytest verification/tests -q
  ```

  Expect identical `2174 passed, 2 skipped`.
- **Opt-out path.** If a test wanted to exercise the resolver's
  intervals.icu auto-default path, can it monkeypatch back to
  `True`? Verify by reading `test_pull_auth.py` or any pull-
  resolver tests — they should not be affected by the autouse
  fixture (they construct `CredentialStore` directly).
- **Cross-check.** Are there any *other* tests that hit live
  network paths besides the eight named in round 1? Spot-check
  by greppping for `requests.get` / `urlopen` / live calls in
  test code.

Verdict: same scale.

### Q4 — F-CDX-IR-04 (rescope honesty) accepted?

The rescope decision: drop the audit-chain-integrity claim from
v0.1.10 entirely; defer W-E + W-F to v0.1.11 as
release-blocker-class.

Audit:

- **`CHANGELOG.md`** v0.1.10 entry — does the theme statement
  honestly describe what the release ships? Does it explicitly
  call out the audit-chain integrity work as deferred? Does it
  reference Codex round 1's `DO_NOT_SHIP` verdict in the
  audit-history note?
- **`reporting/plans/v0_1_10/PLAN.md`** — does the rescope banner
  at the top and § 1 framing match? Does § 1.2 separate
  release-blocker-class from generic backlog?
- **`reporting/plans/v0_1_10/RELEASE_PROOF.md`** — does the
  status header acknowledge round 1 → round 2? Does the
  round-1 → round-2 delta table land all six findings?
- **`reporting/plans/v0_1_11/PLAN.md`** — does it position
  audit-chain integrity (W-E + W-F) as the v0.1.11 thesis, not
  as backlog items? Does the ship-gate language (§ 3) flag
  W-E + W-F as release-blocker-class for v0.1.11?
- **`reporting/plans/v0_1_11/BACKLOG.md`** — do W-E and W-F
  appear at the top under "Release-blocker-class items", not
  buried below mypy and other generic items?

Verdict: `RESCOPE_HONEST` | `RESCOPE_PARTIAL` |
`RESCOPE_MISLEADING`.

---

## Step 3 — Reproduce the round-2 proof

```bash
uv run pytest verification/tests -q
# expect: 2174 passed, 2 skipped

HAI_INTERVALS_ATHLETE_ID=fake \
HAI_INTERVALS_API_KEY=fake \
uv run pytest verification/tests -q
# expect: 2174 passed, 2 skipped (identical)

uvx ruff check src/health_agent_infra/
# expect: All checks passed!

uv run hai capabilities --json | python3 -c \
  "import json,sys; print(json.load(sys.stdin)['hai_version'])"
# expect: 0.1.10

uv run hai capabilities --markdown > /tmp/cap_round2.md
diff /tmp/cap_round2.md reporting/docs/agent_cli_contract.md
# expect: zero drift

rm -rf /tmp/hai_dogfood_run_round2_codex
uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run_round2_codex
# expect: 8 personas, 0 crashes, 3 findings (F-C-04 residuals)
```

Any deviation is a severity-blocker.

---

## Step 4 — What's deliberately NOT changed

These are still in v0.1.10 because the rescope kept them:

- **W-A round-1 sites** (synthesis_policy x7, x2, x3a, x3b +
  nutrition policy/classify) — already coercer-compliant; round 2
  added the missing sites only.
- **W-D activity validator** — round 1's
  `ActivityProjectorInputError` + `_validate_activity_payload`
  unchanged.
- **W-D-ext aggregator wire** — round 1's `cmd_clean` rollup
  invocation unchanged. (Provenance completeness deferred to
  v0.1.11 W-R per F-CDX-IR-05.)
- **W-G gym alias** — unchanged.
- **W-I / W-J ruff cleanup** — unchanged.
- **Persona harness (W-M)** — unchanged. (Drift guards deferred
  to v0.1.11 W-S per F-CDX-IR-06.)

If you find any of these regressed in round 2, that's a blocker.

---

## Step 5 — What's NOT v0.1.10 (do not audit)

Untracked planning files in the working tree from the strategic
+ tactical effort:

- `reporting/plans/strategic_plan_v1.md`
- `reporting/plans/tactical_plan_v0_1_x.md`
- `reporting/plans/eval_strategy/v1.md`
- `reporting/plans/success_framework_v1.md`
- `reporting/plans/risks_and_open_questions.md`
- `reporting/plans/README.md` (the planning-tree index)

**Do not audit these for v0.1.10 review.** They will receive their
own audit round once v0.1.10 ships.

The exceptions are `v0_1_11/PLAN.md` and `v0_1_11/BACKLOG.md`,
which *are* in scope for round 2 because they receive the
deferred items and the rescope decision needs to be visible
there. Audit them only as receivers of the W-E / W-F / W-R / W-S
deferral, not as standalone plan documents.

---

## Step 6 — Output format

Write findings to:

```
reporting/plans/v0_1_10/codex_implementation_review_round2_response.md
```

Schema per finding (only if a blocker remains):

```markdown
### F-CDX-IR-R2-NN. <one-line title>

**Question:** Q1 | Q2 | Q3 | Q4
**Severity:** blocker | concern | nit
**File:** path:line
**Description:** ...
**Recommendation:** fix-before-ship | document-and-defer | accept-as-is
```

Then a per-question summary:

```markdown
## Q1 — F-CDX-IR-01 (W-C wire) closed?
Verdict: CLOSED | CLOSED_WITH_CONCERNS | STILL_OPEN
Reasoning: ...

## Q2 — F-CDX-IR-02 (W-A sweep) closed?
Verdict: ...
...
```

Then an overall verdict:

```markdown
## Overall verdict

- **SHIP** — all four round-1 blockers closed, rescope honest,
  no new blockers. v0.1.10 is ready to commit, tag, publish.
- **SHIP_WITH_NOTES** — closed but with documented concerns
  that the maintainer should fold into v0.1.11 awareness.
- **DO_NOT_SHIP** — at least one round-1 blocker remains, OR the
  rescope is misleading, OR a new blocker surfaced. Name what
  must change.
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
  `verification/tests/`.
- **No new files outside `reporting/plans/v0_1_10/`** unless
  obvious test scaffolding.
- **No CHANGELOG.md edits.**
- **No git operations.**
- **Phase 4 fence.** If you find yourself reading
  `strategic_plan_v1.md` or any non-v0.1.11 planning doc, stop.

Begin.
