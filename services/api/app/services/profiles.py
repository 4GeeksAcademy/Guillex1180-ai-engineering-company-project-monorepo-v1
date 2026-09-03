from __future__ import annotations

from tinydb import Query

if __package__ == "services.api.app.services":
    from ...database import profiles
    from ...models import Profile, ProfileCreate, ProfileUpdate
else:
    from database import profiles
    from models import Profile, ProfileCreate, ProfileUpdate


def get_profile_by_user_id(user_id: int) -> Profile | None:
    record = profiles.get(Query().user_id == user_id)
    if record is None:
        return None
    return Profile(id=record.doc_id, **dict(record))


def create_profile(profile_data: ProfileCreate) -> Profile:
    if get_profile_by_user_id(profile_data.user_id) is not None:
        raise ValueError("User already has a profile")

    profile_id = profiles.insert(profile_data.model_dump(exclude_unset=True))
    profile = profiles.get(doc_id=profile_id)
    return Profile(id=profile_id, **dict(profile))


def update_profile(user_id: int, profile_data: ProfileUpdate) -> Profile | None:
    profile = profiles.get(Query().user_id == user_id)
    if profile is None:
        return None

    updates = profile_data.model_dump(exclude_unset=True)
    if not updates:
        raise ValueError("At least one profile field is required")

    profiles.update(updates, doc_ids=[profile.doc_id])
    updated_profile = profiles.get(doc_id=profile.doc_id)
    return Profile(id=updated_profile.doc_id, **dict(updated_profile))