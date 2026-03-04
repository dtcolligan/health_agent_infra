"""
synthetic_gen.py — Generate synthetic training data for portion estimation.

Maps natural-language quantity descriptions → grams for each food item.
Produces (food_name, description, estimated_grams, calories, protein_g) rows
that can train a model to predict portion size from text.

The key idea: people describe portions in a few distinct patterns:
  1. Container-based:  "a bowl of rice", "a plate of pasta"
  2. Count-based:      "2 eggs", "3 slices of bread"
  3. Size-modified:    "a big plate of chicken", "a small bowl of soup"
  4. Vague:            "some rice", "chicken for lunch"
  5. Metric (precise): "200g chicken breast", "150ml milk"

Each pattern maps to a different gram distribution. The model learns:
  (pattern_type × food_density_class) → grams
"""

import csv
import random
import json
from pathlib import Path

FOODS_CSV = Path(__file__).parent / "foods_reference.csv"
OUTPUT_PATH = Path(__file__).parent / "synthetic_training.csv"

# ---------------------------------------------------------------------------
# Quantity templates: each returns (description_template, gram_multiplier)
# where gram_multiplier is relative to the food's typical_serving_g.
# ---------------------------------------------------------------------------

# Container-based descriptions — multiplier depends on density_class
CONTAINERS = {
    "solid":    [("a plate of",    1.3), ("a portion of",  1.0), ("a piece of",    0.8)],
    "granular": [("a bowl of",     1.0), ("a plate of",    1.3), ("a cup of",      0.7), ("a portion of", 1.0)],
    "liquid":   [("a glass of",    1.0), ("a cup of",      0.8), ("a mug of",      0.9), ("a bowl of",    1.2)],
    "semisolid":[("a bowl of",     1.0), ("a pot of",      0.8), ("a portion of",  1.0), ("a dollop of",  0.4)],
    "leafy":    [("a bowl of",     1.0), ("a handful of",  0.5), ("a plate of",    1.5), ("a side of",    0.8)],
    "countable":[("a portion of",  1.0)],  # countables use their own templates
}

# Size modifiers — applied on top of container descriptions
SIZE_MODIFIERS = [
    ("small",    0.6),
    ("",         1.0),   # no modifier = default
    ("",         1.0),   # weighted: no modifier is most common
    ("",         1.0),
    ("medium",   1.0),
    ("big",      1.4),
    ("large",    1.5),
    ("heaping",  1.3),
    ("generous", 1.4),
    ("tiny",     0.4),
]

# Vague descriptors — no container, just the food name with a vague quantifier
VAGUE_TEMPLATES = [
    ("some {food}",                1.0),
    ("{food}",                     1.0),
    ("{food} for {meal}",          1.0),
    ("had {food}",                 1.0),
    ("a bit of {food}",           0.6),
    ("loads of {food}",            1.8),
    ("lots of {food}",             1.6),
    ("a little {food}",            0.5),
    ("a little bit of {food}",     0.5),
]

# Metric (precise) — gram or ml amounts
METRIC_TEMPLATES = [
    ("{g}g {food}",         None),  # exact grams
    ("{g}g of {food}",      None),
    ("about {g}g {food}",   None),
    ("{g}ml {food}",        None),  # for liquids
]

# Meals for context
MEALS = ["breakfast", "lunch", "dinner", "a snack"]

# Noise: small random variation to make data more realistic
def noise(base: float, spread: float = 0.15) -> float:
    """Add realistic variation: ±spread around base."""
    return base * random.uniform(1 - spread, 1 + spread)


