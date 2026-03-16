import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from app.config import settings


def create_access_token(payload: dict) -> str:
    """Issue a short-lived signed access JWT with a unique jti."""
    data = payload.copy()
    data.update({
        "type": "access",
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    })
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(payload: dict) -> tuple[str, str]:
    """Issue a long-lived refresh JWT. Returns (token, jti)."""
    jti = str(uuid.uuid4())
    data = payload.copy()
    data.update({
        "type": "refresh",
        "jti": jti,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    })
    return jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM), jti


def decode_token(token: str) -> dict:
    """Decode and verify a JWT. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
