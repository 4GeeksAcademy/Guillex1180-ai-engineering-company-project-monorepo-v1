from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.services.password_reset import create_reset_token
from database import audit_logs, password_reset_tokens, profiles, users
from main import app
from rate_limit import limiter
from security import hash_password, verify_password

TEST_EMAIL = "auth-reset-test@example.com"


@pytest.fixture(autouse=True)
def isolate_password_reset_database():
    users.truncate()
    profiles.truncate()
    password_reset_tokens.truncate()
    audit_logs.truncate()
    previous_enabled = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = previous_enabled
    users.truncate()
    profiles.truncate()
    password_reset_tokens.truncate()
    audit_logs.truncate()


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        users.truncate()
        profiles.truncate()
        password_reset_tokens.truncate()
        audit_logs.truncate()
        yield test_client


def register_user(client: TestClient) -> int:
    return users.insert(
        {
            "email": TEST_EMAIL,
            "hashed_password": hash_password("correct-password"),
            "is_active": True,
            "role": "user",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    )


def login_headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/auth/login",
        data={"username": TEST_EMAIL, "password": "correct-password"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_forgot_password_sends_reset_link_and_audits_request(
    client: TestClient,
) -> None:
    user_id = register_user(client)

    with patch("routes.auth.send_reset_password_email") as send_email:
        response = client.post(
            "/auth/forgot-password",
            json={"email": TEST_EMAIL},
            headers={"User-Agent": "auth-test", "X-Forwarded-For": "203.0.113.10"},
        )

    assert response.status_code == 200
    send_email.assert_called_once()
    assert send_email.call_args.kwargs["to_email"] == TEST_EMAIL
    reset_token = send_email.call_args.kwargs["reset_token"]
    assert reset_token
    audit = audit_logs.all()[0]
    assert audit["user_id"] == user_id
    assert audit["event_type"] == "PASSWORD_RESET_REQUESTED"
    assert audit["user_agent"] == "auth-test"
    assert audit["timestamp"].endswith("+00:00")


def test_forgot_password_unknown_email_has_same_success_response(
    client: TestClient,
) -> None:
    registered_response = client.post(
        "/auth/forgot-password",
        json={"email": TEST_EMAIL},
    )
    unknown_response = client.post(
        "/auth/forgot-password",
        json={"email": "unknown@example.com"},
    )

    assert registered_response.status_code == 200
    assert unknown_response.status_code == 200
    assert registered_response.json() == unknown_response.json()


def test_forgot_password_is_rate_limited_to_three_requests_per_hour(
    client: TestClient,
) -> None:
    limiter.enabled = True

    responses = [
        client.post("/auth/forgot-password", json={"email": "unknown@example.com"})
        for _ in range(4)
    ]

    assert [response.status_code for response in responses] == [200, 200, 200, 429]


def test_expired_reset_token_returns_400(client: TestClient) -> None:
    user_id = register_user(client)
    token = create_reset_token(user_id)
    stored_token = password_reset_tokens.all()[0]
    password_reset_tokens.update(
        {"expires_at": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat()},
        doc_ids=[stored_token.doc_id],
    )

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "new-password"},
    )

    assert response.status_code == 400


def test_reset_password_updates_password_and_invalidates_token(
    client: TestClient,
) -> None:
    user_id = register_user(client)
    token = create_reset_token(user_id)

    response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "new-password"},
    )
    repeated_response = client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": "another-password"},
    )

    assert response.status_code == 200
    assert repeated_response.status_code == 400
    assert verify_password("new-password", users.all()[0]["hashed_password"])
    assert password_reset_tokens.all()[0]["used"] is True
    assert audit_logs.all()[-1]["event_type"] == "PASSWORD_RESET_SUCCESS"


def test_change_password_rejects_incorrect_current_password(
    client: TestClient,
) -> None:
    register_user(client)

    response = client.post(
        "/auth/change-password",
        headers=login_headers(client),
        json={
            "current_password": "wrong-password",
            "new_password": "new-password",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "La contraseña actual es incorrecta"


def test_change_password_updates_password_and_audits_event(
    client: TestClient,
) -> None:
    user_id = register_user(client)

    response = client.post(
        "/auth/change-password",
        headers=login_headers(client),
        json={
            "current_password": "correct-password",
            "new_password": "new-password",
        },
    )

    assert response.status_code == 200
    assert verify_password("new-password", users.get(doc_id=user_id)["hashed_password"])
    assert audit_logs.all()[-1]["event_type"] == "PASSWORD_CHANGED"