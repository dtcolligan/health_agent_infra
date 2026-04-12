import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_PATH = os.path.join(REPO_ROOT, "data", "health_log.db")

CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Messages sent between midnight and this hour count as the previous day.
# Matches how Garmin/Whoop/Oura handle sleep day boundaries.
DAY_BOUNDARY_HOUR = 4


def get_user_date() -> str:
    """Return the 'logical' date for logging purposes.

    Between midnight and DAY_BOUNDARY_HOUR, we assume the user is still
    thinking about the previous calendar day (e.g. logging a late dinner
    at 1 AM should land on yesterday's totals).
    """
    now = datetime.now()
    if now.hour < DAY_BOUNDARY_HOUR:
        return (now - timedelta(days=1)).strftime("%Y-%m-%d")
    return now.strftime("%Y-%m-%d")
