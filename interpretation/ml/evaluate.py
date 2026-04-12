"""
evaluate.py — Detailed evaluation of portion estimation models.

Produces per-type metrics, error distributions, and feature importance
analysis. Results are printed and can be used in the evaluation notebook.

Usage: python -m ml.evaluate
"""

import csv
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.inspection import permutation_importance

from ml.features import (
    extract_features, features_to_dataframe, classify_description_type,
    _load_food_lookup
)
from ml.model import (
    RuleBaseline, GBMModel, HybridModel,
    load_training_data, _compute_metrics
)

MODEL_DIR = Path(__file__).parent / "models"


def detailed_evaluation():
    """Run full evaluation with per-type breakdowns and error analysis."""

    # Load data
    descriptions, food_names, targets = load_training_data()
    desc_trainval, desc_test, food_trainval, food_test, y_trainval, y_test = \
        train_test_split(descriptions, food_names, targets, test_size=0.15, random_state=42)

    # Load / retrain models
    baseline = RuleBaseline()
    gbm = GBMModel()
    gbm.train(desc_trainval, food_trainval, y_trainval)
    hybrid = HybridModel(baseline, gbm)

    # Predictions
    base_pred = baseline.predict(desc_test, food_test)
    gbm_pred = gbm.predict(desc_test, food_test)
    hybrid_pred = hybrid.predict(desc_test, food_test)

    # Get description types for test set
    test_types = [classify_description_type(d) for d in desc_test]
    test_foods = food_test

    # Build results DataFrame
    lookup = _load_food_lookup()
    results_df = pd.DataFrame({
        "description": desc_test,
        "food_name": food_test,
        "desc_type": test_types,
        "true_grams": y_test,
        "baseline_pred": base_pred,
        "gbm_pred": gbm_pred,
        "hybrid_pred": hybrid_pred,
    })

    # Add food properties
    results_df["density_class"] = results_df["food_name"].apply(
        lambda f: lookup.get(f.lower(), {}).get("density_class", "unknown"))
    results_df["category"] = results_df["food_name"].apply(
        lambda f: lookup.get(f.lower(), {}).get("category", "unknown"))
    results_df["cal_per_100g"] = results_df["food_name"].apply(
        lambda f: lookup.get(f.lower(), {}).get("calories_per_100g", 0))

    # Errors
    for model in ["baseline", "gbm", "hybrid"]:
        results_df[f"{model}_error"] = results_df[f"{model}_pred"] - results_df["true_grams"]
        results_df[f"{model}_abs_error"] = results_df[f"{model}_error"].abs()
        results_df[f"{model}_pct_error"] = (
            results_df[f"{model}_abs_error"] / results_df["true_grams"].clip(lower=1) * 100
        )
        results_df[f"{model}_cal_error"] = (
            results_df[f"{model}_abs_error"] * results_df["cal_per_100g"] / 100
        )

    # ── Permutation importance ──────────────────────────────────────
    print("Computing permutation importance...")
    X_test = features_to_dataframe(desc_test, food_test)
    perm_imp = permutation_importance(
        gbm.model, X_test, y_test,
        n_repeats=20, random_state=42, scoring="neg_mean_absolute_error"
    )
    importance_df = pd.DataFrame({
        "feature": gbm.feature_names,
        "importance_mean": perm_imp.importances_mean,
        "importance_std": perm_imp.importances_std,
    }).sort_values("importance_mean", ascending=False).reset_index(drop=True)

    # ── Worst predictions ───────────────────────────────────────────
    worst_hybrid = results_df.nlargest(15, "hybrid_abs_error")[
        ["description", "food_name", "true_grams", "hybrid_pred", "hybrid_abs_error", "desc_type"]
    ]

    # ── Summary print ───────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("DETAILED EVALUATION RESULTS")
    print("=" * 70)

    print("\n┌─────────────────────┬───────────┬───────────┬───────────┐")
    print("│ Metric              │ Baseline  │ GBM       │ Hybrid    │")
    print("├─────────────────────┼───────────┼───────────┼───────────┤")
    for model_name, pred in [("baseline", base_pred), ("gbm", gbm_pred), ("hybrid", hybrid_pred)]:
        pass
    bm = _compute_metrics(y_test, base_pred)
    gm = _compute_metrics(y_test, gbm_pred)
    hm = _compute_metrics(y_test, hybrid_pred)
    for label, key in [("MAE (g)", "mae_grams"), ("MAPE (%)", "mape"),
                       ("Acc@20%", "accuracy_at_20pct"), ("Acc@30%", "accuracy_at_30pct")]:
        print(f"│ {label:<19s} │ {bm[key]:>9.1f} │ {gm[key]:>9.1f} │ {hm[key]:>9.1f} │")
    print("└─────────────────────┴───────────┴───────────┴───────────┘")

    print(f"\nMean calorie error (hybrid): {results_df['hybrid_cal_error'].mean():.0f} kcal")
    print(f"Median calorie error (hybrid): {results_df['hybrid_cal_error'].median():.0f} kcal")

    print("\n── Feature importance (permutation) ──")
    for _, row in importance_df.head(10).iterrows():
        bar = "█" * int(abs(row["importance_mean"]) * 3)
        print(f"  {row['feature']:22s} {bar} {row['importance_mean']:.2f} ± {row['importance_std']:.2f}")

    print("\n── Worst hybrid predictions ──")
    for _, row in worst_hybrid.iterrows():
        print(f"  {row['description']:40s} → true={row['true_grams']:.0f}g  "
              f"pred={row['hybrid_pred']:.0f}g  err={row['hybrid_abs_error']:.0f}g  "
              f"({row['desc_type']})")

    return results_df, importance_df


if __name__ == "__main__":
    results_df, importance_df = detailed_evaluation()
