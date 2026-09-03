from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

if __package__ == "services.api.routes":
    from ..app.services.users import (
        create_user as create_user_service,
        delete_user as delete_user_service,
        get_user_by_id,
        list_users as list_users_service,
        update_user as update_user_service,
    )
    from ..models import UserCreate, UserResponse, UserRole, UserUpdate
    from ..dependencies import get_current_user
else:
    from app.services.users import (
        create_user as create_user_service,
        delete_user as delete_user_service,
        get_user_by_id,
        list_users as list_users_service,
        update_user as update_user_service,
    )
    from models import UserCreate, UserResponse, UserRole, UserUpdate
    from dependencies import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


def _response(user) -> UserResponse:
    return UserResponse.model_validate(user.model_dump())


def _ensure_owner_or_admin(user_id: int, current_user: dict) -> None:
    if current_user["id"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> UserResponse:
    try:
        return _response(create_user_service(payload))
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.get("", response_model=list[UserResponse])
def list_users(_: dict = Depends(get_current_user)) -> list[UserResponse]:
    return [_response(user) for user in list_users_service()]


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, current_user: dict = Depends(get_current_user)) -> UserResponse:
    _ensure_owner_or_admin(user_id, current_user)
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return _response(user)


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    _ensure_owner_or_admin(user_id, current_user)
    user = get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if (payload.role is not None or payload.is_active is not None) and current_user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
    try:
        updated_user = update_user_service(user_id, payload)
    except ValueError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    return _response(updated_user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, current_user: dict = Depends(get_current_user)) -> Response:
    _ensure_owner_or_admin(user_id, current_user)
    if not delete_user_service(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)