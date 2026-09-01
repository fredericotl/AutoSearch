from sqlalchemy.orm import Session
from app.models import User
from app.schemas import ChangePassword, ChangeEmail
from app.core import  is_password_equal, hash_password, WrongPassword

def find_user(db: Session, user_id:int):
    return db.query(User).filter(User.id == user_id).first()

def change_user_password(db: Session, user_id:int, change_password_request: ChangePassword):
    user_model = find_user(db, user_id)

    if not is_password_equal(change_password_request.old_password, user_model.hashed_password):
        raise WrongPassword("Incorrect Old Password")

    user_model.hashed_password = hash_password(change_password_request.new_password)
    db.add(user_model)

def change_user_email(db: Session,user_id: int, change_email_request: ChangeEmail):
    user_model = find_user(db, user_id)
    user_model.email = change_email_request.new_email
    db.add(user_model)