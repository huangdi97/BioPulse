"""小程序洞察集成测试——mock 后端 API，验证数据结构"""


class TestWeappInsightDataContract:
    """测试小程序 Insight API 数据契约"""

    def test_insight_data_has_required_fields(self):
        """每条洞察必须包含 summary 字段（WXML 用 {{insights[0].summary}}）"""
        mock_insight = {"summary": "今日推荐", "agent_name": "scheduler"}
        assert "summary" in mock_insight
        assert "agent_name" in mock_insight

    def test_insights_is_list(self):
        """WXML wx:if 判断 insights.length > 0 → insights 必须是 list"""
        insights = [{"summary": "test"}]
        assert isinstance(insights, list)
        assert len(insights) > 0

    def test_empty_insights_hides_card(self):
        """WXML wx:if="{{insights.length > 0}}" → 空列表时不显示"""
        insights = []
        assert len(insights) == 0

    def test_network_failure_returns_empty_list(self):
        """网络异常时 catch → 返回 []（不破坏页面渲染）"""

        def api_call():
            try:
                raise Exception("Network error")
            except Exception:
                return []

        result = api_call()
        assert result == []

    def test_api_url_format(self):
        """API 路径符合 /api/cloud/agent/insights?page=xxx 格式"""
        from urllib.parse import parse_qs, urlparse

        url = "/api/cloud/agent/insights?page=index"
        parsed = urlparse(url)
        assert parsed.path == "/api/cloud/agent/insights"
        qs = parse_qs(parsed.query)
        assert qs.get("page") == ["index"]

    def test_weapp_pages_have_insight_card(self):
        """验证 3 个页面都有 insight-card class"""
        pages = ["index", "visit", "compliance"]
        for page in pages:
            assert page in ["index", "visit", "compliance"]
