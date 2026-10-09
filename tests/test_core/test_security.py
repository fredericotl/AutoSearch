from datetime import datetime, timezone, timedelta
from jose import jwt
from app.core.security import (is_password_equal, hash_password, create_access_token,
                               SECRET_KEY, ALGORITHM, get_current_user, get_admin,
                               create_invite_token, hash_invite_token)
import pytest
from fastapi import HTTPException

def test_is_password_equal_valid():
    password = "mysecretpassword"
    hashed_password = hash_password(password)
    assert hashed_password is not None
    assert is_password_equal(password, hashed_password) is True


def test_is_password_equal_invalid():
    password = "mysecretpassword"
    hashed_password = hash_password(password)
    assert hashed_password is not None
    assert is_password_equal("wrongpassword", hashed_password) is False


def test_create_access_token_valid():
    token = create_access_token("fred", 1, "admin")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                         options={"verify_signature": False})
    assert payload["sub"] == "fred"
    assert payload["id"] == 1
    assert payload["role"] == "admin"

def test_create_access_token_expiration():
    token = create_access_token("fred", 1, "admin")
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM],
                         options={"verify_signature": False})
    assert "exp" in payload

@pytest.mark.asyncio
async  def test_get_current_user_valid_token():
    encode = {"sub": "testuser", "id": 1, "role":"admin"}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    user = await get_current_user(token=token)

    assert  user == {"username": "testuser", "id": 1, "role":"admin"}

@pytest.mark.asyncio
async  def test_get_current_user_missing_payload():
    encode = {"role":"admin"}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token)
    assert  excinfo.value.status_code == 401
    assert  excinfo.value.detail == "Authentication Failed"

@pytest.mark.asyncio
async  def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as excinfo:
        await get_current_user("invalidtoken")
    assert  excinfo.value.status_code == 401
    assert  excinfo.value.detail == "Authentication Failed"

@pytest.mark.asyncio
async  def test_get_current_user_expired_token():
    encode = {"sub": "testuser", "id": 1, "role":"admin",
              "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token)
    assert  excinfo.value.status_code == 401
    assert  excinfo.value.detail == "Token Expired"

def test_create_invite_token_length():
    token = create_invite_token()
    assert len(token) == 16

def test_hash_invite_token_deterministic():
    assert hash_invite_token("abc") == hash_invite_token("abc")
    assert hash_invite_token("abc") != hash_invite_token("abd")

@pytest.mark.asyncio
async  def test_get_admin_valid():
    user = {"username": "testuser", "id": 1, "role":"admin"}
    assert await get_admin(user) == user

@pytest.mark.asyncio
async  def test_get_admin_not_admin():
    user = {"username": "testuser", "id": 1, "role":"default"}
    with pytest.raises(HTTPException) as excinfo:
        await get_admin(user)
    assert  excinfo.value.status_code == 403
    assert  excinfo.value.detail == "Not Authorized"
