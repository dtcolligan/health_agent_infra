# GovernedAgentBench Hermetic HAI Recipe

Benchmark subprocesses must run HAI with an all-or-nothing fixture
environment. The harness must set:

- `HAI_HERMETIC=1` — enables runtime refusal for network and OS keyring
  access.
- `HAI_STATE_DB=<fixture>/state.db` — redirects SQLite state away from
  the user's default state DB.
- `HAI_BASE_DIR=<fixture>/base` — redirects JSONL/proposal/review audit
  files away from `~/.health_agent`.
- `HOME=<fixture>/home` plus platform config overrides such as
  `XDG_CONFIG_HOME=<fixture>/xdg_config` where supported — keeps
  platform-default config lookups inside the fixture.

For commands that need demo-mode resolver overrides, the harness may
also create a HAI demo marker that points at the same fixture DB,
base-dir, and config path. The marker is optional for simple
subprocesses that pass the env redirections above.

Negative rule: setting `HAI_STATE_DB` or `HAI_BASE_DIR` without
`HAI_HERMETIC=1` is not a benchmark run. The harness must refuse to
launch that subprocess, because otherwise a benchmark can silently use
live network/keyring surfaces while still writing to fixture state.

Expected effects:

- live pull sources fail before network access;
- credential commands fail before keyring access;
- read-only commands such as `hai capabilities --json` work;
- default user paths under the redirected `HOME` remain untouched.
