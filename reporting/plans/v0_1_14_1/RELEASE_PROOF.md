**Cycle tier (D15): hardening.**

# v0.1.14.1 RELEASE PROOF — Garmin-live unreliability surfaced as structured signal

**Status.** Implementation + tests + docs landed. Pre-IR ready.
**Date.** 2026-05-02.
**Branch.** `main` (cycle work direct on main per hardening-tier
expectation; commit forthcoming).

## 1. Workstream shipped

| W-id | Status | Detail |
|---|---|---|
| W-GARMIN-MANIFEST-SIGNAL | **closed-this-cycle** | `hai capabilities --json` exposes per-choice metadata under `flags[].choice_metadata`; `hai pull` + `hai daily` `--source` flag both carry `garmin_live -> {reliability: "unreliable", reason: "rate-limited / Cloudflare-blocked (HTTP 429 / 403)", prefer_instead: "intervals_icu"}`. `_resolve_pull_source` emits a single stderr line warning when the resolved source is `garmin_live` (catches programmatic callers that bypass the manifest). 15 new tests across 2 new files. Schema add is purely additive — manifest `schema_version` unchanged. |

**Closed-this-cycle: 1.** **Partial-closure: 0.** **Deferred: 0.**

## 2. Quality gates

### 2.1 Test surface

| Gate | Target | Result |
|---|---|---|
| Pytest narrow | ≥ 2566 (v0.1.14 baseline) | **2581 passed, 3 skipped, 0 failed** (+15 new tests) |
| Pytest broader (`-W error::Warning`) | clean | **2581 passed, 3 skipped, 0 failed, 0 errors** |
| Mypy | 0 errors | **0 errors @ 127 source files** |
| Bandit -ll | 0 Med/High | **46 Low / 0 Medium / 0 High** (unchanged from v0.1.14 baseline) |
| Ruff (modified files) | clean | **All checks passed** on `cli.py`, `walker.py`, capabilities `__init__.py`, both new tests, modified flags-contract test |

Pre-existing ruff findings in *other* files (177 across the repo per
`uvx ruff check src/health_agent_infra verification/tests`) are
out-of-scope for this hardening cycle and pre-date the change.

### 2.2 Capabilities byte-stability

`verification/tests/snapshots/cli_capabilities_v0_1_13.json`
regenerated. Diff is purely additive: two flag entries
(`hai pull --source` and `hai daily --source`) gain a
`choice_metadata` key with the garmin_live unreliability block.
Schema version unchanged (`agent_cli_contract.v1`).

`reporting/docs/agent_cli_contract.md` regenerated; visible diff is
the `hai 0.1.14 → 0.1.14.1` version bump in the trailer line. The
markdown view does not render flag-level detail (per its own
"per-command structured detail lives in the JSON manifest"
disclaimer), so the structural signal is JSON-only by design.

### 2.3 Manual probes

```bash
# Manifest carries the structured signal
$ uv run hai capabilities --json | jq '.commands[] | select(.command == "hai pull").flags[] | select(.name == "--source").choice_metadata'
{
  "garmin_live": {
    "prefer_instead": "intervals_icu",
    "reason": "rate-limited / Cloudflare-blocked (HTTP 429 / 403)",
    "reliability": "unreliable"
  }
}

# Stderr warning fires (regardless of upstream success/failure)
$ uv run hai pull --source garmin_live
WARN [hai pull]: Garmin live is rate-limited and frequently fails ...
mobile+cffi returned 429: Mobile login returned 429 — IP rate limited by Garmin
[...]

# intervals.icu pulls cleanly with no warning
$ uv run hai pull --source intervals_icu
{
  "as_of_date": "2026-05-02",
  ...
}
```

## 3. Files changed

