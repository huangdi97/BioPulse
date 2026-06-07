"""L4 验证结果数据模型。"""

from pydantic import BaseModel


class CheckResult(BaseModel):
    name: str
    passed: bool
    detail: str = ""


class VerificationResult(BaseModel):
    passed: bool = False
    checks: list[CheckResult] = []
    confidence: float = 0.0
