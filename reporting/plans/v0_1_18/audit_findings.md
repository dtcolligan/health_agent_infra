# v0.1.18 — pre-PLAN audit findings

This file accumulates Phase 0 (D11) findings as they surface, plus
any pre-cycle observations that should be visible to PLAN.md
authoring. Per AGENTS.md "Pre-PLAN bug hunt" pattern, items here
are tagged with a `cycle_impact` disposition that the
pre-implementation gate (D11) consumes.

Status: **Phase 0 (D11) bug-hunt active 2026-05-06**. PLAN.md authored 2026-05-06; D14 closed at round 2 (R1 7 findings + R2 3 findings, all close-in-place). Phase 0 findings append below F-OB-PRE-01.

---

## F-OB-PRE-01 — `hai intake` handlers don't auto-apply pending migrations

**Surfaced.** 2026-05-05 evening, maintainer's own state DB.
Maintainer upgraded the wheel to v0.1.17 (which adds migration 026
for the new `body_comp` table) without running `hai init`, then
issued `hai intake weight --kg 82.0 ...`. Result:

```
hai: internal error (OperationalError): no such table: body_comp
```

Other intake handlers (`stress`, `nutrition`, `note`) wrote fine on
the same DB on the same call cycle — they don't touch the
v0.1.17-added table.

**Workaround that worked.** `hai init --skip-skills` is the
documented idempotent upgrade path. Output showed
`schema_version_before: 25 → applied_migrations: [026_body_comp.sql]`.
The weight write then succeeded.

**Why this matters for v0.1.18.** v0.1.18's thesis is that the
**install → first-plan path is the easy path, not the buried `--guided`
flag**. A user upgrading via `pip install --upgrade health-agent-infra`
on an existing `~/.local/share/health_agent_infra/state.db` who runs
any post-W-B intake command on an old schema head will hit
`OperationalError: no such table: body_comp` with no actionable hint
pointing them at `hai init`. That's exactly the failure-mode class
v0.1.18 is supposed to catch — install/upgrade ergonomics — and it's
likely to surface in v0.1.18 W-OB-4 (self-onboard dogfood pass)
unless absorbed proactively.

**Likely fix shape.** Every intake handler should call the same
connect-and-migrate seam used by `hai daily` / `hai today` (which
do not exhibit the bug because they go through a different connect
path that runs pending migrations on open). The fix surface is
finite: each handler module under `cli/handlers/` is a discrete
file post-W-29 split, and a shared connect helper would centralise
the seam. The right place may live next to whatever `hai daily`
already calls — bug investigation will localise it.

**`cycle_impact` tag.** `revises-scope` candidate. Two reasonable
absorption paths:

- **Absorb into a new W-OB-7** (intake-handler migration parity) as
  a discrete fix — cleanest scope, uses the W-29 module split as
  the natural seam edit surface.
- **Absorb into W-OB-5** (`hai doctor onboarding_readiness`
  actionability) — surface a "schema-head-behind-package" warning
  with a `next_action: hai init --skip-skills` field, treating the
  bug as primarily a discoverability gap.

Both have merit; the maintainer's W-OB-3/W-OB-4 dogfood pass should
inform the choice. If the dogfood pass surfaces additional intake-
handler-class issues, the W-OB-7 path becomes more attractive (one
fix surface for a class of bugs). If it doesn't, W-OB-5 is the lighter
absorption.

**`cycle_impact` if the cycle opens with this unaddressed.**
The W-OB-4 dogfood pass run on a clean `pipx` env will not surface
the bug (no prior schema state exists), only an upgrade-from-old-DB
session would. So: if the maintainer doesn't pre-stage an
upgrade-path scenario in the dogfood plan, this finding can fall
through the cracks — file it as W-OB-7 explicitly to ensure it
ships.

**Memory cross-reference.** Saved under
`~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_intake_handlers_dont_apply_migrations.md`
on 2026-05-05.

---

## F-PHASE0-01 — Existing init tests don't mock `sys.stdin.isatty()`

**Surfaced.** 2026-05-06 Phase 0 internal sweep, against HEAD `8e762c2`.

**Evidence.** `verification/tests/test_cli_init_doctor.py` (24 tests) and `verification/tests/test_init_onboarding_flow.py` (6 tests) both pass at HEAD (33 of 33 green; 3.56s). Neither file references `isatty`, `monkeypatch.*stdin`, or `sys.stdin` anywhere. They pass today because pytest stdin is not a TTY in normal CI/dev invocations — `isatty()` returns False, and W-OB-2's default-flip predicate never activates.

**Why this matters for v0.1.18.** After W-OB-2 lands, the bare `cmd_init` path will inspect `sys.stdin.isatty()` AND `check_onboarding_readiness` state. Existing tests that call `cmd_init` without `--guided`, without `--non-interactive`, and without authoring intent/target rows would behave differently in environments where stdin IS a TTY (e.g., a developer running `pytest` in an attached terminal without redirection). The default-flip would fire, the test would block on user input, and the suite would hang or time out.

**Likely fix shape.** Add a `conftest.py` autouse fixture (or per-test fixture) that either:
- sets `os.environ["HAI_INIT_NON_INTERACTIVE"] = "1"` for the test scope (simplest), OR
- monkeypatches `sys.stdin.isatty` to return `False` for the test scope (matches the pattern §2.B acceptance item 3 already names for the new W-OB-2 5-case test).

