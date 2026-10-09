from pydantic import EmailStr
from sqlalchemy.orm import Session
from app.models import Invite
from app.schemas import CreateInvite, InviteResponse, ValidInvite
from app.core import create_invite_token, hash_invite_token, now, INVITE_EXPIRE_DELTA, InvalidInvite

def create_invite(db: Session, invite_request: CreateInvite) -> InviteResponse:
    different_token = False
    token = None
    token_hash = None
    while not different_token:
        token = create_invite_token()
        token_hash = hash_invite_token(token)
        if db.query(Invite).filter(Invite.token_hash == token_hash).first() is None:
            different_token = True
    expires_at = now() + INVITE_EXPIRE_DELTA
    invite_model = Invite(
        token_hash=token_hash,
        email=invite_request.email,
        invited_role=invite_request.invited_role,
        expires_at=expires_at
    )
    db.add(invite_model)
    response = InviteResponse(email=invite_request.email, invited_role=invite_request.invited_role,
                              token=token, expires_at=expires_at)
    return response

def find_invite(db: Session, token: str, email :EmailStr) -> ValidInvite:
    hash_token = hash_invite_token(token)
    hash_token_response = db.query(Invite).filter(Invite.token_hash == hash_token).first()
    if hash_token_response is None:
        raise InvalidInvite("Invite token not found")
    if hash_token_response.expires_at < now():
        raise InvalidInvite("Invite token expired")
    if hash_token_response.used:
        raise InvalidInvite("Invite token already used")
    if hash_token_response.email != email:
        raise InvalidInvite("Invalid email for this token")
    return ValidInvite(id=hash_token_response.id, invited_role=hash_token_response.invited_role)

def update_invite(db: Session, invite_id: int) -> None:
    invite = db.query(Invite).filter(Invite.id == invite_id).first()
    if invite is not None:
        invite.used = True