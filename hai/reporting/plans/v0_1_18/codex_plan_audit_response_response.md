# Maintainer Response — v0.1.18 D14 Round 1

**Author:** Claude (autonomous mode under maintainer ratification).
**Date:** 2026-05-06.
**Round 1 verdict:** PLAN_COHERENT_WITH_REVISIONS — 7 must-fix findings.
**Disposition summary:** **All 7 findings accepted; PLAN revised in lockstep.** No rejections. No challenges. Codex's provenance discipline caught real gaps the PLAN-author missed (handler count off by 2, seam-shape claim wrong, doctor-check scope conflict, parallelization claim copy-pasted from v0.1.17 without updating the dependency chain).

---

## Per-finding triage

### F-PLAN-01 — W-OB-7 handler inventory and seam-shape provenance ⇒ ACCEPT

**Verified on disk** (`grep -n "^def cmd_intake_" src/health_agent_infra/cli/handlers/intake.py`):

```
gym=62, exercise=300, nutrition=420, stress=643, note=790,
readiness=903, gaps=980, weight=1184  →  8 handlers, not 6
```

The PLAN-author missed `cmd_intake_exercise` (writes via `open_connection`, line 352) and `cmd_intake_gaps` (reads via `open_connection`, line 1025; also opens a second presence connection at 1025 then a write connection at 1093).

**Seam-shape verified:** every existing intake handler uses `core.state.open_connection` (lines 227, 352, 602, 753, 880, 1025/1093/1149, 1238). PLAN's "raw `sqlite3.connect`" claim was wrong.

**`hai state init` provenance verified:** `cmd_state_init` is at `cli/handlers/state.py:46-52` and reaches migrations through `initialize_database` (which calls `apply_pending_migrations` at `core/state/store.py:335`). The lines PLAN cited (`state.py:239,273`) belong to `cmd_state_migrate`, the explicit user-facing migration command — not the auto-migrate path on `hai state init`.

**Revisions to PLAN:**
- §1.1 thread-2 line 38: "every intake handler" stays directionally correct but the seam citation gets the actual current shape.
- §1.2 line 54 W-OB-7 row: "every `cmd_intake_*` handler" stays; `apply_pending_migrations` path corrected.
- §2.G files-of-record: enumerate 8 handlers, not 6, with correct line numbers.
- §2.G fix-shape diff: rewrite from "replace raw `sqlite3.connect` with `connect_and_migrate`" to "replace `open_connection` with a migration-applying variant `open_connection_with_migrations`" per OQ-1 below.
- §2.G acceptance items 2-3 and reproducer test: cover all 8 handlers (or explicitly classify which exclude and prove the exclusion safe).

### F-PLAN-02 — W-OB-5 `next_action` example contradicts post-W-OB-2 shape and manifest safety ⇒ ACCEPT

**Verified on disk:** `cli_capabilities_v0_1_13.json` shows `hai init` is `agent_safe: false`. The example in PLAN §2.E with `agent_safe: true` directly contradicts the live manifest. Plus the example shows `"command": "hai init --guided"` while acceptance item 2 demands the post-W-OB-2 default-flipped shape (`hai init`). Two real bugs in the example, both load-bearing if an implementer copy-pastes it.

**Revisions to PLAN:**
- §2.E example block: replace `command: "hai init --guided"` with `command: "hai init"`, replace `agent_safe: true` with `agent_safe: false`, add explicit comment that the field reflects the underlying `hai init` manifest entry's `agent_safe` value (consistency invariant). The `interactive: true` field stays — that's W-OB-5's net-new contract.
- §2.E acceptance items: add an explicit item asserting `next_action.agent_safe` matches the live capabilities manifest entry for the cited command (consistency check, not a copy from PLAN prose).
- §2.E acceptance items: add a test `next_action.command == "hai init"` (not `hai init --guided`) for the missing-intent case post-W-OB-2.

### F-PLAN-03 — W-OB-5 migration-behind acceptance silently widens onboarding_readiness scope ⇒ ACCEPT

