"""Compatibility-backed canonical module wrapper for `agent_bundle_cli`."""

from health_model.agent_bundle_cli import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.agent_bundle_cli import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
