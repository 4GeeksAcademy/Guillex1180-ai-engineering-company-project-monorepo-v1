from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from tinydb import Query

if __package__ == "services.api.app.services":
    from ...database import password_reset_tokens
    from ...settings import settings
else:
    from database import password_reset_tokens
    from settings import settings


RESET_TOKEN_EXPIRE_MINUTES = 30


class InvalidResetTokenError(ValueError):
    pass


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_reset_token(user_id: int) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    token = jwt.encode(
        {
            "sub": str(user_id),
            "jti": secrets.token_urlsafe(32),
            "purpose": "password_reset",
            "exp": expires_at,
        },
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    token_payload = jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    token_query = Query()
    password_reset_tokens.update(
        {"used": True},
        (token_query.user_id == user_id) & (token_query.used == False),
    )
    password_reset_tokens.insert(
        {
            "token_hash": _token_hash(token),
            "user_id": user_id,
            "jti": token_payload["jti"],
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
            "used": False,
        }
    )
    return token


def consume_reset_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        user_id = int(payload["sub"])
        token_id = payload["jti"]
        if payload.get("purpose") != "password_reset":
            raise InvalidResetTokenError("El token no es de restablecimiento")
    except (JWTError, KeyError, TypeError, ValueError) as exc:
        raise InvalidResetTokenError("El token de restablecimiento no es válido") from exc

    stored_token = password_reset_tokens.get(
        Query().token_hash == _token_hash(token)
    )
    if (
        stored_token is None
        or stored_token.get("user_id") != user_id
        or stored_token.get("jti") != token_id
        or stored_token.get("used", True)
    ):
        raise InvalidResetTokenError("El token de restablecimiento no es válido")

    expires_at = datetime.fromisoformat(stored_token["expires_at"])
    if expires_at <= datetime.now(timezone.utc):
        raise InvalidResetTokenError("El token de restablecimiento ha expirado")

    updated_tokens = password_reset_tokens.update(
        {"used": True},
        (Query().token_hash == _token_hash(token)) & (Query().used == False),
    )
    if not updated_tokens:
        raise InvalidResetTokenError("El token de restablecimiento ya fue utilizado")
    return user_id