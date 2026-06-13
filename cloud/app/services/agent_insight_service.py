from cloud.app.agent_runtime.agent_registry import AgentRegistry


class AgentInsightService:
    PAGE_AGENT_MAPPING = {
        "manager_dashboard": ["anomaly_analysis"],
        "rep_dashboard": ["sales_suggestion"],
        "compliance_overview": ["compliance_monitor"],
    }

    async def get_insights(self, page_id: str, user_id: str) -> list:
        agent_keys = self.PAGE_AGENT_MAPPING.get(page_id, [])
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
