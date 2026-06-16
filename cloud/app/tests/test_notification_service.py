from cloud.app.services.notification_service import NotificationService


class TestNotificationService:
    def test_create_notification(self):
        svc = NotificationService()
        result = svc.send(user_id=1, title="test", body="test", category="test")
        assert result is not None
