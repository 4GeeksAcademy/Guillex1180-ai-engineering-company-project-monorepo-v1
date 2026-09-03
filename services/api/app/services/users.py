from __future__ import annotations

from datetime import datetime, timezone

from tinydb import Query

if __package__ == "services.api.app.services":
    from ...database import db, profiles, users
    from ...models import ProfileCreate, User, UserCreate, UserRole, UserUpdate
    from ...security import hash_password
else:
    from database import db, profiles, users
    from models import ProfileCreate, User, UserCreate, UserRole, UserUpdate
    from security import hash_password


def _to_user(record) -> User:
    return User(
        id=record.doc_id,
        email=record["email"],
        hashed_password=record["hashed_password"],
        is_active=record.get("is_active", True),
        role=record.get("role", UserRole.USER),
        created_at=record.get("created_at", datetime.now(timezone.utc).isoformat()),
    )


def _create_profile_for_user(user_id: int, payload: UserCreate) -> None:
    profiles.insert(
        ProfileCreate(
            user_id=user_id,
            name=payload.name,
            phone=payload.phone,
            address=payload.address,
        ).model_dump(exclude_unset=True)
    )


def create_user(payload: UserCreate) -> User:
    if get_user_by_email(str(payload.email)) is not None:
        raise ValueError("Email already registered")

    user_id = users.insert(
        {
            "email": str(payload.email),
            "hashed_password": hash_password(payload.password),
            "is_active": True,
            "role": UserRole.USER.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    try:
        _create_profile_for_user(user_id, payload)
    except Exception:
        users.remove(doc_ids=[user_id])
        raise
    return get_user_by_id(user_id)


def get_user_by_id(user_id: int) -> User | None:
    record = users.get(doc_id=user_id)
    return None if record is None else _to_user(record)


def get_user_by_email(email: str) -> User | None:
    record = users.get(Query().email == email)
    return None if record is None else _to_user(record)


def list_users() -> list[User]:
    return [_to_user(record) for record in users.all()]


def update_user(user_id: int, payload: UserUpdate) -> User | None:
    record = users.get(doc_id=user_id)
    if record is None:
        return None

    updates = payload.model_dump(exclude_unset=True, mode="json")
    if "email" in updates:
        existing_user = get_user_by_email(str(updates["email"]))
        if existing_user is not None and existing_user.id != user_id:
            raise ValueError("Email already registered")
    if "password" in updates:
        updates["hashed_password"] = hash_password(updates.pop("password"))
    if "email" in updates:
        updates["email"] = str(updates["email"])
    users.update(updates, doc_ids=[user_id])
    return get_user_by_id(user_id)


def delete_user(user_id: int) -> bool:
    if users.get(doc_id=user_id) is None:
        return False
    profiles.remove(Query().user_id == user_id)
    users.remove(doc_ids=[user_id])
    return True