The PLAN's W-OB-2 §2.B already names monkeypatch discipline for the *new* default-flip test; F-PHASE0-01 surfaces that **existing init tests need the same treatment** to remain stable post-W-OB-2.

**`cycle_impact` tag.** `informational` — absorbs into W-OB-2 implementation discipline. Not a `revises-scope` finding because PLAN §2.B already acknowledges the monkeypatch pattern; this is enforcement scope, not contract scope. The W-OB-2 commit should land the conftest.py fixture in the same commit as the cmd_init logic change.

---

## F-PHASE0-02 — `core/doctor/checks.py` emits 16 hint strings; W-OB-5 production surface broader than acceptance test floor

**Surfaced.** 2026-05-06 Phase 0 internal sweep, against HEAD `8e762c2`.

**Evidence.** `grep -c '"hint":' src/health_agent_infra/core/doctor/checks.py` returns **16 hint emissions** across at least 6 distinct checks (`check_config`, `check_state_db`, `check_skills`, `check_today`, `check_intake_gaps`, `check_onboarding_readiness`, plus the auth checks `check_auth_garmin` + `check_auth_intervals_icu`). PLAN §2.E acceptance item 1 says W-OB-5 adds `next_action` to "every doctor check that emits `hint` today, where the hint maps to a concrete command (vs prose)." Acceptance item 6 names a **minimum** test floor of three checks (`onboarding_readiness`, `state_db`, `check_auth_intervals_icu`).

**Why this matters for v0.1.18.** The PLAN effort estimate (W-OB-5 at 0.5-1 day) is sized for the test surface (3+ tests × 4 cases each = ~12 test cases). The **production code surface** is broader — at least 5 hint-emitting checks need a `next_action` companion field per the acceptance contract. Most of the 16 hints DO map to concrete commands (`hai init`, `hai state init`, `hai state migrate`, `hai config init`, `hai setup-skills`, `hai pull`, `hai auth ...`), so most are in scope. A few prose-style hints ("re-run `hai doctor` after `hai state migrate`") are borderline.

**Likely fix shape.** W-OB-5 implementer enumerates all hint sites at implementation time, per-site decides "concrete command → emit `next_action`" vs "prose / instructional text → omit `next_action`." The maintainer ratifies any contested classifications. Effort holds at 0.5-1d if classification is mechanical.

**`cycle_impact` tag.** `informational` — absorbs into W-OB-5 implementation sizing. Not a `revises-scope` finding because PLAN §2.E acceptance item 1 already names the broader scope ("every check that emits `hint` today"); F-PHASE0-02 surfaces that the test-floor minimum (item 6) is narrower than the production surface, which is already coherent with PLAN intent. Effort estimate stands.

---

## F-PHASE0-03 — Pre-implementation baseline (informational, not a finding)

**Surfaced.** 2026-05-06 Phase 0 internal sweep, against HEAD `8e762c2`.

**Baseline measurements:**

| Surface | Pre-impl value | IR comparison anchor |
|---|---|---|
| `hai capabilities --json` `hai_version` | `0.1.17` | Becomes `0.1.18` post-impl |
| `hai capabilities --json` command count | `67` | Stays at `67` (W-OB-2 adds a flag, not a command; W-OB-5 adds runtime field, not manifest entry) |
| `hai init` flags | `--thresholds-path, --db-path, --skills-dest, --skip-skills, --force, --with-auth, --with-first-pull, --history-days, --user-id, --guided` (10 flags) | W-OB-2 adds `--non-interactive` → 11 flags |
| 13-persona matrix (`HAI_RUN_PERSONA_MATRIX=1`) | 13/13 reach `synthesized` cleanly; **0 findings, 0 crashes** | v0.1.18 doesn't change classifiers/policy → expect identical post-impl matrix output (any drift is a regression) |
| Init/doctor test surface | 33/33 passed in 3.56s | W-OB-2 + W-OB-5 add new test cases; existing tests must continue to pass |
| Full suite (broader warning gate) | **2688 passed, 5 skipped** in 80.69s under `-W error::Warning` | W-OB-2/3/5/7 commits must keep this clean; +5 expected new tests (cli_init_default_flip, doctor_next_action × 3 cases, intake_migration_parity, intake_weight_on_pre_v0_1_17_db) |
| Schema head | `26` (v0.1.17 `body_comp`) | Unchanged — no schema additions in v0.1.18 |

**`cycle_impact` tag.** `informational` (not a finding) — establishes the IR comparison anchor for v0.1.18 ship.

---

## How to add a finding to this file

1. Number sequentially (`F-OB-PRE-NN`).
2. Include a short title summarising the failure mode in one line.
3. Sections: **Surfaced** (when/where), **Workaround** (if any),
   **Why this matters for v0.1.18** (the cycle thesis lens),
   **Likely fix shape** (informed guess, not committed scope),
   **`cycle_impact` tag** (`absorbs-into-WS` / `revises-scope` /
   `aborts-cycle` / `informational`).
4. If the finding has a memory file, cross-reference its path.
