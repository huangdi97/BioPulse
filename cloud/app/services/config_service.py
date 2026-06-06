"""系统配置服务，提供系统设置键值的读取与更新。"""


class ConfigService:
    """系统配置服务，支持全量获取、单键读取与批量更新 settings 表。"""

    def __init__(self, db):
        self.db = db

    def get_all(self) -> dict:
        rows = self.db.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def get(self, key: str) -> str | None:
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else None

    def update(self, settings: dict) -> dict:
        for key, value in settings.items():
            self.db.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime("now","localtime"))',
                (key, value),
            )
        self.db.commit()
        return self.get_all()
