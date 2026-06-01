from cloud.shared.repository import BaseRepository
from cloud.shared.columns import (
    TABLE_TASK_BOARDS_COLS,
    TABLE_BOARD_TASKS_COLS,
    TABLE_TEAMS_COLS,
)


class TaskBoardsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "task_boards", TABLE_TASK_BOARDS_COLS)

    def get_active_by_id(self, board_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND is_active=1",
            (board_id,),
        ).fetchone()
        return dict(row) if row else None


class BoardTasksRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "board_tasks", TABLE_BOARD_TASKS_COLS)

    def get_by_board_and_id(self, board_id: int, task_id: int):
        placeholders = ", ".join(self.cols)
        row = self.db.execute(
            f"SELECT {placeholders} FROM {self.table_name} WHERE id=? AND board_id=?",
            (task_id, board_id),
        ).fetchone()
        return dict(row) if row else None

    def list_by_board(self, board_id: int, status_filter=None):
        conditions = ["board_id=?", "is_active=1"]
        params = [board_id]
        if status_filter:
            conditions.append("status=?")
            params.append(status_filter)
        return self.list_all(
            conditions=conditions,
            params=params,
            order_by="sort_order ASC, created_at DESC",
        )

    def list_by_assignee(self, user_id: int):
        placeholders = ", ".join(f"bt.{c}" for c in self.cols)
        rows = self.db.execute(
            f"SELECT {placeholders}, tb.name as board_name FROM {self.table_name} bt "
            "LEFT JOIN task_boards tb ON bt.board_id = tb.id "
            "WHERE bt.assignee_id=? AND bt.is_active=1 AND tb.is_active=1 "
            "ORDER BY bt.created_at DESC",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]


class TeamsRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "teams", TABLE_TEAMS_COLS)
