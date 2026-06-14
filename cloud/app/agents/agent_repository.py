"""Agent 仓库 — 从 agents/*/identity.yaml 加载 AgentModel。"""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from cloud.app.agents.agent_model import AgentModel

logger = logging.getLogger(__name__)

__all__ = ["AgentRepository"]

_AGENTS_DIR = Path("agents")


class AgentRepository:
    """从文件系统加载 AgentModel 实例的仓库。"""

    @staticmethod
    def load(agent_id: str, agents_dir: str | Path | None = None) -> AgentModel | None:
        """加载指定 agent_id 对应的 AgentModel（匹配目录名）。"""
        base = Path(agents_dir) if agents_dir else _AGENTS_DIR
        yaml_path = base / agent_id / "identity.yaml"
        return AgentRepository._parse_yaml(yaml_path)

    @staticmethod
    def list_all(agents_dir: str | Path | None = None) -> list[AgentModel]:
        """扫描所有 agents/*/identity.yaml 并返回 AgentModel 列表。"""
        base = Path(agents_dir) if agents_dir else _AGENTS_DIR
        result: list[AgentModel] = []
        for yaml_path in sorted(base.rglob("identity.yaml")):
            try:
                model = AgentRepository._parse_yaml(yaml_path)
                if model is not None:
                    result.append(model)
            except Exception:
                logger.exception("Failed to load agent from %s", yaml_path)
        return result

    @staticmethod
    def _parse_yaml(path: Path) -> AgentModel | None:
        """从 identity.yaml 文件解析为 AgentModel。"""
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except Exception:
            logger.exception("Failed to read YAML: %s", path)
            return None
        if not isinstance(data, dict):
            logger.warning("Empty or invalid YAML in %s, using defaults", path)
            return AgentModel(agent_id=path.parent.name, name=path.parent.name, persona="")
        agent_id = path.parent.name
        model_preference_raw = data.get("model_preference", {})
        if isinstance(model_preference_raw, dict):
            provider = model_preference_raw.get("provider", "deepseek")
            level = model_preference_raw.get("level", "cloud_normal")
            model_preference = f"{provider}/{level}"
        else:
            model_preference = str(model_preference_raw)
        safety = data.get("safety_profile", {})
        if isinstance(safety, dict):
            safety_level = safety.get("max_permission", "read")
        else:
            safety_level = "read"
        return AgentModel(
            agent_id=agent_id,
            name=data.get("name", agent_id),
            persona=f"{data.get('role', '')}: {data.get('goal', '')}",
            capabilities=data.get("allowed_tools", []),
            model_preference=model_preference,
            safety_level=safety_level,
            interrupt_behavior=data.get("trigger_mode", "user_request"),
        )
