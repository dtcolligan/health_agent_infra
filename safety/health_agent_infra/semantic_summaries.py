"""Compatibility-backed canonical module wrapper for `semantic_summaries`."""

from health_model.semantic_summaries import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.semantic_summaries import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
