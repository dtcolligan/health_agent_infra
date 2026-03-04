"""
features.py — Extract structured features from portion descriptions.

Turns raw text like "a big bowl of rice" into a feature vector that a GBM
can learn from. Two feature groups:

1. Linguistic features (from the description text):
   - Description type (metric/count/container/vague)
   - Container word (bowl/plate/glass/cup/etc.)
   - Size modifier (small/medium/big/large/etc.)
   - Quantity number (the explicit number, if any)
   - Word count

2. Food features (from the reference database):
   - Density class (solid/granular/liquid/semisolid/leafy/countable)
   - Typical serving grams
   - Calorie density (kcal/100g)
   - Protein density
   - Category (protein/carb/fat/meal/etc.)

The model learns the INTERACTION between these groups:
  "big" + "bowl" + "granular" → 1.3× serving
  "big" + "bowl" + "leafy"   → 0.7× serving
"""

import re
import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Reference data (loaded once)
# ---------------------------------------------------------------------------
FOODS_CSV = Path(__file__).parent / "data" / "foods_reference.csv"

_FOOD_LOOKUP: dict | None = None


def _load_food_lookup() -> dict:
    """Load food reference as {food_name: {col: val, ...}}."""
    global _FOOD_LOOKUP
    if _FOOD_LOOKUP is not None:
        return _FOOD_LOOKUP
    _FOOD_LOOKUP = {}
    with open(FOODS_CSV) as f:
        for row in csv.DictReader(f):
            name = row["food_name"].lower().strip()
            _FOOD_LOOKUP[name] = {
                "density_class": row["density_class"],
                "typical_serving_g": float(row["typical_serving_g"]),
                "calories_per_100g": float(row["calories_per_100g"]),
                "protein_per_100g": float(row["protein_per_100g"]),
                "carbs_per_100g": float(row["carbs_per_100g"]),
                "fat_per_100g": float(row["fat_per_100g"]),
                "category": row["category"],
            }
    return _FOOD_LOOKUP


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONTAINER_WORDS = [
    "bowl", "plate", "glass", "cup", "mug", "pot", "portion",
    "piece", "handful", "dollop", "side", "bunch", "scoop",
    "tablespoon", "tbsp", "teaspoon", "tsp", "slice", "serving",
]

SIZE_MODIFIERS = {
    "tiny": -2, "small": -1, "little": -1,
    "medium": 0,
    "big": 1, "large": 1, "heaping": 1, "generous": 1, "huge": 2,
}

DESCRIPTION_TYPES = ["metric", "count", "container", "vague"]
DENSITY_CLASSES = ["solid", "granular", "liquid", "semisolid", "leafy", "countable"]
CATEGORIES = ["protein", "carb", "fruit", "vegetable", "dairy", "supplement",
              "fat", "meal", "snack", "drink", "condiment", "tinned"]


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------
def classify_description_type(desc: str) -> str:
    """Classify description into metric/count/container/vague."""
    d = desc.lower().strip()

    # Metric: starts with number + g/ml unit
    if re.match(r"^(about\s+)?\d+\s*(g|ml)\b", d):
        return "metric"

    # Count: starts with a number (but not g/ml)
    if re.match(r"^\d+\s", d) and not re.match(r"^\d+\s*(g|ml)\b", d):
        return "count"

    # Container: has a container word
    if any(w in d for w in CONTAINER_WORDS):
        return "container"

    return "vague"


def extract_container(desc: str) -> str:
    """Extract the container word, or 'none'."""
    d = desc.lower()
    for w in CONTAINER_WORDS:
        if w in d:
            return w
    return "none"


def extract_size_modifier(desc: str) -> tuple[str, int]:
    """Extract size modifier and its ordinal value. Returns (word, ordinal)."""
    d = desc.lower()
    for word, ordinal in SIZE_MODIFIERS.items():
        # Match whole word to avoid "small" matching inside "smallest"
        if re.search(rf"\b{word}\b", d):
            return word, ordinal
    return "none", 0


def extract_quantity_number(desc: str) -> float:
    """Extract the leading quantity number, or 0 if none."""
    d = desc.lower().strip()
    m = re.match(r"^(about\s+)?(\d+(?:\.\d+)?)", d)
    if m:
        return float(m.group(2))
    return 0.0


