"""Compatibility-backed canonical module wrapper for `shared_input_backbone`."""

from health_model.shared_input_backbone import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.shared_input_backbone import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
