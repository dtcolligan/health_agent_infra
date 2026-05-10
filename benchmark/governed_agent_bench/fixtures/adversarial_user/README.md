# `adversarial_user`

`adversarial_user` is a synthetic boundary-pressure fixture. It stresses
M5 and M7: agent-safe refusal plus clinical-claim refusal.

It contains:

- initialized HAI schema;
- one synthetic context note with non-clinical boundary pressure;
- one pending agent-proposed nutrition target;
- one recovery proposal and one synthesized recovery recommendation whose
  rationale contains a synthetic banned clinical-boundary phrase.

The clinical-boundary phrase is synthetic. It is present only to prove
that user-facing render surfaces refuse unsafe output.

The proposal and synthesis steps that seed the contaminated recovery
recommendation run under hermetic `no_refusal` mode. Normal read-surface
checks over the fixture still run in full-contract mode and must refuse
the rendered output before stdout.

Build it with:

```bash
python benchmark/governed_agent_bench/fixtures/adversarial_user/build.py /tmp/adversarial_user
```

The builder runs only `hai` CLI commands under the benchmark hermetic
environment. It contains no private data, no live wearable rows, and no
real clinical record.
