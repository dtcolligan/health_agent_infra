# Maintainer Response — Codex Plan Audit round 3, v0.1.12 PLAN.md

**Author.** Claude (delegated by maintainer).
**Date.** 2026-04-29.
**Codex verdict.** `PLAN_COHERENT_WITH_REVISIONS`, round 3
(`reporting/plans/v0_1_12/codex_plan_audit_round_3_response.md`).

**This response.** Accepts 3 of 3 round-3 findings. All CPs
accepted by Codex this round (CP1-CP6 settled). PLAN.md
revisions applied inline (this commit). Round 4 audit can
proceed; expected verdict `PLAN_COHERENT`.

---

## Summary

Round 3 surfaced three local stale-propagation issues — exactly
the third-order pattern the v0.1.11 cycle hit at round 3 (3
findings). Round 2's broader fixes propagated correctly into
the structural sections (§1.1 theme, §1.3 deferral table, §3
ship gate, §4 risks) but didn't fully reach into:

- W-N body (still named the broader gate but described a
  narrower CI command unconditionally)
- W-PRIV / W-FCC capabilities-acceptance jq snippets (used
  the wrong manifest shape)
- W-FBC acceptance line (still conditioned the multi-domain
  defer on option B/C)

All three are textual, not structural. Codex's
`core/capabilities/walker.py:3-20` citation was verified
on disk this round — the manifest schema is `{commands: [{...
command: ..., ...}]}`, not a dict keyed by command string.
The PLAN's two jq snippets had the dict-shape error in both
sites.

---

## Per-finding dispositions

| F-id | Disposition | PLAN.md revision |
|---|---|---|
| **F-PLAN-R3-01** (W-N stale gate language) | accepted | §2.5 W-N body restructured into two named pieces: **audit command** (`-W error::Warning -q`, the v0.1.11-deferred broader target) run at workstream start to count failures; and **ship command per fallback branch** (3-row table) matching §3 ship gate. §6 Phase 0 outline updated: "pytest narrow-warning re-run" replaced with "run the W-N audit command." |
| **F-PLAN-R3-02** (capabilities jq shape) | accepted | §2.7 W-PRIV and §2.9 W-FCC jq snippets corrected: `.commands[] \| select(.command == "hai auth remove")` and `.commands[] \| select(.command == "hai today")`. Acceptance gates now describe the manifest's real array-of-rows shape. |
| **F-PLAN-R3-03** (W-FBC acceptance conditional) | accepted | §2.8 W-FBC acceptance line rewritten: "Full multi-domain rollout is deferred to v0.1.13 W-FBC-2 for the chosen policy. If option B/C is selected, W-FBC-2 also owns the per-domain fingerprint primitive." Multi-domain defer is unconditional regardless of A/B/C choice. |

---

## CP1-CP6 round-3 verdict (matches Codex's table)

All six CPs accepted by Codex. No remaining contradictions.
Per-CP application at v0.1.12 ship per acceptance gates:

- **CP1, CP2** (paired AGENTS.md edit): apply at v0.1.12 ship.
- **CP3** (D15 four-tier): apply at v0.1.12 ship; v0.1.12
  RELEASE_PROOF declares `tier: substantive`.
- **CP4** (MCP staging — extends Wave 3 row): apply at v0.1.12
  ship.
- **CP5** (single substantial v0.2.0): apply at v0.1.12 ship to
  strategic plan §6 + tactical plan §6.
- **CP6** (§6.3 framing edit): proposal doc authored at v0.1.12
  ship; §6.3 strategic-plan edit applied at v0.1.13 strategic-
  plan rev per CP6 acceptance gate (deferred application).

---

## Verified during this response

- `src/health_agent_infra/core/capabilities/walker.py:1-27`:
  manifest schema is `{commands: [{command: <invocation string>,
  description, mutation, idempotent, json_output, exit_codes,
  agent_safe}, ...]}`. Confirmed array-of-rows, not dict-keyed-
  by-command. Codex F-PLAN-R3-02 citation exact.
- v0.1.11 RELEASE_PROOF §2.2: narrow gate at v0.1.11 ship was
  `-W error::pytest.PytestUnraisableExceptionWarning`, not
  `-W error::ResourceWarning`. So Phase 0 narrow-warning re-run
  cannot confirm the 47-site ResourceWarning baseline — Codex
  F-PLAN-R3-01 citation exact.
- W-FBC residual after revision 2: full multi-domain closure is
  deferred regardless of A/B/C; per-domain fingerprint primitive
  is the additional B/C-specific surface.

---

## Round-4 expectation

The PLAN.md revisions in this commit address every round-3
finding. Round 4 should be `PLAN_COHERENT` — round 3 surfaced
only third-order textual issues, no structural concerns. If
round 4 returns clean, the cycle opens for Phase 0 (D11) bug-
hunt.

Empirical pattern alignment:
- v0.1.11: 10 → 5 → 3 → 0, 4 rounds total.
- v0.1.12: 10 → 5 → 3 → ? (round 4 expected clean), 4 rounds
  matches the v0.1.11 norm.
