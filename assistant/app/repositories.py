from datetime import datetime, timezone

from shared.columns import (
    TABLE_ASSISTANT_HCP_COLS,
    TABLE_HCP_LOCATION_COLS,
    TABLE_HEALTH_RADAR_COLS,
    TABLE_KNOWLEDGE_BASE_COLS,
    TABLE_MEDIA_FILE_COLS,
    TABLE_SURGERY_REMINDER_COLS,
    TABLE_SYNC_QUEUE_COLS,
    TABLE_TASK_COLS,
    TABLE_VISIT_RECORD_COLS,
)
from shared.repository import BaseRepository


class HcpRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp", TABLE_ASSISTANT_HCP_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM hcp WHERE name LIKE ? OR specialty LIKE ? OR hospital LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute("UPDATE hcp SET is_active=0, updated_at=? WHERE id=?", (now, row_id))
        self.db.commit()

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="updated_at DESC")

    def get_by_name(self, name):
        return self.db.execute("SELECT * FROM hcp WHERE name = ?", (name,)).fetchone()


class VisitRecordRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "visit_record", TABLE_VISIT_RECORD_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM visit_record WHERE summary LIKE ? OR notes LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE visit_record SET is_active=0, updated_at=? WHERE id=?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_hcp(self, hcp_id):
        return self.list_all(conditions=["hcp_id=?"], params=[hcp_id], order_by="visit_date DESC")

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="created_at DESC")


class TaskRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "task", TABLE_TASK_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM task WHERE title LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute("UPDATE task SET is_active=0, updated_at=? WHERE id=?", (now, row_id))
        self.db.commit()

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="updated_at DESC")

    def list_by_status(self, status):
        return self.list_all(conditions=["status=?"], params=[status], order_by="updated_at DESC")


class HealthRadarRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "health_radar", TABLE_HEALTH_RADAR_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM health_radar WHERE title LIKE ? OR description LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE health_radar SET is_active=0, updated_at=? WHERE id=?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="updated_at DESC")


class SurgeryReminderRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "surgery_reminder", TABLE_SURGERY_REMINDER_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM surgery_reminder WHERE patient_name LIKE ? OR surgery_type LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE surgery_reminder SET is_active=0, updated_at=? WHERE id=?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="updated_at DESC")


class KnowledgeBaseRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "knowledge_base", TABLE_KNOWLEDGE_BASE_COLS)

    def search(self, keyword, limit=50):
        return self.db.execute(
            "SELECT * FROM knowledge_base WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC LIMIT ?",
            (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%", limit),
        ).fetchall()

    def soft_delete(self, row_id):
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        self.db.execute(
            "UPDATE knowledge_base SET is_active=0, updated_at=? WHERE id=?",
            (now, row_id),
        )
        self.db.commit()

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="updated_at DESC")


class HcpLocationRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "hcp_location", TABLE_HCP_LOCATION_COLS)

    def list_by_hcp(self, hcp_id):
        return self.list_all(conditions=["hcp_id=?"], params=[hcp_id])


class SyncQueueRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "sync_queue", TABLE_SYNC_QUEUE_COLS)

    def list_pending(self):
        return self.list_all(conditions=["status='pending'"], order_by="created_at ASC")


class MediaFileRepository(BaseRepository):
    def __init__(self, db):
        super().__init__(db, "media_file", TABLE_MEDIA_FILE_COLS)

    def list_by_user(self, user_id):
        return self.list_all(conditions=["created_by=?"], params=[user_id], order_by="created_at DESC")
