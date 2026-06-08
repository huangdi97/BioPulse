"""产品匹配评分工具，包含 Jaccard 相似度计算与分词。"""

import json
import re

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
    """Calculate the Jaccard similarity coefficient between two sets.

    Args:
        a: First set of tokens.
        b: Second set of tokens.

    Returns:
        Jaccard similarity score in [0.0, 1.0].
    """
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _tokenize(text: str) -> set[str]:
    """Tokenize text and filter stop words.

    Args:
        text: Raw input text.

    Returns:
        Set of filtered tokens.
    """
    tokens = re.findall(r"[a-zA-Z0-9\+]+", text.lower())
    return {t for t in tokens if t not in STOP_WORDS and len(t) > 1 and not t.isdigit()}


def _parse_json_list(value: str) -> list[str]:
    """Parse a JSON string into a list.

    Args:
        value: JSON string or list.

    Returns:
        Parsed list of strings.
    """
    try:
        return json.loads(value) if isinstance(value, str) else (value or [])
    except (json.JSONDecodeError, TypeError):
        return []
