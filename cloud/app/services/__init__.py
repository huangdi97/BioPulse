"""Service-layer package for cloud app."""

import importlib as _importlib
import sys as _sys

# ── brain sub-package re-exports (backward compat) ──────────────
# Must precede direct imports (memory_namespace, memory_service moved to brain/)
# Modules ordered by dependency to resolve internal cross-references via old paths
_brain_modules = (
    # independent (no deps on other brain-domain files)
    "brain_evolution_stage",
    "brain_folding_stage",
    "brain_unfolding_stage",
    "brain_search_service",
    "brain_task_scheduler",
    "causal_inference",
    "feature_extractor",
    "federated_node_aggregator",
    "federated_node_manager",
    "kg_builder",
    "kg_stats",
    "mcp_guard_service",
    "memory_consolidation_service",
    "memory_episodic_writer",
    "memory_evaluator_service",
    "memory_namespace",
    "memory_procedural_writer",
    "memory_retriever",
    "memory_working_writer",
    "rl_route_optimizer",
    "rl_router_learner",
    "route_calculation",
    "route_optimization",
    "route_tsp",
    "sage_scoring_service",
    "world_model_service",
    "world_tree_search",
    # dependents (deps on independents above)
    "brain_memory_service",
    "brain_orchestrator_service",
    "causal_graph",
    "feature_analyzer",
    "feature_classifier",
    "federated_node_service",
    "kg_service",
    "mcp_tool_service",
    "memory_gate_service",
    "memory_service",
    "rl_routing_service",
    "route_service",
    "sage_scoring",
    "world_tree_query",
    # dependents (deps on batch 1+2)
    "brain_evolution_service",
    "causal_service",
    "world_tree_service",
    # dependents (deps on batch 3)
    "sage_linking",
    # dependents (deps on batch 4+)
    "sage_engine_service",
)
for _mod_name in _brain_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.brain.{_mod_name}",
    )

# ── intel sub-package re-exports (backward compat) ────────────────

_intel_modules = (
    "academic_conference_service",
    "competitor_alert_service",
    "competitor_tools",
    "intel_analyzer",
    "intel_analyzer_mixin",
    "intel_collector_mixin",
    "mrc_workflow_crud",
    "mrc_workflow_service",
    "mrc_workflow_state",
    "nmpa_service",
    "pi_service",
    "pubmed_service",
    "research_audit_service",
    "research_export_service",
    "research_pi_service",
    "research_product_service",
    "research_service",
    "research_trajectory_ai",
    "research_trajectory_service",
    "research_trajectory_stats",
)
for _mod_name in _intel_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.intel.{_mod_name}",
    )

# ── rep_workbench sub-package re-exports (backward compat) ──────────

_rep_workbench_modules = (
    "attribution_assigner",
    "attribution_calc",
    "coach_ability",
    "coach_gap",
    "content_factory_service",
    "content_service",
    "customer_service",
    "dashboard_service",
    "dialogue_service",
    "eval_service",
    "expense_compliance_service",
    "expense_precheck_service",
    "hcp_briefing_service",
    "hcp_channel_preference",
    "hcp_mdm_service",
    "hcp_sandbox_service",
    "hcp_sandbox_sim",
    "hcp_scoring_service",
    "hcp_simulation_core",
    "interaction_service",
    "notification_builder",
    "notification_service",
    "opportunity_scoring",
    "opportunity_service",
    "product_matching_service",
    "product_match_scorer",
    "product_service",
    "recommend_filter",
    "recommend_service",
    "report_generator",
    "report_templates",
    "scheduling_service",
    "settings_service",
    "soap_decision_parser",
    "soap_decision_service",
    "soap_decision_validator",
    "team_service",
    "training_coach_recommender",
    "training_coach_service",
    "training_scripts_service",
    "user_service",
    "visit_extraction_service",
    "visit_prioritization_service",
    "visit_service",
)
for _mod_name in _rep_workbench_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.rep_workbench.{_mod_name}",
    )

# ── agent_ops sub-package re-exports (backward compat) ──────────────

_agent_ops_modules = (
    "a2a_discovery",
    "agent_pipeline_exec",
    "agent_execution",
    "base_provider",
    "token_budget_service",
    "a2a_registry_service",
    "agent_pipeline_service",
    "agent_framework_service",
    "api_providers",
    "llm_service",
    "ai_gateway_service",
    "llm_extraction_service",
    "agent_chain_service",
    "agent_event_bridge",
    "agent_execution_service",
    "agent_health_service",
    "agent_insight_service",
    "agent_role_service",
    "agent_runtime_service",
    "agent_trace_service",
)
for _mod_name in _agent_ops_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.agent_ops.{_mod_name}",
    )

