# v0.1.15.1 hotfix scope — Codex hand-off report

**Authored:** 2026-05-03 evening (post-v0.1.15 PyPI publish + post-CI red).
**Hand-off audience:** Codex (now performing the repo work for this hotfix).
**Maintainer:** Dom; see `~/.claude/CLAUDE.md` "Working Style" + this report's §10 reference list.
**Tier (per AGENTS.md D15):** **hotfix** — single-bug-class fix + named-defer propagation. Hotfix tier may skip Phase 0 + D14; lightweight RELEASE_PROOF; established hotfix pattern is v0.1.12.1 (cloudflare UA) and v0.1.14.1 (garmin manifest signal).

---

## §1 — Trigger

CI ran against v0.1.15 immediately after the 2026-05-03 PyPI publish (commit `ccaf7a4`). Linux runners (`test (3.11)` + `test (3.12)`) returned **14 failed, 2614 passed, 5 skipped in 118.86s**. macOS (maintainer dev) was green at 2630/3 throughout the cycle.

Visible failures from the maintainer's screenshot (CI run `25283872...`):

```
FAILED verification/tests/test_readme_quickstart_smoke.py::test_quickstart_commands_run_cleanly
  - 'hai init' exited 4; stderr='hai: internal error (NoKeyringError):
    No recommended backend was available. Install a recommended 3rd party
    backend package; or, install the keyrings.alt package if you want to
    use the non-recommended backends...'
  - 'hai doctor' exited 4; stderr='hai: internal error (NoKeyringError): ...'
FAILED verification/tests/test_w_pv14_01_csv_isolation.py::test_stats_warns_on_for_date_divergence_over_48h
  assert 4 == 0  (where 0 = exit_codes.OK)
FAILED verification/tests/test_w_pv14_01_csv_isolation.py::test_doctor_warns_on_for_date_divergence_over_48h
  json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
14 failed, 2614 passed, 5 skipped in 118.86s
```

**Visible: 4 failures. Other 10 not shown in the screenshot — Codex should enumerate via the GitHub Actions log for run `25283872...` (or trigger a re-run on the v0.1.15 tag).**

---

## §2 — Diagnosis (root cause + scope)

### 2.1 Root cause — `NoKeyringError` not caught by the credential-store fallback

`src/health_agent_infra/core/pull/auth.py:110-117`:

```python
def _default_backend() -> KeyringBackend:
    """Import keyring lazily; return a null backend if unavailable."""
    try:
        import keyring  # type: ignore
    except ImportError:
        return _NullBackend()
    return keyring
```

The fallback catches `ImportError` only. On Linux CI runners the `keyring` Python package imports fine, but no system backend (`gnome-keyring`, `kwallet`, `keyrings.alt`) is registered. The first call to `keyring.get_password()` raises `keyring.errors.NoKeyringError` — which propagates uncaught through `CredentialStore.load_garmin()` / `load_intervals_icu()` / `garmin_status()` / `intervals_icu_status()` and crashes any command that touches the credential layer eagerly.

### 2.2 Affected commands

Every command that constructs `CredentialStore.default()` and immediately calls a `.load_*()` or `.*_status()` method:

- `hai init` (during the onboarding doctor probe — exits 4 on first run)
- `hai doctor` (`auth_garmin` + `auth_intervals_icu` checks)
- `hai stats` (cred-status enrichment in the sync-freshness block — `cli.py:_credential_store_for(args)`)
- `hai pull` (`_resolve_pull_source` calls `_intervals_icu_configured()` which calls `CredentialStore.default().load_intervals_icu()`)
- `hai daily` (same path as `hai pull`)

### 2.3 Likely pre-existing vs v0.1.15 regression

This is **almost certainly a pre-existing latent bug** — `_default_backend`'s narrow `ImportError`-only catch shipped before v0.1.15 — but the v0.1.15 cycle WIDENED the affected surface:

- F-PV14-01 added `for_date_divergence_*` fields to `cmd_stats` sync_freshness block + `check_sources` doctor block, both reachable from the credential code path.
- F-PV14-01 added new tests (`test_stats_warns_on_for_date_divergence_over_48h` + `test_doctor_warns_on_for_date_divergence_over_48h`) that invoke `hai stats --json` / `hai doctor --json` against a tmp DB. On Linux CI those tests crash before emitting JSON.
- F-PV14-01 hardened the `cmd_pull` guard which now eagerly resolves the source (and therefore the credential check).

