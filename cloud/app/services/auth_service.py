"""认证服务模块，处理用户注册、登录与 Token 刷新。"""

from fastapi import HTTPException
from starlette import status

from cloud.app.repositories import UsersRepository
from shared.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
    verify_token,
)
from shared.base_service import BaseService


class AuthService(BaseService):
    """认证服务，提供注册、登录及 JWT Token 刷新操作。"""

    def __init__(self, db=None):
        super().__init__(db=db)

    def register(self, username: str, password: str) -> dict:
        if len(username) < 3:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Username must be at least 3 characters",
            )
        if len(password) < 6:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                detail="Password must be at least 6 characters",
            )

        users_repo = UsersRepository(self.db)
        existing = users_repo.list_all(conditions=["username=?"], params=[username])
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exists")

        hashed = hash_password(password)
        user_id = users_repo.create({"username": username, "hashed_password": hashed})

        return {"user_id": user_id, "username": username}

    def login(self, username: str, password: str, scope: str = "visit") -> dict:
        users_repo = UsersRepository(self.db)
        rows = users_repo.list_all(conditions=["username=?"], params=[username])
        if not rows:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")
        row = rows[0]

        if not verify_password(password, row["hashed_password"]):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

        if not row["is_active"]:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        role = row["role"] or "rep"
        access_token = create_access_token(row["id"], role, scope)
        refresh_token = create_refresh_token(row["id"], scope)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "role": role,
        }

    def change_password(self, username: str, old_password: str, new_password: str) -> None:
        users_repo = UsersRepository(self.db)
        rows = users_repo.list_all(conditions=["username=?"], params=[username])
        if not rows:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User not found")

        row = rows[0]
        if not verify_password(old_password, row["hashed_password"]):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

        hashed = hash_password(new_password)
        users_repo.update(row["id"], {"hashed_password": hashed})

    def refresh(self, refresh_token: str) -> dict:
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = int(payload["sub"])
        users_repo = UsersRepository(self.db)
        user = users_repo.get_by_id(user_id)

        if not user:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="User not found")

        scope = payload.get("scope", "visit")
        access_token = create_access_token(user["id"], user["role"], scope=scope)
        new_refresh_token = create_refresh_token(user["id"], scope)

        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
        }
