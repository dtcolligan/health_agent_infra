"""Canonical compatibility entrypoint for the WRITEBACK lane implementation."""

from writeback.agent_memory_write_cli import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from writeback.agent_memory_write_cli import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