**Verified on disk:** `check_onboarding_readiness` (`core/doctor/checks.py:470`) covers intent/target/wellness — not migration state. `check_state_db` (line 84) handles pending migrations and emits `pending_migrations` in its result dict (line 146). PLAN line 257 says W-OB-5 "does not change `check_onboarding_readiness` decision logic" but acceptance item 1 says `next_action` covers "FAIL with no DB or migration-behind" — those can't both be true if the field is scoped to onboarding_readiness only.

**Resolution path:** widen W-OB-5's scope from "onboarding_readiness only" to "doctor checks where `next_action` is meaningful, including `state_db` for migration-behind." This is the cleaner contract — every check that emits a `hint` today is a candidate for `next_action`.

**Revisions to PLAN:**
- §2.E source: extend from `check_onboarding_readiness` only to "doctor checks that emit `hint` today" (`check_state_db`, `check_onboarding_readiness`, `check_credentials`, `check_skills`, `check_threshold_overrides_loaded`, `check_capabilities_walker`, etc.). The W-OB-5 contract becomes "`next_action` is the structured-form companion to `hint` across `hai doctor` checks, with `onboarding_readiness` as the primary surface."
- §2.E line 257: rewrite from "does not change `check_onboarding_readiness` decision logic" to "does not change any doctor check's *decision logic* — only the *output schema* gains a structured `next_action` companion to the existing `hint` field."
- §2.E acceptance items: add per-check `next_action` coverage where the corresponding `hint` exists today; tests cover at least three checks (onboarding_readiness, state_db, credentials).

### F-PLAN-04 — W-OB-4 cannot validate post-W-OB-2 default-flipped path as currently sequenced ⇒ ACCEPT

**Reasoning verified:** §1.3 puts W-OB-4 in Phase 1 (before W-OB-2). The dogfood pass therefore can't witness the post-W-OB-2 default-flip. Plus scenario 1's `pipx install health-agent-infra==<v0.1.18-build>` references a not-yet-published artifact at pre-ship gate time. Two distinct issues: sequencing makes W-OB-4 evidence-gathering only; the artifact-source claim is misleading.

**Revisions to PLAN:**
- Split W-OB-4 conceptually into two named sub-passes: **W-OB-4a (early evidence)** in Phase 1 against W-OB-1 + W-OB-7 in tree; **W-OB-4b (post-W-OB-2 local-wheel smoke)** in Phase 2 after W-OB-2 lands. Both produce findings into `dogfood_findings.md`.
- §2.D: split scenarios into `Early evidence (W-OB-4a)` and `Post-W-OB-2 smoke (W-OB-4b)`. The former is exploratory dogfood; the latter is a release-blocker gate that uses a *locally built wheel* (`uvx --from build python -m build` then `pipx install <wheel-path>`), not a PyPI install.
- §1.3 sequencing: W-OB-4a stays in Phase 1 (W-OB-1 → W-OB-7 → W-OB-4a); W-OB-4b is added to Phase 2 after W-OB-2 lands.
- §6 ship gates: add the W-OB-4b post-W-OB-2 wheel-smoke gate explicitly (per F-PLAN-07).
- The original "scenario 2 = upgrade-from-old-DB" stays — it's part of W-OB-4a or W-OB-4b? Cleanest assignment: scenario 1 (clean install) is W-OB-4b smoke (because it needs the post-W-OB-2 default-flip behavior in tree); scenario 2 (upgrade) is W-OB-4a (it tests W-OB-7 in isolation, doesn't need W-OB-2).
- Effort arithmetic (§5): W-OB-4 stays at 1d total but split as W-OB-4a 0.5d + W-OB-4b 0.5d.

### F-PLAN-05 — v0.2.0 parallelization claim contradicts the tactical dependency chain ⇒ ACCEPT

