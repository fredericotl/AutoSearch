from app.db import get_db
from tests.test_api.utils import *
from app.main import app

app.dependency_overrides[get_db] = override_get_db


def test_create_user_valid():
    response = client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678"
    })
    assert response.status_code == 201
    db = TestingSessionLocal()
    user = db.query(User).filter(User.username == "testuser").first()
    assert user is not None
    assert user.email == "testuser@gmail.com"
    assert response.json()["username"] == "testuser"

def test_create_user_duplicated(test_user):
    response = client.post("/auth", json={
        "username": "testuser",
        "email": "testuser@gmail.com",
        "first_name": "Test",
        "last_name": "User",
        "password": "12345678",
        "password_confirm": "12345678"
    })
    assert response.status_code == 409
    assert  response.json()["detail"] == "Username or Email already registered"

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
