# `empty_user`

`empty_user` is the benchmark's empty-but-initialized HAI state. It has
the current SQLite schema and no synthetic health evidence, proposals,
plans, reviews, goals, targets, memories, credentials, or notes.
The packaged `exercise_taxonomy` seed rows are allowed because they are
static runtime vocabulary, not user data.

Build it with:

```bash
python benchmark/governed_agent_bench/fixtures/empty_user/build.py /tmp/empty_user
```

The builder runs `hai state init` through the Python module entrypoint
under the benchmark hermetic environment:

- `HAI_HERMETIC=1`
- `HAI_STATE_DB=<fixture>/state.db`
- `HAI_BASE_DIR=<fixture>/base`
- `HOME=<fixture>/home`
- `XDG_CONFIG_HOME=<fixture>/xdg_config`

This fixture serves L1/L2 setup, abstention, and command-routing tasks.
It stresses the harness allowlist and hermetic setup boundary without
introducing private or clinical data.
