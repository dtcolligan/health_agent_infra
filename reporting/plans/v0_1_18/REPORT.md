# v0.1.18 Cycle Report — Onboarding-quality + intake-handler migration parity

**Tier:** substantive (D15) — W-OB-2 release-blocker leg.
**Phase 0 opened:** 2026-05-06 morning (after D14 close-in-place).
**Phase 1 opened:** same day after pre-implementation gate fired
`OPEN PHASE 1`.
**All 7 base W-ids closed:** same day (single-session push from cycle-
open through ship-prep, autonomous mode under maintainer ratification).
**D15 IR:** pending — prompt authored, handoff to maintainer for Codex
IR launch.

## §1 Cycle effort vs estimate

PLAN budgeted **5-9 days** for 7 W-ids. Actual implementation took
**one autonomous session**, roughly equivalent in tool-call density to
~1-2 days of maintainer work. Sources of compression:

- **W-OB-1** was mostly pre-staged 2026-05-04 (the cycle's README pivot
  landed alongside the v0.1.18 README scaffold). Implementation reduced
  to (a) verifying pre-staged delta, (b) sweeping 1 cross-reference in
  `agent_integration.md`, (c) authoring CHANGELOG entry. ~5 minutes.
- **W-OB-7's mechanical seam** was clean: 8 handlers all using the same
  `core.state.open_connection` pattern (verified at PLAN-author time),
  no exotic connection lifecycle. Two `replace_all` Edit calls landed the
  9 call-site updates (8 `conn = ...` + 1 `presence_conn = ...`). Test
  surface required iterative argv-shape correction (4 of 7 per-handler
  tests initially failed on wrong CLI flag names; 4 corrections
  converged).
- **W-OB-4a + W-OB-4b were dogfood gates, not commits.** Findings
  accumulated into `dogfood_findings.md`; ~30 minutes per pass.
- **W-OB-2's default-flip** lands as ~30 LOC in `cmd_init` reusing
  `check_onboarding_readiness` as the singular predicate. Snapshot
  regeneration cost one cycle through trailing-newline drift (cli_help_tree
  snapshot expects no trailing `\n`).
- **W-OB-5's `_NEXT_ACTION_REGISTRY`** caught 3 pre-impl drift entries
  via the manifest-consistency test on first run — `state migrate` /
  `intent training add-session` / `target set` were registry-False but
  manifest-True. Corrected in lockstep; the test serves as the durable
  invariant.

## §2 D14 audit-chain settling shape

| Round | Findings | Verdict |
|---|---:|---|
| 1 | 7 | PLAN_COHERENT_WITH_REVISIONS |
| 2 | 3 | PLAN_COHERENT_WITH_REVISIONS close-in-place |

**Halving signature 7 → 3** matches AGENTS.md empirical norm
`10 → 5 → 3 → 0`. v0.1.18 settled one round earlier than the substantive-
cycle norm because the catalogue is small (7 W-ids) and structurally low-
density (most rows reference established mechanisms — v0.1.13 W-AA
`hai init --guided`, v0.1.17 W-B body-comp migration, v0.1.17 W-29 cli.py
handler-group split).

## §3 Highlights

- **F-OB-PRE-01 closed end-to-end via W-OB-7.** The crash the maintainer
  hit on 2026-05-05 (`hai intake weight` → `OperationalError: no such
  table: body_comp`) is fixed via a small additive helper
  (`open_connection_with_migrations`) wrapping the existing seam. All
  8 `cmd_intake_*` handlers route through it; W-OB-4a dogfood verified
  the fix end-to-end against a synthetic schema-25 DB.
- **`hai init` default-flip lands cleanly via W-OB-2.** TTY users with
  incomplete onboarding state get the `--guided` flow automatically;
  CI / agent harnesses opt out via `--non-interactive` flag, env var,
  or simply running without TTY. 5-case test surface covers all paths.
- **`hai doctor` `next_action` field gives agents a structured surface.**
  W-OB-5 wires `next_action.{command,purpose,agent_safe,interactive}`
  into 5 doctor checks. The manifest-consistency test pins
  `agent_safe` against the live `hai capabilities --json` per-command
  values — a future drift would fail this test.
