# v0.1.9 backlog

> **Status.** Backlog after v0.1.9 hardening scope cut. Captures items
> deferred from v0.1.8 audit rounds plus roadmap items intentionally not
> closed by the B1-B8 hardening release.

---

## Items deferred from v0.1.8 Codex audits

### B1. Global threshold-runtime type hardening
**Source.** Codex round-4 audit § "New issues found in round 4" item 1.
**Severity.** should-fix.

**Summary.** R2-3 + R3-1 closed bool-as-number at the validator AND
the runtime resolver for `policy.review_summary` only. The same
class of bug exists wherever else the runtime reads numeric
threshold leaves via bare `int()` / `float()` — Codex named:
- `src/health_agent_infra/domains/nutrition/classify.py:99-100`
  (nutrition band thresholds via `float(cfg[...])`)
- `src/health_agent_infra/core/synthesis_policy.py:668, 872`
  (synthesis policy thresholds via bare `float()` / `int()`)

There may be other paths; a deliberate grep of `int(.*cfg\|float(.*cfg`
across `src/health_agent_infra/` is needed.

**Why deferred from v0.1.8.** `hai config validate` catches bools
by type when users explicitly run it, and the round-4 fix only
claimed the `policy.review_summary` runtime boundary. The bug
exists but is not a release-blocker.

**Proposed follow-up fix.** Centralise typed threshold access — either
(a) extract `_coerce_int` / `_coerce_float` from
`core/review/summary.py` into a shared `core/config/coerce.py`
module, OR (b) validate merged `DEFAULT_THRESHOLDS` leaves at
`load_thresholds` time so the config dict is already type-safe
before any consumer reads it. Option (b) catches *every* path
without per-site changes; option (a) is incremental.

### B2. Pytest unraisable warning cleanup
**Source.** Codex round-4 audit § "New issues found in round 4" item 2.
**Severity.** nit.

**Summary.** The full suite emits one
`PytestUnraisableExceptionWarning` from
`safety/tests/test_snapshot_bundle.py::test_snapshot_v1_0_recovery_block_has_three_keys`
("Exception ignored while finalizing file
`<http.client.HTTPResponse object>`"). Pre-existing, unrelated to
v0.1.8 work, doesn't affect pass/fail.

**Proposed follow-up fix.** Audit the test for HTTP-client lifecycle
(probably an unclosed response in an intervals.icu auth-check or
similar) and ensure the response is closed in a `finally` block
or `with` context.

---

## Roadmap items deferred past v0.1.9 hardening

Per `reporting/plans/multi_release_roadmap.md` § 4 v0.1.9 these were
roadmap-committed, but the 2026-04-26 hardening review cut v0.1.9 down
to B1-B8 only. These land after the hardening release:

- **W52: `hai review weekly`** — code-owned weekly aggregation
  across accepted state, intent, target, recommendation, X-rule
  firing, review outcome, data quality.
- **W53: Insight proposal ledger** — `insight_proposal` +
  `insight` tables with status (proposed/committed/rejected/archived).
- **W58: LLM-judge factuality gate for weekly review** — local
  Prometheus-2-7B pinned by SHA, agent-judge negotiation loop per
  Decision 1 (settled 2026-04-25).

See multi_release_roadmap.md § 4 v0.1.9 for the original goal / ships /
does-not-ship / acceptance. Do not mark these closed in the v0.1.9
release proof.

---

## How this file evolves

- New items get added as Codex audits land or as roadmap edits
  surface new candidates.
- When v0.1.9 cycle starts, this file's items get triaged into a
  formal `reporting/plans/v0_1_9/PLAN.md` (same pattern as
  v0.1.7 → v0.1.8).
- Items cut from v0.1.9 stay here with a "deferred to v0.2"
  note; do not silently delete them.
