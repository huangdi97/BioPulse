from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse

from shared.auth import get_current_user
from shared.base import success
from assistant.app.services.voice_service import VoiceService

router = APIRouter(tags=["voice"])


@router.post("/voice/upload")
async def upload_audio(
    file: UploadFile = File(...),
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    data = await service.upload(file, user_id)
    return success(data=data)


@router.post("/voice/chat")
async def voice_chat(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    request: Request = None,
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    user_id = int(current_user["sub"])
    auth_header = request.headers.get("Authorization", "")
    data = await service.chat(file, context, auth_header, user_id)
    return success(data=data)


@router.get("/voice/synthesize")
async def synthesize(
    text: str = Query(..., min_length=1),
    voice: str = Query("zh-CN-XiaoxiaoNeural"),
    service: VoiceService = Depends(),
):
    if not text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    tts_path = await service.synthesize(text, voice)
    return FileResponse(tts_path, media_type="audio/mpeg")


@router.get("/media/audio/{file_id}")
async def download_audio(
    file_id: int,
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    row = service.get_audio(file_id)
    return FileResponse(
        row["storage_path"],
        media_type=row["mime_type"] or "audio/mpeg",
    )
