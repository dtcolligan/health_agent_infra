# Maintainer Response — v0.1.11 Plan Audit Round 2

> **Authored 2026-04-28** by Claude in response to Codex's round 2
> verdict (`PLAN_COHERENT_WITH_REVISIONS`, 5 findings, 3 open
> questions).
>
> **Status.** Triage complete. 2 of 5 findings are pure
> tech/wording fixes (Claude applies autonomously). 3 of 5 findings
> need maintainer decisions before round-3 revisions land.

---

## 1. Triage summary

| Finding | Disposition | Owner |
|---|---|---|
| F-PLAN-R2-01 W-Vb deferral does not propagate to W-Z + demo gate | **Maintainer decision** | Dom answers Q-1 below |
| F-PLAN-R2-02 Default archive conflicts with byte-identical gate | **Maintainer decision** | Dom answers Q-2 below |
| F-PLAN-R2-03 `hai doctor --deep` refused and required in demo | **Maintainer decision** | Dom answers Q-3 below |
| F-PLAN-R2-04 W-W JSONL consistency rule drops valid old rows | **Accept-with-revision** (tech fix) | Claude applies |
| F-PLAN-R2-05 Capabilities ship gate reads as frozen-schema check | **Accept-with-revision** (wording fix) | Claude applies |

All five are real internal contradictions; round 1's revisions
were correct in direction but introduced second-order conflicts
that Codex caught. No disagreements with the audit on substance.

---

## 2. Per-finding response

### F-PLAN-R2-01 — W-Vb deferral propagation

**Maintainer decision required (Q-1 below).**

Codex is right: W-Vb is deferrable, but W-Z hard-deps on W-Vb,
the ship gate counts W-Z toward the 20 workstreams, and the demo
regression gate runs `hai demo start --persona ...` which is
W-Vb fixture scope. The deferral path is currently unexecutable.

**Two coherent branches:**

**(a) W-Vb deferrable; W-Z + regression gate degrade gracefully
when W-Vb defers.**

- W-Z: doc has two variants. Full version with `--persona p1`
  steps when W-Vb ships. Blank-demo version when W-Vb defers
  (uses `hai demo start --blank` and walks the user through
  manual `hai intake *` to seed scratch state). Both variants
  in the doc; opening section names which is canonical based on
  what shipped.
- Demo regression gate: two modes. Persona-replay (full) when
  W-Vb shipped; isolation-replay (W-Va only, blank demo + scripted
  intakes) when W-Vb deferred. Isolation-replay still asserts
  byte-identical real-state checksums and refusal-matrix bite.
- Ship gate count: 19 (without W-Vb) or 20 (with W-Vb), both
  acceptable per named-defer.

**(b) W-Vb non-deferrable.** Drop the deferrable status. W-Vb
must ship for the cycle to ship. Cleanest internally; loses the
"ship safely if cycle runs hot" property. Estimate hardens to
22-30 days with no give.

**Claude recommendation: (a).** Preserves the headroom property
that motivated the original deferral. The doc + gate degradation
is straightforward to author once W-Va lands. Loses some demo
richness on the deferred path, but the core safety invariant
(no real-state pollution) holds either way.

### F-PLAN-R2-02 — Default archive conflicts with byte-identical gate

**Maintainer decision required (Q-2 below).**

Codex is right: W-Vb's `hai demo end` archives by default into
`~/.health_agent/demo_archives/`, which violates the demo
regression gate's "real `~/.health_agent` tree byte-identical"
assertion. As written, the gate is self-failing.

**Three coherent branches:**

**(a) Archive lives outside the real tree.** Default archive
location moves from `~/.health_agent/demo_archives/` to
`/tmp/hai_demo_archives/` (or a path under `XDG_CACHE_HOME`,
which is platform-correct). Real `~/.health_agent` stays
byte-identical. Demo flow ends with `hai demo end` (default).

