from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import Depends,  HTTPException, APIRouter
from starlette import status
from app.schemas import ChangePassword, ChangeEmail, UserResponse
from app.db import get_db
from app.core import get_current_user, WrongPassword, UserNotFound
from app.services import find_user, change_user_password, change_user_email

router = APIRouter(prefix="/user", tags=["User"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
async  def get_user(user: user_dependency, db: db_dependency):
    try:
        user = find_user(db, user.get("id"))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))
    return user

@router.put("/password",status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          change_password_request: ChangePassword):
    try:
        change_user_password(db, user.get("id"), change_password_request)
        db.commit()
    except WrongPassword as e:
        raise HTTPException(status_code=400, detail=str(e))
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.put("/email",status_code=status.HTTP_204_NO_CONTENT)
async def change_email(user: user_dependency, db: db_dependency,
                          change_email_request: ChangeEmail):
    try:
        change_user_email(db, user.get("id"), change_email_request)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    except UserNotFound as e:
        raise HTTPException(status_code=401, detail=str(e))

