import json
import os
import threading

_cache = {}
_loaded = False
_lock = threading.Lock()

RULES_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "cloud", "rules")
VISIT_RULES_PATH = os.path.join(RULES_DIR, "pharma_rules.json")
RESEARCH_RULES_PATH = os.path.join(RULES_DIR, "research_rules.json")


def _is_hard_red_line(rule):
    return rule.get("level") == "L1" or rule.get("hard_red_line") is True


def _load_file(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [rule for rule in data if _is_hard_red_line(rule)]


def load_rules():
    global _loaded, _cache
    with _lock:
        try:
            _cache = {
                "visit": _load_file(VISIT_RULES_PATH),
                "research": _load_file(RESEARCH_RULES_PATH),
            }
            _loaded = True
        except Exception:
            _loaded = False


def get_rules(mode="visit"):
    if not _loaded:
        load_rules()
    return _cache.get(mode, [])


def is_available():
    return _loaded


def clear_cache():
    global _loaded, _cache
    with _lock:
        _cache = {}
        _loaded = False
