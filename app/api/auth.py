from datetime import timedelta
from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from typing import Annotated
from starlette import status
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import CreateUser, Token
from app.core.security import authenticate_user, create_access_token, hash_password
from fastapi.security import OAuth2PasswordRequestForm

EXPIREDELTA = timedelta(minutes=20)
router = APIRouter(prefix="/auth", tags=["Auth"])

db_dependency = Annotated[Session, Depends(get_db)]

#TODO passas para auth_service.py
@router.post("", status_code= status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUser):
    if not create_user_request.password == create_user_request.password_confirm:
        raise HTTPException(status_code=400, detail="Password Does Not Match")
    create_user_model = User(
        email = create_user_request.email,
        username = create_user_request.username,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password = hash_password(create_user_request.password),
        is_active = True,
        role= "default"

    )
    db.add(create_user_model)
    db.commit()

#TODO passas para auth_service.py
@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db:db_dependency):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed")
    token = create_access_token(user, EXPIREDELTA )
    return {"access_token":token, "token_type": "bearer"}