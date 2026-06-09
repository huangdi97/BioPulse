"""实战录音分析数据模型。"""

from pydantic import BaseModel, Field


class SpeechMetrics(BaseModel):
    """语音表达指标。"""

    speech_rate: float = Field(..., ge=0, description="估算语速，字/分钟")
    pause_frequency: float = Field(..., ge=0, description="估算停顿频率，次/分钟")
    filler_word_count: int = Field(..., ge=0, description="填充词数量")
    persuasion_word_count: int = Field(..., ge=0, description="说服力关键词数量")


class RecordingAnalysis(BaseModel):
    """录音分析结果。"""

    user_id: str
    audio_file: str
    transcription: str
    metrics: SpeechMetrics
    improvement_report: list[str]
