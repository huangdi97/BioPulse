"""EdacAgentTrigger 单元测试 — 动态加载 identity.yaml。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from cloud.app.agents.edac_agent_trigger import EdacAgentTrigger


class TestEdacAgentTriggerLoadsFromRepository:
    def test_loads_all_agents_from_real_fs(self) -> None:
        agents_dir = Path("agents")
        if not agents_dir.is_dir():
            pytest.skip("agents directory not found")
        trigger = EdacAgentTrigger()
        ids = trigger.agent_ids
        assert "opportunity_scanner" in ids
        assert "knowledge_worker" in ids
        assert "compliance_agent" in ids
        assert "analysis_agent" in ids
        assert "suggestion_agent" in ids

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_loads_single_agent(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [AgentModel(agent_id="test_agent", name="测试代理", persona="测试角色: 测试目标")]
        trigger = EdacAgentTrigger()
        assert trigger.agent_ids == ["test_agent"]
        assert trigger.get_agent("test_agent") is not None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_empty_when_no_agents(self, mock_list_all: object) -> None:
        mock_list_all.return_value = []
        trigger = EdacAgentTrigger()
        assert trigger.agent_ids == []
        assert trigger.list_agents() == []


class TestEdacAgentTriggerWakewordMatch:
    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_find_agent_by_id(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="compliance_agent", name="合规审查", persona="合规审计专家: 确保合规"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("请 compliance_agent 检查合规")
        assert found is not None
        assert found.agent_id == "compliance_agent"

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_find_agent_by_name(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="kw", name="知识检索", persona="知识库检索: 检索信息"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("知识检索 帮我查一下")
        assert found is not None
        assert found.agent_id == "kw"

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_no_match_returns_none(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="agent_a", name="Agent A", persona="A: 测试"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("无关消息")
        assert found is None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_match_is_case_insensitive(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="Compliance_Agent", name="Compliance Check", persona="合规: 检查"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("compliance_agent please run")
        assert found is not None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_removed_agent_not_triggerable(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="existing", name="Existing Agent", persona="存在: 测试"),
        ]
        trigger = EdacAgentTrigger()
        assert trigger.find_agent("removed_agent") is None
        assert trigger.get_agent("removed_agent") is None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_new_identity_yaml_autodiscovered(self, mock_list_all: object) -> None:
        from cloud.app.agents.agent_model import AgentModel

        mock_list_all.return_value = [
            AgentModel(agent_id="existing", name="现有", persona="现有: 测试"),
            AgentModel(agent_id="new_agent", name="新代理", persona="新: 测试"),
        ]
        trigger = EdacAgentTrigger()
        assert trigger.get_agent("new_agent") is not None
        assert "new_agent" in trigger.agent_ids
