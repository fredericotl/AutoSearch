from sqlalchemy.orm import Session
from unittest.mock import MagicMock
import pytest
from app.models import User
from app.services import find_user, change_user_password, change_user_email
from app.schemas import ChangePassword, ChangeEmail
from app.core import is_password_equal, hash_password, WrongPassword

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def mock_user():
    mock_user = MagicMock(spec=User)
    mock_user.id = 1
    mock_user.email = "test@example.com"
    mock_user.username = "testuser"
    mock_user.first_name = "Test"
    mock_user.last_name = "User"
    mock_user.hashed_password = hash_password("password123")
    mock_user.is_active = True
    return mock_user

def test_find_user():
    db = mock_db_session()
    mock_user_instance = mock_user()
    db.query.return_value.filter.return_value.first.return_value = mock_user_instance
    assert find_user(db, 1) == mock_user_instance

def test_change_user_password_success():
    db = mock_db_session()
    mock_user_instance = mock_user()
    db.query.return_value.filter.return_value.first.return_value = mock_user_instance

    change_password_request = ChangePassword(old_password="password123",
                                             new_password="newpassword",
                                             new_password_confirm="newpassword")
    change_user_password(db, 1, change_password_request)
    assert is_password_equal(change_password_request.new_password,
                             mock_user_instance.hashed_password)

def test_change_user_password_wrong_old_password():
    db = mock_db_session()
    mock_user_instance = mock_user()
    db.query.return_value.filter.return_value.first.return_value = mock_user_instance

    change_password_request = ChangePassword(old_password="wrongpassword",
                                             new_password="newpassword",
                                             new_password_confirm="newpassword")
    with pytest.raises(WrongPassword):
        change_user_password(db, 1, change_password_request)

def test_change_user_email_success():
    db = mock_db_session()
    mock_user_instance = mock_user()
    db.query.return_value.filter.return_value.first.return_value = mock_user_instance

    change_email_request = ChangeEmail(new_email="newemail@example.com",
                                       new_email_confirm="newemail@example.com")
    change_user_email(db, 1, change_email_request)
    assert mock_user_instance.email == "newemail@example.com"