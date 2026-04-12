"""
Build the expanded foods_reference.csv from USDA raw pull + existing curated data.

Pipeline:
1. Load usda_raw_pull.json (raw API results)
2. Filter out: baby foods, raw industrial ingredients, obscure items
3. Clean descriptions into usable food names
4. Infer serving sizes and density classes
5. Deduplicate (prefer existing curated entries)
6. Merge with existing foods_reference.csv
7. Output expanded CSV

Usage:
    python -m ml.data.build_foods_db
"""

import csv
import json
import os
import re
from collections import defaultdict

DATA_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Filters: categories and patterns to exclude ──
EXCLUDE_USDA_CATEGORIES = {
    "Baby Foods",
    "American Indian/Alaska Native Foods",
}

EXCLUDE_PATTERNS = [
    r"infant formula",
    r"baby food",
    r"USDA commodity",
    r"school lunch",
    r"refuse:",
    r"separable lean and fat",
    r"separable lean only",
    r"trimmed to \d",
    r"bone-in",
    r"with bone",
    r"skin only",
    r"giblets",
    r"gizzard",
    r"liver",  # too niche for general use
    r"heart",
    r"kidney",
    r"tongue",
    r"brain",
    r"ear",
    r"sweetbreads",
    r"game meat",
    r"mechanically deboned",
    r"variety meats",
    r"suet",
    r"lard",
    r"shortening",
    r"imitation",
    r"powder, dry",  # milk powder etc - too granular
    r"concentrate, ",
    r"dehydrated",
    r"freeze-dried",
    r"formulated bar",
    r"meal replacement",
]

EXCLUDE_COMPILED = [re.compile(p, re.IGNORECASE) for p in EXCLUDE_PATTERNS]


def should_exclude(food: dict) -> bool:
    """Check if a food should be filtered out."""
    if food["usda_category"] in EXCLUDE_USDA_CATEGORIES:
        return True
    desc = food["usda_description"]
    for pattern in EXCLUDE_COMPILED:
        if pattern.search(desc):
            return True
    return False


def clean_name(usda_desc: str) -> str:
    """Clean verbose USDA description into a concise food name.

    Example:
        'Chicken, broilers or fryers, breast, meat only, cooked, roasted'
        → 'chicken breast roasted'
    """
    desc = usda_desc.lower()

    # Remove parenthetical content
    desc = re.sub(r'\([^)]*\)', '', desc)

    # Remove common USDA qualifiers
    remove_phrases = [
        r"broilers or fryers,?\s*",
        r"mature,?\s*",
        r"meat and skin,?\s*",
        r"meat only,?\s*",
        r"all grades,?\s*",
        r"choice,?\s*",
        r"select,?\s*",
        r"prime,?\s*",
        r"nfs\s*",
        r"ns as to\s*",
        r"commercially prepared,?\s*",
        r"prepared from recipe,?\s*",
        r"with added\s+\w+,?\s*",
        r"without added\s+\w+,?\s*",
        r"enriched,?\s*",
        r"unenriched,?\s*",
        r"fortified,?\s*",
    ]
    for phrase in remove_phrases:
        desc = re.sub(phrase, '', desc, flags=re.IGNORECASE)

    # Split on commas, take meaningful parts
    parts = [p.strip() for p in desc.split(',') if p.strip()]

    # Remove empty parts and rejoin
    result = ' '.join(parts)
    result = re.sub(r'\s+', ' ', result).strip()

    # Remove trailing "raw" for produce (we assume raw by default)
    result = re.sub(r'\s+raw$', '', result)

    return result


# ── Serving size heuristics ──
# Maps USDA food categories to (typical_serving_g, serving_description)
DEFAULT_SERVINGS = {
    "Poultry Products": (150, "1 portion"),
    "Beef Products": (150, "1 portion"),
    "Pork Products": (120, "1 portion"),
    "Lamb, Veal, and Game Products": (150, "1 portion"),
    "Finfish and Shellfish Products": (150, "1 fillet"),
    "Sausages and Luncheon Meats": (60, "2 slices"),
    "Dairy and Egg Products": (100, "1 serving"),
    "Legumes and Legume Products": (130, "1 serving"),
    "Vegetables and Vegetable Products": (100, "1 portion"),
    "Fruits and Fruit Juices": (120, "1 serving"),
    "Cereal Grains and Pasta": (200, "1 serving cooked"),
    "Breakfast Cereals": (40, "1 bowl dry"),
    "Baked Products": (50, "1 piece"),
    "Nut and Seed Products": (30, "1 handful"),
    "Fats and Oils": (14, "1 tablespoon"),
    "Beverages": (250, "1 glass"),
    "Snacks": (30, "1 serving"),
    "Spices and Herbs": (5, "1 teaspoon"),
    "Soups, Sauces, and Gravies": (200, "1 serving"),
    "Sweets": (40, "1 piece"),
    "Meals, Entrees, and Side Dishes": (300, "1 serving"),
    "Fast Foods": (200, "1 item"),
    "Restaurant Foods": (300, "1 serving"),
}

