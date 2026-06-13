from cloud.app.agent_runtime.agent_registry import AgentRegistry


class AgentInsightService:
    PAGE_AGENT_MAPPING = {
        "manager_dashboard": ["anomaly_analysis"],
        "rep_dashboard": ["sales_suggestion"],
        "compliance_overview": ["compliance_monitor"],
        "hcp_detail": ["knowledge_worker"],
        "president_summary": ["anomaly_analysis"],
        "president_compliance": ["compliance_monitor"],
        "president_visit_fraud": ["anomaly_analysis"],
        "president_expense_waste": ["anomaly_analysis"],
        "president_rectify": ["compliance_monitor"],
        "manager_inspection": ["compliance_monitor"],
        "manager_admission": ["knowledge_worker"],
        "sa_precall": ["sales_suggestion"],
        "sa_strategy": ["sales_suggestion"],
        "opportunity_list": ["opportunity_scanner"],
        "intel_page": ["knowledge_worker"],
        "pharma_dashboard": ["anomaly_analysis"],
        "web_compliance": ["compliance_monitor"],
        "mobile_visit_list": ["sales_suggestion"],
        "mobile_hcp_detail": ["knowledge_worker"],
        "mobile_compliance": ["compliance_monitor"],
    }

    FALLBACK_RULES = [
        ("manager_", "anomaly_analysis"),
        ("rep_", "sales_suggestion"),
        ("president_", "anomaly_analysis"),
        ("admin_", "anomaly_analysis"),
        ("mobile_", "knowledge_worker"),
        ("web_", "knowledge_worker"),
        ("sa_", "sales_suggestion"),
        ("opportunity_", "opportunity_scanner"),
    ]

    async def get_insights(self, page_id: str, user_id: str) -> list:
        agent_keys = self.PAGE_AGENT_MAPPING.get(page_id)
        if agent_keys is None:
            for prefix, key in self.FALLBACK_RULES:
                if page_id.startswith(prefix):
                    agent_keys = [key]
                    break
            else:
                agent_keys = []
        results = []
        for key in agent_keys:
            agent = AgentRegistry.get(key)
            if agent:
                try:
                    result = await agent.insights_for(page_id, user_id)
                    if result:
                        results.extend(result)
                except Exception:
                    continue
        return results
