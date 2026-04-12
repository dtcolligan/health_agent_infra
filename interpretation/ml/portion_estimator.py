"""
portion_estimator.py — Deterministic nutrition estimation pipeline.

Architecture:
    User description → ML model → predicted GRAMS (only ML step)
                                        ↓
    grams × per_100g (USDA/health DB) → deterministic calories + macros

The ML model's ONLY job is estimating portion size in grams.
All nutritional values (calories, protein, carbs, fat per 100g) come from
established health databases (USDA FoodData Central, McCance & Widdowson)
and are stored in foods_reference.csv.

This separation guarantees:
  1. Same food + same description → always same output (deterministic)
  2. Nutritional accuracy sourced from clinical databases, not ML guesses
  3. The model specialises on the hard problem (portion estimation)
     while the easy problem (per-100g lookup) is solved by a table

Usage:
    from ml.portion_estimator import PortionEstimator

    estimator = PortionEstimator()

    # Single item
    result = estimator.estimate("a big bowl of rice", "white rice cooked")
    # → {"grams": 285, "calories": 371, "protein_g": 7.7, ...}

    # Or just grams
    grams = estimator.estimate_grams("a big bowl of rice", "white rice cooked")
    # → 285.0
"""

from pathlib import Path
from ml.features import _load_food_lookup
from ml.model import GBMModel, RuleBaseline, HybridModel

MODEL_DIR = Path(__file__).parent / "models"


class PortionEstimator:
    """Deterministic nutrition estimator.

    Two-stage pipeline:
      1. ML model predicts grams from (description, food_name)
      2. Deterministic lookup: grams × per_100g → calories, protein, carbs, fat

    The model is loaded once and reused. All nutritional values come from
    foods_reference.csv (sourced from USDA FoodData Central).
    """

    def __init__(self, model_path: Path = MODEL_DIR / "gbm_portion.pkl"):
        self._lookup = _load_food_lookup()
        self._baseline = RuleBaseline()
        self._gbm = GBMModel()
        self._gbm.load(model_path)
        self._model = HybridModel(self._baseline, self._gbm)

    def estimate_grams(self, description: str, food_name: str) -> float:
        """Predict portion weight in grams from a natural language description.

        This is the ONLY step involving ML inference. The model is deterministic:
        same (description, food_name) → always same grams output.

        Args:
            description: User's portion description (e.g. "a big bowl of")
            food_name: Food item from reference DB (e.g. "white rice cooked")

        Returns:
            Estimated weight in grams (float, always ≥ 5).
        """
        grams = self._model.predict_one(description, food_name)
        return max(5.0, round(grams, 1))

    def estimate(self, description: str, food_name: str) -> dict:
        """Full estimation: grams + deterministic macronutrient calculation.

        Pipeline:
            1. ML model → grams
            2. grams × (per_100g from USDA reference) → calories, protein, carbs, fat

        Args:
            description: User's portion description
            food_name: Food item from reference DB

        Returns:
            dict with keys: food_name, description, grams, calories,
            protein_g, carbs_g, fat_g, source, confidence
        """
        grams = self.estimate_grams(description, food_name)
        return self._compute_macros(food_name, grams, description)

    def estimate_from_grams(self, food_name: str, grams: float) -> dict:
        """Deterministic macro calculation when grams are already known.

        Useful for metric descriptions ("200g chicken") where the user
        has already specified the exact weight — no ML needed.

        Args:
            food_name: Food item from reference DB
            grams: Known weight in grams

        Returns:
            dict with full nutritional breakdown
        """
        return self._compute_macros(food_name, grams, f"{int(grams)}g {food_name}")

    def _compute_macros(self, food_name: str, grams: float,
                        description: str) -> dict:
        """Deterministic: grams × per_100g values → calories + macros.

        This is pure arithmetic — no ML, no randomness, no estimation.
        The per_100g values come from foods_reference.csv (USDA FDC sourced).
        """
        info = self._lookup.get(food_name.lower().strip(), {})

        cal_per_100 = info.get("calories_per_100g", 150.0)
        pro_per_100 = info.get("protein_per_100g", 10.0)
        carb_per_100 = info.get("carbs_per_100g", 20.0)
        fat_per_100 = info.get("fat_per_100g", 5.0)

        factor = grams / 100.0

        return {
            "food_name": food_name,
            "description": description,
            "grams": round(grams),
            "calories": round(cal_per_100 * factor),
            "protein_g": round(pro_per_100 * factor, 1),
            "carbs_g": round(carb_per_100 * factor, 1),
            "fat_g": round(fat_per_100 * factor, 1),
            "source": "ml_portion_model",
            "confidence": self._confidence(food_name, description),
        }

    def _confidence(self, food_name: str, description: str) -> float:
        """Heuristic confidence score based on description type and food match.

        Higher confidence when:
        - Food is in the reference DB (known per-100g values)
        - Description is metric (user specified exact grams)
        - Description is count-based (clear multiplier)

        Lower confidence when:
        - Food is unknown (using fallback per-100g values)
        - Description is vague ("some chicken", "had rice")
        """
        from ml.features import classify_description_type

        # Food in reference DB?
        food_known = food_name.lower().strip() in self._lookup

        # Description type
        desc_type = classify_description_type(description)

        if not food_known:
            return 0.4  # Unknown food, using fallback values

        # Confidence by description type
        type_confidence = {
            "metric": 0.95,    # User said "200g" — we just look up the food
            "count": 0.85,     # "2 eggs" — clear multiplier
            "container": 0.70, # "a bowl of rice" — model estimates size
            "vague": 0.55,     # "some chicken" — highest uncertainty
        }

        return type_confidence.get(desc_type, 0.6)

    def is_known_food(self, food_name: str) -> bool:
        """Check if a food exists in the reference database."""
        return food_name.lower().strip() in self._lookup

    def get_reference_info(self, food_name: str) -> dict | None:
        """Get the USDA-sourced reference data for a food item.

        Returns per-100g values from foods_reference.csv, or None if unknown.
        """
        return self._lookup.get(food_name.lower().strip())

    def list_known_foods(self) -> list[str]:
        """List all foods in the reference database."""
        return sorted(self._lookup.keys())


