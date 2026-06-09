"""FastAPI 路由注册与启动事件。"""

from fastapi import FastAPI

from cloud.app.agent_database import init_agent_db
from cloud.app.database import init_db
from cloud.app.research_database import init_research_db as init_research
from cloud.app.routers.a2a_registry_router import router as a2a_registry_router
from cloud.app.routers.academic_conference_router import router as academic_conference_router
from cloud.app.routers.agent_execution_router import router as agent_execution_router
from cloud.app.routers.agent_framework_router import router as agent_framework_router
from cloud.app.routers.agent_gateway_router import router as agent_gateway_router
from cloud.app.routers.agent_pipeline_router import router as agent_pipeline_router
from cloud.app.routers.agent_role_router import router as agent_role_router
from cloud.app.routers.agent_runtime_router import router as agent_runtime_router
from cloud.app.routers.ai_gateway import router as ai_router
from cloud.app.routers.api_tokens import router as tokens_router
from cloud.app.routers.audit_router import router as audit_router
from cloud.app.routers.auth_router import router as auth_router
from cloud.app.routers.board_router import router as board_router
from cloud.app.routers.brain_memory_router import router as brain_memory_router
from cloud.app.routers.brain_orchestrator_router import router as brain_orchestrator_router
from cloud.app.routers.causal_attribution_router import router as causal_attribution_router
from cloud.app.routers.causal_router import router as causal_router
from cloud.app.routers.cell_network_router import router as cell_network_router
from cloud.app.routers.collaboration_router import router as collaboration_router
from cloud.app.routers.competitor_intel_router import router as competitor_intel_router
from cloud.app.routers.compliance_dashboard_router import (
    router as compliance_dashboard_router,
)
from cloud.app.routers.compliance_router import router as compliance_router
from cloud.app.routers.compliance_v2_router import router as compliance_v2_router
from cloud.app.routers.compute_router import router as compute_router
from cloud.app.routers.config_router import router as config_router
from cloud.app.routers.content_factory_router import router as content_factory_router
from cloud.app.routers.contents_router import router as contents_router
from cloud.app.routers.customer_router import router as customer_router
from cloud.app.routers.dashboard_router import router as dashboard_router
from cloud.app.routers.data_platform_router import router as data_platform_router
from cloud.app.routers.decision_intel_router import router as decision_intel_router
from cloud.app.routers.demo_router import router as demo_router
from cloud.app.routers.enforcer_router import router as enforcer_router
from cloud.app.routers.eval_router import router as eval_router
from cloud.app.routers.event_bus_router import router as event_bus_router
from cloud.app.routers.expense_compliance_router import (
    router as expense_compliance_router,
)
from cloud.app.routers.export_router import router as export_router
from cloud.app.routers.federated_node_router import router as federated_node_router
from cloud.app.routers.flying_inspection_router import router as flying_inspection_router
from cloud.app.routers.hcp_mdm_router import router as hcp_mdm_router
from cloud.app.routers.hcp_preference_router import router as hcp_preference_router
from cloud.app.routers.hcp_sandbox_router import router as hcp_sandbox_router
from cloud.app.routers.hcp_scoring_router import router as hcp_scoring_router
from cloud.app.routers.holographic_router import router as holographic_router
from cloud.app.routers.interaction_router import router as interaction_router
from cloud.app.routers.kg_router import router as kg_router
from cloud.app.routers.langgraph_test_router import router as langgraph_test_router
from cloud.app.routers.market_intel_router import router as market_intel_router
from cloud.app.routers.marketplace_router import router as marketplace_router
from cloud.app.routers.mcp_router import router as mcp_router
from cloud.app.routers.mdt_agent_router import router as mdt_agent_router
from cloud.app.routers.mdt_engine_router import router as mdt_engine_router
from cloud.app.routers.memory_consolidation_router import router as memory_consolidation_router
from cloud.app.routers.memory_gate_router import router as memory_gate_router
from cloud.app.routers.memory_utility_router import router as memory_utility_router
from cloud.app.routers.metrics_router import router as metrics_router
from cloud.app.routers.model_compression_router import router as model_compression_router
from cloud.app.routers.mrc_workflow_router import router as mrc_workflow_router
from cloud.app.routers.nmpa_router import router as nmpa_router
from cloud.app.routers.notification_router import router as notification_router
from cloud.app.routers.opportunity_router import opportunity_v2_router
from cloud.app.routers.opportunity_router import router as opportunity_router
from cloud.app.routers.orchestrate_router import router as orchestrate_router
from cloud.app.routers.part11_compliance_router import router as part11_compliance_router
from cloud.app.routers.pi_router import router as pi_router
from cloud.app.routers.product_router import router as product_router
from cloud.app.routers.pubmed_router import router as pubmed_router
from cloud.app.routers.recommend_router import router as recommend_router
from cloud.app.routers.rep_license_router import router as rep_license_router
from cloud.app.routers.research_audit_router import router as research_audit_router
from cloud.app.routers.research_enforcer_router import (
    router as research_enforcer_router,
)
from cloud.app.routers.research_export_router import router as research_export_router
from cloud.app.routers.research_matching_router import (
    router as research_matching_router,
)
from cloud.app.routers.research_pi_router import router as research_pi_router
from cloud.app.routers.research_product_router import router as research_product_router
from cloud.app.routers.research_quotation_router import (
    router as research_quotation_router,
)
from cloud.app.routers.research_quotation_workflow_router import (
    router as research_quotation_workflow_router,
)
from cloud.app.routers.research_route_router import router as research_route_router
from cloud.app.routers.research_trajectory_router import router as research_trajectory_router
from cloud.app.routers.rl_routing_router import router as rl_routing_router
from cloud.app.routers.route_router import router as route_router
from cloud.app.routers.sage_engine_router import router as sage_engine_router
from cloud.app.routers.settings_router import router as settings_router
from cloud.app.routers.soap_decision_router import router as soap_decision_router
from cloud.app.routers.switch_router import router as switch_router
from cloud.app.routers.task_router import router as task_router
from cloud.app.routers.teams_router import router as teams_router
from cloud.app.routers.token_budget_router import router as token_budget_router
from cloud.app.routers.training_coach_router import router as training_coach_router
from cloud.app.routers.training_scripts_router import router as training_scripts_router
from cloud.app.routers.trust_audit_router import router as trust_audit_router
from cloud.app.routers.users_router import router as users_router
from cloud.app.routers.visit_router import router as visit_router
from cloud.app.routers.world_tree_router import router as world_tree_router
from cloud.app.services.tenant_isolation_service import router as tenant_isolation_router


