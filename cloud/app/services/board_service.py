"""看板服务，管理任务看板、任务卡片及 Kanban 视图。"""

from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import BoardTasksRepository, TaskBoardsRepository
from cloud.app.services.base import BaseService
from shared.base import validate_columns
from shared.columns import TABLE_TASK_BOARDS_COLS


def _board_to_dict(row) -> dict:
    """将数据库行转换为看板字典。"""
    return {
        "id": row["id"],
        "name": row["name"],
        "description": row["description"],
        "owner_id": row["owner_id"],
        "is_active": row["is_active"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _task_to_dict(row) -> dict:
    """将数据库行转换为任务卡片字典。"""
    return {
        "id": row["id"],
        "board_id": row["board_id"],
        "title": row["title"],
        "description": row["description"],
        "status": row["status"],
        "priority": row["priority"],
        "assignee_id": row["assignee_id"],
        "due_date": row["due_date"],
        "sort_order": row["sort_order"],
        "is_active": row["is_active"],
        "created_by": row["created_by"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


class BoardService(BaseService):
    """看板服务，提供看板 CRUD 及 Kanban 列视图。"""

    def _get_board_or_404(self, board_id: int):
        """按ID查找看板，不存在则返回404。"""
        boards_repo = TaskBoardsRepository(self.db)
        rows = boards_repo.list_all(conditions=["id=?", "is_active=1"], params=[board_id])
        if not rows:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Board not found")
        return rows[0]

    def create_board(self, name: str, description: str, owner_id: int) -> dict:
        """创建新看板。"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        boards_repo = TaskBoardsRepository(self.db)
        board_id = boards_repo.create(
            {
                "name": name,
                "description": description,
                "owner_id": owner_id,
                "created_at": now,
                "updated_at": now,
            }
        )
        row = boards_repo.get_by_id(board_id)
        return _board_to_dict(row)

    def list_boards(self) -> list:
        """获取所有活跃看板列表。"""
        boards_repo = TaskBoardsRepository(self.db)
        rows = boards_repo.list_all(
            conditions=["is_active=1"],
            order_by="created_at DESC",
        )
        return [_board_to_dict(r) for r in rows]

    def get_board(self, board_id: int) -> dict:
        """获取指定看板详情。"""
        row = self._get_board_or_404(board_id)
        return _board_to_dict(row)

    def update_board(
        self,
        board_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> dict:
        """更新看板名称或描述。"""
        self._get_board_or_404(board_id)
        boards_repo = TaskBoardsRepository(self.db)
        updates = {}
        if name is not None:
            updates["name"] = name
        if description is not None:
            updates["description"] = description
        if updates:
            updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            validate_columns(updates, "task_boards", TABLE_TASK_BOARDS_COLS)
            boards_repo.update(board_id, updates)
        row = self._get_board_or_404(board_id)
        return _board_to_dict(row)

    def delete_board(self, board_id: int) -> None:
        """软删除指定看板。"""
        self._get_board_or_404(board_id)
        boards_repo = TaskBoardsRepository(self.db)
        boards_repo.soft_delete(board_id)

    def kanban_view(self, board_id: int) -> dict:
        """获取看板的Kanban列视图。"""
        board_row = self._get_board_or_404(board_id)
        tasks_repo = BoardTasksRepository(self.db)
        rows = tasks_repo.list_all(
            conditions=["board_id=?", "is_active=1"],
            params=[board_id],
            order_by="sort_order ASC",
        )

        columns = {"todo": [], "in_progress": [], "done": []}
        for r in rows:
            task = _task_to_dict(r)
            status_key = r["status"] if r["status"] in columns else "todo"
            columns[status_key].append(task)

        return {
            "board": _board_to_dict(board_row),
            "columns": columns,
        }
