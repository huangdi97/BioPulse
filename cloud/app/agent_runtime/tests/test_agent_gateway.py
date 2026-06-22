"""Agent gateway route tests."""

from cloud.app.routers.agent_gateway_router import GATEWAY_ROUTES


class TestGatewayRoutes:
    def test_all_agents_route(self):
        """test all agents route."""
        assert len(GATEWAY_ROUTES) >= 20

    def test_compliance_tools_registered(self):
        """test compliance tools registered."""
        required = [
            "verify_expense",
            "verify_visit",
            "holographic_audit_check",
            "write_audit_log",
            "trigger_red_light",
        ]
        for tool in required:
            assert tool in GATEWAY_ROUTES, f"Missing tool: {tool}"

    def test_analysis_tools_registered(self):
        """test analysis tools registered."""
        required = [
            "collect_related_data",
            "run_pattern_analysis",
            "run_causal_inference",
            "generate_narrative",
        ]
        for tool in required:
            assert tool in GATEWAY_ROUTES, f"Missing tool: {tool}"

    def test_suggestion_tools_registered(self):
        """test suggestion tools registered."""
        required = [
            "query_hcp_profile",
            "query_visit_history",
            "query_competitor_intel",
            "generate_brief",
        ]
        for tool in required:
            assert tool in GATEWAY_ROUTES, f"Missing tool: {tool}"
