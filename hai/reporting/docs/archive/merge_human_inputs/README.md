# Archived merge_human_inputs bucket

This archive preserves the former top-level `merge_human_inputs/` bucket. Typed intake logic itself is not a Python module in this tree; it is an agent concern described by the `merge-human-inputs` skill.

## What lives here

- `examples/` — example payloads illustrating the shape of structured human input the flagship loop consumes. Useful for:
  - hand-crafting a `--manual-readiness-json` file to pass to `hai pull`
  - reference when authoring or revising the merge-human-inputs skill
  - regression fixtures if we add intake-validation tests later

## What used to live here

Before the 2026-04-17 reshape, this bucket contained `intake/` Python modules (`typed_manual_readiness_intake.py`, `voice_note_intake.py`) and `manual_logs/manual_logging.py` that did structured parsing and canonicalisation. The reshape swept those because the judgment they encoded (how to classify free-text soreness language, how to route an ambiguous voice note, etc.) is agent work. That judgment is now expressed in `skills/merge-human-inputs/SKILL.md`.

The flagship Python only sees the *output* of the intake step — a validated manual-readiness dict with `soreness`, `energy`, `planned_session_type`, `active_goal`, `submission_id`. See `src/health_agent_infra/schemas.py::CleanedEvidence` for how the flagship consumes it.

## How intake works now

The agent reads the merge-human-inputs skill and partitions raw user input into dataset slots. For the flagship hot path (manual readiness), the agent has two equivalent paths:

- **`hai intake readiness` -> stdout** (recommended). CLI flags (`--soreness`, `--energy`, `--planned-session-type`, `--active-goal`) emit a validated JSON blob. Compose with `hai pull --manual-readiness-json`.
- **Hand-written JSON file.** For fixtures or replays, skip the intake command and write a JSON object matching the four fields directly to a file, then pass it to `hai pull --manual-readiness-json <path>`.

The runtime does not attempt to parse free text. If the skill returns ambiguous input, the agent asks a clarifying question before calling `hai`.

## Why this archive exists

The eight-bucket mental model was the project's original organising frame, but physical runtime code now lives under `src/health_agent_infra/` and the active intake skill lives under `src/health_agent_infra/skills/merge-human-inputs/`. This archive keeps the old README + examples for doctrine navigation and historical context. It is not a Python package.
