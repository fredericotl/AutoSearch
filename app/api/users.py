from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends,  HTTPException, APIRouter
from starlette import status
from app.models import User
from app.schemas import ChangePassword, ChangeEmail, UserResponse
from app.db.session import get_db
from app.core.security import get_current_user, is_password_equal, hash_password

router = APIRouter(prefix="/user", tags=["User"])

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/", status_code=status.HTTP_200_OK, response_model=UserResponse)
async  def get_user(user: user_dependency, db: db_dependency):
    return db.query(User).filter(User.id == user.get("id")).first()

#TODO passas para user_server.py
@router.put("/password",status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user: user_dependency, db: db_dependency,
                          change_password_request: ChangePassword):
    user_model = db.query(User).filter(User.id == user.get("id")).first()

    if not is_password_equal(change_password_request.old_password,user_model.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect Old Password")

    if not change_password_request.new_password == change_password_request.new_password_confirm:
        raise HTTPException(status_code=400, detail="New Password Does Not Match.")

    user_model.hashed_password=hash_password(change_password_request.new_password)
    db.add(user_model)
    db.commit()

#TODO passas para user_service.py
@router.put("/email",status_code=status.HTTP_204_NO_CONTENT)
async def change_email(user: user_dependency, db: db_dependency,
                          change_email_request: ChangeEmail):

    user_model = db.query(User).filter(User.id == user.get("id")).first()

    if not change_email_request.new_email == change_email_request.new_email_confirm:
        raise HTTPException(status_code=400, detail="New Email Does Not Match.")
    user_model.email = change_email_request.new_email
    db.add(user_model)
    db.commit()