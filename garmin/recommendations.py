"""Map readiness labels to user-facing training guidance."""

RECOMMENDATIONS = {
    "train_hard": "High readiness — hard training is reasonable if it matches the plan.",
    "train_normal": "Good readiness — normal training is appropriate today.",
    "train_easy": "Mixed readiness — keep training lighter or reduce intensity.",
    "recovery_only": "Low readiness — prioritise recovery, mobility, or an easy walk.",
    "rest": "Very low readiness — rest and recover today.",
}


def get_recommendation_text(key: str) -> str:
    return RECOMMENDATIONS.get(key, RECOMMENDATIONS["train_easy"])
