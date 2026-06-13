"""Agent 注册中心 — 扫描 agents/*/identity.yaml 并缓存 Agent 实例。"""

import logging
from pathlib import Path

from cloud.app.agent_runtime.agent import Agent

logger = logging.getLogger(__name__)

_AGENTS_DIR = Path("agents")


class AgentRegistry:
    _agents: dict[str, Agent] = {}
    _loaded = False

    @classmethod
    def load(cls, agents_dir: str | Path | None = None) -> None:
        cls._agents.clear()
        base = Path(agents_dir) if agents_dir else _AGENTS_DIR
        if not base.is_dir():
            logger.warning("Agent directory not found: %s", base)
            cls._loaded = True
            return
        for yaml_path in sorted(base.rglob("identity.yaml")):
            try:
                agent = Agent.from_yaml(str(yaml_path))
                cls._agents[agent.identity.key] = agent
                logger.info("Loaded agent %s from %s", agent.identity.key, yaml_path)
            except Exception:
                logger.exception("Failed to load agent from %s", yaml_path)
        cls._loaded = True
        logger.info("AgentRegistry loaded %d agents", len(cls._agents))

    @classmethod
    def get(cls, key: str) -> Agent | None:
        if not cls._loaded:
            cls.load()
        return cls._agents.get(key)

    @classmethod
    def list(cls) -> list[Agent]:
        if not cls._loaded:
            cls.load()
        return list(cls._agents.values())

    @classmethod
    def reload(cls) -> None:
        cls._loaded = False
        cls.load()
