"""
main.py — Initialize the health logger backend.

Run with: python -m bot.main
"""

import os

from .config import ANTHROPIC_API_KEY, DB_PATH
from .db import init_db


def setup():
    """Validate config and initialize the database."""
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set. Add it to your .env file.")
        print("Get a key at: https://console.anthropic.com/settings/keys")
        return False

    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    init_db()
    return True


if __name__ == "__main__":
    if setup():
        print(f"Database ready at {DB_PATH}")
        print("Backend initialized. Start the web server to use the app.")