**Verified:** `tactical_plan_v0_1_x.md:52` shows v0.2.0 hard-deps on v0.1.19 (post-rename from v0.1.16). v0.1.19 hard-deps on v0.1.18. Therefore v0.1.18 ↛ parallelizable with v0.2.0; v0.1.18 is upstream of v0.2.0 via v0.1.19. The PLAN-author copied the v0.1.17 PLAN's "parallelizable with v0.2.0" claim (which was correct for v0.1.17 because v0.2.0 explicitly NOT dependent on v0.1.17 per tactical line 52) without updating the dependency analysis for v0.1.18.

**Revisions to PLAN:**
- §1.1 theme paragraph (line 13): replace "Parallelizable with v0.2.0 since v0.2.0's hard dependencies do not include this cycle" with "Sequenced upstream of v0.2.0 via v0.1.19 (the renumbered foreign-user empirical cycle); v0.1.18 does not add new v0.2.0 scope or schema dependencies."
- §7 cross-cycle boundary: clarify v0.2.0 sequencing — "v0.2.0 work (W52, W58D, Path A) — out-of-scope; tactically sequenced post-v0.1.19, which is post-v0.1.18."

### F-PLAN-06 — W-OB-3 cites a non-existent test file ⇒ ACCEPT

**Verified on disk:** `verification/tests/test_guided_onboarding.py` does not exist. `verification/tests/test_init_onboarding_flow.py` does exist (the actual W-AA gate per v0.1.13 RELEASE_PROOF lines 166-172).

**Revisions to PLAN:**
- §2.C files-of-record line 165: replace `test_guided_onboarding.py` with `test_init_onboarding_flow.py`.
- §2.C acceptance item 2 (refusal-path tests): clarify "user types 'skip'" → either (a) verify the orchestrator already has a literal `skip` affordance and cite where, or (b) restate as "user provides no input (Enter / empty) → flow treats as skipped." Per Codex's note: current orchestrator treats unrecognized focus text as skipped — that's an empty-input affordance, not a literal `skip` keyword. PLAN must not silently add a new affordance under a content-review WS.

### F-PLAN-07 — §6 ship gates miss two load-bearing acceptance checks ⇒ ACCEPT

**Reasoning verified:** §2.D acceptance item 3 names the W-OB-7-fix-in-tree-before-W-OB-4 sequencing as a no-ship gate, but §6 only has "`dogfood_findings.md` exists" + "W-OB-7 reproducer test passes." Those are unit-test gates, not packaged-dogfood gates. Similarly §2.E acceptance item 2 (`next_action.command` post-W-OB-2 shape) has no §6 gate.

**Revisions to PLAN:**
- §6 ship gates table: add three new rows:
  - W-OB-4b post-W-OB-2 local-wheel smoke (per F-PLAN-04 split): `pipx install <wheel> && hai init` on interactive TTY proves default-flip fires.
  - W-OB-4a scenario 2 packaged upgrade smoke: `hai intake weight` on synthetic schema-25 DB succeeds against the wheel build.
  - W-OB-5 `next_action.command` post-W-OB-2 shape test: asserts `next_action.command == "hai init"` (not `hai init --guided`) for the missing-intent case.
- §6 release-blocker gates: add the W-OB-4b smoke explicitly.

---

## Open-question dispositions (Codex-recommended)