def register_routers(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(tokens_router)
    app.include_router(compliance_router)
    app.include_router(users_router)
    app.include_router(contents_router)
    app.include_router(ai_router)
    app.include_router(teams_router)
    app.include_router(audit_router)
    app.include_router(notification_router)
    app.include_router(board_router)
    app.include_router(dashboard_router)
    app.include_router(data_platform_router)
    app.include_router(customer_router)
    app.include_router(interaction_router)
    app.include_router(config_router)
    app.include_router(export_router)
    app.include_router(opportunity_router)
    app.include_router(opportunity_v2_router)
    app.include_router(task_router)
    app.include_router(market_intel_router)
    app.include_router(competitor_intel_router)
    app.include_router(mrc_workflow_router)
    app.include_router(agent_role_router)
    app.include_router(agent_pipeline_router)
    app.include_router(decision_intel_router)
    app.include_router(compliance_v2_router)
    app.include_router(mdt_engine_router)
    app.include_router(memory_gate_router)
    app.include_router(world_tree_router)
    app.include_router(route_router)
    app.include_router(hcp_sandbox_router)
    app.include_router(training_coach_router)
    app.include_router(soap_decision_router)
    app.include_router(memory_utility_router)
    app.include_router(brain_memory_router)
    app.include_router(kg_router)
    app.include_router(recommend_router)
    app.include_router(collaboration_router)
    app.include_router(event_bus_router)
    app.include_router(expense_compliance_router)
    app.include_router(part11_compliance_router)
    app.include_router(memory_consolidation_router)
    app.include_router(holographic_router)
    app.include_router(sage_engine_router)
    app.include_router(agent_execution_router)
    app.include_router(agent_runtime_router)
    app.include_router(mcp_router)
    app.include_router(orchestrate_router)
    app.include_router(causal_router)
    app.include_router(compute_router)
    app.include_router(nmpa_router)
    app.include_router(training_scripts_router)
    app.include_router(marketplace_router)
    app.include_router(model_compression_router)
    app.include_router(settings_router)
    app.include_router(visit_router)
    app.include_router(pubmed_router)
    app.include_router(pi_router)
    app.include_router(product_router)
    app.include_router(langgraph_test_router)
    app.include_router(enforcer_router)
    app.include_router(compliance_dashboard_router)
    app.include_router(demo_router)
    app.include_router(research_audit_router)
    app.include_router(research_pi_router)
    app.include_router(research_product_router)
    app.include_router(research_quotation_router)
    app.include_router(research_enforcer_router)
    app.include_router(research_export_router)
    app.include_router(research_matching_router)
    app.include_router(research_route_router)
    app.include_router(research_trajectory_router)
    app.include_router(research_quotation_workflow_router)
    app.include_router(switch_router)
    app.include_router(token_budget_router)
    app.include_router(a2a_registry_router)
    app.include_router(agent_framework_router)
    app.include_router(brain_orchestrator_router)
    app.include_router(causal_attribution_router)
    app.include_router(federated_node_router)
    app.include_router(mdt_agent_router)
    app.include_router(rl_routing_router)
    app.include_router(trust_audit_router)
    app.include_router(content_factory_router)
    app.include_router(cell_network_router)
    app.include_router(agent_gateway_router)
    app.include_router(metrics_router)
    app.include_router(eval_router)
    app.include_router(flying_inspection_router)
    app.include_router(hcp_scoring_router)
    app.include_router(hcp_mdm_router)
    app.include_router(academic_conference_router)
    app.include_router(hcp_preference_router)
    app.include_router(rep_license_router)
    app.include_router(tenant_isolation_router)


def register_startup_events(app: FastAPI) -> None:
    @app.on_event("startup")
    def startup():
        init_agent_db()
        init_db()
        init_research()
