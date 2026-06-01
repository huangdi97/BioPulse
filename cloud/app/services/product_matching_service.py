import json
import re
from typing import Any

STOP_WORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "but",
    "if",
    "or",
    "because",
    "as",
    "until",
    "while",
    "of",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "then",
    "once",
    "here",
    "there",
    "when",
    "where",
    "why",
    "how",
    "all",
    "each",
    "every",
    "both",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "just",
    "also",
    "can",
    "will",
    "may",
    "would",
    "could",
    "should",
    "might",
    "method",
    "using",
    "based",
    "use",
    "used",
}


def _compute_jaccard_score(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-zA-Z0-9\+]+", text.lower())
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 1 and not t.isdigit()}


def _parse_json_list(value: str) -> list[str]:
    try:
        return json.loads(value) if isinstance(value, str) else (value or [])
    except (json.JSONDecodeError, TypeError):
        return []


def match_products_for_pi(
    pi_id: int, top_k: int = 3, research_db=None
) -> list[dict[str, Any]]:
    from cloud.app.research_database import get_research_db

    close_db = False
    if research_db is None:
        research_db = get_research_db()
        close_db = True
    try:
        product_count = research_db.execute(
            "SELECT COUNT(*) FROM research_products"
        ).fetchone()[0]
        if product_count == 0:
            return []
        row = research_db.execute(
            "SELECT * FROM research_pi_profiles WHERE pi_id = ?", (pi_id,)
        ).fetchone()
        if not row:
            return []
        pi = dict(row)
        research_areas = _parse_json_list(pi.get("research_areas", "[]"))
        area_tokens = set()
        for area in research_areas:
            area_tokens.update(_tokenize(area))
        if not area_tokens:
            return []
        product_rows = research_db.execute("SELECT * FROM research_products").fetchall()
        scored = []
        for p in product_rows:
            prod = dict(p)
            product_keywords = _parse_json_list(prod.get("keywords", "[]"))
            prod_name_tokens = _tokenize(prod.get("name", ""))
            all_prod_tokens = set(product_keywords) | prod_name_tokens
            score = _compute_jaccard_score(area_tokens, all_prod_tokens)
            if score > 0:
                scored.append(
                    {
                        "product_id": prod["product_id"],
                        "name": prod["name"],
                        "category": prod.get("category", ""),
                        "score": score,
                        "match_reason": f"Similarity: {score:.2f}",
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
    finally:
        if close_db:
            research_db.close()


def match_products_by_method(
    method_description: str, top_k: int = 3, research_db=None
) -> list[dict[str, Any]]:
    if not method_description.strip():
        return []
    from cloud.app.research_database import get_research_db

    close_db = False
    if research_db is None:
        research_db = get_research_db()
        close_db = True
    try:
        method_tokens = _tokenize(method_description)
        if not method_tokens:
            return []
        product_rows = research_db.execute("SELECT * FROM research_products").fetchall()
        scored = []
        for p in product_rows:
            prod = dict(p)
            product_keywords = _parse_json_list(prod.get("keywords", "[]"))
            prod_name_tokens = _tokenize(prod.get("name", ""))
            all_prod_tokens = set(product_keywords) | prod_name_tokens
            score = _compute_jaccard_score(method_tokens, all_prod_tokens)
            if score > 0:
                scored.append(
                    {
                        "product_id": prod["product_id"],
                        "name": prod["name"],
                        "category": prod.get("category", ""),
                        "score": score,
                        "match_reason": f"Similarity: {score:.2f}",
                    }
                )
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]
    finally:
        if close_db:
            research_db.close()
