from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

if __package__ == "services.api.routes":
    from ..app.services.profiles import get_profile_by_user_id
    from ..app.services.users import get_user_by_email
    from ..models import AuthMeResponse, AuthUserResponse, LoginResponse
    from ..dependencies import create_access_token, get_current_user
    from ..security import verify_password
else:
    from app.services.profiles import get_profile_by_user_id
    from app.services.users import get_user_by_email
    from models import AuthMeResponse, AuthUserResponse, LoginResponse
    from dependencies import create_access_token, get_current_user
    from security import verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


def _invalid_credentials() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post("/login", response_model=LoginResponse)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> LoginResponse:
    user = get_user_by_email(form_data.username)
    if (
        user is None
        or not user.is_active
        or not verify_password(form_data.password, user.hashed_password)
    ):
        raise _invalid_credentials()
    return LoginResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=AuthMeResponse)
def get_me(current_user: dict = Depends(get_current_user)) -> AuthMeResponse:
    profile = get_profile_by_user_id(current_user["id"])
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )

    user = AuthUserResponse(
        id=current_user["id"],
        email=current_user["email"],
        role=current_user.get("role", "user"),
        is_active=current_user.get("is_active", True),
    )
    return AuthMeResponse(user=user, profile=profile)