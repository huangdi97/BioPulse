"""AgentModel + AgentRepository 单元测试。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

from cloud.app.agents.agent_model import AgentModel
from cloud.app.agents.agent_repository import AgentRepository

SAMPLE_YAML = {
    "key": "opportunity_scanner",
    "name": "商机雷达",
    "role": "商机雷达",
    "goal": "自动发现并评分新的销售机会",
    "backstory": "",
    "allowed_tools": [
        "query_bidding",
        "query_opportunity",
        "create_notification",
        "analyze_with_llm",
    ],
    "memory_namespace": "opportunity",
    "model_preference": {
        "provider": "deepseek",
        "level": "cloud_normal",
        "temperature": 0.3,
    },
    "cost_budget": 0.20,
    "trigger_mode": "cron",
    "event_subscriptions": [],
    "safety_profile": {
        "max_permission": "write",
        "bulkhead_max_concurrent": 3,
        "rate_limit_per_minute": 20,
        "side_effect_check": True,
        "layer3_deep_check": True,
    },
}

SAMPLE_YAML_2 = {
    "key": "knowledge_worker",
    "name": "知识检索",
    "role": "知识库检索",
    "goal": "快速准确地从知识图谱和记忆中检索信息",
    "backstory": "",
    "allowed_tools": [
        "query_knowledge_graph",
        "search_memory",
        "query_hcp_profile",
        "query_competitor_intel",
        "analyze_with_llm",
    ],
    "memory_namespace": "knowledge",
    "model_preference": {
        "provider": "deepseek",
        "level": "cloud_normal",
        "temperature": 0.1,
    },
    "cost_budget": 0.05,
    "trigger_mode": "user_request",
    "event_subscriptions": [],
    "safety_profile": {
        "max_permission": "read",
        "bulkhead_max_concurrent": 10,
        "rate_limit_per_minute": 100,
        "side_effect_check": True,
        "layer3_deep_check": True,
    },
}


class TestAgentModel:
    def test_create_minimal(self) -> None:
        model = AgentModel(agent_id="test", name="测试代理", persona="测试角色: 测试目标")
        assert model.agent_id == "test"
        assert model.name == "测试代理"
        assert model.persona == "测试角色: 测试目标"
        assert model.capabilities == []
        assert model.model_preference == ""

    def test_create_full(self) -> None:
        model = AgentModel(
            agent_id="scanner",
            name="商机雷达",
            persona="商机雷达: 发现商机",
            capabilities=["query_bidding", "query_opportunity"],
            model_preference="deepseek/cloud_normal",
            safety_level="write",
            interrupt_behavior="cron",
        )
        assert model.agent_id == "scanner"
        assert model.model_preference == "deepseek/cloud_normal"
        assert model.safety_level == "write"
        assert model.interrupt_behavior == "cron"

    def test_immutable(self) -> None:
        model = AgentModel(agent_id="fix", name="固定", persona="角色: 目标")
        with pytest.raises(AttributeError):
            model.agent_id = "changed"  # type: ignore[misc]


class TestAgentRepositoryLoad:
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_returns_model(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = SAMPLE_YAML
        model = AgentRepository.load("opportunity_scanner", agents_dir="/fake/agents")
        assert model is not None
        assert model.agent_id == "opportunity_scanner"
        assert model.name == "商机雷达"
        assert "商机雷达" in model.persona
        assert "query_bidding" in model.capabilities
        assert model.model_preference == "deepseek/cloud_normal"
        assert model.safety_level == "write"
        assert model.interrupt_behavior == "cron"

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_returns_none_for_missing(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_file.side_effect = FileNotFoundError
        model = AgentRepository.load("nonexistent", agents_dir="/fake/agents")
        assert model is None

    def test_load_from_real_file(self) -> None:
        agents_dir = Path("agents")
        if not agents_dir.is_dir():
            pytest.skip("agents directory not found")
        model = AgentRepository.load("opportunity_scanner")
        assert model is not None
        assert model.agent_id == "opportunity_scanner"
        assert len(model.capabilities) > 0

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_handles_empty_yaml(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = None
        model = AgentRepository.load("empty_agent", agents_dir="/fake/agents")
        assert model is not None
        assert model.agent_id == "empty_agent"

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_handles_missing_fields(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = {"key": "minimal"}
        model = AgentRepository.load("minimal", agents_dir="/fake/agents")
        assert model is not None
        assert model.name == "minimal"
        assert model.capabilities == []


class TestAgentRepositoryListAll:
    @patch("cloud.app.agents.agent_repository.Path.rglob")
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_list_all_returns_multiple(self, mock_file: mock_open, mock_yaml_load: object, mock_rglob: object) -> None:
        mock_rglob.return_value = sorted(
            [  # sorted alphabetically = knowledge_worker before opportunity_scanner
                Path("/fake/agents/opportunity_scanner/identity.yaml"),
                Path("/fake/agents/knowledge_worker/identity.yaml"),
            ]
        )
        mock_yaml_load.side_effect = [SAMPLE_YAML_2, SAMPLE_YAML]
        models = AgentRepository.list_all(agents_dir="/fake/agents")
        assert len(models) == 2
        assert models[0].agent_id == "knowledge_worker"
        assert models[1].agent_id == "opportunity_scanner"

    def test_list_all_from_real_fs(self) -> None:
        agents_dir = Path("agents")
        if not agents_dir.is_dir():
            pytest.skip("agents directory not found")
        models = AgentRepository.list_all()
        assert len(models) >= 5
        ids = [m.agent_id for m in models]
        assert "opportunity_scanner" in ids
        assert "knowledge_worker" in ids
        assert "compliance_monitor" in ids
        assert "anomaly_analysis" in ids
        assert "sales_suggestion" in ids

    @patch("cloud.app.agents.agent_repository.Path.is_dir")
    def test_list_all_empty_when_no_dir(self, mock_is_dir: object) -> None:
        mock_is_dir.return_value = False
        models = AgentRepository.list_all(agents_dir="/nonexistent")
        assert models == []

    @patch("cloud.app.agents.agent_repository.Path.rglob")
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_list_all_skips_failed_yaml(self, mock_file: mock_open, mock_yaml_load: object, mock_rglob: object) -> None:
        mock_rglob.return_value = sorted(
            [  # sorted alphabetically = bad before good
                Path("/fake/agents/good/identity.yaml"),
                Path("/fake/agents/bad/identity.yaml"),
            ]
        )
        mock_yaml_load.side_effect = [yaml.YAMLError("bad"), SAMPLE_YAML]
        models = AgentRepository.list_all(agents_dir="/fake/agents")
        assert len(models) == 1
        assert models[0].agent_id == "good"
