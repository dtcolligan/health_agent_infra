# Codex Implementation Review Response - v0.1.10 Round 2

Verdict: **DO_NOT_SHIP**

Round 2 closes the W-C runtime wire, the named raw-cast survivors, and the
pytest hermeticity blocker. The rescope is mostly honest in the public release
proof/changelog, but the W-A/D12 sweep is still incomplete: the new grep guard
passes while threshold consumers that read config leaves directly still accept
bool-shaped numeric values.

## Findings

### F-CDX-IR-R2-01. D12 guard misses direct numeric threshold consumers

**Question:** Q2  
**Severity:** blocker  
**File:** `src/health_agent_infra/domains/nutrition/classify.py:125`  
**Description:** The round-2 fix eliminated the named `int(cfg...)` /
`float(cfg...)` / `bool(cfg...)` survivors, but it did not close W-A/D12 across
threshold consumers. `test_d12_no_raw_cfg_coerce.py` only matches raw casts whose
argument starts with `cfg` or `thresholds`; it does not catch direct numeric
comparisons or arithmetic against config leaves. Representative survivors:
`nutrition/classify.py:125`, `:127`, `:141` compare ratio thresholds directly
from `cfg[...]`; `:278-280` use `float(targets[...])`; `:222-239` subtract
penalty values directly. Because Python bools are numeric, a TOML override such
as `very_low_max_ratio = true` or `protein_target_g = true` is still silently
treated as `1`/`1.0` instead of raising `ConfigCoerceError`. A wider grep also
shows the same direct-`cfg[...]` pattern across recovery, running, sleep,
stress, and strength classifiers. The release proof/changelog claim "every
threshold-consumer site in the runtime" is therefore not true yet.

I verified the guard's blind spot without editing source:
`int(cfg.get("x"))` matches the regex, while
`protein_ratio < cfg["low_max_ratio"]` does not.

**Recommendation:** fix-before-ship. At minimum, finish the claimed W-A scope in
`domains/nutrition/classify.py` by using `coerce_float` for targets, ratio
thresholds, and numeric penalties. Then either extend v0.1.10 to cover all
direct numeric threshold consumers in the runtime or narrow the release claim
and add a v0.1.11 blocker for the remaining domains. The regression guard should
also catch direct numeric config-leaf comparisons/arithmetic, or threshold
loading should schema-validate numeric leaves before consumers see them.

### F-CDX-IR-R2-02. v0.1.10 PLAN still contains stale pre-rescope acceptance text

**Question:** Q4  
**Severity:** concern  
**File:** `reporting/plans/v0_1_10/PLAN.md:313`  
**Description:** The top banner and section 1 rescope are clear, and the
CHANGELOG/RELEASE_PROOF now present v0.1.10 as correctness + persona harness
rather than audit-chain integrity. The lower PLAN body still contains stale
pre-rescope details: W-C says the end-of-day gate is 18:00 (`:148`, `:158`)
while the implementation/proof now use 21:00; the workstream catalogue still
lists W-E/W-F as ordinary in-scope workstreams (`:47-48`); and the acceptance
criteria still expect tests from W-E and an F-B-02 `_v2` plan-id result
(`:315-321`). This does not outweigh the clearer release proof/changelog, but
it is confusing release documentation.

**Recommendation:** document-and-defer only if this file is intentionally
historical; otherwise clean the stale acceptance text before commit so the PLAN
does not contradict the round-2 rescope.

### F-CDX-IR-R2-03. v0.1.11 BACKLOG labels W-R/W-S inconsistently

**Question:** Q4  
**Severity:** nit  
**File:** `reporting/plans/v0_1_11/BACKLOG.md:100`  
**Description:** `v0_1_11/PLAN.md` correctly maps F-CDX-IR-05 to W-R and
F-CDX-IR-06 to W-S. The backlog text still says F-CDX-IR-05 is proposed for
W-S (`:100`) and F-CDX-IR-06 is proposed for W-T (`:123`).

**Recommendation:** document-and-defer or fix-before-commit as a small doc
cleanup.

## Q1 - F-CDX-IR-01 (W-C wire) closed?

Verdict: **CLOSED_WITH_CONCERNS**

`build_snapshot` now reads `(nutrition_today or {}).get("meals_count")`, derives
`is_end_of_day` from `now_local.hour >= r_extreme_deficiency_end_of_day_local_hour`
for today, treats past dates as end-of-day, and passes both into
`evaluate_nutrition_policy`. The new threshold is present in
`DEFAULT_THRESHOLDS["policy"]["nutrition"]` with default `21` and is read through
`coerce_int`.

