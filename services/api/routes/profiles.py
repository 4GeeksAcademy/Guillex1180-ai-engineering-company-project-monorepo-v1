from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

if __package__ == "services.api.routes":
    from ..app.services.profiles import get_profile_by_user_id, update_profile
    from ..models import ProfileResponse, ProfileUpdate
    from ..dependencies import get_current_user
else:
    from app.services.profiles import get_profile_by_user_id, update_profile
    from models import ProfileResponse, ProfileUpdate
    from dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _ensure_owner_or_admin(user_id: int, current_user: dict) -> None:
    if current_user["id"] != user_id and current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(current_user: dict = Depends(get_current_user)) -> ProfileResponse:
    profile = get_profile_by_user_id(current_user["id"])
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.put("/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    try:
        profile = update_profile(current_user["id"], payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.get("/{user_id}", response_model=ProfileResponse)
def get_profile(
    user_id: int,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    _ensure_owner_or_admin(user_id, current_user)
    profile = get_profile_by_user_id(user_id)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.put("/{user_id}", response_model=ProfileResponse)
def update_user_profile(
    user_id: int,
    payload: ProfileUpdate,
    current_user: dict = Depends(get_current_user),
) -> ProfileResponse:
    _ensure_owner_or_admin(user_id, current_user)
    try:
        profile = update_profile(user_id, payload)
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile