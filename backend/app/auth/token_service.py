"""JWT token service for access and refresh tokens."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import hashlib
from jose import JWTError, jwt
from app.core.config import settings


def create_access_token(user_id: str) -> str:
    """Create JWT access token."""
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_refresh_token(user_id: str) -> tuple[str, str]:
    """Create JWT refresh token and return (token, jti)."""
    jti = str(uuid.uuid4())
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": str(user_id),
        "exp": expire,
        "jti": jti,
        "type": "refresh"
    }
    token = jwt.encode(to_encode, settings.JWT_REFRESH_SECRET_KEY, algorithm="HS256")
    return token, jti


def verify_access_token(token: str) -> Optional[str]:
    """Verify access token and return user_id."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def verify_refresh_token(token: str) -> Optional[tuple[str, str]]:
    """Verify refresh token and return (user_id, jti)."""
    try:
        payload = jwt.decode(token, settings.JWT_REFRESH_SECRET_KEY, algorithms=["HS256"])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub"), payload.get("jti")
    except JWTError:
        return None


def hash_token(token: str) -> str:
    """Hash token for storage in database."""
    return hashlib.sha256(token.encode()).hexdigest()