`verification/tests/test_partial_day_nutrition_snapshot_wire.py` exercises the
production `build_snapshot` path for 06:32 suppression, 21:30 escalation, past
date escalation, and threshold override. The one branch requested in the prompt
that is not covered at snapshot-integration level is "today + 06:32 + 4 meals";
it is covered at the policy boundary, and the production wiring appears sound.

## Q2 - F-CDX-IR-02 (W-A sweep) closed?

Verdict: **STILL_OPEN**

The named round-1 raw-cast survivors are fixed:

- `synthesis_policy.py` x4/x5/x6a/x6b now use `coerce_float` /
  `coerce_int` with named `name=` values.
- `garmin_live.py::retry_config_from_thresholds` now uses `coerce_int`,
  `coerce_float`, and `coerce_bool`.
- The exact round-1 greps for `int(cfg...)` and `int(thresholds...)`
  equivalents return zero matches.

However, the W-A/D12 sweep is still incomplete because direct numeric
threshold reads remain and the new guard misses them. See
F-CDX-IR-R2-01.

## Q3 - F-CDX-IR-03 (test-suite hermeticity) closed?

Verdict: **CLOSED**

`verification/tests/conftest.py` adds an autouse fixture that monkeypatches
`health_agent_infra.cli._intervals_icu_configured` to `False` with
`raising=True`. That removes the machine-local credential dependency that caused
the round-1 403 failures. Pull/auth tests construct stores or adapters directly,
so they are not relying on the live auto-default path.

Reproduced:

```text
uv run pytest verification/tests -q
2174 passed, 2 skipped in 57.08s

HAI_INTERVALS_ATHLETE_ID=fake HAI_INTERVALS_API_KEY=fake uv run pytest verification/tests -q
2174 passed, 2 skipped in 55.92s
```

## Q4 - F-CDX-IR-04 (rescope honesty) accepted?

Verdict: **RESCOPE_PARTIAL**

The high-signal release docs are honest: CHANGELOG states the audit-chain work
is deferred, names the Codex round-1 `DO_NOT_SHIP`, and positions v0.1.10 as
persona harness + correctness. RELEASE_PROOF has the round-1 to round-2 delta
table and sends W-E/W-F to v0.1.11 as release-blocker-class. `v0_1_11/PLAN.md`
contains W-E, W-F, W-R, and W-S with appropriate contracts, and its ship gates
make W-E/W-F release-blocker-class.

The rescope is partial rather than fully clean because `v0_1_10/PLAN.md` retains
stale pre-rescope acceptance text, and `v0_1_11/BACKLOG.md` has W-R/W-S label
mismatches. These are documentation concerns; the ship-blocker is Q2.

## Proof Commands

```text
pwd
/Users/domcolligan/health_agent_infra

git branch --show-current
main

pyproject.toml version
0.1.10

uv run pytest verification/tests -q
2174 passed, 2 skipped in 57.08s

HAI_INTERVALS_ATHLETE_ID=fake HAI_INTERVALS_API_KEY=fake uv run pytest verification/tests -q
2174 passed, 2 skipped in 55.92s

uvx ruff check src/health_agent_infra/
All checks passed!

uv run hai capabilities --json
hai_version = 0.1.10

uv run hai capabilities --markdown > /tmp/cap_round2.md
diff /tmp/cap_round2.md reporting/docs/agent_cli_contract.md
zero diff

uv run python -m verification.dogfood.runner /tmp/hai_dogfood_run_round2_codex_20260428
Total personas: 8, findings: 3, crashes: 0
findings_by_kind: strength_volume_spike_on_thin_history_suspect for p1, p4, p6
```

## Overall Verdict

**DO_NOT_SHIP**

The three mechanical round-1 blockers other than W-A are closed. W-A is still
open because the implementation and regression guard do not cover direct
numeric threshold consumers, so bool-shaped numeric config can still flow
silently through runtime threshold decisions. Fix that before commit/tag/publish.

## What I Did NOT Review

- Phase 4 / strategic planning documents outside the v0.1.10 fence.
- `v0_1_11/PLAN.md` as a standalone release plan beyond receiving W-E, W-F,
  W-R, and W-S.
- Package build/publish/tag steps.
- Source edits; this was a read-only review except for this response file.

## What I Expected To Find But Did Not

- I did not find W-C still bypassed in the `build_snapshot` path.
- I did not reproduce the round-1 live-credential pytest failures.
- I did not find capability markdown drift.
- I did not find persona harness crashes or unexpected non-F-C-04 residuals.
