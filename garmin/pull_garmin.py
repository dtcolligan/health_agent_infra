import os
import json
import getpass
import inspect
from datetime import date, timedelta

import pandas as pd
from garminconnect import Garmin

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "garmin")
RAW_DIR = os.path.join(DATA_DIR, "raw_daily_json")
LOG_PATH = os.path.join(DATA_DIR, "pull_log.jsonl")

DAYS_BACK = 60  # set to ~60 since you got the watch recently

def daterange(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)

def dump_json(path, obj):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def append_log(record: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

def call_auto(api: Garmin, method_name: str, ds: str):
    """
    Call a Garmin method by introspecting its signature.
    Supports common patterns:
      - (date) -> e.g. get_sleep_day(ds)
      - (startdate, enddate) -> e.g. get_body_battery(ds, ds)
      - () -> rarely
    Returns (data, error_str_or_None).
    """
    fn = getattr(api, method_name, None)
    if fn is None:
        return None, f"missing_method:{method_name}"

    try:
        sig = inspect.signature(fn)
        params = list(sig.parameters.values())

        # For bound methods, signature will typically show only the real args (no self)
        # Common cases:
        # 0 params: fn()
        # 1 param: fn(date)
        # 2 params: fn(startdate, enddate)
        n = len(params)

        if n == 0:
            return fn(), None
        elif n == 1:
            return fn(ds), None
        elif n == 2:
            return fn(ds, ds), None
        else:
            # Too many args — we won't guess
            return None, f"unsupported_signature:{method_name}:{sig}"
    except Exception as e:
        return None, f"exception:{method_name}:{type(e).__name__}:{e}"

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(RAW_DIR, exist_ok=True)

    email = input("Garmin email: ").strip()
    password = getpass.getpass("Garmin password: ")

    api = Garmin(email, password)
    api.login()

    today = date.today()
    start = today - timedelta(days=DAYS_BACK)

    # 1) Activities
    activities = api.get_activities_by_date(
        startdate=(today - timedelta(days=90)).isoformat(),
        enddate=today.isoformat(),
    )
    pd.json_normalize(activities).to_csv(os.path.join(DATA_DIR, "activities.csv"), index=False)
    print("Activities saved.")

    # 2) Daily pulls — methods to TRY (only those that exist will actually run)
    # We include multiple aliases because garminconnect versions differ.
    metric_methods = {
        "daily_summary": ["get_daily_summary"],
        "sleep": ["get_sleep_day", "get_sleep_data"],
        "stress": ["get_stress_data", "get_stress_day", "get_daily_stress"],
        "body_battery": ["get_body_battery", "get_body_battery_day"],
        "rhr": ["get_rhr_day", "get_resting_heart_rate", "get_rhr"],
        "heart_rate": ["get_heart_rates", "get_heart_rate"],
        "spo2": ["get_spo2_data", "get_daily_spo2"],
        "respiration": ["get_respiration_data", "get_daily_respiration"],
        "hrv": ["get_hrv_data", "get_hrv"],
        "intensity_minutes": ["get_intensity_minutes", "get_daily_intensity_minutes"],
        "training_readiness": ["get_training_readiness"],
        "training_status": ["get_training_status"],
        "max_metrics": ["get_max_metrics"],
        "endurance_score": ["get_endurance_score"],
        "race_predictions": ["get_race_predictions", "get_race_predictor"],
    }

    daily_rows = []
    long_rows = []

    # Clear previous log for a clean run (optional)
    # If you prefer to keep history, comment these 2 lines out.
    if os.path.exists(LOG_PATH):
        os.remove(LOG_PATH)

    for d in daterange(start, today):
        ds = d.isoformat()
        print(f"Pulling daily metrics: {ds}")

        raw_day = {"date": ds, "metrics": {}, "errors": {}}
        daily_blob = {"date": ds}

        for metric_name, candidates in metric_methods.items():
            got = False
            for m in candidates:
                data, err = call_auto(api, m, ds)
                if err is None:
                    # success (even if empty list) — record it
                    raw_day["metrics"][metric_name] = {"method": m, "data": data}
                    daily_blob[metric_name] = data
                    long_rows.append({"date": ds, "metric": metric_name, "method": m, "data": data})
                    got = True
                    break
                else:
                    raw_day["errors"].setdefault(metric_name, []).append(err)

            if not got:
                # record that none worked
                daily_blob[metric_name] = None

        dump_json(os.path.join(RAW_DIR, f"{ds}.json"), raw_day)
        append_log({"date": ds, "ok_metrics": list(raw_day["metrics"].keys()), "error_counts": {k: len(v) for k, v in raw_day["errors"].items()}})

        daily_rows.append(daily_blob)

    # Save daily/long CSVs
    pd.json_normalize(daily_rows).to_csv(os.path.join(DATA_DIR, "daily_metrics_daily.csv"), index=False)
    pd.json_normalize(long_rows).to_csv(os.path.join(DATA_DIR, "daily_metrics_long.csv"), index=False)

    print(f"Wrote {len(long_rows):,} rows -> data/daily_metrics_long.csv")
    print(f"Wrote {len(daily_rows):,} rows -> data/daily_metrics_daily.csv")
    print(f"Log written -> {LOG_PATH}")
    print("Done.")

if __name__ == "__main__":
    main()
