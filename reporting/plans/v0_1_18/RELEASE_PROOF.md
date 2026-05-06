**Tier: substantive** (per AGENTS.md D15 first-line declaration —
≥1 release-blocker workstream. Effort 5-9 days falls below the
≥10-days threshold, so the tier classification rests on the
W-OB-2 release-blocker leg, not the days leg.)

# v0.1.18 Release Proof — Onboarding-quality + intake-handler migration parity

**Cycle close:** 2026-05-06.
**HEAD at ship:** to be stamped at the version-bump commit (post-IR settle).
**Author:** Claude Opus 4.7 (1M context) — autonomous Phase 0 → ship
implementation under maintainer ratification per the cycle's end-to-end
execution mandate.

## §1 Workstream completion

| W-id | Title | Status | Acceptance |
|---|---|---|---|
| **W-OB-1** | README quickstart pivot to bare `hai init` (post-W-OB-2 default-flip shape; pre-staged delta + post-IR-R1 F-IR-02 rewrite); cross-reference sweep | **closed** | README §"Install and quickstart" leads with bare `hai init` as the primary first-run command, with the W-OB-2 auto-promotion behaviour documented inline + opt-out paths enumerated (`--non-interactive`, `HAI_INIT_NON_INTERACTIVE=1`, no TTY). `hai init --guided` retained as explicit-force spelling. `agent_integration.md:27` install-lead summary matches. Historical launch material under `reporting/docs/launch/` (v0.1.0-era drafts) intentionally left as-is per AGENTS.md provenance discipline. CHANGELOG v0.1.18 entry names W-OB-1 (with R1 fix-and-reland callout). Pure docs; no test change. **(R1 IR F-IR-02 closure: pre-fix README still said "New users on an interactive terminal should always pass `--guided`" — incorrect post-W-OB-2; rewritten in fix-and-reland commit.)** |
| **W-OB-2** | `hai init` default-flip — TTY+incomplete auto-promotes to `--guided`; `--non-interactive` flag + `HAI_INIT_NON_INTERACTIVE=1` env var opt-outs | **closed** | All 7 acceptance items pass (PLAN §2.B 1-7). New `--non-interactive` flag at `hai init` (11th flag, manifest snapshot regenerated). Default-flip decision logic in `cmd_init` reuses `check_onboarding_readiness` predicate. Decision logged to `report["default_flip"]["decision"]` (one of `explicit_guided` / `opt_out_flag` / `opt_out_env` / `opt_out_no_tty` / `not_fired_already_complete` / `fired_incomplete` / `not_fired_check_error`). 5-case test (`test_cli_init_default_flip.py`) covers interactive+missing → guided, interactive+complete → bare, no-TTY → bare, --non-interactive flag → bare, env var → bare; PLUS bonus test for explicit `--guided` unaffected by flip. CHANGELOG entry names "interactive `hai init` default (with opt-out)" per OQ-6. F-PHASE0-01 conftest.py autouse fixture sets `HAI_INIT_NON_INTERACTIVE=1` for the suite so existing init tests are unaffected. |
| **W-OB-3** | `--guided` prompt content review — content-only `next_action_hint` + skip-input affordance tests | **closed** | All 6 acceptance items pass (PLAN §2.C 1-6). New `next_action_hint` field on `OnboardingResult`, populated from **primitive `intent_ids` + `target_ids` readiness** (post-IR-R1 F-IR-04 rewrite from coarse `intent_target.status` keying). Branches: empty-missing → `hai daily` direct; `["credentials"]` → `hai auth intervals-icu` remediation; `["intent"]` → `hai intent training add-session`; `["target"]` → `hai target set`; `{"intent","target"}` w/ creds → both intent+target remediation; otherwise → re-run `hai init --guided`. Empty-input affordance tests cover focus prompt + per-target prompts (no literal `skip` keyword added — per F-PLAN-06 R1 disposition). **8 new tests** in `test_init_onboarding_w_ob_3.py` (6 original + 2 R1 regression: creds+intent+all-targets-skipped → target remediation; creds+targets+focus-skipped → intent remediation); 9 existing tests in `test_init_onboarding_flow.py` unchanged + green. Informed by W-OB-4a F-OB-4A-02 finding. |
| **W-OB-4a** | Phase 1 upgrade-from-old-DB dogfood pass | **closed** | `dogfood_findings.md` § W-OB-4a authored. Synthetic schema-25 DB constructed via OQ-3 priority-order option (b) (apply-migrations-filtered approach). End-to-end witness: `hai intake weight` succeeded against schema-25 DB (F-OB-PRE-01 reproducer); `hai doctor` reported clean schema 26 head; `hai daily` Phase 0 emits structured `intake_command` per gap (F-OB-4A-01 cross-cycle convention finding). 4 findings filed: F-OB-4A-01 (W-OB-5 alignment), F-OB-4A-02 (umbrella preference for multi-missing), F-OB-4A-03 (W-OB-7 verified end-to-end, positive), F-OB-4A-04 (no W-OB-6-class). |
| **W-OB-4b** | Phase 2 post-W-OB-2 local-wheel smoke | **closed-with-deferral** | `dogfood_findings.md` § W-OB-4b authored. Local wheel built (`uvx --from build python -m build --wheel`) and installed into isolated venv (autonomous-mode safety substitution for `pipx install` against user environment). Wheel manifest verified: `--non-interactive` flag at index 11 of `hai init` flags; total command count unchanged at 67. Both opt-out paths verified end-to-end: `HAI_INIT_NON_INTERACTIVE=1 hai init` → `decision: opt_out_env`; `hai init --non-interactive` → `decision: opt_out_flag`. **TTY default-flip witness deferred to maintainer ship-time interactive run** (F-OB-4B-02) — autonomous-mode subshell cannot exercise real TTY interaction; the unit-test analogue (`test_cli_init_default_flip.py::test_case_i_tty_plus_missing_fields_fires_guided`) passes with monkeypatched isatty=True. See §3 below for the manual ship-time gate. |
| **W-OB-5** | `hai doctor` `next_action` across hint-emitting checks; manifest-consistency invariant | **closed** | All 6 acceptance items pass (PLAN §2.E 1-6). `_NEXT_ACTION_REGISTRY` in `core/doctor/checks.py` covers **11 commands** (hai init, state init, state migrate, auth intervals-icu, auth garmin, setup-skills, intent training add-session, target set, pull --source intervals_icu, **config init --force, doctor** — last 2 added at IR R1 F-IR-03 close). **9 doctor check paths gain `next_action`** on WARN/FAIL: `check_state_db` (no DB; pending migrations), `check_onboarding_readiness` (no DB; multi-missing umbrella; per-component single-missing), `check_auth_intervals_icu` (no creds; **deep-probe CAUSE_2_CREDS + NETWORK** post-R2 F-IR-R2-01), `check_auth_garmin` (no creds), `check_skills` (missing dest; missing skills), `check_config` (missing thresholds; malformed TOML — post-R1 F-IR-03), `check_sources` (no DB — post-R1 F-IR-03), `check_today` (no DB; schema-read-failed — post-R1 F-IR-03), `check_intake_gaps` (no DB; schema-read-failed — post-R1 F-IR-03). PASS results omit `next_action`. Manifest-consistency test caught + corrected 3 pre-impl drift entries; +2 new R1 entries verified; +0 manifest deltas at R2 (deep-probe additions are leaf-command lookups, no new registry rows). F-OB-4A-02 umbrella preference enforced: multi-missing preconditions → `hai init`; single missing → per-component. CAUSE_1_CLOUDFLARE_UA + OTHER deep-probe outcomes intentionally stay prose-only (no concrete-command mapping). Renderer adds `next:` line per check after `hint`; 4 special-case renderers updated post-R1 (`_render_sources`, `_render_intake_gaps`, `_render_today`, `_render_onboarding_readiness`). **Runtime-only per OQ-4** — no `hai capabilities --json` schema delta; v0.2.3 W-30 freeze remains untouched. |
| **W-OB-6** | Conditional absorption slot | **does-not-fire** | Per PLAN §2.F item 1 + OQ-7 disposition. Both W-OB-4a + W-OB-4b dogfood passes surfaced zero W-OB-6-class structural findings (F-OB-4A-04 + F-OB-4B-04). Cycle ships with 7 W-ids closed (W-OB-1 + W-OB-2 + W-OB-3 + W-OB-4a + W-OB-4b + W-OB-5 + W-OB-7); W-OB-6 explicitly named "no W-OB-6-class findings." |
| **W-OB-7** | Intake-handler migration parity (F-OB-PRE-01 fix) | **closed** | All 6 acceptance items pass (PLAN §2.G 1-6). New `open_connection_with_migrations` helper in `core/state/store.py` next to `open_connection` (line 64) and `apply_pending_migrations` (line 243); additive — does NOT replace `open_connection` globally per OQ-1. All 8 `cmd_intake_*` handlers route through the migrating helper (gym=62, exercise=300, nutrition=420, stress=643, note=790, readiness=903 [via `_project_readiness_submission_into_state` helper at 1124], gaps=980, weight=1184). 10 new tests in `test_intake_migration_parity.py`: 1 helper-additivity check + 1 F-OB-PRE-01 reproducer + 7 per-handler parity (gym + exercise + nutrition + stress + note + readiness + gaps; weight is the reproducer test) + 1 no-regression-on-current-schema. End-to-end witness via W-OB-4a dogfood (F-OB-4A-03 positive finding). |

