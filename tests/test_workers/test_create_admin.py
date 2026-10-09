from app.workers.create_admin import create_new_admin
from app.core import is_password_equal
from app.schemas import CreateUser
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def create_admin_request():
    return CreateUser(
        username="adminuser",
        email="admin@example.com",
        first_name="Admin",
        last_name="User",
        password="password123",
        password_confirm="password123",
        token="0123456789abcdef"
    )

def test_create_new_admin():
    db = mock_db_session()
    request = create_admin_request()

    with patch("app.workers.create_admin.SessionLocal", return_value=db):
        create_new_admin(request)
    user_arg = db.add.call_args[0][0]

    assert user_arg.username == request.username
    assert user_arg.email == request.email
    assert user_arg.role == "admin"
    assert user_arg.is_active == True
    assert is_password_equal(request.password, user_arg.hashed_password)
    db.commit.assert_called_once()
    db.close.assert_called_once()

def test_create_new_admin_duplicated():
    db = mock_db_session()
    db.commit.side_effect = IntegrityError("INSERT", {}, Exception())

    with patch("app.workers.create_admin.SessionLocal", return_value=db):
        create_new_admin(create_admin_request())

    db.rollback.assert_called_once()
    db.close.assert_called_once()