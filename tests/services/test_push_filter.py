"""推送事件过滤测试——验证 PushEventFilter 正确过滤事件"""

from cloud.app.services.agent_push_service import (
    AgentPushService,
    PushEventFilter,
    PushEventType,
)


class TestPushEventFilter:
    """PushEventFilter 单元测试"""

    def test_compliance_red_light_allowed(self):
        """合规红灯事件 → 允许推送"""
        assert PushEventFilter.is_allowed(PushEventType.COMPLIANCE_RED_LIGHT.value)

    def test_high_value_suggestion_allowed(self):
        """高价值建议事件 → 允许推送"""
        assert PushEventFilter.is_allowed(PushEventType.HIGH_VALUE_SUGGESTION.value)

    def test_anomaly_data_allowed(self):
        """异常数据事件 → 允许推送"""
        assert PushEventFilter.is_allowed(PushEventType.ANOMALY_DATA.value)

    def test_low_priority_event_blocked(self):
        """低优先级事件（如 Insight Bar 更新）→ 阻止推送"""
        assert not PushEventFilter.is_allowed("insight_bar_update")

    def test_empty_event_type_blocked(self):
        """空事件类型 → 阻止推送"""
        assert not PushEventFilter.is_allowed("")

    def test_unknown_event_type_blocked(self):
        """未知事件类型 → 阻止推送"""
        assert not PushEventFilter.is_allowed("random_event")

    def test_filter_events_multiple(self):
        """filter_events 混合事件 → 只保留允许的"""
        events = [
            {"event_type": "compliance_red_light", "title": "红灯"},
            {"event_type": "insight_bar_update", "title": "洞察更新"},
            {"event_type": "high_value_suggestion", "title": "高价值"},
            {"event_type": "anomaly_data", "title": "异常"},
        ]
        result = PushEventFilter.filter_events(events)
        assert len(result) == 3
        titles = [e["title"] for e in result]
        assert "红灯" in titles
        assert "洞察更新" not in titles
        assert "高价值" in titles
        assert "异常" in titles


class TestPushFilterIntegration:
    """AgentPushService + PushEventFilter 集成测试"""

    def test_push_insight_with_allowed_event(self):
        """push_insight 传入允许事件类型 → 推送成功（不报错）"""
        service = AgentPushService()
        result = service.push_insight(
            agent_key="test_agent",
            user_id="user_1",
            title="合规红灯",
            message="检测到违规行为",
            event_type="compliance_red_light",
        )
        assert isinstance(result, bool)

    def test_push_insight_with_blocked_event(self):
        """push_insight 传入被拦截事件 → 返回 False"""
        service = AgentPushService()
        result = service.push_insight(
            agent_key="test_agent",
            user_id="user_2",
            title="洞察更新",
            message="Insight Bar 更新",
            event_type="insight_bar_update",
        )
        assert result is False

    def test_push_insight_without_event_type(self):
        """push_insight 不传 event_type（默认 None）→ 不拦截"""
        service = AgentPushService()
        result = service.push_insight(
            agent_key="test_agent",
            user_id="user_3",
            title="无类型事件",
            message="测试",
        )
        assert isinstance(result, bool)