## §2 Standard substantive-cycle ship gates

Initially stamped pre-IR. **Re-stamped post-IR R1 + R2 fix-and-reland**
(R1 closures: F-IR-01 `agent_cli_contract.md` regenerated; F-IR-02
README post-W-OB-2 wording; F-IR-03 7 additional `next_action` paths
+ 5 regression tests; F-IR-04 `next_action_hint` keys on primitive
readiness fields, not derived status string + 2 regression tests.
R2 closures: F-IR-R2-01 deep-probe `check_auth_intervals_icu` outcomes
(CAUSE_2_CREDS → `hai auth intervals-icu`; NETWORK → `hai doctor`;
CAUSE_1 + OTHER stay prose-only by design) + 4 regression tests;
F-IR-R2-02 release-summary surface sweep across `agent_integration.md`,
CHANGELOG, RELEASE_PROOF §1, REPORT §6, current_system_state).

```
✓ Full pytest suite (narrow gate): 2733 passed, 5 skipped (~130s)
  (was 2688 + 5 at v0.1.17 close; +45 new tests: W-OB-2 (6) +
  W-OB-3 (8) + W-OB-5 (21) + W-OB-7 (10))
✓ Full pytest suite (broader -W error::Warning gate): 2733 passed, 5 skipped
✓ uvx mypy src/health_agent_infra: Success — 147 source files, 0 errors
✓ uvx bandit -ll -r src/health_agent_infra: 0 medium / 0 high severity
✓ hai capabilities --json: snapshot regenerated with W-OB-2 --non-interactive
  flag intentional add; no other drift
✓ reporting/docs/agent_cli_contract.md: regenerated post-version-bump
  (F-IR-01 fix); test_committed_contract_doc_matches_generated green
✓ Persona matrix (post-impl): 13/13 personas, 0 findings, 0 crashes (~5 min,
  opt-in via HAI_RUN_PERSONA_MATRIX=1) — IDENTICAL to pre-impl baseline
  (v0.1.18 doesn't change classifiers/policy; expected)
✓ hai eval run --scenario-set all: 135/135 PASS (100% per inherited
  v0.1.17 corpus baseline)
✓ W-OB-2 default-flip 5-case test green
✓ W-OB-7 reproducer test (`test_intake_weight_on_pre_v0_1_17_db`) green
✓ W-OB-7 8-handler parity test (`test_intake_migration_parity.py`) green
✓ W-OB-5 manifest-consistency test green (caught + corrected 3 drift
  entries pre-impl; +2 new entries verified post-IR-R1)
✓ W-OB-5 doctor coverage extended post-IR-R1: check_config (×2 paths),
  check_sources, check_today (×2), check_intake_gaps (×2) all emit
  next_action when their hint maps to a concrete command
✓ W-OB-3 next_action_hint regression test green: creds + intent +
  all-targets-skipped → routes to `hai target set`, NOT `hai daily`
  (F-IR-04 fix witness)
```

