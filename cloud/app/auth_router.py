from typing import Any, Optional

from fastapi import APIRouter, Depends
from starlette import status
from pydantic import BaseModel, Field

from shared.base import success
from cloud.app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    scope: Optional[str] = "visit"


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/register", status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
    description="Creates a new user with username and password. Returns user_id on success.",
)
def register(body: RegisterRequest, service: AuthService = Depends()) -> Any:
    result = service.register(body.username, body.password)
    return success(data=result)


@router.post("/login",
    summary="Authenticate user and get tokens",
    description="Validates credentials and returns access_token and refresh_token.",
)
def login(body: LoginRequest, service: AuthService = Depends()) -> Any:
    result = service.login(body.username, body.password, body.scope)
    return success(data=result)


@router.post("/refresh",
    summary="Refresh access token",
    description="Exchange a valid refresh_token for a new access_token.",
)
def refresh(body: RefreshRequest, service: AuthService = Depends()) -> Any:
    result = service.refresh(body.refresh_token)
    return success(data=result)
