"""录音分析 API 路由。"""

from typing import Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile

from sales_assistant.app.services.voice_analysis_service import VoiceAnalysisService
from shared.base import ApiResponse, success

router = APIRouter(prefix="/api/voice", tags=["拜访"])


@router.post("/upload", summary="上传录音并分析", tags=["拜访"])
def upload_voice(
    file: UploadFile = File(...),
    visit_id: str = Form(...),
    hcp_id: Optional[str] = Form(None),
    service: VoiceAnalysisService = Depends(),
) -> ApiResponse:
    file_path = service.save_upload(file, visit_id)
    result = service.process_audio(file_path, visit_id, hcp_id)
    return success(data={"visit_id": visit_id, "hcp_id": hcp_id, "file_path": file_path, "analysis": result})


@router.get("/analysis/{visit_id}", summary="查看录音分析结果", tags=["拜访"])
def get_voice_analysis(
    visit_id: str,
    service: VoiceAnalysisService = Depends(),
) -> ApiResponse:
    return success(data=service.get_analysis(visit_id))