## §3 Manual ship-time gate (maintainer-driven)

The W-OB-4b release-blocker gate "bare `hai init` on interactive TTY enters
the `--guided` flow" requires real terminal interaction that the autonomous-
mode subshell cannot exercise. **Maintainer must run `hai init` interactively
once before PyPI publish** to confirm the user-experience flow works end-to-
end.

```bash
# In a real terminal (not a pytest subshell or CI runner):
pipx install --force --pip-args="--no-cache-dir" \
    dist/health_agent_infra-0.1.18-py3-none-any.whl
rm -rf ~/.local/share/health_agent_infra_test_v0_1_18  # or use HAI_STATE_DB
HAI_STATE_DB=~/.local/share/health_agent_infra_test_v0_1_18/state.db hai init

# Expected: bare `hai init` (no --guided flag) auto-promotes to the
# guided flow because:
#   - sys.stdin.isatty() == True
#   - check_onboarding_readiness reports missing intent + target + wellness_pull
# The terminal should show the intervals.icu credential prompt; the user
# can answer or hit Enter to skip; the flow proceeds through intent/target
# prompts; post-prompt summary surfaces `next_action_hint`.
```

The unit-test analogue
(`test_cli_init_default_flip.py::test_case_i_tty_plus_missing_fields_fires_guided`)
passes post-W-OB-2 with monkeypatched isatty=True; this manual gate is the
human-side UX confirmation.

