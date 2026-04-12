"""Compatibility wrapper for canonical health logger entrypoint now rooted in `merge_human_inputs`."""

from merge_human_inputs.health_logger.main import *  # noqa: F401,F403


if __name__ == "__main__":
    from merge_human_inputs.health_logger.main import setup

    if setup():
        from merge_human_inputs.health_logger.config import DB_PATH

        print(f"Database ready at {DB_PATH}")
        print("Backend initialized. Start the web server to use the app.")