**(b) Demo flow always uses `--no-archive`.** Default
`hai demo end` keeps archive-by-default; the demo-flow doc and
regression gate explicitly close with `hai demo end --no-archive`.
The default is for real users post-session; demos opt out.

**(c) Checksum gate excludes `demo_archives/`.** Real tree
asserted byte-identical *except* for `demo_archives/`, which is
allowed to gain exactly one new entry (verified by listing diff).

**Claude recommendation: (a).** Cleanest invariant — real
`~/.health_agent` is *never* mutated by demo mode under any
configuration. Aligns with the broader "demo mode never touches
real persistence surfaces" thesis. Archive at
`/tmp/hai_demo_archives/<marker_id>__<persona>__<ended_at>/` (or
`$XDG_CACHE_HOME/hai/demo_archives/...` if set; falls back to
`/tmp/...` otherwise). User-facing message at archive time names
the path explicitly.

### F-PLAN-R2-03 — `hai doctor --deep` refused vs. required

**Maintainer decision required (Q-3 below).**

Codex is right: W-Va refuses `hai doctor --deep` (network probe)
in demo mode; W-X defines it as the live auth probe; W-Z and the
demo regression gate require it to identify a broken-auth state
from a persona fixture. As written, no implementation satisfies
both.

**Two coherent branches:**