| OQ | PLAN-author default | Codex recommendation | Disposition |
|---|---|---|---|
| OQ-1 | `cli/shared.py` | `core/state/store.py` (`open_connection_with_migrations`); don't change `open_connection` globally | **Accept Codex.** Helper goes in `core/state/store.py` next to `open_connection`. Don't replace `open_connection` globally — too many read paths depend on it (would need a separate audit). New variant `open_connection_with_migrations` for write paths that need schema-current. PLAN §2.G updates accordingly. |
| OQ-2 | No project-wide `HAI_NON_INTERACTIVE` for v0.1.18 | Agree on no; tests cover both `--non-interactive` and `HAI_INIT_NON_INTERACTIVE=1` with `isatty()==True` | **Accept.** PLAN §2.B acceptance item 3 expanded — 4-case test stays, but case (iv) splits into (iv-flag) and (iv-env) for explicit coverage. |
| OQ-3 | Snapshot maintainer's pre-v0.1.17 DB; otherwise install v0.1.16 wheel + run `hai init` | Agree; treat targeted rollback as last resort and document the exact mutation | **Accept.** PLAN §2.D scenario-2 instructions clarify the priority order + name the documentation requirement if a manual rollback is performed. |
| OQ-4 | `next_action` at runtime check level only (not in capabilities manifest) | Current default conflicts with §2.E.5 acceptance (which adds `doctor_check_schema` to manifest). Pick one. | **Accept Codex framing.** Resolution: `next_action` is runtime-only (not in the capabilities manifest schema). §2.E.5 acceptance item dropped — no manifest schema delta. Capabilities-manifest schema freeze (v0.2.3 W-30 territory) untouched. |
| OQ-5 | Yes — post-prompt summary surfaces a "next action" hint | Agree — content only, no new guided step | **Accept.** PLAN §2.C clarifies the hint is a content-only addition to the existing post-prompt summary, not a new flow step. |
| OQ-6 | "default-flip (with opt-out)" | "interactive `hai init` default (with opt-out)" for user-facing CHANGELOG | **Accept Codex.** PLAN §2.B acceptance item 6 + §3 CHANGELOG language updated. Internal "default-flip" term stays in PLAN/audit-trail vocabulary. |
| OQ-7 | Reserve W-OB-6 | Reserve; if not fired, RELEASE_PROOF says "no W-OB-6-class findings" + counts as 6 base + W-OB-7 (W-OB-6 unused) | **Accept.** PLAN §2.F acceptance item 1 explicit about the unfired-state RELEASE_PROOF wording. |

---

## Tier ratification

Codex confirms **substantive** stays. Hardening doesn't fit because W-OB-2 changes the most-visible first-run command behaviour and can break automation if wrong — that's a product-behaviour-change shape, not a correctness-only shape. Release-blocker leg holds; days leg below threshold is correctly named in the PLAN's tier annotation.

**No tier change.**

---

## Round-2 expectation

Per Codex closure recommendation: "one focused revision pass by Claude/maintainer, then D14 round 2. Expected round 2 should be small: mostly checking that the W-OB-7 inventory, W-OB-5 schema, W-OB-4 gates, and v0.2.0 wording moved in lockstep across §1, §2, §6, and §8."

**Author's predicted round-2 finding density:** 1-2 findings (provenance drift caught between rounds is the canonical R2 finding shape per AGENTS.md "Audit-chain empirical settling shape" 10 → 5 → 3 → 0 norm; this round was 7, so R2 expected 2-4 actually). Most likely surfaces:

1. **Summary-surface sweep gaps.** A revision in one section not propagating to a downstream section. Particularly W-OB-4 → W-OB-4a/W-OB-4b split must propagate to §1.2 catalogue, §1.3 sequencing, §2.D, §5 effort arithmetic, §6 ship gates, §8 OQ — six surfaces moving in lockstep.
2. **W-OB-7 handler-coverage classification.** If the revised PLAN excludes any of the 8 handlers, R2 will probe whether the exclusion is justified.
3. **W-OB-5 multi-check `next_action` scope.** The widening from onboarding_readiness-only to doctor-checks-with-hints-where-relevant introduces test-surface scope. R2 likely probes whether the test surface is enumerated explicitly.

Round-2 prompt authors after PLAN revisions land + maintainer ratifies the disposition above.

---

## Files revised in lockstep with this response

After this response_response is committed:

- `reporting/plans/v0_1_18/PLAN.md` — 7 must-fix revisions per the per-finding sections above.
- `reporting/plans/v0_1_18/codex_plan_audit_response_response.md` — this file.
- `reporting/plans/v0_1_18/codex_plan_audit_round_2_prompt.md` — authored after PLAN revisions land + maintainer ratifies.
