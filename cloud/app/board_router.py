from typing import Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from starlette import status

from cloud.app.services.board_service import BoardService
from shared.auth_scope import require_scope
from shared.base import success

router = APIRouter(prefix="/boards", tags=["团队管理"])


class BoardCreate(BaseModel):
    name: str
    description: str = ""


class BoardUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_board(
    body: BoardCreate,
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    user_id = int(current_user["sub"])
    result = service.create_board(name=body.name, description=body.description, owner_id=user_id)
    return success(data=result)


@router.get("/")
def list_boards(
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    return success(data=service.list_boards())


@router.get("/{board_id}")
def get_board(
    board_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    return success(data=service.get_board(board_id))


@router.patch("/{board_id}")
def update_board(
    board_id: int,
    body: BoardUpdate,
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    result = service.update_board(board_id, name=body.name, description=body.description)
    return success(data=result)


@router.delete("/{board_id}")
def delete_board(
    board_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    service.delete_board(board_id)
    return success()


@router.get("/{board_id}/kanban")
def kanban_view(
    board_id: int,
    current_user: dict = Depends(require_scope("visit")),
    service: BoardService = Depends(),
) -> Any:
    return success(data=service.kanban_view(board_id))
