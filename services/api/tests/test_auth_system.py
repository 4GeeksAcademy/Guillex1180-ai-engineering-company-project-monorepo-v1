from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from database import profiles, users
from main import app
from security import verify_password
from settings import settings


@pytest.fixture(autouse=True)
def isolate_auth_database():
    users.truncate()
    profiles.truncate()
    yield
    users.truncate()
    profiles.truncate()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client


def register_user(client: TestClient, **overrides: object):
    payload = {
        "email": "user@example.com",
        "password": "correct-password",
        "name": "Test User",
        "phone": "+34123456789",
        "address": "Calle Test 1",
        **overrides,
    }
    return client.post("/users", json=payload)


def login_user(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "correct-password",
):
    return client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )


def auth_headers(client: TestClient, **credentials: str) -> dict[str, str]:
    response = login_user(client, **credentials)
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_register_user_with_profile_hashes_password_and_defaults_role(
    client: TestClient,
) -> None:
    response = register_user(client)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["role"] == "user"
    assert "hashed_password" not in data

    stored_user = users.all()[0]
    assert stored_user["hashed_password"] != "correct-password"
    assert verify_password("correct-password", stored_user["hashed_password"])

    stored_profile = profiles.all()[0]
    assert stored_profile["user_id"] == data["id"]
    assert stored_profile["name"] == "Test User"
    assert stored_profile["phone"] == "+34123456789"
    assert stored_profile["address"] == "Calle Test 1"


def test_login_returns_valid_jwt_for_correct_credentials(client: TestClient) -> None:
    assert register_user(client).status_code == 201

    response = login_user(client)

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    payload = jwt.decode(
        data["access_token"],
        settings.secret_key,
        algorithms=[settings.algorithm],
    )
    assert payload["sub"] == "1"
    assert payload["exp"] > datetime.now(timezone.utc).timestamp()


def test_authenticated_me_returns_user_and_profile(client: TestClient) -> None:
    registration = register_user(client)
    headers = auth_headers(client)

    response = client.get("/auth/me", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["user"] == {
        "id": registration.json()["id"],
        "email": "user@example.com",
        "role": "user",
        "is_active": True,
    }
    assert data["profile"]["user_id"] == registration.json()["id"]
    assert data["profile"]["name"] == "Test User"


def test_get_and_update_authenticated_profile(client: TestClient) -> None:
    assert register_user(client).status_code == 201
    headers = auth_headers(client)

    get_response = client.get("/profiles/me", headers=headers)
    update_response = client.put(
        "/profiles/me",
        headers=headers,
        json={"name": "Updated User", "phone": "+34987654321"},
    )

    assert get_response.status_code == 200
    assert get_response.json()["name"] == "Test User"
    assert update_response.status_code == 200
    assert update_response.json()["name"] == "Updated User"
    assert update_response.json()["phone"] == "+34987654321"
    assert update_response.json()["address"] == "Calle Test 1"


def test_protected_route_without_token_returns_401(client: TestClient) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401


@pytest.mark.parametrize("token_kind", ["expired", "malformed", "invalid_signature"])
def test_invalid_tokens_return_401(client: TestClient, token_kind: str) -> None:
    if token_kind == "expired":
        token = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.secret_key,
            algorithm=settings.algorithm,
        )
    elif token_kind == "invalid_signature":
        token = jwt.encode(
            {"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
            "wrong-secret",
            algorithm=settings.algorithm,
        )
    else:
        token = "not-a-jwt"

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401


@pytest.mark.parametrize("password", ["wrong-password", ""])
def test_login_with_invalid_password_returns_401(
    client: TestClient,
    password: str,
) -> None:
    assert register_user(client).status_code == 201

    response = login_user(client, password=password)

    assert response.status_code == 401


def test_login_with_unknown_email_returns_401(client: TestClient) -> None:
    response = login_user(client, email="missing@example.com")

    assert response.status_code == 401


def test_user_cannot_update_another_users_account(client: TestClient) -> None:
    assert register_user(client).status_code == 201
    other_registration = register_user(
        client,
        email="other@example.com",
        name="Other User",
    )
    headers = auth_headers(client)

    response = client.put(
        f"/users/{other_registration.json()['id']}",
        headers=headers,
        json={"password": "new-password"},
    )

    assert response.status_code == 403


def test_non_admin_cannot_modify_own_role(client: TestClient) -> None:
    registration = register_user(client)
    headers = auth_headers(client)

    response = client.put(
        f"/users/{registration.json()['id']}",
        headers=headers,
        json={"role": "admin"},
    )

    assert response.status_code == 403
