"""EdacAgentTrigger 单元测试 — 动态加载 identity.yaml。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from cloud.app.agent_runtime.core.models import AgentIdentity
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
        assert "compliance_monitor" in ids
        assert "anomaly_analysis" in ids
        assert "sales_suggestion" in ids

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_loads_single_agent(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="test_agent", name="测试代理", role="测试角色", goal="测试目标"),
        ]
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
        mock_list_all.return_value = [
            AgentIdentity(key="compliance_agent", name="合规审查", role="合规审计专家", goal="确保合规"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("请 compliance_agent 检查合规")
        assert found is not None
        assert found.key == "compliance_agent"

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_find_agent_by_name(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="kw", name="知识检索", role="知识库检索", goal="检索信息"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("知识检索 帮我查一下")
        assert found is not None
        assert found.key == "kw"

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_no_match_returns_none(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="agent_a", name="Agent A", role="A", goal="测试"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("无关消息")
        assert found is None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_match_is_case_insensitive(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="Compliance_Agent", name="Compliance Check", role="合规", goal="检查"),
        ]
        trigger = EdacAgentTrigger()
        found = trigger.find_agent("compliance_agent please run")
        assert found is not None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_removed_agent_not_triggerable(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="existing", name="Existing Agent", role="存在", goal="测试"),
        ]
        trigger = EdacAgentTrigger()
        assert trigger.find_agent("removed_agent") is None
        assert trigger.get_agent("removed_agent") is None

    @patch("cloud.app.agents.agent_repository.AgentRepository.list_all")
    def test_new_identity_yaml_autodiscovered(self, mock_list_all: object) -> None:
        mock_list_all.return_value = [
            AgentIdentity(key="existing", name="现有", role="现有", goal="测试"),
            AgentIdentity(key="new_agent", name="新代理", role="新", goal="测试"),
        ]
        trigger = EdacAgentTrigger()
        assert trigger.get_agent("new_agent") is not None
        assert "new_agent" in trigger.agent_ids
