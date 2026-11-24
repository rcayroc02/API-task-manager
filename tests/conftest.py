import os

# Deben fijarse antes de importar la app: sobrescriben cualquier .env local.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "test-secret-key-with-at-least-32-characters"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - registra las tablas en Base.metadata
from app.database import Base, get_db
from app.main import app

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def override_get_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def make_auth_headers(client):
    """Devuelve una función que registra un usuario y entrega su header Authorization."""

    def _make(email: str = "alice@example.com", password: str = "password123") -> dict:
        client.post("/auth/register", json={"email": email, "password": password})
        response = client.post("/auth/login", json={"email": email, "password": password})
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _make


@pytest.fixture()
def auth_headers(make_auth_headers):
    return make_auth_headers("alice@example.com")


@pytest.fixture()
def other_headers(make_auth_headers):
    return make_auth_headers("bob@example.com")
