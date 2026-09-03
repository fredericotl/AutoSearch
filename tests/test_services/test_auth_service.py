from app.services.auth_service import create_new_user, authenticate_user
from app.core import hash_password, is_password_equal, UserNotFound, WrongPassword
from app.schemas  import CreateUser
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.models import User
import pytest

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def test_create_new_user():
    db= mock_db_session()
    create_user_request = CreateUser(
        email = "test@example.com",
        username = "testuser",
        first_name = "Test",
        last_name = "User",
        password = "password123",
        password_confirm= "password123",
    )
    create_new_user(db, create_user_request)
    user_arg = db.add.call_args[0][0]

    assert user_arg.email == create_user_request.email
    assert user_arg.username == create_user_request.username
    assert user_arg.first_name == create_user_request.first_name
    assert user_arg.last_name == create_user_request.last_name
    assert user_arg.is_active == True
    assert is_password_equal(create_user_request.password, user_arg.hashed_password)

def test_authenticate_user_success():
    db= mock_db_session()
    mock_user = MagicMock(spec=User)
    mock_user.username = "testuser"
    mock_user.hashed_password = hash_password("password123")
    db.query.return_value.filter.return_value.first.return_value = mock_user

    response = authenticate_user(db, "testuser", "password123")
    assert response.username == "testuser"
    assert is_password_equal("password123", response.hashed_password)

def test_authenticate_user_not_found():
    db= mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(UserNotFound):
        authenticate_user(db, "nonexistentuser", "password123")

def test_authenticate_user_wrong_password():
    db= mock_db_session()
    mock_user = MagicMock(spec=User)
    mock_user.username = "testuser"
    mock_user.hashed_password = hash_password("password123")
    db.query.return_value.filter.return_value.first.return_value = mock_user

    with pytest.raises(WrongPassword):
        authenticate_user(db, "testuser", "wrongpassword")
