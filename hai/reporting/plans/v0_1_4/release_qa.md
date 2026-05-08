# v0.1.5 release QA ritual

- Author: Claude (Opus 4.7) with Dom Colligan
- Last updated: 2026-04-24 (post-Codex r3)
- Status: **active** — follow this before the v0.1.5 PyPI push.
- Tracks: v0.1.5 §Release criteria.
- Note on versioning: internal planning was scoped as v0.1.4, but
  real PyPI already has an immutable v0.1.4 from commit `81997aa`
  (pre-session state). This work ships as `0.1.5`; the `v0_1_4`
  planning path is retained as a historical reference.

---

## When to run this ritual

- Before tagging `v0.1.5.rc*` / `v0.1.5`.
- Before re-uploading to TestPyPI after a breaking change to any
  public surface (CLI flags, SKILL.md allowed-tools, migration
  sequence, contract manifest shape).
- After any dependency bump to `keyring`, `platformdirs`,
  `garminconnect`, or the `intervals_icu` adapter.

Skip only if every change since the last green run is documented
as trivial (no-logic edits, docstring changes, comment scrub). If
in doubt, run the ritual — it's ~45 minutes end-to-end.

---

## Phase 0 — verify the tree

```bash
git status                       # tree clean; if not, commit / stash first
git log -5 --oneline            # confirm the intended HEAD
python3 -m pytest -q            # full suite green locally (≥1690 tests)
```

Expected: `X passed, 4 skipped, 0 failures`. Any xfail or xpass is a
red flag — investigate before moving on.

Also:

```bash
python3 -c "from health_agent_infra.cli import main; main(['capabilities', '--markdown'])" \
  > /tmp/current_contract.md
diff reporting/docs/agent_cli_contract.md /tmp/current_contract.md
```

Expected: no diff. If there is one, regenerate the committed
contract doc and add the change to the release PR.

---

## Phase 1 — fresh-profile dogfood against TestPyPI

The point: catch anything the test suite can't see — dependency-tree
drift, entry-point breakage, keyring permission surprises, README
copy-paste bugs.

1. **Build + upload to TestPyPI.** From a clean checkout:

   ```bash
   rm -rf dist/
   python3 -m build
   python3 -m twine upload --repository testpypi dist/*
   ```

2. **Fresh user profile.** Either a new macOS user account (`System
   Settings → Users` → `+`) or a throwaway Linux VM. The goal is to
   exercise credential / keyring / platformdirs paths against a
   truly empty home directory.

3. **Install from TestPyPI.** Inside the fresh profile. Because real
   PyPI already has an immutable `0.1.4`, pipx's `--extra-index-url`
   fall-through will prefer that copy unless the version is pinned
   explicitly — pin via `"health-agent-infra==0.1.5"` (or current
   target), and use `--pip-args="--no-cache-dir"` to defeat any
   per-version cache:

   ```bash
   pipx install --index-url https://test.pypi.org/simple/ \
                --pip-args="--extra-index-url https://pypi.org/simple/ --no-cache-dir" \
                --suffix=_tp \
                "health-agent-infra==0.1.5"
   hai_tp --version   # confirm 0.1.5
   ```

   The `--suffix=_tp` keeps the TestPyPI install isolated from the
   operator's real `hai` install (pipx would otherwise refuse to
   install a second copy of the same package).

