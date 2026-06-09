"""录音分析请求与结果 schema。"""

from typing import List, Optional

from pydantic import BaseModel, Field


class VoiceAnalysisRequest(BaseModel):
    file_path: str = Field(..., min_length=1)
    visit_id: str = Field(..., min_length=1)
    hcp_id: Optional[str] = None


class VoiceAnalysisResult(BaseModel):
    transcript: str
    summary: str
    key_points: List[str] = Field(default_factory=list)
    concerns: List[str] = Field(default_factory=list)
    commitments: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    sentiment: str = "neutral"
