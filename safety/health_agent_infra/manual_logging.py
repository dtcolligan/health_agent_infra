"""Compatibility-backed canonical module wrapper for `manual_logging`."""

from health_model.manual_logging import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.manual_logging import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
