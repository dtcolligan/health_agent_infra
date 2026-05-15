# Demo flow

Repeatable end-to-end demo of the `hai` CLI. **Authored 2026-04-28
(v0.1.11 W-Z).** This doc is the canonical script for showing the
system to a third party without polluting the maintainer's real
state.

W-Z has two sections:

- **§ A — Full persona-replay flow** (canonical when W-Vb has
  shipped): `hai demo start --persona p1` pre-populates 14 days
  of synthetic history; the demo walks through reading + reviewing
  + correcting against that history.
- **§ B — Blank-demo flow (boundary-stop demo)** (canonical when
  W-Vb has deferred): `hai demo start --blank` opens an empty
  scratch session; the demo scripts a manual-seed sequence and
  stops at the runtime/skill boundary (`hai daily` returns
  `awaiting_proposals`; `hai today` shows "no plan"). Path (a)
  narrates the boundary as the demo moment. Path (b) optionally
  seeds proposals to demonstrate downstream contracts (synthesis,
  `_v2` auto-supersede, W-F refusal); path (b) requires authoring
  proposal JSONs by hand and is forward-compat to v0.1.12 W-Vb
  when the persona fixture loader pre-populates them.

**v0.1.11 ships § B as canonical.** W-Vb (persona fixture loading +
archive + cleanup polish) is deferred to v0.1.12 per the named-
defer ship-gate. § A is documented here as forward-compat
preview; the snippets work once W-Vb lands.

---

## § B — Blank-demo flow (canonical for v0.1.11)

Every command in this section runs against the demo scratch root.
**No real state is mutated.** W-Va's multi-resolver isolation +
fail-closed marker contract guarantees this.

### 1. Open a demo session

```bash
hai demo start --blank
```

Output (stderr + stdout):

```
[demo session opened — marker_id demo_<ts>_<hex>, scratch root
 /tmp/hai_demo_<id>/]
{
  "status": "started",
  "schema_version": "demo_marker.v1",
  "marker_id": "demo_<ts>_<hex>",
  "scratch_root": "/tmp/hai_demo_<id>/",
  "db_path": "/tmp/hai_demo_<id>/state.db",
  "base_dir_path": "/tmp/hai_demo_<id>/health_agent_root/",
  "config_path": "/tmp/hai_demo_<id>/config/thresholds.toml",
  "persona": null,
  "started_at": "2026-04-28T13:00:00+00:00"
}
```

Every subsequent CLI invocation in this terminal will route to
the scratch root and print a one-line stderr banner. Real
`~/.health_agent`, real `state.db`, real `thresholds.toml`
remain byte-identical for the duration.

### 2. Pre-flight check

```bash
hai doctor --deep
```

In demo mode, `--deep` routes to a fixture-stub probe (W-X) — no
network call. The default stub returns 200-OK. The output
demonstrates the diagnostic-trust feature:

> *"the doctor probes the live API surface, surfaces broken
> credentials. In real mode, a 403 from intervals.icu would flip
> the row to `fail` even though the credential is present."*

### 3. Capabilities recap (the refusal posture)

```bash
hai capabilities --json | jq '.commands | length'
```

Then walk through the most-distinctive commands: `propose` (only
through the validator), `intent commit` (refused without explicit
user gate, W57), `intake *` (typed shape per domain).

In-character framing for the viewer:

> *"This system makes daily recommendations over user-authored
> intent. It doesn't generate the intent. It refuses operations
> that would deactivate authored state without an explicit
> commit. It refuses clinical claims. Nutrition is macros-only in
> v1. Watch what happens when I try to override these."*

Try `hai auth garmin` and watch the demo refusal:

```bash
hai auth garmin
# refused under demo session [credentials]: hai auth garmin touches
# the OS keyring and is refused while a demo session is active.
```

Try `hai pull --source intervals_icu`:

```bash
hai pull --source intervals_icu
# refused under demo session [network]: hai pull --source intervals_icu
# is a live network call and is refused while a demo session is
# active. Use --source csv...
```

### 4. Manual seed for "today's" state

