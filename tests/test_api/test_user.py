from app.core import get_current_user
from app.db import get_db
from tests.test_api.utils import *

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_get_user_success(test_user):
    response = client.get("/user/")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "testuser@gmail.com"

def test_change_password_success(test_user):
    response = client.put("/user/password", json={
        "old_password": "12345678",
        "new_password": "87654321",
        "new_password_confirm": "87654321"
    })
    assert response.status_code == 204


def test_change_password_failure(test_user):
    response = client.put("/user/password", json={
        "old_password": "wrongpassword",
        "new_password": "87654321",
        "new_password_confirm": "87654321"
    })
    assert response.status_code == 400

def test_change_email_success(test_user):
    response = client.put("/user/email", json={
        "new_email": "newemail@gmail.com",
        "new_email_confirm": "newemail@gmail.com"
    })
    assert response.status_code == 204

def test_change_email_fail(test_user):
    db = TestingSessionLocal()
    db.add(User(username="testuser2",
                email="testuser2@gmail.com",
                first_name="Test",
                last_name="User",
                hashed_password=bcrypt_context.hash("12345678"),
                role="default"))
    db.commit()
    response = client.put("/user/email", json={
        "new_email": "testuser2@gmail.com",
        "new_email_confirm": "testuser2@gmail.com"
    })
    assert response.status_code == 409
    assert  response.json()["detail"] == "Email already registered"
