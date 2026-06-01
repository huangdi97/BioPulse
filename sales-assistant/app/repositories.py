import sqlite3
from typing import List

from shared.columns import (
    TABLE_ANOMALY_ALERT_COLS,
    TABLE_ANOMALY_RULE_COLS,
    TABLE_COACHING_PROMPT_COLS,
    TABLE_COACHING_SESSION_COLS,
    TABLE_CONTENT_LIBRARY_COLS,
    TABLE_HCP_PRODUCT_RELATION_COLS,
    TABLE_MEETING_NOTE_COLS,
    TABLE_PRODUCT_COLS,
    TABLE_SALES_ASSISTANT_HCP_COLS,
    TABLE_SCHEDULE_COLS,
    TABLE_STRATEGY_SIMULATION_COLS,
    TABLE_VISIT_HCP_COLS,
)
from shared.repository import BaseRepository


class ScheduleRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "schedule", TABLE_SCHEDULE_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM schedule
               WHERE title LIKE ? OR description LIKE ? OR location LIKE ?
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class NoteRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "meeting_note", TABLE_MEETING_NOTE_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM meeting_note
               WHERE title LIKE ? OR content LIKE ? OR participants LIKE ?
                  OR action_items LIKE ?
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class ContentRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "content_library", TABLE_CONTENT_LIBRARY_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM content_library
               WHERE is_active = 1
                 AND (title LIKE ? OR content_type LIKE ? OR category LIKE ?
                      OR content LIKE ? OR tags LIKE ? OR summary LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class StrategyRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "strategy_simulation", TABLE_STRATEGY_SIMULATION_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM strategy_simulation
               WHERE is_active = 1
                 AND (hcp_name LIKE ? OR goal LIKE ? OR approach LIKE ?
                      OR talking_points LIKE ? OR expected_outcome LIKE ?
                      OR actual_outcome LIKE ? OR reflection LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class HcpRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "hcp", TABLE_SALES_ASSISTANT_HCP_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM hcp
               WHERE is_active = 1
                 AND (name LIKE ? OR hospital LIKE ? OR department LIKE ?
                      OR specialty LIKE ? OR city LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class ProductRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "product", TABLE_PRODUCT_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM product
               WHERE is_active = 1
                 AND (name LIKE ? OR category LIKE ? OR specification LIKE ?
                      OR company LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class RelationRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "hcp_product_relation", TABLE_HCP_PRODUCT_RELATION_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM hcp_product_relation
               WHERE is_active = 1
                 AND (relation_type LIKE ? OR strength LIKE ? OR notes LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class VisitRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "visit_hcp", TABLE_VISIT_HCP_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM visit_hcp
               WHERE products_discussed LIKE ? OR hcp_feedback LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class PromptRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "coaching_prompt", TABLE_COACHING_PROMPT_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM coaching_prompt
               WHERE is_active = 1
                 AND (trigger_type LIKE ? OR trigger_keywords LIKE ? OR scenario LIKE ?
                      OR prompt_template LIKE ? OR category LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class SessionRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "coaching_session", TABLE_COACHING_SESSION_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM coaching_session
               WHERE hcp_name LIKE ? OR current_scenario LIKE ? OR status LIKE ?
                  OR notes LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                f"%{keyword}%",
                limit,
            ),
        ).fetchall()


class AnomalyRuleRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "anomaly_rule", TABLE_ANOMALY_RULE_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM anomaly_rule
               WHERE is_active = 1
                 AND (rule_name LIKE ? OR metric LIKE ? OR description LIKE ?)
               ORDER BY updated_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()


class AlertRepository(BaseRepository):
    def __init__(self, db: sqlite3.Connection):
        super().__init__(db, "anomaly_alert", TABLE_ANOMALY_ALERT_COLS)

    def search(self, keyword: str, limit: int = 50) -> List[sqlite3.Row]:
        return self.db.execute(
            """SELECT * FROM anomaly_alert
               WHERE entity_type LIKE ? OR message LIKE ?
               ORDER BY created_at DESC LIMIT ?""",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()