| File | Change |
|---|---|
| `src/health_agent_infra/core/capabilities/walker.py` | + `RELIABILITY_VALUES` enum, `annotate_choice_metadata` helper, walker round-tripping into `flags[].choice_metadata` |
| `src/health_agent_infra/core/capabilities/__init__.py` | re-export `RELIABILITY_VALUES` + `annotate_choice_metadata` |
| `src/health_agent_infra/cli.py` | + `PULL_SOURCE_CHOICE_METADATA` constant, `_GARMIN_LIVE_WARNING` constant, stderr warning in `_resolve_pull_source`, `annotate_choice_metadata` calls on both `--source` add sites (`hai pull`, `hai daily`) |
| `verification/tests/test_capabilities_choice_metadata.py` | new — 9 tests |
| `verification/tests/test_pull_garmin_live_warning.py` | new — 6 tests |
| `verification/tests/test_capabilities_flags_contract.py` | recognise `choice_metadata` as optional schema key |
| `verification/tests/snapshots/cli_capabilities_v0_1_13.json` | regenerated (additive) |
| `reporting/docs/agent_cli_contract.md` | regenerated (version-line diff only) |
| `pyproject.toml` | version 0.1.14 → 0.1.14.1 |
| `CHANGELOG.md` | new 0.1.14.1 section |
| `AGENTS.md` | "Settled Decisions" Garmin bullet extended with structured-signal pointer |

## 4. Out-of-scope items (named for the audit-chain)

The following were considered and explicitly deferred:

- **Hard CLI gate** (refuse `--source garmin_live` unless an explicit
  `--accept-unreliable-source` flag is passed). Deferred per PLAN.md
  §1 "Out-of-scope". Punishes users who knew what they were doing for
  zero structural gain over the manifest signal + runtime warning.
- **Removal of `garmin_live` as a `--source` choice.** Hard breaking
  change; not warranted by the trap shape.
- **Retry-policy change to garminconnect login flow.** Upstream
  library, not ours to fix.
- **`reliability` enum extensions** (e.g. `"deprecated"`,
  `"requires-confirm"`). Land additively when a real use case
  appears; v0.1.14.1 ships `reliable` / `unreliable` only.
- **`choice_metadata` for `--source` flags on intake commands**
  (`hai intake nutrition --source`, etc.). Those carry semantically
  different values (`user_authored`, `agent_proposed`) unrelated to
  pull-source reliability.

## 5. Audit chain

### D14 plan-audit
Single-round target per hardening-tier expectation. PLAN.md §3
declared this; PLAN.md §6 explained the why-now rationale. Plan-
audit prompt drafted as
`reporting/plans/v0_1_14_1/codex_plan_audit_prompt.md` (forthcoming
in next commit) — single round target.

### Codex implementation review
Single-round `SHIP` or `SHIP_WITH_NOTES` target per hardening-tier.
IR prompt forthcoming.

### Phase 0 (D11)
Abbreviated to internal sweep only. The trap is fully characterised
by the 2026-05-02 incident transcript; no exploration phase needed.
No persona matrix; no Codex external bug-hunt.

## 6. Ship-time freshness checklist (AGENTS.md A8)

- [x] `ROADMAP.md` "Now" — v0.1.14 still shipped, v0.1.15 still next;
  hardening cycle does not move the substantive cadence.
- [x] `AUDIT.md` — entry forthcoming on close (round table + verdict).
- [x] `README.md` — no Now/Next change required (hardening doesn't
  reshape product surface).
- [x] `HYPOTHESES.md` — unchanged.
- [x] `reporting/plans/README.md` — entry forthcoming on close.
- [x] `reporting/plans/tactical_plan_v0_1_x.md` — no v0.1.15 row
  change (this hardening sits between v0.1.14 and v0.1.15).
- [x] `success_framework_v1.md` / `risks_and_open_questions.md` — no
  change implicated.

## 7. Ship gate

Cycle ships when ALL of:

1. ✅ Test surface green at the gates above.
2. ✅ `hai capabilities --json` regenerated and committed.
3. ✅ Stderr warning verified to fire in manual probe.
4. ✅ CHANGELOG + AGENTS.md updated.
5. **Pending:** Codex IR returns `SHIP` or `SHIP_WITH_NOTES`.
6. **Pending:** Maintainer commits version bump and runs `twine upload`.
