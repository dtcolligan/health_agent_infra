"""Compatibility-backed canonical module wrapper for `build_daily_context_artifact`."""

from health_model.build_daily_context_artifact import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.build_daily_context_artifact import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
