from fastapi import APIRouter, Depends, File, Request, UploadFile

from assistant.app.services.media_service import MediaService
from shared.auth import get_current_user
from shared.base import success

router = APIRouter(tags=["media"])


@router.post("/media/upload")
async def upload_media(
    file: UploadFile = File(...),
    service: MediaService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """上传媒体文件。

    Args:
        file: 上传的文件
        service: 媒体服务
        current_user: 当前登录用户

    Returns:
        上传后的文件信息
    """
    user_id = int(current_user["sub"])
    data = await service.upload(file, user_id)
    return success(data=data)


@router.get("/media/{file_id}")
def get_media(
    file_id: int,
    service: MediaService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """获取指定媒体文件的元数据信息。

    Args:
        file_id: 文件 ID
        service: 媒体服务
        current_user: 当前登录用户

    Returns:
        文件元数据
    """
    row = service.get_media(file_id)
    return success(data=row)


@router.post("/media/analyze/{file_id}")
def analyze_media(
    file_id: int,
    request: Request,
    service: MediaService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    """分析指定媒体文件的内容（如 AI 识别）。

    Args:
        file_id: 文件 ID
        request: 请求对象（用于提取认证头）
        service: 媒体服务
        current_user: 当前登录用户

    Returns:
        分析结果
    """
    auth_header = request.headers.get("Authorization", "")
    data = service.analyze(file_id, auth_header)
    return success(data=data)