def load_foods() -> list[dict]:
    """Load the food reference database."""
    foods = []
    with open(FOODS_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["calories_per_100g"] = float(row["calories_per_100g"])
            row["protein_per_100g"] = float(row["protein_per_100g"])
            row["carbs_per_100g"] = float(row["carbs_per_100g"])
            row["fat_per_100g"] = float(row["fat_per_100g"])
            row["typical_serving_g"] = float(row["typical_serving_g"])
            foods.append(row)
    return foods


def generate_container_descriptions(food: dict, n: int = 3) -> list[dict]:
    """Generate container-based descriptions for a food item."""
    results = []
    density = food["density_class"]
    containers = CONTAINERS.get(density, CONTAINERS["solid"])
    base_g = food["typical_serving_g"]

    for _ in range(n):
        container, c_mult = random.choice(containers)
        size_label, s_mult = random.choice(SIZE_MODIFIERS)

        grams = noise(base_g * c_mult * s_mult)
        grams = max(5, round(grams))  # floor at 5g

        # Strip leading article from container before rebuilding
        bare_container = container
        for article in ("a ", "an "):
            if bare_container.startswith(article):
                bare_container = bare_container[len(article):]
                break

        if size_label:
            desc = f"a {size_label} {bare_container} {food['food_name']}"
        else:
            desc = f"a {bare_container} {food['food_name']}"

        results.append(_make_row(food, desc, grams))
    return results


def generate_count_descriptions(food: dict, n: int = 2) -> list[dict]:
    """Generate count-based descriptions: '2 eggs', '3 slices of bread'."""
    results = []
    if food["density_class"] != "countable":
        return results

    base_g = food["typical_serving_g"]
    serving_desc = food["serving_description"]

    # Extract the per-unit weight. If serving_description is "8 pieces"
    # and typical_serving_g is 200, then per_unit_g = 200/8 = 25g.
    # This avoids "3 pieces of sushi" → 600g (which would be 3 servings).
    serving_count = 1
    if serving_desc and serving_desc[0].isdigit():
        try:
            serving_count = int(serving_desc.split()[0])
        except (ValueError, IndexError):
            pass
    per_unit_g = base_g / max(serving_count, 1)

    for _ in range(n):
        count = random.choice([1, 1, 2, 2, 2, 3, 3, 4, 5, 6])
        grams = noise(per_unit_g * count, spread=0.1)
        grams = max(5, round(grams))

        # Build description from serving_description
        # e.g. "1 large egg" → "2 large eggs"
        # Special case: if serving_count > 1 and count == 1, don't use the
        # raw serving desc (e.g. "8 pieces") — say "1 piece of sushi" instead
        if count == 1 and serving_count > 1:
            parts = serving_desc.split(" ", 1)
            if len(parts) == 2:
                noun_part = parts[1]
                # Singularise if plural
                if noun_part.endswith("s") and not noun_part.endswith("ss"):
                    noun_part = noun_part[:-1]
                food_lower = food["food_name"].lower()
                if food_lower not in noun_part.lower():
                    desc = f"1 {noun_part} of {food['food_name']}"
                else:
                    desc = f"1 {noun_part}"
            else:
                desc = f"1 {food['food_name']}"
        elif count == 1:
            desc = serving_desc
        else:
            # Pluralise: "1 medium banana" → "3 medium bananas"
            # Split off the leading number
            parts = serving_desc.split(" ", 1)
            if len(parts) == 2:
                noun_part = parts[1]
                if not noun_part.endswith("s"):
                    noun_part += "s"
                # Check if the noun_part contains the food name — if not,
                # append it (handles "8 pieces" → "3 pieces of sushi")
                food_lower = food["food_name"].lower()
                if food_lower not in noun_part.lower():
                    desc = f"{count} {noun_part} of {food['food_name']}"
                else:
                    desc = f"{count} {noun_part}"
            else:
                desc = f"{count} {food['food_name']}"

        results.append(_make_row(food, desc, grams))
    return results


def generate_vague_descriptions(food: dict, n: int = 2) -> list[dict]:
    """Generate vague descriptions: 'some rice', 'had chicken for lunch'."""
    results = []
    base_g = food["typical_serving_g"]

    for _ in range(n):
        template, mult = random.choice(VAGUE_TEMPLATES)
        meal = random.choice(MEALS)
        grams = noise(base_g * mult, spread=0.25)  # higher variance for vague
        grams = max(5, round(grams))

        desc = template.format(food=food["food_name"], meal=meal)
        results.append(_make_row(food, desc, grams))
    return results


def generate_metric_descriptions(food: dict, n: int = 2) -> list[dict]:
    """Generate metric descriptions: '200g chicken breast'."""
    results = []
    base_g = food["typical_serving_g"]

    for _ in range(n):
        # Pick a realistic gram value (round to 10s or 25s)
        mult = random.choice([0.5, 0.75, 1.0, 1.0, 1.25, 1.5, 2.0])
        raw_g = base_g * mult
        # Round to nearest 10 or 25
        grams = round(raw_g / 25) * 25
        grams = max(25, grams)

        if food["density_class"] == "liquid":
            template = random.choice(["{g}ml {food}", "{g}ml of {food}", "about {g}ml {food}"])
        else:
            template = random.choice(["{g}g {food}", "{g}g of {food}", "about {g}g {food}"])

        desc = template.format(g=int(grams), food=food["food_name"])
        # For metric, the grams ARE the description — small noise only
        actual_g = round(noise(grams, spread=0.05))
        results.append(_make_row(food, desc, actual_g))
    return results


def _make_row(food: dict, description: str, grams: float) -> dict:
    """Compute calories and macros from grams, return a training row."""
    cals = round(food["calories_per_100g"] * grams / 100)
    protein = round(food["protein_per_100g"] * grams / 100, 1)
    carbs = round(food["carbs_per_100g"] * grams / 100, 1)
    fat = round(food["fat_per_100g"] * grams / 100, 1)

    return {
        "food_name": food["food_name"],
        "category": food["category"],
        "density_class": food["density_class"],
        "description": description,
        "grams": grams,
        "calories": cals,
        "protein_g": protein,
        "carbs_g": carbs,
        "fat_g": fat,
    }


# ---------------------------------------------------------------------------
# TODO: This is where YOUR portion-description heuristics go.
#
# The function below decides HOW MANY of each description type to generate
# per food, and what the weight distribution looks like.
#
# This matters because it shapes the training data distribution:
#   - More vague descriptions → model handles ambiguity better
#   - More metric descriptions → model is precise but may overfit to numbers
#   - The ratio reflects how people ACTUALLY log food
#
# Think about how YOU describe food in Telegram messages.
# What's the rough split between "200g chicken" vs "some chicken" vs
# "a plate of chicken"?
# ---------------------------------------------------------------------------

def get_description_weights(food: dict) -> dict:
    """Return how many descriptions of each type to generate per food.

    Args:
        food: dict with keys food_name, category, density_class, etc.

    Returns:
        dict with keys: container, count, vague, metric
        Values are ints (how many examples of each type to generate).

    Example return: {"container": 4, "count": 2, "vague": 3, "metric": 2}
    """
    density = food["density_class"]

    # Base weights — vague is highest because it's the most common real-world
    # pattern AND the hardest for the model. Metric is lowest because it's
    # trivially parseable (the number IS the answer).
    weights = {"container": 6, "count": 0, "vague": 8, "metric": 3}

    # Countable foods: "2 eggs" or "3 slices" is more natural than
    # "a bowl of eggs" — boost count, reduce container
    if density == "countable":
        weights["count"] = 7
        weights["container"] = 2

    # Liquids: limited container vocabulary (glass, cup, mug) so fewer
    # container examples needed, but ml amounts are common ("250ml milk")
    elif density == "liquid":
        weights["container"] = 4
        weights["metric"] = 5

    # Leafy: vague is extremely common ("had a salad", "some spinach")
    # and the gram range is huge, so give the model more practice
    elif density == "leafy":
        weights["vague"] = 10
        weights["container"] = 5

    # Semisolid (yoghurt, curry, hummus): container-based is dominant
    # ("a bowl of curry", "a pot of yoghurt")
    elif density == "semisolid":
        weights["container"] = 7

    return weights


def generate_all(seed: int = 42) -> list[dict]:
    """Generate the full synthetic training dataset."""
    random.seed(seed)
    foods = load_foods()
    all_rows = []

    for food in foods:
        weights = get_description_weights(food)
        all_rows.extend(generate_container_descriptions(food, n=weights["container"]))
        all_rows.extend(generate_count_descriptions(food, n=weights["count"]))
        all_rows.extend(generate_vague_descriptions(food, n=weights["vague"]))
        all_rows.extend(generate_metric_descriptions(food, n=weights["metric"]))

    random.shuffle(all_rows)
    return all_rows


def save_dataset(rows: list[dict], path: Path = OUTPUT_PATH):
    """Write training data to CSV."""
    if not rows:
        print("No rows to save!")
        return

    fieldnames = ["food_name", "category", "density_class", "description",
                  "grams", "calories", "protein_g", "carbs_g", "fat_g"]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved {len(rows)} training examples to {path}")


if __name__ == "__main__":
    rows = generate_all()
    save_dataset(rows)
    # Print some samples
    print("\n--- Sample descriptions ---")
    for r in rows[:20]:
        print(f"  {r['description']:40s} → {r['grams']:4d}g  ({r['calories']:4d} kcal)")
