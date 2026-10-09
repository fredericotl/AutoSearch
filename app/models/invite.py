from app.db import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from app.core import now, INVITE_EXPIRE_DELTA

class Invite(Base):
    __tablename__ = 'invites'

    id = Column(Integer, primary_key=True)
    token_hash = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    invited_role = Column(String, default="default", nullable=False)
    expires_at = Column(DateTime, default=lambda: now() + INVITE_EXPIRE_DELTA, nullable=False)
    used = Column(Boolean, default=False, nullable=False)