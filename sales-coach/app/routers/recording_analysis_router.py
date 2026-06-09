"""实战录音分析 API。"""

from fastapi import APIRouter, File, Form, UploadFile
from sales_coach.app.services.recording_analysis_service import (
    UploadedAudio,
    analyze_recording,
    get_recording_analysis,
)

from shared.base import success

router = APIRouter(prefix="/api/recording", tags=["录音分析"])


@router.post("/upload", summary="上传实战录音", description="上传录音并生成语音表达分析报告", tags=["录音分析"])
async def upload_recording(
    file: UploadFile = File(..., description="录音文件"),
    user_id: str = Form(..., description="用户 ID"),
):
    content = await file.read()
    analysis = analyze_recording(UploadedAudio(filename=file.filename or "recording.wav", content=content, user_id=user_id))
    return success(data=analysis)


@router.get("/analysis/{user_id}", summary="录音分析结果", description="获取用户最近一次录音分析报告", tags=["录音分析"])
def recording_analysis(user_id: str):
    return success(data=get_recording_analysis(user_id))
