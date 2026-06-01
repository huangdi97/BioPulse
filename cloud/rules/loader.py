import json
import os
import functools

_RULES_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_json(filename: str) -> list[dict]:
    """Load a JSON file from the rules directory and return parsed content."""
    filepath = os.path.join(_RULES_DIR, filename)
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


@functools.lru_cache(maxsize=1)
def load_pharma_rules() -> list[dict]:
    """Load all pharma compliance rules from pharma_rules.json."""
    return _load_json("pharma_rules.json")


def get_pharma_l1_rules() -> list[dict]:
    """Return only L1 (hard red-line) rules from the full rule set."""
    return [r for r in load_pharma_rules() if r.get("level") == "L1"]


@functools.lru_cache(maxsize=1)
def load_research_rules() -> list[dict]:
    """Load all research compliance rules from research_rules.json."""
    return _load_json("research_rules.json")


def get_research_l1_rules() -> list[dict]:
    """Return only L1 rules from the research rule set."""
    return [r for r in load_research_rules() if r.get("level") == "L1"]


@functools.lru_cache(maxsize=1)
def load_pharma_l2_rules() -> list[dict]:
    """Load L2 pharma compliance rules from pharma_rules_l2.json."""
    return _load_json("pharma_rules_l2.json")


@functools.lru_cache(maxsize=1)
def load_research_l2_rules() -> list[dict]:
    """Load L2 research compliance rules from research_rules_l2.json."""
    return _load_json("research_rules_l2.json")
