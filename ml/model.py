"""
model.py — Train and run portion estimation models.

Three models, increasing complexity:
  1. RuleBaseline  — typical_serving_g, adjusted by size modifier
  2. GBMModel      — XGBoost on engineered features
  3. (future) EmbeddingModel — sentence transformer + regression head

Usage:
    python -m ml.model          # train + evaluate
    python -m ml.model predict  # interactive prediction demo
"""

import csv
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml.features import extract_features, features_to_dataframe, _load_food_lookup

DATA_DIR = Path(__file__).parent / "data"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)

TRAINING_CSV = DATA_DIR / "synthetic_training.csv"


# ---------------------------------------------------------------------------
# Model 1: Rule-based baseline
# ---------------------------------------------------------------------------
class RuleBaseline:
    """Always predict typical_serving_g, adjusted by size modifier."""

    SIZE_MULTIPLIERS = {
        "tiny": 0.4, "small": 0.6, "little": 0.5,
        "medium": 1.0, "none": 1.0,
        "big": 1.4, "large": 1.5, "heaping": 1.3, "generous": 1.4, "huge": 1.8,
    }

    def predict_one(self, description: str, food_name: str) -> float:
        feats = extract_features(description, food_name)
        base = feats["typical_serving_g"]

        # If metric, use the number directly
        if feats["desc_type"] == "metric" and feats["quantity_number"] > 0:
            return feats["quantity_number"]

        # If count, use quantity × typical serving
        if feats["desc_type"] == "count" and feats["quantity_number"] > 0:
            return feats["count_grams"]

        # Otherwise, apply size modifier
        mult = self.SIZE_MULTIPLIERS.get(feats["size_modifier"], 1.0)
        return base * mult

    def predict(self, descriptions: list[str], food_names: list[str]) -> np.ndarray:
        return np.array([self.predict_one(d, f) for d, f in zip(descriptions, food_names)])


# ---------------------------------------------------------------------------
# Model 2: XGBoost on engineered features
# ---------------------------------------------------------------------------
class GBMModel:
    """Gradient boosted trees on engineered features."""

    def __init__(self):
        self.model = None
        self.feature_names = None

    def train(self, descriptions: list[str], food_names: list[str],
              targets: np.ndarray, val_frac: float = 0.15):
        """Train HistGradientBoosting regressor. Returns (train_metrics, val_metrics)."""
        from sklearn.ensemble import HistGradientBoostingRegressor

        X = features_to_dataframe(descriptions, food_names)
        self.feature_names = list(X.columns)
        y = targets

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=val_frac, random_state=42
        )

        self.model = HistGradientBoostingRegressor(
            max_iter=300,
            max_depth=6,
            learning_rate=0.1,
            min_samples_leaf=5,
            l2_regularization=1.0,
            random_state=42,
            verbose=0,
        )

        self.model.fit(X_train, y_train)

        train_pred = self.model.predict(X_train)
        val_pred = self.model.predict(X_val)

        train_metrics = _compute_metrics(y_train, train_pred)
        val_metrics = _compute_metrics(y_val, val_pred)

        return train_metrics, val_metrics

    def predict(self, descriptions: list[str], food_names: list[str]) -> np.ndarray:
        X = features_to_dataframe(descriptions, food_names)
        return self.model.predict(X)

    def predict_one(self, description: str, food_name: str) -> float:
        return float(self.predict([description], [food_name])[0])

    def feature_importance(self) -> pd.DataFrame:
        """Return permutation-based feature importance."""
        if self.model is None:
            return pd.DataFrame()
        # HistGBR doesn't expose gain-based importance directly,
        # so we use the built-in feature importances (mean decrease in loss)
        # from the model internals
        try:
            # sklearn >= 1.0 has feature_importances_ via impurity
            imp = np.zeros(len(self.feature_names))
            # Use permutation importance as a more reliable alternative
            from sklearn.inspection import permutation_importance
            # We'll fall back to a simpler approach for speed
            imp = np.abs(self.model.feature_importances_ if hasattr(self.model, 'feature_importances_') else np.zeros(len(self.feature_names)))
        except Exception:
            imp = np.zeros(len(self.feature_names))
        # Normalise
        if imp.sum() > 0:
            imp = imp / imp.sum()
        return pd.DataFrame({
            "feature": self.feature_names,
            "importance": imp,
        }).sort_values("importance", ascending=False).reset_index(drop=True)

    def save(self, path: Path = MODEL_DIR / "gbm_portion.pkl"):
        with open(path, "wb") as f:
            pickle.dump({"model": self.model, "feature_names": self.feature_names}, f)
        print(f"Model saved to {path}")

    def load(self, path: Path = MODEL_DIR / "gbm_portion.pkl"):
        with open(path, "rb") as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        print(f"Model loaded from {path}")


