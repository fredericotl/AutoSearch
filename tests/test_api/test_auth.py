from app.db import get_db
from tests.test_api.utils import *
from app.main import app

app.dependency_overrides[get_db] = override_get_db


def test_create_user_valid(test_invite):
    response = client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678",
        "token": INVITE_TOKEN
    })
    assert response.status_code == 201
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.email == "testuser@gmail.com"
    assert user.role == "default"
    assert response.json()["username"] == "testuser"
    invite = db.query(Invite).first()
    assert invite.used is True

def test_create_user_duplicated(test_user, test_invite):
    response = client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678",
        "token": INVITE_TOKEN
    })
    assert response.status_code == 409
    assert  response.json()["detail"] == "Username or Email already registered"
    db = TestingSessionLocal()
    invite = db.query(Invite).first()
    assert invite.used is False

def test_create_user_invite_not_found():
    response = client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678",
        "token": INVITE_TOKEN
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invite token not found"

def test_create_user_invite_already_used(test_invite):
    client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678",
        "token": INVITE_TOKEN
    })
    response = client.post("/auth", json={
        "username": "testuser2",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678",
        "token": INVITE_TOKEN
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invite token already used"

def test_login_for_asses_token_valid(test_user):
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "12345678"
    })
    assert response.status_code == 200

def test_login_for_asses_token_no_user(test_user):
    response = client.post("/auth/token", data={
        "username": "wronguser",
        "password": "12345678"
    })
    assert response.status_code == 401

def test_login_for_asses_token_wrong_password(test_user):
    response = client.post("/auth/token", data={
        "username": "testuser",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