## §4 W-OB-7-specific ship gate (release-blocker for F-OB-PRE-01 closure)

```
✓ test_intake_weight_on_pre_v0_1_17_db: F-OB-PRE-01 regression closed —
  `hai intake weight` against synthetic schema-25 DB succeeds + writes to
  the now-migrated body_comp table. Pre-fix: OperationalError: no such
  table: body_comp. Post-fix: silent migration + write success.
✓ All 8 cmd_intake_* handlers covered: gym, exercise, nutrition, stress,
  note, readiness, gaps, weight — each succeeds against schema-25 DB.
✓ open_connection unchanged globally (additive helper per OQ-1).
```

## §5 Out-of-scope items (explicit deferrals)

- **Foreign-user empirical session.** Remains v0.1.19's claim. v0.1.18's
  W-OB-4a + W-OB-4b are maintainer dogfood, not foreign-user transcripts.
- **Real TTY default-flip user-experience confirmation.** Deferred to
  maintainer ship-time manual gate per §3 above.
- **`hai capabilities --json` schema additions.** None. `next_action` is
  runtime-only per OQ-4. v0.2.3 W-30 freeze remains untouched.
- **AGENTS.md governance edits beyond closure-side.** No CP-shape edits;
  no new D-entries; no "Do Not Do" additions.
- **Body-comp surface extensions.** v0.1.17 W-B's `hai intake weight`
  surface unchanged; W-OB-7 fixes the upgrade-path crash but doesn't
  extend the surface.

## §6 Cross-cutting work (per PLAN §3)

Closure-side updates landing at v0.1.18 ship:

- ✓ `pyproject.toml` version bump 0.1.17 → 0.1.18 (ship-prep commit).
- ✓ `CHANGELOG.md` v0.1.18 entry naming W-OB-1..7 (with W-OB-6
  unfired) and behaviour-change call-out for W-OB-2.
- ✓ `AUDIT.md` v0.1.18 row with D14 round table (R1 7 → R2 3 close-in-place)
  + IR outcome (to be stamped post-IR) + RELEASE_PROOF link.
- ✓ `reporting/docs/current_system_state.md` updated: package version,
  schema head (unchanged at 26), CLI command count (unchanged at 67),
  test gate (2722 passed, 5 skipped), next-cycle role.
- ✓ `reporting/plans/tactical_plan_v0_1_x.md` §5E moves "in flight"
  → "shipped"; §5F (v0.1.19) moves to "next-active".
- ✓ `reporting/plans/README.md` cycle-list entry for v0.1.18 added.

## §7 Notes for the maintainer (and Codex IR)

