from datetime import UTC, datetime, timedelta

import jwt

from app.auth.security import ALGORITHM, create_access_token
from app.config import settings

CREDENTIALS = {"email": "alice@example.com", "password": "password123"}


def test_register_success(client):
    response = client.post("/auth/register", json=CREDENTIALS)

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "created_at" in body


def test_register_never_exposes_password(client):
    body = client.post("/auth/register", json=CREDENTIALS).json()

    assert "password" not in body
    assert "hashed_password" not in body


def test_register_normalizes_email_to_lowercase(client):
    response = client.post(
        "/auth/register",
        json={"email": "Alice@Example.COM", "password": "password123"},
    )

    assert response.status_code == 201
    assert response.json()["email"] == "alice@example.com"


def test_register_duplicate_email_returns_409(client):
    client.post("/auth/register", json=CREDENTIALS)

    response = client.post("/auth/register", json=CREDENTIALS)

    assert response.status_code == 409


def test_register_duplicate_email_is_case_insensitive(client):
    client.post("/auth/register", json=CREDENTIALS)

    response = client.post(
        "/auth/register",
        json={"email": "ALICE@example.com", "password": "password123"},
    )

    assert response.status_code == 409


def test_register_short_password_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"email": "alice@example.com", "password": "123"},
    )

    assert response.status_code == 422


def test_register_invalid_email_returns_422(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )

    assert response.status_code == 422


def test_login_success_returns_bearer_token(client):
    client.post("/auth/register", json=CREDENTIALS)

    response = client.post("/auth/login", json=CREDENTIALS)

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]


def test_login_wrong_password_returns_401(client):
    client.post("/auth/register", json=CREDENTIALS)

    response = client.post(
        "/auth/login",
        json={"email": CREDENTIALS["email"], "password": "wrong-password"},
    )

    assert response.status_code == 401


def test_login_unknown_email_returns_401(client):
    response = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )

    assert response.status_code == 401


def test_login_errors_do_not_reveal_which_emails_exist(client):
    client.post("/auth/register", json=CREDENTIALS)

    wrong_password = client.post(
        "/auth/login",
        json={"email": CREDENTIALS["email"], "password": "wrong-password"},
    )
    unknown_email = client.post(
        "/auth/login",
        json={"email": "ghost@example.com", "password": "password123"},
    )

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()


def test_me_with_valid_token_returns_user(client, auth_headers):
    response = client.get("/auth/me", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["email"] == "alice@example.com"


def test_me_without_token_returns_401(client):
    response = client.get("/auth/me")

    assert response.status_code == 401


def test_me_with_garbage_token_returns_401(client):
    response = client.get("/auth/me", headers={"Authorization": "Bearer not.a.token"})

    assert response.status_code == 401


def test_me_with_expired_token_returns_401(client):
    client.post("/auth/register", json=CREDENTIALS)
    expired = jwt.encode(
        {"sub": "1", "exp": datetime.now(UTC) - timedelta(minutes=1)},
        settings.SECRET_KEY,
        algorithm=ALGORITHM,
    )

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"})

    assert response.status_code == 401


def test_me_with_token_of_nonexistent_user_returns_401(client):
    token = create_access_token(user_id=9999)

    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