**(a) Strict refusal in demo mode.** `hai doctor --deep` exits
USER_INPUT with no network call when a demo marker is active.
Demo regression gate asserts the refusal (not a probe success).
Demo-flow doc shows the refusal as a feature ("notice the system
refuses live network probes in demo mode").

**(b) Fixture-backed stub probe.** Demo mode allows
`hai doctor --deep` against a fixture probe surface (the persona
fixture stubs a `probe()` callable that returns a fixed status
without network). W-Va refusal matrix distinguishes "live probe"
(refused) from "demo-stub probe" (allowed). W-X tests assert the
stub path on demo-mode invocations and the live path on real-mode
invocations. The 403 stub demonstrates the diagnostic-trust
feature in the demo without leaking network calls.

**Claude recommendation: (b).** The whole reason W-X exists is
to surface the diagnostic-trust gap (doctor reports OK while API
403's). Demonstrating that *correctly catching* a 403 is the demo
moment; refusal-only loses the moment. The implementation cost is
one new code path (a `Probe` protocol with `LiveProbe` and
`FixtureProbe` implementations) which is a small, contained
design. Tests for both probes exist in W-X scope already; the
fixture stub is a small additional test fixture.

But (a) is defensible if you'd rather minimise W-Va surface.

### F-PLAN-R2-04 — W-W JSONL consistency drops valid old rows

**Accept-with-revision (tech fix; no maintainer input needed).**

Codex's argument is correct and the recommendation is the right
fix. File-mtime-based filter drops files that received an append
mid-derivation, including their pre-existing valid rows.

**Revision applied:**

W-W approach updated:

> 5. **Read-consistency contract (per Codex F-PLAN-06 +
>    F-PLAN-R2-04).** Snapshot-derived gaps run inside a single
>    read transaction over SQLite, with `as_of_read_ts:
>    <ISO-8601>` captured at transaction start. **JSONL tail
>    reads use a row-level `recorded_at` filter, not a file mtime
>    filter.** At transaction start, capture each tail file's
>    inode + size; subsequent reads iterate the captured byte
>    range and include only rows where the row's own
>    `recorded_at <= as_of_read_ts`. Files appended after
>    transaction start contribute nothing beyond the captured
>    byte range; files appended within the captured byte range
>    are filtered row-by-row. Concurrent writes during gap
>    derivation cannot mix old SQLite state with new
>    manual-tail rows, AND cannot drop valid pre-existing rows
>    that happen to be in a file that received an append.

W-W test surface gains a new test:

> `verification/tests/test_intake_gaps_jsonl_old_rows_kept.py`
> (new) — fixture: JSONL file already contains an old row
> recorded at T-1; transaction starts at T-0; new row appended
> at T+1; assert output includes the T-1 row, excludes the T+1
> row.

Files-changed list adds: the inode-and-byte-range capture helper
in `core/state/snapshot.py` (or wherever the JSONL tail reader
lives — enumerate during implementation).

### F-PLAN-R2-05 — Capabilities ship gate frozen-schema wording

**Accept-with-revision (wording fix; no maintainer input needed).**

Codex is right: the current wording ("regenerates without diff
against manifest schema") points implementers toward a
schema-freeze interpretation that contradicts W30.

**Revision applied:**

W-S § 2.12 ship gate, last bullet, current text:

> **Manifest JSON and generated markdown are updated; tests
> prove the additive `domain_proposal_contracts` top-level block
> does not require freezing `agent_cli_contract.v1` (W30 settled
> decision preserved).** Manifest-as-doc regenerator produces
> deterministic output (same input → byte-identical output
> across runs).

Replaced with:

> **Manifest JSON and regenerated markdown are deterministic
> across runs (same source state → byte-identical output).
> Expected additive rows/fields for W-S (`domain_proposal_contracts`),
> W-Va (`hai demo *` rows), W-W (`--from-state-snapshot` /
> `--allow-stale-snapshot` flags), W-X (`--deep` flag,
> `auth_*.probe` field), and W-Y (`--as-of` aliases on
> `hai pull` / `hai explain`) are all present and pass their
> per-W-id capabilities tests. **No frozen-schema check** —
> W30's "manifest schema not yet frozen" decision is preserved;
> the gate verifies presence of expected additive content and
> determinism, not closure of the schema.**

Same change applied to top-level § 3 ship-gate row that mirrored
the old wording.

---

## 3. Open questions for maintainer (3 decisions)

### Q-1 — F-PLAN-R2-01 — W-Vb deferral propagation path

**(a)** W-Vb deferrable; W-Z + demo regression gate degrade
gracefully (full version when W-Vb ships, blank version when
W-Vb defers). **Claude recommendation.**
**(b)** W-Vb non-deferrable. Drop the headroom property; cycle
hardens to 22-30 days with no give.

### Q-2 — F-PLAN-R2-02 — Demo archive location

**(a)** Archive outside real tree (default
`/tmp/hai_demo_archives/...` or `$XDG_CACHE_HOME/hai/...`).
**Claude recommendation.**
**(b)** Demo flow always uses `--no-archive`; default keeps
archive-by-default for real users.
**(c)** Checksum gate excludes `demo_archives/`; archive stays
inside real tree.

### Q-3 — F-PLAN-R2-03 — `hai doctor --deep` in demo mode

**(a)** Strict refusal; demo gate asserts the refusal.
**(b)** Fixture-backed stub probe with hard no-network
assertion; W-Va refusal matrix distinguishes live probe from
demo-stub probe. **Claude recommendation.**

---

## 4. Net cycle impact after R2 revisions

Negligible additional effort beyond what's already in the plan:

- F-PLAN-R2-04 fix: ~half-day additional test work in W-W
  (JSONL inode-and-byte-range capture + row-level filter test).
- F-PLAN-R2-05 fix: pure wording, zero implementation impact.

If Q-1 = (a): no estimate change; degradation paths are doc + gate
authoring (~half-day inside W-Z and the gate spec).
If Q-3 = (b): ~half-day additional implementation in W-X for the
`Probe` protocol split. ~quarter-day additional test work.

**Cycle estimate range:** still **22-30 days** (R2 fixes are inside
the headroom; no need to revise the upper bound).

---

## 5. Outstanding actions

Once Q-1 / Q-2 / Q-3 are answered:

1. Apply F-PLAN-R2-04 + F-PLAN-R2-05 (already-approved tech +
   wording fixes) to PLAN.md.
2. Apply Q-1 / Q-2 / Q-3 decisions to PLAN.md.
3. Send the same `codex_plan_audit_prompt.md` for round 3 to
   verify all R2 issues resolve cleanly.
4. If round 3 returns `PLAN_COHERENT`, cycle opens to Phase 0.
