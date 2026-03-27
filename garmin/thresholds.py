"""Thresholds and weights for daily readiness scoring."""

READINESS_LABELS = {
    "green": {"min_score": 80, "label": "GREEN", "recommendation": "train_normal"},
    "amber": {"min_score": 60, "label": "AMBER", "recommendation": "train_easy"},
    "red": {"min_score": 0, "label": "RED", "recommendation": "recovery_only"},
}

SLEEP_THRESHOLDS = {
    "good_hours": 7.5,
    "ok_hours": 6.5,
    "poor_hours": 6.0,
    "debt_good": -0.25,
    "debt_bad": -1.5,
}

HRV_THRESHOLDS = {
    "near_weekly_delta": -3.0,
    "bad_delta": -10.0,
}

RESTING_HR_THRESHOLDS = {
    "mild_elevated": 3.0,
    "bad_elevated": 6.0,
}

STRESS_THRESHOLDS = {
    "moderate": 35.0,
    "high": 50.0,
}

RECOVERY_THRESHOLDS = {
    "low_recovery_hours": 12.0,
    "high_recovery_hours": 24.0,
    "moderate_load": 120.0,
    "high_load": 180.0,
}

TRAINING_READINESS_THRESHOLDS = {
    "good": 70.0,
    "poor": 40.0,
}
