"""AgentRepository 单元测试 + AgentIdentity 验证。"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

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
    },
}


class TestAgentRepositoryLoad:
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_returns_identity(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = SAMPLE_YAML
        identity = AgentRepository.load("opportunity_scanner", agents_dir="/fake/agents")
        assert identity is not None
        assert identity.key == "opportunity_scanner"
        assert identity.name == "商机雷达"
        assert identity.role == "商机雷达"
        assert "query_bidding" in identity.allowed_tools
        assert identity.model_preference.provider == "deepseek"
        assert identity.model_preference.level == "cloud_normal"
        assert identity.trigger_mode == "cron"
        assert identity.safety_profile.max_permission == "write"

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_returns_none_for_missing(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_file.side_effect = FileNotFoundError
        identity = AgentRepository.load("nonexistent", agents_dir="/fake/agents")
        assert identity is None

    def test_load_from_real_file(self) -> None:
        agents_dir = Path("agents")
        if not agents_dir.is_dir():
            pytest.skip("agents directory not found")
        identity = AgentRepository.load("opportunity_scanner")
        assert identity is not None
        assert identity.key == "opportunity_scanner"
        assert len(identity.allowed_tools) > 0

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_handles_empty_yaml(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = None
        identity = AgentRepository.load("empty_agent", agents_dir="/fake/agents")
        assert identity is not None
        assert identity.key == "empty_agent"

    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_load_handles_missing_fields(self, mock_file: mock_open, mock_yaml_load: object) -> None:
        mock_yaml_load.return_value = {"key": "minimal", "name": "minimal", "role": "", "goal": ""}
        identity = AgentRepository.load("minimal", agents_dir="/fake/agents")
        assert identity is not None
        assert identity.name == "minimal"
        assert identity.allowed_tools == []


class TestAgentRepositoryListAll:
    @patch("cloud.app.agents.agent_repository.Path.rglob")
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_list_all_returns_multiple(self, mock_file: mock_open, mock_yaml_load: object, mock_rglob: object) -> None:
        mock_rglob.return_value = sorted(
            [
                Path("/fake/agents/opportunity_scanner/identity.yaml"),
                Path("/fake/agents/knowledge_worker/identity.yaml"),
            ]
        )
        mock_yaml_load.side_effect = [SAMPLE_YAML_2, SAMPLE_YAML]
        identities = AgentRepository.list_all(agents_dir="/fake/agents")
        assert len(identities) == 2
        assert identities[0].key == SAMPLE_YAML_2["key"]
        assert identities[1].key == SAMPLE_YAML["key"]

    def test_list_all_from_real_fs(self) -> None:
        agents_dir = Path("agents")
        if not agents_dir.is_dir():
            pytest.skip("agents directory not found")
        identities = AgentRepository.list_all()
        assert len(identities) >= 5
        keys = [i.key for i in identities]
        assert "opportunity_scanner" in keys
        assert "knowledge_worker" in keys
        assert "compliance_monitor" in keys
        assert "anomaly_analysis" in keys
        assert "sales_suggestion" in keys

    @patch("cloud.app.agents.agent_repository.Path.is_dir")
    def test_list_all_empty_when_no_dir(self, mock_is_dir: object) -> None:
        mock_is_dir.return_value = False
        identities = AgentRepository.list_all(agents_dir="/nonexistent")
        assert identities == []

    @patch("cloud.app.agents.agent_repository.Path.rglob")
    @patch("cloud.app.agents.agent_repository.yaml.safe_load")
    @patch("cloud.app.agents.agent_repository.open", new_callable=mock_open)
    def test_list_all_skips_failed_yaml(self, mock_file: mock_open, mock_yaml_load: object, mock_rglob: object) -> None:
        mock_rglob.return_value = sorted(
            [
                Path("/fake/agents/good/identity.yaml"),
                Path("/fake/agents/bad/identity.yaml"),
            ]
        )
        mock_yaml_load.side_effect = [yaml.YAMLError("bad"), SAMPLE_YAML]
        identities = AgentRepository.list_all(agents_dir="/fake/agents")
        assert len(identities) == 1
        assert identities[0].key == SAMPLE_YAML["key"]
