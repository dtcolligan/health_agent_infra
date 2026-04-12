"""
parser.py — Parse natural language health logs via Claude API.

Uses Claude's tool_use (function calling) to get structured JSON output.
Two tools:
  - log_health_entries: main tool, returns meals/exercises/subjective data
  - ask_clarification: used when ambiguity would swing estimate by >200 kcal

Nutrition pipeline (when ML model available):
  1. Claude parses message → identifies food items + portion descriptions
  2. For each food item in our reference DB:
     - ML model estimates grams from (quantity_desc, food_name)
     - Deterministic: grams × USDA per_100g → calories, protein, carbs, fat
  3. For unknown foods → fall back to Claude's original estimate
"""

import json
import logging
import anthropic
from .config import ANTHROPIC_API_KEY, CLAUDE_MODEL

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ML Portion Estimator — loaded lazily on first use
# ---------------------------------------------------------------------------
_estimator = None


def _get_estimator():
    """Lazy-load the ML portion estimator (avoids import cost if unused)."""
    global _estimator
    if _estimator is not None:
        return _estimator
    try:
        from ml.portion_estimator import PortionEstimator
        _estimator = PortionEstimator()
        log.info("ML portion estimator loaded — using deterministic USDA pipeline")
        return _estimator
    except Exception as e:
        log.warning(f"ML portion estimator not available ({e}), using Claude estimates")
        return None


def _match_food_name(item_name: str, estimator) -> str | None:
    """Try to match Claude's item_name to a food in the reference DB.

    Matching strategy (in order):
      1. Exact match (lowercased)
      2. Common suffix variants: "cooked", "raw", "tinned", etc.
      3. Substring match: "grilled chicken breast" contains "chicken breast"
      4. None if no match found → fall back to Claude's estimate

    Returns:
        Matched food name from reference DB, or None.
    """
    name = item_name.lower().strip()
    known = estimator.list_known_foods()

    # 1. Exact match
    if name in known:
        return name

    # 2. Try without common cooking qualifiers
    for suffix in (" cooked", " raw", " boiled", " fried", " grilled",
                   " baked", " roasted", " steamed", " tinned"):
        if name + suffix in known:
            return name + suffix
        if name.endswith(suffix.strip()) and name.replace(suffix.strip(), "").strip() in known:
            return name.replace(suffix.strip(), "").strip()

    # 3. Word-set match: same words in different order
    #    "whole milk" → "milk whole"
    name_words = set(name.split())
    for food in known:
        if set(food.split()) == name_words:
            return food

    # 4. Substring: is any known food a substring of the item name, or vice versa?
    #    "grilled chicken breast" → "chicken breast"
    best_match = None
    best_len = 0
    for food in known:
        if food in name or name in food:
            # Prefer longer matches (more specific)
            if len(food) > best_len:
                best_match = food
                best_len = len(food)

    return best_match


def _refine_with_ml(parsed_data: dict) -> dict:
    """Post-process Claude's output: replace calorie/macro estimates with
    deterministic values from the ML portion model + USDA reference.

    For each food item:
      - If item_name matches a food in reference DB → use ML grams + USDA macros
      - If no match → keep Claude's original estimate (it's still good!)

    This ensures:
      - Known foods: deterministic, USDA-sourced nutrition
      - Unknown foods: graceful fallback to Claude
      - Same input always → same output (deterministic)
    """
    estimator = _get_estimator()
    if estimator is None:
        return parsed_data  # ML not available, return as-is

    for meal in parsed_data.get("meals", []):
        for item in meal.get("items", []):
            ref_name = _match_food_name(item.get("item_name", ""), estimator)
            if ref_name is None:
                continue  # Unknown food — keep Claude's estimate

            # Build the description for the ML model
            desc = item.get("quantity_desc", item.get("item_name", ""))
            if not desc:
                desc = item.get("item_name", "")

            # ML model estimates grams, then deterministic USDA math
            result = estimator.estimate(desc, ref_name)

            # Override Claude's estimates with deterministic values
            item["calories"] = result["calories"]
            item["protein_g"] = result["protein_g"]
            item["carbs_g"] = result["carbs_g"]
            item["fat_g"] = result["fat_g"]
            item["confidence"] = result["confidence"]
            item["grams"] = result["grams"]
            item["source"] = "ml_usda"  # Flag: came from deterministic pipeline
            item["notes"] = (item.get("notes", "") +
                             f" [ML: {result['grams']}g {ref_name}, USDA sourced]").strip()

    return parsed_data

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are a health logging assistant. Parse the user's natural language description of their day into structured nutrition, exercise, and subjective wellness data.

