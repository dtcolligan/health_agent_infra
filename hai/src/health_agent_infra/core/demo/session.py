"""Demo-session marker — fail-closed, multi-resolver isolation.

Marker schema ``demo_marker.v1``::

    {
      "schema_version": "demo_marker.v1",
      "marker_id":      "demo_<unix_ts>_<hex8>",
      "scratch_root":   "/tmp/hai_demo_<ts>/",
      "db_path":        "/tmp/hai_demo_<ts>/state.db",
      "base_dir_path":  "/tmp/hai_demo_<ts>/health_agent_root/",
      "config_path":    "/tmp/hai_demo_<ts>/config/thresholds.toml",
      "persona":        "p1_endurance_runner" | "blank" | null,
      "started_at":     "2026-04-28T13:00:00+00:00"
    }

Marker location resides **outside** the real ``~/.health_agent``
tree (so the byte-identical-tree invariant in the demo regression
gate holds without exclusions). Resolution order::

    HAI_DEMO_MARKER_PATH env (testing override)
    > $XDG_CACHE_HOME/hai/demo_session.json
    > ~/.cache/hai/demo_session.json

Failure modes (per Codex F-PLAN-03 fail-closed contract):

- File parse error                        → ``DemoMarkerError`` (refuse).
- Missing required field                  → ``DemoMarkerError`` (refuse).
- Schema-version mismatch                 → ``DemoMarkerError`` (refuse).
- Required-path field points at missing   → ``DemoMarkerError`` (refuse).

CLI entry-points must call
:func:`require_valid_marker_or_refuse` before performing any work
that touches persistence; if the marker exists but is invalid, the
helper raises ``DemoMarkerError`` and the CLI exits ``USER_INPUT``
without any further action. The only commands allowed past a bad
marker are ``hai demo end`` and ``hai demo cleanup``.
"""

from __future__ import annotations

import json
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


DEMO_MARKER_SCHEMA_VERSION = "demo_marker.v1"
DEMO_MARKER_FILENAME = "demo_session.json"

_HAI_DEMO_MARKER_PATH_ENV = "HAI_DEMO_MARKER_PATH"
_XDG_CACHE_HOME_ENV = "XDG_CACHE_HOME"

_REQUIRED_MARKER_FIELDS: tuple[str, ...] = (
    "schema_version",
    "marker_id",
    "scratch_root",
    "db_path",
    "base_dir_path",
    "config_path",
    "started_at",
)


class DemoMarkerError(Exception):
    """Raised when the demo marker is present but unusable.

    The CLI's fail-closed contract treats any of these as
    ``USER_INPUT`` and refuses to continue (except for the
    cleanup-only commands). The exception message is the user-
    facing diagnostic.
    """


@dataclass(frozen=True)
class DemoMarker:
    """Validated demo-session marker.

    Only :func:`get_active_marker` and :func:`open_session` should
    construct this; downstream consumers use the public attributes.
    """

    schema_version: str
    marker_id: str
    scratch_root: Path
    db_path: Path
    base_dir_path: Path
    config_path: Path
    persona: Optional[str]
    started_at: str
    # v0.1.12 W-Vb: optional record of fixture-application result
    # when --persona is set. None for blank/no-persona sessions.
    fixture_application: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "marker_id": self.marker_id,
            "scratch_root": str(self.scratch_root),
            "db_path": str(self.db_path),
            "base_dir_path": str(self.base_dir_path),
            "config_path": str(self.config_path),
            "persona": self.persona,
            "started_at": self.started_at,
            "fixture_application": self.fixture_application,
        }


def demo_marker_path() -> Path:
    """Resolve the marker file location.

    Test override (``HAI_DEMO_MARKER_PATH``) > XDG cache > home cache.
    """

    override = os.environ.get(_HAI_DEMO_MARKER_PATH_ENV)
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get(_XDG_CACHE_HOME_ENV)
    if xdg:
        return Path(xdg).expanduser() / "hai" / DEMO_MARKER_FILENAME
    return Path.home() / ".cache" / "hai" / DEMO_MARKER_FILENAME


def is_demo_active() -> bool:
    """Cheap presence check — does a marker file exist?

    Does NOT validate the marker; callers that need validation use
    :func:`require_valid_marker_or_refuse` (which fails closed) or
    :func:`get_active_marker` (which returns ``None`` on absence and
    raises on presence-but-invalid).
    """

    return demo_marker_path().exists()


