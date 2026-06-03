from cloud.app.services.base import BaseService


class SettingsService(BaseService):
    """Settings 服务类。"""

    def get_all(self) -> dict:
        """get_all 操作。

        Returns:
            描述
        """
        rows = self.db.execute("SELECT key, value FROM settings").fetchall()
        return {row["key"]: row["value"] for row in rows}

    def update(self, settings: dict) -> dict:
        """更新。

        Args:
            settings: 描述

        Returns:
            描述
        """
        for key, value in settings.items():
            self.db.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime("now","localtime"))',
                (key, value),
            )
        self.db.commit()
        return self.get_all()
