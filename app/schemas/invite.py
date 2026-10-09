from pydantic import BaseModel, EmailStr, ConfigDict, Field
from app.schemas.user import UserRole
from datetime import datetime

class CreateInvite(BaseModel):
    email: EmailStr
    invited_role: UserRole

class InviteResponse(BaseModel):
    email: EmailStr
    invited_role: UserRole = Field(default=UserRole.DEFAULT)
    token: str
    expires_at: datetime

class ValidInvite(BaseModel):
    id: int
    invited_role: UserRole = Field(default=UserRole.DEFAULT)
