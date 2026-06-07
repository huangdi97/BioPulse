import json
import logging
import os
import sqlite3
from typing import Optional

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHARMA_RULES_PATH = os.path.join(_PROJECT_ROOT, "cloud", "rules", "pharma_rules.json")
RESEARCH_RULES_PATH = os.path.join(_PROJECT_ROOT, "cloud", "rules", "research_rules.json")


def load_l1_rules(entity_type: str) -> list[dict]:
    if entity_type == "pharma":
        path = PHARMA_RULES_PATH
    elif entity_type == "research":
        path = RESEARCH_RULES_PATH
    else:
        logger.warning("Unknown entity_type: %s", entity_type)
        return []
    if not os.path.exists(path):
        logger.warning("L1 rules file not found: %s", path)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def init_l1_cache(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute(
        "CREATE TABLE IF NOT EXISTS l1_cache ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "rule_code TEXT UNIQUE NOT NULL, "
        "category TEXT NOT NULL, "
        "rule_data TEXT NOT NULL, "
        "updated_at TEXT DEFAULT CURRENT_TIMESTAMP"
        ")"
    )
    conn.commit()
    return conn


def cache_rules(db: sqlite3.Connection, rules: list[dict], category: str) -> None:
    for rule in rules:
        db.execute(
            "INSERT OR REPLACE INTO l1_cache (rule_code, category, rule_data) VALUES (?, ?, ?)",
            (rule["code"], category, json.dumps(rule, ensure_ascii=False)),
        )
    db.commit()


def get_cached_rules(db: sqlite3.Connection, category: Optional[str] = None) -> list[dict]:
    if category:
        rows = db.execute("SELECT rule_data FROM l1_cache WHERE category = ?", (category,)).fetchall()
    else:
        rows = db.execute("SELECT rule_data FROM l1_cache").fetchall()
    return [json.loads(row["rule_data"]) for row in rows]


def sync_l1_rules(db: sqlite3.Connection, category: str) -> None:
    rules = load_l1_rules(category)
    if not rules:
        logger.warning("sync_l1_rules: no rules loaded for %s, skipping", category)
        return
    cache_rules(db, rules, category)
