"""Agent 仓库 — 从 agents/*/identity.yaml 加载 AgentIdentity。

注意：identity.yaml 是 Agent 定义的主要来源。
agent_specs.py 中的 AGENT_SPECS 是运行时覆盖/补充（用于 L4 编排等高级配置）。
当 identity.yaml 与 AGENT_SPECS 同时存在时，identity.yaml 优先作为源数据。"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from cloud.app.agent_runtime.models import AgentIdentity

logger = logging.getLogger(__name__)

__all__ = ["AgentRepository"]

_AGENTS_DIR = Path("agents")


class AgentRepository:
    """从文件系统加载 AgentIdentity 实例的仓库。"""

    @staticmethod
    def load(agent_id: str, agents_dir: str | Path | None = None) -> AgentIdentity | None:
        """加载指定 agent_id 对应的 AgentIdentity（匹配目录名）。"""
        base = Path(agents_dir) if agents_dir else _AGENTS_DIR
        yaml_path = base / agent_id / "identity.yaml"
        return AgentRepository._parse_yaml(yaml_path)

    @staticmethod
    def list_all(agents_dir: str | Path | None = None) -> list[AgentIdentity]:
        """扫描所有 agents/*/identity.yaml 并返回 AgentIdentity 列表。"""
        base = Path(agents_dir) if agents_dir else _AGENTS_DIR
        result: list[AgentIdentity] = []
        for yaml_path in sorted(base.rglob("identity.yaml")):
            try:
                model = AgentRepository._parse_yaml(yaml_path)
                if model is not None:
                    result.append(model)
            except Exception:
                logger.exception("Failed to load agent from %s", yaml_path)
        return result

    @staticmethod
    def _parse_yaml(path: Path) -> AgentIdentity | None:
        """从 identity.yaml 文件解析为 AgentIdentity。"""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.exception("Failed to read YAML: %s", path)
            return None
        if not isinstance(data, dict):
            logger.warning("Empty or invalid YAML in %s, using defaults", path)
            return AgentIdentity(key=path.parent.name, name=path.parent.name, role="", goal="")
        return AgentIdentity(**data)
