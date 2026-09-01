from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from app.db import get_db
from app.schemas import CreateUser, Token
from app.core import create_access_token, WrongPassword, UserNotFound
from app.services import create_new_user, authenticate_user
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter(prefix="/auth", tags=["Auth"])

db_dependency = Annotated[Session, Depends(get_db)]

@router.post("", status_code= status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUser):
    create_new_user(db, create_user_request)
    db.commit()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        token = create_access_token(username=user.username, user_id=user.id, user_role=user.role)
        return {"access_token": token, "token_type": "bearer"}
    except (UserNotFound, WrongPassword):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")