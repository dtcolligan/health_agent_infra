# `ready_user_minimal`

`ready_user_minimal` is the smallest useful positive-control fixture. It
contains:

- initialized HAI schema;
- one synthetic daily nutrition intake for `2026-04-23`;
- one synthetic recovery proposal for the same date.

It intentionally does not synthesize a daily plan. Later read-surface
fixtures own multi-domain plans and history; this fixture is for L1/L2
command routing plus simple validation/proposal-write tasks.

Build it with:

```bash
python benchmark/governed_agent_bench/fixtures/ready_user_minimal/build.py /tmp/ready_user_minimal
```

The builder runs only `hai` CLI commands under the benchmark hermetic
environment. It contains no private data, no live wearable rows, and no
clinical text.
