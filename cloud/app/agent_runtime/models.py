from dataclasses import dataclass

from pydantic import BaseModel


class ToolDef(BaseModel):
    name: str
    description: str
    params: dict
    permission_level: str = "read"


class AgentSpec(BaseModel):
    key: str
    role_desc: str
    allowed_tools: list[str]
    max_iterations: int
    default_temperature: float
    trigger_cron: str | None


class RuntimeResult(BaseModel):
    status: str
    result: str
    iterations: int
    tool_calls: int
    logs: list[dict]
    metadata: dict = {"cost": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}}


class AgentLogEntry(BaseModel):
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
    trace_id: str
    step: int
    messages: list[dict]
    logs: list[dict]
    tool_calls_so_far: int
    goal: str
    agent_key: str
    context: dict | None = None


class AgentDecision(BaseModel):
    action: str
    tool: str | None = None
    params: dict | None = None
    reasoning: str | None = None