So 2 of the 14 failures are tests I added that exercise the latent bug, and the other 12 are likely the pre-existing README-quickstart-smoke + adjacent surface that was always failing on CI but not blocking releases until now.

**Codex should confirm this hypothesis** via `git log` on `test_readme_quickstart_smoke.py` and adjacent CI history. If it WAS green on v0.1.14.1, then there's a real regression to find. If it was always red on Linux, then the maintainer was shipping despite CI red — a workflow problem in addition to the technical bug.

### 2.4 User impact

- **The named foreign-user candidate on macOS:** unaffected. macOS Keychain handles the keyring-backend lookup transparently.
- **Anyone installing v0.1.15 from PyPI on Linux:** crashes on first `hai init` / `hai doctor` / `hai stats` / `hai pull`. The package is effectively broken on Linux right now.
- **CI signal quality:** red right after a publish — bad for release confidence and for Codex's ability to validate future cycles against a green baseline.

---

## §3 — Required fix (P0)

### 3.1 Add a runtime dependency

`pyproject.toml`:

```toml
dependencies = [
  ...,
  "keyrings.alt",   # always-available file-based backend; Linux falls through here when no system keyring exists
]
```

This is the documented escape route in the `NoKeyringError` message itself ("install the keyrings.alt package if you want to use the non-recommended backends"). It's a tiny pure-Python package; no native deps; safe across all platforms; macOS/Windows still prefer their native keychains because `keyrings.alt` is a fallback backend not a primary.

### 3.2 Defensive catch around credential-store backend access

`src/health_agent_infra/core/pull/auth.py:110-117` — extend `_default_backend()` to catch runtime keyring errors too, not just `ImportError`:

```python
def _default_backend() -> KeyringBackend:
    """Import keyring lazily; return a null backend if unavailable."""
    try:
        import keyring  # type: ignore
    except ImportError:
        return _NullBackend()

    # Defensive probe: if no backend is registered (Linux without
    # keyrings.alt or system keyring), `keyring.get_password` raises
    # NoKeyringError on the first call. Catch here and fall through
    # to the null backend so credential-status checks degrade to
    # "no creds configured" rather than crashing the command.
    try:
        from keyring.errors import NoKeyringError  # type: ignore
    except ImportError:
        return keyring  # very old keyring; trust it
    try:
        keyring.get_password("__hai_probe__", "__hai_probe__")
    except NoKeyringError:
        return _NullBackend()
    except Exception:
        # Any other backend error (lock, dbus failure) — degrade
        # rather than crash. The runtime never depends on keyring
        # access succeeding for non-credential commands.
        return _NullBackend()
    return keyring
```

The defensive catch is a belt-and-braces complement to `keyrings.alt` — even if a future install somehow lacks `keyrings.alt` and the system keyring, the runtime degrades gracefully.

### 3.3 (Optional but recommended) Audit `garmin_status` / `intervals_icu_status` for catch coverage

The `*_status()` methods at `core/pull/auth.py:187-...` call `self.backend.get_password()`. If `_default_backend` returns the real `keyring` and `keyring.get_password` later raises (e.g., backend went away mid-session), the command crashes. Wrap each `get_password` in `try/except` returning the appropriate "credentials_available: False" shape. Codex's call whether to scope this into v0.1.15.1 or defer to v0.1.16 — the §3.1 + §3.2 fixes likely close the CI failure without this.

### 3.4 Verification

After applying §3.1 + §3.2, all 14 CI failures should resolve. Codex should confirm by:

```bash
uv run pytest verification/tests -q                      # expect 2631 pass (+1 regression test)
uvx mypy src/health_agent_infra                          # expect Success
uvx bandit -ll -r src/health_agent_infra                 # expect 0 medium/high
```

Plus a simulated-Linux check (any of):
- Run the specific failing tests with `keyring` backend forced empty (mock `_default_backend` to return a real `keyring` module with no backends registered).
- OR push to a branch and let CI confirm on actual Linux runners before merging to main.

---

