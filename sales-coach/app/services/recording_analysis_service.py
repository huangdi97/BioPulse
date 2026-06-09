"""实战录音分析服务。"""

from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException
from sales_coach.app.schemas.recording_analysis import RecordingAnalysis, SpeechMetrics
from starlette import status

FILLER_WORDS = ("嗯", "啊", "这个")
PERSUASION_KEYWORDS = ("数据证明", "临床证据", "指南推荐", "真实世界研究", "获益", "安全性")

_ANALYSES: dict[str, RecordingAnalysis] = {}


@dataclass
class UploadedAudio:
    """上传音频的轻量输入对象。"""

    filename: str
    content: bytes
    user_id: Optional[str] = None


def _decode_transcription(audio_file: UploadedAudio) -> str:
    try:
        decoded = audio_file.content.decode("utf-8").strip()
    except UnicodeDecodeError:
        decoded = ""
    control_chars = sum(1 for char in decoded if ord(char) < 32 and char not in "\n\r\t")
    if decoded and control_chars == 0 and not decoded.startswith(("RIFF", "ID3")):
        return decoded
    return "您好，今天我想结合数据证明和临床证据，说明这个治疗方案的获益和安全性。嗯，如果您关注患者依从性，我们也可以看真实世界研究。"


def _estimate_duration_minutes(content: bytes, transcription: str) -> float:
    if content:
        estimated_seconds = max(12.0, min(300.0, len(content) / 16000.0))
    else:
        estimated_seconds = max(12.0, len(transcription) / 4.0)
    return estimated_seconds / 60.0


def _count_occurrences(text: str, needles: tuple[str, ...]) -> int:
    return sum(text.count(needle) for needle in needles)


def _build_report(metrics: SpeechMetrics) -> list[str]:
    report = []
    if metrics.speech_rate > 240:
        report.append("语速偏快，建议在核心证据和关键结论前主动降速。")
    elif metrics.speech_rate < 120:
        report.append("语速偏慢，建议缩短铺垫并提高关键信息密度。")
    else:
        report.append("语速处于可理解区间，可继续保持稳定节奏。")

    if metrics.filler_word_count > 2:
        report.append("填充词偏多，建议用短暂停顿替代“嗯、啊、这个”等口头习惯。")
    if metrics.pause_frequency > 8:
        report.append("停顿频率较高，建议提前组织证据链，减少不必要的断句。")
    if metrics.persuasion_word_count < 2:
        report.append("说服力关键词不足，建议补充数据证明、临床证据或指南推荐。")
    else:
        report.append("已使用证据型表达，可进一步把证据与客户关注点明确对应。")
    return report


def analyze_recording(audio_file: UploadedAudio) -> RecordingAnalysis:
    """执行录音 ASR 模拟和 NLP 指标分析。"""

    transcription = _decode_transcription(audio_file)
    duration_minutes = _estimate_duration_minutes(audio_file.content, transcription)
    character_count = len(transcription.replace(" ", ""))
    pause_count = sum(transcription.count(mark) for mark in ("，", "。", "；", ",", ".", ";"))
    metrics = SpeechMetrics(
        speech_rate=round(character_count / duration_minutes, 1),
        pause_frequency=round(pause_count / duration_minutes, 1),
        filler_word_count=_count_occurrences(transcription, FILLER_WORDS),
        persuasion_word_count=_count_occurrences(transcription, PERSUASION_KEYWORDS),
    )
    analysis = RecordingAnalysis(
        user_id=audio_file.user_id or "anonymous",
        audio_file=audio_file.filename,
        transcription=transcription,
        metrics=metrics,
        improvement_report=_build_report(metrics),
    )
    _ANALYSES[analysis.user_id] = analysis
    return analysis


def get_recording_analysis(user_id: str) -> RecordingAnalysis:
    """获取用户最近一次录音分析结果。"""

    analysis = _ANALYSES.get(user_id)
    if analysis is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Recording analysis not found")
    return analysis
