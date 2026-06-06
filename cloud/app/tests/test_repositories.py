from unittest.mock import MagicMock


class TestUsersRepository:
    def test_create(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 42
        mock_db.execute.return_value.fetchone.return_value = [42]
        from cloud.app.repositories import UsersRepository

        repo = UsersRepository(mock_db)
        result = repo.create({"username": "testuser", "role": "user", "hashed_password": "hash"})

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO users" in call_args[0]
        assert mock_db.commit.called
        assert result == 42

    def test_get_by_id(self):
        mock_db = MagicMock()
        mock_row = {"id": 1, "username": "testuser", "role": "user"}
        mock_db.execute.return_value.fetchone.return_value = mock_row
        from cloud.app.repositories import UsersRepository

        repo = UsersRepository(mock_db)
        result = repo.get_by_id(1)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "SELECT" in call_args[0]
        assert "FROM users" in call_args[0]
        assert call_args[1] == (1,)
        assert result["username"] == "testuser"

    def test_update(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.rowcount = 1
        from cloud.app.repositories import UsersRepository

        repo = UsersRepository(mock_db)
        result = repo.update(1, {"role": "admin"})

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "UPDATE users" in call_args[0]
        assert "SET" in call_args[0]
        assert result is True

    def test_soft_delete(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.rowcount = 1
        from cloud.app.repositories import UsersRepository

        repo = UsersRepository(mock_db)
        result = repo.soft_delete(5)

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "UPDATE users" in call_args[0]
        assert "is_active=0" in call_args[0]
        assert result is True

    def test_list_all(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchall.return_value = [
            {"id": 1, "username": "u1"},
            {"id": 2, "username": "u2"},
        ]
        from cloud.app.repositories import UsersRepository

        repo = UsersRepository(mock_db)
        result = repo.list_all()

        assert len(result) == 2
        assert result[0]["username"] == "u1"


class TestContentsRepository:
    def test_create(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 10
        mock_db.execute.return_value.fetchone.return_value = [10]
        from cloud.app.repositories import ContentsRepository

        repo = ContentsRepository(mock_db)
        result = repo.create({"title": "Test", "body": "Body", "category": "medical"})

        mock_db.execute.assert_called_once()
        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO contents" in call_args[0]
        assert result == 10

    def test_get_by_id(self):
        mock_db = MagicMock()
        mock_row = {"id": 5, "title": "Article", "body": "Content body"}
        mock_db.execute.return_value.fetchone.return_value = mock_row
        from cloud.app.repositories import ContentsRepository

        repo = ContentsRepository(mock_db)
        result = repo.get_by_id(5)

        call_args = mock_db.execute.call_args[0]
        assert "FROM contents" in call_args[0]
        assert result["title"] == "Article"

    def test_paginate(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = [25]
        mock_db.execute.return_value.fetchall.return_value = [
            {"id": 1, "title": "Item1"},
            {"id": 2, "title": "Item2"},
        ]
        from cloud.app.repositories import ContentsRepository

        repo = ContentsRepository(mock_db)
        total, pages, items = repo.paginate(page=1, page_size=10)

        assert total == 25
        assert pages == 3
        assert len(items) == 2
        assert items[0]["title"] == "Item1"


class TestAuditLogsRepository:
    def test_create(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 88
        mock_db.execute.return_value.fetchone.return_value = [88]
        from cloud.app.repositories import AuditLogsRepository

        repo = AuditLogsRepository(mock_db)
        result = repo.create(
            {
                "user_id": 1,
                "action": "test",
                "entity_type": "tests",
                "entity_id": 42,
                "detail": "test entry",
            }
        )

        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO audit_logs" in call_args[0]
        assert result == 88

    def test_paginate(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = [10]
        mock_db.execute.return_value.fetchall.return_value = [
            {"id": 1, "action": "create"},
            {"id": 2, "action": "update"},
        ]
        from cloud.app.repositories import AuditLogsRepository

        repo = AuditLogsRepository(mock_db)
        total, pages, items = repo.paginate(page=1, page_size=5)

        assert total == 10
        assert pages == 2
        assert len(items) == 2

    def test_paginate_with_conditions(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = [3]
        mock_db.execute.return_value.fetchall.return_value = [{"id": 1}]
        from cloud.app.repositories import AuditLogsRepository

        repo = AuditLogsRepository(mock_db)
        total, pages, items = repo.paginate(
            page=1,
            page_size=20,
            conditions=["action = ?"],
            params=["test_create"],
        )

        call_args = mock_db.execute.call_args[0]
        assert "WHERE action = ?" in call_args[0]
        assert total == 3


class TestNotificationsRepository:
    def test_create(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 77
        mock_db.execute.return_value.fetchone.return_value = [77]
        from cloud.app.repositories import NotificationsRepository

        repo = NotificationsRepository(mock_db)
        result = repo.create(
            {
                "user_id": 1,
                "title": "Hello",
                "body": "World",
                "category": "system",
            }
        )

        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO notifications" in call_args[0]
        assert result == 77

    def test_create_notification(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 99
        mock_db.execute.return_value.fetchone.return_value = [99]
        from cloud.app.repositories import NotificationsRepository

        repo = NotificationsRepository(mock_db)
        result = repo.create_notification(
            user_id=5,
            title="Alert",
            body_text="New message",
            category="system",
            ref_type="task",
            ref_id=10,
        )

        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO notifications" in call_args[0]
        assert result == 99

    def test_get_by_id(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = {
            "id": 1,
            "title": "Note",
            "is_read": 0,
        }
        from cloud.app.repositories import NotificationsRepository

        repo = NotificationsRepository(mock_db)
        result = repo.get_by_id(1)

        assert result["title"] == "Note"
        assert result["is_read"] == 0

    def test_paginate(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = [5]
        mock_db.execute.return_value.fetchall.return_value = [{"id": 1, "title": "N1"}]
        from cloud.app.repositories import NotificationsRepository

        repo = NotificationsRepository(mock_db)
        total, pages, items = repo.paginate(page=1, page_size=10)

        assert total == 5
        assert items[0]["title"] == "N1"

    def test_update_mark_read(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.rowcount = 1
        from cloud.app.repositories import NotificationsRepository

        repo = NotificationsRepository(mock_db)
        result = repo.update(3, {"is_read": 1})

        call_args = mock_db.execute.call_args[0]
        assert "UPDATE notifications" in call_args[0]
        assert "is_read" in call_args[0]
        assert result is True


class TestTaskBoardsRepository:
    def test_create(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.lastrowid = 55
        mock_db.execute.return_value.fetchone.return_value = [55]
        from cloud.app.repositories import TaskBoardsRepository

        repo = TaskBoardsRepository(mock_db)
        result = repo.create(
            {
                "name": "Sprint Board",
                "description": "Active sprint",
                "owner_id": 1,
            }
        )

        call_args = mock_db.execute.call_args[0]
        assert "INSERT INTO task_boards" in call_args[0]
        assert result == 55

    def test_get_by_id(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = {
            "id": 9,
            "name": "Dev Board",
        }
        from cloud.app.repositories import TaskBoardsRepository

        repo = TaskBoardsRepository(mock_db)
        result = repo.get_by_id(9)

        assert result["name"] == "Dev Board"

    def test_get_active_by_id(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = {
            "id": 3,
            "name": "Active Board",
            "is_active": 1,
        }
        from cloud.app.repositories import TaskBoardsRepository

        repo = TaskBoardsRepository(mock_db)
        result = repo.get_active_by_id(3)

        call_args = mock_db.execute.call_args[0]
        assert "is_active=1" in call_args[0]
        assert result["name"] == "Active Board"

    def test_paginate(self):
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = [2]
        mock_db.execute.return_value.fetchall.return_value = [
            {"id": 1, "name": "Board1"},
            {"id": 2, "name": "Board2"},
        ]
        from cloud.app.repositories import TaskBoardsRepository

        repo = TaskBoardsRepository(mock_db)
        total, pages, items = repo.paginate(page=1, page_size=10)

        assert len(items) == 2
        assert total == 2
        assert items[1]["name"] == "Board2"