## §4 — Optional bundle (decide at scope-set time)

The maintainer's standing question: should v0.1.15.1 be a pure single-bug hotfix (matches v0.1.12.1 / v0.1.14.1 precedent) or a hotfix-plus-doc-backfill?

### 4.1 Doc gaps from v0.1.15 PLAN §3 cross-cutting

**Status as of hand-off:** the maintainer (or a linter) has done a parallel doc-sweep that landed most of the gaps already. Verified via grep at hand-off time:

- ✅ **`reporting/docs/state_model_v1.md`** — now mentions `carbs_g` + `fat_g` + migration 025 at lines 36-37 and 126. Closed.
- ✅ **`reporting/docs/current_system_state.md`** — NEW file, clean operational-truth surface for the v0.1.15 published baseline. Referenced from AGENTS.md "Authoritative orientation" line 34.
- ⚠️ **`reporting/docs/architecture.md`** — partial close. Has the W-C `target_type` extension mention at line 218 but lacks W-A (`present` block, `is_partial_day`, `target_status`), W-D arm-1 (`insufficient_data` short-circuit), W-E (skill consumption). PLAN §3 cross-cutting line:
  > **`reporting/docs/architecture.md`** — extend nutrition section with target-aware classification path (W-C + W-D arm-1).

  Codex should add a short paragraph in the nutrition-pipeline section covering the W-A presence-block read surface, the W-D arm-1 partial-day suppression to `nutrition_status='insufficient_data'`, and the snapshot-side wiring through `derive_nutrition_signals`. ~10-15 lines.

- ⚠️ **`README.md` install instructions** — line 137 still says `pipx install health-agent-infra` without version pin or CDN-cache bypass. Per `reference_pypi_publish_cdn_lag.md` memory, the bare form fails for ~2 min after publish. For the named foreign-user candidate's onboarding (and any future foreign user), the canonical install is:

  ```bash
  pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.15.1'
  ```

  Worth adding to README's onboarding section.

### 4.2 README install hardening

`README.md` install section currently says `pipx install health-agent-infra` without a version pin or CDN-cache bypass. Per `reference_pypi_publish_cdn_lag.md` memory, the bare form fails for ~2 min after publish. For the named foreign-user candidate's onboarding (any future foreign user), the canonical install command is:

```bash
pipx install --force --pip-args="--no-cache-dir --index-url https://pypi.org/simple/" 'health-agent-infra==0.1.15.1'
```

Worth adding to README's onboarding section so the next foreign user doesn't hit the lag.

### 4.3 Scope decision

