"""Repository smoke tests."""


def test_core_repository_imports():
    from cloud.app.repositories import UsersRepository

    assert UsersRepository is not None


def test_core_repository_imports_and_instantiates(tmp_path):
    import sqlite3

    from cloud.app.repositories import UsersRepository

    db_path = tmp_path / "repo.sqlite3"
    conn = sqlite3.connect(db_path)
    try:
        repo = UsersRepository(conn)

        assert isinstance(repo, UsersRepository)
    finally:
        conn.close()