RULES:
1. Be assumption-forward. Make reasonable estimates for portions, preparation methods, and ingredients. Note your assumptions in the "notes" field.
2. UK university student context: JCR = Junior Common Room (college cafeteria). Portions are typical UK servings unless stated otherwise.
3. Calorie estimates should be your best single-point estimate. Do NOT give ranges. Accept ±15-20% error — directional accuracy over precision.
4. Confidence scale:
   - 0.9+ = very standard item (apple, chicken breast, glass of milk)
   - 0.7-0.9 = reasonable estimate (restaurant meal, home-cooked with known ingredients)
   - 0.5-0.7 = significant portion/prep uncertainty (e.g. "big bowl of pasta")
   - <0.5 = highly uncertain, flag in notes
5. Only call ask_clarification if ambiguity would swing the TOTAL day's calories by >200 kcal. One question maximum. Otherwise, make your best estimate and note the assumption.
6. Subjective metrics: normalise to 1-10 scale. Map descriptors:
   - "amazing/incredible" = 9-10
   - "great/really good" = 8-9
   - "good/solid" = 7
   - "fine/ok/decent" = 5-6
   - "not great/meh" = 4
   - "poor/bad" = 2-3
   - "terrible/awful" = 1
7. Extract ALL subjective signals mentioned: energy, mood, sleep_quality, soreness, stress, motivation, focus, etc.
8. For exercise, estimate calories burned assuming an ~80kg male.
9. If the user mentions alcohol, log each drink as a snack item with its calories.
10. For strength/gym exercises, parse each set individually with reps and weight. If the user says "bench press 3x80kg", that's 3 sets of unspecified reps at 80kg. "Bench 3x8 at 80kg" = 3 sets of 8 reps at 80kg. Always use kg for weight. Common patterns: "3x8" = 3 sets of 8 reps, "5/5/5/3/3" = 5 sets with those rep counts, "3 sets at 80kg" = 3 sets at 80kg.
11. If the message doesn't contain any health data (e.g. "thanks", "ok", chit-chat), call log_health_entries with empty arrays for all fields. Do NOT respond with text only.
12. Always tag each exercise with its primary muscle_group. Use: chest (bench press, flies, push-ups, dips), back (rows, pull-ups, deadlifts, lat pulldown), shoulders (OHP, overhead press, lateral raises, face pulls), arms (curls, tricep extensions, hammer curls), legs (squats, lunges, leg press, calf raises, leg curls, leg extensions), core (planks, crunches, ab wheel, hanging leg raises), full_body (cleans, burpees, compound circuits). For cardio (running, cycling, swimming), use null.
13. Use the exercise subtype as the specific exercise name (e.g. "bench press", "barbell squat", "pull-ups") — not generic labels like "upper body". The exercise_type is the category (strength, cardio), subtype is the exercise name.

