"""Agent 运行时数据模型定义，包含工具、规格、结果、日志等结构。"""

from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel, Field


class AgentTier(str, Enum):
    local = "local"
    cloud_normal = "cloud_normal"
    cloud_agent = "cloud_agent"


class TriggerMode(str, Enum):
    l4 = "l4"
    event = "event"
    cron = "cron"
    user_request = "user_request"


class ModelPreference(BaseModel):
    provider: str = "deepseek"
    level: AgentTier = AgentTier.cloud_normal
    temperature: float = 0.3


class SafetyProfile(BaseModel):
    max_permission: str = "read"
    bulkhead_max_concurrent: int = 5
    rate_limit_per_minute: int = 30
    side_effect_check: bool = True
    layer3_deep_check: bool = True


class AgentIdentity(BaseModel):
    key: str
    name: str
    role: str
    goal: str
    backstory: str = ""
    allowed_tools: list[str] = Field(default_factory=list)
    memory_namespace: str = ""
    model_preference: ModelPreference = Field(default_factory=ModelPreference)
    cost_budget: float = 0.10
    trigger_mode: TriggerMode = TriggerMode.user_request
    event_subscriptions: list[str] = Field(default_factory=list)
    safety_profile: SafetyProfile = Field(default_factory=SafetyProfile)


class ExecutionContext(BaseModel):
    page_id: str
    user_id: str
    context_data: dict = Field(default_factory=dict)


class AgentResult(BaseModel):
    agent_key: str
    status: str = "pending"
    result: str = ""
    confidence: float = 0.0
    metadata: dict = Field(default_factory=dict)


class Insight(BaseModel):
    agent_key: str
    page_id: str
    summary: str
    details: dict = Field(default_factory=dict)
    confidence: float = 0.0


class ToolDef(BaseModel):
    """工具定义，含名称、描述、参数、权限级别及允许调用 Agent 列表。"""

    name: str
    description: str
    params: dict
    permission_level: str = "read"
    allowed_agents: list[str] = []


class AgentSpec(BaseModel):
    """Agent 规格，含角色描述、允许工具、迭代上限等配置。"""

    key: str
    role_desc: str
    allowed_tools: list[str]
    max_iterations: int
    default_temperature: float
    trigger_cron: str | None


class RuntimeResult(BaseModel):
    """运行时执行结果，含状态、输出、迭代次数及 token 消耗。"""

    status: str
    result: str
    iterations: int
    tool_calls: int
    logs: list[dict]
    metadata: dict = {"cost": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


class AgentLogEntry(BaseModel):
    """单步日志条目，记录动作、工具调用、耗时及 LLM 交互信息。"""

    step: int
    action: str
    tool: str | None
    params: dict | None
    result: str | None
    duration_ms: int
    llm_prompt: str | None = None
    llm_raw_response: str | None = None
    llm_token_usage: dict | None = None
    tool_input: str | None = None
    tool_output: str | None = None
    retry_count: int = 0
    trace_id: str = ""


@dataclass
class CheckpointData:
    """检查点数据，用于断点续跑时恢复消息与日志状态。"""

    trace_id: str
    step: int
    messages: list[dict]
    logs: list[dict]
    tool_calls_so_far: int
    goal: str
    agent_key: str
    context: dict | None = None


class AgentDecision(BaseModel):
    """Agent 决策，含动作类型、目标工具、参数及推理理由。"""

    action: str
    tool: str | None = None
    params: dict | None = None
    reasoning: str | None = None


class CheckResult(BaseModel):
    """单项验证检查结果。"""

    name: str
    passed: bool
    detail: str = ""


class VerificationResult(BaseModel):
    """L4 验证聚合结果。"""

    passed: bool = False
    checks: list[CheckResult] = []
    confidence: float = 0.0


class Models:
    """Namespace for agent runtime data models."""

    AgentIdentity = AgentIdentity
    ModelPreference = ModelPreference
    SafetyProfile = SafetyProfile
    ExecutionContext = ExecutionContext
    AgentResult = AgentResult
    Insight = Insight
    ToolDef = ToolDef
    AgentSpec = AgentSpec
    RuntimeResult = RuntimeResult
    AgentLogEntry = AgentLogEntry
    CheckpointData = CheckpointData
    AgentDecision = AgentDecision
    CheckResult = CheckResult
    VerificationResult = VerificationResult
