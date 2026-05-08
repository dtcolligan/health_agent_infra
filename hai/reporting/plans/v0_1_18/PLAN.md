# v0.1.18 PLAN — Onboarding-quality + intake-handler migration parity

**Tier (D15):** **substantive** — W-OB-2 changes the default behaviour of `hai init` (the most-touched install-path command) and is therefore a release-blocker workstream per AGENTS.md D15 ("≥1 release-blocker workstream"). Total estimated effort 5-9 days falls below D15's `≥10 days` threshold, so the tier classification rests on the release-blocker leg, not the days leg. W-OB-7 is also a correctness-class fix (an unhandled crash on a real upgrade path) but is mechanically small (one shared seam, **eight callers**); it's tier-relevant as quality-floor evidence, not as a second release-blocker. **(Round-2 caller-count correction per F-PLAN-R2-02.)**

**Status:** **authored 2026-05-06, pre-D14 round 1.** PLAN.md is the artifact under audit; no code has changed against it. Phase 0 (D11) bug-hunt has not started. Cycle workspace at `reporting/plans/v0_1_18/`. Pre-PLAN finding F-OB-PRE-01 (intake-handler migration crash, surfaced 2026-05-05 on the maintainer's own state DB) is absorbed into this PLAN as a new W-OB-7 per the cycle-open decision recorded in `audit_findings.md`.

**Authored:** 2026-05-06 against HEAD `9c651da` (v0.1.17 ship-time freshness sweep + v0.1.18 F-OB-PRE-01 finding). v0.1.17 closed cleanly 2026-05-05; v0.1.18 promoted to next-active per the cancellation-renumber chain (`v0_1_16/README.md` cancellation note, `v0_1_18/README.md` insertion, `v0_1_19/README.md` foreign-user empirical destination).

**Estimated effort:** **5-9 days** (1 maintainer). See §5 arithmetic. Substantially smaller than v0.1.17's 25-40-day catalogue; v0.1.18 is intentionally a tight cycle aimed at closing onboarding gaps proactively before the v0.1.19 foreign-user empirical session.

**D14 expectation:** budget **2-3 rounds** per AGENTS.md empirical norm (twice-validated 10 → 5 → 3 → 0 settling at v0.1.11 + v0.1.12 + v0.1.17). v0.1.18's catalogue is small (7 W-ids), most rows have established source contracts (the v0.1.13 W-AA `hai init --guided` mechanism + the v0.1.17 `body_comp` migration that exposed F-OB-PRE-01), and there are no governance-edit-density triggers like v0.1.12 had. Realistic round expectation 2 — author may settle one round earlier than the substantive norm. Don't bet on it.

**Theme.** v0.1.13 W-AA shipped `hai init --guided` and `hai doctor onboarding_readiness` — the *mechanism* for easy onboarding. The maintainer's own state DB at v0.1.17 ship-time still showed `onboarding_readiness: WARN: missing intent` (`intent_count: 0`), which means the gap is **discoverability and upgrade ergonomics**, not mechanism. v0.1.18 closes that gap before exposing it to a foreign user in v0.1.19. **Ship claim:** the install-and-upgrade path through `hai init` is friction-free for both fresh-install and upgrade-from-old-DB cases, with `hai doctor` actionably hinting at the right next command, intake handlers no longer crash on pending-migration DBs, and the maintainer has dogfood-validated the full path against a locally built wheel. Sequenced upstream of v0.2.0 via v0.1.19 (the renumbered foreign-user empirical cycle); v0.1.18 does not add new v0.2.0 scope or schema dependencies. **(Round-2 revision per F-PLAN-05: original "parallelizable with v0.2.0" claim was inherited from v0.1.17 PLAN; v0.1.18 sits upstream of v0.2.0 via the v0.1.18 → v0.1.19 → v0.2.0 chain in `tactical_plan_v0_1_x.md:52`.)**

**Source inputs:**
- `reporting/plans/v0_1_18/README.md` — provisional scope catalogue (originally 6 W-OB-* W-ids; W-OB-7 added 2026-05-06 per F-OB-PRE-01).
- `reporting/plans/v0_1_18/audit_findings.md` §F-OB-PRE-01 — intake-handler migration crash; surfaced 2026-05-05 on the maintainer's own DB after upgrade to v0.1.17 without re-running `hai init`.
- `reporting/plans/v0_1_17/RELEASE_PROOF.md` — v0.1.17 closure (W-29 cli.py split + W-B body-comp migration 026 in tree). v0.1.18 lands cleanly post-W-29 because every CLI edit lands in a discrete handler-group module.
- `reporting/plans/v0_1_13/` — original W-AA build (`hai init --guided` + `hai doctor onboarding_readiness`). The mechanism this cycle re-surfaces.
- `reporting/plans/v0_1_19/README.md` — downstream foreign-user empirical cycle. v0.1.18 must produce a PyPI-installable build that v0.1.19 runs the foreign-user session against.
- `reporting/plans/tactical_plan_v0_1_x.md` §5E — tactical row for v0.1.18 (onboarding-quality cycle).
- `~/.claude/projects/-Users-domcolligan-health-agent-infra/memory/project_intake_handlers_dont_apply_migrations.md` — maintainer memory cross-reference for F-OB-PRE-01.

---

## 1. What this release ships

### 1.1 Theme

Onboarding ergonomics + upgrade-path correctness over a single small cycle, against the package shape v0.1.17 published. Two threads:

**Thread 1 — UX surfacing of v0.1.13 W-AA mechanism.** The `--guided` flow exists; users on an interactive terminal don't discover it. The thread closes the gap via three coordinated edits:

1. **W-OB-1** — README quickstart pivots to `hai init --guided` as the default install-time command (mostly pre-staged on `main` 2026-05-04; this cycle ratifies + sweeps cross-references for stale `hai auth intervals-icu` calls).
2. **W-OB-2** — `hai init` itself promotes to `--guided` automatically when stdin is a TTY *and* `onboarding_readiness` reports missing fields. Non-interactive callers (CI, agent harnesses) opt out via `--non-interactive` flag or `HAI_INIT_NON_INTERACTIVE=1` env var. The default-flip is the release-blocker — it changes existing users' first-run experience and must not break automation.
3. **W-OB-5** — `hai doctor onboarding_readiness` adds a machine-parsable `next_action` field + sharper hint text so agent consumers can route the user to the right command without prose-parsing.

**Thread 2 — Upgrade-path correctness.** F-OB-PRE-01 (surfaced 2026-05-05 on the maintainer's own DB) shows intake handlers crash with `OperationalError: no such table: body_comp` when invoked on a state DB whose schema head is behind the package head. The fix is mechanically small — every intake handler currently opens its connection via `core.state.open_connection` (which does not apply pending migrations); a new `open_connection_with_migrations` variant in `core/state/store.py` runs `apply_pending_migrations` on the freshly-opened connection. The same `apply_pending_migrations` function is what `cmd_state_init` reaches through `initialize_database` (`core/state/store.py:316,335`) on a fresh-DB `hai state init` invocation. W-OB-7 is the absorbing W-id. **(Round-2 revision per F-PLAN-01: original described "raw `sqlite3.connect` → `connect_and_migrate`" but every intake handler already uses `open_connection`; corrected.)**

**Cross-cutting validation thread.** W-OB-3 reviews the `--guided` prompt content (intent/target stickiness, refusal paths, post-prompt summary). **W-OB-4a** dogfoods the upgrade-from-old-DB scenario in Phase 1 (witnesses W-OB-7 fix); **W-OB-4b** dogfoods the clean-install scenario in Phase 2 against a **locally built wheel** (post-W-OB-2; release-blocker for the default-flip claim). Post-publish PyPI verification is RELEASE_PROOF / ship-time concern, separate from the in-cycle ship gate. W-OB-6 is a conditional absorption slot reserved for any structural finding W-OB-4a/W-OB-4b surfaces.

**Honesty boundary.** v0.1.18's claim is **"the maintainer can install or upgrade health-agent-infra against a locally built wheel and reach a synthesized recommendation without surprise."** It is **not** "a non-maintainer completed the full flow under recorded observation" — that remains v0.1.19's claim. v0.1.18's W-OB-4a + W-OB-4b dogfoods are the maintainer running the path; v0.1.19's foreign-user session is the empirical proof. **(Round-2 wording correction per F-PLAN-R2-01: original "PyPI install" was the pre-split shape; v0.1.18's pre-ship gate uses a locally built wheel because v0.1.18 is unpublished at gate time.)**

### 1.2 Workstream catalogue (7 W-ids)

| Section | W-id | Title | Effort | Source | Severity |
|---|---|---|---|---|---|
| §2.A | **W-OB-1** | README quickstart pivot to `hai init --guided`; sweep stale `hai auth intervals-icu` references; verify pre-staged 2026-05-04 delta | 0.5 d | `v0_1_18/README.md` provisional row 1; partly pre-staged on `main` | doctrine-gap |
| §2.B | **W-OB-2** | `hai init` default-flip: promote to `--guided` when stdin is TTY and `onboarding_readiness` reports missing fields; `--non-interactive` + `HAI_INIT_NON_INTERACTIVE=1` opt-outs | 1-2 d | `v0_1_18/README.md` provisional row 2; maintainer's own-DB `intent_count=0` evidence | release-blocker (default-behaviour change; CI/agent automation must not break) |
| §2.C | **W-OB-3** | `--guided` prompt content review: intent stickiness, target prompts, refusal paths, post-prompt summary; tests for refusal + resume | 1-2 d | `v0_1_18/README.md` provisional row 3; UX judgment call | UX-gap |
| §2.D | **W-OB-4a** | Early-evidence dogfood (Phase 1, against W-OB-1 + W-OB-7 in tree) — synthetic v0.1.16-shaped DB upgrade scenario; exercises W-OB-7 fix in upgrade context; findings inform W-OB-3 prompt content | 0.5 d | `v0_1_18/README.md` provisional row 4; F-OB-PRE-01 upgrade-path expansion | empirical-substitute |
| §2.D | **W-OB-4b** | Post-W-OB-2 local-wheel smoke (Phase 2, after W-OB-2 lands) — `uvx --from build python -m build` then `pipx install <wheel-path>`; clean-install scenario witnessing default-flip on interactive TTY | 0.5 d | F-PLAN-04 round-1 split — original W-OB-4 sequencing couldn't validate post-W-OB-2 behaviour | release-blocker (the post-W-OB-2 default-flip claim has no other ship-gate witness) |
| §2.E | **W-OB-5** | `hai doctor` actionability across checks-with-hints: hint text refresh + machine-parsable `next_action` field for agent consumers (runtime-only, no capabilities manifest extension per OQ-4) | 0.5-1 d | `v0_1_18/README.md` provisional row 5 | doctrine-gap |
| §2.F | **W-OB-6** *(conditional)* | Absorption slot for any structural finding W-OB-4 surfaces (not prompt-content — that's W-OB-3) | bounded by W-OB-4 | conditional | TBD |
| §2.G | **W-OB-7** | Intake-handler migration parity: every `cmd_intake_*` handler applies pending migrations on connect, matching `hai state init`'s `apply_pending_migrations` path | 0.5-1 d | `v0_1_18/audit_findings.md` §F-OB-PRE-01 (added 2026-05-06 per cycle-open decision) | correctness-residual (real crash on real upgrade path) |

**Total:** 7-8 W-ids (6 base catalogue rows; W-OB-4 split into W-OB-4a + W-OB-4b at D14 R1; W-OB-7 absorption; W-OB-6 conditional), **5-9 days estimated effort** (per-WS arithmetic 4.5-8.5, +inter-WS coordination overhead ~5%; see §5), substantive tier (W-OB-2 release-blocker leg).

### 1.3 Sequencing (DAG)

**Phase 1 — Foundation + low-risk evidence (lands first; surfaces W-OB-4a inputs):**

1. **W-OB-1** — README pivot ratification + cross-reference sweep. Mostly pre-staged on `main`; this WS verifies and closes any drift. Independent of all other W-ids; lands first because it's the lowest-risk surface and the W-OB-4a dogfood reads the README cold.
2. **W-OB-7** — intake-handler migration parity. Lands early because it's mechanically small and the W-OB-4a upgrade-path scenario depends on the fix being in tree (otherwise the dogfood will hit the F-OB-PRE-01 crash and the upgrade scenario doesn't validate the no-crash claim). Sequencing W-OB-7 → W-OB-4a is **load-bearing** for the upgrade scenario to be meaningful.
3. **W-OB-4a** — early-evidence dogfood pass against the W-OB-1 + W-OB-7-shipped tree. **Upgrade-from-old-DB scenario** (witnesses W-OB-7 fix in realistic upgrade context). Output is `dogfood_findings.md` in the cycle dir. Findings inform W-OB-3 prompt content review; structural findings absorb into W-OB-6 if applicable.

**Phase 2 — Default behaviour change + actionability + post-W-OB-2 smoke (informed by Phase 1 evidence):**

4. **W-OB-3** — `--guided` prompt content review. **Informed by W-OB-4a findings** (the early-dogfood pass surfaces what's confusing in practice). Touches `core/init/onboarding.py` (the `run_guided_onboarding` orchestrator) + tests.
5. **W-OB-2** — `hai init` default-flip. The release-blocker. Lands after W-OB-3 because the prompt content needs to be solid before the default path routes through it. Touches `cli/handlers/config_init.py:cmd_init` + capabilities manifest (new `--non-interactive` flag). New env-var contract `HAI_INIT_NON_INTERACTIVE=1`.
6. **W-OB-4b** — post-W-OB-2 local-wheel smoke. **Clean-install scenario** against a locally built wheel (`uvx --from build python -m build` then `pipx install <wheel-path>` — NOT a PyPI install, since v0.1.18 isn't published yet at this gate). Witnesses the post-W-OB-2 default-flip on interactive TTY. **Release-blocker** for the post-W-OB-2 ship claim. Output appends to `dogfood_findings.md`.
7. **W-OB-5** — `hai doctor` actionability across checks-with-hints. Touches `core/doctor/checks.py` (multiple checks where `next_action` companions an existing `hint`) + `core/doctor/render.py` rendering. Sequenced after W-OB-2 so `next_action.command` references the post-default-flip command shape.

**Phase 3 — Conditional close-out:**

8. **W-OB-6** *(conditional)* — absorbs any W-OB-4a / W-OB-4b structural finding not already covered by W-OB-3 prompt content or W-OB-5 doctor actionability. If neither dogfood pass surfaces a structural finding, this WS does not fire and the cycle's W-id count is 7 (6 base + W-OB-7), with W-OB-6 explicitly named "no W-OB-6-class findings" in RELEASE_PROOF (per OQ-7 Codex disposition).

**Cross-phase merge friction.** All edits land in distinct files post-W-29 split (W-OB-1 in README.md; W-OB-2 in `cli/handlers/config_init.py`; W-OB-3 in `core/init/onboarding.py`; W-OB-5 in `core/doctor/{checks,render}.py`; W-OB-7 across `cli/handlers/intake.py` callers + new `open_connection_with_migrations` in `core/state/store.py`). Recommended commit cadence: atomic per-W-id commits (W-OB-4a/4b are dogfood-evidence WSs producing findings document, not code commits — they fire as separate "verification gate" boundaries, not commits). Total commits 6 (W-OB-1, W-OB-7, W-OB-3, W-OB-2, W-OB-5, optional W-OB-6).

### 1.4 Source provenance + cycle thesis

This cycle's catalogue inherits from two independent provenance chains plus one in-cycle absorption:

**Chain A — v0.1.16-cancellation restructure (2026-05-04).** v0.1.16 was originally scoped as the foreign-user empirical cycle; its named candidate became unavailable 2026-05-04. The maintainer's directive: "do v0.1.17 (maintainability + eval substrate) first, then close the onboarding gap proactively (this cycle), then run a real foreign-user empirical pass (v0.1.19), then v0.2.0." v0.1.18 was inserted between v0.1.17 ship and v0.1.19 open as a **proactive onboarding-gap closure cycle** so the v0.1.19 foreign-user session isn't burnt on issues we already know about. The thesis is documented in `v0_1_18/README.md`: "the infrastructure for easy onboarding already shipped in v0.1.13 (`hai init --guided`, `hai doctor onboarding_readiness`), but the maintainer's own state DB still shows `onboarding_readiness: WARN: missing intent` (`intent_count: 0`). That means the gap is in surfacing/discoverability/UX, not in mechanism."

**Chain B — F-OB-PRE-01 in-cycle absorption.** Surfaced 2026-05-05 evening on the maintainer's own state DB after upgrading the wheel to v0.1.17 without running `hai init`: `hai intake weight --kg 82.0 ...` crashed with `OperationalError: no such table: body_comp` because v0.1.17 added migration 026 (`body_comp`) that hadn't been applied. Other intake handlers (stress, nutrition, note) wrote fine on the same DB on the same call cycle — they don't touch the v0.1.17-added table. The fix shape is mechanically clean (`apply_pending_migrations` exists at `core/state/store.py:243` and is already used by `hai state init`); the fix is "every intake handler routes through the same connect-and-migrate seam." Filed in `audit_findings.md` 2026-05-05; absorbed as W-OB-7 at cycle-open 2026-05-06 per maintainer decision (option A in audit_findings.md disposition table). The alternative absorption — folding into W-OB-5's `next_action` hint — was rejected because the underlying behaviour is a code bug, not a discoverability gap.

**Cycle thesis.** **The install/upgrade path is the easy path, not the buried `--guided` flag and not a hint pointing to a workaround.** v0.1.18 ships when (a) the README's first-run instructions are correct for both fresh-install and upgrade users, (b) `hai init` defaults to the right thing on an interactive terminal, (c) `hai doctor` actionably tells agent consumers what command to run next, (d) intake handlers don't crash on pending-migration DBs, and (e) the maintainer has dogfood-validated the full path against a locally built wheel (W-OB-4a + W-OB-4b). Post-publish PyPI verification is RELEASE_PROOF concern, not in-cycle.

**Honesty boundary (re-stated for §6 ship gates).** v0.1.18's W-OB-4a + W-OB-4b are **maintainer dogfood, not a foreign-user transcript**. The cycle ships honestly as "onboarding-gap closure with maintainer-side dogfood validation," not "foreign-user-validated onboarding." v0.1.19 owns the foreign-user claim.

---

## 2. Per-workstream contracts

### §2.A W-OB-1 — README quickstart pivot to `hai init --guided` (mostly pre-staged)

**Source.** `v0_1_18/README.md` provisional scope row 1; partly pre-staged on `main` 2026-05-04 alongside the v0.1.18 README scaffold.

**Files of record:**
- `README.md` § "Install and quickstart" (lines 206-244 at HEAD `9c651da`).
- Cross-references: any other doc that cites the install-time command sequence (search corpus: `reporting/docs/agent_integration.md`, `reporting/docs/current_system_state.md`, `reporting/docs/onboarding.md` if it exists, `CHANGELOG.md`).

**Pre-staged delta verification (Phase 1 open, before W-OB-1 commits).** README.md § "Install and quickstart" already shows `hai init --guided` as the recommended interactive command (line 214) and explains idempotency + when to use bare vs `--guided` (lines 221-226). The W-OB-1 commit verifies the pre-staged delta is correct against the HEAD state and sweeps for stale references that the pre-staging missed.

**Acceptance.**
1. README.md § "Install and quickstart" is internally consistent: every command shown either runs cleanly on a fresh install or has a `# (idempotent — safe to rerun)` annotation. No reference to `hai auth intervals-icu` as an install-time step (the `--guided` flow now invokes auth interactively); the existing line 154 reference inside an agent-integration manifest example is allowed because that's a contract example, not an install instruction.
2. Cross-reference sweep: every doc under `reporting/docs/` that cites a `hai init` invocation cites the post-W-OB-1 form. Sweep performed via `grep -rn "hai init" reporting/docs/ README.md CHANGELOG.md`; any stale `hai init --guided` mention with conflicting context is corrected.
3. `CHANGELOG.md` v0.1.18 entry names W-OB-1 as a doc-only doctrine clarification.
4. No code change in this WS. No test change. Pure docs.

**What this WS does NOT do.**
- Does not change `hai init` behaviour (W-OB-2's job).
- Does not change `--guided` prompt content (W-OB-3's job).
- Does not introduce new commands or flags.

### §2.B W-OB-2 — `hai init` default-flip (release-blocker)

**Source.** `v0_1_18/README.md` provisional scope row 2; maintainer's own-DB evidence (`onboarding_readiness: WARN: missing intent`, `intent_count: 0` at v0.1.17 ship-time) demonstrating the gap.

**Files of record:**
- `src/health_agent_infra/cli/handlers/config_init.py:cmd_init` (line 420). The default-flip decision lives in this handler — not in argparse defaults — because the decision depends on runtime state (TTY check + `onboarding_readiness` query), not parse-time defaults.
- `src/health_agent_infra/cli/__init__.py` parser-tree builder (post-W-29 split). New `--non-interactive` flag on `hai init`.
- `verification/tests/snapshots/cli_capabilities_v0_1_17.json` (or the post-v0.1.17 current snapshot) — the new flag is an intentional surface add; snapshot regenerates per F-PLAN-07-style discipline.
- `verification/tests/test_cli_init_default_flip.py` (new) — covers **five cases** (per OQ-2): (i) interactive TTY + missing fields → `--guided` fires; (ii) interactive TTY + complete state → bare init; (iii) non-interactive (no TTY) → bare init regardless of state; (iv-flag) `--non-interactive` flag with `isatty()==True` and missing fields → bare init (explicit flag opt-out); (iv-env) `HAI_INIT_NON_INTERACTIVE=1` with `isatty()==True` and missing fields → bare init (explicit env opt-out).

**Default-flip decision logic (PLAN-author proposal; exact predicate ratifiable at implementation).**

```
if args.guided:
    # explicit user request — honour
    fire_guided = True
elif args.non_interactive or os.environ.get("HAI_INIT_NON_INTERACTIVE") == "1":
    # explicit opt-out — honour
    fire_guided = False
elif not sys.stdin.isatty():
    # CI / agent harness / pipe — opt-out implicitly
    fire_guided = False
else:
    # interactive terminal — check onboarding_readiness state
    readiness = check_onboarding_readiness(...)
    fire_guided = (readiness["status"] in {"WARN", "FAIL"})
```

**Acceptance.**
1. Default-flip decision logic implemented in `cmd_init` per the proposal above (or a maintainer-ratified equivalent). Decision is **logged at INFO level** to the cmd_init audit row so post-hoc analysis can confirm which path fired.
2. `hai init --non-interactive` is a new long flag on the `hai init` parser; `HAI_INIT_NON_INTERACTIVE=1` is a new env-var contract documented in the help text. Both opt-outs are equivalent.
3. `test_cli_init_default_flip.py` covers **five cases** (round-1 expanded per OQ-2 Codex disposition): (i) interactive TTY + missing fields → `--guided` fires; (ii) interactive TTY + complete state → bare init; (iii) non-interactive (no TTY) → bare init regardless of state; (iv-flag) `--non-interactive` flag with `isatty()==True` and missing fields → bare init (explicit flag opt-out); (iv-env) `HAI_INIT_NON_INTERACTIVE=1` with `isatty()==True` and missing fields → bare init (explicit env opt-out). Each test uses `monkeypatch` of `sys.stdin.isatty` + `os.environ` rather than launching subprocesses.
4. `hai capabilities --json` regenerates with the new flag visible at `commands[hai init].flags[--non-interactive]`. Snapshot regenerates in lockstep with the W-OB-2 commit.
5. Existing `cmd_init` tests continue to pass — the default-flip is *additive*; explicit `--guided` and explicit `--non-interactive` continue to behave as before.
6. `CHANGELOG.md` v0.1.18 entry names W-OB-2 with user-facing wording **"interactive `hai init` default (with opt-out)"** (per OQ-6 Codex disposition; internal "default-flip" term stays in PLAN/audit-trail vocabulary). Opt-out path documented: `--non-interactive` flag OR `HAI_INIT_NON_INTERACTIVE=1` env var OR no TTY.
7. Full pytest suite (narrow + broader warning gates) green post-W-OB-2.

**What this WS does NOT do.**
- Does not change `--guided` prompt content (W-OB-3).
- Does not change `onboarding_readiness` check logic (W-OB-5).
- Does not autonomously author intent or target rows — the default-flip routes the user to the existing `--guided` flow, which **prompts**, respecting W57.

**Ship-claim gate:** acceptance items 1, 3, 4 are **release-blocker**. The default-flip must not break CI / agent harnesses calling `hai init` without TTY (item 3 case iii), and the new flag must surface in capabilities (item 4) so agent consumers can route around it.

### §2.C W-OB-3 — `--guided` prompt content review

**Source.** `v0_1_18/README.md` provisional scope row 3; UX judgment call. **Informed by W-OB-4a dogfood findings** (sequenced after W-OB-4a in §1.3).

**Files of record:**
- `src/health_agent_infra/core/init/onboarding.py` — the `run_guided_onboarding` orchestrator + prompt definitions (path verified post-v0.1.13 W-AA build; if v0.1.17 W-29 split moved init code, the path adjusts).
- `verification/tests/test_init_onboarding_flow.py` (existing — the actual W-AA deterministic gate per v0.1.13 RELEASE_PROOF lines 166-172) — covers existing prompt flow; W-OB-3 extends with refusal-path + resume tests. **(Round-2 revision per F-PLAN-06: original cited non-existent `test_guided_onboarding.py`.)**

**Review surfaces (per W-OB-4a findings):**
- **Intent prompt stickiness.** Does the user understand what an "intent" is by the time they're asked? Does the prompt offer a sane default (e.g., "general fitness, no specific goal") for users who don't have a sport-specific intent?
- **Target prompts.** Macros target prompts must respect "ask, pull, or refuse the personalised claim" (`feedback_never_assume_personal_data.md`). No placeholder defaults like 2000 kcal.
- **Refusal paths.** What happens if the user provides empty / no input or hits Ctrl-C mid-prompt? Existing `_run_guided_onboarding` already handles `interrupted` and `partial` statuses (`config_init.py:607`); W-OB-3 verifies the user-facing copy is clear and the resume hint cites the right command. **Note:** the current orchestrator treats unrecognized focus text as skipped (an empty-input affordance); W-OB-3 reviews the copy around that affordance but does NOT add a literal `skip` keyword.
- **Post-prompt summary.** What does the user see when `--guided` completes? Does it surface what was authored, what was deferred, and what the next agent-driven session will look like?

**Acceptance.**
1. Each review surface has a documented decision (kept-as-is / revised) in a section of the W-OB-3 commit message OR in `reporting/plans/v0_1_18/guided_prompt_review.md` (new file in cycle dir).
2. Refusal-path tests cover: (a) user provides empty input (Enter / no-input) at intent prompt → flow treats as skipped and continues with `intent_count=0` and post-prompt summary names the gap. **Note:** the current orchestrator treats unrecognized focus text as skipped (an empty-input affordance, not a literal `skip` keyword); W-OB-3 does NOT add a new affordance under a content-review WS — if a literal `skip` keyword is desired, that's a flow-shape change scoped out of W-OB-3 (per F-PLAN-06). (b) User hits Ctrl-C mid-target prompt → status becomes `interrupted` and the existing hint surfaces; (c) user runs `hai init --guided` a second time after a partial run → flow resumes from the first incomplete step (idempotency claim from README.md:221).
3. Post-prompt summary, if revised, is asserted by an existing or new test that captures stdout and matches against expected substrings (not exact text, to allow copy-edits).
4. No autonomous intent or target authoring — every prompt that would author a row prompts the user first (W57 invariant).
5. Full pytest suite green post-W-OB-3.
6. Post-prompt summary surfaces a content-only "next action" hint pointing the user at `hai today` or `hai daily` as the next agent-driven step — **content-only addition; no new flow step** (per OQ-5 Codex disposition).

**What this WS does NOT do.**
- Does not change which prompts fire — the flow shape from v0.1.13 W-AA is preserved. W-OB-3 reviews **content** within that shape.
- Does not change `hai init` default behaviour (W-OB-2).

### §2.D W-OB-4a + W-OB-4b — Self-onboard dogfood pass (split per F-PLAN-04 round 1)

**Source.** `v0_1_18/README.md` provisional scope row 4; F-OB-PRE-01 upgrade-path expansion (per cycle-open decision 2026-05-06); D14 round-1 F-PLAN-04 split — original single W-OB-4 was sequenced before W-OB-2 and could not validate the post-W-OB-2 default-flip claim. Codex closure recommendation: keep an early dogfood pass, add a post-W-OB-2 local-wheel smoke.

**Why split into two passes.** Two distinct goals: (a) early-evidence informing W-OB-3 prompt content + witnessing W-OB-7 in upgrade context (Phase 1, pre-W-OB-2); (b) release-blocker witness that W-OB-2's default-flip actually fires on an interactive TTY against a packaged build (Phase 2, post-W-OB-2). One pass cannot serve both.

**Why local wheel, not PyPI install.** v0.1.18 is unpublished at ship-gate time. Scenario 1's pre-ship gate cannot depend on the final PyPI artifact existing. Local-wheel smoke (`uvx --from build python -m build` then `pipx install <wheel-path>`) is the substantive gate; post-publish PyPI verification is RELEASE_PROOF / ship-time concern, separate from the in-cycle ship gate.

**Files of record (shared output):**
- `reporting/plans/v0_1_18/dogfood_findings.md` (new) — finding-per-finding write-up, with a `cycle_impact` tag per finding (`absorbs-into-WS` / `revises-scope` / `aborts-cycle` / `informational`) using the same convention as `audit_findings.md`. Both W-OB-4a + W-OB-4b append to this file (separate sections).

---

#### W-OB-4a — Early-evidence dogfood (Phase 1)

**Scenario — upgrade from synthetic v0.1.16-shaped DB:**
1. Construct a synthetic v0.1.16-shaped state DB at `~/.local/share/health_agent_infra/state.db` (schema head 25, pre-W-B). Priority order per OQ-3 Codex disposition: (c) snapshot the maintainer's real pre-v0.1.17 DB if available (most realistic); else (a) install v0.1.16 wheel, run `hai init`, then upgrade in place; **last resort** (b) hand-construct via `hai state init` + targeted migration rollback (document the exact mutation in `dogfood_findings.md` if used).
2. Run a mix of intake commands the user might naturally try first against the post-W-OB-7-shipped tree (HEAD with W-OB-1 + W-OB-7 commits in tree but W-OB-2 NOT yet landed): `hai intake weight ...` (the F-OB-PRE-01 reproducer), `hai intake exercise ...`, `hai intake gaps`, `hai daily`. Record what works, what doesn't, what the user sees.
3. Specifically test: `hai intake weight` post-upgrade does NOT crash (W-OB-7 acceptance witness). `hai intake exercise` and `hai intake gaps` similarly do not crash on the schema-behind DB.

**W-OB-4a acceptance.**
1. `dogfood_findings.md` § "W-OB-4a Phase 1 — upgrade-from-old-DB" exists with at least one finding entry (or "no findings" written explicitly with the test surface + commands run + DB-construction approach documented).
2. Every finding has a `cycle_impact` tag and a recommended absorption (W-OB-3 prompt content / W-OB-5 doctor hint / W-OB-6 conditional / informational).
3. The W-OB-7-fixed handlers (`weight`, `exercise`, `gaps`, all migration-touching `cmd_intake_*`) succeed against the schema-25 DB.
4. Every UX finding routes to W-OB-3 / W-OB-5 / W-OB-6; no silent drop.

---

#### W-OB-4b — Post-W-OB-2 local-wheel smoke (Phase 2)

**Scenario — clean install on throwaway env against locally built wheel:**
1. After W-OB-2 commits, build the local wheel: `uvx --from build python -m build --wheel`.
2. On a clean machine (or `pipx uninstall health-agent-infra && rm -rf ~/.local/share/health_agent_infra/`), `pipx install <wheel-path>`.
3. Read `README.md` § "Install and quickstart" cold (no prior knowledge).
4. Run **bare** `hai init` on an interactive TTY. **Verify the default-flip fires** — i.e. the `--guided` flow auto-promotes per W-OB-2's contract. Observe prompts, complete or refuse as a real user might, record findings.
5. After init completes, run `hai capabilities --human`, `hai doctor`, `hai daily`, `hai today`. Reach a synthesized recommendation OR document the blocker.
6. Separately verify non-interactive opt-out: `HAI_INIT_NON_INTERACTIVE=1 hai init` (still on TTY) returns to bare-init behaviour.

**W-OB-4b acceptance.**
1. `dogfood_findings.md` § "W-OB-4b Phase 2 — clean-install local-wheel smoke" exists with at least one finding entry (or "no findings" written explicitly).
2. Every finding has a `cycle_impact` tag.
3. **Release-blocker:** bare `hai init` on interactive TTY against the locally built wheel demonstrably enters the `--guided` flow (default-flip witness). If it does not, **the cycle does not ship** until W-OB-2 is rebuilt.
4. **Release-blocker:** `HAI_INIT_NON_INTERACTIVE=1 hai init` skips the guided flow (opt-out witness).
5. Every UX finding routes to W-OB-3 / W-OB-5 / W-OB-6; no silent drop.

---

**What W-OB-4a + W-OB-4b do NOT do.**
- Do not produce a foreign-user transcript (v0.1.19's claim).
- Do not run a recorded session against a non-maintainer (also v0.1.19).
- Do not depend on a published PyPI artifact (v0.1.18 is unpublished pre-ship; W-OB-4b uses a locally built wheel).
- Do not commit code — W-OB-4a/4b produce findings documents; absorbing W-ids commit code.

### §2.E W-OB-5 — `hai doctor` actionability across checks-with-hints

**Source.** `v0_1_18/README.md` provisional scope row 5. **Round-2 scope-widening per F-PLAN-03:** the original PLAN scoped W-OB-5 to `check_onboarding_readiness` only, but acceptance item 1 covered "FAIL with migration-behind" — that case is `check_state_db`'s, not `check_onboarding_readiness`'s. Codex disposition: widen the contract to "every doctor check that emits a `hint` today is a candidate for a structured `next_action` companion field," with `onboarding_readiness` as the primary surface but coverage extending to `state_db` (migration-behind), the auth checks (`check_auth_garmin`, `check_auth_intervals_icu`), and any other hint-emitting check.

**Files of record:**
- `src/health_agent_infra/core/doctor/checks.py` — multiple checks gain `next_action` companions: `check_onboarding_readiness` (line 470), `check_state_db` (line 84), `check_auth_garmin` (line 155), `check_auth_intervals_icu` (line 190), `check_skills` (line 239), etc. (every check that already emits `hint`). **(Round-2 correction per F-PLAN-R2-03: original PLAN cited a non-existent `check_credentials`; the actual auth checks live under `check_auth_garmin` + `check_auth_intervals_icu`.)**
- `src/health_agent_infra/core/doctor/render.py:_render_onboarding_readiness` (line 105) and the sibling per-check renderers.
- `verification/tests/test_doctor.py` (existing — extend) or new file `test_doctor_next_action.py`.
- **Not a capabilities manifest schema delta** (per OQ-4 Codex disposition): `next_action` lives at the runtime check level, not in `hai capabilities --json`. The manifest schema freeze (v0.2.3 W-30 territory) remains untouched.

**`next_action` schema (PLAN-author proposal — corrected per F-PLAN-02):**

```json
{
  "name": "onboarding_readiness",
  "status": "WARN",
  "summary": "missing intent",
  "details": {...},
  "hint": "run `hai init` to author your initial intent (interactive)",
  "next_action": {
    "command": "hai init",
    "purpose": "author initial intent and target",
    "agent_safe": false,
    "interactive": true
  }
}
```

**Schema invariants** (round-1 corrections per F-PLAN-02):

- `next_action.command` references the **post-W-OB-2 default-flipped command shape** (`hai init`, not `hai init --guided` — under W-OB-2 the bare command auto-promotes when stdin is a TTY and onboarding is incomplete).
- `next_action.agent_safe` **mirrors the live capabilities-manifest entry** for the cited command. `hai init` is `agent_safe: false` per `cli_capabilities_v0_1_13.json:4` + `reporting/docs/agent_cli_contract.md`; W-OB-5 must not emit `agent_safe: true` for it. Acceptance includes a consistency assertion against the live manifest, not just a copy-from-PLAN.
- `next_action.interactive` is the net-new W-OB-5 contract: commands requiring user TTY interaction surface `interactive: true` so agent consumers know to surface the command to the user rather than auto-running.
- `hint` (existing prose surface) stays; `next_action` is the structured-form companion. Agents reading `hai doctor --json` pattern-match on `next_action.command` rather than parsing hint prose.

**Acceptance.**
1. `next_action` field added to every doctor check that emits `hint` today, where the hint maps to a concrete command (vs prose like "investigate manually"). Coverage at minimum: `check_onboarding_readiness` (missing **intent / target / wellness_pull** per the function's own docstring at lines 478-481), `check_state_db` (no DB; migration-behind via `pending_migrations` field at `core/doctor/checks.py:146`), `check_auth_intervals_icu` and `check_auth_garmin` (where the hint maps to a concrete `hai auth ...` command). PASS-status results omit `next_action`. **(Round-2 correction per F-PLAN-R2-03: onboarding_readiness covers wellness_pull, not "credentials"; credentials live in the auth checks.)**
2. `next_action.command` strings reference the post-W-OB-2 default-flipped shape — for the missing-intent case, `command == "hai init"` (not `"hai init --guided"`). Asserted by an explicit test.
3. `next_action.agent_safe` matches the live capabilities-manifest entry for the cited command. Asserted by a consistency test that loads `hai capabilities --json` and cross-checks `next_action.agent_safe` against `commands[name].agent_safe` for every emitted `next_action.command`.
4. `next_action.interactive` is `true` for any command requiring TTY (anything routing through `cmd_init`'s default-flip path); `false` otherwise.
5. `_render_onboarding_readiness` (and sibling renderers) include the `next_action.purpose` line in human-readable rendering so `hai doctor` text output is sharper.
6. Tests cover at least three checks (`onboarding_readiness`, `state_db`, `check_auth_intervals_icu`): WARN-with-next-action; PASS-without-next-action; FAIL-with-next-action; manifest-consistency assertion.

**What this WS does NOT do.**
- Does not change any doctor check's **decision logic** (what counts as PASS / WARN / FAIL). Only the **output schema** gains a structured `next_action` companion to the existing `hint` field. (Round-2 clarification per F-PLAN-03.)
- Does not auto-run `next_action.command` — that's W57-violating. The field is **informational** for agent consumers.
- Does not extend `hai capabilities --json` schema (per OQ-4 Codex disposition; runtime-only contract, no manifest delta).

### §2.F W-OB-6 — Conditional absorption slot (fires only if W-OB-4a / W-OB-4b surfaces structural finding)

**Source.** `v0_1_18/README.md` provisional scope row 6; conditional.

**Trigger.** W-OB-4a + W-OB-4b dogfood produce `dogfood_findings.md`. If a finding is **structural** (i.e., not absorbable into W-OB-3 prompt content or W-OB-5 doctor hint — for example, a missing CLI command, a broken test path, a documented behaviour that doesn't match implementation), W-OB-6 fires as a discrete W-id with its own commit.

**Files of record (TBD).** Determined by what W-OB-4a / W-OB-4b surfaces; the cycle PLAN does not pre-commit a code-change scope. If W-OB-6 fires, its acceptance is authored as an addendum to this PLAN (or a `W-OB-6.md` cycle-dir file) before the W-OB-6 commit lands.

**Acceptance (meta).**
1. If W-OB-4a + W-OB-4b surface no structural finding: `dogfood_findings.md` explicitly states "no W-OB-6-class findings"; W-OB-6 does not fire; `RELEASE_PROOF.md` records 7 W-ids closed (6 base catalogue + W-OB-7 absorption; W-OB-6 unused per OQ-7 Codex disposition).
2. If W-OB-4a or W-OB-4b surfaces ≥1 structural finding: W-OB-6 acceptance is authored before commit; the addendum cites the dogfood finding ID; `RELEASE_PROOF.md` records 8 W-ids closed.
3. Severity routes apply: a HIGH-severity structural finding (e.g., crash in W-OB-2's default-flip path on a corner case) routes to a hotfix cycle if the v0.1.18 ship is already in progress; lower-severity findings absorb into W-OB-6.

**What this WS does NOT do.** No commitments at PLAN-author time. The conditional shape is the contract.

### §2.G W-OB-7 — Intake-handler migration parity (F-OB-PRE-01 fix)

**Source.** `v0_1_18/audit_findings.md` §F-OB-PRE-01; surfaced 2026-05-05 on the maintainer's own state DB; absorbed at cycle-open 2026-05-06 per maintainer decision (option A in F-OB-PRE-01 disposition).

**Files of record:**
- `src/health_agent_infra/cli/handlers/intake.py` — **eight** `cmd_intake_*` functions (round-1 corrected per F-PLAN-01): `gym` at line 62, `exercise` at 300, `nutrition` at 420, `stress` at 643, `note` at 790, `readiness` at 903, `gaps` at 980, `weight` at 1184. Every handler that touches the canonical state DB (writes via `core.state.open_connection`, or reads with potential schema-current expectations) needs the migrating seam.
- `src/health_agent_infra/core/state/store.py` (per OQ-1 Codex disposition) — new helper `open_connection_with_migrations(db_path: Path) -> sqlite3.Connection` lives next to existing `open_connection` (line 64) and `apply_pending_migrations` (line 243). Helper is **additive** — does NOT replace `open_connection` globally (too many read paths depend on the non-migrating variant; a global change would need a separate audit per Codex OQ-1 note).
- `verification/tests/test_intake_migration_parity.py` (new) — pinned regression test covering **all eight** intake handlers against a synthetic schema-behind DB.

**Fix shape.** Every intake handler currently calls `core.state.open_connection(db_path)` (verified at handler lines 227, 352, 602, 753, 880, 1025/1093/1149, 1238 — the actual seam shape, NOT raw `sqlite3.connect`). The fix introduces a sibling helper that runs migrations on the freshly-opened connection:

```python
# Proposed in core/state/store.py (next to open_connection)
def open_connection_with_migrations(db_path: Path) -> sqlite3.Connection:
    """Open the state DB and apply any pending migrations before
    returning. Used by every intake handler + any other handler
    that opens a writable connection and expects schema-current
    state."""
    conn = open_connection(db_path)
    apply_pending_migrations(conn)
    return conn
```

Each `cmd_intake_*` handler replaces its `open_connection(...)` call with `open_connection_with_migrations(...)`. The seam matches what `cmd_state_init` at `cli/handlers/state.py:46-52` already does via `initialize_database` (which calls `apply_pending_migrations` internally at `core/state/store.py:335`). **(Round-2 provenance correction per F-PLAN-01: original PLAN cited `cli/handlers/state.py:239,273`, which is `cmd_state_migrate` — the explicit user-facing migration command — not the auto-migrate path on a fresh `hai state init`.)**

**Per-handler classification (round-1 disposition per F-PLAN-01).** All eight intake handlers route through `core.state.open_connection` and write to / read schema-dependent tables. Each gets the migrating variant:

| Handler | Line | Connection use | Migrates? |
|---|---|---|---|
| `cmd_intake_gym` | 62 | `open_connection` at 227 | YES |
| `cmd_intake_exercise` | 300 | `open_connection` at 352 | YES |
| `cmd_intake_nutrition` | 420 | `open_connection` at 602 | YES |
| `cmd_intake_stress` | 643 | `open_connection` at 753 | YES |
| `cmd_intake_note` | 790 | `open_connection` at 880 | YES |
| `cmd_intake_readiness` | 903 | `open_connection` at 1149 (via `_project_readiness_submission_into_state` helper at line 1124) | YES (write via helper) |
| `cmd_intake_gaps` | 980 | `open_connection` at 1025 (presence) + 1093 (write) | YES (presence + write) |
| `cmd_intake_weight` | 1184 | `open_connection` at 1238 | YES (the F-OB-PRE-01 reproducer) |

No handler is excluded. If a handler is later determined to not need migration (e.g. read-only against a stable subset), the exclusion is documented in the W-OB-7 commit + a test proves the exclusion cannot hit schema-behind failure.

**Acceptance.**
1. A shared `open_connection_with_migrations(db_path)` helper exists in `core/state/store.py` next to `open_connection` and `apply_pending_migrations`. Helper is additive; `open_connection` is unchanged. (Maintainer ratifies module placement at implementation per OQ-1; PLAN-author proposal is `core/state/store.py` per Codex Codex OQ-1 recommendation.)
2. **All eight `cmd_intake_*` handlers** use `open_connection_with_migrations` instead of `open_connection` for their canonical-state-DB connection. No `cmd_intake_*` handler retains a raw `open_connection(...)` against the canonical state DB. (Round-2 corrected from "all six" per F-PLAN-01.)
3. `test_intake_migration_parity.py` covers: (a) for each of the **eight** intake commands, invoke against a synthetic schema-25 DB (one migration behind); (b) assert the command succeeds; (c) assert the post-command DB is at schema head 26 (or whatever the package head is); (d) assert a `runtime_event_log` row records the migration application IF `apply_pending_migrations` currently emits one for this path — if not, that's a separate finding for v0.1.19+ (W-OB-7's contract is "intake doesn't crash," not "intake's auto-migrate is fully audit-trailed").
4. **Reproducer test for F-OB-PRE-01 specifically.** `test_intake_weight_on_pre_v0_1_17_db` asserts `hai intake weight --kg 82.0 ...` succeeds against a synthetic schema-25 DB and writes the row to the now-migrated `body_comp` table. This is the regression test that prevents the bug from re-introducing in a future schema-add cycle.
5. All eight `cmd_intake_*` handlers continue to write fine on a current-schema DB (no regression on the path that already worked).
6. Full pytest suite (narrow + broader warning gates) green post-W-OB-7.

**What this WS does NOT do.**
- Does not auto-migrate non-state DBs (e.g., the demo CSV fixture environment). The seam is canonical-DB-only.
- Does not change `apply_pending_migrations` itself (existing function at `core/state/store.py:243`).
- Does not change `open_connection` globally — too many read paths depend on the non-migrating variant; a global change would need a separate audit (per OQ-1 Codex disposition).
- Does not extend the audit-event vocabulary — if `apply_pending_migrations` doesn't currently emit a `runtime_event_log` row when called from a non-`cmd_state_init`/`cmd_state_migrate` path, that's left as-is. Treating "auto-migrate from intake" as a fully audit-trailed event is a v0.1.19+ improvement if anyone surfaces it.

**Ship-claim gate:** acceptance items 2 + 4 are **release-blocker for the F-OB-PRE-01 fix claim**. If `cmd_intake_weight` still crashes against a schema-behind DB, W-OB-7 hasn't shipped.

---

## 3. Cross-cutting work + governance edits

**No CP-shape governance edits this cycle.** v0.1.18 proposes only closure-side updates that follow naturally from W-OB-2 + W-OB-7 shipping.

**Closure-side AGENTS.md updates at v0.1.18 ship:**

1. **None planned for "Settled Decisions."** W29/W30 closure already landed at v0.1.17 ship; the cli.py-split entry retired. No new D-entries. v0.1.18's onboarding-quality work doesn't introduce a settled-decision shape — it's UX hardening within existing invariants.
2. **None planned for "Do Not Do."** v0.1.18 doesn't propose new prohibitions. The existing W57 invariant covers the "no autonomous intent authoring" property the W-OB-2 default-flip respects.
3. **Possibly one tactical-plan §5E edit** — when v0.1.18 ships, `tactical_plan_v0_1_x.md` §5E moves from "in flight" to "shipped" and §5F (v0.1.19) moves to "next-active." This is the standard ship-time freshness sweep, not a governance edit.

**`reporting/docs/current_system_state.md` update at v0.1.18 ship:** package version → 0.1.18; CLI command count unchanged (the new `--non-interactive` is a flag on existing `hai init`, not a new command); **no manifest schema delta** (per OQ-4 Codex disposition: `next_action` is runtime-only, not in `hai capabilities --json`); test gate count update.

**CHANGELOG.md v0.1.18 entry** — names W-OB-1 through W-OB-7 (or W-OB-1, 2, 3, 5, 7 + dogfood passes if W-OB-6 doesn't fire) as a single onboarding-quality cycle. The behaviour change (W-OB-2) gets its own bullet with user-facing wording **"interactive `hai init` default (with opt-out)"** (per OQ-6).

**`AUDIT.md` entry** — v0.1.18 row with D14 round-table + IR outcome + RELEASE_PROOF link.

---

## 4. Risks + hidden coupling

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | **W-OB-2 default-flip breaks CI / agent harnesses.** Existing automation calling `hai init` without `--non-interactive` and without TTY would currently get bare init; post-W-OB-2 with TTY check, behaviour preserves (no TTY → bare init). But if any automation runs in a pseudo-TTY (some CI runners, some Docker setups), the flip could fire unexpectedly and prompt-block. | Medium | High | TTY check is the gate, not just env-var; tests cover **five cases** (§2.B item 3 per OQ-2); explicit `--non-interactive` flag + env var give two opt-out paths; CHANGELOG entry calls out the change. |
| 2 | **W-OB-3 prompt content review introduces a regression in `--guided` flow.** `_run_guided_onboarding` is multi-step; refactoring prompt copy could break refusal-path or resume semantics. | Medium | Medium | W-OB-3 acceptance item 2 covers refusal + resume tests explicitly; existing `test_init_onboarding_flow.py` continues to assert flow shape; no new prompt steps added (content-only revision). |
| 3 | **W-OB-4a upgrade dogfood produces no findings because the synthetic old DB doesn't mimic real users.** A maintainer-constructed old DB might miss the actual failure modes an organic upgrade would hit. | Medium | Medium | Per OQ-3: snapshot maintainer's real pre-v0.1.17 DB if available (priority 1), else install v0.1.16 wheel + run `hai init` (priority 2), targeted rollback last resort with documented mutation; treat upgrade scenario as best-effort, not exhaustive. |
| 4 | **W-OB-5 `next_action` field becomes an autonomous-execution vector.** If an agent harness reads `next_action.command` and auto-runs it without user surfacing, that violates W57 for any command that authors intent or target rows. | Low | High | Schema includes `interactive: true` field for any command requiring TTY; agent integration docs (when updated) name the contract: "`next_action` is informational; surface to user, do not auto-run unless `agent_safe: true` AND `interactive: false`." W-OB-5 acceptance item 3 enforces the schema. |
| 5 | **W-OB-7 shared seam introduces a connection-resource-leak regression.** If `open_connection_with_migrations` returns a connection the caller doesn't always close, the seam could leak. | Low | Low | Existing handlers already use `core.state.open_connection` with established connection-lifecycle conventions (the new seam wraps the same `open_connection` and adds an `apply_pending_migrations` step before returning); the seam preserves the existing return/close contract; tests assert the connection closes (acceptance item 6 — full suite green covers leak detection via fd-resource warnings). **(Round-2 wording correction per F-PLAN-R2-02: original referenced the discarded `connect_and_migrate` + `sqlite3.connect` shape; corrected.)** |
| 6 | **W-OB-7 fix masks a class of bugs that would have surfaced as crashes.** If a future migration is buggy, intake handlers will silently re-apply it and fail in a more confusing way than the current "table doesn't exist" crash. | Low | Medium | `apply_pending_migrations` is already battle-tested via `hai state init` + `hai daily` paths; v0.1.18 doesn't change migration-application semantics. If a future migration is buggy, that's a migration-test gap, not a W-OB-7 regression. |
| 7 | **W-OB-2 + W-OB-5 sequencing risk.** W-OB-5's `next_action.command` references the post-default-flipped shape (e.g., recommends `hai init` not `hai init --guided` if W-OB-2 makes the flip implicit). If the sequencing slips and W-OB-5 lands first, the hint text could be wrong. | Low | Low | §1.3 sequencing names W-OB-2 → W-OB-5 explicitly; commit cadence enforces; acceptance item §2.E.2 names the dependency. |
| 8 | **Cycle slippage by Phase 1 W-OB-7 surfacing scope creep.** If the shared-seam refactor surfaces non-trivial coupling in `cli/handlers/intake.py` (e.g., a handler that does its own ad-hoc connection management), W-OB-7 could grow beyond 0.5-1d. | Low | Low | Current intake.py is 1265 LOC across **8** well-shaped handlers (round-1 corrected from "6" per F-PLAN-01); all eight use the same `core.state.open_connection` seam (verified at handler lines 227, 352, 602, 753, 880, 1025/1093/1149, 1238); no exotic connection lifecycle. |
| 9 | **W-OB-4a / W-OB-4b dogfood reveals a finding W-OB-3 + W-OB-5 + W-OB-6 collectively can't absorb.** If a dogfood pass surfaces an architectural issue (e.g., the `hai init --guided` flow fundamentally doesn't fit the agent-driven model), the cycle's thesis is wrong-shaped. | Low | High | Cycle-abort path exists per AGENTS.md D11 pre-implementation gate (`aborts-cycle` finding tag); this would be filed in `audit_findings.md` and escalated to maintainer; v0.1.18 deferred-rebuild rather than ships with a known mismatch. |
| 10 | **Sizing residual.** 5-9 days estimated; one or more W-ids could land at the high end of their range and the cycle stretches to 10-12 days. | Low | Low | Acceptable within tier shape. v0.1.17 closed 25-40 d catalogued in one autonomous session; v0.1.18 has substantial margin. |

---

## 5. Effort arithmetic

| W-id | Low | High | Note |
|---|---:|---:|---|
| W-OB-1 | 0.5 | 0.5 | Mostly pre-staged; sweep + verify only |
| W-OB-2 | 1.0 | 2.0 | New flag + env var + handler logic + 5-case test (per OQ-2) |
| W-OB-3 | 1.0 | 2.0 | Prompt review informed by W-OB-4a findings; tests for refusal + resume |
| W-OB-4a | 0.5 | 0.5 | Phase 1 upgrade-path dogfood; maintainer time + findings write-up |
| W-OB-4b | 0.5 | 0.5 | Phase 2 post-W-OB-2 local-wheel smoke; release-blocker default-flip witness |
| W-OB-5 | 0.5 | 1.0 | Multi-check `next_action` (per F-PLAN-03 widening) + render update + manifest-consistency test; depends on W-OB-2 sequencing |
| W-OB-6 | 0.0 | 1.0 | Conditional; 0d if W-OB-4a + W-OB-4b surface no structural finding; up to 1d if they do |
| W-OB-7 | 0.5 | 1.0 | Shared seam + **8 callers** (per F-PLAN-01) + 9-case regression test (8 per-handler + 1 reproducer) |
| **Subtotal** | **4.5** | **8.5** | |
| Coordination overhead (~5%) | 0.2 | 0.4 | |
| **Total** | **~5** | **~9** | |

**Comparison to recent cycles.**
- v0.1.17 substantive: 25-40 d / 10 W-ids (W-29 was the heavy lift).
- v0.1.15 substantive: 15-24 d / 7 W-ids.
- v0.1.18 substantive: 5-9 d / 6-7 W-ids. **Smaller by design** — onboarding-quality cycle is intentionally tight to clear the path for v0.1.19.

The release-blocker leg (W-OB-2) carries the substantive tier classification; the days leg falls below threshold. Both are honestly named in the tier annotation at the top of this PLAN.

---

## 6. Ship gates

| Gate | Source | Pass condition |
|---|---|---|
| `uv run pytest verification/tests -q` | Always | All passing |
| `uv run pytest verification/tests -W error::Warning -q` | AGENTS.md D13/W-N-broader | All passing under broader warning gate |
| `uvx mypy src/health_agent_infra` | Always | Clean |
| `uvx bandit -ll -r src/health_agent_infra` | Always | Clean |
| `hai capabilities --json` round-trip | W-OB-2 (new `--non-interactive` flag) | Snapshot regenerates with the W-OB-2 flag add; no other drift. **W-OB-5 is a runtime *consumer* of the manifest (consistency test reads it), NOT a producer — no manifest delta from W-OB-5 per OQ-4. (Round-2 attribution correction per F-PLAN-R2-03.)** |
| Persona matrix (13 personas, opt-in) | AGENTS.md substantive-cycle convention | 13/13 reach `synthesized` cleanly; no new findings |
| `hai eval run --scenario-set all` | AGENTS.md substantive-cycle convention | 100% pass-rate (135 fixtures inherited from v0.1.17) |
| `dogfood_findings.md` exists with both passes | W-OB-4a + W-OB-4b acceptance item 1 | File present; both passes documented in separate sections |
| **W-OB-4a upgrade scenario `hai intake weight` succeeds** | W-OB-4a acceptance item 3 + F-PLAN-07 round-1 add | Captured in `dogfood_findings.md` § W-OB-4a; cmd succeeds against synthetic schema-25 DB built from the locally built wheel |
| **W-OB-4b post-W-OB-2 local-wheel smoke proves default-flip** | W-OB-4b acceptance items 3-4 + F-PLAN-07 round-1 add | Captured in `dogfood_findings.md` § W-OB-4b; bare `hai init` on TTY enters `--guided`; `HAI_INIT_NON_INTERACTIVE=1 hai init` skips it |
| W-OB-7 reproducer test passes | W-OB-7 acceptance item 4 | `test_intake_weight_on_pre_v0_1_17_db` green |
| W-OB-7 8-handler parity test passes | W-OB-7 acceptance item 3 | `test_intake_migration_parity.py` covers all 8 cmd_intake_* handlers green |
| W-OB-2 default-flip test covers 5 cases | W-OB-2 acceptance item 3 (per OQ-2) | `test_cli_init_default_flip.py` green for all 5 cases (interactive+missing, interactive+complete, no-TTY, --non-interactive flag, HAI_INIT_NON_INTERACTIVE=1 env) |
| **W-OB-5 `next_action.command` post-W-OB-2 shape test** | W-OB-5 acceptance item 2 + F-PLAN-07 round-1 add | Test asserts `next_action.command == "hai init"` (NOT `"hai init --guided"`) for missing-intent case |
| **W-OB-5 `next_action.agent_safe` manifest consistency test** | W-OB-5 acceptance item 3 (per F-PLAN-02) | Test cross-checks emitted `next_action.agent_safe` against live `hai capabilities --json` for every cited command |
| AGENTS.md ship-time freshness checklist | AGENTS.md "Ship-time freshness checklist (v0.1.12 W-AC)" | All 8 items checked |
| AUDIT.md + CHANGELOG.md entries | Always | Present |
| `current_system_state.md` updated | Always | Reflects v0.1.18 |
| Tactical plan §5E shipped, §5F next-active | Ship-time freshness | Updated |

**Release-blocker gates (cycle does not ship if any fails):**
- W-OB-2 default-flip 5-case test green (acceptance §2.B.3).
- W-OB-4a upgrade dogfood `hai intake weight` succeeds against schema-25 DB (acceptance §2.D W-OB-4a item 3).
- **W-OB-4b post-W-OB-2 local-wheel smoke** proves default-flip on TTY (acceptance §2.D W-OB-4b items 3-4) — round-1 add per F-PLAN-04 + F-PLAN-07.
- W-OB-7 reproducer test green (acceptance §2.G.4).
- W-OB-7 8-handler parity test green (acceptance §2.G.3).
- W-OB-5 next_action.command post-W-OB-2 shape test green + manifest consistency test green (round-1 add per F-PLAN-02 + F-PLAN-07).
- `hai capabilities --json` regenerates with intentional adds only.

---

## 7. What this PLAN does NOT cover

- **No new domains.** Six domains (recovery, running, sleep, stress, strength, nutrition) unchanged.
- **No schema additions.** Schema head stays at 26 (v0.1.17's `body_comp`); v0.2.x territory.
- **No new live data sources.** intervals.icu only; Garmin still marked `unreliable`.
- **No autonomous onboarding actions.** W-OB-2's default-flip prompts the user via `--guided`; doesn't auto-author intent rows from defaults. W-OB-5's `next_action` is informational; agents surface, don't auto-run.
- **No body-comp surface extensions.** v0.1.17 W-B shipped `hai intake weight`; v0.1.18 W-OB-7 fixes the upgrade-path crash but doesn't extend the surface.
- **No foreign-user empirical work.** v0.1.19's claim. v0.1.18 W-OB-4a + W-OB-4b are **maintainer dogfood**, not a recorded foreign-user session.
- **No `hai daily` flow changes.** The agent-driven daily loop is unchanged — v0.1.18 shapes the install/upgrade path that precedes the daily loop.
- **No CP-shape governance edits.** No AGENTS.md "Settled Decisions" or "Do Not Do" entries proposed. (Closure-side updates only — see §3.)
- **No `hai eval` substrate changes.** v0.1.17's 135-fixture corpus inherited as-is.
- **No persona harness changes.** The 13-persona matrix runs as a ship gate but the harness itself is unchanged.

**Cross-cycle boundary checks:**
- v0.1.19 work (foreign-user empirical, W-2U-FIX-P1/P2, W-EXPLAIN-UX-2): out-of-scope; do not pull forward.
- v0.2.0 work (W52 weekly review, W58D factuality, Path A doc adjuncts): out-of-scope; **tactically sequenced post-v0.1.19**, which is itself post-v0.1.18 (per `tactical_plan_v0_1_x.md:52`). v0.1.18 → v0.1.19 → v0.2.0 chain. **(Round-1 correction per F-PLAN-05: original PLAN claimed "parallelizable with v0.2.0" — that was inherited from the v0.1.17 PLAN, where it was correct because v0.2.0 is explicitly NOT v0.1.17-dependent. For v0.1.18 the parallelization claim is wrong because v0.2.0's hard dep on v0.1.19 transitively chains through v0.1.18.)** v0.1.18 does not add new v0.2.0 scope or schema dependencies.
- v0.2.3 work (capabilities-manifest schema freeze): out-of-scope; W-30 regression-test scaffold from v0.1.17 holds. v0.1.18's W-OB-5 explicitly avoids the manifest schema (per OQ-4 disposition; `next_action` is runtime-only).

---

## 8. Open questions

The following questions surfaced at PLAN-author time. **All 7 OQs received explicit dispositions during D14 round 1** (Codex audit response + maintainer ratification per `codex_plan_audit_response_response.md`). Dispositions are settled and propagated into §2 contracts; this section preserves the deliberation trail.

**OQ-1.** **Where does the migrating-connection helper live?** ✅ **Settled D14 R1: `core/state/store.py`** as a new sibling helper `open_connection_with_migrations` next to existing `open_connection` (line 64) and `apply_pending_migrations` (line 243). **Do not change `open_connection` globally** — too many read paths depend on the non-migrating variant; a global change would need a separate audit. (PLAN-author original default was `cli/shared.py`; Codex disposition flipped to `core/state/store.py` for the colocation reason. Maintainer accepted.)

**OQ-2.** **Project-wide `HAI_NON_INTERACTIVE`?** ✅ **Settled D14 R1: no.** `HAI_INIT_NON_INTERACTIVE` is the v0.1.18 contract; a project-wide env var is a v0.2.x concern. **Plus**: W-OB-2 tests separately cover `--non-interactive` flag and `HAI_INIT_NON_INTERACTIVE=1` env var, both with `isatty()==True` (per Codex addition). 5-case test surface per §2.B.3.

**OQ-3.** **W-OB-4a old-DB construction approach?** ✅ **Settled D14 R1: priority order** — (1) snapshot maintainer's real pre-v0.1.17 DB if available; (2) install v0.1.16 wheel + run `hai init`; (3) targeted rollback last resort with documented exact mutation in `dogfood_findings.md`.

**OQ-4.** **`next_action` field placement in capabilities manifest?** ✅ **Settled D14 R1: runtime check level only — NOT in the manifest.** Manifest schema freeze (v0.2.3 W-30 territory) untouched. §2.E acceptance item 5 (original "manifest gains `doctor_check_schema`") **dropped** at round 1.

**OQ-5.** **W-OB-3 post-prompt "next action" hint?** ✅ **Settled D14 R1: yes, content-only.** Hint added to post-prompt summary in §2.C item 6; **no new flow step** under W-OB-3. If a flow change is needed it's scoped out to a separate WS.

**OQ-6.** **CHANGELOG.md user-facing wording?** ✅ **Settled D14 R1: "interactive `hai init` default (with opt-out)"** for user-facing CHANGELOG. Internal "default-flip" term stays in PLAN/audit-trail vocabulary.

**OQ-7.** **W-OB-6 conditional slot — reserve or remove?** ✅ **Settled D14 R1: reserve.** If neither W-OB-4a nor W-OB-4b surfaces a structural finding, RELEASE_PROOF says "no W-OB-6-class findings" + counts shipped W-ids as 7 (6 base + W-OB-7), W-OB-6 unused.

---

## 9. Provenance + evolution

**Authored:** 2026-05-06 against HEAD `9c651da` by Claude (autonomous mode under maintainer ratification). Three pre-PLAN decisions resolved at cycle-open:

1. **F-OB-PRE-01 absorption.** Maintainer chose option A (file as W-OB-7, discrete fix) over option B (absorb into W-OB-5 as a doctor hint). Rationale: code bug, not discoverability gap; W-29 split makes the discrete fix mechanically clean.
2. **W-OB-4 scenario scope.** Maintainer chose two scenarios (clean install + upgrade) over one (clean install only). Rationale: F-OB-PRE-01's tail note shows the upgrade path is where the bug lives; cheap insurance against v0.1.19 burning on already-known issues.
3. **PLAN-authoring shape.** Maintainer chose direct PLAN-authoring this session over a `cycle_open_session_prompt.md` bridge document. Rationale: bridge document was infrastructure for v0.1.17's cross-session handoff; v0.1.18 author + ratifier are in the same session.

**D14 round 1 closed 2026-05-06** at PLAN_COHERENT_WITH_REVISIONS — 7 findings, all accepted, all revised in lockstep across §1.1, §1.2, §1.3, §2.B, §2.C, §2.D, §2.E, §2.F, §2.G, §3, §4, §5, §6, §7, §8 (multi-surface sweep per AGENTS.md "Summary-surface sweep on partial closure"). See `codex_plan_audit_response.md` + `codex_plan_audit_response_response.md`.

**D14 round 2 closed 2026-05-06** at PLAN_COHERENT_WITH_REVISIONS, **close-in-place** — 3 findings (F-PLAN-R2-01 summary-surface propagation gaps; F-PLAN-R2-02 W-OB-7 stale caller-count + readiness/gaps line-number swap + risk 5 stale seam shape; F-PLAN-R2-03 W-OB-5 manifest-vs-runtime contradictions + non-existent `check_credentials`). All 3 accepted; PLAN revised in this same pass. Settling shape **7 → 3** matches AGENTS.md empirical norm `10 → 5 → 3 → 0`. **No round 3 required** per Codex closure recommendation (text-only revisions, no scope shift, no new acceptance semantics). See `codex_plan_audit_round_2_response.md` + `codex_plan_audit_round_2_response_response.md`.

**D14 settled.** Cycle proceeds to Phase 0 (D11) bug-hunt next.

**Cycle position.**
```
Pre-PLAN-open:
  PLAN.md authored
  D14 plan-audit prompt authored
  Codex round 1 closed PLAN_COHERENT_WITH_REVISIONS (7 findings; all accepted)
  PLAN.md revised in lockstep
  Codex round 2 closed PLAN_COHERENT_WITH_REVISIONS close-in-place (3 findings; all accepted)
  PLAN.md revised in lockstep ← here
  D14 settled (no round 3 needed)
  Phase 0 (D11) bug-hunt opens ← next

Phase 0 (D11):
  Internal sweep
  Audit-chain probe
  Persona matrix (13 personas, opt-in)
  Codex external bug-hunt audit (optional per maintainer)
  → audit_findings.md updates with any new findings beyond F-OB-PRE-01

Pre-implementation gate:
  revises-scope findings may revise PLAN (loop back to D14)
  aborts-cycle findings may end the cycle

PLAN.md → opens cycle

Implementation rounds:
  Phase 1: W-OB-1 + W-OB-7 commits; W-OB-4a evidence gate
           (W-OB-4a is a dogfood gate, not a code commit — produces
            findings into dogfood_findings.md)
  Phase 2: W-OB-3 + W-OB-2 commits; W-OB-4b evidence gate
           (W-OB-4b is a post-W-OB-2 dogfood gate, not a code commit);
           W-OB-5 commit
  Phase 3: W-OB-6 conditional commit (only if W-OB-4a/W-OB-4b surface
           a structural finding)
  Codex implementation review (post-implementation, IR)
  ... until SHIP / SHIP_WITH_NOTES (empirical 2-3 IR rounds)

RELEASE_PROOF.md + REPORT.md → ship to PyPI as 0.1.18

v0.1.19 cycle opens — foreign-user empirical session against the
shipped v0.1.18 wheel.
```

**Source artifacts to keep aligned through the cycle.** When this PLAN revises, the following surfaces must move in lockstep per AGENTS.md "Summary-surface sweep on partial closure":
- `reporting/plans/v0_1_18/README.md` — provisional → shipped
- `reporting/plans/v0_1_18/audit_findings.md` — F-OB-PRE-01 status updates
- `reporting/plans/tactical_plan_v0_1_x.md` §5E — in-flight → shipped at ship-time
- `reporting/plans/tactical_plan_v0_1_x.md` §5F — next-active assignment to v0.1.19
- `reporting/docs/current_system_state.md` — version + command count + schema head + tier annotation
- `CHANGELOG.md` — v0.1.18 entry
- `AUDIT.md` — v0.1.18 row
- `README.md` — version reference + quickstart edits if W-OB-1 sweep finds drift
- `AGENTS.md` "Settled Decisions" — no edits planned per §3
- `AGENTS.md` "Do Not Do" — no edits planned per §3
