"""Smoke test the live Intervals.icu wellness API against the user's account.

Reads credentials from env (HAI_INTERVALS_ATHLETE_ID, HAI_INTERVALS_API_KEY) or
keyring via CredentialStore.default(). Pulls the last 14 days of wellness
records and reports what actually flowed through — so we can distinguish
"connection works, data not yet populated" from "connection silently broken."

Prints only field names/values that the downstream adapter reads. Never prints
the api_key.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from health_agent_infra.core.pull.auth import CredentialStore
from health_agent_infra.core.pull.intervals_icu import build_default_client


WELLNESS_FIELDS = (
    "id",
    "restingHR",
    "hrv",
    "hrvSDNN",
    "sleepSecs",
    "sleepHours",
    "sleepScore",
    "atl",
    "ctl",
    "steps",
    "respiration",
    "spO2",
)


def main() -> int:
    store = CredentialStore.default()
    creds = store.load_intervals_icu()
    if not creds:
        print(
            "no intervals.icu credentials found. set env vars:\n"
            "  export HAI_INTERVALS_ATHLETE_ID=<your athlete id>\n"
            "  export HAI_INTERVALS_API_KEY=<your personal api key>"
        )
        return 2

    print(f"athlete_id: {creds.athlete_id}")
    print(f"api_key: <{len(creds.api_key)} chars, not shown>")

    client = build_default_client(creds)
    today = date.today()
    oldest = today - timedelta(days=14)
    print(f"fetching wellness {oldest} .. {today}")

    records = client.fetch_wellness_range(oldest=oldest, newest=today)
    print(f"got {len(records)} record(s)\n")

    if not records:
        print("empty response — garmin has not pushed any wellness to intervals.icu yet")
        print("likely causes: (1) backfill still in progress, (2) silently-broken grant")
        return 1

    populated_days = 0
    for rec in records:
        has_any = any(
            rec.get(f) not in (None, 0, 0.0)
            for f in ("restingHR", "hrv", "sleepSecs", "sleepHours", "sleepScore", "steps")
        )
        if has_any:
            populated_days += 1
        cells = []
        for f in WELLNESS_FIELDS:
            v = rec.get(f)
            cells.append(f"{f}={v}")
        print("  " + " ".join(cells))

    print()
    print(f"{populated_days}/{len(records)} days have at least one populated wellness field")
    return 0 if populated_days else 1


if __name__ == "__main__":
    sys.exit(main())
