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
    user_id = int(current_user["sub"])
    data = await service.upload(file, user_id)
    return success(data=data)


@router.get("/media/{file_id}")
def get_media(
    file_id: int,
    service: MediaService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    row = service.get_media(file_id)
    return success(data=row)


@router.post("/media/analyze/{file_id}")
def analyze_media(
    file_id: int,
    request: Request,
    service: MediaService = Depends(),
    current_user: dict = Depends(get_current_user),
):
    auth_header = request.headers.get("Authorization", "")
    data = service.analyze(file_id, auth_header)
    return success(data=data)
