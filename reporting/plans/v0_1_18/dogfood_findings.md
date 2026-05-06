# v0.1.18 Dogfood Findings — W-OB-4a + W-OB-4b

This file accumulates the maintainer-driven dogfood pass findings for
v0.1.18. Two passes per PLAN.md §2.D:

- **W-OB-4a (Phase 1, this section):** early-evidence pass against the
  W-OB-1 + W-OB-7-shipped tree, using a synthetic v0.1.16-shaped DB
  (schema head 25). Witnesses W-OB-7 fix in upgrade context. Output
  informs W-OB-3 prompt content review and may absorb into W-OB-5
  or W-OB-6.
- **W-OB-4b (Phase 2, separate section below — appended after
  W-OB-2 lands):** post-W-OB-2 local-wheel smoke proving the
  default-flip on interactive TTY.

---

# § W-OB-4a — Phase 1 upgrade-from-old-DB dogfood

**Run date:** 2026-05-06
**Run mode:** autonomous (Claude under maintainer ratification per
the cycle's end-to-end execution mandate)
**Tree state:** post-W-OB-1 + post-W-OB-7 commits in tree; W-OB-2
not yet landed (default-flip absent).

## Setup — constructing the synthetic schema-25 DB

Per OQ-3 priority-order disposition (from D14 R1), construction
order was option (b) hand-construct via `apply_pending_migrations`
filtered to versions ≤ 25. This is the lowest-fidelity option but
mechanically deterministic and reproducible — chosen over option
(a) (install v0.1.16 wheel + run `hai init`) because v0.1.16 was
cancelled and is not on PyPI; and over option (c) (snapshot
maintainer's pre-v0.1.17 DB) because no recoverable snapshot was
captured at the v0.1.17 ship boundary.

Construction command:

```python
from health_agent_infra.core.state import open_connection, apply_pending_migrations
from health_agent_infra.core.state.store import discover_migrations

all_m = discover_migrations()
pre_v0_1_17 = [m for m in all_m if m[0] <= 25]
conn = open_connection(db_path)
apply_pending_migrations(conn, migrations=pre_v0_1_17)
# DB now at schema head 25 (pre-W-B body_comp); package head is 26.
conn.close()
```

This matches the F-OB-PRE-01 surface — DB exists, has the projector
+ target tables from v0.1.15, but is missing migration 026's
`body_comp` table.

## Scenario sequence

Each command was run against the schema-25 DB with `--db-path`
pointing at the synthetic state. Real-life user equivalent: someone
who upgraded the wheel from v0.1.16 → v0.1.18 without re-running
`hai init`.

### Step 1 — `hai intake weight` (the F-OB-PRE-01 reproducer)

```bash
hai intake weight --kg 84.0 --as-of 2026-05-06 --user-id u_dogfood \
  --db-path "$DB_PATH" --base-dir "$BASE_DIR"
```

**Result:** ✅ SUCCESS (post-W-OB-7 fix). JSON output returned with
`body_comp_id: bc_b640ca63a158`, `source: user_authored`. DB silently
auto-migrated from schema 25 → 26 via the new
`open_connection_with_migrations` seam. **Pre-fix this would have
crashed with `OperationalError: no such table: body_comp`.**

**Finding:** F-OB-PRE-01 closed in production via W-OB-7. End-to-end
witness — not just a unit test.

### Step 2 — `hai doctor` post-intake (state-DB now at head 26)

```bash
hai doctor --db-path "$DB_PATH"
```

**Result:** ✅ Overall WARN (expected — missing intent/target/wellness_pull
+ blocking intake gaps). Schema check reports `schema_version: 26,
head_version: 26, size_bytes: 512000`. Full check list:

| Check | Status | Note |
|---|---|---|
| `config` | OK | thresholds.toml found |
| `state_db` | OK | schema 26 = head |
| `auth_garmin` | OK | keyring source |
| `auth_intervals_icu` | OK | keyring source |
| `skills` | OK | 15 installed (14 packaged) |
| `domains` | OK | 6 domains present |
| `sources` | OK | "no sync history yet" |
| `today` | OK | `proposals: 0, recommendations: 0` (NB: shows `user_id: u_local_1` not the supplied `u_dogfood` — known existing behavior of the today check, NOT a v0.1.18 finding) |
| **`onboarding_readiness`** | **WARN** | `missing: intent, target, wellness_pull`; hint cites `hai intent training add-session` OR `hai intent sleep set-window` — see F-OB-4A-02 below |
| **`intake_gaps`** | **WARN** | 3 blocking gaps; each emits structured `intake_command` + `intake_args_template` fields — see F-OB-4A-01 below |

### Step 3 — `hai today` against unplanned day

```bash
hai today --db-path "$DB_PATH" --user-id u_dogfood
```

**Result:** ✅ Clean message: `"No plan for 2026-05-06. Run `hai
daily` first."` Helpful, terse, points to the right next command.

### Step 4 — `hai stats` against intake-only DB

```bash
hai stats --db-path "$DB_PATH" --user-id u_dogfood
```

**Result:** ✅ Renders cleanly: "(no successful syncs yet — run
`hai pull --live` or `hai daily`)" + "(no logged runs yet — `hai
daily` starts recording once the DB exists)". Hint structure good.

### Step 5 — `hai daily` on near-empty DB

```bash
hai daily --db-path "$DB_PATH" --base-dir "$BASE_DIR" \
  --user-id u_dogfood --as-of 2026-05-06
```

**Result:** ✅ `overall_status: awaiting_proposals`. Per-gap output
includes structured fields:
- `intake_command: "hai intake readiness"`
- `intake_args_template: "--soreness <low|moderate|high> --energy
  <low|moderate|high> --planned-session-type <str> ..."`
- `priority: 1`
- `field_description: "morning self-report: soreness (low | moderate
  | high), energy (low | moderate | high), and the session you're
  planning today..."`

This is **already exactly the shape W-OB-5's `next_action` will
emit for `hai doctor`** — see F-OB-4A-01 cross-cycle convention
finding.

### Step 6 — `hai intake readiness` to close one gap

```bash
hai intake readiness --soreness moderate --energy high \
  --planned-session-type easy_run --as-of 2026-05-06 \
  --user-id u_dogfood --db-path "$DB_PATH" --base-dir "$BASE_DIR"
```

**Result:** ✅ JSON returned with `submission_id`, JSONL audit path,
all expected fields. Migration-applying seam handled cleanly (the
readiness handler routes through `_project_readiness_submission_into_state`
helper which now uses `open_connection_with_migrations`).

---

## Findings

### F-OB-4A-01 — `hai daily` already emits structured `next_action`-shaped fields per gap; W-OB-5 should align convention

**Severity:** doctrine-alignment.
**`cycle_impact` tag:** `informational` (absorbs into W-OB-5 implementation discipline).

`hai daily` Phase 0 output emits per-gap entries with these fields:

- `intake_command` (the concrete CLI command to close the gap)
- `intake_args_template` (the flags + value placeholders)
- `priority` (numeric ordering)
- `field_description` (prose describing the missing data)

This is structurally identical to W-OB-5's planned `next_action`
schema (`command`, `purpose`, `agent_safe`, `interactive`). W-OB-5
implementation discipline: **mirror the `hai daily` field naming
where possible** so `hai doctor` and `hai daily` use a coherent
cross-cycle convention.

Concrete recommendation: W-OB-5's `next_action.command` aligns with
`hai daily`'s `intake_command`; the additional W-OB-5 fields
(`agent_safe`, `interactive`) are net-new but compatible additions.

### F-OB-4A-02 — `onboarding_readiness` hint structure favors per-component over umbrella

**Severity:** UX.
**`cycle_impact` tag:** `informational` (absorbs into W-OB-5 implementation discipline; possibly W-OB-3 if prompt-side mirroring helps).

`hai doctor onboarding_readiness` for the missing-intent case emits:

```
hint: no active intent rows — run `hai intent training add-session`
or `hai intent sleep set-window` to author a goal
```

For a fresh user (also missing target + wellness_pull, as the
dogfood DB is), the **umbrella** command is `hai init` (post-W-OB-2,
auto-promotes to `--guided` on TTY) or `hai init --guided` (pre-W-OB-2),
which authors intent + target + first pull all in one flow.

W-OB-5 implementation discipline: when `onboarding_readiness` reports
**multiple** missing fields (i.e. user hasn't initialized at all),
prefer the umbrella `hai init` command in `next_action`; only fall
back to per-component commands when one or two specific fields are
missing post-init. This matches the "easy path is the default"
thesis from PLAN §1.4.

W-OB-3 implementation discipline (cross-cutting): the `--guided` flow
itself should land at this same outcome — completing `--guided`
should leave `onboarding_readiness` at PASS, not WARN with leftover
gaps.

### F-OB-4A-03 — W-OB-7 fix verified end-to-end (positive finding)

**Severity:** none — this is a confirmation, not a defect.
**`cycle_impact` tag:** `informational`.

The synthetic schema-25 DB construction + `hai intake weight`
invocation reproduced exactly the F-OB-PRE-01 failure mode the
maintainer hit on 2026-05-05. Post-W-OB-7, the invocation succeeds.
DB silently auto-migrates to head 26. No user-visible disruption;
no crash; no instructions required from the user. This is the
"easy path" PLAN §1.4 thesis claims.

End-to-end witness through the CLI is stronger than the unit-test-
only witness (`test_intake_weight_on_pre_v0_1_17_db`). Both gates
hold.

### F-OB-4A-04 — No W-OB-6-class structural findings

**Severity:** none.
**`cycle_impact` tag:** `informational` per PLAN §2.F item 1.

The W-OB-4a dogfood scenario surfaced two doctrine-alignment findings
(F-OB-4A-01, F-OB-4A-02) that absorb cleanly into W-OB-5 implementation.
No missing CLI commands. No broken test paths. No documented behavior
diverging from implementation. No architectural blockers.

W-OB-6 conditional slot does not fire on W-OB-4a evidence. Whether
W-OB-4b surfaces W-OB-6-class findings will be determined when that
pass runs (post-W-OB-2 local-wheel smoke).

---

## W-OB-4a closure

**Verdict:** Phase 1 dogfood pass complete. No blockers; no
revises-scope findings; W-OB-7 fix end-to-end-validated.

**Routes for findings:**
- F-OB-4A-01 → W-OB-5 implementation discipline (cross-cycle field-naming convention).
- F-OB-4A-02 → W-OB-5 implementation discipline (umbrella-command preference for multi-missing-field case) + W-OB-3 cross-cutting (the `--guided` flow should leave onboarding at PASS).
- F-OB-4A-03 → no action; positive finding.
- F-OB-4A-04 → W-OB-6 does not fire on W-OB-4a evidence.

W-OB-3 + W-OB-5 implementation may now proceed informed by these findings.

---

# § W-OB-4b — Phase 2 post-W-OB-2 local-wheel smoke

(Pending. Authored after W-OB-2 lands.)
