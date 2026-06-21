"""Agent 身份加载 — 从 agents/{agent_key}/identity.yaml 读取"""

import os
from typing import Any

import yaml

_identity_cache: dict[str, dict[str, Any]] = {}


def get_identity(agent_key: str) -> dict[str, Any]:
    """读取 agents/{agent_key}/identity.yaml 并缓存。"""
    if agent_key in _identity_cache:
        return _identity_cache[agent_key]
    path = os.path.join(os.path.dirname(__file__), "..", "agents", agent_key, "identity.yaml")
    path = os.path.normpath(os.path.abspath(path))
    if not os.path.isfile(path):
        raise FileNotFoundError(f"identity.yaml not found for agent '{agent_key}' at {path}")
    with open(path) as f:
        data: dict[str, Any] = yaml.safe_load(f) or {}
    _identity_cache[agent_key] = data
    return data


def clear_identity_cache() -> None:
    """清空身份缓存（测试用）。"""
    _identity_cache.clear()
