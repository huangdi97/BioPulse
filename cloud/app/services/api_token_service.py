"""API Token 管理服务，负责创建、列表与撤销用户 API 令牌。"""

import hashlib
import secrets

from fastapi import HTTPException
from starlette import status

from shared.base_service import BaseService


class ApiTokenService(BaseService):
    """提供 API Token 的创建、查询与吊销功能。"""

    def create_token(self, name: str, user_id: int) -> dict:
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()

        cursor = self.db.execute(
            "INSERT INTO api_tokens (user_id, token_hash, name) VALUES (?, ?, ?)",
            (user_id, token_hash, name),
        )
        self.db.commit()

        return {
            "id": cursor.lastrowid,
            "name": name,
            "token": raw_token,
        }

    def list_tokens(self, user_id: int) -> list:
        rows = self.db.execute(
            "SELECT id, name, created_at, is_active FROM api_tokens WHERE user_id=? ORDER BY created_at DESC",
            (user_id,),
        ).fetchall()

        tokens = [
            {
                "id": row["id"],
                "name": row["name"],
                "created_at": row["created_at"],
                "is_active": bool(row["is_active"]),
            }
            for row in rows
        ]

        return tokens

    def revoke_token(self, token_id: int, user_id: int) -> None:
        row = self.db.execute(
            "SELECT id FROM api_tokens WHERE id=? AND user_id=?",
            (token_id, user_id),
        ).fetchone()

        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Token not found")

        self.db.execute(
            "UPDATE api_tokens SET is_active=0 WHERE id=?",
            (token_id,),
        )
        self.db.commit()
