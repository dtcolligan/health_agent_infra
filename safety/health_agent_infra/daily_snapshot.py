"""Compatibility-backed canonical module wrapper for `daily_snapshot`."""

from health_model.daily_snapshot import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.daily_snapshot import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