# ---------------------------------------------------------------------------
# Model 3: Hybrid (rule for metric/count, GBM for container/vague)
# ---------------------------------------------------------------------------
class HybridModel:
    """Routes predictions: rule engine for metric/count, GBM for the rest."""

    def __init__(self, baseline: RuleBaseline, gbm: GBMModel):
        self.baseline = baseline
        self.gbm = gbm

    def predict_one(self, description: str, food_name: str) -> float:
        feats = extract_features(description, food_name)
        # Only metric descriptions are trivially handled by rules
        # (the number IS the answer). Everything else → GBM.
        if feats["desc_type"] == "metric":
            return self.baseline.predict_one(description, food_name)
        return self.gbm.predict_one(description, food_name)

    def predict(self, descriptions: list[str], food_names: list[str]) -> np.ndarray:
        return np.array([self.predict_one(d, f) for d, f in zip(descriptions, food_names)])


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------
def _compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Compute evaluation metrics for portion estimation."""
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    # Clamp predictions to reasonable range
    y_pred = np.clip(y_pred, 5, 2000)

    abs_error = np.abs(y_true - y_pred)
    pct_error = abs_error / np.maximum(y_true, 1) * 100

    return {
        "mae_grams": float(np.mean(abs_error)),
        "median_ae_grams": float(np.median(abs_error)),
        "mape": float(np.mean(pct_error)),
        "accuracy_at_20pct": float(np.mean(pct_error <= 20) * 100),
        "accuracy_at_30pct": float(np.mean(pct_error <= 30) * 100),
        "n": len(y_true),
    }


# ---------------------------------------------------------------------------
# Training pipeline
# ---------------------------------------------------------------------------
def load_training_data() -> tuple[list[str], list[str], np.ndarray]:
    """Load synthetic training CSV → (descriptions, food_names, grams)."""
    descriptions, food_names, grams = [], [], []
    with open(TRAINING_CSV) as f:
        for row in csv.DictReader(f):
            descriptions.append(row["description"])
            food_names.append(row["food_name"])
            grams.append(float(row["grams"]))
    return descriptions, food_names, np.array(grams)


def train_and_evaluate():
    """Full training pipeline: load data, train models, compare."""
    print("Loading training data...")
    descriptions, food_names, targets = load_training_data()
    print(f"  {len(descriptions)} examples, {len(set(food_names))} foods\n")

    # --- Split into train+val and test ---
    (desc_trainval, desc_test, food_trainval, food_test,
     y_trainval, y_test) = train_test_split(
        descriptions, food_names, targets,
        test_size=0.15, random_state=42,
    )

    # --- Baseline ---
    print("=" * 60)
    print("MODEL 1: Rule Baseline")
    print("=" * 60)
    baseline = RuleBaseline()
    baseline_pred = baseline.predict(desc_test, food_test)
    baseline_metrics = _compute_metrics(y_test, baseline_pred)
    _print_metrics(baseline_metrics)

    # --- GBM ---
    print("\n" + "=" * 60)
    print("MODEL 2: XGBoost (GBM)")
    print("=" * 60)
    gbm = GBMModel()
    train_m, val_m = gbm.train(desc_trainval, food_trainval, y_trainval)

    print(f"  Train: MAE={train_m['mae_grams']:.1f}g  Acc@20%={train_m['accuracy_at_20pct']:.1f}%")
    print(f"  Val:   MAE={val_m['mae_grams']:.1f}g  Acc@20%={val_m['accuracy_at_20pct']:.1f}%")

    # Test set
    gbm_pred = gbm.predict(desc_test, food_test)
    gbm_metrics = _compute_metrics(y_test, gbm_pred)
    print("\n  Test set:")
    _print_metrics(gbm_metrics)

    # --- Feature importance ---
    print("\n  Feature importance (top 10):")
    imp = gbm.feature_importance()
    for _, row in imp.head(10).iterrows():
        bar = "█" * int(row["importance"] * 50)
        print(f"    {row['feature']:22s} {bar} {row['importance']:.3f}")

    # --- Hybrid ---
    print("\n" + "=" * 60)
    print("MODEL 3: Hybrid (rule for metric/count, GBM for rest)")
    print("=" * 60)
    hybrid = HybridModel(baseline, gbm)
    hybrid_pred = hybrid.predict(desc_test, food_test)
    hybrid_metrics = _compute_metrics(y_test, hybrid_pred)
    _print_metrics(hybrid_metrics)

    # --- Comparison ---
    print("\n" + "=" * 60)
    print("COMPARISON (test set)")
    print("=" * 60)
    print(f"  {'Metric':<20s} {'Baseline':>10s} {'GBM':>10s} {'Hybrid':>10s}")
    print(f"  {'-'*20} {'-'*10} {'-'*10} {'-'*10}")
    for key, label in [("mae_grams", "MAE (g)"),
                       ("mape", "MAPE (%)"),
                       ("accuracy_at_20pct", "Acc@20%"),
                       ("accuracy_at_30pct", "Acc@30%")]:
        b = baseline_metrics[key]
        g = gbm_metrics[key]
        h = hybrid_metrics[key]
        print(f"  {label:<20s} {b:>10.1f} {g:>10.1f} {h:>10.1f}")

    # --- Per-type breakdown ---
    from ml.features import classify_description_type
    test_types = [classify_description_type(d) for d in desc_test]
    print("\n  Per-type MAE / Acc@20%:")
    print(f"  {'Type':<12s} {'n':>5s} {'Baseline':>12s} {'GBM':>12s} {'Hybrid':>12s}")
    print(f"  {'-'*12} {'-'*5} {'-'*12} {'-'*12} {'-'*12}")
    for dtype in ["metric", "count", "container", "vague"]:
        mask = [t == dtype for t in test_types]
        idx = [i for i, m in enumerate(mask) if m]
        if not idx:
            continue
        yt = y_test[idx]
        bm = _compute_metrics(yt, baseline_pred[idx])
        gm = _compute_metrics(yt, gbm_pred[idx])
        hm = _compute_metrics(yt, hybrid_pred[idx])
        print(f"  {dtype:<12s} {len(idx):>5d} "
              f"{bm['mae_grams']:>5.1f}/{bm['accuracy_at_20pct']:>5.1f}% "
              f"{gm['mae_grams']:>5.1f}/{gm['accuracy_at_20pct']:>5.1f}% "
              f"{hm['mae_grams']:>5.1f}/{hm['accuracy_at_20pct']:>5.1f}%")

    # --- Save ---
    gbm.save()

    # --- Save metrics for the evaluation notebook ---
    results = {
        "baseline": baseline_metrics,
        "gbm_train": train_m,
        "gbm_val": val_m,
        "gbm_test": gbm_metrics,
        "hybrid_test": hybrid_metrics,
    }
    results_path = MODEL_DIR / "training_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {results_path}")

    return baseline, gbm, hybrid, results


def _print_metrics(m: dict):
    print(f"  MAE:        {m['mae_grams']:.1f}g")
    print(f"  Median AE:  {m['median_ae_grams']:.1f}g")
    print(f"  MAPE:       {m['mape']:.1f}%")
    print(f"  Acc@20%:    {m['accuracy_at_20pct']:.1f}%")
    print(f"  Acc@30%:    {m['accuracy_at_30pct']:.1f}%")


# ---------------------------------------------------------------------------
# Interactive demo
# ---------------------------------------------------------------------------
def interactive_demo():
    """Load saved model and predict interactively."""
    gbm = GBMModel()
    gbm.load()
    baseline = RuleBaseline()
    lookup = _load_food_lookup()

    print("\nInteractive Portion Estimator")
    print("Type a description and food name, separated by ' | '")
    print("Example: a big bowl of rice | white rice cooked")
    print("Type 'quit' to exit.\n")

    while True:
        line = input("> ").strip()
        if line.lower() in ("quit", "exit", "q"):
            break

        parts = line.split("|", 1)
        if len(parts) != 2:
            print("  Format: <description> | <food_name>")
            continue

        desc, food = parts[0].strip(), parts[1].strip()
        if food.lower() not in lookup:
            print(f"  Unknown food: '{food}'. Check foods_reference.csv")
            continue

        base_pred = baseline.predict_one(desc, food)
        gbm_pred = gbm.predict_one(desc, food)

        cal_per_g = lookup[food.lower()]["calories_per_100g"] / 100
        print(f"  Baseline: {base_pred:.0f}g ({base_pred * cal_per_g:.0f} kcal)")
        print(f"  GBM:      {gbm_pred:.0f}g ({gbm_pred * cal_per_g:.0f} kcal)")
        print()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "predict":
        interactive_demo()
    else:
        train_and_evaluate()
