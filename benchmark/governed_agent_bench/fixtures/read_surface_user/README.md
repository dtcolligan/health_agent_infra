# `read_surface_user`

`read_surface_user` is a synthetic seven-day HAI history for deterministic
read-surface tasks. It stresses M8: narration over audit-row evidence.

It contains:

- initialized HAI schema;
- seven synthetic nutrition intakes for ISO week `2026-W18`;
- six domain proposals and one synthesized daily plan for each day;
- recovery review events and outcomes for each day.

It supports `hai today`, `hai explain`, `hai state snapshot`, and
`hai review weekly` tasks without live wearable data or private rows.

Build it with:

```bash
python benchmark/governed_agent_bench/fixtures/read_surface_user/build.py /tmp/read_surface_user
```

The builder runs only `hai` CLI commands under the benchmark hermetic
environment. It contains no private data, no live wearable rows, and no
clinical text.
