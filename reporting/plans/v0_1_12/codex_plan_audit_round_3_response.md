# Codex Plan Audit Response - v0.1.12 PLAN.md

**Round:** 3  
**Reviewed artifact:** `reporting/plans/v0_1_12/PLAN.md` after
`codex_plan_audit_round_2_response_response.md`  
**Verdict:** `PLAN_COHERENT_WITH_REVISIONS`

Round 2's maintainer response landed the intended fixes. The original
R2 issues are materially resolved: W-Vb no longer combines persona replay
with `--blank`, W-PRIV now points at `core/pull/auth.py` and uses
`hai auth remove`, CP4 correctly extends the existing MCP row, and F-B-04
is now framed as partial closure with W-FBC-2 named for v0.1.13.

Round 3 found three smaller stale-propagation issues. They are not
strategic disagreements, but they still affect acceptance gates and should
be corrected before Phase 0 opens.

---

## Findings

### F-PLAN-R3-01 - W-N still has conflicting warning-gate commands inside the workstream

**Question bucket:** Q2 sequencing honesty, Q5 acceptance bite  
**Severity:** Medium-high

The top-level ship gate is now correctly conditional on the W-N fork
decision (`PLAN.md:737`). The W-N body still has stale unconditional
language:

- The workstream title is the broader `-W error::Warning` gate
  (`PLAN.md:281`), matching the v0.1.11 defer: `-W error::Warning`
  catch-all deferred to v0.1.12, with 47 ResourceWarning failures
  documented (`v0_1_11/RELEASE_PROOF.md:59-61`).
- But the W-N "CI gate" says it runs
  `uv run pytest verification/tests -W error::ResourceWarning -q`,
  and that exit 0 means "ship-gate green" (`PLAN.md:304-306`).
- The fallback ladder then allows three different branch outcomes:
  full broader gate for count <= 80, sqlite3-only ResourceWarning for
  80-150, and the old PytestUnraisableExceptionWarning gate for >150
  (`PLAN.md:315-325`).
- Phase 0 still says a "pytest narrow-warning re-run" confirms the
  47-site baseline (`PLAN.md:823-825`), but the v0.1.11 narrow gate was
  PytestUnraisableExceptionWarning; it does not confirm the
  ResourceWarning site count.

So the global ship gate is fixed, but the workstream body still names a
single unconditional CI command and calls it the ship gate. It also
oscillates between catch-all `Warning`, all `ResourceWarning`, sqlite3
ResourceWarning, and PytestUnraisableExceptionWarning without a single
branch table owning the command.

**Required revision:** make W-N define two things explicitly:

1. The audit command run at workstream start to count failures. If the
   deferred target is truly the v0.1.11 catch-all, this should be
   `uv run pytest verification/tests -W error::Warning -q`; if the
   target has been narrowed to ResourceWarning, rename the workstream
   and top-level gate accordingly.
2. The ship command for each fallback branch, matching `PLAN.md:737`.

Also replace the Phase 0 "pytest narrow-warning re-run" wording with
"run the W-N audit command" so it can actually confirm the 47-site
ResourceWarning baseline or surface drift.

### F-PLAN-R3-02 - Capabilities acceptance commands use the wrong JSON shape

**Question bucket:** Q5 acceptance bite  
**Severity:** Medium

Two acceptance checks index the capabilities manifest as if
`commands` were an object keyed by command string:

- W-PRIV: `hai capabilities --json | jq '.commands."hai auth remove"'`
  (`PLAN.md:402-403`).
- W-FCC: `hai capabilities --json | jq '.commands."hai today"'`
  (`PLAN.md:481-483`).

The manifest schema is a dict whose `commands` member is a list of rows,
not an object. `core/capabilities/walker.py:3-20` documents:

```json
{
  "commands": [
    {
      "command": "hai pull"
    }
  ]
}
```

and `core/capabilities/walker.py:23-25` says nested subcommands are
flattened into one row per leaf command, with the full invocation string
stored in the `command` field.

The PLAN's jq snippets therefore do not prove the intended row exists.
This is especially relevant because W-PRIV's new surface is a leaf
command and W-FCC's enum surface is attached to an existing command row.

**Required revision:** express these gates in the manifest's real shape,
for example:

```bash
hai capabilities --json | jq '.commands[] | select(.command == "hai auth remove")'
hai capabilities --json | jq '.commands[] | select(.command == "hai today")'
```

or avoid jq in the PLAN and state the acceptance as "the `commands[]`
array contains a row whose `command` field is ...".

### F-PLAN-R3-03 - W-FBC acceptance still makes the multi-domain defer conditional on option B/C

**Question bucket:** Q1 cycle-thesis coherence, Q5 acceptance bite  
**Severity:** Medium-low

The F-B-04 reclassification is mostly fixed:

- W-FBC-2 is named in section 1.3 as full multi-domain closure across
  all six domains (`PLAN.md:89`).
- W-CARRY marks F-B-04 as partial closure and defers multi-domain closure
  to W-FBC-2 (`PLAN.md:159`).
- The W-FBC body says multi-domain closure is named-deferred and that
  v0.1.12 does not claim full F-B-04 closure (`PLAN.md:421-425`).
- The risk register repeats that full multi-domain closure is deferred
  to W-FBC-2 (`PLAN.md:769-779`).

The acceptance section still says:

`Multi-domain rollout deferred to v0.1.13 W-FBC-2 if option B/C is chosen
and per-domain primitives are needed` (`PLAN.md:470-471`).

That conditional is stale. After round 2, full multi-domain closure is
deferred regardless of whether option A, B, or C is chosen. If option A
is chosen, the residual is still "implement and test the selected policy
across all six domains." If option B/C is chosen, the residual also
includes the per-domain fingerprint primitive.

**Required revision:** make the W-FBC acceptance line unconditional:

`Full multi-domain rollout is deferred to v0.1.13 W-FBC-2 for the chosen
policy; if option B/C is selected, W-FBC-2 also owns the per-domain
fingerprint primitive.`

---

## CP Quick Verdicts After Round 3

| CP | Round-3 verdict | Note |
|---|---|---|
| CP1 | accept | No remaining contradiction. |
| CP2 | accept | No remaining contradiction. |
| CP3 | accept | Self-application fallback remains explicit. |
| CP4 | accept | R2 provenance issue fixed; security gate remains intact. |
| CP5 | accept | Single substantial v0.2.0 plus shadow-by-default judge remains coherent. |
| CP6 | accept | Author-now / apply-at-v0.1.13 split remains coherent. |

---

## What Would Improve The Verdict

`PLAN_COHERENT` requires only local edits:

- W-N owns one audit command and one branch-specific ship command table,
  with Phase 0 wording aligned to the audit command.
- W-PRIV and W-FCC capabilities checks use the manifest's `commands[]`
  array shape.
- W-FBC acceptance states the multi-domain W-FBC-2 defer unconditionally,
  with only the per-domain fingerprint primitive conditional on option
  B/C.

No tests were run for this audit round; this was a document/source
coherence review only.
