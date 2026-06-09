"""多媒体路由模块，定义文件上传、查看与AI分析的 API 端点。"""

from fastapi import APIRouter, Depends, File, Request, UploadFile

from assistant.app.services.media_service import MediaService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(tags=["media"])


@router.post("/media/upload", summary="上传媒体", description="上传媒体文件到服务器存储。", tags=["设备"])
async def upload_media(
    file: UploadFile = File(...),
    service: MediaService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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


@router.get("/media/{file_id}", summary="获取媒体信息", description="获取指定媒体文件的元数据信息。", tags=["设备"])
def get_media(
    file_id: int,
    service: MediaService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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


@router.post("/media/analyze/{file_id}", summary="分析媒体", description="对指定媒体文件进行AI内容分析识别。", tags=["设备"])
def analyze_media(
    file_id: int,
    request: Request,
    service: MediaService = Depends(),
    current_user: dict = Depends(require_scope("visit")),
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
