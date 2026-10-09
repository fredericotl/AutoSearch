from datetime import timedelta
from app.services.invite_service import create_invite, find_invite, update_invite
from app.core import hash_invite_token, now, InvalidInvite
from app.schemas import CreateInvite
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from app.models import Invite
import pytest

TOKEN = "abcdefghijklmnop"

def mock_db_session():
    mock_session = MagicMock(spec=Session)
    return mock_session

def mock_invite():
    mock = MagicMock(spec=Invite)
    mock.id = 1
    mock.email = "test@example.com"
    mock.invited_role = "admin"
    mock.expires_at = now() + timedelta(days=1)
    mock.used = False
    return mock

def test_create_invite():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = None
    invite_request = CreateInvite(email="test@example.com", invited_role="admin")
    response = create_invite(db, invite_request)
    invite_arg = db.add.call_args[0][0]

    assert invite_arg.token_hash == hash_invite_token(response.token)
    assert invite_arg.token_hash != response.token
    assert invite_arg.email == "test@example.com"
    assert invite_arg.invited_role == "admin"
    assert invite_arg.expires_at == response.expires_at
    assert response.expires_at > now()

def test_create_invite_token_collision():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.side_effect = [mock_invite(), None]
    invite_request = CreateInvite(email="test@example.com", invited_role="admin")
    response = create_invite(db, invite_request)
    invite_arg = db.add.call_args[0][0]

    assert db.query.return_value.filter.return_value.first.call_count == 2
    assert invite_arg.token_hash == hash_invite_token(response.token)

def test_find_invite_valid():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = mock_invite()

    result = find_invite(db, TOKEN, "test@example.com")
    assert result.id == 1
    assert result.invited_role == "admin"

def test_find_invite_not_found():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(InvalidInvite) as excinfo:
        find_invite(db, TOKEN, "test@example.com")
    assert str(excinfo.value) == "Invite token not found"

def test_find_invite_expired():
    db = mock_db_session()
    invite = mock_invite()
    invite.expires_at = now() - timedelta(minutes=1)
    db.query.return_value.filter.return_value.first.return_value = invite

    with pytest.raises(InvalidInvite) as excinfo:
        find_invite(db, TOKEN, "test@example.com")
    assert str(excinfo.value) == "Invite token expired"

def test_find_invite_already_used():
    db = mock_db_session()
    invite = mock_invite()
    invite.used = True
    db.query.return_value.filter.return_value.first.return_value = invite

    with pytest.raises(InvalidInvite) as excinfo:
        find_invite(db, TOKEN, "test@example.com")
    assert str(excinfo.value) == "Invite token already used"

def test_find_invite_wrong_email():
    db = mock_db_session()
    db.query.return_value.filter.return_value.first.return_value = mock_invite()

    with pytest.raises(InvalidInvite) as excinfo:
        find_invite(db, TOKEN, "other@example.com")
    assert str(excinfo.value) == "Invalid email for this token"

def test_update_invite():
    db = mock_db_session()
    invite = mock_invite()
    db.query.return_value.filter.return_value.first.return_value = invite

    update_invite(db, 1)
    assert invite.used is True
