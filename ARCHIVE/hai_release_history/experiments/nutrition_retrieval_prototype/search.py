"""
Retrieval heuristic for Phase 2.5 Track A food-retrieval gate.

This is a simple, transparent scorer. It is locked BEFORE running the 20
queries, to avoid tuning against them.

Design (per Dom's call in the planning exchange):
    - normalize case/punctuation
    - score exact canonical/head-noun match highest
    - otherwise use token overlap
    - add a small phrase/subsequence bonus
    - penalize unmatched query tokens lightly
    - no fuzzy distance; no hand-picked synonyms

Alias source: SR Legacy descriptions follow "HEAD_NOUN, modifier, modifier…".
We treat the pre-first-comma text as the canonical head-noun — that is the
entire alias layer, derived mechanically from USDA's own naming convention.
We do NOT hand-curate synonyms; that would bias the test toward the queries.

Normalization: lowercase, strip punctuation, drop stopwords and quantity
fillers, strip a single trailing 's' from tokens (bananas -> banana). The
trailing-'s' strip is basic English plural normalization, not query-tuning.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass


STOPWORDS = frozenset(
    {
        "a", "an", "the", "of", "some", "with", "and", "or", "to", "for",
        "in", "my", "i", "had", "ate", "at", "on", "from",
        "cup", "cups", "slice", "slices", "piece", "pieces", "bowl",
        "plate", "tablespoon", "tablespoons", "teaspoon", "teaspoons",
        "gram", "grams", "g", "oz", "ounce", "ounces", "ml", "liter", "liters",
        "one", "two", "three", "four", "five", "six", "couple", "few",
    }
)

_PUNCT_RE = re.compile(r"[^\w\s]")


def _strip_trailing_s(tok: str) -> str:
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def normalize(text: str) -> list[str]:
    lowered = text.lower()
    cleaned = _PUNCT_RE.sub(" ", lowered)
    tokens = []
    for raw in cleaned.split():
        if not raw or raw in STOPWORDS:
            continue
        tok = _strip_trailing_s(raw)
        if tok in STOPWORDS:
            continue
        tokens.append(tok)
    return tokens


@dataclass
class Food:
    fdc_id: str
    description: str
    category_id: str
    head_noun: str
    norm_desc: list[str]
    norm_head: list[str]


def load_foods(csv_path: str) -> list[Food]:
    foods: list[Food] = []
    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            desc = row["description"]
            head = desc.split(",", 1)[0].strip()
            foods.append(
                Food(
                    fdc_id=row["fdc_id"],
                    description=desc,
                    category_id=row.get("food_category_id", ""),
                    head_noun=head,
                    norm_desc=normalize(desc),
                    norm_head=normalize(head),
                )
            )
    return foods


def _contiguous(needle: list[str], haystack: list[str]) -> bool:
    n, h = len(needle), len(haystack)
    if n == 0 or n > h:
        return False
    for i in range(h - n + 1):
        if haystack[i : i + n] == needle:
            return True
    return False


def _subsequence(needle: list[str], haystack: list[str]) -> bool:
    it = iter(haystack)
    return all(tok in it for tok in needle)


def score_match(query_tokens: list[str], food: Food) -> float:
    if not query_tokens:
        return 0.0

    if query_tokens == food.norm_head:
        return 10.0 - 0.001 * len(food.norm_desc)

    desc_set = set(food.norm_desc)
    matched = [t for t in query_tokens if t in desc_set]
    unmatched = [t for t in query_tokens if t not in desc_set]
    overlap_ratio = len(matched) / len(query_tokens)

    score = overlap_ratio * 3.0

    head_set = set(food.norm_head)
    head_matched = [t for t in query_tokens if t in head_set]
    if head_matched:
        score += (len(head_matched) / len(query_tokens)) * 2.0

    if _contiguous(query_tokens, food.norm_desc):
        score += 1.0
    elif _subsequence(query_tokens, food.norm_desc):
        score += 0.3

    score -= 0.1 * len(unmatched)

    return score


def top_k(query: str, foods: list[Food], k: int = 5) -> list[tuple[float, Food]]:
    qtoks = normalize(query)
    scored = [(score_match(qtoks, f), f) for f in foods]
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:k]