Always call log_health_entries with your parsed data. Only call ask_clarification INSTEAD of log_health_entries if you truly cannot make a reasonable estimate."""

TOOLS = [
    {
        "name": "log_health_entries",
        "description": "Log parsed nutrition, exercise, and subjective entries from the user's message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "meals": {
                    "type": "array",
                    "description": "Food entries grouped by meal",
                    "items": {
                        "type": "object",
                        "properties": {
                            "meal_type": {
                                "type": "string",
                                "enum": ["breakfast", "lunch", "dinner", "snack"],
                            },
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "item_name": {"type": "string"},
                                        "quantity_desc": {"type": "string"},
                                        "calories": {"type": "integer"},
                                        "protein_g": {"type": "number"},
                                        "carbs_g": {"type": "number"},
                                        "fat_g": {"type": "number"},
                                        "fiber_g": {"type": "number"},
                                        "confidence": {
                                            "type": "number",
                                            "description": "0.0-1.0 confidence in this estimate",
                                        },
                                        "notes": {
                                            "type": "string",
                                            "description": "Assumptions made about portion, preparation, etc.",
                                        },
                                    },
                                    "required": [
                                        "item_name",
                                        "calories",
                                        "protein_g",
                                        "carbs_g",
                                        "fat_g",
                                        "confidence",
                                    ],
                                },
                            },
                        },
                        "required": ["meal_type", "items"],
                    },
                },
                "exercises": {
                    "type": "array",
                    "description": "Exercise entries",
                    "items": {
                        "type": "object",
                        "properties": {
                            "exercise_type": {
                                "type": "string",
                                "description": "e.g. strength, running, cycling, walking, sport, swimming",
                            },
                            "subtype": {
                                "type": "string",
                                "description": "e.g. upper body, legs, 5k, HIIT",
                            },
                            "duration_min": {"type": "integer"},
                            "intensity": {
                                "type": "string",
                                "enum": ["light", "moderate", "hard", "max"],
                            },
                            "calories_est": {"type": "integer"},
                            "muscle_group": {
                                "type": "string",
                                "enum": ["chest", "back", "shoulders", "arms", "legs", "core", "full_body"],
                                "description": "Primary muscle group targeted. Null for cardio.",
                            },
                            "notes": {"type": "string"},
                            "confidence": {"type": "number"},
                            "sets": {
                                "type": "array",
                                "description": "Individual sets for strength/gym exercises. Include for weight training.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "reps": {"type": "integer"},
                                        "weight_kg": {"type": "number", "description": "Weight in kg"},
                                        "duration_sec": {"type": "integer", "description": "For timed sets like planks"},
                                        "is_pr": {"type": "boolean", "description": "True if this is a personal record"},
                                        "notes": {"type": "string"},
                                    },
                                    "required": ["reps"],
                                },
                            },
                        },
                        "required": ["exercise_type", "confidence"],
                    },
                },
                "subjective": {
                    "type": "array",
                    "description": "Subjective wellness metrics (energy, mood, sleep quality, etc.)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "e.g. energy, mood, sleep_quality, stress, soreness, motivation",
                            },
                            "value": {
                                "type": "number",
                                "description": "1-10 normalised score",
                            },
                            "label": {
                                "type": "string",
                                "description": "Human-readable label: 'solid', 'poor', 'great', etc.",
                            },
                            "notes": {"type": "string"},
                        },
                        "required": ["metric", "value", "label"],
                    },
                },
            },
            "required": ["meals", "exercises", "subjective"],
        },
    },
    {
        "name": "ask_clarification",
        "description": "Ask the user ONE follow-up question when ambiguity would swing a calorie estimate by more than 200 kcal. Use sparingly.",
        "input_schema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "A single, concise clarification question",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this clarification matters (internal note)",
                },
            },
            "required": ["question"],
        },
    },
]


def parse_health_message(user_text: str, date_for: str) -> dict:
    """
    Send user text to Claude, get structured health data back.

    Returns one of:
        {"type": "log", "data": {...}, "raw_response": str}
        {"type": "clarification", "question": str}
        {"type": "error", "message": str}
    """
    try:
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            tool_choice={"type": "any"},
            messages=[
                {"role": "user", "content": f"Date: {date_for}\n\n{user_text}"}
            ],
        )
    except anthropic.APIError as e:
        return {"type": "error", "message": f"Claude API error: {e}"}
    except Exception as e:
        return {"type": "error", "message": f"Unexpected error: {e}"}

    # Extract tool call from response
    raw_json = json.dumps(
        [{"type": b.type, **({"text": b.text} if b.type == "text" else {"name": b.name, "input": b.input})}
         for b in response.content],
        indent=2,
    )

    for block in response.content:
        if block.type == "tool_use":
            if block.name == "log_health_entries":
                # Post-process: replace Claude's macro estimates with
                # deterministic ML + USDA values for known foods
                refined = _refine_with_ml(block.input)
                return {"type": "log", "data": refined, "raw_response": raw_json}
            elif block.name == "ask_clarification":
                return {
                    "type": "clarification",
                    "question": block.input["question"],
                    "raw_response": raw_json,
                }

    # Claude responded with text only (no tool call)
    text_parts = [b.text for b in response.content if b.type == "text"]
    return {
        "type": "error",
        "message": "Could not parse into structured data. "
                   + " ".join(text_parts)[:200],
    }


if __name__ == "__main__":
    # Standalone test — requires ANTHROPIC_API_KEY in .env
    test_input = (
        "Had overnight oats with banana and honey for breakfast, "
        "chicken caesar wrap from the JCR for lunch, big bowl of bolognese "
        "with garlic bread for dinner. Snacked on an apple and some dark "
        "chocolate. Did a 45 min upper body session, felt strong. "
        "Energy was solid all day, slept badly last night though."
    )
    result = parse_health_message(test_input, "2026-03-02")
    print(json.dumps(result, indent=2))
