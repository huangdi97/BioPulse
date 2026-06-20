"""L1 cache module."""

import json
import logging
import os
import sqlite3
from typing import Optional

import httpx
import yaml

from shared.ai_gateway import INTERNAL_API_TIMEOUT

logger = logging.getLogger(__name__)

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHARMA_RULES_PATH = os.path.join(_PROJECT_ROOT, "cloud", "rules", "pharma_rules.json")
RESEARCH_RULES_PATH = os.path.join(_PROJECT_ROOT, "cloud", "rules", "research_rules.json")
PHARMA_RULES_YAML = os.path.join(_PROJECT_ROOT, "shared", "l1_rules", "pharma_rules.yaml")
RESEARCH_RULES_YAML = os.path.join(_PROJECT_ROOT, "shared", "l1_rules", "research_rules.yaml")


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


def load_l1_rules_from_yaml(mode: str) -> list[dict]:
    path_map = {"pharma": PHARMA_RULES_YAML, "research": RESEARCH_RULES_YAML}
    path = path_map.get(mode)
    if not path or not os.path.exists(path):
        logger.warning("L1 rules yaml not found for mode: %s", mode)
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("rules", [])


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


class L1RuleCache:
    CACHE_DIR = os.path.join(_PROJECT_ROOT, "data")
    CACHE_FILES = {
        "pharma": os.path.join(CACHE_DIR, "pharma_l1.db"),
        "research": os.path.join(CACHE_DIR, "research_l1.db"),
    }

    def __init__(self, cloud_api_base: str = "http://localhost:8000"):
        self.cloud_api_base = cloud_api_base

    def _get_db(self, mode: str) -> sqlite3.Connection:
        db_path = self.CACHE_FILES.get(mode)
        if not db_path:
            raise ValueError(f"Unknown mode: {mode}")
        return init_l1_cache(db_path)

    def load_rules(self, mode: str) -> list[dict]:
        rules = load_l1_rules_from_yaml(mode)
        if not rules:
            rules = load_l1_rules(mode)
        if not rules:
            logger.warning("load_rules: no rules found for mode: %s", mode)
            return []
        db = self._get_db(mode)
        try:
            cache_rules(db, rules, mode)
        finally:
            db.close()
        return rules

    def get_active_rules(self, mode: str) -> list[dict]:
        db = self._get_db(mode)
        try:
            return get_cached_rules(db, mode)
        finally:
            db.close()

    def sync_from_cloud(self) -> dict:
        results = {}
        for mode in ("pharma", "research"):
            try:
                resp = httpx.get(f"{self.cloud_api_base}/compliance/rules/{mode}", timeout=INTERNAL_API_TIMEOUT)
                if resp.status_code == 200:
                    data = resp.json()
                    rules = data.get("data", data.get("rules", data))
                    if rules:
                        db = self._get_db(mode)
                        try:
                            cache_rules(db, rules, mode)
                        finally:
                            db.close()
                        results[mode] = len(rules)
                        continue
                logger.warning("sync_from_cloud: cloud sync failed for %s, falling back to local", mode)
            except Exception as e:
                logger.warning("sync_from_cloud: error syncing %s: %s", mode, e)
            results[mode] = len(self.load_rules(mode))
        return results
