"""Compatibility-backed canonical module wrapper for `day_nutrition_brief`."""

from health_model.day_nutrition_brief import *  # noqa: F401,F403


if __name__ == "__main__":
    try:
        from health_model.day_nutrition_brief import main as _main
    except ImportError:
        pass
    else:
        raise SystemExit(_main())
