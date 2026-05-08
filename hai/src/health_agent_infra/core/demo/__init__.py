"""Demo-mode helpers for the `hai` CLI (W-Va, v0.1.11).

Demo mode is an isolated session where every read + write routes to
a per-session scratch root, so demos and onboarding flows never
touch the user's real ``~/.health_agent`` tree, real
``state.db``, or real ``thresholds.toml``.

Public API:

    is_demo_active() -> bool
    require_valid_marker_or_refuse() -> Optional[DemoMarker]
    open_session(...) -> DemoMarker
    close_session() -> None
    cleanup_orphans() -> list[str]

The resolver-override hooks live in
``core.state.store.resolve_db_path``,
``core.paths.resolve_base_dir``, and
``core.config.user_config_path``; each of those imports
:func:`get_active_marker` here lazily to avoid import cycles.

Refusal matrix lives in :mod:`health_agent_infra.cli` (the entry
point owns the per-command policy); this module owns only the
state primitive.
"""

from health_agent_infra.core.demo.session import (
    DEMO_MARKER_FILENAME,
    DEMO_MARKER_SCHEMA_VERSION,
    DemoMarker,
    DemoMarkerError,
    cleanup_orphans,
    close_session,
    demo_marker_path,
    get_active_marker,
    is_demo_active,
    open_session,
    require_valid_marker_or_refuse,
)


__all__ = [
    "DEMO_MARKER_FILENAME",
    "DEMO_MARKER_SCHEMA_VERSION",
    "DemoMarker",
    "DemoMarkerError",
    "cleanup_orphans",
    "close_session",
    "demo_marker_path",
    "get_active_marker",
    "is_demo_active",
    "open_session",
    "require_valid_marker_or_refuse",
]
