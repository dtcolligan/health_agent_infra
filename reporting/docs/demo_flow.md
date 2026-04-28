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
- **§ B — Blank-demo flow** (canonical when W-Vb has deferred):
  `hai demo start --blank` opens an empty scratch session; the
  demo scripts manual-seed sequence to populate enough state for
  `hai today` to render.

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

Without W-Vb, the scratch root has no history. Seed enough
state for `hai today` to render:

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

### 5. Synthesise

```bash
hai daily --skip-pull --source csv
```

`--skip-pull` because there's no wearable data in a blank session;
`--source csv` is also forced under the demo refusal matrix even
if you specified another source.

### 6. Walk the plan

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

### 7. Same-day correction

If today's nutrition is partial, log the dinner correction:

```bash
hai intake nutrition \
    --calories 2900 --protein-g 175 --carbs-g 320 --fat-g 95
```

Re-run synthesis:

```bash
hai daily --skip-pull --source csv
```

W-E's state-fingerprint primitive auto-supersedes the canonical
plan with `_v2` because the inputs changed. Both rows persist;
audit chain integrity is preserved (W-F), `hai explain
--plan-version all` walks the chain.

### 8. Try `hai daily --supersede` on the next day

```bash
hai daily --supersede --as-of <tomorrow> --skip-pull --source csv
# rejected: --supersede requires an existing canonical plan for
# (<tomorrow>, u_local_1); none found ...
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
- **CLI flag harmonisation** (W-Y) — `--as-of` works on every
  civil-date subcommand.
- **Capabilities exposure** (W-S) — agents read proposal
  contracts from the manifest.