Two options (revised after the maintainer's parallel doc-sweep landed the bulk of the doc gaps):

- **(A) Pure keyring-fix-only as v0.1.15.1.** Matches v0.1.12.1 / v0.1.14.1 hotfix discipline. The 2 small remaining doc gaps (architecture.md nutrition section + README install snippet) roll into v0.1.16 named-fix.
- **(B) Bundle keyring fix + the 2 small remaining doc items into v0.1.15.1.** Light scope expansion; the 2 doc edits are ≤30 lines combined; tightens the "everything we missed" close-out.

**Maintainer to decide.** With most doc gaps already closed by the parallel sweep, the case for (B) is stronger now than it was — only ~30 lines of doc work remain and they directly improve the named foreign-user candidate's install path (the README snippet) and the audit-visible nutrition-pipeline surface (architecture.md). Default to **(B)** unless the maintainer prefers strict hotfix discipline.

---

## §5 — Files Codex will touch

### 5.1 P0 (required)

| File | Change |
|---|---|
| `pyproject.toml` | bump `version = "0.1.15"` → `"0.1.15.1"`; add `"keyrings.alt"` to `dependencies` |
| `src/health_agent_infra/core/pull/auth.py` | extend `_default_backend()` per §3.2 |
| `CHANGELOG.md` | new `## [0.1.15.1] - 2026-05-03` entry; theme = "Hardening: Linux keyring fall-through" |
| `AUDIT.md` | new `## v0.1.15.1 - 2026-05-03` entry; mark hardening tier; abbreviated audit chain (no D14, no external Codex IR) per AGENTS.md D15 hardening latitude |
| `ROADMAP.md` | new bullet under "Now" listing v0.1.15.1 hardening |
| `reporting/plans/v0_1_15_1/RELEASE_PROOF.md` | new lightweight RELEASE_PROOF (per AGENTS.md "Hotfix … Lightweight RELEASE_PROOF") |
| `reporting/plans/v0_1_15_1/REPORT.md` | new short narrative |
| `reporting/docs/agent_cli_contract.md` | regenerate via `uv run hai capabilities --markdown > reporting/docs/agent_cli_contract.md` (version string changes) |
| `verification/tests/snapshots/cli_capabilities_v0_1_13.json` | regenerate via `uv run hai capabilities --json > verification/tests/snapshots/cli_capabilities_v0_1_13.json` (the `hai_version` field is filtered as volatile per `_VOLATILE_FIELDS` in `test_cli_parser_capabilities_regression.py`, so this may not actually drift — verify before regen) |
| `uv.lock` | will refresh automatically when adding the dep |

### 5.2 If Option B (bundle remaining doc items) — additional

| File | Change |
|---|---|
| `reporting/docs/architecture.md` | add ~10-15 lines in the nutrition-pipeline section covering W-A presence-block read surface + W-D arm-1 `nutrition_status='insufficient_data'` partial-day suppression + snapshot-side wiring through `derive_nutrition_signals`. The W-C `target_type` extension at line 218 is already there; do not duplicate. |
| `README.md` | line 137 install snippet → add `==0.1.15.1` pin + `--no-cache-dir --index-url https://pypi.org/simple/` bypass per §4.2; ~5 lines. |
| (state_model_v1.md, current_system_state.md) | already updated by parallel doc-sweep; do not touch. |

### 5.3 Files Codex must NOT touch (out of scope)

- Any source under `src/health_agent_infra/` other than `core/pull/auth.py` (this is a hotfix; do not bundle other fixes; named-defer to v0.1.16)
- Any test under `verification/tests/` beyond what's needed to exercise the fix (don't add new test surface; prove the fix via the existing red tests going green)
- Any `reporting/plans/v0_1_15/` content (that cycle is sealed; v0.1.15.1 is a separate cycle dir)
- Any AGENTS.md "Settled Decisions" or "Do Not Do" sections (no governance edits in a hotfix)
- Migration files (no schema change in this hotfix)

---

## §6 — Test surface

### 6.1 Tests that should flip from RED → GREEN after the fix

Visible:
- `verification/tests/test_readme_quickstart_smoke.py::test_quickstart_commands_run_cleanly` (catches both the `hai init` + `hai doctor` keyring crashes)
- `verification/tests/test_w_pv14_01_csv_isolation.py::test_stats_warns_on_for_date_divergence_over_48h`
- `verification/tests/test_w_pv14_01_csv_isolation.py::test_doctor_warns_on_for_date_divergence_over_48h`

Not visible from screenshot (Codex enumerate from the CI log):
- ~10 additional failures, likely keyring-family

### 6.2 Tests that must STAY GREEN

- All 6 W-id test files from v0.1.15 (`test_w_gym_setid.py`, `test_w_pv14_01_csv_isolation.py` — non-divergence tests, `test_w_a_presence_block.py`, `test_w_c_target_nutrition.py`, `test_w_d_arm_1_partial_day_suppression.py`, `test_w_e_skill_presence_consumption.py`)
- `test_state_store.py` schema-version assertions (still 25)
- `test_cli_parser_capabilities_regression.py` snapshot tests (only volatile-field changes; `hai_version` is filtered)
- `test_capabilities.test_committed_contract_doc_matches_generated` (regenerate `agent_cli_contract.md` after version bump)
- `test_doc_freshness_assertions.test_v0_1_14_w_id_in_summary_surface_implies_in_plan_catalogue` (v0.1.16/v0.1.17 + carry-over already in allowlist)

### 6.3 New tests Codex may want to add (judgment call)

A test that exercises the `_default_backend()` defensive fall-through with a mocked `keyring` module that raises `NoKeyringError` — proves the fix mechanically and prevents future regression. Optional but cheap.

---

## §7 — Ship procedure

Per AGENTS.md hotfix tier + `reference_release_toolchain.md` memory:

