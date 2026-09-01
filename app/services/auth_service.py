from sqlalchemy.orm import Session
from app.core import is_password_equal, hash_password, WrongPassword, UserNotFound
from app.models import User
from app.schemas  import CreateUser


def create_new_user(db: Session, create_user_request: CreateUser):
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

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(User).filter(User.username== username).first()
    if not user:
        raise UserNotFound("User Not found")
    if not is_password_equal(password, user.hashed_password):
        raise WrongPassword("Incorrect Password")
    return user
