"""Cross-handler shared helpers for the ``hai`` CLI.

W-29.1 placeholder. The actual extraction of `_emit_json` /
`_load_json_arg` / `_coerce_date` / `_coerce_dt` / `_skills_source` /
`_w57_user_gate` from ``cli/__init__.py`` lands at W-29.2 per
``reporting/plans/v0_1_17/w29_boundary_refresh.md`` §(c).

Until W-29.2 commits, ``cli/__init__.py`` continues to own these
helpers. This module exists at W-29.1 only to anchor the package
layout — every handler-group module lands as a sibling of this file
under ``cli/handlers/``.
"""