def get_active_marker() -> Optional[DemoMarker]:
    """Return the validated marker, or ``None`` if no marker file exists.

    Raises :class:`DemoMarkerError` if a marker file exists but is
    unparseable, missing required fields, has a schema-version
    mismatch, or points at scratch paths that no longer exist.
    """

    path = demo_marker_path()
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        raise DemoMarkerError(
            f"demo marker at {path} is unreadable or unparseable: {exc}. "
            f"Run 'hai demo cleanup' to remove."
        ) from exc

    if not isinstance(data, dict):
        raise DemoMarkerError(
            f"demo marker at {path} is not a JSON object. "
            f"Run 'hai demo cleanup' to remove."
        )

    missing = [k for k in _REQUIRED_MARKER_FIELDS if k not in data]
    if missing:
        raise DemoMarkerError(
            f"demo marker at {path} is missing required fields: "
            f"{', '.join(sorted(missing))}. "
            f"Run 'hai demo cleanup' to remove."
        )

    if data["schema_version"] != DEMO_MARKER_SCHEMA_VERSION:
        raise DemoMarkerError(
            f"demo marker at {path} has unsupported schema_version "
            f"{data['schema_version']!r}; expected "
            f"{DEMO_MARKER_SCHEMA_VERSION!r}. "
            f"Run 'hai demo cleanup' to remove."
        )

    scratch_root = Path(data["scratch_root"])
    if not scratch_root.exists():
        raise DemoMarkerError(
            f"demo marker at {path} references a scratch root that "
            f"no longer exists ({scratch_root}). "
            f"Run 'hai demo cleanup' to remove."
        )

    return DemoMarker(
        schema_version=data["schema_version"],
        marker_id=data["marker_id"],
        scratch_root=scratch_root,
        db_path=Path(data["db_path"]),
        base_dir_path=Path(data["base_dir_path"]),
        config_path=Path(data["config_path"]),
        persona=data.get("persona"),
        started_at=data["started_at"],
        fixture_application=data.get("fixture_application"),
    )


def require_valid_marker_or_refuse() -> Optional[DemoMarker]:
    """Resolver-friendly variant: returns the marker if valid, ``None`` if absent.

    Raises :class:`DemoMarkerError` only when a marker file exists
    but cannot be honoured (corrupt / missing fields / schema
    mismatch / missing scratch). The CLI catches the exception and
    exits ``USER_INPUT``, allowing only ``hai demo end`` /
    ``hai demo cleanup`` past the gate.
    """

    return get_active_marker()


def _generate_marker_id() -> str:
    ts = int(datetime.now(timezone.utc).timestamp())
    return f"demo_{ts}_{secrets.token_hex(4)}"