```bash
# 1. Apply fixes (§3 + optionally §4)
# 2. Run full gates locally
uv run pytest verification/tests -q
uvx mypy src/health_agent_infra
uvx bandit -ll -r src/health_agent_infra

# 3. Bump pyproject.toml + regen contract doc
uv run hai capabilities --markdown > reporting/docs/agent_cli_contract.md
uv run hai capabilities --json > verification/tests/snapshots/cli_capabilities_v0_1_13.json

# 4. Commit (one-line message per Dom's preference)
git add <touched files>
git commit -m "v0.1.15.1 hotfix: Linux keyring fall-through (NoKeyringError no longer crashes hai init/doctor/stats/pull); CI Linux test 3.11 + 3.12 green"

# 5. Push
git push origin main

# 6. Build + publish
rm -rf dist/
uvx --from build python -m build --wheel --sdist
ls dist/  # confirm health_agent_infra-0.1.15.1-py3-none-any.whl + .tar.gz

# 7. PyPI publish — single-line invocation per release-paste-safety memory
#    (zsh + bracketed-paste mangles multi-line commands)
uvx twine upload dist/health_agent_infra-0.1.15.1-py3-none-any.whl dist/health_agent_infra-0.1.15.1.tar.gz

# OR write to /tmp script + run with bash:
cat > /tmp/hai-publish-0.1.15.1.sh <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
cd /Users/domcolligan/health_agent_infra
uvx twine upload \
    dist/health_agent_infra-0.1.15.1-py3-none-any.whl \
    dist/health_agent_infra-0.1.15.1.tar.gz
EOF
bash /tmp/hai-publish-0.1.15.1.sh

# 8. Verify
curl -s https://pypi.org/pypi/health-agent-infra/json | python3 -c \
    "import json,sys; print('latest:', json.load(sys.stdin)['info']['version'])"
# expect: latest: 0.1.15.1

# 9. Confirm CI green on the new commit
```

Per Dom's standing instruction: PyPI publish + git push are maintainer-only (token in `~/.pypirc`); Codex should leave Step 5 + Step 7 commands ready in chat for Dom to execute, OR if the runtime allows Codex to invoke them, prompt before running.

---

## §8 — Acceptance criteria for v0.1.15.1

- ✅ `_default_backend()` falls through to `_NullBackend` on `NoKeyringError`, not just `ImportError`.
- ✅ `keyrings.alt` listed as runtime dep in `pyproject.toml`.
- ✅ All 14 CI failures from the v0.1.15 run resolve.
- ✅ Suite 2631 pass / 3 skipped on macOS (Codex added the optional defensive-fall-through test).
- ✅ Mypy clean.
- ✅ Bandit 0 medium/high.
- ✅ pyproject version `0.1.15` → `0.1.15.1`.
- ✅ RELEASE_PROOF.md + REPORT.md authored at `reporting/plans/v0_1_15_1/`.
- ✅ CHANGELOG + AUDIT + ROADMAP entries added.
- ✅ PyPI publish lands; `pip install health-agent-infra==0.1.15.1` works on Linux + Mac.
- ✅ CI green on the post-publish commit.

---

## §9 — Things Codex needs to know about Dom's working style + this repo

From `~/.claude/CLAUDE.md` "Working Style" + project memory:

- **Lead with the verdict.** Cite sources. Separate verified facts from inference. No flattery.
- **One-line `git commit -m` messages on this project.** No heredoc bodies.
- **Don't push to remote without explicit authorization.** PyPI publish too. Both have token-based maintainer-only auth.
- **Don't skip hooks** (`--no-verify`) or bypass signing unless explicitly asked.
- **Stale-checkout discriminator.** Active repo is `/Users/domcolligan/health_agent_infra/`; ignore `/Users/domcolligan/Documents/health_agent_infra/` (HEAD `2811669`, months behind). `pwd` + `git log -1` on session start.
- **Release-paste safety.** zsh + bracketed-paste mangles multi-line commands; write commit messages and complex sequences to `/tmp/*.txt` or `/tmp/*.sh` files and run with `bash`.
- **PyPI publish CDN lag.** First `pip install` after upload fails for ~2 min; bypass with `pipx install --pip-args="--no-cache-dir --index-url https://pypi.org/simple/"`.

