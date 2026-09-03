from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

if __package__ == "services.api":
    from .database import users
    from .settings import settings
else:
    from database import users
    from settings import settings


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _credentials_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expires_at},
        settings.secret_key,
        algorithm=settings.algorithm,
    )


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        subject = payload.get("sub")
        user_id = int(subject)
    except (JWTError, TypeError, ValueError):
        raise _credentials_error() from None

    user = users.get(doc_id=user_id)
    if user is None or not user.get("is_active", True):
        raise _credentials_error()
    return dict(user, id=user.doc_id)