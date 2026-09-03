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