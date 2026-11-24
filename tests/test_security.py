from datetime import UTC, datetime, timedelta

import jwt

from app.auth.security import (
    ALGORITHM,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from app.config import settings


def _token(payload: dict, key: str = settings.SECRET_KEY) -> str:
    return jwt.encode(payload, key, algorithm=ALGORITHM)


def _future() -> datetime:
    return datetime.now(UTC) + timedelta(minutes=5)


def test_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("password123")

    assert hashed != "password123"
    assert verify_password("password123", hashed)
    assert not verify_password("wrong-password", hashed)


def test_hash_is_salted():
    assert hash_password("password123") != hash_password("password123")


def test_token_roundtrip_returns_user_id():
    assert decode_access_token(create_access_token(42)) == 42


def test_decode_garbage_returns_none():
    assert decode_access_token("not.a.token") is None


def test_decode_token_signed_with_other_key_returns_none():
    token = _token({"sub": "1", "exp": _future()}, key="another-secret-key-with-32-characters!")

    assert decode_access_token(token) is None


def test_decode_token_without_sub_returns_none():
    assert decode_access_token(_token({"exp": _future()})) is None


def test_decode_token_with_non_numeric_sub_returns_none():
    assert decode_access_token(_token({"sub": "abc", "exp": _future()})) is None