# ---------------------------------------------------------------------------
# Quick test / demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    estimator = PortionEstimator()

    test_cases = [
        ("a big bowl of rice", "white rice cooked"),
        ("200g chicken breast", "chicken breast"),
        ("2 eggs", "eggs"),
        ("some pasta for dinner", "pasta cooked"),
        ("a small handful of almonds", "almonds"),
        ("a glass of milk", "milk whole"),
        ("loads of salad", "mixed salad"),
    ]

    print("Deterministic Portion Estimator")
    print("=" * 70)
    print("Pipeline: description → ML(grams) → grams × USDA per_100g → macros")
    print("=" * 70)

    for desc, food in test_cases:
        result = estimator.estimate(desc, food)
        print(f"\n  \"{desc}\" ({food})")
        print(f"    → {result['grams']}g  |  "
              f"{result['calories']} kcal  |  "
              f"P:{result['protein_g']}g  C:{result['carbs_g']}g  F:{result['fat_g']}g  |  "
              f"conf={result['confidence']:.2f}")

    # Verify determinism: same input → same output
    print("\n" + "=" * 70)
    print("DETERMINISM CHECK: 5 calls with identical input")
    print("=" * 70)
    results = []
    for _ in range(5):
        r = estimator.estimate("a big bowl of rice", "white rice cooked")
        results.append(r["grams"])
        print(f"  → {r['grams']}g  {r['calories']} kcal")

    assert len(set(results)) == 1, "NOT DETERMINISTIC — outputs differ!"
    print("  ✓ All identical — deterministic confirmed")
