# Codex Plan Audit Round 2 Response — v0.1.11 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS — the round-1 fixes mostly
landed, but the revised plan introduced second-order contradictions
around W-Vb deferral, demo regression, `doctor --deep` in demo mode,
and W-W read consistency. The cycle should not open to Phase 0 until
the named plan edits below are resolved.

**Round:** 2

## Findings

### F-PLAN-R2-01. W-Vb deferral does not propagate to W-Z and the demo gate

**Q-bucket:** Q2 / Q7  
**Severity:** dependency-error / plan-incoherence  
**Reference:** PLAN.md lines 667-670, 732-734, 954-958, 977-982,
1076-1081, 1088-1094

**Argument:** W-Vb is explicitly deferrable as a whole if the cycle
runs hot or W-P finds more than three correctness-class bugs. But W-Z
hard-deps on W-Vb, the ship gate lists W-Z among the 20 workstreams
expected to complete, and the demo regression gate runs
`hai demo start --persona ...`, which is W-Vb fixture scope. As
written, the plan says W-Vb can defer while still requiring a W-Z/demo
gate path that cannot run without W-Vb.

**Recommended response:** Choose one explicit branch:

- Make W-Vb non-deferrable if W-Z and the full demo regression gate
  are mandatory in v0.1.11.
- Or keep W-Vb deferrable and add a named W-Vb-deferred ship path:
  W-Z becomes either deferred with W-Vb or narrowed to a W-Va-only
  blank-demo guide; the demo regression gate runs a W-Va-only
  isolation replay instead of a persona-fixture replay.

Update §3 ship gates, §4 sequencing, and W-Z's hard-dependency text so
the deferral branch is executable.

### F-PLAN-R2-02. Default demo archive conflicts with the real-state checksum gate

**Q-bucket:** Q4 / Q5 / Q7  
**Severity:** hidden-coupling / acceptance-criterion-weak  
**Reference:** PLAN.md lines 650-653, 689-694, 940-950, 994-1003

**Argument:** W-Vb makes `hai demo end` archive the scratch root by
default into `~/.health_agent/demo_archives/...`, unless
`--no-archive` is passed. W-Z's demo flow ends with `hai demo end`,
and the demo regression gate requires the real `~/.health_agent` tree
to be byte-identical before and after. Those two requirements cannot
both pass once W-Vb archive-on-end exists.

**Recommended response:** Make the intended invariant explicit. Good
options:

- The demo-flow doc and regression gate close with
  `hai demo end --no-archive`.
- Or the archive writes outside the checksum-covered real tree.
- Or the checksum gate deliberately excludes `demo_archives/` and adds
  a separate assertion that the archive is the only real-tree delta.

Without one of those clauses, the demo regression gate is
self-failing.

### F-PLAN-R2-03. `hai doctor --deep` is both refused and required in demo mode

**Q-bucket:** Q4 / Q5  
**Severity:** hidden-coupling / acceptance-criterion-weak  
**Reference:** PLAN.md lines 585-589, 858-865, 940-944, 994-1006

**Argument:** W-Va's refusal matrix says `hai doctor --deep` is
refused in demo mode because it is a network probe. W-X defines
`hai doctor --deep` as the live auth probe. W-Z then includes
`hai doctor --deep` in the demo flow, and the demo regression gate
requires it to identify a broken-auth state from a persona fixture.
No implementation can satisfy both "refuse this command in demo" and
"run this command successfully in the demo replay."

**Recommended response:** Pick one contract:

- In demo mode, `hai doctor --deep` exits USER_INPUT with no network
  call, and the demo gate asserts that refusal.
- Or demo mode allows `hai doctor --deep` only against a fixture/stub
  probe surface with a hard no-network assertion, and W-Va's refusal
  matrix is updated to distinguish live probes from demo-stub probes.

Then update W-X tests and W-Z snippets to match the chosen contract.

### F-PLAN-R2-04. W-W's JSONL consistency rule can drop valid pre-existing rows

**Q-bucket:** Q4  
**Severity:** hidden-coupling  
**Reference:** PLAN.md lines 756-761, 773-782, 784-791, 815-822

**Argument:** The revised W-W contract correctly adds a single SQLite
read transaction, but manual intake JSONL tails are outside that
transaction. The plan says JSONL tail reads are bounded by
`as_of_read_ts` and "files-modified-after are ignored." That
file-level rule can drop valid old records if a file containing older
rows is appended during gap derivation, because the append changes the
file mtime after `as_of_read_ts`. Reading the file anyway can mix old
SQLite state with new manual-tail rows. The planned 100-trial
concurrency test will only be meaningful if the JSONL cutoff is
specified at record level or the source is moved fully inside SQLite.

**Recommended response:** Prefer deriving W-W from SQLite projected
state only, inside the single read transaction. If JSONL tails remain
part of the source, specify a stable read strategy: capture the file
snapshot at transaction start and filter records by per-row recorded
timestamp `<= as_of_read_ts`, not by whole-file mtime. Add a test
where a JSONL file already has an old row, receives a new append
during derivation, and the output keeps the old row while excluding
the new row.

### F-PLAN-R2-05. Capabilities ship gate still reads like a frozen-schema check

**Q-bucket:** Q6  
**Severity:** nit / settled-decision-integrity  
**Reference:** PLAN.md lines 419-487, 1023-1024

**Argument:** W-S now correctly frames `domain_proposal_contracts` as
an additive capabilities extension and preserves W30's "manifest
schema not frozen" decision. But the final ship gate still says
`hai capabilities --json` must regenerate "without diff against
manifest schema." That wording points implementers back toward a
schema-freeze interpretation.

**Recommended response:** Reword the gate to the actual intended
check: capabilities JSON and regenerated markdown are deterministic;
expected additive rows/fields for W-S, W-Va, W-W, W-X, and W-Y are
present; no accidental undocumented diff appears. Do not imply a
frozen manifest schema.

## Open questions for maintainer

1. If W-Vb defers, should W-Z and the full demo regression gate defer
   with it, or should v0.1.11 ship a W-Va-only demo path?
2. Are demo archives under `~/.health_agent/demo_archives/` considered
   acceptable real-tree output, or should the "no real-state pollution"
   invariant treat them as pollution unless explicitly requested?
3. In demo mode, should `hai doctor --deep` be a strict refusal or a
   fixture-backed no-network probe?

