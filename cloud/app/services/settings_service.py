"""Settings service for system key-value configuration."""

import json
import sqlite3

from cloud.app.database import DB_PATH


class SettingsService:
    """系统键值配置服务，提供配置项的读写与全局管理。"""

    def _connect(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all(self) -> dict:
        conn = self._connect()
        try:
            rows = conn.execute("SELECT key, value FROM settings").fetchall()
        finally:
            conn.close()
        return {row["key"]: row["value"] for row in rows}

    def get(self, key: str) -> str | None:
        conn = self._connect()
        try:
            row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        finally:
            conn.close()
        return row["value"] if row else None

    def set(self, key: str, value: str, label: str = "") -> None:
        conn = self._connect()
        try:
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, datetime("now","localtime"))',
                (key, value),
            )
            conn.commit()
        finally:
            conn.close()

    def delete(self, key: str) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM settings WHERE key=?", (key,))
            conn.commit()
        finally:
            conn.close()

    def get_company_info(self) -> dict:
        conn = self._connect()
        try:
            row = conn.execute("SELECT value FROM settings WHERE key='company_info'").fetchone()
        finally:
            conn.close()
        if row is None:
            return {}
        return json.loads(row["value"])

    def set_company_info(self, data: dict) -> None:
        conn = self._connect()
        try:
            conn.execute(
                'INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (\'company_info\', ?, datetime("now","localtime"))',
                (json.dumps(data, ensure_ascii=False),),
            )
            conn.commit()
        finally:
            conn.close()
