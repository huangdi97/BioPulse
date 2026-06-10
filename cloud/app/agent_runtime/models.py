"""Agent 运行时数据模型定义，包含工具、规格、结果、日志等结构。"""

from dataclasses import dataclass

from pydantic import BaseModel


class ToolDef(BaseModel):
    """工具定义，含名称、描述、参数及权限级别。"""

    name: str
    description: str
    params: dict
    permission_level: str = "read"


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

    ToolDef = ToolDef
    AgentSpec = AgentSpec
    RuntimeResult = RuntimeResult
    AgentLogEntry = AgentLogEntry
    CheckpointData = CheckpointData
    AgentDecision = AgentDecision
    CheckResult = CheckResult
    VerificationResult = VerificationResult
