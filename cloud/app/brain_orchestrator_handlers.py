"""大脑编排路由的请求与响应模型。"""

from pydantic import BaseModel


class SensoryIngest(BaseModel):
    """SensoryIngest 服务类。"""

    input_type: str = "message"
    raw_content: str = ""
    source: str = ""


class CreateProcedural(BaseModel):
    """CreateProcedural 服务类。"""

    procedure_key: str
    name: str = ""
    description: str = ""
    steps: str = "[]"
    trigger_conditions: str = "[]"


class InvokeProcedural(BaseModel):
    """InvokeProcedural 服务类。"""

    context: dict = {}


class Orchestrate(BaseModel):
    """Orchestrate 服务类。"""

    input_text: str = ""
    input_type: str = "message"
    source: str = ""


class EvolveMemory(BaseModel):
    """EvolveMemory 服务类。"""

    memory_id: int
    new_evidence: str = ""
    memory_type: str = "episodic"


class FoldMemories(BaseModel):
    """FoldMemories 服务类。"""

    memory_ids: list[int]