def open_session(
    *,
    scratch_root: Optional[Path] = None,
    persona: Optional[str] = None,
) -> DemoMarker:
    """Create a new demo-session scratch root + marker.

    Refuses if a marker is already present (the CLI surfaces a clear
    "session already active" message). Creates the scratch root with
    sub-paths for the DB, base_dir, and config; writes the marker.

    Args:
        scratch_root: explicit scratch root (mainly for tests). When
            ``None``, defaults to ``/tmp/hai_demo_<marker_id>/``.
        persona: persona slug (W-Vb fixture loading consumes this).
            ``None`` = unpopulated/blank session at this stage.

    Returns:
        The validated :class:`DemoMarker` for the new session.

    Raises:
        DemoMarkerError: a marker already exists. The caller should
            surface "demo session already active — run 'hai demo end'
            first" to the user.
    """

    marker_path = demo_marker_path()
    if marker_path.exists():
        raise DemoMarkerError(
            f"demo session already active (marker at {marker_path}). "
            f"Run 'hai demo end' to close it, or 'hai demo cleanup' "
            f"if the marker is stale."
        )

    marker_id = _generate_marker_id()
    if scratch_root is None:
        # nosec B108 - /tmp is the documented demo-scratch root for
        # v0.1.11 W-Va. The path is namespaced by `marker_id` (which
        # contains crypto-random hex from secrets.token_hex), so two
        # demo sessions cannot collide. The scratch root never holds
        # production secrets — it's a per-session DB + JSONL slop.
        # Tests pin scratch_root to tmp_path explicitly; this default
        # only runs when the user invokes `hai demo start` directly.
        scratch_root = Path("/tmp") / f"hai_demo_{marker_id}"  # nosec B108

    scratch_root.mkdir(parents=True, exist_ok=False)

    db_path = scratch_root / "state.db"
    base_dir_path = scratch_root / "health_agent_root"
    config_path = scratch_root / "config" / "thresholds.toml"

    base_dir_path.mkdir(parents=True, exist_ok=True)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # v0.1.11 Codex F-IR-02 fix: initialise the scratch state.db so
    # the documented demo flow actually runs end-to-end. Without
    # this, every `hai intake *` call falls back to JSONL-only with
    # the "state DB projection skipped" warning, and `hai daily`
    # short-circuits because the DB doesn't exist. The original W-Va
    # implementation created the path string but never ran the
    # migrations.
    #
    # Lazy import to dodge a circular dependency: the resolver hooks
    # in core/state/store.py call back into this module.
    from health_agent_infra.core.state.store import (  # noqa: PLC0415
        initialize_database,
    )
    initialize_database(db_path)

    # v0.1.12 W-Vb partial-closure: when --persona is set, load the
    # packaged fixture and apply it. v0.1.12 ships skeleton-only
    # fixtures (apply_fixture returns a no-op result with the
    # "deferred_to: v0.1.13" marker); v0.1.13 W-Vb extends fixtures
    # to full persona-replay (proposals pre-populated, hai daily
    # reaches synthesis end-to-end).
    fixture_application: Optional[dict] = None
    if persona is not None:
        # Lazy import: avoid demo.fixtures becoming a hot-path
        # dependency for the no-persona blank-session flow.
        from health_agent_infra.core.demo.fixtures import (  # noqa: PLC0415
            DemoFixtureError,
            apply_fixture,
            load_fixture,
        )
        try:
            fixture_data = load_fixture(persona)
            fixture_application = apply_fixture(
                fixture_data,
                db_path=db_path,
                base_dir_path=base_dir_path,
            )
        except DemoFixtureError as exc:
            # Non-fatal at v0.1.12 scope: log and continue with blank
            # demo behaviour. v0.1.13 may upgrade this to fatal.
            fixture_application = {
                "applied": False,
                "scope": "error",
                "persona_slug": persona,
                "error": str(exc),
            }

    marker = DemoMarker(
        schema_version=DEMO_MARKER_SCHEMA_VERSION,
        marker_id=marker_id,
        scratch_root=scratch_root,
        db_path=db_path,
        base_dir_path=base_dir_path,
        config_path=config_path,
        persona=persona,
        started_at=datetime.now(timezone.utc).isoformat(),
        fixture_application=fixture_application,
    )

    marker_path.parent.mkdir(parents=True, exist_ok=True)
    with marker_path.open("w", encoding="utf-8") as fh:
        json.dump(marker.to_dict(), fh, indent=2)

    return marker


def close_session() -> Optional[DemoMarker]:
    """Remove the marker file. Returns the marker that was active, if any.

    Does NOT remove the scratch root or archive it — that's W-Vb's
    responsibility. W-Va just dissolves the marker so subsequent
    CLI invocations see "no demo active."
    """

    marker_path = demo_marker_path()
    if not marker_path.exists():
        return None

    try:
        marker = get_active_marker()
    except DemoMarkerError:
        # Marker exists but is invalid; remove anyway so cleanup
        # proceeds. Return None to signal "no clean marker."
        marker = None

    marker_path.unlink()
    return marker


def cleanup_orphans() -> list[str]:
    """Remove orphan marker files. Returns the marker_ids cleaned (or empty).

    "Orphan" = the marker exists but is invalid (corrupt, missing
    scratch root, schema mismatch). v0.1.11 W-Va scope: this only
    removes the marker file. Scratch-root cleanup + archive
    rotation is W-Vb scope.
    """

    marker_path = demo_marker_path()
    if not marker_path.exists():
        return []

    cleaned: list[str] = []
    try:
        marker = get_active_marker()
    except DemoMarkerError:
        # Invalid marker — read raw to extract marker_id if present, then nuke.
        try:
            with marker_path.open("r", encoding="utf-8") as fh:
                raw = json.load(fh)
            mid = raw.get("marker_id") if isinstance(raw, dict) else None
        except Exception:  # noqa: BLE001
            mid = None
        cleaned.append(mid or "<unparseable>")
        marker_path.unlink()
        return cleaned

    # Valid marker — only clean if scratch root is missing (truly orphan).
    if marker is not None and not marker.scratch_root.exists():
        cleaned.append(marker.marker_id)
        marker_path.unlink()

    return cleaned
