import json
import logging
import os
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "tenant_configs")
CONFIG_DIR = os.path.normpath(CONFIG_DIR)

_DEFAULT_CONFIG_PATH = os.path.join(CONFIG_DIR, "default.json")


def _load_config(path: str) -> dict[str, Any]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("Tenant config not found: %s", path)
        return {}
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in tenant config %s: %s", path, e)
        return {}


def _merge_config(tenant_cfg: dict[str, Any], default_cfg: dict[str, Any]) -> dict[str, Any]:
    merged = {**default_cfg, **tenant_cfg}
    for key in ("enabled_agents", "model_selection", "feature_modules", "rate_limits"):
        if key in default_cfg and key in tenant_cfg:
            if isinstance(default_cfg[key], dict) and isinstance(tenant_cfg[key], dict):
                merged[key] = {**default_cfg[key], **tenant_cfg[key]}
            elif isinstance(default_cfg[key], list) and isinstance(tenant_cfg[key], list):
                merged[key] = tenant_cfg[key]
    return merged


@lru_cache(maxsize=128)
def get_tenant_config(tenant_id: str) -> dict[str, Any]:
    default_cfg = _load_config(_DEFAULT_CONFIG_PATH)
    if not tenant_id or tenant_id == "default":
        return default_cfg
    tenant_path = os.path.join(CONFIG_DIR, f"{tenant_id}.json")
    tenant_cfg = _load_config(tenant_path)
    if not tenant_cfg:
        logger.info("No tenant-specific config for '%s', falling back to default", tenant_id)
        return default_cfg
    return _merge_config(tenant_cfg, default_cfg)
