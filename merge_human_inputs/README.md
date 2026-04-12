# merge_human_inputs

This lane owns the bounded slice of human-authored input surfaces introduced in structure-migration slice 1.

Contents:
- `intake/voice_note_intake.py`: canonical voice-note intake and bundle shaping
- `manual_logs/manual_logging.py`: canonical manual logging builders for hydration, meals, and gym sets
- `examples/manual_gym_sessions.example.json`: manual gym logging example payload
- `health_logger/`: migrated logger app surfaces previously rooted at `bot/`

Compatibility shims remain at:
- `health_model.voice_note_intake`
- `health_model.manual_logging`
- `bot.*`

Those wrappers preserve current entrypoints while the new canonical lane becomes the architectural source of truth for this slice.
