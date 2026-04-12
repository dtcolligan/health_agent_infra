"""Compatibility wrapper for the canonical `health_model.agent_contract_cli` module."""

from health_model.agent_contract_cli import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.agent_contract_cli import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