# Override serving sizes for specific food name patterns
SERVING_OVERRIDES = [
    (r"egg\b", 60, "1 egg", "countable"),
    (r"slice|bread|toast", 36, "1 slice", "countable"),
    (r"bagel", 105, "1 bagel", "countable"),
    (r"muffin", 115, "1 muffin", "countable"),
    (r"tortilla|wrap", 65, "1 wrap", "countable"),
    (r"cookie", 40, "1 cookie", "countable"),
    (r"doughnut|donut", 60, "1 doughnut", "countable"),
    (r"pancake", 77, "1 pancake", "countable"),
    (r"waffle", 75, "1 waffle", "countable"),
    (r"croissant", 60, "1 croissant", "countable"),
    (r"roll\b", 50, "1 roll", "countable"),
    (r"banana", 120, "1 banana", "countable"),
    (r"apple\b", 180, "1 apple", "countable"),
    (r"orange\b", 180, "1 orange", "countable"),
    (r"juice", 250, "1 glass", "liquid"),
    (r"milk\b", 250, "1 glass", "liquid"),
    (r"yogurt|yoghurt", 170, "1 pot", "semisolid"),
    (r"cheese\b", 30, "1 slice", "solid"),
    (r"butter\b", 10, "1 pat", "solid"),
    (r"cream\b", 30, "2 tablespoons", "liquid"),
    (r"oil\b", 14, "1 tablespoon", "liquid"),
    (r"soup\b", 300, "1 bowl", "liquid"),
    (r"sauce\b", 30, "2 tablespoons", "liquid"),
    (r"rice\b.*cooked", 200, "1 cup cooked", "granular"),
    (r"pasta\b.*cooked", 220, "1 plate", "granular"),
    (r"noodle", 200, "1 portion", "granular"),
    (r"cereal|granola|muesli|oat", 50, "1 serving", "granular"),
    (r"nut\b|almond|walnut|cashew|peanut|pecan", 30, "1 handful", "countable"),
    (r"seed\b", 15, "1 tablespoon", "granular"),
    (r"sausage\b", 68, "1 sausage", "countable"),
    (r"bacon\b", 30, "2 rashers", "countable"),
    (r"ham\b", 60, "2 slices", "countable"),
    (r"steak\b", 200, "1 steak", "solid"),
    (r"fillet\b", 170, "1 fillet", "solid"),
    (r"breast\b", 150, "1 breast", "solid"),
    (r"thigh\b", 120, "1 thigh", "solid"),
    (r"drumstick", 100, "1 drumstick", "solid"),
    (r"wing\b", 60, "2 wings", "countable"),
    (r"bean\b|lentil|chickpea", 130, "half a tin", "granular"),
    (r"berry|berries", 80, "1 handful", "granular"),
    (r"grape\b", 80, "1 handful", "granular"),
    (r"melon|watermelon", 200, "1 slice", "solid"),
    (r"potato\b", 200, "1 medium potato", "solid"),
    (r"pizza\b", 300, "2 slices", "countable"),
    (r"burger|hamburger", 200, "1 burger", "countable"),
    (r"sandwich", 200, "1 sandwich", "countable"),
    (r"taco", 120, "2 tacos", "countable"),
    (r"burrito", 350, "1 burrito", "countable"),
    (r"beer\b", 500, "1 pint", "liquid"),
    (r"wine\b", 175, "1 glass", "liquid"),
    (r"coffee\b", 250, "1 cup", "liquid"),
    (r"tea\b", 250, "1 cup", "liquid"),
    (r"cola|soda|soft drink", 330, "1 can", "liquid"),
    (r"ice cream", 100, "1 scoop", "semisolid"),
    (r"chocolate\b", 45, "1 bar", "countable"),
    (r"candy|sweet", 30, "1 piece", "countable"),
    (r"chip|crisp", 30, "1 bag", "granular"),
    (r"popcorn", 30, "1 bag", "granular"),
    (r"cracker", 30, "4 crackers", "countable"),
    (r"honey\b|jam\b|jelly\b|syrup\b", 20, "1 tablespoon", "liquid"),
    (r"ketchup|mustard|mayo", 15, "1 tablespoon", "liquid"),
    (r"salad\b", 150, "1 bowl", "leafy"),
    (r"spinach|lettuce|kale|arugula", 80, "1 handful", "leafy"),
]


