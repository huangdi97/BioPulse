import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request
import bcrypt
import jwt
from jwt import ExpiredSignatureError, PyJWTError
from starlette import status

from shared.config import settings

ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.refresh_token_expire_days


def _get_secret_key() -> str:
    key = settings.jwt_secret_key
    if not key:
        raise ValueError(
            "JWT_SECRET_KEY is not set in environment or .env file. "
            "This is a security requirement for production."
        )
    return key


SECRET_KEY = _get_secret_key()


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(user_id: int, role: str = "rep", scope: str = "visit") -> str:
    """Create a short-lived JWT access token with user id, role and scope."""
    utcnow = datetime.now(timezone.utc)
    expires = utcnow + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": str(user_id),
        "role": role or "rep",
        "scope": scope,
        "jti": str(uuid.uuid4()),
        "type": "access",
        "exp": expires,
        "iat": utcnow,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def create_refresh_token(user_id: int, scope: str = "visit") -> str:
    """Create a long-lived JWT refresh token for obtaining new access tokens."""
    utcnow = datetime.now(timezone.utc)
    expires = utcnow + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "scope": scope,
        "jti": str(uuid.uuid4()),
        "exp": expires,
        "iat": utcnow,
    }
    return jwt.encode(payload, _get_secret_key(), algorithm=ALGORITHM)


def verify_token(token: str, db=None) -> dict:
    """Decode and validate a JWT token, returning its payload."""
    try:
        payload = jwt.decode(token, _get_secret_key(), algorithms=[ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    jti = payload.get("jti")
    if db and jti:
        _clean_expired_blacklist(db)
        row = db.execute("SELECT 1 FROM token_blacklist WHERE token_jti=?", (jti,)).fetchone()
        if row:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has been revoked")

    return payload


def get_current_user(request: Request, db=None) -> dict:
    """Extract and verify the Bearer token from the Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid auth header")
    token = auth[7:]
    return verify_token(token, db)


def add_token_to_blacklist(token: str, db) -> None:
    """Add a JWT token to the blacklist."""
    try:
        payload = jwt.decode(
            token, _get_secret_key(), algorithms=[ALGORITHM],
            options={"verify_exp": False},
        )
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token")

    jti = payload.get("jti")
    if not jti:
        return

    expires_at = datetime.fromtimestamp(payload["exp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if payload.get("exp") else None
    if not expires_at:
        return

    db.execute(
        "INSERT OR IGNORE INTO token_blacklist (token_jti, expires_at) VALUES (?, ?)",
        (jti, expires_at),
    )
    db.commit()


def _clean_expired_blacklist(db) -> None:
    """Remove expired entries from the blacklist."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    db.execute("DELETE FROM token_blacklist WHERE expires_at < ?", (now,))