4. **Run the README quickstart.** Copy-paste (don't retype) the
   `hai init` / `hai auth` / `hai pull` / `hai daily` / `hai today`
   / `hai stats` sequence from the README. Note any prompt wording
   that feels off, any missing macOS "Always Allow" hint, any
   crash-on-empty-DB.

5. **First-run adequacy check.** After `hai today`, verify:
   - At least one per-domain section surfaces a recommendation
     (not 6 defers).
   - Cold-start footer appears for every domain the user hasn't
     accumulated 14 days on yet.
   - Voice passes the linter smell-test: no rule IDs, no medical
     language, no raw numbers beyond what the rationale names.

6. **Re-author path.** Rerun `hai intake readiness` with a
   different `planned_session_type`, rerun `hai daily --supersede`,
   rerun `hai today`. Confirm the leaf plan renders, the v1 plan
   is invisible, and `hai explain --for-date --plan-version all`
   walks both.

7. **Review record path.** Write an outcome against the plan's
   recovery rec via `hai review record`. Then run `hai daily
   --supersede` again. Record a second outcome against the (now
   superseded) original rec. Confirm the stderr note about
   re-linking and that `sqlite3 ~/.local/share/.../state.db
   'SELECT recommendation_id, re_linked_from_recommendation_id
   FROM review_outcome'` shows the re-link audit.

Any failure at any step → file the issue, fix, re-upload RC.

---

## Phase 2 — spot-check regression catches

For each of these five landmark fixes, revert the fix locally,
confirm CI fails with a specific test name, then `git restore` the
revert before moving on. Goal: prove the test suite actually
guards each regression.

| Fix to revert | Expected failing test(s) |
|---|---|
| D1 `hai propose --replace` revision flag | `safety/tests/e2e/test_reauthor_journey_2026_04_23.py::test_propose_replace_creates_new_revision_and_links_old_leaf` |
| D1 supersede-lineage targets canonical leaf | `safety/tests/test_synthesis_concurrency.py` chain tests + `test_explain_*` leaf resolution |
| D2 `hai intake readiness` persistence | `safety/tests/test_intake_readiness.py` persistence-round-trip tests |
| D4 running cold-start relaxation | `safety/tests/test_running_cold_start_policy.py::test_cold_start_green_recovery_with_planned_session_lifts_defer` |
| Defer review-question per-domain | `safety/tests/test_defer_review_question_per_domain.py` parametrised suite |
| #16 intervals.icu /activities endpoint wired through pull→clean→snapshot | adapter suite `safety/tests/test_pull_intervals_icu.py::test_adapter_surfaces_activities_from_client` + 3 others — verified 2026-04-24: replacing `activities = self._fetch_activities_safe(...)` with `activities = []` fires 4 adapter tests |
| Phase A synthesis safety closure (Codex P1 #1) | `safety/tests/test_synthesis_safety_closure.py` — verified 2026-04-24: removing the `validate_recommendation_dict(rec)` loop in `run_synthesis` fires 7 tests (banned tokens in proposal rationale / action_detail / uncertainty / skill overlay rationale / uncertainty / review_question + atomic rollback) |
| Phase B proposal JSONL recovery (Codex P1 #2) | `safety/tests/test_reproject_proposal_recovery.py` — verified 2026-04-24: forcing `has_proposals_group = False` fires all 11 tests |
| Phase C canonical-leaf uniqueness (Codex P2 #3) | `safety/tests/test_synthesis_safety_closure.py::test_db_partial_unique_index_rejects_second_canonical_leaf` — verified 2026-04-24: removing migration 018 file fires the DB-level IntegrityError test |
| Phase D privacy hardening (Codex §7) | `safety/tests/test_privacy_hardening.py::test_initialize_database_locks_perms_on_creation` + `test_initialize_database_relocks_perms_on_subsequent_init` — verified 2026-04-24: commenting out `secure_state_db(db_path)` fires both (DB file at 0o644 vs expected 0o600) |

Update this table whenever a major fix lands — the value comes from
periodically proving each contract is genuinely tested.

---

## Phase 3 — surface audit

1. **`hai doctor --json`** on a fresh profile → `overall_status=ok`
   when credentials are in place, `overall_status=warn` when a
   source is uncredentialed. Nothing should be `fail` on a
   properly-initialised profile.

2. **`hai capabilities`** (JSON is the default; the CLI rejects
   `--json` explicitly, use `--markdown` only for the doc
   regenerator) → every command has `agent_safe` set; every flag
   has a non-empty `help`; every high-traffic command (`hai today`,
   `hai daily`, `hai synthesize`, `hai propose`, `hai review
   record`) carries `output_schema` + `preconditions`.

3. **Skill integrity:**

   ```bash
   python3 -m pytest safety/tests/test_docs_integrity.py -q
   python3 -m pytest safety/tests/test_recovery_skill_gates.py -q
   ```

   Expected: all green. These guard against the class of drift
   where a skill instructs a command that no longer exists.

---

## Phase 4 — PyPI push

Only after Phases 0–3 are green:

1. Create the release tag: `git tag v0.1.5 && git push origin v0.1.5`.
   (The v0.1.4 tag is already present from commit `81997aa` and is
   locked to that state on PyPI.)
2. Build + upload to real PyPI:

   ```bash
   rm -rf dist/
   python3 -m build
   python3 -m twine upload dist/*
   ```

3. `pipx install --pip-args="--no-cache-dir" "health-agent-infra==0.1.5"`
   on a second fresh profile; rerun the Phase-1 quickstart against
   real PyPI. This is a shorter sanity pass — the full ritual
   already happened on TestPyPI. Version pin required because real
   PyPI still serves the older 0.1.4 and pip's default resolution
   may prefer a cached older wheel.

4. Release notes — copy the acceptance-criteria summary into the
   GitHub Release notes, link each closed item to its PR(s).

---

## Release-criteria checklist (v0.1.5 §Release criteria)

Tick off the eight bullets before pushing:

- [x] All 18 numbered acceptance items complete (see
      `acceptance_criteria.md`).
- [x] All four D-docs (D1/D2/D3/D4) ratified and merged.
- [x] Each workstream's artifact list complete (A correctness, B
      user surface, C contract, D cold-start, E test categories).
- [x] CI green on main with e2e / contract / snapshot categories
      present under `safety/tests/`.
- [x] Dogfood day completed (Phase 1 above) — zero new P0 issues.
- [x] Spot-check regression catch (Phase 2 above) — each reverted
      fix surfaces a specific named test failure (verified 2026-04-24
      for all 5 v0.1.4/v0.1.5 landmark fixes; see landmark-fixes
      table above).
- [ ] `hai doctor` reports `overall_status=ok` on a fresh
      credentialed install.
- [ ] README reader test — a reader running `hai init` +
      `hai daily` + `hai today` with no agent mediation gets a
      useful plan and understands what they're reading.

Any failure → stay on `0.1.3.devN`, file the regression, iterate.

---

## Non-goals for this ritual

- **Performance / load testing.** v0.1.4 is a single-user local
  agent; the only perf concern is that `hai daily` returns in
  seconds on a realistic DB. Anything past that is v0.2+ scope.
- **Cross-Python-version matrix.** 3.11 + 3.12 + 3.13 covered via
  CI; the ritual doesn't re-test versions locally.
- **Cross-platform matrix.** Dogfood runs on macOS (primary
  target). Linux smoke-tests via CI + the Keychain hint is
  macOS-only by design.
