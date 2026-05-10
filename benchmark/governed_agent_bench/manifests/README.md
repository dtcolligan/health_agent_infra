# Frozen Manifests

This directory stores runtime contract snapshots used by benchmark
tasks. The first committed snapshot is `hai_0_2_0.json`, generated
from:

```bash
uv run hai capabilities --json
```

Snapshots are committed as provenance envelopes, not raw command dumps.
The envelope records the source commit, generation command, HAI version,
contract schema version, and embedded manifest. Stability checks compare
the embedded manifest while ignoring `generated_at`.

`hai_0_2_0.json` was generated from source commit
`0f114e31da67bcd245702c903d8e12b0bb92a197`, with embedded
`contract_schema_version` `agent_cli_contract.v2`.

Do not replace a manifest in place after tasks depend on it. Add a new
snapshot and use L7 drift tasks to compare behavior across versions.
