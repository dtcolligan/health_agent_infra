# Maintainer Response — v0.1.11 Plan Audit Round 3

> **Authored 2026-04-28** by Claude in response to Codex's round 3
> verdict (`PLAN_COHERENT_WITH_REVISIONS`, 3 propagation findings,
> 0 maintainer decisions needed).
>
> **Status.** All 3 findings → accept-with-revision (Claude
> applied autonomously; no maintainer input required because
> Codex confirmed the round-2 design choices were correct in
> detail and only catalogue / acceptance / ship-gate clauses
> needed propagation).

---

## 1. Triage summary

| Finding | Disposition |
|---|---|
| F-PLAN-R3-01 W-Z deferral path stale in catalogue + sequencing | **Accept-with-revision** (propagation) |
| F-PLAN-R3-02 W-Vb acceptance archive path + missing resolved-path guard | **Accept-with-revision** (propagation + tightening) |
| F-PLAN-R3-03 Top-level capabilities ship gate frozen-schema wording | **Accept-with-revision** (wording) |

No disagreements. No maintainer decisions required.

---

## 2. Per-finding response

### F-PLAN-R3-01 — W-Z deferral propagation

**Accept.** Codex caught that the round-2 detailed §2.19 W-Z
contract correctly handled the W-Vb deferral with two variants,
but I missed propagating that to (a) the workstream catalogue
hard-deps line, (b) the W-Vb "hard-precedes W-Z" sequencing
note, (c) sequencing item #18, and (d) the demo gate naming at
sequencing item #20.

**Revisions applied:**
- Catalogue row for W-Z: "Requires W-Va; W-Vb required only for
  § A (full persona flow); § B (blank-demo flow) ships as
  canonical if W-Vb defers."
- W-Vb sequencing line: "Hard-precedes W-Z's § A only" — § B is
  independent of W-Vb.
- Sequencing item #18: W-Z hard-deps on W-Va; conditionally
  uses W-Vb for § A; § A annotated "deferred to v0.1.12" when
  W-Vb defers.
- Sequencing item #20: demo regression gate explicitly named
  in persona-replay vs isolation-replay modes.

### F-PLAN-R3-02 — Archive-outside-tree invariant tightened

**Accept.** Two stale clauses + one missing guard:

1. W-Vb acceptance still named `~/.health_agent/demo_archives/...`
   even though the approach correctly moved it out.
2. The XDG_CACHE_HOME path was claimed safe "under any
   configuration" but had no resolved-path guard against a user
   setting `XDG_CACHE_HOME=~/.health_agent/cache`.
3. The demo regression gate's exclusion clause for
   `demo_archives/` was internally confusing now that archives
   live outside the real tree (no exclusion needed).

**Revisions applied:**
- W-Vb step 3 (Archive on `hai demo end`): added explicit
  resolved-path guard. After resolving the archive root,
  compute the real path (resolving symlinks); assert it is not
  under the real base dir's real path. Falls back to
  `/tmp/hai_demo_archives/...` if XDG path lands inside; exits
  USER_INPUT if both candidates fail (e.g., exotic symlink
  topology).
- W-Vb acceptance: archive path corrected to the resolved
  candidate; resolved-path guard test added; real
  `~/.health_agent` checksum byte-identical asserted under
  every archive configuration.
- New test:
  `verification/tests/test_demo_archive_path_guard.py` covering
  XDG-under-real-tree fallback, both-candidates-fail USER_INPUT,
  and symlink edge cases (resolved real path, not lexical).
- Demo regression gate simplified: real-tree byte-identical
  check **without** any `demo_archives/` exclusion (since
  archives now live outside the real tree by construction);
  separate archive-root assertion using `os.path.commonpath`-
  style check on resolved real paths.

### F-PLAN-R3-03 — Top-level ship gate frozen-schema wording

**Accept.** I correctly updated the W-S §2.12 ship gate per
F-PLAN-R2-05 but missed the mirror in the top-level §3 ship
gates. Codex caught the stale wording.

**Revision applied:**
- §3 capabilities ship gate replaced with the W-S §2.12-aligned
  wording: "deterministic across runs; expected additive
  content present; no frozen-schema check (W30 preserved)."

---

## 3. Net cycle impact after R3 revisions

Negligible. All three are propagation/wording/test-addition;
no estimate change. Cycle still **22-30 days**.

The W-Vb resolved-path guard adds maybe ~1 hour to W-Vb
implementation (one helper, one test); fits inside the existing
2-3 day W-Vb sizing.

---

## 4. Outstanding actions

PLAN.md updated. Next step: send the same
`codex_plan_audit_prompt.md` for **round 4** to verify all R3
issues resolve cleanly. If round 4 returns `PLAN_COHERENT`,
cycle opens to Phase 0.

If round 4 surfaces a fourth round of revisions, that is
expected behaviour for the D14 pattern — the AGENTS.md note
already says "Multiple rounds are normal." We continue iterating
until the verdict is positive.
