"""Agent runtime public exports."""

from importlib import import_module

_EXPORTS = {
    "core.agent": ("Agent",),
    "comm.agent_protocol": ("AgentMessage", "AgentMessageBus"),
    "core.agent_registry": ("AgentRegistry",),
    "core.agent_worker": ("AgentWorker",),
    "core.analysis_agent": ("AnalysisAgent",),
    "analyzer": ("Analysis",),
    "safety.approval_workflow": ("ApprovalWorkflow",),
    "safety.cost_governor": ("CostGovernor",),
    "safety.guard": ("Guard", "GuardLayer1", "Layer", "Layer1Filter", "sanitize_tool_output"),
    "core.loop_detector": ("LoopDetector",),
    "tools.metrics": ("agent_requests_total", "agent_llm_duration", "agent_active_count", "agent_tokens_total", "get_metrics"),
    "memory.memory": ("AgentBrain", "AgentMemory", "Memory"),
    "core.models": (
        "AgentDecision",
        "AgentIdentity",
        "AgentLogEntry",
        "AgentResult",
        "AgentSpec",
        "AgentTier",
        "CheckpointData",
        "CheckResult",
        "ExecutionContext",
        "Insight",
        "ModelPreference",
        "Models",
        "RuntimeResult",
        "SafetyProfile",
        "ToolDef",
        "TriggerMode",
        "VerificationResult",
    ),
    "comm.notifier": ("AgentNotifier", "Notifier"),
    "core.pipeline": ("AgentPipeline", "Pipeline", "PipelineStep"),
    "core.planner": ("Plan", "PlanGenerator", "Planner", "PlanStep"),
    "core.queue_manager": ("AgentQueueManager",),
    "reflection.reflector": ("ReflectionResult", "Reflector"),
    "core.hot_reloader": ("PromptHotReloader",),
    "lifecycle.retry": ("retry_with_backoff",),
    "safety.schema_validator": ("OutputSchemaValidator",),
    "lifecycle.rollback_handler": ("RollbackHandler",),
    "core.runtime_core": ("AgentRuntime", "RuntimeCore"),
    "core.runtime_helpers": ("CompositionHelper",),
    "runtime_llm": ("RuntimeLLM",),
    "core.runtime_state": ("ApprovalManager", "CheckpointManager", "RuntimeState"),
    "lifecycle.scheduler": ("AgentScheduler",),
    "memory.storage": ("AgentStorage", "SQLiteAgentStorage"),
    "core.secret_manager": ("SecretManager",),
    "memory.state_snapshot": ("SnapshotManager", "StateSnapshot", "ensure_snapshot_table"),
    "comm.streamer": ("AgentStreamer",),
    "tools.tool_bridge": ("ToolBridge", "ToolRegistry"),
    "memory.vector_memory": ("VectorMemory",),
    "evolution.reflexion_loop": ("ReflexionLoop",),
    "evolution.skill_library": ("SkillLibrary",),
    "safety.validator": ("AgentOutputValidator", "Validator"),
    "safety.verifier": ("RuleEngineLLM", "SafetyGuard", "Verifier"),
}

__all__ = [name for names in _EXPORTS.values() for name in names]

for _module_name, _names in _EXPORTS.items():
    _module = import_module(f"{__name__}.{_module_name}")
    globals().update({name: getattr(_module, name) for name in _names})

del import_module, _module, _module_name, _names, _EXPORTS
