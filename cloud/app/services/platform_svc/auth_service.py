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
        """初始化认证服务。

        参数:
            db: 可选，数据库连接对象。

        返回:
            None
        """
        super().__init__(db=db)

    def register(self, username: str, password: str) -> dict:
        """注册新用户。

        参数:
            username: 用户名，至少 3 个字符。
            password: 密码，至少 6 个字符。

        返回:
            包含 user_id 和 username 的字典。

        异常:
            HTTPException 409: 用户名已存在或不符合长度要求。
        """
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

        users_repo = UsersRepository(self._connection())
        existing = users_repo.list_all(conditions=["username=?"], params=[username])
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="Username already exists")

        hashed = hash_password(password)
        user_id = users_repo.create({"username": username, "hashed_password": hashed})

        return {"user_id": user_id, "username": username}

    def login(self, username: str, password: str, scope: str = "visit") -> dict:
        """用户登录，验证凭据并返回 JWT Token。

        参数:
            username: 用户名。
            password: 密码。
            scope: 作用域，默认为 "visit"。

        返回:
            包含 access_token、refresh_token、token_type 和 role 的字典。

        异常:
            HTTPException 401: 用户名或密码无效。
            HTTPException 403: 账户未激活。
        """
        users_repo = UsersRepository(self._connection())
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
        """修改用户密码。

        参数:
            username: 用户名。
            old_password: 旧密码。
            new_password: 新密码。

        返回:
            None

        异常:
            HTTPException 400: 用户不存在或旧密码错误。
        """
        users_repo = UsersRepository(self._connection())
        rows = users_repo.list_all(conditions=["username=?"], params=[username])
        if not rows:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="User not found")

        row = rows[0]
        if not verify_password(old_password, row["hashed_password"]):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")

        hashed = hash_password(new_password)
        users_repo.update(row["id"], {"hashed_password": hashed})

    def refresh(self, refresh_token: str) -> dict:
        """使用刷新 Token 获取新的访问 Token。

        参数:
            refresh_token: 刷新 Token 字符串。

        返回:
            包含新的 access_token、refresh_token 和 token_type 的字典。

        异常:
            HTTPException 401: 刷新 Token 无效或用户不存在。
        """
        payload = verify_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

        user_id = int(payload["sub"])
        users_repo = UsersRepository(self._connection())
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
