from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm

if __package__ == "services.api.routes":
    from ..app.services.audit_service import record_auth_event
    from ..app.services.email_service import send_reset_password_email
    from ..app.services.profiles import get_profile_by_user_id
    from ..app.services.users import get_user_by_email, get_user_by_id, update_user
    from ..models import (
        AuthMeResponse,
        AuthUserResponse,
        ChangePasswordRequest,
        ForgotPasswordRequest,
        ForgotPasswordResponse,
        LoginResponse,
        PasswordActionResponse,
        ResetPasswordRequest,
        UserUpdate,
    )
    from ..app.services.password_reset import (
        InvalidResetTokenError,
        consume_reset_token,
        create_reset_token,
    )
    from ..dependencies import create_access_token, get_current_user
    from ..rate_limit import limiter
    from ..security import verify_password
else:
    from app.services.audit_service import record_auth_event
    from app.services.email_service import send_reset_password_email
    from app.services.profiles import get_profile_by_user_id
    from app.services.users import get_user_by_email, get_user_by_id, update_user
    from models import (
        AuthMeResponse,
        AuthUserResponse,
        ChangePasswordRequest,
        ForgotPasswordRequest,
        ForgotPasswordResponse,
        LoginResponse,
        PasswordActionResponse,
        ResetPasswordRequest,
        UserUpdate,
    )
    from app.services.password_reset import (
        InvalidResetTokenError,
        consume_reset_token,
        create_reset_token,
    )
    from dependencies import create_access_token, get_current_user
    from rate_limit import limiter
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


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
@limiter.limit("3/hour")
def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest = Body(...),
) -> ForgotPasswordResponse:
    user = get_user_by_email(str(payload.email))
    if user is not None:
        record_auth_event(user.id, "PASSWORD_RESET_REQUESTED", request)

    if user is not None and user.is_active:
        reset_token = create_reset_token(user.id)
        send_reset_password_email(
            to_email=str(payload.email),
            reset_token=reset_token,
        )

    return ForgotPasswordResponse(
        message="Si esa dirección está registrada, recibirás un enlace en breve."
    )


@router.post("/reset-password", response_model=PasswordActionResponse)
def reset_password(
    payload: ResetPasswordRequest,
    request: Request,
) -> PasswordActionResponse:
    try:
        user_id = consume_reset_token(payload.token)
    except InvalidResetTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    user = get_user_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El token de restablecimiento no es válido",
        )

    update_user(user_id, UserUpdate(password=payload.new_password))
    record_auth_event(user_id, "PASSWORD_RESET_SUCCESS", request)
    return PasswordActionResponse(message="Contraseña restablecida correctamente")


@router.post("/change-password", response_model=PasswordActionResponse)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: dict = Depends(get_current_user),
) -> PasswordActionResponse:
    if not verify_password(payload.current_password, current_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    update_user(
        current_user["id"],
        UserUpdate(password=payload.new_password),
    )
    record_auth_event(current_user["id"], "PASSWORD_CHANGED", request)
    return PasswordActionResponse(message="Contraseña actualizada correctamente")


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