Without W-Vb, the scratch root has no proposals. The intakes
below seed accepted-state rows; **they do NOT trigger a
populated `hai today`** — the runtime/skill boundary (proposal
authoring) sits between intake and synthesis. Path (a) narrates
this stopping at the boundary; path (b) seeds proposals
afterward.

```bash
hai intake readiness \
    --soreness low --energy moderate \
    --planned-session-type easy

hai intake gym \
    --session-id demo_today \
    --session-name "Demo upper" \
    --exercise "Bench Press" --set-number 1 \
    --weight-kg 80 --reps 5

hai intake nutrition \
    --calories 2400 --protein-g 150 --carbs-g 280 --fat-g 80
```

Each command prints the demo-session banner, mutates only the
scratch DB, and returns the structured JSON the agent would route.

### 5. Compose proposals (the runtime/agent boundary)

`hai daily` reads existing proposals from `proposal_log` and runs
synthesis over them; it does NOT fabricate proposals on its own.
In a real session, the agent composes proposals after consuming
the snapshot via the per-domain readiness skills, then posts each
via `hai propose --domain <d> --proposal-json <path>`.

For a CLI-only demo without an agent driving, you have two
options:

**(a) Stop here, narrate the boundary.** Run
`hai daily --skip-pull --source csv` and observe
`overall_status: "awaiting_proposals"`. The output explains what
the agent would do next:

```bash
hai daily --skip-pull --source csv
# overall_status: "awaiting_proposals"
# next: agent reads `hai state snapshot`, runs each domain's
#       readiness skill, posts via `hai propose --domain <d>
#       --proposal-json <path>`, re-runs `hai daily`.
```

This is the honest stopping point for a CLI-only demo. It
demonstrates the runtime/skill code-vs-skill boundary
(`AGENTS.md` "Code Vs Skill"): code runs synthesis once
proposals exist; skills compose proposals.

**(b) Manually seed proposals + synthesise.** Compose six
DomainProposal JSONs (one per domain), post via `hai propose`,
then re-run `hai daily`. The cycle's
`reporting/plans/v0_1_11/codex_implementation_review_response.md`
documents this path; it requires authoring six 30-line JSON
files matching each domain's
`<domain>_proposal.v1` schema. Consult
`hai capabilities --json | jq '.domain_proposal_contracts'` for
the per-domain action enum + required fields.

**v0.1.11 W-Z § B canonical stops at (a)**: the boundary
narration is the demo moment; full synthesis is a v0.1.12 W-Vb
deliverable when the persona-fixture loader pre-populates
proposals as part of `hai demo start --persona <name>`.

### 6. Walk the (partial) state — path (a)

```bash
hai today
```

In the canonical (a) stopping point, `hai today` reports
`No plan for <date>. Run \`hai daily\` first.` That's the
honest signal: no canonical plan committed yet because no
proposals were authored. The narration moment for the demo
viewer is **why** there's no plan — the runtime/skill boundary.

Skip to step 8 (`hai daily --supersede` on a fresh date)
which still demonstrates the W-F contract without requiring
proposals.

### 6b. Walk the plan — path (b) only

The remaining steps (6b, 7) require path (b)'s seeded proposals.
If you took path (a), skip to step 8.

```bash
hai today
```

Read each domain's recommendation aloud, naming the bands /
thresholds / R-rule firings the agent surfaced. Compare to the
"what would a generic AI coach say" framing — this system flags
spikes you can't feel, defers when sync is broken, escalates on
objective rules even with favourable subjective signals.

```bash
hai explain --as-of <today> --user-id u_local_1
```

The full audit-chain bundle: proposal → planned → committed →
narrated. Every band, every threshold, every R-rule firing
visible end-to-end.

### 7. Same-day correction — path (b) only

If today's nutrition is partial, log the dinner correction:

```bash
hai intake nutrition \
    --calories 2900 --protein-g 175 --carbs-g 320 --fat-g 95
```

Re-post each affected domain's proposal (the agent re-runs the
relevant readiness skill against the new state), then re-run
synthesis:

```bash
# Re-post nutrition proposal with the new payload.
hai propose --domain nutrition --proposal-json /tmp/p_nutrition.json

# Re-synthesise.
hai daily --skip-pull --source csv
```

W-E's state-fingerprint primitive auto-supersedes the canonical
plan with `_v2` because the inputs changed. Both rows persist;
audit chain integrity is preserved (W-F), `hai explain
--plan-version all` walks the chain.

### 8. `hai daily --supersede` on a fresh date — path (b) only

The W-F fresh-day-supersede USER_INPUT contract requires
proposals to exist for the date so synthesis is reached and
the `--supersede` gate can fire. **Without proposals**, daily
short-circuits at `awaiting_proposals` and the W-F gate never
runs — so this step demonstrates W-F only when path (b) has
seeded proposals.

If you took path (a), skip this step. The W-F contract is
independently verified by
`verification/tests/test_supersede_on_fresh_day.py` (3 tests).
The demo flow does not exercise it without proposal seeding.

If you took path (b):

```bash
# After seeding proposals + running daily for <today> →
# canonical plan minted; now try --supersede on a fresh
# tomorrow's date with no proposals authored for it:
hai daily --supersede --as-of <tomorrow> --skip-pull --source csv
# Note: short-circuits at awaiting_proposals before the W-F
# gate. To trigger the actual W-F refusal, seed tomorrow's
# proposals first; daily then reaches synthesis, the
# --supersede branch checks for tomorrow's canonical (none
# exists), and the gate raises USER_INPUT:
#   --supersede requires an existing canonical plan for
#   (<tomorrow>, u_local_1); none found ...
```

W-F's fresh-day refusal contract: `--supersede` is meaningless
without a canonical to supersede.

### 9. Close the demo session

```bash
hai demo end
```

Removes the marker; subsequent CLI invocations route to real
state. The scratch root is left on disk for inspection (W-Vb
will add archive-on-end behaviour to `/tmp/hai_demo_archives/`
or `$XDG_CACHE_HOME/hai/demo_archives/` outside the real tree).

---

## § A — Full persona-replay flow (forward-compat, deferred to v0.1.12)

Once W-Vb ships, replace step 1 of § B with:

```bash
hai demo start --persona p1_endurance_runner
```

The scratch root populates with 14 days of P1's synthetic history.
Steps 2-3 are the same. Step 4 (manual seed) is unnecessary —
`hai today` renders against the persona's pre-loaded history.
Step 5 onward is the same.

§ A's distinct demo moment:

> *"watch the system flag a volume spike on a real-looking
> training pattern."*

Per W-B (the volume-spike-coverage gate), spikes against a thin
denominator now yield rather than escalate. Persona fixtures with
sufficient sessions still trigger the spike rule for the
demo-relevant escalation.

---

## What the demo proves

End-to-end, the demo demonstrates:

- **Multi-resolver isolation** (W-Va) — real state untouched
  across an arbitrary number of demo CLI invocations.
- **Fail-closed marker** (W-Va, F-PLAN-03) — corrupt-marker tests
  refuse with USER_INPUT, not silent fall-through.
- **Refusal matrix** (W-Va) — network, credentials, operator
  paths all refuse under the demo session.
- **Diagnostic trust** (W-X) — `--deep` is a fixture stub in
  demo mode, hard-no-network-asserted.
- **State-fingerprint supersession** (W-E) — re-run with same
  state is no-op; with different state auto-supersedes.
- **Fresh-day supersede refusal** (W-F) — `--supersede` without
  a canonical exits USER_INPUT.
- **Gaps state-snapshot fallback** (W-W) — derives gaps without
  fresh wearable evidence; row-level read consistency.
- **Volume-spike coverage gate** (W-B) — sparse-history users
  no longer over-escalated.
- **CLI flag harmonisation** (W-Y) — `--as-of` works on the main
  civil-date planning/read surfaces; `hai pull` keeps its source-adapter
  `--date` flag.
- **Capabilities exposure** (W-S) — agents read proposal
  contracts from the manifest.
