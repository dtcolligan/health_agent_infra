# Codex Plan Audit Response - v0.1.12 PLAN.md

**Round:** 4  
**Reviewed artifact:** `reporting/plans/v0_1_12/PLAN.md` after
`codex_plan_audit_round_3_response_response.md`  
**Verdict:** `PLAN_COHERENT`

Round 4 found no blocking findings. The three round-3 findings were
accepted and propagated into the relevant PLAN sections without
introducing a new contradiction.

---

## Verification

### F-PLAN-R3-01 - W-N warning-gate commands

Resolved.

- W-N now separates the **audit command** from branch-specific
  **ship commands** (`PLAN.md:297-313`).
- The audit command is the v0.1.11-deferred broader target:
  `uv run pytest verification/tests -W error::Warning -q`
  (`PLAN.md:301-305`).
- The branch table now matches the top-level ship gate: full
  `-W error::Warning` for <= 80, sqlite3-only ResourceWarning for
  80-150, and v0.1.11 PytestUnraisableExceptionWarning for >150
  (`PLAN.md:309-313`, `PLAN.md:748`).
- Phase 0 now says to run the W-N audit command rather than a
  narrow-warning rerun (`PLAN.md:834-840`).

No remaining W-N gate contradiction found.

### F-PLAN-R3-02 - Capabilities manifest shape

Resolved.

- W-PRIV now checks the manifest through
  `.commands[] | select(.command == "hai auth remove")`
  (`PLAN.md:405-408`).
- W-FCC now checks the manifest through
  `.commands[] | select(.command == "hai today")`
  (`PLAN.md:490-494`).
- This matches the source schema: `commands` is an array of rows, and
  each row's full invocation string lives in the `command` field
  (`src/health_agent_infra/core/capabilities/walker.py:3-25`).

No remaining dict-keyed-by-command manifest assumption found in live
acceptance gates.

### F-PLAN-R3-03 - W-FBC multi-domain defer

Resolved.

- Section 1.3 names W-FBC-2 as the v0.1.13 destination for full
  multi-domain F-B-04 closure (`PLAN.md:89`).
- W-CARRY marks F-B-04 as partial closure in v0.1.12 and defers
  multi-domain closure to W-FBC-2 (`PLAN.md:159`).
- W-FBC acceptance now states the full multi-domain rollout defer
  unconditionally, with the per-domain fingerprint primitive only
  conditional on option B/C (`PLAN.md:475-480`).
- The risk register repeats the same partial-closure framing
  (`PLAN.md:780-790`).

No remaining claim that v0.1.12 fully closes F-B-04 found in operative
scope or acceptance text.

---

## CP Verdicts

| CP | Round-4 verdict | Note |
|---|---|---|
| CP1 | accept | Paired AGENTS.md W-29/W-30 edit is coherent. |
| CP2 | accept | Paired capabilities-freeze edit is coherent. |
| CP3 | accept | Tier self-application fallback is explicit. |
| CP4 | accept | Existing MCP row is extended, not falsely treated as absent; security gate is intact. |
| CP5 | accept | Single substantial v0.2.0 plus shadow-by-default judge remains coherent. |
| CP6 | accept | Proposal authored in v0.1.12; strategic-plan text applied in v0.1.13. |

---

## Residual Notes

These are not required revisions:

- `PLAN.md:3-5` still says D14 plan-audit is not yet opened. That is
  tolerable while this artifact is being authored; Dom can update the
  status banner when declaring the plan-audit closed.
- No tests were run for this audit round. This was a document/source
  coherence review only, per the plan-audit pattern.

The PLAN is coherent enough to open Phase 0 (D11) once Dom accepts this
round-4 verdict.
