"""Default-path resolution for the writeback / intake base directory.

Mirror of ``core/state/store.py:resolve_db_path`` for the SQLite DB
path. Centralising this lets every ``hai intake *``, ``hai propose``,
``hai review *``, ``hai daily``, and ``hai state reproject`` subcommand
treat ``--base-dir`` as optional and fall back to a stable default
without each handler reinventing the resolution.

Resolution order (matches ``resolve_db_path``):

    explicit CLI arg  >  ``$HAI_BASE_DIR`` env var  >  default

The default is ``~/.health_agent``, matching what the v0.1.5 codebase
used in practice for every test run and every real user session up to
and including 2026-04-25 — and what ``hai init`` already scaffolds.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


DEFAULT_BASE_DIR = Path.home() / ".health_agent"

_HAI_BASE_DIR_ENV = "HAI_BASE_DIR"


def resolve_base_dir(explicit: Optional[Path | str] = None) -> Path:
    """Return the writeback / intake base directory.

    Resolution order: explicit > ``$HAI_BASE_DIR`` env var > default.
    The returned path is expanded but not created — handlers that
    write into it should ``mkdir(parents=True, exist_ok=True)`` as
    they do today.
    """

    if explicit is not None:
        return Path(explicit).expanduser()
    env_value = os.environ.get(_HAI_BASE_DIR_ENV)
    if env_value:
        return Path(env_value).expanduser()
    return DEFAULT_BASE_DIR


__all__ = ["DEFAULT_BASE_DIR", "resolve_base_dir"]
