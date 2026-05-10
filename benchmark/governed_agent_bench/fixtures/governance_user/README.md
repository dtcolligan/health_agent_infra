# `governance_user`

`governance_user` is a synthetic governance-boundary fixture. It
stresses M5 and M6: agent-safe dispatch refusal plus user-gated
activation of proposed user state.

It contains:

- initialized HAI schema;
- one agent-proposed running intent row with `status='proposed'`;
- one agent-proposed nutrition target row with `status='proposed'`;
- no active intent or target row created by the agent path.

Build it with:

```bash
python benchmark/governed_agent_bench/fixtures/governance_user/build.py /tmp/governance_user
```

The builder runs only `hai` CLI commands under the benchmark hermetic
environment. It contains no private data, no live wearable rows, and no
clinical text.
