import sqlite3
from datetime import datetime, timezone
from typing import Optional

from shared.columns import TABLE_COACH_SCENARIO_COLS
from shared.repository import BaseRepository


class ScenarioRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "coach_scenario", TABLE_COACH_SCENARIO_COLS)

    def get_active_by_id(self, scenario_id: int) -> Optional[sqlite3.Row]:
        return self.db.execute(
            "SELECT * FROM coach_scenario WHERE id = ? AND is_active = 1",
            (scenario_id,),
        ).fetchone()

    def get_active_or_404(self, scenario_id: int) -> sqlite3.Row:
        row = self.get_active_by_id(scenario_id)
        if not row:
            from fastapi import HTTPException
            from starlette import status

            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Scenario not found")
        return row

    def soft_delete_scenario(self, scenario_id: int) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self.db.execute(
            "UPDATE coach_scenario SET is_active = 0, updated_at = ? WHERE id = ?",
            (now, scenario_id),
        )
        self.db.commit()

    def list_active(self, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.list_all(conditions=conds, params=params, order_by=order_by)

    def paginate_active(self, page=1, page_size=20, conditions=None, params=None, order_by="id DESC"):
        conds = ["is_active = 1"]
        if conditions:
            conds.extend(conditions)
        return self.paginate(
            page=page,
            page_size=page_size,
            conditions=conds,
            params=params,
            order_by=order_by,
        )
