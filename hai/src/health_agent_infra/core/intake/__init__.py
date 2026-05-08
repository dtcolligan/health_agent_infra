"""Core cross-domain intake helpers.

Intake helpers that are not bound to a single domain live here. Phase 1
lands ``note.py`` (cross-domain context notes, ex-``health_agent_infra.intake.note``).
Per-domain intake (gym, nutrition, stress) lives under ``domains/<name>/intake.py``.

Pattern mirrors ``core/writeback/`` and ``core/review/``: validation + JSONL
audit is the durable boundary; DB projection is a best-effort queryable view
that ``hai state reproject --base-dir`` can rebuild from the JSONL.
"""
