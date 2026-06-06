"""语音路由模块，定义音频上传、语音对话与TTS合成的 API 端点。"""

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

from assistant.app.services.voice_service import VoiceService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(tags=["voice"])


@router.post("/voice/upload", summary="上传音频", description="上传音频文件到语音服务存储。")
async def upload_audio(
    file: UploadFile = File(...),
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """上传音频文件到语音服务。

    Args:
        file: 上传的音频文件
        service: 语音服务
        current_user: 当前登录用户

    Returns:
        上传后的文件信息
    """
    user_id = int(current_user["sub"])
    data = await service.upload(file, user_id)
    return success(data=data)


@router.post("/voice/chat", summary="语音对话", description="上传音频并获取AI语音回复进行对话。")
async def voice_chat(
    file: UploadFile = File(...),
    context: Optional[str] = Form(None),
    request: Request = None,
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """语音对话：上传音频并获取 AI 语音回复。

    Args:
        file: 用户输入的音频文件
        context: 对话上下文（可选）
        request: 请求对象（用于提取认证头）
        service: 语音服务
        current_user: 当前登录用户

    Returns:
        AI 回复的语音数据
    """
    user_id = int(current_user["sub"])
    auth_header = request.headers.get("Authorization", "")
    data = await service.chat(file, context, auth_header, user_id)
    return success(data=data)


@router.get("/voice/synthesize", summary="语音合成", description="将文本合成为语音并返回音频文件。")
async def synthesize(
    text: str = Query(..., min_length=1),
    voice: str = Query("zh-CN-XiaoxiaoNeural"),
    service: VoiceService = Depends(),
):
    """将文本合成为语音并返回音频文件。

    Args:
        text: 待合成的文本
        voice: 语音角色（默认中文女声 Xiaoxiao）
        service: 语音服务

    Returns:
        合成的 MP3 音频文件
    """
    if not text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")
    tts_path = await service.synthesize(text, voice)
    return FileResponse(tts_path, media_type="audio/mpeg")


@router.get("/media/audio/{file_id}", summary="下载音频", description="根据文件ID下载指定的音频文件。")
async def download_audio(
    file_id: int,
    service: VoiceService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """下载指定的音频文件。

    Args:
        file_id: 音频文件 ID
        service: 语音服务
        current_user: 当前登录用户

    Returns:
        音频文件响应
    """
    row = service.get_audio(file_id)
    return FileResponse(
        row["storage_path"],
        media_type=row["mime_type"] or "audio/mpeg",
    )
