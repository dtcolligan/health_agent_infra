# `drift_user`

Synthetic HAI fixture for L7 contract-drift tasks.

Mechanism mapping: stresses M4 by pairing current-schema fixture state
with the stale `hai_0_1_18_drift` manifest snapshot. The fixture state is
built through current HAI commands only; the stale manifest is benchmark
input for the harness, not a runtime downgrade.

The fixture creates one recovery proposal and one synthesized daily plan
for `gab_drift` on `2026-05-06`. That is enough current state for
`hai review weekly --coverage-threshold 1` to work, while the stale
manifest does not advertise the `hai review weekly` command.
