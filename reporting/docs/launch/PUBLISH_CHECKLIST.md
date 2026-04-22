# PyPI publish checklist

Pre-launch state of the `health_agent_infra` package, what's already
verified, and the exact commands to push to PyPI when you're ready.
**Nothing here should be executed without an explicit "publish it"
from you** — PyPI releases are visible and hard to un-ship.

## Pre-flight (verified)

- [x] `python -m build` produces both sdist + wheel cleanly.
      Artifacts at `dist/health_agent_infra-0.1.0{.tar.gz,-py3-none-any.whl}`.
- [x] `python -m twine check dist/*` → both PASSED.
- [x] Fresh-venv wheel install works: `pipx install dist/*.whl` →
      `hai --version` prints `hai 0.1.0`, all subcommands register
      (including the new `hai stats`).
- [x] `pyproject.toml` metadata:
  - name: `health_agent_infra`
  - version: `0.1.0`
  - license: MIT (file: LICENSE)
  - requires-python: `>=3.11`
  - entry point: `hai = health_agent_infra.cli:main`
  - classifiers: Development Status :: 4 - Beta, Console, macOS/Linux.
- [x] Full test suite green: **1489 passed, 2 skipped** (the 2 skipped
      are pre-existing).
- [x] `agent_cli_contract.md` matches the auto-generated manifest
      (test `test_committed_contract_doc_matches_generated` passes).

## Pre-flight (to do before you run the publish)

- [ ] Double-check no secrets or personal data in the wheel. Quick
      audit: `unzip -l dist/*.whl | grep -iE '(secret|credential|token|api_key|\.env)'`
      — expected output: **nothing**.
- [ ] Verify the committed `README.md` renders correctly on PyPI.
      Previewable with `python -m readme_renderer README.md -o /tmp/readme.html`
      before pushing. Twine already runs this under `check`; passed.
- [ ] Confirm the 0.1.0 version slot is unclaimed on PyPI:
      `curl -s https://pypi.org/pypi/health_agent_infra/json | jq -r .info.version`
      — if it returns `null` / 404, the slot is free. If it returns
      a version, bump to `0.1.1` in `pyproject.toml` and rebuild.
- [ ] Decide: publish to **TestPyPI first**, or go straight to PyPI?
      TestPyPI is strongly recommended for the first release of any
      package — it catches metadata / README-rendering issues before
      they're permanent. See command below.
- [ ] Have your PyPI API token ready (https://pypi.org/manage/account/token/).
      Scope it to a project or this package only; don't use an
      account-wide token for a CLI upload.

## Commands — TestPyPI smoke (recommended first)

```bash
# 1. Upload to TestPyPI (does NOT affect the real PyPI).
python -m twine upload --repository testpypi dist/*

# 2. Install from TestPyPI in a fresh venv to verify the round-trip.
python -m venv /tmp/testpypi_venv
/tmp/testpypi_venv/bin/pip install \
    --index-url https://test.pypi.org/simple/ \
    --extra-index-url https://pypi.org/simple/ \
    health_agent_infra
/tmp/testpypi_venv/bin/hai --version    # expect: hai 0.1.0
/tmp/testpypi_venv/bin/hai stats --help # expect: clean help text

# 3. If anything is off, fix locally, bump to 0.1.0rc2 etc., re-upload
#    to TestPyPI. Don't reuse a version number on PyPI itself.
```

## Commands — PyPI real publish

Only after TestPyPI round-trip works, OR after deliberately skipping
TestPyPI with full confidence in the artifacts:

```bash
# Real PyPI upload. Visible immediately at:
#   https://pypi.org/project/health_agent_infra/
python -m twine upload dist/*

# Verify from a fresh venv with pipx:
pipx install health-agent-infra
hai --version           # expect: hai 0.1.0
hai init --help         # expect: --with-auth + --with-first-pull shown
hai stats --help        # expect: --db-path, --user-id, --limit, --json
```

## After publish

- [ ] Bump `version` in `pyproject.toml` to `0.1.1-dev0` or similar so
      local installs don't silently conflict with the published 0.1.0.
      Commit the bump on `main`.
- [ ] Tag the released commit: `git tag v0.1.0 && git push origin v0.1.0`.
- [ ] Create a GitHub release from the tag with a terse changelog
      summarising what `0.1.0` ships (the flagship loop, six domains,
      the new `hai init --with-auth --with-first-pull`, and `hai stats`).
- [ ] Update the README's screencast placeholder once a take exists.
- [ ] Stage the Show HN post for the timing window you choose
      (Tue–Thu 8–10am PT; see `show_hn_draft.md`).

## If something goes wrong

- **Wrong version uploaded?** You **cannot** delete and re-upload the
  same version on PyPI. Yank it (`https://pypi.org/help/#yanked`) and
  publish the next patch. Don't try to delete — it's a bad habit and
  usually impossible.
- **Broken package discovered post-publish?** Yank the broken version,
  publish a fixed `0.1.1` as fast as possible, link the yank reason to
  the fix version.
- **README renders wrong on PyPI?** Fix markdown, bump version, republish.
  Not yankable for cosmetics but not worth a panic — fix in the next
  patch.

## Decisions Dom owns before publishing

- [ ] TestPyPI first, or straight to PyPI?
      (Recommendation: TestPyPI first for first-ever release.)
- [ ] PyPI token scope: package-scoped or account-scoped?
      (Recommendation: package-scoped. Create after first publish if
      the scope-to-project option isn't available before.)
- [ ] Tag format: `v0.1.0` or `0.1.0`?
      (Recommendation: `v` prefix — aligns with most GitHub release
      tooling and semver convention.)
- [ ] Announce cadence: tag → GitHub release → screencast → Show HN
      in **one session** (higher risk, higher signal) or staged over
      a week (safer, less momentum)?
      (Recommendation: staged over 7 days — publish Monday, screencast
      by Wed, Show HN Thu 9am PT. Lets the PyPI page settle before
      traffic arrives.)
