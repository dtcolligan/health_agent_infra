"""Compatibility-backed canonical module wrapper for `voice_note_intake`."""

from health_model.voice_note_intake import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.voice_note_intake import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
