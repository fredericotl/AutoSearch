from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    DEFAULT = "default"

class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-zA-Z0-9]+$")
    email: EmailStr
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    password: str = Field(min_length=8, max_length=100)
    password_confirm: str = Field(min_length=8, max_length=100)
    token: str = Field(min_length=16, max_length=16)

    @model_validator(mode="after")
    def _password_match(self):
        if self.password != self.password_confirm:
            raise ValueError("password do not match")
        return self

class Token(BaseModel):
    access_token: str
    token_type: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    username: str
    email: str
    first_name: str = Field(max_length=100)
    last_name: str = Field(max_length=100)
    id: int
    is_active: bool

class ChangePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=100)
    new_password_confirm: str = Field(min_length=8, max_length=100)

    @model_validator(mode="after")
    def _password_match(self):
        if self.new_password != self.new_password_confirm:
            raise ValueError("password do not match")
        return self


class ChangeEmail(BaseModel):
    new_email: EmailStr
    new_email_confirm: EmailStr

    @model_validator(mode="after")
    def _emails_match(self):
        if self.new_email != self.new_email_confirm:
            raise ValueError("email do not match")
        return self

class ViewerRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    first_name: str = Field(max_length=100)