def extract_features(description: str, food_name: str) -> dict:
    """Extract full feature vector from a description + food name.

    Args:
        description: The raw portion description (e.g. "a big bowl of rice")
        food_name: The food item name (e.g. "white rice cooked")

    Returns:
        dict of feature_name → value (floats and strings for categoricals)
    """
    lookup = _load_food_lookup()
    food_info = lookup.get(food_name.lower().strip(), {})

    # --- Linguistic features ---
    desc_type = classify_description_type(description)
    container = extract_container(description)
    size_word, size_ordinal = extract_size_modifier(description)
    quantity = extract_quantity_number(description)
    word_count = len(description.split())

    # --- Food features ---
    density_class = food_info.get("density_class", "solid")
    typical_serving_g = food_info.get("typical_serving_g", 150.0)
    cal_density = food_info.get("calories_per_100g", 150.0)
    protein_density = food_info.get("protein_per_100g", 10.0)
    category = food_info.get("category", "meal")

    # --- Derived features ---
    # If metric, the quantity IS the gram estimate
    metric_grams = quantity if desc_type == "metric" else 0.0

    # If count, multiply by per-unit weight
    count_grams = 0.0
    if desc_type == "count" and quantity > 0:
        count_grams = typical_serving_g * quantity
        # Adjust for foods where serving_description has a count > 1
        # (e.g. sushi "8 pieces" = 200g, so 1 piece = 25g)
        # We approximate: if typical serving is large relative to a
        # single unit, scale down
        if density_class == "countable" and typical_serving_g > 100 and quantity <= 6:
            count_grams = quantity * (typical_serving_g / 3)  # rough heuristic

    # Is the calorie density "high" (>300), "medium" (100-300), or "low" (<100)?
    cal_density_bucket = "medium"
    if cal_density > 300:
        cal_density_bucket = "high"
    elif cal_density < 100:
        cal_density_bucket = "low"

    return {
        # Categorical (will be one-hot encoded or label-encoded)
        "desc_type": desc_type,
        "container": container,
        "size_modifier": size_word,
        "density_class": density_class,
        "category": category,
        "cal_density_bucket": cal_density_bucket,
        # Numeric
        "size_ordinal": size_ordinal,
        "quantity_number": quantity,
        "word_count": word_count,
        "typical_serving_g": typical_serving_g,
        "calories_per_100g": cal_density,
        "protein_per_100g": protein_density,
        "metric_grams": metric_grams,
        "count_grams": count_grams,
    }


# Fixed category mappings — ensures consistent encoding between training and
# inference. Without this, pandas .cat.codes assigns different integers
# depending on which values are present in the batch (a classic ML bug).
CATEGORY_MAPS = {
    "desc_type": {v: i for i, v in enumerate(DESCRIPTION_TYPES)},
    "container": {v: i for i, v in enumerate(["none"] + CONTAINER_WORDS)},
    "size_modifier": {v: i for i, v in enumerate(
        ["none", "tiny", "small", "little", "medium", "big", "large",
         "heaping", "generous", "huge"])},
    "density_class": {v: i for i, v in enumerate(DENSITY_CLASSES)},
    "category": {v: i for i, v in enumerate(CATEGORIES)},
    "cal_density_bucket": {v: i for i, v in enumerate(["low", "medium", "high"])},
}


def features_to_dataframe(descriptions: list[str], food_names: list[str]):
    """Extract features for a batch and return a DataFrame.

    Categorical columns are encoded to integers using fixed mappings,
    ensuring consistent encoding between training and single-example inference.
    """
    import pandas as pd

    rows = [extract_features(d, f) for d, f in zip(descriptions, food_names)]
    df = pd.DataFrame(rows)

    # Encode categoricals using fixed mappings (NOT pandas auto-codes)
    for col, mapping in CATEGORY_MAPS.items():
        df[col] = df[col].map(mapping).fillna(-1).astype(int)

    return df


# ---------------------------------------------------------------------------
# Quick test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        ("a big bowl of rice", "white rice cooked"),
        ("200g chicken breast", "chicken breast"),
        ("2 eggs", "eggs"),
        ("some pasta for dinner", "pasta cooked"),
        ("a small handful of almonds", "almonds"),
        ("loads of salad", "mixed salad"),
        ("a glass of milk", "milk whole"),
        ("a generous plate of spaghetti bolognese", "spaghetti bolognese"),
    ]

    print("Feature extraction examples:")
    print("=" * 80)
    for desc, food in test_cases:
        feats = extract_features(desc, food)
        print(f"\n  \"{desc}\" ({food})")
        print(f"    type={feats['desc_type']:10s}  container={feats['container']:10s}  "
              f"size={feats['size_modifier']:10s}  qty={feats['quantity_number']}")
        print(f"    density={feats['density_class']:10s}  typical={feats['typical_serving_g']:.0f}g  "
              f"cal_density={feats['calories_per_100g']:.0f}")
