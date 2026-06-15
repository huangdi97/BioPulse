from cloud.app.services.notification_service import NotificationService


class TestNotificationService:
    def test_create_notification(self):
        svc = NotificationService()
        result = svc.create_notification(user_id=1, title="test", body="test", source="test")
        assert result is not None
