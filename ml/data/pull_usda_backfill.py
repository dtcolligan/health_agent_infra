"""
Backfill USDA pull for categories that were missed due to DNS drop.
Appends to usda_raw_pull.json, then re-run build_foods_db.py.
"""

import json
import os
import time
import requests

API_KEY = "18uH0StIhViKNzwPqbMsChuFcyxPfnYHLYkYHBMp"
BASE_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"

# The categories that were missed (DNS dropped around query 90)
BACKFILL_QUERIES = [
    # Dairy
    ("cheese", "dairy"), ("yogurt", "dairy"), ("butter", "dairy"),
    ("cream", "dairy"), ("ice cream", "dairy"), ("milk", "dairy"),

    # Nuts & Seeds
    ("almond", "fat"), ("walnut", "fat"), ("peanut", "fat"),
    ("cashew", "fat"), ("pistachio", "fat"), ("pecan", "fat"),
    ("hazelnut", "fat"), ("sunflower seed", "fat"), ("pumpkin seed", "fat"),
    ("chia seed", "fat"), ("flaxseed", "fat"), ("sesame seed", "fat"),

    # Fats & Oils
    ("olive oil", "fat"), ("coconut oil", "fat"), ("peanut butter", "fat"),
    ("almond butter", "fat"),

    # Legumes
    ("lentil", "protein"), ("chickpea", "protein"), ("black bean", "protein"),
    ("kidney bean", "protein"), ("lima bean", "protein"), ("navy bean", "protein"),

    # Drinks
    ("juice", "drink"), ("coffee", "drink"), ("tea", "drink"),
    ("beer", "drink"), ("wine", "drink"), ("soda", "drink"),
    ("cola", "drink"), ("smoothie", "drink"), ("lemonade", "drink"),
    ("energy drink", "drink"), ("cocoa", "drink"),

    # Snacks & Sweets
    ("cookie", "snack"), ("cake", "snack"), ("chocolate", "snack"),
    ("candy", "snack"), ("chip", "snack"), ("cracker", "snack"),
    ("popcorn", "snack"), ("pretzel", "snack"), ("doughnut", "snack"),
    ("brownie", "snack"), ("pie", "snack"), ("muffin", "snack"),
    ("granola bar", "snack"), ("ice cream", "snack"),

    # Condiments & Sauces
    ("ketchup", "condiment"), ("mustard", "condiment"), ("mayonnaise", "condiment"),
    ("soy sauce", "condiment"), ("honey", "condiment"), ("jam", "condiment"),
    ("syrup", "condiment"), ("vinegar", "condiment"), ("salsa", "condiment"),
    ("hummus", "condiment"), ("guacamole", "condiment"), ("barbecue sauce", "condiment"),
    ("hot sauce", "condiment"), ("salad dressing", "condiment"), ("pesto", "condiment"),
    ("gravy", "condiment"), ("tomato sauce", "condiment"), ("curry paste", "condiment"),

    # Prepared / composite meals
    ("soup", "meal"), ("pizza", "meal"), ("burger", "meal"),
    ("burrito", "meal"), ("taco", "meal"), ("sandwich", "meal"),
    ("salad", "meal"), ("stew", "meal"), ("curry", "meal"),
    ("chili", "meal"), ("casserole", "meal"), ("sushi", "meal"),
    ("pasta dish", "meal"), ("fried rice", "meal"), ("lasagna", "meal"),
    ("enchilada", "meal"), ("quesadilla", "meal"), ("nachos", "meal"),
    ("hot dog", "meal"), ("french fries", "meal"), ("mashed potato", "meal"),
    ("coleslaw", "meal"), ("macaroni cheese", "meal"),

    # Baking
    ("flour", "baking"), ("sugar", "baking"), ("baking powder", "baking"),
    ("cocoa powder", "baking"), ("vanilla extract", "baking"),
    ("cornstarch", "baking"), ("yeast", "baking"),
]

NUTRIENT_IDS = {
    1008: "calories_per_100g",
    1003: "protein_per_100g",
    1005: "carbs_per_100g",
    1004: "fat_per_100g",
}

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
    "Breakfast Cereals": "granular",
}


def main():
    data_dir = os.path.dirname(os.path.abspath(__file__))
    raw_path = os.path.join(data_dir, "usda_raw_pull.json")

    # Load existing
    with open(raw_path) as f:
        existing = json.load(f)

    existing_ids = {f["fdc_id"] for f in existing}
    print(f"Existing: {len(existing)} foods ({len(existing_ids)} unique FDC IDs)")

    new_count = 0
    for i, (query, our_category) in enumerate(BACKFILL_QUERIES):
        print(f"  [{i+1}/{len(BACKFILL_QUERIES)}] Searching '{query}'...")

        try:
            resp = requests.get(BASE_URL, params={
                "api_key": API_KEY,
                "query": query,
                "dataType": "SR Legacy",
                "pageSize": 50,
            }, timeout=15)
            resp.raise_for_status()
            foods = resp.json().get("foods", [])
        except Exception as e:
            print(f"    ERROR: {e}")
            continue

        added = 0
        for food in foods:
            fdc_id = food["fdcId"]
            if fdc_id in existing_ids:
                continue

            macros = {}
            for nutrient in food.get("foodNutrients", []):
                nid = nutrient.get("nutrientId")
                if nid in NUTRIENT_IDS:
                    macros[NUTRIENT_IDS[nid]] = round(nutrient.get("value", 0), 1)

            if len(macros) < 4:
                continue

            usda_cat = food.get("foodCategory", "")
            existing.append({
                "fdc_id": fdc_id,
                "usda_description": food["description"],
                "cleaned_name": food["description"].lower(),  # will be cleaned by build_foods_db
                "usda_category": usda_cat,
                "our_category": our_category,
                "density_class": CATEGORY_TO_DENSITY.get(usda_cat, "solid"),
                **macros,
            })
            existing_ids.add(fdc_id)
            added += 1

        new_count += added
        print(f"    → {added} new (total: {len(existing)})")
        time.sleep(0.4)

    # Save
    with open(raw_path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\nBackfill complete: {new_count} new foods added, {len(existing)} total")


if __name__ == "__main__":
    main()
