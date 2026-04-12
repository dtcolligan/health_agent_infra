"""Compatibility-backed canonical module wrapper for `retrieval_request_metadata`."""

from health_model.retrieval_request_metadata import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.retrieval_request_metadata import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
