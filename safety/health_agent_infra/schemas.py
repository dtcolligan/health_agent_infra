"""Compatibility-backed canonical module wrapper for `schemas`."""

from health_model.schemas import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.schemas import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
