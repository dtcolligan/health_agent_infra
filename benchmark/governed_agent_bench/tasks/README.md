# Tasks

Tasks are grouped by benchmark level. Each task must validate against
`../schema/task.schema.json`.

Initial MVP target:

- L1 routing tasks: natural-language intent to valid `hai` command.
- L2 recovery tasks: setup failure or `USER_INPUT` handling.
- L5 narration tasks: faithful use of `hai today` / `hai explain`.
- L6 governance/refusal tasks: forbidden commands and clinical-boundary
  pressure.
- L7 drift tasks: stale manifest or changed command surface.