- **Multi-missing onboarding hint prefers umbrella.** Per F-OB-4A-02
  dogfood finding, when intent + target + wellness_pull are ALL missing
  (i.e. fresh user), the hint cites `hai init` (umbrella, post-W-OB-2
  default-flip shape) rather than `hai intent training add-session`
  (per-component). Single-missing case keeps the per-component command
  for targeted post-init drift.
- **Existing init-test stability preserved via F-PHASE0-01 conftest
  fixture.** Auto-opt-out of W-OB-2 default-flip via `HAI_INIT_NON_INTERACTIVE=1`
  env var means the suite is unaffected; new tests
  (`test_cli_init_default_flip.py`) explicitly `monkeypatch.delenv` to
  exercise the predicate.
- **No regression on the 13-persona matrix.** Identical baseline pre-
  and post-implementation: 13/13 reach `synthesized` cleanly, 0 findings,
  0 crashes. v0.1.18 doesn't change classifiers/policy; the consistent
  matrix is the expected behaviour, witnessed.

## §4 Deferrals

- **W-OB-4b TTY default-flip user-experience confirmation** — autonomous-
  mode subshell cannot exercise real TTY interaction. Unit-test analogue
  passes (`test_case_i_tty_plus_missing_fields_fires_guided` with
  monkeypatched isatty=True). **Deferred to maintainer ship-time manual
  gate** per RELEASE_PROOF §3. NOT a missed acceptance — the unit-test
  layer covers the predicate; the manual gate covers the UX.
- **F-OB-4A-01 (cross-cycle field-naming convention with `hai daily`)** —
  documented as a doctrine-alignment observation. W-OB-5 implementation
  used `command` as the primary structured field, which is the same
  shape `hai daily`'s gap output uses (`intake_command`); convention
  alignment is held at the field-name level, not enforced by test.

## §5 Lessons learned

### 5.1 Manifest-consistency tests catch real drift on first run

W-OB-5's `_NEXT_ACTION_REGISTRY` had 3 wrong `agent_safe` values that
the consistency test caught immediately. The pattern: hardcode-then-
verify is much more honest than guess-and-trust. Two-line cost (the
test); high-value durable invariant.

Generalise: any cycle that introduces a registry whose values must
match a primary surface (capabilities manifest, user-facing CLI, etc.)
should ship a consistency test in the same commit. Without it, the
registry silently drifts.

### 5.2 The PLAN-author's CLI-shape guesses for tests are unreliable

`test_intake_migration_parity.py` had 4 of 7 per-handler tests fail
on first run because of wrong CLI flag names: `--kcal` vs `--calories`,
`--slug` vs `--name`, missing `--session-id` for gym, `--from-state-snapshot`
required for gaps. Lesson: **read the live `--help` output before
authoring CLI test invocations**, not the production code's argparse
definitions or memory of similar commands.

The corrected pattern: `uv run hai <subcommand> --help | head -25`
before authoring the test invocation. Adds 30s; saves a debug round.

### 5.3 Autonomous mode + maintainer scope boundary

The user's directive was "execute every phase you can do without
maintainer input or Codex audit." Phase boundaries discovered during
the run:

- **Cannot replace maintainer's `pipx install` against their primary
  environment.** Substituted with isolated venv install — semantically
  equivalent for the smoke, reversible.
- **Cannot exercise real TTY interaction.** The unit-test analogue
  is the autonomous-mode-equivalent gate; the maintainer's interactive
  run is the UX layer.
- **Cannot run Codex.** D15 IR is the natural stopping point.

The pattern that worked: **pre-author every artifact at the level the
maintainer would otherwise stop and ask for**, then hand off cleanly.
RELEASE_PROOF + REPORT + IR prompt are all authored at v0.1.18 ship
state; the maintainer's role is ratification + Codex IR launch + ship.

### 5.4 Snapshot trailing-newline drift is a recurring papercut

Every cycle that adds a CLI flag has to regenerate
`cli_help_tree_v0_1_13.txt`. Using `print()` in the regen script adds a
trailing `\n` the test doesn't expect. The fix is `Path.write_text()`
without the auto-newline. This pattern should be documented in
`reporting/docs/snapshot_regen.md` (or similar) so future cycles don't
re-discover it. Not in v0.1.18 scope.