---

## §10 — Reference list

### v0.1.15 cycle artifacts (the cycle this hotfix follows)

- `reporting/plans/v0_1_15/PLAN.md` — round-4 final scope (the cycle that just shipped).
- `reporting/plans/v0_1_15/RELEASE_PROOF.md` — what shipped at v0.1.15.
- `reporting/plans/v0_1_15/REPORT.md` — cycle narrative.
- `reporting/plans/v0_1_15/codex_implementation_review_response.md` — D15 IR round 1 (6 findings).
- `reporting/plans/v0_1_15/codex_implementation_review_round_2_response.md` — round 2 (2 findings).
- `reporting/plans/v0_1_15/codex_implementation_review_round_3_response.md` — round 3 (1 nit, SHIP_WITH_NOTES).
- `reporting/plans/v0_1_15/codex_implementation_review_response_response.md` — maintainer triage covering all three IR rounds.

### Hotfix-tier prior art

- `reporting/plans/v0_1_12_1/` — cloudflare User-Agent hotfix (single workstream, no D14, no external IR).
- `reporting/plans/v0_1_14_1/` — Garmin-live unreliability structured-signal hotfix (single workstream, abbreviated audit chain).

### Operating contract

- `AGENTS.md` — operating contract; "Settled Decisions" list (D1-D15); "Do Not Do" list; "Patterns the cycles have validated"; D15 hardening + hotfix tier definitions.
- `CLAUDE.md` (project root) — Claude Code session-efficiency layer over AGENTS.md.
- `~/.claude/CLAUDE.md` — Dom's user-account context (working style, calibration preferences).

### Memories Codex should be aware of (Dom's private agent memory; live at `/Users/domcolligan/.claude/projects/-Users-domcolligan-health-agent-infra/memory/`)

- `feedback_release_paste_safety.md` — zsh paste-mangling workaround (write to /tmp file).
- `feedback_pypi_publish_cdn_lag.md` — bypass cache on first install.
- `reference_release_toolchain.md` — build + publish commands (uvx --from build; explicit dist filenames).
- `feedback_run_commands_dont_print_them.md` — when authorized, execute; only ask for PyPI / push / destructive shared-state ops.
- `project_v0_1_15_w2u_gate_candidate.md` — private memory preserves the candidate identity; KEEP HIS NAME OUT OF PUBLIC ARTIFACTS (CHANGELOG, RELEASE_PROOF, GitHub-visible docs use initials or omit). The v0.1.15 RELEASE_PROOF + REPORT used the full name before the v0.1.15.1 scrub.

---

## §11 — Open questions for Dom (decide before Codex starts implementation)

1. **Scope decision:** Option A (pure keyring fix) or Option B (keyring + 2 small remaining doc items — architecture.md nutrition section + README install snippet)? Doc gaps that landed in the parallel sweep before this report (state_model_v1.md, current_system_state.md, etc.) are out of Codex's touch list either way. Default revised to **(B)** — see §4.3.
2. **Candidate name in public artifacts:** the v0.1.15.1 ship includes the maintainer-approved scrub. Public docs now preserve the structural fact that a named candidate exists while omitting the personal identifier. Private memory keeps the operational identity.
3. **CI workflow audit:** if the README quickstart smoke was failing on Linux pre-v0.1.15, the maintainer was shipping despite red CI. Worth a v0.1.16-or-later cycle proposal to enforce CI-green-before-publish; out of scope for this hotfix but worth noting in the v0.1.16 README scope table.
4. **§3.3 status-method audit:** include in v0.1.15.1 or defer to v0.1.16? Recommend defer — the §3.1 + §3.2 fixes likely close the CI failure; §3.3 is belt-and-braces and adds scope.
5. **Parallel doc-sweep work currently uncommitted:** at hand-off time the maintainer (or linter) has a working tree with ~14 modified files (AGENTS.md, README.md, architecture.md, state_model_v1.md, etc.) and ~3 untracked (current_system_state.md, post_v0_1_15/). Should Codex commit those alongside the hotfix, or are they separate maintainer work that lands independently? Recommend committing as a separate "post-v0.1.15 doc sweep" commit before the v0.1.15.1 hotfix commit so the hotfix delta is clean.