def get_serving_info(cleaned_name: str, usda_category: str, density: str):
    """Get (serving_g, serving_desc, density_class) for a food."""
    name_lower = cleaned_name.lower()

    # Check pattern overrides first
    for pattern, grams, desc, density_override in SERVING_OVERRIDES:
        if re.search(pattern, name_lower):
            return grams, desc, density_override

    # Fall back to category defaults
    default = DEFAULT_SERVINGS.get(usda_category, (100, "1 serving"))
    return default[0], default[1], density


def load_existing_foods() -> dict:
    """Load existing foods_reference.csv as dict keyed by food_name."""
    path = os.path.join(DATA_DIR, "foods_reference.csv")
    existing = {}
    with open(path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing[row["food_name"].lower()] = row
    return existing


def deduplicate_names(foods: list[dict]) -> list[dict]:
    """When multiple USDA entries clean to the same name, keep the one
    with the highest search score (most relevant)."""
    by_name = defaultdict(list)
    for food in foods:
        by_name[food["cleaned_name"]].append(food)

    result = []
    for name, entries in by_name.items():
        # Keep entry with highest calorie value as tiebreaker (more likely the cooked/common variant)
        best = max(entries, key=lambda x: x.get("calories_per_100g", 0))
        result.append(best)

    return result


def main():
    # 1. Load raw USDA pull
    raw_path = os.path.join(DATA_DIR, "usda_raw_pull.json")
    with open(raw_path) as f:
        raw_foods = json.load(f)
    print(f"Loaded {len(raw_foods)} raw USDA foods")

    # 2. Filter
    filtered = [f for f in raw_foods if not should_exclude(f)]
    print(f"After filtering: {filtered.__len__()} foods")

    # 3. Clean names
    for food in filtered:
        food["cleaned_name"] = clean_name(food["usda_description"])

    # 4. Deduplicate by cleaned name
    deduped = deduplicate_names(filtered)
    print(f"After dedup: {len(deduped)} unique foods")

    # 5. Load existing curated foods
    existing = load_existing_foods()
    print(f"Existing curated foods: {len(existing)}")

    # 6. Build merged list — existing entries take priority
    fieldnames = [
        "food_name", "category", "calories_per_100g", "protein_per_100g",
        "carbs_per_100g", "fat_per_100g", "typical_serving_g",
        "serving_description", "density_class", "source", "usda_fdc_id"
    ]

    all_rows = []

    # Add all existing curated entries first
    existing_path = os.path.join(DATA_DIR, "foods_reference.csv")
    with open(existing_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            all_rows.append(row)

    existing_names = set(existing.keys())

    # Add new USDA entries that don't clash with existing
    added = 0
    for food in deduped:
        name = food["cleaned_name"].lower()
        if name in existing_names:
            continue  # existing curated entry takes priority

        serving_g, serving_desc, density = get_serving_info(
            food["cleaned_name"], food["usda_category"], food["density_class"]
        )

        all_rows.append({
            "food_name": food["cleaned_name"],
            "category": food["our_category"],
            "calories_per_100g": food["calories_per_100g"],
            "protein_per_100g": food["protein_per_100g"],
            "carbs_per_100g": food["carbs_per_100g"],
            "fat_per_100g": food["fat_per_100g"],
            "typical_serving_g": serving_g,
            "serving_description": serving_desc,
            "density_class": density,
            "source": "USDA FDC",
            "usda_fdc_id": food["fdc_id"],
        })
        existing_names.add(name)
        added += 1

    # 7. Write expanded CSV
    output_path = os.path.join(DATA_DIR, "foods_reference.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nExpanded foods_reference.csv: {len(all_rows)} total foods")
    print(f"  - {len(existing)} existing curated")
    print(f"  - {added} new from USDA")

    # Category breakdown
    from collections import Counter
    cats = Counter(r["category"] for r in all_rows)
    print("\nCategory breakdown:")
    for cat, count in cats.most_common():
        print(f"  {cat}: {count}")


if __name__ == "__main__":
    main()
