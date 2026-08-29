from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends,  HTTPException, APIRouter
from starlette import status
from app.schemas import ChangePassword, ChangeEmail, UserResponse
from app.db.session import get_db
from app.core.security import get_current_user
from app.core.exceptions import WrongPassword
from app.services import find_user, change_user_password, change_user_email
router = APIRouter(prefix="/user", tags=["User"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
async  def get_user(user: user_dependency, db: db_dependency):
    return find_user(db, user.get("id"))

@router.put("/password",status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          change_password_request: ChangePassword):
    try:
        change_user_password(db, user.get("id"), change_password_request)
        db.commit()
    except WrongPassword as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/email",status_code=status.HTTP_204_NO_CONTENT)
async def change_email(user: user_dependency, db: db_dependency,
                          change_email_request: ChangeEmail):
    change_user_email(db, user.get("id"), change_email_request)
    db.commit()

