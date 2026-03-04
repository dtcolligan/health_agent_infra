"""
Pull common foods from USDA FoodData Central (SR Legacy) and build
an expanded foods_reference.csv.

Uses the FDC search API to pull foods by category, extracts per-100g
macros (Energy, Protein, Carbs, Fat), then maps to our schema.

Usage:
    python -m ml.data.pull_usda
"""

import csv
import json
import os
import re
import time

import requests

API_KEY = "18uH0StIhViKNzwPqbMsChuFcyxPfnYHLYkYHBMp"
BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# Nutrient IDs for the search endpoint
NUTRIENT_IDS = {
    1008: "calories_per_100g",
    1003: "protein_per_100g",
    1005: "carbs_per_100g",
    1004: "fat_per_100g",
}

# ── Search queries to cover major food groups ──
# Each tuple: (search_term, our_category)
# We cast a wide net, then deduplicate + filter
SEARCH_QUERIES = [
    # Proteins
    ("chicken", "protein"),
    ("turkey", "protein"),
    ("beef", "protein"),
    ("pork", "protein"),
    ("lamb", "protein"),
    ("veal", "protein"),
    ("duck", "protein"),
    ("salmon", "protein"),
    ("tuna", "protein"),
    ("cod", "protein"),
    ("shrimp", "protein"),
    ("crab", "protein"),
    ("lobster", "protein"),
    ("sardine", "protein"),
    ("mackerel", "protein"),
    ("trout", "protein"),
    ("haddock", "protein"),
    ("tilapia", "protein"),
    ("egg", "protein"),
    ("tofu", "protein"),
    ("tempeh", "protein"),
    ("ham", "protein"),
    ("bacon", "protein"),
    ("sausage", "protein"),
    ("salami", "protein"),

    # Carbs
    ("rice", "carb"),
    ("pasta", "carb"),
    ("bread", "carb"),
    ("noodle", "carb"),
    ("oat", "carb"),
    ("cereal", "carb"),
    ("potato", "carb"),
    ("sweet potato", "carb"),
    ("quinoa", "carb"),
    ("couscous", "carb"),
    ("tortilla", "carb"),
    ("bagel", "carb"),
    ("muffin", "carb"),
    ("pancake", "carb"),
    ("waffle", "carb"),
    ("croissant", "carb"),
    ("barley", "carb"),
    ("corn", "carb"),

    # Fruits
    ("apple", "fruit"),
    ("banana", "fruit"),
    ("orange", "fruit"),
    ("strawberry", "fruit"),
    ("blueberry", "fruit"),
    ("grape", "fruit"),
    ("mango", "fruit"),
    ("pineapple", "fruit"),
    ("watermelon", "fruit"),
    ("peach", "fruit"),
    ("pear", "fruit"),
    ("cherry", "fruit"),
    ("kiwi", "fruit"),
    ("avocado", "fruit"),
    ("raspberry", "fruit"),
    ("melon", "fruit"),
    ("plum", "fruit"),
    ("fig", "fruit"),
    ("date", "fruit"),
    ("raisin", "fruit"),
    ("cranberry", "fruit"),
    ("lemon", "fruit"),
    ("lime", "fruit"),
    ("coconut", "fruit"),
    ("papaya", "fruit"),
    ("grapefruit", "fruit"),

    # Vegetables
    ("broccoli", "vegetable"),
    ("spinach", "vegetable"),
    ("carrot", "vegetable"),
    ("tomato", "vegetable"),
    ("onion", "vegetable"),
    ("pepper bell", "vegetable"),
    ("mushroom", "vegetable"),
    ("lettuce", "vegetable"),
    ("cabbage", "vegetable"),
    ("cauliflower", "vegetable"),
    ("cucumber", "vegetable"),
    ("celery", "vegetable"),
    ("asparagus", "vegetable"),
    ("kale", "vegetable"),
    ("peas", "vegetable"),
    ("green bean", "vegetable"),
    ("zucchini", "vegetable"),
    ("eggplant", "vegetable"),
    ("artichoke", "vegetable"),
    ("beetroot", "vegetable"),
    ("squash", "vegetable"),

    # Dairy
    ("milk", "dairy"),
    ("cheese", "dairy"),
    ("yogurt", "dairy"),
    ("butter", "dairy"),
    ("cream", "dairy"),
    ("ice cream", "dairy"),

    # Nuts & Seeds
    ("almond", "fat"),
    ("walnut", "fat"),
    ("peanut", "fat"),
    ("cashew", "fat"),
    ("pistachio", "fat"),
    ("pecan", "fat"),
    ("hazelnut", "fat"),
    ("sunflower seed", "fat"),
    ("pumpkin seed", "fat"),
    ("chia seed", "fat"),
    ("flaxseed", "fat"),

    # Fats & Oils
    ("olive oil", "fat"),
    ("coconut oil", "fat"),
    ("peanut butter", "fat"),

    # Legumes
    ("lentil", "protein"),
    ("chickpea", "protein"),
    ("black bean", "protein"),
    ("kidney bean", "protein"),

    # Drinks
    ("juice", "drink"),
    ("coffee", "drink"),
    ("tea", "drink"),
    ("beer", "drink"),
    ("wine", "drink"),
    ("soda", "drink"),
    ("cola", "drink"),

    # Snacks & Sweets
    ("cookie", "snack"),
    ("cake", "snack"),
    ("chocolate", "snack"),
    ("candy", "snack"),
    ("chip", "snack"),
    ("cracker", "snack"),
    ("popcorn", "snack"),
    ("pretzel", "snack"),
    ("doughnut", "snack"),
    ("brownie", "snack"),
    ("pie", "snack"),

    # Condiments
    ("ketchup", "condiment"),
    ("mustard", "condiment"),
    ("mayonnaise", "condiment"),
    ("soy sauce", "condiment"),
    ("honey", "condiment"),
    ("jam", "condiment"),
    ("syrup", "condiment"),
    ("vinegar", "condiment"),
    ("salsa", "condiment"),
    ("hummus", "condiment"),

    # Prepared / composite
    ("soup", "meal"),
    ("pizza", "meal"),
    ("burger", "meal"),
    ("burrito", "meal"),
    ("taco", "meal"),
    ("sandwich", "meal"),
    ("salad", "meal"),
    ("stew", "meal"),
    ("curry", "meal"),
    ("chili", "meal"),
    ("casserole", "meal"),
    ("sushi", "meal"),

    # Baking
    ("flour", "baking"),
    ("sugar", "baking"),
    ("baking", "baking"),
]


