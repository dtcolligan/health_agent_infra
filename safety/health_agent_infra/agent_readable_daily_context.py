"""Compatibility-backed canonical module wrapper for `agent_readable_daily_context`."""

from health_model.agent_readable_daily_context import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.agent_readable_daily_context import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