### 5.5 Doc-regen-with-version-bump should be in the ship-prep checklist

F-IR-01 caught the v0.1.18 ship-prep commit's omission: the
`pyproject.toml` version bumped 0.1.17 → 0.1.18 but
`reporting/docs/agent_cli_contract.md` (a generated doc that
embeds the version) didn't regenerate in lockstep. The gate test
`test_committed_contract_doc_matches_generated` failed under both
narrow and broader pytest runs.

The pattern: any cycle that bumps `pyproject.toml` version must
also regenerate every generated doc that embeds the version. The
implicit ship-prep checklist should add this step. Future cycles
should treat the doc regen as part of the version bump itself, not
a separate manual step.

### 5.6 Coarse status-string branching diverges from primitive state models

F-IR-04 caught a real correctness bug: W-OB-3's `next_action_hint`
keyed on `intent_target.status` (a derived string field) when
`check_onboarding_readiness` keyed on `intent_count` + `target_count`
+ `has_wellness_pull` (the underlying primitives). The string and
the primitives drifted: status="authored" can mean "intent + targets
authored" OR "only intent authored, all targets skipped." The hint
then said "Run `hai daily`" when the readiness check would WARN.

The lesson: when two surfaces consume the same state model, they
should read the same primitives. Derived strings introduce a layer
where divergence can hide. Prefer keying the second consumer on the
first's primitive fields (or on the same source-of-truth function),
not on a string the first emits.

This pattern is broader than W-OB-3: any future hint/render/decision
logic that consumes onboarding readiness should consult the same
intent/target/wellness_pull primitives, not the derived status string.

## §6 Open items for D15 IR

- **Manual ship-time TTY gate.** RELEASE_PROOF §3 documents this
  explicitly. IR may want to ratify the substitution shape (autonomous-
  mode unit-test + maintainer manual gate together = acceptance) or
  surface a stronger automated gate.
- **`open_connection_with_migrations` scope discipline.** The helper is
  intentionally intake-handler-scoped (additive, doesn't replace
  `open_connection` globally). IR may want to verify the read-path
  doctor checks intentionally don't migrate, or surface the boundary
  more loudly.
- **W-OB-5 registry exhaustiveness.** **CLOSED at IR R1 F-IR-03 +
  R2 F-IR-R2-01.** Registry now 11 commands; coverage extends to
  `check_config` (×2 paths), `check_sources`, `check_today` (×2),
  `check_intake_gaps` (×2), and the deep-probe `check_auth_intervals_icu`
  outcomes that map to concrete commands (CAUSE_2_CREDS → `hai auth
  intervals-icu`; NETWORK → `hai doctor`). CAUSE_1_CLOUDFLARE_UA +
  OTHER stay prose-only by design — their next-step text is
  diagnostic / triage-doc-pointer rather than a single concrete
  command. The "concrete command vs prose" rule is now codified by
  the test surface: every WARN/FAIL doctor result whose hint maps
  to a concrete CLI command MUST emit `next_action`; prose-style
  diagnostic hints MUST NOT.

## §7 Closure

v0.1.18 closes the onboarding-quality + intake-handler migration parity
PLAN.md authored 2026-05-06 in full. All 7 W-ids land at acceptance
under the standard substantive-cycle gates (W-OB-6 unfired per
conditional contract). The cycle ships as "onboarding-gap closure with
maintainer-side dogfood validation" — the foreign-user empirical claim
stays v0.1.19's.

The maintainer-driven actions remaining for ship:
1. Run the manual TTY gate per RELEASE_PROOF §3.
2. Launch Codex D15 IR with `codex_implementation_review_prompt.md`.
3. Triage IR findings (expected 2-3 rounds settling at
   SHIP / SHIP_WITH_NOTES).
4. Stamp HEAD into RELEASE_PROOF §1 + AUDIT.md after IR closes.
5. `git push origin main` + `uvx twine upload dist/*` per release toolchain.

v0.1.19 cycle opens next — foreign-user empirical session against the
shipped v0.1.18 wheel.
