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
