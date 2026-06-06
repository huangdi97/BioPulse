"""反思服务模块，对外暴露反思报告生成接口。"""

from typing import Optional

from sales_coach.app.database import DB_PATH
from sales_coach.app.services.reflection_score import generate_reflection_report  # noqa: F401


def get_scenario(scenario_id: int) -> Optional[dict]:
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            "SELECT * FROM coach_scenario WHERE id = ?",
            (scenario_id,),
        ).fetchone()
        if row:
            return dict(row)
        return None
    finally:
        conn.close()
