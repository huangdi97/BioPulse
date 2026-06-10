"""用户服务管理用户信息与认证授权。"""

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import UsersRepository
from shared.base_service import BaseService


class UserService(BaseService):
    def list_users(self) -> list:
        users_repo = UsersRepository(self.db)
        rows = users_repo.list_all(order_by="id ASC")
        return [
            {
                "id": row["id"],
                "username": row["username"],
                "role": row["role"],
                "is_active": bool(row["is_active"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def get_user(self, user_id: int) -> dict:
        users_repo = UsersRepository(self.db)
        row = users_repo.get_by_id(user_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        return {
            "id": row["id"],
            "username": row["username"],
            "role": row["role"],
            "is_active": bool(row["is_active"]),
            "created_at": row["created_at"],
        }

    def update_user(self, user_id: int, updates: dict) -> None:
        users_repo = UsersRepository(self.db)
        row = users_repo.get_by_id(user_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        if updates:
            users_repo.update(user_id, updates)

    def delete_user(self, user_id: int) -> None:
        users_repo = UsersRepository(self.db)
        row = users_repo.get_by_id(user_id)
        if not row:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        users_repo.soft_delete(user_id)
