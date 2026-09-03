from app.schemas.user import CreateUser ,ChangePassword, ChangeEmail
import pytest

def test_create_user_valid():
    base = {"username": "fred", "email":"fred@example.com", "first_name":"Fred", "last_name":"Leite",
            "password":"password123", "password_confirm":"password123"}
    assert CreateUser(**base) is not None

def test_create_user_invalid_password_confirm():
    with pytest.raises(ValueError):
        base = {"username": "fred", "email": "fred@example.com", "first_name": "Fred", "last_name": "Leite",
                "password": "password123", "password_confirm": "different_password"}
        CreateUser(**base)

def test_change_password_valid():
    base = {"old_password":"oldpass", "new_password":"newpass123", "new_password_confirm":"newpass123"}
    assert ChangePassword(**base) is not None

def test_change_password_invalid_confirm():
    with pytest.raises(ValueError):
        base = {"old_password":"oldpass", "new_password":"newpass123", "new_password_confirm":"different_password"}
        ChangePassword(**base)

def test_change_email_valid():
    base = {"new_email":"new@example.com", "new_email_confirm":"new@example.com"}
    assert ChangeEmail(**base) is not None

def test_change_email_invalid_confirm():
    with pytest.raises(ValueError):
        base = {"new_email":"new@example.com", "new_email_confirm":"different@example.com"}
        ChangeEmail(**base)