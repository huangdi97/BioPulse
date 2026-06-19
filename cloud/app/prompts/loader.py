"""Prompt 管理器 — 按名称+版本加载系统提示。"""

import json
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def _load_manifest() -> dict:
    with open(_PROMPTS_DIR / "manifest.json", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(name: str, version: str = "latest") -> str:
    """按名称和版本加载 prompt。version='latest' 加载最高版本。"""
    manifest = _load_manifest()
    if version == "latest":
        candidates = {k: v for k, v in manifest.items() if k.startswith(f"{name}/")}
        if not candidates:
            raise KeyError(f"Prompt '{name}' not found")
        key = max(candidates.keys(), key=lambda k: k.split("/v")[-1])
    else:
        key = f"{name}/{version}"
        if key not in manifest:
            raise KeyError(f"Prompt '{key}' not found")
    entry = manifest[key]
    path = _PROMPTS_DIR / entry["file"]
    return path.read_text(encoding="utf-8")


def list_prompts() -> list[dict]:
    """列出所有可用 prompt。"""
    manifest = _load_manifest()
    return [
        {"name": k.split("/v")[0], "version": k.split("/v")[-1], **v}
        for k, v in manifest.items()
    ]


def get_prompt_hash(name: str, version: str = "latest") -> str:
    """获取 prompt 的 SHA256 哈希。"""
    manifest = _load_manifest()
    if version == "latest":
        candidates = {k: v for k, v in manifest.items() if k.startswith(f"{name}/")}
        if not candidates:
            raise KeyError(f"Prompt '{name}' not found")
        key = max(candidates.keys(), key=lambda k: k.split("/v")[-1])
    else:
        key = f"{name}/{version}"
    return manifest[key]["hash"]
