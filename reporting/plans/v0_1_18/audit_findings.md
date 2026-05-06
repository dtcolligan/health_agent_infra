# v0.1.18 — pre-PLAN audit findings

This file accumulates Phase 0 (D11) findings as they surface, plus
any pre-cycle observations that should be visible to PLAN.md
authoring. Per AGENTS.md "Pre-PLAN bug hunt" pattern, items here
are tagged with a `cycle_impact` disposition that the
pre-implementation gate (D11) consumes.

Status: **pre-cycle**. Cycle is not yet open; PLAN.md not authored.

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

## How to add a finding to this file

1. Number sequentially (`F-OB-PRE-NN`).
2. Include a short title summarising the failure mode in one line.
3. Sections: **Surfaced** (when/where), **Workaround** (if any),
   **Why this matters for v0.1.18** (the cycle thesis lens),
   **Likely fix shape** (informed guess, not committed scope),
   **`cycle_impact` tag** (`absorbs-into-WS` / `revises-scope` /
   `aborts-cycle` / `informational`).
4. If the finding has a memory file, cross-reference its path.