# ── compliance_svc sub-package re-exports (backward compat) ─────────

_compliance_modules = (
    "audit_service",
    "capa_event_service",
    "capa_workflow_service",
    "decision_intel_service",
    "decision_logger",
    "diversion_service",
    "enforcer_service",
    "exclusion_gate_service",
    "holographic_association",
    "holographic_service",
    "part11_compliance_service",
    "remediation_scoring",
    "remediation_service",
    "rule_aggregator",
    "rule_evaluator",
    "trust_audit_service",
)
for _mod_name in _compliance_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.compliance_svc.{_mod_name}",
    )

# ── collab sub-package re-exports (backward compat) ─────────────────

_collab_modules = (
    "collaboration_message",
    "collaboration_service",
    "collaboration_session",
    "marketplace_benchmark",
    "marketplace_service",
    "mdt_agent_service",
    "mdt_debate_scorer",
    "mdt_debater",
    "mdt_engine_service",
    "mdt_resolver",
    "network_crud",
    "network_sync",
)
for _mod_name in _collab_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.collab.{_mod_name}",
    )

# ── platform_svc sub-package re-exports (backward compat) ───────────

_platform_modules = (
    "admission_service",
    "anomaly_context_service",
    "api_token_service",
    "approval_service",
    "asr_service",
    "auth_service",
    "board_service",
    "budget_tracker",
    "cell_topology_service",
    "compute_scheduler",
    "compute_service",
    "config_service",
    "event_bus_service",
    "export_service",
    "extraction_schema",
    "fed_weight_calculator",
    "flying_inspection_calculation",
    "flying_inspection_crud",
    "_flying_inspection_data",
    "inference_pipeline",
    "local_providers",
    "model_compression_service",
    "orchestrate_service",
    "predictive_scoring_service",
    "quotations_service",
    "quotation_workflow_service",
    "redis_event_backend",
    "rep_license_service",
    "semantic_cache_service",
    "sqlite_event_backend",
    "task_service",
    "tenant_isolation_service",
    "tts_service",
    "utility_opt",
    "utility_ranker",
    "utility_score",
)
for _mod_name in _platform_modules:
    _sys.modules[f"cloud.app.services.{_mod_name}"] = _importlib.import_module(
        f"cloud.app.services.platform_svc.{_mod_name}",
    )

from cloud.app.services.attribution_calc import AttributionCalcMixin, AttributionCheckMixin  # noqa: E402
from cloud.app.services.coach_ability import CoachAbility  # noqa: E402
from cloud.app.services.coach_gap import CoachGap  # noqa: E402
from cloud.app.services.collab.network_crud import NetworkCrudMixin  # noqa: E402
from cloud.app.services.collab.network_sync import NetworkSyncMixin  # noqa: E402
from cloud.app.services.intel_analyzer_mixin import IntelAnalyzerMixin  # noqa: E402
from cloud.app.services.intel_collector_mixin import IntelCollectorMixin  # noqa: E402
from cloud.app.services.memory_namespace import MemoryNamespace  # noqa: E402
from cloud.app.services.memory_service import MemoryService  # noqa: E402
from cloud.app.services.platform_svc.utility_opt import UtilityOptMixin  # noqa: E402
from cloud.app.services.platform_svc.utility_score import UtilityScoreMixin  # noqa: E402
from shared.base_service import BaseService  # noqa: E402


class CausalAttributionService(AttributionCalcMixin, AttributionCheckMixin, BaseService):
    """因果归因服务，合并归因刷新、模拟与读取能力。"""


class CellNetworkService(NetworkCrudMixin, NetworkSyncMixin, BaseService):
    """Cell 网络服务，整合网络 CRUD 与节点同步能力。"""


class MemoryUtilityService(UtilityScoreMixin, UtilityOptMixin, BaseService):
    """记忆效用服务，组合评分计算与效用优化混入类。"""


class MarketIntelService(IntelCollectorMixin, IntelAnalyzerMixin, BaseService):
    """市场情报服务，组合情报采集与分析能力。"""


class CoachAssessor(BaseService, CoachAbility, CoachGap):
    """培训教练评估服务。"""


__all__ = [
    "BaseService",
    "MemoryNamespace",
    "MemoryService",
    "CausalAttributionService",
    "CellNetworkService",
    "CoachAssessor",
    "MarketIntelService",
    "MemoryUtilityService",
]

del (
    _importlib,
    _sys,
    _agent_ops_modules,
    _brain_modules,
    _intel_modules,
    _rep_workbench_modules,
    _compliance_modules,
    _collab_modules,
    _platform_modules,
    _mod_name,
)