def search_usda(query: str, page_size: int = 50) -> list[dict]:
    """Search USDA FDC for foods matching query. Returns raw API results."""
    params = {
        "api_key": API_KEY,
        "query": query,
        "dataType": "SR Legacy",
        "pageSize": page_size,
    }
    try:
        resp = requests.get(BASE_URL, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json().get("foods", [])
    except Exception as e:
        print(f"  ERROR fetching '{query}': {e}")
        return []


def extract_macros(food: dict) -> dict | None:
    """Extract per-100g macros from a USDA food result.
    Returns None if any macro is missing."""
    macros = {}
    for nutrient in food.get("foodNutrients", []):
        nid = nutrient.get("nutrientId")
        if nid in NUTRIENT_IDS:
            macros[NUTRIENT_IDS[nid]] = round(nutrient.get("value", 0), 1)

    # Must have all 4 macros
    if len(macros) < 4:
        return None
    return macros


def clean_description(desc: str) -> str:
    """Clean USDA description into a simpler food name.

    USDA descriptions are verbose like:
    'Chicken, broilers or fryers, breast, meat only, cooked, roasted'

    We want: 'chicken breast roasted'
    """
    # Lowercase
    desc = desc.lower()

    # Remove parenthetical content
    desc = re.sub(r'\([^)]*\)', '', desc)

    # Remove common USDA qualifiers
    remove_phrases = [
        "broilers or fryers,", "mature, ",
        "meat and skin,", "meat only,",
        "separable lean and fat,", "separable lean only,",
        "trimmed to .*?,", "all grades,",
        "choice,", "select,", "prime,",
        "nfs", "ns as to",
        "commercially prepared", "prepared from recipe",
    ]
    for phrase in remove_phrases:
        desc = re.sub(phrase, '', desc, flags=re.IGNORECASE)

    # Split on commas, take meaningful parts
    parts = [p.strip() for p in desc.split(',') if p.strip()]

    # Rejoin with spaces, clean up
    result = ' '.join(parts)
    result = re.sub(r'\s+', ' ', result).strip()

    return result


# ── Density class heuristics ──
# Maps USDA food categories to likely density classes
CATEGORY_TO_DENSITY = {
    "Poultry Products": "solid",
    "Beef Products": "solid",
    "Pork Products": "solid",
    "Lamb, Veal, and Game Products": "solid",
    "Finfish and Shellfish Products": "solid",
    "Sausages and Luncheon Meats": "solid",
    "Dairy and Egg Products": "semisolid",
    "Legumes and Legume Products": "granular",
    "Vegetables and Vegetable Products": "solid",
    "Fruits and Fruit Juices": "solid",
    "Cereal Grains and Pasta": "granular",
    "Baked Products": "solid",
    "Nut and Seed Products": "countable",
    "Fats and Oils": "liquid",
    "Beverages": "liquid",
    "Snacks": "granular",
    "Spices and Herbs": "granular",
    "Soups, Sauces, and Gravies": "liquid",
    "Sweets": "solid",
    "Meals, Entrees, and Side Dishes": "semisolid",
    "Fast Foods": "solid",
    "Restaurant Foods": "solid",
    "Baby Foods": "semisolid",
    "Breakfast Cereals": "granular",
    "Cereal Grains and Pasta": "granular",
    "American Indian/Alaska Native Foods": "solid",
}


def infer_density_class(food: dict) -> str:
    """Infer density class from USDA food category."""
    cat = food.get("foodCategory", "")
    return CATEGORY_TO_DENSITY.get(cat, "solid")


def main():
    """Pull foods from USDA, deduplicate, and save as raw JSON for processing."""
    all_foods = {}  # fdcId -> food dict (dedup by ID)

    print(f"Pulling from USDA FDC ({len(SEARCH_QUERIES)} search queries)...")
    print()

    for i, (query, our_category) in enumerate(SEARCH_QUERIES):
        print(f"  [{i+1}/{len(SEARCH_QUERIES)}] Searching '{query}'...")
        results = search_usda(query, page_size=50)

        added = 0
        for food in results:
            fdc_id = food["fdcId"]
            if fdc_id in all_foods:
                continue

            macros = extract_macros(food)
            if macros is None:
                continue

            cleaned = clean_description(food["description"])

            all_foods[fdc_id] = {
                "fdc_id": fdc_id,
                "usda_description": food["description"],
                "cleaned_name": cleaned,
                "usda_category": food.get("foodCategory", ""),
                "our_category": our_category,
                "density_class": infer_density_class(food),
                **macros,
            }
            added += 1

        print(f"         → {added} new foods (total: {len(all_foods)})")

        # Rate limit: USDA allows 1000 requests/hour for free keys
        time.sleep(0.4)

    # Save raw pulled data
    output_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(output_dir, "usda_raw_pull.json")
    with open(raw_path, "w") as f:
        json.dump(list(all_foods.values()), f, indent=2)

    print(f"\nSaved {len(all_foods)} foods to {raw_path}")
    print("Next step: run ml.data.build_foods_db to filter and merge into foods_reference.csv")


if __name__ == "__main__":
    main()
