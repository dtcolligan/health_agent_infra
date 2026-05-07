# Frozen Manifests

This directory stores runtime contract snapshots used by benchmark
tasks. The first planned snapshot is `hai_0_2_0.json`, generated from:

```bash
uv run hai capabilities --json
```

Do not replace a manifest in place after tasks depend on it. Add a new
snapshot and use L7 drift tasks to compare behavior across versions.
