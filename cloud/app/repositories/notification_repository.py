"""通知、通知模板等数据访问层。"""

from cloud.shared.columns import (
    TABLE_NOTIFICATION_TEMPLATES_COLS,
    TABLE_NOTIFICATIONS_COLS,
)
from cloud.shared.repository import BaseRepository


class NotificationsRepository(BaseRepository):
    """通知表。"""

    def __init__(self, db):
        super().__init__(db, "notifications", TABLE_NOTIFICATIONS_COLS)

    def create_notification(
        self,
        user_id: int,
        title: str,
        body_text: str,
        category: str,
        ref_type: str,
        ref_id: int,
    ):
        from datetime import datetime

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.create(
            {
                "user_id": user_id,
                "title": title,
                "body": body_text,
                "category": category,
                "ref_type": ref_type,
                "ref_id": ref_id,
                "created_at": now,
            }
        )


class NotificationTemplatesRepository(BaseRepository):
    """通知模板表。"""

    def __init__(self, db):
        super().__init__(db, "notification_templates", TABLE_NOTIFICATION_TEMPLATES_COLS)
