# Codex Plan Audit Round 3 Response — v0.1.11 PLAN.md

**Verdict:** PLAN_COHERENT_WITH_REVISIONS — the round-2 design
decisions are coherent in the detailed workstream sections, but the
final structure still has stale summary, acceptance, sequencing, and
ship-gate clauses. These are targeted propagation edits; no new
maintainer decision appears necessary.

**Round:** 3

## Findings

### F-PLAN-R3-01. W-Vb deferral path is fixed in W-Z detail but stale in catalogue and sequencing

**Q-bucket:** Q2 / Q7  
**Severity:** dependency-error / nit  
**Reference:** PLAN.md lines 92, 764-766, 1018-1067, 1086-1096,
1216-1221

**Argument:** The detailed W-Z section now has the right two-variant
shape: W-Va is required for both flows, W-Vb is required only for the
full persona flow, and the blank-demo flow is canonical when W-Vb
defers. The ship gate also accepts either 20 shipped workstreams or 19
with W-Vb deferred. But the workstream catalogue still says W-Z
"hard-deps on W-Va + W-Vb", W-Vb still "hard-precedes W-Z", and the
sequencing list still says W-Z hard-deps on W-Va + W-Vb and the demo
gate replays `hai demo start --persona p1`.

**Recommended response:** Propagate the two-variant contract to all
summary/sequencing rows:

- W-Z catalogue: "requires W-Va; W-Vb required only for § A full
  persona flow; § B blank-demo flow ships if W-Vb defers."
- W-Vb sequencing: "hard-precedes W-Z § A only."
- Sequencing item #18: "W-Z hard-deps on W-Va; conditionally uses
  W-Vb for § A."
- Demo gate item #20: name persona-replay vs isolation-replay mode
  instead of only `hai demo start --persona p1`.

### F-PLAN-R3-02. Archive-outside-real-tree invariant still has stale and unguarded clauses

**Q-bucket:** Q4 / Q5  
**Severity:** hidden-coupling / acceptance-criterion-weak  
**Reference:** PLAN.md lines 715-725, 754-759, 1121-1125

**Argument:** W-Vb's approach correctly moves archives outside the
real `~/.health_agent` tree, but W-Vb acceptance still says the
archive lands at `~/.health_agent/demo_archives/...`. The demo
regression gate also says it excludes `demo_archives/` because
archives live outside the real tree, which is internally confusing.
One edge remains: `$XDG_CACHE_HOME/hai/demo_archives/...` is only
outside the real tree if the configured `XDG_CACHE_HOME` is not under
`~/.health_agent`. The plan claims the invariant holds "under any
configuration" but does not require a resolved-path guard.

**Recommended response:** Update W-Vb acceptance to the new archive
root. Add an explicit implementation/test clause: after resolving the
archive root, assert it is not under the real base dir; if it is,
fallback to `/tmp/hai_demo_archives/...` or refuse with USER_INPUT.
Then simplify the demo gate to assert the real `~/.health_agent` tree
is byte-identical and separately assert the archive root is outside
that tree.

### F-PLAN-R3-03. Top-level capabilities ship gate still uses frozen-schema wording

**Q-bucket:** Q6  
**Severity:** settled-decision-integrity / nit  
**Reference:** PLAN.md lines 480-502, 1163-1164

**Argument:** W-S acceptance now has the correct F-PLAN-R2-05 wording:
capabilities output must be deterministic, expected additive content
must be present, and there is no frozen-schema check. The top-level
ship gate still says `hai capabilities --json` regenerates "without
diff against manifest schema", which is the exact stale wording round
2 asked to remove.

**Recommended response:** Replace the top-level ship gate with the
W-S wording or a pointer to it, e.g. "capabilities JSON and generated
markdown are deterministic; expected additive W-S/W-Va/W-W/W-X/W-Y
content is present; no frozen-schema check per W30."

## Open questions for maintainer

None. The remaining work is propagation/wording plus one archive-root
guard required by the already-chosen "real tree never mutates" invariant.

