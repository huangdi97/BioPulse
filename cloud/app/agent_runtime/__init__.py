"""Agent runtime public exports."""

from importlib import import_module

_EXPORTS = {
    "agent": ("Agent",),
    "agent_protocol": ("AgentMessage", "AgentMessageBus"),
    "agent_registry": ("AgentRegistry",),
    "agent_worker": ("AgentWorker",),
    "analysis_agent": ("AnalysisAgent",),
    "analyzer": ("Analysis",),
    "approval_workflow": ("ApprovalWorkflow",),
    "cost_governor": ("CostGovernor",),
    "guard": ("Guard", "GuardLayer1", "Layer", "Layer1Filter", "sanitize_tool_output"),
    "loop_detector": ("LoopDetector",),
    "metrics": ("agent_requests_total", "agent_llm_duration", "agent_active_count", "agent_tokens_total", "get_metrics"),
    "memory": ("AgentBrain", "AgentMemory", "Memory"),
    "models": (
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
    "notifier": ("AgentNotifier", "Notifier"),
    "pipeline": ("AgentPipeline", "Pipeline", "PipelineStep"),
    "planner": ("Plan", "PlanGenerator", "Planner", "PlanStep"),
    "queue_manager": ("AgentQueueManager",),
    "reflector": ("ReflectionResult", "Reflector"),
    "hot_reloader": ("PromptHotReloader",),
    "retry": ("retry_with_backoff",),
    "schema_validator": ("OutputSchemaValidator",),
    "rollback_handler": ("RollbackHandlerMixin",),
    "runtime_core": ("AgentRuntime", "RuntimeCore"),
    "runtime_helpers": ("RuntimeHelper",),
    "runtime_llm": ("RuntimeLLM",),
    "runtime_state": ("ApprovalManager", "CheckpointManager", "RuntimeState"),
    "scheduler": ("AgentScheduler",),
    "storage": ("AgentStorage", "SQLiteAgentStorage"),
    "secret_manager": ("SecretManager",),
    "state_snapshot": ("SnapshotManager", "StateSnapshot", "ensure_snapshot_table"),
    "streamer": ("AgentStreamer",),
    "tool_bridge": ("ToolBridge", "ToolRegistry"),
    "vector_memory": ("VectorMemory",),
    "validator": ("AgentOutputValidator", "Validator"),
    "verifier": ("RuleEngineLLM", "SafetyGuard", "Verifier"),
}

__all__ = [name for names in _EXPORTS.values() for name in names]

for _module_name, _names in _EXPORTS.items():
    _module = import_module(f"{__name__}.{_module_name}")
    globals().update({name: getattr(_module, name) for name in _names})

del import_module, _module, _module_name, _names, _EXPORTS