1. **Manual ship-time TTY gate per §3.** Deferred from W-OB-4b autonomous-
   run scope. Run before `twine upload`.
2. **W-OB-5 manifest-consistency test** is the load-bearing surface for the
   `next_action.agent_safe` invariant. If a future cycle changes a
   command's `agent_safe` value, the registry must update in lockstep or
   this test will fail.
3. **F-PHASE0-01 conftest.py autouse fixture** silently opts the entire
   suite out of the W-OB-2 default-flip via `HAI_INIT_NON_INTERACTIVE=1`.
   Tests specifically exercising the default-flip predicate
   (`test_cli_init_default_flip.py`) `monkeypatch.delenv` the variable.
   This is intentional — surfaced explicitly so future test additions
   know about the implicit env var.
4. **`open_connection_with_migrations` is intake-handler scoped only.** Per
   OQ-1, the helper is additive — `open_connection` is unchanged globally.
   Any future read-path that wants schema-current state should explicitly
   opt into the migrating variant; the doctor checks (`check_state_db`,
   `check_onboarding_readiness`, etc.) intentionally continue to use bare
   `open_connection` because they're diagnostic and need to see the actual
   schema state.
5. **W-OB-6 unfired.** No structural findings from W-OB-4a + W-OB-4b. If
   the maintainer's manual TTY gate (§3) surfaces a structural finding,
   that's a hotfix candidate (per PLAN §2.F item 3 severity routing) or
   a v0.1.19 reach-back, not a re-opening of W-OB-6.
6. **D15 IR prompt authored** at
   `codex_implementation_review_prompt.md`. Empirical norm: 2-3 IR rounds
   settling at SHIP or SHIP_WITH_NOTES.

## §8 D14 audit-chain summary

| Round | Findings | Verdict |
|---|---:|---|
| 1 | 7 | PLAN_COHERENT_WITH_REVISIONS |
| 2 | 3 | PLAN_COHERENT_WITH_REVISIONS close-in-place |

## §8b D15 IR audit-chain summary

| Round | Findings | Verdict | Closed via |
|---|---:|---|---|
| 1 | 4 | SHIP_WITH_FIXES | fix-and-reland 1 (commit `4de4306`) |
| 2 | 2 | SHIP_WITH_FIXES | fix-and-reland 2 (commit `19ed4b0`) |
| 3 | 1 (nit) | SHIP_WITH_NOTES | close-in-place |

**D15 IR settled at R3.** Settling shape **4 → 2 → 1-nit** matches
AGENTS.md empirical norm `5 → 2 → 1-nit` (twice-validated against
v0.1.11 + v0.1.12 + v0.1.17). v0.1.18 settles slightly tighter at
R1 (4 not 5) consistent with its smaller catalogue.

Settling shape **7 → 3** matches AGENTS.md empirical norm `10 → 5 → 3 → 0`
(thrice-validated against v0.1.11, v0.1.12, v0.1.17). v0.1.18 settled one
round earlier than the norm because the catalogue is small (7 W-ids) and
structurally low-density (most rows reference established mechanisms).

## §9 Phase 0 (D11) summary

| Finding | Tag | Disposition |
|---|---|---|
| F-OB-PRE-01 | revises-scope | absorbed as W-OB-7 at cycle-open 2026-05-06 |
| F-PHASE0-01 | informational | absorbed into W-OB-2 implementation discipline (conftest.py autouse fixture) |
| F-PHASE0-02 | informational | absorbed into W-OB-5 implementation sizing (effort estimate held) |
| F-PHASE0-03 | informational | pre-impl baselines (no-action; IR comparison anchor) |

No `aborts-cycle` findings. Pre-implementation gate fired GREEN.

## §10 Persona run-time + eval-corpus run-time

- 13-persona matrix: ~5 min wall-clock (opt-in via `HAI_RUN_PERSONA_MATRIX=1`;
  not a CI gate per AGENTS.md D10).
- `hai eval run --scenario-set all`: ~20s wall-clock for 135 fixtures.
- `uvx mypy src/health_agent_infra`: ~10s.
- `uvx bandit -ll -r src/health_agent_infra`: ~3s.
- Full pytest suite under broader warning gate: 80.7s.
